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
  const [validationData, setValidationData] = useState(null);
  const [activeFilters, setActiveFilters] = useState({});
  const [selectedRecords, setSelectedRecords] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    // Simulate loading validation data
    const loadValidationData = () => {
      setIsProcessing(true);
      setTimeout(() => {
        setIsProcessing(false);
      }, 1500);
    };

    loadValidationData();
  }, []);

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
                Apply business rules, resolve validation conflicts, and ensure data quality before outreach deployment
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
        </div>

        {/* Validation Summary */}
        <div className="px-6 py-4">
          <ValidationSummaryCard
            totalRecords={2156}
            passedRecords={1847}
            warningRecords={234}
            failedRecords={75}
            onPromoteRecords={handlePromoteRecords}
            onExportResults={handleExportResults}
          />
        </div>

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