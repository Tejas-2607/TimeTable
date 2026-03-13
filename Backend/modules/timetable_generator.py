# Schedules all practical lab sessions across 5 labs
# Now supports practical_hrs (2-hour or 3-hour practicals)

from datetime import datetime
from config import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
SLOTS = ['11:15', '14:15', '16:20']  # Practical slots (3 per day)
LUNCH_SLOT = '13:15'

subjects_collection = db['subjects']
faculty_collection = db['faculty']
workload_collection = db['workload']
labs_collection = db['labs']
class_timetable_collection = db['class_timetable']
master_lab_timetable_collection = db['master_lab_timetable']


class TimetableGenerator:
    """Generate practical timetables using greedy constraint satisfaction"""
    
    def __init__(self):
        self.timetable = {'labs': {}}
        self.class_timetables = {}
        self.faculty_names = {}
        self.labs_list = []
        
    def prepare_assignments(self):
        """
        Prepare assignments from workload collection.
        
        ✨ FIX: Creates MULTIPLE entries for each practical based on practical_hrs
        So a 2-hour practical gets 2 entries (hour 1, hour 2)
        
        Each entry is scheduled in a DIFFERENT time slot.
        
        Output:
        {
          (SY, A, 1): [
            {subject: DS, hour: 1, faculty: RKD},
            {subject: DS, hour: 2, faculty: RKD},  ← 2nd hour of same practical!
            {subject: CG, hour: 1, faculty: KRP},
            {subject: CG, hour: 2, faculty: KRP},
            {subject: OOPJ, hour: 1, faculty: AMP},
            {subject: OOPJ, hour: 2, faculty: AMP},
            ...
          ],
          (SY, A, 2): [...],
          (SY, A, 3): [...],
          ...
        }
        """
        assignments = {}
        try:
            workloads = list(workload_collection.find({}))
            faculties = list(faculty_collection.find({}, {'_id': 1, 'name': 1}))
            
            # Build faculty name map
            for f in faculties:
                self.faculty_names[str(f['_id'])] = f['name']
            
            logger.info(f"Reading {len(workloads)} workload entries...")
            
            for w in workloads:
                year = (w.get('year') or '').strip().upper()
                division = w.get('division', 'A')
                batches = w.get('batches', [1, 2, 3])
                subject = w.get('subject')
                subject_full = w.get('subject_full', subject)
                faculty_id = str(w.get('faculty_id', ''))
                faculty_name = self.faculty_names.get(faculty_id, faculty_id)
                
                # ✨ KEY FIX: Read practical_hrs for MULTI-HOUR SUPPORT
                practical_hrs = w.get('practical_hrs', 1)
                
                logger.debug(f"{year}-{division}-{subject}: {practical_hrs} hours, batches {batches}")
                
                # FOR EACH BATCH
                for batch in batches:
                    
                    # ✨ NEW LOOP: Create one entry PER HOUR
                    # So a 2-hour practical gets 2 entries
                    for hour_num in range(practical_hrs):
                        practical = {
                            'subject': subject,
                            'subject_full': subject_full,
                            'batch': batch,
                            'faculty_id': faculty_id,
                            'faculty': faculty_name,
                            'hour': hour_num + 1,  # Which hour (1st, 2nd, etc)
                            'year': year,
                            'division': division
                        }
                        
                        key = (year, division, batch)
                        
                        if key not in assignments:
                            assignments[key] = []
                        
                        assignments[key].append(practical)
            
            logger.info(f"✓ Prepared {len(assignments)} batch assignments")
            total_practicals = sum(len(practicals) for practicals in assignments.values())
            logger.info(f"✓ Total practical entries to schedule: {total_practicals}")
            
            # Log breakdown
            for key, practicals in sorted(assignments.items()):
                logger.info(f"  {key[0]}-{key[1]}-B{key[2]}: {len(practicals)} entries")
            
            return assignments
        
        except Exception as e:
            logger.error(f"Error preparing assignments: {e}", exc_info=True)
            return {}
    
    def get_faculty_names(self):
        """Build faculty name lookup dictionary"""
        try:
            faculties = list(faculty_collection.find({}, {'_id': 1, 'name': 1}))
            for f in faculties:
                self.faculty_names[str(f['_id'])] = f['name']
            logger.info(f"✓ Loaded {len(self.faculty_names)} faculty members")
        except Exception as e:
            logger.error(f"Error loading faculty: {e}")
    
    def get_labs(self):
        """Get list of labs from database"""
        try:
            labs = list(labs_collection.find({}))
            self.labs_list = [lab.get('name') for lab in labs if lab.get('name')]
            
            logger.info(f"✓ Loaded {len(self.labs_list)} labs: {self.labs_list}")
            
            # Initialize timetable for each lab
            for lab_name in self.labs_list:
                self.timetable['labs'][lab_name] = {}
                for day in DAYS:
                    self.timetable['labs'][lab_name][day] = {}
                    for slot in SLOTS:
                        self.timetable['labs'][lab_name][day][slot] = []
            
            return self.labs_list
        except Exception as e:
            logger.error(f"Error loading labs: {e}")
            return []
    
    def get_class_timetables(self):
        """Get class timetables to check for conflicts"""
        try:
            timetables = list(class_timetable_collection.find({}))
            for tt in timetables:
                key = (tt.get('class'), tt.get('division'))
                self.class_timetables[key] = tt
            
            logger.info(f"✓ Loaded {len(timetables)} class timetables")
            return timetables
        except Exception as e:
            logger.error(f"Error loading class timetables: {e}")
            return []
    
    def faculty_busy(self, faculty_name, day, slot):
        """
        Check if faculty is already teaching at this time in ANY lab.
        
        Prevents faculty from being in 2 labs at same time.
        """
        for lab_name, lab_schedule in self.timetable['labs'].items():
            day_schedule = lab_schedule.get(day, {})
            slot_sessions = day_schedule.get(slot, [])
            
            for session in slot_sessions:
                if session.get('faculty') == faculty_name:
                    return True
        
        return False
    
    def is_slot_available_in_class(self, year, division, day, slot):
        """
        Check if slot is available in class timetable.
        
        A slot is available if nothing else (lecture or practical) is there.
        """
        key = (year, division)
        if key not in self.class_timetables:
            return False
        
        timetable = self.class_timetables[key]
        schedule = timetable.get('schedule', {})
        day_schedule = schedule.get(day, {})
        slot_sessions = day_schedule.get(slot, [])
        
        return len(slot_sessions) == 0
    
    def get_free_labs(self, day, slot):
        """
        Get list of labs with empty slots at [day][slot].
        
        Returns: List of lab names that are free
        """
        free_labs = []
        
        for lab_name, lab_schedule in self.timetable['labs'].items():
            day_schedule = lab_schedule.get(day, {})
            slot_sessions = day_schedule.get(slot, [])
            
            if len(slot_sessions) == 0:
                free_labs.append(lab_name)
        
        return free_labs
    
    def select_compatible_batches(self, day, slot, pending_assignments, years_priority):
        """
        Select batches that can be scheduled together in this slot.
        
        Compatible means:
        - Different subjects (not scheduling same batch twice)
        - Different batches (Batch 1, 2, 3 different)
        - Faculty available
        - Free labs exist
        
        Returns: List of (key, practical) tuples to schedule
        """
        compatible = []
        used_batches = set()
        used_faculties = set()
        required_labs = 0
        
        # Sort by priority
        sorted_keys = sorted(
            [k for k in pending_assignments.keys()],
            key=lambda k: (years_priority.index(k[0]), k[1], k[2])
        )
        
        for key in sorted_keys:
            if key in used_batches:
                continue
            
            pending = pending_assignments[key]
            if not pending:
                continue
            
            practical = pending[0]
            faculty = practical['faculty']
            batch = practical['batch']
            
            # Check if faculty already scheduled in this slot
            if faculty in used_faculties:
                continue
            
            # Check if we have enough free labs
            if required_labs + 1 > len(self.labs_list):
                continue
            
            # Check faculty is free globally
            if self.faculty_busy(faculty, day, slot):
                continue
            
            # Check slot available in class
            year, division, _ = key
            if not self.is_slot_available_in_class(year, division, day, slot):
                continue
            
            # All checks passed
            compatible.append((key, practical))
            used_batches.add(key)
            used_faculties.add(faculty)
            required_labs += 1
        
        return compatible
    
    def generate(self):
        """
        Main algorithm to generate practical timetable.
        
        ALGORITHM: Greedy Constraint Satisfaction
        - Batch-level grouping (prevents same batch in 2 labs)
        - Priority ordering (SY > TY > BE)
        - Constraint checking (faculty, lab availability, slot)
        - Sequential processing (spreads across week)
        
        CONSTRAINTS CHECKED:
        ✓ Batch location uniqueness (batch not in 2 labs same time)
        ✓ Faculty availability (faculty not in 2 labs same time)
        ✓ Lab availability (free labs exist)
        ✓ Slot availability (slot empty in class)
        ✓ ✨ Multi-hour support (2-hour practical gets 2 slots)
        """
        try:
            logger.info("=" * 80)
            logger.info("STARTING PRACTICAL TIMETABLE GENERATION")
            logger.info("=" * 80)
            
            # Step 1: Load data
            self.get_faculty_names()
            self.get_labs()
            assignments = self.prepare_assignments()
            self.get_class_timetables()
            
            if not assignments:
                logger.error("No assignments found!")
                return {
                    'success': False,
                    'error': 'No assignments found',
                    'deleted_records': 0,
                    'labs_generated': 0
                }
            
            if not self.labs_list:
                logger.error("No labs found!")
                return {
                    'success': False,
                    'error': 'No labs found',
                    'deleted_records': 0,
                    'labs_generated': 0
                }
            
            # Step 2: Initialize timetable
            years_priority = ['SY', 'TY', 'BE']
            scheduled_count = 0
            
            # Step 3: Main scheduling loop
            for day in DAYS:
                logger.info(f"\n=== Scheduling for {day} ===")
                
                for slot in SLOTS:
                    logger.info(f"\n--- {day} {slot} ---")
                    
                    # Get compatible batches for this slot
                    compatible = self.select_compatible_batches(
                        day, slot, assignments, years_priority
                    )
                    
                    if not compatible:
                        logger.debug(f"  No compatible batches for {day} {slot}")
                        continue
                    
                    # Get free labs
                    free_labs = self.get_free_labs(day, slot)
                    
                    if not free_labs:
                        logger.debug(f"  No free labs at {day} {slot}")
                        continue
                    
                    # Place compatible batches in free labs
                    for i, (key, practical) in enumerate(compatible):
                        if i >= len(free_labs):
                            break
                        
                        lab = free_labs[i]
                        year, division, batch = key
                        subject = practical['subject']
                        faculty = practical['faculty']
                        hour = practical['hour']
                        
                        # Add to lab timetable
                        self.timetable['labs'][lab][day][slot].append({
                            'batch': f"Batch {batch}",
                            'subject': subject,
                            'subject_full': practical['subject_full'],
                            'faculty': faculty,
                            'division': division,
                            'class': year,
                            'hour': hour
                        })
                        
                        # Add to class timetable
                        class_key = (year, division)
                        if class_key not in self.class_timetables:
                            self.class_timetables[class_key] = {
                                'class': year,
                                'division': division,
                                'schedule': {}
                            }
                        
                        ct = self.class_timetables[class_key]
                        if day not in ct['schedule']:
                            ct['schedule'][day] = {}
                        if slot not in ct['schedule'][day]:
                            ct['schedule'][day][slot] = []
                        
                        ct['schedule'][day][slot].append({
                            'batch': f"Batch {batch}",
                            'subject': subject,
                            'subject_full': practical['subject_full'],
                            'faculty': faculty,
                            'lab': lab,
                            'type': 'practical'
                        })
                        
                        # Remove from pending
                        assignments[key].pop(0)
                        scheduled_count += 1
                        
                        logger.info(
                            f"  ✓ {year}-{division}-B{batch}-{subject} "
                            f"(Hour {hour}) → {lab} by {faculty}"
                        )
            
            # Step 4: Save master lab timetable
            logger.info(f"\n=== Saving Master Lab Timetable ===")
            
            for lab_name, schedule in self.timetable['labs'].items():
                doc = {
                    'lab_name': lab_name,
                    'schedule': schedule,
                    'generated_at': datetime.now()
                }
                
                master_lab_timetable_collection.replace_one(
                    {'lab_name': lab_name},
                    doc,
                    upsert=True
                )
                logger.info(f"✓ Saved {lab_name}")
            
            # Step 5: Save class timetables
            logger.info(f"\n=== Saving Class Timetables ===")
            
            for (year, division), timetable in self.class_timetables.items():
                timetable['generated_at'] = datetime.now()
                class_timetable_collection.replace_one(
                    {'class': year, 'division': division},
                    timetable,
                    upsert=True
                )
                logger.info(f"✓ Saved {year}-{division}")
            
            # Step 6: Report leftovers
            leftovers = {}
            for key, pending in assignments.items():
                if pending:
                    year, division, batch = key
                    leftovers[f"{year}-{division}-B{batch}"] = {
                        'count': len(pending),
                        'subjects': [p['subject'] for p in pending]
                    }
            
            if leftovers:
                logger.warning(f"\n⚠️ {len(leftovers)} assignments incomplete:")
                for key, data in leftovers.items():
                    logger.warning(f"  {key}: {data['count']} entries - {data['subjects']}")
            else:
                logger.info("\n✅ All practicals successfully scheduled!")
            
            logger.info("=" * 80)
            logger.info(f"PRACTICAL GENERATION COMPLETE: {scheduled_count} practicals scheduled")
            logger.info("=" * 80)
            
            return {
                'success': True,
                'message': f'Scheduled {scheduled_count} practical sessions',
                'labs_generated': len(self.labs_list),
                'practicals_scheduled': scheduled_count,
                'leftovers': leftovers
            }
        
        except Exception as e:
            logger.error(f"Error in generate: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}


# Main function to call from app.py
def generate():
    """Generate practical timetable"""
    generator = TimetableGenerator()
    return generator.generate()