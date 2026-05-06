# class_timetable_handler.py

from flask import jsonify
from config import db
from datetime import datetime
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)

master_lab_timetable_collection = db['master_lab_timetable']
class_timetable_collection      = db['class_timetable']

DAYS        = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
ALL_SLOTS   = ['10:15', '11:15', '12:15', '13:15', '14:15', '15:15', '16:20', '17:20']
START_SLOTS = {'11:15', '14:15', '16:20'}
NEXT_SLOT   = {'11:15': '12:15', '14:15': '15:15'}


# CH-02 FIX: return int, not string "Batch N".
# timetable_generator.py stores batches as int (1, 2, 3).
# class_timetable_handler was returning "Batch 1" — inconsistent across
# collections.  We normalise to int here so both collections agree on type.
def _normalise_batch(raw) -> int:
    """
    Accept any of: int 1, string '1', string 'Batch 1', string 'Batch Batch 1'.
    Always returns a plain int.  Returns 0 on total parse failure (sentinel
    value — callers should log/skip 0-batch entries).
    """
    if isinstance(raw, int):
        return raw
    s = str(raw).strip()
    # Strip any number of leading 'Batch ' prefixes
    while s.lower().startswith('batch '):
        s = s[len('batch '):].strip()
    try:
        return int(s)
    except ValueError:
        logger.warning(f"_normalise_batch: could not parse '{raw}', returning 0")
        return 0


def _is_two_hour_practical(lab_doc: dict, day: str, slot: str, session: dict) -> bool:
    """
    Return True if this session is part of a 2-hour practical by checking
    whether the same batch+subject appears in the follow-on slot of the
    master lab schedule.
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

                    if slot not in START_SLOTS:
                        continue

                    for session in (sessions or []):
                        class_name = session.get('class')
                        division   = session.get('division')
                        if not class_name or not division:
                            logger.warning(
                                f"Missing class/div in {lab_name} {day} {slot}")
                            continue

                        # CH-02 FIX: store batch as int to match timetable_generator
                        batch_int = _normalise_batch(session.get('batch', ''))
                        if batch_int == 0:
                            logger.warning(
                                f"Skipping unresolvable batch '{session.get('batch')}' "
                                f"in {lab_name} {day} {slot}")
                            continue

                        key = (class_name, division)
                        if key not in class_schedules:
                            class_schedules[key] = {
                                d: {s: [] for s in ALL_SLOTS}
                                for d in DAYS
                            }

                        entry = {
                            'batch':        batch_int,          # int, not "Batch N"
                            'subject':      session.get('subject'),
                            'subject_full': session.get('subject_full'),
                            'faculty':      session.get('faculty'),
                            'faculty_id':   session.get('faculty_id'),
                            'lab':          lab_name,
                            'type':         'practical',
                        }

                        # Write primary START slot
                        class_schedules[key][day][slot].append(dict(entry))

                        # Write follow-on slot for 2-hr practicals
                        if _is_two_hour_practical(lab_doc, day, slot, session):
                            next_slot = NEXT_SLOT[slot]
                            class_schedules[key][day][next_slot].append(dict(entry))

        logger.info(f"Found {len(class_schedules)} class-division groups")

        timetables_created = 0
        for (class_name, division), schedule in class_schedules.items():

            # CH-01 FIX: count only entries that sit in a START_SLOT.
            # Previously the loop counted follow-on slots too, doubling the
            # total for every 2-hour practical.
            total_practicals = sum(
                len(schedule[day][slot])
                for day in DAYS
                for slot in START_SLOTS          # only START_SLOTS, not ALL_SLOTS
                if slot in schedule.get(day, {})
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
                        f"({total_practicals} practicals)")

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


def delete_class_timetable(timetable_id: str):
    try:
        if not timetable_id or not ObjectId.is_valid(timetable_id):
            return jsonify({'error': 'Invalid timetable id'}), 400

        result = class_timetable_collection.delete_one({'_id': ObjectId(timetable_id)})
        if result.deleted_count == 0:
            return jsonify({'error': 'Class timetable not found'}), 404

        return jsonify({'message': 'Class timetable deleted successfully'}), 200
    except Exception as e:
        logger.error(f"delete_class_timetable error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def _remove_matching_sessions_from_class_timetables(matcher):
    docs = list(class_timetable_collection.find({}))
    updated_count = 0

    for doc in docs:
        schedule = doc.get('schedule', {})
        changed = False

        for day, day_slots in schedule.items():
            for slot, sessions in day_slots.items():
                filtered = [s for s in sessions if not matcher(s)]
                if len(filtered) != len(sessions):
                    schedule[day][slot] = filtered
                    changed = True

        if changed:
            class_timetable_collection.update_one(
                {'_id': doc['_id']},
                {'$set': {'schedule': schedule}}
            )
            updated_count += 1

    return updated_count


def delete_faculty_timetable(faculty_short_name: str):
    try:
        faculty_short_name = (faculty_short_name or '').strip()
        if not faculty_short_name:
            return jsonify({'error': 'Missing faculty short name'}), 400

        updated_count = _remove_matching_sessions_from_class_timetables(
            lambda s: any(
                f.strip() == faculty_short_name
                for f in str(s.get('faculty', '')).split(',')
                if f.strip()
            )
        )

        if updated_count == 0:
            return jsonify({'error': f'No sessions found for faculty {faculty_short_name}'}), 404

        return jsonify({
            'message': f'Faculty timetable deleted for {faculty_short_name}',
            'updated_class_timetables': updated_count
        }), 200
    except Exception as e:
        logger.error(f"delete_faculty_timetable error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def delete_lab_timetable(lab_name: str):
    try:
        lab_name = (lab_name or '').strip()
        if not lab_name:
            return jsonify({'error': 'Missing lab name'}), 400

        updated_count = _remove_matching_sessions_from_class_timetables(
            lambda s: str(s.get('lab', '')).strip() == lab_name
        )

        if updated_count == 0:
            return jsonify({'error': f'No sessions found for lab {lab_name}'}), 404

        return jsonify({
            'message': f'Lab timetable deleted for {lab_name}',
            'updated_class_timetables': updated_count
        }), 200
    except Exception as e:
        logger.error(f"delete_lab_timetable error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500