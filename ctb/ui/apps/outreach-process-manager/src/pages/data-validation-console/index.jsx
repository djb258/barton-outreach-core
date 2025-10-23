import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from '../../components/ui/Header';
import WorkflowProgressTracker from '../../components/ui/WorkflowProgressTracker';
import DoctrinalMetadataDisplay from '../../components/ui/DoctrinalMetadataDisplay';
import SystemHealthIndicator from '../../components/ui/SystemHealthIndicator';
import ValidationRulePanel from './components/ValidationRulePanel';
import ValidationResultsTable from './components/ValidationResultsTable';
import ValidationFilterToolbar from './components/ValidationFilterToolbar';
import IntegrationStatusPanel from './components/IntegrationStatusPanel';
import ValidationSummaryCard from './components/ValidationSummaryCard';
import Icon from '../../components/AppIcon';
import Button from '../../components/ui/Button';

const DataValidationConsole = () => {
  // BARTON DOCTRINE: Step 2A Validation vs Step 2B Enrichment State
  const [validationType, setValidationType] = useState('companies'); // 'companies' | 'people' | 'enrichment'
  const [validationData, setValidationData] = useState(null);
  const [activeFilters, setActiveFilters] = useState({});
  const [selectedRecords, setSelectedRecords] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [validationResults, setValidationResults] = useState(null);
  const [enrichmentStatus, setEnrichmentStatus] = useState(null);
  const [summaryStats, setSummaryStats] = useState({
    total: 0,
    validated: 0,
    failed: 0,
    warnings: 0
  });

  useEffect(() => {
    // Load validation data based on selected type
    loadValidationData();
  }, [validationType]);

  const loadValidationData = async () => {
    setIsProcessing(true);

    // Reset stats
    setSummaryStats({ total: 0, validated: 0, failed: 0, warnings: 0 });

    try {
      if (validationType === 'enrichment') {
        // Load enrichment status
        const response = await fetch('/api/enrich-status');
        const statusData = await response.json();
        setEnrichmentStatus(statusData);

        // Set summary stats for enrichment
        setSummaryStats({
          total: statusData.companies.total_records + statusData.people.total_records,
          validated: statusData.companies.enriched + statusData.people.enriched,
          failed: statusData.companies.failed + statusData.people.failed,
          warnings: statusData.companies.pending + statusData.people.pending
        });
      } else {
        // Mock data for validation types
        setTimeout(() => {
          if (validationType === 'companies') {
            setSummaryStats({
              total: 2156,
              validated: 1847,
              failed: 75,
              warnings: 234
            });
          } else {
            setSummaryStats({
              total: 8642,
              validated: 7234,
              failed: 456,
              warnings: 952
            });
          }
        }, 1500);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRuleChange = (ruleId, updates) => {
    console.log('Rule updated:', ruleId, updates);
    // Handle rule configuration changes
  };

  const handleTestRule = (ruleId, logic) => {
    console.log('Testing rule:', ruleId, logic);
    // Handle rule testing
  };

  const handleFilterChange = (filters) => {
    setActiveFilters(filters);
    console.log('Filters applied:', filters);
    // Apply filters to validation results
  };

  const handleBulkAction = (action, recordIds) => {
    console.log('Bulk action:', action, recordIds);
    setIsProcessing(true);
    
    setTimeout(() => {
      setIsProcessing(false);
      setSelectedRecords([]);
    }, 2000);
  };

  const handleRecordEdit = (recordId, updates) => {
    console.log('Record edited:', recordId, updates);
    // Handle inline record editing
  };

  const handleRecordApprove = (recordId) => {
    console.log('Record approved:', recordId);
    // Handle record approval
  };

  // BARTON DOCTRINE: Validation Type Toggle Handler
  const handleValidationTypeChange = (newType) => {
    if (newType !== validationType) {
      setValidationType(newType);
      setSelectedRecords([]);
      setActiveFilters({});
      console.log(`[VALIDATION-CONSOLE] Switched to ${newType} validation`);
    }
  };

  // BARTON DOCTRINE: Run Validation Process
  const handleRunValidation = async () => {
    setIsProcessing(true);
    setValidationResults(null);

    try {
      let endpoint;
      let sampleData;

      if (validationType === 'companies') {
        endpoint = '/api/validate-company';
        sampleData = {
          companies: [
            {
              company_name: "Test Company",
              website_url: "https://test.com",
              industry: "Technology",
              employee_count: 100,
              company_phone: "+15551234567",
              address_street: "123 Main St",
              address_city: "San Francisco",
              address_state: "CA",
              address_zip: "94105",
              address_country: "USA"
            }
          ],
          metadata: {
            tool_source: "neon",
            batch_id: `console_test_${Date.now()}`
          }
        };
      } else {
        endpoint = '/api/validate-people';
        sampleData = {
          people: [
            {
              company_unique_id: "04.04.01.04.10000.001",
              slot_type: "CEO",
              first_name: "John",
              last_name: "Doe",
              title: "Chief Executive Officer",
              email: "john@test.com"
            }
          ],
          metadata: {
            tool_source: "apify",
            batch_id: `console_test_people_${Date.now()}`
          }
        };
      }

      console.log(`[VALIDATION-CONSOLE] Calling ${endpoint}`);

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(sampleData),
      });

      const result = await response.json();
      setValidationResults(result);

      if (result.success) {
        setSummaryStats({
          total: result.total_processed,
          validated: result.rows_validated,
          failed: result.rows_failed,
          warnings: result.details?.filter(d => d.warnings?.length > 0).length || 0
        });
      }

      console.log(`[VALIDATION-CONSOLE] Validation complete:`, result);

    } catch (error) {
      console.error('[VALIDATION-CONSOLE] Validation failed:', error);
      setValidationResults({
        success: false,
        error: error.message,
        rows_validated: 0,
        rows_failed: 1,
        total_processed: 1,
        details: []
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // BARTON DOCTRINE: Run Enrichment Batch Process
  const handleRunEnrichment = async (recordType = 'companies') => {
    setIsProcessing(true);
    setValidationResults(null);

    try {
      const endpoint = recordType === 'companies' ? '/api/enrich-companies' : '/api/enrich-people';
      const requestData = {
        batchSize: 10,
        statusFilter: 'failed'
      };

      console.log(`[VALIDATION-CONSOLE] Running enrichment batch: ${endpoint}`);

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      const result = await response.json();
      setValidationResults(result);

      if (result.rows_enriched !== undefined) {
        setSummaryStats({
          total: result.rows_enriched + result.rows_failed + result.rows_partial,
          validated: result.rows_enriched,
          failed: result.rows_failed,
          warnings: result.rows_partial
        });
      }

      console.log(`[VALIDATION-CONSOLE] Enrichment complete:`, result);

      // Refresh enrichment status after processing
      setTimeout(() => {
        loadValidationData();
      }, 1000);

    } catch (error) {
      console.error('[VALIDATION-CONSOLE] Enrichment failed:', error);
      setValidationResults({
        success: false,
        error: error.message,
        rows_enriched: 0,
        rows_failed: 1,
        audit_log: []
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handlePromoteRecords = () => {
    console.log('Promoting valid records to next stage');
    setIsProcessing(true);

    setTimeout(() => {
      setIsProcessing(false);
    }, 3000);
  };

  const handleExportResults = () => {
    console.log('Exporting validation results');
    // Handle export functionality
  };

  const handleSaveProfile = (filters) => {
    console.log('Saving filter profile:', filters);
    // Handle saving filter profiles
  };

  const handleLoadProfile = (profile) => {
    console.log('Loading filter profile:', profile);
    // Handle loading filter profiles
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      {/* Main Content */}
      <div className="pt-16">
        {/* Top Bar with Metadata and Progress */}
        <div className="bg-card border-b border-border px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <DoctrinalMetadataDisplay
                uniqueId="WF-2025-001"
                processId="PRC-VAL-001"
                altitude="OPERATIONAL"
              />
              <WorkflowProgressTracker
                currentStep={2}
                totalSteps={9}
                workflowId="WF-2025-001"
                processId="PRC-VAL-001"
                altitude="OPERATIONAL"
              />
            </div>
            <div className="flex items-center space-x-4">
              <SystemHealthIndicator />
              <div className="flex items-center space-x-2">
                <span className="text-sm text-muted-foreground">Last Updated:</span>
                <span className="text-sm font-data text-foreground">
                  {new Date()?.toLocaleTimeString('en-US', { hour12: false })}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Page Header */}
        <div className="px-6 py-6 border-b border-border">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">Data Validation Console</h1>
              <p className="text-muted-foreground">
                {validationType === 'enrichment'
                  ? 'Step 2B Enrichment - Fix failed records with data enhancement and normalization'
                  : `Step 2A Validation - ${validationType === 'companies' ? 'Company' : 'People'} records with 6-part unique IDs and audit trails`
                }
              </p>
            </div>
            <div className="flex items-center space-x-3">
              {isProcessing && (
                <div className="flex items-center space-x-2 px-3 py-2 bg-accent/10 text-accent rounded-md">
                  <Icon name="Loader2" size={16} className="animate-spin" />
                  <span className="text-sm">Processing...</span>
                </div>
              )}
              <Link to="/system-administration-panel">
                <Button variant="outline" iconName="Settings">
                  System Admin
                </Button>
              </Link>
              <Link to="/data-intake-dashboard">
                <Button variant="outline" iconName="ArrowLeft">
                  Back to Intake
                </Button>
              </Link>
            </div>
          </div>

          {/* BARTON DOCTRINE: Step 2A/2B Toggle */}
          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-foreground">Process Step:</span>
              <div className="flex items-center bg-muted rounded-lg p-1">
                <button
                  onClick={() => handleValidationTypeChange('companies')}
                  className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    validationType === 'companies'
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground hover:bg-background'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <Icon name="Building2" size={16} />
                    <span>Step 2A - Companies</span>
                  </div>
                </button>
                <button
                  onClick={() => handleValidationTypeChange('people')}
                  className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    validationType === 'people'
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground hover:bg-background'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <Icon name="Users" size={16} />
                    <span>Step 2A - People</span>
                  </div>
                </button>
                <button
                  onClick={() => handleValidationTypeChange('enrichment')}
                  className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    validationType === 'enrichment'
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground hover:bg-background'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <Icon name="Zap" size={16} />
                    <span>Step 2B - Enrichment</span>
                  </div>
                </button>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-3">
              {validationType === 'enrichment' ? (
                <>
                  <Button
                    onClick={() => handleRunEnrichment('companies')}
                    disabled={isProcessing}
                    variant="outline"
                    iconName="Building2"
                  >
                    {isProcessing ? 'Enriching...' : 'Enrich Companies'}
                  </Button>
                  <Button
                    onClick={() => handleRunEnrichment('people')}
                    disabled={isProcessing}
                    variant="default"
                    iconName="Users"
                  >
                    {isProcessing ? 'Enriching...' : 'Enrich People'}
                  </Button>
                </>
              ) : (
                <Button
                  onClick={handleRunValidation}
                  disabled={isProcessing}
                  variant="default"
                  iconName="Play"
                >
                  {isProcessing ? 'Validating...' : `Run ${validationType === 'companies' ? 'Company' : 'People'} Validation`}
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Validation Summary */}
        <div className="px-6 py-4">
          <ValidationSummaryCard
            totalRecords={summaryStats.total}
            passedRecords={summaryStats.validated}
            warningRecords={summaryStats.warnings}
            failedRecords={summaryStats.failed}
            validationType={validationType}
            onPromoteRecords={handlePromoteRecords}
            onExportResults={handleExportResults}
          />
        </div>

        {/* Results Display - Validation or Enrichment */}
        {validationResults && (
          <div className="px-6 py-4">
            <div className="bg-card rounded-lg border border-border p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-foreground">
                  {validationType === 'enrichment'
                    ? 'Enrichment Results'
                    : `${validationType === 'companies' ? 'Company' : 'People'} Validation Results`
                  }
                </h3>
                <div className="flex items-center space-x-2">
                  <div className={`px-2 py-1 rounded text-xs font-medium ${
                    (validationResults.success || validationResults.rows_enriched > 0)
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {(validationResults.success || validationResults.rows_enriched > 0) ? 'Success' : 'Failed'}
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {validationType === 'enrichment'
                      ? `Session: ${validationResults.session_id}`
                      : `Batch: ${validationResults.metadata?.batch_id}`
                    }
                  </span>
                </div>
              </div>

              {/* Results Summary */}
              {validationType === 'enrichment' ? (
                <div className="grid grid-cols-4 gap-4 mb-6">
                  <div className="text-center p-3 bg-muted/30 rounded-lg">
                    <div className="text-2xl font-bold text-foreground">
                      {validationResults.rows_enriched + validationResults.rows_failed + (validationResults.rows_partial || 0)}
                    </div>
                    <div className="text-sm text-muted-foreground">Total Processed</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">{validationResults.rows_enriched}</div>
                    <div className="text-sm text-muted-foreground">Enriched</div>
                  </div>
                  <div className="text-center p-3 bg-yellow-50 rounded-lg">
                    <div className="text-2xl font-bold text-yellow-600">{validationResults.rows_partial || 0}</div>
                    <div className="text-sm text-muted-foreground">Partial</div>
                  </div>
                  <div className="text-center p-3 bg-red-50 rounded-lg">
                    <div className="text-2xl font-bold text-red-600">{validationResults.rows_failed}</div>
                    <div className="text-sm text-muted-foreground">Failed</div>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-4 gap-4 mb-6">
                  <div className="text-center p-3 bg-muted/30 rounded-lg">
                    <div className="text-2xl font-bold text-foreground">{validationResults.total_processed}</div>
                    <div className="text-sm text-muted-foreground">Total Processed</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">{validationResults.rows_validated}</div>
                    <div className="text-sm text-muted-foreground">Validated</div>
                  </div>
                  <div className="text-center p-3 bg-red-50 rounded-lg">
                    <div className="text-2xl font-bold text-red-600">{validationResults.rows_failed}</div>
                    <div className="text-sm text-muted-foreground">Failed</div>
                  </div>
                  <div className="text-center p-3 bg-yellow-50 rounded-lg">
                    <div className="text-2xl font-bold text-yellow-600">
                      {validationResults.metadata?.processing_time_ms}ms
                    </div>
                    <div className="text-sm text-muted-foreground">Processing Time</div>
                  </div>
                </div>
              )}

              {/* Detailed Results */}
              {(validationResults.details || validationResults.audit_log) && (
                <div className="space-y-3">
                  <h4 className="text-md font-medium text-foreground">Detailed Results:</h4>
                  <div className="max-h-96 overflow-y-auto">
                    {(validationResults.audit_log || validationResults.details)?.map((detail, index) => (
                      <div key={index} className={`p-4 rounded-lg border ${
                        detail.status === 'success'
                          ? 'border-green-200 bg-green-50'
                          : detail.status === 'partial'
                          ? 'border-yellow-200 bg-yellow-50'
                          : 'border-red-200 bg-red-50'
                      }`}>
                        <div className="flex items-center justify-between mb-2">
                          <div className="font-medium text-foreground">
                            {validationType === 'enrichment'
                              ? `Record: ${detail.unique_id}`
                              : validationType === 'companies'
                              ? detail.company_name || detail.normalized_data?.company_name
                              : `${detail.full_name} (${detail.slot_type})`}
                          </div>
                          <div className="flex items-center space-x-2">
                            {detail.unique_id && (
                              <span className="text-xs font-mono bg-muted px-2 py-1 rounded">
                                {detail.unique_id}
                              </span>
                            )}
                            <div className={`px-2 py-1 rounded text-xs font-medium ${
                              detail.status === 'success'
                                ? 'bg-green-100 text-green-800'
                                : detail.status === 'partial'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {detail.status}
                            </div>
                          </div>
                        </div>

                        {/* Enrichment-specific: Before/After values */}
                        {validationType === 'enrichment' && (detail.before_values || detail.after_values) && (
                          <div className="mt-3 space-y-2">
                            {detail.fields_enriched && detail.fields_enriched.length > 0 && (
                              <div className="text-sm">
                                <span className="font-medium text-green-700">Fields Enriched: </span>
                                <span className="text-green-600">{detail.fields_enriched.join(', ')}</span>
                              </div>
                            )}

                            {Object.keys(detail.after_values || {}).some(key =>
                              detail.after_values[key] !== detail.before_values?.[key]
                            ) && (
                              <div className="grid grid-cols-2 gap-4 mt-2">
                                <div>
                                  <div className="text-xs font-medium text-muted-foreground mb-1">Before:</div>
                                  <div className="text-xs bg-red-50 p-2 rounded border">
                                    {Object.entries(detail.before_values || {})
                                      .filter(([key, value]) => detail.after_values?.[key] !== value)
                                      .map(([key, value]) => (
                                        <div key={key} className="flex justify-between">
                                          <span className="font-mono">{key}:</span>
                                          <span className="text-red-600">{value || '(empty)'}</span>
                                        </div>
                                      ))
                                    }
                                  </div>
                                </div>
                                <div>
                                  <div className="text-xs font-medium text-muted-foreground mb-1">After:</div>
                                  <div className="text-xs bg-green-50 p-2 rounded border">
                                    {Object.entries(detail.after_values || {})
                                      .filter(([key, value]) => detail.before_values?.[key] !== value)
                                      .map(([key, value]) => (
                                        <div key={key} className="flex justify-between">
                                          <span className="font-mono">{key}:</span>
                                          <span className="text-green-600">{value || '(empty)'}</span>
                                        </div>
                                      ))
                                    }
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Show errors */}
                        {detail.errors && detail.errors.length > 0 && (
                          <div className="mt-2">
                            <div className="text-sm font-medium text-red-700 mb-1">Errors:</div>
                            <ul className="text-sm text-red-600 space-y-1">
                              {detail.errors.map((error, errorIndex) => (
                                <li key={errorIndex} className="flex items-center space-x-1">
                                  <Icon name="AlertCircle" size={12} />
                                  <span>{error}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Show warnings */}
                        {detail.warnings && detail.warnings.length > 0 && (
                          <div className="mt-2">
                            <div className="text-sm font-medium text-yellow-700 mb-1">Warnings:</div>
                            <ul className="text-sm text-yellow-600 space-y-1">
                              {detail.warnings.map((warning, warningIndex) => (
                                <li key={warningIndex} className="flex items-center space-x-1">
                                  <Icon name="AlertTriangle" size={12} />
                                  <span>{warning}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Show company linkage for people */}
                        {validationType === 'people' && detail.company_slot_unique_id && (
                          <div className="mt-2">
                            <div className="text-xs text-muted-foreground">
                              Company: {detail.company_unique_id} | Slot: {detail.company_slot_unique_id}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Main Console Layout */}
        <div className="px-6 pb-6">
          <div className="grid grid-cols-12 gap-6 h-[calc(100vh-400px)]">
            {/* Left Panel - Validation Rules (40%) */}
            <div className="col-span-5">
              <ValidationRulePanel
                onRuleChange={handleRuleChange}
                onTestRule={handleTestRule}
              />
            </div>

            {/* Right Panel - Validation Results (60%) */}
            <div className="col-span-7 flex flex-col">
              {/* Filter Toolbar */}
              <ValidationFilterToolbar
                onFilterChange={handleFilterChange}
                onSaveProfile={handleSaveProfile}
                onLoadProfile={handleLoadProfile}
              />

              {/* Results Table */}
              <div className="flex-1">
                <ValidationResultsTable
                  data={validationData}
                  onBulkAction={handleBulkAction}
                  onRecordEdit={handleRecordEdit}
                  onRecordApprove={handleRecordApprove}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Integration Status Panel */}
        <div className="px-6 pb-6">
          <IntegrationStatusPanel />
        </div>

        {/* Next Step Navigation */}
        <div className="px-6 py-4 border-t border-border bg-muted/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Icon name="CheckCircle" size={20} color="var(--color-success)" />
              <span className="text-sm text-muted-foreground">
                Validation complete. Ready to proceed to next workflow step.
              </span>
            </div>
            <div className="flex space-x-3">
              <Button variant="outline" iconName="Save">
                Save Progress
              </Button>
              <Button variant="default" iconName="ArrowRight" iconPosition="right">
                Next Step: Quality Assessment
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataValidationConsole;