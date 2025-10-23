import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from '../../components/ui/Header';
import WorkflowProgressTracker from '../../components/ui/WorkflowProgressTracker';
import SystemHealthIndicator from '../../components/ui/SystemHealthIndicator';
import AttributionSummaryCard from './components/AttributionSummaryCard';
import AttributionResultsTable from './components/AttributionResultsTable';
import AttributionAnalytics from './components/AttributionAnalytics';
import Button from '../../components/ui/Button';
import Icon from '../../components/AppIcon';

const AttributionConsole = () => {
  // BARTON DOCTRINE: Step 5 Attribution Console State
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'analytics' | 'ple' | 'bit'
  const [dateRange, setDateRange] = useState('30_days'); // '7_days' | '30_days' | '90_days' | 'custom'
  const [attributionSummary, setAttributionSummary] = useState({
    total_attributions: 0,
    outcomes: {
      closed_won: { count: 0, revenue: 0 },
      closed_lost: { count: 0, potential_revenue: 0 },
      nurture: { count: 0 },
      churn: { count: 0 },
      qualified: { count: 0 },
      disqualified: { count: 0 }
    },
    conversion_rates: {
      win_rate: 0,
      qualification_rate: 0,
      churn_rate: 0
    },
    revenue_metrics: {
      total_revenue: 0,
      average_deal_size: 0,
      revenue_per_attribution: 0
    },
    time_metrics: {
      average_sales_cycle_days: 0,
      average_touchpoints_to_close: 0
    }
  });
  const [attributionRecords, setAttributionRecords] = useState([]);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadAttributionData();
  }, [dateRange, activeTab]);

  // Load attribution summary and records
  const loadAttributionData = async () => {
    setIsLoading(true);

    try {
      console.log(`[ATTRIBUTION-CONSOLE] Loading attribution data for ${dateRange}`);

      const dateParams = getDateRangeParams(dateRange);

      // Load summary data
      const summaryResponse = await fetch(
        `/api/attribution-analytics?type=summary${dateParams}`
      );
      const summaryData = await summaryResponse.json();

      if (summaryData.success) {
        setAttributionSummary(summaryData.data);
      }

      // Load detailed records
      const recordsResponse = await fetch(
        `/api/attribution-records?limit=100${dateParams}`
      );
      const recordsData = await recordsResponse.json();

      if (recordsData.success) {
        setAttributionRecords(recordsData.data);
      }

      // Load analytics data for specific tabs
      if (activeTab === 'analytics') {
        await loadAnalyticsData();
      }

      console.log(`[ATTRIBUTION-CONSOLE] Loaded ${attributionSummary.total_attributions} attribution records`);

    } catch (error) {
      console.error('[ATTRIBUTION-CONSOLE] Load error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Load analytics data (PLE, BIT performance)
  const loadAnalyticsData = async () => {
    try {
      const dateParams = getDateRangeParams(dateRange);

      const [pleResponse, bitResponse] = await Promise.all([
        fetch(`/api/attribution-analytics?type=ple_performance${dateParams}`),
        fetch(`/api/attribution-analytics?type=bit_signals${dateParams}`)
      ]);

      const [pleData, bitData] = await Promise.all([
        pleResponse.json(),
        bitResponse.json()
      ]);

      setAnalyticsData({
        ple: pleData.success ? pleData.data : null,
        bit: bitData.success ? bitData.data : null
      });

    } catch (error) {
      console.error('[ATTRIBUTION-CONSOLE] Analytics load error:', error);
    }
  };

  // Handle date range change
  const handleDateRangeChange = (newRange) => {
    setDateRange(newRange);
  };

  // Handle tab change
  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  // Export attribution data
  const handleExportData = () => {
    const exportData = {
      summary: attributionSummary,
      records: attributionRecords,
      analytics: analyticsData,
      exported_at: new Date().toISOString(),
      date_range: dateRange,
      barton_doctrine_step: 5
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attribution_export_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Get date range parameters for API calls
  const getDateRangeParams = (range) => {
    const now = new Date();
    let dateFrom, dateTo;

    switch (range) {
      case '7_days':
        dateFrom = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30_days':
        dateFrom = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      case '90_days':
        dateFrom = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
        break;
      default:
        return '';
    }

    dateTo = now;
    return `&date_from=${dateFrom.toISOString().split('T')[0]}&date_to=${dateTo.toISOString().split('T')[0]}`;
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <WorkflowProgressTracker
        currentStep={5}
        workflowId="WF-2025-001"
        processId="PRC-ATTR-001"
        canProceed={attributionSummary.total_attributions > 0}
      />

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {/* Header */}
        <Header
          title="Attribution Console"
          subtitle="Step 5 of Barton Doctrine Pipeline - Closed-Loop Attribution Analytics"
          processId="02.01.03.05.10000.001"
          altitude="EXECUTION"
        />

        {/* Content Area */}
        <div className="p-6 space-y-6 overflow-y-auto h-[calc(100vh-80px)]">

          {/* Tab Navigation & Controls */}
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <h3 className="text-lg font-medium">Attribution Analytics:</h3>
                <div className="flex space-x-1">
                  {[
                    { id: 'overview', label: 'Overview', icon: 'BarChart3' },
                    { id: 'analytics', label: 'Analytics', icon: 'TrendingUp' },
                    { id: 'ple', label: 'PLE Performance', icon: 'Target' },
                    { id: 'bit', label: 'BIT Signals', icon: 'Zap' }
                  ].map((tab) => (
                    <Button
                      key={tab.id}
                      variant={activeTab === tab.id ? 'default' : 'outline'}
                      size="sm"
                      iconName={tab.icon}
                      onClick={() => handleTabChange(tab.id)}
                      disabled={isLoading}
                    >
                      {tab.label}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="flex items-center space-x-2">
                {/* Date Range Selector */}
                <select
                  value={dateRange}
                  onChange={(e) => handleDateRangeChange(e.target.value)}
                  className="px-3 py-1 border border-border rounded text-sm bg-background"
                  disabled={isLoading}
                >
                  <option value="7_days">Last 7 Days</option>
                  <option value="30_days">Last 30 Days</option>
                  <option value="90_days">Last 90 Days</option>
                </select>

                <Button
                  variant="outline"
                  size="sm"
                  iconName="Download"
                  onClick={handleExportData}
                  disabled={isLoading || attributionRecords.length === 0}
                >
                  Export Data
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  iconName="RefreshCcw"
                  onClick={loadAttributionData}
                  disabled={isLoading}
                >
                  {isLoading ? 'Loading...' : 'Refresh'}
                </Button>
              </div>
            </div>
          </div>

          {/* Attribution Summary Card */}
          <AttributionSummaryCard
            summary={attributionSummary}
            dateRange={dateRange}
            isLoading={isLoading}
          />

          {/* Tab Content */}
          {activeTab === 'overview' && (
            <AttributionResultsTable
              records={attributionRecords}
              isLoading={isLoading}
              onRecordClick={(record) => {
                console.log('Attribution record clicked:', record);
              }}
            />
          )}

          {activeTab === 'analytics' && analyticsData && (
            <AttributionAnalytics
              pleData={analyticsData.ple}
              bitData={analyticsData.bit}
              isLoading={isLoading}
            />
          )}

          {activeTab === 'ple' && analyticsData?.ple && (
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-medium mb-4">PLE (Perpetual Lead Engine) Performance</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-success">
                    {analyticsData.ple.model_accuracy.overall_accuracy}%
                  </div>
                  <div className="text-sm text-muted-foreground">Overall Accuracy</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-info">
                    {analyticsData.ple.scoring_impact.accurate_predictions}
                  </div>
                  <div className="text-sm text-muted-foreground">Accurate Predictions</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-warning">
                    {analyticsData.ple.scoring_impact.prediction_errors}
                  </div>
                  <div className="text-sm text-muted-foreground">Prediction Errors</div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'bit' && analyticsData?.bit && (
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-medium mb-4">BIT (Buyer Intent Trigger) Signals</h3>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Top Performing Signals</h4>
                  <div className="flex flex-wrap gap-2">
                    {analyticsData.bit.top_performing_signals.map((signal, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-success/10 text-success rounded text-xs"
                      >
                        {signal}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Underperforming Signals</h4>
                  <div className="flex flex-wrap gap-2">
                    {analyticsData.bit.underperforming_signals.map((signal, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-destructive/10 text-destructive rounded text-xs"
                      >
                        {signal}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Control Buttons */}
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  iconName="Settings"
                  onClick={() => console.log('Configure attribution settings')}
                >
                  Configure Settings
                </Button>

                <Button
                  variant="outline"
                  iconName="Webhook"
                  onClick={() => console.log('Manage webhooks')}
                >
                  Manage Webhooks
                </Button>
              </div>

              <div className="flex space-x-3">
                <Link to="/promotion-console">
                  <Button variant="outline" iconName="ArrowLeft">
                    Back to Promotion
                  </Button>
                </Link>

                <Link to="/dashboard">
                  <Button
                    variant="default"
                    iconName="ArrowRight"
                    iconPosition="right"
                  >
                    View Dashboard
                  </Button>
                </Link>
              </div>
            </div>
          </div>

          {/* Status Messages */}
          {attributionSummary.total_attributions === 0 && !isLoading && (
            <div className="bg-info/10 border border-info/20 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Icon name="Info" size={20} color="var(--color-info)" />
                <span className="text-sm font-medium text-info">
                  No attribution data found for the selected time period.
                  Set up CRM webhooks to start receiving attribution data.
                </span>
              </div>
            </div>
          )}

          {attributionSummary.total_attributions > 0 && (
            <div className="bg-success/10 border border-success/20 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Icon name="CheckCircle" size={20} color="var(--color-success)" />
                <span className="text-sm font-medium text-success">
                  Closed-loop attribution active: {attributionSummary.total_attributions} outcomes tracked,
                  feeding back into PLE and BIT systems for continuous learning.
                </span>
              </div>
            </div>
          )}

          {/* Step 5 Doctrine Notice */}
          <div className="bg-accent/10 border border-accent/20 rounded-lg p-4">
            <div className="flex items-start space-x-2">
              <Icon name="Repeat" size={16} color="var(--color-accent)" className="mt-0.5" />
              <div className="text-xs text-accent">
                <span className="font-medium">Barton Doctrine Step 5:</span> Closed-loop attribution captures
                CRM outcomes and feeds them back to PLE scoring and BIT signal weighting for continuous pipeline improvement.
              </div>
            </div>
          </div>

          <SystemHealthIndicator />

        </div>
      </div>
    </div>
  );
};

export default AttributionConsole;