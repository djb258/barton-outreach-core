import React from 'react';
import Icon from '../../../components/AppIcon';

const AttributionCard = ({
  metrics = {
    closed_won: {
      count: 0,
      total_revenue: 0,
      average_revenue: 0,
      avg_sales_cycle_days: 0,
      avg_touchpoints_to_close: 0
    },
    closed_lost: {
      count: 0,
      avg_sales_cycle_days: 0,
      avg_touchpoints_to_close: 0
    },
    nurture: { count: 0 },
    qualified: { count: 0 },
    disqualified: { count: 0 },
    churn: { count: 0 }
  },
  trends = [],
  isLoading = false,
  onDrillDown,
  timeRange = '30_days',
  showTrends = false,
  className = ''
}) => {
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount || 0);
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('en-US').format(num || 0);
  };

  const formatPercentage = (num) => {
    return `${(num || 0).toFixed(1)}%`;
  };

  const getOutcomeIcon = (outcome) => {
    switch (outcome) {
      case 'closed_won':
        return { icon: 'CheckCircle', color: 'text-success' };
      case 'closed_lost':
        return { icon: 'XCircle', color: 'text-destructive' };
      case 'qualified':
        return { icon: 'UserCheck', color: 'text-info' };
      case 'nurture':
        return { icon: 'Clock', color: 'text-warning' };
      case 'disqualified':
        return { icon: 'UserX', color: 'text-muted-foreground' };
      case 'churn':
        return { icon: 'UserMinus', color: 'text-accent' };
      default:
        return { icon: 'Circle', color: 'text-muted-foreground' };
    }
  };

  // Calculate totals and win rate
  const totalDeals = (metrics.closed_won?.count || 0) + (metrics.closed_lost?.count || 0);
  const winRate = totalDeals > 0 ? ((metrics.closed_won?.count || 0) / totalDeals) * 100 : 0;
  const totalAttributions = Object.values(metrics).reduce((sum, metric) => sum + (metric.count || 0), 0);

  // Calculate recent trend (last 4 weeks if trends available)
  const recentRevenue = showTrends && trends?.length > 0
    ? trends.slice(0, 4).reduce((sum, week) => sum + (week.weekly_revenue || 0), 0)
    : metrics.closed_won?.total_revenue || 0;

  if (isLoading) {
    return (
      <div className={`bg-card border border-border rounded-lg p-8 text-center ${className}`}>
        <Icon name="Loader2" size={32} className="animate-spin mx-auto mb-4 text-muted-foreground" />
        <p className="text-muted-foreground">Loading attribution metrics...</p>
      </div>
    );
  }

  return (
    <div className={`bg-card border border-border rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Icon name="Repeat" size={24} color="var(--color-primary)" />
          <div>
            <h3 className="text-lg font-medium text-foreground">
              Attribution Outcomes
            </h3>
            <p className="text-sm text-muted-foreground">
              Revenue attribution and pipeline outcomes
            </p>
          </div>
        </div>

        {winRate > 0 && (
          <div className="text-right">
            <div className="text-2xl font-bold text-success">
              {formatPercentage(winRate)}
            </div>
            <div className="text-xs text-muted-foreground">Win Rate</div>
          </div>
        )}
      </div>

      {/* Key Revenue Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
        {/* Total Revenue */}
        <div
          className="text-center cursor-pointer hover:bg-muted/10 rounded p-3 transition-colors"
          onClick={() => onDrillDown?.('total_revenue', metrics.closed_won?.total_revenue)}
        >
          <div className="text-3xl font-bold text-success mb-1">
            {formatCurrency(metrics.closed_won?.total_revenue || 0)}
          </div>
          <div className="text-sm text-muted-foreground">Total Revenue</div>
          <div className="text-xs text-success mt-1">
            Closed-Won deals
          </div>
        </div>

        {/* Average Deal Size */}
        <div className="text-center">
          <div className="text-3xl font-bold text-primary mb-1">
            {formatCurrency(metrics.closed_won?.average_revenue || 0)}
          </div>
          <div className="text-sm text-muted-foreground">Avg Deal Size</div>
          <div className="text-xs text-primary mt-1">
            Per closed deal
          </div>
        </div>

        {/* Deals Won */}
        <div
          className="text-center cursor-pointer hover:bg-muted/10 rounded p-3 transition-colors"
          onClick={() => onDrillDown?.('deals_won', metrics.closed_won?.count)}
        >
          <div className="text-3xl font-bold text-info mb-1">
            {formatNumber(metrics.closed_won?.count || 0)}
          </div>
          <div className="text-sm text-muted-foreground">Deals Won</div>
          <div className="text-xs text-info mt-1">
            Successful outcomes
          </div>
        </div>

        {/* Sales Cycle */}
        <div className="text-center">
          <div className="text-3xl font-bold text-warning mb-1">
            {Math.round(metrics.closed_won?.avg_sales_cycle_days || 0)}
          </div>
          <div className="text-sm text-muted-foreground">Avg Sales Cycle</div>
          <div className="text-xs text-warning mt-1">
            Days to close
          </div>
        </div>
      </div>

      {/* Outcome Distribution */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-foreground mb-3">Outcome Distribution</h4>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
          {Object.entries(metrics).map(([outcome, data]) => {
            const iconInfo = getOutcomeIcon(outcome);
            const percentage = totalAttributions > 0 ? ((data.count || 0) / totalAttributions) * 100 : 0;

            return (
              <div
                key={outcome}
                className="text-center cursor-pointer hover:bg-muted/10 rounded p-3 transition-colors"
                onClick={() => onDrillDown?.(outcome, data)}
              >
                <div className="flex items-center justify-center mb-2">
                  <Icon name={iconInfo.icon} size={16} className={iconInfo.color} />
                </div>
                <div className={`text-lg font-bold ${iconInfo.color} mb-1`}>
                  {formatNumber(data.count || 0)}
                </div>
                <div className="text-xs text-muted-foreground mb-1">
                  {outcome.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </div>
                <div className="w-full bg-muted rounded-full h-1">
                  <div
                    className={`h-1 rounded-full transition-all duration-500 ${
                      outcome === 'closed_won' ? 'bg-success' :
                      outcome === 'closed_lost' ? 'bg-destructive' :
                      outcome === 'qualified' ? 'bg-info' :
                      outcome === 'nurture' ? 'bg-warning' :
                      outcome === 'disqualified' ? 'bg-muted-foreground' :
                      'bg-accent'
                    }`}
                    style={{ width: `${Math.min(percentage, 100)}%` }}
                  />
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {formatPercentage(percentage)}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-foreground mb-3">Performance Insights</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">

          {/* Touchpoints to Close */}
          <div className="text-center p-3 bg-muted/10 rounded">
            <div className="text-lg font-bold text-accent mb-1">
              {Math.round(metrics.closed_won?.avg_touchpoints_to_close || 0)}
            </div>
            <div className="text-xs text-muted-foreground">Avg Touchpoints</div>
            <div className="text-xs text-accent mt-1">To close deals</div>
          </div>

          {/* Lost Deals Sales Cycle */}
          <div className="text-center p-3 bg-muted/10 rounded">
            <div className="text-lg font-bold text-destructive mb-1">
              {Math.round(metrics.closed_lost?.avg_sales_cycle_days || 0)}
            </div>
            <div className="text-xs text-muted-foreground">Lost Deal Cycle</div>
            <div className="text-xs text-destructive mt-1">Days before lost</div>
          </div>

          {/* Pipeline Velocity */}
          <div className="text-center p-3 bg-muted/10 rounded">
            <div className="text-lg font-bold text-info mb-1">
              {metrics.closed_won?.avg_sales_cycle_days && metrics.closed_won?.average_revenue
                ? Math.round((metrics.closed_won.average_revenue / metrics.closed_won.avg_sales_cycle_days) * 30)
                : 0}
            </div>
            <div className="text-xs text-muted-foreground">Pipeline Velocity</div>
            <div className="text-xs text-info mt-1">Revenue per month</div>
          </div>

          {/* Active Pipeline */}
          <div className="text-center p-3 bg-muted/10 rounded">
            <div className="text-lg font-bold text-warning mb-1">
              {formatNumber((metrics.qualified?.count || 0) + (metrics.nurture?.count || 0))}
            </div>
            <div className="text-xs text-muted-foreground">Active Pipeline</div>
            <div className="text-xs text-warning mt-1">Qualified + Nurture</div>
          </div>
        </div>
      </div>

      {/* Trends Chart (if trends data available) */}
      {showTrends && trends && trends.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-foreground mb-3">Revenue Trend (Last 12 Weeks)</h4>
          <div className="space-y-2">
            {trends.slice(0, 6).map((week, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-muted/10 rounded">
                <span className="text-sm text-muted-foreground">
                  Week of {new Date(week.week_start).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </span>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-success">
                    {formatNumber(week.weekly_closed_won || 0)} won
                  </span>
                  <span className="text-sm font-medium text-foreground">
                    {formatCurrency(week.weekly_revenue || 0)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Attribution Confidence */}
      <div className="pt-4 border-t border-border">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="text-center p-4 bg-gradient-to-r from-success/10 to-success/20 rounded-lg">
            <div className="text-2xl font-bold text-success mb-1">
              {formatNumber(totalAttributions)}
            </div>
            <div className="text-sm text-muted-foreground mb-1">Total Attributions</div>
            <div className="text-xs text-success">
              All tracked outcomes
            </div>
          </div>

          <div className="text-center p-4 bg-gradient-to-r from-primary/10 to-primary/20 rounded-lg">
            <div className="text-2xl font-bold text-primary mb-1">
              {showTrends && trends?.length > 0
                ? formatCurrency(recentRevenue)
                : formatCurrency(metrics.closed_won?.total_revenue || 0)
              }
            </div>
            <div className="text-sm text-muted-foreground mb-1">
              {showTrends ? 'Recent Revenue (4 weeks)' : 'Total Revenue'}
            </div>
            <div className="text-xs text-primary">
              Attributed to campaigns
            </div>
          </div>
        </div>
      </div>

      {/* Closed-Loop Learning Indicator */}
      <div className="mt-4 p-3 bg-accent/10 rounded-lg border border-accent/20">
        <div className="flex items-start space-x-2">
          <Icon name="Repeat" size={16} color="var(--color-accent)" className="mt-0.5" />
          <div className="text-xs text-accent">
            <span className="font-medium">Attribution Impact:</span>
            {' '}{formatNumber(totalAttributions)} outcomes tracked, feeding back into PLE scoring and BIT signal optimization.
            {' '}Win rate {formatPercentage(winRate)} with {Math.round(metrics.closed_won?.avg_sales_cycle_days || 0)} day average sales cycle.
            Closed-loop learning improves future campaign targeting.
          </div>
        </div>
      </div>
    </div>
  );
};

export default AttributionCard;