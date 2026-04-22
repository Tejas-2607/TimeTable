# class_timetable_handler.py

from flask import jsonify
from config import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

master_lab_timetable_collection = db['master_lab_timetable']
class_timetable_collection      = db['class_timetable']

from modules import settings_handler

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']


def _normalise_batch(raw: str) -> str:
    s = str(raw).strip()
    while s.startswith('Batch Batch'):
        s = s[len('Batch '):].strip()
    return s


def _is_two_hour_practical(lab_doc: dict, day: str, slot: str, session: dict, next_slot_map: dict) -> bool:
    """
    Determine if this session at (day, slot) is part of a 2-hour practical
    by checking whether the same batch+subject appears in the follow-on slot
    of the master lab schedule.
    """
    if slot not in next_slot_map:
        return False
    next_slot     = next_slot_map[slot]
    next_sessions = lab_doc.get('schedule', {}).get(day, {}).get(next_slot, [])
    batch   = session.get('batch', '')
    subject = session.get('subject', '')
    return any(
        s.get('batch') == batch and s.get('subject') == subject
        for s in next_sessions
    )


def generate_class_timetables() -> dict:
    try:
        logger.info("Starting class timetable generation…")
        deleted = class_timetable_collection.delete_many({}).deleted_count
        logger.info(f"Deleted {deleted} existing class timetables")

        master_sessions = list(master_lab_timetable_collection.find({}))
        if not master_sessions:
            return {'success': False, 'error': 'Master timetable not found'}

        # (year, division) → day → slot → [entry, …]
        class_schedules: dict = {}

        # Fetch dynamic slots
        timings = settings_handler.get_timings()
        all_slots, lec_slots, break_slots = settings_handler.calculate_slots(timings)
        
        # START_SLOTS and NEXT_SLOT derived dynamically
        start_slots = set(lec_slots)
        next_slot_map = {}
        for i in range(len(all_slots) - 1):
            if all_slots[i] in lec_slots and all_slots[i+1] in lec_slots:
                next_slot_map[all_slots[i]] = all_slots[i+1]

        # PRE-INITIALIZE based on Class Structure + Workload Filter
        from modules.class_structure_handler import class_structure_collection
        structure_doc = class_structure_collection.find_one({})
        
        # Get years that actually have workloads to avoid empty boxes
        workload_col = db['workload']
        years_with_workload = set(workload_col.distinct('year'))
        years_with_workload = {y.upper() for y in years_with_workload}

        if structure_doc:
            for year, data in structure_doc.items():
                if year == '_id': continue
                upper_year = year.upper()
                if upper_year not in years_with_workload:
                    continue
                
                # Handle both formats: dictionary {num_divisions, ...} or list of divs
                if isinstance(data, dict):
                    num_divs = data.get('num_divisions', 0)
                    div_names = [chr(65 + i) for i in range(num_divs)] # A, B, C...
                    for div in div_names:
                        key = (upper_year, div)
                        class_schedules[key] = {
                            d: {s: [] for s in all_slots}
                            for d in DAYS
                        }
                elif isinstance(data, list):
                    for div_info in data:
                        div = div_info.get('div', 'A')
                        key = (upper_year, div)
                        class_schedules[key] = {
                            d: {s: [] for s in all_slots}
                            for d in DAYS
                        }

        for lab_doc in master_sessions:
            lab_name = lab_doc.get('lab_name', 'Unknown')

            for day in DAYS:
                for slot, sessions in lab_doc.get('schedule', {}).get(day, {}).items():

                    # Only process START slots to avoid double-counting
                    if slot not in start_slots:
                        continue

                    for session in (sessions or []):
                        # Handle both 'class' and 'year' for backward/forward compatibility
                        class_name = session.get('class') or session.get('year')
                        division   = session.get('division')
                        if not class_name or not division:
                            logger.warning(
                                f"Missing class/div in {lab_name} {day} {slot}")
                            continue

                        key = (class_name, division)
                        if key not in class_schedules:
                            class_schedules[key] = {
                                d: {s: [] for s in all_slots}
                                for d in DAYS
                            }

                        entry = {
                            'batch':        _normalise_batch(session.get('batch', '')),
                            'subject':      session.get('subject'),
                            'subject_full': session.get('subject_full'),
                            'faculty':      session.get('faculty'),
                            'faculty_id':   session.get('faculty_id'),
                            'lab':          lab_name,
                            'type':         'practical',
                        }

                        # Write session as is (timetable_generator already expanded sessions across slots)
                        class_schedules[key][day][slot].append(dict(entry))

        logger.info(f"Found {len(class_schedules)} class-division groups")

        timetables_created = 0
        for (class_name, division), schedule in class_schedules.items():
            # Count practicals in PRIMARY slots only (avoid double-counting 2-hr sessions)
            total_practicals = sum(
                1
                for d_name, d_slots in schedule.items()
                for sl, slot_sessions in d_slots.items()
                if sl in start_slots          # only primary start slots
                for s in slot_sessions
                if s.get('type') == 'practical'
            )

            doc = {
                'class':            class_name,
                'division':         division,
                'class_key':        f"{class_name}-{division}",
                'schedule':         schedule,
                'generated_at':     datetime.now(),
                'total_practicals': total_practicals,
            }
            class_timetable_collection.insert_one(doc)
            timetables_created += 1
            logger.info(f"Created {class_name}-{division} "
                        f"({total_practicals} practical slot-entries)")

        logger.info(f"✅ Created {timetables_created} class timetables")
        return {
            'success':            True,
            'message':            f'Generated {timetables_created} class timetables',
            'timetables_created': timetables_created,
        }

    except Exception as e:
        logger.error(f"generate_class_timetables error: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


def get_class_timetable(class_name: str, division: str):
    try:
        if not class_name or not division:
            return jsonify({'error': 'Missing class_name or division'}), 400
        tt = class_timetable_collection.find_one(
            {'class': class_name.upper(), 'division': division.upper()})
        if not tt:
            return jsonify({'error': f'No timetable for {class_name}-{division}'}), 404
        tt['_id'] = str(tt['_id'])
        if tt.get('generated_at'):
            tt['generated_at'] = tt['generated_at'].isoformat()
        return jsonify(tt), 200
    except Exception as e:
        logger.error(f"get_class_timetable error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def get_all_class_timetables():
    try:
        timetables = list(class_timetable_collection.find({}))
        for t in timetables:
            t['_id'] = str(t['_id'])
            if t.get('generated_at'):
                t['generated_at'] = t['generated_at'].isoformat()
        return jsonify({'total': len(timetables), 'timetables': timetables}), 200
    except Exception as e:
        logger.error(f"get_all_class_timetables error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def get_class_timetable_summary(class_name: str, division: str):
    try:
        tt = class_timetable_collection.find_one(
            {'class': class_name.upper(), 'division': division.upper()})
        if not tt:
            return jsonify({'error': f'No timetable for {class_name}-{division}'}), 404
        summary = {
            day: {slot: [s.get('subject') for s in sess]
                  for slot, sess in slots.items() if sess}
            for day, slots in tt.get('schedule', {}).items()
        }
        return jsonify({'class_key': tt.get('class_key'), 'summary': summary}), 200
    except Exception as e:
        logger.error(f"get_class_timetable_summary error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500