import { useState, useEffect } from 'react';
import { storage } from '../lib/storage';
import { Search } from 'lucide-react';

export default function ViewTimetables() {
  const [academicYear, setAcademicYear] = useState('');
  const [semester, setSemester] = useState('odd');
  const [timetables, setTimetables] = useState([]);
  const [showResults, setShowResults] = useState(false);

  const handleSearch = () => {
    if (!academicYear) {
      alert('Please enter academic year');
      return;
    }

    const data = storage.timetables.getByYearAndSemester(academicYear, semester);
    setTimetables(data);
    setShowResults(true);
  };

  const groupByYear = () => {
    const grouped = { SY: [], TY: [], 'Final Year': [] };
    timetables.forEach((tt) => {
      if (grouped[tt.year]) {
        grouped[tt.year].push(tt);
      }
    });
    return grouped;
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-800">View Timetables</h2>
        <p className="text-slate-600 mt-1">
          Search and view generated timetables
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6 mb-8 border border-slate-200">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Academic Year
            </label>
            <input
              type="text"
              value={academicYear}
              onChange={(e) => setAcademicYear(e.target.value)}
              placeholder="e.g., 2024-2025"
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Semester
            </label>
            <select
              value={semester}
              onChange={(e) => setSemester(e.target.value)}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="odd">Odd Semester</option>
              <option value="even">Even Semester</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={handleSearch}
              className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Search size={18} />
              Search Timetables
            </button>
          </div>
        </div>
      </div>

      {showResults && (
        <div className="space-y-8">
          {Object.entries(groupByYear()).map(([year, tts]) => (
            <div key={year}>
              {tts.length > 0 && (
                <div>
                  <h3 className="text-2xl font-bold text-slate-800 mb-4">
                    {year}
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {tts.map((tt) => (
                      <div
                        key={tt.id}
                        className="bg-white rounded-lg shadow p-6 border border-slate-200 hover:shadow-lg transition-shadow"
                      >
                        <h4 className="font-semibold text-lg text-slate-800 mb-2">
                          Division {tt.division}
                        </h4>
                        <div className="text-sm text-slate-600 space-y-1">
                          <p>Academic Year: {tt.academic_year}</p>
                          <p>
                            Semester:{' '}
                            {tt.semester.charAt(0).toUpperCase() +
                              tt.semester.slice(1)}
                          </p>
                          <p className="text-xs text-slate-500 mt-2">
                            Created: {new Date(tt.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <button className="mt-4 w-full bg-blue-50 text-blue-600 py-2 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium">
                          View Details
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
          {timetables.length === 0 && (
            <div className="bg-white rounded-xl shadow-lg p-12 text-center border border-slate-200">
              <p className="text-slate-500 text-lg">
                No timetables found for the selected criteria
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
