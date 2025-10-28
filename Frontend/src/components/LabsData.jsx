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
  const [formData, setFormData] = useState({
    name: '',
    short_name: '',
  });

  // ✅ Load labs from backend
  const loadLabs = async () => {
    try {
      const data = await getAllLabs();
      // Sort newest first if backend sends `created_at`
      const sorted = data.sort(
        (a, b) => new Date(b.created_at) - new Date(a.created_at)
      );
      setLabs(sorted);
    } catch (error) {
      console.error('Error loading labs:', error);
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
        id = {"_id":id}
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
          <h2 className="text-3xl font-bold text-slate-800">Labs Data</h2>
          <p className="text-slate-600 mt-1">Manage laboratory information</p>
        </div>
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors shadow-lg"
          >
            <Plus size={20} />
            Add Lab
          </button>
        )}
      </div>

      {showForm && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8 border border-slate-200">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-slate-800">
              {editingId ? 'Edit Lab' : 'Add New Lab'}
            </h3>
            <button
              onClick={() => {
                setShowForm(false);
                setEditingId(null);
                setFormData({ name: '', short_name: '' });
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
                  Lab Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., CNL"
                  required
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
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
                Lab Name
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">
                Short Form
              </th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-slate-700">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {labs.map((lab) => (
              <tr key={lab._id || lab.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4 text-sm font-medium text-slate-800">
                  {lab.name}
                </td>
                <td className="px-6 py-4 text-sm text-slate-600">
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
        {labs.length === 0 && (
          <div className="text-center py-12 text-slate-500">No labs added yet</div>
        )}
      </div>
    </div>
  );
}
