import api from '../lib/api';

// ---------- GET ALL MASTER TIMETABLES ----------
export const getMasterTimetables = async (filters = {}) => {
  try {
    const res = await api.get('/master_timetables', { params: filters });
    return res;
  } catch (err) {
    console.error('Error fetching master timetables:', err);
    throw err;
  }
};

// ---------- DELETE MASTER TIMETABLE ----------
export const deleteMasterTimetable = async (labName) => {
  try {
    const res = await api.delete(`/master_timetable/${labName}`);
    return res;
  } catch (err) {
    console.error(`Error deleting master timetable for ${labName}:`, err);
    throw err;
  }
};

// ---------- GET TIMETABLES BY YEAR ----------
export const getTimetablesByYear = async (year) => {
  try {
    const res = await api.get('/master_timetables', { params: { year } });
    return res;
  } catch (err) {
    console.error('Error fetching timetables by year:', err);
    throw err;
  }
};