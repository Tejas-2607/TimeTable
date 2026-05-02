/**
 * src/lib/excelExport.js
 *
 * Zero-dependency CSV export helpers for all four timetable views.
 *
 * FORMATTING:
 * - Each batch/session gets its own dedicated row
 * - Blank spacer row between every time-slot group
 * - 13:15 labelled as LUNCH BREAK
 * - Plain text labels only (no emojis — breaks Excel encoding on Windows)
 * - UTF-8 BOM added so Excel opens the file with correct encoding automatically
 */

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const LUNCH_SLOT = "13:15";
const NUM_COLS = 6;

// ─── UTILITIES ────────────────────────────────────────────────────────────────

function sortTimeSlots(slots) {
  const toMins = (t) => {
    const [h, m = "0"] = t.replace(".", ":").split(":");
    return parseInt(h, 10) * 60 + parseInt(m, 10);
  };
  return [...slots].sort((a, b) => toMins(a) - toMins(b));
}

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
 * Download CSV with UTF-8 BOM prepended.
 * The BOM (\uFEFF) tells Excel to open the file as UTF-8 instead of
 * the system default encoding, preventing garbled characters.
 */
function downloadCSV(csvString, filename) {
  const BOM = "\uFEFF";
  const blob = new Blob([BOM + csvString], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${filename}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

const SPACER_ROW = () => Array(NUM_COLS).fill("");

// ─── CELL CONTENT BUILDERS ────────────────────────────────────────────────────
// Plain text labels only — no emojis.
// \n inside a quoted CSV cell renders as a line break in Excel (enable Wrap Text).

function cellForClassSession(s) {
  const lines = [];
  if (s.subject)
    lines.push(`${s.subject}${s.subject_full ? ` (${s.subject_full})` : ""}`);
  if (s.faculty) lines.push(`Faculty: ${s.faculty}`);
  if (s.batch && s.batch !== "All") lines.push(`Batch: ${s.batch}`);
  if (s.lab) lines.push(`Lab: ${s.lab}`);
  return lines.join("\n");
}

function cellForPracticalSession(s) {
  const cls = [s.class, s.division].filter(Boolean).join("-");
  const lines = [];
  if (cls) lines.push(`Class: ${cls}`);
  if (s.batch) lines.push(`Batch: B${s.batch}`);
  if (s.subject) lines.push(`Sub: ${s.subject}`);
  if (s.faculty) lines.push(`Faculty: ${s.faculty}`);
  return lines.join("\n");
}

function cellForFacultySession(s) {
  const cls = [s.class_key, s.division ? `Div ${s.division}` : ""]
    .filter(Boolean)
    .join(" ");
  const lines = [];
  if (cls) lines.push(`Class: ${cls}`);
  if (s.subject) lines.push(`Sub: ${s.subject}`);
  if (s.batch && s.batch !== "All") lines.push(`Batch: ${s.batch}`);
  if (s.lab) lines.push(`Lab: ${s.lab}`);
  return lines.join("\n");
}

function cellForLabSession(s) {
  const cls = [s.class_key, s.division].filter(Boolean).join("-");
  const lines = [];
  if (cls) lines.push(`Class: ${cls}`);
  if (s.batch) lines.push(`Batch: B${s.batch}`);
  if (s.subject) lines.push(`Sub: ${s.subject}`);
  if (s.faculty) lines.push(`Faculty: ${s.faculty}`);
  return lines.join("\n");
}

// ─── CORE GRID BUILDER ────────────────────────────────────────────────────────

function buildExpandedGrid(slots, sessionsFn, formatFn) {
  const rows = [["Time / Day", ...DAYS]];

  for (const time of slots) {
    if (time === LUNCH_SLOT) {
      rows.push([time, ...DAYS.map(() => "--- LUNCH BREAK ---")]);
      rows.push(SPACER_ROW());
      continue;
    }

    const sessionsByDay = DAYS.map((day) => sessionsFn(day, time));
    const maxSessions = Math.max(...sessionsByDay.map((s) => s.length), 1);

    for (let i = 0; i < maxSessions; i++) {
      const row = [i === 0 ? time : ""];
      for (const daySessions of sessionsByDay) {
        const session = daySessions[i];
        row.push(session ? formatFn(session) : "");
      }
      rows.push(row);
    }

    rows.push(SPACER_ROW());
  }

  return rows;
}

// ─── PUBLIC EXPORT FUNCTIONS ──────────────────────────────────────────────────

export function exportClassTimetable(classData, timeSlots) {
  const schedule = classData.schedule || {};
  const label = `${classData.class_key}-Div${classData.division}`;

  const slots = timeSlots?.length
    ? timeSlots
    : sortTimeSlots([
        ...new Set(Object.values(schedule).flatMap((d) => Object.keys(d))),
      ]);

  const aoa = buildExpandedGrid(
    slots,
    (day, time) => (schedule[day] || {})[time] || [],
    cellForClassSession,
  );

  downloadCSV(aoaToCSV(aoa), `Class_Timetable_${label}`);
}

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
      const aoa = buildExpandedGrid(
        slots,
        (day, time) => (schedule[day] || {})[time] || [],
        cellForPracticalSession,
      );
      const safeName = labName.replace(/[^a-zA-Z0-9_-]/g, "_");
      downloadCSV(aoaToCSV(aoa), `Practical_Plan_${safeName}`);
    }, idx * 300);
  });
}

export function exportFacultyTimetable(facName, schedule, timeSlots) {
  const slots = timeSlots?.length
    ? timeSlots
    : sortTimeSlots([
        ...new Set(Object.values(schedule).flatMap((d) => Object.keys(d))),
      ]);

  const aoa = buildExpandedGrid(
    slots,
    (day, time) => (schedule[day] || {})[time] || [],
    cellForFacultySession,
  );

  const safeName = facName.replace(/[^a-zA-Z0-9_-]/g, "_");
  downloadCSV(aoaToCSV(aoa), `Faculty_Timetable_${safeName}`);
}

export function exportLabTimetable(labName, schedule, timeSlots) {
  const slots = timeSlots?.length
    ? timeSlots
    : sortTimeSlots([
        ...new Set(Object.values(schedule).flatMap((d) => Object.keys(d))),
      ]);

  const aoa = buildExpandedGrid(
    slots,
    (day, time) => (schedule[day] || {})[time] || [],
    cellForLabSession,
  );

  const safeName = labName.replace(/[^a-zA-Z0-9_-]/g, "_");
  downloadCSV(aoaToCSV(aoa), `Lab_Timetable_${safeName}`);
}
