import React from 'react';
import Icon from '../../../components/AppIcon';

const CampaignPerformanceCard = ({
  metrics = {
    PLE: {
      email_open_rate: 0,
      email_click_rate: 0,
      email_response_rate: 0,
      linkedin_open_rate: 0,
      linkedin_response_rate: 0,
      phone_connect_rate: 0,
      meeting_booking_rate: 0,
      total_emails_sent: 0,
      total_linkedin_sent: 0,
      total_calls_made: 0,
      overall_effectiveness_score: 0
    },
    BIT: {
      email_open_rate: 0,
      email_click_rate: 0,
      email_response_rate: 0,
      linkedin_open_rate: 0,
      linkedin_response_rate: 0,
      phone_connect_rate: 0,
      meeting_booking_rate: 0,
      total_emails_sent: 0,
      total_linkedin_sent: 0,
      total_calls_made: 0,
      overall_effectiveness_score: 0
    }
  },
  isLoading = false,
  onDrillDown,
  timeRange = '30_days',
  showComparison = true,
  className = ''
}) => {
  const formatPercentage = (num) => {
    return `${(num || 0).toFixed(1)}%`;
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('en-US').format(num || 0);
  };

  const getPerformanceStatus = (rate) => {
    if (rate >= 5) return { color: 'text-success', bg: 'bg-success/10', icon: 'TrendingUp' };
    if (rate >= 3) return { color: 'text-warning', bg: 'bg-warning/10', icon: 'Minus' };
    return { color: 'text-destructive', bg: 'bg-destructive/10', icon: 'TrendingDown' };
  };

  const plePerformance = getPerformanceStatus(metrics.PLE?.email_response_rate || 0);
  const bitPerformance = getPerformanceStatus(metrics.BIT?.email_response_rate || 0);

  // Calculate comparison metrics
  const getComparisonIndicator = (pleValue, bitValue) => {
    if (!pleValue || !bitValue) return null;
    const diff = ((bitValue - pleValue) / pleValue) * 100;
    if (Math.abs(diff) < 5) return { icon: 'Minus', color: 'text-muted-foreground', text: 'Similar' };
    if (diff > 0) return { icon: 'ArrowUp', color: 'text-success', text: `+${diff.toFixed(0)}%` };
    return { icon: 'ArrowDown', color: 'text-destructive', text: `${diff.toFixed(0)}%` };
  };

  if (isLoading) {
    return (
      <div className={`bg-card border border-border rounded-lg p-8 text-center ${className}`}>
        <Icon name="Loader2" size={32} className="animate-spin mx-auto mb-4 text-muted-foreground" />
        <p className="text-muted-foreground">Loading campaign performance metrics...</p>
      </div>
    );
  }

  return (
    <div className={`bg-card border border-border rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Icon name="Target" size={24} color="var(--color-primary)" />
          <div>
            <h3 className="text-lg font-medium text-foreground">
              Campaign Performance
            </h3>
            <p className="text-sm text-muted-foreground">
              Cold Outreach (PLE) vs Sniper Marketing (BIT) effectiveness
            </p>
          </div>
        </div>
      </div>

      {/* Campaign Strategy Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">

        {/* PLE (Cold Outreach) Performance */}
        <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Icon name="Target" size={16} className="text-blue-600" />
              <span className="text-sm font-medium text-blue-900 dark:text-blue-100">Cold Outreach (PLE)</span>
            </div>
            <div className={`px-2 py-1 rounded text-xs font-medium ${plePerformance.bg} ${plePerformance.color}`}>
              <Icon name={plePerformance.icon} size={10} className="inline mr-1" />
              {formatPercentage(metrics.PLE?.overall_effectiveness_score || 0)}
            </div>
          </div>

          <div className="space-y-3">
            {/* Email Performance */}
            <div className="flex justify-between items-center">
              <span className="text-xs text-blue-700 dark:text-blue-300">Email Response</span>
              <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                {formatPercentage(metrics.PLE?.email_response_rate || 0)}
              </span>
            </div>

            {/* LinkedIn Performance */}
            <div className="flex justify-between items-center">
              <span className="text-xs text-blue-700 dark:text-blue-300">LinkedIn Response</span>
              <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                {formatPercentage(metrics.PLE?.linkedin_response_rate || 0)}
              </span>
            </div>

            {/* Phone Performance */}
            <div className="flex justify-between items-center">
              <span className="text-xs text-blue-700 dark:text-blue-300">Meeting Bookings</span>
              <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                {formatPercentage(metrics.PLE?.meeting_booking_rate || 0)}
              </span>
            </div>
          </div>

          {/* Volume Metrics */}
          <div className="mt-4 pt-3 border-t border-blue-200 dark:border-blue-800">
            <div className="flex justify-between text-xs text-blue-600">
              <span>{formatNumber(metrics.PLE?.total_emails_sent || 0)} emails</span>
              <span>{formatNumber(metrics.PLE?.total_calls_made || 0)} calls</span>
            </div>
          </div>
        </div>

        {/* BIT (Sniper Marketing) Performance */}
        <div className="bg-purple-50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Icon name="Zap" size={16} className="text-purple-600" />
              <span className="text-sm font-medium text-purple-900 dark:text-purple-100">Sniper Marketing (BIT)</span>
            </div>
            <div className={`px-2 py-1 rounded text-xs font-medium ${bitPerformance.bg} ${bitPerformance.color}`}>
              <Icon name={bitPerformance.icon} size={10} className="inline mr-1" />
              {formatPercentage(metrics.BIT?.overall_effectiveness_score || 0)}
            </div>
          </div>

          <div className="space-y-3">
            {/* Email Performance */}
            <div className="flex justify-between items-center">
              <span className="text-xs text-purple-700 dark:text-purple-300">Email Response</span>
              <span className="text-sm font-medium text-purple-900 dark:text-purple-100">
                {formatPercentage(metrics.BIT?.email_response_rate || 0)}
              </span>
            </div>

            {/* LinkedIn Performance */}
            <div className="flex justify-between items-center">
              <span className="text-xs text-purple-700 dark:text-purple-300">LinkedIn Response</span>
              <span className="text-sm font-medium text-purple-900 dark:text-purple-100">
                {formatPercentage(metrics.BIT?.linkedin_response_rate || 0)}
              </span>
            </div>

            {/* Phone Performance */}
            <div className="flex justify-between items-center">
              <span className="text-xs text-purple-700 dark:text-purple-300">Meeting Bookings</span>
              <span className="text-sm font-medium text-purple-900 dark:text-purple-100">
                {formatPercentage(metrics.BIT?.meeting_booking_rate || 0)}
              </span>
            </div>
          </div>

          {/* Volume Metrics */}
          <div className="mt-4 pt-3 border-t border-purple-200 dark:border-purple-800">
            <div className="flex justify-between text-xs text-purple-600">
              <span>{formatNumber(metrics.BIT?.total_emails_sent || 0)} emails</span>
              <span>{formatNumber(metrics.BIT?.total_calls_made || 0)} calls</span>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Performance Metrics */}
      {showComparison && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-foreground mb-3">Channel Performance Breakdown</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/10 border-b border-border">
                <tr>
                  <th className="text-left py-2 px-3 font-medium text-muted-foreground">Channel</th>
                  <th className="text-center py-2 px-3 font-medium text-muted-foreground">PLE</th>
                  <th className="text-center py-2 px-3 font-medium text-muted-foreground">BIT</th>
                  <th className="text-center py-2 px-3 font-medium text-muted-foreground">Comparison</th>
                </tr>
              </thead>
              <tbody>
                {/* Email Open Rate */}
                <tr className="border-b border-border">
                  <td className="py-2 px-3">
                    <div className="flex items-center space-x-2">
                      <Icon name="Mail" size={12} className="text-muted-foreground" />
                      <span>Email Open Rate</span>
                    </div>
                  </td>
                  <td className="text-center py-2 px-3 text-blue-600">
                    {formatPercentage(metrics.PLE?.email_open_rate || 0)}
                  </td>
                  <td className="text-center py-2 px-3 text-purple-600">
                    {formatPercentage(metrics.BIT?.email_open_rate || 0)}
                  </td>
                  <td className="text-center py-2 px-3">
                    {(() => {
                      const comparison = getComparisonIndicator(
                        metrics.PLE?.email_open_rate,
                        metrics.BIT?.email_open_rate
                      );
                      return comparison ? (
                        <span className={`text-xs ${comparison.color}`}>
                          <Icon name={comparison.icon} size={10} className="inline mr-1" />
                          {comparison.text}
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground">-</span>
                      );
                    })()}
                  </td>
                </tr>

                {/* Email Click Rate */}
                <tr className="border-b border-border">
                  <td className="py-2 px-3">
                    <div className="flex items-center space-x-2">
                      <Icon name="MousePointer" size={12} className="text-muted-foreground" />
                      <span>Email Click Rate</span>
                    </div>
                  </td>
                  <td className="text-center py-2 px-3 text-blue-600">
                    {formatPercentage(metrics.PLE?.email_click_rate || 0)}
                  </td>
                  <td className="text-center py-2 px-3 text-purple-600">
                    {formatPercentage(metrics.BIT?.email_click_rate || 0)}
                  </td>
                  <td className="text-center py-2 px-3">
                    {(() => {
                      const comparison = getComparisonIndicator(
                        metrics.PLE?.email_click_rate,
                        metrics.BIT?.email_click_rate
                      );
                      return comparison ? (
                        <span className={`text-xs ${comparison.color}`}>
                          <Icon name={comparison.icon} size={10} className="inline mr-1" />
                          {comparison.text}
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground">-</span>
                      );
                    })()}
                  </td>
                </tr>

                {/* Email Response Rate */}
                <tr className="border-b border-border">
                  <td className="py-2 px-3">
                    <div className="flex items-center space-x-2">
                      <Icon name="MessageSquare" size={12} className="text-muted-foreground" />
                      <span>Email Response Rate</span>
                    </div>
                  </td>
                  <td className="text-center py-2 px-3 text-blue-600 font-medium">
                    {formatPercentage(metrics.PLE?.email_response_rate || 0)}
                  </td>
                  <td className="text-center py-2 px-3 text-purple-600 font-medium">
                    {formatPercentage(metrics.BIT?.email_response_rate || 0)}
                  </td>
                  <td className="text-center py-2 px-3">
                    {(() => {
                      const comparison = getComparisonIndicator(
                        metrics.PLE?.email_response_rate,
                        metrics.BIT?.email_response_rate
                      );
                      return comparison ? (
                        <span className={`text-xs font-medium ${comparison.color}`}>
                          <Icon name={comparison.icon} size={10} className="inline mr-1" />
                          {comparison.text}
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground">-</span>
                      );
                    })()}
                  </td>
                </tr>

                {/* Phone Connect Rate */}
                <tr className="border-b border-border">
                  <td className="py-2 px-3">
                    <div className="flex items-center space-x-2">
                      <Icon name="Phone" size={12} className="text-muted-foreground" />
                      <span>Phone Connect Rate</span>
                    </div>
                  </td>
                  <td className="text-center py-2 px-3 text-blue-600">
                    {formatPercentage(metrics.PLE?.phone_connect_rate || 0)}
                  </td>
                  <td className="text-center py-2 px-3 text-purple-600">
                    {formatPercentage(metrics.BIT?.phone_connect_rate || 0)}
                  </td>
                  <td className="text-center py-2 px-3">
                    {(() => {
                      const comparison = getComparisonIndicator(
                        metrics.PLE?.phone_connect_rate,
                        metrics.BIT?.phone_connect_rate
                      );
                      return comparison ? (
                        <span className={`text-xs ${comparison.color}`}>
                          <Icon name={comparison.icon} size={10} className="inline mr-1" />
                          {comparison.text}
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground">-</span>
                      );
                    })()}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Performance Summary */}
      <div className="pt-4 border-t border-border">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div
            className="text-center p-4 bg-muted/10 rounded-lg cursor-pointer hover:bg-muted/20 transition-colors"
            onClick={() => onDrillDown?.('total_volume', {
              ple_emails: metrics.PLE?.total_emails_sent || 0,
              bit_emails: metrics.BIT?.total_emails_sent || 0
            })}
          >
            <div className="text-lg font-bold text-primary mb-1">
              {formatNumber((metrics.PLE?.total_emails_sent || 0) + (metrics.BIT?.total_emails_sent || 0))}
            </div>
            <div className="text-sm text-muted-foreground mb-1">Total Emails Sent</div>
            <div className="text-xs text-muted-foreground">
              PLE: {formatNumber(metrics.PLE?.total_emails_sent || 0)} • BIT: {formatNumber(metrics.BIT?.total_emails_sent || 0)}
            </div>
          </div>

          <div className="text-center p-4 bg-muted/10 rounded-lg">
            <div className="text-lg font-bold text-success mb-1">
              {formatPercentage(((metrics.PLE?.overall_effectiveness_score || 0) + (metrics.BIT?.overall_effectiveness_score || 0)) / 2)}
            </div>
            <div className="text-sm text-muted-foreground mb-1">Overall Effectiveness</div>
            <div className="text-xs text-muted-foreground">
              Combined PLE & BIT performance
            </div>
          </div>

          <div className="text-center p-4 bg-muted/10 rounded-lg">
            <div className="text-lg font-bold text-accent mb-1">
              {(metrics.BIT?.email_response_rate || 0) > (metrics.PLE?.email_response_rate || 0) ? 'BIT' : 'PLE'}
            </div>
            <div className="text-sm text-muted-foreground mb-1">Top Performer</div>
            <div className="text-xs text-muted-foreground">
              Higher response rates
            </div>
          </div>
        </div>
      </div>

      {/* Campaign Strategy Indicator */}
      <div className="mt-4 p-3 bg-accent/10 rounded-lg border border-accent/20">
        <div className="flex items-start space-x-2">
          <Icon name="Target" size={16} color="var(--color-accent)" className="mt-0.5" />
          <div className="text-xs text-accent">
            <span className="font-medium">Campaign Performance:</span>
            {' '}BIT (Sniper Marketing) typically outperforms PLE (Cold Outreach) with higher response rates due to intent signals.
            {' '}PLE provides broader reach while BIT offers precision targeting. Optimal strategy combines both approaches.
          </div>
        </div>
      </div>
    </div>
  );
};

export default CampaignPerformanceCard;