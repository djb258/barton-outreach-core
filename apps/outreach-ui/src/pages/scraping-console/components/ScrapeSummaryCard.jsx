export default function ScrapeSummaryCard({ meta }) {
  return (
    <div className="grid grid-cols-4 gap-4 bg-white p-4 rounded-2xl shadow">
      <div>
        <p className="text-sm text-gray-500">TOTAL SCRAPED 📊</p>
        <p className="text-lg font-bold text-blue-600">{meta?.total_scraped || 0}</p>
      </div>
      <div>
        <p className="text-sm text-gray-500">SCRAPING ACTIVE 🔄</p>
        <p className="text-lg font-bold text-yellow-600">{meta?.scraping_active || 0}</p>
      </div>
      <div>
        <p className="text-sm text-gray-500">SCRAPING FAILED ❌</p>
        <p className="text-lg font-bold text-red-600">{meta?.scraping_failed || 0}</p>
      </div>
      <div>
        <p className="text-sm text-gray-500">PROCESSING TIMESTAMP</p>
        <p className="text-sm font-mono text-gray-700">
          {meta?.processing_timestamp || "N/A"}
        </p>
      </div>
    </div>
  );
}