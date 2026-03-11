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
    timetable_generator
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
    Regenerate master practical timetable from workload.
    
    This endpoint:
    1. Deletes existing master timetable
    2. Generates new master practical timetable (lab-wise)
    3. Automatically generates class timetables from master timetable
    4. Returns status of both generations
    """
    try:
        from config import db

        master_lab_timetable_collection = db['master_lab_timetable']

        logger.info("Starting master practical timetable regeneration...")

        # 1️⃣ Delete existing timetable data
        deleted_count = master_lab_timetable_collection.delete_many({}).deleted_count
        logger.info(f"Deleted {deleted_count} existing lab timetables")

        # 2️⃣ Generate new timetable using parallel scheduling algorithm
        logger.info("Generating master practical timetable...")
        result = timetable_generator.generate({})

        if not result:
            logger.error("Timetable generation failed")
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
            response_message = f"Timetable generated, but {total_leftovers} assignments were NOT scheduled. Check the 'leftovers' report for details."
            status_code = 206

        # 3️⃣ Store each lab's schedule as an independent document
        labs_schedule = result.get("labs", {})
        for lab_name, schedule in labs_schedule.items():
            master_lab_timetable_collection.insert_one({
                "lab_name": lab_name,
                "schedule": schedule,
                "generated_at": datetime.now()
            })

        logger.info(f"Stored {len(labs_schedule)} lab timetables")

        # 4️⃣ **NEW**: Generate class timetables automatically
        logger.info("Generating class timetables...")
        class_timetables_result = class_timetable_handler.generate_class_timetables()
        
        logger.info("Master practical timetable regeneration completed")

        return jsonify({
            "message": response_message,
            "deleted_records": deleted_count,
            "labs_generated": len(labs_schedule),
            "leftovers": leftovers,
            "class_timetables": {
                "success": class_timetables_result['success'],
                "message": class_timetables_result.get('message', ''),
                "timetables_created": class_timetables_result.get('timetables_created', 0)
            }
        }), status_code

    except Exception as e:
        logger.error(f"Error in regenerate_master_practical_timetable: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/master_timetables', methods=['GET'])
def get_all_master_timetables():
    """Get all master practical timetables (lab-wise)"""
    return timetable_handler.get_master_practical_timetable()


# ============================================================================
# CLASS TIMETABLE ENDPOINTS (NEW!)
# ============================================================================

@app.route('/api/generate_class_timetables', methods=['POST'])
def generate_class_timetables_endpoint():
    """
    Manually trigger class timetable generation from existing master timetable.
    
    This is useful if you need to regenerate class timetables without
    regenerating the master timetable.
    
    Returns:
    {
        "success": true,
        "message": "Successfully generated X class timetables",
        "timetables_created": X
    }
    """
    try:
        logger.info("Manually generating class timetables...")
        result = class_timetable_handler.generate_class_timetables()
        
        if result['success']:
            logger.info(f"Successfully created {result.get('timetables_created', 0)} class timetables")
            return jsonify(result), 201
        else:
            logger.error(f"Class timetable generation failed: {result.get('error', 'Unknown error')}")
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error in generate_class_timetables: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/class_timetable/<class_name>/<division>', methods=['GET'])
def get_class_timetable_endpoint(class_name, division):
    """
    Get complete timetable for a specific class-division.
    
    Example: GET /api/class_timetable/SY/A
    
    Returns complete timetable with all time slots (10:15 to 16:20)
    showing which subjects/batches have practicals at each slot.
    """
    return class_timetable_handler.get_class_timetable(class_name, division)


@app.route('/api/class_timetable/<class_name>/<division>/summary', methods=['GET'])
def get_class_timetable_summary_endpoint(class_name, division):
    """
    Get summary of class timetable (shows only subject names in each slot).
    
    Example: GET /api/class_timetable/SY/A/summary
    
    Lightweight response showing just the subjects scheduled for each time slot.
    """
    return class_timetable_handler.get_class_timetable_summary(class_name, division)


@app.route('/api/class_timetables', methods=['GET'])
def get_all_class_timetables_endpoint():
    """
    Get all class timetables.
    
    Returns list of all class (SY-A, SY-B, TY-A, TY-B, BE-A, etc.) timetables.
    """
    return class_timetable_handler.get_all_class_timetables()


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