import React from 'react';
import Icon from '../../../components/AppIcon';

const AttributionAnalytics = ({
  pleData = null,
  bitData = null,
  isLoading = false,
  className = ''
}) => {
  if (isLoading) {
    return (
      <div className={`bg-card border border-border rounded-lg p-8 text-center ${className}`}>
        <Icon name="Loader2" size={32} className="animate-spin mx-auto mb-4 text-muted-foreground" />
        <p className="text-muted-foreground">Loading analytics data...</p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* PLE Performance Section */}
      {pleData && (
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-6">
            <Icon name="Target" size={24} color="var(--color-primary)" />
            <div>
              <h3 className="text-lg font-medium text-foreground">
                PLE (Perpetual Lead Engine) Performance
              </h3>
              <p className="text-sm text-muted-foreground">
                Lead scoring model accuracy and continuous learning metrics
              </p>
            </div>
          </div>

          {/* PLE Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            {/* Overall Accuracy */}
            <div className="text-center">
              <div className="text-3xl font-bold text-success mb-1">
                {pleData.model_accuracy.overall_accuracy}%
              </div>
              <div className="text-sm text-muted-foreground">Overall Accuracy</div>
              <div className="text-xs text-success mt-1">
                Prediction vs Actual Outcomes
              </div>
            </div>

            {/* Accurate Predictions */}
            <div className="text-center">
              <div className="text-3xl font-bold text-info mb-1">
                {pleData.scoring_impact.accurate_predictions?.toLocaleString()}
              </div>
              <div className="text-sm text-muted-foreground">Accurate Predictions</div>
              <div className="text-xs text-info mt-1">
                Predictions ≥ 80% accuracy
              </div>
            </div>

            {/* Score Improvements */}
            <div className="text-center">
              <div className="text-3xl font-bold text-warning mb-1">
                {pleData.scoring_impact.score_improvements?.toLocaleString()}
              </div>
              <div className="text-sm text-muted-foreground">Score Improvements</div>
              <div className="text-xs text-warning mt-1">
                Models improved by attribution
              </div>
            </div>
          </div>

          {/* Accuracy by Outcome */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-foreground mb-3">Accuracy by Outcome</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.entries(pleData.model_accuracy.accuracy_by_outcome || {}).map(([outcome, accuracy]) => (
                <div key={outcome} className="text-center p-3 bg-muted/20 rounded">
                  <div className="text-lg font-bold text-foreground mb-1">
                    {accuracy}%
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {outcome.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Accuracy Trend */}
          {pleData.model_accuracy.accuracy_trend && pleData.model_accuracy.accuracy_trend.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-foreground mb-3">Accuracy Trend</h4>
              <div className="space-y-2">
                {pleData.model_accuracy.accuracy_trend.slice(0, 5).map((point, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-muted/10 rounded">
                    <span className="text-sm text-muted-foreground">
                      {new Date(point.date).toLocaleDateString()}
                    </span>
                    <span className="font-medium text-foreground">
                      {point.accuracy}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* BIT Signals Section */}
      {bitData && (
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-6">
            <Icon name="Zap" size={24} color="var(--color-primary)" />
            <div>
              <h3 className="text-lg font-medium text-foreground">
                BIT (Buyer Intent Trigger) Signal Performance
              </h3>
              <p className="text-sm text-muted-foreground">
                Intent signal effectiveness and weight adjustments based on attribution
              </p>
            </div>
          </div>

          {/* Top Performing Signals */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-foreground mb-3">Top Performing Signals</h4>
            <div className="flex flex-wrap gap-2">
              {bitData.top_performing_signals?.map((signal, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-success/10 text-success rounded-full text-sm font-medium"
                >
                  <Icon name="TrendingUp" size={12} className="inline mr-1" />
                  {signal.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </span>
              ))}
            </div>
          </div>

          {/* Underperforming Signals */}
          {bitData.underperforming_signals && bitData.underperforming_signals.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-medium text-foreground mb-3">Underperforming Signals</h4>
              <div className="flex flex-wrap gap-2">
                {bitData.underperforming_signals.map((signal, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-destructive/10 text-destructive rounded-full text-sm font-medium"
                  >
                    <Icon name="TrendingDown" size={12} className="inline mr-1" />
                    {signal.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Signal Effectiveness Table */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-foreground mb-3">Signal Effectiveness Metrics</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/10 border-b border-border">
                  <tr>
                    <th className="text-left py-2 px-3 font-medium text-muted-foreground">Signal Type</th>
                    <th className="text-left py-2 px-3 font-medium text-muted-foreground">Correlation</th>
                    <th className="text-left py-2 px-3 font-medium text-muted-foreground">True Positive</th>
                    <th className="text-left py-2 px-3 font-medium text-muted-foreground">False Positive</th>
                    <th className="text-left py-2 px-3 font-medium text-muted-foreground">Weight Adj.</th>
                    <th className="text-left py-2 px-3 font-medium text-muted-foreground">Outcomes</th>
                  </tr>
                </thead>
                <tbody>
                  {bitData.signal_effectiveness?.slice(0, 10).map((signal, index) => (
                    <tr key={index} className="border-b border-border last:border-b-0">
                      <td className="py-2 px-3">
                        <span className="font-medium text-foreground">
                          {signal.signal_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                      </td>
                      <td className="py-2 px-3">
                        <div className="flex items-center space-x-2">
                          <span className={`font-medium ${
                            signal.correlation_strength >= 0.7 ? 'text-success' :
                            signal.correlation_strength >= 0.4 ? 'text-warning' : 'text-destructive'
                          }`}>
                            {(signal.correlation_strength * 100).toFixed(1)}%
                          </span>
                        </div>
                      </td>
                      <td className="py-2 px-3">
                        <span className="text-success">
                          {(signal.true_positive_rate * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-2 px-3">
                        <span className="text-destructive">
                          {(signal.false_positive_rate * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-2 px-3">
                        <span className={`font-medium ${
                          signal.weight_adjustment > 0 ? 'text-success' :
                          signal.weight_adjustment < 0 ? 'text-destructive' : 'text-muted-foreground'
                        }`}>
                          {signal.weight_adjustment > 0 ? '+' : ''}{(signal.weight_adjustment * 10000).toFixed(1)}
                        </span>
                      </td>
                      <td className="py-2 px-3">
                        <span className="text-muted-foreground">
                          {signal.outcomes_influenced}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Recent Weight Changes */}
          {bitData.signal_weight_changes && bitData.signal_weight_changes.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-foreground mb-3">Recent Weight Adjustments</h4>
              <div className="space-y-2">
                {bitData.signal_weight_changes.slice(0, 5).map((change, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-muted/10 rounded">
                    <div className="flex-1">
                      <div className="font-medium text-foreground text-sm">
                        {change.signal_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {change.reason}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-muted-foreground">
                          {change.weight_before.toFixed(4)}
                        </span>
                        <Icon
                          name="ArrowRight"
                          size={12}
                          className={
                            change.weight_after > change.weight_before ? 'text-success' : 'text-destructive'
                          }
                        />
                        <span className={`text-xs font-medium ${
                          change.weight_after > change.weight_before ? 'text-success' : 'text-destructive'
                        }`}>
                          {change.weight_after.toFixed(4)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Learning Impact Summary */}
      {(pleData || bitData) && (
        <div className="bg-accent/10 border border-accent/20 rounded-lg p-4">
          <div className="flex items-start space-x-2">
            <Icon name="Brain" size={16} color="var(--color-accent)" className="mt-0.5" />
            <div className="text-xs text-accent">
              <span className="font-medium">Continuous Learning Impact:</span>
              {' '}Attribution outcomes are actively improving model accuracy
              {pleData && ` (${pleData.scoring_impact.score_improvements} PLE improvements)`}
              {pleData && bitData && ' and '}
              {bitData && ` (${bitData.signal_effectiveness?.length || 0} BIT signals optimized)`}.
              This closed-loop feedback ensures the Barton Doctrine pipeline gets smarter over time.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AttributionAnalytics;