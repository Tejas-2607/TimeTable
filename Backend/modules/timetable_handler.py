from flask import jsonify
from config import db
from modules import timetable_generator

timetable_collection = db['timetable']
master_lab_timetable_collection = db['master_lab_timetable']

# ---------- Generate timetable for single year ----------
def generate_timetable(data):
    """
    Generate timetable for a specific year/semester
    Expected data:
    {
        "year": "SY",
        "sem": "1"
    }
    """
    year = data.get("year")
    sem = data.get("sem")

    if not year or not sem:
        return jsonify({"error": "Missing year or semester"}), 400

    try:
        # Call the timetable generator module
        generated_tt = timetable_generator.generate(data)

        if not generated_tt:
            return jsonify({"error": "Failed to generate timetable"}), 500

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


# ---------- Generate timetable for ALL classes ----------
def generate_all_timetables(data):
    """
    Generate timetables for all years (SY, TY, BE) for a specific semester
    Expected data:
    {
        "sem": "1"
    }
    """
    sem = data.get("sem")

    if not sem:
        return jsonify({"error": "Missing semester"}), 400

    try:
        years = ["SY", "TY", "BE"]
        results = {
            "semester": sem,
            "generated_timetables": []
        }

        for year in years:
            # Generate timetable for this year
            generated_tt = timetable_generator.generate({
                "year": year,
                "sem": sem
            })

            if generated_tt:
                # Delete existing timetable for this year/sem
                master_lab_timetable_collection.delete_many({
                    "year": year,
                    "semester": sem
                })

                # Save the generated timetable
                result = master_lab_timetable_collection.insert_one({
                    "year": year,
                    "semester": sem,
                    "schedule": generated_tt
                })

                results["generated_timetables"].append({
                    "year": year,
                    "status": "success",
                    "id": str(result.inserted_id)
                })
            else:
                results["generated_timetables"].append({
                    "year": year,
                    "status": "failed",
                    "reason": "No practicals found or constraint satisfaction failed"
                })

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Get all generated timetables ----------
def get_all_master_timetables():
    """
    Retrieve all generated master lab timetables
    """
    try:
        timetables = list(master_lab_timetable_collection.find({}, {'_id': 0}))
        return jsonify(timetables)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Get timetable for specific year/semester ----------
def get_master_timetable(data):
    """
    Retrieve master lab timetable for specific year/semester
    Expected data:
    {
        "year": "SY",
        "sem": "1"
    }
    """
    year = data.get("year")
    sem = data.get("sem")

    if not year or not sem:
        return jsonify({"error": "Missing year or semester"}), 400

    try:
        timetable = master_lab_timetable_collection.find_one({
            "year": year,
            "semester": sem
        }, {'_id': 0})

        if not timetable:
            return jsonify({"error": f"Timetable not found for {year} sem {sem}"}), 404

        return jsonify(timetable)
    except Exception as e:
        return jsonify({"error": str(e)}), 500