/**
 * Instrument Selector Component
 * 
 * Dropdown selector for choosing instruments with search and filtering
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient, queryKeys } from '../../services/apiClient';
import { Instrument } from '../../types/models';
import { LoadingSpinner } from './LoadingSpinner';
import './InstrumentSelector.css';

interface InstrumentSelectorProps {
  value?: number;
  onChange: (instrumentId: number, symbol: string) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

export const InstrumentSelector: React.FC<InstrumentSelectorProps> = ({
  value,
  onChange,
  placeholder = 'Select instrument',
  className = '',
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const { data: instruments, isLoading } = useQuery({
    queryKey: queryKeys.instruments(),
    queryFn: () => apiClient.getInstruments(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const selectedInstrument = useMemo(() => {
    return instruments?.find(inst => inst.id === value);
  }, [instruments, value]);

  const filteredInstruments = useMemo(() => {
    if (!instruments) return [];
    
    if (!searchTerm) return instruments;
    
    const term = searchTerm.toLowerCase();
    return instruments.filter(instrument => 
      instrument.symbol.toLowerCase().includes(term) ||
      instrument.name.toLowerCase().includes(term)
    );
  }, [instruments, searchTerm]);

  const handleSelect = (instrument: Instrument) => {
    onChange(instrument.id, instrument.symbol);
    setIsOpen(false);
    setSearchTerm('');
  };

  const handleToggle = () => {
    if (!disabled) {
      setIsOpen(!isOpen);
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (!target.closest('.instrument-selector')) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [isOpen]);

  return (
    <div className={`instrument-selector ${className} ${disabled ? 'instrument-selector--disabled' : ''}`}>
      <div 
        className={`instrument-selector__trigger ${isOpen ? 'instrument-selector__trigger--open' : ''}`}
        onClick={handleToggle}
      >
        <div className="instrument-selector__content">
          {selectedInstrument ? (
            <div className="instrument-selector__selected">
              <span className="instrument-selector__symbol">{selectedInstrument.symbol}</span>
              <span className="instrument-selector__name">{selectedInstrument.name}</span>
            </div>
          ) : (
            <span className="instrument-selector__placeholder">{placeholder}</span>
          )}
        </div>
        <div className="instrument-selector__arrow">
          {isLoading ? (
            <LoadingSpinner size="small" />
          ) : (
            <svg width="12" height="8" viewBox="0 0 12 8" fill="none">
              <path 
                d="M1 1.5L6 6.5L11 1.5" 
                stroke="currentColor" 
                strokeWidth="1.5" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
            </svg>
          )}
        </div>
      </div>

      {isOpen && (
        <div className="instrument-selector__dropdown">
          <div className="instrument-selector__search">
            <input
              type="text"
              placeholder="Search instruments..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="instrument-selector__search-input"
              autoFocus
            />
          </div>
          
          <div className="instrument-selector__options">
            {filteredInstruments.length > 0 ? (
              filteredInstruments.map((instrument) => (
                <div
                  key={instrument.id}
                  className={`instrument-selector__option ${
                    instrument.id === value ? 'instrument-selector__option--selected' : ''
                  }`}
                  onClick={() => handleSelect(instrument)}
                >
                  <div className="instrument-selector__option-content">
                    <span className="instrument-selector__option-symbol">{instrument.symbol}</span>
                    <span className="instrument-selector__option-name">{instrument.name}</span>
                  </div>
                  <div className="instrument-selector__option-type">
                    {instrument.type}
                  </div>
                </div>
              ))
            ) : (
              <div className="instrument-selector__no-results">
                {searchTerm ? 'No instruments match your search' : 'No instruments available'}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};