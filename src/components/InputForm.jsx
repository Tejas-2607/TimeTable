import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { generateTimeSlots } from '../utils/timeUtils';

// Reusable components
const InputField = ({ label, disabled = false, ...props }) => ( <div className="flex flex-col"> <label className={`mb-1 text-sm font-medium ${disabled ? 'text-gray-400' : 'text-gray-700'}`}>{label}</label> <input className={`px-3 py-2 border border-gray-300 rounded-md shadow-sm ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`} disabled={disabled} {...props} /> </div>);
const SelectField = ({ label, disabled = false, children, ...props }) => (<div className="flex flex-col"><label className={`mb-1 text-sm font-medium ${disabled ? 'text-gray-400' : 'text-gray-700'}`}>{label}</label><select className={`px-3 py-2 border border-gray-300 rounded-md shadow-sm ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`} disabled={disabled} {...props}>{children}</select></div>);

export default function InputForm({ departments, setDepartments, labs, setLabs, subjects, setSubjects, faculties, setFaculties, classStructure, setClassStructure, subjectConstraints, setSubjectConstraints }) {
    const navigate = useNavigate();
    const [feedback, setFeedback] = useState('');
    const [currentDept, setCurrentDept] = useState('');
    
    // States for all form sections
    const [startTime, setStartTime] = useState('09:15');
    const [endTime, setEndTime] = useState('17:20');
    const [lectureDuration, setLectureDuration] = useState('60');
    const [breakName, setBreakName] = useState('Lunch');
    const [breakStartTime, setBreakStartTime] = useState('12:15');
    const [breakDuration, setBreakDuration] = useState('65');
    const [labName, setLabName] = useState('');
    const [labShortForm, setLabShortForm] = useState('');
    const [facultyTitle, setFacultyTitle] = useState('Prof.');
    const [facultyName, setFacultyName] = useState('');
    const [facultyYears, setFacultyYears] = useState({ 2: false, 3: false, 4: false });
    const [facultySubjects, setFacultySubjects] = useState({});
    const [subjectName, setSubjectName] = useState('');
    const [subjectShortForm, setSubjectShortForm] = useState('');
    const [subjectYear, setSubjectYear] = useState('2');
    const [classType, setClassType] = useState('both');
    const [lecturesPerWeek, setLecturesPerWeek] = useState(4);
    const [practicalsPerWeek, setPracticalsPerWeek] = useState(1);
    const [practicalType, setPracticalType] = useState('specific_lab');
    const [specificLab, setSpecificLab] = useState('');
    const [activeConstraintTab, setActiveConstraintTab] = useState('joint'); // 'joint' or 'slot'
    const [constraintYear, setConstraintYear] = useState('2');
    const [constraintSubject, setConstraintSubject] = useState('');
    const [constraintSessionType, setConstraintSessionType] = useState('lecture');
    const [constraintFaculty, setConstraintFaculty] = useState([]);
    const [constraintNotes, setConstraintNotes] = useState('');
    const [slotConstraintDay, setSlotConstraintDay] = useState('Monday');
    const [slotConstraintTime, setSlotConstraintTime] = useState('');

    const handleClassStructureChange = (year, field, value) => {
        setClassStructure(prev => ({ ...prev, [year]: { ...prev[year], [field]: Number(value) } }));
    };

    const handleAddSubject = () => {
        if (!subjectName || !subjectShortForm) return alert("Please provide both a full name and a short form.");
        const newSubject = {
            id: Date.now(), department: currentDept, name: subjectName, shortForm: subjectShortForm.toUpperCase(), year: subjectYear, classType,
            workload: { lectures: classType === 'practical' ? 0 : lecturesPerWeek, practicals: classType === 'theory' ? 0 : practicalsPerWeek },
            practicalDetails: classType !== 'theory' ? { type: practicalType, lab: practicalType === 'specific_lab' ? specificLab : "None" } : null
        };
        setSubjects([...subjects, newSubject]);
        setSubjectName(''); setSubjectShortForm('');
    };
    
    const handleAddConstraint = () => {
        if (!constraintYear || !constraintSubject) return alert("Please select a year and subject.");
        let newConstraint;
        if (activeConstraintTab === 'joint') {
            newConstraint = { id: Date.now(), type: 'joint', department: currentDept, year: constraintYear, subjectShortForm: constraintSubject, sessionType: constraintSessionType, assignedFaculty: constraintFaculty.map(id => faculties.find(f => f.id === id)?.name || ''), notes: constraintNotes };
        } else { // Slot constraint
            if (!slotConstraintDay || !slotConstraintTime) return alert("Please select a day and a specific time slot.");
            const [start, end] = slotConstraintTime.split('-');
            newConstraint = { id: Date.now(), type: 'slot', department: currentDept, year: constraintYear, subjectShortForm: constraintSubject, sessionType: constraintSessionType, day: slotConstraintDay, startTime: start.trim(), endTime: end.trim() };
        }
        setSubjectConstraints([...subjectConstraints, newConstraint]);
        setConstraintSubject(''); setConstraintFaculty([]); setConstraintNotes(''); setSlotConstraintTime('');
    };
    
    const handleSetDeptTimings = () => { if (!currentDept) { alert('Please select a department first.'); return; } const breakInfo = { name: breakName, startTime: breakStartTime, duration: breakDuration }; const timeSlots = generateTimeSlots(startTime, endTime, lectureDuration, breakInfo); const existingDeptIndex = departments.findIndex(d => d.name === currentDept); let updatedDepts; if (existingDeptIndex > -1) { updatedDepts = [...departments]; updatedDepts[existingDeptIndex] = { ...updatedDepts[existingDeptIndex], startTime, endTime, lectureDuration, breakInfo, timeSlots }; } else { updatedDepts = [...departments, { name: currentDept, startTime, endTime, lectureDuration, breakInfo, timeSlots }]; } setDepartments(updatedDepts); setFeedback(`Timings for ${currentDept} set.`); setTimeout(() => setFeedback(''), 4000); };
    const handleAddLab = () => { if (!labName || !labShortForm) return; setLabs([...labs, { id: Date.now(), name: labName, shortForm: labShortForm.toUpperCase() }]); setLabName(''); setLabShortForm(''); };
    const handleAddFaculty = () => { if (!facultyName) return; setFaculties([...faculties, { id: Date.now(), department: currentDept, title: facultyTitle, name: facultyName, subjectsByYear: facultySubjects }]); setFacultyName(''); setFacultySubjects({}); setFacultyYears({ 2: false, 3: false, 4: false }); };
    const handleFacultyYearChange = (year) => { const updatedYears = { ...facultyYears, [year]: !facultyYears[year] }; if (!updatedYears[year]) { const updatedSubjects = { ...facultySubjects }; delete updatedSubjects[year]; setFacultySubjects(updatedSubjects); } setFacultyYears(updatedYears); };
    const handleFacultySubjectSelection = (year, shortForm) => { const current = facultySubjects[year] || []; const newSubjects = current.includes(shortForm) ? current.filter(s => s !== shortForm) : [...current, shortForm]; setFacultySubjects({ ...facultySubjects, [year]: newSubjects }); };
    const isFormDisabled = !currentDept;
    
    const selectedDeptForSlots = departments.find(d => d.name === currentDept);

    return (
        <main className="container mx-auto px-6 py-8">
            <section className="bg-white p-6 rounded-lg shadow mb-8"><h2 className="text-xl font-semibold mb-2">1. Select Current Department</h2><SelectField value={currentDept} onChange={e => setCurrentDept(e.target.value)}><option value="">-- Select a Department --</option>{["CSE", "ENTC", "ECM", "MECH", "CIVIL", "IT"].map(opt => <option key={opt} value={opt}>{opt}</option>)}</SelectField></section>
            
            <div className={`space-y-8 ${isFormDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}>
                <section className="bg-white p-6 rounded-lg shadow"><h2 className="text-xl font-semibold mb-4 border-b pb-2">2. Department Timings & Structure for <span className="text-indigo-600 font-bold">{currentDept}</span></h2>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4"><InputField label="Lecture Duration (mins)" type="number" value={lectureDuration} onChange={e => setLectureDuration(e.target.value)} disabled={isFormDisabled} /><InputField label="Day Start Time" type="time" value={startTime} onChange={e => setStartTime(e.target.value)} disabled={isFormDisabled} /><InputField label="Day End Time" type="time" value={endTime} onChange={e => setEndTime(e.target.value)} disabled={isFormDisabled} /></div>
                    <div className="grid grid-cols-3 gap-4 border-t mt-4 pt-4"><InputField label="Break Name" value={breakName} onChange={e => setBreakName(e.target.value)} disabled={isFormDisabled} /><InputField label="Break Start Time" type="time" value={breakStartTime} onChange={e => setBreakStartTime(e.target.value)} disabled={isFormDisabled} /><InputField label="Break Duration (mins)" type="number" value={breakDuration} onChange={e => setBreakDuration(e.target.value)} disabled={isFormDisabled} /></div>
                    <button onClick={handleSetDeptTimings} disabled={isFormDisabled} className="mt-4 w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:bg-gray-400">Set/Update Timings</button>
                    {feedback && <div className="mt-2 p-2 text-center bg-green-100 text-green-800 rounded-md text-sm">{feedback}</div>}
                    <div className="border-t mt-4 pt-4"><h3 className="font-semibold mb-2">Class & Batch Structure</h3><div className="grid grid-cols-3 gap-4">{['2', '3', '4'].map(year => (<div key={year} className="p-2 border rounded"><p className="font-bold text-sm text-center">{year === '2' ? 'SY' : year === '3' ? 'TY' : 'Final'}</p><InputField label="Divisions" type="number" min="0" value={classStructure[year].divisions} onChange={e => handleClassStructureChange(year, 'divisions', e.target.value)} disabled={isFormDisabled} /><InputField label="Batches/Div" type="number" min="0" value={classStructure[year].batchesPerDivision} onChange={e => handleClassStructureChange(year, 'batchesPerDivision', e.target.value)} disabled={isFormDisabled} /></div>))}</div></div>
                </section>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="space-y-8">
                        <section className="bg-white p-6 rounded-lg shadow"><h2 className="text-xl font-semibold mb-4 border-b pb-2">3. Laboratories</h2><div className="grid grid-cols-2 gap-4"><InputField label="Lab Name" value={labName} onChange={e => setLabName(e.target.value)} disabled={isFormDisabled} /><InputField label="Short Form" value={labShortForm} onChange={e => setLabShortForm(e.target.value)} disabled={isFormDisabled} /></div><button onClick={handleAddLab} disabled={isFormDisabled} className="mt-4 w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:bg-gray-400">Add Lab</button></section>
                        <section className="bg-white p-6 rounded-lg shadow"><h2 className="text-xl font-semibold mb-4 border-b pb-2">5. Faculty for <span className="text-indigo-600 font-bold">{currentDept}</span></h2><div className="grid grid-cols-3 gap-4"><SelectField label="Title" value={facultyTitle} onChange={e => setFacultyTitle(e.target.value)} disabled={isFormDisabled}><option>Prof.</option><option>Dr.</option><option>Mr.</option><option>Mrs.</option></SelectField><div className="col-span-2"><InputField label="Full Name" value={facultyName} onChange={e => setFacultyName(e.target.value)} disabled={isFormDisabled} /></div></div><div className="mt-4"><label className={`block text-sm font-medium ${isFormDisabled ? 'text-gray-400' : 'text-gray-700'}`}>Teaches in Years:</label><div className="flex space-x-4 mt-2">{[2, 3, 4].map(year => (<div key={year} className="flex items-center"><input type="checkbox" id={`fy-${year}`} checked={!!facultyYears[year]} onChange={() => handleFacultyYearChange(year)} disabled={isFormDisabled} /><label htmlFor={`fy-${year}`} className="ml-2">{year}yr</label></div>))}</div></div>{Object.entries(facultyYears).map(([year, isTeaching]) => isTeaching && (<div className="mt-4 border-t pt-4" key={year}><label className="block text-sm font-medium mb-2">Select Subjects for Year {year}:</label><div className="grid grid-cols-2 gap-2">{subjects.filter(s => s.department === currentDept && s.year === year).map(s => (<div key={s.shortForm} className="flex items-center"><input type="checkbox" id={`${year}-${s.shortForm}`} checked={facultySubjects[year]?.includes(s.shortForm)} onChange={() => handleFacultySubjectSelection(year, s.shortForm)} /><label htmlFor={`${year}-${s.shortForm}`} className="ml-2 text-sm">{s.shortForm}</label></div>))}</div></div>))}<button onClick={handleAddFaculty} disabled={isFormDisabled} className="mt-4 w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:bg-gray-400">Add Faculty</button></section>
                    </div>
                    <div className="space-y-8">
                        <section className="bg-white p-6 rounded-lg shadow"><h2 className="text-xl font-semibold mb-4 border-b pb-2">4. Subjects for <span className="text-indigo-600 font-bold">{currentDept}</span></h2><SelectField label="Year" value={subjectYear} onChange={e => setSubjectYear(e.target.value)} disabled={isFormDisabled}><option value="2">2nd Year</option><option value="3">3rd Year</option><option value="4">4th Year</option></SelectField><div className="grid grid-cols-2 gap-4 mt-4"><InputField label="Subject Full Name" value={subjectName} onChange={e => setSubjectName(e.target.value)} disabled={isFormDisabled} /><InputField label="Subject Short Form" value={subjectShortForm} onChange={e => setSubjectShortForm(e.target.value)} disabled={isFormDisabled} /></div><div className="mt-4"><label className={`block text-sm font-medium mb-2 ${isFormDisabled ? 'text-gray-400' : 'text-gray-700'}`}>Class Type:</label><div className="flex space-x-4">{['theory', 'practical', 'both'].map(type => <div key={type} className="flex items-center"><input type="radio" id={type} name="classType" value={type} checked={classType === type} onChange={e => setClassType(e.target.value)} disabled={isFormDisabled} /><label htmlFor={type} className="ml-2 capitalize">{type}</label></div>)}</div></div><div className="grid grid-cols-2 gap-4 mt-4 border-t pt-4">{classType !== 'practical' && <InputField label="Lectures / Week" type="number" value={lecturesPerWeek} onChange={e => setLecturesPerWeek(e.target.value)} disabled={isFormDisabled} />}{classType !== 'theory' && <InputField label="Practicals / Week" type="number" value={practicalsPerWeek} onChange={e => setPracticalsPerWeek(e.target.value)} disabled={isFormDisabled} />}</div>
                            {classType !== 'theory' && <div className="p-3 bg-gray-50 rounded-md border space-y-3 mt-4">
                                <label className="block text-sm font-medium">Practical Type:</label>
                                <div className="space-y-2">
                                    <div className="flex items-center"><input type="radio" id="prac_lab" name="pracType" value="specific_lab" checked={practicalType === 'specific_lab'} onChange={e => setPracticalType(e.target.value)} disabled={isFormDisabled} /><label htmlFor="prac_lab" className="ml-2 text-sm">Requires a specific lab</label></div>
                                    {practicalType === 'specific_lab' && <div className="pl-5"><SelectField label="Select Lab" value={specificLab} onChange={e => setSpecificLab(e.target.value)} disabled={isFormDisabled}><option value="">Any</option>{labs.map(l => <option key={l.shortForm} value={l.shortForm}>{l.shortForm} ({l.name})</option>)}</SelectField></div>}
                                    <div className="flex items-center"><input type="radio" id="prac_class" name="pracType" value="classroom_only" checked={practicalType === 'classroom_only'} onChange={e => setPracticalType(e.target.value)} disabled={isFormDisabled} /><label htmlFor="prac_class" className="ml-2 text-sm">Requires a classroom (no lab)</label></div>
                                    <div className="flex items-center"><input type="radio" id="prac_noroom" name="pracType" value="no_room_last_slots" checked={practicalType === 'no_room_last_slots'} onChange={e => setPracticalType(e.target.value)} disabled={isFormDisabled} /><label htmlFor="prac_noroom" className="ml-2 text-sm">No dedicated room (schedule last)</label></div>
                                </div>
                            </div>}
                        <button onClick={handleAddSubject} disabled={isFormDisabled} className="mt-4 w-full bg-indigo-600 text-white py-2 px-4 rounded-md disabled:bg-gray-400">Add Subject</button></section>
                    </div>
                </div>

                <section className="bg-white p-6 rounded-lg shadow"><h2 className="text-xl font-semibold mb-4 border-b pb-2">6. Subject Constraints</h2>
                    <div className="flex border-b mb-4"><button onClick={() => setActiveConstraintTab('joint')} className={`py-2 px-4 ${activeConstraintTab === 'joint' ? 'border-b-2 border-indigo-500 font-semibold' : ''}`}>Joined Sessions</button><button onClick={() => setActiveConstraintTab('slot')} className={`py-2 px-4 ${activeConstraintTab === 'slot' ? 'border-b-2 border-indigo-500 font-semibold' : ''}`}>Slot Specification</button></div>
                    
                    {activeConstraintTab === 'joint' && <div><div className="grid grid-cols-1 md:grid-cols-3 gap-4"><SelectField label="Year" value={constraintYear} onChange={e => setConstraintYear(e.target.value)} disabled={isFormDisabled}><option value="2">SY</option><option value="3">TY</option><option value="4">Final</option></SelectField><SelectField label="Subject" value={constraintSubject} onChange={e => setConstraintSubject(e.target.value)} disabled={isFormDisabled}><option value="">-- Select --</option>{subjects.filter(s => s.department === currentDept && s.year === constraintYear).map(s => <option key={s.shortForm} value={s.shortForm}>{s.shortForm}</option>)}</SelectField><SelectField label="Session Type" value={constraintSessionType} onChange={e => setConstraintSessionType(e.target.value)} disabled={isFormDisabled}><option value="lecture">Joint Lectures</option><option value="practical">Joint Practicals</option><option value="both">Both</option></SelectField></div><div className="mt-4"><label className="block text-sm font-medium mb-2">Assign Faculty:</label><div className="grid grid-cols-2 md:grid-cols-3 gap-2">{faculties.filter(f => f.department === currentDept).map(f => <div key={f.id} className="flex items-center"><input type="checkbox" id={`cf-${f.id}`} checked={constraintFaculty.includes(f.id)} onChange={() => setConstraintFaculty(prev => prev.includes(f.id) ? prev.filter(id => id !== f.id) : [...prev, f.id])} /><label htmlFor={`cf-${f.id}`} className="ml-2 text-sm">{f.name}</label></div>)}</div></div><div className="mt-4"><InputField label="Faculty Division Notes (e.g., Prof A for Div A/C)" value={constraintNotes} onChange={e => setConstraintNotes(e.target.value)} disabled={isFormDisabled} /></div></div>}
                    
                    {activeConstraintTab === 'slot' && <div><div className="grid grid-cols-1 md:grid-cols-3 gap-4"><SelectField label="Year" value={constraintYear} onChange={e => setConstraintYear(e.target.value)} disabled={isFormDisabled}><option value="2">SY</option><option value="3">TY</option><option value="4">Final</option></SelectField><SelectField label="Subject" value={constraintSubject} onChange={e => setConstraintSubject(e.target.value)} disabled={isFormDisabled}><option value="">-- Select --</option>{subjects.filter(s => s.department === currentDept && s.year === constraintYear).map(s => <option key={s.shortForm} value={s.shortForm}>{s.shortForm}</option>)}</SelectField><SelectField label="Session Type" value={constraintSessionType} onChange={e => setConstraintSessionType(e.target.value)} disabled={isFormDisabled}><option value="lecture">Theory</option><option value="practical">Practical</option></SelectField></div><div className="grid grid-cols-2 gap-4 mt-4"><SelectField label="Day" value={slotConstraintDay} onChange={e => setSlotConstraintDay(e.target.value)} disabled={isFormDisabled}>{['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'].map(day => <option key={day} value={day}>{day}</option>)}</SelectField><SelectField label="Time Slot" value={slotConstraintTime} onChange={e => setSlotConstraintTime(e.target.value)} disabled={isFormDisabled || !selectedDeptForSlots}><option value="">-- Select Slot --</option>{selectedDeptForSlots?.timeSlots['Monday'].filter(s => s.type === 'lecture').map(slot => <option key={slot.start} value={`${slot.start} - ${slot.end}`}>{`${slot.start} - ${slot.end}`}</option>)}</SelectField></div></div>}

                    <button onClick={handleAddConstraint} disabled={isFormDisabled} className="mt-4 w-full bg-indigo-600 text-white py-2 px-4 rounded-md disabled:bg-gray-400">Add Constraint</button>
                </section>
                <section className="mt-12 text-center"><button onClick={() => navigate('/report')} disabled={isFormDisabled} className="bg-green-600 text-white font-bold py-3 px-8 rounded-lg shadow-lg hover:bg-green-700 disabled:bg-gray-400">View Configuration Report →</button></section>
            </div>
        </main>
    );
}