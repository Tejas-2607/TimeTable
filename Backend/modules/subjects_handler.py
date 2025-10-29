from flask import jsonify
from bson import ObjectId
from config import db

workload_collection = db['workload']
faculty_collection = db['faculty']
subjects_collection = db['subjects']  # Add subjects collection

def save_subjects(data):
    """
    Save a single subject to the appropriate year.
    Expected data format:
    {
        "year": "sy",  # or "ty" or "be"
        "name": "Data Structures",
        "short_name": "DS",
        "hrs_per_week_lec": 4,
        "hrs_per_week_practical": 0,
        "practical_duration": 2,  # in slots
        "practical_type": "Specific Lab",  # or "Common Lab"
        "required_labs": "OS Lab"  # optional
    }
    """
    try:
        # Validate required fields
        required_fields = ['year', 'name', 'short_name', 'hrs_per_week_lec', 'hrs_per_week_practical', 
                          'practical_duration', 'practical_type']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: '{field}'"}), 400

        year = data.get('year').lower()
        valid_years = ['sy', 'ty', 'be']
        
        if year not in valid_years:
            return jsonify({"error": f"Invalid year. Must be one of: {', '.join(valid_years)}"}), 400

        # Prepare subject object (without year field)
        subject_obj = {
            "name": data.get('name'),
            "short_name": data.get('short_name'),
            "hrs_per_week_lec": data.get('hrs_per_week_lec'),
            "hrs_per_week_practical": data.get('hrs_per_week_practical'),
            "practical_duration": data.get('practical_duration'),
            "practical_type": data.get('practical_type')
        }
        
        # Add optional field if provided
        if 'required_labs' in data and data.get('required_labs'):
            subject_obj['required_labs'] = data.get('required_labs')

        # Check if subjects document exists
        existing_doc = subjects_collection.find_one({})
        
        if existing_doc:
            # Check if this subject already exists (by short_name) in the year
            year_subjects = existing_doc.get(year, [])
            subject_exists = any(s.get('short_name') == subject_obj['short_name'] for s in year_subjects)
            
            if subject_exists:
                return jsonify({"error": f"Subject with short_name '{subject_obj['short_name']}' already exists in {year.upper()}"}), 409
            
            # Append subject to the appropriate year array
            subjects_collection.update_one(
                {"_id": existing_doc["_id"]},
                {"$push": {year: subject_obj}}
            )
            message = f"Subject '{data.get('name')}' added to {year.upper()}"
        else:
            # Create new document with this subject
            new_doc = {year: [subject_obj]}
            subjects_collection.insert_one(new_doc)
            message = f"Subjects collection created and '{data.get('name')}' added to {year.upper()}"

        return jsonify({"message": message}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_subjects():
    """
    Retrieve all subjects organized by year.
    Returns:
    {
        "sy": [...],
        "ty": [...],
        "be": [...]
    }
    """
    try:
        subjects_doc = subjects_collection.find_one({})
        
        if not subjects_doc:
            return jsonify({"sy": [], "ty": [], "be": []}), 200
        
        # Remove MongoDB _id from response
        subjects_doc.pop('_id', None)
        
        # Ensure all years exist in response
        for year in ['sy', 'ty', 'be']:
            if year not in subjects_doc:
                subjects_doc[year] = []
        
        return jsonify(subjects_doc), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def delete_subject(data):
    """
    Delete a subject by short_name and year.
    Expected data:
    {
        "year": "sy",
        "short_name": "DS"
    }
    """
    try:
        year = data.get('year', '').lower()
        short_name = data.get('short_name')
        
        if not year or not short_name:
            return jsonify({"error": "Missing 'year' or 'short_name'"}), 400
        
        valid_years = ['sy', 'ty', 'be']
        if year not in valid_years:
            return jsonify({"error": f"Invalid year. Must be one of: {', '.join(valid_years)}"}), 400
        
        # Remove subject from the year array
        result = subjects_collection.update_one(
            {},
            {"$pull": {year: {"short_name": short_name}}}
        )
        
        if result.modified_count > 0:
            return jsonify({"message": f"Subject '{short_name}' deleted from {year.upper()}"}), 200
        else:
            return jsonify({"error": f"Subject '{short_name}' not found in {year.upper()}"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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