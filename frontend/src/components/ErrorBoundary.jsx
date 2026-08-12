import React from 'react';
import { ShieldAlert, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error(`[DeepGuard ErrorBoundary Catch - ${this.props.viewName || 'Module'}]:`, error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null, showDetails: false });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      const viewName = this.props.viewName || 'Telemetry Module';
      
      return (
        <div className="w-full max-w-4xl mx-auto my-8 p-8 rounded-3xl bg-slate-900/90 border border-red-500/30 shadow-2xl backdrop-blur-xl text-left">
          <div className="flex items-start space-x-5">
            <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 flex-shrink-0">
              <ShieldAlert className="w-8 h-8" />
            </div>
            
            <div className="flex-1 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold tracking-widest uppercase text-red-400 bg-red-500/10 px-2.5 py-1 rounded border border-red-500/20">
                  {viewName} • Telemetry Interrupted
                </span>
                <span className="text-xs text-slate-500 font-mono">STATUS 500_UI_FAULT</span>
              </div>

              <h2 className="text-2xl font-extrabold text-white tracking-tight">
                Control-Room Telemetry View Interrupted
              </h2>
              
              <p className="text-sm text-slate-300 leading-relaxed">
                An unhandled component rendering error occurred in <strong className="text-slate-100">{viewName}</strong>. To ensure zero operational loss, neighboring grid components remain active.
              </p>

              {/* Retry & Details Controls */}
              <div className="pt-4 flex items-center space-x-4">
                <button
                  onClick={this.handleReset}
                  className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white font-extrabold text-sm px-5 py-3 rounded-xl shadow-lg shadow-blue-600/20 transition-all duration-200 focus-visible:ring-2 focus-visible:ring-blue-400"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Retry Loading View</span>
                </button>

                <button
                  onClick={() => this.setState(prev => ({ showDetails: !prev.showDetails }))}
                  className="flex items-center space-x-1.5 bg-slate-800/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs font-semibold px-4 py-3 rounded-xl border border-slate-700 transition-all"
                >
                  <span>{this.state.showDetails ? 'Hide Diagnostics' : 'Show Diagnostics'}</span>
                  {this.state.showDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
              </div>

              {/* Stack Trace Accordion */}
              {this.state.showDetails && (
                <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-red-300 overflow-x-auto space-y-2">
                  <p className="font-bold text-slate-200">{this.state.error && this.state.error.toString()}</p>
                  <pre className="text-[11px] text-slate-400 leading-normal whitespace-pre-wrap">
                    {this.state.errorInfo && this.state.errorInfo.componentStack}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
