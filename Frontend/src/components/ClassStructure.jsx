import { useState, useEffect } from 'react';
import { Save, Plus, Trash2, ChevronDown, CheckSquare, Square } from 'lucide-react';
import { saveClassStructure, getClassStructure } from '../services/classStructureService';

const AVAILABLE_YEARS = ['FY', 'SY', 'TY', 'BE'];

export default function ClassStructure() {
  const [structures, setStructures] = useState({});
  const [loading, setLoading] = useState(true);
  const [showYearDropdown, setShowYearDropdown] = useState(false);

  // ✅ Load from backend
  useEffect(() => {
    loadStructures();
  }, []);

  const loadStructures = async () => {
    try {
      setLoading(true);
      const data = await getClassStructure();
      if (data && Object.keys(data).length > 0) {
        const { _id, ...structureData } = data;
        // Normalize keys to uppercase
        const normalized = {};
        Object.entries(structureData).forEach(([k, v]) => {
          normalized[k.toUpperCase()] = v;
        });
        setStructures(normalized);
      } else {
        // Default only SY for first time view
        setStructures({
          SY: { num_divisions: 1, batches_per_division: 2 },
        });
      }
    } catch (error) {
      console.error('Failed to load class structure:', error);
      setStructures({
        SY: { num_divisions: 1, batches_per_division: 2 },
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleYear = (year) => {
    const upperYear = year.toUpperCase();
    setStructures(prev => {
      const next = { ...prev };
      if (next[upperYear]) {
        delete next[upperYear];
      } else {
        next[upperYear] = { num_divisions: 1, batches_per_division: 2 };
      }
      return next;
    });
  };

  const handleChange = (year, field, value) => {
    setStructures((prev) => ({
      ...prev,
      [year]: {
        ...prev[year],
        [field]: parseInt(value) || 0,
      },
    }));
  };

  const handleAddCustomYear = () => {
    const yearName = prompt('Enter custom class name (e.g., Diploma):');
    if (yearName && yearName.trim()) {
      const name = yearName.trim().toUpperCase();
      if (structures[name]) {
        alert('Class already exists!');
        return;
      }
      setStructures(prev => ({
        ...prev,
        [name]: { num_divisions: 1, batches_per_division: 3 }
      }));
    }
  };

  const getTotalBatches = (year) => {
    const yearData = structures[year];
    if (!yearData) return 0;
    return (yearData.num_divisions || 0) * (yearData.batches_per_division || 0);
  };

  const handleSave = async () => {
    try {
      await saveClassStructure(structures);
      alert('Class structure saved successfully!');
    } catch (error) {
      alert('Failed to save class structure.');
      console.error(error);
    }
  };

  return (
    <div className="p-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h2 className="text-3xl font-bold text-slate-800 tracking-tight">Class Structure</h2>
          <p className="text-slate-500 mt-2">
            Select years and configure their divisions & batches
          </p>
        </div>

        <div className="flex gap-3 w-full md:w-auto">
          {/* Year Selector Dropdown */}
          <div className="relative flex-1 md:flex-initial">
            <button
              onClick={() => setShowYearDropdown(!showYearDropdown)}
              className="w-full md:w-56 flex items-center justify-between gap-2 bg-white border border-slate-300 px-4 py-2.5 rounded-xl hover:bg-slate-50 transition-all shadow-sm active:scale-[0.98]"
            >
              <span className="font-semibold text-slate-700">Select Years</span>
              <ChevronDown size={20} className={`text-slate-400 transition-transform ${showYearDropdown ? 'rotate-180' : ''}`} />
            </button>

            {showYearDropdown && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowYearDropdown(false)}
                />
                <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-slate-200 rounded-xl shadow-xl z-20 py-2 min-w-[200px]">
                  {AVAILABLE_YEARS.map(year => (
                    <button
                      key={year}
                      onClick={() => toggleYear(year)}
                      className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 transition-colors"
                    >
                      {structures[year] ? (
                        <CheckSquare size={20} className="text-blue-600" />
                      ) : (
                        <Square size={20} className="text-slate-300" />
                      )}
                      <span className={`font-medium ${structures[year] ? 'text-slate-900' : 'text-slate-500'}`}>
                        {year}
                      </span>
                    </button>
                  ))}
                  <div className="border-t border-slate-100 mt-1 pt-1">
                    <button
                      onClick={() => {
                        setShowYearDropdown(false);
                        handleAddCustomYear();
                      }}
                      className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 text-blue-600 transition-colors font-semibold"
                    >
                      <Plus size={18} />
                      Add Custom Class
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>

          <button
            onClick={handleSave}
            disabled={loading || Object.keys(structures).length === 0}
            className="flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-6 py-2.5 rounded-xl hover:from-blue-700 hover:to-cyan-700 transition-all shadow-lg active:scale-95 font-semibold disabled:opacity-50 disabled:scale-100"
          >
            <Save size={20} />
            Save Structure
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[...Array(3)].map((_, idx) => (
              <div key={idx} className="bg-white rounded-2xl shadow-md p-6 border border-slate-200 animate-pulse h-64" />
            ))}
          </div>
        ) : Object.keys(structures).length === 0 ? (
          <div className="py-20 text-center bg-white rounded-3xl border-2 border-dashed border-slate-200 shadow-sm">
            <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <Square size={32} className="text-slate-300" />
            </div>
            <h3 className="text-xl font-bold text-slate-800">No Years Selected</h3>
            <p className="text-slate-500 mt-2 max-w-xs mx-auto">
              Select years from the dropdown above to configure their structure.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {Object.entries(structures).map(([year, data]) => (
              <div
                key={year}
                className="bg-white rounded-2xl shadow-lg p-6 border border-slate-100 hover:border-blue-200 transition-all relative group"
              >
                {!AVAILABLE_YEARS.includes(year) && (
                  <button
                    onClick={() => toggleYear(year)}
                    className="absolute top-4 right-4 p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 size={18} />
                  </button>
                )}

                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-lg">
                    {year}
                  </div>
                  <h3 className="text-xl font-bold text-slate-800">Configuration</h3>
                </div>

                <div className="space-y-5">
                  <div>
                    <label className="block text-sm font-semibold text-slate-600 mb-2">
                      Number of Divisions
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={data.num_divisions}
                      onChange={(e) => handleChange(year, 'num_divisions', e.target.value)}
                      className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-400 outline-none transition-all font-medium"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-slate-600 mb-2">
                      Batches per Division
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={data.batches_per_division}
                      onChange={(e) => handleChange(year, 'batches_per_division', e.target.value)}
                      className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-400 outline-none transition-all font-medium"
                    />
                  </div>

                  <div className="pt-4 border-t border-slate-100 mt-2">
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-slate-500">Total Batches:</span>
                      <span className="font-bold text-blue-600 text-lg">
                        {getTotalBatches(year)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
