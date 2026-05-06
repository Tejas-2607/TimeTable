// src/services/subjectService.js
import api from "../lib/api";

// ---------- GET ALL SUBJECTS ----------
export const getSubjects = async () => {
  try {
    const res = await api.get("/subjects");
    return res.data;
  } catch (err) {
    console.error("Error fetching subjects:", err);
    throw err;
  }
};

// ---------- ADD NEW SUBJECT ----------
export const addSubject = async (subjectData) => {
  try {
    if (subjectData && subjectData.id) {
      console.warn(
        "addSubject called with id — this should not happen. Use updateSubject for edits.",
        subjectData
      );
      throw new Error(
        "Invalid call: addSubject should not receive an id. Use updateSubject() instead."
      );
    }

    console.log("Calling POST /api/subjects to add new subject");
    const res = await api.post("/subjects", subjectData);
    return res.data;
  } catch (err) {
    console.error("Error adding subject:", err.response?.data || err);
    throw err;
  }
};

// ---------- UPDATE SUBJECT (PUT) ----------
export const updateSubject = async (subjectData) => {
  try {
    if (!subjectData || !subjectData.id) {
      throw new Error("Subject ID is required for update");
    }

    const subjectId = String(subjectData.id);
    console.log("Calling PUT /api/subjects to update subject", {
      id: subjectId,
    });

    // Primary contract: resource-specific endpoint
    try {
      const res = await api.put(`/subjects/${subjectId}`, subjectData);
      return res.data;
    } catch (err) {
      // Backward compatibility for older backend route shape
      if (err.response?.status === 404) {
        const fallbackRes = await api.put("/subjects", subjectData);
        return fallbackRes.data;
      }
      throw err;
    }
  } catch (err) {
    console.error("Error updating subject:", err.response?.data || err);
    throw err;
  }
};

// ---------- DELETE SUBJECT ----------
export const deleteSubject = async (year, id) => {
  try {
    const subjectId = String(id);

    // Primary contract: id in path, year in query params
    try {
      const res = await api.delete(`/subjects/${subjectId}`, {
        params: { year },
      });
      return res.data;
    } catch (err) {
      // Backward compatibility for older backend route shape
      if (err.response?.status === 404) {
        const fallbackRes = await api.delete("/subjects", {
          params: { id: subjectId, year },
        });
        return fallbackRes.data;
      }
      throw err;
    }
  } catch (err) {
    console.error("Error deleting subject:", err.response?.data || err);
    throw err;
  }
};
