from flask import jsonify
from config import db
from modules import timetable_generator  # new module

timetable_collection = db['timetable']
master_lab_timetable_collection = db['master_lab_timetable']

# ---------- Generate timetable ----------
def generate_timetable(data):
    """
    Delegate timetable generation to timetable_generator module
    and save the generated timetable in the database.
    Expected data:
    {
        "year": "SY",
        "sem": "1",
        "other_parameters": {...}  # can include faculty, labs, subjects, constraints
    }
    """
    year = data.get("year")
    sem = data.get("sem")

    if not year or not sem:
        return jsonify({"error": "Missing year or semester"}), 400

    try:
        # Call the timetable generator module
        generated_tt = timetable_generator.generate(data)

        # Delete existing timetable for this year/sem
        timetable_collection.delete_many({"year": year, "sem": sem})

        # Save the generated timetable
        timetable_collection.insert_one({
            "year": year,
            "sem": sem,
            "timetable": generated_tt
        })

        return jsonify({"message": f"Timetable generated and saved for {year} sem {sem}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
