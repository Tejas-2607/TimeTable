from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for all routes
CORS(app)

from modules import (
    faculty_handler,
    labs_handler,
    timetable_handler,
    class_structure_handler,
    subjects_handler,
    workload_handler,
    constraints_handler
)

@app.route('/')
def home():
    return jsonify({"message": "Flask Timetable API is running!"})


# ---------- FACULTY ----------
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


# ---------- LABS ----------
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


# ---------- PREVIOUS YEAR TIMETABLE ----------
@app.route('/api/previous_timetable', methods=['POST'])
def previous_timetable():
    data = request.json
    return timetable_handler.get_master_timetable(data)


# ---------- CLASS STRUCTURE ----------
@app.route('/api/class_structure', methods=['GET'])
def get_class_structure():
    return class_structure_handler.get_class_structure()

@app.route('/api/class_structure', methods=['POST'])
def save_class_structure():
    data = request.json or {}
    return class_structure_handler.save_class_structure(data)
    

# ---------- CONFIRM LABS ----------
@app.route('/api/confirm_labs', methods=['POST'])
def confirm_labs():
    data = request.json
    return labs_handler.confirm_labs(data)


# ---------- SAVE SUBJECTS ----------
@app.route('/api/subjects', methods=['POST'])
def save_subjects():
    data = request.json
    return subjects_handler.save_subjects(data)

# ---------- GET SUBJECTS ----------
@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    return subjects_handler.get_subjects()


# ---------- DELETE SUBJECTS ----------
@app.route('/api/subjects', methods=['DELETE'])
def delete_subject():
    data = request.json
    return subjects_handler.delete_subject(data)

# ---------- UPDATE SUBJECTS ----------
@app.route('/api/subjects', methods=['PUT'])
def update_subject():
    data = request.json
    return subjects_handler.update_subject(data)

# ---------- SAVE FACULTY WORKLOAD ----------
@app.route('/api/faculty_workload', methods=['POST'])
def save_workload():
    data = request.json
    return workload_handler.add_faculty_workload(data)

# ---------- GET FACULTY WORKLOAD ----------
@app.route('/api/faculty_workload', methods=['GET'])
def get_faculty_workload():
    return workload_handler.get_faculty_workload()


# ---------- DELETE FACULTY WORKLOAD ----------
@app.route('/api/faculty_workload', methods=['DELETE'])
def delete_faculty_workload():
    data = request.json
    return workload_handler.delete_faculty_workload(data)

# ---------- UPDATE FACULTY WORKLOAD ----------
@app.route('/api/faculty_workload', methods=['PUT'])
def update_faculty_workload():
    data = request.json
    return workload_handler.update_faculty_workload(data)


# ---------- SAVE CONSTRAINTS ----------
@app.route('/api/constraints', methods=['POST'])
def save_constraints():
    data = request.json
    return constraints_handler.save_constraints(data)


# ---------- GENERATE TIMETABLE (Single Year) ----------
@app.route('/api/generate_timetable', methods=['POST'])
def generate_timetable():
    data = request.json
    return timetable_handler.generate_timetable(data)


# ---------- REGENERATE MASTER PRACTICAL TIMETABLE ----------
@app.route('/api/regenerate_master_practical_timetable', methods=['POST'])
def regenerate_master_practical_timetable():
    """
    Deletes all existing records from master_lab_timetable collection
    and generates a new consolidated lab-wise timetable.

    No input fields required.
    """
    try:
        from modules import timetable_generator
        from config import db

        master_lab_timetable_collection = db['master_lab_timetable']

        # 1️⃣ Delete existing timetable data
        deleted_count = master_lab_timetable_collection.delete_many({}).deleted_count

        # 2️⃣ Generate new timetable (single unified generation)
        result = timetable_generator.generate({})

        if not result:
            return jsonify({
                "error": "Failed to generate new timetable. Please verify subject, faculty, and workload data."
            }), 400

        # 3️⃣ Store each lab’s schedule as an independent document
        labs_schedule = result.get("labs", {})
        for lab_name, schedule in labs_schedule.items():
            master_lab_timetable_collection.insert_one({
                "lab_name": lab_name,
                "schedule": schedule
            })

        return jsonify({
            "message": "Master practical timetable regenerated successfully!",
            "deleted_records": deleted_count,
            "labs_generated": len(labs_schedule)
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ---------- GET ALL MASTER TIMETABLES ----------
@app.route('/api/master_timetables', methods=['GET'])
def get_all_master_timetables():
    return timetable_handler.get_master_practical_timetable()


if __name__ == '__main__':
    app.run(debug=True)