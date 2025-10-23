import { useEffect, useState } from "react";
import { useLocation, useSearchParams } from "react-router-dom";
import WorkflowSidebar from '../data-intake-dashboard/components/WorkflowSidebar';
import AuditLogSummaryCard from "./components/AuditLogSummaryCard";
import AuditLogResultsTable from "./components/AuditLogResultsTable";
import AuditLogFilterToolbar from "./components/AuditLogFilterToolbar";
import AuditLogControls from "./components/AuditLogControls";

export default function AuditLogConsole() {
  const [logs, setLogs] = useState([]);
  const [allLogs, setAllLogs] = useState([]); // Store all logs for filtering
  const [searchParams] = useSearchParams();
  const sourceFilter = searchParams.get('source'); // Get source filter from URL

  const [filters, setFilters] = useState({
    date_range: [],
    status: "ALL",
    batch_id: "",
    source: sourceFilter || "all" // Add source filter
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
      // Fetch from multiple sources to create unified audit log
      const [auditRes, scrapeRes] = await Promise.all([
        fetch("/api/audit-log", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filters: { ...filters, source: undefined } }), // Remove source filter for API call
        }),
        fetch("/api/scrape-log", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filters: {} }), // Get all scrape logs
        })
      ]);

      const auditData = await auditRes?.json();
      const scrapeData = await scrapeRes?.json();

      // Format audit logs (promotion logs)
      const formattedAuditLogs = (auditData?.results || []).map(log => ({
        ...log,
        source: 'promotion',
        timestamp: log.promotion_timestamp,
        unique_id: log.promoted_unique_id,
        altitude: 10000
      }));

      // Format scrape logs
      const formattedScrapeLogs = (scrapeData?.results || []).map(log => ({
        log_id: log.scrape_id,
        timestamp: log.scrape_timestamp,
        unique_id: log.unique_id || generateDoctrineId(),
        process_id: log.process_id,
        status: log.status,
        error_log: log.error_log,
        batch_id: log.batch_id,
        source: 'scrape-log',
        // Additional scrape fields
        scrape_type: log.scrape_type,
        target_url: log.target_url,
        records_scraped: log.records_scraped,
        altitude: log.altitude || 10000,
        doctrine_version: log.doctrine_version
      }));

      // Combine all logs
      const combinedLogs = [...formattedAuditLogs, ...formattedScrapeLogs]
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

      setAllLogs(combinedLogs);

      // Apply source filtering
      const filteredLogs = sourceFilter
        ? combinedLogs.filter(log => log.source === sourceFilter)
        : combinedLogs;

      setLogs(filteredLogs);
      setMeta({
        altitude: 10000,
        doctrine: 'STAMPED',
        doctrine_version: 'v2.1.0',
      });
    } catch (err) {
      console.error("Failed to fetch audit logs", err);
    } finally {
      setLoading(false);
    }
  };

  // Apply client-side filtering when source changes
  useEffect(() => {
    if (allLogs.length > 0) {
      const filteredLogs = sourceFilter
        ? allLogs.filter(log => log.source === sourceFilter)
        : allLogs;
      setLogs(filteredLogs);
    }
  }, [sourceFilter, allLogs]);

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleDownloadJSON = () => {
    // Include source field in JSON export
    const exportLogs = logs.map(log => ({
      ...log,
      source: log.source || 'unknown'
    }));

    const blob = new Blob([JSON.stringify(exportLogs, null, 2)], {
      type: "application/json"
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = sourceFilter
      ? `audit-log-${sourceFilter}.json`
      : "audit-log-unified.json";
    a?.click();
    URL.revokeObjectURL(url);
  };

  // Generate Doctrine ID helper
  const generateDoctrineId = () => {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 8);
    return `SHP-03-IMO-1-AUD-${timestamp}-${random}`.toUpperCase();
  };

  return (
    <div className="flex min-h-screen">
      <WorkflowSidebar currentStep={5} onNextStep={() => {}} />
      <main className="flex-1 p-6 space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-xl font-semibold">
            Unified Audit Log Console
            {sourceFilter && (
              <span className="ml-2 px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full">
                Source: {sourceFilter}
              </span>
            )}
          </h1>
          {sourceFilter && (
            <button
              onClick={() => window.location.href = '/audit-log-console'}
              className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Clear Filter
            </button>
          )}
        </div>

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