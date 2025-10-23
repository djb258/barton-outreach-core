import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import Input from '../../../components/ui/Input';
import Select from '../../../components/ui/Select';
import { Checkbox } from '../../../components/ui/Checkbox';

const ValidationFilterToolbar = ({ onFilterChange, onSaveProfile, onLoadProfile }) => {
  const [activeFilters, setActiveFilters] = useState({
    ruleTypes: [],
    severityLevels: [],
    dataSource: '',
    validationStatus: '',
    dateRange: '',
    searchQuery: ''
  });
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [savedProfiles, setSavedProfiles] = useState([
    { id: 'critical-only', name: 'Critical Issues Only', filters: { severityLevels: ['critical'] } },
    { id: 'failed-records', name: 'Failed Records', filters: { validationStatus: 'failed' } },
    { id: 'recent-uploads', name: 'Recent Uploads', filters: { dateRange: 'today' } }
  ]);

  const ruleTypeOptions = [
    { value: 'data-quality', label: 'Data Quality' },
    { value: 'business-rules', label: 'Business Rules' },
    { value: 'compliance', label: 'Compliance' },
    { value: 'custom', label: 'Custom Rules' }
  ];

  const severityOptions = [
    { value: 'critical', label: 'Critical' },
    { value: 'warning', label: 'Warning' },
    { value: 'info', label: 'Info' }
  ];

  const statusOptions = [
    { value: 'passed', label: 'Passed' },
    { value: 'warning', label: 'Warning' },
    { value: 'failed', label: 'Failed' },
    { value: 'pending', label: 'Pending' }
  ];

  const dataSourceOptions = [
    { value: 'csv-upload', label: 'CSV Upload' },
    { value: 'api-import', label: 'API Import' },
    { value: 'manual-entry', label: 'Manual Entry' },
    { value: 'bulk-import', label: 'Bulk Import' }
  ];

  const dateRangeOptions = [
    { value: 'today', label: 'Today' },
    { value: 'yesterday', label: 'Yesterday' },
    { value: 'last-7-days', label: 'Last 7 Days' },
    { value: 'last-30-days', label: 'Last 30 Days' },
    { value: 'custom', label: 'Custom Range' }
  ];

  const handleFilterChange = (filterType, value) => {
    const newFilters = { ...activeFilters, [filterType]: value };
    setActiveFilters(newFilters);
    onFilterChange?.(newFilters);
  };

  const handleMultiSelectChange = (filterType, value, checked) => {
    const currentValues = activeFilters?.[filterType] || [];
    const newValues = checked 
      ? [...currentValues, value]
      : currentValues?.filter(v => v !== value);
    
    handleFilterChange(filterType, newValues);
  };

  const clearAllFilters = () => {
    const clearedFilters = {
      ruleTypes: [],
      severityLevels: [],
      dataSource: '',
      validationStatus: '',
      dateRange: '',
      searchQuery: ''
    };
    setActiveFilters(clearedFilters);
    onFilterChange?.(clearedFilters);
  };

  const getActiveFilterCount = () => {
    return Object.values(activeFilters)?.filter(value => 
      Array.isArray(value) ? value?.length > 0 : value !== ''
    )?.length;
  };

  const loadProfile = (profile) => {
    setActiveFilters(profile?.filters);
    onFilterChange?.(profile?.filters);
    onLoadProfile?.(profile);
  };

  return (
    <div className="bg-card border-b border-border">
      {/* Main Filter Bar */}
      <div className="p-4">
        <div className="flex items-center space-x-4 mb-3">
          {/* Search */}
          <div className="flex-1 max-w-md">
            <Input
              type="search"
              placeholder="Search companies, emails, domains..."
              value={activeFilters?.searchQuery}
              onChange={(e) => handleFilterChange('searchQuery', e?.target?.value)}
              className="text-sm"
            />
          </div>

          {/* Quick Filters */}
          <Select
            placeholder="Validation Status"
            options={statusOptions}
            value={activeFilters?.validationStatus}
            onChange={(value) => handleFilterChange('validationStatus', value)}
            clearable
            className="w-40"
          />

          <Select
            placeholder="Data Source"
            options={dataSourceOptions}
            value={activeFilters?.dataSource}
            onChange={(value) => handleFilterChange('dataSource', value)}
            clearable
            className="w-40"
          />

          <Select
            placeholder="Date Range"
            options={dateRangeOptions}
            value={activeFilters?.dateRange}
            onChange={(value) => handleFilterChange('dateRange', value)}
            clearable
            className="w-40"
          />

          {/* Advanced Filters Toggle */}
          <Button
            variant="outline"
            size="sm"
            iconName="Filter"
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
          >
            Advanced
            {getActiveFilterCount() > 0 && (
              <span className="ml-1 px-1.5 py-0.5 bg-accent text-accent-foreground rounded text-xs">
                {getActiveFilterCount()}
              </span>
            )}
          </Button>

          {/* Clear Filters */}
          {getActiveFilterCount() > 0 && (
            <Button
              variant="ghost"
              size="sm"
              iconName="X"
              onClick={clearAllFilters}
            >
              Clear
            </Button>
          )}
        </div>

        {/* Saved Profiles */}
        <div className="flex items-center space-x-2">
          <span className="text-sm text-muted-foreground">Quick Profiles:</span>
          {savedProfiles?.map((profile) => (
            <Button
              key={profile?.id}
              variant="ghost"
              size="sm"
              onClick={() => loadProfile(profile)}
              className="text-xs"
            >
              {profile?.name}
            </Button>
          ))}
          <Button
            variant="outline"
            size="sm"
            iconName="Save"
            onClick={() => onSaveProfile?.(activeFilters)}
            className="text-xs"
          >
            Save Current
          </Button>
        </div>
      </div>
      {/* Advanced Filters Panel */}
      {showAdvancedFilters && (
        <div className="px-4 pb-4 border-t border-border bg-muted/20">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
            {/* Rule Types */}
            <div>
              <label className="text-sm font-medium text-foreground mb-2 block">
                Rule Types
              </label>
              <div className="space-y-2">
                {ruleTypeOptions?.map((option) => (
                  <Checkbox
                    key={option?.value}
                    label={option?.label}
                    checked={activeFilters?.ruleTypes?.includes(option?.value)}
                    onChange={(e) => handleMultiSelectChange('ruleTypes', option?.value, e?.target?.checked)}
                    size="sm"
                  />
                ))}
              </div>
            </div>

            {/* Severity Levels */}
            <div>
              <label className="text-sm font-medium text-foreground mb-2 block">
                Severity Levels
              </label>
              <div className="space-y-2">
                {severityOptions?.map((option) => (
                  <Checkbox
                    key={option?.value}
                    label={option?.label}
                    checked={activeFilters?.severityLevels?.includes(option?.value)}
                    onChange={(e) => handleMultiSelectChange('severityLevels', option?.value, e?.target?.checked)}
                    size="sm"
                  />
                ))}
              </div>
            </div>

            {/* Advanced Search */}
            <div>
              <label className="text-sm font-medium text-foreground mb-2 block">
                Advanced Search
              </label>
              <div className="space-y-2">
                <Input
                  placeholder="Company name contains..."
                  className="text-sm"
                />
                <Input
                  placeholder="Email domain equals..."
                  className="text-sm"
                />
                <Input
                  placeholder="Employee count range..."
                  className="text-sm"
                />
              </div>
            </div>
          </div>

          {/* Field-Specific Operators */}
          <div className="mt-4 p-3 bg-card border border-border rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <Icon name="Search" size={14} color="var(--color-muted-foreground)" />
              <span className="text-sm font-medium text-foreground">Complex Query Builder</span>
            </div>
            <div className="text-xs text-muted-foreground mb-2">
              Use operators: = (equals), != (not equals), &gt; (greater than), &lt; (less than), CONTAINS, STARTS_WITH
            </div>
            <textarea
              placeholder="Example: company_name CONTAINS 'Tech' AND employee_count > 100 AND validation_score < 80"
              className="w-full h-16 px-3 py-2 text-xs font-data bg-input border border-border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <div className="flex justify-end mt-2">
              <Button variant="outline" size="sm" iconName="Play">
                Apply Query
              </Button>
            </div>
          </div>
        </div>
      )}
      {/* Active Filters Summary */}
      {getActiveFilterCount() > 0 && (
        <div className="px-4 py-2 bg-accent/5 border-t border-border">
          <div className="flex items-center space-x-2 text-sm">
            <Icon name="Filter" size={14} color="var(--color-accent)" />
            <span className="text-accent font-medium">Active Filters:</span>
            <div className="flex flex-wrap gap-1">
              {activeFilters?.validationStatus && (
                <span className="px-2 py-1 bg-accent/10 text-accent rounded text-xs">
                  Status: {activeFilters?.validationStatus}
                </span>
              )}
              {activeFilters?.dataSource && (
                <span className="px-2 py-1 bg-accent/10 text-accent rounded text-xs">
                  Source: {activeFilters?.dataSource}
                </span>
              )}
              {activeFilters?.dateRange && (
                <span className="px-2 py-1 bg-accent/10 text-accent rounded text-xs">
                  Date: {activeFilters?.dateRange}
                </span>
              )}
              {activeFilters?.ruleTypes?.length > 0 && (
                <span className="px-2 py-1 bg-accent/10 text-accent rounded text-xs">
                  Rules: {activeFilters?.ruleTypes?.length} selected
                </span>
              )}
              {activeFilters?.severityLevels?.length > 0 && (
                <span className="px-2 py-1 bg-accent/10 text-accent rounded text-xs">
                  Severity: {activeFilters?.severityLevels?.length} selected
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ValidationFilterToolbar;