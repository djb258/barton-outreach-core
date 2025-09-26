import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from '../../components/ui/Header';
import WorkflowProgressTracker from '../../components/ui/WorkflowProgressTracker';
import SystemHealthIndicator from '../../components/ui/SystemHealthIndicator';
import PipelineHealthCard from './components/PipelineHealthCard';
import DataQualityCard from './components/DataQualityCard';
import CampaignPerformanceCard from './components/CampaignPerformanceCard';
import AttributionCard from './components/AttributionCard';
import Button from '../../components/ui/Button';
import Icon from '../../components/AppIcon';

const MarketingDashboard = () => {
  const [activeTimeRange, setActiveTimeRange] = useState('30_days');
  const [activeView, setActiveView] = useState('overview');
  const [dashboardMetrics, setDashboardMetrics] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, [activeTimeRange, activeView]);

  const loadDashboardData = async () => {
    setIsLoading(true);

    try {
      console.log(`[MARKETING-DASHBOARD] Loading dashboard data (${activeTimeRange})`);

      const [metricsResponse, trendsResponse] = await Promise.all([
        fetch('/api/dashboard-metrics'),
        fetch(`/api/dashboard-trends?period=${activeView === 'trends' ? 'weekly' : 'monthly'}`)
      ]);

      const [metricsData, trendsData] = await Promise.all([
        metricsResponse.json(),
        trendsResponse.json()
      ]);

      if (metricsData.success) {
        setDashboardMetrics(metricsData.data);
      }

      if (trendsData.success) {
        setTrendData(trendsData.data);
      }

      setLastRefresh(new Date());
      console.log('[MARKETING-DASHBOARD] Dashboard data loaded successfully');

    } catch (error) {
      console.error('[MARKETING-DASHBOARD] Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefreshData = async () => {
    setIsLoading(true);

    try {
      const [metricsResponse, trendsResponse] = await Promise.all([
        fetch('/api/dashboard-metrics?refresh=true'),
        fetch(`/api/dashboard-trends?period=weekly&refresh=true`)
      ]);

      const [metricsData, trendsData] = await Promise.all([
        metricsResponse.json(),
        trendsResponse.json()
      ]);

      if (metricsData.success) {
        setDashboardMetrics(metricsData.data);
      }

      if (trendsData.success) {
        setTrendData(trendsData.data);
      }

      setLastRefresh(new Date());
      console.log('[MARKETING-DASHBOARD] Dashboard refreshed with latest data');

    } catch (error) {
      console.error('[MARKETING-DASHBOARD] Failed to refresh dashboard:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportDashboard = () => {
    const exportData = {
      metrics: dashboardMetrics,
      trends: trendData,
      exported_at: new Date().toISOString(),
      time_range: activeTimeRange,
      view: activeView,
      barton_doctrine_step: 6
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `marketing_dashboard_export_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDrillDown = (metric, value) => {
    console.log(`[MARKETING-DASHBOARD] Drilling down into ${metric}:`, value);
    // TODO: Navigate to detailed view or modal with raw records
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <WorkflowProgressTracker
        currentStep={6}
        workflowId="WF-2025-001"
        processId="PRC-DASH-001"
        canProceed={dashboardMetrics !== null}
      />

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {/* Header */}
        <Header
          title="Marketing Dashboard"
          subtitle="Step 6 of Barton Doctrine Pipeline - Performance Analytics & Insights"
          processId="02.01.03.06.10000.001"
          altitude="EXECUTION"
        />

        {/* Content Area */}
        <div className="p-6 space-y-6 overflow-y-auto h-[calc(100vh-80px)]">

          {/* Dashboard Controls */}
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <h3 className="text-lg font-medium">Dashboard View:</h3>
                <div className="flex space-x-1">
                  {[
                    { id: 'overview', label: 'Overview', icon: 'BarChart3' },
                    { id: 'performance', label: 'Performance', icon: 'TrendingUp' },
                    { id: 'trends', label: 'Trends', icon: 'LineChart' },
                    { id: 'attribution', label: 'Attribution', icon: 'Repeat' }
                  ].map((view) => (
                    <Button
                      key={view.id}
                      variant={activeView === view.id ? 'default' : 'outline'}
                      size="sm"
                      iconName={view.icon}
                      onClick={() => setActiveView(view.id)}
                      disabled={isLoading}
                    >
                      {view.label}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="flex items-center space-x-2">
                {/* Time Range Selector */}
                <select
                  value={activeTimeRange}
                  onChange={(e) => setActiveTimeRange(e.target.value)}
                  className="px-3 py-1 border border-border rounded text-sm bg-background"
                  disabled={isLoading}
                >
                  <option value="7_days">Last 7 Days</option>
                  <option value="30_days">Last 30 Days</option>
                  <option value="90_days">Last 90 Days</option>
                  <option value="6_months">Last 6 Months</option>
                  <option value="1_year">Last Year</option>
                </select>

                <Button
                  variant="outline"
                  size="sm"
                  iconName="Download"
                  onClick={handleExportDashboard}
                  disabled={isLoading || !dashboardMetrics}
                >
                  Export
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  iconName="RefreshCcw"
                  onClick={handleRefreshData}
                  disabled={isLoading}
                >
                  {isLoading ? 'Refreshing...' : 'Refresh'}
                </Button>
              </div>
            </div>

            {lastRefresh && (
              <div className="mt-2 text-xs text-muted-foreground">
                Last updated: {lastRefresh.toLocaleString()}
              </div>
            )}
          </div>

          {/* Dashboard Cards */}
          {dashboardMetrics && (
            <>
              {/* Pipeline Health Card */}
              <PipelineHealthCard
                metrics={dashboardMetrics.pipeline_health}
                isLoading={isLoading}
                onDrillDown={handleDrillDown}
                timeRange={activeTimeRange}
              />

              {/* Data Quality Card */}
              <DataQualityCard
                metrics={dashboardMetrics.data_quality}
                isLoading={isLoading}
                onDrillDown={handleDrillDown}
                timeRange={activeTimeRange}
              />

              {/* Campaign Performance Card */}
              <CampaignPerformanceCard
                metrics={dashboardMetrics.campaign_performance}
                isLoading={isLoading}
                onDrillDown={handleDrillDown}
                timeRange={activeTimeRange}
                showComparison={activeView === 'performance'}
              />

              {/* Attribution Card */}
              <AttributionCard
                metrics={dashboardMetrics.attribution_summary}
                trends={trendData?.trends}
                isLoading={isLoading}
                onDrillDown={handleDrillDown}
                timeRange={activeTimeRange}
                showTrends={activeView === 'trends'}
              />
            </>
          )}

          {/* Loading State */}
          {isLoading && !dashboardMetrics && (
            <div className="bg-card border border-border rounded-lg p-8 text-center">
              <Icon name="Loader2" size={32} className="animate-spin mx-auto mb-4 text-muted-foreground" />
              <p className="text-muted-foreground">Loading marketing dashboard...</p>
            </div>
          )}

          {/* No Data State */}
          {!isLoading && !dashboardMetrics && (
            <div className="bg-card border border-border rounded-lg p-8 text-center">
              <Icon name="BarChart3" size={48} className="mx-auto mb-4 text-muted-foreground opacity-50" />
              <h3 className="text-lg font-medium text-foreground mb-2">No Dashboard Data</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Unable to load dashboard metrics. Check that the materialized views are created and populated.
              </p>
              <Button
                variant="default"
                iconName="RefreshCcw"
                onClick={loadDashboardData}
              >
                Retry Loading
              </Button>
            </div>
          )}

          {/* Control Buttons */}
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  iconName="Settings"
                  onClick={() => console.log('Configure dashboard settings')}
                >
                  Dashboard Settings
                </Button>

                <Button
                  variant="outline"
                  iconName="Filter"
                  onClick={() => console.log('Advanced filters')}
                >
                  Advanced Filters
                </Button>
              </div>

              <div className="flex space-x-3">
                <Link to="/attribution-console">
                  <Button variant="outline" iconName="ArrowLeft">
                    Back to Attribution
                  </Button>
                </Link>

                <Link to="/dashboard">
                  <Button
                    variant="default"
                    iconName="ArrowRight"
                    iconPosition="right"
                  >
                    Main Dashboard
                  </Button>
                </Link>
              </div>
            </div>
          </div>

          {/* Step 6 Doctrine Notice */}
          <div className="bg-accent/10 border border-accent/20 rounded-lg p-4">
            <div className="flex items-start space-x-2">
              <Icon name="BarChart3" size={16} color="var(--color-accent)" className="mt-0.5" />
              <div className="text-xs text-accent">
                <span className="font-medium">Barton Doctrine Step 6:</span> Marketing dashboard provides real-time insights into
                pipeline health, data quality, and campaign performance. All metrics trace back to Barton IDs and differentiate
                Cold Outreach (PLE) vs Sniper Marketing (BIT) effectiveness.
              </div>
            </div>
          </div>

          {/* Performance Metrics Summary */}
          {dashboardMetrics && (
            <div className="bg-success/10 border border-success/20 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Icon name="CheckCircle" size={20} color="var(--color-success)" />
                <span className="text-sm font-medium text-success">
                  Dashboard Active: {dashboardMetrics.pipeline_health?.total_company_leads + dashboardMetrics.pipeline_health?.total_people_leads || 0} leads tracked,
                  {' '}{dashboardMetrics.attribution_summary?.closed_won?.count || 0} deals won,
                  {' '}${(dashboardMetrics.attribution_summary?.closed_won?.total_revenue || 0).toLocaleString()} revenue attributed.
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

export default MarketingDashboard;