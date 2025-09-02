/**
 * Configuration Manager Component - Phase 3
 * 
 * Provides interface for viewing, validating, and managing runtime
 * configuration settings with live reload capabilities.
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardHeader, 
  CardContent, 
  CardTitle 
} from '../common/Card';
import { Alert, AlertDescription } from '../common/Alert';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../common/Tabs';

export interface ConfigSection {
  [key: string]: any;
}

export interface Configuration {
  api_limits: ConfigSection;
  validation: ConfigSection;
  indicators: ConfigSection;
  cache: ConfigSection;
  monitoring: ConfigSection;
}

export interface ValidationSummary {
  total_sections: number;
  valid_sections: number;
  invalid_sections: number;
  warnings: number;
}

export interface SectionDetail {
  valid: boolean;
  errors: string[];
  warnings: string[];
  settings_count: number;
}

export interface CrossSectionValidation {
  valid: boolean;
  errors: string[];
}

export interface ConfigurationValidationResponse {
  success: boolean;
  timestamp: string;
  validation_summary: ValidationSummary;
  section_details: Record<string, SectionDetail>;
  cross_section_validation: CrossSectionValidation;
  error?: string;
}

export interface ConfigurationResponse {
  success: boolean;
  timestamp: string;
  configuration: Configuration;
  metadata: {
    sections_included: number;
    sensitive_data_included: boolean;
  };
}

export interface ConfigurationChange {
  section: string;
  setting: string;
  previous_value: any;
  new_value: any;
}

export interface ReloadResponse {
  success: boolean;
  timestamp: string;
  reload_summary: {
    sections_reloaded: number;
    changes_detected: number;
  };
  configuration_changes: ConfigurationChange[];
  message: string;
}

const ConfigurationManager: React.FC = () => {
  const [configuration, setConfiguration] = useState<Configuration | null>(null);
  const [validation, setValidation] = useState<ConfigurationValidationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [showSensitive, setShowSensitive] = useState(false);
  const [reloadHistory, setReloadHistory] = useState<ConfigurationChange[]>([]);

  const fetchConfiguration = async (includeSensitive: boolean = false) => {
    try {
      const response = await fetch(`/api/health/config/current?include_sensitive=${includeSensitive}`);
      const data: ConfigurationResponse = await response.json();
      
      if (data.success) {
        setConfiguration(data.configuration);
        setError(null);
      } else {
        throw new Error('Failed to fetch configuration');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    }
  };

  const validateConfiguration = async () => {
    try {
      const response = await fetch('/api/health/config/validate');
      const data: ConfigurationValidationResponse = await response.json();
      
      if (data.success || data.validation_summary) {
        setValidation(data);
      } else {
        throw new Error(data.error || 'Failed to validate configuration');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Validation failed');
    }
  };

  const reloadConfiguration = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/health/config/reload', {
        method: 'POST'
      });
      const data: ReloadResponse = await response.json();
      
      if (data.success) {
        setReloadHistory(data.configuration_changes);
        
        // Refresh configuration and validation after reload
        await Promise.all([
          fetchConfiguration(showSensitive),
          validateConfiguration()
        ]);
        
        setError(null);
      } else {
        throw new Error('Failed to reload configuration');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reload failed');
    } finally {
      setLoading(false);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchConfiguration(showSensitive),
        validateConfiguration()
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [showSensitive]);

  const formatConfigValue = (value: any): string => {
    if (value === null || value === undefined) {
      return 'null';
    }
    if (typeof value === 'boolean') {
      return value.toString();
    }
    if (typeof value === 'string') {
      return value === '***REDACTED***' ? value : `"${value}"`;
    }
    if (Array.isArray(value)) {
      return `[${value.join(', ')}]`;
    }
    return value.toString();
  };

  const getSectionBadgeVariant = (sectionName: string): "success" | "destructive" | "warning" | "secondary" => {
    if (!validation?.section_details[sectionName]) return 'secondary';
    
    const detail = validation.section_details[sectionName];
    if (!detail.valid) return 'destructive';
    if (detail.warnings.length > 0) return 'warning';
    return 'success';
  };

  const renderConfigurationSection = (sectionName: string, sectionData: ConfigSection) => (
    <Card key={sectionName} className="mb-4">
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg capitalize">
            {sectionName.replace('_', ' ')} Configuration
          </CardTitle>
          <Badge variant={getSectionBadgeVariant(sectionName)}>
            {validation?.section_details[sectionName]?.valid ? 'Valid' : 
             validation?.section_details[sectionName] ? 'Invalid' : 'Unknown'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {/* Validation Issues */}
        {validation?.section_details[sectionName] && (
          <>
            {validation.section_details[sectionName].errors.length > 0 && (
              <Alert variant="destructive" className="mb-4">
                <AlertDescription>
                  <strong>Errors:</strong>
                  <ul className="list-disc list-inside mt-2">
                    {validation.section_details[sectionName].errors.map((error, idx) => (
                      <li key={idx}>{error}</li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}
            {validation.section_details[sectionName].warnings.length > 0 && (
              <Alert variant="warning" className="mb-4">
                <AlertDescription>
                  <strong>Warnings:</strong>
                  <ul className="list-disc list-inside mt-2">
                    {validation.section_details[sectionName].warnings.map((warning, idx) => (
                      <li key={idx}>{warning}</li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}
          </>
        )}
        
        {/* Configuration Settings */}
        <div className="grid gap-2">
          {Object.entries(sectionData).map(([key, value]) => (
            <div key={key} className="flex justify-between items-center py-2 px-3 bg-gray-50 rounded">
              <span className="font-mono text-sm text-gray-700">{key}</span>
              <span className="font-mono text-sm text-blue-600">
                {formatConfigValue(value)}
              </span>
            </div>
          ))}
        </div>
        
        {/* Settings Count */}
        <div className="mt-3 text-sm text-gray-500">
          {Object.keys(sectionData).length} settings configured
        </div>
      </CardContent>
    </Card>
  );

  if (loading && !configuration) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Configuration Manager</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4">Loading configuration data...</div>
        </CardContent>
      </Card>
    );
  }

  if (error && !configuration) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Configuration Manager</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertDescription>
              Error loading configuration: {error}
            </AlertDescription>
          </Alert>
          <Button onClick={loadData} className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Configuration Manager</h2>
          <p className="text-sm text-gray-500 mt-1">
            Manage and validate runtime configuration settings
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={showSensitive ? "default" : "outline"}
            onClick={() => setShowSensitive(!showSensitive)}
          >
            {showSensitive ? "Hide Sensitive" : "Show Sensitive"}
          </Button>
          <Button onClick={loadData} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh"}
          </Button>
          <Button 
            onClick={reloadConfiguration} 
            variant="secondary"
            disabled={loading}
          >
            {loading ? "Reloading..." : "Reload Config"}
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Validation Overview */}
      {validation && (
        <Card>
          <CardHeader>
            <CardTitle>Configuration Validation</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {validation.validation_summary.total_sections}
                </div>
                <div className="text-sm text-gray-500">Total Sections</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {validation.validation_summary.valid_sections}
                </div>
                <div className="text-sm text-gray-500">Valid Sections</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {validation.validation_summary.invalid_sections}
                </div>
                <div className="text-sm text-gray-500">Invalid Sections</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {validation.validation_summary.warnings}
                </div>
                <div className="text-sm text-gray-500">Warnings</div>
              </div>
            </div>
            
            {/* Cross-section Validation */}
            {!validation.cross_section_validation.valid && (
              <Alert variant="destructive">
                <AlertDescription>
                  <strong>Cross-section validation errors:</strong>
                  <ul className="list-disc list-inside mt-2">
                    {validation.cross_section_validation.errors.map((error, idx) => (
                      <li key={idx}>{error}</li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Configuration Sections */}
      {configuration && (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-6 w-full">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="api_limits">API Limits</TabsTrigger>
            <TabsTrigger value="validation">Validation</TabsTrigger>
            <TabsTrigger value="indicators">Indicators</TabsTrigger>
            <TabsTrigger value="cache">Cache</TabsTrigger>
            <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(configuration).map(([sectionName, sectionData]) => (
                <Card key={sectionName} className="cursor-pointer hover:shadow-md transition-shadow"
                      onClick={() => setActiveTab(sectionName)}>
                  <CardHeader>
                    <div className="flex justify-between items-center">
                      <CardTitle className="text-base capitalize">
                        {sectionName.replace('_', ' ')}
                      </CardTitle>
                      <Badge variant={getSectionBadgeVariant(sectionName)} size="sm">
                        {Object.keys(sectionData).length} settings
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-sm text-gray-600">
                      Click to view detailed configuration
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            
            {/* Recent Changes */}
            {reloadHistory.length > 0 && (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Recent Configuration Changes</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {reloadHistory.slice(0, 10).map((change, idx) => (
                      <div key={idx} className="flex justify-between items-center p-2 bg-gray-50 rounded text-sm">
                        <div>
                          <span className="font-medium">{change.section}.{change.setting}</span>
                        </div>
                        <div className="flex gap-2">
                          <span className="text-red-600">{formatConfigValue(change.previous_value)}</span>
                          <span>→</span>
                          <span className="text-green-600">{formatConfigValue(change.new_value)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
          
          {Object.entries(configuration).map(([sectionName, sectionData]) => (
            <TabsContent key={sectionName} value={sectionName}>
              {renderConfigurationSection(sectionName, sectionData)}
            </TabsContent>
          ))}
        </Tabs>
      )}
    </div>
  );
};

export default ConfigurationManager;