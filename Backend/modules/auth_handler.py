# modules/auth_handler.py

import jwt
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from config import db, SECRET_KEY
from datetime import datetime, timedelta

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