/**
 * Dashboard Component
 * 
 * Main trading dashboard providing real-time instrument monitoring,
 * recent alerts, and quick access to alert rule management.
 */

import React from 'react';
import InstrumentWatchlist from './InstrumentWatchlist';
import RealTimeStatus from './RealTimeStatus';

interface DashboardProps {
  className?: string;
}

const Dashboard: React.FC<DashboardProps> = ({ className = '' }) => {
  const handleAddAlert = (instrumentId: number) => {
    // TODO: Open alert rule creation modal/form
    console.log('Add alert for instrument:', instrumentId);
  };

  return (
    <div className={`dashboard ${className}`}>
      <div className="dashboard-header">
        <h1>Trading Dashboard</h1>
        <RealTimeStatus />
      </div>
      
      <div className="dashboard-content">
        <div className="dashboard-grid">
          <div className="watchlist-section">
            <InstrumentWatchlist
              onAddAlert={handleAddAlert}
              maxInstruments={15}
              showAddButton={true}
            />
          </div>
          
          <div className="alerts-section">
            {/* Recent alerts will be added later */}
            <div className="card">
              <h3>Recent Alerts</h3>
              <p>Recent alerts component coming soon...</p>
            </div>
          </div>
        </div>
        
        <div className="stats-section">
          {/* System stats will be added later */}
          <div className="card">
            <h3>System Statistics</h3>
            <p>System statistics component coming soon...</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;