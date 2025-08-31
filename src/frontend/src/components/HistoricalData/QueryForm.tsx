/**
 * Query Form Component
 * 
 * Form for configuring historical data query parameters with validation.
 */

import React, { useState, useEffect } from 'react';
import {
  QueryFormProps,
  QueryFormData,
  HistoricalDataQuery,
  DataFrequency,
  AssetClass,
  RollPolicy,
  TimeRangePreset,
  ValidationError
} from '../../types/historicalData';
import './QueryForm.css';

const QueryForm: React.FC<QueryFormProps> = ({
  onSubmit,
  initialValues,
  isLoading = false,
  frequencies = Object.values(DataFrequency)
}) => {
  // =============================================================================
  // STATE
  // =============================================================================
  
  const [formData, setFormData] = useState<QueryFormData>({
    symbols: initialValues?.symbols || '',
    timeRange: TimeRangePreset.LAST_30_DAYS,
    customStartDate: '',
    customEndDate: '',
    frequency: initialValues?.frequency || DataFrequency.ONE_DAY,
    assetClass: initialValues?.assetClass || AssetClass.STOCK,
    includeExtendedHours: initialValues?.includeExtendedHours || false,
    maxRecords: initialValues?.maxRecords || 1000,
    continuousSeries: initialValues?.continuousSeries || false,
    rollPolicy: initialValues?.rollPolicy || RollPolicy.CALENDAR
  });

  const [errors, setErrors] = useState<ValidationError[]>([]);

  // =============================================================================
  // EFFECTS
  // =============================================================================
  
  useEffect(() => {
    if (initialValues) {
      setFormData(prev => ({
        ...prev,
        ...initialValues,
        timeRange: initialValues.customStartDate || initialValues.customEndDate 
          ? TimeRangePreset.CUSTOM 
          : prev.timeRange
      }));
    }
  }, [initialValues]);

  // =============================================================================
  // VALIDATION
  // =============================================================================
  
  const validateForm = (): boolean => {
    const newErrors: ValidationError[] = [];

    if (!formData.symbols.trim()) {
      newErrors.push({ field: 'symbols', message: 'At least one symbol is required' });
    } else {
      const symbols = formData.symbols.split(',').map(s => s.trim());
      const invalidSymbols = symbols.filter(s => !isValidSymbol(s));
      if (invalidSymbols.length > 0) {
        newErrors.push({
          field: 'symbols',
          message: `Invalid symbols: ${invalidSymbols.join(', ')}`
        });
      }
    }

    if (formData.timeRange === TimeRangePreset.CUSTOM) {
      if (!formData.customStartDate) {
        newErrors.push({ field: 'customStartDate', message: 'Start date is required for custom range' });
      }
      if (!formData.customEndDate) {
        newErrors.push({ field: 'customEndDate', message: 'End date is required for custom range' });
      }
      if (formData.customStartDate && formData.customEndDate) {
        const start = new Date(formData.customStartDate);
        const end = new Date(formData.customEndDate);
        if (start >= end) {
          newErrors.push({ field: 'customEndDate', message: 'End date must be after start date' });
        }
      }
    }

    if (formData.maxRecords < 1 || formData.maxRecords > 10000) {
      newErrors.push({ field: 'maxRecords', message: 'Max records must be between 1 and 10000' });
    }

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  const isValidSymbol = (symbol: string): boolean => {
    // Basic symbol validation - alphanumeric, /, _, -
    return /^[A-Z0-9\/_-]+$/i.test(symbol);
  };

  // =============================================================================
  // HANDLERS
  // =============================================================================
  
  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : type === 'number' ? parseInt(value) : value
    }));
    
    // Clear error for this field
    setErrors(prev => prev.filter(err => err.field !== name));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    const { startDate, endDate } = getDateRange();
    const symbols = formData.symbols
      .split(',')
      .map(s => s.trim())
      .filter(s => s.length > 0);

    const query: HistoricalDataQuery = {
      symbols,
      startDate,
      endDate,
      frequency: formData.frequency,
      assetClass: formData.assetClass,
      includeExtendedHours: formData.includeExtendedHours,
      maxRecords: formData.maxRecords,
      continuousSeries: formData.continuousSeries,
      rollPolicy: formData.rollPolicy
    };

    onSubmit(query);
  };

  const getDateRange = (): { startDate?: Date; endDate?: Date } => {
    const now = new Date();
    let startDate: Date | undefined;
    let endDate: Date | undefined = new Date();

    switch (formData.timeRange) {
      case TimeRangePreset.TODAY:
        startDate = new Date(now.setHours(0, 0, 0, 0));
        break;
      case TimeRangePreset.YESTERDAY:
        const yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);
        startDate = new Date(yesterday.setHours(0, 0, 0, 0));
        endDate = new Date(yesterday.setHours(23, 59, 59, 999));
        break;
      case TimeRangePreset.LAST_7_DAYS:
        startDate = new Date(now);
        startDate.setDate(startDate.getDate() - 7);
        break;
      case TimeRangePreset.LAST_30_DAYS:
        startDate = new Date(now);
        startDate.setDate(startDate.getDate() - 30);
        break;
      case TimeRangePreset.LAST_90_DAYS:
        startDate = new Date(now);
        startDate.setDate(startDate.getDate() - 90);
        break;
      case TimeRangePreset.LAST_YEAR:
        startDate = new Date(now);
        startDate.setFullYear(startDate.getFullYear() - 1);
        break;
      case TimeRangePreset.CUSTOM:
        if (formData.customStartDate) {
          startDate = new Date(formData.customStartDate);
        }
        if (formData.customEndDate) {
          endDate = new Date(formData.customEndDate);
        }
        break;
    }

    return { startDate, endDate };
  };

  const getFieldError = (field: string): string | undefined => {
    return errors.find(err => err.field === field)?.message;
  };

  // =============================================================================
  // RENDER
  // =============================================================================
  
  return (
    <form className="query-form" onSubmit={handleSubmit}>
      <div className="form-section">
        <h3>Symbol Selection</h3>
        
        <div className="form-group">
          <label htmlFor="symbols">
            Symbols <span className="required">*</span>
          </label>
          <input
            id="symbols"
            name="symbols"
            type="text"
            value={formData.symbols}
            onChange={handleInputChange}
            placeholder="Enter symbols separated by commas (e.g., AAPL, SPY, /ES)"
            className={getFieldError('symbols') ? 'error' : ''}
            disabled={isLoading}
          />
          {getFieldError('symbols') && (
            <span className="error-text">{getFieldError('symbols')}</span>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="assetClass">Asset Class</label>
          <select
            id="assetClass"
            name="assetClass"
            value={formData.assetClass}
            onChange={handleInputChange}
            disabled={isLoading}
          >
            <option value={AssetClass.STOCK}>Stock</option>
            <option value={AssetClass.INDEX}>Index</option>
            <option value={AssetClass.FUTURE}>Future</option>
          </select>
        </div>
      </div>

      <div className="form-section">
        <h3>Time Range</h3>
        
        <div className="form-group">
          <label htmlFor="timeRange">Time Period</label>
          <select
            id="timeRange"
            name="timeRange"
            value={formData.timeRange}
            onChange={handleInputChange}
            disabled={isLoading}
          >
            <option value={TimeRangePreset.TODAY}>Today</option>
            <option value={TimeRangePreset.YESTERDAY}>Yesterday</option>
            <option value={TimeRangePreset.LAST_7_DAYS}>Last 7 Days</option>
            <option value={TimeRangePreset.LAST_30_DAYS}>Last 30 Days</option>
            <option value={TimeRangePreset.LAST_90_DAYS}>Last 90 Days</option>
            <option value={TimeRangePreset.LAST_YEAR}>Last Year</option>
            <option value={TimeRangePreset.CUSTOM}>Custom Range</option>
          </select>
        </div>

        {formData.timeRange === TimeRangePreset.CUSTOM && (
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="customStartDate">Start Date</label>
              <input
                id="customStartDate"
                name="customStartDate"
                type="datetime-local"
                value={formData.customStartDate}
                onChange={handleInputChange}
                className={getFieldError('customStartDate') ? 'error' : ''}
                disabled={isLoading}
              />
              {getFieldError('customStartDate') && (
                <span className="error-text">{getFieldError('customStartDate')}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="customEndDate">End Date</label>
              <input
                id="customEndDate"
                name="customEndDate"
                type="datetime-local"
                value={formData.customEndDate}
                onChange={handleInputChange}
                className={getFieldError('customEndDate') ? 'error' : ''}
                disabled={isLoading}
              />
              {getFieldError('customEndDate') && (
                <span className="error-text">{getFieldError('customEndDate')}</span>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="form-section">
        <h3>Data Configuration</h3>
        
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="frequency">Frequency</label>
            <select
              id="frequency"
              name="frequency"
              value={formData.frequency}
              onChange={handleInputChange}
              disabled={isLoading}
            >
              {frequencies.map(freq => (
                <option key={freq} value={freq}>
                  {freq}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="maxRecords">Max Records</label>
            <input
              id="maxRecords"
              name="maxRecords"
              type="number"
              value={formData.maxRecords}
              onChange={handleInputChange}
              min="1"
              max="10000"
              className={getFieldError('maxRecords') ? 'error' : ''}
              disabled={isLoading}
            />
            {getFieldError('maxRecords') && (
              <span className="error-text">{getFieldError('maxRecords')}</span>
            )}
          </div>
        </div>

        <div className="form-group checkbox-group">
          <label>
            <input
              type="checkbox"
              name="includeExtendedHours"
              checked={formData.includeExtendedHours}
              onChange={handleInputChange}
              disabled={isLoading}
            />
            Include Extended Hours
          </label>
        </div>

        {formData.assetClass === AssetClass.FUTURE && (
          <>
            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  name="continuousSeries"
                  checked={formData.continuousSeries}
                  onChange={handleInputChange}
                  disabled={isLoading}
                />
                Continuous Series
              </label>
            </div>

            {formData.continuousSeries && (
              <div className="form-group">
                <label htmlFor="rollPolicy">Roll Policy</label>
                <select
                  id="rollPolicy"
                  name="rollPolicy"
                  value={formData.rollPolicy}
                  onChange={handleInputChange}
                  disabled={isLoading}
                >
                  <option value={RollPolicy.CALENDAR}>Calendar</option>
                  <option value={RollPolicy.VOLUME}>Volume</option>
                  <option value={RollPolicy.OPEN_INTEREST}>Open Interest</option>
                </select>
              </div>
            )}
          </>
        )}
      </div>

      <div className="form-actions">
        <button
          type="submit"
          className="btn btn-primary"
          disabled={isLoading}
        >
          {isLoading ? 'Loading...' : 'Fetch Data'}
        </button>
      </div>
    </form>
  );
};

export default QueryForm;