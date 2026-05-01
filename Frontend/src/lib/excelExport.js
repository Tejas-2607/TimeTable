/**
 * src/lib/excelExport.js
 *
 * Professional CSV export helpers for all timetable views.
 * Designed for readability in Microsoft Excel and Google Sheets.
 */

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

// ─── INTERNAL UTILITIES ──────────────────────────────────────────────────────

/**
 * Sorts time slots chronologically for the Y-axis.
 */
function sortTimeSlots(slots) {
  const toMins = (t) => {
    const [h, m = "0"] = t.replace(".", ":").split(":");
    return parseInt(h, 10) * 60 + parseInt(m, 10);
  };
  return [...slots].sort((a, b) => toMins(a) - toMins(b));
}

/**
 * Escapes cells for CSV safety, handling commas and quotes.
 */
function escapeCell(value) {
  const str = String(value ?? "");
  if (str.includes(",") || str.includes('"') || str.includes("\n")) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function aoaToCSV(aoa) {
  return aoa.map((row) => row.map(escapeCell).join(",")).join("\n");
}

/**
 * Triggers browser download for the generated CSV.
 */
function downloadCSV(csvString, filename) {
  const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${filename}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Builds the 2D array grid for the timetable.
 */
function buildGrid(slots, cellFn) {
  const header = ["Time / Day", ...DAYS];
  const rows = slots.map((time) => [
    time,
    ...DAYS.map((day) => cellFn(day, time)),
  ]);
  return [header, ...rows];
}

// ─── COMPACT SESSION FORMATTERS ──────────────────────────────────────────────

/**
 * Format: Subject (Full Name) | Faculty | Batch | Lab
 */
function formatClassSession(s) {
  const parts = [];
  if (s.subject) {
    parts.push(`${s.subject}${s.subject_full ? ` (${s.subject_full})` : ""}`);
  }
  if (s.faculty) parts.push(s.faculty);
  if (s.batch && s.batch !== "All") parts.push(s.batch);
  if (s.lab) parts.push(s.lab);
  return parts.join(" | ");
}

/**
 * Format: Year-Div | B1 | Subject | Faculty
 */
function formatPracticalSession(s) {
  const cls = [s.class, s.division].filter(Boolean).join("-");
  const parts = [];
  if (cls) parts.push(cls);
  if (s.batch) parts.push(`B${s.batch}`);
  if (s.subject) parts.push(s.subject);
  if (s.faculty) parts.push(s.faculty);
  return parts.join(" | ");
}

/**
 * Format: Class Div | Subject | Batch | Lab
 */
function formatFacultySession(s) {
  const cls = [s.class_key, s.division ? `Div ${s.division}` : ""]
    .filter(Boolean)
    .join(" ");
  const parts = [];
  if (cls) parts.push(cls);
  if (s.subject) parts.push(s.subject);
  if (s.batch && s.batch !== "All") parts.push(s.batch);
  if (s.lab) parts.push(s.lab);
  return parts.join(" | ");
}

/**
 * Format: Class-Div | B1 | Subject | Faculty
 */
function formatLabSession(s) {
  const cls = [s.class_key, s.division].filter(Boolean).join("-");
  const parts = [];
  if (cls) parts.push(cls);
  if (s.batch) parts.push(`B${s.batch}`);
  if (s.subject) parts.push(s.subject);
  if (s.faculty) parts.push(s.faculty);
  return parts.join(" | ");
}

// ─── PUBLIC EXPORT FUNCTIONS ──────────────────────────────────────────────────

/**
 * Export Class Timetable
 */
export function exportClassTimetable(classData, timeSlots) {
  const schedule = classData.schedule || {};
  const label = `${classData.class_key}-Div${classData.division}`;

  const slots = timeSlots?.length
    ? timeSlots
    : sortTimeSlots([
        ...new Set(Object.values(schedule).flatMap((d) => Object.keys(d))),
      ]);

  const aoa = buildGrid(slots, (day, time) => {
    const sessions = (schedule[day] || {})[time] || [];
    return sessions.map(formatClassSession).join(" || ");
  });

  downloadCSV(aoaToCSV(aoa), `Class_Timetable_${label}`);
}

/**
 * Export Master Practical Plan (Staggered downloads)
 */
export function exportMasterPractical(allLabs, practicalSlots) {
  const labNames = Object.keys(allLabs);
  if (labNames.length === 0) return;

  const slots = practicalSlots?.length
    ? practicalSlots
    : sortTimeSlots([
        ...new Set(
          labNames.flatMap((lab) =>
            Object.values(allLabs[lab]).flatMap((d) => Object.keys(d)),
          ),
        ),
      ]);

  labNames.forEach((labName, idx) => {
    setTimeout(() => {
      const schedule = allLabs[labName];
      const aoa = buildGrid(slots, (day, time) => {
        const sessions = (schedule[day] || {})[time] || [];
        return sessions.map(formatPracticalSession).join(" || ");
      });
      const safeName = labName.replace(/[^a-zA-Z0-9_-]/g, "_");
      downloadCSV(aoaToCSV(aoa), `Practical_Plan_${safeName}`);
    }, idx * 300); // 300ms stagger
  });
}

/**
 * Export Faculty Timetable
 */
export function exportFacultyTimetable(facName, schedule, timeSlots) {
  const slots = timeSlots?.length
    ? timeSlots
    : sortTimeSlots([
        ...new Set(Object.values(schedule).flatMap((d) => Object.keys(d))),
      ]);

  const aoa = buildGrid(slots, (day, time) => {
    const sessions = (schedule[day] || {})[time] || [];
    return sessions.map(formatFacultySession).join(" || ");
  });

  const safeName = facName.replace(/[^a-zA-Z0-9_-]/g, "_");
  downloadCSV(aoaToCSV(aoa), `Faculty_Timetable_${safeName}`);
}

/**
 * Export Lab Timetable
 */
export function exportLabTimetable(labName, schedule, timeSlots) {
  const slots = timeSlots?.length
    ? timeSlots
    : sortTimeSlots([
        ...new Set(Object.values(schedule).flatMap((d) => Object.keys(d))),
      ]);

  const aoa = buildGrid(slots, (day, time) => {
    const sessions = (schedule[day] || {})[time] || [];
    return sessions.map(formatLabSession).join(" || ");
  });

  const safeName = labName.replace(/[^a-zA-Z0-9_-]/g, "_");
  downloadCSV(aoaToCSV(aoa), `Lab_Timetable_${safeName}`);
}
