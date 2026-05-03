# lecture_tt_generator.py

from datetime import datetime
from config import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LG-01 FIX: Round-robin weights per year.
# Pattern: SY, SY, TY, TY, BE — repeating.
# This gives SY and TY 2 turns each before BE gets 1 turn,
# preserving priority while guaranteeing BE is never locked out.
ROUND_ROBIN_CYCLE = ['SY', 'SY', 'TY', 'TY', 'BE']

workload_collection        = db['workload']
faculty_collection         = db['faculty']
subjects_collection        = db['subjects']
class_timetable_collection = db['class_timetable']
constraints_collection     = db['constraints']
settings_collection        = db['settings']


class LectureTimetableGenerator:

    def __init__(self):
        self.class_timetables        = {}   # (year, div) → full timetable doc
        self.subject_map             = {}   # short_name → subject doc
        self._warned_missing_keys    = set()  # LG-02 FIX: suppress repeated warnings
        self.preferred_off           = set()  # (faculty, day, slot) tuples — cached constraints
        self.fixed_time_locked       = set()  # (faculty, day, slot) tuples that have fixed_time constraints
        self.days                    = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        self.morning_slots           = []
        self.afternoon_slots         = []
        self.all_lecture_slots       = []
        self.lunch_slot              = ''

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_settings(self):
        doc = settings_collection.find_one({"type": "department_timings"})
        if not doc:
            # Default values
            self.morning_slots = ['10:15', '11:15', '12:15']
            self.afternoon_slots = ['14:15', '15:15', '16:20', '17:20']
            self.lunch_slot = '13:15'
        else:
            from modules.settings_handler import calculate_slots
            slots = calculate_slots(doc)
            breaks = doc.get('breaks', [])
            lunch_break = next((b for b in breaks if 'lunch' in b.get('name', '').lower()), None)
            if lunch_break:
                self.lunch_slot = lunch_break['start_time']
            else:
                self.lunch_slot = '13:15'  # default
            self.morning_slots = [s for s in slots if s < self.lunch_slot]
            self.afternoon_slots = [s for s in slots if s > self.lunch_slot]
        self.all_lecture_slots = self.morning_slots + self.afternoon_slots
        logger.info(f"✓ Loaded settings: morning {self.morning_slots}, afternoon {self.afternoon_slots}, lunch {self.lunch_slot}")

    def _load_class_timetables(self):
        for tt in class_timetable_collection.find({}):
            # LG-02 FIX: normalise to uppercase so 'sy'/'SY' mismatches are caught
            key = (tt['class'].upper(), tt['division'].upper())
            self.class_timetables[key] = tt
        logger.info(f"✓ Loaded {len(self.class_timetables)} class timetables")

    def _load_subject_map(self):
        doc = subjects_collection.find_one({})
        if not doc:
            logger.warning("No subjects document found!")
            return
        for yr in ['sy', 'ty', 'be']:
            for subj in doc.get(yr, []):
                sname = subj.get('short_name', '')
                if sname:
                    self.subject_map[sname] = subj
        logger.info(f"✓ Loaded {len(self.subject_map)} subjects for lecture lookup")

    def _load_constraints(self):
        """
        LG-CACHE FIX: Load all constraints into memory ONCE at the start,
        never query the DB in the hot loop. This prevents thousands of
        MongoDB queries that cause the 10-second timeout.
        """
        try:
            for c in constraints_collection.find({}):
                fac  = c.get("faculty_name", "")
                day  = c.get("day", "")
                slot = c.get("time_slot", "")
                
                if c.get("type") == "preferred_off":
                    # Faculty should not teach at this day+slot
                    self.preferred_off.add((fac, day, slot))
                    
                elif c.get("type") == "fixed_time":
                    # Faculty is locked to teach at this day+slot (for a specific class+subject)
                    self.fixed_time_locked.add((fac, day, slot))
            
            logger.info(f"✓ Loaded {len(self.preferred_off)} preferred_off constraints")
            logger.info(f"✓ Loaded {len(self.fixed_time_locked)} fixed_time constraints")
        except Exception as e:
            logger.error(f"Error loading constraints: {e}", exc_info=True)

    # ── Assignment preparation ────────────────────────────────────────────────

    def prepare_lecture_assignments(self) -> tuple[dict, list]:
        """
        Returns:
            assignments : {(year, div, subject): [lecture_dict, …]}
            unresolved  : [{'year', 'division', 'subject'}, …]  — LG-03 FIX

        theory_hrs is read from subjects.hrs_per_week_lec (authoritative).
        Falls back to workload.theory_hrs only when subject not found.
        Subjects whose theory_hrs resolves to 0 through all fallbacks are
        collected in `unresolved` and returned to the caller instead of being
        silently dropped.
        """
        assignments: dict = {}
        unresolved:  list = []   # LG-03 FIX

        try:
            faculties = list(faculty_collection.find(
                {}, {'_id': 1, 'name': 1, 'short_name': 1}))
            fid_to_name = {
                str(f['_id']): f.get('short_name') or f.get('name', '')
                for f in faculties
            }

            workloads = list(workload_collection.find({}))
            logger.info(f"Reading {len(workloads)} workload entries…")

            for w in workloads:
                # LG-02 FIX: normalise year and division to uppercase here so
                # they always match the uppercase keys in self.class_timetables
                year         = (w.get('year') or '').strip().upper()
                division     = w.get('division', 'A').strip().upper()
                subject      = w.get('subject', '')
                subject_full = w.get('subject_full', subject)
                faculty_id   = str(w.get('faculty_id', ''))
                faculty_name = fid_to_name.get(faculty_id, faculty_id)

                # ── Authoritative theory hours from subjects collection ────
                subj_doc   = self.subject_map.get(subject, {})
                theory_hrs = int(subj_doc['hrs_per_week_lec']) if 'hrs_per_week_lec' in subj_doc else 0

                # Fallback: try workload fields if subject not in map
                if theory_hrs == 0:
                    for field in ('theory_hrs', 'lectures_per_week', 'lecture_hours',
                                  'theory', 'hours'):
                        val = w.get(field)
                        if isinstance(val, (int, float)) and val > 0:
                            theory_hrs = int(val)
                            logger.warning(
                                f"  Using workload.{field}={theory_hrs} for "
                                f"{year}-{division}-{subject} (not found in subjects)")
                            break

                # LG-03 FIX: collect unresolved instead of silently dropping
                if theory_hrs == 0:
                    logger.warning(
                        f"No theory_hrs for {year}-{division}-{subject}, "
                        f"adding to unresolved_subjects")
                    unresolved.append({
                        'year':     year,
                        'division': division,
                        'subject':  subject,
                        'faculty':  faculty_name,
                    })
                    continue

                key = (year, division, subject)
                # Overwrite with the same faculty if duplicate workload entries exist
                assignments[key] = [
                    {
                        'subject':        subject,
                        'subject_full':   subject_full,
                        'class':          year,
                        'division':       division,
                        'faculty_id':     faculty_id,
                        'faculty':        faculty_name,
                        'hours':          1,
                        'lecture_number': n + 1,
                    }
                    for n in range(theory_hrs)
                ]

            total = sum(len(v) for v in assignments.values())
            logger.info(f"✓ {len(assignments)} subjects, {total} lecture slots to fill")
            for k in sorted(assignments):
                logger.info(f"   {k[0]}-{k[1]}-{k[2]}: {len(assignments[k])} lectures")

            if unresolved:
                skipped_labels = [
                    "{}-{}-{}".format(u['year'], u['division'], u['subject'])
                    for u in unresolved
                ]
                logger.warning(
                    f"⚠️  {len(unresolved)} subject(s) had no resolvable theory_hrs "
                    f"and were skipped: {skipped_labels}"
                )

            return assignments, unresolved

        except Exception as e:
            logger.error(f"prepare_lecture_assignments error: {e}", exc_info=True)
            return {}, []

    # ── Constraint helpers ────────────────────────────────────────────────────

    def _faculty_busy(self, faculty: str, day: str, slot: str) -> bool:
        """
        Global check — faculty cannot be in two classes at once.
        LG-CACHE FIX: Use in-memory constraint sets instead of DB queries.
        """
        for tt in self.class_timetables.values():
            for sess in tt.get('schedule', {}).get(day, {}).get(slot, []):
                if sess.get('faculty') == faculty:
                    return True
        # Check preferred_off constraints (in-memory, no DB query)
        if (faculty, day, slot) in self.preferred_off:
            logger.debug(f"Faculty {faculty} busy at {day} {slot} due to preferred_off constraint")
            return True
        # Check fixed_time constraints
        if (faculty, day, slot) in self.fixed_time_locked:
            logger.debug(f"Faculty {faculty} busy at {day} {slot} due to fixed_time constraint")
            return True
        return False

    def _slot_free(self, year: str, division: str, day: str, slot: str) -> bool:
        # LG-02 FIX: normalise lookup key to uppercase; log a warning once if missing
        key = (year.upper(), division.upper())
        if key not in self.class_timetables:
            if key not in self._warned_missing_keys:
                logger.warning(
                    f"No class timetable found for {year}-{division}. "
                    f"All lecture slots will appear busy for this class. "
                    f"Check year/division spelling and case in workload data."
                )
                self._warned_missing_keys.add(key)
            return False
        return len(
            self.class_timetables[key]['schedule'].get(day, {}).get(slot, [])
        ) == 0

    _ADJACENT = {
        '10:15': ['11:15'],
        '11:15': ['10:15', '12:15'],
        '12:15': ['11:15'],
        '14:15': ['15:15'],
        '15:15': ['14:15', '16:20'],
        '16:20': ['15:15', '17:20'],
        '17:20': ['16:20'],
    }

    def _consecutive_ok(self, year: str, division: str, day: str,
                    slot: str, subject: str, faculty: str) -> bool:
        """
        Return True if placing this lecture is acceptable. Blocks:
          1. Same subject already anywhere on this day for this class
             (enforces one lecture per subject per day — the spread constraint).
          2. Same subject in an immediately adjacent slot for this class
             (redundant given rule 1, kept as safety net).
          3. Same faculty in an adjacent slot within this class
             (faculty gets a break between sessions in the same class).

        Cross-class faculty adjacency is intentionally NOT blocked — teaching
        different classes in adjacent slots is normal and was the root cause
        of VM's lecture starvation when it was blocked.
        """
        tt = self.class_timetables.get((year.upper(), division.upper()))
        if not tt:
            return True

        day_schedule = tt['schedule'].get(day, {})

        # Rule 1 — same subject must not appear anywhere else on this day
        for s, entries in day_schedule.items():
            if s == slot:
                continue   # skip the target slot itself
            for sess in entries:
                if sess.get('subject') == subject and sess.get('type') == 'lecture':
                    return False  # subject already has a lecture today

        # Rule 2 & 3 — adjacent slot checks (faculty break within class)
        for adj in self._ADJACENT.get(slot, []):
            for sess in day_schedule.get(adj, []):
                if sess.get('faculty') == faculty:
                    return False  # same faculty back-to-back within this class

        return True

    # ── Write helper ──────────────────────────────────────────────────────────

    def _place_lecture(self, year: str, division: str, day: str,
                       slot: str, lecture: dict):
        key = (year.upper(), division.upper())
        tt  = self.class_timetables[key]
        schedule = tt.setdefault('schedule', {})
        schedule.setdefault(day, {}).setdefault(slot, []).append({
            'subject':      lecture['subject'],
            'subject_full': lecture['subject_full'],
            'faculty':      lecture['faculty'],
            'faculty_id':   lecture['faculty_id'],
            'hours':        1,
            'type':         'lecture',
        })
        logger.debug(f"  ✓ {year}-{division} {lecture['subject']} "
                     f"L#{lecture['lecture_number']} → {day} {slot}")

    # ── Round-robin key ordering (LG-01 FIX) ─────────────────────────────────

    @staticmethod
    def _build_round_robin_order(pending_keys: list) -> list:
        """
        Returns pending_keys reordered using the ROUND_ROBIN_CYCLE pattern:
        SY, SY, TY, TY, BE  (repeating).

        Mirrors the identical logic in TimetableGenerator so both schedulers
        use the same fairness policy.
        """
        by_year: dict = {}
        for k in pending_keys:
            yr = k[0]
            by_year.setdefault(yr, []).append(k)
        for yr in by_year:
            by_year[yr].sort(key=lambda k: (k[1], k[2]))  # division, subject alphabetically

        pointers: dict = {yr: 0 for yr in by_year}

        ordered = []
        total = len(pending_keys)
        cycle_pos = 0

        while len(ordered) < total:
            found = False
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
                found = True
                break

            if not found:
                # Remaining keys belong to a year not represented in the cycle
                # (e.g. only BE keys left when cycle has no more BE slots before
                # exhausting SY/TY turns). Append them all now.
                cycle_pos += 1
                for yr, keys in by_year.items():
                    while pointers[yr] < len(keys):
                        ordered.append(keys[pointers[yr]])
                        pointers[yr] += 1
                break

        return ordered

    # ── Apply fixed_time constraints (Phase 0) ────────────────────────────────

    def _apply_fixed_time_constraints(self, assignments: dict) -> tuple[int, list]:
        """
        Apply fixed_time constraints BEFORE the main scheduling loop.
        This is Phase 0 of the lecture generation.

        Returns:
            (num_placed, unplaced_constraints)
            where unplaced_constraints are constraints that could not be placed.
        """
        constraints = list(constraints_collection.find({'type': 'fixed_time'}))
        placed_count = 0
        unplaced = []

        for constraint in constraints:
            try:
                # LG-05 FIX: accept both "class" and "year" fields for backward compatibility
                # Existing constraints may have "year", new ones store as "class"
                year         = (constraint.get('class') or constraint.get('year') or '').strip().upper()
                division     = constraint.get('division', 'A').strip().upper()
                subject      = constraint.get('subject', '')
                day          = constraint.get('day', '')
                slot         = constraint.get('time_slot', '')
                faculty_name = constraint.get('faculty_name', '')

                # Validate required fields
                if not all([year, division, subject, day, slot, faculty_name]):
                    logger.warning(
                        f"Incomplete fixed_time constraint: {constraint}. Skipping."
                    )
                    unplaced.append(constraint)
                    continue

                # Check if slot is free
                if not self._slot_free(year, division, day, slot):
                    logger.warning(
                        f"Cannot place fixed_time constraint {year}-{division} "
                        f"{subject} @ {day} {slot}: slot occupied"
                    )
                    unplaced.append(constraint)
                    continue

                # Find the matching assignment and place it
                key = (year, division, subject)
                if key not in assignments or not assignments[key]:
                    logger.warning(
                        f"No assignment found for fixed_time constraint: "
                        f"{year}-{division}-{subject}. Check if workload exists."
                    )
                    unplaced.append(constraint)
                    continue

                # Find the lecture from this faculty within the pending list
                found = False
                for idx, lecture in enumerate(assignments[key]):
                    if lecture['faculty'] == faculty_name:
                        # Place it
                        self._place_lecture(year, division, day, slot, lecture)
                        assignments[key].pop(idx)
                        placed_count += 1
                        found = True
                        logger.info(
                            f"✓ Fixed_time constraint placed: {year}-{division} "
                            f"{subject} ({faculty_name}) → {day} {slot}"
                        )
                        break

                if not found:
                    logger.warning(
                        f"No lecture found for fixed_time constraint faculty "
                        f"{faculty_name} in {year}-{division}-{subject}"
                    )
                    unplaced.append(constraint)

            except Exception as e:
                logger.error(
                    f"Error applying fixed_time constraint {constraint}: {e}"
                )
                unplaced.append(constraint)

        return placed_count, unplaced

    # ── Main scheduling loop ──────────────────────────────────────────────────

    def generate(self) -> dict:
        logger.info("=" * 80)
        logger.info("STARTING LECTURE TIMETABLE GENERATION")
        logger.info("=" * 80)

        try:
            self._load_class_timetables()
            self._load_subject_map()
            self._load_constraints()  # ← LG-CACHE FIX: Load constraints once at start
            self._load_settings()  # Load dynamic slots

            if not self.class_timetables:
                return {'success': False, 'error': 'No class timetables found'}

            # LG-03 FIX: unpack the tuple — assignments + unresolved subjects
            assignments, unresolved_subjects = self.prepare_lecture_assignments()

            if not assignments:
                return {
                    'success':             False,
                    'message':             'No lecture assignments found',
                    'lectures_scheduled':  0,
                    'unresolved_subjects': unresolved_subjects,
                }

            scheduled_count = 0

            # ── Phase 0: Apply fixed_time constraints ────────────────────────
            fixed_time_placed, fixed_time_unplaced = self._apply_fixed_time_constraints(assignments)
            scheduled_count += fixed_time_placed
            if fixed_time_unplaced:
                logger.warning(
                    f"⚠️  {len(fixed_time_unplaced)} fixed_time constraint(s) could not be placed"
                )

            for pass_num in range(30):
                progress = False

                for day in self.days:
                    for slot in self.all_lecture_slots:
                        if slot == self.lunch_slot:
                            continue

                        # LG-01 FIX: use round-robin ordering instead of fixed year_order
                        pending_keys = [(y, d, s) for (y, d, s) in assignments
                                        if assignments[(y, d, s)]]
                        ordered_keys = self._build_round_robin_order(pending_keys)

                        for year, division, subject in ordered_keys:
                            pending = assignments[(year, division, subject)]
                            if not pending:
                                continue
                            lecture = pending[0]

                            # LG-02 FIX: _slot_free normalises key internally
                            if not self._slot_free(year, division, day, slot):
                                continue
                            if self._faculty_busy(lecture['faculty'], day, slot):
                                continue
                            # LG-04 FIX: pass faculty to _consecutive_ok
                            if not self._consecutive_ok(
                                    year, division, day, slot,
                                    subject, lecture['faculty']):
                                continue

                            self._place_lecture(year, division, day, slot, lecture)
                            pending.pop(0)
                            scheduled_count += 1
                            progress = True

                if not progress:
                    logger.info(f"Stable after {pass_num + 1} pass(es).")
                    break

                if all(len(q) == 0 for q in assignments.values()):
                    logger.info(f"All lectures placed after {pass_num + 1} pass(es).")
                    break

            # ── Save ──────────────────────────────────────────────────────
            # Use ALL_LECTURE_SLOTS + LUNCH_SLOT so the scaffold always matches
            # whatever slots are defined at the top of this file.
            # Previously this was a hardcoded list that didn't include 17:20.
            save_slots = sorted(set(self.all_lecture_slots + [self.lunch_slot]))
            for (year, division), tt in self.class_timetables.items():
                for day in self.days:
                    for sl in save_slots:
                        tt['schedule'].setdefault(day, {}).setdefault(sl, [])
                tt['generated_at'] = datetime.now()
                class_timetable_collection.replace_one(
                    {'class': year, 'division': division}, tt, upsert=True
                )
                logger.info(f"✓ Saved {year}-{division}")

            # ── Leftovers ─────────────────────────────────────────────────
            leftovers = {
                f"{y}-{d}-{s}": [f"L#{l['lecture_number']}" for l in q]
                for (y, d, s), q in assignments.items() if q
            }
            if leftovers:
                logger.warning(f"⚠️  Unscheduled lectures: {leftovers}")
            else:
                logger.info("✅ All lectures successfully scheduled!")

            if unresolved_subjects:
                logger.warning(
                    f"⚠️  {len(unresolved_subjects)} subject(s) had no theory_hrs "
                    f"and were excluded from scheduling entirely."
                )

            logger.info(f"DONE: {scheduled_count} lectures scheduled")

            return {
                'success':             True,
                'message':             f'Scheduled {scheduled_count} lectures',
                'lectures_scheduled':  scheduled_count,
                'fixed_time_placed':   fixed_time_placed,
                'fixed_time_unplaced': len(fixed_time_unplaced),
                'leftovers':           leftovers,
                'unresolved_subjects': unresolved_subjects,
            }

        except Exception as e:
            logger.error(f"generate() error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}


def generate():
    return LectureTimetableGenerator().generate()
