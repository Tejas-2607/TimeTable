import { useState, useEffect } from 'react';
import { Trash2, Edit2, Plus, Save, X } from 'lucide-react';
import {
  getFaculties,
  createFaculty,
  updateFaculty,
  deleteFaculty,
} from '../services/facultyService';

export default function FacultyData() {
  const [faculties, setFaculties] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: 'Prof',
    full_name: '',
    short_name: '',
  });

  // ✅ Load faculties from backend
  useEffect(() => {
    loadFaculties();
  }, []);

  const loadFaculties = async () => {
    try {
      setLoading(true);
      const data = await getFaculties();
      // Sort by created_at if available
      const sorted = data.sort(
        (a, b) => new Date(b.created_at) - new Date(a.created_at)
      );
      setFaculties(sorted);
    } catch (error) {
      console.error('Failed to load faculties:', error);
      alert('Error loading faculties');
    } finally {
      setLoading(false);
    }
  };

  // ✅ Submit (Add / Edit)
  const handleSubmit = async (e) => {
    e.preventDefault();

    const facultyData = {
      ...formData,
    };

    try {
      if (editingId) {
        await updateFaculty(editingId, facultyData);
      } else {
        await createFaculty(facultyData);
      }
      await loadFaculties();
      resetForm();
    } catch (error) {
      console.error('Error saving faculty:', error);
      alert('Failed to save faculty');
    }
  };

  // ✅ Edit
  const handleEdit = (faculty) => {
    setFormData({
      title: faculty.title,
      full_name: faculty.full_name,
      short_name : faculty.short_name
    });
    setEditingId(faculty._id || faculty.id);
    setShowForm(true);
  };

  // ✅ Delete
  const handleDelete = async (id) => {
    if (confirm('Are you sure you want to delete this faculty?')) {
      try {
        await deleteFaculty(id);
        await loadFaculties();
      } catch (error) {
        console.error('Error deleting faculty:', error);
        alert('Failed to delete faculty');
      }
    }
  };

  const toggleYear = (year) => {
    setFormData((prev) => ({
      ...prev
    }));
  };

  const resetForm = () => {
    setFormData({ title: 'Prof', full_name: '', teaches_year: [] });
    setEditingId(null);
    setShowForm(false);
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
              onClick={resetForm}
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
              <label className="block text-sm font-medium text-slate-700 mb-2">
                  Short Name
                </label>
                <input
                  type="text"
                  value={formData.short_name}
                  onChange={(e) =>
                    setFormData({ ...formData, full_name: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
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
                onClick={resetForm}
                className="px-6 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-slate-200">
        {loading ? (
          <div className="text-center py-12 text-slate-500">Loading...</div>
        ) : faculties.length > 0 ? (
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
                  Short Name
                </th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-slate-700">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {faculties.map((faculty) => (
                <tr
                  key={faculty._id || faculty.id}
                  className="hover:bg-slate-50 transition-colors"
                >
                  <td className="px-6 py-4 text-sm text-slate-600">
                    {faculty.title}
                  </td>
                  <td className="px-6 py-4 text-sm font-medium text-slate-800">
                    {faculty.full_name}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">
                    {faculty.short_name}
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
                        onClick={() =>
                          handleDelete(faculty._id || faculty.id)
                        }
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
        ) : (
          <div className="text-center py-12 text-slate-500">
            No faculty members added yet
          </div>
        )}
      </div>
    </div>
  );
}
