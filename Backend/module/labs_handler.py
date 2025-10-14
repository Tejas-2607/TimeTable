from flask import jsonify
from config import db

# Collection for labs
labs_collection = db['labs']

# ---------- Display all labs ----------
def display_labs():
    try:
        labs = list(labs_collection.find({}, {'_id': 0}))
        return jsonify(labs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Add a new lab ----------
def add_lab(data):
    name = data.get('name')
    short_name = data.get('short_name')

    if not name or not short_name:
        return jsonify({"error": "Missing name or short_name"}), 400

    # Check if lab already exists
    existing = labs_collection.find_one({"name": name})
    if existing:
        return jsonify({"error": f"Lab '{name}' already exists"}), 400

    try:
        labs_collection.insert_one({
            "name": name,
            "short_name": short_name
        })
        return jsonify({"message": f"Lab '{name}' added successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Delete a lab ----------
def delete_lab(data):
    name = data.get('name')

    if not name:
        return jsonify({"error": "Missing name"}), 400

    try:
        result = labs_collection.delete_one({"name": name})
        if result.deleted_count == 0:
            return jsonify({"error": f"Lab '{name}' not found"}), 404
        return jsonify({"message": f"Lab '{name}' deleted successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Update a lab ----------
def update_lab(data):
    name = data.get('name')
    updates = data.get('updates')  # e.g., {"name": "New Lab Name", "short_name": "NL"}

    if not name or not updates:
        return jsonify({"error": "Missing name or updates"}), 400

    try:
        result = labs_collection.update_one({"name": name}, {"$set": updates})
        if result.matched_count == 0:
            return jsonify({"error": f"Lab '{name}' not found"}), 404
        return jsonify({"message": f"Lab '{name}' updated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Confirm labs ----------
def confirm_labs(data):
    """
    Custom function: confirm labs (for example, set a 'confirmed' flag)
    Expected data: {"lab_names": ["Lab1", "Lab2"]}
    """
    lab_names = data.get('lab_names', [])

    if not lab_names:
        return jsonify({"error": "No labs provided for confirmation"}), 400

    try:
        result = labs_collection.update_many(
            {"name": {"$in": lab_names}},
            {"$set": {"confirmed": True}}
        )
        return jsonify({
            "message": f"{result.modified_count} labs confirmed successfully!"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
