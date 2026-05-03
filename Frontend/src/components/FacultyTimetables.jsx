import { useState, useEffect } from "react";
import { getClassTimetables } from "../services/classTimetableService";
import { getFaculties } from "../services/facultyService";
import { exportFacultyTimetable } from "../lib/excelExport";
import {
  Clock,
  ArrowLeft,
  Users,
  ChevronRight,
  BookOpen,
  FlaskConical,
  Briefcase,
  Printer,
  Search,
} from "lucide-react";

export default function FacultyTimetables({
  isSubComponent = false,
  onBackToDashboard = null,
}) {
  const [view, setView] = useState("landing"); // 'landing' | 'schedule'
  const [facultyData, setFacultyData] = useState({});
  const [facultyNames, setFacultyNames] = useState([]);
  const [facultyMap, setFacultyMap] = useState({});
  const [selectedFaculty, setSelectedFaculty] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const daysOfWeek = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
  const [allTimeSlots, setAllTimeSlots] = useState([]);

  useEffect(() => {
    loadFacultyData();
  }, []);

  const loadFacultyData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Fetch both timetables and faculty details
      const [res, facRes] = await Promise.all([
        getClassTimetables(),
        getFaculties().catch(() => []), // Fallback to avoid complete failure if this API is down
      ]);

      const classTimetables = res.timetables || res.data?.timetables || [];
      const extractedData = {};

      // Map short names to full titles/names
      const fMap = {};
      const facultiesList =
        (Array.isArray(facRes) && facRes) ||
        (Array.isArray(facRes?.data) && facRes.data) ||
        [];
      facultiesList.forEach((f) => {
        if (f.short_name) {
          fMap[f.short_name] = `${f.title} ${f.name}`;
        }
      });
      setFacultyMap(fMap);

      // Collect all unique time slots from the actual data
      const timeSlotsSet = new Set();

      classTimetables.forEach((ct) => {
        const sched = ct.schedule || {};
        Object.values(sched).forEach((dayObj) => {
          Object.keys(dayObj).forEach((t) => timeSlotsSet.add(t));
        });
      });

      const parseTime = (t) => {
        const [hh, mm = "0"] = t.split(".").join(":").split(":");
        return parseInt(hh) * 60 + parseInt(mm);
      };
      const combinedTimeSlots = Array.from(timeSlotsSet).sort(
        (a, b) => parseTime(a) - parseTime(b),
      );
      setAllTimeSlots(combinedTimeSlots);

      classTimetables.forEach((ct) => {
        const className = ct.class_key;
        const division = ct.division;
        const schedule = ct.schedule || {};

        Object.entries(schedule).forEach(([day, times]) => {
          Object.entries(times).forEach(([time, sessions]) => {
            sessions.forEach((session) => {
              if (!session.faculty) return;

              const faculties = session.faculty.split(",").map((f) => f.trim());

              faculties.forEach((fac) => {
                if (!fac) return;
                if (!extractedData[fac]) extractedData[fac] = {};
                if (!extractedData[fac][day]) extractedData[fac][day] = {};
                if (!extractedData[fac][day][time])
                  extractedData[fac][day][time] = [];

                extractedData[fac][day][time].push({
                  class_key: className,
                  division: division,
                  subject: session.subject,
                  batch: session.batch,
                  lab: session.lab,
                  isPractical: !!session.lab,
                });
              });
            });
          });
        });
      });

      setFacultyData(extractedData);
      setFacultyNames(Object.keys(extractedData).sort());
    } catch (err) {
      console.error("Error extracting faculty timetables:", err);
      setError("Failed to load timetables for faculty.");
    } finally {
      setIsLoading(false);
    }
  };

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
          <div
            key={idx}
            className={`border rounded p-2 flex-1 ${session.isPractical ? "bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200" : "bg-gradient-to-br from-indigo-50 to-purple-50 border-indigo-200"}`}
          >
            <div
              className={`font-semibold text-xs mb-1 ${session.isPractical ? "text-emerald-900" : "text-indigo-900"}`}
            >
              {session.class_key} (Div {session.division})
              {session.batch && session.batch !== "All"
                ? ` - ${session.batch}`
                : ""}
            </div>
            <div className="flex items-start gap-1 text-slate-700 mb-0.5">
              <BookOpen size={11} className="mt-0.5 flex-shrink-0" />
              <span className="font-medium text-xs">{session.subject}</span>
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

  const renderScheduleTable = (facName) => {
    const schedule = facultyData[facName] || {};
    return (
      <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-slate-200">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gradient-to-r from-indigo-600 to-purple-600">
                <th className="border border-indigo-700 px-4 py-3 text-white font-semibold text-left sticky left-0 bg-gradient-to-r from-indigo-600 to-purple-600 z-10">
                  Time / Day
                </th>
                {daysOfWeek.map((day) => (
                  <th
                    key={day}
                    className="border border-indigo-700 px-3 py-3 text-white font-semibold text-center"
                  >
                    {day}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {allTimeSlots.map((time, timeIdx) => {
                return (
                  <tr
                    key={time}
                    className={timeIdx % 2 === 0 ? "bg-white" : "bg-slate-50"}
                  >
                    <td
                      className="border border-slate-300 px-4 py-3 font-semibold text-slate-800 sticky left-0 z-10 whitespace-nowrap"
                      style={{
                        backgroundColor:
                          timeIdx % 2 === 0 ? "white" : "#f8fafc",
                      }}
                    >
                      <div className="flex items-center gap-1.5">
                        <Clock size={14} className="text-slate-500" />
                        <span>{time}</span>
                      </div>
                    </td>
                    {daysOfWeek.map((day) => {
                      const daySchedule = schedule[day] || {};
                      const sessions = daySchedule[time] || [];
                      return (
                        <td
                          key={`${time}-${day}`}
                          className="border border-slate-300 p-2 min-w-[160px]"
                        >
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

  const filteredFacultyNames = facultyNames.filter((fac) => {
    const searchLower = searchQuery.toLowerCase();
    const matchesShort = fac.toLowerCase().includes(searchLower);
    const fullName = facultyMap[fac] || "";
    const matchesFull = fullName.toLowerCase().includes(searchLower);
    return matchesShort || matchesFull;
  });

  const renderLanding = () => (
    <div className="space-y-6">
      {isSubComponent && onBackToDashboard && (
        <button
          onClick={onBackToDashboard}
          className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 font-medium mb-2 transition-colors"
        >
          <ArrowLeft size={18} />
          Back to Dashboard
        </button>
      )}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <h3 className="text-xl font-bold text-slate-700 flex items-center gap-2">
          <span className="inline-block w-1.5 h-6 bg-indigo-500 rounded-full" />
          Faculty Directory
        </h3>

        <div className="relative w-full sm:w-72">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            size={18}
          />
          <input
            type="text"
            placeholder="Search faculty..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-4 focus:ring-indigo-100 focus:border-indigo-400 outline-none transition-all shadow-sm"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        {filteredFacultyNames.length === 0 ? (
          <div className="col-span-full py-12 text-center text-slate-500 bg-white rounded-2xl border border-slate-200 border-dashed">
            No faculty found matching "{searchQuery}"
          </div>
        ) : (
          filteredFacultyNames.map((fac) => {
            let practicalCount = 0;
            let theoryCount = 0;
            Object.values(facultyData[fac]).forEach((dayObj) => {
              Object.values(dayObj).forEach((timeArr) => {
                timeArr.forEach((session) => {
                  if (session.isPractical) practicalCount++;
                  else theoryCount++;
                });
              });
            });

            return (
              <button
                key={fac}
                onClick={() => {
                  setSelectedFaculty(fac);
                  setView("schedule");
                }}
                className="group bg-white rounded-2xl shadow-md hover:shadow-xl border border-slate-200 hover:border-indigo-300 transition-all duration-300 p-5 text-left cursor-pointer"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-11 h-11 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
                    <Briefcase size={20} />
                  </div>
                  <div>
                    <p className="font-bold text-lg text-slate-800 group-hover:text-indigo-700 transition-colors">
                      {fac}
                    </p>
                    <p className="text-xs text-slate-500 line-clamp-1">
                      {facultyMap[fac] || "Faculty Member"}
                    </p>
                  </div>
                </div>
                <div className="text-xs text-slate-500 space-y-1 border-t border-slate-100 pt-3">
                  <p>
                    Theory Sessions:{" "}
                    <span className="font-semibold text-slate-700">
                      {theoryCount}
                    </span>
                  </p>
                  <p>
                    Practical Sessions:{" "}
                    <span className="font-semibold text-slate-700">
                      {practicalCount}
                    </span>
                  </p>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );

  const renderScheduleView = () => {
    if (!selectedFaculty) return null;
    return (
      <div className="print:px-0">
        <button
          onClick={() => {
            setSelectedFaculty(null);
            setView("landing");
          }}
          className="print:hidden flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-800 font-medium mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          Back to Faculty Directory
        </button>

        <div className="mb-6 flex justify-between items-end">
          <div>
            <h3 className="text-2xl font-bold text-slate-800">
              {facultyMap[selectedFaculty]
                ? `${facultyMap[selectedFaculty]} (${selectedFaculty})`
                : selectedFaculty}
              <span className="ml-2 text-base font-normal text-slate-500">
                — Personal Timetable
              </span>
            </h3>
            <p className="text-sm text-slate-500 mt-1">
              Consolidated view of all assigned theory and practical sessions
            </p>
          </div>
          <button
            onClick={() =>
              exportFacultyTimetable(
                selectedFaculty,
                facultyData[selectedFaculty],
                allTimeSlots,
              )
            } //
            className="print:hidden flex items-center gap-2 bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium shadow-sm hover:bg-slate-50 transition-colors"
          >
            <Briefcase size={18} />
            <span>Download CSV</span>
          </button>
        </div>

        {renderScheduleTable(selectedFaculty)}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-slate-200">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse" />
        {!isSubComponent && (
          <div className="mb-8 print:hidden">
            <h1 className="text-3xl font-bold text-slate-800 tracking-tight">
              Faculty Timetables
            </h1>
            <p className="text-slate-500 mt-2">
              Individual, consolidated schedules for all faculty members
            </p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 text-red-700">
            <p className="font-semibold">Error Loading Timetables</p>
            <p className="text-sm mt-1">{error}</p>
            <button
              onClick={loadFacultyData}
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
        ) : facultyNames.length === 0 && !error ? (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <Users size={48} className="mx-auto mb-4 text-slate-400" />
            <h2 className="text-2xl font-semibold text-slate-800 mb-4">
              No Faculty Data Found
            </h2>
            <p className="text-slate-600 mb-6">
              Timetables haven't been generated yet or no faculty assignments
              were found.
            </p>
            <button
              onClick={loadFacultyData}
              className="px-8 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all shadow-lg hover:shadow-xl"
            >
              Refresh
            </button>
          </div>
        ) : (
          <>
            {view === "landing" && renderLanding()}
            {view === "schedule" && renderScheduleView()}
          </>
        )}
      </div>
    </div>
  );
}
