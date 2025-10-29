import { useState } from 'react';
import { Menu, X, Calendar, Users, FlaskConical, Grid3x3, Eye, BookOpen } from 'lucide-react';

export default function Sidebar({ activeTab, onTabChange }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const menuItems = [
    { id: 'generate', label: 'Generate Timetable', icon: Calendar },
    { id: 'faculty', label: 'Faculty Data', icon: Users },
    { id: 'labs', label: 'Labs Data', icon: FlaskConical },
    { id: 'structure', label: 'Class Structure', icon: Grid3x3 },
    { id: 'view', label: 'View Timetables', icon: Eye },
    { id: 'practical', label: 'Practical Plan', icon: BookOpen },
  ];

  return (
    <div
      className={`${
        isCollapsed ? 'w-20' : 'w-64'
      } bg-gradient-to-b from-slate-900 to-slate-800 text-white min-h-screen transition-all duration-300 flex flex-col shadow-2xl`}
    >
      <div className="p-6 flex items-center justify-between border-b border-slate-700">
        {!isCollapsed && (
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              Schedulo
            </h1>
            <p className="text-xs text-slate-400 mt-1">CSE Dept Timetable</p>
          </div>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
        >
          {isCollapsed ? <Menu size={20} /> : <X size={20} />}
        </button>
      </div>

      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.id}>
                <button
                  onClick={() => onTabChange(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                    activeTab === item.id
                      ? 'bg-blue-600 shadow-lg shadow-blue-600/50'
                      : 'hover:bg-slate-700'
                  }`}
                >
                  <Icon size={20} />
                  {!isCollapsed && (
                    <span className="font-medium text-sm">{item.label}</span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
}
