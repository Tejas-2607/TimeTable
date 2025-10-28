import { useState, useEffect } from 'react';
import { storage } from '../lib/storage';
import { Save } from 'lucide-react';

export default function ClassStructure() {
  const [structures, setStructures] = useState({
    SY: { num_divisions: 2, batches_per_division: 3 },
    TY: { num_divisions: 2, batches_per_division: 3 },
    'Final Year': { num_divisions: 1, batches_per_division: 3 },
  });

  useEffect(() => {
    loadStructures();
  }, []);

  const loadStructures = () => {
    const data = storage.classStructure.getAll();

    const structureMap = {};
    data.forEach((item) => {
      structureMap[item.year] = {
        num_divisions: item.num_divisions,
        batches_per_division: item.batches_per_division,
      };
    });
    if (Object.keys(structureMap).length > 0) {
      setStructures((prev) => ({ ...prev, ...structureMap }));
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

  const handleSave = () => {
    for (const [year, data] of Object.entries(structures)) {
      const structureData = {
        num_divisions: data.num_divisions,
        batches_per_division: data.batches_per_division,
        total_batches: data.num_divisions * data.batches_per_division,
      };

      storage.classStructure.upsert(year, structureData);
    }

    alert('Class structure saved successfully!');
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
