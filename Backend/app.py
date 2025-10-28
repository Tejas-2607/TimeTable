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


# ---------- SAVE FACULTY WORKLOAD ----------
@app.route('/api/faculty_workload', methods=['POST'])
def save_workload():
    data = request.json
    return workload_handler.save_faculty_workload(data)


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


# ---------- GENERATE ALL TIMETABLES (SY, TY, BE) ----------
@app.route('/api/generate_all_timetables', methods=['POST'])
def generate_all_timetables():
    """
    Generate master practical timetables for all classes (SY, TY, BE)
    Body: {"sem": "1"}
    """
    data = request.json or {}
    return timetable_handler.generate_all_timetables(data)


# ---------- GET ALL MASTER TIMETABLES ----------
@app.route('/api/master_timetables', methods=['GET'])
def get_all_master_timetables():
    """
    Retrieve all generated master practical timetables
    """
    return timetable_handler.get_all_master_timetables()


# ---------- GET SPECIFIC MASTER TIMETABLE ----------
@app.route('/api/master_timetable', methods=['POST'])
def get_master_timetable():
    """
    Retrieve master practical timetable for specific year/semester
    Body: {"year": "SY", "sem": "1"}
    """
    data = request.json or {}
    return timetable_handler.get_master_timetable(data)


if __name__ == '__main__':
    app.run(debug=True)