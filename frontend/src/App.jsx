import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import OfflineBanner from './components/OfflineBanner';
import ErrorBoundary from './components/ErrorBoundary';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import CustomerDetail from './pages/CustomerDetail';
import Alerts from './pages/Alerts';
import Reports from './pages/Reports';
import NetworkRiskMap from './pages/NetworkRiskMap';

// Layout wrapper that adds the Sticky Offline Banner and Navbar for logged-in sessions
const Layout = () => {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-dark-bg text-slate-100 flex flex-col selection:bg-blue-600/30 selection:text-white">
      <OfflineBanner />
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
};

function AppRoutes() {
  return (
    <Routes>
      {/* Public Route */}
      <Route
        path="/login"
        element={
          <ErrorBoundary viewName="Login Module">
            <Login />
          </ErrorBoundary>
        }
      />

      {/* Protected Routes Wrapper */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route
            path="/"
            element={
              <ErrorBoundary viewName="System Overview Dashboard">
                <Dashboard />
              </ErrorBoundary>
            }
          />
          <Route
            path="/customer/:id"
            element={
              <ErrorBoundary viewName="Customer Audit Profile">
                <CustomerDetail />
              </ErrorBoundary>
            }
          />
          <Route
            path="/alerts"
            element={
              <ErrorBoundary viewName="Audit Alerts Queue">
                <Alerts />
              </ErrorBoundary>
            }
          />
          <Route
            path="/reports"
            element={
              <ErrorBoundary viewName="Executive Reports Module">
                <Reports />
              </ErrorBoundary>
            }
          />
          <Route
            path="/network"
            element={
              <ErrorBoundary viewName="3D Network Risk Spatial Map">
                <NetworkRiskMap />
              </ErrorBoundary>
            }
          />
        </Route>
      </Route>

      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}

export default App;
