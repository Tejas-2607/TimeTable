# lecture_tt_generator.py

from datetime import datetime
from config import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DAYS              = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
MORNING_SLOTS     = ['10:15', '11:15', '12:15']
AFTERNOON_SLOTS   = ['14:15', '15:15', '16:20', '17:20']
ALL_LECTURE_SLOTS = MORNING_SLOTS + AFTERNOON_SLOTS
LUNCH_SLOT        = '13:15'


ROUND_ROBIN_CYCLE = ['SY', 'SY', 'TY', 'TY', 'BE']

workload_collection        = db['workload']
faculty_collection         = db['faculty']
subjects_collection        = db['subjects']
class_timetable_collection = db['class_timetable']


class LectureTimetableGenerator:

    def __init__(self):
        self.class_timetables        = {}   # (year, div) → full timetable doc
        self.subject_map             = {}   # short_name → subject doc
        self._warned_missing_keys    = set()  # LG-02 FIX: suppress repeated warnings

    # ── Data loading ──────────────────────────────────────────────────────────

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
        """Global check — faculty cannot be in two classes at once."""
        for tt in self.class_timetables.values():
            for sess in tt.get('schedule', {}).get(day, {}).get(slot, []):
                if sess.get('faculty') == faculty:
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
        Return True if placing this lecture at (day, slot) does not create an
        undesirable back-to-back situation.

        Rules enforced:
          1. Same subject must not appear in an adjacent slot for this class
             (no two DS lectures at 10:15 and 11:15 for the same class).
          2. Same faculty must not appear in an adjacent slot FOR THIS SAME CLASS
             (the faculty gets no break within the class).

        What is intentionally NOT blocked:
          - Faculty teaching a different class in an adjacent slot. This is normal
            scheduling (e.g. faculty teaches TY-A at 10:15 and SY-B at 11:15).
            Blocking this was the root cause of VM's lectures being completely
            unschedulable because VM's practicals occupied adjacent slots in
            multiple classes simultaneously.
        """
        tt = self.class_timetables.get((year.upper(), division.upper()))
        if not tt:
            return True
        day_sched = tt['schedule'].get(day, {})
        for adj in self._ADJACENT.get(slot, []):
            for sess in day_sched.get(adj, []):
                if sess.get('subject') == subject:
                    return False   # same subject back-to-back for this class
                if sess.get('faculty') == faculty:
                    return False   # same faculty back-to-back within this class
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

    # ── Main scheduling loop ──────────────────────────────────────────────────

    def generate(self) -> dict:
        logger.info("=" * 80)
        logger.info("STARTING LECTURE TIMETABLE GENERATION")
        logger.info("=" * 80)

        try:
            self._load_class_timetables()
            self._load_subject_map()

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

            for pass_num in range(30):
                progress = False

                for day in DAYS:
                    for slot in ALL_LECTURE_SLOTS:
                        if slot == LUNCH_SLOT:
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
            save_slots = sorted(set(ALL_LECTURE_SLOTS + [LUNCH_SLOT]))
            for (year, division), tt in self.class_timetables.items():
                for day in DAYS:
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
                'leftovers':           leftovers,
                # LG-03 FIX: expose unresolved subjects so the API caller can
                # show them in the UI rather than leaving the user confused
                'unresolved_subjects': unresolved_subjects,
            }

        except Exception as e:
            logger.error(f"generate() error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}


def generate():
    return LectureTimetableGenerator().generate()