// src/services/subjectService.js
import api from '../lib/api';

// ---------- GET ALL SUBJECTS ----------
export const getSubjects = async () => {
  try {
    const res = await api.get('/subjects');
    console.log(res);
    
    return res;
  } catch (err) {
    console.error("Error fetching subjects:", err);
    throw err;
  }
};

// ---------- ADD NEW SUBJECT ----------
export const addSubject = async (subjectData) => {
  try {
    const res = await api.post('/subjects', subjectData);
    return res.data;
  } catch (err) {
    console.error("Error adding subject:", err.response?.data || err);
    throw err;
  }
};

// ---------- UPDATE SUBJECT ----------
export const updateSubject = async (subjectData) => {
  try {
    const res = await api.put('/subjects', subjectData);
    return res.data;
  } catch (err) {
    console.error("Error updating subject:", err.response?.data || err);
    throw err;
  }
};

// ---------- DELETE SUBJECT ----------
export const deleteSubject = async (year, id) => {
  try {
    const res = await api.delete('/subjects', {
      data: { id, year },
    });
    return res.data;
  } catch (err) {
    console.error("Error deleting subject:", err.response?.data || err);
    throw err;
  }
};
