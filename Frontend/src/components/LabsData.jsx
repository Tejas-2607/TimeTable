import { useState, useEffect } from "react";
import { Trash2, Edit2, Plus, Save, X, Clock, Settings2 } from "lucide-react";
import {
  getAllLabs,
  addLab,
  updateLab,
  deleteLab,
} from "../services/labsService";
import {
  getLabSessions,
  saveLabSessions,
} from "../services/labSettingsService";

// --- Modal Component ---
const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm animate-in fade-in"
        onClick={onClose}
      />
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-lg z-10 overflow-hidden animate-in zoom-in-95 duration-200">
        <div className="px-8 py-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <h3 className="text-xl font-bold text-slate-800">{title}</h3>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        <div className="p-8">{children}</div>
      </div>
    </div>
  );
};

export default function LabsData() {
  const [labs, setLabs] = useState([]);
  const [loading, setLoading] = useState(true);

  // Lab CRUD States
  const [isLabModalOpen, setIsLabModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ name: "", short_name: "" });

  // Session CRUD States
  const [labSessions, setLabSessions] = useState([]);
  const [isSessionModalOpen, setIsSessionModalOpen] = useState(false);
  const [editingSessionId, setEditingSessionId] = useState(null);
  const [sessionFormData, setSessionFormData] = useState({
    startTime: "",
    endTime: "",
  });

  // ✅ Load Data
  const loadLabs = async () => {
    try {
      setLoading(true);
      const data = await getAllLabs();

      if (!data) {
        setLabs([]);
        return;
      }

      // Handle cases where data might be an array or an object containing an array
      let labsArray = [];
      if (Array.isArray(data)) {
        labsArray = data;
      } else if (data.labs && Array.isArray(data.labs)) {
        labsArray = data.labs;
      } else if (data.data && Array.isArray(data.data)) {
        labsArray = data.data;
      }

      const sorted = labsArray.sort(
        (a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0),
      );
      setLabs(sorted);
    } catch (error) {
      console.error("Error loading labs:", error);
      setLabs([]);
    } finally {
      setLoading(false);
    }
  };

  const loadLabSessions = async () => {
    try {
      const sessions = await getLabSessions();
      setLabSessions(sessions);
    } catch (error) {
      console.error("Error loading lab sessions:", error);
      setLabSessions([]);
    }
  };

  useEffect(() => {
    loadLabs();
    loadLabSessions();
  }, []);

  // ✅ Lab Operations
  const handleOpenLabModal = (lab = null) => {
    if (lab) {
      setFormData({ name: lab.name, short_name: lab.short_name });
      setEditingId(lab._id || lab.id);
    } else {
      setFormData({ name: "", short_name: "" });
      setEditingId(null);
    }
    setIsLabModalOpen(true);
  };

  const handleLabSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await updateLab(editingId, formData);
      } else {
        await addLab(formData);
      }
      setIsLabModalOpen(false);
      loadLabs();
    } catch (error) {
      console.error("Error saving lab:", error);
    }
  };

  const handleDeleteLab = async (id) => {
    if (confirm("Are you sure you want to delete this lab?")) {
      try {
        await deleteLab({ _id: id });
        loadLabs();
      } catch (error) {
        console.error("Error deleting lab:", error);
      }
    }
  };

  // ✅ Session Operations
  const handleOpenSessionModal = (session = null) => {
    if (session) {
      setSessionFormData({
        startTime: session.startTime,
        endTime: session.endTime,
      });
      setEditingSessionId(session.id);
    } else {
      setSessionFormData({ startTime: "", endTime: "" });
      setEditingSessionId(null);
    }
    setIsSessionModalOpen(true);
  };

  const handleSaveSession = async () => {
    if (!sessionFormData.startTime || !sessionFormData.endTime) {
      alert("Please fill both times");
      return;
    }
    let updated;
    if (editingSessionId) {
      updated = labSessions.map((s) =>
        s.id === editingSessionId ? { ...s, ...sessionFormData } : s,
      );
    } else {
      updated = [...labSessions, { id: Date.now(), ...sessionFormData }];
    }
    updated.sort((a, b) => a.startTime.localeCompare(b.startTime));
    setLabSessions(updated);
    await saveLabSessions(updated);
    setIsSessionModalOpen(false);
  };

  const handleDeleteSession = async (id) => {
    if (confirm("Delete this session timing?")) {
      const updated = labSessions.filter((s) => s.id !== id);
      setLabSessions(updated);
      await saveLabSessions(updated);
    }
  };

  return (
    <div className="p-8 max-w-[1600px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-10">
        <div>
          <h2 className="text-4xl font-black text-slate-800 tracking-tight">
            Labs Management
          </h2>
          <p className="text-slate-500 mt-2 font-medium">
            Manage academic laboratories and session timings
          </p>
        </div>
        <button
          onClick={() => handleOpenLabModal()}
          className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-8 py-3.5 rounded-2xl hover:from-blue-700 hover:to-cyan-700 transition-all shadow-xl shadow-blue-200 active:scale-95 font-bold"
        >
          <Plus size={22} strokeWidth={3} />
          Add New Lab
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
        {/* elegant Session Sidebar - left col */}
        <div className="xl:col-span-1">
          <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="p-6 border-b border-slate-100 bg-slate-50/50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-200">
                    <Settings2 className="text-white" size={20} />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800">Lab Slots</h3>
                    <p className="text-xs text-slate-500">Global Timings</p>
                  </div>
                </div>
                <button
                  onClick={() => handleOpenSessionModal()}
                  className="p-2 bg-blue-50 text-blue-600 rounded-xl hover:bg-blue-100 transition-colors"
                >
                  <Plus size={18} strokeWidth={2.5} />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-3">
              {labSessions.length === 0 ? (
                <div className="text-center py-6 text-slate-400 text-sm italic">
                  No slots defined
                </div>
              ) : (
                labSessions.map((session, index) => (
                  <div
                    key={session.id}
                    className="group relative flex items-center justify-between p-4 rounded-2xl bg-slate-50 border border-slate-100 hover:border-blue-200 hover:bg-white transition-all hover:shadow-md"
                  >
                    <div className="flex flex-col">
                      <span className="text-[10px] uppercase font-bold text-slate-400 tracking-widest leading-none mb-1">
                        Slot {index + 1}
                      </span>
                      <div className="flex items-center gap-2 text-slate-700 font-bold">
                        <Clock size={14} className="text-blue-500" />
                        <span className="text-sm">
                          {session.startTime} — {session.endTime}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleOpenSessionModal(session)}
                        className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                      >
                        <Edit2 size={14} />
                      </button>
                      <button
                        onClick={() => handleDeleteSession(session.id)}
                        className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Labs Table - right col */}
        <div className="xl:col-span-3">
          <div className="bg-white rounded-3xl shadow-md border border-slate-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200/60">
                <tr>
                  <th className="px-8 py-5 text-left text-sm font-bold text-slate-700 w-[45%]">
                    Lab Name
                  </th>
                  <th className="px-8 py-5 text-left text-sm font-bold text-slate-700 w-[35%]">
                    Short Form
                  </th>
                  <th className="px-8 py-5 text-right text-sm font-bold text-slate-700 w-[20%]">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {loading
                  ? [...Array(4)].map((_, idx) => (
                      <tr key={idx} className="animate-pulse">
                        <td className="px-8 py-6">
                          <div className="h-4 bg-slate-200 rounded w-48"></div>
                        </td>
                        <td className="px-8 py-6">
                          <div className="h-4 bg-slate-200 rounded w-24"></div>
                        </td>
                        <td className="px-8 py-6 text-right">
                          <div className="w-16 h-8 bg-slate-200 rounded-lg ml-auto"></div>
                        </td>
                      </tr>
                    ))
                  : labs.map((lab) => (
                      <tr
                        key={lab._id || lab.id}
                        className="hover:bg-slate-50/80 transition-colors"
                      >
                        <td className="px-8 py-6 font-semibold text-slate-800 tracking-tight">
                          {lab.name}
                        </td>
                        <td className="px-8 py-6">
                          <span className="px-3 py-1 bg-slate-100 text-slate-600 text-xs font-black rounded-lg border border-slate-200">
                            {lab.short_name}
                          </span>
                        </td>
                        <td className="px-8 py-6 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => handleOpenLabModal(lab)}
                              className="p-2.5 text-blue-600 hover:bg-blue-50 rounded-xl transition-colors"
                            >
                              <Edit2 size={18} />
                            </button>
                            <button
                              onClick={() => handleDeleteLab(lab._id || lab.id)}
                              className="p-2.5 text-red-500 hover:bg-red-50 rounded-xl transition-colors"
                            >
                              <Trash2 size={18} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* --- MODALS --- */}

      {/* Lab Modal */}
      <Modal
        isOpen={isLabModalOpen}
        onClose={() => setIsLabModalOpen(false)}
        title={editingId ? "Edit Laboratory" : "Create New Laboratory"}
      >
        <form onSubmit={handleLabSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-bold text-slate-700 ml-1">
              Lab Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              className="w-full px-5 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-blue-50 focus:border-blue-400 outline-none transition-all font-medium"
              placeholder="e.g., Computer Vision Lab"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-bold text-slate-700 ml-1">
              Short Code
            </label>
            <input
              type="text"
              value={formData.short_name}
              onChange={(e) =>
                setFormData({ ...formData, short_name: e.target.value })
              }
              className="w-full px-5 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-blue-50 focus:border-blue-400 outline-none transition-all font-black tracking-widest"
              placeholder="e.g., CVL"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full py-4 bg-slate-900 text-white rounded-2xl font-bold shadow-lg hover:bg-slate-800 transition-all flex items-center justify-center gap-2"
          >
            <Save size={20} />
            {editingId ? "Update Lab" : "Save Laboratory"}
          </button>
        </form>
      </Modal>

      {/* Session Modal */}
      <Modal
        isOpen={isSessionModalOpen}
        onClose={() => setIsSessionModalOpen(false)}
        title={editingSessionId ? "Edit Session Slot" : "New Session Slot"}
      >
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-bold text-slate-700 ml-1">
                Start Time
              </label>
              <input
                type="time"
                value={sessionFormData.startTime}
                onChange={(e) =>
                  setSessionFormData({
                    ...sessionFormData,
                    startTime: e.target.value,
                  })
                }
                className="w-full px-5 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-blue-50 focus:border-blue-400 outline-none transition-all font-medium"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-bold text-slate-700 ml-1">
                End Time
              </label>
              <input
                type="time"
                value={sessionFormData.endTime}
                onChange={(e) =>
                  setSessionFormData({
                    ...sessionFormData,
                    endTime: e.target.value,
                  })
                }
                className="w-full px-5 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-blue-50 focus:border-blue-400 outline-none transition-all font-medium"
              />
            </div>
          </div>
          <button
            onClick={handleSaveSession}
            className="w-full py-4 bg-blue-600 text-white rounded-2xl font-bold shadow-lg hover:bg-blue-700 transition-all flex items-center justify-center gap-2"
          >
            <Save size={20} />
            Save Session
          </button>
        </div>
      </Modal>
    </div>
  );
}
