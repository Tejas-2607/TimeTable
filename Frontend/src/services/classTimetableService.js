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
// ---------- DELETE CLASS TIMETABLE ----------
export const deleteClassTimetable = async (className, division) => {
  try {
    const res = await api.delete(`/class_timetable/${className}/${division}`);
    return res;
  } catch (err) {
    console.error(`Error deleting timetable for ${className}-${division}:`, err);
    throw err;
  }
};
