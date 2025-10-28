import { useState, useEffect } from 'react';
import { storage } from '../../lib/storage';
import { Plus, Trash2, Edit2, X } from 'lucide-react';

export default function TheoryAssignment({ data, onDataChange }) {
  const [year, setYear] = useState('SY');
  const [faculties, setFaculties] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [structure, setStructure] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);

  const [formData, setFormData] = useState({
    faculty_id: '',
    subject_id: '',
    division: 'A',
    workload_hours: 0,
  });

  useEffect(() => {
    loadFaculties();
    loadSubjects();
    loadStructure();
    loadAssignments();
  }, [year]);

  const loadFaculties = () => {
    const data = storage.faculties.getAll();
    setFaculties(data.sort((a, b) => a.full_name.localeCompare(b.full_name)));
  };

  const loadSubjects = () => {
    const data = storage.subjects.getByYearAndType(year, ['Theory', 'Both']);
    setSubjects(data);
  };

  const loadStructure = () => {
    const data = storage.classStructure.getByYear(year);
    setStructure(data);
  };

  const loadAssignments = () => {
    const data = storage.facultyAssignments.getByYearAndType(year, 'theory');
    setAssignments(data);
  };

  const handleEdit = (assignment) => {
    setFormData({
      faculty_id: assignment.faculty_id,
      subject_id: assignment.subject_id,
      division: assignment.division,
      workload_hours: assignment.workload_hours,
    });
    setEditingId(assignment.id);
    setShowForm(true);
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const assignmentData = {
      ...formData,
      year,
      assignment_type: 'theory',
      workload_hours: parseFloat(formData.workload_hours),
    };

    if (editingId) {
      storage.facultyAssignments.update(editingId, assignmentData);
    } else {
      storage.facultyAssignments.insert(assignmentData);
    }

    setFormData({
      faculty_id: '',
      subject_id: '',
      division: 'A',
      workload_hours: 0,
    });
    setEditingId(null);
    setShowForm(false);

    loadAssignments();
  };

  const handleDelete = (id) => {
    if (confirm('Are you sure you want to delete this assignment?')) {
      storage.facultyAssignments.delete(id);
      loadAssignments();
    }
  };

  const getDivisions = () => {
    if (!structure) return [];
    return Array.from({ length: structure.num_divisions }, (_, i) =>
      String.fromCharCode(65 + i)
    );
  };

  return (
    <div className="space-y-8">
      <div>
        <h3 className="text-2xl font-bold text-slate-800 mb-2">
          Step 4: Theory Assignment
        </h3>
        <p className="text-slate-600">
          Assign faculties to theory subjects for each year
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Select Year
          </label>
          <select
            value={year}
            onChange={(e) => setYear(e.target.value)}
            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="SY">2nd Year (SY)</option>
            <option value="TY">3rd Year (TY)</option>
            <option value="Final Year">Final Year</option>
          </select>
        </div>
        {!showForm && (
          <div className="flex items-end">
            <button
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus size={20} />
              Add Assignment
            </button>
          </div>
        )}
      </div>

      {showForm && (
        <div className="bg-white rounded-xl shadow-lg p-6 border-2 border-blue-200">
          <div className="flex items-center justify-between mb-6">
            <h4 className="text-lg font-semibold text-slate-800">
              {editingId ? 'Edit Assignment' : 'Add New Assignment'} for {year}
            </h4>
            <button
              onClick={() => {
                setShowForm(false);
                setEditingId(null);
                setFormData({
                  faculty_id: '',
                  subject_id: '',
                  division: 'A',
                  workload_hours: 0,
                });
              }}
              className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Theory Subject
                </label>
                <select
                  value={formData.subject_id}
                  onChange={(e) =>
                    setFormData({ ...formData, subject_id: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Select Subject</option>
                  {subjects.map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {subject.subject_full_name} ({subject.subject_short_form})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Faculty Name
                </label>
                <select
                  value={formData.faculty_id}
                  onChange={(e) =>
                    setFormData({ ...formData, faculty_id: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Select Faculty</option>
                  {faculties.map((faculty) => (
                    <option key={faculty.id} value={faculty.id}>
                      {faculty.title} {faculty.full_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Division
                </label>
                <select
                  value={formData.division}
                  onChange={(e) =>
                    setFormData({ ...formData, division: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  {getDivisions().map((div) => (
                    <option key={div} value={div}>
                      Division {div}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Workload (hrs/week)
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  value={formData.workload_hours}
                  onChange={(e) =>
                    setFormData({ ...formData, workload_hours: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus size={18} />
                {editingId ? 'Update' : 'Add'} Assignment
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditingId(null);
                  setFormData({
                    faculty_id: '',
                    subject_id: '',
                    division: 'A',
                    workload_hours: 0,
                  });
                }}
                className="px-6 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-gradient-to-br from-green-50 to-slate-50 rounded-xl shadow-lg p-6 border border-slate-200">
        <h4 className="text-xl font-bold text-slate-800 mb-4">
          Theory Assignments for {year} ({assignments.length})
        </h4>

        {assignments.length > 0 ? (
          <div className="space-y-4">
            {assignments.map((assignment) => (
              <div
                key={assignment.id}
                className="bg-white rounded-lg p-5 border border-slate-200 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 grid grid-cols-2 gap-x-6 gap-y-3">
                    <div>
                      <span className="text-xs font-semibold text-slate-500 uppercase">Faculty</span>
                      <p className="text-slate-800 font-semibold mt-1">
                        {assignment.faculties?.title} {assignment.faculties?.full_name}
                      </p>
                    </div>
                    <div>
                      <span className="text-xs font-semibold text-slate-500 uppercase">Subject</span>
                      <p className="text-slate-800 font-semibold mt-1">
                        {assignment.subjects?.subject_full_name}
                        <span className="ml-2 px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
                          {assignment.subjects?.subject_short_form}
                        </span>
                      </p>
                    </div>
                    <div>
                      <span className="text-xs font-semibold text-slate-500 uppercase">Division</span>
                      <p className="text-slate-800 font-semibold mt-1">
                        Division {assignment.division}
                      </p>
                    </div>
                    <div>
                      <span className="text-xs font-semibold text-slate-500 uppercase">Workload</span>
                      <p className="text-slate-800 font-semibold mt-1">
                        {assignment.workload_hours} hrs/week
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <button
                      onClick={() => handleEdit(assignment)}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Edit assignment"
                    >
                      <Edit2 size={18} />
                    </button>
                    <button
                      onClick={() => handleDelete(assignment.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete assignment"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-slate-500 text-lg">No theory assignments for {year} yet</p>
            <p className="text-slate-400 text-sm mt-2">
              Click "Add Assignment" to get started
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
