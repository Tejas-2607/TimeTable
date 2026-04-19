import { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Menu, X, Calendar, Users, FlaskConical, Grid3x3, Eye, Briefcase, LogOut, ShieldAlert } from 'lucide-react';

export default function Sidebar({ onTabChange }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();
  const activeTab = location.pathname.substring(1) || 'generate';

  const menuItems = [
    { id: 'generate', label: 'Generate Timetable', icon: Calendar, role: 'admin' },
    { id: 'faculty', label: 'Faculty Data', icon: Users, role: 'admin' },
    { id: 'labs', label: 'Labs Data', icon: FlaskConical, role: 'admin' },
    { id: 'structure', label: 'Class Structure', icon: Grid3x3, role: 'admin' },
    { id: 'view', label: 'View Timetables', icon: Eye },
    { id: 'faculty_timetables', label: 'Faculty Timetables', icon: Briefcase },
    { id: 'constraints', label: 'Special Constraints', icon: ShieldAlert },
  ].filter(item => !item.role || user?.role === item.role);

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

      {/* User portion */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/50 backdrop-blur-sm">
        <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} p-2 rounded-xl bg-slate-800/30`}>
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold shrink-0 shadow-lg shadow-blue-500/20">
            {user?.name?.charAt(0).toUpperCase() || 'U'}
          </div>
          {!isCollapsed && (
            <div className="flex-1 min-w-0 overflow-hidden">
              <p className="text-sm font-semibold text-white truncate">{user?.name || 'User'}</p>
              <p className="text-[10px] text-slate-500 truncate">{user?.email}</p>
            </div>
          )}
        </div>
        <button
          onClick={logout}
          className={`mt-4 flex items-center gap-3 text-slate-400 hover:text-red-400 transition-colors ${isCollapsed ? 'justify-center w-full px-0' : 'px-4'} py-2 rounded-xl hover:bg-red-400/10`}
          title={isCollapsed ? 'Logout' : undefined}
        >
          <LogOut size={20} />
          {!isCollapsed && <span className="text-sm font-medium">Logout</span>}
        </button>
      </div>
    </div>
  );
}
