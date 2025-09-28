import React from 'react';
import Select from '../../../components/ui/Select';
import Icon from '../../../components/AppIcon';

const AdjusterFilterToolbar = ({
  currentFilter = 'all',
  onFilterChange,
  currentErrorType = 'all',
  onErrorTypeChange,
  totalCount = 0,
  promotedCount = 0,
  pendingCount = 0,
  adjustedCount = 0,
  errorTypeCounts = {},
  recordType = 'company',
  className = ''
}) => {
  const filterOptions = [
    {
      value: 'all',
      label: `All (${totalCount})`,
      icon: 'List',
      count: totalCount
    },
    {
      value: 'promoted',
      label: `Promoted (${promotedCount})`,
      icon: 'CheckCircle',
      count: promotedCount
    },
    {
      value: 'pending',
      label: `Pending (${pendingCount})`,
      icon: 'Clock',
      count: pendingCount
    },
    {
      value: 'adjusted',
      label: `Adjusted (${adjustedCount})`,
      icon: 'Edit',
      count: adjustedCount
    }
  ];

  // Common error types based on the schema
  const commonErrorTypes = [
    { value: 'all', label: 'All Error Types' },
    { value: 'missing_state', label: 'Missing State' },
    { value: 'invalid_state', label: 'Invalid State' },
    { value: 'bad_phone_format', label: 'Bad Phone Format' },
    { value: 'invalid_phone', label: 'Invalid Phone' },
    { value: 'invalid_url', label: 'Invalid URL' },
    { value: 'missing_protocol', label: 'Missing Protocol' },
    { value: 'bad_url_format', label: 'Bad URL Format' },
    { value: 'missing_linkedin', label: 'Missing LinkedIn' },
    { value: 'invalid_linkedin', label: 'Invalid LinkedIn' },
    { value: 'missing_website', label: 'Missing Website' },
    { value: 'website_not_found', label: 'Website Not Found' },
    { value: 'missing_ein', label: 'Missing EIN' },
    { value: 'missing_permit', label: 'Missing Permit' },
    { value: 'missing_revenue', label: 'Missing Revenue' },
    { value: 'complex_validation_failure', label: 'Complex Validation' },
    { value: 'multiple_field_failure', label: 'Multiple Field Issues' },
    { value: 'data_inconsistency', label: 'Data Inconsistency' }
  ];

  // Add count information to error type options
  const errorTypeOptions = commonErrorTypes.map(option => ({
    ...option,
    label: option.value === 'all'
      ? option.label
      : `${option.label} (${errorTypeCounts[option.value] || 0})`
  }));

  const getFilterStats = () => {
    switch (currentFilter) {
      case 'promoted':
        return { count: promotedCount, status: 'Promoted ✅' };
      case 'pending':
        return { count: pendingCount, status: 'Pending ⏳' };
      case 'adjusted':
        return { count: adjustedCount, status: 'Adjusted ⚠️' };
      default:
        return { count: totalCount, status: 'All Records' };
    }
  };

  const stats = getFilterStats();

  return (
    <div className={`bg-card border border-border rounded-lg p-4 space-y-3 ${className}`}>
      {/* Filter Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Icon name="Filter" size={16} color="var(--color-muted-foreground)" />
            <span className="text-sm font-medium text-foreground">Filter Results:</span>
          </div>

          <Select
            value={currentFilter}
            onValueChange={onFilterChange}
            options={filterOptions}
            placeholder="Select filter"
            className="w-48"
          />

          <Select
            value={currentErrorType}
            onValueChange={onErrorTypeChange}
            options={errorTypeOptions}
            placeholder="Select error type"
            className="w-64"
          />
        </div>

        <div className="flex items-center space-x-6">
          {/* Current Filter Stats */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">Showing:</span>
            <span className="text-sm font-medium text-foreground">
              {stats?.count} {stats?.status}
            </span>
            {currentErrorType !== 'all' && (
              <span className="text-xs text-muted-foreground">
                • {currentErrorType.replace(/_/g, ' ')}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="flex items-center justify-between border-t border-border pt-3">
        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-success rounded-full"></div>
            <span className="text-muted-foreground">Promoted: {promotedCount}</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-warning rounded-full"></div>
            <span className="text-muted-foreground">Pending: {pendingCount}</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-info rounded-full"></div>
            <span className="text-muted-foreground">Adjusted: {adjustedCount}</span>
          </div>
        </div>

        <div className="text-xs text-muted-foreground">
          Record Type: <span className="font-medium text-foreground capitalize">{recordType}</span>
        </div>
      </div>
    </div>
  );
};

export default AdjusterFilterToolbar;