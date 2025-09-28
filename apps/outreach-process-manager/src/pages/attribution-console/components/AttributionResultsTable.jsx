import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';

const AttributionResultsTable = ({
  records = [],
  isLoading = false,
  onRecordClick,
  className = ''
}) => {
  const [sortField, setSortField] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc');
  const [filterOutcome, setFilterOutcome] = useState('all');
  const [filterCRM, setFilterCRM] = useState('all');

  if (isLoading) {
    return (
      <div className={`bg-card border border-border rounded-lg p-8 text-center ${className}`}>
        <Icon name="Loader2" size={32} className="animate-spin mx-auto mb-4 text-muted-foreground" />
        <p className="text-muted-foreground">Loading attribution records...</p>
      </div>
    );
  }

  if (!records || records.length === 0) {
    return (
      <div className={`bg-card border border-border rounded-lg p-8 text-center ${className}`}>
        <Icon name="Database" size={48} className="mx-auto mb-4 text-muted-foreground opacity-50" />
        <h3 className="text-lg font-medium text-foreground mb-2">No Attribution Data</h3>
        <p className="text-sm text-muted-foreground">
          No attribution records found for the selected time period.
          Set up CRM webhooks to start receiving attribution data.
        </p>
      </div>
    );
  }

  // Filter records based on selected filters
  const filteredRecords = records.filter(record => {
    if (filterOutcome !== 'all' && record.outcome !== filterOutcome) {
      return false;
    }
    if (filterCRM !== 'all' && record.crm_system !== filterCRM) {
      return false;
    }
    return true;
  });

  // Sort records
  const sortedRecords = [...filteredRecords].sort((a, b) => {
    let aValue = a[sortField];
    let bValue = b[sortField];

    if (sortField === 'revenue_amount') {
      aValue = parseFloat(aValue || 0);
      bValue = parseFloat(bValue || 0);
    } else if (sortField === 'created_at' || sortField === 'actual_close_date') {
      aValue = new Date(aValue);
      bValue = new Date(bValue);
    }

    if (sortDirection === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const getOutcomeIcon = (outcome) => {
    switch (outcome) {
      case 'closed_won':
        return <Icon name="CheckCircle" size={16} className="text-success" />;
      case 'closed_lost':
        return <Icon name="XCircle" size={16} className="text-destructive" />;
      case 'qualified':
        return <Icon name="UserCheck" size={16} className="text-info" />;
      case 'disqualified':
        return <Icon name="UserX" size={16} className="text-muted-foreground" />;
      case 'nurture':
        return <Icon name="Clock" size={16} className="text-warning" />;
      case 'churn':
        return <Icon name="UserMinus" size={16} className="text-accent" />;
      default:
        return <Icon name="Circle" size={16} className="text-muted-foreground" />;
    }
  };

  const getOutcomeColor = (outcome) => {
    switch (outcome) {
      case 'closed_won':
        return 'text-success bg-success/10';
      case 'closed_lost':
        return 'text-destructive bg-destructive/10';
      case 'qualified':
        return 'text-info bg-info/10';
      case 'disqualified':
        return 'text-muted-foreground bg-muted';
      case 'nurture':
        return 'text-warning bg-warning/10';
      case 'churn':
        return 'text-accent bg-accent/10';
      default:
        return 'text-muted-foreground bg-muted';
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount || 0);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getUniqueValues = (field) => {
    return [...new Set(records.map(record => record[field]).filter(Boolean))];
  };

  return (
    <div className={`bg-card border border-border rounded-lg overflow-hidden ${className}`}>
      {/* Table Header */}
      <div className="px-4 py-3 bg-muted/10 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Icon name="Repeat" size={16} color="var(--color-muted-foreground)" />
            <h3 className="text-sm font-medium text-foreground">Attribution Records</h3>
            <span className="text-xs text-muted-foreground">({sortedRecords.length} of {records.length})</span>
          </div>

          {/* Filters */}
          <div className="flex items-center space-x-2">
            <select
              value={filterOutcome}
              onChange={(e) => setFilterOutcome(e.target.value)}
              className="px-2 py-1 text-xs border border-border rounded bg-background"
            >
              <option value="all">All Outcomes</option>
              {getUniqueValues('outcome').map(outcome => (
                <option key={outcome} value={outcome}>
                  {outcome.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </option>
              ))}
            </select>

            <select
              value={filterCRM}
              onChange={(e) => setFilterCRM(e.target.value)}
              className="px-2 py-1 text-xs border border-border rounded bg-background"
            >
              <option value="all">All CRM Systems</option>
              {getUniqueValues('crm_system').map(crm => (
                <option key={crm} value={crm}>{crm}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/10 border-b border-border">
            <tr>
              <th
                className="text-left py-3 px-4 font-medium text-muted-foreground cursor-pointer hover:text-foreground"
                onClick={() => handleSort('company_unique_id')}
              >
                <div className="flex items-center space-x-1">
                  <span>Company</span>
                  {sortField === 'company_unique_id' && (
                    <Icon name={sortDirection === 'asc' ? 'ArrowUp' : 'ArrowDown'} size={12} />
                  )}
                </div>
              </th>

              <th
                className="text-left py-3 px-4 font-medium text-muted-foreground cursor-pointer hover:text-foreground"
                onClick={() => handleSort('outcome')}
              >
                <div className="flex items-center space-x-1">
                  <span>Outcome</span>
                  {sortField === 'outcome' && (
                    <Icon name={sortDirection === 'asc' ? 'ArrowUp' : 'ArrowDown'} size={12} />
                  )}
                </div>
              </th>

              <th
                className="text-left py-3 px-4 font-medium text-muted-foreground cursor-pointer hover:text-foreground"
                onClick={() => handleSort('revenue_amount')}
              >
                <div className="flex items-center space-x-1">
                  <span>Revenue</span>
                  {sortField === 'revenue_amount' && (
                    <Icon name={sortDirection === 'asc' ? 'ArrowUp' : 'ArrowDown'} size={12} />
                  )}
                </div>
              </th>

              <th
                className="text-left py-3 px-4 font-medium text-muted-foreground cursor-pointer hover:text-foreground"
                onClick={() => handleSort('crm_system')}
              >
                <div className="flex items-center space-x-1">
                  <span>CRM System</span>
                  {sortField === 'crm_system' && (
                    <Icon name={sortDirection === 'asc' ? 'ArrowUp' : 'ArrowDown'} size={12} />
                  )}
                </div>
              </th>

              <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                Sales Cycle
              </th>

              <th
                className="text-left py-3 px-4 font-medium text-muted-foreground cursor-pointer hover:text-foreground"
                onClick={() => handleSort('actual_close_date')}
              >
                <div className="flex items-center space-x-1">
                  <span>Close Date</span>
                  {sortField === 'actual_close_date' && (
                    <Icon name={sortDirection === 'asc' ? 'ArrowUp' : 'ArrowDown'} size={12} />
                  )}
                </div>
              </th>

              <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                Attribution
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedRecords.map((record, index) => (
              <tr
                key={record.id || index}
                className={`border-b border-border last:border-b-0 hover:bg-muted/10 transition-colors cursor-pointer ${
                  record.outcome === 'closed_won' ? 'bg-success/5' :
                  record.outcome === 'closed_lost' ? 'bg-destructive/5' : ''
                }`}
                onClick={() => onRecordClick?.(record)}
              >
                <td className="py-3 px-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                      <Icon name="Building2" size={12} className="text-primary" />
                    </div>
                    <div>
                      <div className="font-medium text-foreground text-xs">
                        {record.company_name || 'Company'}
                      </div>
                      <code className="text-xs text-muted-foreground">
                        {record.company_unique_id}
                      </code>
                    </div>
                  </div>
                </td>

                <td className="py-3 px-4">
                  <div className="flex items-center space-x-2">
                    {getOutcomeIcon(record.outcome)}
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getOutcomeColor(record.outcome)}`}>
                      {record.outcome.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  </div>
                  {record.outcome_reason && (
                    <div className="text-xs text-muted-foreground mt-1">
                      {record.outcome_reason}
                    </div>
                  )}
                </td>

                <td className="py-3 px-4">
                  <div className="font-medium text-foreground">
                    {record.revenue_amount ? formatCurrency(record.revenue_amount) : '-'}
                  </div>
                  {record.lost_to_competitor && (
                    <div className="text-xs text-destructive mt-1">
                      Lost to: {record.lost_to_competitor}
                    </div>
                  )}
                </td>

                <td className="py-3 px-4">
                  <div className="flex items-center space-x-2">
                    <Icon name="Database" size={12} className="text-muted-foreground" />
                    <span className="text-sm">{record.crm_system}</span>
                  </div>
                  <code className="text-xs text-muted-foreground">{record.crm_record_id}</code>
                </td>

                <td className="py-3 px-4">
                  {record.sales_cycle_days ? (
                    <div className="text-sm">
                      {record.sales_cycle_days} days
                    </div>
                  ) : (
                    <span className="text-muted-foreground">-</span>
                  )}
                  {record.touchpoints_to_close && (
                    <div className="text-xs text-muted-foreground">
                      {record.touchpoints_to_close} touchpoints
                    </div>
                  )}
                </td>

                <td className="py-3 px-4">
                  <div className="text-sm">
                    {formatDate(record.actual_close_date)}
                  </div>
                  {record.expected_close_date && record.actual_close_date && (
                    <div className="text-xs text-muted-foreground">
                      Expected: {formatDate(record.expected_close_date)}
                    </div>
                  )}
                </td>

                <td className="py-3 px-4">
                  <div className="flex items-center space-x-1">
                    <span className="text-xs text-muted-foreground">
                      {record.attribution_model || 'first_touch'}
                    </span>
                    {record.attribution_confidence && (
                      <span className="text-xs text-info">
                        ({Math.round(record.attribution_confidence * 100)}%)
                      </span>
                    )}
                  </div>
                  {record.touchpoint_sequence && record.touchpoint_sequence.length > 0 && (
                    <div className="text-xs text-muted-foreground mt-1">
                      {record.touchpoint_sequence.slice(0, 3).join(' → ')}
                      {record.touchpoint_sequence.length > 3 && '...'}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Table Footer */}
      <div className="px-4 py-3 bg-muted/10 border-t border-border">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center space-x-4">
            <span>Showing {sortedRecords.length} of {records.length} records</span>
            {filterOutcome !== 'all' && (
              <span className="text-info">Filtered by outcome: {filterOutcome}</span>
            )}
            {filterCRM !== 'all' && (
              <span className="text-info">Filtered by CRM: {filterCRM}</span>
            )}
          </div>

          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <Icon name="CheckCircle" size={12} className="text-success" />
              <span>{records.filter(r => r.outcome === 'closed_won').length} won</span>
            </span>
            <span className="flex items-center space-x-1">
              <Icon name="XCircle" size={12} className="text-destructive" />
              <span>{records.filter(r => r.outcome === 'closed_lost').length} lost</span>
            </span>
            <span className="flex items-center space-x-1">
              <Icon name="DollarSign" size={12} className="text-warning" />
              <span>
                {formatCurrency(
                  records
                    .filter(r => r.outcome === 'closed_won')
                    .reduce((sum, r) => sum + (r.revenue_amount || 0), 0)
                )}
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AttributionResultsTable;