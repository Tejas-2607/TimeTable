from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enable CORS for all routes
CORS(app)

# Import all handlers
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
    settings_handler,
    auth_handler,
    constraints_handler
)
from functools import wraps

# ============================================================================
# AUTH DECORATORS
# ============================================================================

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        # Remove "Bearer " prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
            
        payload = auth_handler.verify_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        # Add user info to request context
        request.user = payload
        return f(*args, **kwargs)
    
    return decorated

def role_required(role):
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            if request.user.get('role') != role:
                return jsonify({'error': f'Access denied. {role} role required.'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

# ============================================================================
# HOME ENDPOINT
# ============================================================================

@app.route('/')
def home():
    return jsonify({"message": "Flask Timetable API is running!"})


# ============================================================================
# FACULTY ENDPOINTS
# ============================================================================

@app.route('/api/faculty', methods=['GET'])
def get_faculty():
    """Get all faculty members"""
    return faculty_handler.display_faculty()


@app.route('/api/faculty', methods=['POST'])
@role_required('admin')
def add_faculty():
    """Add a new faculty member"""
    data = request.json or {}
    return faculty_handler.add_faculty(data)


@app.route('/api/faculty', methods=['PUT'])
@role_required('admin')
def update_faculty():
    """Update a faculty member"""
    data = request.json or {}
    return faculty_handler.update_faculty(data)


@app.route('/api/faculty', methods=['DELETE'])
@role_required('admin')
def delete_faculty():
    """Delete a faculty member"""
    data = request.json or {}
    return faculty_handler.delete_faculty(data)


# ============================================================================
# LABS ENDPOINTS
# ============================================================================

@app.route('/api/labs', methods=['GET'])
def get_labs():
    """Get all labs"""
    return labs_handler.display_labs()


@app.route('/api/labs', methods=['POST'])
@role_required('admin')
def add_lab():
    """Add a new lab"""
    data = request.json or {}
    return labs_handler.add_lab(data)


@app.route('/api/labs', methods=['PUT'])
@role_required('admin')
def update_lab():
    """Update a lab"""
    data = request.json or {}
    return labs_handler.update_lab(data)


@app.route('/api/labs', methods=['DELETE'])
@role_required('admin')
def delete_lab():
    """Delete a lab"""
    data = request.json or {}
    return labs_handler.delete_lab(data)


@app.route('/api/confirm_labs', methods=['POST'])
@role_required('admin')
def confirm_labs():
    """Confirm labs"""
    data = request.json
    return labs_handler.confirm_labs(data)


# ============================================================================
# CLASS STRUCTURE ENDPOINTS
# ============================================================================

@app.route('/api/class_structure', methods=['GET'])
def get_class_structure():
    """Get class structure"""
    return class_structure_handler.get_class_structure()


@app.route('/api/class_structure', methods=['POST'])
@role_required('admin')
def save_class_structure():
    """Save class structure"""
    data = request.json or {}
    return class_structure_handler.save_class_structure(data)


# ============================================================================
# SUBJECTS ENDPOINTS
# ============================================================================

@app.route('/api/subjects', methods=['POST'])
@role_required('admin')
def save_subjects():
    """Add a new subject"""
    data = request.json
    return subjects_handler.save_subjects(data)


@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    """Get all subjects"""
    return subjects_handler.get_subjects()


@app.route('/api/subjects', methods=['DELETE'])
@role_required('admin')
def delete_subject():
    """Delete a subject"""
    data = request.json
    return subjects_handler.delete_subject(data)


@app.route('/api/subjects', methods=['PUT'])
@role_required('admin')
def update_subject():
    """Update a subject"""
    data = request.json
    return subjects_handler.update_subject(data)


# ============================================================================
# FACULTY WORKLOAD ENDPOINTS
# ============================================================================

@app.route('/api/faculty_workload', methods=['POST'])
@role_required('admin')
def save_workload():
    """Add faculty workload"""
    data = request.json
    return workload_handler.add_faculty_workload(data)


@app.route('/api/faculty_workload', methods=['GET'])
def get_faculty_workload():
    """Get all faculty workloads"""
    return workload_handler.get_faculty_workload()


@app.route('/api/faculty_workload', methods=['DELETE'])
@role_required('admin')
def delete_faculty_workload():
    """Delete faculty workload"""
    data = request.json
    return workload_handler.delete_faculty_workload(data)


@app.route('/api/faculty_workload', methods=['PUT'])
@role_required('admin')
def update_faculty_workload():
    """Update faculty workload"""
    data = request.json
    return workload_handler.update_faculty_workload(data)


# ============================================================================
# MASTER PRACTICAL TIMETABLE ENDPOINTS
# ============================================================================

@app.route('/api/regenerate_master_practical_timetable', methods=['POST'])
@role_required('admin')
def regenerate_master_practical_timetable():
    """
    MAIN ENDPOINT - Regenerate master practical timetable + lectures.

    Pipeline (order matters):
    1. Delete existing master lab timetables and class timetables
    2. timetable_generator  → schedules practicals, saves master lab timetable ONLY
    3. class_timetable_handler → reads master lab timetable, builds class timetables
                                  (single writer — prevents duplicate follow-on entries)
    4. lecture_tt_generator → reads class timetables, fills in lectures, re-saves
    """
    try:
        from config import db

        master_lab_timetable_collection = db['master_lab_timetable']
        class_timetable_col             = db['class_timetable']

        logger.info("=" * 80)
        logger.info("STARTING COMPLETE TIMETABLE GENERATION")
        logger.info("=" * 80)

        # STEP 1: Delete all existing timetable data
        logger.info("\n[STEP 1] Deleting existing timetables...")
        deleted_labs    = master_lab_timetable_collection.delete_many({}).deleted_count
        deleted_classes = class_timetable_col.delete_many({}).deleted_count
        logger.info(f"✓ Deleted {deleted_labs} lab timetables, "
                    f"{deleted_classes} class timetables")

        # STEP 2: Generate master practical timetable (writes to master_lab_timetable only)
        logger.info("\n[STEP 2] Generating master practical timetable...")
        result = timetable_generator.generate()

        if not result or not result.get('success'):
            logger.error("✗ Practical timetable generation failed")
            return jsonify({
                "error": "Failed to generate practical timetable. "
                         "Please verify subject, faculty, and workload data.",
                "detail": result.get('error', '') if result else ''
            }), 400

        leftovers = result.get("leftovers", {})

        # STEP 3: Build class timetables from master lab timetable
        # (this is the ONLY place class timetables are written for practicals)
        logger.info("\n[STEP 3] Building class timetables from master lab timetable...")
        class_timetables_result = class_timetable_handler.generate_class_timetables()
        if not class_timetables_result.get('success'):
            logger.error(f"✗ Class timetable generation failed: "
                         f"{class_timetables_result.get('error')}")
            return jsonify({
                "error": "Failed to build class timetables.",
                "detail": class_timetables_result.get('error', '')
            }), 500
        logger.info(f"✓ {class_timetables_result.get('message', '')}")

        # STEP 4: Fill lectures into class timetables
        logger.info("\n[STEP 4] Generating lecture timetable...")
        lecture_result = lecture_tt_generator.generate()
        logger.info(f"✓ {lecture_result.get('message', '')}")

        if not lecture_result.get('success'):
            logger.warning(
                f"⚠️ Lecture generation had issues: {lecture_result.get('error', '')}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ COMPLETE TIMETABLE GENERATION FINISHED")
        logger.info("=" * 80)

        status_code      = 201
        response_message = "Timetable regenerated successfully!"
        if leftovers:
            unscheduled = sum(len(v) for v in leftovers.values())
            response_message = (f"Timetable generated, but {unscheduled} practical "
                                f"session(s) could not be scheduled.")
            status_code = 206

        return jsonify({
            "message":          response_message,
            "deleted_records":  deleted_labs,
            "labs_generated":   result.get('labs_generated', 0),
            "practicals_scheduled": result.get('practicals_scheduled', 0),
            "class_timetables": {
                "success":            class_timetables_result['success'],
                "message":            class_timetables_result.get('message', ''),
                "timetables_created": class_timetables_result.get('timetables_created', 0),
            },
            "lectures": {
                "success":            lecture_result.get('success', False),
                "message":            lecture_result.get('message', ''),
                "lectures_scheduled": lecture_result.get('lectures_scheduled', 0),
                "leftovers":          lecture_result.get('leftovers', {}),
            },
            "practical_leftovers": leftovers,
        }), status_code

    except Exception as e:
        logger.error(
            f"✗ Error in regenerate_master_practical_timetable: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/master_timetables', methods=['GET'])
def get_all_master_timetables():
    """Get all master practical timetables (lab-wise)"""
    return timetable_handler.get_master_practical_timetable()


@app.route('/api/master_timetable/<lab_name>', methods=['DELETE'])
@role_required('admin')
def delete_master_timetable(lab_name):
    """Delete a specific lab's master timetable"""
    from modules.timetable_handler import master_lab_timetable_collection
    try:
        result = master_lab_timetable_collection.delete_one({'lab_name': lab_name})
        if result.deleted_count > 0:
            return jsonify({'message': f'Master timetable for {lab_name} deleted successfully'}), 200
        return jsonify({'error': f'No master timetable found for {lab_name}'}), 404
    except Exception as e:
        logger.error(f"Error deleting master timetable: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# CLASS TIMETABLE ENDPOINTS - Main Endpoint Only
# ============================================================================

@app.route('/api/class_timetable/<class_name>/<division>', methods=['GET'])
def get_class_timetable_endpoint(class_name, division):
    """
    Get complete timetable for a specific class with LECTURES + PRACTICALS.
    
    Example: GET /api/class_timetable/SY/A
    
    Returns complete timetable showing:
    - Morning: Lectures (10:15, 11:15, 12:15)
    - Lunch: Break (13:15)
    - Afternoon: Practicals (14:15, 15:15, 16:20)
    """
    try:
        if not class_name or not division:
            return jsonify({'error': 'Missing class_name or division'}), 400
        
        class_name = class_name.upper()
        division = division.upper()
        
        # Import here to avoid circular imports
        from config import db
        class_timetable_collection = db['class_timetable']
        
        # Find timetable
        timetable = class_timetable_collection.find_one({
            'class': class_name,
            'division': division
        })
        
        if not timetable:
            return jsonify({
                'error': f'No timetable found for {class_name}-{division}'
            }), 404
        
        # Convert ObjectId to string
        timetable['_id'] = str(timetable['_id'])
        if 'generated_at' in timetable:
            timetable['generated_at'] = timetable['generated_at'].isoformat()
        
        return jsonify(timetable), 200
        
    except Exception as e:
        logger.error(f"Error fetching class timetable: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/class_timetables', methods=['GET'])
def get_all_class_timetables_endpoint():
    """
    Get all class timetables with both lectures and practicals.
    
    Returns list of all class timetables (SY-A, SY-B, TY-A, TY-B, BE-A)
    Each timetable shows:
    - Morning: Lectures (10:15, 11:15, 12:15)
    - Lunch: Break (13:15)
    - Afternoon: Practicals (14:15, 15:15, 16:20)
    """
    try:
        from config import db
        class_timetable_collection = db['class_timetable']
        
        timetables = list(class_timetable_collection.find({}))
        
        for t in timetables:
            t['_id'] = str(t['_id'])
            if 'generated_at' in t:
                t['generated_at'] = t['generated_at'].isoformat()
        
        return jsonify({
            'total': len(timetables),
            'timetables': timetables
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching all class timetables: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/class_timetable/<class_name>/<division>', methods=['DELETE'])
@role_required('admin')
def delete_class_timetable_endpoint(class_name, division):
    """Delete a specific class-division timetable"""
    try:
        from config import db
        class_timetable_collection = db['class_timetable']
        
        result = class_timetable_collection.delete_one({
            'class': class_name.upper(),
            'division': division.upper()
        })
        
        if result.deleted_count > 0:
            return jsonify({'message': f'Timetable for {class_name}-{division} deleted successfully'}), 200
        return jsonify({'error': f'No timetable found for {class_name}-{division}'}), 404
        
    except Exception as e:
        logger.error(f"Error deleting class timetable: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# SETTINGS ENDPOINTS
# ============================================================================

@app.route('/api/settings/timings', methods=['GET'])
def get_timings():
    """Get department timings and calculated slots"""
    return jsonify(settings_handler.get_timings())


@app.route('/api/settings/timings', methods=['POST'])
@role_required('admin')
def save_timings():
    """Save department timings"""
    data = request.json or {}
    return settings_handler.save_timings(data)


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/auth/authenticate', methods=['POST'])
def authenticate():
    """Unified login/registration endpoint"""
    data = request.json or {}
    return auth_handler.login_or_register(data)


# ============================================================================
# SPECIAL CONSTRAINTS ENDPOINTS
# ============================================================================

@app.route('/api/constraints', methods=['GET'])
@token_required
def get_constraints():
    """Get constraints filtered by user role"""
    user_id = request.user.get('sub')
    role = request.user.get('role')
    return constraints_handler.get_constraints(user_id=user_id, role=role)


@app.route('/api/constraints', methods=['POST'])
@token_required
def add_constraint():
    """Add a new constraint"""
    data = request.json or {}
    user_id = request.user.get('sub')
    user_name = request.user.get('name')
    role = request.user.get('role')
    return constraints_handler.add_constraint(data, user_id, user_name, role)


@app.route('/api/constraints/<constraint_id>', methods=['DELETE'])
@token_required
def delete_constraint(constraint_id):
    """Delete a constraint"""
    user_id = request.user.get('sub')
    role = request.user.get('role')
    return constraints_handler.delete_constraint(constraint_id, user_id, role)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == '__main__':
    logger.info("Starting Flask Timetable API...")
    app.run(debug=True,port=5001)