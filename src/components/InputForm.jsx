import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { generateTimeSlots } from '../utils/timeUtils';

// Reusable components
const InputField = ({ label, disabled = false, ...props }) => ( <div className="flex flex-col"> <label className={`mb-1 text-sm font-medium ${disabled ? 'text-gray-400' : 'text-gray-700'}`}>{label}</label> <input className={`px-3 py-2 border border-gray-300 rounded-md shadow-sm ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`} disabled={disabled} {...props} /> </div>);
const SelectField = ({ label, disabled = false, children, ...props }) => (<div className="flex flex-col"><label className={`mb-1 text-sm font-medium ${disabled ? 'text-gray-400' : 'text-gray-700'}`}>{label}</label><select className={`px-3 py-2 border border-gray-300 rounded-md shadow-sm ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`} disabled={disabled} {...props}>{children}</select></div>);

export default function InputForm({ departments, setDepartments, labs, setLabs, subjects, setSubjects, faculties, setFaculties, jointConstraints, setJointConstraints }) {
    const navigate = useNavigate();
    const [feedback, setFeedback] = useState('');
    const [currentDept, setCurrentDept] = useState('');
    
    // States for Department, Lab, Faculty forms...
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

    // States for updated Subject form
    const [subjectName, setSubjectName] = useState('');
    const [subjectShortForm, setSubjectShortForm] = useState('');
    const [subjectYear, setSubjectYear] = useState('2');
    const [classType, setClassType] = useState('both'); 
    const [lecturesPerWeek, setLecturesPerWeek] = useState(4);
    const [practicalsPerWeek, setPracticalsPerWeek] = useState(1);
    const [noLabPractical, setNoLabPractical] = useState(false);
    const [labRequired, setLabRequired] = useState(true);
    const [specificLab, setSpecificLab] = useState('');

    // States for Constraints form
    const [constraintYear, setConstraintYear] = useState('2');
    const [constraintSubject, setConstraintSubject] = useState('');
    const [constraintType, setConstraintType] = useState('lecture');
    const [constraintFaculty, setConstraintFaculty] = useState([]);
    const [constraintNotes, setConstraintNotes] = useState('');

    // --- Handlers ---
    const handleSetDeptTimings = () => {
        if (!currentDept) return;
        const breakInfo = { name: breakName, startTime: breakStartTime, duration: breakDuration };
        const timeSlots = generateTimeSlots(startTime, endTime, lectureDuration, breakInfo);
        const existingDeptIndex = departments.findIndex(d => d.name === currentDept);
        let updatedDepts;
        if (existingDeptIndex > -1) {
            updatedDepts = [...departments];
            updatedDepts[existingDeptIndex] = { ...updatedDepts[existingDeptIndex], startTime, endTime, lectureDuration, breakInfo, timeSlots };
        } else {
            updatedDepts = [...departments, { name: currentDept, startTime, endTime, lectureDuration, breakInfo, timeSlots }];
        }
        setDepartments(updatedDepts);
        setFeedback(`Timings for ${currentDept} set.`);
        setTimeout(() => setFeedback(''), 4000);
    };

    const handleAddLab = () => {
        if (!labName || !labShortForm) return;
        setLabs([...labs, { id: Date.now(), name: labName, shortForm: labShortForm.toUpperCase() }]);
        setLabName(''); setLabShortForm('');
    };

    const handleAddSubject = () => {
        if (!subjectName || !subjectShortForm) return alert("Please provide both a full name and a short form.");
        setSubjects([...subjects, {
            id: Date.now(), department: currentDept, name: subjectName, shortForm: subjectShortForm.toUpperCase(), year: subjectYear, classType,
            workload: { lectures: classType === 'practical' ? 0 : lecturesPerWeek, practicals: classType === 'theory' ? 0 : practicalsPerWeek },
            practicalDetails: classType !== 'theory' ? { lab: labRequired ? specificLab : "None", noLabRequired: noLabPractical } : null
        }]);
        setSubjectName(''); setSubjectShortForm('');
    };
    
    const handleAddFaculty = () => {
        if (!facultyName) return;
        setFaculties([...faculties, { id: Date.now(), department: currentDept, title: facultyTitle, name: facultyName, subjectsByYear: facultySubjects }]);
        setFacultyName(''); setFacultySubjects({}); setFacultyYears({ 2: false, 3: false, 4: false });
    };

    const handleAddConstraint = () => {
        if (!constraintYear || !constraintSubject) return alert("Please select a year and subject.");
        setJointConstraints([...jointConstraints, {
            id: Date.now(), department: currentDept, year: constraintYear, subjectShortForm: constraintSubject, type: constraintType,
            assignedFacultyIds: constraintFaculty, notes: constraintNotes,
        }]);
        setConstraintSubject(''); setConstraintFaculty([]); setConstraintNotes('');
    };

    const handleFacultyYearChange = (year) => {
        const updatedYears = { ...facultyYears, [year]: !facultyYears[year] };
        if (!updatedYears[year]) {
            const updatedSubjects = { ...facultySubjects };
            delete updatedSubjects[year];
            setFacultySubjects(updatedSubjects);
        }
        setFacultyYears(updatedYears);
    };

    const handleFacultySubjectSelection = (year, shortForm) => {
        const current = facultySubjects[year] || [];
        const newSubjects = current.includes(shortForm) ? current.filter(s => s !== shortForm) : [...current, shortForm];
        setFacultySubjects({ ...facultySubjects, [year]: newSubjects });
    };

    const isFormDisabled = !currentDept;

    return (
        <main className="container mx-auto px-6 py-8">
            <section className="bg-white p-6 rounded-lg shadow mb-8">
                <h2 className="text-xl font-semibold mb-2">1. Select Current Department</h2>
                <SelectField value={currentDept} onChange={e => setCurrentDept(e.target.value)}><option value="">-- Select a Department --</option>{["CSE", "ENTC", "ECM", "MECH", "CIVIL", "IT"].map(opt => <option key={opt} value={opt}>{opt}</option>)}</SelectField>
            </section>
            
            <div className={`space-y-8 ${isFormDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}>
                <section className="bg-white p-6 rounded-lg shadow"><h2 className="text-xl font-semibold mb-4 border-b pb-2">2. Department Timings</h2><div className="grid grid-cols-2 lg:grid-cols-4 gap-4"><InputField label="Lecture Duration (mins)" type="number" value={lectureDuration} onChange={e => setLectureDuration(e.target.value)} disabled={isFormDisabled} /><InputField label="Day Start Time" type="time" value={startTime} onChange={e => setStartTime(e.target.value)} disabled={isFormDisabled} /><InputField label="Day End Time" type="time" value={endTime} onChange={e => setEndTime(e.target.value)} disabled={isFormDisabled} /></div><div className="grid grid-cols-3 gap-4 border-t mt-4 pt-4"><InputField label="Break Name" value={breakName} onChange={e => setBreakName(e.target.value)} disabled={isFormDisabled} /><InputField label="Break Start Time" type="time" value={breakStartTime} onChange={e => setBreakStartTime(e.target.value)} disabled={isFormDisabled} /><InputField label="Break Duration (mins)" type="number" value={breakDuration} onChange={e => setBreakDuration(e.target.value)} disabled={isFormDisabled} /></div><button onClick={handleSetDeptTimings} disabled={isFormDisabled} className="mt-4 w-full bg-indigo-600 text-white py-2 px-4 rounded-md disabled:bg-gray-400">Set Timings</button>{feedback && <div className="mt-2 p-2 text-center bg-green-100 text-sm">{feedback}</div>}</section>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <section className="bg-white p-6 rounded-lg shadow"><h2 className="text-xl font-semibold mb-4 border-b pb-2">3. Laboratories</h2><div className="grid grid-cols-2 gap-4"><InputField label="Lab Name" value={labName} onChange={e => setLabName(e.target.value)} disabled={isFormDisabled} /><InputField label="Short Form" value={labShortForm} onChange={e => setLabShortForm(e.target.value)} disabled={isFormDisabled} /></div><button onClick={handleAddLab} disabled={isFormDisabled} className="mt-4 w-full bg-indigo-600 text-white py-2 px-4 rounded-md disabled:bg-gray-400">Add Lab</button></section>
                    
                    <section className="bg-white p-6 rounded-lg shadow"><h2 className="text-xl font-semibold mb-4 border-b pb-2">4. Subjects</h2>
                        <SelectField label="Year" value={subjectYear} onChange={e => setSubjectYear(e.target.value)} disabled={isFormDisabled}><option value="2">2nd Year</option><option value="3">3rd Year</option><option value="4">4th Year</option></SelectField>
                        <div className="grid grid-cols-2 gap-4 mt-4"><InputField label="Subject Full Name" value={subjectName} onChange={e => setSubjectName(e.target.value)} disabled={isFormDisabled} /><InputField label="Subject Short Form" value={subjectShortForm} onChange={e => setSubjectShortForm(e.target.value)} disabled={isFormDisabled} /></div>
                        <div className="mt-4"><label className="block text-sm font-medium mb-2">Class Type:</label><div className="flex space-x-4">{['theory', 'practical', 'both'].map(type => <div key={type} className="flex items-center"><input type="radio" id={type} name="classType" value={type} checked={classType === type} onChange={e => setClassType(e.target.value)} disabled={isFormDisabled} /><label htmlFor={type} className="ml-2 capitalize">{type}</label></div>)}</div></div>
                        <div className="grid grid-cols-2 gap-4 mt-4 border-t pt-4">{classType !== 'practical' && <InputField label="Lectures / Week" type="number" value={lecturesPerWeek} onChange={e => setLecturesPerWeek(e.target.value)} disabled={isFormDisabled} />}{classType !== 'theory' && <InputField label="Practicals / Week" type="number" value={practicalsPerWeek} onChange={e => setPracticalsPerWeek(e.target.value)} disabled={isFormDisabled} />}</div>
                        {classType !== 'theory' && <div className="p-3 bg-gray-50 rounded-md border space-y-3 mt-4"><div className="flex items-center"><input type="checkbox" id="noLab" checked={noLabPractical} onChange={e => {setNoLabPractical(e.target.checked); if(e.target.checked) setLabRequired(false)}} disabled={isFormDisabled} /><label htmlFor="noLab" className="ml-2 text-sm">No dedicated lab (schedule last)</label></div><div className="flex items-center"><input type="checkbox" id="labReq" checked={labRequired} onChange={e => {setLabRequired(e.target.checked); if(e.target.checked) setNoLabPractical(false)}} disabled={isFormDisabled || noLabPractical} /><label htmlFor="labReq" className="ml-2 text-sm">Requires a specific lab?</label></div>{labRequired && !noLabPractical && <SelectField label="Select Lab" value={specificLab} onChange={e => setSpecificLab(e.target.value)} disabled={isFormDisabled}><option value="">Any</option>{labs.map(l => <option key={l.shortForm} value={l.shortForm}>{l.shortForm}</option>)}</SelectField>}</div>}
                        <button onClick={handleAddSubject} disabled={isFormDisabled} className="mt-4 w-full bg-indigo-600 text-white py-2 px-4 rounded-md disabled:bg-gray-400">Add Subject</button>
                    </section>
                </div>
                
                <section className="bg-white p-6 rounded-lg shadow"><h2 className="text-xl font-semibold mb-4 border-b pb-2">5. Faculty</h2><div className="grid grid-cols-3 gap-4"><SelectField label="Title" value={facultyTitle} onChange={e => setFacultyTitle(e.target.value)} disabled={isFormDisabled}><option>Prof.</option><option>Dr.</option><option>Mr.</option><option>Mrs.</option></SelectField><div className="col-span-2"><InputField label="Full Name" value={facultyName} onChange={e => setFacultyName(e.target.value)} disabled={isFormDisabled} /></div></div><div className="mt-4"><label className="block text-sm font-medium">Teaches in Years:</label><div className="flex space-x-4 mt-2">{[2, 3, 4].map(year => (<div key={year} className="flex items-center"><input type="checkbox" id={`fy-${year}`} checked={!!facultyYears[year]} onChange={() => handleFacultyYearChange(year)} disabled={isFormDisabled} /><label htmlFor={`fy-${year}`} className="ml-2">{year}yr</label></div>))}</div></div>{Object.entries(facultyYears).map(([year, isTeaching]) => isTeaching && (<div className="mt-4 border-t pt-4" key={year}><label className="block text-sm font-medium mb-2">Select Subjects for Year {year}:</label><div className="grid grid-cols-2 gap-2">{subjects.filter(s => s.department === currentDept && s.year === year).map(s => (<div key={s.shortForm} className="flex items-center"><input type="checkbox" id={`${year}-${s.shortForm}`} checked={facultySubjects[year]?.includes(s.shortForm)} onChange={() => handleFacultySubjectSelection(year, s.shortForm)} disabled={isFormDisabled} /><label htmlFor={`${year}-${s.shortForm}`} className="ml-2 text-sm">{s.shortForm}</label></div>))}</div></div>))}<button onClick={handleAddFaculty} disabled={isFormDisabled} className="mt-4 w-full bg-indigo-600 text-white py-2 px-4 rounded-md disabled:bg-gray-400">Add Faculty</button></section>
                
                <section className="bg-white p-6 rounded-lg shadow"><h2 className="text-xl font-semibold mb-4 border-b pb-2">6. Joint Subject Constraints</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4"><SelectField label="Year" value={constraintYear} onChange={e => setConstraintYear(e.target.value)} disabled={isFormDisabled}><option value="2">SY</option><option value="3">TY</option><option value="4">Final</option></SelectField><SelectField label="Subject" value={constraintSubject} onChange={e => setConstraintSubject(e.target.value)} disabled={isFormDisabled}><option value="">-- Select Subject --</option>{subjects.filter(s => s.department === currentDept && s.year === constraintYear).map(s => <option key={s.shortForm} value={s.shortForm}>{s.shortForm}</option>)}</SelectField><SelectField label="Type" value={constraintType} onChange={e => setConstraintType(e.target.value)} disabled={isFormDisabled}><option value="lecture">Joint Lecture</option><option value="practical">Joint Practical</option></SelectField></div>
                    <div className="mt-4"><label className="block text-sm font-medium mb-2">Assign Faculty:</label><div className="grid grid-cols-2 md:grid-cols-3 gap-2">{faculties.filter(f => f.department === currentDept).map(f => <div key={f.id} className="flex items-center"><input type="checkbox" id={`cf-${f.id}`} checked={constraintFaculty.includes(f.id)} onChange={() => setConstraintFaculty(prev => prev.includes(f.id) ? prev.filter(id => id !== f.id) : [...prev, f.id])} disabled={isFormDisabled} /><label htmlFor={`cf-${f.id}`} className="ml-2 text-sm">{f.title} {f.name}</label></div>)}</div></div>
                    <div className="mt-4"><InputField label="Faculty Division Notes (Optional)" value={constraintNotes} onChange={e => setConstraintNotes(e.target.value)} disabled={isFormDisabled} /></div>
                    <button onClick={handleAddConstraint} disabled={isFormDisabled} className="mt-4 w-full bg-indigo-600 text-white py-2 px-4 rounded-md disabled:bg-gray-400">Add Constraint</button>
                </section>
                
                <section className="mt-12 text-center"><button onClick={() => navigate('/report')} disabled={isFormDisabled} className="bg-green-600 text-white font-bold py-3 px-8 rounded-lg shadow-lg disabled:bg-gray-400">View Configuration Report →</button></section>
            </div>
            
        </main>
    );
}