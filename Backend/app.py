from flask import Flask, request, jsonify
from modules import (
    faculty_handler,
    labs_handler,
    timetable_handler,
    class_structure_handler,
    subjects_handler,
    workload_handler,
    constraints_handler
)

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Flask Timetable API is running!"})


# ---------- FACULTY ----------
@app.route('/api/faculty', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_faculty():
    data = request.json or {}
    action = data.get('action', '').lower()

    if action == 'add':
        return faculty_handler.add_faculty(data)
    elif action == 'delete':
        return faculty_handler.delete_faculty(data)
    elif action == 'update':
        return faculty_handler.update_faculty(data)
    else:
        return faculty_handler.display_faculty()


# ---------- LABS ----------
@app.route('/api/labs', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_labs():
    data = request.json or {}
    action = data.get('action', '').lower()

    if action == 'add':
        return labs_handler.add_lab(data)
    elif action == 'delete':
        return labs_handler.delete_lab(data)
    elif action == 'update':
        return labs_handler.update_lab(data)
    else:
        return labs_handler.display_labs()


# ---------- PREVIOUS YEAR TIMETABLE ----------
@app.route('/api/previous_timetable', methods=['POST'])
def previous_timetable():
    data = request.json
    return timetable_handler.get_previous_year_timetable(data)


# ---------- CLASS STRUCTURE ----------
@app.route('/api/class_structure', methods=['POST'])
def save_class_structure():
    data = request.json
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


# ---------- GENERATE TIMETABLE ----------
@app.route('/api/generate_timetable', methods=['POST'])
def generate_timetable():
    data = request.json
    return timetable_handler.generate_timetable(data)


if __name__ == '__main__':
    app.run(debug=True)
