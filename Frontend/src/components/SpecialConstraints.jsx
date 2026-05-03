// src/components/SpecialConstraints.jsx
import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import {
  getConstraints,
  addConstraint,
  deleteConstraint,
} from "../services/constraintsService";
import { getFaculties } from "../services/facultyService";
import { getDepartmentTimings } from "../services/settingsService";
import { getSubjects } from "../services/subjectService";
import { getClassStructure } from "../services/classStructureService";
import {
  Plus,
  Trash2,
  ShieldAlert,
  Clock,
  Calendar,
  User,
  Info,
  Loader2,
  CheckCircle2,
  AlertCircle,
  BookOpen,
  Layers,
} from "lucide-react";

export default function SpecialConstraints() {
  const { user } = useAuth();
  const [constraints, setConstraints] = useState([]);
  const [faculties, setFaculties] = useState([]);
  const [timings, setTimings] = useState([]);
  const [subjectsByYear, setSubjectsByYear] = useState({});
  const [classStructure, setClassStructure] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const [formData, setFormData] = useState({
    type: "preferred_off",
    faculty_name: user?.role?.toLowerCase() === "faculty" ? user.name : "",
    day: "Monday",
    time_slot: "",
    description: "",
    year: "",
    division: "",
    subject: "",
  });

  const daysOfWeek = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [
        constraintsData,
        facultiesData,
        timingsData,
        subjectsData,
        structureData,
      ] = await Promise.all([
        getConstraints(),
        getFaculties(),
        getDepartmentTimings(),
        getSubjects(),
        getClassStructure(),
      ]);

      setConstraints(constraintsData);
      setFaculties(facultiesData);
      setSubjectsByYear(subjectsData || {});
      setClassStructure(structureData || {});

      if (timingsData && Array.isArray(timingsData.slots)) {
        setTimings(timingsData.slots);
        if (timingsData.slots.length > 0) {
          setFormData((prev) => ({
            ...prev,
            time_slot: timingsData.slots[0],
          }));
        }
      }

      // Initialize year/div if possible
      const yearsSet = Object.keys(structureData || {}).filter(
        (k) => k !== "_id",
      );
      if (yearsSet.length > 0) {
        const firstYear = yearsSet[0].toUpperCase();
        setFormData((prev) => ({ ...prev, year: firstYear }));

        const yearData =
          structureData[yearsSet[0]] || structureData[firstYear.toLowerCase()];
        const numDivs = yearData?.num_divisions || 0;
        const divs = Array.from({ length: numDivs }, (_, i) =>
          String.fromCharCode(65 + i),
        );

        if (divs.length > 0) {
          setFormData((prev) => ({ ...prev, division: divs[0] }));
        }
      }
    } catch (err) {
      console.error(err);
      setError("Failed to load data. Please check your network and try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const activeYears = Object.keys(classStructure)
    .filter((k) => k !== "_id")
    .map((y) => y.toUpperCase())
    .sort();

  const getYearData = (year) => {
    if (!year) return null;
    return (
      classStructure[year.toLowerCase()] ||
      classStructure[year.toUpperCase()] ||
      null
    );
  };

  const currentYearData = getYearData(formData.year);
  const numDivs = currentYearData?.num_divisions || 0;
  const currentDivisions = Array.from({ length: numDivs }, (_, i) =>
    String.fromCharCode(65 + i),
  );
  const currentSubjects =
    subjectsByYear[formData.year?.toLowerCase()] ||
    subjectsByYear[formData.year?.toUpperCase()] ||
    [];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSuccess(null);

    const payload = { ...formData };
    if (payload.type === "preferred_off") {
      delete payload.year;
      delete payload.division;
      delete payload.subject;
    }

    try {
      await addConstraint(payload);
      setSuccess("Constraint added successfully!");
      loadData();
      setFormData((prev) => ({
        ...prev,
        description: "",
      }));
    } catch (err) {
      setError("Failed to add constraint.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this constraint?"))
      return;
    try {
      await deleteConstraint(id);
      loadData();
    } catch (err) {
      setError("Failed to delete constraint.");
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <Loader2 className="animate-spin text-blue-600 mb-4" size={40} />
        <p className="text-slate-600 font-medium">
          Loading constraints data...
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-2">
          <ShieldAlert className="text-blue-600" />
          Special Constraints
        </h1>
        <p className="text-slate-500 mt-2">
          Define preferred off-times or fixed lecture timings. The generator
          will prioritize these settings.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Add Constraint Form */}
        <div className="xl:col-span-1">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 sticky top-8">
            <h2 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
              <Plus size={20} className="text-blue-600" />
              Add Constraint
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1">
                  Constraint Type
                </label>
                <select
                  value={formData.type}
                  onChange={(e) =>
                    setFormData({ ...formData, type: e.target.value })
                  }
                  className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 transition-all outline-none"
                >
                  <option value="preferred_off">Preferred Off Time</option>
                  <option value="fixed_time">
                    Fixed Lecture/Practical Time
                  </option>
                </select>
              </div>

              {user?.role?.toLowerCase() === "admin" ? (
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1">
                    Faculty Name
                  </label>
                  <select
                    value={formData.faculty_name}
                    onChange={(e) =>
                      setFormData({ ...formData, faculty_name: e.target.value })
                    }
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 transition-all outline-none"
                    required
                  >
                    <option value="">Select Faculty</option>
                    {faculties.map((f) => (
                      <option key={f._id} value={f.name}>
                        {f.name}
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1">
                    Faculty
                  </label>
                  <input
                    type="text"
                    value={user?.name}
                    disabled
                    className="w-full px-4 py-2 bg-slate-100 border border-slate-200 rounded-lg text-slate-500 cursor-not-allowed"
                  />
                </div>
              )}

              {formData.type === "fixed_time" && (
                <div className="space-y-4 pt-2 border-t border-slate-100">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-1">
                        Year
                      </label>
                      <select
                        value={formData.year}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            year: e.target.value,
                            division: "",
                            subject: "",
                          })
                        }
                        className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 transition-all outline-none"
                        required
                      >
                        {activeYears.map((y) => (
                          <option key={y} value={y}>
                            {y}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-1">
                        Division
                      </label>
                      <select
                        value={formData.division}
                        onChange={(e) =>
                          setFormData({ ...formData, division: e.target.value })
                        }
                        className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 transition-all outline-none"
                        required
                      >
                        <option value="">Select Div</option>
                        {currentDivisions.map((d) => (
                          <option key={d} value={d}>
                            {d}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1">
                      Subject
                    </label>
                    <select
                      value={formData.subject}
                      onChange={(e) =>
                        setFormData({ ...formData, subject: e.target.value })
                      }
                      className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 transition-all outline-none"
                      required
                    >
                      <option value="">Select Subject</option>
                      {currentSubjects.map((s) => (
                        <option key={s.short_name} value={s.short_name}>
                          {s.name} ({s.short_name})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-100">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1">
                    Day
                  </label>
                  <select
                    value={formData.day}
                    onChange={(e) =>
                      setFormData({ ...formData, day: e.target.value })
                    }
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 transition-all outline-none"
                  >
                    {daysOfWeek.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1">
                    Time Slot
                  </label>
                  <select
                    value={formData.time_slot}
                    onChange={(e) =>
                      setFormData({ ...formData, time_slot: e.target.value })
                    }
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 transition-all outline-none"
                    required
                  >
                    <option value="" disabled>
                      {timings.length === 0
                        ? "No time slots available"
                        : "Select time slot"}
                    </option>
                    {timings.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1">
                  Description / Reason
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  placeholder="e.g. Medical appointment, Personal work, or specific room req"
                  className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 transition-all outline-none h-20 resize-none"
                />
              </div>

              {error && (
                <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                  <AlertCircle size={16} />
                  {error}
                </div>
              )}

              {success && (
                <div className="flex items-center gap-2 p-3 bg-green-50 text-green-700 rounded-lg text-sm">
                  <CheckCircle2 size={16} />
                  {success}
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition-all shadow-md shadow-blue-200 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isSubmitting ? (
                  <Loader2 className="animate-spin" size={20} />
                ) : (
                  <Plus size={20} />
                )}
                Add Constraint
              </button>
            </form>
          </div>
        </div>

        {/* Constraints List */}
        <div className="xl:col-span-2 space-y-4">
          <h2 className="text-xl font-bold text-slate-800 mb-2 flex items-center gap-2">
            <Calendar size={20} className="text-blue-600" />
            Existing Constraints
          </h2>

          {constraints.length === 0 ? (
            <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-12 text-center text-slate-500">
              <Info size={40} className="mx-auto mb-3 opacity-20" />
              <p>No special constraints added yet.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {constraints.map((c) => (
                <div
                  key={c._id}
                  className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 hover:shadow-md transition-all group"
                >
                  <div className="flex justify-between items-start mb-3">
                    <span
                      className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                        c.type === "preferred_off"
                          ? "bg-orange-50 text-orange-700"
                          : "bg-blue-50 text-blue-700"
                      }`}
                    >
                      {c.type === "preferred_off"
                        ? "Preferred Off"
                        : "Fixed Time"}
                    </span>
                    <button
                      onClick={() => handleDelete(c._id)}
                      className="text-slate-300 hover:text-red-500 transition-colors p-1"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-slate-700 border-b border-slate-50 pb-2">
                      <User size={14} className="text-blue-500" />
                      <span className="font-bold">
                        {c.faculty_name || c.user_name}
                      </span>
                    </div>

                    {c.type === "fixed_time" && (
                      <div className="grid grid-cols-1 gap-2">
                        <div className="flex items-center gap-2 text-slate-600 text-sm">
                          <BookOpen size={14} className="text-emerald-500" />
                          <span className="font-semibold">{c.subject}</span>
                          <span className="text-xs text-slate-400">
                            ({c.class || c.year || "N/A"}-{c.division || "N/A"})
                          </span>
                        </div>
                      </div>
                    )}

                    <div className="flex items-center gap-2 text-slate-600 text-sm bg-slate-50 p-2 rounded-lg">
                      <Clock size={14} className="text-indigo-500" />
                      <span className="font-medium">
                        {c.day} at {c.time_slot}
                      </span>
                    </div>

                    {c.description && (
                      <div className="text-xs text-slate-500 italic">
                        "{c.description}"
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
