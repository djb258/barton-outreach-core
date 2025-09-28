import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from '../../components/ui/Header';
import WorkflowProgressTracker from '../../components/ui/WorkflowProgressTracker';
import DoctrinalMetadataDisplay from '../../components/ui/DoctrinalMetadataDisplay';
import SystemHealthIndicator from '../../components/ui/SystemHealthIndicator';
import AdjusterSummaryCard from './components/AdjusterSummaryCard';
import AdjusterResultsTable from './components/AdjusterResultsTable';
import AdjusterFilterToolbar from './components/AdjusterFilterToolbar';
import Icon from '../../components/AppIcon';
import Button from '../../components/ui/Button';

const AdjusterConsole = () => {
  // BARTON DOCTRINE: Step 3 Adjuster Console State
  const [recordType, setRecordType] = useState('company'); // 'company' | 'people'
  const [failedRecords, setFailedRecords] = useState([]);
  const [filteredRecords, setFilteredRecords] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);

  // Filter states
  const [currentFilter, setCurrentFilter] = useState('all');
  const [currentErrorType, setCurrentErrorType] = useState('all');

  const [summaryStats, setSummaryStats] = useState({
    validation_failed: 0,
    enrichment_failed: 0,
    ready_for_adjustment: 0
  });

  const [errorTypeCounts, setErrorTypeCounts] = useState({});

  useEffect(() => {
    loadFailedRecords();
  }, [recordType]);

  // Apply filters when data or filters change
  useEffect(() => {
    applyFilters();
  }, [failedRecords, currentFilter, currentErrorType]);

  const applyFilters = () => {
    let filtered = [...failedRecords];

    // Apply status filter
    if (currentFilter !== 'all') {
      filtered = filtered.filter(record => {
        switch (currentFilter) {
          case 'promoted':
            return record.validation_status === 'validated';
          case 'pending':
            return record.validation_status === 'pending';
          case 'adjusted':
            return record.validation_status === 'failed' && record.validation_failures?.some(f => f.status === 'fixed');
          default:
            return true;
        }
      });
    }

    // Apply error type filter
    if (currentErrorType !== 'all') {
      filtered = filtered.filter(record => {
        return record.validation_failures?.some(failure => failure.error_type === currentErrorType);
      });
    }

    setFilteredRecords(filtered);
  };

  const calculateErrorTypeCounts = (records) => {
    const counts = {};
    records.forEach(record => {
      if (record.validation_failures) {
        record.validation_failures.forEach(failure => {
          counts[failure.error_type] = (counts[failure.error_type] || 0) + 1;
        });
      }
    });
    return counts;
  };

  const loadFailedRecords = async () => {
    setIsLoading(true);

    try {
      console.log(`[ADJUSTER-CONSOLE] Loading ${recordType} records for adjustment`);

      const response = await fetch(`/api/adjuster-fetch?type=${recordType}&limit=50`);
      const data = await response.json();

      if (data.success) {
        setFailedRecords(data.records);
        setSummaryStats(data.summary);
        setErrorTypeCounts(calculateErrorTypeCounts(data.records));
        console.log(`[ADJUSTER-CONSOLE] Loaded ${data.records.length} failed ${recordType} records`);
      } else {
        console.error('[ADJUSTER-CONSOLE] Failed to load records:', data.error);
        setFailedRecords([]);
        setFilteredRecords([]);
        setErrorTypeCounts({});
      }

    } catch (error) {
      console.error('[ADJUSTER-CONSOLE] Load error:', error);
      setFailedRecords([]);
      setFilteredRecords([]);
      setErrorTypeCounts({});
    } finally {
      setIsLoading(false);
    }
  };

  // Handle record type change
  const handleRecordTypeChange = (newType) => {
    setRecordType(newType);
    setCurrentFilter('all');
    setCurrentErrorType('all');
  };

  // Handle filter changes
  const handleFilterChange = (newFilter) => {
    setCurrentFilter(newFilter);
  };

  const handleErrorTypeChange = (newErrorType) => {
    setCurrentErrorType(newErrorType);
  };

  // Handle saving a record after manual adjustment
  const handleSaveRecord = async (uniqueId, updatedFields) => {
    setIsSaving(true);

    try {
      console.log(`[ADJUSTER-CONSOLE] Saving adjustments for ${uniqueId}`, updatedFields);

      const response = await fetch('/api/adjuster-save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          unique_id: uniqueId,
          updated_fields: updatedFields,
          record_type: recordType
        })
      });

      const data = await response.json();

      if (data.status === 'success') {
        console.log(`[ADJUSTER-CONSOLE] Successfully saved ${uniqueId}:`, data.changes_applied);

        // Reload the failed records to reflect changes
        await loadFailedRecords();

        return {
          success: true,
          message: `Applied ${data.changes_applied.length} changes. Re-validation ${data.validation_triggered ? 'triggered' : 'skipped'}.`
        };
      } else {
        console.error('[ADJUSTER-CONSOLE] Save failed:', data.errors);
        return {
          success: false,
          message: data.errors.join(', ')
        };
      }

    } catch (error) {
      console.error('[ADJUSTER-CONSOLE] Save error:', error);
      return {
        success: false,
        message: 'Failed to save record adjustments'
      };
    } finally {
      setIsSaving(false);
    }
  };

  // Handle record selection for future bulk operations
  const handleRecordSelect = (uniqueId, selected) => {
    setSelectedRecord(selected ? uniqueId : null);
  };

  // Calculate filter counts
  const promotedCount = failedRecords.filter(r => r.validation_status === 'validated').length;
  const pendingCount = failedRecords.filter(r => r.validation_status === 'pending').length;
  const adjustedCount = failedRecords.filter(r =>
    r.validation_status === 'failed' && r.validation_failures?.some(f => f.status === 'fixed')
  ).length;

  const adjustedRecordsCount = failedRecords.filter(r => r.validation_status === 'pending').length;
  const canProceedToNextStep = adjustedRecordsCount > 0;

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <WorkflowProgressTracker
        currentStep={3}
        workflowId="WF-2025-001"
        processId="PRC-ADJ-001"
        canProceed={canProceedToNextStep}
      />

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {/* Header */}
        <Header
          title="Adjuster Console"
          subtitle="Step 3 of Barton Doctrine Pipeline - Human Review & Correction"
          processId="02.01.03.04.10000.001"
          altitude="EXECUTION"
        />

        {/* Content Area */}
        <div className="p-6 space-y-6 overflow-y-auto h-[calc(100vh-80px)]">

          {/* Record Type Selector */}
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center space-x-4">
              <h3 className="text-lg font-medium">Record Type:</h3>
              <div className="flex space-x-2">
                <Button
                  variant={recordType === 'company' ? 'default' : 'outline'}
                  onClick={() => handleRecordTypeChange('company')}
                  disabled={isLoading}
                >
                  Companies
                </Button>
                <Button
                  variant={recordType === 'people' ? 'default' : 'outline'}
                  onClick={() => handleRecordTypeChange('people')}
                  disabled={isLoading}
                >
                  People
                </Button>
              </div>
            </div>
          </div>

          {/* Adjuster Summary Card */}
          <AdjusterSummaryCard
            summaryStats={summaryStats}
            recordType={recordType}
            isLoading={isLoading}
          />

          {/* Filter Toolbar */}
          <AdjusterFilterToolbar
            currentFilter={currentFilter}
            onFilterChange={handleFilterChange}
            currentErrorType={currentErrorType}
            onErrorTypeChange={handleErrorTypeChange}
            totalCount={failedRecords.length}
            promotedCount={promotedCount}
            pendingCount={pendingCount}
            adjustedCount={adjustedCount}
            errorTypeCounts={errorTypeCounts}
            recordType={recordType}
          />

          {/* Results Table */}
          <AdjusterResultsTable
            records={filteredRecords}
            recordType={recordType}
            isLoading={isLoading}
            isSaving={isSaving}
            selectedRecord={selectedRecord}
            onRecordSelect={handleRecordSelect}
            onSaveRecord={handleSaveRecord}
          />

          {/* Control Buttons */}
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  iconName="RefreshCcw"
                  onClick={loadFailedRecords}
                  disabled={isLoading}
                >
                  {isLoading ? 'Loading...' : 'Refresh Records'}
                </Button>
              </div>

              <div className="flex space-x-3">
                <Link to="/data-validation-console">
                  <Button variant="outline" iconName="ArrowLeft">
                    Back to Validation
                  </Button>
                </Link>

                <Link to="/campaign-deployment">
                  <Button
                    variant="default"
                    iconName="ArrowRight"
                    iconPosition="right"
                    disabled={!canProceedToNextStep}
                  >
                    Proceed to Campaign
                  </Button>
                </Link>
              </div>
            </div>
          </div>

          {/* Status Messages */}
          {failedRecords.length === 0 && !isLoading && (
            <div className="bg-success/10 border border-success/20 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Icon name="CheckCircle" size={20} color="var(--color-success)" />
                <span className="text-sm font-medium text-success">
                  No {recordType} records need adjustment. All validation issues have been resolved.
                </span>
              </div>
            </div>
          )}

          {failedRecords.length > 0 && filteredRecords.length === 0 && !isLoading && (
            <div className="bg-warning/10 border border-warning/20 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Icon name="Filter" size={20} color="var(--color-warning)" />
                <span className="text-sm font-medium text-warning">
                  No records match the current filters. Try adjusting your filter selection.
                </span>
              </div>
            </div>
          )}

          {filteredRecords.length > 0 && (
            <div className="bg-info/10 border border-info/20 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Icon name="Info" size={20} color="var(--color-info)" />
                <span className="text-sm font-medium text-info">
                  {filteredRecords.length} {recordType} records {currentFilter !== 'all' || currentErrorType !== 'all' ? 'matching filters' : ''} require manual adjustment. Click on any field to edit inline.
                </span>
              </div>
            </div>
          )}

          <SystemHealthIndicator />

        </div>
      </div>
    </div>
  );
};

export default AdjusterConsole;