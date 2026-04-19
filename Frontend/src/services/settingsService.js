import api from '../lib/api';

export const getDepartmentTimings = async () => {
    try {
        const res = await api.get('/settings/timings');
        return res;
    } catch (err) {
        console.error('Error fetching department timings:', err);
        throw err;
    }
};

export const saveDepartmentTimings = async (timings) => {
    try {
        const res = await api.post('/settings/timings', timings);
        return res;
    } catch (err) {
        console.error('Error saving department timings:', err);
        throw err;
    }
};
