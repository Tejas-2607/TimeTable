from flask import jsonify
from config import db

# Collection for faculty
faculty_collection = db['faculty']

# ---------- Display all faculties ----------
def display_faculty():
    try:
        faculties = list(faculty_collection.find({}, {'_id': 0}))
        return jsonify(faculties)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Add a new faculty ----------
def add_faculty(data):
    name = data.get('name')
    short_name = data.get('short_name')

    if not name or not short_name:
        return jsonify({"error": "Missing name or short_name"}), 400

    # Check if faculty already exists
    existing = faculty_collection.find_one({"name": name})
    if existing:
        return jsonify({"error": f"Faculty '{name}' already exists"}), 400

    try:
        faculty_collection.insert_one({
            "name": name,
            "short_name": short_name
        })
        return jsonify({"message": f"Faculty '{name}' added successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Delete a faculty ----------
def delete_faculty(data):
    name = data.get('name')

    if not name:
        return jsonify({"error": "Missing name"}), 400

    try:
        result = faculty_collection.delete_one({"name": name})
        if result.deleted_count == 0:
            return jsonify({"error": f"Faculty '{name}' not found"}), 404
        return jsonify({"message": f"Faculty '{name}' deleted successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Update a faculty ----------
def update_faculty(data):
    name = data.get('name')
    updates = data.get('updates')  # e.g., {"name": "New Name", "short_name": "NN"}

    if not name or not updates:
        return jsonify({"error": "Missing name or updates"}), 400

    try:
        result = faculty_collection.update_one({"name": name}, {"$set": updates})
        if result.matched_count == 0:
            return jsonify({"error": f"Faculty '{name}' not found"}), 404
        return jsonify({"message": f"Faculty '{name}' updated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
