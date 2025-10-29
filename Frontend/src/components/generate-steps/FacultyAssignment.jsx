import { useState, useEffect } from 'react';
import { storage } from '../../lib/storage';
import { Plus, Trash2, Edit2, X } from 'lucide-react';

export default function FacultyAssignment({ data, onDataChange }) {
  const [year, setYear] = useState('SY');
  const [faculties, setFaculties] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [structure, setStructure] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [selectedSubjectType, setSelectedSubjectType] = useState(null);

  const [formData, setFormData] = useState({
    faculty_id: '',
    subject_id: '',
    division: 'A',
    batches: [],
    theory_workload_hours: 0,
    practical_workload_hours: 0,
  });

  useEffect(() => {
    loadFaculties();
    loadSubjects();
    loadStructure();
    loadAssignments();
  }, [year]);

  useEffect(() => {
    if (formData.subject_id) {
      const subject = subjects.find(s => s.id === formData.subject_id);
      setSelectedSubjectType(subject?.class_type || null);
    } else {
      setSelectedSubjectType(null);
    }
  }, [formData.subject_id, subjects]);

  const loadFaculties = () => {
    const data = storage.faculties.getAll();
    setFaculties(data.sort((a, b) => a.full_name.localeCompare(b.full_name)));
  };

  const loadSubjects = () => {
    const data = storage.subjects.getByYear(year);
    setSubjects(data);
  };

  const loadStructure = () => {
    const data = storage.classStructure.getByYear(year);
    setStructure(data);
  };

  const loadAssignments = () => {
    const theoryData = storage.facultyAssignments.getByYearAndType(year, 'theory');
    const practicalData = storage.facultyAssignments.getByYearAndType(year, 'practical');
    setAssignments([...theoryData, ...practicalData].sort((a, b) =>
      new Date(b.created_at) - new Date(a.created_at)
    ));
  };

  const handleEdit = (assignment) => {
    const subject = subjects.find(s => s.id === assignment.subject_id);
    let theoryWorkload = 0;
    let practicalWorkload = 0;
    let batchesList = [];

    if (subject?.class_type === 'Both') {
      const theory = assignments.find(
        a => a.faculty_id === assignment.faculty_id &&
        a.subject_id === assignment.subject_id &&
        a.division === assignment.division &&
        a.assignment_type === 'theory'
      );
      const practicals = assignments.filter(
        a => a.faculty_id === assignment.faculty_id &&
        a.subject_id === assignment.subject_id &&
        a.division === assignment.division &&
        a.assignment_type === 'practical'
      );
      theoryWorkload = theory?.workload_hours || 0;
      practicalWorkload = practicals.length > 0 ? practicals[0].workload_hours : 0;
      batchesList = practicals.map(p => p.batch);
    } else if (assignment.assignment_type === 'theory') {
      theoryWorkload = assignment.workload_hours;
    } else {
      const practicals = assignments.filter(
        a => a.faculty_id === assignment.faculty_id &&
        a.subject_id === assignment.subject_id &&
        a.division === assignment.division &&
        a.assignment_type === 'practical'
      );
      practicalWorkload = practicals.length > 0 ? practicals[0].workload_hours : 0;
      batchesList = practicals.map(p => p.batch);
    }

    setFormData({
      faculty_id: assignment.faculty_id,
      subject_id: assignment.subject_id,
      division: assignment.division,
      batches: batchesList,
      theory_workload_hours: theoryWorkload,
      practical_workload_hours: practicalWorkload,
    });
    setEditingId(assignment.id);
    setShowForm(true);
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const subject = subjects.find(s => s.id === formData.subject_id);
    if (!subject) return;

    const isTheory = subject.class_type === 'Theory';
    const isPractical = subject.class_type === 'Practical';
    const isBoth = subject.class_type === 'Both';

    if (isBoth) {
      const theoryAssignment = {
        faculty_id: formData.faculty_id,
        subject_id: formData.subject_id,
        division: formData.division,
        year,
        assignment_type: 'theory',
        workload_hours: parseFloat(formData.theory_workload_hours),
      };

      const practicalAssignments = formData.batches.map(batch => ({
        faculty_id: formData.faculty_id,
        subject_id: formData.subject_id,
        division: formData.division,
        batch: batch,
        year,
        assignment_type: 'practical',
        workload_hours: parseFloat(formData.practical_workload_hours),
      }));

      if (editingId) {
        const existing = assignments.find(a => a.id === editingId);
        const theoryMatch = assignments.find(
          a => a.faculty_id === existing.faculty_id &&
          a.subject_id === existing.subject_id &&
          a.division === existing.division &&
          a.assignment_type === 'theory'
        );
        const practicalMatches = assignments.filter(
          a => a.faculty_id === existing.faculty_id &&
          a.subject_id === existing.subject_id &&
          a.division === existing.division &&
          a.assignment_type === 'practical'
        );

        if (theoryMatch) {
          storage.facultyAssignments.update(theoryMatch.id, theoryAssignment);
        }

        practicalMatches.forEach(p => storage.facultyAssignments.delete(p.id));
        practicalAssignments.forEach(pa => storage.facultyAssignments.insert(pa));
      } else {
        storage.facultyAssignments.insert(theoryAssignment);
        practicalAssignments.forEach(pa => storage.facultyAssignments.insert(pa));
      }
    } else {
      if (isTheory) {
        const assignmentData = {
          faculty_id: formData.faculty_id,
          subject_id: formData.subject_id,
          division: formData.division,
          year,
          assignment_type: 'theory',
          workload_hours: parseFloat(formData.theory_workload_hours),
        };

        if (editingId) {
          storage.facultyAssignments.update(editingId, assignmentData);
        } else {
          storage.facultyAssignments.insert(assignmentData);
        }
      } else {
        const practicalAssignments = formData.batches.map(batch => ({
          faculty_id: formData.faculty_id,
          subject_id: formData.subject_id,
          division: formData.division,
          batch: batch,
          year,
          assignment_type: 'practical',
          workload_hours: parseFloat(formData.practical_workload_hours),
        }));

        if (editingId) {
          const existing = assignments.find(a => a.id === editingId);
          const practicalMatches = assignments.filter(
            a => a.faculty_id === existing.faculty_id &&
            a.subject_id === existing.subject_id &&
            a.division === existing.division &&
            a.assignment_type === 'practical'
          );

          practicalMatches.forEach(p => storage.facultyAssignments.delete(p.id));
          practicalAssignments.forEach(pa => storage.facultyAssignments.insert(pa));
        } else {
          practicalAssignments.forEach(pa => storage.facultyAssignments.insert(pa));
        }
      }
    }

    setFormData({
      faculty_id: '',
      subject_id: '',
      division: 'A',
      batches: [],
      theory_workload_hours: 0,
      practical_workload_hours: 0,
    });
    setEditingId(null);
    setShowForm(false);

    loadAssignments();
  };

  const handleDelete = (id) => {
    if (confirm('Are you sure you want to delete this assignment?')) {
      const assignment = assignments.find(a => a.id === id);
      storage.facultyAssignments.delete(id);

      if (assignment) {
        const allRelated = assignments.filter(
          a => a.faculty_id === assignment.faculty_id &&
          a.subject_id === assignment.subject_id &&
          a.division === assignment.division &&
          a.id !== id
        );
        allRelated.forEach(r => storage.facultyAssignments.delete(r.id));
      }

      loadAssignments();
    }
  };

  const getDivisions = () => {
    if (!structure) return [];
    return Array.from({ length: structure.num_divisions }, (_, i) =>
      String.fromCharCode(65 + i)
    );
  };

  const getBatches = () => {
    if (!structure) return [];
    return Array.from(
      { length: structure.batches_per_division },
      (_, i) => `Batch ${i + 1}`
    );
  };

  const needsBatchSelection = () => {
    if (!selectedSubjectType) return false;
    return selectedSubjectType === 'Practical' || selectedSubjectType === 'Both';
  };

  const groupedAssignments = assignments.reduce((acc, assignment) => {
    const key = `${assignment.subject_id}-${assignment.faculty_id}-${assignment.division}`;
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(assignment);
    return acc;
  }, {});

  const displayAssignments = Object.values(groupedAssignments).map(group => {
    if (group.length === 1) {
      return group[0];
    }
    const theory = group.find(a => a.assignment_type === 'theory');
    const practicals = group.filter(a => a.assignment_type === 'practical');

    if (theory && practicals.length > 0) {
      return {
        ...theory,
        isCombined: true,
        practicalBatches: practicals.map(p => p.batch),
        totalWorkload: theory.workload_hours + (practicals[0]?.workload_hours || 0),
      };
    }

    return {
      ...group[0],
      practicalBatches: practicals.map(p => p.batch),
    };
  });

  return (
    <div className="space-y-8">
      <div>
        <h3 className="text-2xl font-bold text-slate-800 mb-2">
          Step 3: Faculty Assignment
        </h3>
        <p className="text-slate-600">
          Assign faculties to subjects for each year
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
                  batch: 'Batch 1',
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
                  Subject
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
                      {subject.subject_full_name} ({subject.subject_short_form}) - {subject.class_type}
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

            <div className={`grid ${needsBatchSelection() ? 'grid-cols-2' : 'grid-cols-1'} gap-6`}>
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

              {needsBatchSelection() && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-3">
                    Batches (for Practical)
                  </label>
                  <div className="flex flex-wrap gap-4">
                    {getBatches().map((batch) => (
                      <label key={batch} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.batches.includes(batch)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFormData({ ...formData, batches: [...formData.batches, batch] });
                            } else {
                              setFormData({ ...formData, batches: formData.batches.filter(b => b !== batch) });
                            }
                          }}
                          className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                        />
                        <span className="text-slate-700">{batch}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-6">
              {(selectedSubjectType === 'Theory' || selectedSubjectType === 'Both') && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Theory Workload (hrs/week)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    value={formData.theory_workload_hours}
                    onChange={(e) =>
                      setFormData({ ...formData, theory_workload_hours: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
              )}

              {(selectedSubjectType === 'Practical' || selectedSubjectType === 'Both') && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Practical Workload (hrs/week)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    value={formData.practical_workload_hours}
                    onChange={(e) =>
                      setFormData({ ...formData, practical_workload_hours: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
              )}
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
                    batch: 'Batch 1',
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

      <div className="bg-gradient-to-br from-blue-50 to-slate-50 rounded-xl shadow-lg p-6 border border-slate-200">
        <h4 className="text-xl font-bold text-slate-800 mb-4">
          Faculty Assignments for {year} ({displayAssignments.length})
        </h4>

        {displayAssignments.length > 0 ? (
          <div className="space-y-4">
            {displayAssignments.map((assignment) => (
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
                        <span className={`ml-2 px-2 py-1 rounded text-xs ${
                          assignment.subjects?.class_type === 'Theory'
                            ? 'bg-green-100 text-green-700'
                            : assignment.subjects?.class_type === 'Practical'
                            ? 'bg-orange-100 text-orange-700'
                            : 'bg-purple-100 text-purple-700'
                        }`}>
                          {assignment.subjects?.subject_short_form}
                        </span>
                      </p>
                    </div>
                    <div>
                      <span className="text-xs font-semibold text-slate-500 uppercase">
                        {assignment.isCombined ? 'Division & Batches' :
                         assignment.assignment_type === 'practical' ? 'Division & Batches' : 'Division'}
                      </span>
                      <p className="text-slate-800 font-semibold mt-1">
                        Division {assignment.division}
                        {assignment.isCombined && assignment.practicalBatches && assignment.practicalBatches.length > 0 &&
                          ` - ${assignment.practicalBatches.join(', ')}`}
                        {assignment.assignment_type === 'practical' && assignment.practicalBatches && assignment.practicalBatches.length > 0 &&
                          ` - ${assignment.practicalBatches.join(', ')}`}
                        {assignment.assignment_type === 'practical' && assignment.batch &&
                          ` - ${assignment.batch}`}
                      </p>
                    </div>
                    <div>
                      <span className="text-xs font-semibold text-slate-500 uppercase">Workload</span>
                      <p className="text-slate-800 font-semibold mt-1">
                        {assignment.isCombined ? assignment.totalWorkload : assignment.workload_hours} hrs/week
                      </p>
                    </div>
                    {assignment.isCombined && (
                      <div className="col-span-2">
                        <span className="text-xs font-semibold text-slate-500 uppercase">Assignment Type</span>
                        <p className="text-slate-800 font-semibold mt-1">
                          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                            Theory + Practical
                          </span>
                        </p>
                      </div>
                    )}
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
            <p className="text-slate-500 text-lg">No assignments for {year} yet</p>
            <p className="text-slate-400 text-sm mt-2">
              Click "Add Assignment" to get started
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
