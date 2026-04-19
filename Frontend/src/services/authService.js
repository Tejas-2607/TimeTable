// src/services/authService.js
import api from '../lib/api';

/**
 * Authenticate user (Unified Login/Registration)
 * @param {Object} credentials - { email, password, name, short_name }
 */
export const authenticate = async (credentials) => {
    try {
        const response = await api.post('/auth/authenticate', credentials);
        return response;
    } catch (error) {
        console.error('Authentication Error:', error.response?.data || error.message);
        throw error;
    }
};

/**
 * Handle Logout
 */
export const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
};

/**
 * Get current user from storage
 */
export const getCurrentUser = () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
};

/**
 * Get token from storage
 */
export const getToken = () => {
    return localStorage.getItem('token');
};
