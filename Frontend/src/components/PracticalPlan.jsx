import { useState, useEffect } from 'react';
import { Clock, Users as UsersIcon, BookOpen } from 'lucide-react';
import { getMasterTimetables } from '../services/masterTimetableService';

export default function PracticalPlan() {
  const [practicalData, setPracticalData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
  const timeSlots = ['11:15', '14:15', '16:20'];

  // Load timetables on component mount
  useEffect(() => {
    loadTimetables();
  }, []);

  const loadTimetables = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getMasterTimetables();
      console.log('Timetables response:', response);
      
      const timetablesData = response.timetables || response.data?.timetables || [];
      setPracticalData({ timetables: timetablesData });
    } catch (err) {
      console.error('Error loading timetables:', err);
      setError('Failed to load practical plan. Please try again.');
      setPracticalData(null);
    } finally {
      setIsLoading(false);
    }
  };

  const getAllLabs = () => {
    if (!practicalData || !practicalData.timetables) return {};

    const allLabs = {};

    practicalData.timetables.forEach(timetable => {
      if (timetable.lab_name && timetable.schedule) {
        if (!allLabs[timetable.lab_name]) {
          allLabs[timetable.lab_name] = timetable.schedule;
        }
      }
    });

    return allLabs;
  };

  const renderSessionCell = (sessions) => {
    if (!sessions || sessions.length === 0) {
      return (
        <div className="h-full min-h-[80px] bg-slate-50 border border-slate-200 rounded p-2 flex items-center justify-center text-xs text-slate-400">
          -
        </div>
      );
    }

    return (
      <div className="h-full min-h-[80px] flex flex-col gap-1">
        {sessions.map((session, idx) => (
          <div key={idx} className="bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-200 rounded p-2 flex-1">
            <div className="font-semibold text-blue-900 text-xs mb-1">
              {session.class} {session.division}-B{session.batch}
            </div>
            <div className="flex items-start gap-1 text-slate-700 mb-1">
              <BookOpen size={11} className="mt-0.5 flex-shrink-0" />
              <span className="font-medium text-xs">{session.subject}</span>
            </div>
            <div className="flex items-start gap-1 text-slate-600">
              <UsersIcon size={10} className="mt-0.5 flex-shrink-0" />
              <span className="text-xs leading-tight">{session.faculty}</span>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderMasterTimetable = () => {
    const allLabs = getAllLabs();
    const labNames = Object.keys(allLabs);

    if (labNames.length === 0) {
      return (
        <div className="text-center py-8 text-slate-500">
          No practical data available
        </div>
      );
    }

    return (
      <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-slate-200">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gradient-to-r from-blue-600 to-cyan-600">
                <th className="border border-blue-700 px-4 py-3 text-white font-semibold text-left sticky left-0 bg-gradient-to-r from-blue-600 to-cyan-600 z-10">
                  Lab / Day
                </th>
                {daysOfWeek.map(day => (
                  <th key={day} className="border border-blue-700 px-4 py-3 text-white font-semibold text-center" colSpan={3}>
                    {day}
                  </th>
                ))}
              </tr>
              <tr className="bg-blue-500">
                <th className="border border-blue-600 px-4 py-2 text-white text-sm font-medium sticky left-0 bg-blue-500 z-10">
                  Session
                </th>
                {daysOfWeek.map(day => (
                  timeSlots.map((time, idx) => (
                    <th key={`${day}-${time}`} className="border border-blue-600 px-2 py-2 text-white text-xs font-medium">
                      <div className="flex items-center justify-center gap-1">
                        <Clock size={12} />
                        <span>{time}</span>
                      </div>
                    </th>
                  ))
                ))}
              </tr>
            </thead>
            <tbody>
              {labNames.map((labName, labIdx) => {
                const labSchedule = allLabs[labName];
                return (
                  <tr key={labName} className={labIdx % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                    <td className="border border-slate-300 px-4 py-3 font-semibold text-slate-800 sticky left-0 z-10" style={{ backgroundColor: labIdx % 2 === 0 ? 'white' : '#f8fafc' }}>
                      {labName}
                    </td>
                    {daysOfWeek.map(day => {
                      const daySchedule = labSchedule[day] || {};
                      return timeSlots.map(time => {
                        const sessions = daySchedule[time] || [];
                        return (
                          <td key={`${labName}-${day}-${time}`} className="border border-slate-300 p-2">
                            {renderSessionCell(sessions)}
                          </td>
                        );
                      });
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8">
      <div className="max-w-[1800px] mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-800 mb-2">Master Practical Timetable</h1>
          <p className="text-slate-600">Comprehensive view of all lab schedules across all years</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 text-red-700">
            <p className="font-semibold">Error Loading Timetable</p>
            <p className="text-sm mt-1">{error}</p>
            <button
              onClick={loadTimetables}
              className="mt-3 px-4 py-2 bg-red-200 text-red-800 rounded hover:bg-red-300 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {isLoading ? (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <div className="max-w-md mx-auto">
              <BookOpen size={48} className="mx-auto mb-4 text-blue-600 animate-pulse" />
              <h2 className="text-2xl font-semibold text-slate-800 mb-4">Loading Practical Plan</h2>
              <p className="text-slate-600">Fetching timetable schedules...</p>
            </div>
          </div>
        ) : !practicalData || !practicalData.timetables || practicalData.timetables.length === 0 ? (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <div className="max-w-md mx-auto">
              <BookOpen size={48} className="mx-auto mb-4 text-blue-600" />
              <h2 className="text-2xl font-semibold text-slate-800 mb-4">No Practical Plan Generated</h2>
              <p className="text-slate-600 mb-6">The master practical timetable has not been generated yet. Please generate it from the "Generate Timetable" section.</p>
              <button
                onClick={loadTimetables}
                className="px-8 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all shadow-lg hover:shadow-xl"
              >
                Refresh
              </button>
            </div>
          </div>
        ) : (
          renderMasterTimetable()
        )}
      </div>
    </div>
  );
}