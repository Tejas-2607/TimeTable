# timetable_generator.py


from datetime import datetime
from config import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from modules import class_structure_handler, settings_handler

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
# Removing static ALL_SLOTS, START_SLOTS, NEXT_SLOT, TWO_HR_START_SLOTS as they are now dynamic

subjects_collection             = db['subjects']
faculty_collection              = db['faculty']
workload_collection             = db['workload']
labs_collection                 = db['labs']
master_lab_timetable_collection = db['master_lab_timetable']
constraints_collection         = db['constraints']


def _normalise_batch(raw) -> int:
    if isinstance(raw, int):
        return raw
    s = str(raw).replace('Batch', '').strip()
    try:
        return int(s)
    except ValueError:
        return 1


class TimetableGenerator:

    def __init__(self):
        # ── Dynamic Timings ──────────────────────────────────────────────────
        timings = settings_handler.get_timings()
        all_s, lec_s, brk_s = settings_handler.calculate_slots(timings)
        
        self.ALL_SLOTS   = all_s
        self.BREAK_SLOTS = brk_s
        
        # START_SLOTS for 2-hr practicals: slots where the NEXT slot is also a lecture slot
        self.TWO_HR_START_SLOTS = []
        self.NEXT_SLOT = {}
        for i in range(len(all_s) - 1):
            if all_s[i] in lec_s and all_s[i+1] in lec_s:
                self.TWO_HR_START_SLOTS.append(all_s[i])
                self.NEXT_SLOT[all_s[i]] = all_s[i+1]
        
        # All possible start slots for any practical
        self.START_SLOTS = lec_s
        
        # ── State ───────────────────────────────────────────────────────────
        self.lab_schedule   = {}   # lab_name → day → slot → [sessions]
        self.batch_occupied = {}   # (year, div, batch) → day → slot → bool
        self.faculty_names  = {}
        self.labs_list      = []
        self.subject_map    = {}   # short_name → subject doc
        self.constraints    = []

    # ── Data loading ─────────────────────────────────────────────────────────

    def _load_faculty_names(self):
        for f in faculty_collection.find({}, {'_id': 1, 'name': 1, 'short_name': 1}):
            self.faculty_names[str(f['_id'])] = f.get('short_name') or f.get('name', '')
        logger.info(f"✓ Loaded {len(self.faculty_names)} faculty")

    def _load_subject_map(self):
        doc = subjects_collection.find_one({})
        if not doc:
            return
        from modules.class_structure_handler import get_active_years_list
        years = [y.lower() for y in get_active_years_list()]
        for yr in years:
            for subj in doc.get(yr, []) or doc.get(yr.upper(), []):
                sname = subj.get('short_name', '')
                if sname:
                    self.subject_map[sname] = subj
        logger.info(f"✓ Loaded {len(self.subject_map)} subjects")

    def _load_labs(self):
        labs = list(labs_collection.find({}))
        self.labs_list = [lab['name'] for lab in labs if lab.get('name')]
        for lab_name in self.labs_list:
            self.lab_schedule[lab_name] = {
                day: {slot: [] for slot in self.ALL_SLOTS}
                for day in DAYS
            }
        logger.info(f"✓ Loaded {len(self.labs_list)} labs")

    def _load_constraints(self):
        self.constraints = list(constraints_collection.find({}))
        logger.info(f"✓ Loaded {len(self.constraints)} special constraints")

    def _ensure_batch(self, year, division, batch):
        key = (year, division, batch)
        if key not in self.batch_occupied:
            self.batch_occupied[key] = {
                day: {slot: False for slot in self.ALL_SLOTS}
                for day in DAYS
            }

    # ── Assignment preparation ────────────────────────────────────────────────

    def prepare_assignments(self) -> dict:
        assignments: dict = {}
        try:
            self._load_faculty_names()
            self._load_subject_map()
            workloads = list(workload_collection.find({}))
            logger.info(f"Reading {len(workloads)} workload entries…")

            for w in workloads:
                year         = (w.get('year') or '').strip().upper()
                division     = w.get('division', 'A')
                batches_raw  = w.get('batches', [1])
                subject      = w.get('subject', '')
                subject_full = w.get('subject_full', subject)
                faculty_id   = str(w.get('faculty_id', '')) if w.get('faculty_id') else ''
                faculty_name = self.faculty_names.get(faculty_id, faculty_id)

                subj_doc       = self.subject_map.get(subject, {})
                practical_hrs  = int(subj_doc.get('practical_duration',
                                     w.get('practical_hrs', 2)))
                practical_type = subj_doc.get('practical_type', 'Common Lab')
                required_lab   = (subj_doc.get('required_labs')
                                  if practical_type == 'Specific Lab' else None)

                for raw_batch in batches_raw:
                    batch = _normalise_batch(raw_batch)
                    self._ensure_batch(year, division, batch)
                    key = (year, division, batch)
                    assignments.setdefault(key, []).append({
                        'subject':       subject,
                        'subject_full':  subject_full,
                        'batch':         batch,
                        'faculty_id':    faculty_id,
                        'faculty':       faculty_name,
                        'year':          year,
                        'division':      division,
                        'practical_hrs': practical_hrs,
                        'required_lab':  required_lab,
                    })

            total = sum(len(v) for v in assignments.values())
            logger.info(f"✓ {len(assignments)} batch-queues, {total} practicals to schedule")
            for k in sorted(assignments):
                logger.info(f"   {k[0]}-{k[1]}-B{k[2]}: "
                            f"{[p['subject'] for p in assignments[k]]}")
            return assignments

        except Exception as e:
            logger.error(f"prepare_assignments error: {e}", exc_info=True)
            return {}

    # ── Constraint helpers ────────────────────────────────────────────────────

    def _faculty_busy(self, faculty: str, day: str, slot: str) -> bool:
        for lab_sched in self.lab_schedule.values():
            for sess in lab_sched.get(day, {}).get(slot, []):
                if sess.get('faculty') == faculty:
                    return True
        
        # Check special constraints (preferred_off)
        for c in self.constraints:
            if c.get('type') == 'preferred_off' and c.get('faculty_name') == faculty:
                if c.get('day') == day and c.get('time_slot') == slot:
                    return True
        return False

    def _batch_slot_free(self, year, division, batch, day, slot) -> bool:
        key = (year, division, batch)
        if key not in self.batch_occupied:
            return True
        return not self.batch_occupied[key][day][slot]

    def _lab_slot_free(self, lab: str, day: str, slot: str) -> bool:
        return len(self.lab_schedule.get(lab, {}).get(day, {}).get(slot, [])) == 0

    def _select_lab(self, practical: dict, day: str, slot: str,
                    used_labs: set) -> str | None:
        hrs       = practical['practical_hrs']
        next_slot = self.NEXT_SLOT.get(slot) if hrs == 2 else None
        required  = practical.get('required_lab')
        
        # If a specific lab is required, only consider that one
        if required:
            candidates = [required]
        else:
            candidates = self.labs_list

        for lab in candidates:
            if not lab:
                continue
            
            # Normalize for matching if needed, but here we expect EXACT match 
            # with self.lab_schedule keys. We'll add a helper to be sure.
            if lab not in self.lab_schedule:
                # Try finding case-insensitively
                found_lab = None
                for real_lab in self.lab_schedule.keys():
                    if real_lab.strip().upper() == lab.strip().upper():
                        found_lab = real_lab
                        break
                if found_lab:
                    lab = found_lab
                else:
                    logger.warning(f"  ⚠️ Required lab '{lab}' not found in registered labs!")
                    continue
            if lab in used_labs:
                continue
            if not self._lab_slot_free(lab, day, slot):
                continue
            if next_slot and not self._lab_slot_free(lab, day, next_slot):
                continue
            return lab
        return None

    def _can_schedule(self, practical: dict, day: str, slot: str,
                      used_faculty: set, used_labs: set) -> bool:
        year, division, batch = practical['year'], practical['division'], practical['batch']
        faculty, hrs          = practical['faculty'], practical['practical_hrs']
        
        if hrs == 2 and slot not in self.TWO_HR_START_SLOTS:
            return False
        if faculty in used_faculty:
            return False
        if self._faculty_busy(faculty, day, slot):
            return False
        if not self._batch_slot_free(year, division, batch, day, slot):
            return False
        if hrs == 2:
            if not self._batch_slot_free(year, division, batch, day, self.NEXT_SLOT[slot]):
                return False
        
        # Check special constraints (fixed_time for OTHER subjects/faculty)
        for c in self.constraints:
            if c.get('type') == 'fixed_time':
                if c.get('day') == day and c.get('time_slot') == slot:
                    # If this slot is fixed for someone else, we can't schedule here
                    if c.get('year') == year and c.get('division') == division:
                        if c.get('subject') != practical['subject'] or c.get('faculty_name') != faculty:
                            return False
                    if c.get('faculty_name') == faculty and c.get('subject') != practical['subject']:
                        return False

        if self._select_lab(practical, day, slot, used_labs) is None:
            return False
        return True

    # ── Write ─────────────────────────────────────────────────────────────────

    def _write_session(self, practical: dict, day: str, slot: str, lab: str):
        """
        Writes to lab_schedule and batch_occupied ONLY.
        class_timetable_handler reads from master lab timetable (saved at end)
        and is the sole writer for class-level timetables — preventing duplicates.
        """
        year, division, batch = practical['year'], practical['division'], practical['batch']
        hrs = practical['practical_hrs']

        session = {
            'batch':        f"Batch {batch}",
            'subject':      practical['subject'],
            'subject_full': practical['subject_full'],
            'faculty':      practical['faculty'],
            'faculty_id':   practical['faculty_id'] or None,
            'division':     division,
            'class':        year,
        }

        # Lab timetable — primary slot
        self.lab_schedule[lab][day][slot].append(dict(session))
        # Lab timetable — follow-on slot (for 2-hr practicals)
        if hrs == 2 and slot in self.NEXT_SLOT:
            self.lab_schedule[lab][day][self.NEXT_SLOT[slot]].append(dict(session))

        # Mark this batch occupied at both slots
        key = (year, division, batch)
        self.batch_occupied[key][day][slot] = True
        if hrs == 2 and slot in self.NEXT_SLOT:
            self.batch_occupied[key][day][self.NEXT_SLOT[slot]] = True
        
        extra = f"+{self.NEXT_SLOT[slot]}" if hrs == 2 and slot in self.NEXT_SLOT else ""
        logger.info(f"  ✓ {year}-{division}-B{batch} {practical['subject']} "
                    f"→ {lab} @ {day} {slot}{extra}")

    # ── Main loop ─────────────────────────────────────────────────────────────

    def generate(self) -> dict:
        logger.info("=" * 80)
        logger.info("STARTING PRACTICAL TIMETABLE GENERATION")
        logger.info("=" * 80)

        try:
            self._load_labs()
            self._load_constraints()
            assignments = self.prepare_assignments()

            if not assignments:
                return {'success': False, 'error': 'No assignments found'}
            if not self.labs_list:
                return {'success': False, 'error': 'No labs found'}

            scheduled_count = 0
            
            # --- PHASE 0: Process Fixed Time Constraints ---
            for c in self.constraints:
                if c.get('type') == 'fixed_time':
                    day = c.get('day')
                    slot = c.get('time_slot')
                    year = c.get('year')
                    division = c.get('division')
                    subject = c.get('subject')
                    faculty = c.get('faculty_name')

                    # Find matching practical assignment
                    key = (year, division, 1) # Simplification: assume batch 1 for fixed lecture/practical pins if not specified
                    # Actually, better match accurately if possible. 
                    # For now, let's find the first matching subject in ANY batch of that class
                    target_key = None
                    target_idx = None
                    for k, queue in assignments.items():
                        if k[0] == year and k[1] == division:
                            for idx, p in enumerate(queue):
                                if p['subject'] == subject and p['faculty'] == faculty:
                                    target_key = k
                                    target_idx = idx
                                    break
                        if target_key: break
                    
                    if target_key:
                        practical = assignments[target_key][target_idx]
                        # Try to schedule at the fixed slot
                        lab = self._select_lab(practical, day, slot, set()) # No labs used yet in Phase 0
                        if lab:
                            self._write_session(practical, day, slot, lab)
                            assignments[target_key].pop(target_idx)
                            scheduled_count += 1
                            logger.info(f"  📌 Scheduled FIXED constraint: {year}-{division} {subject} at {day} {slot}")

            from modules.class_structure_handler import get_active_years_list
            years = [y.upper() for y in get_active_years_list()]
            year_order = {yr: idx for idx, yr in enumerate(years)}

            for pass_num in range(30):
                progress = False
                
                for day in DAYS:
                    for slot in self.START_SLOTS:
                        sorted_keys = sorted(
                            [k for k in assignments if assignments[k]],
                            key=lambda k: (year_order.get(k[0], 9), k[1], k[2])
                        )

                        used_faculty : set = set()
                        used_labs    : set = set()

                        for key in sorted_keys:
                            queue = assignments[key]
                            if not queue:
                                continue

                            placed_idx = None
                            for idx, practical in enumerate(queue):
                                if not self._can_schedule(practical, day, slot,
                                                          used_faculty, used_labs):
                                    continue
                                lab = self._select_lab(practical, day, slot, used_labs)
                                if lab is None:
                                    continue

                                used_faculty.add(practical['faculty'])
                                used_labs.add(lab)
                                self._write_session(practical, day, slot, lab)
                                scheduled_count += 1
                                progress = True
                                placed_idx = idx
                                break

                            if placed_idx is not None:
                                queue.pop(placed_idx)

                if not progress:
                    logger.info(f"Stable after pass {pass_num + 1}.")
                    break

                remaining = sum(len(q) for q in assignments.values())
                logger.info(f"Pass {pass_num + 1}: {remaining} remaining")
                if remaining == 0:
                    logger.info(f"✅ All done after {pass_num + 1} pass(es).")
                    break

            # ── Save master lab timetable only ────────────────────────────
            for lab_name, schedule in self.lab_schedule.items():
                master_lab_timetable_collection.replace_one(
                    {'lab_name': lab_name},
                    {'lab_name': lab_name, 'schedule': schedule,
                     'generated_at': datetime.now()},
                    upsert=True
                )
                logger.info(f"✓ Saved lab: {lab_name}")

            leftovers = {
                f"{y}-{d}-B{b}": [p['subject'] for p in q]
                for (y, d, b), q in assignments.items() if q
            }
            if leftovers:
                logger.warning(f"⚠️  Unscheduled: {leftovers}")
            else:
                logger.info("✅ All practicals scheduled!")

            logger.info(f"DONE: {scheduled_count} sessions scheduled")
            return {
                'success':              True,
                'message':              f'Scheduled {scheduled_count} practical sessions',
                'labs_generated':       len(self.labs_list),
                'practicals_scheduled': scheduled_count,
                'leftovers':            leftovers,
            }

        except Exception as e:
            logger.error(f"generate() error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}


def generate():
    return TimetableGenerator().generate()