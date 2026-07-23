import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ArrowLeft, BrainCircuit, Activity, CloudSun, Calendar, ShieldCheck, Zap, HardDrive } from 'lucide-react';

const CustomerDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [customer, setCustomer] = useState(null);
  const [readings, setReadings] = useState([]);
  const [history, setHistory] = useState([]);
  const [weatherAnalysis, setWeatherAnalysis] = useState(null);
  
  const [loading, setLoading] = useState(true);
  const [predicting, setPredicting] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const fetchData = async () => {
    try {
      const [custRes, readingsRes, historyRes, weatherRes] = await Promise.all([
        api.get(`/customers/${id}`),
        api.get(`/customers/${id}/consumption`),
        api.get(`/predictions/customer/${id}`),
        api.get(`/weather/analysis/${id}`)
      ]);

      setCustomer(custRes.data);
      
      // Map readings for Recharts
      const formattedReadings = readingsRes.data.readings.map(r => ({
        date: new Date(r.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
        load: parseFloat(r.consumption_kwh),
        flag: r.quality_flag
      }));
      setReadings(formattedReadings);
      setHistory(historyRes.data);
      setWeatherAnalysis(weatherRes.data);
    } catch (error) {
      console.error('Error fetching customer details:', error);
      setErrorMsg('Failed to load profile details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleRunPrediction = async () => {
    setPredicting(true);
    setSuccessMsg('');
    setErrorMsg('');
    try {
      const response = await api.post('/predictions/run', { customer_id: parseInt(id) });
      setSuccessMsg('Prediction model executed successfully!');
      
      // Refresh prediction history
      const historyRes = await api.get(`/predictions/customer/${id}`);
      setHistory(historyRes.data);
    } catch (error) {
      setErrorMsg(error.response?.data?.message || 'Error occurred while running models.');
    } finally {
      setPredicting(false);
    }
  };

  const getRiskLevelColor = (level) => {
    switch (level.toLowerCase()) {
      case 'low': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      case 'medium': return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      case 'high': return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
      case 'critical': return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
      default: return 'text-slate-400 bg-slate-500/10 border-slate-500/20';
    }
  };

  const getRiskDotColor = (level) => {
    switch (level.toLowerCase()) {
      case 'low': return '#10B981';
      case 'medium': return '#F59E0B';
      case 'high': return '#F97316';
      case 'critical': return '#EF4444';
      default: return '#94A3B8';
    }
  };

  if (loading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const latestPrediction = history[0];

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
      {/* Back to list and Actions */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/')}
          className="flex items-center space-x-2 text-dark-muted hover:text-slate-200 transition-colors duration-150"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-sm font-semibold">Back to directory</span>
        </button>
        
        {/* Run Prediction Trigger */}
        <button
          onClick={handleRunPrediction}
          disabled={predicting}
          className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-extrabold px-6 py-3.5 rounded-2xl shadow-lg shadow-blue-500/10 hover:shadow-blue-500/20 transition-all duration-150"
        >
          {predicting ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <>
              <BrainCircuit className="w-4 h-4" />
              <span>Trigger AI Prediction</span>
            </>
          )}
        </button>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-4 rounded-2xl flex items-center space-x-3">
          <ShieldCheck className="w-5 h-5 flex-shrink-0" />
          <span className="text-sm font-medium">{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-2xl flex items-center space-x-3">
          <Activity className="w-5 h-5 flex-shrink-0" />
          <span className="text-sm font-medium">{errorMsg}</span>
        </div>
      )}

      {/* Customer overview header */}
      {customer && (
        <div className="glass-panel p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="text-left space-y-2">
            <div className="flex items-center space-x-3">
              <span className="font-mono text-sm font-bold text-blue-400 bg-blue-500/10 px-3 py-1 rounded-lg border border-blue-500/10">{customer.customer_code}</span>
              <h2 className="text-3xl font-extrabold text-white leading-tight">{customer.name}</h2>
            </div>
            <p className="text-sm text-slate-400">{customer.address}, {customer.city}</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            <div className="text-left border-l border-dark-border pl-4">
              <span className="text-[10px] font-bold text-dark-muted uppercase tracking-wider block">Region</span>
              <span className="text-sm font-bold text-slate-300 mt-1 block">{customer.region}</span>
            </div>
            <div className="text-left border-l border-dark-border pl-4">
              <span className="text-[10px] font-bold text-dark-muted uppercase tracking-wider block">Connection Type</span>
              <span className="text-sm font-bold text-slate-300 mt-1 block capitalize">{customer.connection_type}</span>
            </div>
            <div className="text-left border-l border-dark-border pl-4">
              <span className="text-[10px] font-bold text-dark-muted uppercase tracking-wider block">Latest Risk Index</span>
              {latestPrediction ? (
                <span className={`inline-block text-xs font-extrabold uppercase mt-1 px-2.5 py-0.5 rounded border ${getRiskLevelColor(latestPrediction.risk_level)}`}>
                  {latestPrediction.risk_score} - {latestPrediction.risk_level}
                </span>
              ) : (
                <span className="text-xs text-dark-muted mt-1 block font-semibold">Not Scanned</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Row 2: Graph & Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Load History Chart */}
        <div className="glass-panel p-6 rounded-2xl lg:col-span-2 space-y-6">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center space-x-2">
              <Zap className="w-5 h-5 text-yellow-500" />
              <span>14-Day Consumption Timeline</span>
            </h3>
            <p className="text-xs text-dark-muted mt-1">Daily energy consumption levels measured in kilowatt-hours (kWh)</p>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={readings} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="loadColor" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                <XAxis dataKey="date" stroke="#94A3B8" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#94A3B8" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: '#121824', borderColor: '#1E293B', borderRadius: '12px', fontSize: '12px' }} />
                <Area type="monotone" dataKey="load" stroke="#3B82F6" strokeWidth={2} fillOpacity={1} fill="url(#loadColor)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Weather & Diagnostics */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between">
          <div className="space-y-6">
            <div>
              <h3 className="text-xl font-bold text-white flex items-center space-x-2">
                <CloudSun className="w-5 h-5 text-indigo-400" />
                <span>Weather Correlation</span>
              </h3>
              <p className="text-xs text-dark-muted mt-1">Monitors how load changes track ambient local temperature peaks</p>
            </div>
            
            {weatherAnalysis ? (
              <div className="space-y-5 text-left">
                <div className="p-4 rounded-xl bg-slate-900/60 border border-dark-border">
                  <span className="text-[10px] font-bold text-dark-muted uppercase tracking-wider block">Correlation Index</span>
                  <div className="flex items-baseline space-x-2 mt-1.5">
                    <h4 className="text-3xl font-black text-white">{weatherAnalysis.correlation_coefficient}</h4>
                    <span className="text-xs text-emerald-400 font-bold">Normal</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-dark-muted uppercase tracking-wider block">System Diagnostics</span>
                  <p className="text-sm text-slate-300 leading-normal">{weatherAnalysis.interpretation}</p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-dark-muted text-center py-10">Weather correlation statistics unavailable.</p>
            )}
          </div>

          <div className="p-4 rounded-xl bg-slate-800/20 border border-dark-border text-left flex items-start space-x-3">
            <HardDrive className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="leading-tight">
              <span className="text-xs font-bold text-slate-300">Meter Infrastructure</span>
              <p className="text-xs text-dark-muted mt-1">Smart meter SM-2024 active. Install date: Jan 15, 2023.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Row 3: Predictions History */}
      <div className="glass-panel p-6 rounded-2xl space-y-6">
        <div>
          <h3 className="text-xl font-bold text-white">Neural Network Prediction History</h3>
          <p className="text-xs text-dark-muted mt-1">Individual neural network model outputs along with final ensemble consensus scores</p>
        </div>

        {/* Prediction Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-dark-border text-xs font-bold text-dark-muted uppercase tracking-wider">
                <th className="py-4 px-4">Evaluation Date</th>
                <th className="py-4 px-4">Bi-LSTM Prob</th>
                <th className="py-4 px-4">Transformer Prob</th>
                <th className="py-4 px-4">Fused Probability</th>
                <th className="py-4 px-4">Risk Score</th>
                <th className="py-4 px-4">Risk Level</th>
                <th className="py-4 px-4">Model Version</th>
              </tr>
            </thead>
            <tbody>
              {history.map((pred) => (
                <tr key={pred.id} className="border-b border-dark-border/40 hover:bg-slate-800/10 transition-colors duration-150">
                  <td className="py-4 px-4 text-sm font-semibold text-slate-300 flex items-center space-x-2">
                    <Calendar className="w-4 h-4 text-dark-muted" />
                    <span>{new Date(pred.predicted_at).toLocaleString()}</span>
                  </td>
                  <td className="py-4 px-4 text-sm font-mono text-slate-400">{(pred.bilstm_score * 100).toFixed(1)}%</td>
                  <td className="py-4 px-4 text-sm font-mono text-slate-400">{(pred.transformer_score * 100).toFixed(1)}%</td>
                  <td className="py-4 px-4 text-sm font-mono text-slate-300 font-semibold">{(pred.fused_score * 100).toFixed(1)}%</td>
                  <td className="py-4 px-4 text-sm font-black text-white">{pred.risk_score}<span className="text-xs font-normal text-dark-muted">/100</span></td>
                  <td className="py-4 px-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-extrabold uppercase border ${getRiskLevelColor(pred.risk_level)}`}>
                      {pred.risk_level}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-xs font-mono text-dark-muted">{pred.model_version}</td>
                </tr>
              ))}
              {history.length === 0 && (
                <tr>
                  <td colSpan="7" className="py-8 text-center text-sm text-dark-muted">No security evaluation history found. Run AI Prediction to scan.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default CustomerDetail;
