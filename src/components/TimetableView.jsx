import React from 'react';
import { Link } from 'react-router-dom';

export default function TimetableView({ config, timetable }) {
    if (!timetable) {
        return (
            <main className="container mx-auto px-6 py-8 text-center">
                <h1 className="text-2xl font-bold">No Timetable Generated</h1>
                <p className="mt-2 text-gray-600">Please configure your settings and generate a timetable from the report page.</p>
                <Link to="/report" className="mt-4 inline-block bg-indigo-600 text-white py-2 px-4 rounded-md">Go to Report</Link>
            </main>
        );
    }
    
    return (
        <main className="container mx-auto px-6 py-8">
            <h1 className="text-3xl font-bold text-gray-800 mb-4">Generated Timetable</h1>
            <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-xl font-semibold text-indigo-700 border-b pb-2">Generation Status</h2>
                <p className="mt-4"><strong>Status:</strong> <span className="text-green-600 font-bold">{timetable.status}</span></p>
                <p><strong>Timestamp:</strong> {new Date(timetable.generatedAt).toLocaleString()}</p>
                <p className="mt-4 text-sm text-gray-500">
                    The visual timetable grid would be displayed here. The generation itself is a complex backend process that uses the configuration below.
                </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow mt-8">
                <h2 className="text-xl font-semibold text-indigo-700 border-b pb-2">Final Configuration Used</h2>
                <pre className="mt-4 bg-gray-100 p-4 rounded-md text-xs overflow-x-auto">
                    {JSON.stringify(config, null, 2)}
                </pre>
            </div>
        </main>
    );
}