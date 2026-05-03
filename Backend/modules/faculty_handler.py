from flask import jsonify
from bson import ObjectId
from config import db
from modules.email_service import send_faculty_welcome_email
from werkzeug.security import generate_password_hash

# Collection for faculty
faculty_collection = db['faculty']

# ---------- Display all faculties ----------
def display_faculty():
    try:
        faculties = list(faculty_collection.find({}))
        # Convert ObjectId to string for JSON serialization
        for faculty in faculties:
            faculty['_id'] = str(faculty['_id'])
        return jsonify(faculties)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Add a new faculty ----------
def add_faculty(data):
    name = data.get('name')
    short_name = data.get('short_name')
    email = data.get('email') # NEW: Extract email
    title = data.get('title')

    # UPDATED: Check for email presence
    if not name or not short_name or not email:
        return jsonify({"error": "Missing name, short_name, or email"}), 400

    # NEW: Check if email already exists to prevent duplicates
    if faculty_collection.find_one({"email": email.lower()}):
        return jsonify({"error": f"Faculty with email '{email}' already exists"}), 400

    try:
        # Set default password for new faculty
        default_password = "password123"
        hashed_password = generate_password_hash(default_password)
        
        faculty_data = {
            "name": name,
            "short_name": short_name,
            "email": email.lower(), # NEW: Save lowercase email
            "role": "faculty",       # NEW: Assign default role for auth compatibility
            "password": hashed_password  # NEW: Set default password
        }
        
        if title:
            faculty_data["title"] = title
        
        result = faculty_collection.insert_one(faculty_data)

        send_faculty_welcome_email(name, email.lower())

        return jsonify({
            "message": f"Faculty '{name}' added successfully!",
            "_id": str(result.inserted_id)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------- Delete a faculty ----------
def delete_faculty(data):
    faculty_id = data.get('_id')

    if not faculty_id:
        return jsonify({"error": "Missing _id"}), 400

    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(faculty_id)
        
        result = faculty_collection.delete_one({"_id": object_id})
        if result.deleted_count == 0:
            return jsonify({"error": f"Faculty with ID '{faculty_id}' not found"}), 404
        return jsonify({"message": f"Faculty deleted successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Update a faculty ----------
def update_faculty(data):
    faculty_id = data.get('_id')
    updates = data.get('updates')  # e.g., {"name": "New Name", "short_name": "NN", "title": "Professor"}

    if not faculty_id or not updates:
        return jsonify({"error": "Missing _id or updates"}), 400

    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(faculty_id)
        
        result = faculty_collection.update_one({"_id": object_id}, {"$set": updates})
        if result.matched_count == 0:
            return jsonify({"error": f"Faculty with ID '{faculty_id}' not found"}), 404
        return jsonify({"message": f"Faculty updated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500