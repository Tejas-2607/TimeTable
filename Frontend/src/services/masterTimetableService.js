import api from "../lib/api";

// ---------- GET ALL MASTER TIMETABLES ----------
export const getMasterTimetables = async (filters = {}) => {
  try {
    const res = await api.get("/master_timetables", { params: filters });
    return res.data;
  } catch (err) {
    console.error("Error fetching master timetables:", err);
    throw err;
  }
};

// ---------- GET TIMETABLES BY YEAR ----------
export const getTimetablesByYear = async (year) => {
  try {
    const res = await api.get("/master_timetables", { params: { year } });
    return res.data;
  } catch (err) {
    console.error("Error fetching timetables by year:", err);
    throw err;
  }
};

export const deleteMasterTimetable = async (id) => {
  try {
    const res = await api.delete(`/master_timetables/${id}`);
    return res.data;
  } catch (err) {
    console.error(
      "Error deleting master practical timetable:",
      err.response?.data || err,
    );
    throw err;
  }
};

export const deleteMasterTimetableByLab = async (labName) => {
  try {
    const res = await api.delete(
      `/master_timetables/lab/${encodeURIComponent(labName)}`,
    );
    return res.data;
  } catch (err) {
    console.error(
      "Error deleting master practical timetable by lab:",
      err.response?.data || err,
    );
    throw err;
  }
};
