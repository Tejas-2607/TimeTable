import { useState, useEffect } from 'react';
import { storage } from '../../lib/storage';
import { Plus, Trash2 } from 'lucide-react';

export default function DepartmentTimings({ data, onDataChange }) {
  const [formData, setFormData] = useState({
    lecture_duration: 60,
    day_start_time: '09:15',
    day_end_time: '17:20',
    breaks: [{ name: 'Lunch', start_time: '12:15', duration: 65 }],
  });

  useEffect(() => {
    loadTimings();
  }, []);

  const loadTimings = () => {
    const timings = storage.departmentTimings.get();

    if (timings) {
      setFormData({
        lecture_duration: timings.lecture_duration,
        day_start_time: timings.day_start_time,
        day_end_time: timings.day_end_time,
        breaks: timings.breaks || [],
      });
    }
  };

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const addBreak = () => {
    setFormData((prev) => ({
      ...prev,
      breaks: [...prev.breaks, { name: '', start_time: '', duration: 0 }],
    }));
  };

  const removeBreak = (index) => {
    setFormData((prev) => ({
      ...prev,
      breaks: prev.breaks.filter((_, i) => i !== index),
    }));
  };

  const updateBreak = (index, field, value) => {
    setFormData((prev) => ({
      ...prev,
      breaks: prev.breaks.map((brk, i) =>
        i === index ? { ...brk, [field]: value } : brk
      ),
    }));
  };

  const handleSave = () => {
    storage.departmentTimings.upsert(formData);
    onDataChange('timings', formData);
    alert('Timings saved successfully!');
  };

  return (
    <div className="space-y-8">
      <div>
        <h3 className="text-2xl font-bold text-slate-800 mb-6">
          Step 1: Department Timings & Time Slots
        </h3>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Lecture Duration (mins)
          </label>
          <input
            type="number"
            value={formData.lecture_duration}
            onChange={(e) => handleChange('lecture_duration', e.target.value)}
            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Day Start Time
          </label>
          <input
            type="time"
            value={formData.day_start_time}
            onChange={(e) => handleChange('day_start_time', e.target.value)}
            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Day End Time
          </label>
          <input
            type="time"
            value={formData.day_end_time}
            onChange={(e) => handleChange('day_end_time', e.target.value)}
            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      <div className="border-t border-slate-200 pt-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-lg font-semibold text-slate-800">Breaks</h4>
          <button
            onClick={addBreak}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm"
          >
            <Plus size={16} />
            Add Break
          </button>
        </div>

        <div className="space-y-4">
          {formData.breaks.map((brk, index) => (
            <div
              key={index}
              className="grid grid-cols-4 gap-4 p-4 bg-slate-50 rounded-lg border border-slate-200"
            >
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Break Name
                </label>
                <input
                  type="text"
                  value={brk.name}
                  onChange={(e) => updateBreak(index, 'name', e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., Lunch"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Break Start Time
                </label>
                <input
                  type="time"
                  value={brk.start_time}
                  onChange={(e) =>
                    updateBreak(index, 'start_time', e.target.value)
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Break Duration (mins)
                </label>
                <input
                  type="number"
                  value={brk.duration}
                  onChange={(e) =>
                    updateBreak(index, 'duration', e.target.value)
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="flex items-end">
                <button
                  onClick={() => removeBreak(index)}
                  className="w-full bg-red-50 text-red-600 px-3 py-2 rounded-lg hover:bg-red-100 transition-colors flex items-center justify-center gap-2"
                >
                  <Trash2 size={16} />
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="pt-6">
        <button
          onClick={handleSave}
          className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors text-lg font-semibold"
        >
          Set/Update Timings & Generate Slots
        </button>
      </div>
    </div>
  );
}
