from flask import jsonify
from bson import ObjectId
from config import db

# MongoDB collection
workload_collection = db['workload']


def parse_batch_item(value):
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        normalized = value.strip()
        if normalized.lower().startswith("batch "):
            normalized = normalized[6:]
        return int(normalized)
    raise ValueError(f"Invalid batch value: {value}")


def normalize_batches(raw_batches):
    if not isinstance(raw_batches, list):
        raw_batches = [raw_batches]
    normalized = [parse_batch_item(b) for b in raw_batches]
    return sorted(set(normalized))


# ---------- GET FACULTY WORKLOAD ----------
def get_faculty_workload():
    """
    Retrieve all faculty workloads.
    """
    try:
        workload_data = list(workload_collection.find({}))

        for w in workload_data:
            w["_id"] = str(w["_id"])

        return jsonify({"workloads": workload_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- ADD FACULTY WORKLOAD ----------
def add_faculty_workload(data):
    """
    Add a new faculty workload entry.
    Expected JSON structure:
    {
        "faculty_id": "64b25f9ed1a4b5d8f0e6a9b3",
        "year": "SY",
        "subject": "OOPJ",
        "subject_full": "Java Programming (OOPJ)",
        "division": "A",
        "batches": [1, 2],
        "theory_hrs": 2,
        "practical_hrs": 2,
        
        // NEW: Optional fields for electives/honors
        "subject_type": "regular|elective|honors",  // Default: "regular"
        "elective_group_id": "ELE-AI-DS-2026"      // Required if subject_type != "regular"
    }
    """
    try:
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Basic presence check before any processing
        required_fields = ["faculty_id", "year", "subject"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

        # WH-01 FIX: build a sanitised document with explicit type casts instead
        # of inserting the raw request dict.  This prevents string practical_hrs,
        # comma-separated batch strings, MongoDB operator injection, and extra
        # client-supplied fields from reaching the database.
        try:
            faculty_id_str = str(data["faculty_id"]).strip()
            if not ObjectId.is_valid(faculty_id_str):
                return jsonify({"error": "Invalid faculty_id — must be a 24-character hex ObjectId"}), 400

            raw_batches = data.get("batches", [1])
            batches = normalize_batches(raw_batches)

            # WH-03 FIX: Validate subject_type and elective_group_id for parallel subjects
            subject_type = str(data.get("subject_type", "regular")).strip().lower()
            if subject_type not in ["regular", "elective", "honors"]:
                return jsonify({"error": "subject_type must be 'regular', 'elective', or 'honors'"}), 400
            
            elective_group_id = None
            if subject_type in ["elective", "honors"]:
                elective_group_id = str(data.get("elective_group_id", "")).strip()
                if not elective_group_id:
                    return jsonify({
                        "error": f"elective_group_id is required when subject_type is '{subject_type}'"
                    }), 400

            sanitised = {
                "faculty_id":    faculty_id_str,
                "year":          str(data["year"]).strip().upper(),
                "division":      str(data.get("division", "A")).strip().upper(),
                "subject":       str(data["subject"]).strip(),
                "subject_full":  str(data.get("subject_full", data["subject"])).strip(),
                "batches":       batches,
                "theory_hrs":    int(data.get("theory_hrs", 0)),
                "practical_hrs": int(data.get("practical_hrs", 2)),
                "subject_type":  subject_type,
                "elective_group_id": elective_group_id,
            }
        except (TypeError, ValueError) as e:
            return jsonify({"error": f"Invalid field type: {e}"}), 400

        # WH-02 FIX: reject duplicate (faculty_id, year, division, subject) before
        # inserting.  Without this check a double-click or network retry creates two
        # identical workload entries which the scheduler then queues twice.
        existing = workload_collection.find_one({
            "faculty_id": sanitised["faculty_id"],
            "year":       sanitised["year"],
            "division":   sanitised["division"],
            "subject":    sanitised["subject"],
        })
        if existing:
            return jsonify({
                "error": (
                    f"Workload entry already exists for faculty {sanitised['faculty_id']} — "
                    f"{sanitised['year']}-{sanitised['division']} {sanitised['subject']}. "
                    f"Use PUT /api/faculty_workload to update it."
                )
            }), 409

        result = workload_collection.insert_one(sanitised)
        return jsonify({
            "message":     "Workload added successfully",
            "inserted_id": str(result.inserted_id)
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- DELETE FACULTY WORKLOAD ----------
def delete_faculty_workload(data):
    """
    Delete a workload entry by its _id.
    Expected JSON: {"_id": "<workload_id>"}
    """
    try:
        workload_id = data.get("_id")
        if not workload_id or not ObjectId.is_valid(workload_id):
            return jsonify({"error": "Invalid or missing workload ID"}), 400

        result = workload_collection.delete_one({"_id": ObjectId(workload_id)})

        if result.deleted_count == 0:
            return jsonify({"error": "Workload not found"}), 404

        return jsonify({"message": "Workload deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- UPDATE FACULTY WORKLOAD ----------
def update_faculty_workload(data):
    """
    Update a workload entry by its _id.
    Expected JSON:
    {
        "_id": "<workload_id>",
        "subject": "OOPJ",
        "practical_hrs": 3
    }

    Only the fields listed below are accepted — no arbitrary keys can be
    injected into the document via this endpoint.
    """
    try:
        workload_id = data.get("_id")
        if not workload_id or not ObjectId.is_valid(workload_id):
            return jsonify({"error": "Invalid or missing workload ID"}), 400

        # WH-01 FIX (update path): whitelist the fields that are allowed to be
        # updated and apply the same type casts as add_faculty_workload.
        # This prevents a client from overwriting _id, injecting operators, or
        # storing wrong types for fields the scheduler reads numerically.
        UPDATABLE = {
            "subject":       str,
            "subject_full":  str,
            "division":      lambda v: str(v).strip().upper(),
            "year":          lambda v: str(v).strip().upper(),
            "theory_hrs":    int,
            "practical_hrs": int,
            "subject_type":  None,   # Handled separately below
            "elective_group_id": None,  # Handled separately below
            "batches":       None,   # handled separately below
        }

        update_data = {}
        for field, cast in UPDATABLE.items():
            if field not in data:
                continue
            if field == "batches":
                raw = data["batches"]
                try:
                    update_data["batches"] = normalize_batches(raw)
                except (TypeError, ValueError) as e:
                    return jsonify({"error": f"batches must be a list of integers or batch labels: {e}"}), 400
            elif field == "subject_type":
                subject_type = str(data.get("subject_type", "regular")).strip().lower()
                if subject_type not in ["regular", "elective", "honors"]:
                    return jsonify({"error": "subject_type must be 'regular', 'elective', or 'honors'"}), 400
                update_data["subject_type"] = subject_type
            elif field == "elective_group_id":
                elective_group_id = str(data.get("elective_group_id", "")).strip()
                # Validate consistency: if subject_type is elective/honors, group_id required
                existing = workload_collection.find_one({"_id": ObjectId(workload_id)})
                if existing:
                    current_type = existing.get("subject_type", "regular")
                    if subject_type in data:
                        current_type = str(data["subject_type"]).strip().lower()
                    
                    if current_type in ["elective", "honors"] and not elective_group_id:
                        return jsonify({
                            "error": f"elective_group_id required when subject_type is '{current_type}'"
                        }), 400
                update_data["elective_group_id"] = elective_group_id if elective_group_id else None
            else:
                try:
                    update_data[field] = cast(data[field])
                except (TypeError, ValueError) as e:
                    return jsonify({"error": f"Invalid value for '{field}': {e}"}), 400

        if not update_data:
            return jsonify({"error": "No updatable fields provided"}), 400

        result = workload_collection.update_one(
            {"_id": ObjectId(workload_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            return jsonify({"error": "Workload not found"}), 404

        return jsonify({"message": "Workload updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500