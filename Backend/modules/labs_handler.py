from flask import jsonify
from bson import ObjectId
from config import db

# Collection for labs
labs_collection = db['labs']

# ---------- Display all labs ----------
def display_labs():
    try:
        labs = list(labs_collection.find({}))
        # Convert ObjectId to string for JSON serialization
        for lab in labs:
            lab['_id'] = str(lab['_id'])
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
        result = labs_collection.insert_one({
            "name": name,
            "short_name": short_name
        })
        return jsonify({
            "message": f"Lab '{name}' added successfully!",
            "_id": str(result.inserted_id)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Delete a lab ----------
def delete_lab(data):
    lab_id = data.get('_id')

    if not lab_id:
        return jsonify({"error": "Missing _id"}), 400

    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(lab_id)
        
        result = labs_collection.delete_one({"_id": object_id})
        if result.deleted_count == 0:
            return jsonify({"error": f"Lab with ID '{lab_id}' not found"}), 404
        return jsonify({"message": f"Lab deleted successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Update a lab ----------
def update_lab(data):
    lab_id = data.get('_id')
    updates = data.get('updates')  # e.g., {"name": "New Lab Name", "short_name": "NL"}

    if not lab_id or not updates:
        return jsonify({"error": "Missing _id or updates"}), 400

    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(lab_id)
        
        result = labs_collection.update_one({"_id": object_id}, {"$set": updates})
        if result.matched_count == 0:
            return jsonify({"error": f"Lab with ID '{lab_id}' not found"}), 404
        return jsonify({"message": f"Lab updated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Confirm labs ----------
def confirm_labs(data):
    """
    Custom function: confirm labs (for example, set a 'confirmed' flag)
    Expected data: {"lab_ids": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"]}
    """
    lab_ids = data.get('lab_ids', [])

    if not lab_ids:
        return jsonify({"error": "No labs provided for confirmation"}), 400

    try:
        # Convert string IDs to ObjectIds
        object_ids = [ObjectId(lab_id) for lab_id in lab_ids]
        
        result = labs_collection.update_many(
            {"_id": {"$in": object_ids}},
            {"$set": {"confirmed": True}}
        )
        return jsonify({
            "message": f"{result.modified_count} labs confirmed successfully!"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500