import { useState, useEffect } from 'react';
import { getClassTimetables } from '../services/classTimetableService';
import { getMasterTimetables } from '../services/masterTimetableService';
import {
  Clock, ArrowLeft, Calendar, ChevronRight, BookOpen,
  Users as UsersIcon, FlaskConical, Layers, Printer
} from 'lucide-react';


export default function ViewTimetables() {
  // views: 'landing' | 'classCards' | 'schedule' | 'practicalTable'
  const [view, setView] = useState('landing');
  const [timetables, setTimetables] = useState([]);
  const [practicalData, setPracticalData] = useState(null);
  const [selectedClass, setSelectedClass] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPracticalLoading, setIsPracticalLoading] = useState(true);
  const [error, setError] = useState(null);

  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
  const [timeSlots, setTimeSlots] = useState([]);
  const [practicalTimeSlots, setPracticalTimeSlots] = useState([]);

  // Fetch both datasets on mount
  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setIsLoading(true);
    setIsPracticalLoading(true);
    setError(null);

    // Fetch class timetables
    try {
      const res = await getClassTimetables();
      const data = res.timetables || res.data?.timetables || [];
      setTimetables(data);

      // Dynamically extract all unique time slots from the actual schedule data
      const parseTime = t => {
        const [hh, mm = '0'] = t.split(':');
        return parseInt(hh) * 60 + parseInt(mm);
      };
      const slotSet = new Set();
      data.forEach(tt => {
        const sched = tt.schedule || {};
        Object.values(sched).forEach(dayObj => {
          Object.keys(dayObj).forEach(t => slotSet.add(t));
        });
      });
      const sorted = Array.from(slotSet).sort((a, b) => parseTime(a) - parseTime(b));
      setTimeSlots(sorted);
    } catch (err) {
      console.error('Error loading class timetables:', err);
      setError('Failed to load class timetables.');
      setTimetables([]);
    } finally {
      setIsLoading(false);
    }

    // Fetch practical plan
    try {
      const res = await getMasterTimetables();
      const data = res.timetables || res.data?.timetables || [];
      setPracticalData({ timetables: data });

      // Extract practical time slots from master timetable data
      const parseTime = t => {
        const [hh, mm = '0'] = t.split(':');
        return parseInt(hh) * 60 + parseInt(mm);
      };
      const pSlotSet = new Set();
      data.forEach(tt => {
        const sched = tt.schedule || {};
        Object.values(sched).forEach(dayObj => {
          Object.keys(dayObj).forEach(t => pSlotSet.add(t));
        });
      });
      if (pSlotSet.size > 0) {
        const sorted = Array.from(pSlotSet).sort((a, b) => parseTime(a) - parseTime(b));
        setPracticalTimeSlots(sorted);
      }
    } catch (err) {
      console.warn('Could not load practical data:', err);
      setPracticalData(null);
    } finally {
      setIsPracticalLoading(false);
    }
  };

  // ---------- helpers ----------
  const latestDate = timetables.length
    ? new Date(Math.max(...timetables.map(t => new Date(t.generated_at)))).toLocaleString()
    : '';

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
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

  // ---------- session cell (class timetable) ----------
  const renderSessionCell = (sessions) => {
    if (!sessions || sessions.length === 0) {
      return (
        <div className="h-full min-h-[70px] bg-slate-50 border border-slate-200 rounded p-2 flex items-center justify-center text-xs text-slate-400">
          —
        </div>
      );
    }
    return (
      <div className="h-full min-h-[70px] flex flex-col gap-1">
        {sessions.map((session, idx) => (
          <div key={idx} className={`border rounded p-2 flex-1 ${session.lab ? 'bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200' : 'bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200'}`}>
            <div className={`font-semibold text-xs mb-1 ${session.lab ? 'text-emerald-900' : 'text-blue-900'}`}>{session.batch}</div>
            <div className="flex items-start gap-1 text-slate-700 mb-0.5">
              <BookOpen size={11} className="mt-0.5 flex-shrink-0" />
              <span className="font-medium text-xs">{session.subject} — {session.subject_full}</span>
            </div>
            <div className="flex items-start gap-1 text-slate-600 mb-0.5">
              <UsersIcon size={10} className="mt-0.5 flex-shrink-0" />
              <span className="text-xs leading-tight">{session.faculty}</span>
            </div>
            {session.lab && (
              <div className="flex items-start gap-1 text-slate-500">
                <FlaskConical size={10} className="mt-0.5 flex-shrink-0" />
                <span className="text-xs leading-tight">{session.lab}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  // ---------- practical plan session cell ----------
  const renderPracticalSessionCell = (sessions) => {
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
          <div key={idx} className="bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-200 rounded p-2 flex-1">
            <div className="font-semibold text-emerald-900 text-xs mb-1">
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

  // ---------- class schedule table ----------
  const renderScheduleTable = (classData) => {
    const schedule = classData.schedule || {};
    return (
      <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-slate-200">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gradient-to-r from-blue-600 to-cyan-600">
                <th className="border border-blue-700 px-4 py-3 text-white font-semibold text-left sticky left-0 bg-gradient-to-r from-blue-600 to-cyan-600 z-10">
                  Time / Day
                </th>
                {daysOfWeek.map(day => (
                  <th key={day} className="border border-blue-700 px-3 py-3 text-white font-semibold text-center">
                    {day}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {timeSlots.map((time, timeIdx) => {
                const isPracticalSlot = practicalTimeSlots.includes(time);
                return (
                  <tr key={time} className={timeIdx % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                    <td
                      className={`border border-slate-300 px-4 py-3 font-semibold sticky left-0 z-10 whitespace-nowrap ${isPracticalSlot ? 'text-blue-700' : 'text-slate-800'}`}
                      style={{ backgroundColor: timeIdx % 2 === 0 ? 'white' : '#f8fafc' }}
                    >
                      <div className="flex items-center gap-1.5">
                        <Clock size={14} className={isPracticalSlot ? 'text-blue-500' : 'text-slate-500'} />
                        <span>{time}</span>
                      </div>
                    </td>
                    {daysOfWeek.map(day => {
                      const daySchedule = schedule[day] || {};
                      const sessions = daySchedule[time] || [];
                      return (
                        <td key={`${time}-${day}`} className="border border-slate-300 p-2 min-w-[160px]">
                          {renderSessionCell(sessions)}
                        </td>
                      );
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

  // ---------- master practical table (lab-wise) ----------
  const renderMasterPracticalTable = () => {
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
              <tr className="bg-gradient-to-r from-emerald-600 to-teal-600">
                <th className="border border-emerald-700 px-4 py-3 text-white font-semibold text-left sticky left-0 bg-gradient-to-r from-emerald-600 to-teal-600 z-10">
                  Lab / Day
                </th>
                {daysOfWeek.map(day => (
                  <th key={day} className="border border-emerald-700 px-4 py-3 text-white font-semibold text-center" colSpan={practicalTimeSlots.length}>
                    {day}
                  </th>
                ))}
              </tr>
              <tr className="bg-emerald-500">
                <th className="border border-emerald-600 px-4 py-2 text-white text-sm font-medium sticky left-0 bg-emerald-500 z-10">
                  Time
                </th>
                {daysOfWeek.map(day => (
                  practicalTimeSlots.map(time => (
                    <th key={`${day}-${time}`} className="border border-emerald-600 px-2 py-2 text-white text-xs font-medium">
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
                      return practicalTimeSlots.map(time => {
                        const sessions = daySchedule[time] || [];
                        return (
                          <td key={`${labName}-${day}-${time}`} className="border border-slate-300 p-2 min-w-[140px]">
                            {renderPracticalSessionCell(sessions)}
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

  // ============================= VIEWS =============================

  // 1. Landing view — single card for latest timetable
  const renderLanding = () => (
    <div className="space-y-10">
      {/* Latest Timetable */}
      <section>
        <h3 className="text-xl font-bold text-slate-700 mb-4 flex items-center gap-2">
          <span className="inline-block w-1.5 h-6 bg-blue-500 rounded-full" />
          Latest Timetable
        </h3>
        <button
          onClick={() => setView('classCards')}
          className="group w-full max-w-md bg-white rounded-2xl shadow-md hover:shadow-xl border border-slate-200 hover:border-blue-300 transition-all duration-300 p-6 text-left cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-md shadow-blue-500/20">
                <Calendar size={28} className="text-white" />
              </div>
              <div>
                <p className="font-bold text-lg text-slate-800 group-hover:text-blue-700 transition-colors">
                  Class Timetables
                </p>
                <p className="text-sm text-slate-500 mt-0.5">
                  {timetables.length} class{timetables.length !== 1 ? 'es' : ''} generated
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  {latestDate}
                </p>
              </div>
            </div>
            <ChevronRight size={22} className="text-slate-400 group-hover:text-blue-500 transition-colors" />
          </div>
        </button>
      </section>

      {/* Previous Timetables */}
      <section>
        <h3 className="text-xl font-bold text-slate-700 mb-4 flex items-center gap-2">
          <span className="inline-block w-1.5 h-6 bg-slate-400 rounded-full" />
          Previous Timetables
        </h3>
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-10 text-center">
          <Layers size={40} className="mx-auto mb-3 text-slate-300" />
          <p className="text-slate-400 text-sm">No previous timetables available</p>
        </div>
      </section>
    </div>
  );

  // 2. Cards view — practical plan card + class cards
  const renderClassCards = () => (
    <div className="space-y-10">
      <button
        onClick={() => setView('landing')}
        className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
      >
        <ArrowLeft size={18} />
        Back to Timetables
      </button>

      <section>
        <h3 className="text-xl font-bold text-slate-700 mb-4 flex items-center gap-2">
          <span className="inline-block w-1.5 h-6 bg-blue-500 rounded-full" />
          Timetables
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {/* Practical Plan Card */}
          <button
            onClick={() => setView('practicalTable')}
            className="group bg-white rounded-2xl shadow-md hover:shadow-xl border border-slate-200 hover:border-blue-300 transition-all duration-300 p-5 text-left cursor-pointer"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-11 h-11 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-md shadow-blue-500/20">
                <FlaskConical size={20} className="text-white" />
              </div>
              <div>
                <p className="font-bold text-lg text-slate-800 group-hover:text-blue-700 transition-colors">
                  Master Practical Plan
                </p>
                <p className="text-xs text-slate-500">Lab-wise schedule</p>
              </div>
            </div>
            <div className="flex items-center justify-between border-t border-slate-100 pt-3">
              <p className="text-xs text-slate-400">View all lab schedules</p>
              <ChevronRight size={16} className="text-slate-400 group-hover:text-blue-500 transition-colors" />
            </div>
          </button>

          {/* Class-wise Cards */}
          {timetables.map((tt) => (
            <button
              key={tt._id}
              onClick={() => { setSelectedClass(tt); setView('schedule'); }}
              className="group bg-white rounded-2xl shadow-md hover:shadow-xl border border-slate-200 hover:border-blue-300 transition-all duration-300 p-5 text-left cursor-pointer"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-11 h-11 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-blue-500/20">
                  {tt.class_key.split('-')[0]}
                </div>
                <div>
                  <p className="font-bold text-lg text-slate-800 group-hover:text-blue-700 transition-colors">
                    {tt.class_key}
                  </p>
                  <p className="text-xs text-slate-500">Division {tt.division}</p>
                </div>
              </div>
              <div className="text-xs text-slate-400 space-y-1 border-t border-slate-100 pt-3">
                <p>Total Practicals: <span className="font-semibold text-slate-600">{tt.total_practicals}</span></p>
                <p>Generated: {formatDate(tt.generated_at)}</p>
              </div>
            </button>
          ))}
        </div>
      </section>
    </div>
  );

  // 3. Schedule table view
  const renderScheduleView = () => {
    if (!selectedClass) return null;
    return (
      <div className="print:px-0">
        <button
          onClick={() => { setSelectedClass(null); setView('classCards'); }}
          className="print:hidden flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 font-medium mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          Back to Timetables
        </button>

        <div className="mb-6 flex justify-between items-end">
          <div>
            <h3 className="text-2xl font-bold text-slate-800">
              {selectedClass.class_key}
              <span className="ml-2 text-base font-normal text-slate-500">— Division {selectedClass.division}</span>
            </h3>
            <p className="text-sm text-slate-500 mt-1">
              Generated on {formatDate(selectedClass.generated_at)} &nbsp;·&nbsp; {selectedClass.total_practicals} practicals assigned
            </p>
          </div>
          <button
            onClick={() => window.print()}
            className="print:hidden flex items-center gap-2 bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium shadow-sm hover:bg-slate-50 transition-colors"
          >
            <Printer size={18} />
            <span>Download PDF</span>
          </button>
        </div>

        {renderScheduleTable(selectedClass)}
      </div>
    );
  };

  // 4. Practical table full view
  const renderPracticalTableView = () => (
    <div className="print:px-0">
      <button
        onClick={() => setView('classCards')}
        className="print:hidden flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 font-medium mb-6 transition-colors"
      >
        <ArrowLeft size={18} />
        Back to Timetables
      </button>

      <div className="mb-6 flex justify-between items-end">
        <div>
          <h3 className="text-2xl font-bold text-slate-800">Master Practical Plan</h3>
          <p className="text-sm text-slate-500 mt-1">Lab-wise schedule across all years</p>
        </div>
        <button
          onClick={() => window.print()}
          className="print:hidden flex items-center gap-2 bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium shadow-sm hover:bg-slate-50 transition-colors"
        >
          <Printer size={18} />
          <span>Download PDF</span>
        </button>
      </div>

      {isPracticalLoading ? (
        <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden animate-pulse">
          <div className="h-12 bg-slate-300/50 border-b border-slate-300" />
          <div className="h-10 bg-slate-200/50 border-b border-slate-200" />
          {[...Array(4)].map((_, idx) => (
            <div key={idx} className="flex border-b border-slate-100">
              <div className="w-24 border-r border-slate-200 bg-slate-50" />
              <div className="flex-1 h-20 p-2 flex gap-4">
                {[...Array(4)].map((_, cellIdx) => (
                  <div key={cellIdx} className="flex-1 bg-slate-100 rounded border border-slate-200" />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : practicalData && practicalData.timetables && practicalData.timetables.length > 0 ? (
        renderMasterPracticalTable()
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
          <FlaskConical size={44} className="mx-auto mb-3 text-slate-300" />
          <p className="text-slate-400">No practical plan data available</p>
        </div>
      )}
    </div>
  );

  // ============================= ROOT =============================
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8 print:p-0 print:bg-white">
      <div className="max-w-[1800px] mx-auto">
        <div className="mb-8 print:hidden">
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">View Timetables</h1>
          <p className="text-slate-500 mt-2">Browse and inspect generated class timetables</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 text-red-700">
            <p className="font-semibold">Error Loading Timetables</p>
            <p className="text-sm mt-1">{error}</p>
            <button
              onClick={loadAllData}
              className="mt-3 px-4 py-2 bg-red-200 text-red-800 rounded hover:bg-red-300 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {isLoading ? (
          <div className="space-y-4 animate-pulse">
            <div className="h-28 bg-white rounded-2xl border border-slate-200" />
            <div className="h-28 bg-white rounded-2xl border border-slate-200" />
          </div>
        ) : timetables.length === 0 && !error ? (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <Calendar size={48} className="mx-auto mb-4 text-blue-600" />
            <h2 className="text-2xl font-semibold text-slate-800 mb-4">No Timetables Found</h2>
            <p className="text-slate-600 mb-6">
              No class timetables have been generated yet. Generate one from the "Generate Timetable" section.
            </p>
            <button
              onClick={loadAllData}
              className="px-8 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all shadow-lg hover:shadow-xl"
            >
              Refresh
            </button>
          </div>
        ) : (
          <>
            {view === 'landing' && renderLanding()}
            {view === 'classCards' && renderClassCards()}
            {view === 'schedule' && renderScheduleView()}
            {view === 'practicalTable' && renderPracticalTableView()}
          </>
        )}
      </div>
    </div>
  );
}
