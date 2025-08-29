/**
 * Volume Profile Component
 * 
 * Displays volume profile analysis with Point of Control and Value Area
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface VolumeProfileProps {
  instrumentId: number;
  lookbackHours: number;
}

interface VolumeProfileData {
  timestamp: string;
  point_of_control: number;
  value_area_high: number;
  value_area_low: number;
  total_volume: number;
  price_levels: number[];
  volume_at_price: number[];
}

const VolumeProfile: React.FC<VolumeProfileProps> = ({ instrumentId, lookbackHours }) => {
  const [profileData, setProfileData] = useState<VolumeProfileData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const fetchVolumeProfile = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/v1/analytics/volume-profile', {
        instrument_id: instrumentId,
        lookback_hours: lookbackHours,
        price_bins: 50
      });
      setProfileData(response.data);
    } catch (error) {
      console.error('Failed to fetch volume profile:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVolumeProfile();
  }, [instrumentId, lookbackHours]);

  if (loading) {
    return <div className="loading">Loading volume profile...</div>;
  }

  if (!profileData) {
    return <div className="no-data">Unable to generate volume profile</div>;
  }

  const maxVolume = Math.max(...profileData.volume_at_price);

  return (
    <div className="volume-profile">
      <div className="profile-header">
        <h2>Volume Profile</h2>
        <div className="profile-stats">
          <div className="stat">
            <label>POC:</label>
            <span>${profileData.point_of_control.toFixed(4)}</span>
          </div>
          <div className="stat">
            <label>Value Area:</label>
            <span>${profileData.value_area_low.toFixed(4)} - ${profileData.value_area_high.toFixed(4)}</span>
          </div>
          <div className="stat">
            <label>Total Volume:</label>
            <span>{profileData.total_volume.toLocaleString()}</span>
          </div>
        </div>
      </div>

      <div className="profile-chart">
        <div className="price-axis">
          {profileData.price_levels.map((price, index) => (
            <div key={index} className="price-level" style={{ top: `${index * 2}px` }}>
              {price.toFixed(4)}
            </div>
          ))}
        </div>
        
        <div className="volume-bars">
          {profileData.volume_at_price.map((volume, index) => {
            const width = (volume / maxVolume) * 100;
            const price = profileData.price_levels[index];
            const isPOC = Math.abs(price - profileData.point_of_control) < 0.001;
            const isValueArea = price >= profileData.value_area_low && price <= profileData.value_area_high;
            
            return (
              <div 
                key={index} 
                className={`volume-bar ${isPOC ? 'poc' : ''} ${isValueArea ? 'value-area' : ''}`}
                style={{ 
                  width: `${width}%`,
                  height: '2px',
                  marginBottom: '1px'
                }}
                title={`Price: ${price.toFixed(4)}, Volume: ${volume}`}
              />
            );
          })}
        </div>
      </div>

      <div className="profile-legend">
        <div className="legend-item">
          <div className="legend-color poc"></div>
          <span>Point of Control (POC)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color value-area"></div>
          <span>Value Area (70% of volume)</span>
        </div>
      </div>
    </div>
  );
};

export default VolumeProfile;