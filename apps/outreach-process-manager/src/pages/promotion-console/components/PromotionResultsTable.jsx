import React from 'react';
import Icon from '../../../components/AppIcon';

const PromotionResultsTable = ({
  results = [],
  recordType = 'company',
  isLoading = false,
  className = ''
}) => {
  if (isLoading) {
    return (
      <div className={`p-8 text-center ${className}`}>
        <Icon name="Loader2" size={24} className="animate-spin mx-auto mb-4 text-muted-foreground" />
        <p className="text-muted-foreground">Loading promotion results...</p>
      </div>
    );
  }

  if (!results || results.length === 0) {
    return (
      <div className={`bg-card border border-border rounded-lg p-8 text-center ${className}`}>
        <Icon name="Database" size={48} className="mx-auto mb-4 text-muted-foreground opacity-50" />
        <h3 className="text-lg font-medium text-foreground mb-2">No Promotion Results</h3>
        <p className="text-sm text-muted-foreground">
          Execute a promotion batch to see detailed results for each {recordType} record.
        </p>
      </div>
    );
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <Icon name="CheckCircle" size={16} className="text-success" />;
      case 'failed':
        return <Icon name="XCircle" size={16} className="text-destructive" />;
      default:
        return <Icon name="Circle" size={16} className="text-muted-foreground" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
        return 'text-success bg-success/10';
      case 'failed':
        return 'text-destructive bg-destructive/10';
      default:
        return 'text-muted-foreground bg-muted';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'success':
        return 'Promoted';
      case 'failed':
        return 'Failed';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className={`bg-card border border-border rounded-lg overflow-hidden ${className}`}>
      {/* Table Header */}
      <div className="px-4 py-3 bg-muted/10 border-b border-border">
        <div className="flex items-center space-x-2">
          <Icon name="Upload" size={16} color="var(--color-muted-foreground)" />
          <h3 className="text-sm font-medium text-foreground">Promotion Results</h3>
          <span className="text-xs text-muted-foreground">({results.length} records)</span>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/10 border-b border-border">
            <tr>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                {recordType === 'company' ? 'Company' : 'Person'}
              </th>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                Barton ID
              </th>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                Promotion Status
              </th>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                Target Table
              </th>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                Audit Log ID
              </th>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                Error Details
              </th>
            </tr>
          </thead>
          <tbody>
            {results.map((result, index) => (
              <tr
                key={result.unique_id || index}
                className={`border-b border-border last:border-b-0 hover:bg-muted/10 transition-colors ${
                  result.status === 'success' ? 'bg-success/5' : result.status === 'failed' ? 'bg-destructive/5' : ''
                }`}
              >
                <td className="py-3 px-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                      <Icon
                        name={recordType === 'company' ? 'Building2' : 'User'}
                        size={14}
                        className="text-primary"
                      />
                    </div>
                    <span className="font-medium text-foreground">
                      {recordType === 'company' ? 'Company Record' : 'Person Record'}
                    </span>
                  </div>
                </td>

                <td className="py-3 px-4">
                  <code className="px-2 py-1 bg-muted rounded text-xs font-mono text-foreground">
                    {result.unique_id}
                  </code>
                </td>

                <td className="py-3 px-4">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(result.status)}
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(result.status)}`}>
                      {getStatusText(result.status)}
                    </span>
                  </div>
                </td>

                <td className="py-3 px-4">
                  <span className="text-xs text-muted-foreground font-mono">
                    {recordType === 'company' ? 'company_master' : 'people_master'}
                  </span>
                </td>

                <td className="py-3 px-4">
                  {result.audit_log_id ? (
                    <span className="text-xs text-muted-foreground font-mono">
                      #{result.audit_log_id}
                    </span>
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </td>

                <td className="py-3 px-4">
                  {result.error ? (
                    <div className="flex items-start space-x-2">
                      <Icon name="AlertTriangle" size={12} className="text-destructive shrink-0 mt-0.5" />
                      <span className="text-xs text-destructive">{result.error}</span>
                    </div>
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
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
          <span>Batch Results: {results.length} records processed</span>
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <Icon name="CheckCircle" size={12} className="text-success" />
              <span>{results.filter(r => r.status === 'success').length} promoted</span>
            </span>
            <span className="flex items-center space-x-1">
              <Icon name="XCircle" size={12} className="text-destructive" />
              <span>{results.filter(r => r.status === 'failed').length} failed</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PromotionResultsTable;