from flask import jsonify
from bson import ObjectId
from config import db

workload_collection = db['workload']
faculty_collection = db['faculty']

def save_faculty_workload(data):
    """
    Save workload for a faculty by deleting previous workload and adding new one.
    Expected data:
    {
        "faculty_name": "Dr. Aditi",
        "subjects": [
            {"year": "SY", "class": "A", "practical_hrs": 2, "lec_hrs": 3},
            {"year": "SY", "class": "B", "practical_hrs": 0, "lec_hrs": 2}
        ]
    }
    """
    faculty_name = data.get("faculty_name")
    subjects = data.get("subjects")

    if not faculty_name or not subjects:
        return jsonify({"error": "Missing faculty_name or subjects"}), 400

    try:
        # Get faculty ID
        faculty = faculty_collection.find_one({"name": faculty_name})
        if not faculty:
            return jsonify({"error": f"Faculty '{faculty_name}' not found"}), 404

        faculty_id = faculty.get("_id")

        # Delete existing workload for this faculty
        workload_collection.delete_many({"faculty_id": faculty_id})

        # Insert new workload
        workload_collection.insert_one({
            "faculty_id": faculty_id,
            "subjects": subjects
        })

        return jsonify({"message": f"Workload saved for faculty '{faculty_name}'"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
