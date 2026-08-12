import React, { useState, useEffect, useMemo } from 'react';
import api from '../services/api';
import { useDebounce } from '../hooks/useDebounce';
import Pagination from '../components/Pagination';
import { TableRowSkeleton } from '../components/SkeletonLoaders';
import { AlertCircle, CheckCircle, Search, Calendar, RefreshCw, X, UserCheck, AlertTriangle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Alerts = () => {
  const { user } = useAuth();

  const [activeAlerts, setActiveAlerts] = useState([]);
  const [resolvedAlerts, setResolvedAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);

  // Search & Pagination State
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);

  const [activePage, setActivePage] = useState(1);
  const [activePageSize, setActivePageSize] = useState(10);

  const [resolvedPage, setResolvedPage] = useState(1);
  const [resolvedPageSize, setResolvedPageSize] = useState(10);

  // Modal state
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [newStatus, setNewStatus] = useState('');
  const [notes, setNotes] = useState('');
  const [updating, setUpdating] = useState(false);
  const [validationError, setValidationError] = useState('');

  const fetchAlerts = async () => {
    setLoading(true);
    setFetchError(null);
    try {
      const [activeRes, resolvedRes] = await Promise.all([
        api.get('/alerts/'),
        api.get('/alerts/history')
      ]);
      setActiveAlerts(Array.isArray(activeRes.data) ? activeRes.data : []);
      setResolvedAlerts(Array.isArray(resolvedRes.data) ? resolvedRes.data : []);
    } catch (error) {
      console.error('Error fetching alerts:', error);
      setFetchError(error.response?.data?.message || 'Failed to fetch audit queue. Verify backend API connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  // Reset pagination on debounced search change
  useEffect(() => {
    setActivePage(1);
    setResolvedPage(1);
  }, [debouncedSearch]);

  const handleOpenUpdateModal = (alert) => {
    setSelectedAlert(alert);
    setNewStatus(alert.status);
    setNotes(alert.notes || '');
    setValidationError('');
  };

  const handleCloseUpdateModal = () => {
    setSelectedAlert(null);
    setNewStatus('');
    setNotes('');
    setValidationError('');
  };

  const handleUpdateStatus = async (e) => {
    e.preventDefault();
    setValidationError('');

    // Client-side Validation (Part 2d)
    if (!newStatus) {
      setValidationError('Please select a valid audit status code.');
      return;
    }
    if (!notes.trim() || notes.trim().length < 5) {
      setValidationError('Auditor notes are required (minimum 5 characters).');
      return;
    }

    setUpdating(true);
    try {
      await api.put(`/alerts/${selectedAlert.id}/status`, {
        status: newStatus,
        notes: notes.trim()
      });
      await fetchAlerts();
      handleCloseUpdateModal();
    } catch (error) {
      setValidationError(error.response?.data?.message || 'Failed to update alert status. Verify permissions.');
    } finally {
      setUpdating(false);
    }
  };

  const getSeverityBadgeColor = (severity = '') => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
      case 'high': return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
      case 'warning': return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
      default: return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
    }
  };

  const getStatusBadgeColor = (status = '') => {
    switch (status) {
      case 'open': return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
      case 'investigating': return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
      case 'resolved': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
      default: return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
    }
  };

  // Filter function using debounced search query
  const filterFn = (a) => {
    if (!debouncedSearch.trim()) return true;
    const query = debouncedSearch.toLowerCase().trim();
    return (
      (a.title && a.title.toLowerCase().includes(query)) ||
      (a.message && a.message.toLowerCase().includes(query)) ||
      (a.severity && a.severity.toLowerCase().includes(query)) ||
      (a.status && a.status.toLowerCase().includes(query)) ||
      (a.customer && a.customer.name && a.customer.name.toLowerCase().includes(query)) ||
      (a.customer && a.customer.customer_code && a.customer.customer_code.toLowerCase().includes(query))
    );
  };

  const filteredActive = useMemo(() => activeAlerts.filter(filterFn), [activeAlerts, debouncedSearch]);
  const filteredResolved = useMemo(() => resolvedAlerts.filter(filterFn), [resolvedAlerts, debouncedSearch]);

  // Paginated active alerts
  const paginatedActive = useMemo(() => {
    const start = (activePage - 1) * activePageSize;
    return filteredActive.slice(start, start + activePageSize);
  }, [filteredActive, activePage, activePageSize]);

  // Paginated resolved alerts
  const paginatedResolved = useMemo(() => {
    const start = (resolvedPage - 1) * resolvedPageSize;
    return filteredResolved.slice(start, start + resolvedPageSize);
  }, [filteredResolved, resolvedPage, resolvedPageSize]);

  const activeTotalPages = Math.ceil(filteredActive.length / activePageSize) || 1;
  const resolvedTotalPages = Math.ceil(filteredResolved.length / resolvedPageSize) || 1;

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8 relative">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight font-display">
            Audit Alerts Queue
          </h1>
          <p className="text-dark-muted mt-1.5 text-xs md:text-sm">
            Investigate, resolve, and audit system-flagged theft risk anomalies
          </p>
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-muted" />
          <input
            type="text"
            placeholder="Search alerts, customers, codes..."
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

      {/* Fetch Error Banner */}
      {fetchError && (
        <div className="bg-rose-950/40 border border-rose-500/40 text-rose-200 px-5 py-4 rounded-2xl flex items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <div>
              <span className="font-bold text-sm block">Alerts Queue Telemetry Error</span>
              <p className="text-xs text-rose-300/80">{fetchError}</p>
            </div>
          </div>
          <button
            onClick={fetchAlerts}
            className="px-4 py-2 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-100 text-xs font-bold border border-rose-500/30 transition-all"
          >
            Retry Telemetry
          </button>
        </div>
      )}

      {/* ⚠️ Conditional Synthetic Demo Banner */}
      {[...activeAlerts, ...resolvedAlerts].some(a => a.data_source === 'synthetic_demo') && (
        <div className="bg-amber-950/40 border border-amber-500/30 text-amber-200 px-5 py-4 rounded-2xl flex items-center gap-3">
          <span className="text-xl">⚠️</span>
          <div className="text-left">
            <span className="font-bold text-sm block">NOTICE: Running on Synthetic Demo Data</span>
            <p className="text-xs text-amber-300/80">These metrics demonstrate pipeline flow correctness and should not be used for production operations.</p>
          </div>
        </div>
      )}

      {/* Row 1: Active Alerts Queue */}
      <div className="glass-panel p-6 rounded-2xl space-y-6">
        <div className="flex items-center space-x-2.5">
          <AlertCircle className="w-5 h-5 text-rose-400" />
          <h2 className="text-xl font-bold text-white font-display">Active Audits Queue</h2>
          <span className="text-xs font-mono font-bold bg-rose-500/10 text-rose-400 px-2.5 py-0.5 rounded border border-rose-500/20">
            {filteredActive.length} Open
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-dark-border text-[11px] font-bold text-dark-muted uppercase tracking-wider">
                <th className="py-3.5 px-4">Severity</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Trigger Date</th>
                <th className="py-3.5 px-4">Customer Account</th>
                <th className="py-3.5 px-4">Anomaly Title</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 4 }).map((_, idx) => <TableRowSkeleton key={idx} columns={6} />)
              ) : paginatedActive.length > 0 ? (
                paginatedActive.map((alert) => (
                  <tr
                    key={alert.id}
                    className="border-b border-dark-border/40 hover:bg-slate-800/20 transition-colors duration-150"
                  >
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-[10px] font-extrabold uppercase border ${getSeverityBadgeColor(alert.severity)}`}>
                        {alert.severity}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-[10px] font-extrabold uppercase border ${getStatusBadgeColor(alert.status)}`}>
                        {alert.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-400 font-medium">
                      <div className="flex items-center space-x-1.5 font-mono">
                        <Calendar className="w-3.5 h-3.5 text-dark-muted" />
                        <span>{new Date(alert.created_at).toLocaleDateString()}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-xs font-semibold text-slate-200">
                      {alert.customer ? `${alert.customer.name} (${alert.customer.customer_code})` : 'Unknown Account'}
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-300 font-medium max-w-xs truncate">{alert.title}</td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => handleOpenUpdateModal(alert)}
                        className="inline-flex items-center space-x-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white px-3.5 py-1.5 rounded-lg text-xs font-bold border border-dark-border transition-all focus-visible:ring-2 focus-visible:ring-blue-500"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                        <span>Audit Status</span>
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" className="py-12 text-center text-xs text-dark-muted">
                    {debouncedSearch ? (
                      <div className="space-y-2">
                        <p className="text-slate-300 font-semibold">No active alerts match search criteria "{debouncedSearch}".</p>
                        <button
                          onClick={() => setSearch('')}
                          className="px-3.5 py-1.5 rounded-lg bg-slate-800 text-slate-200 text-xs font-bold border border-dark-border"
                        >
                          Clear Search
                        </button>
                      </div>
                    ) : (
                      'No active anomalies currently flagged in audit queue.'
                    )}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {!loading && filteredActive.length > 0 && (
          <Pagination
            currentPage={activePage}
            totalPages={activeTotalPages}
            totalItems={filteredActive.length}
            pageSize={activePageSize}
            onPageChange={setActivePage}
            onPageSizeChange={(newSize) => {
              setActivePageSize(newSize);
              setActivePage(1);
            }}
          />
        )}
      </div>

      {/* Row 2: Closed & Audited History */}
      <div className="glass-panel p-6 rounded-2xl space-y-6">
        <div className="flex items-center space-x-2.5">
          <CheckCircle className="w-5 h-5 text-emerald-400" />
          <h2 className="text-xl font-bold text-white font-display">Closed & Audited History</h2>
          <span className="text-xs font-mono font-bold bg-emerald-500/10 text-emerald-400 px-2.5 py-0.5 rounded border border-emerald-500/20">
            {filteredResolved.length} Audited
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-dark-border text-[11px] font-bold text-dark-muted uppercase tracking-wider">
                <th className="py-3.5 px-4">Severity</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Resolution Date</th>
                <th className="py-3.5 px-4">Customer Account</th>
                <th className="py-3.5 px-4">Anomaly Title</th>
                <th className="py-3.5 px-4">Auditor Notes</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 4 }).map((_, idx) => <TableRowSkeleton key={idx} columns={6} />)
              ) : paginatedResolved.length > 0 ? (
                paginatedResolved.map((alert) => (
                  <tr
                    key={alert.id}
                    className="border-b border-dark-border/40 hover:bg-slate-800/20 transition-colors duration-150"
                  >
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-[10px] font-extrabold uppercase border ${getSeverityBadgeColor(alert.severity)}`}>
                        {alert.severity}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-[10px] font-extrabold uppercase border ${getStatusBadgeColor(alert.status)}`}>
                        {alert.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-400 font-medium">
                      <div className="flex items-center space-x-1.5 font-mono">
                        <Calendar className="w-3.5 h-3.5 text-dark-muted" />
                        <span>{alert.resolved_at ? new Date(alert.resolved_at).toLocaleDateString() : 'N/A'}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-xs font-semibold text-slate-200">
                      {alert.customer ? `${alert.customer.name} (${alert.customer.customer_code})` : 'Unknown Account'}
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-300 font-medium max-w-xs truncate">{alert.title}</td>
                    <td className="py-3.5 px-4 text-xs text-dark-muted max-w-xs truncate">{alert.notes || 'No auditor notes recorded.'}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" className="py-12 text-center text-xs text-dark-muted">
                    No historical resolutions found matching filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {!loading && filteredResolved.length > 0 && (
          <Pagination
            currentPage={resolvedPage}
            totalPages={resolvedTotalPages}
            totalItems={filteredResolved.length}
            pageSize={resolvedPageSize}
            onPageChange={setResolvedPage}
            onPageSizeChange={(newSize) => {
              setResolvedPageSize(newSize);
              setResolvedPage(1);
            }}
          />
        )}
      </div>

      {/* Audit Status Update Drawer Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/75 backdrop-blur-md" onClick={handleCloseUpdateModal}></div>

          <div className="glass-panel w-full max-w-lg p-6 rounded-3xl relative z-10 space-y-6 border border-slate-700 shadow-2xl animate-fadeIn">
            <div className="flex items-center justify-between border-b border-dark-border pb-4">
              <div>
                <span className="text-[10px] font-mono font-bold text-blue-400 uppercase tracking-widest block">AUDIT DECISION FORM</span>
                <h3 className="text-xl font-bold text-white font-display mt-0.5">Update Anomaly Audit Status</h3>
              </div>
              <button
                onClick={handleCloseUpdateModal}
                className="text-dark-muted hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors focus-visible:ring-2 focus-visible:ring-blue-500"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Validation Error Alert */}
            {validationError && (
              <div className="bg-rose-950/50 border border-rose-500/30 text-rose-300 p-4 rounded-xl flex items-center space-x-2 text-xs">
                <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                <span className="font-semibold">{validationError}</span>
              </div>
            )}

            <form onSubmit={handleUpdateStatus} className="space-y-5 text-left">
              <div className="p-4 rounded-2xl bg-slate-900/80 border border-dark-border text-xs space-y-1">
                <p className="text-[10px] font-bold text-dark-muted uppercase tracking-wider">MONITORED TARGET ACCOUNT</p>
                <p className="font-semibold text-slate-200">{selectedAlert.customer?.name} ({selectedAlert.customer?.customer_code})</p>
                <p className="text-dark-muted mt-2 block leading-relaxed">{selectedAlert.message}</p>
              </div>

              {/* Status Selection */}
              <div className="space-y-1.5">
                <label htmlFor="audit-status-select" className="text-xs font-bold text-slate-300 uppercase tracking-wider block pl-0.5">New Audit Status Code</label>
                <select
                  id="audit-status-select"
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full bg-slate-900 border border-dark-border focus:border-blue-500/50 rounded-xl px-4 py-3 text-xs text-white focus:outline-none transition-all focus-visible:ring-2 focus-visible:ring-blue-500"
                >
                  <option value="open">Open (Unassigned / Pending Review)</option>
                  <option value="investigating">Investigating (Field Crew Dispatched)</option>
                  <option value="resolved">Resolved (Theft Action Confirmed & Remediated)</option>
                  <option value="false_positive">False Positive (Permitted Equipment Load Deviation)</option>
                </select>
              </div>

              {/* Auditor Notes */}
              <div className="space-y-1.5">
                <label htmlFor="auditor-notes-textarea" className="text-xs font-bold text-slate-300 uppercase tracking-wider block pl-0.5">Auditor Field Notes / Rationale</label>
                <textarea
                  id="auditor-notes-textarea"
                  rows="4"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Record investigation details, physical inspection findings, or equipment verification rationale..."
                  className="w-full bg-slate-900 border border-dark-border focus:border-blue-500/50 rounded-xl px-4 py-3 text-xs text-white placeholder-slate-600 focus:outline-none transition-all focus-visible:ring-2 focus-visible:ring-blue-500"
                ></textarea>
                <span className="text-[10px] text-dark-muted block text-right">Required (min 5 chars)</span>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-3 pt-2">
                <button
                  type="button"
                  onClick={handleCloseUpdateModal}
                  className="w-1/2 py-3 rounded-xl border border-dark-border hover:bg-slate-800 text-xs font-bold text-slate-300 transition-all focus-visible:ring-2 focus-visible:ring-blue-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updating || user?.role === 'viewer'}
                  className="w-1/2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white py-3 rounded-xl text-xs font-extrabold flex items-center justify-center space-x-1.5 shadow-lg shadow-blue-600/20 transition-all focus-visible:ring-2 focus-visible:ring-blue-400"
                >
                  {updating ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <>
                      <UserCheck className="w-4 h-4" />
                      <span>Submit Audit Record</span>
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
