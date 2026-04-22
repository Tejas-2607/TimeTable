from flask import jsonify
from bson import ObjectId
from config import db

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

        year = data.get('year').upper()
        
        # Get dynamic years from class_structure
        from modules.class_structure_handler import get_active_years_list
        valid_years = [y.upper() for y in get_active_years_list()]
        
        if year not in valid_years:
            return jsonify({"error": f"Invalid year. Must be one of: {', '.join(valid_years)}"}), 400

        # Prepare subject object (without year field)
        subject_obj = {
            "_id": str(ObjectId()),  # Generate unique ID for the subject
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
            # Create new document with all years from structure
            from modules.class_structure_handler import get_active_years_list
            new_doc = {yr.upper(): [] for yr in get_active_years_list()}
            new_doc[year] = [subject_obj]
            subjects_collection.insert_one(new_doc)
            message = f"Subjects collection created and '{data.get('name')}' added to {year.upper()}"

        return jsonify({"message": message, "subject_id": subject_obj["_id"]}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_subjects():
    """
    Retrieve all subjects, regardless of the year.
    Always returns all subjects organized by year (sy, ty, be).
    """
    try:
        subjects_doc = subjects_collection.find_one({})
        
        from modules.class_structure_handler import get_active_years_list
        active_years = get_active_years_list() # e.g., ['SY', 'TY', 'BE'] or ['sy', 'ty', 'be']
        
        if not subjects_doc:
            return jsonify({yr: [] for yr in active_years}), 200
        
        # Remove MongoDB _id from response
        subjects_doc.pop('_id', None)
        
        # Prepare normalized response
        response_data = {}
        
        # Populate with data from DB
        for yr in active_years:
            yr_upper = yr.upper()
            yr_lower = yr.lower()
            
            # Combine subjects from both upper and lower case keys if they both exist (safety)
            combined_subjects = subjects_doc.get(yr_upper, []) + subjects_doc.get(yr_lower, [])
            
            # Remove duplicates by short_name
            seen = set()
            unique_subjects = []
            for s in combined_subjects:
                short_name = s.get('short_name')
                if short_name and short_name not in seen:
                    unique_subjects.append(s)
                    seen.add(short_name)
            
            # Use the EXACT casing from active_years for the response key
            response_data[yr] = unique_subjects
        
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def update_subject(data):
    """
    Update a subject by its ID.
    Expected data:
    {
        "id": "subject_id_here",
        "year": "sy",  # year where the subject exists
        "name": "Updated Name",
        "short_name": "UN",
        "hrs_per_week_lec": 4,
        "hrs_per_week_practical": 2,
        "practical_duration": 2,
        "practical_type": "Specific Lab",
        "required_labs": "OS Lab"  # optional
    }
    """
    try:
        subject_id = data.get('id')
        year = data.get('year', '').lower()
        
        if not subject_id or not year:
            return jsonify({"error": "Missing 'id' or 'year'"}), 400
        
        from modules.class_structure_handler import get_active_years_list
        valid_years = [y.upper() for y in get_active_years_list()]
        if year.upper() not in valid_years:
            return jsonify({"error": f"Invalid year. Must be one of: {', '.join(valid_years)}"}), 400
        
        # Get existing subjects document
        subjects_doc = subjects_collection.find_one({})
        if not subjects_doc:
            return jsonify({"error": "No subjects found"}), 404
        
        # Find the subject in the specified year (try both cases)
        year_upper = year.upper()
        year_lower = year.lower()
        
        found_year = None
        if year_upper in subjects_doc:
            found_year = year_upper
        elif year_lower in subjects_doc:
            found_year = year_lower
        
        if not found_year:
            return jsonify({"error": f"Year '{year}' not found in subjects"}), 404
            
        year_subjects = subjects_doc.get(found_year, [])
        subject_index = None
        for idx, subject in enumerate(year_subjects):
            if subject.get('_id') == subject_id:
                subject_index = idx
                break
        
        if subject_index is None:
            return jsonify({"error": f"Subject with ID '{subject_id}' not found in {found_year}"}), 404
        
        # Prepare updated subject object
        updated_subject = {
            "_id": subject_id,  # Keep the same ID
            "name": data.get('name'),
            "short_name": data.get('short_name'),
            "hrs_per_week_lec": data.get('hrs_per_week_lec'),
            "hrs_per_week_practical": data.get('hrs_per_week_practical'),
            "practical_duration": data.get('practical_duration'),
            "practical_type": data.get('practical_type')
        }
        
        # Add optional field if provided
        if 'required_labs' in data and data.get('required_labs'):
            updated_subject['required_labs'] = data.get('required_labs')
        
        # Update the subject at the specific index
        update_field = f"{found_year}.{subject_index}"
        subjects_collection.update_one(
            {"_id": subjects_doc["_id"]},
            {"$set": {update_field: updated_subject}}
        )
        
        return jsonify({"message": f"Subject '{data.get('name')}' updated successfully"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def delete_subject(data):
    """
    Delete a subject by its ID.
    Expected data:
    {
        "id": "subject_id_here",
        "year": "sy"  # year where the subject exists
    }
    """
    try:
        subject_id = data.get('id')
        year = data.get('year', '').lower()
        
        if not subject_id or not year:
            return jsonify({"error": "Missing 'id' or 'year'"}), 400
        
        from modules.class_structure_handler import get_active_years_list
        valid_years = [y.upper() for y in get_active_years_list()]
        if year.upper() not in valid_years:
            return jsonify({"error": f"Invalid year. Must be one of: {', '.join(valid_years)}"}), 400
        
        # Remove subject with the specified ID from the year array (check both cases)
        year_upper = year.upper()
        year_lower = year.lower()
        
        result = subjects_collection.update_one(
            {},
            {"$pull": {year_upper: {"_id": subject_id}}}
        )
        
        if result.modified_count == 0:
            result = subjects_collection.update_one(
                {},
                {"$pull": {year_lower: {"_id": subject_id}}}
            )
        
        if result.modified_count > 0:
            return jsonify({"message": f"Subject deleted successfully from {year.upper()}"}), 200
        else:
            return jsonify({"error": f"Subject with ID '{subject_id}' not found in {year.upper()}"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


