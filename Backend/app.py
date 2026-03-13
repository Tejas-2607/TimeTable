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
    lecture_tt_generator
)

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
def add_faculty():
    """Add a new faculty member"""
    data = request.json or {}
    return faculty_handler.add_faculty(data)


@app.route('/api/faculty', methods=['PUT'])
def update_faculty():
    """Update a faculty member"""
    data = request.json or {}
    return faculty_handler.update_faculty(data)


@app.route('/api/faculty', methods=['DELETE'])
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
def add_lab():
    """Add a new lab"""
    data = request.json or {}
    return labs_handler.add_lab(data)


@app.route('/api/labs', methods=['PUT'])
def update_lab():
    """Update a lab"""
    data = request.json or {}
    return labs_handler.update_lab(data)


@app.route('/api/labs', methods=['DELETE'])
def delete_lab():
    """Delete a lab"""
    data = request.json or {}
    return labs_handler.delete_lab(data)


@app.route('/api/confirm_labs', methods=['POST'])
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
def save_class_structure():
    """Save class structure"""
    data = request.json or {}
    return class_structure_handler.save_class_structure(data)


# ============================================================================
# SUBJECTS ENDPOINTS
# ============================================================================

@app.route('/api/subjects', methods=['POST'])
def save_subjects():
    """Add a new subject"""
    data = request.json
    return subjects_handler.save_subjects(data)


@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    """Get all subjects"""
    return subjects_handler.get_subjects()


@app.route('/api/subjects', methods=['DELETE'])
def delete_subject():
    """Delete a subject"""
    data = request.json
    return subjects_handler.delete_subject(data)


@app.route('/api/subjects', methods=['PUT'])
def update_subject():
    """Update a subject"""
    data = request.json
    return subjects_handler.update_subject(data)


# ============================================================================
# FACULTY WORKLOAD ENDPOINTS
# ============================================================================

@app.route('/api/faculty_workload', methods=['POST'])
def save_workload():
    """Add faculty workload"""
    data = request.json
    return workload_handler.add_faculty_workload(data)


@app.route('/api/faculty_workload', methods=['GET'])
def get_faculty_workload():
    """Get all faculty workloads"""
    return workload_handler.get_faculty_workload()


@app.route('/api/faculty_workload', methods=['DELETE'])
def delete_faculty_workload():
    """Delete faculty workload"""
    data = request.json
    return workload_handler.delete_faculty_workload(data)


@app.route('/api/faculty_workload', methods=['PUT'])
def update_faculty_workload():
    """Update faculty workload"""
    data = request.json
    return workload_handler.update_faculty_workload(data)


# ============================================================================
# MASTER PRACTICAL TIMETABLE ENDPOINTS
# ============================================================================

@app.route('/api/regenerate_master_practical_timetable', methods=['POST'])
def regenerate_master_practical_timetable():
    """
    MAIN ENDPOINT - Regenerate master practical timetable + auto-generate lectures.
    
    This is the ONLY button in frontend that:
    1. Deletes existing timetables
    2. Generates master practical timetable (lab-wise)
    3. Automatically generates class timetables from master timetable
    4. **AUTOMATICALLY GENERATES LECTURES** ← New!
    5. Returns complete status
    
    This is a complete "Generate All Timetables" endpoint.
    """
    try:
        from config import db

        master_lab_timetable_collection = db['master_lab_timetable']

        logger.info("=" * 80)
        logger.info("STARTING COMPLETE TIMETABLE GENERATION")
        logger.info("=" * 80)

        # STEP 1: Delete existing timetable data
        logger.info("\n[STEP 1] Deleting existing timetables...")
        deleted_count = master_lab_timetable_collection.delete_many({}).deleted_count
        logger.info(f"✓ Deleted {deleted_count} existing lab timetables")

        # STEP 2: Generate master practical timetable
        logger.info("\n[STEP 2] Generating master practical timetable...")
        result = timetable_generator.generate()

        if not result:
            logger.error("✗ Timetable generation failed")
            return jsonify({
                "error": "Failed to generate new timetable. Please verify subject, faculty, and workload data."
            }), 400

        # --- LEFTOVER CHECK AND REPORT ---
        leftovers = result.get("leftovers", {})
        total_leftovers = 0
        for year_dict in leftovers.values():
            if isinstance(year_dict, dict):
                for div_data in year_dict.values():
                    if isinstance(div_data, dict) and 'count' in div_data:
                        total_leftovers += div_data['count']
                    elif isinstance(div_data, list):
                        total_leftovers += len(div_data)

        response_message = "Master practical timetable regenerated successfully!"
        status_code = 201
        
        if total_leftovers > 0:
            response_message = f"Timetable generated, but {total_leftovers} assignments were NOT scheduled."
            status_code = 206

        # STEP 3: Store each lab's schedule
        logger.info("\n[STEP 3] Storing master lab timetables...")
        labs_schedule = result.get("labs", {})
        for lab_name, schedule in labs_schedule.items():
            master_lab_timetable_collection.insert_one({
                "lab_name": lab_name,
                "schedule": schedule,
                "generated_at": datetime.now()
            })
        logger.info(f"✓ Stored {len(labs_schedule)} lab timetables")

        # STEP 4: Generate class timetables automatically
        logger.info("\n[STEP 4] Generating class timetables...")
        class_timetables_result = class_timetable_handler.generate_class_timetables()
        logger.info(f"✓ {class_timetables_result.get('message', '')}")

        # STEP 5: **NEW** - AUTOMATICALLY GENERATE LECTURES
        logger.info("\n[STEP 5] Generating lecture timetable (AUTO)...")
        lecture_result = lecture_tt_generator.generate()
        logger.info(f"✓ {lecture_result.get('message', '')}")
        
        if not lecture_result.get('success'):
            logger.warning(f"⚠️ Lecture generation had issues: {lecture_result.get('error', '')}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ COMPLETE TIMETABLE GENERATION FINISHED SUCCESSFULLY!")
        logger.info("=" * 80)

        return jsonify({
            "message": response_message,
            "deleted_records": deleted_count,
            "labs_generated": len(labs_schedule),
            "class_timetables": {
                "success": class_timetables_result['success'],
                "message": class_timetables_result.get('message', ''),
                "timetables_created": class_timetables_result.get('timetables_created', 0)
            },
            "lectures": {
                "success": lecture_result.get('success', False),
                "message": lecture_result.get('message', ''),
                "lectures_scheduled": lecture_result.get('lectures_scheduled', 0),
                "leftovers": lecture_result.get('leftovers', {})
            },
            "practical_leftovers": leftovers
        }), status_code

    except Exception as e:
        logger.error(f"✗ Error in regenerate_master_practical_timetable: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/master_timetables', methods=['GET'])
def get_all_master_timetables():
    """Get all master practical timetables (lab-wise)"""
    return timetable_handler.get_master_practical_timetable()


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
    app.run(debug=True)