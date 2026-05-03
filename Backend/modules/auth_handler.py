# modules/auth_handler.py

import jwt
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from config import db, SECRET_KEY
from datetime import datetime, timedelta
from bson import ObjectId

faculty_collection = db['faculty']


def authenticate(data):
    email = data.get('email', '').strip().lower()
    password = data.get('password')
    full_name = data.get('name', '').strip()
    short_name = data.get('short_name', '').strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    faculty = faculty_collection.find_one({"email": email})

    # ================= REGISTER =================
    if not faculty:
        if not full_name or not short_name:
            return jsonify({
                "error": "Faculty not found. Please register by providing full name and short name."
            }), 404

        hashed_password = generate_password_hash(password)

        new_faculty = {
            "name": full_name,
            "short_name": short_name,
            "email": email,
            "password": hashed_password,
            "role": "faculty",
            "title": data.get("title", ""),
            "created_at": datetime.utcnow()
        }

        result = faculty_collection.insert_one(new_faculty)

        token = _generate_token(
            str(result.inserted_id),
            full_name,
            email,
            "faculty"
        )

        return jsonify({
            "message": "Registration successful",
            "token": token,
            "user": {
                "id": str(result.inserted_id),
                "name": full_name,
                "email": email,
                "short_name": short_name,
                "title": data.get("title", ""),
                "role": "faculty"
            }
        }), 201

    # ================= LOGIN =================
    if not check_password_hash(faculty.get('password', ''), password):
        return jsonify({"error": "Invalid password"}), 401

    token = _generate_token(
        str(faculty['_id']),
        faculty.get("name"),
        email,
        faculty.get("role", "faculty")
    )

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "id": str(faculty['_id']),
            "name": faculty.get("name"),
            "email": email,
            "short_name": faculty.get("short_name"),
            "role": faculty.get("role", "faculty")
        }
    }), 200


def reset_password(user_id, data):
    """Reset password for authenticated user"""
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not current_password or not new_password or not confirm_password:
        return jsonify({"error": "Current password, new password, and confirm password are required"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "New password and confirm password do not match"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    try:
        faculty = faculty_collection.find_one({"_id": ObjectId(user_id)})
        if not faculty:
            return jsonify({"error": "Faculty not found"}), 404

        # Verify current password
        if not check_password_hash(faculty.get('password', ''), current_password):
            return jsonify({"error": "Current password is incorrect"}), 401

        # Update password
        hashed_password = generate_password_hash(new_password)
        faculty_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password": hashed_password, "password_updated_at": datetime.utcnow()}}
        )

        return jsonify({"message": "Password updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def forgot_password(data):
    """Reset password for unauthenticated user using email"""
    email = data.get('email', '').strip().lower()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not email or not current_password or not new_password or not confirm_password:
        return jsonify({"error": "Email, current password, new password, and confirm password are required"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "New password and confirm password do not match"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    try:
        faculty = faculty_collection.find_one({"email": email})
        if not faculty:
            return jsonify({"error": "Faculty with this email not found"}), 404

        # Verify current password
        if not check_password_hash(faculty.get('password', ''), current_password):
            return jsonify({"error": "Current password is incorrect"}), 401

        # Update password
        hashed_password = generate_password_hash(new_password)
        faculty_collection.update_one(
            {"email": email},
            {"$set": {"password": hashed_password, "password_updated_at": datetime.utcnow()}}
        )

        return jsonify({"message": "Password reset successfully. Please login with your new password."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _generate_token(user_id, name, email, role):
    payload = {
        "sub": user_id,
        "name": name,
        "email": email,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")