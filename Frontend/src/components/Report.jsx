import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Report({ departments, faculties, subjects, labs, facultyUnavailability, setFacultyUnavailability, setGeneratedTimetable, classStructure, subjectConstraints = [] }) {
    const navigate = useNavigate();
    const [selectedDeptName, setSelectedDeptName] = useState('');
    const [timingGridVisibleFor, setTimingGridVisibleFor] = useState(null);

    useEffect(() => {
        if (departments.length > 0 && !selectedDeptName) {
            setSelectedDeptName(departments[0].name);
        }
    }, [departments, selectedDeptName]);

    const handleSlotToggle = (facultyId, day, slot) => {
        const slotIdentifier = `${slot.start}-${slot.end}`;
        setFacultyUnavailability(prevUnavailability => {
            const currentUnavailability = prevUnavailability[facultyId] || {};
            const dayUnavailability = currentUnavailability[day] || [];
            const newDayUnavailability = dayUnavailability.includes(slotIdentifier)
                ? dayUnavailability.filter(s => s !== slotIdentifier)
                : [...dayUnavailability, slotIdentifier];
            return {
                ...prevUnavailability,
                [facultyId]: {
                    ...currentUnavailability,
                    [day]: newDayUnavailability,
                },
            };
        });
    };

    const getPracticalInfo = (details) => {
        if (!details) return null;
        switch (details.type) {
            case 'specific_lab':
                return `Requires Lab(s): ${details.labs && details.labs.length > 0 ? details.labs.join(', ') : 'Any'}`;
            case 'classroom_only':
                return 'Requires Classroom (No Lab)';
            case 'no_room_last_slots':
                return <span className="font-semibold text-red-600">No Room (Schedule Last)</span>;
            default:
                return 'Practical';
        }
    };

    // Filter data based on the selected department
    const selectedDeptData = departments.find(d => d.name === selectedDeptName);
    const filteredSubjects = subjects.filter(s => s.department === selectedDeptName);
    const filteredFaculty = faculties.filter(f => f.department === selectedDeptName);
    const filteredConstraints = subjectConstraints.filter(c => c.department === selectedDeptName);
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

            {/* BOX 1: Department Details */}
            {selectedDeptData && <section className="bg-white p-6 rounded-lg shadow mb-8">
                <h2 className="text-2xl font-bold text-indigo-700">{selectedDeptData.name}</h2>
                <div className="text-sm text-gray-600 mt-2 grid grid-cols-2 md:grid-cols-4 gap-2">
                    <p><strong>Start Time:</strong> {selectedDeptData.startTime}</p>
                    <p><strong>End Time:</strong> {selectedDeptData.endTime}</p>
                    <p><strong>Break:</strong> {selectedDeptData.breakInfo.name} at {selectedDeptData.breakInfo.startTime}</p>
                    <p><strong>Lecture Duration:</strong> {selectedDeptData.lectureDuration} mins</p>
                </div>
                {/* --- FIX IS APPLIED HERE --- */}
                <div className="border-t mt-4 pt-4">
                    <h3 className="font-semibold mb-2">Class Structure</h3>
                    <div className="flex justify-around text-center">
                        {Object.entries(classStructure).map(([year, data]) => (
                            <div key={year}>
                                <p className="font-bold">{year === '2' ? 'SY' : year === '3' ? 'TY' : 'Final'}</p>
                                <p className="text-sm">{data.divisions} Divs &times; {data.batchesPerDivision} Batches/Div = <span className="font-bold">{data.divisions * data.batchesPerDivision} Total Batches</span></p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>}

            {/* BOX 2: Subjects by Year */}
            <section className="bg-white p-6 rounded-lg shadow mb-8">
                <h2 className="text-xl font-semibold mb-4 border-b pb-2">Subjects</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {['2', '3', '4'].map(year => (
                        <div key={year}>
                            <h3 className="font-bold text-lg mb-2">{year === '2' ? 'Second Year (SY)' : year === '3' ? 'Third Year (TY)' : 'Final Year'}</h3>
                            <div className="space-y-2">
                                {subjectsByYear[year].map(s => <div key={s.id} className="p-2 bg-gray-50 rounded text-sm"><p className="font-bold">{s.shortForm} - {s.name}</p><p className="text-xs text-gray-600">Lec/wk: {s.workload.lectures}, Prac/wk: {s.workload.practicals}</p>{s.classType !== 'theory' && <p className="text-xs text-blue-600">{getPracticalInfo(s.practicalDetails)}</p>}</div>)}
                            </div>
                        </div>
                    ))}
                </div>
            </section>
            
            {/* BOX 3: Lab Assignments */}
            <section className="bg-white p-6 rounded-lg shadow mb-8">
                <h2 className="text-xl font-semibold mb-4 border-b pb-2">Lab Assignments</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {labs.map(lab => (
                        <div key={lab.id} className="p-3 bg-gray-50 rounded">
                            <h3 className="font-bold">{lab.name} ({lab.shortForm})</h3>
                            <ul className="list-disc list-inside text-sm mt-1">
                                {subjects
                                    .filter(s => s.practicalDetails?.labs?.includes(lab.shortForm))
                                    .map(s => <li key={s.id}>{s.shortForm}</li>)}
                            </ul>
                        </div>
                    ))}
                </div>
            </section>

            {/* BOX 4: Subject Constraints */}
            <section className="bg-white p-6 rounded-lg shadow mb-8">
                <h2 className="text-xl font-semibold mb-4 border-b pb-2">Scheduling Constraints</h2>
                <div className="space-y-3">{filteredConstraints.length > 0 ? filteredConstraints.map(c => (<div key={c.id} className="p-3 bg-gray-50 rounded-lg border"><p className="font-bold capitalize">{c.type}: <span className="text-indigo-600">{c.subjectShortForm}</span> for Year {c.year}</p></div>)) : <p className="text-gray-500">No subject constraints defined.</p>}</div>
            </section>

            {/* BOX 5: Faculty List */}
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