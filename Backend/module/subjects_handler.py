from flask import jsonify
from config import db

# Collection for subjects
subjects_collection = db['subjects']

def save_subjects(data):
    """
    Saves subjects by first deleting existing subjects and then inserting new ones.
    Expected data format:
    {
        "year": {
            "sy": [
                {"name": "Math", "short_name": "MATH", "hrs_per_week_practical": 0, "hrs_per_week_lec": 3},
                ...
            ],
            "ty": [...],
            "be": [...]
        }
    }
    """

    if not data or "year" not in data:
        return jsonify({"error": "Missing 'year' data"}), 400

    try:
        # Delete existing subjects
        subjects_collection.delete_many({})

        # Insert new subjects
        subjects_collection.insert_one(data)

        return jsonify({"message": "Subjects saved successfully!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
