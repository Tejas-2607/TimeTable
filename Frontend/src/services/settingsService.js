// src/services/settingsService.js
import api from "../lib/api";

export const getDepartmentTimings = async () => {
  const res = await api.get("/settings/timings");
  return res.data;
};

export const saveDepartmentTimings = async (timings) => {
  const res = await api.post("/settings/timings", timings);
  return res.data;
};
