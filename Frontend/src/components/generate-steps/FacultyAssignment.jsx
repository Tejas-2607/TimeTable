import { useState, useEffect } from 'react';
import { Plus, Trash2, Edit2, X } from 'lucide-react';
import { getSubjects } from '../../services/subjectService';
import { getFaculties } from '../../services/facultyService';
import { 
  getFacultyWorkload, 
  addFacultyWorkload, 
  updateFacultyWorkload, 
  deleteFacultyWorkload 
} from '../../services/workloadService';

export default function FacultyAssignment({ data, onDataChange }) {
  const [year, setYear] = useState('sy');
  const [faculties, setFaculties] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [workloads, setWorkloads] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState(null);

  const [formData, setFormData] = useState({
    faculty_id: '',
    subject: '',
    subject_full: '',
    division: 'A',
    batches: [],
    theory_hrs: '0',
    practical_hrs: '0',
  });

  // Load all static data on mount
  useEffect(() => {
    loadAllStaticData();
    loadWorkloads();
  }, []);

  // Load workloads when year changes
  useEffect(() => {
    if (year) {
      loadWorkloads();
    }
  }, [year]);

  // Update selected subject info when subject changes
  useEffect(() => {
    if (formData.subject) {
      const yearSubjectsArray = getYearSubjects();
      const subject = yearSubjectsArray.find(s => s.short_name === formData.subject);
      setSelectedSubject(subject || null);
      if (subject) {
        setFormData(prev => ({ ...prev, subject_full: subject.name }));
      }
    } else {
      setSelectedSubject(null);
    }
  }, [formData.subject, subjects, year]);

  const loadAllStaticData = async () => {
    try {
      setLoading(true);
      
      // Load faculties
      const facultiesRes = await getFaculties();
      const facultiesArray = Array.isArray(facultiesRes) ? facultiesRes : facultiesRes.data || [];
      setFaculties(
        facultiesArray.sort((a, b) => 
          `${a.title || ''} ${a.full_name || ''}`.localeCompare(`${b.title || ''} ${b.full_name || ''}`)
        )
      );

      // Load subjects for all years
      const subjectsRes = await getSubjects();
      const subjectsData = subjectsRes.data || subjectsRes;
      setSubjects(subjectsData || {});
    } catch (err) {
      console.error('Error loading static data:', err);
      setFaculties([]);
      setSubjects({});
    } finally {
      setLoading(false);
    }
  };

  const loadWorkloads = async () => {
    try {
      setLoading(true);
      const res = await getFacultyWorkload();
      const workloadData = res.workloads || res.data?.workloads || [];
      
      // console.log('All workload data:', workloadData);
      
      // Filter workloads by year - handle both uppercase and lowercase
      const yearFilter = year.toUpperCase();
      const yearWorkloads = workloadData.filter(w => {
        const wYear = String(w.year).toUpperCase();
        return wYear === yearFilter;
      });
      
      console.log('Filtered workloads for', yearFilter, ':', yearWorkloads);
      setWorkloads(yearWorkloads);
    } catch (err) {
      console.error('Error loading workloads:', err);
      setWorkloads([]);
    } finally {
      setLoading(false);
    }
  };

  const getSubjectType = (subject) => {
    if (!subject) return null;
    
    const theoryHrs = subject.hrs_per_week_lec || 0;
    const practicalHrs = subject.hrs_per_week_practical || 0;

    if (theoryHrs > 0 && practicalHrs > 0) return 'Both';
    if (theoryHrs > 0) return 'Theory';
    if (practicalHrs > 0) return 'Practical';
    return null;
  };

  const getYearSubjects = () => {
    if (!subjects || typeof subjects !== 'object') return [];
    const yearKey = year.toLowerCase();
    const yearSubjectsArray = subjects[yearKey];
    return Array.isArray(yearSubjectsArray) ? yearSubjectsArray : [];
  };

  const getStructureInfo = () => {
    // Get divisions (A, B, C, D, etc.) - assuming max 4 divisions
    const divisions = ['A', 'B', 'C', 'D'];
    // Get batches (Batch 1, Batch 2, Batch 3)
    const batches = ['Batch 1', 'Batch 2', 'Batch 3'];
    return { divisions, batches };
  };

  const handleEdit = (workload) => {
    setFormData({
      faculty_id: workload.faculty_id,
      subject: workload.subject,
      subject_full: workload.subject_full,
      division: workload.division,
      batches: workload.batches || [],
      theory_hrs: String(workload.theory_hrs || 0),
      practical_hrs: String(workload.practical_hrs || 0),
    });
    setEditingId(workload._id);
    setShowForm(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);

      const workloadData = {
        faculty_id: formData.faculty_id,
        year: year.toUpperCase(),
        subject: formData.subject,
        subject_full: formData.subject_full,
        division: formData.division,
        batches: formData.batches,
        theory_hrs: parseInt(formData.theory_hrs),
        practical_hrs: parseInt(formData.practical_hrs),
      };

      if (editingId) {
        await updateFacultyWorkload({
          _id: editingId,
          ...workloadData,
        });
      } else {
        await addFacultyWorkload(workloadData);
      }

      setFormData({
        faculty_id: '',
        subject: '',
        subject_full: '',
        division: 'A',
        batches: [],
        theory_hrs: '0',
        practical_hrs: '0',
      });
      setEditingId(null);
      setShowForm(false);

      await loadWorkloads();
    } catch (err) {
      console.error('Error submitting workload:', err);
      alert('Error saving workload. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (confirm('Are you sure you want to delete this workload?')) {
      try {
        setLoading(true);
        await deleteFacultyWorkload(id);
        await loadWorkloads();
      } catch (err) {
        console.error('Error deleting workload:', err);
        alert('Error deleting workload. Please try again.');
      } finally {
        setLoading(false);
      }
    }
  };

  const toggleBatch = (batch) => {
    setFormData(prev => ({
      ...prev,
      batches: prev.batches.includes(batch)
        ? prev.batches.filter(b => b !== batch)
        : [...prev.batches, batch],
    }));
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

  const getSubjectTypeLabel = (type) => {
    switch (type) {
      case 'Theory':
        return 'bg-green-100 text-green-700';
      case 'Practical':
        return 'bg-orange-100 text-orange-700';
      case 'Both':
        return 'bg-purple-100 text-purple-700';
      default:
        return 'bg-slate-100 text-slate-700';
    }
  };

  const getFacultyName = (facultyId) => {
    const faculty = faculties.find(f => f._id === facultyId);
    return faculty ? `${faculty.title || ''} ${faculty.name || ''}`.trim() : 'Unknown';
  };

  const { divisions, batches } = getStructureInfo();
  const yearSubjects = getYearSubjects();

  return (
    <div className="space-y-8">
      <div>
        <h3 className="text-2xl font-bold text-slate-800 mb-2">
          Step 3: Faculty Workload Assignment
        </h3>
        <p className="text-slate-600">
          Assign faculties to subjects and manage their workload for each year
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
              disabled={loading || yearSubjects.length === 0 || faculties.length === 0}
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
              {editingId ? 'Edit Assignment' : 'Add New Assignment'} for {getYearLabel(year)}
            </h4>
            <button
              onClick={() => {
                setShowForm(false);
                setEditingId(null);
                setFormData({
                  faculty_id: '',
                  subject: '',
                  subject_full: '',
                  division: 'A',
                  batches: [],
                  theory_hrs: '0',
                  practical_hrs: '0',
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
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Select Subject</option>
                  {yearSubjects.map((subject) => {
                    const type = getSubjectType(subject);
                    return (
                      <option key={subject._id} value={subject.short_name}>
                        {subject.name} ({subject.short_name}) - {type}
                      </option>
                    );
                  })}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Faculty Name
                </label>
                <select
                  value={formData.faculty_id}
                  onChange={(e) => setFormData({ ...formData, faculty_id: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Select Faculty</option>
                  {faculties.map((faculty) => (
                    <option key={faculty._id} value={faculty._id}>
                      {faculty.title} {faculty.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className={`grid ${selectedSubject && (getSubjectType(selectedSubject) === 'Practical' || getSubjectType(selectedSubject) === 'Both') ? 'grid-cols-2' : 'grid-cols-1'} gap-6`}>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Division
                </label>
                <select
                  value={formData.division}
                  onChange={(e) => setFormData({ ...formData, division: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  {divisions.map((div) => (
                    <option key={div} value={div}>
                      Division {div}
                    </option>
                  ))}
                </select>
              </div>

              {selectedSubject && (getSubjectType(selectedSubject) === 'Practical' || getSubjectType(selectedSubject) === 'Both') && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-3">
                    Batches (for Practical)
                  </label>
                  <div className="flex flex-wrap gap-4">
                    {batches.map((batch) => (
                      <label key={batch} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.batches.includes(batch)}
                          onChange={() => toggleBatch(batch)}
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
              {selectedSubject && (getSubjectType(selectedSubject) === 'Theory' || getSubjectType(selectedSubject) === 'Both') && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Theory Workload (hrs/week)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    value={formData.theory_hrs}
                    onChange={(e) => setFormData({ ...formData, theory_hrs: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
              )}

              {selectedSubject && (getSubjectType(selectedSubject) === 'Practical' || getSubjectType(selectedSubject) === 'Both') && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Practical Workload (hrs/week)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    value={formData.practical_hrs}
                    onChange={(e) => setFormData({ ...formData, practical_hrs: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
              )}
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                disabled={loading || !selectedSubject}
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
                    subject: '',
                    subject_full: '',
                    division: 'A',
                    batches: [],
                    theory_hrs: '0',
                    practical_hrs: '0',
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
          Faculty Workload for {getYearLabel(year)} ({workloads.length})
        </h4>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-slate-500">Loading workloads...</p>
          </div>
        ) : workloads.length > 0 ? (
          <div className="space-y-4">
            {workloads.map((workload) => {
              const subject = yearSubjects.find(s => s.short_name === workload.subject);
              const subjectType = getSubjectType(subject);

              return (
                <div
                  key={workload._id}
                  className="bg-white rounded-lg p-5 border border-slate-200 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 grid grid-cols-2 gap-x-6 gap-y-3">
                      <div>
                        <span className="text-xs font-semibold text-slate-500 uppercase">Faculty</span>
                        <p className="text-slate-800 font-semibold mt-1">
                          {getFacultyName(workload.faculty_id)}
                        </p>
                      </div>
                      <div>
                        <span className="text-xs font-semibold text-slate-500 uppercase">Subject</span>
                        <p className="text-slate-800 font-semibold mt-1">
                          {workload.subject_full}
                          <span className={`ml-2 px-2 py-1 rounded text-xs font-semibold ${getSubjectTypeLabel(subjectType)}`}>
                            {workload.subject}
                          </span>
                        </p>
                      </div>
                      <div>
                        <span className="text-xs font-semibold text-slate-500 uppercase">Division & Batches</span>
                        <p className="text-slate-800 font-semibold mt-1">
                          Division {workload.division}
                          {workload.batches && workload.batches.length > 0 && ` - ${workload.batches.join(', ')}`}
                        </p>
                      </div>
                      <div>
                        <span className="text-xs font-semibold text-slate-500 uppercase">Workload</span>
                        <p className="text-slate-800 font-semibold mt-1">
                          {subjectType === 'Both'
                            ? `${workload.theory_hrs} (Theory) + ${workload.practical_hrs} (Practical) hrs/week`
                            : subjectType === 'Theory'
                            ? `${workload.theory_hrs} hrs/week`
                            : `${workload.practical_hrs} hrs/week`}
                        </p>
                      </div>
                      <div className="col-span-2">
                        <span className="text-xs font-semibold text-slate-500 uppercase">Assignment Type</span>
                        <p className="text-slate-800 font-semibold mt-1">
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${
                            subjectType === 'Theory'
                              ? 'bg-green-100 text-green-700'
                              : subjectType === 'Practical'
                              ? 'bg-orange-100 text-orange-700'
                              : 'bg-blue-100 text-blue-700'
                          }`}>
                            {subjectType === 'Both' ? 'Theory + Practical' : subjectType}
                          </span>
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => handleEdit(workload)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
                        title="Edit assignment"
                        disabled={loading}
                      >
                        <Edit2 size={18} />
                      </button>
                      <button
                        onClick={() => handleDelete(workload._id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                        title="Delete assignment"
                        disabled={loading}
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-slate-500 text-lg">No workloads assigned for {getYearLabel(year)} yet</p>
            <p className="text-slate-400 text-sm mt-2">
              Click "Add Assignment" to get started
            </p>
          </div>
        )}
      </div>
    </div>
  );
}