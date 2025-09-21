import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../../components/ui/Header';
import SystemHealthIndicator from '../../components/ui/SystemHealthIndicator';
import FileUploadZone from './components/FileUploadZone';
import DataPreviewTable from './components/DataPreviewTable';
import WorkflowSidebar from './components/WorkflowSidebar';
import ProcessingStatusPanel from './components/ProcessingStatusPanel';
import IntegrationStatusIndicator from './components/IntegrationStatusIndicator';
import Button from '../../components/ui/Button';
import { MASTER_SCHEMA, getAutoMappingSuggestions } from '../../constants/masterSchema';
import Icon from '../../components/AppIcon';

// Add SCHEMA_CATEGORIES constant
const SCHEMA_CATEGORIES = {
  company: { label: 'Company', icon: 'Building', color: 'blue' },
  contact: { label: 'Contact', icon: 'User', color: 'green' },
  financial: { label: 'Financial', icon: 'DollarSign', color: 'yellow' },
  location: { label: 'Location', icon: 'MapPin', color: 'red' },
  social: { label: 'Social', icon: 'Share', color: 'purple' },
  technology: { label: 'Technology', icon: 'Code', color: 'indigo' },
  industry: { label: 'Industry', icon: 'Briefcase', color: 'orange' },
  metrics: { label: 'Metrics', icon: 'BarChart', color: 'teal' },
  dates: { label: 'Dates', icon: 'Calendar', color: 'pink' },
  sources: { label: 'Sources', icon: 'Database', color: 'gray' },
  custom: { label: 'Custom', icon: 'Settings', color: 'cyan' },
  validation: { label: 'Validation', icon: 'CheckCircle', color: 'emerald' }
};

const DataIntakeDashboard = () => {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileData, setFileData] = useState(null);
  const [columnMapping, setColumnMapping] = useState({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingResults, setProcessingResults] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);
  const [schemaValidation, setSchemaValidation] = useState({});

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e?.ctrlKey || e?.metaKey) {
        switch (e?.key) {
          case 'u':
            e?.preventDefault();
            document.getElementById('file-upload')?.click();
            break;
          case 'ArrowRight':
            e?.preventDefault();
            if (processingResults && processingResults?.successfulRows > 0) {
              handleNextStep();
            }
            break;
        }
      }
      
      if (e?.key === 'Enter' && fileData && Object.keys(columnMapping)?.length > 0) {
        e?.preventDefault();
        handleIngestData();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [fileData, columnMapping, processingResults]);

  const handleFileSelect = useCallback((file) => {
    setSelectedFile(file);
    setProcessingResults(null);
    setValidationErrors([]);
    setSchemaValidation({});
    
    // Parse CSV file
    const reader = new FileReader();
    reader.onload = (e) => {
      const csv = e?.target?.result;
      const lines = csv?.split('\n');
      const headers = lines?.[0]?.split(',')?.map(h => h?.trim()?.replace(/"/g, ''));
      
      const data = lines?.slice(1)?.filter(line => line?.trim())?.map(line => {
          const values = line?.split(',')?.map(v => v?.trim()?.replace(/"/g, ''));
          const row = {};
          headers?.forEach((header, index) => {
            row[header] = values?.[index] || '';
          });
          return row;
        });
      
      setFileData(data);
      
      // Enhanced auto-detect column mappings using master schema
      const autoMapping = {};
      headers?.forEach(header => {
        const suggestion = getAutoMappingSuggestions(header);
        if (suggestion && !Object.values(autoMapping)?.includes(suggestion)) {
          autoMapping[header] = suggestion;
        }
      });
      setColumnMapping(autoMapping);

      // Validate against master schema
      validateAgainstMasterSchema(data, autoMapping);
    };
    reader?.readAsText(file);
  }, []);

  // New validation function for master schema
  const validateAgainstMasterSchema = useCallback((data, mapping) => {
    const errors = [];
    const requiredFields = MASTER_SCHEMA?.filter(field => field?.required);
    
    // Check for missing required fields
    requiredFields?.forEach(field => {
      const isMapped = Object.values(mapping)?.includes(field?.value);
      if (!isMapped) {
        errors?.push({
          type: 'missing_required_field',
          field: field?.value,
          label: field?.label,
          message: `Required field "${field?.label}" is not mapped`,
          severity: 'error'
        });
      }
    });
    
    // Validate data types and formats
    data?.slice(0, 100)?.forEach((row, rowIndex) => {
      Object.entries(mapping)?.forEach(([csvColumn, schemaField]) => {
        const field = MASTER_SCHEMA?.find(f => f?.value === schemaField);
        const value = row?.[csvColumn];
        
        if (field && value) {
          let isValid = true;
          let errorMessage = '';
          
          switch (field?.type) {
            case 'url':
              isValid = /^https?:\/\//?.test(value);
              errorMessage = 'Invalid URL format';
              break;
            case 'phone':
              isValid = /^[\+]?[\d\s\-\(\)]+$/?.test(value);
              errorMessage = 'Invalid phone format';
              break;
            case 'number':
              isValid = /^\d+$/?.test(value);
              errorMessage = 'Must be a number';
              break;
            case 'currency':
              isValid = /^[\$]?[\d,]+\.?\d*$/?.test(value);
              errorMessage = 'Invalid currency format';
              break;
            case 'date':
              isValid = /^\d{4}-\d{2}-\d{2}/?.test(value);
              errorMessage = 'Invalid date format (use YYYY-MM-DD)';
              break;
          }
          
          if (!isValid) {
            errors?.push({
              type: 'invalid_format',
              row: rowIndex + 1,
              column: csvColumn,
              field: schemaField,
              value: value,
              message: errorMessage,
              severity: field?.required ? 'error' : 'warning'
            });
          }
        }
      });
    });
    
    setSchemaValidation({
      isValid: !errors?.some(e => e?.severity === 'error'),
      errors: errors,
      totalErrors: errors?.filter(e => e?.severity === 'error')?.length,
      totalWarnings: errors?.filter(e => e?.severity === 'warning')?.length
    });
  }, []);

  const handleIngestData = useCallback(async () => {
    if (!fileData || Object.keys(columnMapping)?.length === 0) return;
    
    setIsProcessing(true);
    
    // Re-validate before processing
    validateAgainstMasterSchema(fileData, columnMapping);
    
    // Simulate processing with realistic delay and enhanced results
    setTimeout(() => {
      const mappedFieldsCount = Object.values(columnMapping)?.filter(Boolean)?.length;
      const totalSchemaFields = MASTER_SCHEMA?.length;
      const completenessScore = (mappedFieldsCount / totalSchemaFields * 100)?.toFixed(1);
      
      const mockResults = {
        totalRows: fileData?.length,
        successfulRows: Math.floor(fileData?.length * 0.95),
        failedRows: Math.ceil(fileData?.length * 0.05),
        schemaCompleteness: completenessScore,
        mappedFields: mappedFieldsCount,
        totalSchemaFields: totalSchemaFields,
        validationErrors: schemaValidation?.errors?.slice(0, 10) || [],
        processingTime: '3.7s',
        uniqueId: `WF-2025-001-BATCH-${Date.now()}`,
        timestamp: new Date()?.toISOString(),
        masterSchemaCompliance: schemaValidation?.isValid || false
      };
      
      setProcessingResults(mockResults);
      setIsProcessing(false);
    }, 4000);
  }, [fileData, columnMapping, schemaValidation]);

  const handleExportSchemaTemplate = useCallback(() => {
    const csvContent = [
      MASTER_SCHEMA?.map(field => field?.label)?.join(','),
      MASTER_SCHEMA?.map(field => `"${field?.description}"`)?.join(','),
      MASTER_SCHEMA?.map(field => field?.required ? 'Required' : 'Optional')?.join(',')
    ]?.join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `master-schema-template-${Date.now()}.csv`;
    a?.click();
    URL.revokeObjectURL(url);
  }, []);

  const handleExportErrors = useCallback(() => {
    if (!processingResults?.validationErrors) return;
    
    const csvContent = [
      'Row,Column,Value,Error,Severity',
      ...processingResults?.validationErrors?.map(error => 
        `${error?.row},"${error?.column}","${error?.value}","${error?.error}",${error?.severity}`
      )
    ]?.join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `validation-errors-${Date.now()}.csv`;
    a?.click();
    URL.revokeObjectURL(url);
  }, [processingResults]);

  const handlePromoteRecords = useCallback(() => {
    // Simulate promoting valid records
    alert(`Promoting ${processingResults?.successfulRows} valid records to next workflow step.`);
  }, [processingResults]);

  const handleNextStep = useCallback(() => {
    navigate('/data-validation-console');
  }, [navigate]);

  const canProceed = processingResults && processingResults?.successfulRows > 0 && 
                    (schemaValidation?.isValid || schemaValidation?.totalErrors === 0);

  return (
    <div className="min-h-screen bg-background">
      <Header />
      {/* Main Content */}
      <div className="flex pt-16">
        {/* Main Dashboard Area */}
        <div className="flex-1 p-6 pr-0">
          {/* Top Bar */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-semibold text-foreground">Outreach Process Data Ingestor</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Upload CSV files and map to master schema with 37 standardized fields for company prospect data
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                iconName="Download"
                iconPosition="left"
                onClick={handleExportSchemaTemplate}
              >
                Schema Template
              </Button>
              <IntegrationStatusIndicator />
              <SystemHealthIndicator />
            </div>
          </div>

          {/* Schema Overview */}
          {!fileData && (
            <div className="mb-8 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6">
              <div className="flex items-start space-x-4">
                <Icon name="Database" size={24} className="text-blue-600 mt-1" />
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Master Schema Overview</h3>
                  <p className="text-sm text-gray-700 mb-4">
                    Our master schema includes {MASTER_SCHEMA?.length} standardized fields across 12 categories for comprehensive company data management.
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
                    {Object.entries(SCHEMA_CATEGORIES)?.map(([key, category]) => (
                      <div key={key} className="flex items-center space-x-2 text-xs">
                        <Icon name={category?.icon} size={14} className={`text-${category?.color}-600`} />
                        <span className="text-gray-700">{category?.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Upload Section */}
          <div className="mb-8">
            <FileUploadZone 
              onFileSelect={handleFileSelect}
              isProcessing={isProcessing}
            />
          </div>

          {/* Schema Validation Summary */}
          {schemaValidation?.errors?.length > 0 && (
            <div className="mb-8">
              <div className={`p-4 rounded-lg border ${schemaValidation?.isValid ? 'bg-yellow-50 border-yellow-200' : 'bg-red-50 border-red-200'}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Icon 
                      name={schemaValidation?.isValid ? 'AlertTriangle' : 'XCircle'} 
                      size={20} 
                      className={schemaValidation?.isValid ? 'text-yellow-600' : 'text-red-600'}
                    />
                    <div>
                      <h4 className="font-medium text-gray-900">Schema Validation Results</h4>
                      <p className="text-sm text-gray-600">
                        {schemaValidation?.totalErrors} errors, {schemaValidation?.totalWarnings} warnings
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    iconName="Download"
                    iconPosition="left"
                    onClick={() => {
                      const csvContent = [
                        'Type,Field,Row,Column,Value,Message,Severity',
                        ...schemaValidation?.errors?.map(error => 
                          `${error?.type},"${error?.field || ''}",${error?.row || ''},"${error?.column || ''}","${error?.value || ''}","${error?.message}",${error?.severity}`
                        )
                      ]?.join('\n');
                      const blob = new Blob([csvContent], { type: 'text/csv' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `schema-validation-errors-${Date.now()}.csv`;
                      a?.click();
                      URL.revokeObjectURL(url);
                    }}
                  >
                    Export Issues
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Data Preview Section */}
          {fileData && (
            <div className="mb-8">
              <DataPreviewTable
                fileData={fileData}
                onColumnMapping={setColumnMapping}
                columnMapping={columnMapping}
                validationErrors={validationErrors}
              />
            </div>
          )}

          {/* Action Buttons */}
          {fileData && Object.keys(columnMapping)?.length > 0 && (
            <div className="mb-8">
              <div className="flex items-center justify-center space-x-4">
                <Button
                  variant="outline"
                  iconName="RotateCcw"
                  iconPosition="left"
                  onClick={() => {
                    setSelectedFile(null);
                    setFileData(null);
                    setColumnMapping({});
                    setProcessingResults(null);
                    setSchemaValidation({});
                  }}
                >
                  Reset Upload
                </Button>
                
                <Button
                  variant="default"
                  size="lg"
                  iconName="Database"
                  iconPosition="left"
                  loading={isProcessing}
                  disabled={isProcessing || Object.keys(columnMapping)?.length === 0}
                  onClick={handleIngestData}
                >
                  {isProcessing ? 'Processing with Master Schema...' : 'Ingest Data'}
                </Button>
              </div>
              
              <div className="text-center mt-3">
                <p className="text-xs text-muted-foreground">
                  Press <kbd className="px-1.5 py-0.5 bg-muted rounded font-data">Enter</kbd> to ingest data • 
                  Schema compliance: {((Object.values(columnMapping)?.filter(Boolean)?.length / MASTER_SCHEMA?.length) * 100)?.toFixed(1)}%
                </p>
              </div>
            </div>
          )}

          {/* Processing Status */}
          {(isProcessing || processingResults) && (
            <div className="mb-8">
              <ProcessingStatusPanel
                isProcessing={isProcessing}
                processingResults={processingResults}
                onExportErrors={handleExportErrors}
                onPromoteRecords={handlePromoteRecords}
              />
            </div>
          )}

          {/* Mobile-only Next Step Button */}
          <div className="lg:hidden">
            {canProceed && (
              <div className="fixed bottom-6 right-6 z-50">
                <Button
                  variant="default"
                  size="lg"
                  iconName="ArrowRight"
                  iconPosition="right"
                  onClick={handleNextStep}
                  className="shadow-elevation-3"
                >
                  Next Step
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Workflow Sidebar */}
        <WorkflowSidebar
          currentStep={1}
          workflowId="WF-2025-001"
          processId="PRC-001"
          onNextStep={handleNextStep}
          canProceed={canProceed}
        />
      </div>
    </div>
  );
};

export default DataIntakeDashboard;