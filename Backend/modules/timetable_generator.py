# Correctly schedules batches without putting same batch in multiple places
from datetime import datetime
from config import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
SLOTS = ['11:15', '14:15', '16:20']

subjects_collection = db['subjects']
faculty_collection = db['faculty']
labs_collection = db['labs']
class_structure_collection = db['class_structure']
workload_collection = db['workload']
master_lab_timetable_collection = db['master_lab_timetable']


class PracticalTimetableGenerator:
    """Build per-batch assignment queues from workload collection."""
    def __init__(self, year, semester='1'):
        self.year = year
        self.semester = semester

    def prepare_assignments(self):
        """
        Group assignments by (year, division, batch).
        
        KEY CHANGE: Now groups by BATCH, not just division!
        
        This ensures:
        - Each batch has its own queue
        - Subjects for same batch are scheduled separately
        - No same batch in multiple labs at same time
        
        Returns: {(year, division, batch): [subject1, subject2, ...]}
        """
        assignments_by_batch = {}
        try:
            workloads = list(workload_collection.find({}))
            faculties = list(faculty_collection.find({}, {'_id': 1, 'name': 1}))
            faculty_id_to_name = {str(f['_id']): f['name'] for f in faculties}
            
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

                # Create one assignment per batch
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
                    
                    # KEY FIX: Group by (year, division, batch)
                    # Each batch gets its own queue
                    key = (self.year.upper(), division, batch)
                    assignments_by_batch.setdefault(key, []).append(a)

            logger.info(f"Prepared assignments for {self.year}")
            for key, queue in assignments_by_batch.items():
                logger.info(f"  {key[0]}-{key[1]}-Batch{key[2]}: {len(queue)} subjects")
            
            return assignments_by_batch

        except Exception as e:
            logger.error(f"Error preparing assignments for {self.year}: {e}", exc_info=True)
            return {}


def generate(data=None):
    """
    FIXED PARALLEL SCHEDULING: Schedule multiple DIFFERENT BATCHES at same time in different labs.
    
    KEY CONSTRAINT: SAME BATCH can only appear ONCE per time slot across all labs.
    
    CORRECT:
      Monday 11:15:
        Lab1: SY-A-B1-DS (different subject/batch from Lab2)
        Lab2: SY-A-B2-CG (different batch!)
        Lab3: SY-A-B3-OOPJ (different batch!)
    
    WRONG (WHAT WE HAD):
      Monday 11:15:
        Lab1: SY-A-B1-DS
        Lab2: SY-A-B1-CG (SAME BATCH! ❌)
        Lab3: SY-A-B1-OOPJ (SAME BATCH! ❌)
    """
    try:
        master_lab_timetable_collection.delete_many({})

        labs = list(labs_collection.find({}, {'_id': 0, 'name': 1}))
        if not labs:
            logger.error("No labs found in DB. Aborting.")
            return None
        lab_names = [l.get('name', 'Unknown Lab') for l in labs]
        logger.info(f"Available labs: {lab_names} (total: {len(lab_names)})")

        merged_timetable = {'labs': {}}
        for lab_name in lab_names:
            merged_timetable['labs'][lab_name] = {day: {slot: [] for slot in SLOTS} for day in DAYS}

        # Prepare assignments: (year, division, batch) → [subjects]
        years_prio = ['SY', 'TY', 'BE']
        assignments = {}
        for y in years_prio:
            gen = PracticalTimetableGenerator(y)
            assignments.update(gen.prepare_assignments())

        logger.info(f"Total assignment batches: {len(assignments)}")

        # Helper functions
        def faculty_busy(faculty_name, day, slot):
            """Check if faculty is already assigned at this time."""
            for lab_schedule in merged_timetable['labs'].values():
                for sess in lab_schedule[day][slot]:
                    if sess.get('faculty') == faculty_name:
                        return True
            return False

        def batch_has_session(batch_id, division, class_name, day, slot):
            """Check if this batch already has a session in this time slot."""
            for lab_schedule in merged_timetable['labs'].values():
                for sess in lab_schedule[day][slot]:
                    if (sess.get('batch') == batch_id and 
                        sess.get('division') == division and 
                        sess.get('class') == class_name):
                        return True
            return False

        def free_labs_count(day, slot):
            """Count free labs at this slot."""
            return sum(1 for ln in lab_names if len(merged_timetable['labs'][ln][day][slot]) == 0)

        def get_free_labs(day, slot):
            """Get list of free lab names at this slot."""
            return [ln for ln in lab_names if len(merged_timetable['labs'][ln][day][slot]) == 0]

        def count_practicals_today(division, class_name, day):
            """Count how many practicals this division has today."""
            count = 0
            for lab_schedule in merged_timetable['labs'].values():
                for slot in SLOTS:
                    for sess in lab_schedule[day][slot]:
                        if sess.get('division') == division and sess.get('class') == class_name:
                            count += 1
            return count

        # Main scheduling loop
        for day in DAYS:
            scheduled_divisions_today = {}  # Track practicals per division per day
            sorted_keys = sorted(assignments.keys(),
                                key=lambda k: (years_prio.index(k[0]), k[1], k[2]))

            for slot in SLOTS:
                
                for key in list(sorted_keys):
                    year, division, batch = key
                    queue = assignments.get(key)
                    
                    if not queue or len(queue) == 0:
                        continue
                    
                    division_key = (year, division)

                    # CONSTRAINT 1: Max 2 practicals per division per day
                    practicals_today = count_practicals_today(year, division, day)
                    if practicals_today >= 2:
                        logger.debug(f"Skipping {year}-{division}-B{batch}: Already has 2 practicals today")
                        continue

                    # CONSTRAINT 2: Batch already has session in this time slot? (THE FIX!)
                    if batch_has_session(batch, division, year, day, slot):
                        logger.debug(f"Skipping {year}-{division}-B{batch}: Already scheduled this time")
                        continue

                    # CONSTRAINT 3: Take next subject from this batch's queue
                    assignment = queue[0]  # Get first subject for this batch
                    
                    # CONSTRAINT 4: Faculty must be free
                    if faculty_busy(assignment['faculty'], day, slot):
                        logger.debug(f"Skipping {year}-{division}-B{batch}-{assignment['subject']}: Faculty busy")
                        continue

                    # CONSTRAINT 5: Must have a free lab
                    free_labs = get_free_labs(day, slot)
                    if not free_labs:
                        logger.debug(f"Skipping {year}-{division}-B{batch}: No free labs")
                        continue

                    # All checks passed - place this subject
                    lab_name = free_labs[0]
                    
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
                    
                    logger.info(f"Placing {year}-{division}-B{batch}-{assignment['subject']} at {day} {slot}: {lab_name}")

                    # Remove this subject from queue
                    queue.pop(0)
                    
                    # If queue empty, remove the key
                    if not queue:
                        assignments.pop(key, None)
                    
                    # Re-sort for next iteration
                    sorted_keys = sorted([k for k in assignments.keys()],
                                        key=lambda k: (years_prio.index(k[0]), k[1], k[2]))

        # Gather leftovers
        leftovers = {}
        for (year, div, batch), queue in assignments.items():
            if queue and len(queue) > 0:
                leftovers.setdefault(year, {})[f"{div}-B{batch}"] = {
                    'count': len(queue),
                    'subjects': [q.get('subject') for q in queue]
                }

        if leftovers:
            total_leftovers = sum(len(d) for y_dict in leftovers.values() for d in y_dict.values() if isinstance(d, dict) and 'count' in d)
            logger.warning(f"⚠️ Leftover (unscheduled) assignments: {total_leftovers}")
            for year, div_dict in leftovers.items():
                for div, data in div_dict.items():
                    if isinstance(data, dict):
                        logger.warning(f"  → {year}-{div}: {data['count']} subjects: {data['subjects']}")
        else:
            logger.info("✅ All assignments successfully scheduled!")

        # Return results
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
        logger.error(f"Error in generate(): {e}", exc_info=True)
        return None