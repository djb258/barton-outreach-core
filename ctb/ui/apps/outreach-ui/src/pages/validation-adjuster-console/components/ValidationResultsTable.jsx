import React from 'react';
import Icon from '../../../components/AppIcon';

const ValidationResultsTable = ({ 
  data = [],
  isLoading = false,
  className = ''
}) => {
  const getStatusBadge = (validated) => {
    return validated ? (
      <div className="inline-flex items-center space-x-1 px-2 py-1 bg-success/10 text-success rounded-full text-xs font-medium">
        <Icon name="Check" size={12} />
        <span>Validated ✅</span>
      </div>
    ) : (
      <div className="inline-flex items-center space-x-1 px-2 py-1 bg-error/10 text-error rounded-full text-xs font-medium">
        <Icon name="X" size={12} />
        <span>Failed ❌</span>
      </div>
    );
  };

  const formatErrors = (errors) => {
    if (!errors || errors?.length === 0) return '-';
    
    return (
      <div className="space-y-1">
        {errors?.map((error, index) => (
          <div key={index} className="text-xs bg-error/10 text-error px-2 py-1 rounded">
            {error?.replace(/_/g, ' ')?.replace(/\b\w/g, l => l?.toUpperCase())}
          </div>
        ))}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className={`bg-card border border-border rounded-lg ${className}`}>
        <div className="p-8 text-center">
          <Icon name="Loader2" size={32} className="animate-spin mx-auto mb-4 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Loading validation results...</p>
        </div>
      </div>
    );
  }

  if (!data || data?.length === 0) {
    return (
      <div className={`bg-card border border-border rounded-lg ${className}`}>
        <div className="p-8 text-center">
          <Icon name="Database" size={32} className="mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-medium text-foreground mb-2">No Records Found</h3>
          <p className="text-sm text-muted-foreground">
            No validation data available. Please run validation first.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-card border border-border rounded-lg overflow-hidden ${className}`}>
      {/* Table Header */}
      <div className="px-4 py-3 bg-muted/20 border-b border-border">
        <div className="flex items-center space-x-2">
          <Icon name="Table" size={16} color="var(--color-muted-foreground)" />
          <h3 className="text-sm font-medium text-foreground">Validation Results</h3>
          <span className="text-xs text-muted-foreground">({data?.length} records)</span>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/10 border-b border-border">
            <tr>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">Company Name</th>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">Unique ID</th>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">Process ID</th>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">Status</th>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">Errors</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((record, index) => (
              <tr 
                key={record?.unique_id || index} 
                className={`
                  border-b border-border last:border-b-0 hover:bg-muted/10 transition-colors
                  ${record?.validated ? 'bg-success/5' : 'bg-error/5'}
                `}
              >
                <td className="py-3 px-4">
                  <div className="font-medium text-foreground">
                    {record?.company_name || 'Unknown Company'}
                  </div>
                </td>
                
                <td className="py-3 px-4">
                  <div className="font-mono text-xs text-muted-foreground">
                    {record?.unique_id || 'N/A'}
                  </div>
                </td>
                
                <td className="py-3 px-4">
                  <div className="font-mono text-xs text-muted-foreground">
                    {record?.process_id || 'N/A'}
                  </div>
                </td>
                
                <td className="py-3 px-4">
                  {getStatusBadge(record?.validated)}
                </td>
                
                <td className="py-3 px-4 max-w-xs">
                  {formatErrors(record?.errors)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Table Footer */}
      <div className="px-4 py-3 bg-muted/10 border-t border-border">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Total records: {data?.length}</span>
          <span>
            Valid: {data?.filter(r => r?.validated)?.length} | 
            Failed: {data?.filter(r => !r?.validated)?.length}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ValidationResultsTable;