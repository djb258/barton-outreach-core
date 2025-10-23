import React, { useState, useEffect } from 'react';
import Icon from '../../components/AppIcon';
import Button from '../../components/ui/Button';
import { Card, CardHeader, CardContent } from '../../components/ui/Card';

const FeedbackReport = ({
  report = null,
  isLoading = false,
  onGenerateReport,
  onRefresh,
  className = ''
}) => {
  const [selectedTimeframe, setSelectedTimeframe] = useState('7_days');
  const [reportType, setReportType] = useState('weekly');
  const [analysisDepth, setAnalysisDepth] = useState('standard');
  const [isGenerating, setIsGenerating] = useState(false);

  const timeframeOptions = [
    { value: '1_day', label: 'Last 24 Hours', days: 1 },
    { value: '7_days', label: 'Last 7 Days', days: 7 },
    { value: '30_days', label: 'Last 30 Days', days: 30 },
    { value: '90_days', label: 'Last 90 Days', days: 90 }
  ];

  const reportTypeOptions = [
    { value: 'daily', label: 'Daily Report' },
    { value: 'weekly', label: 'Weekly Report' },
    { value: 'monthly', label: 'Monthly Report' },
    { value: 'ad_hoc', label: 'Ad-Hoc Analysis' }
  ];

  const analysisDepthOptions = [
    { value: 'basic', label: 'Basic Analysis', description: 'Quick overview of main error patterns' },
    { value: 'standard', label: 'Standard Analysis', description: 'Comprehensive error analysis with trends' },
    { value: 'deep', label: 'Deep Analysis', description: 'Detailed analysis with correlations and predictions' }
  ];

  const handleGenerateReport = async () => {
    setIsGenerating(true);

    const selectedTimeframeData = timeframeOptions.find(opt => opt.value === selectedTimeframe);
    const endDate = new Date();
    const startDate = new Date(endDate.getTime() - (selectedTimeframeData.days * 24 * 60 * 60 * 1000));

    const options = {
      startDate,
      endDate,
      reportType,
      analysisDepth,
      reportName: `${reportType.charAt(0).toUpperCase() + reportType.slice(1)} Report - ${selectedTimeframeData.label}`
    };

    try {
      await onGenerateReport(options);
    } finally {
      setIsGenerating(false);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'generated': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'reviewed': return 'text-purple-600 bg-purple-50 border-purple-200';
      case 'acted_upon': return 'text-green-600 bg-green-50 border-green-200';
      case 'archived': return 'text-gray-600 bg-gray-50 border-gray-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (isLoading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <Card>
          <CardContent className="p-8 text-center">
            <Icon name="Loader2" size={32} className="animate-spin mx-auto mb-4 text-gray-400" />
            <p className="text-sm text-gray-600">Loading feedback report...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Report Generation Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Generate Feedback Report</h3>
              <p className="text-sm text-gray-600 mt-1">
                Analyze error patterns and generate improvement recommendations
              </p>
            </div>
            <div className="flex space-x-2">
              {report && (
                <Button
                  variant="outline"
                  size="sm"
                  iconName="RefreshCw"
                  onClick={onRefresh}
                  disabled={isGenerating}
                >
                  Refresh
                </Button>
              )}
              <Button
                variant="default"
                size="sm"
                iconName="FileText"
                onClick={handleGenerateReport}
                disabled={isGenerating}
              >
                {isGenerating ? 'Generating...' : 'Generate Report'}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Timeframe Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Analysis Timeframe
              </label>
              <select
                value={selectedTimeframe}
                onChange={(e) => setSelectedTimeframe(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isGenerating}
              >
                {timeframeOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Report Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Report Type
              </label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isGenerating}
              >
                {reportTypeOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Analysis Depth */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Analysis Depth
              </label>
              <select
                value={analysisDepth}
                onChange={(e) => setAnalysisDepth(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isGenerating}
              >
                {analysisDepthOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                {analysisDepthOptions.find(opt => opt.value === analysisDepth)?.description}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Report Display */}
      {report && (
        <>
          {/* Report Header */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <h2 className="text-xl font-semibold text-gray-900">{report.report_name}</h2>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getPriorityColor(report.priority_level)}`}>
                      {report.priority_level?.toUpperCase()}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(report.status)}`}>
                      {report.status?.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  <div className="mt-2 space-y-1 text-sm text-gray-600">
                    <p>Report ID: <span className="font-mono">{report.report_id}</span></p>
                    <p>Period: {formatDate(report.report_period_start)} - {formatDate(report.report_period_end)}</p>
                    <p>Generated by: {report.generated_by} • {formatDate(report.created_at)}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {report.tags && report.tags.map(tag => (
                    <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                      {tag.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Executive Summary */}
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <Icon name="FileText" size={20} className="mr-2" />
                Executive Summary
              </h3>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 leading-relaxed">{report.executive_summary}</p>
            </CardContent>
          </Card>

          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <Icon name="AlertTriangle" size={24} className="text-red-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Errors</p>
                    <p className="text-2xl font-bold text-gray-900">{formatNumber(report.total_errors_found)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Icon name="BarChart3" size={24} className="text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Error Categories</p>
                    <p className="text-2xl font-bold text-gray-900">{report.error_categories_count}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Icon name="Target" size={24} className="text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Quick Wins</p>
                    <p className="text-2xl font-bold text-gray-900">{report.quick_wins?.length || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Icon name="TrendingUp" size={24} className="text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Strategic Items</p>
                    <p className="text-2xl font-bold text-gray-900">{report.long_term_improvements?.length || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recommendations */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Quick Wins */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <Icon name="Zap" size={20} className="mr-2 text-yellow-500" />
                  Quick Wins
                </h3>
                <p className="text-sm text-gray-600">Immediate improvements that can be implemented quickly</p>
              </CardHeader>
              <CardContent>
                {report.quick_wins && report.quick_wins.length > 0 ? (
                  <ul className="space-y-3">
                    {report.quick_wins.map((item, index) => (
                      <li key={index} className="flex items-start space-x-3">
                        <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-green-600 text-xs font-bold">{index + 1}</span>
                        </div>
                        <span className="text-sm text-gray-700">{item}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500 italic">No quick wins identified in this analysis.</p>
                )}
              </CardContent>
            </Card>

            {/* Strategic Improvements */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <Icon name="Target" size={20} className="mr-2 text-blue-500" />
                  Strategic Improvements
                </h3>
                <p className="text-sm text-gray-600">Long-term improvements requiring planning and resources</p>
              </CardHeader>
              <CardContent>
                {report.long_term_improvements && report.long_term_improvements.length > 0 ? (
                  <ul className="space-y-3">
                    {report.long_term_improvements.map((item, index) => (
                      <li key={index} className="flex items-start space-x-3">
                        <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-blue-600 text-xs font-bold">{index + 1}</span>
                        </div>
                        <span className="text-sm text-gray-700">{item}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500 italic">No strategic improvements identified in this analysis.</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Error Patterns Analysis */}
          {report.error_patterns && (
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <Icon name="Search" size={20} className="mr-2" />
                  Error Pattern Analysis
                </h3>
                <p className="text-sm text-gray-600">
                  Detailed breakdown of error patterns identified during analysis
                </p>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Validation Failures */}
                  {report.error_patterns.validation_failures && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-3">Validation Failures</h4>
                      <div className="space-y-2">
                        <div className="text-sm">
                          <span className="text-gray-600">Total Count:</span>
                          <span className="ml-2 font-semibold">{formatNumber(report.error_patterns.validation_failures.total_count)}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-600">Resolution Rate:</span>
                          <span className="ml-2 font-semibold">
                            {(report.error_patterns.validation_failures.resolution_rate * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-600">Error Types:</span>
                          <span className="ml-2 font-semibold">{report.error_patterns.validation_failures.unique_error_types?.length || 0}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Audit Log Errors */}
                  {report.error_patterns.audit_log_errors && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-3">System Errors</h4>
                      <div className="space-y-2">
                        <div className="text-sm">
                          <span className="text-gray-600">Total Count:</span>
                          <span className="ml-2 font-semibold">{formatNumber(report.error_patterns.audit_log_errors.total_count)}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-600">Performance Issues:</span>
                          <span className="ml-2 font-semibold">{report.error_patterns.audit_log_errors.performance_issues?.length || 0}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-600">Retry Patterns:</span>
                          <span className="ml-2 font-semibold">{Object.keys(report.error_patterns.audit_log_errors.retry_patterns || {}).length}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Enrichment Failures */}
                  {report.error_patterns.enrichment_failures && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-3">Enrichment Issues</h4>
                      <div className="space-y-2">
                        <div className="text-sm">
                          <span className="text-gray-600">Total Count:</span>
                          <span className="ml-2 font-semibold">{formatNumber(report.error_patterns.enrichment_failures.total_count)}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-600">Low Confidence:</span>
                          <span className="ml-2 font-semibold">{report.error_patterns.enrichment_failures.low_confidence_sources?.length || 0}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-600">Slow Sources:</span>
                          <span className="ml-2 font-semibold">{report.error_patterns.enrichment_failures.slow_sources?.length || 0}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Detailed Findings */}
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <Icon name="FileSearch" size={20} className="mr-2" />
                Detailed Findings
              </h3>
            </CardHeader>
            <CardContent>
              <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono bg-gray-50 p-4 rounded-lg overflow-x-auto">
                {report.detailed_findings}
              </pre>
            </CardContent>
          </Card>

          {/* Follow-up Actions */}
          {report.follow_up_required && (
            <Card className="border-orange-200 bg-orange-50">
              <CardHeader>
                <h3 className="text-lg font-semibold text-orange-900 flex items-center">
                  <Icon name="Clock" size={20} className="mr-2" />
                  Follow-up Required
                </h3>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-orange-800">
                      This report requires follow-up action due to its {report.priority_level} priority level.
                    </p>
                    <p className="text-sm text-orange-600 mt-1">
                      Due date: {formatDate(report.follow_up_by)}
                    </p>
                  </div>
                  <Button variant="outline" size="sm" className="border-orange-300 text-orange-700 hover:bg-orange-100">
                    Create Action Plan
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* No Report State */}
      {!report && !isLoading && (
        <Card>
          <CardContent className="p-8 text-center">
            <Icon name="FileText" size={48} className="mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Report Generated</h3>
            <p className="text-sm text-gray-600 mb-4">
              Generate a feedback report to analyze error patterns and get improvement recommendations.
            </p>
            <Button
              variant="default"
              iconName="FileText"
              onClick={handleGenerateReport}
              disabled={isGenerating}
            >
              Generate Your First Report
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default FeedbackReport;