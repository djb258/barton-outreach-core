import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from '../../components/ui/Header';
import WorkflowProgressTracker from '../../components/ui/WorkflowProgressTracker';
import DoctrinalMetadataDisplay from '../../components/ui/DoctrinalMetadataDisplay';
import SystemHealthIndicator from '../../components/ui/SystemHealthIndicator';
import AdjusterSummaryCard from './components/AdjusterSummaryCard';
import AdjusterResultsTable from './components/AdjusterResultsTable';
import Icon from '../../components/AppIcon';
import Button from '../../components/ui/Button';

const AdjusterConsole = () => {
  // BARTON DOCTRINE: Step 3 Adjuster Console State
  const [recordType, setRecordType] = useState('company'); // 'company' | 'people'
  const [failedRecords, setFailedRecords] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [summaryStats, setSummaryStats] = useState({
    validation_failed: 0,
    enrichment_failed: 0,
    ready_for_adjustment: 0
  });

  useEffect(() => {
    loadFailedRecords();
  }, [recordType]);

  const loadFailedRecords = async () => {
    setIsLoading(true);

    try {
      console.log(`[ADJUSTER-CONSOLE] Loading ${recordType} records for adjustment`);

      const response = await fetch(`/api/adjuster-fetch?type=${recordType}&limit=50`);
      const data = await response.json();

      if (data.success) {
        setFailedRecords(data.records);
        setSummaryStats(data.summary);
        console.log(`[ADJUSTER-CONSOLE] Loaded ${data.records.length} failed ${recordType} records`);
      } else {
        console.error('[ADJUSTER-CONSOLE] Failed to load records:', data.error);
        setFailedRecords([]);
      }

    } catch (error) {
      console.error('[ADJUSTER-CONSOLE] Load error:', error);
      setFailedRecords([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle record type change
  const handleRecordTypeChange = (newType) => {
    setRecordType(newType);
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

          {/* Results Table */}
          <AdjusterResultsTable
            records={failedRecords}
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

          {failedRecords.length > 0 && (
            <div className="bg-info/10 border border-info/20 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Icon name="Info" size={20} color="var(--color-info)" />
                <span className="text-sm font-medium text-info">
                  {failedRecords.length} {recordType} records require manual adjustment. Click on any field to edit inline.
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