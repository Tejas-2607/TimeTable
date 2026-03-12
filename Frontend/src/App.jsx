import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import GenerateTimetable from './components/GenerateTimetable';
import FacultyData from './components/FacultyData';
import LabsData from './components/LabsData';
import ClassStructure from './components/ClassStructure';
import ViewTimetables from './components/ViewTimetables';
import PracticalPlan from './components/PracticalPlan';

function App() {
  const [activeTab, setActiveTab] = useState('generate');

  return (
    <Router>
      <div className="flex h-screen bg-slate-50 font-sans overflow-hidden">
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
        <main className="flex-1 h-full overflow-y-auto overflow-x-hidden">
          <Routes>
            <Route path="/" element={<Navigate to="/generate" replace />} />
            <Route path="/generate" element={<GenerateTimetable />} />
            <Route path="/faculty" element={<FacultyData />} />
            <Route path="/labs" element={<LabsData />} />
            <Route path="/structure" element={<ClassStructure />} />
            <Route path="/view" element={<ViewTimetables />} />
            <Route path="/practical" element={<PracticalPlan />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
