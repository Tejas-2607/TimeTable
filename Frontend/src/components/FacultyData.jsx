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
    name: '',
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
      console.log(sorted);

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
    const facultyData = { ...formData };

    try {
      console.log(facultyData);

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
      name: faculty.name,
      short_name: faculty.short_name,
    });
    setEditingId(faculty._id || faculty.id);
    setShowForm(true);
  };

  // ✅ Delete
  const handleDelete = async (id) => {
    if (confirm('Are you sure you want to delete this faculty?')) {
      try {
        id = { "_id": id };
        console.log(id);
        await deleteFaculty(id);
        await loadFaculties();
      } catch (error) {
        console.error('Error deleting faculty:', error);
        alert('Failed to delete faculty');
      }
    }
  };

  const resetForm = () => {
    setFormData({ title: 'Prof', name: '', short_name: '' });
    setEditingId(null);
    setShowForm(false);
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-3xl font-bold text-slate-800 tracking-tight">Faculty Data</h2>
          <p className="text-slate-500 mt-2">Manage faculty information</p>
        </div>
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-6 py-3 rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all shadow-lg active:scale-95"
          >
            <Plus size={20} />
            Add Faculty
          </button>
        )}
      </div>

      {showForm && (
        <div className="bg-white rounded-xl shadow-md p-6 mb-8 border border-slate-200">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-slate-800">
              {editingId ? 'Edit Faculty' : 'Add New Faculty'}
            </h3>
            <button
              onClick={resetForm}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Title
                </label>
                <select
                  value={formData.title}
                  onChange={(e) =>
                    setFormData({ ...formData, title: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-4 focus:ring-slate-100 focus:border-slate-400 outline-none transition-all shadow-sm"
                  required
                >
                  <option value="Prof">Prof</option>
                  <option value="Asst Prof">Asst Prof</option>
                  <option value="Dr">Dr</option>
                </select>
              </div>

              {/* Full Name */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Full Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-4 focus:ring-slate-100 focus:border-slate-400 outline-none transition-all shadow-sm"
                  required
                />
              </div>
            </div>

            {/* Short Name */}
            <div className="grid grid-cols-2 gap-6 mt-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Short Name
                </label>
                <input
                  type="text"
                  value={formData.short_name}
                  onChange={(e) =>
                    setFormData({ ...formData, short_name: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-4 focus:ring-slate-100 focus:border-slate-400 outline-none transition-all shadow-sm"
                  required
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-6 py-2 rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all shadow-md active:scale-95"
              >
                <Save size={18} />
                {editingId ? 'Update' : 'Save'} Faculty
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="px-6 py-2 border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors text-slate-600 font-medium"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-md overflow-hidden border border-slate-200">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200/60">
            <tr>
              <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700 w-[15%]">
                Title
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700 w-[40%]">
                Full Name
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700 w-[25%]">
                Short Name
              </th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-slate-700 w-[20%]">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {loading ? (
              // Skeleton Loader Rows
              [...Array(5)].map((_, idx) => (
                <tr key={`skeleton-${idx}`} className="animate-pulse">
                  <td className="px-6 py-4">
                    <div className="h-4 bg-slate-200 rounded w-16"></div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-4 bg-slate-200 rounded w-48"></div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-4 bg-slate-200 rounded w-24"></div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-8 h-8 bg-slate-200 rounded-lg"></div>
                      <div className="w-8 h-8 bg-slate-200 rounded-xl"></div>
                    </div>
                  </td>
                </tr>
              ))
            ) : faculties.length > 0 ? (
              faculties.map((faculty) => (
                <tr
                  key={faculty._id || faculty.id}
                  className="hover:bg-slate-50/80 transition-colors"
                >
                  <td className="px-6 py-4 text-sm text-slate-500">
                    {faculty.title}
                  </td>
                  <td className="px-6 py-4 text-sm font-semibold text-slate-800">
                    {faculty.name}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500">
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
                        className="p-2 text-red-500 hover:bg-red-50 rounded-xl transition-colors"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="4" className="text-center py-12 text-slate-500">
                  No faculty members added yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
