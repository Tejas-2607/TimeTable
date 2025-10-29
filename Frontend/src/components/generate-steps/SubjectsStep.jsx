import { useState, useEffect } from 'react';
import { Plus, Trash2, Edit2, X } from 'lucide-react';
import { getSubjects, addSubject, updateSubject, deleteSubject } from '../../services/subjectService';
import { getAllLabs } from '../../services/labsService';

export default function SubjectsStep({ data, onDataChange }) {
  const [year, setYear] = useState('sy');
  const [subjects, setSubjects] = useState([]);
  const [labs, setLabs] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    short_name: '',
    hrs_per_week_lec: '4',
    hrs_per_week_practical: '1',
    practical_duration: '2',
    practical_type: 'Specific Lab',
    required_labs: '',
  });

  // Load labs only once on mount
  useEffect(() => {
    loadLabs();
  }, []);

  // Load subjects when year changes
  useEffect(() => {
    loadSubjects();
  }, [year]);

  const loadSubjects = async () => {
    try {
      setLoading(true);
      const res = await getSubjects();
      console.log('Subjects response:', res);
      
      const data = res.data || res;
      const yearData = data[year] || [];
      
      console.log('Year data for', year, ':', yearData);
      setSubjects(Array.isArray(yearData) ? yearData : []);
    } catch (err) {
      console.error('Error loading subjects:', err);
      setSubjects([]);
    } finally {
      setLoading(false);
    }
  };

  const loadLabs = async () => {
    try {
      const res = await getAllLabs();
      console.log('Labs full response:', res);
      
      // Check different possible response structures
      let labsArray = [];
      
      if (res.data && Array.isArray(res.data)) {
        labsArray = res.data;
      } else if (res.data && res.data.data && Array.isArray(res.data.data)) {
        labsArray = res.data.data;
      } else if (Array.isArray(res)) {
        labsArray = res;
      }
      
      console.log('Processed labs array:', labsArray);
      console.log('Labs count:', labsArray.length);
      setLabs(labsArray);
    } catch (err) {
      console.error('Error loading labs:', err);
      setLabs([]);
    }
  };

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleEdit = (subject) => {
    setFormData({
      name: subject.name,
      short_name: subject.short_name,
      hrs_per_week_lec: String(subject.hrs_per_week_lec),
      hrs_per_week_practical: String(subject.hrs_per_week_practical),
      practical_duration: String(subject.practical_duration),
      practical_type: subject.practical_type || 'Specific Lab',
      required_labs: subject.required_labs || '',
    });
    setEditingId(subject._id);
    setShowForm(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);
      const subjectData = {
        year,
        name: formData.name,
        short_name: formData.short_name,
        hrs_per_week_lec: parseInt(formData.hrs_per_week_lec),
        hrs_per_week_practical: parseInt(formData.hrs_per_week_practical),
        practical_duration: parseInt(formData.practical_duration),
        practical_type: formData.practical_type,
        ...(formData.required_labs && { required_labs: formData.required_labs }),
      };

      if (editingId) {
        await updateSubject({
          id: editingId,
          ...subjectData,
        });
      } else {
        await addSubject(subjectData);
      }

      setFormData({
        name: '',
        short_name: '',
        hrs_per_week_lec: '4',
        hrs_per_week_practical: '1',
        practical_duration: '2',
        practical_type: 'Specific Lab',
        required_labs: '',
      });
      setEditingId(null);
      setShowForm(false);

      await loadSubjects();
    } catch (err) {
      console.error('Error submitting subject:', err);
      alert('Error saving subject. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (confirm('Are you sure you want to delete this subject?')) {
      try {
        setLoading(true);
        await deleteSubject(year, id);
        await loadSubjects();
      } catch (err) {
        console.error('Error deleting subject:', err);
        alert('Error deleting subject. Please try again.');
      } finally {
        setLoading(false);
      }
    }
  };

  const getYearLabel = (yearCode) => {
    switch (yearCode) {
      case 'sy':
        return '2nd Year (SY)';
      case 'ty':
        return '3rd Year (TY)';
      case 'be':
        return 'Final Year (BE)';
      default:
        return yearCode;
    }
  };

  const getPracticalTypeLabel = (type) => {
    switch (type) {
      case 'Specific Lab':
        return 'Specific Lab';
      case 'Common Lab':
        return 'Common Lab';
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
            <option value="sy">{getYearLabel('sy')}</option>
            <option value="ty">{getYearLabel('ty')}</option>
            <option value="be">{getYearLabel('be')}</option>
          </select>
        </div>
        {!showForm && (
          <div className="flex items-end">
            <button
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              disabled={loading}
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
              {editingId ? 'Edit Subject' : 'Add New Subject'} for {getYearLabel(year)}
            </h4>
            <button
              onClick={() => {
                setShowForm(false);
                setEditingId(null);
                setFormData({
                  name: '',
                  short_name: '',
                  hrs_per_week_lec: '4',
                  hrs_per_week_practical: '1',
                  practical_duration: '2',
                  practical_type: 'Specific Lab',
                  required_labs: '',
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
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., Data Structures"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Subject Short Form
                </label>
                <input
                  type="text"
                  value={formData.short_name}
                  onChange={(e) => handleChange('short_name', e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., DS"
                  required
                />
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
                  value={formData.hrs_per_week_lec}
                  onChange={(e) => handleChange('hrs_per_week_lec', e.target.value)}
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
                  value={formData.hrs_per_week_practical}
                  onChange={(e) => handleChange('hrs_per_week_practical', e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {parseInt(formData.hrs_per_week_practical) > 0 && (
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
                        value="Specific Lab"
                        checked={formData.practical_type === 'Specific Lab'}
                        onChange={(e) => handleChange('practical_type', e.target.value)}
                        className="w-4 h-4 text-blue-600 mt-1"
                      />
                      <div className="flex-1">
                        <span className="text-slate-700">Requires specific lab(s)</span>
                        {formData.practical_type === 'Specific Lab' && (
                          <div className="mt-3 pl-6 space-y-2 bg-white p-3 rounded border border-slate-200">
                            <div>
                              <label className="block text-sm font-medium text-slate-700 mb-2">
                                Required Lab
                              </label>
                              <select
                                value={formData.required_labs}
                                onChange={(e) => handleChange('required_labs', e.target.value)}
                                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                              >
                                <option value="">Select a lab (optional)</option>
                                {labs && labs.length > 0 ? (
                                  labs.map((lab) => (
                                    <option key={lab._id} value={lab.name}>
                                      {lab.name}
                                    </option>
                                  ))
                                ) : (
                                  <option disabled>No labs available</option>
                                )}
                              </select>
                            </div>
                          </div>
                        )}
                      </div>
                    </label>

                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="practical_type"
                        value="Common Lab"
                        checked={formData.practical_type === 'Common Lab'}
                        onChange={(e) => handleChange('practical_type', e.target.value)}
                        className="w-4 h-4 text-blue-600"
                      />
                      <span className="text-slate-700">Common Lab</span>
                    </label>
                  </div>
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <button
                type="submit"
                className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                disabled={loading}
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
                    name: '',
                    short_name: '',
                    hrs_per_week_lec: '4',
                    hrs_per_week_practical: '1',
                    practical_duration: '2',
                    practical_type: 'Specific Lab',
                    required_labs: '',
                  });
                }}
                className="px-6 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50"
                disabled={loading}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-gradient-to-br from-blue-50 to-slate-50 rounded-xl shadow-lg p-6 border border-slate-200">
        <h4 className="text-xl font-bold text-slate-800 mb-4">
          Subjects for {getYearLabel(year)} ({subjects.length})
        </h4>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-slate-500">Loading subjects...</p>
          </div>
        ) : subjects.length > 0 ? (
          <div className="space-y-4">
            {subjects.map((subject) => (
              <div
                key={subject._id}
                className="bg-white rounded-lg p-5 border border-slate-200 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <h5 className="text-lg font-bold text-slate-800">
                        {subject.name}
                      </h5>
                      <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold">
                        {subject.short_name}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="flex items-center gap-2">
                        <span className="text-slate-600 font-medium">Lectures/Week:</span>
                        <span className="text-slate-800 font-semibold">
                          {subject.hrs_per_week_lec}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-600 font-medium">Practicals/Week:</span>
                        <span className="text-slate-800 font-semibold">
                          {subject.hrs_per_week_practical}
                        </span>
                      </div>
                      {subject.hrs_per_week_practical > 0 && (
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
                          {subject.practical_type === 'Specific Lab' && subject.required_labs && (
                            <div className="col-span-2 flex items-start gap-2">
                              <span className="text-slate-600 font-medium">Required Lab:</span>
                              <span className="text-slate-800 font-semibold">
                                {subject.required_labs}
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
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
                      title="Edit subject"
                      disabled={loading}
                    >
                      <Edit2 size={18} />
                    </button>
                    <button
                      onClick={() => handleDelete(subject._id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                      title="Delete subject"
                      disabled={loading}
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
            <p className="text-slate-500 text-lg">No subjects added for {getYearLabel(year)} yet</p>
            <p className="text-slate-400 text-sm mt-2">
              Click "Add Subject" to get started
            </p>
          </div>
        )}
      </div>
    </div>
  );
}