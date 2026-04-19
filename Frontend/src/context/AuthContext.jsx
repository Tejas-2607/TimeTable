// src/context/AuthContext.jsx
import { createContext, useContext, useState, useEffect } from 'react';
import { authenticate, getCurrentUser, getToken } from '../services/authService';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(getCurrentUser());
    const [token, setToken] = useState(getToken());
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check if user session is valid
        const storedUser = getCurrentUser();
        const storedToken = getToken();
        if (storedUser && storedToken) {
            setUser(storedUser);
            setToken(storedToken);
        }
        setLoading(false);
    }, []);

    const login = async (credentials) => {
        try {
            const data = await authenticate(credentials);
            if (data && data.token) {
                localStorage.setItem('token', data.token);
                localStorage.setItem('user', JSON.stringify(data.user));
                setUser(data.user);
                setToken(data.token);
                return data.user;
            }
        } catch (error) {
            throw error;
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
        setToken(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
