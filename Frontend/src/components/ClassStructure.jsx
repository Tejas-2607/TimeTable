import { useState, useEffect } from 'react';
import { Save } from 'lucide-react';
import { saveClassStructure, getClassStructure } from '../services/classStructureService';

export default function ClassStructure() {
  const [structures, setStructures] = useState({
    SY: { num_divisions: 2, batches_per_division: 3 },
    TY: { num_divisions: 2, batches_per_division: 3 },
    'Final Year': { num_divisions: 1, batches_per_division: 3 },
  });

  // ✅ Load from backend
  useEffect(() => {
    loadStructures();
  }, []);

  const loadStructures = async () => {
    try {
      const data = await getClassStructure();
      console.log('Loaded class structure:', data);
      if (data && Object.keys(data).length > 0) {
        const { _id, ...structureData } = data; // remove MongoDB ID
        setStructures(structureData);
      }

    } catch (error) {
      console.error('Failed to load class structure:', error);
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
        <h2 className="text-3xl font-bold text-slate-800">Class Structure</h2>
        <p className="text-slate-600 mt-1">
          Configure divisions and batches for each year
        </p>
      </div>

      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {Object.entries(structures).map(([year, data]) => (
            <div
              key={year}
              className="bg-white rounded-xl shadow-lg p-6 border-2 border-slate-200"
            >
              <h3 className="text-xl font-bold text-blue-600 mb-6">
                {year === 'SY' && 'SY (Second Year)'}
                {year === 'TY' && 'TY (Third Year)'}
                {year === 'Final Year' && 'Final Year'}
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
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div className="pt-4 border-t border-slate-200">
                  <p className="text-sm text-slate-600">
                    Total Batches:{' '}
                    <span className="font-bold text-green-600 text-lg">
                      {getTotalBatches(year)}
                    </span>
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-end">
          <button
            onClick={handleSave}
            className="flex items-center gap-2 bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors shadow-lg text-lg font-semibold"
          >
            <Save size={20} />
            Save Class Structure
          </button>
        </div>
      </div>
    </div>
  );
}
