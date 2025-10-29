import { useState } from 'react';
import Sidebar from './components/Sidebar';
import GenerateTimetable from './components/GenerateTimetable';
import FacultyData from './components/FacultyData';
import LabsData from './components/LabsData';
import ClassStructure from './components/ClassStructure';
import ViewTimetables from './components/ViewTimetables';
import PracticalPlan from './components/PracticalPlan';

function App() {
  const [activeTab, setActiveTab] = useState('generate');

  const renderContent = () => {
    switch (activeTab) {
      case 'generate':
        return <GenerateTimetable />;
      case 'faculty':
        return <FacultyData />;
      case 'labs':
        return <LabsData />;
      case 'structure':
        return <ClassStructure />;
      case 'view':
        return <ViewTimetables />;
      case 'practical':
        return <PracticalPlan />;
      default:
        return <GenerateTimetable />;
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-100">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="flex-1 overflow-auto">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;
