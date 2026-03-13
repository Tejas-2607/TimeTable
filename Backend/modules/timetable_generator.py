# timetable_generator.py
"""
Schedules all practical lab sessions across labs.

BUGS FIXED:
1. Class slot was blocked for ALL batches the moment any one batch occupied it.
   Batches from the same class CAN be in different labs at the same time.
   Fixed: tracking is now per (year, div, batch_int), not per (year, div).

2. timetable_generator was writing class timetables directly, then
   class_timetable_handler also rebuilt them from the master lab timetable —
   causing duplicate entries in follow-on slots (12:15, 15:15).
   Fixed: timetable_generator ONLY writes the master lab timetable.
   class_timetable_handler is the single writer for class timetables.

3. Lab follow-on slots were untracked, allowing double-booking of labs.
   Fixed: lab_schedule tracks ALL slots; _write_session fills both
   primary and follow-on slot in the lab schedule.

4. required_labs field from subjects was ignored.
   Fixed: _select_lab() enforces required_labs for Specific Lab subjects.

5. practical_duration in subjects is now authoritative (not workload.practical_hrs).

6. Only queue[0] was tried per batch per slot.
   Fixed: inner loop tries every pending subject in the batch queue.

7. Multiple candidates could grab the same lab in one pass.
   Fixed: used_labs set prevents double-claiming.
"""

from datetime import datetime
from config import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DAYS              = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
ALL_SLOTS         = ['10:15', '11:15', '12:15', '13:15', '14:15', '15:15', '16:20']
START_SLOTS       = ['11:15', '14:15', '16:20']
NEXT_SLOT         = {'11:15': '12:15', '14:15': '15:15'}
TWO_HR_START_SLOTS = ['11:15', '14:15']

subjects_collection             = db['subjects']
faculty_collection              = db['faculty']
workload_collection             = db['workload']
labs_collection                 = db['labs']
master_lab_timetable_collection = db['master_lab_timetable']


def _normalise_batch(raw) -> int:
    if isinstance(raw, int):
        return raw
    s = str(raw).replace('Batch', '').strip()
    try:
        return int(s)
    except ValueError:
        return 1


class TimetableGenerator:

    def __init__(self):
        self.lab_schedule   = {}   # lab_name → day → slot → [sessions]
        self.batch_occupied = {}   # (year, div, batch) → day → slot → bool
        self.faculty_names  = {}
        self.labs_list      = []
        self.subject_map    = {}   # short_name → subject doc

    # ── Data loading ─────────────────────────────────────────────────────────

    def _load_faculty_names(self):
        for f in faculty_collection.find({}, {'_id': 1, 'name': 1, 'short_name': 1}):
            self.faculty_names[str(f['_id'])] = f.get('short_name') or f.get('name', '')
        logger.info(f"✓ Loaded {len(self.faculty_names)} faculty")

    def _load_subject_map(self):
        doc = subjects_collection.find_one({})
        if not doc:
            return
        for yr in ['sy', 'ty', 'be']:
            for subj in doc.get(yr, []):
                sname = subj.get('short_name', '')
                if sname:
                    self.subject_map[sname] = subj
        logger.info(f"✓ Loaded {len(self.subject_map)} subjects")

    def _load_labs(self):
        labs = list(labs_collection.find({}))
        self.labs_list = [lab['name'] for lab in labs if lab.get('name')]
        for lab_name in self.labs_list:
            self.lab_schedule[lab_name] = {
                day: {slot: [] for slot in ALL_SLOTS}
                for day in DAYS
            }
        logger.info(f"✓ Loaded {len(self.labs_list)} labs")

    def _ensure_batch(self, year, division, batch):
        key = (year, division, batch)
        if key not in self.batch_occupied:
            self.batch_occupied[key] = {
                day: {slot: False for slot in ALL_SLOTS}
                for day in DAYS
            }

    # ── Assignment preparation ────────────────────────────────────────────────

    def prepare_assignments(self) -> dict:
        assignments: dict = {}
        try:
            self._load_faculty_names()
            self._load_subject_map()
            workloads = list(workload_collection.find({}))
            logger.info(f"Reading {len(workloads)} workload entries…")

            for w in workloads:
                year         = (w.get('year') or '').strip().upper()
                division     = w.get('division', 'A')
                batches_raw  = w.get('batches', [1])
                subject      = w.get('subject', '')
                subject_full = w.get('subject_full', subject)
                faculty_id   = str(w.get('faculty_id', '')) if w.get('faculty_id') else ''
                faculty_name = self.faculty_names.get(faculty_id, faculty_id)

                subj_doc       = self.subject_map.get(subject, {})
                practical_hrs  = int(subj_doc.get('practical_duration',
                                     w.get('practical_hrs', 2)))
                practical_type = subj_doc.get('practical_type', 'Common Lab')
                required_lab   = (subj_doc.get('required_labs')
                                  if practical_type == 'Specific Lab' else None)

                for raw_batch in batches_raw:
                    batch = _normalise_batch(raw_batch)
                    self._ensure_batch(year, division, batch)
                    key = (year, division, batch)
                    assignments.setdefault(key, []).append({
                        'subject':       subject,
                        'subject_full':  subject_full,
                        'batch':         batch,
                        'faculty_id':    faculty_id,
                        'faculty':       faculty_name,
                        'year':          year,
                        'division':      division,
                        'practical_hrs': practical_hrs,
                        'required_lab':  required_lab,
                    })

            total = sum(len(v) for v in assignments.values())
            logger.info(f"✓ {len(assignments)} batch-queues, {total} practicals to schedule")
            for k in sorted(assignments):
                logger.info(f"   {k[0]}-{k[1]}-B{k[2]}: "
                            f"{[p['subject'] for p in assignments[k]]}")
            return assignments

        except Exception as e:
            logger.error(f"prepare_assignments error: {e}", exc_info=True)
            return {}

    # ── Constraint helpers ────────────────────────────────────────────────────

    def _faculty_busy(self, faculty: str, day: str, slot: str) -> bool:
        for lab_sched in self.lab_schedule.values():
            for sess in lab_sched.get(day, {}).get(slot, []):
                if sess.get('faculty') == faculty:
                    return True
        return False

    def _batch_slot_free(self, year, division, batch, day, slot) -> bool:
        key = (year, division, batch)
        if key not in self.batch_occupied:
            return True
        return not self.batch_occupied[key][day][slot]

    def _lab_slot_free(self, lab: str, day: str, slot: str) -> bool:
        return len(self.lab_schedule.get(lab, {}).get(day, {}).get(slot, [])) == 0

    def _select_lab(self, practical: dict, day: str, slot: str,
                    used_labs: set) -> str | None:
        hrs       = practical['practical_hrs']
        next_slot = NEXT_SLOT.get(slot) if hrs == 2 else None
        required  = practical.get('required_lab')
        candidates = [required] if required else self.labs_list

        for lab in candidates:
            if lab not in self.lab_schedule:
                continue
            if lab in used_labs:
                continue
            if not self._lab_slot_free(lab, day, slot):
                continue
            if next_slot and not self._lab_slot_free(lab, day, next_slot):
                continue
            return lab
        return None

    def _can_schedule(self, practical: dict, day: str, slot: str,
                      used_faculty: set, used_labs: set) -> bool:
        year, division, batch = practical['year'], practical['division'], practical['batch']
        faculty, hrs          = practical['faculty'], practical['practical_hrs']

        if hrs == 2 and slot not in TWO_HR_START_SLOTS:
            return False
        if faculty in used_faculty:
            return False
        if self._faculty_busy(faculty, day, slot):
            return False
        if not self._batch_slot_free(year, division, batch, day, slot):
            return False
        if hrs == 2:
            if not self._batch_slot_free(year, division, batch, day, NEXT_SLOT[slot]):
                return False
        if self._select_lab(practical, day, slot, used_labs) is None:
            return False
        return True

    # ── Write ─────────────────────────────────────────────────────────────────

    def _write_session(self, practical: dict, day: str, slot: str, lab: str):
        """
        Writes to lab_schedule and batch_occupied ONLY.
        class_timetable_handler reads from master lab timetable (saved at end)
        and is the sole writer for class-level timetables — preventing duplicates.
        """
        year, division, batch = practical['year'], practical['division'], practical['batch']
        hrs = practical['practical_hrs']

        session = {
            'batch':        f"Batch {batch}",
            'subject':      practical['subject'],
            'subject_full': practical['subject_full'],
            'faculty':      practical['faculty'],
            'faculty_id':   practical['faculty_id'] or None,
            'division':     division,
            'class':        year,
        }

        # Lab timetable — primary slot
        self.lab_schedule[lab][day][slot].append(dict(session))
        # Lab timetable — follow-on slot (for 2-hr practicals)
        if hrs == 2 and slot in NEXT_SLOT:
            self.lab_schedule[lab][day][NEXT_SLOT[slot]].append(dict(session))

        # Mark this batch occupied at both slots
        key = (year, division, batch)
        self.batch_occupied[key][day][slot] = True
        if hrs == 2 and slot in NEXT_SLOT:
            self.batch_occupied[key][day][NEXT_SLOT[slot]] = True

        extra = f"+{NEXT_SLOT[slot]}" if hrs == 2 and slot in NEXT_SLOT else ""
        logger.info(f"  ✓ {year}-{division}-B{batch} {practical['subject']} "
                    f"→ {lab} @ {day} {slot}{extra}")

    # ── Main loop ─────────────────────────────────────────────────────────────

    def generate(self) -> dict:
        logger.info("=" * 80)
        logger.info("STARTING PRACTICAL TIMETABLE GENERATION")
        logger.info("=" * 80)

        try:
            self._load_labs()
            assignments = self.prepare_assignments()

            if not assignments:
                return {'success': False, 'error': 'No assignments found'}
            if not self.labs_list:
                return {'success': False, 'error': 'No labs found'}

            scheduled_count = 0
            year_order = {'SY': 0, 'TY': 1, 'BE': 2}

            for pass_num in range(30):
                progress = False

                for day in DAYS:
                    for slot in START_SLOTS:
                        sorted_keys = sorted(
                            [k for k in assignments if assignments[k]],
                            key=lambda k: (year_order.get(k[0], 9), k[1], k[2])
                        )

                        used_faculty : set = set()
                        used_labs    : set = set()

                        for key in sorted_keys:
                            queue = assignments[key]
                            if not queue:
                                continue

                            placed_idx = None
                            for idx, practical in enumerate(queue):
                                if not self._can_schedule(practical, day, slot,
                                                          used_faculty, used_labs):
                                    continue
                                lab = self._select_lab(practical, day, slot, used_labs)
                                if lab is None:
                                    continue

                                used_faculty.add(practical['faculty'])
                                used_labs.add(lab)
                                self._write_session(practical, day, slot, lab)
                                scheduled_count += 1
                                progress = True
                                placed_idx = idx
                                break

                            if placed_idx is not None:
                                queue.pop(placed_idx)

                if not progress:
                    logger.info(f"Stable after pass {pass_num + 1}.")
                    break

                remaining = sum(len(q) for q in assignments.values())
                logger.info(f"Pass {pass_num + 1}: {remaining} remaining")
                if remaining == 0:
                    logger.info(f"✅ All done after {pass_num + 1} pass(es).")
                    break

            # ── Save master lab timetable only ────────────────────────────
            for lab_name, schedule in self.lab_schedule.items():
                master_lab_timetable_collection.replace_one(
                    {'lab_name': lab_name},
                    {'lab_name': lab_name, 'schedule': schedule,
                     'generated_at': datetime.now()},
                    upsert=True
                )
                logger.info(f"✓ Saved lab: {lab_name}")

            leftovers = {
                f"{y}-{d}-B{b}": [p['subject'] for p in q]
                for (y, d, b), q in assignments.items() if q
            }
            if leftovers:
                logger.warning(f"⚠️  Unscheduled: {leftovers}")
            else:
                logger.info("✅ All practicals scheduled!")

            logger.info(f"DONE: {scheduled_count} sessions scheduled")
            return {
                'success':              True,
                'message':              f'Scheduled {scheduled_count} practical sessions',
                'labs_generated':       len(self.labs_list),
                'practicals_scheduled': scheduled_count,
                'leftovers':            leftovers,
            }

        except Exception as e:
            logger.error(f"generate() error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}


def generate():
    return TimetableGenerator().generate()