# lecture_tt_generator.py
"""
Fills class timetables with lectures after practicals have been placed.

BUG FIXED — over-scheduled lectures for WD and AJP:
Previously theory_hrs was read from the workload collection, which stores the
faculty's total assignment hours (including practical hours together).
The authoritative value for lectures per week is hrs_per_week_lec in the
subjects collection. workload.theory_hrs is now only used as a fallback
when the subject is not found in the subjects collection.

All other bugs remain fixed from the previous version:
1. Afternoon phase was gated on any_pending checked once — fixed.
2. One subject exhausted all slots for all classes — fixed (round-robin).
3. No retry for blocked lectures — fixed (outer retry loop).
4. 13:15 lunch slot implicit skip — fixed (explicit).
5. schedule dict KeyError on edge cases — fixed.
"""

from datetime import datetime
from config import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DAYS              = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
MORNING_SLOTS     = ['10:15', '11:15', '12:15']
AFTERNOON_SLOTS   = ['14:15', '15:15', '16:20']
ALL_LECTURE_SLOTS = MORNING_SLOTS + AFTERNOON_SLOTS
LUNCH_SLOT        = '13:15'

workload_collection        = db['workload']
faculty_collection         = db['faculty']
subjects_collection        = db['subjects']
class_timetable_collection = db['class_timetable']


class LectureTimetableGenerator:

    def __init__(self):
        self.class_timetables = {}   # (year, div) → full timetable doc
        self.subject_map      = {}   # short_name → subject doc

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_class_timetables(self):
        for tt in class_timetable_collection.find({}):
            key = (tt['class'], tt['division'])
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

    def prepare_lecture_assignments(self) -> dict:
        """
        Returns {(year, div, subject): [lecture_dict, …]} with one entry per
        required lecture-hour per week.

        theory_hrs is read from subjects.hrs_per_week_lec (authoritative).
        Falls back to workload.theory_hrs only when subject not found.
        """
        assignments = {}
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
                year         = (w.get('year') or '').strip().upper()
                division     = w.get('division', 'A')
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

                if theory_hrs == 0:
                    logger.warning(
                        f"No theory_hrs for {year}-{division}-{subject}, skipping")
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
            return assignments

        except Exception as e:
            logger.error(f"prepare_lecture_assignments error: {e}", exc_info=True)
            return {}

    # ── Constraint helpers ────────────────────────────────────────────────────

    def _faculty_busy(self, faculty: str, day: str, slot: str) -> bool:
        """Global check — faculty cannot be in two classes at once."""
        for tt in self.class_timetables.values():
            for sess in tt.get('schedule', {}).get(day, {}).get(slot, []):
                if sess.get('faculty') == faculty:
                    return True
        return False

    def _slot_free(self, year: str, division: str, day: str, slot: str) -> bool:
        key = (year, division)
        if key not in self.class_timetables:
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
        '16:20': ['15:15'],
    }

    def _consecutive_ok(self, year: str, division: str, day: str,
                        slot: str, subject: str) -> bool:
        """Return True if placing subject at slot doesn't create a back-to-back."""
        tt = self.class_timetables.get((year, division))
        if not tt:
            return True
        day_sched = tt['schedule'].get(day, {})
        for adj in self._ADJACENT.get(slot, []):
            for sess in day_sched.get(adj, []):
                if sess.get('subject') == subject:
                    return False
        return True

    # ── Write helper ──────────────────────────────────────────────────────────

    def _place_lecture(self, year: str, division: str, day: str,
                       slot: str, lecture: dict):
        key = (year, division)
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

            assignments = self.prepare_lecture_assignments()
            if not assignments:
                return {'success': False, 'message': 'No lecture assignments found',
                        'lectures_scheduled': 0}

            year_order      = {'SY': 0, 'TY': 1, 'BE': 2}
            scheduled_count = 0

            for pass_num in range(30):
                progress = False

                for day in DAYS:
                    for slot in ALL_LECTURE_SLOTS:
                        if slot == LUNCH_SLOT:
                            continue

                        sorted_keys = sorted(
                            [(y, d, s) for (y, d, s) in assignments
                             if assignments[(y, d, s)]],
                            key=lambda k: (year_order.get(k[0], 9), k[1], k[2])
                        )

                        for year, division, subject in sorted_keys:
                            pending = assignments[(year, division, subject)]
                            if not pending:
                                continue
                            lecture = pending[0]

                            if not self._slot_free(year, division, day, slot):
                                continue
                            if self._faculty_busy(lecture['faculty'], day, slot):
                                continue
                            if not self._consecutive_ok(year, division, day, slot, subject):
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
            all_slots = ['10:15', '11:15', '12:15', '13:15',
                         '14:15', '15:15', '16:20']
            for (year, division), tt in self.class_timetables.items():
                for day in DAYS:
                    for sl in all_slots:
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

            logger.info(f"DONE: {scheduled_count} lectures scheduled")

            return {
                'success':            True,
                'message':            f'Scheduled {scheduled_count} lectures',
                'lectures_scheduled': scheduled_count,
                'leftovers':          leftovers,
            }

        except Exception as e:
            logger.error(f"generate() error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}


def generate():
    return LectureTimetableGenerator().generate()