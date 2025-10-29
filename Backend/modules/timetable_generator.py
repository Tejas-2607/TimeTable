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
    Build per-year assignment queues from workload collection.
    Each assignment corresponds to one batch needing one practical slot/week.
    """
    def __init__(self, year, semester='1'):
        self.year = year  # 'SY'|'TY'|'BE'
        self.semester = semester

    def prepare_assignments(self):
        """
        Return a dict mapping (year, division, subject) -> list of assignments.
        This ensures we schedule one subject for one division at a time.
        Each assignment: {
            'subject','subject_full','class','division','batch','faculty_id','faculty'
        }
        """
        assignments_by_subject_div = {}
        try:
            workloads = list(workload_collection.find({}))
            faculties = list(faculty_collection.find({}, {'_id': 1, 'name': 1}))
            faculty_id_to_name = {str(f['_id']): f['name'] for f in faculties}
            
            # --- DEBUG: CHECK IF WORKLOADS ARE FETCHED ---
            # logger.info(f"Workloads found: {len(workloads)}")
            # ---------------------------------------------

            for w in workloads:
                year = (w.get('year') or '').strip().upper()
                if not year or year != self.year.upper():
                    continue

                division = w.get('division', 'A')
                batches = w.get('batches', []) or []
                subject = w.get('subject') or w.get('short_name') or ''
                subject_full = w.get('subject_full') or w.get('name') or subject
                faculty_id = str(w.get('faculty_id', ''))
                faculty_name = faculty_id_to_name.get(faculty_id, faculty_id)

                # Create one assignment per batch (1 practical-slot per week per batch)
                for batch in batches:
                    a = {
                        'subject': subject,
                        'subject_full': subject_full,
                        'class': self.year.upper(),
                        'division': division,
                        'batch': batch,
                        'faculty_id': faculty_id,
                        'faculty': faculty_name
                    }
                    # NEW KEY: (Year, Division, Subject)
                    key = (self.year.upper(), division, subject) 
                    assignments_by_subject_div.setdefault(key, []).append(a)

            # --- DEBUG: CHECK ASSIGNMENT COUNT ---
            # logger.info(f"Assignments prepared for {self.year}: {sum(len(q) for q in assignments_by_subject_div.values())}")
            # -------------------------------------
            return assignments_by_subject_div

        except Exception as e:
            logger.error(f"Error preparing assignments for {self.year}: {e}", exc_info=True)
            return {}


def generate(data=None):
    """
    Unified lab-wise timetable generator with parallel-batch scheduling.
    """
    try:
        master_lab_timetable_collection.delete_many({})

        labs = list(labs_collection.find({}, {'_id': 0, 'name': 1}))
        if not labs:
            logger.error("No labs found in DB. Aborting.")
            return None
        lab_names = [l.get('name', 'Unknown Lab') for l in labs]

        merged_timetable = {'labs': {}}
        for lab_name in lab_names:
            merged_timetable['labs'][lab_name] = {day: {slot: [] for slot in SLOTS} for day in DAYS}

        # Prepare assignments per year, division, AND subject
        years_prio = ['BE', 'TY', 'SY']
        assignments = {}
        for y in years_prio:
            gen = PracticalTimetableGenerator(y)
            assignments.update(gen.prepare_assignments()) 

        # Helper functions
        def faculty_busy(faculty_name, day, slot):
            """Checks if a faculty member is already assigned to a lab at this time."""
            # IMPORTANT: This checks the *final* timetable, not the assignment queue
            for L in merged_timetable['labs'].values():
                for sess in L[day][slot]:
                    if sess.get('faculty') == faculty_name:
                        return True
            return False

        def free_labs_count(day, slot):
            return sum(1 for ln in lab_names if len(merged_timetable['labs'][ln][day][slot]) == 0)

        def get_free_labs(day, slot):
            return [ln for ln in lab_names if len(merged_timetable['labs'][ln][day][slot]) == 0]

        
        for day in DAYS:
            # 1. Constraint: Reset tracker for divisions scheduled today (Tracks only Year and Division)
            scheduled_divisions_today = set() 
            
            # Sort keys by Year priority (BE > TY > SY) then by Division, then by Subject
            sorted_assignment_keys = sorted(assignments.keys(), 
                                            key=lambda k: (years_prio.index(k[0]), k[1], k[2]))

            for slot in SLOTS:
                
                # Iterate through subjects/divisions in priority order
                for key in list(sorted_assignment_keys): # Use list() to iterate over a copy
                    year, division, subject = key
                    queue = assignments.get(key)
                    
                    if not queue:
                        continue
                    
                    division_key = (year, division)

                    # 1. Constraint: Skip if the (Year, Division) combination is already scheduled today
                    if division_key in scheduled_divisions_today:
                        continue 

                    num_batches = len(queue)
                    free = free_labs_count(day, slot)
                    
                    if free < num_batches:
                        continue

                    # Get required faculties (can be duplicates, e.g., 'AMP', 'AMP')
                    faculties_needed = [a['faculty'] for a in queue]
                    
                    # 3. Constraint: Check for faculty conflict against *previously scheduled* sessions
                    faculty_conflict = any(faculty_busy(f, day, slot) for f in faculties_needed)
                    
                    if faculty_conflict:
                        logger.info(f"Skipping {year}-{division}-{subject} at {day} {slot}: Faculty conflict detected.")
                        continue
                        
                    # Passed checks: Place batches atomically (2. Constraint)
                    free_labs = get_free_labs(day, slot)
                    selected_labs = free_labs[:num_batches]

                    for idx, assignment in enumerate(queue):
                        lab_name = selected_labs[idx]
                        sess = {
                            'batch': assignment.get('batch'),
                            'class': assignment.get('class'),
                            'division': assignment.get('division'),
                            'faculty': assignment.get('faculty'),
                            'faculty_id': assignment.get('faculty_id'),
                            'subject': assignment.get('subject'),
                            'subject_full': assignment.get('subject_full')
                        }
                        merged_timetable['labs'][lab_name][day][slot].append(sess)
                        logger.info(f"Placed {sess['class']}-{sess['division']}-B{sess['batch']} {sess['subject']} in {lab_name} at {day} {slot} by {sess['faculty']}")

                    # Remove scheduled assignments (4. Constraint: All practicals must be completed)
                    assignments.pop(key, None)
                    
                    # Mark the division as scheduled for the day (1. Constraint)
                    scheduled_divisions_today.add(division_key) 

                    # Re-sort/Filter keys list for the next iteration (important for priority)
                    sorted_assignment_keys = sorted([k for k in assignments.keys()], 
                                                    key=lambda k: (years_prio.index(k[0]), k[1], k[2]))

        # After attempting all day+slots, gather leftovers
        leftovers = {}
        for (year, div, sub), q in assignments.items():
            if q:
                leftovers.setdefault(year, {}).setdefault(div, {}).setdefault(sub, q)

        if leftovers:
            total_leftovers = sum(len(q) for y_divs in leftovers.values() for div_subs in y_divs.values() for q in div_subs.values())
            logger.warning(f"Leftover (unscheduled) assignments exist. Total: {total_leftovers}.")
            logger.warning(f"Summary: { {y: sum(len(q) for sub_q in left.values() for q in sub_q.values()) for y, left in leftovers.items()} }")

        # Return all generated schedules (lab-wise) and any leftovers
        timetables = []
        for lab_name, schedule in merged_timetable['labs'].items():
            doc = {
                'lab_name': lab_name,
                'schedule': schedule,
                'generated_at': datetime.now()
            }
            timetables.append(doc)

        return {'timetables': timetables, 'leftovers': leftovers, 'labs': merged_timetable['labs']}

    except Exception as e:
        logger.error(f"Error in unified generate(): {e}", exc_info=True)
        return None