import React from 'react';
import Icon from '../../../components/AppIcon';

const PromotionResultsTable = ({ results = [], isLoading = false, className = '' }) => {
  if (isLoading) {
    return (
      <div className={`p-8 text-center ${className}`}>
        <Icon name="Loader2" size={24} className="animate-spin mx-auto mb-4 text-muted-foreground" />
        <p className="text-muted-foreground">Loading promotion results...</p>
      </div>
    );
  }

  if (!results || results?.length === 0) {
    return (
      <div className={`p-8 text-center ${className}`}>
        <Icon name="Database" size={48} className="mx-auto mb-4 text-muted-foreground opacity-50" />
        <p className="text-muted-foreground">No promotion results available.</p>
        <p className="text-sm text-muted-foreground mt-2">
          Click "Promote Valid Records" to start the promotion process.
        </p>
      </div>
    );
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case "Promoted":
        return <Icon name="CheckCircle" size={16} className="text-success" />;
      case "Pending":
        return <Icon name="Clock" size={16} className="text-warning" />;
      case "Failed":
        return <Icon name="XCircle" size={16} className="text-destructive" />;
      default:
        return <Icon name="Circle" size={16} className="text-muted-foreground" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "Promoted":
        return "text-success bg-success/10";
      case "Pending":
        return "text-warning bg-warning/10";
      case "Failed":
        return "text-destructive bg-destructive/10";
      default:
        return "text-muted-foreground bg-muted";
    }
  };

  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="w-full">
        <thead className="bg-muted/50 border-b border-border">
          <tr>
            <th className="text-left p-4 text-sm font-semibold text-foreground">
              Company Name
            </th>
            <th className="text-left p-4 text-sm font-semibold text-foreground">
              Unique ID
            </th>
            <th className="text-left p-4 text-sm font-semibold text-foreground">
              Status
            </th>
            <th className="text-left p-4 text-sm font-semibold text-foreground">
              Errors
            </th>
          </tr>
        </thead>
        <tbody>
          {results?.map((row, idx) => (
            <tr 
              key={idx} 
              className="border-b border-border hover:bg-muted/30 transition-colors"
            >
              <td className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                    <Icon name="Building2" size={14} className="text-primary" />
                  </div>
                  <span className="font-medium text-foreground">
                    {row?.company_name || 'Unknown Company'}
                  </span>
                </div>
              </td>
              
              <td className="p-4">
                <code className="px-2 py-1 bg-muted rounded text-xs font-mono text-foreground">
                  {row?.unique_id}
                </code>
              </td>
              
              <td className="p-4">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(row?.promotion_status)}
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(row?.promotion_status)}`}>
                    {row?.promotion_status}
                  </span>
                </div>
              </td>
              
              <td className="p-4">
                {row?.errors && row?.errors?.length > 0 ? (
                  <div className="space-y-1">
                    {row?.errors?.map((error, errorIdx) => (
                      <div key={errorIdx} className="flex items-center space-x-2">
                        <Icon name="AlertTriangle" size={12} className="text-destructive shrink-0" />
                        <span className="text-xs text-destructive">{error}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="text-muted-foreground text-sm">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {/* Table Footer */}
      <div className="bg-muted/30 px-4 py-3 border-t border-border">
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>Total Records: {results?.length}</span>
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <Icon name="CheckCircle" size={12} className="text-success" />
              <span>{results?.filter(r => r?.promotion_status === "Promoted")?.length} promoted</span>
            </span>
            <span className="flex items-center space-x-1">
              <Icon name="Clock" size={12} className="text-warning" />
              <span>{results?.filter(r => r?.promotion_status === "Pending")?.length} pending</span>
            </span>
            <span className="flex items-center space-x-1">
              <Icon name="XCircle" size={12} className="text-destructive" />
              <span>{results?.filter(r => r?.promotion_status === "Failed")?.length} failed</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PromotionResultsTable;