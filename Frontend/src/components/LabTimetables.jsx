import { useState, useEffect } from "react";
import { getClassTimetables } from "../services/classTimetableService";
import { getAllLabs } from "../services/labsService";
import { exportLabTimetable } from "../lib/excelExport";
import {
  Clock,
  ArrowLeft,
  FlaskConical,
  ChevronRight,
  BookOpen,
  Users,
  Printer,
  Search,
} from "lucide-react";
import { getSessionTimes } from "../services/labSettingsService";

export default function LabTimetables({
  isSubComponent = false,
  onBackToDashboard = null,
}) {
  const [view, setView] = useState("landing"); // 'landing' | 'schedule'
  const [labData, setLabData] = useState({}); // { labShortName: { day: { time: [sessions] } } }
  const [labNames, setLabNames] = useState([]); // list of lab short_names found in timetables
  const [labMap, setLabMap] = useState({}); // { short_name -> full name }
  const [selectedLab, setSelectedLab] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const daysOfWeek = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
  const [allTimeSlots, setAllTimeSlots] = useState([]);

  useEffect(() => {
    loadLabData();
  }, []);

  const loadLabData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [res, labsRes] = await Promise.all([
        getClassTimetables(),
        getAllLabs().catch(() => []),
      ]);

      const classTimetables = res.timetables || res.data?.timetables || [];

      // Build lab short_name → full name map
      const lMap = {};
      const labsList = Array.isArray(labsRes)
        ? labsRes
        : labsRes?.labs || labsRes?.data || [];
      labsList.forEach((l) => {
        if (l.short_name) {
          lMap[l.short_name] = l.name;
        }
      });
      setLabMap(lMap);

      // Dynamically collect all unique time slots from actual data
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

      const extractedData = {};

      classTimetables.forEach((ct) => {
        const className = ct.class_key;
        const division = ct.division;
        const schedule = ct.schedule || {};

        Object.entries(schedule).forEach(([day, times]) => {
          Object.entries(times).forEach(([time, sessions]) => {
            sessions.forEach((session) => {
              if (!session.lab) return; // only sessions assigned to a lab
              const labKey = session.lab.trim();
              if (!labKey) return;

              if (!extractedData[labKey]) extractedData[labKey] = {};
              if (!extractedData[labKey][day]) extractedData[labKey][day] = {};
              if (!extractedData[labKey][day][time])
                extractedData[labKey][day][time] = [];

              extractedData[labKey][day][time].push({
                class_key: className,
                division: division,
                subject: session.subject,
                batch: session.batch,
                faculty: session.faculty,
              });
            });
          });
        });
      });

      setLabData(extractedData);
      setLabNames(Object.keys(extractedData).sort());
    } catch (err) {
      console.error("Error extracting lab timetables:", err);
      setError("Failed to load timetables for labs.");
    } finally {
      setIsLoading(false);
    }
  };

  // ─── Cell Renderer ───────────────────────────────────────────────────────────
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
            className="border rounded p-2 flex-1 bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200"
          >
            <div className="font-semibold text-xs mb-1 text-emerald-900">
              {session.class_key} (Div {session.division})
              {session.batch && session.batch !== "All"
                ? ` — ${session.batch}`
                : ""}
            </div>
            <div className="flex items-start gap-1 text-slate-700 mb-0.5">
              <BookOpen size={11} className="mt-0.5 flex-shrink-0" />
              <span className="font-medium text-xs">{session.subject}</span>
            </div>
            {session.faculty && (
              <div className="flex items-start gap-1 text-slate-500">
                <Users size={10} className="mt-0.5 flex-shrink-0" />
                <span className="text-xs leading-tight">{session.faculty}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  // ─── Schedule Table ───────────────────────────────────────────────────────────
  const renderScheduleTable = (labKey) => {
    const schedule = labData[labKey] || {};
    return (
      <div className="bg-white rounded-xl shadow-lg border border-slate-200">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gradient-to-r from-emerald-600 to-teal-600">
                <th className="border border-emerald-700 px-4 py-3 text-white font-semibold text-left sticky left-0 bg-gradient-to-r from-emerald-600 to-teal-600 z-10">
                  Time / Day
                </th>
                {daysOfWeek.map((day) => (
                  <th
                    key={day}
                    className="border border-emerald-700 px-3 py-3 text-white font-semibold text-center"
                  >
                    {day}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {allTimeSlots.map((time, timeIdx) => (
                <tr
                  key={time}
                  className={timeIdx % 2 === 0 ? "bg-white" : "bg-slate-50"}
                >
                  <td
                    className="border border-slate-300 px-4 py-3 font-semibold text-slate-800 sticky left-0 z-10 whitespace-nowrap"
                    style={{
                      backgroundColor: timeIdx % 2 === 0 ? "white" : "#f8fafc",
                    }}
                  >
                    <div className="flex items-center gap-1.5">
                      <Clock size={14} className="text-slate-500" />
                      <span>{time}</span>
                    </div>
                  </td>
                  {daysOfWeek.map((day) => {
                    const sessions = (schedule[day] || {})[time] || [];
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
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  // ─── Filtered Labs ────────────────────────────────────────────────────────────
  const filteredLabNames = labNames.filter((lab) => {
    const q = searchQuery.toLowerCase();
    const fullName = labMap[lab] || "";
    return lab.toLowerCase().includes(q) || fullName.toLowerCase().includes(q);
  });

  // ─── Landing Page ─────────────────────────────────────────────────────────────
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
          <span className="inline-block w-1.5 h-6 bg-emerald-500 rounded-full" />
          Lab Directory
        </h3>

        <div className="relative w-full sm:w-72">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            size={18}
          />
          <input
            type="text"
            placeholder="Search lab..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-4 focus:ring-emerald-100 focus:border-emerald-400 outline-none transition-all shadow-sm"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        {filteredLabNames.length === 0 ? (
          <div className="col-span-full py-12 text-center text-slate-500 bg-white rounded-2xl border border-slate-200 border-dashed">
            No labs found matching &quot;{searchQuery}&quot;
          </div>
        ) : (
          filteredLabNames.map((lab) => {
            let sessionCount = 0;
            Object.values(labData[lab]).forEach((dayObj) => {
              Object.values(dayObj).forEach((arr) => {
                sessionCount += arr.length;
              });
            });

            return (
              <button
                key={lab}
                onClick={() => {
                  setSelectedLab(lab);
                  setView("schedule");
                }}
                className="group bg-white rounded-2xl shadow-md hover:shadow-xl border border-slate-200 hover:border-emerald-300 transition-all duration-300 p-5 text-left cursor-pointer"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-11 h-11 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-white shadow-md shadow-emerald-500/20">
                    <FlaskConical size={20} />
                  </div>
                  <div>
                    <p className="font-bold text-lg text-slate-800 group-hover:text-emerald-700 transition-colors">
                      {lab}
                    </p>
                    <p className="text-xs text-slate-500 line-clamp-1">
                      {labMap[lab] || "Laboratory"}
                    </p>
                  </div>
                </div>
                <div className="text-xs text-slate-500 space-y-1 border-t border-slate-100 pt-3">
                  <p>
                    Practical Sessions:{" "}
                    <span className="font-semibold text-slate-700">
                      {sessionCount}
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

  // ─── Schedule View ────────────────────────────────────────────────────────────
  const renderScheduleView = () => {
    if (!selectedLab) return null;
    return (
      <div className="print:px-0">
        <button
          onClick={() => {
            setSelectedLab(null);
            setView("landing");
          }}
          className="print:hidden flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-800 font-medium mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          Back to Lab Directory
        </button>

        <div className="mb-6 flex justify-between items-end">
          <div>
            <h3 className="text-2xl font-bold text-slate-800">
              {labMap[selectedLab]
                ? `${labMap[selectedLab]} (${selectedLab})`
                : selectedLab}
              <span className="ml-2 text-base font-normal text-slate-500">
                — Lab Timetable
              </span>
            </h3>
            <p className="text-sm text-slate-500 mt-1">
              Consolidated view of all practical sessions assigned to this lab
            </p>
          </div>
          <button
            onClick={() =>
              exportLabTimetable(
                selectedLab,
                labData[selectedLab],
                allTimeSlots,
              )
            } //[cite: 2]
            className="print:hidden flex items-center gap-2 bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium shadow-sm hover:bg-slate-50 transition-colors"
          >
            <FlaskConical size={18} />
            <span>Download CSV</span>
          </button>
        </div>

        {renderScheduleTable(selectedLab)}
      </div>
    );
  };

  // ─── Root Render ──────────────────────────────────────────────────────────────
  return (
    <div
      className={
        isSubComponent
          ? ""
          : "min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8 print:p-0 print:bg-white"
      }
    >
      <div className={isSubComponent ? "" : "max-w-[1800px] mx-auto"}>
        {!isSubComponent && (
          <div className="mb-8 print:hidden">
            <h1 className="text-3xl font-bold text-slate-800 tracking-tight">
              Lab Timetables
            </h1>
            <p className="text-slate-500 mt-2">
              Individual, consolidated schedules for all laboratories
            </p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 text-red-700">
            <p className="font-semibold">Error Loading Timetables</p>
            <p className="text-sm mt-1">{error}</p>
            <button
              onClick={loadLabData}
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
        ) : labNames.length === 0 && !error ? (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <FlaskConical size={48} className="mx-auto mb-4 text-slate-400" />
            <h2 className="text-2xl font-semibold text-slate-800 mb-4">
              No Lab Data Found
            </h2>
            <p className="text-slate-600 mb-6">
              Timetables haven&apos;t been generated yet or no lab assignments
              were found.
            </p>
            <button
              onClick={loadLabData}
              className="px-8 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-semibold rounded-lg hover:from-emerald-700 hover:to-teal-700 transition-all shadow-lg hover:shadow-xl"
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
