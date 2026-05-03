// src/services/constraintsService.js
// Uses the shared api.js axios instance — token is attached automatically
// by the existing request interceptor (localStorage.getItem('token')).
import api from "../lib/api";

export const getConstraints = async () => {
  const res = await api.get("/constraints");
  return res.data;
};

export const addConstraint = async (constraintData) => {
  const res = await api.post("/constraints", constraintData);
  return res.data;
};

export const deleteConstraint = async (constraintId) => {
  const res = await api.delete(`/constraints/${constraintId}`);
  return res.data;
};
