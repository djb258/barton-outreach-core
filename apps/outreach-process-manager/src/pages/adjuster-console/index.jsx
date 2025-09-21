import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import WorkflowSidebar from '../data-intake-dashboard/components/WorkflowSidebar';
import AdjusterSummaryCard from './components/AdjusterSummaryCard';
import AdjusterFilterToolbar from './components/AdjusterFilterToolbar';
import AdjusterResultsTable from './components/AdjusterResultsTable';
import DoctrinalMetadataDisplay from '../../components/ui/DoctrinalMetadataDisplay';
import Button from '../../components/ui/Button';
import Icon from '../../components/AppIcon';

const AdjusterConsole = () => {
  const [adjustmentData, setAdjustmentData] = useState(null);
  const [filteredData, setFilteredData] = useState([]);
  const [currentFilter, setCurrentFilter] = useState('all');
  const [isLoading, setIsLoading] = useState(false);
  const [isAdjusting, setIsAdjusting] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [selectedRows, setSelectedRows] = useState(new Set());

  // Mock API call to fetch adjustment data
  const fetchAdjustmentData = async () => {
    setIsLoading(true);
    
    // Simulate API call to /api/promote
    setTimeout(() => {
      const mockResponse = {
        rows_promoted: 87,
        rows_pending: 13,
        rows_adjusted: 5,
        results: [
          {
            unique_id: "02.01.03.04.10000.001",
            process_id: "PRC-001",
            company_name: "Acme Corp",
            promoted: true,
            adjusted: false,
            adjustment_notes: "",
            errors: []
          },
          {
            unique_id: "02.01.03.04.10000.002", 
            process_id: "PRC-002",
            company_name: "Tech Solutions Inc",
            promoted: true,
            adjusted: true,
            adjustment_notes: "Email domain corrected",
            errors: []
          },
          {
            unique_id: "02.01.03.04.10000.003",
            process_id: "PRC-003", 
            company_name: "Global Manufacturing",
            promoted: false,
            adjusted: false,
            adjustment_notes: "",
            errors: ["pending_verification"]
          },
          {
            unique_id: "02.01.03.04.10000.004",
            process_id: "PRC-004",
            company_name: "Data Services LLC",
            promoted: true,
            adjusted: true,
            adjustment_notes: "Phone number format standardized",
            errors: []
          },
          {
            unique_id: "02.01.03.04.10000.005",
            process_id: "PRC-005",
            company_name: "Enterprise Solutions",
            promoted: false,
            adjusted: false,
            adjustment_notes: "",
            errors: ["manual_review_required"]
          }
        ]
      };
      
      setAdjustmentData(mockResponse);
      setFilteredData(mockResponse?.results);
      setIsLoading(false);
    }, 1500);
  };

  // Filter data based on current filter
  const applyFilter = (filterType) => {
    setCurrentFilter(filterType);
    
    if (!adjustmentData?.results) return;
    
    let filtered = adjustmentData?.results;
    
    switch (filterType) {
      case 'promoted':
        filtered = adjustmentData?.results?.filter(record => record?.promoted);
        break;
      case 'pending':
        filtered = adjustmentData?.results?.filter(record => !record?.promoted);
        break;
      case 'adjusted':
        filtered = adjustmentData?.results?.filter(record => record?.adjusted);
        break;
      default:
        filtered = adjustmentData?.results;
    }
    
    setFilteredData(filtered);
  };

  // Handle bulk adjustments
  const handleBulkAdjust = async () => {
    if (selectedRows?.size === 0) return;
    
    setIsAdjusting(true);
    
    // Simulate bulk adjustment API call
    setTimeout(() => {
      console.log('Bulk adjusted records:', Array.from(selectedRows));
      setSelectedRows(new Set());
      fetchAdjustmentData();
      setIsAdjusting(false);
    }, 2000);
  };

  // Deploy campaign
  const handleDeployCampaign = async () => {
    setIsDeploying(true);
    
    // Simulate campaign deployment API call
    setTimeout(() => {
      console.log('Campaign deployed with promoted records');
      setIsDeploying(false);
      // Navigate to campaign deployment success page
    }, 3000);
  };

  // Handle row selection
  const handleRowSelect = (uniqueId, selected) => {
    setSelectedRows(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet?.add(uniqueId);
      } else {
        newSet?.delete(uniqueId);
      }
      return newSet;
    });
  };

  // Handle single row adjustment
  const handleRowAdjustment = async (uniqueId, adjustmentData) => {
    // Simulate single row adjustment
    console.log('Adjusting row:', uniqueId, adjustmentData);
    setTimeout(() => {
      fetchAdjustmentData();
    }, 1000);
  };

  useEffect(() => {
    fetchAdjustmentData();
  }, []);

  const promotedCount = adjustmentData?.results?.filter(r => r?.promoted)?.length || 0;
  const pendingCount = adjustmentData?.results?.filter(r => !r?.promoted)?.length || 0;
  const adjustedCount = adjustmentData?.results?.filter(r => r?.adjusted)?.length || 0;
  const canDeployCampaign = promotedCount > 0;

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <WorkflowSidebar 
        currentStep={3}
        workflowId="WF-2025-001" 
        processId="PRC-ADJ-001"
        canProceed={canDeployCampaign}
        onNextStep={() => {}}
      />
      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {/* Header */}
        <div className="bg-card border-b border-border px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div>
                <h1 className="text-2xl font-bold text-foreground">Adjuster Console</h1>
                <p className="text-sm text-muted-foreground">Step 3 of Outreach Process Manager</p>
              </div>
              
              {/* Execution Layer Badge */}
              <div className="px-3 py-1 bg-accent/10 text-accent rounded-md text-sm font-medium">
                Altitude: 10,000ft - Execution Layer
              </div>
            </div>
            
            <DoctrinalMetadataDisplay
              uniqueId="02.01.03.04.10000.001"
              processId="PRC-ADJ-001"
              altitude="EXECUTION"
              className="flex-row space-x-4 space-y-0"
            />
          </div>
        </div>

        {/* Content Area */}
        <div className="p-6 space-y-6 overflow-y-auto h-[calc(100vh-80px)]">
          
          {/* Adjuster Summary Card */}
          <AdjusterSummaryCard
            rowsPromoted={adjustmentData?.rows_promoted || 0}
            rowsPending={adjustmentData?.rows_pending || 0}
            rowsAdjusted={adjustmentData?.rows_adjusted || 0}
            isLoading={isLoading}
          />

          {/* Filter Toolbar */}
          <AdjusterFilterToolbar
            currentFilter={currentFilter}
            onFilterChange={applyFilter}
            totalCount={adjustmentData?.results?.length || 0}
            promotedCount={promotedCount}
            pendingCount={pendingCount}
            adjustedCount={adjustedCount}
          />

          {/* Results Table */}
          <AdjusterResultsTable
            data={filteredData}
            isLoading={isLoading}
            selectedRows={selectedRows}
            onRowSelect={handleRowSelect}
            onRowAdjust={handleRowAdjustment}
          />

          {/* Control Buttons */}
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  iconName="Edit"
                  onClick={handleBulkAdjust}
                  disabled={selectedRows?.size === 0 || isAdjusting}
                >
                  {isAdjusting ? 'Adjusting...' : `Bulk Adjust (${selectedRows?.size})`}
                </Button>
                
                <Button
                  variant="default"
                  iconName="Rocket"
                  onClick={handleDeployCampaign}
                  disabled={!canDeployCampaign || isDeploying}
                >
                  {isDeploying ? 'Deploying...' : 'Deploy Campaign'}
                </Button>
              </div>
              
              <div className="flex space-x-3">
                <Link to="/validation-adjuster-console">
                  <Button variant="outline" iconName="ArrowLeft">
                    Back to Validation
                  </Button>
                </Link>
                
                <Link to="/campaign-deployment">
                  <Button 
                    variant="default" 
                    iconName="ArrowRight" 
                    iconPosition="right"
                    disabled={!canDeployCampaign}
                  >
                    View Campaign Status
                  </Button>
                </Link>
              </div>
            </div>
          </div>

          {/* Status Message */}
          {!canDeployCampaign && (
            <div className="bg-warning/10 border border-warning/20 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Icon name="AlertTriangle" size={20} color="var(--color-warning)" />
                <span className="text-sm font-medium text-warning">
                  No promoted records available for campaign deployment. Please adjust and promote records first.
                </span>
              </div>
            </div>
          )}

          {selectedRows?.size > 0 && (
            <div className="bg-info/10 border border-info/20 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Icon name="Info" size={20} color="var(--color-info)" />
                <span className="text-sm font-medium text-info">
                  {selectedRows?.size} records selected for bulk operations.
                </span>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default AdjusterConsole;