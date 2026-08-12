import React, { useState, useEffect } from 'react';
import { WifiOff, RefreshCw, AlertTriangle } from 'lucide-react';
import { subscribeNetworkStatus, checkApiHealth } from '../services/api';

const OfflineBanner = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [apiUnreachable, setApiUnreachable] = useState(false);
  const [rechecking, setRechecking] = useState(false);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Subscribe to API custom status events dispatched from axios interceptors
    const unsubscribe = subscribeNetworkStatus((status) => {
      setApiUnreachable(!status.reachable);
    });

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      unsubscribe();
    };
  }, []);

  const handleManualRecheck = async () => {
    setRechecking(true);
    const reachable = await checkApiHealth();
    setApiUnreachable(!reachable);
    setRechecking(false);
  };

  const isDisconnected = !isOnline || apiUnreachable;

  if (!isDisconnected) return null;

  return (
    <div className="bg-rose-950/90 border-b border-rose-500/40 text-rose-200 px-6 py-2.5 flex items-center justify-between shadow-xl backdrop-blur-md sticky top-0 z-[60] animate-fadeIn">
      <div className="flex items-center space-x-3 text-xs md:text-sm font-semibold">
        <div className="p-1 rounded bg-rose-500/20 text-rose-400 animate-pulse">
          <WifiOff className="w-4 h-4" />
        </div>
        <div>
          <span className="font-extrabold uppercase tracking-wider text-white mr-2">
            {!isOnline ? 'NETWORK DISCONNECTED' : 'BACKEND TELEMETRY UNREACHABLE'}
          </span>
          <span className="text-rose-300/80 hidden sm:inline">
            {!isOnline
              ? 'Your device lost network connectivity. Telemetry updates paused.'
              : 'DeepGuard backend service is not responding. Automatic retries active.'}
          </span>
        </div>
      </div>

      <button
        onClick={handleManualRecheck}
        disabled={rechecking}
        className="flex items-center space-x-1.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-100 text-xs font-bold px-3 py-1.5 rounded-lg border border-rose-500/30 transition-all disabled:opacity-50"
      >
        <RefreshCw className={`w-3.5 h-3.5 ${rechecking ? 'animate-spin' : ''}`} />
        <span>{rechecking ? 'Checking...' : 'Recheck Status'}</span>
      </button>
    </div>
  );
};

export default OfflineBanner;
