from datetime import datetime
from config import db
import logging
import random

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
            faculty_subjects_map = self._get_faculty_subjects_mapping()

            if not labs or not faculties or not faculty_subjects_map:
                logger.error("Missing labs, faculties, or faculty-subject mapping")
                logger.error(
                    f"Labs: {len(labs)}, Faculties: {len(faculties)}, Faculty-Subject Map: {len(faculty_subjects_map)}"
                )
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

            # Shuffle for fairer distribution
            random.shuffle(DAYS)
            random.shuffle(SLOTS)
            random.shuffle(labs)
            random.shuffle(faculties)

            # Phase 5: Backtracking assignment
            success = self._backtrack_assign(
                batch_assignments, labs, faculties, faculty_subjects_map, 0
            )

            if success:
                logger.info("Timetable generated successfully")
                return self.timetable
            else:
                logger.error("Failed to generate valid timetable - backtracking exhausted")
                return None

        except Exception as e:
            logger.error(f"Error generating timetable: {str(e)}", exc_info=True)
            return None

    # -------------------- DATA LOADING --------------------

    def _load_practicals(self):
        """Load practical subjects for this year"""
        try:
            subjects_doc = subjects_collection.find_one({})
            if not subjects_doc:
                logger.error("No subjects document found")
                return []

            year_key = self.year.lower()
            year_subjects = subjects_doc.get(year_key, [])

            practicals = [
                s for s in year_subjects if s.get("hrs_per_week_practical", 0) >= MIN_PRACTICAL_HOURS
            ]

            logger.info(f"Loaded {len(practicals)} practicals for {self.year}")
            return practicals
        except Exception as e:
            logger.error(f"Error loading practicals: {str(e)}")
            return []

    def _get_available_labs(self):
        """Get all available labs"""
        try:
            return list(labs_collection.find({}, {"_id": 0}))
        except Exception as e:
            logger.error(f"Error loading labs: {str(e)}")
            return []

    def _get_all_faculties(self):
        """Get all faculties"""
        try:
            return list(faculty_collection.find({}, {"_id": 1, "name": 1}))
        except Exception as e:
            logger.error(f"Error loading faculties: {str(e)}")
            return []

    def _get_faculty_subjects_mapping(self):
        """
        Build a mapping of faculty_name → list of subjects they teach (for this year).
        Works with the new workload structure (each doc = one subject entry).
        """
        try:
            faculty_subjects = {}
            workloads = list(workload_collection.find({}))

            faculties = list(faculty_collection.find({}, {"_id": 1, "name": 1}))
            faculty_id_to_name = {str(f["_id"]): f["name"] for f in faculties}

            for workload in workloads:
                faculty_id = str(workload.get("faculty_id", ""))
                faculty_name = faculty_id_to_name.get(faculty_id)
                if not faculty_name:
                    continue

                subject = workload.get("subject_full") or workload.get("subject")
                year = workload.get("year")

                if year == self.year:
                    if faculty_name not in faculty_subjects:
                        faculty_subjects[faculty_name] = []
                    faculty_subjects[faculty_name].append(subject)

            logger.info(f"Faculty-Subject mapping created for {len(faculty_subjects)} faculties")
            return faculty_subjects

        except Exception as e:
            logger.error(f"Error building faculty-subject mapping: {str(e)}")
            return {}

    # -------------------- ASSIGNMENT PREPARATION --------------------

    def _get_classes_for_year(self):
        """Get class structure for this year"""
        try:
            class_struct = class_structure_collection.find_one({})
            if not class_struct:
                logger.error("No class structure found")
                return []

            year_key = self.year.lower()
            return class_struct.get(year_key, [])
        except Exception as e:
            logger.error(f"Error loading class structure: {str(e)}")
            return []

    def _prepare_batch_assignments(self, practicals):
        """Create one assignment per batch-hour per subject"""
        batch_assignments = []
        year_classes = self._get_classes_for_year()

        if not year_classes:
            logger.error("No classes found for year")
            return []

        for practical in practicals:
            total_hrs = practical.get("hrs_per_week_practical", 0)
            for class_info in year_classes:
                div = class_info["div"]
                num_batches = class_info.get("batches", 1)
                for batch_num in range(1, num_batches + 1):
                    for _ in range(total_hrs):
                        batch_assignments.append({
                            "subject": practical["short_name"],
                            "subject_full": practical["name"],
                            "class": self.year,
                            "division": div,
                            "batch": batch_num,
                        })

        return batch_assignments

    def _initialize_timetable(self, labs):
        """Create empty timetable slots for each lab"""
        self.timetable = {
            "year": self.year,
            "semester": self.semester,
            "labs": {}
        }

        for lab in labs:
            lab_name = lab.get("name", "Unknown Lab")
            self.timetable["labs"][lab_name] = {
                day: {slot: [] for slot in SLOTS} for day in DAYS
            }

    # -------------------- CONFLICT CHECKS --------------------

    def _is_valid_assignment(self, assignment, day, slot, lab, faculty_name):
        """Ensure no conflicts before placing assignment"""
        return (
            not self._has_batch_conflict(assignment, day, slot)
            and not self._has_lab_conflict(lab, day, slot)
            and not self._has_faculty_conflict(faculty_name, day, slot)
        )

    def _has_batch_conflict(self, assignment, day, slot):
        """Batch cannot have 2 practicals at same time"""
        for lab_schedule in self.timetable["labs"].values():
            for existing in lab_schedule[day][slot]:
                if (
                    existing["class"] == assignment["class"]
                    and existing["division"] == assignment["division"]
                    and existing["batch"] == assignment["batch"]
                ):
                    return True
        return False

    def _has_lab_conflict(self, lab, day, slot):
        """Lab cannot host two batches at same time"""
        lab_name = lab.get("name", "Unknown Lab")
        return len(self.timetable["labs"][lab_name][day][slot]) > 0

    def _has_faculty_conflict(self, faculty_name, day, slot):
        """Faculty cannot teach multiple batches simultaneously"""
        for lab_schedule in self.timetable["labs"].values():
            for existing in lab_schedule[day][slot]:
                if existing["faculty"] == faculty_name:
                    return True
        return False

    def _is_faculty_qualified(self, faculty_name, subject_full, faculty_subjects_map):
        """Check if faculty can teach this subject"""
        return faculty_name in faculty_subjects_map and subject_full in faculty_subjects_map[faculty_name]

    # -------------------- ASSIGNMENT / BACKTRACKING --------------------

    def _backtrack_assign(self, batch_assignments, labs, faculties, faculty_subjects_map, index):
        """Recursive assignment generator"""
        if index == len(batch_assignments):
            return True  # all assigned

        assignment = batch_assignments[index]

        for day in DAYS:
            for slot in SLOTS:
                for lab in labs:
                    for faculty in faculties:
                        faculty_name = faculty.get("name", "")
                        if not self._is_faculty_qualified(faculty_name, assignment["subject_full"], faculty_subjects_map):
                            continue

                        if self._is_valid_assignment(assignment, day, slot, lab, faculty_name):
                            self._make_assignment(assignment, day, slot, lab, faculty_name)
                            if self._backtrack_assign(batch_assignments, labs, faculties, faculty_subjects_map, index + 1):
                                return True
                            self._undo_assignment(day, slot, lab)
        return False

    def _make_assignment(self, assignment, day, slot, lab, faculty_name):
        """Place assignment into timetable"""
        lab_name = lab.get("name", "Unknown Lab")
        self.timetable["labs"][lab_name][day][slot].append({
            "class": assignment["class"],
            "division": assignment["division"],
            "batch": assignment["batch"],
            "subject": assignment["subject"],
            "subject_full": assignment["subject_full"],
            "faculty": faculty_name,
        })
        self.assignments.append((lab_name, day, slot, assignment, faculty_name))

    def _undo_assignment(self, day, slot, lab):
        """Remove last placed assignment for backtracking"""
        lab_name = lab.get("name", "Unknown Lab")
        if self.timetable["labs"][lab_name][day][slot]:
            self.timetable["labs"][lab_name][day][slot].pop()
        if self.assignments:
            self.assignments.pop()

    # -------------------- SAVE TO DATABASE --------------------

    def save_to_database(self):
        """Save generated timetable to database (lab-wise format)"""
        try:
            lab_wise_schedule = self.timetable.get("labs", {})
            master_lab_timetable_collection.delete_many({"semester": self.semester})

            for lab_name, schedule in lab_wise_schedule.items():
                doc = {
                    "lab_name": lab_name,
                    "year": self.year,
                    "semester": self.semester,
                    "schedule": schedule,
                    "generated_at": datetime.now(),
                    "total_assignments": len(self.assignments),
                }
                master_lab_timetable_collection.insert_one(doc)

            logger.info(f"Saved {len(lab_wise_schedule)} lab-wise timetables successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving timetable to database: {str(e)}")
            return False


# -------------------- PUBLIC ENTRY FUNCTION --------------------

def generate(data):
    """Entry point for timetable generation"""
    year = data.get("year")
    semester = data.get("sem")

    if not year or not semester:
        logger.error("Missing year or semester")
        return None

    generator = PracticalTimetableGenerator(year, semester)
    timetable = generator.generate()

    if timetable:
        generator.save_to_database()
        return timetable

    return None
