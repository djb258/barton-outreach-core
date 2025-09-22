export default function ScrapeResultsTable({ scrapeData, loading }) {
  if (loading) return <p className="text-center py-4">Loading scrape data...</p>;

  if (!scrapeData || scrapeData?.length === 0) {
    return (
      <div className="bg-white p-8 rounded-2xl shadow text-center">
        <p className="text-gray-500">No scrape data available</p>
      </div>
    );
  }

  const getStatusColor = (status) => {
    switch (status) {
      case "Success": return "text-green-600";
      case "Failed": return "text-red-600";
      case "In Progress": return "text-blue-600";
      default: return "text-gray-600";
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "Success": return "✅";
      case "Failed": return "❌";
      case "In Progress": return "🔄";
      default: return "⚪";
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-14px">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Scrape Timestamp
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Company Name
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Company URL
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Unique ID
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Scrape Type
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Error Log
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Batch ID
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {scrapeData?.map((row, index) => (
              <tr key={row?.unique_id || index} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-mono text-gray-900">
                  {row?.scrape_timestamp}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">
                  {row?.company_name}
                </td>
                <td className="px-4 py-3 text-sm text-blue-600 hover:underline max-w-xs truncate">
                  <a 
                    href={row?.company_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    title={row?.company_url}
                  >
                    {row?.company_url}
                  </a>
                </td>
                <td className="px-4 py-3 text-sm font-mono text-gray-600">
                  {row?.unique_id}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900">
                  {row?.scrape_type}
                </td>
                <td className={`px-4 py-3 text-sm font-medium ${getStatusColor(row?.status)}`}>
                  {getStatusBadge(row?.status)} {row?.status}
                </td>
                <td className="px-4 py-3 text-sm text-red-600 max-w-xs">
                  {row?.error_log ? (
                    <div className="group relative">
                      <span className="truncate cursor-help">
                        {Array.isArray(row?.error_log) ? row?.error_log?.join(", ") : row?.error_log}
                      </span>
                      {row?.error_log && (
                        <div className="absolute z-10 invisible group-hover:visible bg-black text-white text-xs rounded py-1 px-2 -top-8 left-0 w-64">
                          {Array.isArray(row?.error_log) ? row?.error_log?.join(", ") : row?.error_log}
                        </div>
                      )}
                    </div>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="px-4 py-3 text-sm font-mono text-gray-600">
                  {row?.batch_id}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}