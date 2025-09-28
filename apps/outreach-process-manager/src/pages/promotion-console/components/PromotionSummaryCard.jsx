import React from 'react';
import Icon from '../../../components/AppIcon';

const PromotionSummaryCard = ({
  summary = {
    total_eligible: 0,
    rows_promoted: 0,
    rows_failed: 0,
    last_promotion_at: null,
    success_rate: 100
  },
  recordType = 'company',
  isLoading = false,
  className = ''
}) => {
  const { total_eligible, rows_promoted, rows_failed, last_promotion_at, success_rate } = summary;

  const pendingPromotion = total_eligible - rows_promoted - rows_failed;
  const promotionRate = success_rate || 0;

  return (
    <div className={`bg-card border border-border rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Icon name="Upload" size={24} color="var(--color-primary)" />
          <h2 className="text-xl font-semibold text-foreground">
            {recordType === 'company' ? 'Company' : 'People'} Promotion Summary
          </h2>
        </div>

        {isLoading && (
          <div className="flex items-center space-x-2 text-muted-foreground">
            <Icon name="Loader2" size={16} className="animate-spin" />
            <span className="text-sm">Loading promotion data...</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-4 gap-6">
        {/* Total Eligible Records */}
        <div className="text-center">
          <div className="text-3xl font-bold text-info mb-1">
            {total_eligible?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Eligible for Promotion</div>
          <div className="text-xs text-muted-foreground mt-1">
            Validated records ready
          </div>
        </div>

        {/* Promoted Records */}
        <div className="text-center">
          <div className="text-3xl font-bold text-success mb-1">
            {rows_promoted?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Promoted to Master</div>
          <div className="text-xs text-success mt-1">
            Successfully moved
          </div>
        </div>

        {/* Pending Promotion */}
        <div className="text-center">
          <div className="text-3xl font-bold text-warning mb-1">
            {pendingPromotion > 0 ? pendingPromotion.toLocaleString() : '0'}
          </div>
          <div className="text-sm text-muted-foreground">Pending Promotion</div>
          <div className="text-xs text-warning mt-1">
            Awaiting batch processing
          </div>
        </div>

        {/* Failed Promotions */}
        <div className="text-center">
          <div className="text-3xl font-bold text-destructive mb-1">
            {rows_failed?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Failed Promotions</div>
          <div className="text-xs text-destructive mt-1">
            Requires investigation
          </div>
        </div>
      </div>

      {/* Promotion Progress Bar */}
      {total_eligible > 0 && (
        <div className="mt-6 space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-foreground">Promotion Progress</span>
              <span className="text-sm text-muted-foreground">
                {rows_promoted} / {total_eligible} records promoted ({Math.round((rows_promoted / total_eligible) * 100)}%)
              </span>
            </div>
            <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
              <div className="h-full flex">
                <div
                  className="bg-success transition-all duration-500"
                  style={{ width: `${(rows_promoted / total_eligible) * 100}%` }}
                />
                <div
                  className="bg-warning transition-all duration-500"
                  style={{ width: `${(pendingPromotion / total_eligible) * 100}%` }}
                />
                <div
                  className="bg-destructive transition-all duration-500"
                  style={{ width: `${(rows_failed / total_eligible) * 100}%` }}
                />
              </div>
            </div>
          </div>

          {/* Last Promotion Timestamp */}
          {last_promotion_at && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Last promotion batch:</span>
              <span className="font-medium text-foreground font-mono">
                {new Date(last_promotion_at).toLocaleString()}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Step 4 Master Table Notice */}
      <div className="mt-4 p-3 bg-accent/10 rounded-lg border border-accent/20">
        <div className="flex items-start space-x-2">
          <Icon name="Database" size={16} color="var(--color-accent)" className="mt-0.5" />
          <div className="text-xs text-accent">
            <span className="font-medium">Target:</span> {recordType === 'company' ? 'marketing.company_master' : 'marketing.people_master'}
            {' '}• Only validated records with validation_status='passed' can be promoted.
          </div>
        </div>
      </div>
    </div>
  );
};

export default PromotionSummaryCard;