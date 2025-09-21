import React from 'react';
import Icon from '../../../components/AppIcon';

const AdjusterSummaryCard = ({ 
  rowsPromoted = 0,
  rowsPending = 0,
  rowsAdjusted = 0,
  isLoading = false,
  className = ''
}) => {
  const totalRows = rowsPromoted + rowsPending;
  const promotionRate = totalRows > 0 ? Math.round((rowsPromoted / totalRows) * 100) : 0;
  const adjustmentRate = totalRows > 0 ? Math.round((rowsAdjusted / totalRows) * 100) : 0;

  return (
    <div className={`bg-card border border-border rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Icon name="Settings" size={24} color="var(--color-primary)" />
          <h2 className="text-xl font-semibold text-foreground">Adjustment Summary</h2>
        </div>
        
        {isLoading && (
          <div className="flex items-center space-x-2 text-muted-foreground">
            <Icon name="Loader2" size={16} className="animate-spin" />
            <span className="text-sm">Loading...</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-4 gap-6">
        {/* Total Records */}
        <div className="text-center">
          <div className="text-3xl font-bold text-foreground mb-1">
            {totalRows?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Total Records</div>
        </div>

        {/* Promoted Records */}
        <div className="text-center">
          <div className="text-3xl font-bold text-success mb-1">
            {rowsPromoted?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Promoted</div>
          <div className="text-xs text-success mt-1">
            {promotionRate}% promoted
          </div>
        </div>

        {/* Pending Records */}
        <div className="text-center">
          <div className="text-3xl font-bold text-warning mb-1">
            {rowsPending?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Pending</div>
          <div className="text-xs text-warning mt-1">
            {totalRows > 0 ? Math.round((rowsPending / totalRows) * 100) : 0}% pending
          </div>
        </div>

        {/* Adjusted Records */}
        <div className="text-center">
          <div className="text-3xl font-bold text-info mb-1">
            {rowsAdjusted?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Adjusted</div>
          <div className="text-xs text-info mt-1">
            {adjustmentRate}% adjusted
          </div>
        </div>
      </div>

      {/* Progress Indicators */}
      {totalRows > 0 && (
        <div className="mt-6 space-y-4">
          {/* Promotion Progress */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-foreground">Promotion Progress</span>
              <span className="text-sm text-muted-foreground">{promotionRate}% promoted</span>
            </div>
            <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
              <div className="h-full flex">
                <div 
                  className="bg-success transition-all duration-500"
                  style={{ width: `${promotionRate}%` }}
                />
                <div 
                  className="bg-warning transition-all duration-500"
                  style={{ width: `${100 - promotionRate}%` }}
                />
              </div>
            </div>
          </div>

          {/* Adjustment Indicator */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Records requiring adjustments:</span>
            <span className="font-medium text-foreground">
              {rowsAdjusted} ({adjustmentRate}%)
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdjusterSummaryCard;