/**
 * Volume Profile Section Component
 * 
 * Displays volume profile analysis with Point of Control (POC),
 * Value Area High/Low, and volume distribution visualization.
 */

import React from 'react';
import { useVolumeProfile } from '../../hooks/useAnalytics';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import './VolumeProfileSection.css';

interface VolumeProfileSectionProps {
  instrumentId: number;
  symbol: string;
  className?: string;
}

export const VolumeProfileSection: React.FC<VolumeProfileSectionProps> = ({
  instrumentId,
  symbol,
  className = ''
}) => {
  const { data: volumeProfile, isLoading, error, refetch } = useVolumeProfile(instrumentId, {
    timeframe: 'day',
    priceSegments: 50,
    includePointOfControl: true
  });

  if (error) {
    return (
      <div className={`volume-profile-section ${className}`}>
        <div className="volume-profile-section__header">
          <h3 className="volume-profile-section__title">Volume Profile</h3>
        </div>
        <ErrorAlert 
          message="Failed to load volume profile" 
          error={error}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={`volume-profile-section ${className}`}>
        <div className="volume-profile-section__header">
          <h3 className="volume-profile-section__title">Volume Profile</h3>
        </div>
        <div className="volume-profile-section__loading">
          <LoadingSpinner size="medium" />
          <p>Analyzing volume profile...</p>
        </div>
      </div>
    );
  }

  const formatPrice = (price: number): string => {
    return price.toFixed(2);
  };

  const formatVolume = (volume: number): string => {
    if (volume >= 1000000) {
      return `${(volume / 1000000).toFixed(1)}M`;
    } else if (volume >= 1000) {
      return `${(volume / 1000).toFixed(1)}K`;
    }
    return volume.toFixed(0);
  };

  const formatPercentage = (value: number): string => {
    return `${value.toFixed(1)}%`;
  };

  return (
    <div className={`volume-profile-section ${className}`}>
      <div className="volume-profile-section__header">
        <h3 className="volume-profile-section__title">
          Volume Profile - {symbol}
        </h3>
        {volumeProfile?.timestamp && (
          <div className="volume-profile-section__timestamp">
            Timeframe: {volumeProfile.timeframe} | Updated: {new Date(volumeProfile.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
      
      {volumeProfile && (
        <div className="volume-profile-section__content">
          {/* Key Metrics */}
          <div className="volume-metrics">
            <div className="volume-metric-item">
              <div className="volume-metric-item__label">Point of Control</div>
              <div className="volume-metric-item__value volume-metric-item__value--poc">
                ${formatPrice(volumeProfile.poc)}
              </div>
            </div>
            
            <div className="volume-metric-item">
              <div className="volume-metric-item__label">Value Area High</div>
              <div className="volume-metric-item__value volume-metric-item__value--vah">
                ${formatPrice(volumeProfile.valueAreaHigh)}
              </div>
            </div>
            
            <div className="volume-metric-item">
              <div className="volume-metric-item__label">Value Area Low</div>
              <div className="volume-metric-item__value volume-metric-item__value--val">
                ${formatPrice(volumeProfile.valueAreaLow)}
              </div>
            </div>
            
            <div className="volume-metric-item">
              <div className="volume-metric-item__label">Value Area Volume</div>
              <div className="volume-metric-item__value">
                {formatVolume(volumeProfile.valueAreaVolume)}
              </div>
            </div>
          </div>

          {/* Volume Profile Chart */}
          <div className="volume-profile-chart">
            <h4 className="section-subtitle">Volume Distribution</h4>
            
            <div className="volume-chart">
              <div className="volume-chart__y-axis">
                {volumeProfile.profile
                  .slice()
                  .reverse()
                  .map((level, index) => (
                    <div key={index} className="volume-chart__y-label">
                      ${formatPrice(level.priceLevel)}
                    </div>
                  ))}
              </div>
              
              <div className="volume-chart__bars">
                {volumeProfile.profile
                  .slice()
                  .reverse()
                  .map((level, index) => {
                    const isVolumeArea = level.priceLevel >= volumeProfile.valueAreaLow && 
                                       level.priceLevel <= volumeProfile.valueAreaHigh;
                    const isPOC = Math.abs(level.priceLevel - volumeProfile.poc) < 0.01;
                    
                    return (
                      <div key={index} className="volume-chart__bar-container">
                        <div 
                          className={`volume-chart__bar ${
                            isPOC ? 'volume-chart__bar--poc' :
                            isVolumeArea ? 'volume-chart__bar--value-area' :
                            'volume-chart__bar--normal'
                          }`}
                          style={{ 
                            width: `${level.percentage}%`,
                            minWidth: level.percentage > 0 ? '2px' : '0'
                          }}
                          title={`Price: $${formatPrice(level.priceLevel)}, Volume: ${formatVolume(level.volume)}, ${formatPercentage(level.percentage)}`}
                        />
                        <div className="volume-chart__bar-info">
                          <span className="volume-chart__volume">{formatVolume(level.volume)}</span>
                          <span className="volume-chart__percentage">({formatPercentage(level.percentage)})</span>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          </div>

          {/* Top Volume Levels */}
          <div className="top-volume-levels">
            <h4 className="section-subtitle">Top Volume Levels</h4>
            
            <div className="top-levels-list">
              {volumeProfile.profile
                .slice()
                .sort((a, b) => b.volume - a.volume)
                .slice(0, 5)
                .map((level, index) => {
                  const isPOC = Math.abs(level.priceLevel - volumeProfile.poc) < 0.01;
                  const isVolumeArea = level.priceLevel >= volumeProfile.valueAreaLow && 
                                     level.priceLevel <= volumeProfile.valueAreaHigh;
                  
                  return (
                    <div key={index} className="top-level-item">
                      <div className="top-level-item__rank">#{index + 1}</div>
                      <div className="top-level-item__info">
                        <div className="top-level-item__price">
                          ${formatPrice(level.priceLevel)}
                          {isPOC && <span className="top-level-item__badge top-level-item__badge--poc">POC</span>}
                          {!isPOC && isVolumeArea && <span className="top-level-item__badge top-level-item__badge--va">VA</span>}
                        </div>
                        <div className="top-level-item__volume">
                          {formatVolume(level.volume)} ({formatPercentage(level.percentage)})
                        </div>
                      </div>
                      <div className="top-level-item__bar">
                        <div 
                          className="top-level-item__bar-fill"
                          style={{ width: `${(level.percentage / Math.max(...volumeProfile.profile.map(p => p.percentage))) * 100}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>

          {/* Analysis Summary */}
          <div className="volume-analysis">
            <h4 className="section-subtitle">Volume Analysis</h4>
            <div className="volume-analysis__content">
              <p className="volume-analysis__text">
                The Point of Control at <strong>${formatPrice(volumeProfile.poc)}</strong> represents 
                the price level with the highest traded volume, indicating strong support/resistance.
              </p>
              
              <p className="volume-analysis__text">
                The Value Area encompasses {formatPercentage(
                  (volumeProfile.valueAreaVolume / volumeProfile.profile.reduce((sum, level) => sum + level.volume, 0)) * 100
                )} of total volume between <strong>${formatPrice(volumeProfile.valueAreaLow)}</strong> and{' '}
                <strong>${formatPrice(volumeProfile.valueAreaHigh)}</strong>.
              </p>
              
              <p className="volume-analysis__text">
                Volume concentration at these levels suggests potential{' '}
                {volumeProfile.poc > (volumeProfile.valueAreaHigh + volumeProfile.valueAreaLow) / 2 ? 
                  'resistance' : 'support'} zones for future price action.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};