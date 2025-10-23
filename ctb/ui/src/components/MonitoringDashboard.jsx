import React, { useState, useEffect, useCallback } from 'react';
import { httpsCallable } from 'firebase/functions';
import { functions } from '../firebase/config';

const MonitoringDashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    summary: null,
    pipelineMetrics: null,
    errorMetrics: null,
    throughputData: null,
    auditTimeline: []
  });

  const [refreshStatus, setRefreshStatus] = useState({
    isLoading: false,
    lastRefresh: null,
    autoRefresh: true,
    refreshInterval: 30000 // 30 seconds
  });

  const [filters, setFilters] = useState({
    timeRange: '24h',
    granularity: 'hour',
    eventTypes: null,
    maxTimelineEvents: 50
  });

  const [ui, setUi] = useState({
    selectedTab: 'overview',
    expandedSections: {
      pipelineHealth: true,
      errorAnalysis: true,
      throughput: true,
      timeline: true
    },
    showAdvancedFilters: false
  });

  // Cloud Function calls
  const getDashboardSummary = httpsCallable(functions, 'getDashboardSummary');
  const getPipelineMetrics = httpsCallable(functions, 'getPipelineMetrics');
  const getErrorMetrics = httpsCallable(functions, 'getErrorMetrics');
  const getThroughputMetrics = httpsCallable(functions, 'getThroughputMetrics');
  const getAuditTimeline = httpsCallable(functions, 'getAuditTimeline');

  useEffect(() => {
    loadDashboardData();
  }, [filters.timeRange, filters.granularity]);

  useEffect(() => {
    if (refreshStatus.autoRefresh) {
      const interval = setInterval(() => {
        loadDashboardData();
      }, refreshStatus.refreshInterval);

      return () => clearInterval(interval);
    }
  }, [refreshStatus.autoRefresh, refreshStatus.refreshInterval]);

  const loadDashboardData = async () => {
    setRefreshStatus(prev => ({ ...prev, isLoading: true }));

    try {
      const [summaryResult, pipelineResult, errorResult, throughputResult, timelineResult] =
        await Promise.all([
          getDashboardSummary({ timeRange: filters.timeRange }),
          getPipelineMetrics({ timeRange: filters.timeRange }),
          getErrorMetrics({
            timeRange: filters.timeRange,
            groupBy: filters.granularity
          }),
          getThroughputMetrics({
            timeRange: filters.timeRange,
            granularity: filters.granularity
          }),
          getAuditTimeline({
            timeRange: filters.timeRange,
            limit: filters.maxTimelineEvents,
            eventTypes: filters.eventTypes
          })
        ]);

      setDashboardData({
        summary: summaryResult.data.summary,
        pipelineMetrics: pipelineResult.data.stageCounts,
        errorMetrics: errorResult.data,
        throughputData: throughputResult.data,
        auditTimeline: timelineResult.data.timeline
      });

      setRefreshStatus(prev => ({
        ...prev,
        isLoading: false,
        lastRefresh: new Date()
      }));

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setRefreshStatus(prev => ({ ...prev, isLoading: false }));
    }
  };

  const toggleSection = (section) => {
    setUi(prev => ({
      ...prev,
      expandedSections: {
        ...prev.expandedSections,
        [section]: !prev.expandedSections[section]
      }
    }));
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num?.toString() || '0';
  };

  const getHealthColor = (health) => {
    const colors = {
      excellent: '#10B981',
      good: '#22C55E',
      fair: '#F59E0B',
      poor: '#EF4444'
    };
    return colors[health] || '#6B7280';
  };

  const getSeverityColor = (severity) => {
    const colors = {
      error: '#EF4444',
      warning: '#F59E0B',
      success: '#10B981',
      info: '#3B82F6'
    };
    return colors[severity] || '#6B7280';
  };

  const getStageProgress = (stage, count, total) => {
    if (total === 0) return 0;
    return Math.round((count / total) * 100);
  };

  return (
    <div className="monitoring-dashboard">
      {/* Dashboard Header */}
      <div className="dashboard-header">
        <div className="header-content">
          <h1>📊 Step 7: Pipeline Monitoring Dashboard</h1>
          <p>Real-time pipeline health, throughput, and audit monitoring</p>
        </div>

        <div className="header-controls">
          <div className="refresh-controls">
            <button
              onClick={loadDashboardData}
              disabled={refreshStatus.isLoading}
              className="btn-refresh"
            >
              {refreshStatus.isLoading ? '🔄' : '↻'} Refresh
            </button>

            <label className="auto-refresh-toggle">
              <input
                type="checkbox"
                checked={refreshStatus.autoRefresh}
                onChange={(e) => setRefreshStatus(prev => ({
                  ...prev,
                  autoRefresh: e.target.checked
                }))}
              />
              Auto-refresh
            </label>

            {refreshStatus.lastRefresh && (
              <span className="last-refresh">
                Last: {refreshStatus.lastRefresh.toLocaleTimeString()}
              </span>
            )}
          </div>

          <div className="time-range-selector">
            <select
              value={filters.timeRange}
              onChange={(e) => setFilters(prev => ({ ...prev, timeRange: e.target.value }))}
              className="time-range-select"
            >
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
          </div>
        </div>
      </div>

      {refreshStatus.isLoading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <span>Loading dashboard data...</span>
        </div>
      )}

      {/* Pipeline Health Overview */}
      {dashboardData.summary && (
        <div className="health-overview">
          <div className="health-card">
            <div className="health-status">
              <div
                className="health-indicator"
                style={{ backgroundColor: getHealthColor(dashboardData.summary.pipelineHealth.status) }}
              ></div>
              <div className="health-info">
                <h3>Pipeline Health</h3>
                <span className="health-label">
                  {dashboardData.summary.pipelineHealth.status.toUpperCase()}
                </span>
              </div>
            </div>

            <div className="health-metrics">
              <div className="metric">
                <span className="metric-value">{formatNumber(dashboardData.summary.totalRecords)}</span>
                <span className="metric-label">Total Records</span>
              </div>
              <div className="metric">
                <span className="metric-value">{dashboardData.summary.pipelineHealth.completionRate}%</span>
                <span className="metric-label">Completion Rate</span>
              </div>
              <div className="metric">
                <span className="metric-value">{dashboardData.summary.errorRate}%</span>
                <span className="metric-label">Error Rate</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pipeline Stage Metrics */}
      {dashboardData.pipelineMetrics && (
        <div className="section pipeline-section">
          <div className="section-header" onClick={() => toggleSection('pipelineHealth')}>
            <h2>🏭 Pipeline Stages</h2>
            <span className="toggle-icon">
              {ui.expandedSections.pipelineHealth ? '▼' : '▶'}
            </span>
          </div>

          {ui.expandedSections.pipelineHealth && (
            <div className="pipeline-stages">
              {Object.entries(dashboardData.pipelineMetrics).map(([stage, count]) => {
                const totalRecords = dashboardData.summary?.totalRecords || 1;
                const progress = getStageProgress(stage, count, totalRecords);

                return (
                  <div key={stage} className="stage-card">
                    <div className="stage-header">
                      <h4>{stage.charAt(0).toUpperCase() + stage.slice(1)}</h4>
                      <span className="stage-count">{formatNumber(count)}</span>
                    </div>
                    <div className="stage-progress">
                      <div
                        className="progress-bar"
                        style={{ width: `${progress}%` }}
                      ></div>
                    </div>
                    <div className="stage-percentage">{progress}%</div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Error Analysis */}
      {dashboardData.errorMetrics && (
        <div className="section error-section">
          <div className="section-header" onClick={() => toggleSection('errorAnalysis')}>
            <h2>⚠️ Error Analysis</h2>
            <span className="toggle-icon">
              {ui.expandedSections.errorAnalysis ? '▼' : '▶'}
            </span>
          </div>

          {ui.expandedSections.errorAnalysis && (
            <div className="error-analysis">
              <div className="error-summary">
                <div className="error-metric">
                  <span className="metric-value">
                    {dashboardData.errorMetrics.averageResolutionTimeHours?.toFixed(1) || '0'}h
                  </span>
                  <span className="metric-label">Avg Resolution Time</span>
                </div>
                <div className="error-metric">
                  <span className="metric-value">
                    {dashboardData.errorMetrics.errorDistribution?.length || 0}
                  </span>
                  <span className="metric-label">Error Types</span>
                </div>
              </div>

              {dashboardData.errorMetrics.errorDistribution && (
                <div className="error-distribution">
                  <h4>Error Distribution</h4>
                  {dashboardData.errorMetrics.errorDistribution.map((error, index) => (
                    <div key={index} className="error-type">
                      <div className="error-info">
                        <span className="error-name">{error.errorType}</span>
                        <span className="error-percentage">{error.percentage}%</span>
                      </div>
                      <div className="error-count">{error.count} occurrences</div>
                    </div>
                  ))}
                </div>
              )}

              {dashboardData.errorMetrics.errorRates && dashboardData.errorMetrics.errorRates.length > 0 && (
                <div className="error-rates">
                  <h4>Error Rate Trend</h4>
                  <div className="error-chart">
                    {dashboardData.errorMetrics.errorRates.map((rate, index) => (
                      <div key={index} className="rate-bar">
                        <div
                          className="rate-fill"
                          style={{ height: `${Math.min(rate.errorRate * 10, 100)}%` }}
                          title={`${rate.timestamp}: ${rate.errorRate}% error rate`}
                        ></div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Throughput Analysis */}
      {dashboardData.throughputData && (
        <div className="section throughput-section">
          <div className="section-header" onClick={() => toggleSection('throughput')}>
            <h2>📈 Throughput Analysis</h2>
            <span className="toggle-icon">
              {ui.expandedSections.throughput ? '▼' : '▶'}
            </span>
          </div>

          {ui.expandedSections.throughput && (
            <div className="throughput-analysis">
              <div className="throughput-summary">
                <div className="throughput-metric">
                  <span className="metric-value">
                    {formatNumber(dashboardData.throughputData.totalThroughput?.totalEvents || 0)}
                  </span>
                  <span className="metric-label">Total Events</span>
                </div>
                <div className="throughput-metric">
                  <span className="metric-value">
                    {formatNumber(dashboardData.throughputData.totalThroughput?.promoted || 0)}
                  </span>
                  <span className="metric-label">Promoted</span>
                </div>
                <div className="throughput-metric">
                  <span className="metric-value">
                    {formatNumber(dashboardData.throughputData.totalThroughput?.synced || 0)}
                  </span>
                  <span className="metric-label">Synced</span>
                </div>
              </div>

              {dashboardData.throughputData.throughputData && (
                <div className="throughput-chart">
                  <h4>Throughput Over Time</h4>
                  <div className="chart-container">
                    {dashboardData.throughputData.throughputData.map((period, index) => (
                      <div key={index} className="throughput-bar">
                        <div className="bar-stack">
                          <div
                            className="bar-segment ingested"
                            style={{ height: `${(period.ingested / 10) || 1}px` }}
                            title={`Ingested: ${period.ingested}`}
                          ></div>
                          <div
                            className="bar-segment validated"
                            style={{ height: `${(period.validated / 10) || 1}px` }}
                            title={`Validated: ${period.validated}`}
                          ></div>
                          <div
                            className="bar-segment promoted"
                            style={{ height: `${(period.promoted / 10) || 1}px` }}
                            title={`Promoted: ${period.promoted}`}
                          ></div>
                          <div
                            className="bar-segment synced"
                            style={{ height: `${(period.synced / 10) || 1}px` }}
                            title={`Synced: ${period.synced}`}
                          ></div>
                        </div>
                        <div className="bar-label">
                          {new Date(period.timestamp).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Audit Timeline */}
      {dashboardData.auditTimeline && (
        <div className="section timeline-section">
          <div className="section-header" onClick={() => toggleSection('timeline')}>
            <h2>📋 Audit Timeline</h2>
            <span className="toggle-icon">
              {ui.expandedSections.timeline ? '▼' : '▶'}
            </span>
          </div>

          {ui.expandedSections.timeline && (
            <div className="audit-timeline">
              <div className="timeline-filters">
                <select
                  value={filters.maxTimelineEvents}
                  onChange={(e) => setFilters(prev => ({
                    ...prev,
                    maxTimelineEvents: parseInt(e.target.value)
                  }))}
                  className="timeline-limit-select"
                >
                  <option value={25}>Last 25 events</option>
                  <option value={50}>Last 50 events</option>
                  <option value={100}>Last 100 events</option>
                </select>
              </div>

              <div className="timeline-events">
                {dashboardData.auditTimeline.map((event, index) => (
                  <div key={event.id} className="timeline-event">
                    <div className="event-time">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </div>
                    <div
                      className="event-indicator"
                      style={{ backgroundColor: getSeverityColor(event.severity) }}
                    ></div>
                    <div className="event-content">
                      <div className="event-header">
                        <span className="event-action">{event.action}</span>
                        <span className={`event-severity severity-${event.severity}`}>
                          {event.severity}
                        </span>
                      </div>
                      <div className="event-description">{event.description}</div>
                      {event.processId && (
                        <div className="event-details">
                          Process: {event.processId}
                          {event.duration && ` | Duration: ${event.duration}ms`}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <style jsx>{`
        .monitoring-dashboard {
          padding: 20px;
          max-width: 1600px;
          margin: 0 auto;
          background: #f8fafc;
          min-height: 100vh;
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 30px;
          padding: 20px;
          background: white;
          border-radius: 8px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .header-content h1 {
          color: #1f2937;
          margin: 0 0 5px 0;
        }

        .header-content p {
          color: #6b7280;
          margin: 0;
        }

        .header-controls {
          display: flex;
          gap: 20px;
          align-items: center;
        }

        .refresh-controls {
          display: flex;
          gap: 10px;
          align-items: center;
        }

        .btn-refresh {
          padding: 8px 16px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }

        .btn-refresh:hover:not(:disabled) {
          background: #2563eb;
        }

        .btn-refresh:disabled {
          background: #9ca3af;
          cursor: not-allowed;
        }

        .auto-refresh-toggle {
          display: flex;
          align-items: center;
          gap: 5px;
          font-size: 14px;
          color: #4b5563;
        }

        .last-refresh {
          font-size: 12px;
          color: #6b7280;
        }

        .time-range-select {
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          background: white;
        }

        .loading-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          z-index: 1000;
          color: white;
        }

        .loading-spinner {
          width: 40px;
          height: 40px;
          border: 4px solid rgba(255, 255, 255, 0.3);
          border-top: 4px solid white;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 10px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .health-overview {
          margin-bottom: 30px;
        }

        .health-card {
          background: white;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .health-status {
          display: flex;
          align-items: center;
          gap: 15px;
        }

        .health-indicator {
          width: 20px;
          height: 20px;
          border-radius: 50%;
        }

        .health-info h3 {
          margin: 0 0 5px 0;
          color: #1f2937;
        }

        .health-label {
          font-weight: bold;
          font-size: 14px;
        }

        .health-metrics {
          display: flex;
          gap: 30px;
        }

        .metric {
          text-align: center;
        }

        .metric-value {
          display: block;
          font-size: 24px;
          font-weight: bold;
          color: #1f2937;
        }

        .metric-label {
          display: block;
          font-size: 12px;
          color: #6b7280;
          margin-top: 5px;
        }

        .section {
          background: white;
          border-radius: 8px;
          margin-bottom: 20px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .section-header {
          padding: 15px 20px;
          border-bottom: 1px solid #e5e7eb;
          cursor: pointer;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .section-header h2 {
          margin: 0;
          color: #1f2937;
        }

        .toggle-icon {
          color: #6b7280;
        }

        .pipeline-stages {
          padding: 20px;
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
        }

        .stage-card {
          padding: 15px;
          border: 1px solid #e5e7eb;
          border-radius: 6px;
        }

        .stage-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }

        .stage-header h4 {
          margin: 0;
          color: #374151;
        }

        .stage-count {
          font-weight: bold;
          color: #1f2937;
        }

        .stage-progress {
          height: 8px;
          background: #e5e7eb;
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 5px;
        }

        .progress-bar {
          height: 100%;
          background: #3b82f6;
          transition: width 0.3s ease;
        }

        .stage-percentage {
          font-size: 12px;
          color: #6b7280;
          text-align: right;
        }

        .error-analysis, .throughput-analysis, .audit-timeline {
          padding: 20px;
        }

        .error-summary, .throughput-summary {
          display: flex;
          gap: 30px;
          margin-bottom: 20px;
        }

        .error-metric, .throughput-metric {
          text-align: center;
        }

        .error-distribution, .error-rates {
          margin-bottom: 20px;
        }

        .error-distribution h4, .error-rates h4, .throughput-chart h4 {
          margin: 0 0 15px 0;
          color: #374151;
        }

        .error-type {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 10px 0;
          border-bottom: 1px solid #f3f4f6;
        }

        .error-info {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .error-name {
          font-weight: 500;
          color: #374151;
        }

        .error-percentage {
          color: #ef4444;
          font-weight: bold;
        }

        .error-count {
          color: #6b7280;
          font-size: 14px;
        }

        .error-chart {
          display: flex;
          align-items: end;
          gap: 2px;
          height: 100px;
        }

        .rate-bar {
          flex: 1;
          height: 100%;
          background: #f3f4f6;
          display: flex;
          align-items: end;
        }

        .rate-fill {
          width: 100%;
          background: #ef4444;
          min-height: 2px;
        }

        .chart-container {
          display: flex;
          align-items: end;
          gap: 4px;
          height: 150px;
          overflow-x: auto;
        }

        .throughput-bar {
          display: flex;
          flex-direction: column;
          align-items: center;
          min-width: 60px;
        }

        .bar-stack {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1px;
        }

        .bar-segment {
          width: 20px;
          min-height: 2px;
        }

        .bar-segment.ingested { background: #3b82f6; }
        .bar-segment.validated { background: #10b981; }
        .bar-segment.promoted { background: #f59e0b; }
        .bar-segment.synced { background: #8b5cf6; }

        .bar-label {
          font-size: 10px;
          color: #6b7280;
          margin-top: 5px;
          transform: rotate(-45deg);
          white-space: nowrap;
        }

        .timeline-filters {
          margin-bottom: 15px;
        }

        .timeline-limit-select {
          padding: 6px 10px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          background: white;
        }

        .timeline-events {
          max-height: 400px;
          overflow-y: auto;
        }

        .timeline-event {
          display: flex;
          align-items: flex-start;
          gap: 15px;
          padding: 10px 0;
          border-bottom: 1px solid #f3f4f6;
        }

        .event-time {
          font-size: 12px;
          color: #6b7280;
          min-width: 80px;
        }

        .event-indicator {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          margin-top: 6px;
        }

        .event-content {
          flex: 1;
        }

        .event-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 5px;
        }

        .event-action {
          font-weight: 500;
          color: #374151;
        }

        .event-severity {
          font-size: 12px;
          padding: 2px 6px;
          border-radius: 3px;
          text-transform: uppercase;
          font-weight: bold;
        }

        .severity-error {
          background: #fef2f2;
          color: #dc2626;
        }

        .severity-warning {
          background: #fffbeb;
          color: #d97706;
        }

        .severity-success {
          background: #f0fdf4;
          color: #16a34a;
        }

        .severity-info {
          background: #eff6ff;
          color: #2563eb;
        }

        .event-description {
          color: #4b5563;
          font-size: 14px;
          margin-bottom: 5px;
        }

        .event-details {
          font-size: 12px;
          color: #6b7280;
        }
      `}</style>
    </div>
  );
};

export default MonitoringDashboard;