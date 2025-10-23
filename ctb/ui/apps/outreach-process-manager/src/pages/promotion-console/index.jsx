import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from '../../components/ui/Header';
import WorkflowProgressTracker from '../../components/ui/WorkflowProgressTracker';
import SystemHealthIndicator from '../../components/ui/SystemHealthIndicator';
import PromotionSummaryCard from './components/PromotionSummaryCard';
import PromotionResultsTable from './components/PromotionResultsTable';
import Button from '../../components/ui/Button';
import Icon from '../../components/AppIcon';

const PromotionConsole = () => {
  // BARTON DOCTRINE: Step 4 Promotion Console State
  const [recordType, setRecordType] = useState('company'); // 'company' | 'people'
  const [promotionSummary, setPromotionSummary] = useState({
    total_eligible: 0,
    rows_promoted: 0,
    rows_failed: 0,
    last_promotion_at: null,
    success_rate: 100
  });
  const [promotionResults, setPromotionResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isPromoting, setIsPromoting] = useState(false);

  useEffect(() => {
    loadPromotionSummary();
  }, [recordType]);

  // Load promotion summary and eligible records
  const loadPromotionSummary = async () => {
    setIsLoading(true);

    try {
      console.log(`[PROMOTION-CONSOLE] Loading ${recordType} promotion summary`);

      // Get eligible records count from intake table
      const eligibleResponse = await fetch(`/api/promotion-eligible?type=${recordType}`);
      const eligibleData = await eligibleResponse.json();

      if (eligibleData.success) {
        setPromotionSummary(eligibleData.summary);
        console.log(`[PROMOTION-CONSOLE] Found ${eligibleData.summary.total_eligible} eligible ${recordType} records`);
      } else {
        console.error('[PROMOTION-CONSOLE] Failed to load eligible records:', eligibleData.error);
        setPromotionSummary({
          total_eligible: 0,
          rows_promoted: 0,
          rows_failed: 0,
          last_promotion_at: null,
          success_rate: 100
        });
      }

    } catch (error) {
      console.error('[PROMOTION-CONSOLE] Load error:', error);
      setPromotionSummary({
        total_eligible: 0,
        rows_promoted: 0,
        rows_failed: 0,
        last_promotion_at: null,
        success_rate: 100
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Handle record type change
  const handleRecordTypeChange = (newType) => {
    setRecordType(newType);
    setPromotionResults([]); // Clear previous results
  };

  // Handle promotion execution
  const handlePromoteRecords = async () => {
    setIsPromoting(true);

    try {
      console.log(`[PROMOTION-CONSOLE] Starting ${recordType} promotion batch`);

      const response = await fetch('/api/promote', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: recordType,
          batchSize: 50 // Process in batches of 50
        })
      });

      const data = await response.json();

      if (data.success) {
        console.log(`[PROMOTION-CONSOLE] Promotion completed: ${data.rows_promoted} promoted, ${data.rows_failed} failed`);

        setPromotionResults(data.details);

        // Update summary with new promotion results
        setPromotionSummary(prev => ({
          ...prev,
          rows_promoted: prev.rows_promoted + data.rows_promoted,
          rows_failed: prev.rows_failed + data.rows_failed,
          last_promotion_at: data.promotion_timestamp,
          success_rate: data.summary.promotion_success_rate
        }));

        // Reload summary to get updated counts
        await loadPromotionSummary();

        return {
          success: true,
          message: `Successfully promoted ${data.rows_promoted} ${recordType} records to master tables`
        };
      } else {
        console.error('[PROMOTION-CONSOLE] Promotion failed:', data.error);
        return {
          success: false,
          message: data.error || 'Promotion failed'
        };
      }

    } catch (error) {
      console.error('[PROMOTION-CONSOLE] Promotion error:', error);
      return {
        success: false,
        message: 'Failed to execute promotion batch'
      };
    } finally {
      setIsPromoting(false);
    }
  };

  // Download promotion report
  const handleDownloadReport = () => {
    const reportData = {
      record_type: recordType,
      summary: promotionSummary,
      results: promotionResults,
      generated_at: new Date().toISOString(),
      barton_doctrine_step: 4,
      process_id: 'step_4_promotion'
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `promotion_report_${recordType}_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const canPromote = promotionSummary.total_eligible > 0;

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <WorkflowProgressTracker
        currentStep={4}
        workflowId="WF-2025-001"
        processId="PRC-PROMOTE-001"
        canProceed={promotionSummary.rows_promoted > 0}
      />

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {/* Header */}
        <Header
          title="Promotion Console"
          subtitle="Step 4 of Barton Doctrine Pipeline - Master Table Promotion"
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
                  disabled={isLoading || isPromoting}
                >
                  Companies
                </Button>
                <Button
                  variant={recordType === 'people' ? 'default' : 'outline'}
                  onClick={() => handleRecordTypeChange('people')}
                  disabled={isLoading || isPromoting}
                >
                  People
                </Button>
              </div>
            </div>
          </div>

          {/* Promotion Summary Card */}
          <PromotionSummaryCard
            summary={promotionSummary}
            recordType={recordType}
            isLoading={isLoading}
          />

          {/* Promotion Results Table */}
          <PromotionResultsTable
            results={promotionResults}
            recordType={recordType}
            isLoading={isLoading}
          />

          {/* Control Buttons */}
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex space-x-3">
                <Button
                  variant="default"
                  iconName="Upload"
                  onClick={handlePromoteRecords}
                  disabled={!canPromote || isPromoting || isLoading}
                >
                  {isPromoting ? 'Promoting...' : `Promote ${recordType === 'company' ? 'Companies' : 'People'}`}
                </Button>

                <Button
                  variant="outline"
                  iconName="Download"
                  onClick={handleDownloadReport}
                  disabled={promotionResults.length === 0}
                >
                  Download Report
                </Button>

                <Button
                  variant="outline"
                  iconName="RefreshCcw"
                  onClick={loadPromotionSummary}
                  disabled={isLoading}
                >
                  {isLoading ? 'Loading...' : 'Refresh'}
                </Button>
              </div>

              <div className="flex space-x-3">
                <Link to="/adjuster-console">
                  <Button variant="outline" iconName="ArrowLeft">
                    Back to Adjuster
                  </Button>
                </Link>

                <Link to="/campaign-deployment">
                  <Button
                    variant="default"
                    iconName="ArrowRight"
                    iconPosition="right"
                    disabled={promotionSummary.rows_promoted === 0}
                  >
                    View Campaigns
                  </Button>
                </Link>
              </div>
            </div>
          </div>

          {/* Status Messages */}
          {!canPromote && !isLoading && (
            <div className="bg-success/10 border border-success/20 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Icon name="CheckCircle" size={20} color="var(--color-success)" />
                <span className="text-sm font-medium text-success">
                  All eligible {recordType} records have been promoted to master tables.
                </span>
              </div>
            </div>
          )}

          {canPromote && (
            <div className="bg-info/10 border border-info/20 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Icon name="Info" size={20} color="var(--color-info)" />
                <span className="text-sm font-medium text-info">
                  {promotionSummary.total_eligible} validated {recordType} records are ready for promotion to master tables.
                </span>
              </div>
            </div>
          )}

          {/* Step 4 Doctrine Notice */}
          <div className="bg-accent/10 border border-accent/20 rounded-lg p-4">
            <div className="flex items-start space-x-2">
              <Icon name="AlertCircle" size={16} color="var(--color-accent)" className="mt-0.5" />
              <div className="text-xs text-accent">
                <span className="font-medium">Barton Doctrine Step 4:</span> Only validated records can be promoted.
                Barton IDs remain intact. All promotions are logged to audit tables with full traceability.
              </div>
            </div>
          </div>

          <SystemHealthIndicator />

        </div>
      </div>
    </div>
  );
};

export default PromotionConsole;