from flask import jsonify
from bson import ObjectId
from config import db

# MongoDB collection
workload_collection = db['workload']


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
        "practical_hrs": 2
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
            # Accept both a list and a single integer
            if not isinstance(raw_batches, list):
                raw_batches = [raw_batches]
            batches = [int(b) for b in raw_batches]

            sanitised = {
                "faculty_id":    faculty_id_str,
                "year":          str(data["year"]).strip().upper(),
                "division":      str(data.get("division", "A")).strip().upper(),
                "subject":       str(data["subject"]).strip(),
                "subject_full":  str(data.get("subject_full", data["subject"])).strip(),
                "batches":       batches,
                "theory_hrs":    int(data.get("theory_hrs", 0)),
                "practical_hrs": int(data.get("practical_hrs", 2)),
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
            "batches":       None,   # handled separately below
        }

        update_data = {}
        for field, cast in UPDATABLE.items():
            if field not in data:
                continue
            if field == "batches":
                raw = data["batches"]
                if not isinstance(raw, list):
                    raw = [raw]
                try:
                    update_data["batches"] = [int(b) for b in raw]
                except (TypeError, ValueError):
                    return jsonify({"error": "batches must be a list of integers"}), 400
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