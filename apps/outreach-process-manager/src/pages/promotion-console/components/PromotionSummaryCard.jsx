import React from 'react';
import Icon from '../../../components/AppIcon';

const PromotionSummaryCard = ({ summary, isLoading = false, className = '' }) => {
  if (!summary && !isLoading) return null;

  const rowsPromoted = summary?.rows_promoted || 0;
  const rowsPending = summary?.rows_pending || 0;
  const rowsFailed = summary?.rows_failed || 0;
  const totalRows = rowsPromoted + rowsPending + rowsFailed;
  
  const promotionRate = totalRows > 0 ? Math.round((rowsPromoted / totalRows) * 100) : 0;
  const failureRate = totalRows > 0 ? Math.round((rowsFailed / totalRows) * 100) : 0;

  return (
    <div className={`bg-card border border-border rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Icon name="Send" size={24} color="var(--color-primary)" />
          <div>
            <h2 className="text-xl font-semibold text-foreground">Promotion Summary</h2>
            {summary?.doctrine && summary?.altitude && (
              <span className="text-sm text-muted-foreground">
                {summary?.doctrine} • Alt {summary?.altitude}
              </span>
            )}
          </div>
        </div>
        
        {isLoading && (
          <div className="flex items-center space-x-2 text-muted-foreground">
            <Icon name="Loader2" size={16} className="animate-spin" />
            <span className="text-sm">Processing promotion...</span>
          </div>
        )}
      </div>
      <div className="grid grid-cols-4 gap-6">
        {/* Promoted Records */}
        <div className="text-center">
          <div className="text-3xl font-bold text-success mb-1">
            {rowsPromoted?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Promoted</div>
          <div className="text-xs text-success mt-1">
            {promotionRate}% success rate
          </div>
        </div>

        {/* Pending Records */}
        <div className="text-center">
          <div className="text-3xl font-bold text-warning mb-1">
            {rowsPending?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Pending</div>
          <div className="text-xs text-warning mt-1">
            {totalRows > 0 ? Math.round((rowsPending / totalRows) * 100) : 0}% in queue
          </div>
        </div>

        {/* Failed Records */}
        <div className="text-center">
          <div className="text-3xl font-bold text-destructive mb-1">
            {rowsFailed?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Failed</div>
          <div className="text-xs text-destructive mt-1">
            {failureRate}% failed
          </div>
        </div>

        {/* Timestamp */}
        <div className="text-center">
          <div className="text-sm text-muted-foreground mb-1">Timestamp</div>
          <div className="text-xs font-mono text-foreground bg-muted px-2 py-1 rounded">
            {summary?.promotion_timestamp || new Date()?.toISOString()}
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            Last promotion
          </div>
        </div>
      </div>
      {/* Progress Bar */}
      {totalRows > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-foreground">Promotion Progress</span>
            <span className="text-sm text-muted-foreground">
              {rowsPromoted} / {totalRows} records promoted
            </span>
          </div>
          <div className="w-full bg-muted rounded-full h-3 overflow-hidden">
            <div className="h-full flex">
              <div 
                className="bg-success transition-all duration-500"
                style={{ width: `${promotionRate}%` }}
              />
              <div 
                className="bg-warning transition-all duration-500"
                style={{ width: `${(rowsPending / totalRows) * 100}%` }}
              />
              <div 
                className="bg-destructive transition-all duration-500"
                style={{ width: `${failureRate}%` }}
              />
            </div>
          </div>
          <div className="flex justify-between text-xs text-muted-foreground mt-2">
            <span>✅ Promoted ({promotionRate}%)</span>
            <span>⏳ Pending ({Math.round((rowsPending / totalRows) * 100)}%)</span>
            <span>❌ Failed ({failureRate}%)</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default PromotionSummaryCard;