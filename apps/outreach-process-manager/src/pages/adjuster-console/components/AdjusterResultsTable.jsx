import React, { useState, useEffect } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import Input from '../../../components/ui/Input';
import { Checkbox } from '../../../components/ui/Checkbox';

const AdjusterResultsTable = ({
  records = [],
  recordType = 'company',
  isLoading = false,
  isSaving = false,
  selectedRecord = null,
  onRecordSelect,
  onSaveRecord,
  className = ''
}) => {
  const [editingRows, setEditingRows] = useState({});
  const [fieldValues, setFieldValues] = useState({});
  const [saveStatus, setSaveStatus] = useState({});

  // Initialize field values when records change
  useEffect(() => {
    const initialValues = {};
    records.forEach(record => {
      const uniqueId = recordType === 'company' ? record.company_unique_id : record.unique_id;
      initialValues[uniqueId] = { ...record };
    });
    setFieldValues(initialValues);
  }, [records, recordType]);

  const getStatusBadge = (validationStatus) => {
    switch (validationStatus) {
      case 'failed':
        return (
          <div className="inline-flex items-center space-x-1 px-2 py-1 bg-destructive/10 text-destructive rounded-full text-xs font-medium">
            <Icon name="AlertCircle" size={12} />
            <span>Failed</span>
          </div>
        );
      case 'pending':
        return (
          <div className="inline-flex items-center space-x-1 px-2 py-1 bg-warning/10 text-warning rounded-full text-xs font-medium">
            <Icon name="Clock" size={12} />
            <span>Re-validating</span>
          </div>
        );
      case 'passed':
        return (
          <div className="inline-flex items-center space-x-1 px-2 py-1 bg-success/10 text-success rounded-full text-xs font-medium">
            <Icon name="Check" size={12} />
            <span>Passed</span>
          </div>
        );
      default:
        return (
          <div className="inline-flex items-center space-x-1 px-2 py-1 bg-muted/10 text-muted-foreground rounded-full text-xs font-medium">
            <Icon name="HelpCircle" size={12} />
            <span>Unknown</span>
          </div>
        );
    }
  };

  const formatErrors = (errors) => {
    if (!errors || errors.length === 0) return '-';

    return (
      <div className="space-y-1 max-w-xs">
        {errors.slice(0, 3).map((error, index) => (
          <div key={index} className="text-xs bg-destructive/10 text-destructive px-2 py-1 rounded">
            {error.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </div>
        ))}
        {errors.length > 3 && (
          <div className="text-xs text-muted-foreground px-2">
            +{errors.length - 3} more
          </div>
        )}
      </div>
    );
  };

  const handleEditToggle = (uniqueId) => {
    setEditingRows(prev => ({
      ...prev,
      [uniqueId]: !prev[uniqueId]
    }));
  };

  const handleFieldChange = (uniqueId, field, value) => {
    setFieldValues(prev => ({
      ...prev,
      [uniqueId]: {
        ...prev[uniqueId],
        [field]: value
      }
    }));
  };

  const handleSaveRecord = async (uniqueId) => {
    const originalRecord = records.find(r => {
      const id = recordType === 'company' ? r.company_unique_id : r.unique_id;
      return id === uniqueId;
    });

    if (!originalRecord) return;

    const updatedFields = {};
    const currentValues = fieldValues[uniqueId] || {};

    // Compare current values with original record to find changes
    Object.keys(currentValues).forEach(field => {
      if (field.includes('unique_id') && field !== 'company_slot_unique_id') {
        // Skip Barton ID fields - they cannot be changed
        return;
      }

      if (currentValues[field] !== originalRecord[field]) {
        updatedFields[field] = currentValues[field];
      }
    });

    if (Object.keys(updatedFields).length === 0) {
      setSaveStatus(prev => ({
        ...prev,
        [uniqueId]: { type: 'info', message: 'No changes detected' }
      }));
      setEditingRows(prev => ({ ...prev, [uniqueId]: false }));
      return;
    }

    try {
      const result = await onSaveRecord(uniqueId, updatedFields);

      setSaveStatus(prev => ({
        ...prev,
        [uniqueId]: {
          type: result.success ? 'success' : 'error',
          message: result.message
        }
      }));

      if (result.success) {
        setEditingRows(prev => ({ ...prev, [uniqueId]: false }));
      }

      // Clear status after 3 seconds
      setTimeout(() => {
        setSaveStatus(prev => {
          const newStatus = { ...prev };
          delete newStatus[uniqueId];
          return newStatus;
        });
      }, 3000);

    } catch (error) {
      setSaveStatus(prev => ({
        ...prev,
        [uniqueId]: { type: 'error', message: 'Failed to save record' }
      }));
    }
  };

  // Get editable fields for the current record type
  const getEditableFields = (record) => {
    if (recordType === 'company') {
      return [
        { key: 'company_name', label: 'Company Name', type: 'text' },
        { key: 'website_url', label: 'Website URL', type: 'url' },
        { key: 'industry', label: 'Industry', type: 'text' },
        { key: 'employee_count', label: 'Employee Count', type: 'number' },
        { key: 'company_phone', label: 'Phone', type: 'tel' },
        { key: 'address_street', label: 'Street Address', type: 'text' },
        { key: 'address_city', label: 'City', type: 'text' },
        { key: 'address_state', label: 'State', type: 'text' },
        { key: 'address_zip', label: 'ZIP Code', type: 'text' },
        { key: 'address_country', label: 'Country', type: 'text' },
        { key: 'linkedin_url', label: 'LinkedIn URL', type: 'url' }
      ];
    } else {
      return [
        { key: 'first_name', label: 'First Name', type: 'text' },
        { key: 'last_name', label: 'Last Name', type: 'text' },
        { key: 'title', label: 'Title', type: 'text' },
        { key: 'seniority', label: 'Seniority', type: 'text' },
        { key: 'department', label: 'Department', type: 'text' },
        { key: 'email', label: 'Email', type: 'email' },
        { key: 'work_phone_e164', label: 'Work Phone', type: 'tel' },
        { key: 'personal_phone_e164', label: 'Personal Phone', type: 'tel' },
        { key: 'linkedin_url', label: 'LinkedIn URL', type: 'url' }
      ];
    }
  };

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

  if (!records || records.length === 0) {
    return (
      <div className={`bg-card border border-border rounded-lg ${className}`}>
        <div className="p-8 text-center">
          <Icon name="CheckCircle" size={32} className="mx-auto mb-4 text-success" />
          <h3 className="text-lg font-medium text-foreground mb-2">All Clear!</h3>
          <p className="text-sm text-muted-foreground">
            No {recordType} records require manual adjustment.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {records.map((record, index) => {
        const uniqueId = recordType === 'company' ? record.company_unique_id : record.unique_id;
        const isEditing = editingRows[uniqueId];
        const editableFields = getEditableFields(record);
        const currentValues = fieldValues[uniqueId] || record;
        const status = saveStatus[uniqueId];

        return (
          <div
            key={uniqueId || index}
            className="bg-card border border-border rounded-lg overflow-hidden"
          >
            {/* Record Header */}
            <div className="px-4 py-3 bg-muted/10 border-b border-border">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div>
                    <h4 className="font-medium text-foreground">
                      {recordType === 'company'
                        ? record.company_name || 'Unknown Company'
                        : `${record.first_name || ''} ${record.last_name || ''}`.trim() || 'Unknown Person'
                      }
                    </h4>
                    <div className="text-xs text-muted-foreground font-mono">{uniqueId}</div>
                  </div>
                  {getStatusBadge(record.validation_status)}
                </div>

                <div className="flex items-center space-x-2">
                  {!isEditing ? (
                    <Button
                      variant="outline"
                      size="sm"
                      iconName="Edit"
                      onClick={() => handleEditToggle(uniqueId)}
                      disabled={isSaving}
                    >
                      Edit Fields
                    </Button>
                  ) : (
                    <div className="flex space-x-2">
                      <Button
                        variant="default"
                        size="sm"
                        iconName="Save"
                        onClick={() => handleSaveRecord(uniqueId)}
                        disabled={isSaving}
                      >
                        {isSaving ? 'Saving...' : 'Save Changes'}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEditToggle(uniqueId)}
                        disabled={isSaving}
                      >
                        Cancel
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </div>
            {/* Record Content */}
            <div className="p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Validation Errors */}
                <div>
                  <h5 className="text-sm font-medium text-foreground mb-2">Validation Issues</h5>
                  {record.validation_failures && record.validation_failures.length > 0 ? (
                    <div className="space-y-2">
                      {record.validation_failures.slice(0, 3).map((failure, idx) => (
                        <div key={idx} className="bg-destructive/10 border border-destructive/20 rounded p-2">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="text-xs font-medium text-destructive mb-1">
                                {failure.error_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                              </div>
                              <div className="text-xs text-muted-foreground">
                                Field: <span className="font-mono">{failure.error_field}</span>
                              </div>
                              {failure.raw_value && (
                                <div className="text-xs text-muted-foreground mt-1">
                                  Current: <span className="font-mono bg-muted/20 px-1 rounded">{failure.raw_value}</span>
                                </div>
                              )}
                              {failure.expected_format && (
                                <div className="text-xs text-muted-foreground">
                                  Expected: {failure.expected_format}
                                </div>
                              )}
                            </div>
                            <div className="ml-2">
                              <div className={`text-xs px-2 py-1 rounded ${
                                failure.status === 'pending' ? 'bg-warning/20 text-warning' :
                                failure.status === 'fixed' ? 'bg-success/20 text-success' :
                                'bg-muted/20 text-muted-foreground'
                              }`}>
                                {failure.status}
                              </div>
                            </div>
                          </div>
                          {failure.attempts > 0 && (
                            <div className="text-xs text-muted-foreground mt-1">
                              {failure.attempts} attempt(s) by {failure.last_attempt_source || 'unknown'}
                            </div>
                          )}
                        </div>
                      ))}
                      {record.validation_failures.length > 3 && (
                        <div className="text-xs text-muted-foreground px-2">
                          +{record.validation_failures.length - 3} more validation issues
                        </div>
                      )}
                    </div>
                  ) : (
                    formatErrors(record.errors)
                  )}
                </div>

                {/* Enrichment Attempts */}
                <div>
                  <h5 className="text-sm font-medium text-foreground mb-2">Enrichment History</h5>
                  {record.enrichment_attempts && record.enrichment_attempts.length > 0 ? (
                    <div className="space-y-1">
                      {record.enrichment_attempts.slice(0, 2).map((attempt, idx) => (
                        <div key={idx} className="text-xs bg-muted/20 px-2 py-1 rounded">
                          <span className={`font-medium ${
                            attempt.status === 'success' ? 'text-success' :
                            attempt.status === 'failed' ? 'text-destructive' : 'text-warning'
                          }`}>
                            {attempt.status.toUpperCase()}
                          </span>
                          {' '}- {attempt.source} ({new Date(attempt.created_at).toLocaleDateString()})
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs text-muted-foreground">No enrichment attempts</div>
                  )}
                </div>
              </div>

              {/* Editable Fields */}
              {isEditing && (
                <div className="mt-6">
                  <h5 className="text-sm font-medium text-foreground mb-3">Edit Fields</h5>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {editableFields.map((field) => (
                      <div key={field.key}>
                        <label className="block text-xs font-medium text-muted-foreground mb-1">
                          {field.label}
                        </label>
                        <Input
                          type={field.type}
                          value={currentValues[field.key] || ''}
                          onChange={(e) => handleFieldChange(uniqueId, field.key, e.target.value)}
                          placeholder={`Enter ${field.label.toLowerCase()}`}
                          className="text-sm"
                          disabled={isSaving}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Save Status */}
              {status && (
                <div className={`mt-3 p-2 rounded text-xs ${
                  status.type === 'success' ? 'bg-success/10 text-success' :
                  status.type === 'error' ? 'bg-destructive/10 text-destructive' :
                  'bg-info/10 text-info'
                }`}>
                  <div className="flex items-center space-x-1">
                    <Icon
                      name={status.type === 'success' ? 'Check' : status.type === 'error' ? 'AlertCircle' : 'Info'}
                      size={12}
                    />
                    <span>{status.message}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        );
      })}

      {/* Summary Footer */}
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            Showing {records.length} {recordType} records requiring adjustment
          </span>
          <div className="flex items-center space-x-4 text-xs text-muted-foreground">
            <span>Failed: {records.filter(r => r.validation_status === 'failed').length}</span>
            <span>Re-validating: {records.filter(r => r.validation_status === 'pending').length}</span>
            <span>Passed: {records.filter(r => r.validation_status === 'passed').length}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdjusterResultsTable;