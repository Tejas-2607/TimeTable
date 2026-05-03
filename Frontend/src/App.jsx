// src/App.jsx
import { useState } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";
import Sidebar from "./components/Sidebar";
import GenerateTimetable from "./components/GenerateTimetable";
import FacultyData from "./components/FacultyData";
import LabsData from "./components/LabsData";
import ClassStructure from "./components/ClassStructure";
import ViewTimetables from "./components/ViewTimetables";
import FacultyTimetables from "./components/FacultyTimetables";
import SpecialConstraints from "./components/SpecialConstraints";
import Login from "./components/Login";
import ResetPassword from "./components/ResetPassword";
import { AuthProvider, useAuth } from "./context/AuthContext";

// ── Protected route wrapper ────────────────────────────────────────────────

const ProtectedRoute = ({ children, requiredRole }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-slate-50">
        <div className="w-12 h-12 border-4 border-blue-600/30 border-t-blue-600 rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user.role?.toLowerCase() !== requiredRole.toLowerCase()) {
    return (
      <Navigate
        to={user.role?.toLowerCase() === "admin" ? "/generate" : "/view"}
        replace
      />
    );
  }

  return children;
};

// ── Inner layout (needs router context for useLocation) ───────────────────

function AppContent() {
  const [activeTab, setActiveTab] = useState("generate");
  const { user } = useAuth();
  const location = useLocation();

  const showSidebar = user && location.pathname !== "/login" && location.pathname !== "/reset-password";

  return (
    <div className="flex h-screen bg-slate-50 font-sans overflow-hidden">
      {showSidebar && (
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      )}
      <main className="flex-1 h-full overflow-y-auto overflow-x-hidden">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/reset-password" element={<ResetPassword />} />

          {/* Root: redirect based on role */}
          <Route
            path="/"
            element={
              user ? (
                <Navigate
                  to={
                    user.role?.toLowerCase() === "admin" ? "/generate" : "/view"
                  }
                  replace
                />
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />

          {/* Admin-only */}
          <Route
            path="/generate"
            element={
              <ProtectedRoute requiredRole="admin">
                <GenerateTimetable />
              </ProtectedRoute>
            }
          />
          <Route
            path="/faculty"
            element={
              <ProtectedRoute requiredRole="admin">
                <FacultyData />
              </ProtectedRoute>
            }
          />
          <Route
            path="/labs"
            element={
              <ProtectedRoute requiredRole="admin">
                <LabsData />
              </ProtectedRoute>
            }
          />
          <Route
            path="/structure"
            element={
              <ProtectedRoute requiredRole="admin">
                <ClassStructure />
              </ProtectedRoute>
            }
          />

          {/* Any authenticated user */}
          <Route
            path="/view"
            element={
              <ProtectedRoute>
                <ViewTimetables />
              </ProtectedRoute>
            }
          />
          <Route
            path="/view/:tab"
            element={
              <ProtectedRoute>
                <ViewTimetables />
              </ProtectedRoute>
            }
          />
          <Route
            path="/faculty_timetables"
            element={
              <ProtectedRoute>
                <FacultyTimetables />
              </ProtectedRoute>
            }
          />
          <Route
            path="/constraints"
            element={
              <ProtectedRoute>
                <SpecialConstraints />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </div>
  );
}

// ── Root App ──────────────────────────────────────────────────────────────

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}
