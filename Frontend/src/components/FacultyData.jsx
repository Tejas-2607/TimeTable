import { useState, useEffect } from 'react';
import { storage } from '../lib/storage';
import { Trash2, Edit2, Plus, Save, X } from 'lucide-react';

export default function FacultyData() {
  const [faculties, setFaculties] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    title: 'Prof',
    full_name: '',
    teaches_year: [],
  });

  useEffect(() => {
    loadFaculties();
  }, []);

  const loadFaculties = () => {
    const data = storage.faculties.getAll();
    setFaculties(data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const facultyData = {
      ...formData,
      teaches_year: formData.teaches_year.join(', '),
    };

    if (editingId) {
      storage.faculties.update(editingId, facultyData);
    } else {
      storage.faculties.insert(facultyData);
    }

    setFormData({ title: 'Prof', full_name: '', teaches_year: [] });
    setEditingId(null);
    setShowForm(false);
    loadFaculties();
  };

  const handleEdit = (faculty) => {
    setFormData({
      title: faculty.title,
      full_name: faculty.full_name,
      teaches_year: faculty.teaches_year.split(', '),
    });
    setEditingId(faculty.id);
    setShowForm(true);
  };

  const handleDelete = (id) => {
    if (confirm('Are you sure you want to delete this faculty?')) {
      storage.faculties.delete(id);
      loadFaculties();
    }
  };

  const toggleYear = (year) => {
    setFormData((prev) => ({
      ...prev,
      teaches_year: prev.teaches_year.includes(year)
        ? prev.teaches_year.filter((y) => y !== year)
        : [...prev.teaches_year, year],
    }));
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-3xl font-bold text-slate-800">Faculty Data</h2>
          <p className="text-slate-600 mt-1">Manage faculty information</p>
        </div>
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors shadow-lg"
          >
            <Plus size={20} />
            Add Faculty
          </button>
        )}
      </div>

      {showForm && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8 border border-slate-200">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-slate-800">
              {editingId ? 'Edit Faculty' : 'Add New Faculty'}
            </h3>
            <button
              onClick={() => {
                setShowForm(false);
                setEditingId(null);
                setFormData({ title: 'Prof', full_name: '', teaches_year: [] });
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
                  Title
                </label>
                <select
                  value={formData.title}
                  onChange={(e) =>
                    setFormData({ ...formData, title: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="Prof">Prof</option>
                  <option value="Asst Prof">Asst Prof</option>
                  <option value="Dr">Dr</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Full Name
                </label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) =>
                    setFormData({ ...formData, full_name: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-3">
                Teaches in Year
              </label>
              <div className="flex gap-4">
                {['SY', 'TY', 'Final Year'].map((year) => (
                  <label
                    key={year}
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={formData.teaches_year.includes(year)}
                      onChange={() => toggleYear(year)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                    />
                    <span className="text-slate-700">{year}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Save size={18} />
                {editingId ? 'Update' : 'Save'} Faculty
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditingId(null);
                  setFormData({ title: 'Prof', full_name: '', teaches_year: [] });
                }}
                className="px-6 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-slate-200">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">
                Title
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">
                Full Name
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">
                Teaches Year
              </th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-slate-700">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {faculties.map((faculty) => (
              <tr key={faculty.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4 text-sm text-slate-600">
                  {faculty.title}
                </td>
                <td className="px-6 py-4 text-sm font-medium text-slate-800">
                  {faculty.full_name}
                </td>
                <td className="px-6 py-4 text-sm text-slate-600">
                  {faculty.teaches_year}
                </td>
                <td className="px-6 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => handleEdit(faculty)}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={() => handleDelete(faculty.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {faculties.length === 0 && (
          <div className="text-center py-12 text-slate-500">
            No faculty members added yet
          </div>
        )}
      </div>
    </div>
  );
}
