import React from 'react';
import Icon from '../../../components/AppIcon';

const DataQualityCard = ({
  metrics = {
    email_deliverability_rate: 0,
    email_completeness_rate: 0,
    phone_accuracy_rate: 0,
    personal_phone_accuracy_rate: 0,
    linkedin_match_rate: 0,
    company_name_completeness: 0,
    job_title_completeness: 0,
    overall_quality_score: 0,
    total_people_records: 0,
    promoted_people_records: 0
  },
  isLoading = false,
  onDrillDown,
  timeRange = '30_days',
  className = ''
}) => {
  const formatPercentage = (num) => {
    return `${(num || 0).toFixed(1)}%`;
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('en-US').format(num || 0);
  };

  const getQualityStatus = (rate) => {
    if (rate >= 90) return { color: 'text-success', bg: 'bg-success/10', icon: 'CheckCircle', label: 'Excellent' };
    if (rate >= 80) return { color: 'text-success', bg: 'bg-success/10', icon: 'CheckCircle', label: 'Good' };
    if (rate >= 70) return { color: 'text-warning', bg: 'bg-warning/10', icon: 'AlertCircle', label: 'Fair' };
    if (rate >= 50) return { color: 'text-destructive', bg: 'bg-destructive/10', icon: 'AlertTriangle', label: 'Poor' };
    return { color: 'text-destructive', bg: 'bg-destructive/10', icon: 'XCircle', label: 'Critical' };
  };

  const overallQuality = getQualityStatus(metrics.overall_quality_score);
  const emailQuality = getQualityStatus(metrics.email_deliverability_rate);
  const phoneQuality = getQualityStatus(metrics.phone_accuracy_rate);
  const linkedinQuality = getQualityStatus(metrics.linkedin_match_rate);

  if (isLoading) {
    return (
      <div className={`bg-card border border-border rounded-lg p-8 text-center ${className}`}>
        <Icon name="Loader2" size={32} className="animate-spin mx-auto mb-4 text-muted-foreground" />
        <p className="text-muted-foreground">Loading data quality metrics...</p>
      </div>
    );
  }

  return (
    <div className={`bg-card border border-border rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Icon name="Shield" size={24} color="var(--color-primary)" />
          <div>
            <h3 className="text-lg font-medium text-foreground">
              Data Quality
            </h3>
            <p className="text-sm text-muted-foreground">
              Validation accuracy and completeness metrics
            </p>
          </div>
        </div>

        <div className={`px-3 py-1 rounded-full text-sm font-medium ${overallQuality.bg} ${overallQuality.color}`}>
          <Icon name={overallQuality.icon} size={12} className="inline mr-1" />
          {overallQuality.label}
        </div>
      </div>

      {/* Overall Quality Score */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-foreground">Overall Quality Score</span>
          <span className={`text-sm font-medium ${overallQuality.color}`}>
            {formatPercentage(metrics.overall_quality_score)}
          </span>
        </div>
        <div className="w-full bg-muted rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${
              metrics.overall_quality_score >= 90 ? 'bg-success' :
              metrics.overall_quality_score >= 80 ? 'bg-success' :
              metrics.overall_quality_score >= 70 ? 'bg-warning' :
              'bg-destructive'
            }`}
            style={{ width: `${Math.min(metrics.overall_quality_score, 100)}%` }}
          />
        </div>
      </div>

      {/* Key Data Quality Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">

        {/* Email Quality */}
        <div
          className="cursor-pointer hover:bg-muted/10 rounded p-3 transition-colors"
          onClick={() => onDrillDown?.('email_quality', metrics.email_deliverability_rate)}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Icon name="Mail" size={16} className={emailQuality.color} />
              <span className="text-sm font-medium">Email Quality</span>
            </div>
            <Icon name={emailQuality.icon} size={14} className={emailQuality.color} />
          </div>

          <div className={`text-2xl font-bold ${emailQuality.color} mb-1`}>
            {formatPercentage(metrics.email_deliverability_rate)}
          </div>

          <div className="text-xs text-muted-foreground mb-2">
            Deliverability Rate
          </div>

          <div className="text-xs text-muted-foreground">
            {formatPercentage(metrics.email_completeness_rate)} completeness
          </div>

          <div className="w-full bg-muted rounded-full h-1 mt-2">
            <div
              className={`h-1 rounded-full transition-all duration-500 ${
                metrics.email_deliverability_rate >= 90 ? 'bg-success' :
                metrics.email_deliverability_rate >= 80 ? 'bg-warning' :
                'bg-destructive'
              }`}
              style={{ width: `${Math.min(metrics.email_deliverability_rate, 100)}%` }}
            />
          </div>
        </div>

        {/* Phone Quality */}
        <div
          className="cursor-pointer hover:bg-muted/10 rounded p-3 transition-colors"
          onClick={() => onDrillDown?.('phone_quality', metrics.phone_accuracy_rate)}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Icon name="Phone" size={16} className={phoneQuality.color} />
              <span className="text-sm font-medium">Phone Quality</span>
            </div>
            <Icon name={phoneQuality.icon} size={14} className={phoneQuality.color} />
          </div>

          <div className={`text-2xl font-bold ${phoneQuality.color} mb-1`}>
            {formatPercentage(metrics.phone_accuracy_rate)}
          </div>

          <div className="text-xs text-muted-foreground mb-2">
            Work Phone Accuracy
          </div>

          <div className="text-xs text-muted-foreground">
            {formatPercentage(metrics.personal_phone_accuracy_rate)} personal
          </div>

          <div className="w-full bg-muted rounded-full h-1 mt-2">
            <div
              className={`h-1 rounded-full transition-all duration-500 ${
                metrics.phone_accuracy_rate >= 90 ? 'bg-success' :
                metrics.phone_accuracy_rate >= 80 ? 'bg-warning' :
                'bg-destructive'
              }`}
              style={{ width: `${Math.min(metrics.phone_accuracy_rate, 100)}%` }}
            />
          </div>
        </div>

        {/* LinkedIn Quality */}
        <div
          className="cursor-pointer hover:bg-muted/10 rounded p-3 transition-colors"
          onClick={() => onDrillDown?.('linkedin_quality', metrics.linkedin_match_rate)}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Icon name="Linkedin" size={16} className={linkedinQuality.color} />
              <span className="text-sm font-medium">LinkedIn Quality</span>
            </div>
            <Icon name={linkedinQuality.icon} size={14} className={linkedinQuality.color} />
          </div>

          <div className={`text-2xl font-bold ${linkedinQuality.color} mb-1`}>
            {formatPercentage(metrics.linkedin_match_rate)}
          </div>

          <div className="text-xs text-muted-foreground mb-2">
            Profile Match Rate
          </div>

          <div className="text-xs text-muted-foreground">
            Social data enrichment
          </div>

          <div className="w-full bg-muted rounded-full h-1 mt-2">
            <div
              className={`h-1 rounded-full transition-all duration-500 ${
                metrics.linkedin_match_rate >= 90 ? 'bg-success' :
                metrics.linkedin_match_rate >= 80 ? 'bg-warning' :
                'bg-destructive'
              }`}
              style={{ width: `${Math.min(metrics.linkedin_match_rate, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Completeness Metrics */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-foreground mb-3">Data Completeness</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">

          {/* Email Completeness */}
          <div className="text-center">
            <div className="text-lg font-bold text-info mb-1">
              {formatPercentage(metrics.email_completeness_rate)}
            </div>
            <div className="text-xs text-muted-foreground">Email</div>
            <div className="w-full bg-muted rounded-full h-1 mt-1">
              <div
                className="bg-info h-1 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(metrics.email_completeness_rate, 100)}%` }}
              />
            </div>
          </div>

          {/* Company Name Completeness */}
          <div className="text-center">
            <div className="text-lg font-bold text-success mb-1">
              {formatPercentage(metrics.company_name_completeness)}
            </div>
            <div className="text-xs text-muted-foreground">Company Name</div>
            <div className="w-full bg-muted rounded-full h-1 mt-1">
              <div
                className="bg-success h-1 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(metrics.company_name_completeness, 100)}%` }}
              />
            </div>
          </div>

          {/* Job Title Completeness */}
          <div className="text-center">
            <div className="text-lg font-bold text-warning mb-1">
              {formatPercentage(metrics.job_title_completeness)}
            </div>
            <div className="text-xs text-muted-foreground">Job Title</div>
            <div className="w-full bg-muted rounded-full h-1 mt-1">
              <div
                className="bg-warning h-1 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(metrics.job_title_completeness, 100)}%` }}
              />
            </div>
          </div>

          {/* LinkedIn Completeness */}
          <div className="text-center">
            <div className="text-lg font-bold text-accent mb-1">
              {formatPercentage(metrics.linkedin_match_rate)}
            </div>
            <div className="text-xs text-muted-foreground">LinkedIn</div>
            <div className="w-full bg-muted rounded-full h-1 mt-1">
              <div
                className="bg-accent h-1 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(metrics.linkedin_match_rate, 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Record Volume */}
      <div className="pt-4 border-t border-border">
        <h4 className="text-sm font-medium text-foreground mb-3">Data Volume</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            className="text-center p-4 bg-muted/10 rounded-lg cursor-pointer hover:bg-muted/20 transition-colors"
            onClick={() => onDrillDown?.('total_records', metrics.total_people_records)}
          >
            <div className="text-2xl font-bold text-primary mb-1">
              {formatNumber(metrics.total_people_records)}
            </div>
            <div className="text-sm text-muted-foreground mb-1">Total Records</div>
            <div className="text-xs text-primary">
              All people in database
            </div>
          </div>

          <div
            className="text-center p-4 bg-muted/10 rounded-lg cursor-pointer hover:bg-muted/20 transition-colors"
            onClick={() => onDrillDown?.('promoted_records', metrics.promoted_people_records)}
          >
            <div className="text-2xl font-bold text-success mb-1">
              {formatNumber(metrics.promoted_people_records)}
            </div>
            <div className="text-sm text-muted-foreground mb-1">Promoted Records</div>
            <div className="text-xs text-success">
              Campaign-ready people
            </div>
          </div>
        </div>
      </div>

      {/* Quality Improvement Recommendations */}
      <div className="mt-4 p-3 bg-accent/10 rounded-lg border border-accent/20">
        <div className="flex items-start space-x-2">
          <Icon name="Shield" size={16} color="var(--color-accent)" className="mt-0.5" />
          <div className="text-xs text-accent">
            <span className="font-medium">Data Quality Summary:</span>
            {' '}Overall score {formatPercentage(metrics.overall_quality_score)} across {formatNumber(metrics.total_people_records)} records.
            {metrics.overall_quality_score < 80 && (
              <span>
                {' '}Focus on improving {metrics.email_deliverability_rate < 80 ? 'email validation' : ''}
                {metrics.phone_accuracy_rate < 80 ? (metrics.email_deliverability_rate < 80 ? ', phone accuracy' : 'phone accuracy') : ''}
                {metrics.linkedin_match_rate < 80 ? (metrics.email_deliverability_rate < 80 || metrics.phone_accuracy_rate < 80 ? ', LinkedIn matching' : 'LinkedIn matching') : ''}.
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataQualityCard;