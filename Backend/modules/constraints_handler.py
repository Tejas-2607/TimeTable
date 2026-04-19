# modules/constraints_handler.py

from flask import jsonify
from bson import ObjectId
from config import db
import datetime

constraints_collection = db['constraints']

def get_constraints(user_id=None, role=None):
    """
    Get constraints. 
    Admin sees all. 
    Faculty sees only their own.
    """
    try:
        query = {}
        if role == 'faculty':
            query = {'user_id': user_id}
            
        constraints = list(constraints_collection.find(query))
        
        # Convert ObjectId to string
        for c in constraints:
            c['_id'] = str(c['_id'])
            if 'created_at' in c:
                c['created_at'] = c['created_at'].isoformat()
                
        return jsonify(constraints), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def add_constraint(data, user_id, user_name, role):
    """
    Add a new constraint.
    """
    try:
        constraint_type = data.get('type') # 'preferred_off' or 'fixed_time'
        day = data.get('day')
        time_slot = data.get('time_slot')
        description = data.get('description', '')
        year = data.get('year', '')
        division = data.get('division', '')
        subject = data.get('subject', '')
        faculty_name = data.get('faculty_name', user_name)
        
        if not constraint_type or not day or not time_slot:
            return jsonify({"error": "Type, day, and time_slot are required"}), 400
            
        new_constraint = {
            "user_id": user_id,
            "user_name": user_name,
            "faculty_name": faculty_name,
            "role": role,
            "type": constraint_type,
            "day": day,
            "time_slot": time_slot,
            "description": description,
            "year": year,
            "division": division,
            "subject": subject,
            "created_at": datetime.datetime.utcnow()
        }
        
        result = constraints_collection.insert_one(new_constraint)
        return jsonify({
            "message": "Constraint added successfully",
            "id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def delete_constraint(constraint_id, user_id, role):
    """
    Delete a constraint.
    Admin can delete any.
    Faculty can only delete their own.
    """
    try:
        query = {"_id": ObjectId(constraint_id)}
        if role != 'admin':
            query["user_id"] = user_id
            
        result = constraints_collection.delete_one(query)
        if result.deleted_count > 0:
            return jsonify({"message": "Constraint deleted successfully"}), 200
        return jsonify({"error": "Constraint not found or access denied"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
