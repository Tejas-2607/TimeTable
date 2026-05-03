// src/context/AuthContext.jsx
import { createContext, useContext, useState, useEffect } from "react";
import { authenticate as apiAuthenticate } from "../services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Restore session from localStorage on mount
  useEffect(() => {
    try {
      const storedToken = localStorage.getItem("token");
      const storedUser = localStorage.getItem("user");
      if (storedToken && storedUser) {
        const parsedUser = JSON.parse(storedUser);
        setToken(storedToken);
        setUser({
          ...parsedUser,
          role: parsedUser.role?.toLowerCase(),
        });
      }
    } catch (e) {
      console.error("Failed to restore session:", e);
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    } finally {
      setLoading(false);
    }
  }, []);

  const login = async (credentials) => {
    const response = await apiAuthenticate(credentials);
    const { token: newToken, user: newUser } = response || {};
    if (!newToken || !newUser) {
      throw new Error("Invalid authentication response from server.");
    }
    const normalizedUser = {
      ...newUser,
      role: newUser.role?.toLowerCase(),
    };
    localStorage.setItem("token", newToken);
    localStorage.setItem("user", JSON.stringify(normalizedUser));
    setToken(newToken);
    setUser(normalizedUser);
    return response;
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
