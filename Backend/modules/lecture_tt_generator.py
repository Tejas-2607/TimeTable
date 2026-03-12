# Uses morning first, then fills free afternoon slots
from datetime import datetime
from config import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
LECTURE_SLOTS_PRIORITY = ['10:15', '11:15', '12:15']  # Morning (priority)
LUNCH_SLOT = '13:15'
AFTERNOON_SLOTS = ['14:15', '15:15', '16:20']  # Afternoon (secondary)
ALL_LECTURE_SLOTS = ['10:15', '11:15', '12:15', '14:15', '15:15', '16:20']  # All slots

subjects_collection = db['subjects']
faculty_collection = db['faculty']
workload_collection = db['workload']
class_timetable_collection = db['class_timetable']


class LectureTimetableGenerator:
    """Generate lecture timetables and fill ALL available slots in class timetables"""
    
    def __init__(self):
        self.lecture_assignments = {}  # (year, division, subject) → [lectures to schedule]
        self.class_timetables = {}  # (year, division) → timetable object
        
    def get_lectures_per_week(self, workload_doc):
        """
        Intelligently extract lectures per week from workload document.
        
        Tries multiple possible field names:
        1. lectures_per_week (if exists)
        2. theory_hrs (if exists)
        3. lecture_hours (if exists)
        4. theory (if exists)
        5. Default to 1 if none found
        """
        possible_fields = ['lectures_per_week', 'theory_hrs', 'lecture_hours', 'theory', 'hours']
        
        for field in possible_fields:
            if field in workload_doc and workload_doc[field]:
                value = workload_doc[field]
                if isinstance(value, (int, float)) and value > 0:
                    return int(value)
        
        logger.warning(f"Could not find lectures per week for {workload_doc.get('subject')} - using default 1")
        return 1
        
    def prepare_lecture_assignments(self):
        """
        Prepare lecture assignments directly from workload collection.
        
        For EACH workload entry:
        - Get the number of lectures per week
        - Create that many lecture entries
        - Group by (year, division, subject)
        """
        assignments = {}
        try:
            workloads = list(workload_collection.find({}))
            faculties = list(faculty_collection.find({}, {'_id': 1, 'name': 1}))
            faculty_id_to_name = {str(f['_id']): f['name'] for f in faculties}
            
            logger.info(f"Reading {len(workloads)} workload entries from database...")
            
            for w in workloads:
                year = (w.get('year') or '').strip().upper()
                division = w.get('division', 'A')
                subject = w.get('subject') or w.get('short_name') or ''
                subject_full = w.get('subject_full') or w.get('name') or subject
                faculty_id = str(w.get('faculty_id', ''))
                faculty_name = faculty_id_to_name.get(faculty_id, faculty_id)
                
                # GET LECTURES PER WEEK FROM WORKLOAD (smart detection)
                lectures_per_week = self.get_lectures_per_week(w)
                
                logger.debug(f"Workload: {year}-{division}-{subject} = {lectures_per_week} lectures/week by {faculty_name}")
                
                # Create MULTIPLE lecture entries based on lectures_per_week
                lectures_for_this_subject = []
                for lecture_num in range(lectures_per_week):
                    lecture = {
                        'subject': subject,
                        'subject_full': subject_full,
                        'class': year,
                        'division': division,
                        'faculty_id': faculty_id,
                        'faculty': faculty_name,
                        'hours': 1,  # 1-hour lecture
                        'lecture_number': lecture_num + 1  # Which lecture this is (1st, 2nd, 3rd, etc)
                    }
                    lectures_for_this_subject.append(lecture)
                
                # Group by (year, division, subject)
                key = (year, division, subject)
                assignments[key] = lectures_for_this_subject
            
            logger.info(f"✓ Prepared {len(assignments)} lecture groups from workload")
            total_lectures = sum(len(lectures) for lectures in assignments.values())
            logger.info(f"✓ Total lectures to schedule: {total_lectures}")
            
            for key, lectures in sorted(assignments.items()):
                logger.info(f"  {key[0]}-{key[1]}-{key[2]}: {len(lectures)} lectures")
            
            return assignments
        
        except Exception as e:
            logger.error(f"Error preparing lecture assignments: {e}", exc_info=True)
            return {}
    
    def get_class_timetables(self):
        """
        Fetch all class timetables from database.
        These are the ones we'll fill with lectures.
        """
        try:
            timetables = list(class_timetable_collection.find({}))
            
            for tt in timetables:
                key = (tt.get('class'), tt.get('division'))
                self.class_timetables[key] = tt
            
            logger.info(f"✓ Loaded {len(timetables)} class timetables")
            return timetables
        
        except Exception as e:
            logger.error(f"Error fetching class timetables: {e}", exc_info=True)
            return []
    
    def faculty_busy(self, faculty_name, day, slot):
        """
        Check if faculty is already teaching at this time in ANY class.
        
        Searches all class timetables to prevent faculty conflicts.
        """
        for (year, div), timetable in self.class_timetables.items():
            schedule = timetable.get('schedule', {})
            day_schedule = schedule.get(day, {})
            slot_sessions = day_schedule.get(slot, [])
            
            for session in slot_sessions:
                if session.get('faculty') == faculty_name:
                    return True
        
        return False
    
    def is_slot_available(self, class_name, division, day, slot):
        """Check if a slot is empty in a class timetable"""
        key = (class_name, division)
        if key not in self.class_timetables:
            return False
        
        timetable = self.class_timetables[key]
        schedule = timetable.get('schedule', {})
        day_schedule = schedule.get(day, {})
        slot_sessions = day_schedule.get(slot, [])
        
        # Slot is available if it's empty
        return len(slot_sessions) == 0
    
    def add_lecture_to_slot(self, class_name, division, day, slot, lecture):
        """Add a lecture to a class timetable at specific slot"""
        key = (class_name, division)
        if key not in self.class_timetables:
            return False
        
        timetable = self.class_timetables[key]
        
        # Create lecture session entry
        session = {
            'subject': lecture.get('subject'),
            'subject_full': lecture.get('subject_full'),
            'faculty': lecture.get('faculty'),
            'faculty_id': lecture.get('faculty_id'),
            'hours': lecture.get('hours'),
            'type': 'lecture'
        }
        
        # Add to timetable
        schedule = timetable.get('schedule', {})
        day_schedule = schedule.get(day, {})
        
        if day not in schedule:
            schedule[day] = {}
        
        if slot not in schedule[day]:
            schedule[day][slot] = []
        
        schedule[day][slot].append(session)
        
        logger.debug(f"Added {class_name}-{division}-{lecture['subject']} L#{lecture['lecture_number']} at {day} {slot}")
        return True
    
    def generate_lectures(self):
        """
        Main algorithm to generate and fill lecture timetables.
        
        NEW: Uses ALL available slots:
        1. Try morning slots first (10:15, 11:15, 12:15)
        2. If morning full, use afternoon slots (14:15, 15:15, 16:20)
        3. Maximizes lecture scheduling across full day
        """
        try:
            logger.info("=" * 80)
            logger.info("STARTING LECTURE TIMETABLE GENERATION (Using All Slots)")
            logger.info("=" * 80)
            
            # Step 1: Get lecture assignments (directly from workload)
            lecture_assignments = self.prepare_lecture_assignments()
            
            if not lecture_assignments:
                logger.warning("No lecture assignments found in workload!")
                return {
                    'success': False,
                    'message': 'No lecture assignments found',
                    'lectures_scheduled': 0
                }
            
            # Step 2: Load class timetables
            self.get_class_timetables()
            
            if not self.class_timetables:
                logger.error("No class timetables found!")
                return {'success': False, 'error': 'No class timetables found'}
            
            # Step 3: Schedule lectures using ALL slots
            years_priority = ['SY', 'TY', 'BE']
            divisions = ['A', 'B', 'C']
            
            scheduled_count = 0
            
            for day in DAYS:
                logger.info(f"\n=== Scheduling Lectures for {day} ===")
                
                # TRY MORNING SLOTS FIRST
                for slot in LECTURE_SLOTS_PRIORITY:
                    logger.info(f"\n--- {day} {slot} (MORNING) ---")
                    
                    # Sort by priority: SY > TY > BE, then by division, then by subject
                    sorted_keys = sorted(
                        [k for k in lecture_assignments.keys()],
                        key=lambda k: (years_priority.index(k[0]), k[1], k[2])
                    )
                    
                    for year, division, subject in sorted_keys:
                        pending_lectures = lecture_assignments[(year, division, subject)]
                        
                        # Check if this subject has pending lectures
                        if not pending_lectures:
                            continue
                        
                        # Check if slot is available in class timetable
                        if not self.is_slot_available(year, division, day, slot):
                            logger.debug(f"Slot {slot} not available for {year}-{division}")
                            continue
                        
                        # Take next lecture for this subject
                        lecture = pending_lectures[0]
                        
                        # Check if faculty is free
                        if self.faculty_busy(lecture['faculty'], day, slot):
                            logger.debug(f"Faculty {lecture['faculty']} busy at {day} {slot}")
                            continue
                        
                        # All checks passed - schedule the lecture
                        self.add_lecture_to_slot(year, division, day, slot, lecture)
                        
                        # Remove from pending list
                        pending_lectures.pop(0)
                        scheduled_count += 1
                        
                        logger.info(f"✓ {year}-{division}-{subject} L#{lecture['lecture_number']} by {lecture['faculty']} (MORNING)")
                
                # THEN TRY AFTERNOON SLOTS (only if there are still pending lectures)
                any_pending = any(len(lectures) > 0 for lectures in lecture_assignments.values())
                
                if any_pending:
                    for slot in AFTERNOON_SLOTS:
                        logger.info(f"\n--- {day} {slot} (AFTERNOON) ---")
                        
                        sorted_keys = sorted(
                            [k for k in lecture_assignments.keys()],
                            key=lambda k: (years_priority.index(k[0]), k[1], k[2])
                        )
                        
                        for year, division, subject in sorted_keys:
                            pending_lectures = lecture_assignments[(year, division, subject)]
                            
                            if not pending_lectures:
                                continue
                            
                            # Check if slot is available
                            if not self.is_slot_available(year, division, day, slot):
                                logger.debug(f"Slot {slot} not available for {year}-{division}")
                                continue
                            
                            lecture = pending_lectures[0]
                            
                            # Check if faculty is free
                            if self.faculty_busy(lecture['faculty'], day, slot):
                                logger.debug(f"Faculty {lecture['faculty']} busy at {day} {slot}")
                                continue
                            
                            # Schedule the lecture in afternoon slot
                            self.add_lecture_to_slot(year, division, day, slot, lecture)
                            
                            pending_lectures.pop(0)
                            scheduled_count += 1
                            
                            logger.info(f"✓ {year}-{division}-{subject} L#{lecture['lecture_number']} by {lecture['faculty']} (AFTERNOON)")
            
            # Step 4: Save updated timetables
            logger.info(f"\n=== Saving {len(self.class_timetables)} timetables ===")
            for (year, division), timetable in self.class_timetables.items():
                timetable['generated_at'] = datetime.now()
                class_timetable_collection.replace_one(
                    {'class': year, 'division': division},
                    timetable,
                    upsert=True
                )
                logger.info(f"✓ Saved {year}-{division}")
            
            # Step 5: Report leftovers
            leftovers = {}
            for (year, division, subject), pending in lecture_assignments.items():
                if pending:
                    leftovers[f"{year}-{division}-{subject}"] = {
                        'count': len(pending),
                        'lectures': [f"L#{p['lecture_number']}" for p in pending]
                    }
            
            if leftovers:
                logger.warning(f"\n⚠️ {len(leftovers)} subjects have unscheduled lectures:")
                for key, data in leftovers.items():
                    logger.warning(f"  {key}: {data['count']} lectures - {data['lectures']}")
            else:
                logger.info("\n✅ All lectures successfully scheduled!")
            
            logger.info("=" * 80)
            logger.info(f"LECTURE GENERATION COMPLETE: {scheduled_count} lectures scheduled")
            logger.info("=" * 80)
            
            return {
                'success': True,
                'message': f'Scheduled {scheduled_count} lectures from workload',
                'lectures_scheduled': scheduled_count,
                'leftovers': leftovers
            }
        
        except Exception as e:
            logger.error(f"Error in generate_lectures: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}


# Main function to call from app.py
def generate():
    """Generate and fill lecture timetables"""
    generator = LectureTimetableGenerator()
    return generator.generate_lectures()