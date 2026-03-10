import { useState, useEffect } from 'react';
import { Save } from 'lucide-react';
import { saveClassStructure, getClassStructure } from '../services/classStructureService';

export default function ClassStructure() {
  const [structures, setStructures] = useState({
    SY: { num_divisions: 2, batches_per_division: 3 },
    TY: { num_divisions: 2, batches_per_division: 3 },
    'Final Year': { num_divisions: 1, batches_per_division: 3 },
  });
  const [loading, setLoading] = useState(true);

  // ✅ Load from backend
  useEffect(() => {
    loadStructures();
  }, []);

  const loadStructures = async () => {
    try {
      setLoading(true);
      const data = await getClassStructure();
      console.log('Loaded class structure:', data);
      if (data && Object.keys(data).length > 0) {
        const { _id, ...structureData } = data; // remove MongoDB ID
        setStructures(structureData);
      }

    } catch (error) {
      console.error('Failed to load class structure:', error);
    } finally {
      setLoading(false);
    }
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

  const getTotalBatches = (year) => {
    const { num_divisions, batches_per_division } = structures[year];
    return num_divisions * batches_per_division;
  };

  // ✅ Save to backend
  const handleSave = async () => {
    try {
      const payload = { ...structures };
      await saveClassStructure(payload);
      alert('Class structure saved successfully!');
    } catch (error) {
      alert('Failed to save class structure.');
      console.error(error);
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">Class Structure</h2>
        <p className="text-slate-500 mt-2">
          Configure divisions and batches for each year
        </p>
      </div>

      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {loading ? (
            // Skeleton Loader Cards
            [...Array(3)].map((_, idx) => (
              <div key={`skeleton-${idx}`} className="bg-white rounded-xl shadow-md p-6 border border-slate-200 animate-pulse">
                <div className="h-6 bg-slate-200 rounded w-1/2 mb-6"></div>
                <div className="space-y-4">
                  <div>
                    <div className="h-4 bg-slate-200 rounded w-1/3 mb-2"></div>
                    <div className="h-10 bg-slate-200 rounded-xl w-full"></div>
                  </div>
                  <div>
                    <div className="h-4 bg-slate-200 rounded w-1/4 mb-2"></div>
                    <div className="h-10 bg-slate-200 rounded-xl w-full"></div>
                  </div>
                  <div className="pt-4 mt-6 border-t border-slate-200">
                    <div className="h-4 bg-slate-200 rounded w-1/3"></div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            Object.entries(structures)
              .sort(([yearA], [yearB]) => {
                const order = { 'Final Year': 1, 'SY': 2, 'TY': 3 };
                return (order[yearA] || 99) - (order[yearB] || 99);
              })
              .map(([year, data]) => (
                <div
                  key={year}
                  className="bg-white rounded-xl shadow-md p-6 border border-slate-200"
                >
                  <h3 className="text-xl font-bold text-blue-600 mb-6">
                    {year === 'SY' ? 'Second year' :
                      year === 'TY' ? 'Third year' :
                        year === 'Final Year' ? 'Final year' :
                          year}
                  </h3>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">
                        Number of Divisions
                      </label>
                      <input
                        type="number"
                        min="1"
                        value={data.num_divisions}
                        onChange={(e) =>
                          handleChange(year, 'num_divisions', e.target.value)
                        }
                        className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-4 focus:ring-slate-100 focus:border-slate-400 outline-none transition-all shadow-sm"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">
                        Batches per Division
                      </label>
                      <input
                        type="number"
                        min="1"
                        value={data.batches_per_division}
                        onChange={(e) =>
                          handleChange(year, 'batches_per_division', e.target.value)
                        }
                        className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-4 focus:ring-slate-100 focus:border-slate-400 outline-none transition-all shadow-sm"
                      />
                    </div>

                    <div className="pt-4 border-t border-slate-200">
                      <p className="text-sm text-slate-600">
                        Total Batches:{' '}
                        <span className="font-bold text-emerald-600 text-lg">
                          {getTotalBatches(year)}
                        </span>
                      </p>
                    </div>
                  </div>
                </div>
              ))
          )}
        </div>

        <div className="flex justify-end">
          <button
            onClick={handleSave}
            className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-8 py-3 rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all shadow-lg active:scale-95 text-lg font-semibold"
          >
            <Save size={20} />
            Save Class Structure
          </button>
        </div>
      </div>
    </div>
  );
}
