import { useState, useEffect } from 'react';
import { storage } from '../../lib/storage';
import { Plus, Trash2, Edit2, X } from 'lucide-react';

export default function SubjectsStep({ data, onDataChange }) {
  const [year, setYear] = useState('SY');
  const [subjects, setSubjects] = useState([]);
  const [labs, setLabs] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    subject_full_name: '',
    subject_short_form: '',
    class_type: 'Both',
    lectures_per_week: 4,
    practicals_per_week: 1,
    practical_duration: 2,
    practical_type: 'specific_lab',
    required_labs: [],
  });

  useEffect(() => {
    loadSubjects();
    loadLabs();
  }, [year]);

  const loadSubjects = () => {
    const subjectsData = storage.subjects.getByYear(year);
    setSubjects(subjectsData.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
  };

  const loadLabs = () => {
    const labsData = storage.labs.getAll();
    setLabs(labsData);
  };

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const toggleLab = (labId) => {
    setFormData((prev) => ({
      ...prev,
      required_labs: prev.required_labs.includes(labId)
        ? prev.required_labs.filter((id) => id !== labId)
        : [...prev.required_labs, labId],
    }));
  };

  const handleEdit = (subject) => {
    setFormData({
      subject_full_name: subject.subject_full_name,
      subject_short_form: subject.subject_short_form,
      class_type: subject.class_type,
      lectures_per_week: subject.lectures_per_week,
      practicals_per_week: subject.practicals_per_week,
      practical_duration: subject.practical_duration,
      practical_type: subject.practical_type || 'specific_lab',
      required_labs: subject.required_labs || [],
    });
    setEditingId(subject.id);
    setShowForm(true);
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const subjectData = {
      year,
      ...formData,
      lectures_per_week: parseInt(formData.lectures_per_week),
      practicals_per_week: parseInt(formData.practicals_per_week),
      practical_duration: parseInt(formData.practical_duration),
    };

    if (editingId) {
      storage.subjects.update(editingId, subjectData);
    } else {
      storage.subjects.insert(subjectData);
    }

    setFormData({
      subject_full_name: '',
      subject_short_form: '',
      class_type: 'Both',
      lectures_per_week: 4,
      practicals_per_week: 1,
      practical_duration: 2,
      practical_type: 'specific_lab',
      required_labs: [],
    });
    setEditingId(null);
    setShowForm(false);

    loadSubjects();
  };

  const handleDelete = (id) => {
    if (confirm('Are you sure you want to delete this subject?')) {
      storage.subjects.delete(id);
      loadSubjects();
    }
  };

  const getLabNames = (labIds) => {
    if (!labIds || labIds.length === 0) return 'None';
    return labs
      .filter((lab) => labIds.includes(lab.id))
      .map((lab) => lab.lab_short_form)
      .join(', ');
  };

  const getPracticalTypeLabel = (type) => {
    switch (type) {
      case 'specific_lab':
        return 'Specific Lab';
      case 'classroom':
        return 'Classroom';
      case 'no_room':
        return 'No Room';
      default:
        return type;
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h3 className="text-2xl font-bold text-slate-800 mb-2">
          Step 2: Subjects for CSE
        </h3>
        <p className="text-slate-600">Add and manage subjects for each year</p>
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
              Add Subject
            </button>
          </div>
        )}
      </div>

      {showForm && (
        <div className="bg-white rounded-xl shadow-lg p-6 border-2 border-blue-200">
          <div className="flex items-center justify-between mb-6">
            <h4 className="text-lg font-semibold text-slate-800">
              {editingId ? 'Edit Subject' : 'Add New Subject'} for {year}
            </h4>
            <button
              onClick={() => {
                setShowForm(false);
                setEditingId(null);
                setFormData({
                  subject_full_name: '',
                  subject_short_form: '',
                  class_type: 'Both',
                  lectures_per_week: 4,
                  practicals_per_week: 1,
                  practical_duration: 2,
                  practical_type: 'specific_lab',
                  required_labs: [],
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
                  Subject Full Name
                </label>
                <input
                  type="text"
                  value={formData.subject_full_name}
                  onChange={(e) => handleChange('subject_full_name', e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., Data Structures and Algorithms"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Subject Short Form
                </label>
                <input
                  type="text"
                  value={formData.subject_short_form}
                  onChange={(e) => handleChange('subject_short_form', e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., DSA"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-3">
                Class Type
              </label>
              <div className="flex gap-6">
                {['Theory', 'Practical', 'Both'].map((type) => (
                  <label key={type} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="class_type"
                      value={type}
                      checked={formData.class_type === type}
                      onChange={(e) => handleChange('class_type', e.target.value)}
                      className="w-4 h-4 text-blue-600"
                    />
                    <span className="text-slate-700">{type}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Lectures / Week
                </label>
                <input
                  type="number"
                  min="0"
                  value={formData.lectures_per_week}
                  onChange={(e) => handleChange('lectures_per_week', e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Practicals / Week
                </label>
                <input
                  type="number"
                  min="0"
                  value={formData.practicals_per_week}
                  onChange={(e) => handleChange('practicals_per_week', e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {(formData.class_type === 'Practical' || formData.class_type === 'Both') && (
              <div className="p-4 bg-slate-50 rounded-lg border border-slate-300">
                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Practical Duration (in slots)
                  </label>
                  <select
                    value={formData.practical_duration}
                    onChange={(e) => handleChange('practical_duration', e.target.value)}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {[1, 2, 3, 4].map((num) => (
                      <option key={num} value={num}>
                        {num} slot{num > 1 ? 's' : ''}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-3">
                    Practical Type
                  </label>
                  <div className="space-y-3">
                    <label className="flex items-start gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="practical_type"
                        value="specific_lab"
                        checked={formData.practical_type === 'specific_lab'}
                        onChange={(e) => handleChange('practical_type', e.target.value)}
                        className="w-4 h-4 text-blue-600 mt-1"
                      />
                      <div className="flex-1">
                        <span className="text-slate-700">Requires specific lab(s)</span>
                        {formData.practical_type === 'specific_lab' && (
                          <div className="mt-3 pl-6 space-y-2 bg-white p-3 rounded border border-slate-200">
                            <p className="text-sm font-medium text-slate-700 mb-2">
                              Select Labs:
                            </p>
                            {labs.length > 0 ? (
                              labs.map((lab) => (
                                <label
                                  key={lab.id}
                                  className="flex items-center gap-2 cursor-pointer"
                                >
                                  <input
                                    type="checkbox"
                                    checked={formData.required_labs.includes(lab.id)}
                                    onChange={() => toggleLab(lab.id)}
                                    className="w-4 h-4 text-blue-600 rounded"
                                  />
                                  <span className="text-sm text-slate-700">
                                    {lab.lab_name} ({lab.lab_short_form})
                                  </span>
                                </label>
                              ))
                            ) : (
                              <p className="text-sm text-slate-500">
                                No labs available. Please add labs first.
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    </label>

                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="practical_type"
                        value="classroom"
                        checked={formData.practical_type === 'classroom'}
                        onChange={(e) => handleChange('practical_type', e.target.value)}
                        className="w-4 h-4 text-blue-600"
                      />
                      <span className="text-slate-700">Requires a classroom (no lab)</span>
                    </label>

                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="practical_type"
                        value="no_room"
                        checked={formData.practical_type === 'no_room'}
                        onChange={(e) => handleChange('practical_type', e.target.value)}
                        className="w-4 h-4 text-blue-600"
                      />
                      <span className="text-slate-700">
                        No dedicated room (schedule last)
                      </span>
                    </label>
                  </div>
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <button
                type="submit"
                className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus size={18} />
                {editingId ? 'Update' : 'Add'} Subject
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditingId(null);
                  setFormData({
                    subject_full_name: '',
                    subject_short_form: '',
                    class_type: 'Both',
                    lectures_per_week: 4,
                    practicals_per_week: 1,
                    practical_duration: 2,
                    practical_type: 'specific_lab',
                    required_labs: [],
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
          Subjects for {year} ({subjects.length})
        </h4>

        {subjects.length > 0 ? (
          <div className="space-y-4">
            {subjects.map((subject) => (
              <div
                key={subject.id}
                className="bg-white rounded-lg p-5 border border-slate-200 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <h5 className="text-lg font-bold text-slate-800">
                        {subject.subject_full_name}
                      </h5>
                      <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold">
                        {subject.subject_short_form}
                      </span>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          subject.class_type === 'Theory'
                            ? 'bg-green-100 text-green-700'
                            : subject.class_type === 'Practical'
                            ? 'bg-orange-100 text-orange-700'
                            : 'bg-purple-100 text-purple-700'
                        }`}
                      >
                        {subject.class_type}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="flex items-center gap-2">
                        <span className="text-slate-600 font-medium">Lectures/Week:</span>
                        <span className="text-slate-800 font-semibold">
                          {subject.lectures_per_week}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-600 font-medium">Practicals/Week:</span>
                        <span className="text-slate-800 font-semibold">
                          {subject.practicals_per_week}
                        </span>
                      </div>
                      {(subject.class_type === 'Practical' || subject.class_type === 'Both') && (
                        <>
                          <div className="flex items-center gap-2">
                            <span className="text-slate-600 font-medium">
                              Practical Duration:
                            </span>
                            <span className="text-slate-800 font-semibold">
                              {subject.practical_duration} slot{subject.practical_duration > 1 ? 's' : ''}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-slate-600 font-medium">Practical Type:</span>
                            <span className="text-slate-800 font-semibold">
                              {getPracticalTypeLabel(subject.practical_type)}
                            </span>
                          </div>
                          {subject.practical_type === 'specific_lab' && (
                            <div className="col-span-2 flex items-start gap-2">
                              <span className="text-slate-600 font-medium">Required Labs:</span>
                              <span className="text-slate-800 font-semibold">
                                {getLabNames(subject.required_labs)}
                              </span>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <button
                      onClick={() => handleEdit(subject)}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Edit subject"
                    >
                      <Edit2 size={18} />
                    </button>
                    <button
                      onClick={() => handleDelete(subject.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete subject"
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
            <p className="text-slate-500 text-lg">No subjects added for {year} yet</p>
            <p className="text-slate-400 text-sm mt-2">
              Click "Add Subject" to get started
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
