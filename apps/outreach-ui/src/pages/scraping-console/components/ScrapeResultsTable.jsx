export default function ScrapeResultsTable({ scrapeData, loading }) {
  if (loading) return <p className="text-center py-4">Loading scrape data...</p>;

  if (!scrapeData || scrapeData?.length === 0) {
    return (
      <div className="bg-white p-8 rounded-2xl shadow text-center">
        <p className="text-gray-500">No scrape data available</p>
      </div>
    );
  }

  // CSV headers exactly as they appear in the CSV file
  const csvHeaders = [
    { key: 'Number', label: 'Number' },
    { key: 'Company', label: 'Company' },
    { key: 'Company Name for Emails', label: 'Company Name for Emails' },
    { key: 'Account Stage', label: 'Account Stage' },
    { key: 'Lists', label: 'Lists' },
    { key: '# Employees', label: '# Employees' },
    { key: 'Industry', label: 'Industry' },
    { key: 'Account Owner', label: 'Account Owner' },
    { key: 'Website', label: 'Website' },
    { key: 'Company Linkedin Url', label: 'Company Linkedin Url' },
    { key: 'Facebook Url', label: 'Facebook Url' },
    { key: 'Twitter Url', label: 'Twitter Url' },
    { key: 'Company Street', label: 'Company Street' },
    { key: 'Company City', label: 'Company City' },
    { key: 'Company State', label: 'Company State' },
    { key: 'Company Country', label: 'Company Country' },
    { key: 'Company Postal Code', label: 'Company Postal Code' },
    { key: 'Company Address', label: 'Company Address' },
    { key: 'Keywords', label: 'Keywords' },
    { key: 'Company Phone', label: 'Company Phone' },
    { key: 'SEO Description', label: 'SEO Description' },
    { key: 'Technologies', label: 'Technologies' },
    { key: 'Total Funding', label: 'Total Funding' },
    { key: 'Latest Funding', label: 'Latest Funding' },
    { key: 'Latest Funding Amount', label: 'Latest Funding Amount' },
    { key: 'Last Raised At', label: 'Last Raised At' },
    { key: 'Annual Revenue', label: 'Annual Revenue' },
    { key: 'Number of Retail Locations', label: 'Number of Retail Locations' },
    { key: 'Apollo Account Id', label: 'Apollo Account Id' },
    { key: 'SIC Codes', label: 'SIC Codes' },
    { key: 'Short Description', label: 'Short Description' },
    { key: 'Founded Year', label: 'Founded Year' },
    { key: 'Logo Url', label: 'Logo Url' },
    { key: 'Subsidiary of', label: 'Subsidiary of' },
    { key: 'Primary Intent Topic', label: 'Primary Intent Topic' },
    { key: 'Primary Intent Score', label: 'Primary Intent Score' },
    { key: 'Secondary Intent Topic', label: 'Secondary Intent Topic' },
    { key: 'Secondary Intent Score', label: 'Secondary Intent Score' }
  ];

  // Doctrine metadata columns (always pinned at start)
  const doctrineColumns = [
    { key: 'unique_id', label: 'Unique ID', pinned: true },
    { key: 'process_id', label: 'Process ID', pinned: true },
    { key: 'altitude', label: 'Altitude', pinned: true }
  ];

  // Status and scrape specific columns
  const scrapeColumns = [
    { key: 'scrape_timestamp', label: 'Scrape Timestamp' },
    { key: 'scrape_type', label: 'Scrape Type' },
    { key: 'status', label: 'Status' },
    { key: 'error_log', label: 'Error Log' },
    { key: 'batch_id', label: 'Batch ID' }
  ];

  // Combine all columns: doctrine + scrape + CSV data
  const allColumns = [...doctrineColumns, ...scrapeColumns, ...csvHeaders];

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case "success":
      case "completed":
        return "text-green-600 bg-green-50";
      case "failed":
      case "error":
        return "text-red-600 bg-red-50";
      case "pending":
      case "in progress":
      case "processing":
        return "text-blue-600 bg-blue-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const getStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case "success":
      case "completed":
        return "✅";
      case "failed":
      case "error":
        return "❌";
      case "pending":
      case "in progress":
      case "processing":
        return "⏳";
      default:
        return "⚪";
    }
  };

  const getAltitudeBadge = (altitude) => {
    const altitudeNum = parseInt(altitude);
    if (altitudeNum === 10000) {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
          🛰️ 10K (Scraping)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
        {altitude || '—'}
      </span>
    );
  };

  const formatCellValue = (value, columnKey) => {
    if (!value && value !== 0) return '—';

    // Handle URLs
    if (columnKey.toLowerCase().includes('url') || columnKey === 'Website') {
      return (
        <a
          href={value}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline max-w-xs truncate block"
          title={value}
        >
          {value}
        </a>
      );
    }

    // Handle Logo URLs specially
    if (columnKey === 'Logo Url' && value) {
      return (
        <div className="flex items-center">
          <img
            src={value}
            alt="Company logo"
            className="w-6 h-6 rounded mr-2"
            onError={(e) => {e.target.style.display = 'none'}}
          />
          <a
            href={value}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline text-xs truncate"
            title={value}
          >
            View
          </a>
        </div>
      );
    }

    // Handle funding amounts
    if (columnKey.includes('Funding') || columnKey === 'Annual Revenue') {
      if (typeof value === 'number') {
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0
        }).format(value);
      }
      return value;
    }

    // Handle arrays (for technologies, keywords, lists, etc.)
    if (Array.isArray(value)) {
      return (
        <div className="group relative">
          <span className="truncate cursor-help max-w-xs block">
            {value.slice(0, 3).join(', ')}{value.length > 3 ? '...' : ''}
          </span>
          {value.length > 0 && (
            <div className="absolute z-10 invisible group-hover:visible bg-black text-white text-xs rounded py-2 px-3 -top-8 left-0 w-64 max-w-sm">
              {value.join(', ')}
            </div>
          )}
        </div>
      );
    }

    // Handle objects
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }

    // Handle long text with truncation
    if (typeof value === 'string' && value.length > 50) {
      return (
        <div className="group relative">
          <span className="truncate cursor-help max-w-xs block">
            {value.substring(0, 50)}...
          </span>
          <div className="absolute z-10 invisible group-hover:visible bg-black text-white text-xs rounded py-2 px-3 -top-8 left-0 w-64 max-w-sm">
            {value}
          </div>
        </div>
      );
    }

    return value;
  };

  const exportToJSON = () => {
    const exportData = scrapeData.map(row => {
      const exportRow = {};

      // Include all doctrine metadata
      doctrineColumns.forEach(col => {
        exportRow[col.key] = row[col.key];
      });

      // Include all scrape metadata
      scrapeColumns.forEach(col => {
        exportRow[col.key] = row[col.key];
      });

      // Include all CSV fields
      csvHeaders.forEach(col => {
        exportRow[col.key] = row[col.key];
      });

      return exportRow;
    });

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scrape-data-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white rounded-2xl shadow overflow-hidden">
      {/* Export Button */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-medium text-gray-900">
            Scrape Results ({scrapeData.length} records)
          </h3>
          <button
            onClick={exportToJSON}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            📥 Export JSON
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              {allColumns.map((column) => (
                <th
                  key={column.key}
                  className={`px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap ${
                    column.pinned ? 'sticky left-0 bg-gray-100 z-10 border-r' : ''
                  }`}
                  style={column.pinned ? { minWidth: '120px' } : {}}
                >
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {scrapeData?.map((row, index) => (
              <tr key={row?.unique_id || index} className="hover:bg-gray-50">
                {allColumns.map((column) => (
                  <td
                    key={column.key}
                    className={`px-4 py-3 text-sm ${
                      column.pinned ? 'sticky left-0 bg-white z-10 border-r font-medium' : ''
                    } ${
                      column.key === 'status' ? getStatusColor(row[column.key]) : 'text-gray-900'
                    }`}
                    style={column.pinned ? { minWidth: '120px' } : {}}
                  >
                    {/* Special handling for doctrine columns */}
                    {column.key === 'unique_id' && (
                      <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                        {row[column.key] || '—'}
                      </span>
                    )}

                    {column.key === 'process_id' && (
                      <span className="font-medium text-blue-800 bg-blue-50 px-2 py-1 rounded text-xs">
                        {row[column.key] || '—'}
                      </span>
                    )}

                    {column.key === 'altitude' && getAltitudeBadge(row[column.key])}

                    {/* Special handling for scrape metadata */}
                    {column.key === 'status' && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium">
                        {getStatusBadge(row[column.key])} {row[column.key]}
                      </span>
                    )}

                    {column.key === 'scrape_timestamp' && (
                      <span className="font-mono text-xs">
                        {row[column.key] ? new Date(row[column.key]).toLocaleString() : '—'}
                      </span>
                    )}

                    {column.key === 'error_log' && (
                      <div className="max-w-xs">
                        {row[column.key] ? (
                          <div className="group relative">
                            <span className="truncate cursor-help text-red-600 block">
                              {Array.isArray(row[column.key]) ? row[column.key].join(", ") : row[column.key]}
                            </span>
                            <div className="absolute z-10 invisible group-hover:visible bg-red-900 text-white text-xs rounded py-1 px-2 -top-8 left-0 w-64">
                              {Array.isArray(row[column.key]) ? row[column.key].join(", ") : row[column.key]}
                            </div>
                          </div>
                        ) : (
                          "—"
                        )}
                      </div>
                    )}

                    {column.key === 'batch_id' && (
                      <span className="font-mono text-xs bg-yellow-50 text-yellow-800 px-2 py-1 rounded">
                        {row[column.key] || '—'}
                      </span>
                    )}

                    {column.key === 'scrape_type' && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                        {row[column.key] || 'COMPANY_DATA'}
                      </span>
                    )}

                    {/* Handle CSV data columns with exact key matching */}
                    {csvHeaders.some(h => h.key === column.key) && (
                      formatCellValue(row[column.key], column.key)
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary Footer */}
      <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
        <div className="flex justify-between items-center text-sm text-gray-600">
          <span>
            Total Records: <strong>{scrapeData.length}</strong>
          </span>
          <span>
            Execution Layer: <strong>10,000ft (Scraping)</strong>
          </span>
        </div>
      </div>
    </div>
  );
}