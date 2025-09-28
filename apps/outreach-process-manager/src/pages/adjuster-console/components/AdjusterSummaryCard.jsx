import React from 'react';
import Icon from '../../../components/AppIcon';

const AdjusterSummaryCard = ({
  summaryStats = {
    validation_failed: 0,
    enrichment_failed: 0,
    ready_for_adjustment: 0
  },
  recordType = 'company',
  isLoading = false,
  className = ''
}) => {
  const { validation_failed, enrichment_failed, ready_for_adjustment } = summaryStats;

  const enrichmentSuccessRate = validation_failed > 0
    ? Math.round(((validation_failed - enrichment_failed) / validation_failed) * 100)
    : 0;

  return (
    <div className={`bg-card border border-border rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Icon name="Settings" size={24} color="var(--color-primary)" />
          <h2 className="text-xl font-semibold text-foreground">
            {recordType === 'company' ? 'Company' : 'People'} Adjustment Summary
          </h2>
        </div>

        {isLoading && (
          <div className="flex items-center space-x-2 text-muted-foreground">
            <Icon name="Loader2" size={16} className="animate-spin" />
            <span className="text-sm">Loading...</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Validation Failed Records */}
        <div className="text-center">
          <div className="text-3xl font-bold text-destructive mb-1">
            {validation_failed?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Validation Failed</div>
          <div className="text-xs text-muted-foreground mt-1">
            Original validation failures
          </div>
        </div>

        {/* Enrichment Failed Records */}
        <div className="text-center">
          <div className="text-3xl font-bold text-warning mb-1">
            {enrichment_failed?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Enrichment Failed</div>
          <div className="text-xs text-warning mt-1">
            Could not auto-fix
          </div>
        </div>

        {/* Ready for Adjustment */}
        <div className="text-center">
          <div className="text-3xl font-bold text-info mb-1">
            {ready_for_adjustment?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Ready for Adjustment</div>
          <div className="text-xs text-info mt-1">
            Manual review required
          </div>
        </div>
      </div>

      {/* Enrichment Success Rate */}
      {validation_failed > 0 && (
        <div className="mt-6 space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-foreground">Enrichment Success Rate</span>
              <span className="text-sm text-muted-foreground">{enrichmentSuccessRate}%</span>
            </div>
            <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
              <div className="h-full flex">
                <div
                  className="bg-success transition-all duration-500"
                  style={{ width: `${enrichmentSuccessRate}%` }}
                />
                <div
                  className="bg-destructive transition-all duration-500"
                  style={{ width: `${100 - enrichmentSuccessRate}%` }}
                />
              </div>
            </div>
          </div>

          {/* Human Review Indicator */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Requiring human review:</span>
            <span className="font-medium text-foreground">
              {ready_for_adjustment} records ({Math.round((ready_for_adjustment / validation_failed) * 100)}%)
            </span>
          </div>
        </div>
      )}

      {/* Step 3 Doctrine Notice */}
      <div className="mt-4 p-3 bg-accent/10 rounded-lg border border-accent/20">
        <div className="flex items-start space-x-2">
          <Icon name="AlertCircle" size={16} color="var(--color-accent)" className="mt-0.5" />
          <div className="text-xs text-accent">
            <span className="font-medium">Barton Doctrine Step 3:</span> Human adjusters can only modify data fields.
            Barton IDs remain intact. All changes are logged to audit tables.
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdjusterSummaryCard;