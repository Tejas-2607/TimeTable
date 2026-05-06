import api from "../lib/api";

// ---------- REGENERATE MASTER PRACTICAL TIMETABLE ----------
export const regenerateMasterTimetable = async () => {
  try {
    // Generation is CPU-heavy and can take longer than default API timeout.
    const res = await api.post("/regenerate_master_practical_timetable", null, {
      timeout: 120000,
    });
    return res.data;
  } catch (err) {
    console.error("Error regenerating timetable:", err.response?.data || err);
    throw err;
  }
};
