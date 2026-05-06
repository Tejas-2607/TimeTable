import api from "../lib/api";

// ---------- GET ALL CLASS TIMETABLES ----------
export const getClassTimetables = async () => {
  try {
    const res = await api.get("/class_timetables");
    return res.data;
  } catch (err) {
    console.error("Error fetching class timetables:", err);
    throw err;
  }
};

export const deleteClassTimetable = async (id) => {
  try {
    const res = await api.delete(`/class_timetables/${id}`);
    return res.data;
  } catch (err) {
    console.error("Error deleting class timetable:", err.response?.data || err);
    throw err;
  }
};

export const deleteFacultyTimetable = async (facultyShortName) => {
  try {
    const res = await api.delete(
      `/faculty_timetables/${encodeURIComponent(facultyShortName)}`,
    );
    return res.data;
  } catch (err) {
    console.error("Error deleting faculty timetable:", err.response?.data || err);
    throw err;
  }
};

export const deleteLabTimetable = async (labName) => {
  try {
    const res = await api.delete(`/lab_timetables/${encodeURIComponent(labName)}`);
    return res.data;
  } catch (err) {
    console.error("Error deleting lab timetable:", err.response?.data || err);
    throw err;
  }
};
