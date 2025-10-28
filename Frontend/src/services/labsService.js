import api from '../lib/api'; // <-- your axios instance

// ✅ Fetch all labs
export const getAllLabs = async () => {
  return await api.get('/labs');
};

// ✅ Add a new lab
export const addLab = async (labData) => {
  return await api.post('/labs', labData);
};

// ✅ Update existing lab
export const updateLab = async (id, labData) => {
  return await api.put('/labs', {
    _id: id,
    updates: labData,
  });
};

// ✅ Delete lab by ID
export const deleteLab = async (id) => {
  return await api.delete(`/labs`,  { data: id });
};
