# timetable_generator.py - PARALLEL SCHEDULING (SMART VERSION)
# This version intelligently selects batches to schedule in parallel
from datetime import datetime
from config import db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
SLOTS = ['11:15', '14:15', '16:20']

# Database collections
subjects_collection = db['subjects']
faculty_collection = db['faculty']
labs_collection = db['labs']
class_structure_collection = db['class_structure']
workload_collection = db['workload']
master_lab_timetable_collection = db['master_lab_timetable']


class PracticalTimetableGenerator:
    """Build per-year assignment queues from workload collection."""
    def __init__(self, year, semester='1'):
        self.year = year
        self.semester = semester

    def prepare_assignments(self):
        """
        Group all batches of a division together.
        Returns dict: (year, division) → list of batch assignments
        """
        assignments_by_division = {}
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

                # Create assignment for each batch
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
                    # Group by division only
                    key = (self.year.upper(), division)
                    assignments_by_division.setdefault(key, []).append(a)

            logger.info(f"Prepared assignments for {self.year}")
            for key, queue in assignments_by_division.items():
                logger.info(f"  {key[0]}-{key[1]}: {len(queue)} batches total")
            
            return assignments_by_division

        except Exception as e:
            logger.error(f"Error preparing assignments for {self.year}: {e}", exc_info=True)
            return {}


def generate(data=None):
    """
    SMART PARALLEL SCHEDULING: Schedule multiple batches at same time in different labs
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

        # Prepare assignments
        years_prio = ['SY', 'TY', 'BE']
        assignments = {}
        for y in years_prio:
            gen = PracticalTimetableGenerator(y)
            assignments.update(gen.prepare_assignments())

        logger.info(f"Total assignment groups: {len(assignments)}")

        # Helper functions
        def faculty_busy(faculty_name, day, slot):
            """Check if faculty is already assigned at this time."""
            for lab_schedule in merged_timetable['labs'].values():
                for sess in lab_schedule[day][slot]:
                    if sess.get('faculty') == faculty_name:
                        return True
            return False

        def free_labs_count(day, slot):
            """Count free labs at this slot."""
            return sum(1 for ln in lab_names if len(merged_timetable['labs'][ln][day][slot]) == 0)

        def get_free_labs(day, slot):
            """Get list of free lab names at this slot."""
            return [ln for ln in lab_names if len(merged_timetable['labs'][ln][day][slot]) == 0]

        def select_compatible_batches(queue, day, slot):
            """
            SMART: Select batches that can be placed in parallel.
            
            Returns: (selected_batches, remaining_queue)
            
            Selection criteria:
            1. All faculties must be different (no duplicate faculty)
            2. All faculties must be free
            3. Must fit in available labs
            """
            free_labs = get_free_labs(day, slot)
            selected = []
            remaining = []
            used_faculties = set()
            
            for batch in queue:
                faculty = batch['faculty']
                
                # Can we add this batch?
                can_add = (
                    faculty not in used_faculties and  # Faculty not already selected
                    not faculty_busy(faculty, day, slot) and  # Faculty is free
                    len(selected) < len(free_labs)  # We have a free lab
                )
                
                if can_add:
                    selected.append(batch)
                    used_faculties.add(faculty)
                else:
                    remaining.append(batch)
            
            return selected, remaining

        # Main scheduling loop
        for day in DAYS:
            scheduled_divisions_today = set()
            sorted_keys = sorted(assignments.keys(),
                                key=lambda k: (years_prio.index(k[0]), k[1]))

            for slot in SLOTS:
                
                for key in list(sorted_keys):
                    year, division = key
                    queue = assignments.get(key)
                    
                    if not queue or len(queue) == 0:
                        continue
                    
                    division_key = (year, division)

                    # CONSTRAINT 1: One division per day
                    if division_key in scheduled_divisions_today:
                        logger.debug(f"Skipping {year}-{division}: Already scheduled today")
                        continue

                    # CONSTRAINT 2: Intelligently select batches that can be placed in parallel
                    selected_batches, remaining_batches = select_compatible_batches(queue, day, slot)
                    
                    if not selected_batches:
                        logger.debug(f"Skipping {year}-{division} at {day} {slot}: No compatible batches")
                        continue

                    # CONSTRAINT 3: Place selected batches
                    free_labs = get_free_labs(day, slot)
                    
                    placement_log = f"Placing {year}-{division} at {day} {slot}: "
                    for idx, batch in enumerate(selected_batches):
                        lab_name = free_labs[idx]
                        
                        sess = {
                            'batch': batch.get('batch'),
                            'class': batch.get('class'),
                            'division': batch.get('division'),
                            'faculty': batch.get('faculty'),
                            'faculty_id': batch.get('faculty_id'),
                            'subject': batch.get('subject'),
                            'subject_full': batch.get('subject_full')
                        }
                        merged_timetable['labs'][lab_name][day][slot].append(sess)
                        placement_log += f"[{lab_name}:{sess['subject']}({sess['faculty']})] "
                    
                    logger.info(placement_log)

                    # Update queue with remaining batches
                    if remaining_batches:
                        assignments[key] = remaining_batches
                    else:
                        assignments.pop(key, None)
                    
                    # Mark division as scheduled for the day
                    scheduled_divisions_today.add(division_key)

                    # Re-sort keys
                    sorted_keys = sorted([k for k in assignments.keys()],
                                        key=lambda k: (years_prio.index(k[0]), k[1]))

        # Gather leftovers
        leftovers = {}
        for (year, div), queue in assignments.items():
            if queue and len(queue) > 0:
                leftovers.setdefault(year, {})[div] = queue

        if leftovers:
            total_leftovers = 0
            for year_dict in leftovers.values():
                for queue in year_dict.values():
                    total_leftovers += len(queue)
            
            logger.warning(f"⚠️ Leftover (unscheduled) assignments: {total_leftovers}")
            for year, div_dict in leftovers.items():
                for div, queue in div_dict.items():
                    logger.warning(f"  → {year}-{div}: {len(queue)} batches")
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

        # Convert leftovers to serializable format
        leftovers_clean = {}
        for year, div_dict in leftovers.items():
            leftovers_clean[year] = {}
            for div, queue in div_dict.items():
                leftovers_clean[year][div] = {
                    'count': len(queue),
                    'batches': [{'batch': b.get('batch'), 'subject': b.get('subject'), 'faculty': b.get('faculty')} for b in queue]
                }

        return {'timetables': timetables, 'leftovers': leftovers_clean, 'labs': merged_timetable['labs']}

    except Exception as e:
        logger.error(f"Error in generate(): {e}", exc_info=True)
        return None