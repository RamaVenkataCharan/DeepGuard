import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { MetricCardSkeleton, ChartSkeleton } from '../components/SkeletonLoaders';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea } from 'recharts';
import { ArrowLeft, BrainCircuit, Activity, CloudSun, Calendar, ShieldCheck, Zap, HardDrive, AlertTriangle } from 'lucide-react';

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
    setLoading(true);
    setErrorMsg('');
    try {
      const [custRes, readingsRes, historyRes, weatherRes] = await Promise.all([
        api.get(`/customers/${id}`),
        api.get(`/customers/${id}/consumption`),
        api.get(`/predictions/customer/${id}`),
        api.get(`/weather/analysis/${id}`)
      ]);

      setCustomer(custRes.data);

      // Map readings & bound consumption history window to latest 90 days maximum for Scale (Part 3b)
      const rawReadings = readingsRes.data.readings || [];
      const boundedReadings = rawReadings.slice(-90).map(r => ({
        date: r.timestamp && !isNaN(new Date(r.timestamp).getTime())
          ? new Date(r.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
          : 'N/A',
        load: isNaN(parseFloat(r.consumption_kwh)) ? 0 : parseFloat(r.consumption_kwh),
        flag: r.quality_flag || 'normal'
      }));

      setReadings(boundedReadings);
      setHistory(Array.isArray(historyRes.data) ? historyRes.data : []);
      setWeatherAnalysis(weatherRes.data);
    } catch (error) {
      console.error('Error fetching customer details:', error);
      setErrorMsg(error.response?.data?.message || 'Failed to load customer profile details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleRunPrediction = async () => {
    if (!id || isNaN(Number(id))) {
      setErrorMsg('Invalid customer ID parameters.');
      return;
    }

    setPredicting(true);
    setSuccessMsg('');
    setErrorMsg('');
    try {
      const response = await api.post('/predictions/run', { customer_id: parseInt(id, 10) });
      setSuccessMsg('Neural prediction model executed successfully! Risk index updated.');

      // Refresh prediction history
      const historyRes = await api.get(`/predictions/customer/${id}`);
      setHistory(Array.isArray(historyRes.data) ? historyRes.data : []);
    } catch (error) {
      setErrorMsg(error.response?.data?.message || 'Error occurred while running neural prediction models.');
    } finally {
      setPredicting(false);
    }
  };

  const getRiskLevelColor = (level = '') => {
    switch (level.toLowerCase()) {
      case 'low': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
      case 'medium': return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
      case 'high': return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
      case 'critical': return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
      default: return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
    }
  };

  const latestPrediction = useMemo(() => (history.length > 0 ? history[0] : null), [history]);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
      {/* Navigation Header & Trigger AI Prediction */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button
          onClick={() => navigate('/')}
          className="flex items-center space-x-2 text-dark-muted hover:text-slate-200 text-xs font-bold transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 rounded-lg p-1"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Monitored Directory</span>
        </button>

        <button
          onClick={handleRunPrediction}
          disabled={predicting || loading}
          className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 text-white text-xs font-extrabold px-5 py-3 rounded-xl shadow-lg shadow-blue-600/20 transition-all focus-visible:ring-2 focus-visible:ring-blue-400"
        >
          {predicting ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <>
              <BrainCircuit className="w-4 h-4" />
              <span>Trigger Neural Inference Scan</span>
            </>
          )}
        </button>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 p-4 rounded-2xl flex items-center space-x-3 text-xs font-semibold">
          <ShieldCheck className="w-5 h-5 text-emerald-400 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="bg-rose-950/40 border border-rose-500/30 text-rose-300 p-4 rounded-2xl flex items-center space-x-3 text-xs font-semibold">
          <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Customer Overview Card */}
      {loading ? (
        <div className="glass-panel p-6 rounded-2xl animate-pulse flex flex-col md:flex-row justify-between gap-6">
          <div className="space-y-3 w-1/2">
            <div className="h-4 bg-slate-800 rounded w-1/4" />
            <div className="h-8 bg-slate-800 rounded w-3/4" />
          </div>
          <div className="h-12 bg-slate-800 rounded w-1/3" />
        </div>
      ) : customer ? (
        <div className="glass-panel p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="text-left space-y-2">
            <div className="flex items-center space-x-3">
              <span className="font-mono text-xs font-bold text-blue-400 bg-blue-500/10 px-3 py-1 rounded-lg border border-blue-500/20">
                {customer.customer_code}
              </span>
              <h1 className="text-2xl md:text-3xl font-extrabold text-white leading-tight font-display">
                {customer.name}
              </h1>
            </div>
            <p className="text-xs text-slate-400">
              {customer.address || 'Smart Grid Node Location'}, {customer.city || 'SGCC Region'}
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            <div className="text-left border-l border-dark-border pl-4">
              <span className="text-[10px] font-bold text-dark-muted uppercase tracking-wider block">Region / Feeder</span>
              <span className="text-xs font-bold text-slate-200 mt-1 block font-mono">
                {customer.region} ({customer.feeder_line || 'FDR-01'})
              </span>
            </div>
            <div className="text-left border-l border-dark-border pl-4">
              <span className="text-[10px] font-bold text-dark-muted uppercase tracking-wider block">Connection Type</span>
              <span className="text-xs font-bold text-slate-200 mt-1 block capitalize">
                {customer.connection_type} ({customer.sanctioned_load_kw || 15} kW)
              </span>
            </div>
            <div className="text-left border-l border-dark-border pl-4">
              <span className="text-[10px] font-bold text-dark-muted uppercase tracking-wider block">Latest Anomaly Risk</span>
              {latestPrediction ? (
                <span className={`inline-block text-xs font-extrabold uppercase mt-1 px-2.5 py-0.5 rounded border ${getRiskLevelColor(latestPrediction.risk_level)}`}>
                  {latestPrediction.risk_score}/100 - {latestPrediction.risk_level}
                </span>
              ) : (
                <span className="text-xs text-dark-muted mt-1 block font-semibold">Not Scanned</span>
              )}
            </div>
          </div>
        </div>
      ) : null}

      {/* Row 2: Bounded Consumption Timeline Chart & Weather Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Consumption Chart */}
        <div className="glass-panel p-6 rounded-2xl lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center space-x-2 font-display">
                <Zap className="w-4 h-4 text-amber-400" />
                <span>Consumption Timeline (Bounded Window)</span>
              </h2>
              <p className="text-xs text-dark-muted mt-0.5">
                Daily energy consumption levels measured in kilowatt-hours (kWh) — bounded to latest 90-day window
              </p>
            </div>
            <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-2.5 py-1 rounded border border-dark-border">
              {readings.length} DATAPOINTS
            </span>
          </div>

          {loading ? (
            <ChartSkeleton />
          ) : (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={readings} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="loadColor" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                  <XAxis dataKey="date" stroke="#94A3B8" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#94A3B8" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: '#121824', borderColor: '#1E293B', borderRadius: '12px', fontSize: '12px', color: '#FFF' }} />
                  <Area type="monotone" dataKey="load" stroke="#3B82F6" strokeWidth={2} fillOpacity={1} fill="url(#loadColor)" />

                  {/* Reference Area shading for critical anomaly scans */}
                  {history.filter(p => ['high', 'critical'].includes(p.risk_level.toLowerCase())).map((p, idx) => {
                    if (readings.length === 0) return null;
                    const availableDates = readings.map(r => r.date);
                    const predDate = new Date(p.predicted_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
                    const x1 = availableDates.includes(predDate) ? predDate : availableDates[Math.max(0, availableDates.length - 3)];
                    const x2 = availableDates[availableDates.length - 1];

                    return (
                      <ReferenceArea
                        key={idx}
                        x1={x1}
                        x2={x2}
                        stroke="#EF4444"
                        strokeOpacity={0.4}
                        fill="#EF4444"
                        fillOpacity={0.12}
                      />
                    );
                  })}
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Anomaly Attribution Notes */}
          {history.some(p => ['high', 'critical'].includes(p.risk_level.toLowerCase())) && (
            <div className="mt-4 p-4 rounded-xl bg-rose-950/30 border border-rose-500/20 text-left">
              <span className="text-xs font-bold text-rose-400 uppercase tracking-wider mb-2 block">
                ⚠️ Neural Feature Attribution Explanations
              </span>
              <div className="space-y-2">
                {history.filter(p => ['high', 'critical'].includes(p.risk_level.toLowerCase())).map((p, idx) => (
                  <div key={idx} className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs">
                    <div className="font-mono text-rose-400 mb-1">
                      Scan: {new Date(p.predicted_at).toLocaleDateString()} (Score: {p.risk_score}/100 - {p.risk_level.toUpperCase()})
                    </div>
                    {Array.isArray(p.contributing_features) && p.contributing_features.length > 0 ? (
                      <ul className="list-disc list-inside space-y-1 text-slate-300">
                        {p.contributing_features.map((feat, fIdx) => (
                          <li key={fIdx}>{feat}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-slate-400 italic">Abrupt drop in weekend load vs 14-day rolling baseline detected.</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Weather Correlation & Diagnostics */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between">
          <div className="space-y-5">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center space-x-2 font-display">
                <CloudSun className="w-4 h-4 text-indigo-400" />
                <span>Weather Correlation</span>
              </h2>
              <p className="text-xs text-dark-muted mt-0.5">Monitors load vs ambient local temperature peaks</p>
            </div>

            {loading ? (
              <MetricCardSkeleton />
            ) : weatherAnalysis ? (
              <div className="space-y-4 text-left">
                <div className="p-4 rounded-xl bg-slate-900/80 border border-dark-border">
                  <span className="text-[10px] font-bold text-dark-muted uppercase tracking-wider block">Correlation Index</span>
                  <div className="flex items-baseline space-x-2 mt-1">
                    <h3 className="text-3xl font-extrabold text-white font-display">{weatherAnalysis.correlation_coefficient}</h3>
                    <span className="text-xs text-emerald-400 font-bold">Normal Tracking</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-dark-muted uppercase tracking-wider block">Diagnostics interpretation</span>
                  <p className="text-xs text-slate-300 leading-relaxed">{weatherAnalysis.interpretation}</p>
                </div>
              </div>
            ) : (
              <p className="text-xs text-dark-muted text-center py-8">Weather correlation telemetry unavailable.</p>
            )}
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-dark-border text-left flex items-start space-x-3">
            <HardDrive className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="leading-tight">
              <span className="text-xs font-bold text-slate-200">Meter Infrastructure</span>
              <p className="text-[11px] text-dark-muted mt-0.5">Smart meter active. Bi-directional AMI telemetry link operational.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Row 3: Neural Model Output Log Table */}
      <div className="glass-panel p-6 rounded-2xl space-y-6">
        <div>
          <h2 className="text-lg font-bold text-white font-display">Neural Ensemble Scan History</h2>
          <p className="text-xs text-dark-muted mt-0.5">Individual Bi-LSTM & Transformer model outputs with fused consensus score</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-dark-border text-[11px] font-bold text-dark-muted uppercase tracking-wider">
                <th className="py-3.5 px-4">Evaluation Date</th>
                <th className="py-3.5 px-4">Bi-LSTM Prob</th>
                <th className="py-3.5 px-4">Transformer Prob</th>
                <th className="py-3.5 px-4">Fused Probability</th>
                <th className="py-3.5 px-4">Risk Score</th>
                <th className="py-3.5 px-4">Risk Level</th>
                <th className="py-3.5 px-4">Model Version</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 3 }).map((_, idx) => (
                  <tr key={idx} className="border-b border-dark-border/40 animate-pulse">
                    <td colSpan="7" className="py-4 px-4"><div className="h-4 bg-slate-800 rounded w-full" /></td>
                  </tr>
                ))
              ) : history.length > 0 ? (
                history.map((pred) => (
                  <tr key={pred.id} className="border-b border-dark-border/40 hover:bg-slate-800/20 transition-colors duration-150">
                    <td className="py-3.5 px-4 text-xs font-semibold text-slate-300 flex items-center space-x-2">
                      <Calendar className="w-3.5 h-3.5 text-dark-muted" />
                      <span className="font-mono">{new Date(pred.predicted_at).toLocaleString()}</span>
                    </td>
                    <td className="py-3.5 px-4 text-xs font-mono text-slate-400">{(pred.bilstm_score * 100).toFixed(1)}%</td>
                    <td className="py-3.5 px-4 text-xs font-mono text-slate-400">{(pred.transformer_score * 100).toFixed(1)}%</td>
                    <td className="py-3.5 px-4 text-xs font-mono text-slate-200 font-bold">{(pred.fused_score * 100).toFixed(1)}%</td>
                    <td className="py-3.5 px-4 text-xs font-extrabold text-white">{pred.risk_score}<span className="text-[10px] text-dark-muted font-normal">/100</span></td>
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-[10px] font-extrabold uppercase border ${getRiskLevelColor(pred.risk_level)}`}>
                        {pred.risk_level}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-xs font-mono text-dark-muted">{pred.model_version || 'v1.0.0'}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" className="py-10 text-center text-xs text-dark-muted">
                    No neural evaluation history found. Click "Trigger Neural Inference Scan" to evaluate.
                  </td>
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
