import React from 'react';
import Icon from '../../../components/AppIcon';

const AttributionSummaryCard = ({
  summary = {
    total_attributions: 0,
    outcomes: {
      closed_won: { count: 0, revenue: 0 },
      closed_lost: { count: 0, potential_revenue: 0 },
      nurture: { count: 0 },
      churn: { count: 0 },
      qualified: { count: 0 },
      disqualified: { count: 0 }
    },
    conversion_rates: {
      win_rate: 0,
      qualification_rate: 0,
      churn_rate: 0
    },
    revenue_metrics: {
      total_revenue: 0,
      average_deal_size: 0,
      revenue_per_attribution: 0
    },
    time_metrics: {
      average_sales_cycle_days: 0,
      average_touchpoints_to_close: 0
    }
  },
  dateRange = '30_days',
  isLoading = false,
  className = ''
}) => {
  const { outcomes, conversion_rates, revenue_metrics, time_metrics } = summary;

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatNumber = (num, decimals = 1) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(num);
  };

  const getDateRangeLabel = (range) => {
    switch (range) {
      case '7_days': return 'Last 7 Days';
      case '30_days': return 'Last 30 Days';
      case '90_days': return 'Last 90 Days';
      default: return 'Custom Range';
    }
  };

  return (
    <div className={`bg-card border border-border rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Icon name="Repeat" size={24} color="var(--color-primary)" />
          <div>
            <h2 className="text-xl font-semibold text-foreground">
              Closed-Loop Attribution Summary
            </h2>
            <p className="text-sm text-muted-foreground">
              {getDateRangeLabel(dateRange)} • CRM Outcomes → PLE & BIT Feedback
            </p>
          </div>
        </div>

        {isLoading && (
          <div className="flex items-center space-x-2 text-muted-foreground">
            <Icon name="Loader2" size={16} className="animate-spin" />
            <span className="text-sm">Loading attribution data...</span>
          </div>
        )}
      </div>

      {/* Main Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
        {/* Total Attributions */}
        <div className="text-center">
          <div className="text-3xl font-bold text-info mb-1">
            {summary.total_attributions?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Total Attributions</div>
          <div className="text-xs text-info mt-1">
            All CRM outcomes tracked
          </div>
        </div>

        {/* Closed Won */}
        <div className="text-center">
          <div className="text-3xl font-bold text-success mb-1">
            {outcomes.closed_won.count?.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Closed Won</div>
          <div className="text-xs text-success mt-1">
            {formatCurrency(outcomes.closed_won.revenue)}
          </div>
        </div>

        {/* Win Rate */}
        <div className="text-center">
          <div className="text-3xl font-bold text-primary mb-1">
            {formatNumber(conversion_rates.win_rate)}%
          </div>
          <div className="text-sm text-muted-foreground">Win Rate</div>
          <div className="text-xs text-muted-foreground mt-1">
            Won vs Lost deals
          </div>
        </div>

        {/* Average Deal Size */}
        <div className="text-center">
          <div className="text-3xl font-bold text-warning mb-1">
            {formatCurrency(revenue_metrics.average_deal_size)}
          </div>
          <div className="text-sm text-muted-foreground">Avg Deal Size</div>
          <div className="text-xs text-warning mt-1">
            Per closed won deal
          </div>
        </div>
      </div>

      {/* Outcomes Breakdown */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-foreground mb-3">Outcome Distribution</h3>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
          {/* Closed Won */}
          <div className="text-center">
            <div className="text-lg font-bold text-success mb-1">
              {outcomes.closed_won.count}
            </div>
            <div className="text-xs text-muted-foreground">Won</div>
            <div className="w-full bg-muted rounded-full h-1 mt-1">
              <div
                className="bg-success h-1 rounded-full transition-all duration-500"
                style={{
                  width: `${summary.total_attributions > 0 ? (outcomes.closed_won.count / summary.total_attributions) * 100 : 0}%`
                }}
              />
            </div>
          </div>

          {/* Closed Lost */}
          <div className="text-center">
            <div className="text-lg font-bold text-destructive mb-1">
              {outcomes.closed_lost.count}
            </div>
            <div className="text-xs text-muted-foreground">Lost</div>
            <div className="w-full bg-muted rounded-full h-1 mt-1">
              <div
                className="bg-destructive h-1 rounded-full transition-all duration-500"
                style={{
                  width: `${summary.total_attributions > 0 ? (outcomes.closed_lost.count / summary.total_attributions) * 100 : 0}%`
                }}
              />
            </div>
          </div>

          {/* Qualified */}
          <div className="text-center">
            <div className="text-lg font-bold text-info mb-1">
              {outcomes.qualified.count}
            </div>
            <div className="text-xs text-muted-foreground">Qualified</div>
            <div className="w-full bg-muted rounded-full h-1 mt-1">
              <div
                className="bg-info h-1 rounded-full transition-all duration-500"
                style={{
                  width: `${summary.total_attributions > 0 ? (outcomes.qualified.count / summary.total_attributions) * 100 : 0}%`
                }}
              />
            </div>
          </div>

          {/* Nurture */}
          <div className="text-center">
            <div className="text-lg font-bold text-warning mb-1">
              {outcomes.nurture.count}
            </div>
            <div className="text-xs text-muted-foreground">Nurture</div>
            <div className="w-full bg-muted rounded-full h-1 mt-1">
              <div
                className="bg-warning h-1 rounded-full transition-all duration-500"
                style={{
                  width: `${summary.total_attributions > 0 ? (outcomes.nurture.count / summary.total_attributions) * 100 : 0}%`
                }}
              />
            </div>
          </div>

          {/* Disqualified */}
          <div className="text-center">
            <div className="text-lg font-bold text-muted-foreground mb-1">
              {outcomes.disqualified.count}
            </div>
            <div className="text-xs text-muted-foreground">Disqualified</div>
            <div className="w-full bg-muted rounded-full h-1 mt-1">
              <div
                className="bg-muted-foreground h-1 rounded-full transition-all duration-500"
                style={{
                  width: `${summary.total_attributions > 0 ? (outcomes.disqualified.count / summary.total_attributions) * 100 : 0}%`
                }}
              />
            </div>
          </div>

          {/* Churn */}
          <div className="text-center">
            <div className="text-lg font-bold text-accent mb-1">
              {outcomes.churn.count}
            </div>
            <div className="text-xs text-muted-foreground">Churn</div>
            <div className="w-full bg-muted rounded-full h-1 mt-1">
              <div
                className="bg-accent h-1 rounded-full transition-all duration-500"
                style={{
                  width: `${summary.total_attributions > 0 ? (outcomes.churn.count / summary.total_attributions) * 100 : 0}%`
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Key Performance Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-border">
        {/* Total Revenue */}
        <div className="text-center">
          <div className="text-sm text-muted-foreground mb-1">Total Revenue</div>
          <div className="text-lg font-bold text-success">
            {formatCurrency(revenue_metrics.total_revenue)}
          </div>
        </div>

        {/* Sales Cycle */}
        <div className="text-center">
          <div className="text-sm text-muted-foreground mb-1">Avg Sales Cycle</div>
          <div className="text-lg font-bold text-info">
            {formatNumber(time_metrics.average_sales_cycle_days, 0)} days
          </div>
        </div>

        {/* Touchpoints */}
        <div className="text-center">
          <div className="text-sm text-muted-foreground mb-1">Avg Touchpoints</div>
          <div className="text-lg font-bold text-warning">
            {formatNumber(time_metrics.average_touchpoints_to_close, 0)}
          </div>
        </div>

        {/* Revenue per Attribution */}
        <div className="text-center">
          <div className="text-sm text-muted-foreground mb-1">Revenue/Attribution</div>
          <div className="text-lg font-bold text-primary">
            {formatCurrency(revenue_metrics.revenue_per_attribution)}
          </div>
        </div>
      </div>

      {/* Closed-Loop Learning Indicator */}
      <div className="mt-4 p-3 bg-accent/10 rounded-lg border border-accent/20">
        <div className="flex items-start space-x-2">
          <Icon name="Brain" size={16} color="var(--color-accent)" className="mt-0.5" />
          <div className="text-xs text-accent">
            <span className="font-medium">Learning Loop Active:</span> Attribution outcomes are
            continuously fed back to PLE scoring models and BIT signal weights for improved predictions.
          </div>
        </div>
      </div>
    </div>
  );
};

export default AttributionSummaryCard;