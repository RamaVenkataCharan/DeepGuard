import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useDebounce } from '../hooks/useDebounce';
import Pagination from '../components/Pagination';
import { MetricCardSkeleton, TableRowSkeleton, ChartSkeleton } from '../components/SkeletonLoaders';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Users, AlertTriangle, Activity, Search, ShieldAlert, ChevronRight, Eye, RefreshCw, XCircle } from 'lucide-react';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [distribution, setDistribution] = useState(null);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [customers, setCustomers] = useState([]);
  
  // Filtering & Pagination State
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  
  // Loading & Error States
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);
  const navigate = useNavigate();

  const fetchDashboardData = async () => {
    setLoading(true);
    setFetchError(null);
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
      setRecentAlerts(alertsRes.data || []);
      setCustomers(Array.isArray(custRes.data) ? custRes.data : []);
    } catch (error) {
      console.error('Error fetching dashboard statistics:', error);
      setFetchError(error.response?.data?.message || 'Failed to fetch dashboard telemetry. Check API connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Reset to page 1 whenever debounced search query changes
  useEffect(() => {
    setCurrentPage(1);
  }, [debouncedSearch]);

  const getRiskLevelColor = (level = '') => {
    switch (level.toLowerCase()) {
      case 'low': return '#10B981';
      case 'medium': return '#F59E0B';
      case 'high': return '#F97316';
      case 'critical': return '#EF4444';
      default: return '#94A3B8';
    }
  };

  // Filtered customer list driven by debounced query
  const filteredCustomers = useMemo(() => {
    if (!debouncedSearch.trim()) return customers;
    const query = debouncedSearch.toLowerCase().trim();
    return customers.filter(c =>
      (c.name && c.name.toLowerCase().includes(query)) ||
      (c.customer_code && c.customer_code.toLowerCase().includes(query)) ||
      (c.region && c.region.toLowerCase().includes(query)) ||
      (c.feeder_line && c.feeder_line.toLowerCase().includes(query))
    );
  }, [customers, debouncedSearch]);

  // Paginated Slice for Scale (Render 10-25 items per page instead of 42k into DOM at once)
  const paginatedCustomers = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredCustomers.slice(start, start + pageSize);
  }, [filteredCustomers, currentPage, pageSize]);

  const totalPages = Math.ceil(filteredCustomers.length / pageSize) || 1;

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight font-display">
            System Overview
          </h1>
          <p className="text-dark-muted mt-1.5 text-xs md:text-sm">
            Real-time electricity consumption telemetry and theft hazard risk index analytics
          </p>
        </div>

        <button
          onClick={fetchDashboardData}
          disabled={loading}
          className="self-start md:self-auto flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 text-slate-300 border border-dark-border px-4 py-2.5 rounded-xl text-xs font-semibold transition-all focus-visible:ring-2 focus-visible:ring-blue-500 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {/* Fetch Error Retry Alert */}
      {fetchError && (
        <div className="bg-rose-950/40 border border-rose-500/40 text-rose-200 px-5 py-4 rounded-2xl flex items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <XCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <div>
              <span className="font-bold text-sm block">Telemetry Stream Error</span>
              <p className="text-xs text-rose-300/80">{fetchError}</p>
            </div>
          </div>
          <button
            onClick={fetchDashboardData}
            className="px-4 py-2 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-100 text-xs font-bold border border-rose-500/30 transition-all"
          >
            Retry Call
          </button>
        </div>
      )}

      {/* ⚠️ Conditional Synthetic Demo Banner */}
      {recentAlerts.some(a => a.data_source === 'synthetic_demo') && (
        <div className="bg-amber-950/40 border border-amber-500/30 text-amber-200 px-5 py-4 rounded-2xl flex items-center gap-3">
          <span className="text-xl">⚠️</span>
          <div className="text-left">
            <span className="font-bold text-sm block">NOTICE: Running on Synthetic Demo Data</span>
            <p className="text-xs text-amber-300/80">These metrics demonstrate pipeline flow correctness and should not be used for production operations.</p>
          </div>
        </div>
      )}

      {/* Stats Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <MetricCardSkeleton />
          <MetricCardSkeleton />
          <MetricCardSkeleton />
          <MetricCardSkeleton />
        </div>
      ) : stats ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Card 1: Monitored Accounts */}
          <div className="glass-panel glass-panel-hover p-6 rounded-2xl flex items-center space-x-5">
            <div className="p-4 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <p className="text-[11px] font-bold text-dark-muted uppercase tracking-wider">Monitored Customers</p>
              <h2 className="text-3xl font-extrabold text-white mt-1 font-display">{stats.total_customers.toLocaleString()}</h2>
            </div>
          </div>

          {/* Card 2: Active Alerts */}
          <div className="glass-panel glass-panel-hover p-6 rounded-2xl flex items-center space-x-5">
            <div className="p-4 rounded-xl bg-red-500/10 text-red-400 border border-red-500/20">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <p className="text-[11px] font-bold text-dark-muted uppercase tracking-wider">Active Alerts</p>
              <h2 className="text-3xl font-extrabold text-white mt-1 font-display">{stats.active_alerts}</h2>
            </div>
          </div>

          {/* Card 3: Avg Risk Score */}
          <div className="glass-panel glass-panel-hover p-6 rounded-2xl flex items-center space-x-5">
            <div className="p-4 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <p className="text-[11px] font-bold text-dark-muted uppercase tracking-wider">Average Risk Index</p>
              <h2 className="text-3xl font-extrabold text-white mt-1 font-display">
                {stats.average_risk_score.toFixed(1)}
                <span className="text-sm font-normal text-dark-muted">/100</span>
              </h2>
            </div>
          </div>

          {/* Card 4: Critical High-Risk Count */}
          <div className="glass-panel glass-panel-hover p-6 rounded-2xl flex items-center space-x-5">
            <div className="p-4 rounded-xl bg-orange-500/10 text-orange-400 border border-orange-500/20">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <p className="text-[11px] font-bold text-dark-muted uppercase tracking-wider">Critical Theft Hazards</p>
              <h2 className="text-3xl font-extrabold text-white mt-1 font-display">{stats.critical_risk_count}</h2>
            </div>
          </div>
        </div>
      ) : null}

      {/* Row 2: Risk Distribution Chart & Recent Alerts Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Chart */}
        <div className="glass-panel p-6 rounded-2xl lg:col-span-2 space-y-6">
          <div>
            <h2 className="text-lg font-bold text-white font-display">Risk Level Breakdown</h2>
            <p className="text-xs text-dark-muted mt-0.5">Total customer accounts categorized across risk levels</p>
          </div>
          {loading ? (
            <ChartSkeleton />
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                  <XAxis dataKey="name" stroke="#94A3B8" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#94A3B8" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip
                    cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                    contentStyle={{ background: '#121824', borderColor: '#1E293B', borderRadius: '12px', fontSize: '12px', color: '#FFF' }}
                  />
                  <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                    {distribution && distribution.map((entry, index) => (
                      <Bar key={`cell-${index}`} dataKey="count" fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Recent Alerts Feed */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-bold text-white mb-4 font-display">Recent Anomaly Signals</h2>
            <div className="space-y-3">
              {loading ? (
                Array.from({ length: 4 }).map((_, idx) => (
                  <div key={idx} className="h-16 bg-slate-900/60 rounded-xl animate-pulse" />
                ))
              ) : recentAlerts.length > 0 ? (
                recentAlerts.slice(0, 4).map((alert) => (
                  <div
                    key={alert.id}
                    onClick={() => navigate('/alerts')}
                    className="flex items-start space-x-3 p-3 rounded-xl bg-slate-900/50 border border-dark-border/40 hover:border-blue-500/30 cursor-pointer transition-all duration-150"
                  >
                    <div
                      className="w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0 animate-pulse"
                      style={{ backgroundColor: getRiskLevelColor(alert.severity) }}
                    />
                    <div className="leading-tight text-left">
                      <h3 className="text-xs font-bold text-slate-200">{alert.title}</h3>
                      <p className="text-[11px] text-dark-muted line-clamp-2 mt-1">{alert.message}</p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-10 space-y-2">
                  <p className="text-xs text-dark-muted">No active theft anomalies currently flagged.</p>
                </div>
              )}
            </div>
          </div>
          <button
            onClick={() => navigate('/alerts')}
            className="w-full mt-4 flex items-center justify-center space-x-2 py-3 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-xs font-bold text-slate-200 border border-dark-border transition-all focus-visible:ring-2 focus-visible:ring-blue-500"
          >
            <span>Manage Audit Alerts Queue</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Row 3: Monitored Customers Directory */}
      <div className="glass-panel p-6 rounded-2xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white font-display">Monitored Customers Directory</h2>
            <p className="text-xs text-dark-muted mt-0.5">Audit status, region codes, and meter infrastructure parameters</p>
          </div>

          {/* Search Box */}
          <div className="relative w-full md:w-80">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-muted" />
            <input
              type="text"
              placeholder="Search code, name, or region..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-900/80 focus:bg-slate-900 border border-dark-border focus:border-blue-500/50 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none transition-all duration-200 focus-visible:ring-2 focus-visible:ring-blue-500"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
              >
                ×
              </button>
            )}
          </div>
        </div>

        {/* Customer Directory Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-dark-border text-[11px] font-bold text-dark-muted uppercase tracking-wider">
                <th className="py-3.5 px-4">Customer Code</th>
                <th className="py-3.5 px-4">Account Name</th>
                <th className="py-3.5 px-4">Region Code</th>
                <th className="py-3.5 px-4">Feeder Line</th>
                <th className="py-3.5 px-4">Connection</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, idx) => (
                  <TableRowSkeleton key={idx} columns={7} />
                ))
              ) : paginatedCustomers.length > 0 ? (
                paginatedCustomers.map((cust) => (
                  <tr
                    key={cust.id}
                    className="border-b border-dark-border/40 hover:bg-slate-800/30 transition-colors duration-150"
                  >
                    <td className="py-3.5 px-4 font-mono text-xs text-blue-400 font-bold">{cust.customer_code}</td>
                    <td className="py-3.5 px-4 text-xs font-semibold text-slate-200">{cust.name}</td>
                    <td className="py-3.5 px-4 text-xs font-mono text-slate-400">{cust.region || cust.region_code || 'N/A'}</td>
                    <td className="py-3.5 px-4 text-xs font-mono text-slate-400">{cust.feeder_line || 'N/A'}</td>
                    <td className="py-3.5 px-4 text-xs capitalize text-slate-400">{cust.connection_type}</td>
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-extrabold capitalize ${
                        cust.account_status === 'active'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}>
                        {cust.account_status || 'Active'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => navigate(`/customer/${cust.id}`)}
                        className="inline-flex items-center space-x-1.5 bg-blue-600/10 hover:bg-blue-600 text-blue-400 hover:text-white px-3.5 py-1.5 rounded-lg text-xs font-bold border border-blue-500/20 hover:border-transparent transition-all duration-150 focus-visible:ring-2 focus-visible:ring-blue-500"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Audit Profile</span>
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-xs text-dark-muted">
                    <div className="space-y-3">
                      <p className="text-slate-300 font-semibold">No monitored accounts match search criteria "{debouncedSearch}".</p>
                      <button
                        onClick={() => setSearch('')}
                        className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-dark-border transition-all"
                      >
                        Reset Search Filter
                      </button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Scale Pagination Controls */}
        {!loading && filteredCustomers.length > 0 && (
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={filteredCustomers.length}
            pageSize={pageSize}
            onPageChange={setCurrentPage}
            onPageSizeChange={(newSize) => {
              setPageSize(newSize);
              setCurrentPage(1);
            }}
          />
        )}
      </div>
    </div>
  );
};

export default Dashboard;
