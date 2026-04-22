# modules/auth_handler.py

import jwt
import datetime
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from config import db, SECRET_KEY
faculty_collection = db['faculty']

def login_or_register(data):
    """
    Unified Login and Registration for Faculty.
    If email doesn't exist: Register (Create Faculty + Password)
    If email exists: Login (Verify Password)
    """
    email = data.get('email', '').strip().lower()
    password = data.get('password')
    full_name = data.get('name', '').strip()
    short_name = data.get('short_name', '').strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Find faculty by email
    faculty = faculty_collection.find_one({"email": email})

    if not faculty:
        # REGISTRATION FLOW
        if not full_name or not short_name:
            return jsonify({
                "error": "Faculty not found. Please provide name and short_name to register."
            }), 404

        # Check if they exist by Name instead (Onboarding existing record)
        existing_by_name = faculty_collection.find_one({"name": full_name})
        hashed_password = generate_password_hash(password)
        
        if existing_by_name:
            # If they already have an email, they should login with THAT email
            if existing_by_name.get('email'):
                return jsonify({
                    "error": f"Faculty '{full_name}' is already registered with email: {existing_by_name.get('email')}. Please use that to login."
                }), 400
            
            # Onboard existing record: set email and password
            faculty_collection.update_one(
                {"_id": existing_by_name["_id"]},
                {"$set": {
                    "email": email,
                    "password": hashed_password,
                    "short_name": short_name, # Update short name too if provided
                    "updated_at": datetime.datetime.utcnow()
                }}
            )
            faculty_id = str(existing_by_name["_id"])
            message = "Account linked and registered successfully"
        else:
            # Create completely new faculty
            new_faculty = {
                "name": full_name,
                "short_name": short_name,
                "email": email,
                "password": hashed_password,
                "created_at": datetime.datetime.utcnow()
            }
            result = faculty_collection.insert_one(new_faculty)
            faculty_id = str(result.inserted_id)
            message = "Registration successful"
        
        token = _generate_token(faculty_id, full_name, email, role="faculty")
        
        return jsonify({
            "message": message,
            "token": token,
            "user": {
                "id": faculty_id,
                "name": full_name,
                "email": email,
                "short_name": short_name,
                "role": "faculty"
            }
        }), 201

    else:
        # LOGIN FLOW (checks password for existing email)
        if not check_password_hash(faculty.get('password', ''), password):
            return jsonify({"error": "Invalid password. Use the password you set during registration."}), 401
        
        faculty_id = str(faculty['_id'])
        full_name = faculty.get('name')
        role = faculty.get('role', 'faculty')
        
        token = _generate_token(faculty_id, full_name, email, role=role)
        
        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "id": faculty_id,
                "name": full_name,
                "email": email,
                "short_name": faculty.get('short_name'),
                "role": role
            }
        }), 200

def _generate_token(user_id, name, email, role="faculty"):
    """Generate JWT token"""
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
        'iat': datetime.datetime.utcnow(),
        'sub': user_id,
        'name': name,
        'email': email,
        'role': role
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
