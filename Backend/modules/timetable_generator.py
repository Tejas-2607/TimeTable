from datetime import datetime
from config import db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
SLOTS = ['11:15', '14:15', '16:20']
MIN_PRACTICAL_HOURS = 2

# Database collections
subjects_collection = db['subjects']
faculty_collection = db['faculty']
labs_collection = db['labs']
class_structure_collection = db['class_structure']
workload_collection = db['workload']
master_lab_timetable_collection = db['master_lab_timetable']


class PracticalTimetableGenerator:
    def __init__(self, year, semester):
        self.year = year
        self.semester = semester
        self.timetable = {}
        self.assignments = []

    def generate(self):
        """Main timetable generation logic"""
        try:
            logger.info(f"Generating timetable for {self.year} Sem {self.semester}")

            practicals = self._load_practicals()
            if not practicals:
                logger.warning(f"No practicals found for {self.year}")
                return None

            labs = self._get_available_labs()
            faculties = self._get_all_faculties()
            faculty_subjects_map = self._get_faculty_subjects_mapping(practicals)

            if not labs or not faculties or not faculty_subjects_map:
                logger.error("Missing labs, faculties, or workload data")
                return None

            batch_assignments = self._prepare_batch_assignments(practicals)
            if not batch_assignments:
                logger.warning("No batch assignments created")
                return None

            self._initialize_timetable(labs)
            success = self._backtrack_assign(batch_assignments, labs, faculties, faculty_subjects_map, 0)

            if success:
                logger.info(f"✅ Timetable generated successfully for {self.year}")
                return self.timetable
            else:
                logger.error("Failed to generate timetable after backtracking")
                return None

        except Exception as e:
            logger.error(f"Error generating timetable: {str(e)}", exc_info=True)
            return None

    # ---------- Helper Functions ----------
    def _load_practicals(self):
        try:
            subjects_doc = subjects_collection.find_one({})
            if not subjects_doc:
                return []

            year_subjects = subjects_doc.get(self.year.lower(), [])
            practicals = [s for s in year_subjects if s.get('hrs_per_week_practical', 0) >= MIN_PRACTICAL_HOURS]
            return practicals
        except Exception as e:
            logger.error(f"Error loading practicals: {str(e)}")
            return []

    def _get_available_labs(self):
        try:
            return list(labs_collection.find({}, {'_id': 0}))
        except Exception as e:
            logger.error(f"Error loading labs: {str(e)}")
            return []

    def _get_all_faculties(self):
        try:
            return list(faculty_collection.find({}, {'_id': 1, 'name': 1}))
        except Exception as e:
            logger.error(f"Error loading faculties: {str(e)}")
            return []

    def _get_faculty_subjects_mapping(self, practicals):
        try:
            faculty_subjects = {}
            workloads = list(workload_collection.find({}))
            faculties = list(faculty_collection.find({}, {'_id': 1, 'name': 1}))
            faculty_id_to_name = {str(f['_id']): f['name'] for f in faculties}

            for workload in workloads:
                faculty_id = str(workload.get('faculty_id', ''))
                faculty_name = faculty_id_to_name.get(faculty_id)
                if not faculty_name:
                    continue

                # Directly use subject from workload (not subjects list)
                subject_full = workload.get('subject_full')
                year = workload.get('year', '').upper()

                if year == self.year.upper() and subject_full:
                    if faculty_name not in faculty_subjects:
                        faculty_subjects[faculty_name] = []
                    faculty_subjects[faculty_name].append({
                        "subject_full": subject_full,
                        "year": year
                    })

            return faculty_subjects

        except Exception as e:
            logger.error(f"Error building faculty-subject mapping: {str(e)}")
            return {}

    def _get_classes_for_year(self):
        try:
            class_struct = class_structure_collection.find_one({})
            if not class_struct:
                return []

            year_key_map = {
                "SY": "SY",
                "TY": "TY",
                "BE": "Final Year"
            }

            key = year_key_map.get(self.year.upper())
            if not key or key not in class_struct:
                return []

            year_info = class_struct[key]
            num_divs = year_info.get('num_divisions', 1)
            batches_per_div = year_info.get('batches_per_division', 3)

            # Convert it to expected structure
            return [
                {"div": chr(65 + i), "batches": batches_per_div}
                for i in range(num_divs)
            ]
        except Exception as e:
            logger.error(f"Error loading class structure: {str(e)}")
            return []


    def _prepare_batch_assignments(self, practicals):
        batch_assignments = []
        year_classes = self._get_classes_for_year()
        if not year_classes:
            return []

        for practical in practicals:
            for class_info in year_classes:
                div = class_info['div']
                num_batches = class_info.get('batches', 1)
                for batch_num in range(1, num_batches + 1):
                    batch_assignments.append({
                        'subject': practical['short_name'],
                        'subject_full': practical['name'],
                        'class': self.year,
                        'division': div,
                        'batch': batch_num,
                        'hours': 2
                    })
        return batch_assignments

    def _initialize_timetable(self, labs):
        self.timetable = {'labs': {}}
        for lab in labs:
            lab_name = lab.get('name', 'Unknown Lab')
            self.timetable['labs'][lab_name] = {
                day: {slot: [] for slot in SLOTS} for day in DAYS
            }

    def _backtrack_assign(self, batch_assignments, labs, faculties, faculty_subjects_map, index):
        if index == len(batch_assignments):
            return self._validate_final_timetable()

        assignment = batch_assignments[index]
        for day in DAYS:
            for slot in SLOTS:
                for lab in labs:
                    for faculty in faculties:
                        faculty_name = faculty.get('name', '')
                        if not self._is_faculty_qualified(faculty_name, assignment['subject_full'], faculty_subjects_map):
                            continue
                        if self._is_valid_assignment(assignment, day, slot, lab, faculty_name):
                            self._make_assignment(assignment, day, slot, lab, faculty_name)
                            if self._backtrack_assign(batch_assignments, labs, faculties, faculty_subjects_map, index + 1):
                                return True
                            self._undo_assignment(assignment, day, slot, lab)
        return False

    def _is_valid_assignment(self, assignment, day, slot, lab, faculty_name):
        return (
            not self._has_batch_conflict(assignment, day, slot)
            and not self._has_lab_conflict(lab, day, slot)
            and not self._has_faculty_conflict(faculty_name, day, slot)
        )

    def _has_batch_conflict(self, assignment, day, slot):
        for lab_name, lab_schedule in self.timetable['labs'].items():
            for existing in lab_schedule[day][slot]:
                if (
                    existing['class'] == assignment['class']
                    and existing['division'] == assignment['division']
                    and existing['batch'] == assignment['batch']
                ):
                    return True
        return False

    def _has_lab_conflict(self, lab, day, slot):
        lab_name = lab.get('name', 'Unknown Lab')
        return len(self.timetable['labs'][lab_name][day][slot]) > 0

    def _has_faculty_conflict(self, faculty_name, day, slot):
        for lab_schedule in self.timetable['labs'].values():
            for existing in lab_schedule[day][slot]:
                if existing['faculty'] == faculty_name:
                    return True
        return False

    def _is_faculty_qualified(self, faculty_name, subject_full, faculty_subjects_map):
        if faculty_name not in faculty_subjects_map:
            return False
        for workload_entry in faculty_subjects_map[faculty_name]:
            if workload_entry.get('year') == self.year:
                return True
        return False

    def _make_assignment(self, assignment, day, slot, lab, faculty_name):
        lab_name = lab.get('name', 'Unknown Lab')
        self.timetable['labs'][lab_name][day][slot].append({
            'class': assignment['class'],
            'division': assignment['division'],
            'batch': assignment['batch'],
            'subject': assignment['subject'],
            'subject_full': assignment['subject_full'],
            'faculty': faculty_name
        })
        self.assignments.append({
            'day': day,
            'slot': slot,
            'lab': lab_name,
            'faculty': faculty_name
        })

    def _undo_assignment(self, assignment, day, slot, lab):
        lab_name = lab.get('name', 'Unknown Lab')
        if self.timetable['labs'][lab_name][day][slot]:
            self.timetable['labs'][lab_name][day][slot].pop()

    def _validate_final_timetable(self):
        for lab_schedule in self.timetable['labs'].values():
            for day in DAYS:
                for slot in SLOTS:
                    if len(lab_schedule[day][slot]) > 1:
                        return False
        return True


# ---------- UNIFIED GENERATOR FUNCTION ----------
def generate(data=None):
    """
    Unified lab-wise timetable generator.
    Generates and stores timetable for all years together.
    """
    try:
        master_lab_timetable_collection.delete_many({})
        years = ['SY', 'TY', 'BE']
        merged_timetable = {'labs': {}}

        for year in years:
            generator = PracticalTimetableGenerator(year, '1')
            timetable = generator.generate()
            if timetable and 'labs' in timetable:
                for lab_name, schedule in timetable['labs'].items():
                    if lab_name not in merged_timetable['labs']:
                        merged_timetable['labs'][lab_name] = schedule
                    else:
                        for day, slots in schedule.items():
                            for time, sessions in slots.items():
                                merged_timetable['labs'][lab_name][day][time].extend(sessions)

        # Save lab-wise only (no year or sem)
        for lab_name, schedule in merged_timetable['labs'].items():
            master_lab_timetable_collection.insert_one({
                'lab_name': lab_name,
                'schedule': schedule,
                'generated_at': datetime.now()
            })

        logger.info("✅ Unified lab-wise timetable generated for all years.")
        return merged_timetable

    except Exception as e:
        logger.error(f"Error generating unified timetable: {str(e)}", exc_info=True)
        return None
