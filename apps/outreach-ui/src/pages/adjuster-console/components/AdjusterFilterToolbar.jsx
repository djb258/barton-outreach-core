import React from 'react';
import Select from '../../../components/ui/Select';
import Icon from '../../../components/AppIcon';

const AdjusterFilterToolbar = ({ 
  currentFilter = 'all',
  onFilterChange,
  totalCount = 0,
  promotedCount = 0,
  pendingCount = 0,
  adjustedCount = 0,
  className = ''
}) => {
  const filterOptions = [
    { 
      value: 'all', 
      label: `All (${totalCount})`,
      icon: 'List',
      count: totalCount
    },
    { 
      value: 'promoted', 
      label: `Promoted (${promotedCount})`,
      icon: 'CheckCircle',
      count: promotedCount
    },
    { 
      value: 'pending', 
      label: `Pending (${pendingCount})`,
      icon: 'Clock', 
      count: pendingCount
    },
    { 
      value: 'adjusted', 
      label: `Adjusted (${adjustedCount})`,
      icon: 'Edit', 
      count: adjustedCount
    }
  ];

  const getFilterStats = () => {
    switch (currentFilter) {
      case 'promoted':
        return { count: promotedCount, status: 'Promoted ✅' };
      case 'pending':
        return { count: pendingCount, status: 'Pending ⏳' };
      case 'adjusted':
        return { count: adjustedCount, status: 'Adjusted ⚠️' };
      default:
        return { count: totalCount, status: 'All Records' };
    }
  };

  const stats = getFilterStats();

  return (
    <div className={`bg-card border border-border rounded-lg p-4 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Icon name="Filter" size={16} color="var(--color-muted-foreground)" />
            <span className="text-sm font-medium text-foreground">Filter Results:</span>
          </div>
          
          <Select
            value={currentFilter}
            onValueChange={onFilterChange}
            options={filterOptions}
            placeholder="Select filter"
            className="w-48"
          />
        </div>

        <div className="flex items-center space-x-6">
          {/* Current Filter Stats */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">Showing:</span>
            <span className="text-sm font-medium text-foreground">
              {stats?.count} {stats?.status}
            </span>
          </div>

          {/* Quick Stats */}
          <div className="flex items-center space-x-4 text-xs">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-success rounded-full"></div>
              <span className="text-muted-foreground">Promoted: {promotedCount}</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-warning rounded-full"></div>
              <span className="text-muted-foreground">Pending: {pendingCount}</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-info rounded-full"></div>
              <span className="text-muted-foreground">Adjusted: {adjustedCount}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdjusterFilterToolbar;