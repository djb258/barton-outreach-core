import React, { useState, useEffect } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const ProcessingStatusPanel = ({ 
  isProcessing, 
  processingResults, 
  onExportErrors,
  onPromoteRecords 
}) => {
  const [expandedSection, setExpandedSection] = useState('summary');

  const mockProcessingResults = {
    totalRows: 2847,
    successfulRows: 2731,
    failedRows: 116,
    validationErrors: [
      {
        row: 23,
        column: 'email',
        value: 'invalid-email',
        error: 'Invalid email format',
        severity: 'error'
      },
      {
        row: 45,
        column: 'phone',
        value: '123',
        error: 'Phone number too short',
        severity: 'warning'
      },
      {
        row: 67,
        column: 'company_name',
        value: '',
        error: 'Required field is empty',
        severity: 'error'
      },
      {
        row: 89,
        column: 'website',
        value: 'not-a-url',
        error: 'Invalid URL format',
        severity: 'warning'
      },
      {
        row: 112,
        column: 'email',
        value: 'duplicate@company.com',
        error: 'Duplicate email address',
        severity: 'error'
      }
    ],
    processingTime: '2.3s',
    uniqueId: 'WF-2025-001-BATCH-001',
    timestamp: new Date()?.toISOString()
  };

  const results = processingResults || mockProcessingResults;
  const successRate = ((results?.successfulRows / results?.totalRows) * 100)?.toFixed(1);

  const getErrorSeverityColor = (severity) => {
    switch (severity) {
      case 'error': return 'text-error bg-error/10 border-error/20';
      case 'warning': return 'text-warning bg-warning/10 border-warning/20';
      default: return 'text-muted-foreground bg-muted border-border';
    }
  };

  const getErrorSeverityIcon = (severity) => {
    switch (severity) {
      case 'error': return 'XCircle';
      case 'warning': return 'AlertTriangle';
      default: return 'Info';
    }
  };

  if (!isProcessing && !processingResults) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 text-center">
        <Icon name="Activity" size={48} color="var(--color-muted-foreground)" />
        <h3 className="text-lg font-semibold text-foreground mt-4 mb-2">Ready to Process</h3>
        <p className="text-sm text-muted-foreground">
          Upload a file and configure column mapping to begin processing
        </p>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-border bg-muted/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`
              flex items-center justify-center w-10 h-10 rounded-full
              ${isProcessing ? 'bg-accent text-accent-foreground' : 'bg-success text-success-foreground'}
            `}>
              {isProcessing ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Icon name="CheckCircle" size={20} />
              )}
            </div>
            <div>
              <h3 className="text-sm font-semibold text-foreground">
                {isProcessing ? 'Processing Data...' : 'Processing Complete'}
              </h3>
              <p className="text-xs text-muted-foreground">
                {isProcessing ? 'Validating and ingesting records' : `Completed in ${results?.processingTime}`}
              </p>
            </div>
          </div>
          
          {!isProcessing && (
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                iconName="Download"
                iconPosition="left"
                onClick={onExportErrors}
                disabled={results?.failedRows === 0}
              >
                Export Errors
              </Button>
              <Button
                variant="default"
                size="sm"
                iconName="ArrowUp"
                iconPosition="left"
                onClick={onPromoteRecords}
                disabled={results?.successfulRows === 0}
              >
                Promote Valid Records
              </Button>
            </div>
          )}
        </div>
      </div>
      {/* Processing Progress */}
      {isProcessing && (
        <div className="p-4 border-b border-border">
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-foreground">Processing rows...</span>
              <span className="text-muted-foreground font-data">1,247 / 2,847</span>
            </div>
            <div className="w-full bg-muted rounded-full h-2">
              <div className="bg-accent h-2 rounded-full transition-all duration-300" style={{ width: '44%' }} />
            </div>
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Validation in progress</span>
              <span>ETA: 1m 23s</span>
            </div>
          </div>
        </div>
      )}
      {/* Results Summary */}
      {!isProcessing && (
        <div className="p-4">
          <div className="grid grid-cols-3 gap-4 mb-6">
            {/* Total Records */}
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold text-foreground">{results?.totalRows?.toLocaleString()}</div>
              <div className="text-xs text-muted-foreground">Total Records</div>
            </div>
            
            {/* Successful Records */}
            <div className="text-center p-3 bg-success/10 rounded-lg">
              <div className="text-2xl font-bold text-success">{results?.successfulRows?.toLocaleString()}</div>
              <div className="text-xs text-muted-foreground">Valid Records</div>
            </div>
            
            {/* Failed Records */}
            <div className="text-center p-3 bg-error/10 rounded-lg">
              <div className="text-2xl font-bold text-error">{results?.failedRows?.toLocaleString()}</div>
              <div className="text-xs text-muted-foreground">Failed Records</div>
            </div>
          </div>

          {/* Success Rate */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-foreground">Success Rate</span>
              <span className="text-sm font-bold text-success">{successRate}%</span>
            </div>
            <div className="w-full bg-muted rounded-full h-3">
              <div 
                className="bg-success h-3 rounded-full transition-all duration-500"
                style={{ width: `${successRate}%` }}
              />
            </div>
          </div>

          {/* Validation Errors */}
          {results?.validationErrors && results?.validationErrors?.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-foreground">Validation Errors</h4>
                <Button
                  variant="ghost"
                  size="sm"
                  iconName={expandedSection === 'errors' ? 'ChevronUp' : 'ChevronDown'}
                  iconPosition="right"
                  onClick={() => setExpandedSection(expandedSection === 'errors' ? '' : 'errors')}
                >
                  {results?.validationErrors?.length} errors
                </Button>
              </div>

              {expandedSection === 'errors' && (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {results?.validationErrors?.slice(0, 10)?.map((error, index) => (
                    <div
                      key={index}
                      className={`
                        flex items-start space-x-3 p-3 rounded-lg border text-sm
                        ${getErrorSeverityColor(error?.severity)}
                      `}
                    >
                      <Icon name={getErrorSeverityIcon(error?.severity)} size={16} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="font-medium">Row {error?.row}</span>
                          <span className="text-xs bg-muted px-1.5 py-0.5 rounded font-data">
                            {error?.column}
                          </span>
                        </div>
                        <div className="text-xs opacity-90 mb-1">{error?.error}</div>
                        {error?.value && (
                          <div className="text-xs font-data bg-muted/50 px-2 py-1 rounded truncate">
                            "{error?.value}"
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  
                  {results?.validationErrors?.length > 10 && (
                    <div className="text-center py-2">
                      <Button variant="ghost" size="sm">
                        Show {results?.validationErrors?.length - 10} more errors
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Processing Metadata */}
          <div className="mt-6 pt-4 border-t border-border">
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-muted-foreground">Batch ID:</span>
                <span className="ml-2 font-data text-foreground">{results?.uniqueId}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Processing Time:</span>
                <span className="ml-2 font-data text-foreground">{results?.processingTime}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Timestamp:</span>
                <span className="ml-2 font-data text-foreground">
                  {new Date(results.timestamp)?.toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Status:</span>
                <span className="ml-2 font-medium text-success">Completed</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProcessingStatusPanel;