from flask import jsonify
from bson import ObjectId
from config import db

subjects_collection = db['subjects']


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
        "practical_duration": 2,
        "practical_type": "Specific Lab",  # or "Common Lab"
        "required_labs": "OS Lab"          # optional
    }
    """
    try:
        required_fields = [
            'year', 'name', 'short_name', 'hrs_per_week_lec',
            'hrs_per_week_practical', 'practical_duration', 'practical_type'
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: '{field}'"}), 400

        year = data.get('year').lower()
        valid_years = ['sy', 'ty', 'be']
        if year not in valid_years:
            return jsonify({"error": f"Invalid year. Must be one of: {', '.join(valid_years)}"}), 400

        # SH-02 FIX: store a real ObjectId, not str(ObjectId()).
        # Serialise to string only in the API response below.
        new_oid = ObjectId()

        subject_obj = {
            "_id":                    new_oid,          # real ObjectId in DB
            "name":                   data.get('name'),
            "short_name":             data.get('short_name'),
            "hrs_per_week_lec":       data.get('hrs_per_week_lec'),
            "hrs_per_week_practical": data.get('hrs_per_week_practical'),
            "practical_duration":     data.get('practical_duration'),
            "practical_type":         data.get('practical_type'),
        }

        if 'required_labs' in data and data.get('required_labs'):
            subject_obj['required_labs'] = data.get('required_labs')

        existing_doc = subjects_collection.find_one({})

        if existing_doc:
            year_subjects = existing_doc.get(year, [])
            subject_exists = any(
                s.get('short_name') == subject_obj['short_name']
                for s in year_subjects
            )
            if subject_exists:
                return jsonify({
                    "error": (f"Subject with short_name '{subject_obj['short_name']}' "
                              f"already exists in {year.upper()}")
                }), 409

            subjects_collection.update_one(
                {"_id": existing_doc["_id"]},
                {"$push": {year: subject_obj}}
            )
            message = f"Subject '{data.get('name')}' added to {year.upper()}"
        else:
            new_doc = {"sy": [], "ty": [], "be": []}
            new_doc[year] = [subject_obj]
            subjects_collection.insert_one(new_doc)
            message = (f"Subjects collection created and "
                       f"'{data.get('name')}' added to {year.upper()}")

        return jsonify({"message": message, "subject_id": str(new_oid)}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_subjects():
    """
    Retrieve all subjects organised by year (sy, ty, be).
    Subject _id ObjectIds are serialised to strings for JSON transport.
    """
    try:
        subjects_doc = subjects_collection.find_one({})

        if not subjects_doc:
            return jsonify({"sy": [], "ty": [], "be": []}), 200

        subjects_doc.pop('_id', None)

        for yr in ['sy', 'ty', 'be']:
            if yr not in subjects_doc:
                subjects_doc[yr] = []
            # Serialise any ObjectId _ids to strings so JSON doesn't choke
            for subj in subjects_doc[yr]:
                if isinstance(subj.get('_id'), ObjectId):
                    subj['_id'] = str(subj['_id'])

        return jsonify(subjects_doc), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def update_subject(data):
    """
    Update a subject by its _id.

    SH-01 FIX: uses the $ positional operator with an array-element filter
    instead of a positional index.  This is atomic — no race condition even
    if two requests arrive simultaneously.

    Expected data:
    {
        "id": "<subject_id>",   # string representation of the ObjectId
        "year": "sy",
        "name": "Updated Name",
        "short_name": "UN",
        "hrs_per_week_lec": 4,
        "hrs_per_week_practical": 2,
        "practical_duration": 2,
        "practical_type": "Specific Lab",
        "required_labs": "OS Lab"   # optional
    }
    """
    try:
        subject_id_raw = data.get('id')
        year           = data.get('year', '').lower()

        if not subject_id_raw or not year:
            return jsonify({"error": "Missing 'id' or 'year'"}), 400

        valid_years = ['sy', 'ty', 'be']
        if year not in valid_years:
            return jsonify({
                "error": f"Invalid year. Must be one of: {', '.join(valid_years)}"
            }), 400

        # Accept both ObjectId and legacy string _ids stored by older code (SH-02
        # migration compatibility: existing docs may still have string _ids).
        try:
            subject_id_oid = ObjectId(subject_id_raw)
            id_filter_value = subject_id_oid   # real ObjectId
        except Exception:
            id_filter_value = subject_id_raw   # fallback: plain string

        # SH-02 compatibility: also try matching as the string form in case the
        # document was written before this fix was deployed.
        # We match whichever form is actually stored.
        existing_doc = subjects_collection.find_one({})
        if not existing_doc:
            return jsonify({"error": "No subjects found"}), 404

        # Detect which form is stored so we use the right filter value
        year_subjects = existing_doc.get(year, [])
        stored_id = None
        for subj in year_subjects:
            raw = subj.get('_id')
            if str(raw) == str(subject_id_raw):
                stored_id = raw   # use exactly what's in the DB as the filter
                break

        if stored_id is None:
            return jsonify({
                "error": f"Subject with ID '{subject_id_raw}' not found in {year.upper()}"
            }), 404

        # Build the replacement object, preserving the stored _id type
        updated_subject = {
            "_id":                    stored_id,
            "name":                   data.get('name'),
            "short_name":             data.get('short_name'),
            "hrs_per_week_lec":       data.get('hrs_per_week_lec'),
            "hrs_per_week_practical": data.get('hrs_per_week_practical'),
            "practical_duration":     data.get('practical_duration'),
            "practical_type":         data.get('practical_type'),
        }
        if 'required_labs' in data and data.get('required_labs'):
            updated_subject['required_labs'] = data.get('required_labs')

        # SH-01 FIX: $ positional operator — filter on the array element's _id,
        # then set the matched element to the new object.  No index needed.
        result = subjects_collection.update_one(
            {f"{year}._id": stored_id},
            {"$set": {f"{year}.$": updated_subject}}
        )

        if result.matched_count == 0:
            return jsonify({
                "error": f"Subject with ID '{subject_id_raw}' not found in {year.upper()}"
            }), 404

        return jsonify({"message": f"Subject '{data.get('name')}' updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def delete_subject(data):
    """
    Delete a subject by its _id.
    Expected data: { "id": "<subject_id>", "year": "sy" }
    """
    try:
        subject_id_raw = data.get('id')
        year           = data.get('year', '').lower()

        if not subject_id_raw or not year:
            return jsonify({"error": "Missing 'id' or 'year'"}), 400

        valid_years = ['sy', 'ty', 'be']
        if year not in valid_years:
            return jsonify({
                "error": f"Invalid year. Must be one of: {', '.join(valid_years)}"
            }), 400

        # Migration compatibility: try $pull with both ObjectId and string forms
        # so documents written before the SH-02 fix are also deletable.
        try:
            oid = ObjectId(subject_id_raw)
        except Exception:
            oid = None

        # Try ObjectId form first
        result = subjects_collection.update_one(
            {}, {"$pull": {year: {"_id": oid}}}
        ) if oid else None

        if not result or result.modified_count == 0:
            # Fall back to string form (pre-fix documents)
            result = subjects_collection.update_one(
                {}, {"$pull": {year: {"_id": subject_id_raw}}}
            )

        if result.modified_count > 0:
            return jsonify({"message": f"Subject deleted successfully from {year.upper()}"}), 200
        else:
            return jsonify({
                "error": f"Subject with ID '{subject_id_raw}' not found in {year.upper()}"
            }), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500