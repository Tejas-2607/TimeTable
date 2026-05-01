# timetable_handler.py
# Read-only handlers for the master lab timetable collection.
# Generation logic lives in timetable_generator.py — this file only reads.

from flask import jsonify
from config import db
import logging

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