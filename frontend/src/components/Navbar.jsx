import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, LayoutDashboard, AlertTriangle, FileBarChart, LogOut, User } from 'lucide-react';

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
    <nav className="glass-panel sticky top-0 z-50 px-6 py-4 flex items-center justify-between border-b border-dark-border">
      {/* Brand Logo */}
      <div className="flex items-center space-x-3 cursor-pointer" onClick={() => navigate('/')}>
        <div className="bg-gradient-to-tr from-blue-600 to-indigo-500 p-2.5 rounded-xl shadow-lg shadow-blue-500/20">
          <Shield className="w-6 h-6 text-white" />
        </div>
        <span className="font-extrabold text-2xl tracking-wide bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
          DeepGuard<span className="text-blue-500">.ai</span>
        </span>
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
              className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-250 ${
                isActive
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/10'
                  : 'text-dark-muted hover:text-slate-200 hover:bg-slate-800/20'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      {/* User Actions */}
      <div className="flex items-center space-x-5">
        {/* User Card */}
        {user && (
          <div className="flex items-center space-x-3 border-r border-dark-border pr-5">
            <div className="bg-slate-800/60 p-2 rounded-lg border border-dark-border">
              <User className="w-4 h-4 text-slate-300" />
            </div>
            <div className="text-left leading-tight">
              <p className="text-sm font-bold text-slate-200">{user.full_name}</p>
              <span className={`inline-block text-[10px] font-extrabold tracking-wider uppercase px-2 py-0.5 mt-0.5 rounded ${getRoleColor(user.role)}`}>
                {user.role}
              </span>
            </div>
          </div>
        )}

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="flex items-center space-x-2 bg-slate-800/40 hover:bg-red-500/10 text-dark-muted hover:text-red-400 border border-dark-border hover:border-red-500/20 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
        >
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
