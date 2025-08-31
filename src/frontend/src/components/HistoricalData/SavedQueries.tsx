/**
 * Saved Queries Component
 * 
 * Component for managing and loading saved historical data queries.
 */

import React, { useState, useMemo } from 'react';
import { SavedQueriesProps, SavedQuery } from '../../types/historicalData';
import './SavedQueries.css';

const SavedQueries: React.FC<SavedQueriesProps> = ({
  queries,
  onLoad,
  onEdit,
  onDelete,
  onToggleFavorite,
  isLoading = false
}) => {
  // =============================================================================
  // STATE
  // =============================================================================
  
  const [searchTerm, setSearchTerm] = useState('');
  const [filterFavorites, setFilterFavorites] = useState(false);
  const [sortBy, setSortBy] = useState<'name' | 'created' | 'lastExecuted' | 'favorite'>('created');

  // =============================================================================
  // FILTERING & SORTING
  // =============================================================================
  
  const filteredQueries = useMemo(() => {
    let filtered = [...queries];
    
    // Search filter
    if (searchTerm.trim()) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(query =>
        query.name.toLowerCase().includes(search) ||
        query.description?.toLowerCase().includes(search) ||
        query.symbols.some(s => s.toLowerCase().includes(search))
      );
    }
    
    // Favorites filter
    if (filterFavorites) {
      filtered = filtered.filter(query => query.isFavorite);
    }
    
    // Sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'created':
          return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
        case 'lastExecuted':
          if (!a.lastExecuted) return 1;
          if (!b.lastExecuted) return -1;
          return new Date(b.lastExecuted).getTime() - new Date(a.lastExecuted).getTime();
        case 'favorite':
          if (a.isFavorite === b.isFavorite) {
            return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
          }
          return a.isFavorite ? -1 : 1;
        default:
          return 0;
      }
    });
    
    return filtered;
  }, [queries, searchTerm, filterFavorites, sortBy]);

  // =============================================================================
  // HELPERS
  // =============================================================================
  
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      if (diffHours === 0) {
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
      }
      return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const getFrequencyLabel = (frequency: string): string => {
    const labels: Record<string, string> = {
      '1min': '1 Minute',
      '5min': '5 Minutes',
      '15min': '15 Minutes',
      '30min': '30 Minutes',
      '1h': '1 Hour',
      '4h': '4 Hours',
      '1d': 'Daily',
      '1w': 'Weekly',
      '1M': 'Monthly'
    };
    return labels[frequency] || frequency;
  };

  // =============================================================================
  // RENDER
  // =============================================================================
  
  if (isLoading) {
    return (
      <div className="saved-queries loading">
        <div className="spinner" />
        <p>Loading saved queries...</p>
      </div>
    );
  }

  return (
    <div className="saved-queries">
      <div className="queries-header">
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search queries by name, description, or symbol..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
        
        <div className="filter-controls">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={filterFavorites}
              onChange={(e) => setFilterFavorites(e.target.checked)}
            />
            <span>Favorites only</span>
          </label>
          
          <div className="sort-control">
            <label>Sort by:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            >
              <option value="created">Created Date</option>
              <option value="name">Name</option>
              <option value="lastExecuted">Last Executed</option>
              <option value="favorite">Favorites First</option>
            </select>
          </div>
        </div>
      </div>

      {filteredQueries.length === 0 ? (
        <div className="no-queries">
          <p>
            {searchTerm || filterFavorites
              ? 'No queries found matching your criteria'
              : 'No saved queries yet'}
          </p>
          {!searchTerm && !filterFavorites && (
            <p className="hint">
              Create a new query and save it to see it here
            </p>
          )}
        </div>
      ) : (
        <div className="queries-grid">
          {filteredQueries.map(query => (
            <div key={query.id} className="query-card">
              <div className="query-header">
                <h4>{query.name}</h4>
                <button
                  className={`favorite-btn ${query.isFavorite ? 'active' : ''}`}
                  onClick={() => onToggleFavorite(query.id, !query.isFavorite)}
                  title={query.isFavorite ? 'Remove from favorites' : 'Add to favorites'}
                >
                  {query.isFavorite ? '★' : '☆'}
                </button>
              </div>
              
              {query.description && (
                <p className="query-description">{query.description}</p>
              )}
              
              <div className="query-details">
                <div className="detail-item">
                  <span className="detail-label">Symbols:</span>
                  <span className="detail-value symbols">
                    {query.symbols.slice(0, 3).join(', ')}
                    {query.symbols.length > 3 && ` +${query.symbols.length - 3} more`}
                  </span>
                </div>
                
                <div className="detail-item">
                  <span className="detail-label">Frequency:</span>
                  <span className="detail-value">{getFrequencyLabel(query.frequency)}</span>
                </div>
                
                <div className="detail-item">
                  <span className="detail-label">Created:</span>
                  <span className="detail-value">{formatDate(query.createdAt)}</span>
                </div>
                
                {query.lastExecuted && (
                  <div className="detail-item">
                    <span className="detail-label">Last Run:</span>
                    <span className="detail-value">{formatDate(query.lastExecuted)}</span>
                  </div>
                )}
                
                {query.executionCount > 0 && (
                  <div className="detail-item">
                    <span className="detail-label">Runs:</span>
                    <span className="detail-value">{query.executionCount}</span>
                  </div>
                )}
              </div>
              
              <div className="query-actions">
                <button
                  className="btn btn-primary"
                  onClick={() => onLoad(query)}
                >
                  Load & Run
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => onEdit(query)}
                >
                  Edit
                </button>
                <button
                  className="btn btn-danger"
                  onClick={() => onDelete(query.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SavedQueries;