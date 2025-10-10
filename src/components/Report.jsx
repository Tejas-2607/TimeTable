import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Report({ departments, faculties, subjects, labs, facultyUnavailability, setFacultyUnavailability, setGeneratedTimetable, jointConstraints }) {
    const navigate = useNavigate();
    const [selectedDeptName, setSelectedDeptName] = useState('');
    const [timingGridVisibleFor, setTimingGridVisibleFor] = useState(null); // State to track which grid is open

    useEffect(() => {
        if (departments.length > 0 && !selectedDeptName) {
            setSelectedDeptName(departments[0].name);
        }
    }, [departments, selectedDeptName]);

    // Handler to toggle a slot's availability
    const handleSlotToggle = (facultyId, day, slot) => {
        const slotIdentifier = `${slot.start}-${slot.end}`;
        const currentUnavailability = facultyUnavailability[facultyId] || {};
        const dayUnavailability = currentUnavailability[day] || [];

        const newDayUnavailability = dayUnavailability.includes(slotIdentifier)
            ? dayUnavailability.filter(s => s !== slotIdentifier) // Make available
            : [...dayUnavailability, slotIdentifier]; // Make unavailable

        setFacultyUnavailability({
            ...facultyUnavailability,
            [facultyId]: {
                ...currentUnavailability,
                [day]: newDayUnavailability,
            },
        });
    };

    // Filter data based on the selected department
    const selectedDeptData = departments.find(d => d.name === selectedDeptName);
    const filteredSubjects = subjects.filter(s => s.department === selectedDeptName);
    const filteredFaculty = faculties.filter(f => f.department === selectedDeptName);
    const filteredConstraints = jointConstraints.filter(c => c.department === selectedDeptName);
    const subjectsByYear = { '2': filteredSubjects.filter(s => s.year === '2'), '3': filteredSubjects.filter(s => s.year === '3'), '4': filteredSubjects.filter(s => s.year === '4') };

    const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

    if (departments.length === 0) {
        return <main className="container mx-auto p-8 text-center"><h2 className="text-2xl">No data to report. Please add a department and its timings first.</h2></main>;
    }

    return (
        <main className="container mx-auto px-6 py-8">
            <div className="mb-6 flex justify-between items-center">
                <div><label htmlFor="dept-select" className="mr-2 font-semibold">Viewing Report For:</label><select id="dept-select" value={selectedDeptName} onChange={e => setSelectedDeptName(e.target.value)} className="p-2 border rounded-md">{departments.map(d => <option key={d.name} value={d.name}>{d.name}</option>)}</select></div>
                <button onClick={() => navigate('/timetable')} className="bg-blue-600 text-white font-bold py-2 px-4 rounded-md hover:bg-blue-700">Generate Time Table</button>
            </div>

            {/* BOX 1, 2, 3 and Constraints (Unchanged) */}
            {selectedDeptData && <section className="bg-white p-6 rounded-lg shadow mb-8"><h2 className="text-2xl font-bold text-indigo-700">{selectedDeptData.name}</h2><p className="text-gray-600">Timings: {selectedDeptData.startTime} – {selectedDeptData.endTime} | Lecture Duration: <span className="font-semibold">{selectedDeptData.lectureDuration} mins</span></p><div className="flex space-x-2 overflow-x-auto p-2 mt-2 bg-gray-50 rounded">{selectedDeptData.timeSlots['Monday'].map((slot, i) => <div key={i} className={`p-2 rounded-md text-center flex-shrink-0 w-28 ${slot.type === 'break' ? 'bg-yellow-200' : 'bg-indigo-100'}`}><p className="font-semibold text-sm">{slot.start}-{slot.end}</p><p className="text-xs">{slot.name || 'Lecture'}</p></div>)}</div></section>}
            <section className="bg-white p-6 rounded-lg shadow mb-8"><h2 className="text-xl font-semibold mb-4 border-b pb-2">Subjects</h2><div className="grid grid-cols-1 md:grid-cols-3 gap-6">{['2', '3', '4'].map(year => ( <div key={year}><h3 className="font-bold text-lg mb-2">{year === '2' ? 'SY' : year === '3' ? 'TY' : 'Final Year'}</h3><div className="space-y-2">{subjectsByYear[year].map(s => <div key={s.id} className="p-2 bg-gray-50 rounded text-sm"><p className="font-bold">{s.shortForm} - {s.name}</p></div>)}</div></div>))}</div></section>
            <section className="bg-white p-6 rounded-lg shadow mb-8"><h2 className="text-xl font-semibold mb-4 border-b pb-2">Lab Assignments</h2><div className="grid grid-cols-1 md:grid-cols-2 gap-4">{labs.map(lab => (<div key={lab.id} className="p-3 bg-gray-50 rounded"><h3 className="font-bold">{lab.name} ({lab.shortForm})</h3><ul className="list-disc list-inside text-sm mt-1">{subjects.filter(s => s.practicalDetails?.lab === lab.shortForm).map(s => <li key={s.id}>{s.shortForm}</li>)}</ul></div>))}</div></section>
            <section className="bg-white p-6 rounded-lg shadow mb-8"><h2 className="text-xl font-semibold mb-4 border-b pb-2">Scheduling Constraints</h2><div className="space-y-3">{filteredConstraints.length > 0 ? filteredConstraints.map(c => (<div key={c.id} className="p-3 bg-gray-50 rounded-lg border"><p className="font-bold capitalize">{c.type}: <span className="text-indigo-600">{c.subjectShortForm}</span> for Year {c.year}</p></div>)) : <p className="text-gray-500">No joint subject constraints defined.</p>}</div></section>

            {/* BOX 4: Faculty List with NEW Timings Grid */}
            <section className="bg-white p-6 rounded-lg shadow mb-8">
                <h2 className="text-xl font-semibold mb-4 border-b pb-2">Faculty in {selectedDeptName}</h2>
                <div className="space-y-4">
                    {filteredFaculty.map(faculty => (
                        <div key={faculty.id} className="p-4 bg-gradient-to-br from-indigo-50 to-blue-50 rounded-lg shadow-sm border border-indigo-100">
                            <div className="flex justify-between items-start">
                                <div>
                                    <h3 className="font-bold text-lg text-indigo-800">{faculty.title} {faculty.name}</h3>
                                    <div className="mt-2"><h4 className="font-semibold text-sm">Subjects:</h4>{Object.entries(faculty.subjectsByYear).map(([year, subjectList]) => (<p key={year} className="text-sm"><span className="font-medium">Year {year}:</span> {subjectList.join(', ')}</p>))}</div>
                                </div>
                                <button onClick={() => setTimingGridVisibleFor(timingGridVisibleFor === faculty.id ? null : faculty.id)} className="bg-white text-indigo-600 px-3 py-1 border border-indigo-300 rounded-full text-sm hover:bg-indigo-100">
                                    {timingGridVisibleFor === faculty.id ? 'Close Timings' : 'Set Timings'}
                                </button>
                            </div>
                            
                            {/* --- The Timings Grid --- */}
                            {timingGridVisibleFor === faculty.id && selectedDeptData && (
                                <div className="mt-4 pt-4 border-t border-indigo-200 overflow-x-auto">
                                    <div className="grid grid-cols-6 gap-1 text-center font-bold text-sm">
                                        <div className="p-2">Time</div>
                                        {weekDays.map(day => <div key={day} className="p-2">{day}</div>)}
                                    </div>
                                    {selectedDeptData.timeSlots['Monday'].map((slot, slotIndex) => (
                                        <div key={slotIndex} className="grid grid-cols-6 gap-1 text-center text-sm items-center">
                                            <div className="p-2 font-semibold bg-gray-100 rounded-l-md">{slot.type === 'break' ? slot.name : `${slot.start} - ${slot.end}`}</div>
                                            {weekDays.map(day => {
                                                if (slot.type === 'break') {
                                                    return <div key={day} className="bg-yellow-200 h-full flex items-center justify-center">Break</div>;
                                                }
                                                const slotIdentifier = `${slot.start}-${slot.end}`;
                                                const isUnavailable = facultyUnavailability[faculty.id]?.[day]?.includes(slotIdentifier);
                                                return (
                                                    <button 
                                                        key={day} 
                                                        onClick={() => handleSlotToggle(faculty.id, day, slot)}
                                                        className={`p-2 h-full rounded-md transition-colors ${isUnavailable ? 'bg-red-500 hover:bg-red-600 text-white' : 'bg-green-400 hover:bg-green-500 text-white'}`}
                                                    >
                                                        {isUnavailable ? 'Unavailable' : 'Available'}
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </section>
        </main>
    );
}