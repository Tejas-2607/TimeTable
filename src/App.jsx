import React, { useState } from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import InputForm from './components/InputForm';
import Report from './components/Report';
import TimetableView from './components/TimetableView';

export default function App() {
  // Central state for the entire application
  const [departments, setDepartments] = useState([]);
  const [faculties, setFaculties] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [labs, setLabs] = useState([]);
  const [facultyUnavailability, setFacultyUnavailability] = useState({});
  const [generatedTimetable, setGeneratedTimetable] = useState(null);
  const [jointConstraints, setJointConstraints] = useState([]);

  return (
    <div className="min-h-screen bg-gray-100 text-gray-800">
      <header className="bg-white shadow-md">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-indigo-700">Smart Timetable Generator 🗓️</h1>
            <p className="text-gray-600 mt-1">An advanced tool for creating conflict-free academic schedules.</p>
          </div>
          <nav className="space-x-4">
            <Link to="/" className="text-indigo-600 hover:underline">Input Form</Link>
            <Link to="/report" className="text-indigo-600 hover:underline">Configuration Report</Link>
          </nav>
        </div>
      </header>
      
      <Routes>
        <Route 
          path="/" 
          element={
            <InputForm 
              departments={departments} setDepartments={setDepartments}
              faculties={faculties} setFaculties={setFaculties}
              subjects={subjects} setSubjects={setSubjects}
              labs={labs} setLabs={setLabs}
              jointConstraints={jointConstraints} setJointConstraints={setJointConstraints}
            />
          } 
        />
        <Route 
          path="/report" 
          element={
            <Report 
              departments={departments} setDepartments={setDepartments}
              faculties={faculties} setFaculties={setFaculties}
              subjects={subjects} setSubjects={setSubjects}
              labs={labs} setLabs={setLabs}
              facultyUnavailability={facultyUnavailability} setFacultyUnavailability={setFacultyUnavailability}
              setGeneratedTimetable={setGeneratedTimetable}
              jointConstraints={jointConstraints}
            />
          } 
        />
        <Route
          path="/timetable"
          element={ <TimetableView config={{ departments, faculties, subjects, labs, facultyUnavailability, jointConstraints }} timetable={generatedTimetable} /> }
        />
      </Routes>
    </div>
  );
}