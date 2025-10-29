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
        "faculty_id": "68efe2d652ff29887ed00756",
        "subjects": [
            {"subject_short_name": "DS", "year": "SY", "class": "A", "practical_hrs": 2, "lec_hrs": 3},
            {"subject_short_name": "CG", "year": "SY", "class": "B", "practical_hrs": 2, "lec_hrs": 2}
        ]
    }
    """
    faculty_id = data.get("faculty_id")
    subjects = data.get("subjects")

    if not faculty_id or not subjects:
        return jsonify({"error": "Missing faculty_id or subjects"}), 400

    try:
        # Convert string ID to ObjectId
        faculty_oid = ObjectId(faculty_id)
        
        # Verify faculty exists
        faculty = faculty_collection.find_one({"_id": faculty_oid})
        if not faculty:
            return jsonify({"error": f"Faculty with ID '{faculty_id}' not found"}), 404

        # Delete existing workload for this faculty
        workload_collection.delete_many({"faculty_id": faculty_oid})

        # Insert new workload
        workload_collection.insert_one({
            "faculty_id": faculty_oid,
            "subjects": subjects
        })

        return jsonify({"message": f"Workload saved for faculty '{faculty.get('name', 'Unknown')}'"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500