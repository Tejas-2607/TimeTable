# modules/settings_handler.py

from flask import jsonify
from config import db
from datetime import datetime, timedelta

collection = db["settings"]


def calculate_slots(settings):
    start = datetime.strptime(settings["day_start_time"], "%H:%M")
    end = datetime.strptime(settings["day_end_time"], "%H:%M")
    duration = settings["lecture_duration"]

    slots = []
    current = start

    while current < end:
        next_time = current + timedelta(minutes=duration)
        slots.append(f"{current.strftime('%H:%M')}-{next_time.strftime('%H:%M')}")
        current = next_time

    return slots


def get_timings():
    settings = collection.find_one({"type": "department_timings"})

    if not settings:
        return jsonify({
            "day_start_time": "10:00",
            "day_end_time": "17:00",
            "lecture_duration": 60,
            "slots": []
        }), 200

    settings["_id"] = str(settings["_id"])
    settings["slots"] = calculate_slots(settings)

    return jsonify(settings), 200


def save_timings(data):
    data["type"] = "department_timings"
    data["updated_at"] = datetime.utcnow()

    collection.update_one(
        {"type": "department_timings"},
        {"$set": data},
        upsert=True
    )

    return jsonify({"message": "Timings saved"}), 200