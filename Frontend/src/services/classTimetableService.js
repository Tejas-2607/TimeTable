import api from '../lib/api';

// ---------- GET ALL CLASS TIMETABLES ----------
export const getClassTimetables = async () => {
  try {
    const res = await api.get('/class_timetables');
    return res;
  } catch (err) {
    console.error('Error fetching class timetables:', err);
    throw err;
  }
};
