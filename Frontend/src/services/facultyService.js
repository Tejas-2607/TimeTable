// src/services/facultyService.js
import api from '../lib/api';

// ✅ Get all faculties
export const getFaculties = async () => {
  return await api.get('/faculty');
};

// ✅ Add new faculty
export const createFaculty = async (facultyData) => {
  return await api.post('/faculty', facultyData);
};

// ✅ Update faculty by ID
export const updateFaculty = async (id, facultyData) => {
  return await api.put(`/faculty`, {
    _id: id,
    updates: facultyData
  });
};

// ✅ Delete faculty by ID
export const deleteFaculty = async (id) => {
  return await api.delete(`/faculty`, { data: id });
};
