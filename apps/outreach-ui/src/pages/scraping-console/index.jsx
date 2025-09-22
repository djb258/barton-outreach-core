import { useEffect, useState } from "react";
import WorkflowSidebar from '../data-intake-dashboard/components/WorkflowSidebar';
import ScrapeSummaryCard from "./components/ScrapeSummaryCard";
import ScrapeResultsTable from "./components/ScrapeResultsTable";
import ScrapeFilterToolbar from "./components/ScrapeFilterToolbar";
import ScrapeControls from "./components/ScrapeControls";

export default function ScrapingConsole() {
  const [scrapeData, setScrapeData] = useState([]);
  const [filters, setFilters] = useState({ 
    date_range: [], 
    status: "All", 
    scrape_type: "All",
    batch_id: "" 
  });
  const [meta, setMeta] = useState({ 
    total_scraped: 0,
    scraping_active: 0,
    scraping_failed: 0,
    processing_timestamp: null
  });
  const [loading, setLoading] = useState(false);

  const fetchScrapeData = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/scrape-log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filters }),
      });
      const data = await res?.json();
      setScrapeData(data?.results || []);
      
      // Calculate summary metrics
      const totalScraped = data?.results?.length || 0;
      const activeScraping = data?.results?.filter(r => r?.status === "In Progress")?.length || 0;
      const failedScraping = data?.results?.filter(r => r?.status === "Failed")?.length || 0;
      const latestTimestamp = data?.results?.length > 0 ? data?.results?.[0]?.scrape_timestamp : null;

      setMeta({
        total_scraped: totalScraped,
        scraping_active: activeScraping,
        scraping_failed: failedScraping,
        processing_timestamp: latestTimestamp
      });
    } catch (err) {
      console.error("Failed to fetch scrape logs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScrapeData();
  }, []);

  const handleDownloadJSON = () => {
    const blob = new Blob([JSON.stringify(scrapeData, null, 2)], { 
      type: "application/json" 
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "scrape-data.json";
    a?.click();
    URL.revokeObjectURL(url);
  };

  const handleBackToAuditLog = () => {
    window.location.href = "/audit-log-console";
  };

  return (
    <div className="flex min-h-screen">
      <WorkflowSidebar currentStep={6} onNextStep={() => {}} />
      <main className="flex-1 p-6 space-y-6">
        <h1 className="text-xl font-semibold">Scraping Console</h1>

        <ScrapeSummaryCard meta={meta} />
        <ScrapeFilterToolbar 
          filters={filters} 
          setFilters={setFilters} 
          fetchData={fetchScrapeData} 
        />
        <ScrapeControls 
          onRefresh={fetchScrapeData} 
          onDownload={handleDownloadJSON}
          onBackToAuditLog={handleBackToAuditLog}
        />
        <ScrapeResultsTable scrapeData={scrapeData} loading={loading} />
      </main>
    </div>
  );
}