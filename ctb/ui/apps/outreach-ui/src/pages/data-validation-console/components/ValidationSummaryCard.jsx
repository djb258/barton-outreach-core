import React from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const ValidationSummaryCard = ({ 
  totalRecords = 2156,
  passedRecords = 1847,
  warningRecords = 234,
  failedRecords = 75,
  onPromoteRecords,
  onExportResults,
  className = ''
}) => {
  const passRate = Math.round((passedRecords / totalRecords) * 100);
  const warningRate = Math.round((warningRecords / totalRecords) * 100);
  const failureRate = Math.round((failedRecords / totalRecords) * 100);

  const summaryStats = [
    {
      label: 'Total Records',
      value: totalRecords?.toLocaleString(),
      icon: 'Database',
      color: 'text-foreground bg-muted/20'
    },
    {
      label: 'Passed',
      value: passedRecords?.toLocaleString(),
      percentage: passRate,
      icon: 'CheckCircle',
      color: 'text-success bg-success/10'
    },
    {
      label: 'Warnings',
      value: warningRecords?.toLocaleString(),
      percentage: warningRate,
      icon: 'AlertTriangle',
      color: 'text-warning bg-warning/10'
    },
    {
      label: 'Failed',
      value: failedRecords?.toLocaleString(),
      percentage: failureRate,
      icon: 'XCircle',
      color: 'text-error bg-error/10'
    }
  ];

  const validationMetrics = [
    {
      label: 'Data Quality Score',
      value: '87%',
      trend: '+2.3%',
      trendDirection: 'up',
      description: 'Overall data quality improvement'
    },
    {
      label: 'Compliance Rate',
      value: '94%',
      trend: '+1.1%',
      trendDirection: 'up',
      description: 'GDPR and regulatory compliance'
    },
    {
      label: 'Processing Time',
      value: '2.4s',
      trend: '-0.8s',
      trendDirection: 'down',
      description: 'Average validation time per record'
    },
    {
      label: 'Auto-Corrections',
      value: '156',
      trend: '+23',
      trendDirection: 'up',
      description: 'Records automatically corrected'
    }
  ];

  const getTrendColor = (direction) => {
    return direction === 'up' ? 'text-success' : 'text-error';
  };

  const getTrendIcon = (direction) => {
    return direction === 'up' ? 'TrendingUp' : 'TrendingDown';
  };

  return (
    <div className={`bg-card border border-border rounded-lg ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Icon name="BarChart3" size={20} color="var(--color-accent)" />
            <div>
              <h3 className="text-lg font-semibold text-foreground">Validation Summary</h3>
              <p className="text-sm text-muted-foreground">Real-time validation status and metrics</p>
            </div>
          </div>
          <div className="flex space-x-2">
            <Button variant="outline" size="sm" iconName="Download" onClick={onExportResults}>
              Export
            </Button>
            <Button variant="default" size="sm" iconName="ArrowRight" onClick={onPromoteRecords}>
              Promote Valid Records
            </Button>
          </div>
        </div>
      </div>
      {/* Summary Statistics */}
      <div className="p-4">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {summaryStats?.map((stat, index) => (
            <div key={index} className="text-center">
              <div className={`
                inline-flex items-center justify-center w-12 h-12 rounded-lg mb-2
                ${stat?.color}
              `}>
                <Icon name={stat?.icon} size={20} />
              </div>
              <div className="text-2xl font-bold text-foreground">{stat?.value}</div>
              <div className="text-sm text-muted-foreground">{stat?.label}</div>
              {stat?.percentage !== undefined && (
                <div className="text-xs text-muted-foreground mt-1">
                  {stat?.percentage}% of total
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-foreground">Validation Progress</span>
            <span className="text-sm text-muted-foreground">{passRate}% passed</span>
          </div>
          <div className="w-full bg-muted rounded-full h-3 overflow-hidden">
            <div className="h-full flex">
              <div 
                className="bg-success transition-all duration-500"
                style={{ width: `${passRate}%` }}
              />
              <div 
                className="bg-warning transition-all duration-500"
                style={{ width: `${warningRate}%` }}
              />
              <div 
                className="bg-error transition-all duration-500"
                style={{ width: `${failureRate}%` }}
              />
            </div>
          </div>
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>Passed: {passRate}%</span>
            <span>Warnings: {warningRate}%</span>
            <span>Failed: {failureRate}%</span>
          </div>
        </div>

        {/* Validation Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {validationMetrics?.map((metric, index) => (
            <div key={index} className="p-3 bg-muted/20 rounded-lg border border-border">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-foreground">{metric?.label}</span>
                <div className="flex items-center space-x-1">
                  <span className="text-lg font-bold text-foreground">{metric?.value}</span>
                  <div className={`flex items-center space-x-1 ${getTrendColor(metric?.trendDirection)}`}>
                    <Icon name={getTrendIcon(metric?.trendDirection)} size={12} />
                    <span className="text-xs font-medium">{metric?.trend}</span>
                  </div>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">{metric?.description}</p>
            </div>
          ))}
        </div>
      </div>
      {/* Action Items */}
      <div className="p-4 border-t border-border bg-muted/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Icon name="AlertCircle" size={16} color="var(--color-warning)" />
            <span className="text-sm font-medium text-foreground">
              {failedRecords + warningRecords} records require attention
            </span>
          </div>
          <div className="flex space-x-2">
            <Button variant="outline" size="sm" iconName="Eye">
              Review Issues
            </Button>
            <Button variant="outline" size="sm" iconName="Settings">
              Adjust Rules
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ValidationSummaryCard;