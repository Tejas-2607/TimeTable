import api from '../lib/api';

// ---------- REGENERATE MASTER PRACTICAL TIMETABLE ----------
export const regenerateMasterTimetable = async () => {
  try {
    const res = await api.post('/regenerate_master_practical_timetable');
    return res;
  } catch (err) {
    console.error('Error regenerating timetable:', err.response?.data || err);
    throw err;
  }
};