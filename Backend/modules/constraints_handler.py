# modules/constraints_handler.py

from flask import jsonify, request
from bson import ObjectId
from config import db
from datetime import datetime

constraints_collection = db['constraints']


def get_constraints():
    try:
        user = getattr(request, "user", None)

        if user and user.get("role") == "faculty":
            query = {
                "$or": [
                    {"requested_by_user_id": user.get("sub")},
                    {"faculty_name": user.get("name")}
                ]
            }
        else:
            query = {}

        constraints = list(constraints_collection.find(query))

        for c in constraints:
            c["_id"] = str(c["_id"])
            if "created_at" in c:
                c["created_at"] = c["created_at"].isoformat()
            if "reviewed_at" in c and c["reviewed_at"]:
                c["reviewed_at"] = c["reviewed_at"].isoformat()

        return jsonify(constraints), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def add_constraint(data):
    try:
        user = getattr(request, "user", {})
        role = (user.get("role") or "").lower()

        constraint_type = data.get("type")
        day = data.get("day")
        time_slot = data.get("time_slot")

        if not constraint_type or not day or not time_slot:
            return jsonify({"error": "type, day, time_slot required"}), 400

        # CH-01 FIX: validate required fields for fixed_time constraints
        if role == "faculty":
            faculty_name = user.get("name")
        else:
            faculty_name = data.get("faculty_name", user.get("name"))

        if constraint_type == "fixed_time":
            # Accept both 'class' and 'year' from frontend (year → class mapping)
            class_name = data.get("class") or data.get("year")
            division = data.get("division")
            subject = data.get("subject")

            if not all([class_name, division, subject, faculty_name]):
                return jsonify({
                    "error": "fixed_time constraints require: class/year, division, subject, faculty_name"
                }), 400

        # Get faculty short name
        from config import db
        faculty_collection = db['faculty']
        faculty_doc = faculty_collection.find_one({"name": faculty_name})
        faculty_short = faculty_doc.get("short_name", faculty_name) if faculty_doc else faculty_name

        # ✅ duplicate check — more comprehensive for fixed_time
        if constraint_type == "fixed_time":
            # CH-02 FIX: check for both "class" and "year" fields since we're migrating
            class_val = data.get("class") or data.get("year")
            existing = constraints_collection.find_one({
                "$or": [
                    {
                        "type": constraint_type,
                        "class": class_val,
                        "division": data.get("division"),
                        "subject": data.get("subject"),
                        "day": day,
                        "time_slot": time_slot
                    },
                    {
                        "type": constraint_type,
                        "year": class_val,  # Check old "year" field too
                        "division": data.get("division"),
                        "subject": data.get("subject"),
                        "day": day,
                        "time_slot": time_slot
                    }
                ]
            })
        else:
            existing = constraints_collection.find_one({
                "type": constraint_type,
                "faculty_name": faculty_name,
                "day": day,
                "time_slot": time_slot
            })

        if existing:
            return jsonify({"error": "Constraint already exists"}), 409

        # CH-01 FIX: use "class" not "year" so lecture_tt_generator can read it
        # Map year → class for new constraints
        class_val = data.get("class") or data.get("year")
        new_constraint = {
            "faculty_name": faculty_name,
            "faculty_short": faculty_short,
            "type": constraint_type,
            "day": day,
            "time_slot": time_slot,
            "class": class_val,           # FIXED: renamed from "year"
            "year": class_val,            # For frontend display
            "division": data.get("division"),
            "subject": data.get("subject"),
            "description": data.get("description", ""),
            "status": "pending" if role == "faculty" else "approved",
            "review_reason": "",
            "requested_by_user_id": user.get("sub"),
            "requested_by_role": role,
            "reviewed_by_user_id": user.get("sub") if role == "admin" else None,
            "reviewed_by_name": user.get("name") if role == "admin" else None,
            "reviewed_at": datetime.utcnow() if role == "admin" else None,
            "created_at": datetime.utcnow()
        }

        result = constraints_collection.insert_one(new_constraint)

        return jsonify({
            "message": "Constraint request submitted" if role == "faculty" else "Constraint added",
            "id": str(result.inserted_id)
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def delete_constraint(constraint_id):
    try:
        user = getattr(request, "user", {})

        query = {"_id": ObjectId(constraint_id)}

        if user.get("role") != "admin":
            query["$or"] = [
                {"requested_by_user_id": user.get("sub")},
                {"faculty_name": user.get("name")}
            ]

        result = constraints_collection.delete_one(query)

        if result.deleted_count == 0:
            return jsonify({"error": "Not found or not allowed"}), 404

        return jsonify({"message": "Constraint deleted"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def review_constraint(constraint_id, data):
    try:
        user = getattr(request, "user", {})
        if user.get("role") != "admin":
            return jsonify({"error": "Only admin can review requests"}), 403

        decision = (data.get("status") or "").strip().lower()
        if decision not in ["approved", "rejected"]:
            return jsonify({"error": "status must be 'approved' or 'rejected'"}), 400

        reason = (data.get("review_reason") or "").strip()
        if decision == "rejected" and not reason:
            return jsonify({"error": "Rejection reason is required"}), 400

        update_data = {
            "status": decision,
            "review_reason": reason,
            "reviewed_by_user_id": user.get("sub"),
            "reviewed_by_name": user.get("name"),
            "reviewed_at": datetime.utcnow()
        }

        result = constraints_collection.update_one(
            {"_id": ObjectId(constraint_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            return jsonify({"error": "Constraint request not found"}), 404

        return jsonify({"message": f"Constraint request {decision}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500