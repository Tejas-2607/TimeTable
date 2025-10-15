import React, { useState, useEffect, useMemo } from 'react';
import { ChevronDown, Download, Printer, Edit2, X, Check, Plus, Search } from 'lucide-react';

const generateMockTimetable = (appData, department, year, division) => {
    if (!appData.departments.length || !department || !year || !division) return [];
    const deptData = appData.departments.find(d => d.name === department);
    if (!deptData) return [];
    const yearSubjects = appData.subjects.filter(s => s.department === department && s.year === year);
    const yearFaculty = appData.faculties.filter(f => f.department === department && Object.keys(f.subjectsByYear).includes(year));
    const timeSlots = deptData.timeSlots['Monday'];
    const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    const timetable = Array(timeSlots.length).fill(0).map(() => Array(weekDays.length).fill(null));
    return timetable;
};

export default function TempTimetable({ appData }) {
    const [selectedDept, setSelectedDept] = useState('');
    const [selectedYear, setSelectedYear] = useState('2');
    const [selectedDivision, setSelectedDivision] = useState('A');
    const [timetableData, setTimetableData] = useState([]);
    const [isEditing, setIsEditing] = useState(false);
    const [editingCell, setEditingCell] = useState(null);
    const [editFormData, setEditFormData] = useState({ subject: '', faculty: '', room: '' });

    useEffect(() => {
        if (appData.departments.length > 0 && !selectedDept) {
            setSelectedDept(appData.departments[0].name);
        }
    }, [appData.departments, selectedDept]);

    useEffect(() => {
        const data = generateMockTimetable(appData, selectedDept, selectedYear, selectedDivision);
        setTimetableData(data);
    }, [appData, selectedDept, selectedYear, selectedDivision]);
    
    const divisionOptions = useMemo(() => { 
        const divisions = appData.classStructure[selectedYear]?.divisions || 0; 
        return Array.from({ length: divisions }, (_, i) => String.fromCharCode(65 + i)); 
    }, [appData.classStructure, selectedYear]);

    const timeSlots = useMemo(() => { 
        const dept = appData.departments.find(d => d.name === selectedDept); 
        return dept ? dept.timeSlots['Monday'] : []; 
    }, [appData.departments, selectedDept]);

    const handleCellClick = (slotIndex, dayIndex) => { 
        const data = timetableData[slotIndex]?.[dayIndex] || {}; 
        setEditingCell({ slotIndex, dayIndex, data }); 
        setEditFormData({ subject: data.subject || '', faculty: data.faculty || '', room: data.room || '' }); 
        setIsEditing(true); 
    };

    const handleSaveEdit = () => { 
        const { slotIndex, dayIndex } = editingCell; 
        const newTimetableData = [...timetableData]; 
        newTimetableData[slotIndex][dayIndex] = { ...newTimetableData[slotIndex][dayIndex], ...editFormData }; 
        setTimetableData(newTimetableData); 
        setIsEditing(false); 
        setEditingCell(null); 
    };

    const handleClearSlot = () => { 
        const { slotIndex, dayIndex } = editingCell; 
        const newTimetableData = [...timetableData]; 
        newTimetableData[slotIndex][dayIndex] = null; 
        setTimetableData(newTimetableData); 
        setIsEditing(false); 
        setEditingCell(null); 
    };

    const handleExportCSV = () => { 
        let csvContent = "data:text/csv;charset=utf-8,Time," + ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'].join(',') + "\n"; 
        timeSlots.forEach((slot, slotIndex) => { 
            let row = `${slot.start}-${slot.end},`; 
            row += timetableData[slotIndex].map(cell => cell ? `"${cell.subject} (${cell.faculty})"` : "").join(','); 
            csvContent += row + "\n"; 
        }); 
        const encodedUri = encodeURI(csvContent); 
        const link = document.createElement("a"); 
        link.setAttribute("href", encodedUri); 
        link.setAttribute("download", `timetable_${selectedDept}_${selectedYear}${selectedDivision}.csv`); 
        document.body.appendChild(link); 
        link.click(); 
        document.body.removeChild(link); 
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
            <div className="container mx-auto p-4 sm:p-6 lg:p-8">
                {/* Header Section */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold text-gray-900 mb-2">Timetable Management</h1>
                    <p className="text-gray-600">Manage and view class schedules efficiently</p>
                </div>

                {/* Control Panel */}
                <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-6 mb-8">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                        {/* Department Selector */}
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                                <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
                                Department
                            </label>
                            <div className="relative">
                                <select 
                                    value={selectedDept} 
                                    onChange={(e) => setSelectedDept(e.target.value)} 
                                    className="w-full px-4 py-3 rounded-lg border border-gray-200 bg-white text-gray-900 font-medium focus:ring-2 focus:ring-indigo-500 focus:border-transparent appearance-none cursor-pointer hover:border-gray-300 transition"
                                >
                                    <option value="">Select Department</option>
                                    {appData.departments && appData.departments.map((d) => (
                                        <option key={d.name} value={d.name}>{d.name}</option>
                                    ))}
                                </select>
                                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Year Selector */}
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                                Year
                            </label>
                            <div className="relative">
                                <select 
                                    value={selectedYear} 
                                    onChange={(e) => setSelectedYear(e.target.value)} 
                                    className="w-full px-4 py-3 rounded-lg border border-gray-200 bg-white text-gray-900 font-medium focus:ring-2 focus:ring-indigo-500 focus:border-transparent appearance-none cursor-pointer hover:border-gray-300 transition"
                                >
                                    <option value="2">Second Year</option>
                                    <option value="3">Third Year</option>
                                    <option value="4">Final Year</option>
                                </select>
                                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Division Selector */}
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                                Division
                            </label>
                            <div className="relative">
                                <select 
                                    value={selectedDivision} 
                                    onChange={(e) => setSelectedDivision(e.target.value)} 
                                    className="w-full px-4 py-3 rounded-lg border border-gray-200 bg-white text-gray-900 font-medium focus:ring-2 focus:ring-indigo-500 focus:border-transparent appearance-none cursor-pointer hover:border-gray-300 transition"
                                >
                                    {divisionOptions.map((div) => (
                                        <option key={div} value={div}>{div}</option>
                                    ))}
                                </select>
                                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Action Buttons */}
                        <button 
                            onClick={() => window.print()} 
                            className="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-slate-600 hover:bg-slate-700 text-white font-medium transition transform hover:scale-105 shadow-sm"
                        >
                            <Printer className="w-4 h-4" />
                            <span className="hidden sm:inline">Print</span>
                        </button>

                        <button 
                            onClick={handleExportCSV} 
                            className="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-medium transition transform hover:scale-105 shadow-sm"
                        >
                            <Download className="w-4 h-4" />
                            <span className="hidden sm:inline">Export</span>
                        </button>
                    </div>
                </div>

                {/* Timetable Grid */}
                <div className="bg-white rounded-2xl shadow-md border border-gray-100 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full min-w-[900px]">
                            <thead>
                                <tr className="bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200">
                                    <th className="px-4 py-4 font-semibold text-sm text-gray-700 text-left w-32">Time</th>
                                    {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'].map((day) => (
                                        <th key={day} className="px-4 py-4 font-semibold text-sm text-gray-700 text-center border-l border-gray-100">{day}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {timeSlots.map((slot, slotIndex) => (
                                    <tr key={slotIndex} className={`${slotIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'} border-b border-gray-100 hover:bg-indigo-50 transition`}>
                                        <td className="px-4 py-4 font-bold text-xs text-center text-gray-600 bg-gray-50">
                                            {slot.type === 'break' ? (
                                                <span className="inline-block px-2 py-1 rounded-full bg-amber-100 text-amber-700 font-semibold text-xs">{slot.name}</span>
                                            ) : (
                                                <div className="flex flex-col gap-1">
                                                    <span>{slot.start}</span>
                                                    <span className="text-gray-300">−</span>
                                                    <span>{slot.end}</span>
                                                </div>
                                            )}
                                        </td>
                                        {timetableData[slotIndex]?.map((cell, dayIndex) => (
                                            <td 
                                                key={dayIndex} 
                                                onClick={() => slot.type !== 'break' && handleCellClick(slotIndex, dayIndex)}
                                                className={`px-2 py-4 border-l border-gray-100 text-center ${slot.type !== 'break' ? 'cursor-pointer hover:bg-indigo-100 transition' : ''}`}
                                            >
                                                {cell && cell.type !== 'break' ? (
                                                    <div className={`p-3 rounded-lg h-20 flex flex-col justify-center ${cell.type === 'practical' ? 'bg-gradient-to-br from-sky-100 to-sky-50 border-l-4 border-sky-500 text-sky-900' : 'bg-gradient-to-br from-emerald-100 to-emerald-50 border-l-4 border-emerald-500 text-emerald-900'}`}>
                                                        <p className="font-bold text-sm leading-tight">{cell.subject}</p>
                                                        <p className="text-xs mt-1 opacity-80">{cell.faculty}</p>
                                                        <p className="text-xs italic opacity-60 mt-1">{cell.room}</p>
                                                    </div>
                                                ) : (
                                                    <div className="h-20 flex items-center justify-center text-gray-300">
                                                        <Plus className="w-5 h-5" />
                                                    </div>
                                                )}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Editing Modal */}
                {isEditing && (
                    <div className="fixed inset-0 bg-black bg-opacity-40 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setIsEditing(false)}>
                        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md border border-gray-200" onClick={(e) => e.stopPropagation()}>
                            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                                <h3 className="text-xl font-bold text-gray-900">Edit Time Slot</h3>
                                <button onClick={() => setIsEditing(false)} className="p-1 hover:bg-gray-100 rounded-lg transition">
                                    <X className="w-5 h-5 text-gray-500" />
                                </button>
                            </div>
                            
                            <div className="px-6 py-4 space-y-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-gray-700">Subject (Short Form)</label>
                                    <input 
                                        type="text" 
                                        value={editFormData.subject} 
                                        onChange={(e) => setEditFormData({...editFormData, subject: e.target.value})}
                                        className="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                                        placeholder="e.g., CS201"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-gray-700">Faculty</label>
                                    <input 
                                        type="text" 
                                        value={editFormData.faculty} 
                                        onChange={(e) => setEditFormData({...editFormData, faculty: e.target.value})}
                                        className="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                                        placeholder="e.g., Dr. John Doe"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-gray-700">Room / Lab</label>
                                    <input 
                                        type="text" 
                                        value={editFormData.room} 
                                        onChange={(e) => setEditFormData({...editFormData, room: e.target.value})}
                                        className="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                                        placeholder="e.g., CR-101"
                                    />
                                </div>
                            </div>

                            <div className="px-6 py-4 border-t border-gray-100 flex gap-3">
                                <button 
                                    onClick={handleClearSlot} 
                                    className="flex-1 px-4 py-2 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 font-medium transition"
                                >
                                    Clear
                                </button>
                                <button 
                                    onClick={() => setIsEditing(false)} 
                                    className="flex-1 px-4 py-2 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 font-medium transition"
                                >
                                    Cancel
                                </button>
                                <button 
                                    onClick={handleSaveEdit} 
                                    className="flex-1 px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 font-medium transition flex items-center justify-center gap-2"
                                >
                                    <Check className="w-4 h-4" />
                                    Save
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}