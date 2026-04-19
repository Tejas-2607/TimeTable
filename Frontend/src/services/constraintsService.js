// src/services/constraintsService.js

const API_BASE_URL = 'http://localhost:5001/api';

const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
};

export const getConstraints = async () => {
    const response = await fetch(`${API_BASE_URL}/constraints`, {
        headers: getAuthHeaders()
    });
    if (!response.ok) {
        throw new Error('Failed to fetch constraints');
    }
    return response.json();
};

export const addConstraint = async (constraintData) => {
    const response = await fetch(`${API_BASE_URL}/constraints`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(constraintData)
    });
    if (!response.ok) {
        throw new Error('Failed to add constraint');
    }
    return response.json();
};

export const deleteConstraint = async (constraintId) => {
    const response = await fetch(`${API_BASE_URL}/constraints/${constraintId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
    });
    if (!response.ok) {
        throw new Error('Failed to delete constraint');
    }
    return response.json();
};
