# timetable_generator.py

from datetime import datetime
from config import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DAYS               = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
ALL_SLOTS          = ['10:15', '11:15', '12:15', '13:15', '14:15', '15:15', '16:20']
START_SLOTS        = ['11:15', '14:15', '16:20']
NEXT_SLOT          = {'11:15': '12:15', '14:15': '15:15'}
TWO_HR_START_SLOTS = ['11:15', '14:15']

# TG-02 FIX: follow-on slot → the start slot that "covers" it
# e.g. a 2-hr session starting at 11:15 occupies 12:15 as well.
# When checking if faculty is busy at 12:15, we must also look at 11:15.
COVERS = {'12:15': '11:15', '15:15': '14:15'}

# TG-01 FIX: Round-robin weights per year.
# Pattern: SY, SY, TY, TY, BE — repeating.
# This gives SY and TY 2 turns each before BE gets 1 turn,
# preserving priority while guaranteeing BE is never locked out.
ROUND_ROBIN_CYCLE = ['SY', 'SY', 'TY', 'TY', 'BE']

subjects_collection             = db['subjects']
faculty_collection              = db['faculty']
workload_collection             = db['workload']
labs_collection                 = db['labs']
master_lab_timetable_collection = db['master_lab_timetable']


# TG-03 FIX: return None on parse failure instead of silently returning 1
def _normalise_batch(raw) -> int | None:
    if isinstance(raw, int):
        return raw
    s = str(raw).replace('Batch', '').strip()
    try:
        return int(s)
    except ValueError:
        logger.warning(f"Cannot normalise batch value: {raw!r} — skipping this batch entry")
        return None


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

            # TG-04 FIX: track seen (year, division, batch, subject) combos
            # to skip duplicate workload documents
            seen_combos: set = set()

            for w in workloads:
                year         = (w.get('year') or '').strip().upper()
                division     = w.get('division', 'A')
                batches_raw  = w.get('batches', [1])
                subject      = w.get('subject', '')
                subject_full = w.get('subject_full', subject)
                faculty_id   = str(w.get('faculty_id', '')) if w.get('faculty_id') else ''
                faculty_name = self.faculty_names.get(faculty_id, faculty_id)

                subj_doc       = self.subject_map.get(subject, {})

                # TG-05 FIX: warn when subject not found in subject_map
                if not subj_doc:
                    logger.warning(
                        f"Subject '{subject}' not found in subject_map for "
                        f"{year}-{division}. Defaulting practical_hrs=2."
                    )

                practical_hrs  = int(subj_doc.get('practical_duration',
                                     w.get('practical_hrs', 2)))
                practical_type = subj_doc.get('practical_type', 'Common Lab')
                required_lab   = (subj_doc.get('required_labs')
                                  if practical_type == 'Specific Lab' else None)

                for raw_batch in batches_raw:
                    # TG-03 FIX: skip batches that cannot be normalised
                    batch = _normalise_batch(raw_batch)
                    if batch is None:
                        continue

                    # TG-04 FIX: skip duplicate (year, division, batch, subject) combos
                    combo = (year, division, batch, subject)
                    if combo in seen_combos:
                        logger.warning(
                            f"Duplicate workload entry skipped: {combo}"
                        )
                        continue
                    seen_combos.add(combo)

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
        # TG-02 FIX: also check the start slot that covers this follow-on slot.
        # e.g. if slot='12:15', also scan '11:15' because a 2-hr session that
        # started at 11:15 occupies 12:15 as well — checking only 12:15 misses it.
        slots_to_check = {slot}
        if slot in COVERS:
            slots_to_check.add(COVERS[slot])

        for lab_sched in self.lab_schedule.values():
            for s in slots_to_check:
                for sess in lab_sched.get(day, {}).get(s, []):
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
        if self._faculty_busy(faculty, day, slot):   # TG-02 fix applied inside here
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

    # ── Round-robin key ordering (TG-01 FIX) ──────────────────────────────────

    @staticmethod
    def _build_round_robin_order(pending_keys: list) -> list:
        """
        Returns pending_keys reordered using the ROUND_ROBIN_CYCLE pattern:
        SY, SY, TY, TY, BE  (repeating).

        How it works:
        - Group keys by year.
        - Walk through the cycle pattern. On each cycle step, take the next
          available key from that year's group (round-robin within the year too).
        - Repeat until all keys are consumed.

        This guarantees BE is visited once every 5 turns, SY and TY twice each,
        so BE can never be locked out across the full pass even when slots are scarce.
        Within each year group, keys are sorted alphabetically so ordering is stable.
        """
        # Group by year, sorted within each group for stability
        by_year: dict = {}
        for k in pending_keys:
            yr = k[0]
            by_year.setdefault(yr, []).append(k)
        for yr in by_year:
            by_year[yr].sort(key=lambda k: (k[1], k[2]))  # sort by division, batch

        # Pointers for round-robin within each year group
        pointers: dict = {yr: 0 for yr in by_year}

        ordered = []
        total = len(pending_keys)
        cycle_pos = 0

        while len(ordered) < total:
            # Walk the cycle until we find a year that still has keys left
            found_in_this_cycle = False
            for _ in range(len(ROUND_ROBIN_CYCLE)):
                yr = ROUND_ROBIN_CYCLE[cycle_pos % len(ROUND_ROBIN_CYCLE)]
                cycle_pos += 1
                if yr not in by_year:
                    continue
                idx = pointers[yr]
                if idx >= len(by_year[yr]):
                    continue
                ordered.append(by_year[yr][idx])
                pointers[yr] += 1
                found_in_this_cycle = True
                break

            if not found_in_this_cycle:
                # Safety: no year matched this cycle step — advance and retry.
                # This handles edge cases like only BE keys remaining.
                cycle_pos += 1
                # Collect whatever is left in any group
                for yr, keys in by_year.items():
                    while pointers[yr] < len(keys):
                        ordered.append(keys[pointers[yr]])
                        pointers[yr] += 1
                break

        return ordered

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

            for pass_num in range(30):
                progress = False

                for day in DAYS:
                    for slot in START_SLOTS:

                        # TG-01 FIX: build round-robin ordered list instead of
                        # fixed year_order sort.  Only include keys that still
                        # have pending practicals.
                        pending_keys = [k for k in assignments if assignments[k]]
                        ordered_keys = self._build_round_robin_order(pending_keys)

                        used_faculty: set = set()
                        used_labs:    set = set()

                        for key in ordered_keys:
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