import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import WorkflowSidebar from '../data-intake-dashboard/components/WorkflowSidebar';
import ValidationSummaryCard from './components/ValidationSummaryCard';
import ValidationFilterToolbar from './components/ValidationFilterToolbar';
import ValidationResultsTable from './components/ValidationResultsTable';
import DoctrinalMetadataDisplay from '../../components/ui/DoctrinalMetadataDisplay';
import Button from '../../components/ui/Button';
import Icon from '../../components/AppIcon';

const ValidationAdjusterConsole = () => {
  const [validationData, setValidationData] = useState(null);
  const [filteredData, setFilteredData] = useState([]);
  const [currentFilter, setCurrentFilter] = useState('all');
  const [isLoading, setIsLoading] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [isPromoting, setIsPromoting] = useState(false);

  // Mock API call to fetch validation data
  const fetchValidationData = async () => {
    setIsLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      const mockResponse = {
        rows_validated: 95,
        rows_failed: 5,
        results: [
          {
            unique_id: "02.01.03.04.10000.001",
            process_id: "PRC-001",
            company_name: "Acme Corp",
            validated: true,
            errors: []
          },
          {
            unique_id: "02.01.03.04.10000.002", 
            process_id: "PRC-002",
            company_name: "Tech Solutions Inc",
            validated: true,
            errors: []
          },
          {
            unique_id: "02.01.03.04.10000.003",
            process_id: "PRC-003", 
            company_name: "Bad Email LLC",
            validated: false,
            errors: ["missing_email", "duplicate_domain"]
          },
          {
            unique_id: "02.01.03.04.10000.004",
            process_id: "PRC-004",
            company_name: "Global Industries",
            validated: true,
            errors: []
          },
          {
            unique_id: "02.01.03.04.10000.005",
            process_id: "PRC-005",
            company_name: "Invalid Data Co",
            validated: false,
            errors: ["invalid_phone", "missing_website"]
          }
        ]
      };
      
      setValidationData(mockResponse);
      setFilteredData(mockResponse?.results);
      setIsLoading(false);
    }, 1500);
  };

  // Filter data based on current filter
  const applyFilter = (filterType) => {
    setCurrentFilter(filterType);
    
    if (!validationData?.results) return;
    
    let filtered = validationData?.results;
    
    switch (filterType) {
      case 'valid':
        filtered = validationData?.results?.filter(record => record?.validated);
        break;
      case 'failed':
        filtered = validationData?.results?.filter(record => !record?.validated);
        break;
      default:
        filtered = validationData?.results;
    }
    
    setFilteredData(filtered);
  };

  // Re-run validation
  const handleRerunValidation = async () => {
    setIsValidating(true);
    
    // Simulate API call to /api/validate
    setTimeout(() => {
      fetchValidationData();
      setIsValidating(false);
    }, 2000);
  };

  // Promote valid records
  const handlePromoteValidRecords = async () => {
    setIsPromoting(true);
    
    // Simulate API call to /api/promote
    setTimeout(() => {
      console.log('Promoted valid records to company table');
      setIsPromoting(false);
      // You could navigate to next step here
      // navigate('/promotion-console');
    }, 2500);
  };

  useEffect(() => {
    fetchValidationData();
  }, []);

  const validRecordCount = validationData?.results?.filter(r => r?.validated)?.length || 0;
  const canProceedToNext = validRecordCount > 0;

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <WorkflowSidebar 
        currentStep={2}
        workflowId="WF-2025-001" 
        processId="PRC-VAL-001"
        canProceed={canProceedToNext}
        onNextStep={() => {}}
      />
      
      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {/* Header */}
        <div className="bg-card border-b border-border px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div>
                <h1 className="text-2xl font-bold text-foreground">Validation Adjuster</h1>
                <p className="text-sm text-muted-foreground">Step 2 of Outreach Process Manager</p>
              </div>
              
              {/* Execution Layer Badge */}
              <div className="px-3 py-1 bg-accent/10 text-accent rounded-md text-sm font-medium">
                Altitude: 10,000ft - Execution Layer
              </div>
            </div>
            
            <DoctrinalMetadataDisplay
              uniqueId="02.01.03.04.10000.001"
              processId="PRC-VAL-001"
              altitude="EXECUTION"
              className="flex-row space-x-4 space-y-0"
            />
          </div>
        </div>

        {/* Content Area */}
        <div className="p-6 space-y-6 overflow-y-auto h-[calc(100vh-80px)]">
          
          {/* Validation Summary Card */}
          <ValidationSummaryCard
            rowsValidated={validationData?.rows_validated || 0}
            rowsFailed={validationData?.rows_failed || 0}
            isLoading={isLoading}
          />

          {/* Filter Toolbar */}
          <ValidationFilterToolbar
            currentFilter={currentFilter}
            onFilterChange={applyFilter}
            totalCount={validationData?.results?.length || 0}
            validCount={validRecordCount}
            failedCount={validationData?.rows_failed || 0}
          />

          {/* Results Table */}
          <ValidationResultsTable
            data={filteredData}
            isLoading={isLoading}
          />

          {/* Control Buttons */}
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  iconName="RefreshCw"
                  onClick={handleRerunValidation}
                  disabled={isValidating}
                >
                  {isValidating ? 'Re-running...' : 'Re-run Validation'}
                </Button>
                
                <Button
                  variant="default"
                  iconName="ArrowUp"
                  onClick={handlePromoteValidRecords}
                  disabled={!canProceedToNext || isPromoting}
                >
                  {isPromoting ? 'Promoting...' : 'Promote Valid Records'}
                </Button>
              </div>
              
              <div className="flex space-x-3">
                <Link to="/data-intake-dashboard">
                  <Button variant="outline" iconName="ArrowLeft">
                    Back to Ingestor
                  </Button>
                </Link>
                
                <Link to="/promotion-console">
                  <Button 
                    variant="default" 
                    iconName="ArrowRight" 
                    iconPosition="right"
                    disabled={!canProceedToNext}
                  >
                    Next Step → Promotion
                  </Button>
                </Link>
              </div>
            </div>
          </div>

          {/* Status Message */}
          {!canProceedToNext && (
            <div className="bg-warning/10 border border-warning/20 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Icon name="AlertTriangle" size={20} color="var(--color-warning)" />
                <span className="text-sm font-medium text-warning">
                  No valid records available. Please resolve validation errors before proceeding.
                </span>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default ValidationAdjusterConsole;