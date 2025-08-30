/**
 * RuleManagement Component
 * 
 * Complete alert rule management interface with real-time validation, rule testing,
 * bulk operations, and template support. Optimized for efficient rule creation
 * and management workflows.
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, queryKeys } from '../../services/apiClient';
import {
  AlertRule,
  AlertRuleWithDetails,
  Instrument,
  RuleType,
  RuleCondition,
  InstrumentStatus,
  CreateAlertRuleRequest,
  UpdateAlertRuleRequest,
  AlertRuleFilters
} from '../../types';

// =============================================================================
// TYPES
// =============================================================================

interface RuleManagementProps {
  className?: string;
}

interface RuleFormData {
  instrument_id: number;
  rule_type: RuleType;
  condition: RuleCondition;
  threshold: number;
  active: boolean;
  name: string;
  description: string;
  time_window_seconds?: number;
  moving_average_period?: number;
  cooldown_seconds: number;
}

interface RuleTemplate {
  id: string;
  name: string;
  description: string;
  rule_type: RuleType;
  condition: RuleCondition;
  threshold: number;
  cooldown_seconds: number;
  time_window_seconds?: number;
  moving_average_period?: number;
}

interface BulkAction {
  type: 'enable' | 'disable' | 'delete';
  rules: AlertRule[];
}

// Rule Templates
const RULE_TEMPLATES: RuleTemplate[] = [
  {
    id: 'price_above',
    name: 'Price Above Threshold',
    description: 'Alert when price goes above a specific value',
    rule_type: RuleType.THRESHOLD,
    condition: RuleCondition.ABOVE,
    threshold: 0,
    cooldown_seconds: 300
  },
  {
    id: 'price_below',
    name: 'Price Below Threshold', 
    description: 'Alert when price drops below a specific value',
    rule_type: RuleType.THRESHOLD,
    condition: RuleCondition.BELOW,
    threshold: 0,
    cooldown_seconds: 300
  },
  {
    id: 'price_crossover_up',
    name: 'Price Breakout Up',
    description: 'Alert when price breaks above moving average',
    rule_type: RuleType.CROSSOVER,
    condition: RuleCondition.CROSSES_ABOVE,
    threshold: 0,
    cooldown_seconds: 600,
    moving_average_period: 20
  },
  {
    id: 'volume_spike',
    name: 'Volume Spike',
    description: 'Alert when volume exceeds normal levels',
    rule_type: RuleType.VOLUME_SPIKE,
    condition: RuleCondition.VOLUME_ABOVE,
    threshold: 1000,
    cooldown_seconds: 180
  },
  {
    id: 'percent_change_up',
    name: 'Percent Change Up',
    description: 'Alert on significant percentage increase',
    rule_type: RuleType.RATE_OF_CHANGE,
    condition: RuleCondition.PERCENT_CHANGE_UP,
    threshold: 2.0,
    cooldown_seconds: 900,
    time_window_seconds: 300
  }
];

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

const getInitialFormData = (): RuleFormData => ({
  instrument_id: 0,
  rule_type: RuleType.THRESHOLD,
  condition: RuleCondition.ABOVE,
  threshold: 0,
  active: true,
  name: '',
  description: '',
  cooldown_seconds: 300
});

const validateForm = (data: RuleFormData, instruments: Instrument[]): string[] => {
  const errors: string[] = [];
  
  if (!data.instrument_id || data.instrument_id === 0) {
    errors.push('Please select an instrument');
  } else if (!instruments.find(i => i.id === data.instrument_id)) {
    errors.push('Selected instrument not found');
  }
  
  if (!data.name.trim()) {
    errors.push('Rule name is required');
  }
  
  if (data.threshold <= 0 && data.rule_type !== RuleType.CROSSOVER) {
    errors.push('Threshold must be greater than 0');
  }
  
  if (data.cooldown_seconds < 0) {
    errors.push('Cooldown cannot be negative');
  }
  
  if (data.time_window_seconds && data.time_window_seconds < 1) {
    errors.push('Time window must be at least 1 second');
  }
  
  if (data.moving_average_period && data.moving_average_period < 2) {
    errors.push('Moving average period must be at least 2');
  }
  
  return errors;
};

const getRuleConditionsForType = (ruleType: RuleType): RuleCondition[] => {
  switch (ruleType) {
    case RuleType.THRESHOLD:
      return [RuleCondition.ABOVE, RuleCondition.BELOW, RuleCondition.EQUALS];
    case RuleType.CROSSOVER:
      return [RuleCondition.CROSSES_ABOVE, RuleCondition.CROSSES_BELOW];
    case RuleType.RATE_OF_CHANGE:
      return [RuleCondition.PERCENT_CHANGE_UP, RuleCondition.PERCENT_CHANGE_DOWN];
    case RuleType.VOLUME_SPIKE:
      return [RuleCondition.VOLUME_ABOVE];
    case RuleType.MULTI_CONDITION:
      return [RuleCondition.ABOVE, RuleCondition.BELOW, RuleCondition.CROSSES_ABOVE, RuleCondition.CROSSES_BELOW];
    default:
      return [RuleCondition.ABOVE, RuleCondition.BELOW];
  }
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

const RuleManagement: React.FC<RuleManagementProps> = ({ className = '' }) => {
  const [showForm, setShowForm] = useState(false);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);
  const [formData, setFormData] = useState<RuleFormData>(getInitialFormData);
  const [selectedRules, setSelectedRules] = useState<Set<number>>(new Set());
  const [filters, setFilters] = useState<AlertRuleFilters>({});
  const [testingRule, setTestingRule] = useState<number | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  
  const queryClient = useQueryClient();

  // Data fetching
  const {
    data: rules = [],
    isLoading: rulesLoading,
    error: rulesError
  } = useQuery({
    queryKey: queryKeys.alertRules(filters),
    queryFn: () => apiClient.getAlertRules(filters),
    refetchInterval: 30000
  });

  const {
    data: instruments = [],
    isLoading: instrumentsLoading
  } = useQuery({
    queryKey: queryKeys.instruments({ status: InstrumentStatus.ACTIVE }),
    queryFn: () => apiClient.getInstruments({ status: InstrumentStatus.ACTIVE })
  });

  // Mutations
  const createRuleMutation = useMutation({
    mutationFn: (data: CreateAlertRuleRequest) => apiClient.createAlertRule(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alertRules() });
      setShowForm(false);
      setFormData(getInitialFormData());
    }
  });

  const updateRuleMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateAlertRuleRequest }) => 
      apiClient.updateAlertRule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alertRules() });
      setEditingRule(null);
      setShowForm(false);
      setFormData(getInitialFormData());
    }
  });

  const deleteRuleMutation = useMutation({
    mutationFn: (id: number) => apiClient.deleteAlertRule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alertRules() });
    }
  });

  const bulkToggleMutation = useMutation({
    mutationFn: ({ ids, active }: { ids: number[]; active: boolean }) => 
      apiClient.toggleAlertRules(ids, active),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alertRules() });
      setSelectedRules(new Set());
    }
  });

  // Event handlers
  const handleCreateRule = useCallback(() => {
    setEditingRule(null);
    setFormData(getInitialFormData());
    setShowForm(true);
  }, []);

  const handleEditRule = useCallback((rule: AlertRule) => {
    setEditingRule(rule);
    setFormData({
      instrument_id: rule.instrument_id,
      rule_type: rule.rule_type,
      condition: rule.condition,
      threshold: rule.threshold,
      active: rule.active,
      name: rule.name || '',
      description: rule.description || '',
      time_window_seconds: rule.time_window_seconds || undefined,
      moving_average_period: rule.moving_average_period || undefined,
      cooldown_seconds: rule.cooldown_seconds
    });
    setShowForm(true);
  }, []);

  const handleSubmitForm = useCallback(() => {
    const errors = validateForm(formData, instruments);
    if (errors.length > 0) {
      alert('Form validation errors:\n' + errors.join('\n'));
      return;
    }

    const requestData: CreateAlertRuleRequest | UpdateAlertRuleRequest = {
      instrument_id: formData.instrument_id,
      rule_type: formData.rule_type,
      condition: formData.condition,
      threshold: formData.threshold,
      active: formData.active,
      name: formData.name,
      description: formData.description,
      time_window_seconds: formData.time_window_seconds,
      moving_average_period: formData.moving_average_period,
      cooldown_seconds: formData.cooldown_seconds
    };

    if (editingRule) {
      updateRuleMutation.mutate({ id: editingRule.id, data: requestData });
    } else {
      createRuleMutation.mutate(requestData as CreateAlertRuleRequest);
    }
  }, [formData, instruments, editingRule, createRuleMutation, updateRuleMutation]);

  const handleDeleteRule = useCallback((id: number) => {
    if (window.confirm('Are you sure you want to delete this rule?')) {
      deleteRuleMutation.mutate(id);
    }
  }, [deleteRuleMutation]);

  const handleBulkAction = useCallback((action: 'enable' | 'disable' | 'delete') => {
    const ids = Array.from(selectedRules);
    if (ids.length === 0) return;

    switch (action) {
      case 'enable':
        bulkToggleMutation.mutate({ ids, active: true });
        break;
      case 'disable':
        bulkToggleMutation.mutate({ ids, active: false });
        break;
      case 'delete':
        if (window.confirm(`Delete ${ids.length} selected rules?`)) {
          Promise.all(ids.map(id => deleteRuleMutation.mutateAsync(id))).then(() => {
            setSelectedRules(new Set());
          });
        }
        break;
    }
  }, [selectedRules, bulkToggleMutation, deleteRuleMutation]);

  const handleApplyTemplate = useCallback((template: RuleTemplate) => {
    setFormData({
      ...getInitialFormData(),
      rule_type: template.rule_type,
      condition: template.condition,
      threshold: template.threshold,
      name: template.name,
      description: template.description,
      cooldown_seconds: template.cooldown_seconds,
      time_window_seconds: template.time_window_seconds,
      moving_average_period: template.moving_average_period
    });
  }, []);

  const handleRuleSelection = useCallback((ruleId: number, selected: boolean) => {
    const newSelection = new Set(selectedRules);
    if (selected) {
      newSelection.add(ruleId);
    } else {
      newSelection.delete(ruleId);
    }
    setSelectedRules(newSelection);
  }, [selectedRules]);

  // Computed values
  const filteredRules = useMemo(() => {
    return rules.filter(rule => {
      if (filters.active !== undefined && rule.active !== filters.active) return false;
      if (filters.rule_type && rule.rule_type !== filters.rule_type) return false;
      if (filters.instrument_id && rule.instrument_id !== filters.instrument_id) return false;
      return true;
    });
  }, [rules, filters]);

  const validationErrors = useMemo(() => {
    return validateForm(formData, instruments);
  }, [formData, instruments]);

  const availableConditions = useMemo(() => {
    return getRuleConditionsForType(formData.rule_type);
  }, [formData.rule_type]);

  const selectedInstrument = useMemo(() => {
    return instruments.find(i => i.id === formData.instrument_id);
  }, [instruments, formData.instrument_id]);

  const previewText = useMemo(() => {
    if (!selectedInstrument || validationErrors.length > 0) return '';
    
    const conditionText = {
      [RuleCondition.ABOVE]: `rises above ${formData.threshold}`,
      [RuleCondition.BELOW]: `falls below ${formData.threshold}`,
      [RuleCondition.EQUALS]: `equals ${formData.threshold}`,
      [RuleCondition.CROSSES_ABOVE]: `crosses above its ${formData.moving_average_period || 20}-period moving average`,
      [RuleCondition.CROSSES_BELOW]: `crosses below its ${formData.moving_average_period || 20}-period moving average`,
      [RuleCondition.PERCENT_CHANGE_UP]: `increases by ${formData.threshold}% ${formData.time_window_seconds ? `in ${formData.time_window_seconds} seconds` : ''}`,
      [RuleCondition.PERCENT_CHANGE_DOWN]: `decreases by ${formData.threshold}% ${formData.time_window_seconds ? `in ${formData.time_window_seconds} seconds` : ''}`,
      [RuleCondition.VOLUME_ABOVE]: `volume exceeds ${formData.threshold}`
    }[formData.condition];

    return `Alert when ${selectedInstrument.symbol} ${conditionText}. Cooldown: ${formData.cooldown_seconds} seconds.`;
  }, [selectedInstrument, formData, validationErrors]);

  if (rulesLoading || instrumentsLoading) {
    return (
      <div className={`rule-management ${className}`}>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading rules...</p>
        </div>
      </div>
    );
  }

  if (rulesError) {
    return (
      <div className={`rule-management ${className}`}>
        <div className="error-container">
          <h2>Error Loading Rules</h2>
          <p>Failed to load alert rules. Please try refreshing the page.</p>
          <button onClick={() => window.location.reload()} className="btn btn-primary">
            Refresh Page
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`rule-management ${className}`}>
      {/* Header */}
      <div className="rule-management-header">
        <div className="header-left">
          <h2>Alert Rule Management</h2>
          <p>{filteredRules.length} rules ({rules.filter(r => r.active).length} active)</p>
        </div>
        <div className="header-actions">
          <button 
            onClick={handleCreateRule} 
            className="btn btn-primary"
          >
            Create Rule
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="rule-filters">
        <div className="filter-group">
          <label>Status:</label>
          <select 
            value={filters.active === undefined ? '' : String(filters.active)} 
            onChange={(e) => setFilters({
              ...filters,
              active: e.target.value === '' ? undefined : e.target.value === 'true'
            })}
            className="filter-select"
          >
            <option value="">All Rules</option>
            <option value="true">Active Only</option>
            <option value="false">Inactive Only</option>
          </select>
        </div>
        
        <div className="filter-group">
          <label>Rule Type:</label>
          <select 
            value={filters.rule_type || ''} 
            onChange={(e) => setFilters({
              ...filters,
              rule_type: e.target.value as RuleType || undefined
            })}
            className="filter-select"
          >
            <option value="">All Types</option>
            {Object.values(RuleType).map(type => (
              <option key={type} value={type}>{type.replace('_', ' ').toUpperCase()}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Instrument:</label>
          <select 
            value={filters.instrument_id || ''} 
            onChange={(e) => setFilters({
              ...filters,
              instrument_id: e.target.value ? parseInt(e.target.value) : undefined
            })}
            className="filter-select"
          >
            <option value="">All Instruments</option>
            {instruments.map(instrument => (
              <option key={instrument.id} value={instrument.id}>{instrument.symbol}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedRules.size > 0 && (
        <div className="bulk-actions">
          <span>{selectedRules.size} rules selected</span>
          <div className="bulk-action-buttons">
            <button 
              onClick={() => handleBulkAction('enable')} 
              className="btn btn-secondary"
            >
              Enable
            </button>
            <button 
              onClick={() => handleBulkAction('disable')} 
              className="btn btn-secondary"
            >
              Disable
            </button>
            <button 
              onClick={() => handleBulkAction('delete')} 
              className="btn btn-danger"
            >
              Delete
            </button>
          </div>
        </div>
      )}

      {/* Rules List */}
      <div className="rules-list">
        {filteredRules.length === 0 ? (
          <div className="empty-state">
            <h3>No Alert Rules</h3>
            <p>Create your first alert rule to start monitoring market movements.</p>
            <button onClick={handleCreateRule} className="btn btn-primary">
              Create Your First Rule
            </button>
          </div>
        ) : (
          <div className="rules-table">
            <div className="table-header">
              <div className="col-checkbox">
                <input
                  type="checkbox"
                  checked={selectedRules.size === filteredRules.length && filteredRules.length > 0}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedRules(new Set(filteredRules.map(r => r.id)));
                    } else {
                      setSelectedRules(new Set());
                    }
                  }}
                />
              </div>
              <div className="col-name">Rule Name</div>
              <div className="col-instrument">Instrument</div>
              <div className="col-type">Type</div>
              <div className="col-condition">Condition</div>
              <div className="col-threshold">Threshold</div>
              <div className="col-status">Status</div>
              <div className="col-actions">Actions</div>
            </div>
            
            {filteredRules.map(rule => {
              const instrument = instruments.find(i => i.id === rule.instrument_id);
              return (
                <div key={rule.id} className={`table-row ${!rule.active ? 'inactive' : ''}`}>
                  <div className="col-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedRules.has(rule.id)}
                      onChange={(e) => handleRuleSelection(rule.id, e.target.checked)}
                    />
                  </div>
                  <div className="col-name">
                    <div className="rule-name">{rule.name || `Rule ${rule.id}`}</div>
                    {rule.description && (
                      <div className="rule-description">{rule.description}</div>
                    )}
                  </div>
                  <div className="col-instrument">
                    <span className="instrument-symbol">{instrument?.symbol || 'Unknown'}</span>
                  </div>
                  <div className="col-type">
                    <span className="rule-type">{rule.rule_type.replace('_', ' ')}</span>
                  </div>
                  <div className="col-condition">
                    <span className="rule-condition">{rule.condition.replace('_', ' ')}</span>
                  </div>
                  <div className="col-threshold">
                    <span className="threshold-value">{rule.threshold}</span>
                  </div>
                  <div className="col-status">
                    <span className={`status-badge ${rule.active ? 'active' : 'inactive'}`}>
                      {rule.active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="col-actions">
                    <button 
                      onClick={() => handleEditRule(rule)} 
                      className="btn btn-sm btn-secondary"
                      title="Edit Rule"
                    >
                      Edit
                    </button>
                    <button 
                      onClick={() => handleDeleteRule(rule.id)} 
                      className="btn btn-sm btn-danger"
                      title="Delete Rule"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Rule Form Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingRule ? 'Edit Rule' : 'Create New Rule'}</h3>
              <button 
                onClick={() => setShowForm(false)} 
                className="close-button"
              >
                ×
              </button>
            </div>

            <div className="modal-body">
              {/* Templates */}
              {!editingRule && (
                <div className="templates-section">
                  <h4>Quick Templates</h4>
                  <div className="template-grid">
                    {RULE_TEMPLATES.map(template => (
                      <div 
                        key={template.id} 
                        className="template-card"
                        onClick={() => handleApplyTemplate(template)}
                      >
                        <div className="template-name">{template.name}</div>
                        <div className="template-description">{template.description}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Form Fields */}
              <div className="form-section">
                <div className="form-group">
                  <label>Rule Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Enter rule name"
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label>Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Optional description"
                    className="form-textarea"
                    rows={2}
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Instrument *</label>
                    <select
                      value={formData.instrument_id}
                      onChange={(e) => setFormData({ ...formData, instrument_id: parseInt(e.target.value) })}
                      className="form-select"
                    >
                      <option value={0}>Select Instrument</option>
                      {instruments.map(instrument => (
                        <option key={instrument.id} value={instrument.id}>
                          {instrument.symbol} - {instrument.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Rule Type *</label>
                    <select
                      value={formData.rule_type}
                      onChange={(e) => {
                        const newRuleType = e.target.value as RuleType;
                        const availableConditions = getRuleConditionsForType(newRuleType);
                        setFormData({ 
                          ...formData, 
                          rule_type: newRuleType,
                          condition: availableConditions[0]
                        });
                      }}
                      className="form-select"
                    >
                      {Object.values(RuleType).map(type => (
                        <option key={type} value={type}>
                          {type.replace('_', ' ').toUpperCase()}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Condition *</label>
                    <select
                      value={formData.condition}
                      onChange={(e) => setFormData({ ...formData, condition: e.target.value as RuleCondition })}
                      className="form-select"
                    >
                      {availableConditions.map(condition => (
                        <option key={condition} value={condition}>
                          {condition.replace('_', ' ').toUpperCase()}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Threshold *</label>
                    <input
                      type="number"
                      step="0.01"
                      value={formData.threshold}
                      onChange={(e) => setFormData({ ...formData, threshold: parseFloat(e.target.value) || 0 })}
                      className="form-input"
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Cooldown (seconds)</label>
                    <input
                      type="number"
                      min="0"
                      value={formData.cooldown_seconds}
                      onChange={(e) => setFormData({ ...formData, cooldown_seconds: parseInt(e.target.value) || 300 })}
                      className="form-input"
                    />
                  </div>

                  {(formData.rule_type === RuleType.RATE_OF_CHANGE) && (
                    <div className="form-group">
                      <label>Time Window (seconds)</label>
                      <input
                        type="number"
                        min="1"
                        value={formData.time_window_seconds || ''}
                        onChange={(e) => setFormData({ ...formData, time_window_seconds: parseInt(e.target.value) || undefined })}
                        className="form-input"
                      />
                    </div>
                  )}

                  {(formData.rule_type === RuleType.CROSSOVER) && (
                    <div className="form-group">
                      <label>Moving Average Period</label>
                      <input
                        type="number"
                        min="2"
                        value={formData.moving_average_period || ''}
                        onChange={(e) => setFormData({ ...formData, moving_average_period: parseInt(e.target.value) || undefined })}
                        className="form-input"
                      />
                    </div>
                  )}
                </div>

                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.active}
                      onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                    />
                    Active (rule will evaluate immediately)
                  </label>
                </div>
              </div>

              {/* Rule Preview */}
              {showPreview && previewText && (
                <div className="rule-preview">
                  <h4>Rule Preview</h4>
                  <p className="preview-text">{previewText}</p>
                </div>
              )}

              {/* Validation Errors */}
              {validationErrors.length > 0 && (
                <div className="validation-errors">
                  <h4>Please fix the following errors:</h4>
                  <ul>
                    {validationErrors.map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button 
                onClick={() => setShowPreview(!showPreview)}
                className="btn btn-secondary"
              >
                {showPreview ? 'Hide Preview' : 'Show Preview'}
              </button>
              <button 
                onClick={() => setShowForm(false)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button 
                onClick={handleSubmitForm}
                className="btn btn-primary"
                disabled={validationErrors.length > 0 || createRuleMutation.isPending || updateRuleMutation.isPending}
              >
                {createRuleMutation.isPending || updateRuleMutation.isPending 
                  ? 'Saving...' 
                  : editingRule ? 'Update Rule' : 'Create Rule'
                }
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RuleManagement;