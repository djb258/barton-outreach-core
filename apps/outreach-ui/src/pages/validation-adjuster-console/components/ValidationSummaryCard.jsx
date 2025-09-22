import React from 'react';
import Icon from '../../../components/AppIcon';

const ValidationSummaryCard = ({ 
  rowsValidated = 0,
  rowsFailed = 0,
  isLoading = false,
  className = ''
}) => {
  const totalRows = rowsValidated + rowsFailed;
  const validationRate = totalRows > 0 ? Math.round((rowsValidated / totalRows) * 100) : 0;

  return (
    <div className={`bg-card border border-border rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Icon name="CheckCircle" size={24} color="var(--color-success)" />
          <h2 className="text-xl font-semibold text-foreground">Validation Summary</h2>
        </div>
        
        {isLoading && (
          <div className="flex items-center space-x-2 text-muted-foreground">
            <Icon name="Loader2" size={16} className="animate-spin" />
            <span className="text-sm">Loading...</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Total Records */}
        <div className="text-center">
          <div className="text-3xl font-bold text-foreground mb-1">
            {totalRows?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Total Records</div>
        </div>

        {/* Validated Records */}
        <div className="text-center">
          <div className="text-3xl font-bold text-success mb-1">
            {rowsValidated?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Rows Validated</div>
          <div className="text-xs text-success mt-1">
            {validationRate}% success rate
          </div>
        </div>

        {/* Failed Records */}
        <div className="text-center">
          <div className="text-3xl font-bold text-error mb-1">
            {rowsFailed?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Rows Failed</div>
          <div className="text-xs text-error mt-1">
            {totalRows > 0 ? Math.round((rowsFailed / totalRows) * 100) : 0}% failure rate
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      {totalRows > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-foreground">Validation Progress</span>
            <span className="text-sm text-muted-foreground">{validationRate}% complete</span>
          </div>
          <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
            <div className="h-full flex">
              <div 
                className="bg-success transition-all duration-500"
                style={{ width: `${validationRate}%` }}
              />
              <div 
                className="bg-error transition-all duration-500"
                style={{ width: `${100 - validationRate}%` }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ValidationSummaryCard;