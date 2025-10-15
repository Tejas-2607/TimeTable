from datetime import datetime
from config import db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
SLOTS = ['11:15', '14:15', '16:20']  # 11:15 AM, 2:15 PM, 4:20 PM
MIN_PRACTICAL_HOURS = 2  # Only practicals with 2+ hours go to labs

# Database collections
subjects_collection = db['subjects']
faculty_collection = db['faculty']
labs_collection = db['labs']
class_structure_collection = db['class_structure']
workload_collection = db['workload']
master_lab_timetable_collection = db['master_lab_timetable']


class PracticalTimetableGenerator:
    def __init__(self, year, semester):
        self.year = year  # 'SY', 'TY', 'BE'
        self.semester = semester  # '1' or '2'
        self.timetable = {}
        self.assignments = []
        
    def generate(self):
        """Main generation method"""
        try:
            logger.info(f"Generating timetable for {self.year} Sem {self.semester}")
            
            # Phase 1: Load and validate data
            practicals = self._load_practicals()
            if not practicals:
                logger.warning(f"No practicals found for {self.year}")
                return None
            
            logger.info(f"Found {len(practicals)} practicals")
            
            # Phase 2: Get available resources
            labs = self._get_available_labs()
            faculties = self._get_all_faculties()
            faculty_subjects_map = self._get_faculty_subjects_mapping(practicals)
            
            if not labs or not faculties or not faculty_subjects_map:
                logger.error("Missing labs, faculties, or faculty-subject mapping")
                logger.error(f"Labs: {len(labs)}, Faculties: {len(faculties)}, Faculty-Subject Map: {len(faculty_subjects_map)}")
                return None
            
            logger.info(f"Found {len(labs)} labs and {len(faculties)} faculties")
            logger.info(f"Faculty-Subject mapping has {len(faculty_subjects_map)} entries")
            
            # Phase 3: Prepare batch assignments
            batch_assignments = self._prepare_batch_assignments(practicals)
            logger.info(f"Created {len(batch_assignments)} batch assignments")
            
            if not batch_assignments:
                logger.warning("No batch assignments created")
                return None
            
            # Phase 4: Initialize timetable structure
            self._initialize_timetable(labs)
            
            # Phase 5: Backtrack search to assign practicals
            success = self._backtrack_assign(batch_assignments, labs, faculties, faculty_subjects_map, 0)
            
            if success:
                logger.info("Timetable generated successfully")
                return self.timetable
            else:
                logger.error("Failed to generate valid timetable - backtracking exhausted")
                return None
                
        except Exception as e:
            logger.error(f"Error generating timetable: {str(e)}", exc_info=True)
            return None
    
    def _load_practicals(self):
        """Load practicals from database and filter non-lab practicals"""
        try:
            subjects_doc = subjects_collection.find_one({})
            if not subjects_doc or 'year' not in subjects_doc:
                logger.error("No subjects document found")
                return []
            
            year_key = self.year.lower()
            year_subjects = subjects_doc['year'].get(year_key, [])
            
            # Filter practicals: hrs_per_week_practical >= 2
            practicals = [
                s for s in year_subjects 
                if s.get('hrs_per_week_practical', 0) >= MIN_PRACTICAL_HOURS
            ]
            
            logger.info(f"Loaded {len(practicals)} practicals for {self.year}")
            return practicals
        except Exception as e:
            logger.error(f"Error loading practicals: {str(e)}")
            return []
    
    def _get_available_labs(self):
        """Get all available labs"""
        try:
            labs = list(labs_collection.find({}, {'_id': 0}))
            return labs
        except Exception as e:
            logger.error(f"Error loading labs: {str(e)}")
            return []
    
    def _get_all_faculties(self):
        """Get all faculties"""
        try:
            faculties = list(faculty_collection.find({}, {'_id': 1, 'name': 1}))
            return faculties
        except Exception as e:
            logger.error(f"Error loading faculties: {str(e)}")
            return []
    
    def _get_faculty_subjects_mapping(self, practicals):
        """Create mapping of faculty to subjects they can teach"""
        try:
            faculty_subjects = {}
            
            # Get all workloads
            workloads = list(workload_collection.find({}))
            
            # Get all faculties with their IDs
            faculties = list(faculty_collection.find({}, {'_id': 1, 'name': 1}))
            faculty_id_to_name = {str(f['_id']): f['name'] for f in faculties}
            
            # Build mapping from workload
            for workload in workloads:
                faculty_id = str(workload.get('faculty_id', ''))
                faculty_name = faculty_id_to_name.get(faculty_id)
                
                if not faculty_name:
                    continue
                
                # Get subjects this faculty teaches for this year
                year_subjects = workload.get('subjects', [])
                practical_subjects = [s for s in year_subjects if s.get('year') == self.year]
                
                if practical_subjects:
                    faculty_subjects[faculty_name] = practical_subjects
            
            logger.info(f"Faculty-Subject mapping: {faculty_subjects}")
            return faculty_subjects
            
        except Exception as e:
            logger.error(f"Error building faculty-subject mapping: {str(e)}")
            return {}
    
    def _get_classes_for_year(self):
        """Get class structure for this year"""
        try:
            class_struct = class_structure_collection.find_one({})
            if not class_struct:
                logger.error("No class structure found")
                return []
            
            year_key = self.year.lower()
            year_classes = class_struct.get(year_key, [])
            
            return year_classes
        except Exception as e:
            logger.error(f"Error loading class structure: {str(e)}")
            return []
    
    def _prepare_batch_assignments(self, practicals):
        """Split practicals into batches (1 hour each)"""
        batch_assignments = []
        year_classes = self._get_classes_for_year()
        
        if not year_classes:
            logger.error("No classes found for year")
            return []
        
        for practical in practicals:
            total_hrs = practical.get('hrs_per_week_practical', 0)
            num_batches = int(total_hrs)  # Each batch is 1 hour
            
            for class_info in year_classes:
                div = class_info['div']
                num_div_batches = class_info.get('batches', 1)
                
                for batch_num in range(1, num_div_batches + 1):
                    batch_assignments.append({
                        'subject': practical['short_name'],
                        'subject_full': practical['name'],
                        'class': self.year,
                        'division': div,
                        'batch': batch_num,
                        'hours': 1
                    })
        
        return batch_assignments
    
    def _initialize_timetable(self, labs):
        """Initialize empty timetable structure"""
        self.timetable = {
            'year': self.year,
            'semester': self.semester,
            'labs': {}
        }
        
        # Create structure for each lab
        for lab in labs:
            lab_name = lab.get('name', 'Unknown Lab')
            self.timetable['labs'][lab_name] = {}
            
            for day in DAYS:
                self.timetable['labs'][lab_name][day] = {
                    slot: [] for slot in SLOTS
                }
    
    def _backtrack_assign(self, batch_assignments, labs, faculties, faculty_subjects_map, index):
        """Backtracking algorithm to assign batches to slots"""
        
        # Base case: all batches assigned
        if index == len(batch_assignments):
            return self._validate_final_timetable()
        
        assignment = batch_assignments[index]
        
        # Try all possible combinations
        for day in DAYS:
            for slot in SLOTS:
                for lab in labs:
                    # Only try faculties who teach this subject for this year
                    for faculty in faculties:
                        faculty_name = faculty.get('name', '')
                        
                        # Check if faculty is qualified for this subject
                        if not self._is_faculty_qualified(faculty_name, assignment['subject_full'], faculty_subjects_map):
                            continue
                        
                        # Check if this assignment is valid
                        if self._is_valid_assignment(
                            assignment, day, slot, lab, faculty_name
                        ):
                            # Make assignment
                            self._make_assignment(
                                assignment, day, slot, lab, faculty_name
                            )
                            
                            # Recursively try next assignment
                            if self._backtrack_assign(
                                batch_assignments, labs, faculties, faculty_subjects_map, index + 1
                            ):
                                return True
                            
                            # Backtrack if failed
                            self._undo_assignment(assignment, day, slot, lab)
        
        return False
    
    def _is_valid_assignment(self, assignment, day, slot, lab, faculty_name):
        """Check if assignment is valid (no conflicts)"""
        
        # C1: No batch conflict - same batch can't have 2 practicals in same slot
        if self._has_batch_conflict(assignment, day, slot):
            return False
        
        # C2: No lab conflict - lab can't have 2 practicals in same slot
        if self._has_lab_conflict(lab, day, slot):
            return False
        
        # C3: No faculty conflict - faculty can't teach 2 batches in same slot
        if self._has_faculty_conflict(faculty_name, day, slot):
            return False
        
        return True
    
    def _has_batch_conflict(self, assignment, day, slot):
        """Check if batch already has practical in this slot"""
        class_key = assignment['class']
        div = assignment['division']
        batch = assignment['batch']
        
        # Check all labs for existing assignments
        for lab_name, lab_schedule in self.timetable['labs'].items():
            slot_assignments = lab_schedule[day][slot]
            for existing in slot_assignments:
                if (existing['class'] == class_key and 
                    existing['division'] == div and 
                    existing['batch'] == batch):
                    return True
        
        return False
    
    def _has_lab_conflict(self, lab, day, slot):
        """Check if lab is already occupied in this slot"""
        lab_name = lab.get('name', 'Unknown Lab')
        
        if lab_name in self.timetable['labs']:
            slot_assignments = self.timetable['labs'][lab_name][day][slot]
            return len(slot_assignments) > 0
        
        return False
    
    def _has_faculty_conflict(self, faculty_name, day, slot):
        """Check if faculty is already teaching in this slot"""
        for lab_name, lab_schedule in self.timetable['labs'].items():
            slot_assignments = lab_schedule[day][slot]
            for existing in slot_assignments:
                if existing['faculty'] == faculty_name:
                    return True
        
        return False
    
    def _is_faculty_qualified(self, faculty_name, subject_full, faculty_subjects_map):
        """Check if faculty is assigned to teach this subject"""
        if faculty_name not in faculty_subjects_map:
            return False
        
        # Check if this subject is in their workload
        faculty_workload = faculty_subjects_map[faculty_name]
        for workload_entry in faculty_workload:
            # The workload entry has year, class, practical_hrs, lec_hrs
            # We just check if the faculty has any workload for this year
            if workload_entry.get('year') == self.year:
                return True
        
        return False
    
    def _make_assignment(self, assignment, day, slot, lab, faculty_name):
        """Add assignment to timetable"""
        lab_name = lab.get('name', 'Unknown Lab')
        
        slot_entry = {
            'class': assignment['class'],
            'division': assignment['division'],
            'batch': assignment['batch'],
            'subject': assignment['subject'],
            'subject_full': assignment['subject_full'],
            'faculty': faculty_name
        }
        
        if lab_name in self.timetable['labs']:
            self.timetable['labs'][lab_name][day][slot].append(slot_entry)
        
        self.assignments.append({
            'assignment': assignment,
            'day': day,
            'slot': slot,
            'lab': lab_name,
            'faculty': faculty_name
        })
    
    def _undo_assignment(self, assignment, day, slot, lab):
        """Remove last assignment from timetable"""
        if self.assignments:
            self.assignments.pop()
        
        lab_name = lab.get('name', 'Unknown Lab')
        if lab_name in self.timetable['labs']:
            slot_list = self.timetable['labs'][lab_name][day][slot]
            if slot_list:
                slot_list.pop()
    
    def _validate_final_timetable(self):
        """Validate final timetable meets all constraints"""
        
        # Check all hard constraints are satisfied
        for lab_name, lab_schedule in self.timetable['labs'].items():
            for day in DAYS:
                for slot in SLOTS:
                    slot_assignments = lab_schedule[day][slot]
                    
                    # Ensure no duplicates or conflicts
                    if len(slot_assignments) > 1:
                        return False
        
        return True
    
    def save_to_database(self):
        """Save generated timetable to database"""
        try:
            # Prepare document
            doc = {
                'year': self.year,
                'semester': self.semester,
                'generated_at': datetime.now(),
                'schedule': self.timetable,
                'total_assignments': len(self.assignments)
            }
            
            # Delete existing timetable for this year/semester
            master_lab_timetable_collection.delete_many({
                'year': self.year,
                'semester': self.semester
            })
            
            # Insert new timetable
            result = master_lab_timetable_collection.insert_one(doc)
            logger.info(f"Timetable saved with ID: {result.inserted_id}")
            return result.inserted_id
            
        except Exception as e:
            logger.error(f"Error saving timetable to database: {str(e)}")
            return None


def generate(data):
    """Entry point for timetable generation"""
    year = data.get('year')
    semester = data.get('sem')
    
    if not year or not semester:
        logger.error("Missing year or semester")
        return None
    
    # Generate timetable
    generator = PracticalTimetableGenerator(year, semester)
    timetable = generator.generate()
    
    if timetable:
        # Save to database
        generator.save_to_database()
        return timetable
    
    return None