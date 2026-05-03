// src/services/authService.js
import api from "../lib/api";

/**
 * Unified Login / Registration.
 * @param {{ email, password, name?, short_name? }} credentials
 */
export const authenticate = async (credentials) => {
  const response = await api.post("/auth/authenticate", credentials);
  return response.data;
};

export const resetPassword = async (resetData) => {
  const response = await api.post("/auth/reset-password", resetData);
  return response.data;
};

export const logout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  window.location.href = "/login";
};

export const getCurrentUser = () => {
  const user = localStorage.getItem("user");
  return user ? JSON.parse(user) : null;
};

export const getToken = () => localStorage.getItem("token");
