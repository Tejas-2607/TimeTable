import { useState, useEffect } from 'react';
import { Trash2, Edit2, Plus, Save, X } from 'lucide-react';
import {
  getAllLabs,
  addLab,
  updateLab,
  deleteLab,
} from '../services/labsService';

export default function LabsData() {
  const [labs, setLabs] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    short_name: '',
  });

  // ✅ Load labs from backend
  const loadLabs = async () => {
    try {
      setLoading(true);
      const data = await getAllLabs();
      // Sort newest first if backend sends `created_at`
      const sorted = data.sort(
        (a, b) => new Date(b.created_at) - new Date(a.created_at)
      );
      setLabs(sorted);
    } catch (error) {
      console.error('Error loading labs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLabs();
  }, []);

  // ✅ Handle Save or Update
  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      if (editingId) {
        await updateLab(editingId, formData);
      } else {
        await addLab(formData);
      }

      setFormData({ name: '', short_name: '' });
      setEditingId(null);
      setShowForm(false);
      loadLabs();
    } catch (error) {
      console.error('Error saving lab:', error);
    }
  };

  // ✅ Edit existing lab
  const handleEdit = (lab) => {
    setFormData({
      name: lab.name,
      short_name: lab.short_name,
    });
    setEditingId(lab._id || lab.id);
    setShowForm(true);
  };

  // ✅ Delete lab
  const handleDelete = async (id) => {
    if (confirm('Are you sure you want to delete this lab?')) {
      try {
        id = { "_id": id }
        await deleteLab(id);
        loadLabs();
      } catch (error) {
        console.error('Error deleting lab:', error);
      }
    }
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-3xl font-bold text-slate-800 tracking-tight">Labs Data</h2>
          <p className="text-slate-500 mt-2">Manage laboratory information</p>
        </div>
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-6 py-3 rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all shadow-lg active:scale-95"
          >
            <Plus size={20} />
            Add Lab
          </button>
        )}
      </div>

      {showForm && (
        <div className="bg-white rounded-xl shadow-md p-6 mb-8 border border-slate-200">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-slate-800">
              {editingId ? 'Edit Lab' : 'Add New Lab'}
            </h3>
            <button
              onClick={() => {
                setShowForm(false);
                setEditingId(null);
                setFormData({ name: '', short_name: '' });
              }}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Lab Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-4 focus:ring-slate-100 focus:border-slate-400 outline-none transition-all shadow-sm"
                  placeholder="e.g., Computer Networks Lab"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Lab Short Form
                </label>
                <input
                  type="text"
                  value={formData.short_name}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      short_name: e.target.value,
                    })
                  }
                  className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-4 focus:ring-slate-100 focus:border-slate-400 outline-none transition-all shadow-sm"
                  placeholder="e.g., CNL"
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
                {editingId ? 'Update' : 'Save'} Lab
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditingId(null);
                  setFormData({ name: '', short_name: '' });
                }}
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
              <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700 w-[45%]">
                Lab Name
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700 w-[35%]">
                Short Form
              </th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-slate-700 w-[20%]">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {loading ? (
              // Skeleton Loader Rows
              [...Array(4)].map((_, idx) => (
                <tr key={`skeleton-${idx}`} className="animate-pulse">
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
            ) : labs.length > 0 ? (
              labs.map((lab) => (
                <tr key={lab._id || lab.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-6 py-4 text-sm font-semibold text-slate-800">
                    {lab.name}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500">
                    {lab.short_name}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleEdit(lab)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      >
                        <Edit2 size={16} />
                      </button>
                      <button
                        onClick={() => handleDelete(lab._id || lab.id)}
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
                <td colSpan="3" className="text-center py-12 text-slate-500">
                  No labs added yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
