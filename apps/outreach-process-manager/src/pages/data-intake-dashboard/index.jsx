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


const DataIntakeDashboard = () => {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileData, setFileData] = useState(null);
  const [columnMapping, setColumnMapping] = useState({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingResults, setProcessingResults] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);

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
      
      // Auto-detect column mappings
      const autoMapping = {};
      headers?.forEach(header => {
        const lowerHeader = header?.toLowerCase();
        if (lowerHeader?.includes('company') || lowerHeader?.includes('name')) {
          autoMapping[header] = 'company_name';
        } else if (lowerHeader?.includes('email') || lowerHeader?.includes('mail')) {
          autoMapping[header] = 'email';
        } else if (lowerHeader?.includes('phone') || lowerHeader?.includes('tel')) {
          autoMapping[header] = 'phone';
        } else if (lowerHeader?.includes('website') || lowerHeader?.includes('url')) {
          autoMapping[header] = 'website';
        }
      });
      setColumnMapping(autoMapping);
    };
    reader?.readAsText(file);
  }, []);

  const handleIngestData = useCallback(async () => {
    if (!fileData || Object.keys(columnMapping)?.length === 0) return;
    
    setIsProcessing(true);
    
    // Simulate processing with realistic delay
    setTimeout(() => {
      const mockResults = {
        totalRows: fileData?.length,
        successfulRows: Math.floor(fileData?.length * 0.92),
        failedRows: Math.ceil(fileData?.length * 0.08),
        validationErrors: [
          {
            row: 23,
            column: 'email',
            value: 'invalid-email',
            error: 'Invalid email format',
            severity: 'error'
          },
          {
            row: 45,
            column: 'phone',
            value: '123',
            error: 'Phone number too short',
            severity: 'warning'
          }
        ],
        processingTime: '2.3s',
        uniqueId: `WF-2025-001-BATCH-${Date.now()}`,
        timestamp: new Date()?.toISOString()
      };
      
      setProcessingResults(mockResults);
      setIsProcessing(false);
    }, 3000);
  }, [fileData, columnMapping]);

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

  const canProceed = processingResults && processingResults?.successfulRows > 0;

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
              <h1 className="text-2xl font-semibold text-foreground">Data Intake Dashboard</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Upload and process company prospect data through the IMO workflow
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <IntegrationStatusIndicator />
              <SystemHealthIndicator />
            </div>
          </div>

          {/* Upload Section */}
          <div className="mb-8">
            <FileUploadZone 
              onFileSelect={handleFileSelect}
              isProcessing={isProcessing}
            />
          </div>

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
                  {isProcessing ? 'Processing Data...' : 'Ingest Data'}
                </Button>
              </div>
              
              <div className="text-center mt-3">
                <p className="text-xs text-muted-foreground">
                  Press <kbd className="px-1.5 py-0.5 bg-muted rounded font-data">Enter</kbd> to ingest data
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