export default function ScrapeFilterToolbar({ filters, setFilters, fetchData }) {
  const handleChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="bg-white p-4 rounded-2xl shadow">
      <div className="flex flex-wrap items-center gap-4">
        {/* Date Range */}
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Date Range:</label>
          <input
            type="date"
            value={filters?.date_range?.[0] || ""}
            onChange={e => handleChange("date_range", [e?.target?.value, filters?.date_range?.[1]])}
            className="border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <span className="text-gray-400">to</span>
          <input
            type="date"
            value={filters?.date_range?.[1] || ""}
            onChange={e => handleChange("date_range", [filters?.date_range?.[0], e?.target?.value])}
            className="border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Status:</label>
          <select
            value={filters?.status}
            onChange={e => handleChange("status", e?.target?.value)}
            className="border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="All">All</option>
            <option value="Success">Success</option>
            <option value="Failed">Failed</option>
            <option value="In Progress">In Progress</option>
          </select>
        </div>

        {/* Scrape Type Filter */}
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Scrape Type:</label>
          <select
            value={filters?.scrape_type}
            onChange={e => handleChange("scrape_type", e?.target?.value)}
            className="border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="All">All</option>
            <option value="Company Info">Company Info</option>
            <option value="Contact Data">Contact Data</option>
            <option value="Social Media">Social Media</option>
          </select>
        </div>

        {/* Batch ID Filter */}
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Batch ID:</label>
          <input
            type="text"
            placeholder="Enter Batch ID"
            value={filters?.batch_id}
            onChange={e => handleChange("batch_id", e?.target?.value)}
            className="border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-40"
          />
        </div>

        {/* Apply Button */}
        <button 
          onClick={fetchData} 
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          Apply Filters
        </button>
      </div>
    </div>
  );
}