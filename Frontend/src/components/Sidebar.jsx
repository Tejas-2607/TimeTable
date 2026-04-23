import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Calendar, Users, FlaskConical, Grid3x3, Eye, BookOpen, Briefcase } from 'lucide-react';

export default function Sidebar({ onTabChange }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();
  const activeTab = location.pathname.substring(1) || 'generate';

  const menuItems = [
    { id: 'generate', label: 'Generate Timetable', icon: Calendar },
    { id: 'faculty', label: 'Faculty Data', icon: Users },
    { id: 'labs', label: 'Labs Data', icon: FlaskConical },
    { id: 'structure', label: 'Class Structure', icon: Grid3x3 },
    { id: 'view', label: 'View Timetables', icon: Eye },
  ];

  return (
    <div
      className={`${isCollapsed ? 'w-20' : 'w-64'
        } bg-gradient-to-b from-slate-900 to-slate-950 text-slate-300 min-h-screen transition-all duration-300 flex flex-col shadow-2xl border-r border-slate-800 print:hidden`}
    >
      <div className={`p-6 flex items-center border-b border-slate-700 ${isCollapsed ? 'justify-center' : 'justify-between'}`}>
        <div className={`overflow-hidden whitespace-nowrap transition-all duration-300 ease-in-out ${isCollapsed ? 'max-w-0 opacity-0 hidden' : 'max-w-[200px] opacity-100 flex-1'}`}>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent tracking-tight">
            Schedulo
          </h1>
          <p className="text-xs text-slate-400 mt-1">CSE Dept Timetable</p>
        </div>
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-2 hover:bg-slate-800 text-slate-400 hover:text-white rounded-lg transition-colors shrink-0"
        >
          {isCollapsed ? <Menu size={20} /> : <X size={20} />}
        </button>
      </div>

      <nav className={`flex-1 ${isCollapsed ? 'p-2' : 'p-4'}`}>
        <ul className="space-y-2 mt-4">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.id} className={isCollapsed ? 'flex justify-center' : ''}>
                <Link
                  to={`/${item.id}`}
                  onClick={() => onTabChange && onTabChange()}
                  className={`flex items-center transition-all duration-200 ${activeTab === item.id
                    ? 'bg-blue-500/10 text-blue-400 font-semibold'
                    : 'hover:bg-slate-800/50 text-slate-400 hover:text-slate-200'
                    } ${isCollapsed ? 'justify-center p-3 rounded-2xl w-14 h-14' : 'w-full gap-3 px-4 py-3 rounded-xl justify-start'}`}
                  title={isCollapsed ? item.label : undefined}
                >
                  <Icon size={24} className={`shrink-0 ${activeTab === item.id ? "text-blue-400" : "text-slate-500"}`} />
                  <span className={`text-sm whitespace-nowrap overflow-hidden transition-all duration-300 ease-in-out ${isCollapsed ? 'max-w-0 opacity-0 hidden' : 'max-w-[200px] opacity-100'
                    }`}>
                    {item.label}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
}
