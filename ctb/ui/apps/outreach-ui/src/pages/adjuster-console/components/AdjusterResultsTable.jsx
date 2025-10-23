import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import Input from '../../../components/ui/Input';
import Select from '../../../components/ui/Select';
import { Checkbox } from '../../../components/ui/Checkbox';

const AdjusterResultsTable = ({ 
  data = [],
  isLoading = false,
  selectedRows = new Set(),
  onRowSelect,
  onRowAdjust,
  className = ''
}) => {
  const [editingRows, setEditingRows] = useState({});
  const [adjustmentValues, setAdjustmentValues] = useState({});

  const getStatusBadge = (promoted, adjusted = false) => {
    if (promoted) {
      return (
        <div className="inline-flex items-center space-x-1 px-2 py-1 bg-success/10 text-success rounded-full text-xs font-medium">
          <Icon name="Check" size={12} />
          <span>Promoted ✅</span>
        </div>
      );
    }
    
    if (adjusted) {
      return (
        <div className="inline-flex items-center space-x-1 px-2 py-1 bg-warning/10 text-warning rounded-full text-xs font-medium">
          <Icon name="Edit" size={12} />
          <span>Adjusted ⚠️</span>
        </div>
      );
    }
    
    return (
      <div className="inline-flex items-center space-x-1 px-2 py-1 bg-warning/10 text-warning rounded-full text-xs font-medium">
        <Icon name="Clock" size={12} />
        <span>Pending ⏳</span>
      </div>
    );
  };

  const formatErrors = (errors) => {
    if (!errors || errors?.length === 0) return '-';
    
    return (
      <div className="space-y-1">
        {errors?.map((error, index) => (
          <div key={index} className="text-xs bg-warning/10 text-warning px-2 py-1 rounded">
            {error?.replace(/_/g, ' ')?.replace(/\b\w/g, l => l?.toUpperCase())}
          </div>
        ))}
      </div>
    );
  };

  const handleEditToggle = (uniqueId) => {
    setEditingRows(prev => ({
      ...prev,
      [uniqueId]: !prev?.[uniqueId]
    }));
  };

  const handleAdjustmentChange = (uniqueId, field, value) => {
    setAdjustmentValues(prev => ({
      ...prev,
      [uniqueId]: {
        ...prev?.[uniqueId],
        [field]: value
      }
    }));
  };

  const handleSaveAdjustment = async (uniqueId) => {
    const adjustments = adjustmentValues?.[uniqueId] || {};
    await onRowAdjust?.(uniqueId, adjustments);
    setEditingRows(prev => ({ ...prev, [uniqueId]: false }));
    setAdjustmentValues(prev => ({ ...prev, [uniqueId]: {} }));
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      data?.forEach(record => {
        if (!record?.promoted) {
          onRowSelect?.(record?.unique_id, true);
        }
      });
    } else {
      data?.forEach(record => {
        onRowSelect?.(record?.unique_id, false);
      });
    }
  };

  const selectableRows = data?.filter(record => !record?.promoted) || [];
  const allSelectableSelected = selectableRows?.length > 0 && 
    selectableRows?.every(record => selectedRows?.has(record?.unique_id));

  if (isLoading) {
    return (
      <div className={`bg-card border border-border rounded-lg ${className}`}>
        <div className="p-8 text-center">
          <Icon name="Loader2" size={32} className="animate-spin mx-auto mb-4 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Loading adjustment results...</p>
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
            No adjustment data available. Please run validation first.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-card border border-border rounded-lg overflow-hidden ${className}`}>
      {/* Table Header */}
      <div className="px-4 py-3 bg-muted/20 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Icon name="Edit" size={16} color="var(--color-muted-foreground)" />
            <h3 className="text-sm font-medium text-foreground">Adjuster Results</h3>
            <span className="text-xs text-muted-foreground">({data?.length} records)</span>
          </div>
          
          {selectableRows?.length > 0 && (
            <div className="flex items-center space-x-2">
              <Checkbox
                checked={allSelectableSelected}
                onChange={handleSelectAll}
                id="select-all"
              />
              <label htmlFor="select-all" className="text-sm text-muted-foreground">
                Select All Pending
              </label>
            </div>
          )}
        </div>
      </div>
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/10 border-b border-border">
            <tr>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground w-12"></th>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">Company Name</th>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">Unique ID</th>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">Process ID</th>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">Status</th>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">Issues</th>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">Adjustment Notes</th>
              <th className="text-left py-3 px-4 font-medium text-muted-foreground">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((record, index) => {
              const isEditing = editingRows?.[record?.unique_id];
              const adjustments = adjustmentValues?.[record?.unique_id] || {};
              const canSelect = !record?.promoted;
              const isSelected = selectedRows?.has(record?.unique_id);
              
              return (
                <tr 
                  key={record?.unique_id || index} 
                  className={`
                    border-b border-border last:border-b-0 hover:bg-muted/10 transition-colors
                    ${record?.promoted ? 'bg-success/5' : record?.adjusted ? 'bg-warning/5' : 'bg-muted/5'}
                  `}
                >
                  <td className="py-3 px-4">
                    {canSelect && (
                      <Checkbox
                        checked={isSelected}
                        onChange={(checked) => onRowSelect?.(record?.unique_id, checked)}
                        id={`select-${record?.unique_id}`}
                      />
                    )}
                  </td>
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
                    {getStatusBadge(record?.promoted, record?.adjusted)}
                  </td>
                  <td className="py-3 px-4 max-w-xs">
                    {formatErrors(record?.errors)}
                  </td>
                  <td className="py-3 px-4 max-w-sm">
                    {isEditing ? (
                      <div className="space-y-2">
                        <Input
                          placeholder="Add adjustment note..."
                          value={adjustments?.note || ''}
                          onChange={(e) => handleAdjustmentChange(record?.unique_id, 'note', e?.target?.value)}
                          className="text-xs"
                        />
                      </div>
                    ) : (
                      <div className="text-xs text-muted-foreground">
                        {record?.adjustment_notes || 'No adjustments'}
                      </div>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    {!record?.promoted && (
                      <div className="flex space-x-2">
                        {isEditing ? (
                          <>
                            <Button
                              variant="default"
                              size="sm"
                              onClick={() => handleSaveAdjustment(record?.unique_id)}
                              disabled={!adjustments?.note}
                            >
                              Save
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleEditToggle(record?.unique_id)}
                            >
                              Cancel
                            </Button>
                          </>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            iconName="Edit"
                            onClick={() => handleEditToggle(record?.unique_id)}
                          >
                            Adjust
                          </Button>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {/* Table Footer */}
      <div className="px-4 py-3 bg-muted/10 border-t border-border">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Total records: {data?.length}</span>
          <span>
            Promoted: {data?.filter(r => r?.promoted)?.length} | 
            Pending: {data?.filter(r => !r?.promoted && !r?.adjusted)?.length} |
            Adjusted: {data?.filter(r => r?.adjusted)?.length}
          </span>
        </div>
      </div>
    </div>
  );
};

export default AdjusterResultsTable;