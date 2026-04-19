# settings_handler.py

from flask import jsonify
from config import db
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
settings_collection = db['settings']

def get_timings():
    try:
        timings = settings_collection.find_one({'type': 'department_timings'})
        if not timings:
            # Default timings
            timings = {
                'lecture_duration': 60,
                'day_start_time': '10:15',
                'day_end_time': '17:20',
                'breaks': [{'name': 'Lunch', 'start_time': '13:15', 'duration': 60}]
            }
        else:
            del timings['_id']
            del timings['type']
        
        # Calculate dynamic slots
        all_s, lec_s, brk_s = calculate_slots(timings)
        timings['slots'] = all_s
        timings['lecture_slots'] = lec_s
        timings['break_slots'] = brk_s
        
        return timings
    except Exception as e:
        logger.error(f"Error fetching timings: {e}")
        return None

def save_timings(data):
    try:
        data['type'] = 'department_timings'
        data['updated_at'] = datetime.now()
        settings_collection.replace_one({'type': 'department_timings'}, data, upsert=True)
        return jsonify({'message': 'Timings saved successfully'}), 200
    except Exception as e:
        logger.error(f"Error saving timings: {e}")
        return jsonify({'error': str(e)}), 500

def calculate_slots(timings):
    """
    Calculate ALL_SLOTS, LECTURE_SLOTS, and BREAK_SLOTS based on timings.
    """
    if not timings:
        return [], [], []

    start_str = timings.get('day_start_time', '10:15')
    duration = int(timings.get('lecture_duration', 60))
    end_str = timings.get('day_end_time', '17:20')
    breaks = timings.get('breaks', [])

    start_time = datetime.strptime(start_str, '%H:%M')
    end_time = datetime.strptime(end_str, '%H:%M')
    
    all_slots = []
    break_slots = []
    lecture_slots = []
    
    current = start_time
    while current + timedelta(minutes=duration) <= end_time:
        slot_str = current.strftime('%H:%M')
        
        # Check if current time is a break
        is_break = False
        for b in breaks:
            b_start = datetime.strptime(b['start_time'], '%H:%M').time()
            if current.time() == b_start:
                is_break = True
                break_slots.append(slot_str)
                # Adjust duration for break if needed, but usually breaks occupy a slot
                break_duration = int(b.get('duration', duration))
                current += timedelta(minutes=break_duration)
                break
        
        if not is_break:
            lecture_slots.append(slot_str)
            all_slots.append(slot_str)
            current += timedelta(minutes=duration)
        else:
            all_slots.append(slot_str)

    return all_slots, lecture_slots, break_slots
