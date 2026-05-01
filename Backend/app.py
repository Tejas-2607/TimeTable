from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

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


# ============================================================================
# HOME
# ============================================================================

@app.route('/')
def home():
    return jsonify({"message": "Flask Timetable API is running!"})


# ============================================================================
# FACULTY
# ============================================================================

@app.route('/api/faculty', methods=['GET'])
def get_faculty():
    return faculty_handler.display_faculty()


@app.route('/api/faculty', methods=['POST'])
def add_faculty():
    data = request.json or {}
    return faculty_handler.add_faculty(data)


@app.route('/api/faculty', methods=['PUT'])
def update_faculty():
    data = request.json or {}
    return faculty_handler.update_faculty(data)


@app.route('/api/faculty', methods=['DELETE'])
def delete_faculty():
    data = request.json or {}
    return faculty_handler.delete_faculty(data)


# ============================================================================
# LABS
# ============================================================================

@app.route('/api/labs', methods=['GET'])
def get_labs():
    return labs_handler.display_labs()


@app.route('/api/labs', methods=['POST'])
def add_lab():
    data = request.json or {}
    return labs_handler.add_lab(data)


@app.route('/api/labs', methods=['PUT'])
def update_lab():
    data = request.json or {}
    return labs_handler.update_lab(data)


@app.route('/api/labs', methods=['DELETE'])
def delete_lab():
    data = request.json or {}
    return labs_handler.delete_lab(data)


@app.route('/api/confirm_labs', methods=['POST'])
def confirm_labs():
    data = request.json
    return labs_handler.confirm_labs(data)


# ============================================================================
# CLASS STRUCTURE
# ============================================================================

@app.route('/api/class_structure', methods=['GET'])
def get_class_structure():
    return class_structure_handler.get_class_structure()


@app.route('/api/class_structure', methods=['POST'])
def save_class_structure():
    data = request.json or {}
    return class_structure_handler.save_class_structure(data)


# ============================================================================
# SUBJECTS
# ============================================================================

@app.route('/api/subjects', methods=['POST'])
def save_subjects():
    data = request.json
    return subjects_handler.save_subjects(data)


@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    return subjects_handler.get_subjects()


@app.route('/api/subjects', methods=['DELETE'])
def delete_subject():
    data = request.json
    return subjects_handler.delete_subject(data)


@app.route('/api/subjects', methods=['PUT'])
def update_subject():
    data = request.json
    return subjects_handler.update_subject(data)


# ============================================================================
# FACULTY WORKLOAD
# ============================================================================

@app.route('/api/faculty_workload', methods=['POST'])
def save_workload():
    data = request.json
    return workload_handler.add_faculty_workload(data)


@app.route('/api/faculty_workload', methods=['GET'])
def get_faculty_workload():
    return workload_handler.get_faculty_workload()


@app.route('/api/faculty_workload', methods=['DELETE'])
def delete_faculty_workload():
    data = request.json
    return workload_handler.delete_faculty_workload(data)


@app.route('/api/faculty_workload', methods=['PUT'])
def update_faculty_workload():
    data = request.json
    return workload_handler.update_faculty_workload(data)


# ============================================================================
# MASTER PRACTICAL TIMETABLE — main generation pipeline
# ============================================================================

@app.route('/api/regenerate_master_practical_timetable', methods=['POST'])
def regenerate_master_practical_timetable():
    """
    Full pipeline:
      1. Snapshot existing data (for rollback)
      2. Delete existing timetables
      3. timetable_generator   → practicals → master_lab_timetable
      4. class_timetable_handler → class timetables
      5. lecture_tt_generator  → lectures merged into class timetables

    AP-01 FIX: if step 4 or 5 raises an unrecoverable error the collections
    that were cleared in step 2 are restored from the snapshot taken before
    deletion, leaving the DB in its original state instead of empty.
    """
    from config import db

    master_col = db['master_lab_timetable']
    class_col  = db['class_timetable']

    logger.info("=" * 80)
    logger.info("STARTING COMPLETE TIMETABLE GENERATION")
    logger.info("=" * 80)

    # ── Snapshot for rollback (AP-01) ────────────────────────────────────────
    snapshot_master = list(master_col.find({}))
    snapshot_class  = list(class_col.find({}))
    logger.info(f"Snapshot taken: {len(snapshot_master)} lab docs, "
                f"{len(snapshot_class)} class docs")

    def _rollback(reason: str):
        """Restore both collections from the pre-run snapshot."""
        logger.error(f"Rolling back due to: {reason}")
        master_col.delete_many({})
        class_col.delete_many({})
        if snapshot_master:
            master_col.insert_many(snapshot_master)
        if snapshot_class:
            class_col.insert_many(snapshot_class)
        logger.info("Rollback complete — DB restored to pre-run state")

    try:
        # ── Step 1: Delete existing data ─────────────────────────────────────
        logger.info("\n[STEP 1] Deleting existing timetables…")
        deleted_labs    = master_col.delete_many({}).deleted_count
        deleted_classes = class_col.delete_many({}).deleted_count
        logger.info(f"✓ Deleted {deleted_labs} lab docs, {deleted_classes} class docs")

        # ── Step 2: Generate master practical timetable ──────────────────────
        logger.info("\n[STEP 2] Generating master practical timetable…")
        result = timetable_generator.generate()

        if not result or not result.get('success'):
            # Step 2 failed — nothing was written yet, no rollback needed
            logger.error("✗ Practical timetable generation failed")
            _rollback("practical generation failed")
            return jsonify({
                "error":  ("Failed to generate practical timetable. "
                           "Verify subject, faculty, and workload data."),
                "detail": result.get('error', '') if result else '',
            }), 400

        leftovers = result.get("leftovers", {})

        # ── Step 3: Build class timetables ───────────────────────────────────
        logger.info("\n[STEP 3] Building class timetables…")
        class_result = class_timetable_handler.generate_class_timetables()

        if not class_result.get('success'):
            err = class_result.get('error', 'unknown error')
            logger.error(f"✗ Class timetable generation failed: {err}")
            _rollback(f"class timetable generation failed: {err}")
            return jsonify({
                "error":  "Failed to build class timetables.",
                "detail": err,
            }), 500

        logger.info(f"✓ {class_result.get('message', '')}")

        # ── Step 4: Fill lectures ────────────────────────────────────────────
        logger.info("\n[STEP 4] Generating lecture timetable…")
        lecture_result = lecture_tt_generator.generate()

        if not lecture_result.get('success'):
            err = lecture_result.get('error', 'unknown error')
            logger.error(f"✗ Lecture generation failed: {err}")
            _rollback(f"lecture generation failed: {err}")
            return jsonify({
                "error":  "Failed to generate lecture timetable.",
                "detail": err,
            }), 500

        logger.info(f"✓ {lecture_result.get('message', '')}")

        # ── Build response ───────────────────────────────────────────────────
        logger.info("\n" + "=" * 80)
        logger.info("✅ COMPLETE TIMETABLE GENERATION FINISHED")
        logger.info("=" * 80)

        status_code      = 201
        response_message = "Timetable regenerated successfully!"
        if leftovers:
            unscheduled      = sum(len(v) for v in leftovers.values())
            response_message = (f"Timetable generated, but {unscheduled} practical "
                                f"session(s) could not be scheduled.")
            status_code = 206

        return jsonify({
            "message":              response_message,
            "deleted_records":      deleted_labs,
            "labs_generated":       result.get('labs_generated', 0),
            "practicals_scheduled": result.get('practicals_scheduled', 0),
            "class_timetables": {
                "success":            class_result['success'],
                "message":            class_result.get('message', ''),
                "timetables_created": class_result.get('timetables_created', 0),
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
        logger.error(f"✗ Unexpected error in pipeline: {e}", exc_info=True)
        _rollback(f"unexpected exception: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# MASTER TIMETABLE (read-only)
# ============================================================================

@app.route('/api/master_timetables', methods=['GET'])
def get_all_master_timetables():
    return timetable_handler.get_master_practical_timetable()


# ============================================================================
# CLASS TIMETABLE (read-only)
# ============================================================================

@app.route('/api/class_timetable/<class_name>/<division>', methods=['GET'])
def get_class_timetable_endpoint(class_name, division):
    """GET /api/class_timetable/SY/A"""
    try:
        if not class_name or not division:
            return jsonify({'error': 'Missing class_name or division'}), 400

        from config import db
        collection = db['class_timetable']
        timetable  = collection.find_one({
            'class':    class_name.upper(),
            'division': division.upper(),
        })

        if not timetable:
            return jsonify({
                'error': f'No timetable found for {class_name.upper()}-{division.upper()}'
            }), 404

        timetable['_id'] = str(timetable['_id'])
        if 'generated_at' in timetable:
            timetable['generated_at'] = timetable['generated_at'].isoformat()

        return jsonify(timetable), 200

    except Exception as e:
        logger.error(f"Error fetching class timetable: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/class_timetables', methods=['GET'])
def get_all_class_timetables_endpoint():
    try:
        from config import db
        collection = db['class_timetable']
        timetables = list(collection.find({}))

        for t in timetables:
            t['_id'] = str(t['_id'])
            if 'generated_at' in t:
                t['generated_at'] = t['generated_at'].isoformat()

        return jsonify({'total': len(timetables), 'timetables': timetables}), 200

    except Exception as e:
        logger.error(f"Error fetching all class timetables: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

# AP-02 FIX: return JSON for client errors, not Flask's default HTML page.
# Covers malformed JSON body, missing Content-Type, and validation failures
# raised explicitly with abort(400) anywhere in the app.
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'detail': str(error)}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


# AP-02 FIX: wrong HTTP method (e.g. GET on a POST-only route) also returns
# HTML by default — catch it here.
@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# RUN
# ============================================================================

if __name__ == '__main__':
    logger.info("Starting Flask Timetable API…")
    app.run(debug=True)