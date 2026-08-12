import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, LayoutDashboard, AlertTriangle, FileBarChart, LogOut, User, Network, Radio } from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/alerts', label: 'Alerts', icon: AlertTriangle },
    { path: '/reports', label: 'Reports', icon: FileBarChart },
    { path: '/network', label: '3D Network Map', icon: Network },
  ];

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin':
        return 'bg-red-500/10 text-red-400 border border-red-500/20';
      case 'analyst':
        return 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
      default:
        return 'bg-blue-500/10 text-blue-400 border border-blue-500/20';
    }
  };

  return (
    <nav className="glass-panel sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between border-b border-dark-border shadow-lg">
      {/* Brand Logo & Grid Status Pill */}
      <div className="flex items-center space-x-4">
        <div
          tabIndex={0}
          role="button"
          onClick={() => navigate('/')}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/')}
          className="flex items-center space-x-3 cursor-pointer group focus-visible:ring-2 focus-visible:ring-blue-500 rounded-xl p-1"
        >
          <div className="bg-gradient-to-tr from-blue-600 to-indigo-500 p-2.5 rounded-xl shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform duration-200">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <span className="font-extrabold text-xl tracking-wide bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent font-display">
            DeepGuard<span className="text-blue-500">.ai</span>
          </span>
        </div>

        {/* Tactical Telemetry Heartbeat Pill */}
        <div className="hidden lg:flex items-center space-x-2 bg-slate-900/80 px-3 py-1 rounded-full border border-slate-800 text-[11px] font-mono text-slate-300">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="font-bold text-slate-200">SGCC GRID LIVE</span>
          <span className="text-slate-500">| 42.3K METERS</span>
        </div>
      </div>

      {/* Nav Links */}
      <div className="flex items-center space-x-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs md:text-sm font-semibold transition-all duration-200 focus-visible:ring-2 focus-visible:ring-blue-500 ${
                isActive
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-md shadow-blue-600/10'
                  : 'text-dark-muted hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      {/* User Actions */}
      <div className="flex items-center space-x-4">
        {/* User Card */}
        {user && (
          <div className="hidden md:flex items-center space-x-3 border-r border-dark-border pr-4">
            <div className="bg-slate-800/80 p-2 rounded-lg border border-dark-border">
              <User className="w-4 h-4 text-slate-300" />
            </div>
            <div className="text-left leading-tight">
              <p className="text-xs font-bold text-slate-200">{user.full_name}</p>
              <span className={`inline-block text-[9px] font-extrabold tracking-wider uppercase px-2 py-0.5 mt-0.5 rounded ${getRoleColor(user.role)}`}>
                {user.role}
              </span>
            </div>
          </div>
        )}

        {/* Logout Button */}
        <button
          onClick={handleLogout}
          aria-label="Logout user session"
          className="flex items-center space-x-1.5 bg-slate-800/60 hover:bg-red-500/10 text-dark-muted hover:text-red-400 border border-dark-border hover:border-red-500/20 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all duration-200 focus-visible:ring-2 focus-visible:ring-red-400"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Logout</span>
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
