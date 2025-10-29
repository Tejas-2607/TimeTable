import api from '../lib/api';

// ---------- GET ALL FACULTY WORKLOADS ----------
export const getFacultyWorkload = async () => {
  try {
    const res = await api.get('/faculty_workload');
    console.log(res);
    
    return res;
  } catch (err) {
    console.error('Error fetching faculty workloads:', err);
    throw err;
  }
};

// ---------- ADD NEW FACULTY WORKLOAD ----------
export const addFacultyWorkload = async (workloadData) => {
  try {
    const res = await api.post('/faculty_workload', workloadData);
    return res;
  } catch (err) {
    console.error('Error adding faculty workload:', err.response?.data || err);
    throw err;
  }
};

// ---------- UPDATE FACULTY WORKLOAD ----------
export const updateFacultyWorkload = async (workloadData) => {
  try {
    const res = await api.put('/faculty_workload', workloadData);
    return res;
  } catch (err) {
    console.error('Error updating faculty workload:', err.response?.data || err);
    throw err;
  }
};

// ---------- DELETE FACULTY WORKLOAD ----------
export const deleteFacultyWorkload = async (id) => {
  try {
    const res = await api.delete('/faculty_workload', {
      data: { _id: id },
    });
    return res;
  } catch (err) {
    console.error('Error deleting faculty workload:', err.response?.data || err);
    throw err;
  }
};