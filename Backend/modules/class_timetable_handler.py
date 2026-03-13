# class_timetable_handler.py
"""
Converts the Master Lab Timetable into individual Class Timetables.

This is the SINGLE authoritative writer for class timetables.
timetable_generator.py only writes the master lab timetable;
this module reads it and produces the per-class view.

BUG FIXED — duplicate follow-on slot entries:
Previously _write_session in timetable_generator also wrote to class schedules,
then this module re-read the master lab timetable and wrote the follow-on slot
a second time.  Now timetable_generator does NOT write class schedules at all —
this module is the sole source of truth for class timetables.

LOGIC:
- A practical session in the master lab timetable appears at its START slot.
  For 2-hour practicals the master also stores an entry in the follow-on slot
  (so the lab shows as occupied for both hours).
- When building class timetables we only read the START slots (11:15, 14:15,
  16:20) from the master lab timetable and write BOTH the primary and follow-on
  slots into the class schedule ourselves — exactly once.
"""

from flask import jsonify
from config import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

master_lab_timetable_collection = db['master_lab_timetable']
class_timetable_collection      = db['class_timetable']

DAYS       = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
ALL_SLOTS  = ['10:15', '11:15', '12:15', '13:15', '14:15', '15:15', '16:20']

# Slots where a practical can START (follow-on slots are derived from these)
START_SLOTS = {'11:15', '14:15', '16:20'}
# For 2-hour practicals: the follow-on slot for each start slot
NEXT_SLOT   = {'11:15': '12:15', '14:15': '15:15'}


def _normalise_batch(raw: str) -> str:
    s = str(raw).strip()
    while s.startswith('Batch Batch'):
        s = s[len('Batch '):].strip()
    return s


def _is_two_hour_practical(lab_doc: dict, day: str, slot: str, session: dict) -> bool:
    """
    Determine if this session at (day, slot) is part of a 2-hour practical
    by checking whether the same batch+subject appears in the follow-on slot
    of the master lab schedule.
    """
    if slot not in NEXT_SLOT:
        return False
    next_slot     = NEXT_SLOT[slot]
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

        for lab_doc in master_sessions:
            lab_name = lab_doc.get('lab_name', 'Unknown')

            for day in DAYS:
                for slot, sessions in lab_doc.get('schedule', {}).get(day, {}).items():

                    # Only process START slots to avoid double-counting
                    if slot not in START_SLOTS:
                        continue

                    for session in (sessions or []):
                        class_name = session.get('class')
                        division   = session.get('division')
                        if not class_name or not division:
                            logger.warning(
                                f"Missing class/div in {lab_name} {day} {slot}")
                            continue

                        key = (class_name, division)
                        if key not in class_schedules:
                            class_schedules[key] = {
                                d: {s: [] for s in ALL_SLOTS}
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

                        # Write primary slot (always)
                        class_schedules[key][day][slot].append(dict(entry))

                        # Write follow-on slot if this is a 2-hour practical
                        if _is_two_hour_practical(lab_doc, day, slot, session):
                            next_slot = NEXT_SLOT[slot]
                            class_schedules[key][day][next_slot].append(dict(entry))

        logger.info(f"Found {len(class_schedules)} class-division groups")

        timetables_created = 0
        for (class_name, division), schedule in class_schedules.items():
            total_practicals = sum(
                1
                for d in schedule.values()
                for slot_sessions in d.values()
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