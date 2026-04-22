# timetable_generator.py
from datetime import datetime
from config import db
import logging
from collections import defaultdict
from bson import ObjectId

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from modules import settings_handler

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

workload_collection = db['workload']
faculty_collection = db['faculty']
subjects_collection = db['subjects']
master_lab_timetable_collection = db['master_lab_timetable']
constraints_collection = db['constraints']
labs_collection = db['labs']

class TimetableGenerator:
    def __init__(self):
        timings = settings_handler.get_timings()
        all_s, lec_s, brk_s = settings_handler.calculate_slots(timings)
        self.ALL_LECTURE_SLOTS = lec_s
        self.BREAK_SLOTS = brk_s
        self.ALL_SLOTS = all_s
        
        # Build adjacent slots map for duration checking
        self.NEXT_SLOT = {}
        for i in range(len(all_s)-1):
            self.NEXT_SLOT[all_s[i]] = all_s[i+1]

        self.lab_schedule = {} # lab_name -> day -> slot -> list of sessions
        self.labs_list = []
        self.faculty_names = {}
        self.faculty_full_names = {}
        self.constraints = []
        self.subject_map = {}

    def _load_labs(self):
        labs = list(labs_collection.find({}))
        self.labs_list = labs
        for lab in labs:
            lname = lab.get('lab_name') or lab.get('name')
            self.lab_schedule[lname] = {day: {slot: [] for slot in self.ALL_SLOTS} for day in DAYS}
        logger.info(f"✓ Loaded {len(labs)} labs")

    def _load_faculty_names(self):
        for f in faculty_collection.find({}, {'_id': 1, 'short_name': 1, 'name': 1}):
            fid = str(f['_id'])
            self.faculty_names[fid] = f.get('short_name') or f.get('name')
            self.faculty_full_names[fid] = f.get('name')
        logger.info(f"✓ Loaded faculty names")

    def _load_constraints(self):
        self.constraints = list(constraints_collection.find({}))
        logger.info(f"✓ Loaded {len(self.constraints)} constraints")

    def _load_subject_map(self):
        doc = subjects_collection.find_one({})
        if not doc: return
        from modules.class_structure_handler import get_active_years_list
        years = [y.lower() for y in get_active_years_list()]
        for yr in years:
            for subj in doc.get(yr, []) or doc.get(yr.upper(), []):
                sname = subj.get('short_name', '')
                if sname:
                    self.subject_map[sname] = subj
        logger.info(f"✓ Loaded subject map")

    def _prepare_assignments(self):
        """
        Group assignments by (year, division, subject).
        Returns: { (year, div): { subject: [session_list_for_all_batches] } }
        """
        assignments = {}
        workloads = list(workload_collection.find({}))
        
        for w in workloads:
            prac_hrs = w.get('practical_hrs', 0)
            if prac_hrs <= 0: continue
            
            subj_name = w.get('subject', '')
            subj_doc = self.subject_map.get(subj_name, {})
            duration = int(subj_doc.get('practical_duration', 2))
            sessions_per_week = int(subj_doc.get('hrs_per_week_practical', 1))

            year = w.get('year', '').upper()
            div = w.get('division', 'A')
            batches = w.get('batches', [])
            f_id = str(w.get('faculty_id', ''))
            f_name = self.faculty_names.get(f_id, f_id)
            f_full = self.faculty_full_names.get(f_id, f_name)

            class_key = (year, div)
            if class_key not in assignments: assignments[class_key] = {}
            if subj_name not in assignments[class_key]: assignments[class_key][subj_name] = []

            for b in batches:
                batch_label = b if b.startswith('Batch') else f"Batch {b}"
                for s_idx in range(sessions_per_week):
                    assignments[class_key][subj_name].append({
                        'subject': subj_name,
                        'subject_full': w.get('subject_full', subj_name),
                        'faculty': f_name,
                        'faculty_full': f_full,
                        'faculty_id': f_id,
                        'batch': batch_label,
                        'duration': duration,
                        'year': year,
                        'division': div,
                        'session_id': f"{subj_name}_{batch_label}_{s_idx}"
                    })
        return assignments

    def _faculty_busy(self, faculty, day, slot):
        for lab in self.lab_schedule:
            for sess in self.lab_schedule[lab][day][slot]:
                if sess.get('faculty') == faculty:
                    return True
        return False

    def _batch_busy(self, year, div, batch, day, slot):
        for lab in self.lab_schedule:
            for sess in self.lab_schedule[lab][day][slot]:
                if sess.get('year') == year and sess.get('division') == div and sess.get('batch') == batch:
                    return True
        return False

    def _can_place_synchronized(self, class_key, subject, sessions, day, slot):
        """
        Check if ALL batches of a subject can be placed at the same time in different labs.
        """
        if not sessions: return None
        
        duration = sessions[0]['duration']
        slots_needed = [slot]
        curr = slot
        for _ in range(duration - 1):
            if curr not in self.NEXT_SLOT: return None
            curr = self.NEXT_SLOT[curr]
            if curr in self.BREAK_SLOTS: return None
            slots_needed.append(curr)

        # Group sessions by batch
        batch_sessions = defaultdict(list)
        for s in sessions:
            batch_sessions[s['batch']].append(s)
        
        # We only take ONE session per batch for this synchronization
        to_place = []
        for b in batch_sessions:
            to_place.append(batch_sessions[b][0])

        # Check Faculty/Batch availability for all
        for s_entry in to_place:
            for sl in slots_needed:
                if self._faculty_busy(s_entry['faculty'], day, sl): return None
                if self._batch_busy(s_entry['year'], s_entry['division'], s_entry['batch'], day, sl): return None

        # Lab Allocation (find a unique lab for each batch)
        allocation = {} # batch -> lab_name
        used_labs = set()
        
        for s_entry in to_place:
            found_lab = None
            subj_doc = self.subject_map.get(s_entry['subject'], {})
            req_type = subj_doc.get('practical_type')
            req_lab  = subj_doc.get('required_labs')

            # Pass 1: Try required lab
            for lab in self.labs_list:
                lname = lab.get('lab_name') or lab.get('name')
                if lname in used_labs: continue
                
                if req_type == "Specific Lab" and req_lab and lname != req_lab: continue
                if req_type and req_type not in ["Specific Lab", "Common Lab", "None"] and req_type not in lname:
                    continue
                
                free = True
                for sl in slots_needed:
                    if self.lab_schedule[lname][day][sl]:
                        free = False; break
                if free:
                    found_lab = lname; break
            
            # Pass 2: Fallback (Highly important for synchronization)
            if not found_lab:
                for lab in self.labs_list:
                    lname = lab.get('lab_name') or lab.get('name')
                    if lname in used_labs: continue
                    free = True
                    for sl in slots_needed:
                        if self.lab_schedule[lname][day][sl]:
                            free = False; break
                    if free:
                        found_lab = lname; break

            if found_lab:
                allocation[s_entry['batch']] = found_lab
                used_labs.add(found_lab)
            else:
                return None # No lab available
        
        return {
            'sessions': to_place,
            'allocation': allocation,
            'slots': slots_needed
        }

    def _write_synchronized(self, placement, day):
        for s_entry in placement['sessions']:
            lab = placement['allocation'][s_entry['batch']]
            entry = {
                'subject': s_entry['subject'],
                'subject_full': s_entry['subject_full'],
                'faculty': s_entry['faculty'],
                'faculty_id': s_entry['faculty_id'],
                'batch': s_entry['batch'],
                'class': s_entry['year'],
                'division': s_entry['division'],
                'type': 'practical'
            }
            for sl in placement['slots']:
                self.lab_schedule[lab][day][sl].append(entry)

    def generate(self):
        logger.info("Starting synchronized practical timetable generation...")
        try:
            self._load_labs()
            self._load_faculty_names()
            self._load_subject_map()
            self._load_constraints()
            
            class_assignments = self._prepare_assignments()
            if not class_assignments:
                return {'success': False, 'error': 'No assignments found'}
            
            scheduled_count = 0
            class_days_busy = defaultdict(set)

            # Practicals prioritized in slots from 14:00 onwards
            PREFERRED_START_SLOTS = sorted(self.ALL_LECTURE_SLOTS, reverse=True) 

            for pass_num in range(5):
                progress = False
                # Iterate DAYS first to evenly distribute across the week
                for day in DAYS:
                    for slot in PREFERRED_START_SLOTS:
                        if slot in self.BREAK_SLOTS: continue
                        
                        # Iterate through classes
                        for class_key in sorted(class_assignments.keys()):
                            if day in class_days_busy[class_key]: 
                                continue # One practical per day rule
                            
                            subject_map = class_assignments[class_key]
                            for subj in sorted(subject_map.keys()):
                                sessions = subject_map[subj]
                                if not sessions: continue
                                
                                placement = self._can_place_synchronized(class_key, subj, sessions, day, slot)
                                if placement:
                                    self._write_synchronized(placement, day)
                                    for s_placed in placement['sessions']:
                                        for i, s_in_queue in enumerate(subject_map[subj]):
                                            if s_in_queue['session_id'] == s_placed['session_id']:
                                                subject_map[subj].pop(i)
                                                break
                                    
                                    scheduled_count += len(placement['sessions'])
                                    class_days_busy[class_key].add(day)
                                    progress = True
                                    break # Move to next class
                if not progress: break

            # Save
            master_lab_timetable_collection.delete_many({})
            for lab_name, schedule in self.lab_schedule.items():
                master_lab_timetable_collection.insert_one({
                    'lab_name': lab_name,
                    'schedule': schedule,
                    'generated_at': datetime.now()
                })
            
            leftovers_map = {}
            for ck, sm in class_assignments.items():
                total = sum(len(v) for v in sm.values())
                if total > 0:
                    leftovers_map[f"{ck[0]}-{ck[1]}"] = total

            logger.info(f"DONE: {scheduled_count} scheduled. Leftovers: {leftovers_map}")
            return {'success': True, 'practicals_scheduled': scheduled_count, 'leftovers': leftovers_map}
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

def generate():
    return TimetableGenerator().generate()