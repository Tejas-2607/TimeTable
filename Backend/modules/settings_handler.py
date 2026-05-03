# modules/settings_handler.py

from flask import jsonify
from config import db
from datetime import datetime, timedelta

collection = db["settings"]

def calculate_slots(settings):
    start_str = settings.get("day_start_time", "10:15")
    end_str = settings.get("day_end_time", "18:20")
    duration_mins = int(settings.get("lecture_duration", 60))
    breaks = settings.get("breaks", [])

    # Parse start and end times
    current = datetime.strptime(start_str, "%H:%M")
    end_time = datetime.strptime(end_str, "%H:%M")

    slots = []

    while current < end_time:
        current_str = current.strftime("%H:%M")
        
        # Check if the current time matches a break start time
        active_break = next((b for b in breaks if b['start_time'] == current_str), None)
        
        if active_break:
            # Skip the break duration (e.g., 60 mins for Lunch, 5 mins for Break)
            break_duration = int(active_break.get("duration", 0))
            current = current + timedelta(minutes=break_duration)
            continue
        
        # Calculate when this lecture would end
        next_lecture_end = current + timedelta(minutes=duration_mins)
        
        # Only add the slot if it doesn't exceed the end of the day
        if next_lecture_end <= end_time:
            slots.append(current_str)
            current = next_lecture_end
        else:
            break
    # print("\n" + "="*30)
    # print(f"VERIFYING SLOTS FOR: {settings.get('day_start_time')} to {settings.get('day_end_time')}")
    # print(f"Generated Slots: {slots}")
    # print("="*30 + "\n")

    return slots

def save_timings(data):
    data["type"] = "department_timings"
    data["updated_at"] = datetime.utcnow()

    # Ensure numeric types for calculation
    if "lecture_duration" in data:
        data["lecture_duration"] = int(data["lecture_duration"])

    collection.update_one(
        {"type": "department_timings"},
        {"$set": data},
        upsert=True
    )

    # Generate the correct slots based on the new logic
    data["slots"] = calculate_slots(data)
    
    # Remove MongoDB internal ID for clean JSON response
    if "_id" in data:
        data.pop("_id")

    return jsonify(data), 200


def get_timings():
    settings = collection.find_one({"type": "department_timings"})

    if not settings:
        return jsonify({
            "day_start_time": "10:15",
            "day_end_time": "18:20",
            "lecture_duration": 60,
            "breaks": [],
            "slots": []
        }), 200

    settings["_id"] = str(settings["_id"])
    settings["slots"] = calculate_slots(settings)

    return jsonify(settings), 200


def save_lab_timings(data):
    data["type"] = "lab_timings"
    data["updated_at"] = datetime.utcnow()

    sessions = data.get("sessions", [])
    normalized_sessions = []
    for session in sessions:
        start_time = session.get("startTime") or session.get("start_time")
        end_time = session.get("endTime") or session.get("end_time")
        if not start_time or not end_time:
            continue
        normalized_sessions.append({
            "startTime": start_time,
            "endTime": end_time,
        })

    data["sessions"] = normalized_sessions

    collection.update_one(
        {"type": "lab_timings"},
        {"$set": data},
        upsert=True
    )

    if "_id" in data:
        data.pop("_id")

    return jsonify(data), 200


def get_lab_timings():
    settings = collection.find_one({"type": "lab_timings"})

    if not settings:
        return jsonify({
            "sessions": [],
        }), 200

    settings["_id"] = str(settings["_id"])
    return jsonify(settings), 200