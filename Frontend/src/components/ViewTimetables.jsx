import { useState, useEffect } from "react";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import {
  deleteClassTimetable,
  getClassTimetables,
} from "../services/classTimetableService";
import {
  deleteMasterTimetable,
  getMasterTimetables,
} from "../services/masterTimetableService";
import {
  exportClassTimetable,
  exportMasterPractical,
} from "../lib/excelExport"; //[cite: 2]
import { getDepartmentTimings } from "../services/settingsService";
import { getUserFriendlyErrorMessage } from "../lib/errorMessages";
import { renderSessionCell } from "../lib/timetableUtils.jsx"; // NEW: Import parallel session renderer
import {
  Clock,
  ArrowLeft,
  Calendar,
  ChevronRight,
  BookOpen,
  Users as UsersIcon,
  FlaskConical,
  Layers,
  Printer,
  Briefcase,
  Grid3x3,
  Trash2,
} from "lucide-react";

import FacultyTimetables from "./FacultyTimetables";
import LabTimetables from "./LabTimetables";

export default function ViewTimetables() {
  const navigate = useNavigate();
  const { tab } = useParams();

  // views: 'landing' | 'classCards' | 'schedule' | 'practicalTable' | 'faculty' | 'labs'
  const [view, setView] = useState("landing");

  // Map URL tabs to internal view states
  useEffect(() => {
    if (!tab) {
      setView("landing");
      setSelectedClass(null);
    } else if (tab === "classes") {
      // If we are in 'schedule' view but navigate to 'classes', it means we are going back to the list
      setView("classCards");
    } else if (tab === "practical") {
      setView("practicalTable");
    } else if (tab === "faculty") {
      setView("faculty");
    } else if (tab === "labs") {
      setView("labs");
    }
  }, [tab]);
  const [timetables, setTimetables] = useState([]);
  const [practicalData, setPracticalData] = useState(null);
  const [selectedClass, setSelectedClass] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPracticalLoading, setIsPracticalLoading] = useState(true);
  const [error, setError] = useState(null);

  const daysOfWeek = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
  const [timeSlots, setTimeSlots] = useState([]);
  const [practicalTimeSlots, setPracticalTimeSlots] = useState([]);
  const [breaks, setBreaks] = useState([]);

  // Fetch both datasets on mount
  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    // Local sets to accumulate all unique time slots (lectures + breaks)
    const slotSet = new Set();
    const pSlotSet = new Set();

    setIsLoading(true);
    setIsPracticalLoading(true);
    setError(null);

    // Fetch class timetables
    try {
      const res = await getClassTimetables();
      const data = res.timetables || res.data?.timetables || [];
      setTimetables(data);

      // Dynamically extract all unique time slots from the actual schedule data
      data.forEach((tt) => {
        const sched = tt.schedule || {};
        Object.values(sched).forEach((dayObj) => {
          Object.keys(dayObj).forEach((t) => slotSet.add(t));
        });
      });
    } catch (err) {
      console.error("Error loading class timetables:", err);
      setError(
        getUserFriendlyErrorMessage(
          err,
          "Unable to load class timetables. Please try again.",
        ),
      );
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
      data.forEach((tt) => {
        const sched = tt.schedule || {};
        Object.values(sched).forEach((dayObj) => {
          Object.keys(dayObj).forEach((t) => pSlotSet.add(t));
        });
      });
    } catch (err) {
      console.warn("Could not load practical data:", err);
      setError(
        getUserFriendlyErrorMessage(
          err,
          "Unable to load practical timetable data. Please try again.",
        ),
      );
      setPracticalData(null);
    } finally {
      setIsPracticalLoading(false);
    }

    // Fetch breaks from settings
    try {
      const timingsRes = await getDepartmentTimings();
      const breaksData = timingsRes.breaks || [];
      setBreaks(breaksData);

      // Include every break start time as its own row in both
      // class and practical timetables.
      breaksData.forEach((b) => {
        if (b.start_time) {
          slotSet.add(b.start_time);
          pSlotSet.add(b.start_time);
        }
      });
    } catch (err) {
      console.warn("Could not load breaks:", err);
      setError(
        getUserFriendlyErrorMessage(
          err,
          "Unable to load break settings. Please try again.",
        ),
      );
      setBreaks([]);
    }

    // Finally, sort and commit the combined time slot lists
    const parseTime = (t) => {
      const [hh, mm = "0"] = String(t).split(":");
      return parseInt(hh, 10) * 60 + parseInt(mm, 10);
    };

    if (slotSet.size > 0) {
      const sorted = Array.from(slotSet).sort(
        (a, b) => parseTime(a) - parseTime(b),
      );
      setTimeSlots(sorted);
    } else {
      setTimeSlots([]);
    }

    if (pSlotSet.size > 0) {
      const sorted = Array.from(pSlotSet).sort(
        (a, b) => parseTime(a) - parseTime(b),
      );
      setPracticalTimeSlots(sorted);
    } else {
      setPracticalTimeSlots([]);
    }
  };

  const handleDeleteClassTimetable = async (timetableId) => {
    if (!timetableId) return;
    if (!window.confirm("Delete this class timetable?")) return;
    try {
      await deleteClassTimetable(timetableId);
      if (selectedClass?._id === timetableId) {
        setSelectedClass(null);
        setView("classCards");
      }
      await loadAllData();
    } catch (err) {
      alert(
        getUserFriendlyErrorMessage(
          err,
          "Unable to delete class timetable. Please try again.",
        ),
      );
    }
  };

  const handleDeleteMasterTimetable = async (timetableId) => {
    if (!timetableId) return;
    if (!window.confirm("Delete this master practical timetable entry?"))
      return;
    try {
      await deleteMasterTimetable(timetableId);
      await loadAllData();
    } catch (err) {
      alert(
        getUserFriendlyErrorMessage(
          err,
          "Unable to delete master practical timetable entry. Please try again.",
        ),
      );
    }
  };

  // ---------- helpers ----------
  const latestDate = timetables.length
    ? new Date(
        Math.max(...timetables.map((t) => new Date(t.generated_at))),
      ).toLocaleString()
    : "";

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getAllLabs = () => {
    if (!practicalData || !practicalData.timetables) return {};
    const allLabs = {};
    practicalData.timetables.forEach((timetable) => {
      if (timetable.lab_name && timetable.schedule) {
        if (!allLabs[timetable.lab_name]) {
          allLabs[timetable.lab_name] = timetable.schedule;
        }
      }
    });
    return allLabs;
  };

  // Helper function to get break name for a specific time
  const getBreakAtTime = (time) => {
    return breaks.find((b) => b.start_time === time);
  };

  const renderBreakCell = (breakInfo, minHeight = "70px") => (
    <div
      className="h-full bg-amber-100 border-2 border-dashed border-amber-300 rounded p-2 flex flex-col items-center justify-center"
      style={{ minHeight }}
    >
      <span className="text-[10px] font-bold tracking-wide text-amber-800">
        BREAK
      </span>
      <span className="text-sm font-semibold text-amber-700 text-center">
        {breakInfo?.name || "Break"}
      </span>
    </div>
  );

  // ---------- session cell (class timetable) ----------
  // NOTE: renderSessionCell is now imported from timetableUtils.js
  // It handles both single and parallel sessions automatically

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
          <div
            key={idx}
            className="bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-200 rounded p-2 flex-1"
          >
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
                {daysOfWeek.map((day) => (
                  <th
                    key={day}
                    className="border border-blue-700 px-3 py-3 text-white font-semibold text-center"
                  >
                    {day}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {timeSlots.map((time, timeIdx) => {
                const isPracticalSlot = practicalTimeSlots.includes(time);
                const breakInfo = getBreakAtTime(time);
                const isBreakTime = breakInfo !== undefined;

                return (
                  <tr
                    key={time}
                    className={
                      isBreakTime
                        ? "bg-amber-50"
                        : timeIdx % 2 === 0
                          ? "bg-white"
                          : "bg-slate-50"
                    }
                  >
                    <td
                      className={`border ${isBreakTime ? "border-amber-300" : "border-slate-300"} px-4 py-3 font-semibold sticky left-0 z-10 whitespace-nowrap ${
                        isBreakTime
                          ? "text-amber-700 bg-amber-50"
                          : isPracticalSlot
                            ? "text-blue-700"
                            : "text-slate-800"
                      }`}
                      style={{
                        backgroundColor: isBreakTime
                          ? "#fef3c7"
                          : timeIdx % 2 === 0
                            ? "white"
                            : "#f8fafc",
                      }}
                    >
                      <div className="flex items-center gap-1.5">
                        <Clock
                          size={14}
                          className={
                            isBreakTime
                              ? "text-amber-600"
                              : isPracticalSlot
                                ? "text-blue-500"
                                : "text-slate-500"
                          }
                        />
                        <div className="flex flex-col">
                          <span>{time}</span>
                          {isBreakTime && (
                            <span className="text-xs font-bold text-amber-700 uppercase">
                              {breakInfo.name}
                            </span>
                          )}
                        </div>
                      </div>
                    </td>
                    {daysOfWeek.map((day) => {
                      const daySchedule = schedule[day] || {};
                      const sessions = daySchedule[time] || [];
                      return (
                        <td
                          key={`${time}-${day}`}
                          className={`border ${isBreakTime ? "border-amber-200 bg-amber-50" : "border-slate-300"} p-2 min-w-[160px]`}
                        >
                          {isBreakTime
                            ? renderBreakCell(breakInfo, "70px")
                            : renderSessionCell(sessions)}
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
                {daysOfWeek.map((day) => (
                  <th
                    key={day}
                    className="border border-emerald-700 px-4 py-3 text-white font-semibold text-center"
                    colSpan={practicalTimeSlots.length}
                  >
                    {day}
                  </th>
                ))}
              </tr>
              <tr className="bg-emerald-500">
                <th className="border border-emerald-600 px-4 py-2 text-white text-sm font-medium sticky left-0 bg-emerald-500 z-10">
                  Time
                </th>
                {daysOfWeek.map((day) =>
                  practicalTimeSlots.map((time) => {
                    const breakInfo = getBreakAtTime(time);
                    const isBreakTime = breakInfo !== undefined;
                    return (
                      <th
                        key={`${day}-${time}`}
                        className={`border px-2 py-2 text-xs font-medium ${
                          isBreakTime
                            ? "border-amber-600 bg-amber-500 text-white"
                            : "border-emerald-600 text-white"
                        }`}
                      >
                        <div className="flex flex-col items-center justify-center leading-tight">
                          <div className="flex items-center justify-center gap-1">
                            <Clock size={12} />
                            <span>{time}</span>
                          </div>
                          {isBreakTime && (
                            <span className="text-[10px] font-bold uppercase">
                              {breakInfo.name}
                            </span>
                          )}
                        </div>
                      </th>
                    );
                  }),
                )}
              </tr>
            </thead>
            <tbody>
              {labNames.map((labName, labIdx) => {
                const labSchedule = allLabs[labName];
                const masterTimetableId = practicalData?.timetables?.find(
                  (t) => t.lab_name === labName,
                )?._id;
                return (
                  <tr
                    key={labName}
                    className={labIdx % 2 === 0 ? "bg-white" : "bg-slate-50"}
                  >
                    <td
                      className="border border-slate-300 px-4 py-3 font-semibold text-slate-800 sticky left-0 z-10"
                      style={{
                        backgroundColor: labIdx % 2 === 0 ? "white" : "#f8fafc",
                      }}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span>{labName}</span>
                        <button
                          onClick={() =>
                            handleDeleteMasterTimetable(masterTimetableId)
                          }
                          className="p-1.5 rounded-md text-red-600 hover:bg-red-50"
                          title="Delete master practical timetable"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                    {daysOfWeek.map((day) => {
                      const daySchedule = labSchedule[day] || {};
                      return practicalTimeSlots.map((time) => {
                        const breakInfo = getBreakAtTime(time);
                        const isBreakTime = breakInfo !== undefined;
                        const sessions = daySchedule[time] || [];
                        return (
                          <td
                            key={`${labName}-${day}-${time}`}
                            className={`border p-2 min-w-[140px] ${
                              isBreakTime
                                ? "border-amber-200 bg-amber-50"
                                : "border-slate-300"
                            }`}
                          >
                            {isBreakTime
                              ? renderBreakCell(breakInfo, "80px")
                              : renderPracticalSessionCell(sessions)}
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

  // 1. Landing view — 4 main cards
  const renderLanding = () => (
    <div className="space-y-6">
      <section className="bg-white/40 backdrop-blur-md rounded-3xl p-8 border border-white/50 shadow-xl shadow-slate-200/50">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h3 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
              <span className="w-2 h-8 bg-gradient-to-b from-blue-500 to-indigo-600 rounded-full" />
              Timetable Dashboard
            </h3>
            <p className="text-slate-500 mt-1 ml-5">
              Select a category to view consolidated schedules
            </p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 1. Master Practical Plan */}
          <button
            onClick={() => navigate("/view/practical")}
            className="group bg-white rounded-2xl shadow-md hover:shadow-xl border border-slate-200 hover:border-emerald-300 transition-all duration-300 p-6 text-left cursor-pointer"
          >
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <FlaskConical size={32} className="text-white" />
              </div>
              <div>
                <p className="font-bold text-xl text-slate-800 group-hover:text-emerald-700 transition-colors">
                  Master Practical Plan
                </p>
                <p className="text-sm text-slate-500 mt-1">
                  Lab-wise schedule across all years
                </p>
              </div>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 group-hover:text-emerald-500">
                View lab allocations
              </span>
              <ChevronRight
                size={18}
                className="text-slate-300 group-hover:text-emerald-500 transition-transform group-hover:translate-x-1"
              />
            </div>
          </button>

          {/* 2. Class Timetables */}
          <button
            onClick={() => navigate("/view/classes")}
            className="group bg-white rounded-2xl shadow-md hover:shadow-xl border border-slate-200 hover:border-blue-300 transition-all duration-300 p-6 text-left cursor-pointer"
          >
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Calendar size={32} className="text-white" />
              </div>
              <div>
                <p className="font-bold text-xl text-slate-800 group-hover:text-blue-700 transition-colors">
                  Class Timetables
                </p>
                <p className="text-sm text-slate-500 mt-1">
                  {timetables.length} classes generated
                </p>
              </div>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 group-hover:text-blue-500">
                Browse by class/div
              </span>
              <ChevronRight
                size={18}
                className="text-slate-300 group-hover:text-blue-500 transition-transform group-hover:translate-x-1"
              />
            </div>
          </button>

          {/* 3. Faculty Timetables */}
          <button
            onClick={() => navigate("/view/faculty")}
            className="group bg-white rounded-2xl shadow-md hover:shadow-xl border border-slate-200 hover:border-indigo-300 transition-all duration-300 p-6 text-left cursor-pointer"
          >
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                <Briefcase size={32} className="text-white" />
              </div>
              <div>
                <p className="font-bold text-xl text-slate-800 group-hover:text-indigo-700 transition-colors">
                  Faculty Timetables
                </p>
                <p className="text-sm text-slate-500 mt-1">
                  Personal schedules for all staff
                </p>
              </div>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 group-hover:text-indigo-500">
                Search by name
              </span>
              <ChevronRight
                size={18}
                className="text-slate-300 group-hover:text-indigo-500 transition-transform group-hover:translate-x-1"
              />
            </div>
          </button>

          {/* 4. Lab Timetables */}
          <button
            onClick={() => navigate("/view/labs")}
            className="group bg-white rounded-2xl shadow-md hover:shadow-xl border border-slate-200 hover:border-teal-300 transition-all duration-300 p-6 text-left cursor-pointer"
          >
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-teal-500 to-emerald-500 flex items-center justify-center shadow-lg shadow-teal-500/20">
                <Grid3x3 size={32} className="text-white" />
              </div>
              <div>
                <p className="font-bold text-xl text-slate-800 group-hover:text-teal-700 transition-colors">
                  Lab Timetables
                </p>
                <p className="text-sm text-slate-500 mt-1">
                  Consolidated schedules for laboratories
                </p>
              </div>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 group-hover:text-teal-500">
                View lab directory
              </span>
              <ChevronRight
                size={18}
                className="text-slate-300 group-hover:text-teal-500 transition-transform group-hover:translate-x-1"
              />
            </div>
          </button>
        </div>
      </section>

      {/* Stats/Info Section */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white/60 backdrop-blur-sm rounded-xl p-4 border border-emerald-100/50 shadow-sm flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-600">
            <FlaskConical size={20} />
          </div>
          <div>
            <p className="text-slate-400 text-[10px] font-semibold uppercase tracking-wider">
              Total Sessions
            </p>
            <p className="text-xl font-bold text-slate-800">
              {timetables.reduce(
                (acc, curr) => acc + (curr.total_practicals || 0),
                0,
              )}{" "}
              <span className="text-xs font-medium text-slate-500">Practs</span>
            </p>
          </div>
        </div>

        <div className="bg-white/60 backdrop-blur-sm rounded-xl p-4 border border-blue-100/50 shadow-sm flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center text-blue-600">
            <Clock size={20} />
          </div>
          <div>
            <p className="text-slate-400 text-[10px] font-semibold uppercase tracking-wider">
              Last Gen
            </p>
            <p className="text-xl font-bold text-slate-800">
              {latestDate.split(",")[0]}
            </p>
          </div>
        </div>

        <div className="bg-white/60 backdrop-blur-sm rounded-xl p-4 border border-indigo-100/50 shadow-sm flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600">
            <UsersIcon size={20} />
          </div>
          <div>
            <p className="text-slate-400 text-[10px] font-semibold uppercase tracking-wider">
              Classes
            </p>
            <p className="text-xl font-bold text-slate-800">
              {timetables.length}{" "}
              <span className="text-xs font-medium text-slate-500">Divs</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  // 2. Cards view — practical plan card + class cards
  const renderClassCards = () => (
    <div className="space-y-10">
      <button
        onClick={() => navigate("/view")}
        className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
      >
        <ArrowLeft size={18} />
        Back to Dashboard
      </button>

      <section>
        <h3 className="text-xl font-bold text-slate-700 mb-4 flex items-center gap-2">
          <span className="inline-block w-1.5 h-6 bg-blue-500 rounded-full" />
          Class Timetables
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {/* Class-wise Cards */}
          {timetables.map((tt) => (
            <div
              key={tt._id}
              onClick={() => {
                setSelectedClass(tt);
                setView("schedule");
              }}
              className="relative group bg-white rounded-2xl shadow-md hover:shadow-xl border border-slate-200 hover:border-blue-300 transition-all duration-300 p-5 text-left cursor-pointer"
            >
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteClassTimetable(tt._id);
                }}
                className="absolute top-3 right-3 p-2 rounded-lg text-red-600 hover:bg-red-50"
                title="Delete class timetable"
              >
                <Trash2 size={16} />
              </button>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-11 h-11 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-blue-500/20">
                  {tt.class_key.split("-")[0]}
                </div>
                <div>
                  <p className="font-bold text-lg text-slate-800 group-hover:text-blue-700 transition-colors">
                    {tt.class_key}
                  </p>
                  <p className="text-xs text-slate-500">
                    Division {tt.division}
                  </p>
                </div>
              </div>
              <div className="text-xs text-slate-400 space-y-1 border-t border-slate-100 pt-3">
                <p>
                  Total Practicals:{" "}
                  <span className="font-semibold text-slate-600">
                    {tt.total_practicals}
                  </span>
                </p>
                <p>Generated: {formatDate(tt.generated_at)}</p>
              </div>
            </div>
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
          onClick={() => {
            setSelectedClass(null);
            setView("classCards"); // Force internal state change to be safe
            navigate("/view/classes");
          }}
          className="print:hidden flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 font-medium mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          Back to Class List
        </button>

        <div className="mb-6 flex justify-between items-end">
          <div>
            <h3 className="text-2xl font-bold text-slate-800">
              {selectedClass.class_key}
              <span className="ml-2 text-base font-normal text-slate-500">
                — Division {selectedClass.division}
              </span>
            </h3>
            <p className="text-sm text-slate-500 mt-1">
              Generated on {formatDate(selectedClass.generated_at)}{" "}
              &nbsp;·&nbsp; {selectedClass.total_practicals} practicals assigned
            </p>
          </div>
          <button
            onClick={() => exportClassTimetable(selectedClass, timeSlots)} //[cite: 2]
            className="print:hidden flex items-center gap-2 bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium shadow-sm hover:bg-slate-50 transition-colors"
          >
            <span>Download CSV</span>
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
        onClick={() => navigate("/view")}
        className="print:hidden flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 font-medium mb-6 transition-colors"
      >
        <ArrowLeft size={18} />
        Back to Dashboard
      </button>

      <div className="mb-6 flex justify-between items-end">
        <div>
          <h3 className="text-2xl font-bold text-slate-800">
            Master Practical Plan
          </h3>
          <p className="text-sm text-slate-500 mt-1">
            Lab-wise schedule across all years
          </p>
        </div>
        <button
          onClick={() =>
            exportMasterPractical(getAllLabs(), practicalTimeSlots)
          } //[cite: 2]
          className="print:hidden flex items-center gap-2 bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium shadow-sm hover:bg-slate-50 transition-colors"
        >
          <span>Download CSV (All Labs)</span>
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
                  <div
                    key={cellIdx}
                    className="flex-1 bg-slate-100 rounded border border-slate-200"
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : practicalData &&
        practicalData.timetables &&
        practicalData.timetables.length > 0 ? (
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
    <div className="min-h-full bg-gradient-to-br from-slate-50 to-slate-100 p-6 print:p-0 print:bg-white">
      <div className="max-w-[1600px] mx-auto w-full">
        <div className="mb-6 print:hidden shrink-0">
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">
            View Timetables
          </h1>
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
            <h2 className="text-2xl font-semibold text-slate-800 mb-4">
              No Timetables Found
            </h2>
            <p className="text-slate-600 mb-6">
              No class timetables have been generated yet. Generate one from the
              "Generate Timetable" section.
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
            {view === "landing" && renderLanding()}
            {view === "classCards" && renderClassCards()}
            {view === "schedule" && renderScheduleView()}
            {view === "practicalTable" && renderPracticalTableView()}
            {view === "faculty" && (
              <FacultyTimetables
                isSubComponent={true}
                onBackToDashboard={() => navigate("/view")}
              />
            )}
            {view === "labs" && (
              <LabTimetables
                isSubComponent={true}
                onBackToDashboard={() => navigate("/view")}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
