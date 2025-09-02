/**
 * Historical Data Page Component
 * 
 * Main page for historical data functionality with tab navigation
 * between new queries and saved queries.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from '../../context/WebSocketContext';
import { historicalDataService } from '../../services/historicalDataService';
import { notificationService } from '../../services/notificationService';
import QueryForm from './QueryForm';
import DataPreview from './DataPreview';
import SavedQueries from './SavedQueries';
import {
  HistoricalDataQuery,
  SavedQuery,
  DataFrequency,
  SaveQueryRequest,
  HistoricalDataPageProps
} from '../../types/historicalData';
import {
  MarketDataBar,
  SymbolDataResponse
} from '../../services/historicalDataService';
import './HistoricalDataPage.css';

const HistoricalDataPage: React.FC<HistoricalDataPageProps> = ({ defaultTab = 'new' }) => {
  // =============================================================================
  // STATE
  // =============================================================================
  
  const [activeTab, setActiveTab] = useState<'new' | 'saved'>(defaultTab);
  const [isLoading, setIsLoading] = useState(false);
  const [data, setData] = useState<MarketDataBar[]>([]);
  const [currentQuery, setCurrentQuery] = useState<HistoricalDataQuery | null>(null);
  const [savedQueries, setSavedQueries] = useState<SavedQuery[]>([]);
  const [frequencies, setFrequencies] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  const { isConnected } = useWebSocket();

  // =============================================================================
  // EFFECTS
  // =============================================================================
  
  useEffect(() => {
    loadFrequencies();
    if (activeTab === 'saved') {
      loadSavedQueries();
    }
  }, [activeTab]);

  // =============================================================================
  // DATA LOADING
  // =============================================================================
  
  const loadFrequencies = async () => {
    try {
      const freqs = await historicalDataService.getFrequencies();
      setFrequencies(freqs);
    } catch (error) {
      console.error('Failed to load frequencies:', error);
      notificationService.error('Failed to load data frequencies');
    }
  };

  const loadSavedQueries = async () => {
    try {
      setIsLoading(true);
      const queries = await historicalDataService.getSavedQueries();
      setSavedQueries(queries);
    } catch (error) {
      console.error('Failed to load saved queries:', error);
      notificationService.error('Failed to load saved queries');
    } finally {
      setIsLoading(false);
    }
  };

  // =============================================================================
  // QUERY HANDLERS
  // =============================================================================
  
  const handleQuerySubmit = useCallback(async (query: HistoricalDataQuery) => {
    try {
      setIsLoading(true);
      setError(null);
      setCurrentQuery(query);
      
      const request = {
        symbols: query.symbols,
        startDate: query.startDate?.toISOString(),
        endDate: query.endDate?.toISOString(),
        frequency: query.frequency,
        includeExtendedHours: query.includeExtendedHours,
        maxRecords: query.maxRecords,
        assetClass: query.assetClass,
        continuousSeries: query.continuousSeries,
        rollPolicy: query.rollPolicy
      };
      
      const response = await historicalDataService.fetchData(request);
      
      // Extract all bars from all symbols into a flat array for the UI
      const allBars: MarketDataBar[] = [];
      response.data.forEach((symbolResult: SymbolDataResponse) => {
        if (symbolResult.bars && symbolResult.bars.length > 0) {
          symbolResult.bars.forEach(bar => {
            allBars.push({
              symbol: symbolResult.symbol,
              timestamp: bar.timestamp,
              open: bar.open,
              high: bar.high,
              low: bar.low,
              close: bar.close,
              volume: bar.volume,
              vwap: bar.vwap,
              trades: bar.trades,
              openInterest: bar.openInterest,
              contractMonth: bar.contractMonth,
              qualityScore: bar.qualityScore
            });
          });
        }
      });
      
      setData(allBars);
      
      // Check if any of the symbol results were cached
      const anyCached = response.data.some(symbolResult => symbolResult.cached);
      if (anyCached) {
        notificationService.info('Data loaded from cache');
      }
      
      notificationService.success(`Loaded ${allBars.length} records`);
    } catch (error) {
      console.error('Failed to fetch historical data:', error);
      setError(error instanceof Error ? error.message : 'Failed to fetch data');
      notificationService.error('Failed to fetch historical data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleSaveQuery = useCallback(async (name: string, description?: string) => {
    if (!currentQuery) return;
    
    try {
      const saveRequest: SaveQueryRequest = {
        name,
        description,
        symbols: currentQuery.symbols,
        frequency: currentQuery.frequency.toString(),
        filters: {
          assetClass: currentQuery.assetClass,
          includeExtendedHours: currentQuery.includeExtendedHours,
          continuousSeries: currentQuery.continuousSeries,
          rollPolicy: currentQuery.rollPolicy
        }
      };
      
      await historicalDataService.saveQuery(saveRequest);
      notificationService.success('Query saved successfully');
      
      if (activeTab === 'saved') {
        await loadSavedQueries();
      }
    } catch (error) {
      console.error('Failed to save query:', error);
      notificationService.error('Failed to save query');
    }
  }, [currentQuery, activeTab]);

  const handleLoadQuery = useCallback(async (query: SavedQuery) => {
    const historicalQuery: HistoricalDataQuery = {
      symbols: query.symbols,
      frequency: query.frequency as DataFrequency,
      assetClass: query.filters?.assetClass,
      includeExtendedHours: query.filters?.includeExtendedHours,
      continuousSeries: query.filters?.continuousSeries,
      rollPolicy: query.filters?.rollPolicy
    };
    
    setActiveTab('new');
    await handleQuerySubmit(historicalQuery);
  }, [handleQuerySubmit]);

  const handleEditQuery = useCallback((query: SavedQuery) => {
    const historicalQuery: HistoricalDataQuery = {
      symbols: query.symbols,
      frequency: query.frequency as DataFrequency,
      assetClass: query.filters?.assetClass,
      includeExtendedHours: query.filters?.includeExtendedHours,
      continuousSeries: query.filters?.continuousSeries,
      rollPolicy: query.filters?.rollPolicy
    };
    
    setCurrentQuery(historicalQuery);
    setActiveTab('new');
  }, []);

  const handleDeleteQuery = useCallback(async (queryId: number) => {
    if (!window.confirm('Are you sure you want to delete this query?')) {
      return;
    }
    
    try {
      await historicalDataService.deleteQuery(queryId);
      notificationService.success('Query deleted successfully');
      await loadSavedQueries();
    } catch (error) {
      console.error('Failed to delete query:', error);
      notificationService.error('Failed to delete query');
    }
  }, []);

  const handleToggleFavorite = useCallback(async (queryId: number, isFavorite: boolean) => {
    try {
      await historicalDataService.updateQuery(queryId, { is_favorite: isFavorite });
      await loadSavedQueries();
    } catch (error) {
      console.error('Failed to update query:', error);
      notificationService.error('Failed to update query');
    }
  }, []);

  const handleExport = useCallback(async (format: 'csv' | 'json') => {
    if (!data.length) {
      notificationService.warning('No data to export');
      return;
    }
    
    try {
      let blob: Blob;
      let filename: string;
      
      if (format === 'csv') {
        blob = await historicalDataService.exportToCSV(data);
        filename = `historicalData_${Date.now()}.csv`;
      } else {
        blob = await historicalDataService.exportToJSON(data);
        filename = `historicalData_${Date.now()}.json`;
      }
      
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      notificationService.success(`Data exported as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Failed to export data:', error);
      notificationService.error('Failed to export data');
    }
  }, [data]);

  const handleRerun = useCallback(() => {
    if (currentQuery) {
      handleQuerySubmit(currentQuery);
    }
  }, [currentQuery, handleQuerySubmit]);

  // =============================================================================
  // RENDER
  // =============================================================================
  
  return (
    <div className="historical-data-page">
      <div className="page-header">
        <h1>Historical Data</h1>
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`} />
          <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'new' ? 'active' : ''}`}
          onClick={() => setActiveTab('new')}
        >
          New Query
        </button>
        <button
          className={`tab ${activeTab === 'saved' ? 'active' : ''}`}
          onClick={() => setActiveTab('saved')}
        >
          Saved Queries
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'new' ? (
          <div className="new-query-tab">
            <QueryForm
              onSubmit={handleQuerySubmit}
              isLoading={isLoading}
              frequencies={Array.isArray(frequencies) ? frequencies.map(f => f as DataFrequency) : []}
              initialValues={currentQuery ? {
                symbols: currentQuery.symbols.join(', '),
                frequency: currentQuery.frequency,
                assetClass: currentQuery.assetClass,
                includeExtendedHours: currentQuery.includeExtendedHours || false,
                maxRecords: currentQuery.maxRecords || 1000,
                continuousSeries: currentQuery.continuousSeries || false,
                rollPolicy: currentQuery.rollPolicy
              } : undefined}
            />
            
            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
            
            {data.length > 0 && (
              <DataPreview
                data={data}
                query={currentQuery!}
                isLoading={isLoading}
                onSaveQuery={handleSaveQuery}
                onExport={handleExport}
                onRerun={handleRerun}
              />
            )}
          </div>
        ) : (
          <div className="saved-queries-tab">
            <SavedQueries
              queries={savedQueries}
              onLoad={handleLoadQuery}
              onEdit={handleEditQuery}
              onDelete={handleDeleteQuery}
              onToggleFavorite={handleToggleFavorite}
              isLoading={isLoading}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoricalDataPage;