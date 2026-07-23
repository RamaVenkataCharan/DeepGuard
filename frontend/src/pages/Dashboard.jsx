import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Users, AlertTriangle, Activity, Search, ShieldAlert, ChevronRight, Eye } from 'lucide-react';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [distribution, setDistribution] = useState(null);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [statsRes, distRes, alertsRes, custRes] = await Promise.all([
          api.get('/dashboard/stats'),
          api.get('/dashboard/risk-distribution'),
          api.get('/dashboard/recent-alerts'),
          api.get('/customers/')
        ]);

        setStats(statsRes.data);
        
        // Format distribution for Recharts
        const distData = Object.entries(distRes.data).map(([level, count]) => ({
          name: level.toUpperCase(),
          count,
          fill: getRiskLevelColor(level)
        }));
        setDistribution(distData);
        setRecentAlerts(alertsRes.data);
        setCustomers(custRes.data);
      } catch (error) {
        console.error('Error fetching dashboard statistics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const getRiskLevelColor = (level) => {
    switch (level.toLowerCase()) {
      case 'low': return '#10B981';
      case 'medium': return '#F59E0B';
      case 'high': return '#F97316';
      case 'critical': return '#EF4444';
      default: return '#94A3B8';
    }
  };

  const filteredCustomers = customers.filter(c => 
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.customer_code.toLowerCase().includes(search.toLowerCase()) ||
    c.region.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-4xl font-extrabold text-white tracking-tight">System Overview</h1>
        <p className="text-dark-muted mt-2">Real-time electricity consumption monitoring and theft hazard risk index analytics</p>
      </div>

      {/* Stats Cards Grid */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Card 1: Monitored Accounts */}
          <div className="glass-panel p-6 rounded-2xl flex items-center space-x-5">
            <div className="p-4 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/10">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold text-dark-muted uppercase tracking-wider">Monitored Customers</p>
              <h3 className="text-3xl font-extrabold text-white mt-1">{stats.total_customers}</h3>
            </div>
          </div>

          {/* Card 2: Active Alerts */}
          <div className="glass-panel p-6 rounded-2xl flex items-center space-x-5">
            <div className="p-4 rounded-xl bg-red-500/10 text-red-400 border border-red-500/10">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold text-dark-muted uppercase tracking-wider">Active Alerts</p>
              <h3 className="text-3xl font-extrabold text-white mt-1">{stats.active_alerts}</h3>
            </div>
          </div>

          {/* Card 3: Avg Risk Score */}
          <div className="glass-panel p-6 rounded-2xl flex items-center space-x-5">
            <div className="p-4 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/10">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold text-dark-muted uppercase tracking-wider">Average Risk Score</p>
              <h3 className="text-3xl font-extrabold text-white mt-1">{stats.average_risk_score.toFixed(1)}<span className="text-sm font-medium text-dark-muted">/100</span></h3>
            </div>
          </div>

          {/* Card 4: Critical High-Risk Count */}
          <div className="glass-panel p-6 rounded-2xl flex items-center space-x-5">
            <div className="p-4 rounded-xl bg-orange-500/10 text-orange-400 border border-orange-500/10">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold text-dark-muted uppercase tracking-wider">Critical Risk Count</p>
              <h3 className="text-3xl font-extrabold text-white mt-1">{stats.critical_risk_count}</h3>
            </div>
          </div>
        </div>
      )}

      {/* Row 2: Chart & Recent Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Chart */}
        <div className="glass-panel p-6 rounded-2xl lg:col-span-2 space-y-6">
          <div>
            <h3 className="text-xl font-bold text-white">Risk Distribution</h3>
            <p className="text-xs text-dark-muted mt-1">Total customer count categorized across security risk levels</p>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={distribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                <XAxis dataKey="name" stroke="#94A3B8" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#94A3B8" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip cursor={{ fill: 'rgba(255,255,255,0.02)' }} contentStyle={{ background: '#121824', borderColor: '#1E293B', borderRadius: '12px', fontSize: '12px' }} />
                <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                  {distribution && distribution.map((entry, index) => (
                    <Bar key={`cell-${index}`} dataKey="count" fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Alerts Feed */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <h3 className="text-xl font-bold text-white mb-4">Recent Anomalies</h3>
            <div className="space-y-4">
              {recentAlerts.length > 0 ? (
                recentAlerts.map((alert) => (
                  <div key={alert.id} className="flex items-start space-x-3 p-3.5 rounded-xl bg-slate-900/40 border border-dark-border/40 hover:border-dark-border transition-all duration-200">
                    <div className={`w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0 animate-pulse`} style={{ backgroundColor: getRiskLevelColor(alert.severity === 'critical' ? 'critical' : alert.severity === 'high' ? 'high' : 'medium') }} />
                    <div className="leading-tight text-left">
                      <h4 className="text-sm font-semibold text-slate-200">{alert.title}</h4>
                      <p className="text-xs text-dark-muted line-clamp-2 mt-1">{alert.message}</p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-dark-muted py-8 text-center">No active alerts requiring review.</p>
              )}
            </div>
          </div>
          <button onClick={() => navigate('/alerts')} className="w-full mt-4 flex items-center justify-center space-x-2 py-3 rounded-xl bg-slate-800/50 hover:bg-slate-800 text-sm font-semibold text-slate-300 border border-dark-border transition-all duration-200">
            <span>Manage Audit Alerts</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Row 3: Customers Directory */}
      <div className="glass-panel p-6 rounded-2xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold text-white">Monitored Customers Directory</h3>
            <p className="text-xs text-dark-muted mt-1">Audit status, geographic distribution, and connection metrics</p>
          </div>
          <div className="relative w-full md:w-80">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-muted" />
            <input
              type="text"
              placeholder="Search code, name, or region..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-900/60 focus:bg-slate-900 border border-dark-border focus:border-blue-500/50 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none transition-all duration-200"
            />
          </div>
        </div>

        {/* Customer Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-dark-border text-xs font-bold text-dark-muted uppercase tracking-wider">
                <th className="py-4 px-4">Code</th>
                <th className="py-4 px-4">Name</th>
                <th className="py-4 px-4">Region</th>
                <th className="py-4 px-4">Connection</th>
                <th className="py-4 px-4">Status</th>
                <th className="py-4 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredCustomers.map((cust) => (
                <tr key={cust.id} className="border-b border-dark-border/40 hover:bg-slate-800/10 transition-colors duration-150">
                  <td className="py-4 px-4 font-mono text-sm text-blue-400 font-bold">{cust.customer_code}</td>
                  <td className="py-4 px-4 font-semibold text-slate-200">{cust.name}</td>
                  <td className="py-4 px-4 text-sm text-slate-400">{cust.region}</td>
                  <td className="py-4 px-4 text-sm capitalize text-slate-400">{cust.connection_type}</td>
                  <td className="py-4 px-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold capitalize ${
                      cust.account_status === 'active'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}>
                      {cust.account_status}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-right">
                    <button
                      onClick={() => navigate(`/customer/${cust.id}`)}
                      className="inline-flex items-center space-x-1.5 bg-blue-600/10 hover:bg-blue-600 text-blue-400 hover:text-white px-4 py-2 rounded-xl text-xs font-bold border border-blue-500/20 hover:border-transparent transition-all duration-200"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Audit Profile</span>
                    </button>
                  </td>
                </tr>
              ))}
              {filteredCustomers.length === 0 && (
                <tr>
                  <td colSpan="6" className="py-8 text-center text-sm text-dark-muted">No monitored accounts match your criteria.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
