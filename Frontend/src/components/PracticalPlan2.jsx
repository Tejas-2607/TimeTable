import { useState, useEffect } from 'react';
import { Clock, Users as UsersIcon, BookOpen } from 'lucide-react';
import { getMasterTimetables } from '../services/timetableService';

export default function PracticalPlan() {
  const [timetables, setTimetables] = useState([]);
  const [selectedYear, setSelectedYear] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
  const timeSlots = ['11:15', '14:15', '16:20'];

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
      setTimetables(timetablesData);

      // Set selected year to first available year
      if (timetablesData.length > 0) {
        const firstYear = timetablesData[0].year;
        setSelectedYear(firstYear);
      }
    } catch (err) {
      console.error('Error loading timetables:', err);
      setError('Failed to load practical plan. Please try again.');
      setTimetables([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Get unique years from timetables
  const getAvailableYears = () => {
    const yearsSet = new Set(timetables.map(t => t.year));
    return Array.from(yearsSet).sort();
  };

  // Get timetables for selected year
  const getYearTimetables = () => {
    return timetables.filter(t => t.year === selectedYear);
  };

  const renderSessionCard = (session) => {
    if (!session) {
      return (
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-center text-slate-400">
          No Session
        </div>
      );
    }

    return (
      <div className="bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-200 rounded-lg p-4">
        <div className="font-semibold text-blue-900 mb-2">
          {session.class} {session.division} - Batch {session.batch}
        </div>
        <div className="flex items-center gap-2 text-slate-700 mb-2">
          <BookOpen size={14} />
          <span className="font-medium">{session.subject}</span>
        </div>
        <div className="text-slate-600 text-sm mb-2">
          {session.subject_full}
        </div>
        <div className="flex items-center gap-2 text-slate-600 text-sm">
          <UsersIcon size={13} />
          <span>{session.faculty}</span>
        </div>
      </div>
    );
  };

  const renderLabCard = (labName, labSchedule) => {
    return (
      <div key={labName} className="bg-white rounded-xl shadow-md overflow-hidden border border-slate-200 hover:shadow-lg transition-shadow">
        <div className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-6 py-4">
          <h3 className="text-lg font-semibold">{labName}</h3>
        </div>

        <div className="p-6">
          <div className="space-y-6">
            {daysOfWeek.map(day => {
              const daySchedule = labSchedule[day] || {};

              const sessions = timeSlots.map(time => {
                const timeSlotSessions = daySchedule[time];
                return timeSlotSessions && timeSlotSessions.length > 0 ? timeSlotSessions[0] : null;
              });

              return (
                <div key={day} className="border-b border-slate-200 last:border-b-0 pb-6 last:pb-0">
                  <h4 className="text-lg font-semibold text-slate-800 mb-4">{day}</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {sessions.map((session, idx) => (
                      <div key={idx}>
                        <div className="flex items-center gap-2 text-sm font-medium text-slate-600 mb-2">
                          <Clock size={14} />
                          <span>{idx === 0 ? '1st' : idx === 1 ? '2nd' : '3rd'} Session ({timeSlots[idx]})</span>
                        </div>
                        {renderSessionCard(session)}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  const renderYearSection = () => {
    const yearTimetables = getYearTimetables();

    if (yearTimetables.length === 0) {
      return (
        <div className="text-center py-8 text-slate-500">
          No practical data available for {selectedYear}
        </div>
      );
    }

    // Group labs by year - if multiple timetables exist for same year, merge their labs
    const allLabs = {};
    yearTimetables.forEach(timetable => {
      if (timetable.schedule && timetable.schedule.labs) {
        Object.assign(allLabs, timetable.schedule.labs);
      }
    });

    if (Object.keys(allLabs).length === 0) {
      return (
        <div className="text-center py-8 text-slate-500">
          No practical data available for {selectedYear}
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {Object.keys(allLabs).map(labName => renderLabCard(labName, allLabs[labName]))}
      </div>
    );
  };

  const availableYears = getAvailableYears();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8">
      <div className="max-w-[1600px] mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-800 mb-2">Practical Plan</h1>
          <p className="text-slate-600">View the current year's practical schedule for all classes</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 text-red-700">
            {error}
          </div>
        )}

        {!timetables || timetables.length === 0 ? (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <div className="max-w-md mx-auto">
              <BookOpen size={48} className="mx-auto mb-4 text-blue-600" />
              <h2 className="text-2xl font-semibold text-slate-800 mb-4">
                {isLoading ? 'Loading Practical Plan...' : 'Load Practical Plan Data'}
              </h2>
              <p className="text-slate-600 mb-6">
                {isLoading ? 'Fetching schedules...' : 'Click the button below to fetch and display the practical schedules'}
              </p>
              {!isLoading && (
                <button
                  onClick={loadTimetables}
                  disabled={isLoading}
                  className="px-8 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Load Practical Plan
                </button>
              )}
            </div>
          </div>
        ) : (
          <>
            <div className="flex gap-4 mb-6 flex-wrap">
              {availableYears.map(year => (
                <button
                  key={year}
                  onClick={() => setSelectedYear(year)}
                  className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                    selectedYear === year
                      ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg'
                      : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
                  }`}
                >
                  {year}
                </button>
              ))}
            </div>

            <div className="space-y-6">
              {renderYearSection()}
            </div>
          </>
        )}
      </div>
    </div>
  );
}