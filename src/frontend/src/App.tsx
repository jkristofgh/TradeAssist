import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { WebSocketProvider } from './context/WebSocketContext';
import Dashboard from './components/Dashboard/Dashboard';
import RuleManagement from './components/Rules/RuleManagement';
import AlertHistory from './components/History/AlertHistory';
import SystemHealth from './components/Health/SystemHealth';
import HistoricalDataPage from './components/HistoricalData/HistoricalDataPage';
import { AnalyticsDashboard } from './components/Analytics/AnalyticsDashboard';
import { OAuthCallback } from './components/Auth/OAuthCallback';
import { AuthenticationPanel } from './components/Auth/AuthenticationPanel';

const App: React.FC = () => {
  const location = useLocation();

  return (
    <div className="app">
      <AuthProvider>
        <WebSocketProvider>
          <div className="container">
            <header className="app-header">
              <div className="header-content">
                <h1 className="app-title">TradeAssist Dashboard</h1>
                
                <nav className="main-nav">
                  <Link 
                    to="/" 
                    className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
                  >
                    Dashboard
                  </Link>
                  <Link 
                    to="/rules" 
                    className={`nav-link ${location.pathname === '/rules' ? 'active' : ''}`}
                  >
                    Alert Rules
                  </Link>
                  <Link 
                    to="/history" 
                    className={`nav-link ${location.pathname === '/history' ? 'active' : ''}`}
                  >
                    History
                  </Link>
                  <Link 
                    to="/historical-data" 
                    className={`nav-link ${location.pathname === '/historical-data' ? 'active' : ''}`}
                  >
                    Historical Data
                  </Link>
                  <Link 
                    to="/analytics" 
                    className={`nav-link ${location.pathname === '/analytics' ? 'active' : ''}`}
                  >
                    Analytics
                  </Link>
                  <Link 
                    to="/auth" 
                    className={`nav-link ${location.pathname === '/auth' ? 'active' : ''}`}
                  >
                    Authentication
                  </Link>
                  <Link 
                    to="/health" 
                    className={`nav-link ${location.pathname === '/health' ? 'active' : ''}`}
                  >
                    System Health
                  </Link>
                </nav>
              </div>
            </header>
            
            <main className="app-main">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/rules" element={<RuleManagement />} />
                <Route path="/history" element={<AlertHistory />} />
                <Route path="/historical-data" element={<HistoricalDataPage />} />
                <Route path="/analytics" element={<AnalyticsDashboard />} />
                <Route path="/auth" element={<AuthenticationPanel />} />
                <Route path="/callback" element={<OAuthCallback />} />
                <Route path="/health" element={<SystemHealth />} />
              </Routes>
            </main>
          </div>
        </WebSocketProvider>
      </AuthProvider>
    </div>
  );
};

export default App;