# class_timetable_handler.py
"""
Converts the Master Practical Timetable into individual Class Timetables.

BUGS FIXED:
1. Practicals only occupied 1 slot — now 2 consecutive slots per practical.
2. "Batch Batch 1" double-prefix normalised.
3. Missing class/division sessions now warn instead of silent skip.
4. generated_at consistently stored as datetime (isoformat on GET).
"""

from flask import jsonify
from config import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

master_lab_timetable_collection = db['master_lab_timetable']
class_timetable_collection      = db['class_timetable']
class_structure_collection      = db['class_structure']

DAYS       = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
TIME_SLOTS = ['10:15', '11:15', '12:15', '13:15', '14:15', '15:15', '16:20']

PRACTICAL_NEXT_SLOT = {'11:15': '12:15', '14:15': '15:15'}


def _normalise_batch(raw: str) -> str:
    s = str(raw).strip()
    while s.startswith('Batch Batch'):
        s = s[len('Batch '):].strip()
    return s


def generate_class_timetables() -> dict:
    try:
        logger.info("Starting class timetable generation...")
        deleted = class_timetable_collection.delete_many({}).deleted_count
        logger.info(f"Deleted {deleted} existing class timetables")

        master_sessions = list(master_lab_timetable_collection.find({}))
        if not master_sessions:
            return {'success': False, 'error': 'Master timetable not found'}

        class_sessions: dict = {}

        for lab_doc in master_sessions:
            lab_name = lab_doc.get('lab_name', 'Unknown')
            for day in DAYS:
                for slot, sessions in lab_doc.get('schedule', {}).get(day, {}).items():
                    for session in (sessions or []):
                        class_name = session.get('class')
                        division   = session.get('division')
                        if not class_name or not division:
                            logger.warning(f"Missing class/div in {lab_name} {day} {slot}")
                            continue
                        key = (class_name, division)
                        class_sessions.setdefault(key, []).append({
                            'day':          day,
                            'slot':         slot,
                            'lab':          lab_name,
                            'subject':      session.get('subject'),
                            'subject_full': session.get('subject_full'),
                            'batch':        _normalise_batch(session.get('batch', '')),
                            'faculty':      session.get('faculty'),
                            'faculty_id':   session.get('faculty_id'),
                        })

        logger.info(f"Found {len(class_sessions)} class-division groups")
        timetables_created = 0

        for (class_name, division), sessions in class_sessions.items():
            timetable = {
                'class':    class_name,
                'division': division,
                'class_key': f"{class_name}-{division}",
                'schedule': {day: {slot: [] for slot in TIME_SLOTS} for day in DAYS},
            }

            for s in sessions:
                day, slot = s['day'], s['slot']
                entry = {
                    'batch': s['batch'], 'subject': s['subject'],
                    'subject_full': s['subject_full'], 'faculty': s['faculty'],
                    'faculty_id': s['faculty_id'], 'lab': s['lab'], 'type': 'practical',
                }
                if slot in timetable['schedule'].get(day, {}):
                    timetable['schedule'][day][slot].append(entry)
                next_slot = PRACTICAL_NEXT_SLOT.get(slot)
                if next_slot and next_slot in timetable['schedule'].get(day, {}):
                    timetable['schedule'][day][next_slot].append(dict(entry))

            timetable['generated_at']     = datetime.now()
            timetable['total_practicals'] = len(sessions)
            result = class_timetable_collection.insert_one(timetable)
            timetables_created += 1
            logger.info(f"Created {class_name}-{division} ({result.inserted_id})")

        logger.info(f"✅ Created {timetables_created} class timetables")
        return {'success': True, 'message': f'Generated {timetables_created} class timetables',
                'timetables_created': timetables_created}

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