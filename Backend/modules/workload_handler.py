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

        # Basic validation
        required_fields = ["faculty_id", "year", "subject"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

        result = workload_collection.insert_one(data)
        return jsonify({
            "message": "Workload added successfully",
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
    """
    try:
        workload_id = data.get("_id")
        if not workload_id or not ObjectId.is_valid(workload_id):
            return jsonify({"error": "Invalid or missing workload ID"}), 400

        update_data = {k: v for k, v in data.items() if k != "_id"}

        result = workload_collection.update_one(
            {"_id": ObjectId(workload_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            return jsonify({"error": "Workload not found"}), 404

        return jsonify({"message": "Workload updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
