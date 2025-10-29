# timetable_generator.py
from datetime import datetime
from config import db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
SLOTS = ['11:15', '14:15', '16:20']   # time slots
MIN_PRACTICAL_HOURS = 2               # threshold to treat subject as practical

# Database collections
subjects_collection = db['subjects']
faculty_collection = db['faculty']
labs_collection = db['labs']
class_structure_collection = db['class_structure']
workload_collection = db['workload']
master_lab_timetable_collection = db['master_lab_timetable']


class PracticalTimetableGenerator:
    """
    Single-year generator. It produces a lab-wise timetable skeleton for one year
    by listing (from workload) what batch-subject pairs need practical sessions.
    NOTE: This implementation only prepares per-year assignments (not the final merge).
    """
    def __init__(self, year, semester):
        self.year = year  # 'SY'|'TY'|'BE'
        self.semester = semester
        self.timetable = {'labs': {}}
        self.assignments = []  # flat list of assignments for this year

    def generate(self):
        """
        Load required workloads for this year and return a skeleton timetable object:
        { 'labs': { lab_name: { day: { slot: [] }}}}
        This function DOES NOT merge across years — that's done by the unified generate() below.
        """
        try:
            logger.info(f"Generating timetable for {self.year} Sem {self.semester}")

            # load practical subjects (we use workload entries as source of sessions)
            assignments = self._prepare_batch_assignments_from_workload()
            if not assignments:
                logger.warning(f"No batch assignments created for {self.year}")
                return None

            # Initialize labs skeleton to report (but we don't populate here - merging will place items)
            labs = self._get_available_labs()
            if not labs:
                logger.error("No labs available in DB")
                return None

            for lab in labs:
                lab_name = lab.get('name', 'Unknown Lab')
                self.timetable['labs'][lab_name] = {day: {slot: [] for slot in SLOTS} for day in DAYS}

            # Provide the assignments list back (the unified generator will place them)
            # We'll return the assignments in the same shape as earlier timetables: labs -> (we keep empty schedule but we attach assignments list under '_assignments' for merging)
            self.timetable['_assignments'] = assignments
            logger.info(f"Prepared {len(assignments)} assignments for {self.year}")
            return self.timetable

        except Exception as e:
            logger.error(f"Error generating year timetable: {str(e)}", exc_info=True)
            return None

    def _get_available_labs(self):
        try:
            return list(labs_collection.find({}, {'_id': 0, 'name': 1}))
        except Exception as e:
            logger.error(f"Error loading labs: {str(e)}")
            return []

    def _prepare_batch_assignments_from_workload(self):
        """
        Build a list of assignments from workload entries for this year.

        Each assignment is a dict:
        {
          'subject': 'DS', 'subject_full': 'Data Structures',
          'class': 'SY', 'division': 'A', 'batch': 1,
          'faculty_id': '69025...', 'faculty_name': 'AMP'
        }

        We use the workload_collection which contains faculty_id, year, division, batches, subject_full, ...
        """
        try:
            assignments = []
            workloads = list(workload_collection.find({}))
            # map faculty id -> name for readability
            faculties = list(faculty_collection.find({}, {'_id': 1, 'name': 1}))
            faculty_id_to_name = {str(f['_id']): f['name'] for f in faculties}

            for w in workloads:
                year = (w.get('year') or '').strip().lower()
                if not year:
                    continue
                if year != self.year.lower():
                    continue

                faculty_id = str(w.get('faculty_id', ''))
                faculty_name = faculty_id_to_name.get(faculty_id, faculty_id)

                division = w.get('division', 'A')
                batches = w.get('batches', []) or []
                subject = w.get('subject') or w.get('short_name') or ''
                subject_full = w.get('subject_full') or w.get('subject_name') or subject

                # Each workload entry represents practical sessions for the batches listed.
                # We'll create one assignment per (batch) — treating practical as single slot/session per week.
                # If workloads ever specify multiple practical hours per week, we could expand to multiple assignments.
                for batch in batches:
                    assignments.append({
                        'subject': subject,
                        'subject_full': subject_full,
                        'class': self.year,
                        'division': division,
                        'batch': batch,
                        'faculty_id': faculty_id,
                        'faculty': faculty_name
                    })

            return assignments

        except Exception as e:
            logger.error(f"Error preparing assignments from workload: {str(e)}", exc_info=True)
            return []


# ---------- UNIFIED GENERATOR FUNCTION ----------
def generate(data=None):
    """
    Unified lab-wise timetable generator that:
      - pulls per-year assignments from PracticalTimetableGenerator
      - fills the lab-wise grid (labs x days x slots)
      - enforces:
          * at most one assignment per lab/day/slot
          * a faculty cannot teach two places at the same day/slot
          * at most one practical per division per day
      - best-effort: skip conflicting sessions rather than failing the whole run
      - saves final lab-wise timetables into master_lab_timetable collection
    """
    try:
        # clear existing master timetable
        master_lab_timetable_collection.delete_many({})

        years = ['SY', 'TY', 'BE']

        # fetch available labs and create skeleton
        labs = list(labs_collection.find({}, {'_id': 0, 'name': 1}))
        if not labs:
            logger.error("No labs found in DB. Aborting generation.")
            return None
        lab_names = [l.get('name', 'Unknown Lab') for l in labs]

        # initialize merged timetable skeleton
        merged_timetable = {'labs': {}}
        for lab_name in lab_names:
            merged_timetable['labs'][lab_name] = {day: {slot: [] for slot in SLOTS} for day in DAYS}

        # helper checks
        def faculty_busy(faculty_name, day, slot):
            """Return True if faculty is scheduled at any lab at the given day/slot."""
            for L in merged_timetable['labs'].values():
                for sess in L[day][slot]:
                    if sess.get('faculty') == faculty_name:
                        return True
            return False

        def division_has_practical(division, year, day):
            """Return True if division (e.g., 'A' for year 'SY') already has a practical on that day."""
            for L in merged_timetable['labs'].values():
                for slot in SLOTS:
                    for sess in L[day][slot]:
                        if sess.get('division') == division and sess.get('class') == year:
                            return True
            return False

        def find_free_lab(day, slot):
            """Return a lab name which is free at day/slot or None."""
            for lab_name in lab_names:
                if len(merged_timetable['labs'][lab_name][day][slot]) == 0:
                    return lab_name
            return None

        # Gather all assignments by year (using per-year generator)
        all_year_assignments = {}  # year -> list of assignments
        for year in years:
            generator = PracticalTimetableGenerator(year, '1')
            y_timetable = generator.generate()
            if not y_timetable:
                logger.warning(f"No assignments produced for year {year}")
                all_year_assignments[year] = []
                continue
            assignments = y_timetable.get('_assignments', [])
            all_year_assignments[year] = assignments

        # Strategy: iterate days and slots (in week order) and attempt to schedule assignments
        # For fairness, we iterate years in order BE, TY, SY? User didn't decide; we'll keep BE->TY->SY priority.
        priority_years = ['BE', 'TY', 'SY']

        # We will attempt to schedule until no more assignments can be placed or all lists empty.
        any_placed = True
        # We'll run a bounded number of passes to avoid infinite loops
        max_passes = len(DAYS) * len(SLOTS) * 3  # heuristic upper bound
        pass_count = 0

        # Convert assignment lists into queues per year
        assignment_queues = {y: list(all_year_assignments.get(y, [])) for y in years}

        # Greedy fill: for each day, slot, for each year in priority, try to place at most one session per division
        for day in DAYS:
            for slot in SLOTS:
                # For each year in priority, try to schedule assignments
                for year in priority_years:
                    queue = assignment_queues.get(year, [])
                    if not queue:
                        continue

                    # We'll attempt to place assignments for this year at (day,slot) while respecting division-per-day rule.
                    # We iterate over a copy because we may pop from original.
                    i = 0
                    while i < len(queue):
                        assignment = queue[i]
                        division = assignment.get('division')
                        faculty = assignment.get('faculty')

                        # If division already has practical this day -> skip scheduling this assignment into this day
                        if division_has_practical(division, year, day):
                            # move to next assignment (this one can be attempted for another day/slot later)
                            i += 1
                            continue

                        # If faculty busy at this day/slot -> skip this assignment for this slot
                        if faculty_busy(faculty, day, slot):
                            i += 1
                            continue

                        # find any free lab for this slot
                        free_lab = find_free_lab(day, slot)
                        if not free_lab:
                            # no free labs at this day/slot; cannot place more for any year -> break to next slot
                            break

                        # place the assignment
                        sess = {
                            'batch': assignment.get('batch'),
                            'class': assignment.get('class'),
                            'division': division,
                            'faculty': faculty,
                            'faculty_id': assignment.get('faculty_id'),
                            'subject': assignment.get('subject'),
                            'subject_full': assignment.get('subject_full')
                        }
                        merged_timetable['labs'][free_lab][day][slot].append(sess)
                        logger.info(f"Placed {sess['subject']} (year {year} batch {sess['batch']}) in lab '{free_lab}' at {day} {slot} (faculty {faculty})")

                        # remove from queue (we scheduled it)
                        queue.pop(i)
                        # Do not increment i because we removed current; next element is at same index

                        # Per rule: once this division has a practical for the day, no other assignments for that division on this day
                        # The division_has_practical() helper will now reflect that.

                    # update queue back
                    assignment_queues[year] = queue

        # After attempting all days/slots, we may still have leftover assignments (couldn't schedule due to lack of labs/faculty/day limits)
        leftover = {y: assignment_queues[y] for y in years if assignment_queues.get(y)}
        if leftover:
            # Log summary of leftovers
            for y, rem in leftover.items():
                logger.warning(f"Unscheduled assignments for {y}: {len(rem)} items. Examples (up to 5): {rem[:5]}")
        else:
            logger.info("All assignments scheduled (or no assignments to schedule).")

        # Save final lab-wise timetable documents into DB and build return payload
        timetables = []
        for lab_name, schedule in merged_timetable['labs'].items():
            doc = {
                'lab_name': lab_name,
                'schedule': schedule,
                'generated_at': datetime.now()
            }
            master_lab_timetable_collection.insert_one(doc)
            timetables.append(doc)

        logger.info("✅ Unified lab-wise timetable generated and saved.")
        return {'timetables': timetables}

    except Exception as e:
        logger.error(f"Error generating unified timetable: {str(e)}", exc_info=True)
        return None
