# lecture_tt_generator.py
from datetime import datetime
from config import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from modules import settings_handler

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

workload_collection        = db['workload']
faculty_collection         = db['faculty']
subjects_collection        = db['subjects']
class_timetable_collection = db['class_timetable']
constraints_collection     = db['constraints']

class LectureTimetableGenerator:
    def __init__(self):
        timings = settings_handler.get_timings()
        all_s, lec_s, brk_s = settings_handler.calculate_slots(timings)
        self.ALL_LECTURE_SLOTS = lec_s
        self.BREAK_SLOTS = brk_s
        self.ALL_SLOTS = all_s
        self.class_timetables = {}
        self.subject_map = {}
        self.constraints = []

    def _load_class_timetables(self):
        for tt in class_timetable_collection.find({}):
            key = (tt['class'], tt['division'])
            self.class_timetables[key] = tt

    def _load_subject_map(self):
        doc = subjects_collection.find_one({})
        if not doc: return
        from modules.class_structure_handler import get_active_years_list
        years = [y.lower() for y in get_active_years_list()]
        for yr in years:
            for s in doc.get(yr, []) or doc.get(yr.upper(), []):
                if s.get('short_name'): self.subject_map[s['short_name']] = s

    def _load_constraints(self):
        self.constraints = list(constraints_collection.find({}))

    def prepare_lecture_assignments(self):
        assignments = {}
        faculties = list(faculty_collection.find({}, {'_id': 1, 'name': 1, 'short_name': 1}))
        fid_to_name = {str(f['_id']): f.get('short_name') or f.get('name') for f in faculties}
        fid_to_full = {str(f['_id']): f.get('name') for f in faculties}
        
        workloads = list(workload_collection.find({}))
        for w in workloads:
            subj_name = w.get('subject', '')
            subj_doc = self.subject_map.get(subj_name, {})
            theory_hrs = int(subj_doc.get('hrs_per_week_lec', 0))
            if theory_hrs == 0: continue
            
            f_id = str(w.get('faculty_id', ''))
            f_name = fid_to_name.get(f_id, f_id)
            f_full = fid_to_full.get(f_id, f_id)
            
            key = (w['year'].upper(), w.get('division', 'A'), subj_name)
            if key not in assignments: assignments[key] = []
            
            for n in range(theory_hrs):
                assignments[key].append({
                    'subject': subj_name,
                    'subject_full': w.get('subject_full', subj_name),
                    'faculty': f_name,
                    'faculty_full': f_full,
                    'faculty_id': f_id,
                    'lecture_number': len(assignments[key]) + 1
                })
        return assignments

    def _faculty_busy(self, faculty, day, slot):
        for tt in self.class_timetables.values():
            for sess in tt.get('schedule', {}).get(day, {}).get(slot, []):
                if sess.get('faculty') == faculty: return True
        for c in self.constraints:
            if c.get('type') == 'preferred_off' and c.get('faculty_name') == faculty:
                if c.get('day') == day and c.get('time_slot') == slot: return True
        return False

    def _slot_free(self, yr, div, day, slot):
        key = (yr, div)
        if key not in self.class_timetables: return False
        return len(self.class_timetables[key]['schedule'].get(day, {}).get(slot, [])) == 0

    def _subject_on_day(self, yr, div, day, subject):
        tt = self.class_timetables.get((yr, div))
        if not tt: return False
        for sess_list in tt['schedule'].get(day, {}).values():
            for s in sess_list:
                if s.get('type') == 'lecture' and s.get('subject') == subject: return True
        return False

    def _consecutive_ok(self, yr, div, day, slot, subject):
        tt = self.class_timetables.get((yr, div))
        if not tt: return True
        idx = self.ALL_LECTURE_SLOTS.index(slot)
        adj = []
        if idx > 0: adj.append(self.ALL_LECTURE_SLOTS[idx-1])
        if idx < len(self.ALL_LECTURE_SLOTS)-1: adj.append(self.ALL_LECTURE_SLOTS[idx+1])
        for a in adj:
            for s in tt['schedule'].get(day, {}).get(a, []):
                if s.get('subject') == subject: return False
        return True

    def _place_lecture(self, yr, div, day, slot, lecture):
        self.class_timetables[(yr, div)]['schedule'].setdefault(day, {}).setdefault(slot, []).append({
            'subject': lecture['subject'],
            'subject_full': lecture['subject_full'],
            'faculty': lecture['faculty'],
            'faculty_id': lecture['faculty_id'],
            'type': 'lecture',
            'hours': 1
        })

    def generate(self):
        try:
            self._load_class_timetables()
            self._load_subject_map()
            self._load_constraints()
            assignments = self.prepare_lecture_assignments()
            scheduled_count = 0

            # Phase 0: Fixed Time
            for c in self.constraints:
                if c.get('type') == 'fixed_time':
                    day, slot = c['day'], c['time_slot']
                    yr, div = c['year'], c['division']
                    subj, fac = c['subject'], c['faculty_name']
                    
                    key = (yr, div, subj)
                    if key in assignments and assignments[key]:
                        found_idx = None
                        for i, l in enumerate(assignments[key]):
                            if l['faculty'] == fac or l.get('faculty_full') == fac:
                                found_idx = i; break
                        if found_idx is not None and self._slot_free(yr, div, day, slot) and not self._faculty_busy(fac, day, slot):
                            lec = assignments[key].pop(found_idx)
                            self._place_lecture(yr, div, day, slot, lec)
                            scheduled_count += 1
                            logger.info(f"  📌 FIXED: {yr}-{div} {subj} @ {day} {slot}")

            # Phase 1: Loops
            from modules.class_structure_handler import get_active_years_list
            years = [y.upper() for y in get_active_years_list()]
            year_order = {yr: i for i, yr in enumerate(years)}

            for pass_num in range(10):
                progress = False
                for day in DAYS:
                    for slot in self.ALL_LECTURE_SLOTS:
                        if slot in self.BREAK_SLOTS: continue
                        
                        sorted_keys = sorted([k for k in assignments if assignments[k]], 
                                            key=lambda x: (year_order.get(x[0], 9), x[1], x[2]))
                        for yr, div, subj in sorted_keys:
                            queue = assignments[(yr, div, subj)]
                            if not queue: continue
                            lec = queue[0]
                            
                            if self._slot_free(yr, div, day, slot) and \
                               not self._faculty_busy(lec['faculty'], day, slot) and \
                               not self._subject_on_day(yr, div, day, subj) and \
                               self._consecutive_ok(yr, div, day, slot, subj):
                                
                                self._place_lecture(yr, div, day, slot, lec)
                                queue.pop(0)
                                scheduled_count += 1
                                progress = True
                if not progress: break

            # Save
            for (yr, div), tt in self.class_timetables.items():
                tt['generated_at'] = datetime.now()
                class_timetable_collection.replace_one({'class': yr, 'division': div}, tt, upsert=True)
            
            leftovers = {f"{k[0]}-{k[1]}-{k[2]}": len(v) for k,v in assignments.items() if v}
            return {'success': True, 'lectures_scheduled': scheduled_count, 'leftovers': leftovers}
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

def generate():
    return LectureTimetableGenerator().generate()