/**
 * timetableUtils.jsx
 * Utility functions for rendering class timetables with parallel session support
 */

const getBatchLabel = (batch, classContext, isPractical) => {
  if (!batch || batch === "All" || !isPractical) return batch ? `Batch ${batch}` : "";
  let prefix = "B";
  if (classContext) {
    const yr = (classContext.year || "").toUpperCase();
    if (yr.includes("SY") || yr.includes("S.Y") || yr.includes("SECOND")) prefix = "S";
    else if (yr.includes("TY") || yr.includes("T.Y") || yr.includes("THIRD")) prefix = "T";
    const div = (classContext.division || "").toUpperCase();
    return `${prefix}${div}${batch}`;
  }
  return `Batch ${batch}`;
};

/**
 * Renders a single session entry (non-parallel)
 */
export const renderSingleSession = (session, classContext) => {
  const isPractical = session.type !== "lecture" && !!session.lab;
  return (
    <div className={`border rounded p-2 flex-1 ${isPractical ? "bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200" : "bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200"}`}>
      {session.batch && session.batch !== "All" && (
        <div className={`font-semibold text-xs mb-1 ${isPractical ? "text-emerald-900" : "text-blue-900"}`}>
          {isPractical ? getBatchLabel(session.batch, classContext, isPractical) : `Batch ${session.batch}`}
        </div>
      )}
      <div className="flex items-start gap-1 text-slate-700 mb-0.5">
        <span className="font-medium text-xs">
          {session.subject} — {session.subject_full}
        </span>
      </div>
      <div className="flex items-start gap-1 text-slate-600 mb-0.5">
        <span className="text-xs leading-tight">{session.faculty}</span>
      </div>
      {session.lab && (
        <div className="flex items-start gap-1 text-slate-500">
          <span className="text-xs leading-tight">{session.lab}</span>
        </div>
      )}
    </div>
  );
};

/**
 * Renders parallel elective sessions grouped together
 */
export const renderParallelSessions = (parallelEntry, classContext) => {
  const { group_name, sessions } = parallelEntry;

  return (
    <div className="border-2 border-purple-400 rounded p-2 flex-1 bg-gradient-to-br from-purple-50 to-pink-50">
      <div className="font-bold text-xs mb-2 text-purple-900 bg-purple-100 px-2 py-1 rounded">
        {group_name || "Parallel"}
      </div>
      <div className="flex flex-col gap-2">
        {sessions.map((session, idx) => (
          <div
            key={idx}
            className="border border-purple-300 rounded p-1.5 bg-white flex-1"
          >
            <div className="font-medium text-xs text-purple-800 mb-0.5">
              {session.subject}
            </div>
            <div className="flex items-start gap-1 text-slate-700 text-xs mb-0.5">
              <span className="font-medium">{session.faculty}</span>
            </div>
            {session.lab && (
              <div className="flex items-start gap-1 text-slate-600 text-xs">
                <span>{session.lab}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * Main render function for a time slot's sessions
 * Handles both single and parallel sessions
 */
export const renderSessionCell = (sessions, classContext) => {
  if (!sessions || sessions.length === 0) {
    return (
      <div className="h-full min-h-[70px] bg-slate-50 border border-slate-200 rounded p-2 flex items-center justify-center text-xs text-slate-400">
        —
      </div>
    );
  }

  return (
    <div className="h-full min-h-[70px] flex flex-col gap-1">
      {sessions.map((entry, idx) => {
        // Check if this is a parallel entry
        if (entry.parallel === true) {
          return <div key={idx}>{renderParallelSessions(entry, classContext)}</div>;
        } else {
          // Single session entry
          return <div key={idx}>{renderSingleSession(entry, classContext)}</div>;
        }
      })}
    </div>
  );
};
