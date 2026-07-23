import { useState, useEffect } from 'react';
import api from '../services/api';
import { FileText, Download, Calendar, Plus, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Reports = () => {
  const { user } = useAuth();
  
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  
  // New report form states
  const [title, setTitle] = useState('');
  const [type, setType] = useState('theft_summary');
  const [format, setFormat] = useState('pdf');
  
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const fetchReports = async () => {
    try {
      const response = await api.get('/reports/');
      setReports(response.data);
    } catch (error) {
      console.error('Error fetching reports list:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleGenerateReport = async (e) => {
    e.preventDefault();
    setGenerating(true);
    setSuccessMsg('');
    setErrorMsg('');
    try {
      await api.post('/reports/generate', {
        report_type: type,
        title,
        format,
        parameters: {}
      });
      setSuccessMsg('Report compiled successfully!');
      setTitle('');
      await fetchReports();
    } catch (error) {
      setErrorMsg(error.response?.data?.message || 'Failed to compile report. Verify permissions.');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadReport = async (reportId, filename) => {
    try {
      const response = await api.get(`/reports/${reportId}/download`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Error downloading report file:', error);
      alert('Could not download report file from server.');
    }
  };

  const getReportTypeLabel = (type) => {
    switch (type) {
      case 'theft_summary': return 'Theft Summary';
      case 'risk_assessment': return 'Risk Assessment';
      case 'alert_digest': return 'Alert Digest';
      case 'customer_report': return 'Customer Report';
      default: return 'Custom Report';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case 'failed': return <AlertCircle className="w-4 h-4 text-rose-400" />;
      default: return <RefreshCw className="w-4 h-4 text-amber-400 animate-spin" />;
    }
  };

  const getStatusTextClass = (status) => {
    switch (status) {
      case 'completed': return 'text-emerald-400';
      case 'failed': return 'text-rose-400';
      default: return 'text-amber-400';
    }
  };

  if (loading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-extrabold text-white tracking-tight">Analytics Reports</h1>
        <p className="text-dark-muted mt-2">Generate and download compiled system reports, risk digests, and theft summaries</p>
      </div>

      {/* Grid: Create Report & Reports List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Compiler Form Panel */}
        <div className="glass-panel p-6 rounded-2xl space-y-6">
          <div className="flex items-center space-x-2 border-b border-dark-border pb-4">
            <Plus className="w-5 h-5 text-blue-500" />
            <h3 className="text-xl font-bold text-white">Compile System Report</h3>
          </div>

          {successMsg && (
            <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-4 rounded-xl flex items-center space-x-2">
              <CheckCircle2 className="w-5 h-5" />
              <span className="text-sm font-semibold">{successMsg}</span>
            </div>
          )}
          {errorMsg && (
            <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl flex items-center space-x-2">
              <AlertCircle className="w-5 h-5" />
              <span className="text-sm font-semibold">{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleGenerateReport} className="space-y-5 text-left">
            {/* Title */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block pl-1">Report Title</label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Q3 Electricity Theft Assessment"
                className="w-full bg-slate-900 border border-dark-border focus:border-blue-500/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none transition-all"
              />
            </div>

            {/* Type */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block pl-1">Report Category</label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="w-full bg-slate-900 border border-dark-border focus:border-blue-500/50 rounded-xl px-4 py-3 text-sm text-white focus:outline-none transition-all"
              >
                <option value="theft_summary">Theft Summary</option>
                <option value="risk_assessment">Risk Assessment</option>
                <option value="alert_digest">Alert Digest</option>
                <option value="customer_report">Customer Report</option>
              </select>
            </div>

            {/* Format */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block pl-1">Output Format</label>
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                className="w-full bg-slate-900 border border-dark-border focus:border-blue-500/50 rounded-xl px-4 py-3 text-sm text-white focus:outline-none transition-all"
              >
                <option value="pdf">PDF Document (.pdf)</option>
                <option value="csv">Data Sheet (.csv)</option>
              </select>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={generating || user?.role === 'viewer'}
              className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold py-4 rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-blue-500/10 active:scale-[0.98] transition-all"
            >
              {generating ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <>
                  <FileText className="w-4 h-4" />
                  <span>Compile and Export</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Reports Directory Panel */}
        <div className="glass-panel p-6 rounded-2xl lg:col-span-2 space-y-6">
          <div className="flex items-center space-x-2 border-b border-dark-border pb-4">
            <FileText className="w-5 h-5 text-indigo-400" />
            <h3 className="text-xl font-bold text-white">Exports Directory</h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-dark-border text-xs font-bold text-dark-muted uppercase tracking-wider">
                  <th className="py-4 px-4">Title</th>
                  <th className="py-4 px-4">Category</th>
                  <th className="py-4 px-4">Format</th>
                  <th className="py-4 px-4">Status</th>
                  <th className="py-4 px-4">Created At</th>
                  <th className="py-4 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((report) => (
                  <tr key={report.id} className="border-b border-dark-border/40 hover:bg-slate-800/10 transition-colors duration-150">
                    <td className="py-4 px-4 text-sm font-semibold text-slate-200">{report.title}</td>
                    <td className="py-4 px-4 text-sm text-slate-400">{getReportTypeLabel(report.report_type)}</td>
                    <td className="py-4 px-4 text-xs font-mono text-slate-400 uppercase">{report.format}</td>
                    <td className="py-4 px-4">
                      <div className="flex items-center space-x-1.5 text-sm font-semibold capitalize">
                        {getStatusIcon(report.status)}
                        <span className={getStatusTextClass(report.status)}>{report.status}</span>
                      </div>
                    </td>
                    <td className="py-4 px-4 text-sm text-slate-400 font-medium">
                      <div className="flex items-center space-x-1.5">
                        <Calendar className="w-3.5 h-3.5 text-dark-muted" />
                        <span>{new Date(report.created_at).toLocaleDateString()}</span>
                      </div>
                    </td>
                    <td className="py-4 px-4 text-right">
                      {report.status === 'completed' ? (
                        <button
                          onClick={() => handleDownloadReport(report.id, `export_${report.id}.${report.format}`)}
                          className="inline-flex items-center space-x-1.5 bg-indigo-600/10 hover:bg-indigo-600 text-indigo-400 hover:text-white px-4 py-2 rounded-xl text-xs font-bold border border-indigo-500/20 hover:border-transparent transition-all duration-200"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>Download</span>
                        </button>
                      ) : (
                        <button disabled className="text-dark-muted opacity-40 px-4 py-2 text-xs font-bold">Download</button>
                      )}
                    </td>
                  </tr>
                ))}
                {reports.length === 0 && (
                  <tr>
                    <td colSpan="6" className="py-8 text-center text-sm text-dark-muted">No exports generated. Add a query in the panel.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Reports;
