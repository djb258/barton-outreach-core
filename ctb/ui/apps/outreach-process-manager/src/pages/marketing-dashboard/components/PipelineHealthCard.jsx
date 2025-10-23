import React from 'react';
import Icon from '../../../components/AppIcon';

const PipelineHealthCard = ({
  metrics = {
    total_company_leads: 0,
    total_people_leads: 0,
    validated_companies: 0,
    validated_people: 0,
    promoted_companies: 0,
    promoted_people: 0,
    cold_outreach_companies: 0,
    cold_outreach_people: 0,
    sniper_companies: 0,
    sniper_people: 0,
    company_validation_rate: 0,
    people_validation_rate: 0,
    company_promotion_rate: 0,
    people_promotion_rate: 0,
    end_to_end_company_efficiency: 0,
    end_to_end_people_efficiency: 0
  },
  isLoading = false,
  onDrillDown,
  timeRange = '30_days',
  className = ''
}) => {
  const formatNumber = (num) => {
    return new Intl.NumberFormat('en-US').format(num || 0);
  };

  const formatPercentage = (num) => {
    return `${(num || 0).toFixed(1)}%`;
  };

  const getHealthStatus = (rate) => {
    if (rate >= 80) return { color: 'text-success', bg: 'bg-success/10', icon: 'CheckCircle' };
    if (rate >= 60) return { color: 'text-warning', bg: 'bg-warning/10', icon: 'AlertCircle' };
    return { color: 'text-destructive', bg: 'bg-destructive/10', icon: 'XCircle' };
  };

  const companyHealth = getHealthStatus(metrics.company_validation_rate);
  const peopleHealth = getHealthStatus(metrics.people_validation_rate);

  if (isLoading) {
    return (
      <div className={`bg-card border border-border rounded-lg p-8 text-center ${className}`}>
        <Icon name="Loader2" size={32} className="animate-spin mx-auto mb-4 text-muted-foreground" />
        <p className="text-muted-foreground">Loading pipeline health metrics...</p>
      </div>
    );
  }

  return (
    <div className={`bg-card border border-border rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Icon name="TrendingUp" size={24} color="var(--color-primary)" />
          <div>
            <h3 className="text-lg font-medium text-foreground">
              Pipeline Health
            </h3>
            <p className="text-sm text-muted-foreground">
              Lead flow through Barton Doctrine stages
            </p>
          </div>
        </div>
      </div>

      {/* Main Pipeline Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
        {/* Total Leads */}
        <div
          className="text-center cursor-pointer hover:bg-muted/10 rounded p-3 transition-colors"
          onClick={() => onDrillDown?.('total_leads', metrics.total_company_leads + metrics.total_people_leads)}
        >
          <div className="text-3xl font-bold text-info mb-1">
            {formatNumber(metrics.total_company_leads + metrics.total_people_leads)}
          </div>
          <div className="text-sm text-muted-foreground">Total Leads</div>
          <div className="text-xs text-info mt-1">
            {formatNumber(metrics.total_company_leads)} companies • {formatNumber(metrics.total_people_leads)} people
          </div>
        </div>

        {/* Validated Leads */}
        <div
          className="text-center cursor-pointer hover:bg-muted/10 rounded p-3 transition-colors"
          onClick={() => onDrillDown?.('validated_leads', metrics.validated_companies + metrics.validated_people)}
        >
          <div className="text-3xl font-bold text-success mb-1">
            {formatNumber(metrics.validated_companies + metrics.validated_people)}
          </div>
          <div className="text-sm text-muted-foreground">Validated</div>
          <div className="text-xs text-success mt-1">
            {formatNumber(metrics.validated_companies)} companies • {formatNumber(metrics.validated_people)} people
          </div>
        </div>

        {/* Promoted Leads */}
        <div
          className="text-center cursor-pointer hover:bg-muted/10 rounded p-3 transition-colors"
          onClick={() => onDrillDown?.('promoted_leads', metrics.promoted_companies + metrics.promoted_people)}
        >
          <div className="text-3xl font-bold text-warning mb-1">
            {formatNumber(metrics.promoted_companies + metrics.promoted_people)}
          </div>
          <div className="text-sm text-muted-foreground">Promoted</div>
          <div className="text-xs text-warning mt-1">
            {formatNumber(metrics.promoted_companies)} companies • {formatNumber(metrics.promoted_people)} people
          </div>
        </div>

        {/* Campaign Ready */}
        <div className="text-center">
          <div className="text-3xl font-bold text-primary mb-1">
            {formatNumber(metrics.cold_outreach_companies + metrics.cold_outreach_people + metrics.sniper_companies + metrics.sniper_people)}
          </div>
          <div className="text-sm text-muted-foreground">Campaign Ready</div>
          <div className="text-xs text-primary mt-1">
            PLE + BIT combined
          </div>
        </div>
      </div>

      {/* Campaign Strategy Breakdown */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-foreground mb-3">Campaign Strategy Distribution</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

          {/* Cold Outreach (PLE) */}
          <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Icon name="Target" size={16} className="text-blue-600" />
                <span className="text-sm font-medium text-blue-900 dark:text-blue-100">Cold Outreach (PLE)</span>
              </div>
              <span className="text-xs text-blue-600 bg-blue-100 dark:bg-blue-900/30 px-2 py-1 rounded">
                Lead Scoring
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="text-center">
                <div className="text-xl font-bold text-blue-600 mb-1">
                  {formatNumber(metrics.cold_outreach_companies)}
                </div>
                <div className="text-xs text-blue-700 dark:text-blue-300">Companies</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-blue-600 mb-1">
                  {formatNumber(metrics.cold_outreach_people)}
                </div>
                <div className="text-xs text-blue-700 dark:text-blue-300">People</div>
              </div>
            </div>
          </div>

          {/* Sniper Marketing (BIT) */}
          <div className="bg-purple-50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Icon name="Zap" size={16} className="text-purple-600" />
                <span className="text-sm font-medium text-purple-900 dark:text-purple-100">Sniper Marketing (BIT)</span>
              </div>
              <span className="text-xs text-purple-600 bg-purple-100 dark:bg-purple-900/30 px-2 py-1 rounded">
                Intent Signals
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="text-center">
                <div className="text-xl font-bold text-purple-600 mb-1">
                  {formatNumber(metrics.sniper_companies)}
                </div>
                <div className="text-xs text-purple-700 dark:text-purple-300">Companies</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-purple-600 mb-1">
                  {formatNumber(metrics.sniper_people)}
                </div>
                <div className="text-xs text-purple-700 dark:text-purple-300">People</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Conversion Rates */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-foreground mb-3">Pipeline Conversion Rates</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">

          {/* Company Validation Rate */}
          <div className={`text-center p-3 rounded ${companyHealth.bg}`}>
            <div className="flex items-center justify-center space-x-1 mb-2">
              <Icon name={companyHealth.icon} size={16} className={companyHealth.color} />
              <span className="text-xs text-muted-foreground">Companies</span>
            </div>
            <div className={`text-lg font-bold ${companyHealth.color} mb-1`}>
              {formatPercentage(metrics.company_validation_rate)}
            </div>
            <div className="text-xs text-muted-foreground">Validation Rate</div>
          </div>

          {/* People Validation Rate */}
          <div className={`text-center p-3 rounded ${peopleHealth.bg}`}>
            <div className="flex items-center justify-center space-x-1 mb-2">
              <Icon name={peopleHealth.icon} size={16} className={peopleHealth.color} />
              <span className="text-xs text-muted-foreground">People</span>
            </div>
            <div className={`text-lg font-bold ${peopleHealth.color} mb-1`}>
              {formatPercentage(metrics.people_validation_rate)}
            </div>
            <div className="text-xs text-muted-foreground">Validation Rate</div>
          </div>

          {/* Company Promotion Rate */}
          <div className="text-center p-3 bg-muted/10 rounded">
            <div className="flex items-center justify-center space-x-1 mb-2">
              <Icon name="ArrowUp" size={16} className="text-warning" />
              <span className="text-xs text-muted-foreground">Companies</span>
            </div>
            <div className="text-lg font-bold text-warning mb-1">
              {formatPercentage(metrics.company_promotion_rate)}
            </div>
            <div className="text-xs text-muted-foreground">Promotion Rate</div>
          </div>

          {/* People Promotion Rate */}
          <div className="text-center p-3 bg-muted/10 rounded">
            <div className="flex items-center justify-center space-x-1 mb-2">
              <Icon name="ArrowUp" size={16} className="text-warning" />
              <span className="text-xs text-muted-foreground">People</span>
            </div>
            <div className="text-lg font-bold text-warning mb-1">
              {formatPercentage(metrics.people_promotion_rate)}
            </div>
            <div className="text-xs text-muted-foreground">Promotion Rate</div>
          </div>
        </div>
      </div>

      {/* End-to-End Efficiency */}
      <div className="pt-4 border-t border-border">
        <h4 className="text-sm font-medium text-foreground mb-3">End-to-End Pipeline Efficiency</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="text-center p-4 bg-gradient-to-r from-success/10 to-success/20 rounded-lg">
            <div className="text-2xl font-bold text-success mb-1">
              {formatPercentage(metrics.end_to_end_company_efficiency)}
            </div>
            <div className="text-sm text-muted-foreground mb-1">Company Efficiency</div>
            <div className="text-xs text-success">
              Intake → Campaign Ready
            </div>
          </div>
          <div className="text-center p-4 bg-gradient-to-r from-success/10 to-success/20 rounded-lg">
            <div className="text-2xl font-bold text-success mb-1">
              {formatPercentage(metrics.end_to_end_people_efficiency)}
            </div>
            <div className="text-sm text-muted-foreground mb-1">People Efficiency</div>
            <div className="text-xs text-success">
              Intake → Campaign Ready
            </div>
          </div>
        </div>
      </div>

      {/* Pipeline Flow Indicator */}
      <div className="mt-4 p-3 bg-accent/10 rounded-lg border border-accent/20">
        <div className="flex items-start space-x-2">
          <Icon name="TrendingUp" size={16} color="var(--color-accent)" className="mt-0.5" />
          <div className="text-xs text-accent">
            <span className="font-medium">Pipeline Health:</span>
            {' '}Tracking {formatNumber(metrics.total_company_leads + metrics.total_people_leads)} total leads through Barton Doctrine stages.
            {' '}{formatPercentage((metrics.end_to_end_company_efficiency + metrics.end_to_end_people_efficiency) / 2)} average efficiency from intake to campaign readiness.
          </div>
        </div>
      </div>
    </div>
  );
};

export default PipelineHealthCard;