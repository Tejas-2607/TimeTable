// src/services/classStructureService.js
import api from '../lib/api';

// ✅ Save the full class structure
export const saveClassStructure = async (structureData) => {
  try {
    const response = await api.post('/class_structure', structureData);
    return response.data;
  } catch (error) {
    console.error('API Error (saveClassStructure):', error);
    throw error;
  }
};

// ✅ Fetch the saved class structure
export const getClassStructure = async () => {
  try {
    const response = await api.get('/class_structure');
        console.log("Backend Response:", response);
    return response;
  } catch (error) {
    console.error('API Error (getClassStructure):', error);
    throw error;
  }
};
