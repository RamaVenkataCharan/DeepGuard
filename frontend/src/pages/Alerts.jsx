import { useState, useEffect } from 'react';
import api from '../services/api';
import { AlertCircle, CheckCircle, Search, Calendar, ChevronRight, X, UserCheck, RefreshCw } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Alerts = () => {
  const { user } = useAuth();
  
  const [activeAlerts, setActiveAlerts] = useState([]);
  const [resolvedAlerts, setResolvedAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedAlert, setSelectedAlert] = useState(null);
  
  // Form fields for updating status
  const [newStatus, setNewStatus] = useState('');
  const [notes, setNotes] = useState('');
  const [updating, setUpdating] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const fetchAlerts = async () => {
    try {
      const [activeRes, resolvedRes] = await Promise.all([
        api.get('/alerts/'),
        api.get('/alerts/history')
      ]);
      setActiveAlerts(activeRes.data);
      setResolvedAlerts(resolvedRes.data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const handleOpenUpdateModal = (alert) => {
    setSelectedAlert(alert);
    setNewStatus(alert.status);
    setNotes(alert.notes || '');
    setErrorMsg('');
  };

  const handleCloseUpdateModal = () => {
    setSelectedAlert(null);
    setNewStatus('');
    setNotes('');
  };

  const handleUpdateStatus = async (e) => {
    e.preventDefault();
    setUpdating(true);
    setErrorMsg('');
    try {
      await api.put(`/alerts/${selectedAlert.id}/status`, {
        status: newStatus,
        notes
      });
      await fetchAlerts();
      handleCloseUpdateModal();
    } catch (error) {
      setErrorMsg(error.response?.data?.message || 'Failed to update alert status. Verify permissions.');
    } finally {
      setUpdating(false);
    }
  };

  const getSeverityBadgeColor = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
      case 'high': return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
      default: return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
    }
  };

  const getStatusBadgeColor = (status) => {
    switch (status) {
      case 'open': return 'text-red-400 bg-red-500/10 border-red-500/20';
      case 'investigating': return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      case 'resolved': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      default: return 'text-slate-400 bg-slate-500/10 border-slate-500/20';
    }
  };

  // Filter alerts by search term
  const filterFn = (a) => 
    a.title.toLowerCase().includes(search.toLowerCase()) ||
    a.message.toLowerCase().includes(search.toLowerCase()) ||
    (a.customer && a.customer.name.toLowerCase().includes(search.toLowerCase())) ||
    (a.customer && a.customer.customer_code.toLowerCase().includes(search.toLowerCase()));

  const filteredActive = activeAlerts.filter(filterFn);
  const filteredResolved = resolvedAlerts.filter(filterFn);

  if (loading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8 relative">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-extrabold text-white tracking-tight">Audit Alerts</h1>
          <p className="text-dark-muted mt-2">Manage, investigate, and audit system-flagged theft risk anomalies</p>
        </div>
        
        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-muted" />
          <input
            type="text"
            placeholder="Search alerts or customers..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-900/60 focus:bg-slate-900 border border-dark-border focus:border-blue-500/50 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none transition-all duration-200"
          />
        </div>
      </div>

      {/* Row: Active Alerts */}
      <div className="glass-panel p-6 rounded-2xl space-y-6">
        <div className="flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-red-400" />
          <h3 className="text-xl font-bold text-white">Active Audits Queue</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-dark-border text-xs font-bold text-dark-muted uppercase tracking-wider">
                <th className="py-4 px-4">Severity</th>
                <th className="py-4 px-4">Status</th>
                <th className="py-4 px-4">Trigger Date</th>
                <th className="py-4 px-4">Customer</th>
                <th className="py-4 px-4">Title</th>
                <th className="py-4 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredActive.map((alert) => (
                <tr key={alert.id} className="border-b border-dark-border/40 hover:bg-slate-800/10 transition-colors duration-150">
                  <td className="py-4 px-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-extrabold uppercase border ${getSeverityBadgeColor(alert.severity)}`}>
                      {alert.severity}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-extrabold uppercase border ${getStatusBadgeColor(alert.status)}`}>
                      {alert.status}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-sm text-slate-400 font-medium">
                    <div className="flex items-center space-x-1.5">
                      <Calendar className="w-3.5 h-3.5 text-dark-muted" />
                      <span>{new Date(alert.created_at).toLocaleDateString()}</span>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-sm font-semibold text-slate-200">
                    {alert.customer ? `${alert.customer.name} (${alert.customer.customer_code})` : 'Unknown'}
                  </td>
                  <td className="py-4 px-4 text-sm text-slate-300 font-medium max-w-xs truncate">{alert.title}</td>
                  <td className="py-4 px-4 text-right">
                    <button
                      onClick={() => handleOpenUpdateModal(alert)}
                      className="inline-flex items-center space-x-1 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white px-3.5 py-2 rounded-xl text-xs font-bold border border-dark-border transition-all duration-200"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>Audit Status</span>
                    </button>
                  </td>
                </tr>
              ))}
              {filteredActive.length === 0 && (
                <tr>
                  <td colSpan="6" className="py-8 text-center text-sm text-dark-muted">No active anomalies flagged in queue.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Row: Resolved Alerts */}
      <div className="glass-panel p-6 rounded-2xl space-y-6">
        <div className="flex items-center space-x-2">
          <CheckCircle className="w-5 h-5 text-emerald-400" />
          <h3 className="text-xl font-bold text-white">Closed & Audited History</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-dark-border text-xs font-bold text-dark-muted uppercase tracking-wider">
                <th className="py-4 px-4">Severity</th>
                <th className="py-4 px-4">Status</th>
                <th className="py-4 px-4">Resolution Date</th>
                <th className="py-4 px-4">Customer</th>
                <th className="py-4 px-4">Title</th>
                <th className="py-4 px-4">Audited Notes</th>
              </tr>
            </thead>
            <tbody>
              {filteredResolved.map((alert) => (
                <tr key={alert.id} className="border-b border-dark-border/40 hover:bg-slate-800/10 transition-colors duration-150">
                  <td className="py-4 px-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-extrabold uppercase border ${getSeverityBadgeColor(alert.severity)}`}>
                      {alert.severity}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-extrabold uppercase border ${getStatusBadgeColor(alert.status)}`}>
                      {alert.status}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-sm text-slate-400 font-medium">
                    <div className="flex items-center space-x-1.5">
                      <Calendar className="w-3.5 h-3.5 text-dark-muted" />
                      <span>{alert.resolved_at ? new Date(alert.resolved_at).toLocaleDateString() : 'N/A'}</span>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-sm font-semibold text-slate-200">
                    {alert.customer ? `${alert.customer.name} (${alert.customer.customer_code})` : 'Unknown'}
                  </td>
                  <td className="py-4 px-4 text-sm text-slate-300 font-medium max-w-xs truncate">{alert.title}</td>
                  <td className="py-4 px-4 text-xs text-dark-muted max-w-xs truncate">{alert.notes || 'No comments added.'}</td>
                </tr>
              ))}
              {filteredResolved.length === 0 && (
                <tr>
                  <td colSpan="6" className="py-8 text-center text-sm text-dark-muted">No historical resolutions found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Drawer Modal for Status Update */}
      {selectedAlert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop blur */}
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={handleCloseUpdateModal}></div>
          
          <div className="glass-panel w-full max-w-lg p-6 rounded-3xl relative z-10 space-y-6">
            <div className="flex items-center justify-between border-b border-dark-border pb-4">
              <h3 className="text-xl font-bold text-white">Update Audit Status</h3>
              <button onClick={handleCloseUpdateModal} className="text-dark-muted hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            {errorMsg && (
              <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl flex items-center space-x-2">
                <AlertCircle className="w-5 h-5" />
                <span className="text-sm font-medium">{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleUpdateStatus} className="space-y-5 text-left">
              {/* Alert Info Summary */}
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-dark-border text-sm space-y-1">
                <p className="text-xs text-dark-muted font-bold">MONITORED OBJECT</p>
                <p className="font-semibold text-slate-200">{selectedAlert.customer?.name} ({selectedAlert.customer?.customer_code})</p>
                <p className="text-xs text-dark-muted mt-2 block font-medium">{selectedAlert.message}</p>
              </div>

              {/* Status Selection */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block pl-1">New Audit Status</label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full bg-slate-900 border border-dark-border focus:border-blue-500/50 rounded-xl px-4 py-3 text-sm text-white focus:outline-none transition-all"
                >
                  <option value="open">Open</option>
                  <option value="investigating">Investigating</option>
                  <option value="resolved">Resolved</option>
                  <option value="false_positive">False Positive</option>
                </select>
              </div>

              {/* Auditor Notes */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block pl-1">Auditor Notes / Comments</label>
                <textarea
                  required
                  rows="4"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Enter details about investigations, inspection reports, field worker feedback, etc..."
                  className="w-full bg-slate-900 border border-dark-border focus:border-blue-500/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none transition-all"
                ></textarea>
              </div>

              {/* Submit Buttons */}
              <div className="flex items-center space-x-4 pt-2">
                <button
                  type="button"
                  onClick={handleCloseUpdateModal}
                  className="w-1/2 py-3.5 rounded-xl border border-dark-border hover:bg-slate-800 text-sm font-semibold text-slate-300 transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updating || user?.role === 'viewer'}
                  className="w-1/2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white py-3.5 rounded-xl text-sm font-extrabold flex items-center justify-center space-x-1.5 shadow-lg shadow-blue-500/10 transition-all"
                >
                  {updating ? (
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <>
                      <UserCheck className="w-4 h-4" />
                      <span>Apply Changes</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Alerts;
