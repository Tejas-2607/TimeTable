from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import logging
from functools import wraps
import jwt
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ✅ Load config
app.config.from_object(config)
SECRET_KEY = app.config.get("SECRET_KEY", "fallback-secret")


# ========================================================================
# IMPORT MODULES
# ========================================================================

from modules import (
    faculty_handler,
    labs_handler,
    timetable_handler,
    class_structure_handler,
    subjects_handler,
    workload_handler,
    class_timetable_handler,
    timetable_generator,
    lecture_tt_generator,
)

# NEW modules
from modules import auth_handler, settings_handler, constraints_handler


# ========================================================================
# AUTH DECORATORS
# ========================================================================

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            try:
                token = request.headers["Authorization"].split(" ")[1]
            except:
                return jsonify({"error": "Invalid Authorization header"}), 401

        if not token:
            return jsonify({"error": "Token missing"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            data['role'] = data.get('role', 'faculty').lower()
            request.user = data
        except Exception:
            return jsonify({"error": "Invalid or expired token"}), 401

        return f(*args, **kwargs)
    return decorated


def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, "user"):
                return jsonify({"error": "Unauthorized"}), 401

            user_role = request.user.get("role", "").lower()
            if user_role != role.lower():
                return jsonify({"error": "Forbidden"}), 403

            return f(*args, **kwargs)
        return decorated
    return wrapper


# ========================================================================
# HOME
# ========================================================================

@app.route('/')
def home():
    return jsonify({"message": "Flask Timetable API is running!"})


# ========================================================================
# AUTH (PUBLIC)
# ========================================================================

@app.route('/api/auth/authenticate', methods=['POST'])
def authenticate():
    data = request.json or {}
    return auth_handler.authenticate(data)


@app.route('/api/auth/reset-password', methods=['POST'])
@token_required
def reset_password():
    data = request.json or {}
    user_id = request.user.get('sub')
    return auth_handler.reset_password(user_id, data)


@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json or {}
    return auth_handler.forgot_password(data)


# ========================================================================
# SETTINGS
# ========================================================================

@app.route('/api/settings/timings', methods=['GET'])
def get_timings():
    return settings_handler.get_timings()


@app.route('/api/settings/timings', methods=['POST'])
@token_required
@role_required('admin')
def save_timings():
    data = request.json or {}
    return settings_handler.save_timings(data)


@app.route('/api/settings/lab-timings', methods=['GET'])
def get_lab_timings():
    return settings_handler.get_lab_timings()


@app.route('/api/settings/lab-timings', methods=['POST'])
@token_required
@role_required('admin')
def save_lab_timings():
    data = request.json or {}
    return settings_handler.save_lab_timings(data)


# ========================================================================
# CONSTRAINTS
# ========================================================================

@app.route('/api/constraints', methods=['GET'])
@token_required
def get_constraints():
    return constraints_handler.get_constraints()


@app.route('/api/constraints', methods=['POST'])
@token_required
def add_constraint():
    data = request.json or {}
    return constraints_handler.add_constraint(data)


@app.route('/api/constraints/<id>', methods=['DELETE'])
@token_required
def delete_constraint(id):
    return constraints_handler.delete_constraint(id)


# ========================================================================
# FACULTY
# ========================================================================

@app.route('/api/faculty', methods=['GET'])
@token_required
def get_faculty():
    return faculty_handler.display_faculty()


@app.route('/api/faculty', methods=['POST'])
@token_required
@role_required('admin')
def add_faculty():
    data = request.json or {}
    return faculty_handler.add_faculty(data)


@app.route('/api/faculty', methods=['PUT'])
@token_required
@role_required('admin')
def update_faculty():
    data = request.json or {}
    return faculty_handler.update_faculty(data)


@app.route('/api/faculty', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_faculty():
    data = request.json or {}
    return faculty_handler.delete_faculty(data)


# ========================================================================
# LABS
# ========================================================================

@app.route('/api/labs', methods=['GET'])
@token_required
def get_labs():
    return labs_handler.display_labs()


@app.route('/api/labs', methods=['POST'])
@token_required
@role_required('admin')
def add_lab():
    data = request.json or {}
    return labs_handler.add_lab(data)


@app.route('/api/labs', methods=['PUT'])
@token_required
@role_required('admin')
def update_lab():
    data = request.json or {}
    return labs_handler.update_lab(data)


@app.route('/api/labs', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_lab():
    data = request.json or {}
    return labs_handler.delete_lab(data)


@app.route('/api/confirm_labs', methods=['POST'])
@token_required
@role_required('admin')
def confirm_labs():
    data = request.json
    return labs_handler.confirm_labs(data)


# ========================================================================
# CLASS STRUCTURE
# ========================================================================

@app.route('/api/class_structure', methods=['GET'])
@token_required
def get_class_structure():
    return class_structure_handler.get_class_structure()


@app.route('/api/class_structure', methods=['POST'])
@token_required
@role_required('admin')
def save_class_structure():
    data = request.json or {}
    return class_structure_handler.save_class_structure(data)


# ========================================================================
# SUBJECTS
# ========================================================================

@app.route('/api/subjects', methods=['POST'])
@token_required
@role_required('admin')
def save_subjects():
    data = request.json
    return subjects_handler.save_subjects(data)


@app.route('/api/subjects', methods=['GET'])
@token_required
def get_subjects():
    return subjects_handler.get_subjects()


@app.route('/api/subjects', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_subject():
    data = request.json
    return subjects_handler.delete_subject(data)


@app.route('/api/subjects', methods=['PUT'])
@token_required
@role_required('admin')
def update_subject():
    data = request.json
    return subjects_handler.update_subject(data)


# ========================================================================
# FACULTY WORKLOAD
# ========================================================================

@app.route('/api/faculty_workload', methods=['POST'])
@token_required
@role_required('admin')
def save_workload():
    data = request.json
    return workload_handler.add_faculty_workload(data)


@app.route('/api/faculty_workload', methods=['GET'])
@token_required
def get_faculty_workload():
    return workload_handler.get_faculty_workload()


@app.route('/api/faculty_workload', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_faculty_workload():
    data = request.json
    return workload_handler.delete_faculty_workload(data)


@app.route('/api/faculty_workload', methods=['PUT'])
@token_required
@role_required('admin')
def update_faculty_workload():
    data = request.json
    return workload_handler.update_faculty_workload(data)


# ========================================================================
# MASTER PRACTICAL TIMETABLE
# ========================================================================

@app.route('/api/regenerate_master_practical_timetable', methods=['POST'])
@token_required
@role_required('admin')
def regenerate_master_practical_timetable():
    from config import db

    master_col = db['master_lab_timetable']
    class_col  = db['class_timetable']

    logger.info("=" * 80)
    logger.info("STARTING COMPLETE TIMETABLE GENERATION")
    logger.info("=" * 80)

    snapshot_master = list(master_col.find({}))
    snapshot_class  = list(class_col.find({}))

    def _rollback(reason: str):
        logger.error(f"Rolling back due to: {reason}")
        master_col.delete_many({})
        class_col.delete_many({})
        if snapshot_master:
            master_col.insert_many(snapshot_master)
        if snapshot_class:
            class_col.insert_many(snapshot_class)

    try:
        master_col.delete_many({})
        class_col.delete_many({})

        result = timetable_generator.generate()

        if not result or not result.get('success'):
            _rollback("practical generation failed")
            return jsonify({"error": "Practical generation failed"}), 400

        class_result = class_timetable_handler.generate_class_timetables()

        if not class_result.get('success'):
            _rollback("class timetable failed")
            return jsonify({"error": "Class timetable failed"}), 500

        lecture_result = lecture_tt_generator.generate()

        if not lecture_result.get('success'):
            _rollback("lecture generation failed")
            return jsonify({"error": "Lecture generation failed"}), 500

        return jsonify({"message": "Timetable generated successfully"}), 201

    except Exception as e:
        _rollback(str(e))
        return jsonify({"error": str(e)}), 500


# ========================================================================
# TIMETABLES
# ========================================================================

@app.route('/api/master_timetables', methods=['GET'])
@token_required
def get_master_timetables():
    return timetable_handler.get_master_practical_timetable()


@app.route('/api/class_timetables', methods=['GET'])
@token_required
def get_class_timetables():
    return class_timetable_handler.get_all_class_timetables()


# ========================================================================
# RUN
# ========================================================================

if __name__ == '__main__':
    logger.info("Starting Flask Timetable API…")
    app.run(debug=True)