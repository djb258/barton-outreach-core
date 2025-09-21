import React, { useState, useEffect } from 'react';
import WorkflowSidebar from '../data-intake-dashboard/components/WorkflowSidebar';
import PromotionSummaryCard from './components/PromotionSummaryCard';
import PromotionResultsTable from './components/PromotionResultsTable';
import PromotionControls from './components/PromotionControls';
import DoctrinalMetadataDisplay from '../../components/ui/DoctrinalMetadataDisplay';

const PromotionConsole = () => {
  const [summary, setSummary] = useState(null);
  const [results, setResults] = useState([]);
  const [auditLog, setAuditLog] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchPromotion = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("/api/promote", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filters: { validated: true } })
      });
      const data = await res?.json();
      setSummary(data);

      // Process promoted rows
      const promotedRows = data?.promoted_unique_ids?.map(id => ({
        unique_id: id,
        company_name: "-",
        promotion_status: "Promoted",
        errors: []
      })) || [];

      // Process failed rows
      const failedRows = data?.failed_rows?.map(fr => ({
        unique_id: fr?.unique_id,
        company_name: fr?.company_name,
        promotion_status: "Failed",
        errors: fr?.errors || []
      })) || [];

      setResults([...promotedRows, ...failedRows]);
      setAuditLog(data);
    } catch (error) {
      console.error('Error fetching promotion data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    if (!auditLog) return;
    const blob = new Blob([JSON.stringify(auditLog, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `promotion_audit_log_${new Date()?.toISOString()?.slice(0, 10)}.json`;
    a?.click();
    URL.revokeObjectURL(url);
  };

  const handleBack = () => {
    window.location.href = "/adjuster-console";
  };

  useEffect(() => {
    fetchPromotion();
  }, []);

  return (
    <div className="flex min-h-screen bg-background">
      <WorkflowSidebar 
        currentStep={4} 
        workflowId="WF-2025-PROMO"
        processId="PRC-PROMOTION"
        canProceed={summary?.rows_promoted > 0}
        onNextStep={() => {}}
      />
      
      <main className="flex-1 p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Step 4: Promotion Console</h1>
            <p className="text-muted-foreground mt-1">
              Execute final campaign deployment and monitor promotion status
            </p>
          </div>
          
          <DoctrinalMetadataDisplay
            uniqueId="02.01.03.04.10000.001"
            processId="PRC-PROMOTION"
            altitude="EXECUTION"
            className="flex items-center space-x-4"
          />
        </div>

        {/* Summary Card */}
        <PromotionSummaryCard summary={summary} isLoading={isLoading} />

        {/* Results Table */}
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <div className="p-6 border-b border-border">
            <h2 className="text-xl font-semibold text-foreground">Promotion Results</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Detailed status for each company record in the promotion batch
            </p>
          </div>
          
          <PromotionResultsTable results={results} isLoading={isLoading} />
        </div>

        {/* Controls */}
        <PromotionControls
          onPromote={fetchPromotion}
          onDownload={handleDownload}
          onBack={handleBack}
          isLoading={isLoading}
          canDownload={!!auditLog}
        />
      </main>
    </div>
  );
};

export default PromotionConsole;