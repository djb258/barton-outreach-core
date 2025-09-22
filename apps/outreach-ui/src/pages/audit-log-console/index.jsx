import { useEffect, useState } from "react";
import WorkflowSidebar from '../data-intake-dashboard/components/WorkflowSidebar';
import AuditLogSummaryCard from "./components/AuditLogSummaryCard";
import AuditLogResultsTable from "./components/AuditLogResultsTable";
import AuditLogFilterToolbar from "./components/AuditLogFilterToolbar";
import AuditLogControls from "./components/AuditLogControls";

export default function AuditLogConsole() {
  const [logs, setLogs] = useState([]);
  const [filters, setFilters] = useState({ 
    date_range: [], 
    status: "ALL", 
    batch_id: "" 
  });
  const [meta, setMeta] = useState({ 
    altitude: null, 
    doctrine: null, 
    doctrine_version: null 
  });
  const [loading, setLoading] = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/audit-log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filters }),
      });
      const data = await res?.json();
      setLogs(data?.results || []);
      setMeta({
        altitude: data?.altitude,
        doctrine: data?.doctrine,
        doctrine_version: data?.results?.[0]?.doctrine_version || null,
      });
    } catch (err) {
      console.error("Failed to fetch audit logs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleDownloadJSON = () => {
    const blob = new Blob([JSON.stringify(logs, null, 2)], { 
      type: "application/json" 
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "audit-log.json";
    a?.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex min-h-screen">
      <WorkflowSidebar currentStep={5} onNextStep={() => {}} />
      <main className="flex-1 p-6 space-y-6">
        <h1 className="text-xl font-semibold">Audit Log Viewer Console</h1>

        <AuditLogSummaryCard logs={logs} meta={meta} />
        <AuditLogFilterToolbar 
          filters={filters} 
          setFilters={setFilters} 
          fetchLogs={fetchLogs} 
        />
        <AuditLogControls 
          onRefresh={fetchLogs} 
          onDownload={handleDownloadJSON} 
        />
        <AuditLogResultsTable logs={logs} loading={loading} />
      </main>
    </div>
  );
}