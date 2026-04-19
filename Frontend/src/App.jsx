import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import GenerateTimetable from './components/GenerateTimetable';
import FacultyData from './components/FacultyData';
import LabsData from './components/LabsData';
import ClassStructure from './components/ClassStructure';
import ViewTimetables from './components/ViewTimetables';
import FacultyTimetables from './components/FacultyTimetables';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './components/Login';
import SpecialConstraints from './components/SpecialConstraints';

const ProtectedRoute = ({ children, requiredRole }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-slate-50">
        <div className="w-12 h-12 border-4 border-blue-600/30 border-t-blue-600 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to={user.role === 'admin' ? '/generate' : '/view'} replace />;
  }

  return children;
};

function AppContent() {
  const [activeTab, setActiveTab] = useState('generate');
  const { user } = useAuth();
  const location = useLocation();

  const showSidebar = user && location.pathname !== '/login';

  return (
    <div className="flex h-screen bg-slate-50 font-sans overflow-hidden">
      {showSidebar && <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />}
      <main className="flex-1 h-full overflow-y-auto overflow-x-hidden">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              user ? (
                <Navigate to={user.role === 'admin' ? "/generate" : "/view"} replace />
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />
          <Route path="/generate" element={<ProtectedRoute requiredRole="admin"><GenerateTimetable /></ProtectedRoute>} />
          <Route path="/faculty" element={<ProtectedRoute requiredRole="admin"><FacultyData /></ProtectedRoute>} />
          <Route path="/labs" element={<ProtectedRoute requiredRole="admin"><LabsData /></ProtectedRoute>} />
          <Route path="/structure" element={<ProtectedRoute requiredRole="admin"><ClassStructure /></ProtectedRoute>} />
          <Route path="/view" element={<ProtectedRoute><ViewTimetables /></ProtectedRoute>} />
          <Route path="/faculty_timetables" element={<ProtectedRoute><FacultyTimetables /></ProtectedRoute>} />
          <Route path="/constraints" element={<ProtectedRoute><SpecialConstraints /></ProtectedRoute>} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;
