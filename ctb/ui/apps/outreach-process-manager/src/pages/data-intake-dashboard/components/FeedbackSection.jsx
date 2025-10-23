import React, { useState, useEffect } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const FeedbackSection = ({
  processingResults,
  validationErrors,
  onGenerateReport,
  onViewReports
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [feedbackData, setFeedbackData] = useState(null);
  const [showFeedbackPanel, setShowFeedbackPanel] = useState(false);

  // Auto-show feedback panel when there are errors
  useEffect(() => {
    if (processingResults?.failedRows > 0 || validationErrors?.length > 0) {
      setShowFeedbackPanel(true);
    }
  }, [processingResults, validationErrors]);

  const handleGenerateFeedbackReport = async () => {
    setIsGenerating(true);

    try {
      // Simulate API call to generate feedback report
      const response = await fetch('/api/feedback-reports', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          action: 'generate',
          timeframe_days: 1,
          report_type: 'validation_errors',
          analysis_depth: 'detailed',
          filters: {
            source_system: 'data_intake_dashboard'
          }
        })
      });

      const result = await response.json();

      if (result.success) {
        setFeedbackData(result.data);
        if (onGenerateReport) onGenerateReport(result.data);
      }
    } catch (error) {
      console.error('Failed to generate feedback report:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const getErrorSummary = () => {
    if (!processingResults && !validationErrors?.length) return null;

    const totalErrors = (processingResults?.failedRows || 0) + (validationErrors?.length || 0);
    const errorTypes = new Set();

    validationErrors?.forEach(error => {
      errorTypes.add(error.type || 'validation_error');
    });

    return {
      totalErrors,
      errorTypes: Array.from(errorTypes),
      hasValidationErrors: validationErrors?.length > 0,
      hasProcessingErrors: processingResults?.failedRows > 0
    };
  };

  const errorSummary = getErrorSummary();

  if (!errorSummary?.totalErrors && !showFeedbackPanel) {
    return null;
  }

  return (
    <div className="bg-card border border-border rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center space-x-3">
          <Icon name="AlertTriangle" size={20} className="text-yellow-600" />
          <div>
            <h3 className="text-lg font-semibold text-foreground">Data Quality Feedback</h3>
            <p className="text-sm text-muted-foreground">
              Step 8: Continuous improvement analysis
            </p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setShowFeedbackPanel(!showFeedbackPanel)}
        >
          <Icon name={showFeedbackPanel ? "ChevronUp" : "ChevronDown"} size={16} />
        </Button>
      </div>

      {showFeedbackPanel && (
        <div className="p-4 space-y-4">
          {/* Error Summary */}
          {errorSummary?.totalErrors > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <Icon name="Info" size={20} className="text-yellow-600 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-medium text-yellow-900">
                    Quality Issues Detected ({errorSummary.totalErrors})
                  </h4>
                  <p className="text-sm text-yellow-800 mt-1">
                    The system identified {errorSummary.totalErrors} data quality issues that can help improve future uploads.
                  </p>

                  {/* Error Type Breakdown */}
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    {errorSummary.hasValidationErrors && (
                      <div className="flex items-center space-x-2 text-sm">
                        <Icon name="XCircle" size={14} className="text-red-500" />
                        <span className="text-gray-700">
                          {validationErrors?.length} validation errors
                        </span>
                      </div>
                    )}
                    {errorSummary.hasProcessingErrors && (
                      <div className="flex items-center space-x-2 text-sm">
                        <Icon name="AlertCircle" size={14} className="text-orange-500" />
                        <span className="text-gray-700">
                          {processingResults?.failedRows} processing failures
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Feedback Actions */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                iconName="BarChart"
                iconPosition="left"
                loading={isGenerating}
                onClick={handleGenerateFeedbackReport}
              >
                {isGenerating ? 'Analyzing Patterns...' : 'Generate Feedback Report'}
              </Button>

              <Button
                variant="ghost"
                iconName="FileText"
                iconPosition="left"
                onClick={onViewReports}
              >
                View Past Reports
              </Button>
            </div>

            <div className="text-xs text-muted-foreground">
              Automated error pattern analysis • Barton Doctrine Step 8
            </div>
          </div>

          {/* Feedback Report Preview */}
          {feedbackData && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
              <div className="flex items-start space-x-3">
                <Icon name="CheckCircle" size={20} className="text-blue-600 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-medium text-blue-900">
                    Feedback Report Generated
                  </h4>
                  <p className="text-sm text-blue-800 mt-1">
                    Report ID: {feedbackData.report_id}
                  </p>

                  {/* Key Insights */}
                  {feedbackData.summary && (
                    <div className="mt-3">
                      <h5 className="text-sm font-medium text-blue-900 mb-2">Key Insights:</h5>
                      <ul className="text-sm text-blue-800 space-y-1">
                        <li>• {feedbackData.summary.total_errors || 0} errors analyzed</li>
                        <li>• {feedbackData.error_patterns?.length || 0} patterns identified</li>
                        <li>• {feedbackData.recommendations?.length || 0} improvement recommendations</li>
                      </ul>
                    </div>
                  )}

                  {/* Quick Actions */}
                  <div className="mt-3 flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      iconName="Eye"
                      iconPosition="left"
                      onClick={() => window.open(`/feedback-reports/${feedbackData.report_id}`, '_blank')}
                    >
                      View Full Report
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      iconName="Download"
                      iconPosition="left"
                      onClick={() => {
                        // Export report as CSV
                        const csvContent = [
                          'Pattern,Frequency,Recommendation,Priority',
                          ...(feedbackData.error_patterns || []).map(pattern =>
                            `"${pattern.pattern}",${pattern.frequency},"${pattern.recommendation}",${pattern.priority}`
                          )
                        ].join('\n');

                        const blob = new Blob([csvContent], { type: 'text/csv' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `feedback-report-${feedbackData.report_id}.csv`;
                        a.click();
                        URL.revokeObjectURL(url);
                      }}
                    >
                      Export CSV
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Educational Content */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <Icon name="Lightbulb" size={20} className="text-gray-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-gray-900">How Feedback Analysis Works</h4>
                <p className="text-sm text-gray-700 mt-1">
                  Our system automatically analyzes validation errors and processing failures to identify recurring patterns.
                  This helps improve data quality guidelines and prevent similar issues in future uploads.
                </p>
                <ul className="text-sm text-gray-600 mt-2 space-y-1">
                  <li>• Pattern recognition across error types and sources</li>
                  <li>• Automated recommendations for data preparation</li>
                  <li>• Historical trend analysis for continuous improvement</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FeedbackSection;