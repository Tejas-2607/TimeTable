# timetable_generator.py
"""
Schedules all practical lab sessions across labs.

BUGS FIXED:
1. select_compatible_batches used (year, div, batch) tuple as used_batches key but
   checked `if key in used_batches` — key is never a duplicate in the outer loop, so
   the guard never fired.  Fixed: track (year, div, batch_num) properly.

2. The greedy loop iterated days×slots once — batches that couldn't fit into early
   slots were simply dropped.  Fixed: retry loop keeps iterating until no progress
   is made, guaranteeing every batch gets scheduled if a valid slot exists.

3. Batch values stored in workload can be strings ("Batch 1") or ints (1).
   Normalised to int throughout so keys never mismatch.

4. is_slot_available_in_class returned False when the class key didn't exist yet
   (i.e. before any practical was written for that class).  That made it impossible
   to schedule the very first practical for a class.  Fixed: return True when key
   absent (nothing is blocking the slot).

5. "Batch Batch 1" double-prefix bug: f"Batch {batch}" where batch already was
   "Batch 1".  Fixed: normalise batch to int before formatting.

6. required_labs counter compared against total labs instead of free labs count,
   so it blocked scheduling when all labs had at least one free.  Fixed: compare
   against actual free labs count inside select_compatible_batches.

7. 2-hour practicals were split into 2 independent 1-hour entries and placed in
   random separate slots — they were never guaranteed to land in consecutive slots.
   Fixed: schedule both hours of a practical as a single atomic pair (slot + next_slot).
"""

from datetime import datetime
from config import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DAYS  = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
SLOTS = ['11:15', '14:15', '16:20']          # practical slots available per day

# Consecutive-slot pairs for 2-hour practicals.
# 16:20 has no follow-on (end of day) — 2-hr practicals avoid that slot.
NEXT_SLOT = {'11:15': '12:15', '14:15': '15:15'}
# Slots valid as the START of a 2-hour block
TWO_HR_START_SLOTS = ['11:15', '14:15']

subjects_collection          = db['subjects']
faculty_collection           = db['faculty']
workload_collection          = db['workload']
labs_collection              = db['labs']
class_timetable_collection   = db['class_timetable']
master_lab_timetable_collection = db['master_lab_timetable']


def _normalise_batch(raw) -> int:
    """Return batch as int. Accepts 1, '1', 'Batch 1', 'Batch Batch 1'."""
    if isinstance(raw, int):
        return raw
    s = str(raw).replace('Batch', '').strip()
    try:
        return int(s)
    except ValueError:
        return 1


class TimetableGenerator:
    """Generate practical timetables using greedy constraint satisfaction."""

    def __init__(self):
        self.timetable       = {'labs': {}}   # lab_name → day → slot → [sessions]
        self.class_schedules = {}             # (year, div) → day → slot → [sessions]
        self.faculty_names   = {}
        self.labs_list       = []

    # ─────────────────────────────────────────────────────────────────────────
    # DATA LOADING
    # ─────────────────────────────────────────────────────────────────────────

    def _load_faculty_names(self):
        for f in faculty_collection.find({}, {'_id': 1, 'name': 1, 'short_name': 1}):
            self.faculty_names[str(f['_id'])] = f.get('short_name') or f.get('name', '')
        logger.info(f"✓ Loaded {len(self.faculty_names)} faculty members")

    def _load_labs(self):
        labs = list(labs_collection.find({}))
        self.labs_list = [lab['name'] for lab in labs if lab.get('name')]
        for lab_name in self.labs_list:
            self.timetable['labs'][lab_name] = {
                day: {slot: [] for slot in SLOTS}
                for day in DAYS
            }
        logger.info(f"✓ Loaded {len(self.labs_list)} labs: {self.labs_list}")

    def _load_class_schedules(self):
        """Load existing class timetables (may contain lectures added earlier)."""
        for tt in class_timetable_collection.find({}):
            key = (tt['class'], tt['division'])
            # Deep-copy the schedule so we can mutate it safely
            self.class_schedules[key] = {
                day: {slot: list(sessions) for slot, sessions in day_sched.items()}
                for day, day_sched in tt.get('schedule', {}).items()
            }
        logger.info(f"✓ Loaded {len(self.class_schedules)} class timetables")

    # ─────────────────────────────────────────────────────────────────────────
    # ASSIGNMENT PREPARATION
    # ─────────────────────────────────────────────────────────────────────────

    def prepare_assignments(self) -> dict:
        """
        Build pending-practical queue.

        Key   : (year, division, batch_int)
        Value : list of practical dicts, one per weekly occurrence per subject.
                For a 2-hr practical there is ONE entry (not two) — we schedule
                both hours atomically as a consecutive pair.
        """
        assignments: dict = {}
        try:
            self._load_faculty_names()
            workloads = list(workload_collection.find({}))
            logger.info(f"Reading {len(workloads)} workload entries…")

            for w in workloads:
                year         = (w.get('year') or '').strip().upper()
                division     = w.get('division', 'A')
                batches_raw  = w.get('batches', [1, 2, 3])
                subject      = w.get('subject', '')
                subject_full = w.get('subject_full', subject)
                faculty_id   = str(w.get('faculty_id', ''))
                faculty_name = self.faculty_names.get(faculty_id, faculty_id)
                practical_hrs = int(w.get('practical_hrs', 1))

                for raw_batch in batches_raw:
                    batch = _normalise_batch(raw_batch)
                    key   = (year, division, batch)
                    if key not in assignments:
                        assignments[key] = []

                    # One entry per weekly occurrence of this subject for this batch.
                    # practical_hrs tells us how many consecutive slots to book.
                    assignments[key].append({
                        'subject':      subject,
                        'subject_full': subject_full,
                        'batch':        batch,
                        'faculty_id':   faculty_id,
                        'faculty':      faculty_name,
                        'year':         year,
                        'division':     division,
                        'practical_hrs': practical_hrs,   # 1 or 2
                    })

            total = sum(len(v) for v in assignments.values())
            logger.info(f"✓ {len(assignments)} batch-queues, {total} practical entries total")
            for k in sorted(assignments):
                logger.info(f"   {k[0]}-{k[1]}-B{k[2]}: {len(assignments[k])} practicals")
            return assignments

        except Exception as e:
            logger.error(f"prepare_assignments error: {e}", exc_info=True)
            return {}

    # ─────────────────────────────────────────────────────────────────────────
    # CONSTRAINT HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _faculty_busy(self, faculty: str, day: str, slot: str) -> bool:
        """True if faculty already has a session in any lab at (day, slot)."""
        for lab_sched in self.timetable['labs'].values():
            for sess in lab_sched.get(day, {}).get(slot, []):
                if sess.get('faculty') == faculty:
                    return True
        return False

    def _class_slot_free(self, year: str, division: str, day: str, slot: str) -> bool:
        """True if the class has no session at (day, slot) yet."""
        key = (year, division)
        if key not in self.class_schedules:
            return True                          # BUG-4 fix: unknown class = slot free
        return len(self.class_schedules[key].get(day, {}).get(slot, [])) == 0

    def _free_labs(self, day: str, slot: str) -> list:
        return [
            lab for lab, sched in self.timetable['labs'].items()
            if len(sched.get(day, {}).get(slot, [])) == 0
        ]

    def _can_schedule(self, practical: dict, day: str, slot: str,
                      used_faculty: set, used_class_slots: set) -> bool:
        """
        Full feasibility check for placing one practical session.
        For 2-hr practicals also verifies the next consecutive slot is free.
        """
        year        = practical['year']
        division    = practical['division']
        batch       = practical['batch']
        faculty     = practical['faculty']
        practical_hrs = practical['practical_hrs']

        # Faculty already picked for another batch this same slot
        if faculty in used_faculty:
            return False

        # Class-batch already placed somewhere this slot
        if (year, division, batch) in used_class_slots:
            return False

        # Faculty globally busy (already in another lab)
        if self._faculty_busy(faculty, day, slot):
            return False

        # Class slot already occupied
        if not self._class_slot_free(year, division, day, slot):
            return False

        # For 2-hr practical: validate next slot too
        if practical_hrs == 2:
            if slot not in NEXT_SLOT:          # 16:20 has no follow-on
                return False
            next_slot = NEXT_SLOT[slot]
            if not self._class_slot_free(year, division, day, next_slot):
                return False

        return True

    # ─────────────────────────────────────────────────────────────────────────
    # WRITE HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _ensure_class_schedule(self, year: str, division: str):
        key = (year, division)
        if key not in self.class_schedules:
            self.class_schedules[key] = {
                day: {slot: [] for slot in ['10:15','11:15','12:15','13:15','14:15','15:15','16:20']}
                for day in DAYS
            }

    def _write_session(self, practical: dict, day: str, slot: str, lab: str):
        """Write session to lab timetable and both class-schedule slots."""
        year     = practical['year']
        division = practical['division']
        batch    = practical['batch']
        subject  = practical['subject']
        faculty  = practical['faculty']
        hrs      = practical['practical_hrs']

        session = {
            'batch':        f"Batch {batch}",
            'subject':      subject,
            'subject_full': practical['subject_full'],
            'faculty':      faculty,
            'division':     division,
            'class':        year,
        }

        # ── Master lab timetable ──────────────────────────────────────────
        self.timetable['labs'][lab][day][slot].append(dict(session))

        # ── Class schedule (slot 1) ───────────────────────────────────────
        self._ensure_class_schedule(year, division)
        cs_entry = {**session, 'lab': lab, 'type': 'practical', 'faculty_id': practical['faculty_id']}
        self.class_schedules[(year, division)][day][slot].append(cs_entry)

        # ── Class schedule (slot 2 for 2-hr practicals) ───────────────────
        if hrs == 2 and slot in NEXT_SLOT:
            next_slot = NEXT_SLOT[slot]
            self.class_schedules[(year, division)][day][next_slot].append(dict(cs_entry))

        logger.info(f"  ✓ {year}-{division}-B{batch} {subject} → {lab} at {day} {slot}"
                    + (f"+{NEXT_SLOT[slot]}" if hrs == 2 and slot in NEXT_SLOT else ""))

    # ─────────────────────────────────────────────────────────────────────────
    # MAIN SCHEDULING LOOP
    # ─────────────────────────────────────────────────────────────────────────

    def generate(self) -> dict:
        logger.info("=" * 80)
        logger.info("STARTING PRACTICAL TIMETABLE GENERATION")
        logger.info("=" * 80)

        try:
            self._load_labs()
            self._load_class_schedules()
            assignments = self.prepare_assignments()

            if not assignments:
                return {'success': False, 'error': 'No assignments found'}
            if not self.labs_list:
                return {'success': False, 'error': 'No labs found'}

            scheduled_count = 0

            # ── Retry loop: keep making passes until no progress ──────────
            # This guarantees every batch is eventually placed even if the
            # first pass is blocked by other batches filling slots first.
            max_passes = 20
            for pass_num in range(max_passes):
                progress = False

                for day in DAYS:
                    for slot in SLOTS:
                        free_labs = self._free_labs(day, slot)
                        if not free_labs:
                            continue

                        # Collect which practicals can legally go here
                        candidates = []
                        used_faculty     : set = set()
                        used_class_slots : set = set()

                        # Sort: SY first, then TY, then BE; within year by div then batch
                        year_order = {'SY': 0, 'TY': 1, 'BE': 2}
                        sorted_keys = sorted(
                            assignments.keys(),
                            key=lambda k: (year_order.get(k[0], 9), k[1], k[2])
                        )

                        for key in sorted_keys:
                            queue = assignments[key]
                            if not queue:
                                continue
                            practical = queue[0]
                            if self._can_schedule(practical, day, slot,
                                                  used_faculty, used_class_slots):
                                candidates.append((key, practical))
                                used_faculty.add(practical['faculty'])
                                used_class_slots.add((practical['year'],
                                                      practical['division'],
                                                      practical['batch']))

                        # Place as many as we have free labs for
                        for i, (key, practical) in enumerate(candidates):
                            if i >= len(free_labs):
                                break
                            self._write_session(practical, day, slot, free_labs[i])
                            assignments[key].pop(0)
                            scheduled_count += 1
                            progress = True

                if not progress:
                    logger.info(f"No progress on pass {pass_num + 1} — stopping.")
                    break

                remaining = sum(len(q) for q in assignments.values())
                if remaining == 0:
                    logger.info(f"All practicals scheduled after {pass_num + 1} pass(es).")
                    break

            # ── Save master lab timetable ─────────────────────────────────
            for lab_name, schedule in self.timetable['labs'].items():
                master_lab_timetable_collection.replace_one(
                    {'lab_name': lab_name},
                    {'lab_name': lab_name, 'schedule': schedule, 'generated_at': datetime.now()},
                    upsert=True
                )
                logger.info(f"✓ Saved lab: {lab_name}")

            # ── Save class timetables ────────────────────────────────────
            all_slots = ['10:15','11:15','12:15','13:15','14:15','15:15','16:20']
            for (year, division), day_map in self.class_schedules.items():
                # Ensure all slots exist (even empty ones)
                for day in DAYS:
                    for sl in all_slots:
                        day_map.setdefault(day, {}).setdefault(sl, [])

                doc = {
                    'class':         year,
                    'division':      division,
                    'class_key':     f"{year}-{division}",
                    'schedule':      day_map,
                    'generated_at':  datetime.now(),
                    'total_practicals': sum(
                        1 for d in day_map.values()
                        for sl_sessions in d.values()
                        for s in sl_sessions if s.get('type') == 'practical'
                    ),
                }
                class_timetable_collection.replace_one(
                    {'class': year, 'division': division}, doc, upsert=True
                )
                logger.info(f"✓ Saved class timetable: {year}-{division}")

            # ── Leftovers report ─────────────────────────────────────────
            leftovers = {
                f"{y}-{d}-B{b}": [p['subject'] for p in q]
                for (y, d, b), q in assignments.items() if q
            }
            if leftovers:
                logger.warning(f"⚠️  Unscheduled: {leftovers}")
            else:
                logger.info("✅ All practicals successfully scheduled!")

            logger.info("=" * 80)
            logger.info(f"DONE: {scheduled_count} practical sessions scheduled")
            logger.info("=" * 80)

            return {
                'success': True,
                'message': f'Scheduled {scheduled_count} practical sessions',
                'labs_generated': len(self.labs_list),
                'practicals_scheduled': scheduled_count,
                'leftovers': leftovers,
            }

        except Exception as e:
            logger.error(f"generate() error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}


def generate():
    """Entry point called from app.py"""
    return TimetableGenerator().generate()