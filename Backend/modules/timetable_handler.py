# timetable_handler.py
# Read-only handlers for the master lab timetable collection.
# Generation logic lives in timetable_generator.py — this file only reads.

from flask import jsonify
from config import db
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)

master_lab_timetable_collection = db['master_lab_timetable']


def get_master_practical_timetable():
    """
    GET /api/master_timetables
    Returns all lab timetables from master_lab_timetable collection.
    """
    try:
        timetables = list(master_lab_timetable_collection.find({}))

        if not timetables:
            return jsonify({
                'total': 0,
                'timetables': [],
                'message': 'No timetables found. Run generation first.'
            }), 200

        for t in timetables:
            t['_id'] = str(t['_id'])
            if t.get('generated_at'):
                t['generated_at'] = t['generated_at'].isoformat()

        return jsonify({
            'total': len(timetables),
            'timetables': timetables
        }), 200

    except Exception as e:
        logger.error(f"get_master_practical_timetable error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def delete_master_timetable(timetable_id: str):
    try:
        if not timetable_id or not ObjectId.is_valid(timetable_id):
            return jsonify({'error': 'Invalid timetable id'}), 400

        result = master_lab_timetable_collection.delete_one({'_id': ObjectId(timetable_id)})
        if result.deleted_count == 0:
            return jsonify({'error': 'Master practical timetable not found'}), 404

        return jsonify({'message': 'Master practical timetable deleted successfully'}), 200
    except Exception as e:
        logger.error(f"delete_master_timetable error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def delete_master_timetable_by_lab(lab_name: str):
    try:
        lab_name = (lab_name or '').strip()
        if not lab_name:
            return jsonify({'error': 'Missing lab name'}), 400

        result = master_lab_timetable_collection.delete_one({'lab_name': lab_name})
        if result.deleted_count == 0:
            return jsonify({'error': f'Master timetable for {lab_name} not found'}), 404

        return jsonify({'message': f'Master practical timetable deleted for {lab_name}'}), 200
    except Exception as e:
        logger.error(f"delete_master_timetable_by_lab error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500