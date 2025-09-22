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
    'Number',
    'Company',
    'Company Name for Emails',
    'Account Stage',
    'Lists',
    '# Employees',
    'Industry',
    'Account Owner',
    'Website',
    'Company Linkedin Url',
    'Facebook Url',
    'Twitter Url',
    'Company Street',
    'Company City',
    'Company State',
    'Company Country',
    'Company Postal Code',
    'Company Address',
    'Keywords',
    'Company Phone',
    'SEO Description',
    'Technologies',
    'Total Funding',
    'Latest Funding',
    'Latest Funding Amount',
    'Last Raised At',
    'Annual Revenue',
    'Number of Retail Locations',
    'Apollo Account Id',
    'SIC Codes',
    'Short Description',
    'Founded Year',
    'Logo Url',
    'Subsidiary of',
    'Primary Intent Topic',
    'Primary Intent Score',
    'Secondary Intent Topic',
    'Secondary Intent Score'
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

  const getStatusColor = (status) => {
    const statusLower = status?.toLowerCase();
    switch (statusLower) {
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
    const statusLower = status?.toLowerCase();
    switch (statusLower) {
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

    // Handle URLs - check if column name includes 'Url' or is 'Website'
    if (columnKey === 'Website' ||
        columnKey === 'Company Linkedin Url' ||
        columnKey === 'Facebook Url' ||
        columnKey === 'Twitter Url' ||
        columnKey === 'Logo Url') {
      return (
        <a
          href={value}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline truncate block max-w-xs"
          title={value}
        >
          {value}
        </a>
      );
    }

    // Handle Logo Url specially with thumbnail
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

    // Handle funding amounts and revenue
    if (columnKey === 'Total Funding' ||
        columnKey === 'Latest Funding' ||
        columnKey === 'Latest Funding Amount' ||
        columnKey === 'Annual Revenue') {
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

    // Handle arrays (Technologies, Keywords, Lists, SIC Codes)
    if (Array.isArray(value)) {
      return (
        <div className="group relative">
          <span className="truncate cursor-help block max-w-xs">
            {value.slice(0, 3).join(', ')}{value.length > 3 ? '...' : ''}
          </span>
          {value.length > 0 && (
            <div className="absolute z-10 invisible group-hover:visible bg-gray-900 text-white text-xs rounded py-2 px-3 bottom-full mb-1 left-0 w-64 max-w-sm">
              <div className="font-semibold mb-1">{columnKey}:</div>
              {value.join(', ')}
            </div>
          )}
        </div>
      );
    }

    // Handle long descriptions with tooltips
    if ((columnKey === 'SEO Description' ||
         columnKey === 'Short Description' ||
         columnKey === 'Keywords' ||
         columnKey === 'Company Address') &&
        typeof value === 'string' && value.length > 50) {
      return (
        <div className="group relative">
          <span className="truncate cursor-help block max-w-xs">
            {value.substring(0, 50)}...
          </span>
          <div className="absolute z-10 invisible group-hover:visible bg-gray-900 text-white text-xs rounded py-2 px-3 bottom-full mb-1 left-0 w-96 max-w-sm">
            <div className="font-semibold mb-1">{columnKey}:</div>
            {value}
          </div>
        </div>
      );
    }

    // Handle objects
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }

    return value;
  };

  const exportToJSON = () => {
    const exportData = scrapeData.map(row => {
      const exportRow = {};

      // Include doctrine metadata
      doctrineColumns.forEach(col => {
        if (row[col.key]) {
          exportRow[col.key] = row[col.key];
        }
      });

      // Include scrape metadata
      scrapeColumns.forEach(col => {
        if (row[col.key]) {
          exportRow[col.key] = row[col.key];
        }
      });

      // Include all CSV fields with exact header names
      csvHeaders.forEach(header => {
        if (row[header] !== undefined) {
          exportRow[header] = row[header];
        }
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
      {/* Header with Export Button */}
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
              {/* Doctrine columns (pinned) */}
              {doctrineColumns.map(col => (
                <th
                  key={col.key}
                  className="sticky left-0 z-10 px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-100 border-r"
                  style={{ minWidth: '120px' }}
                >
                  {col.label}
                </th>
              ))}

              {/* Scrape metadata columns */}
              {scrapeColumns.map(col => (
                <th
                  key={col.key}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
                >
                  {col.label}
                </th>
              ))}

              {/* CSV data columns */}
              {csvHeaders.map(header => (
                <th
                  key={header}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {scrapeData?.map((row, index) => {
              const rowKey = row?.unique_id || index;

              return (
                <tr key={rowKey} className="hover:bg-gray-50">
                  {/* Doctrine columns (pinned) */}
                  <td className="sticky left-0 z-10 px-4 py-3 text-sm bg-white border-r">
                    <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                      {row.unique_id || '—'}
                    </span>
                  </td>
                  <td className="sticky left-[120px] z-10 px-4 py-3 text-sm bg-white border-r">
                    <span className="font-medium text-blue-800 bg-blue-50 px-2 py-1 rounded text-xs">
                      {row.process_id || '—'}
                    </span>
                  </td>
                  <td className="sticky left-[240px] z-10 px-4 py-3 text-sm bg-white border-r">
                    {getAltitudeBadge(row.altitude)}
                  </td>

                  {/* Scrape metadata columns */}
                  <td className="px-4 py-3 text-sm">
                    <span className="font-mono text-xs">
                      {row.scrape_timestamp ? new Date(row.scrape_timestamp).toLocaleString() : '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                      {row.scrape_type || 'COMPANY_DATA'}
                    </span>
                  </td>
                  <td className={`px-4 py-3 text-sm ${getStatusColor(row.status)}`}>
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium">
                      {getStatusBadge(row.status)} {row.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {row.error_log ? (
                      <div className="group relative">
                        <span className="truncate cursor-help text-red-600 block max-w-xs">
                          {Array.isArray(row.error_log) ? row.error_log.join(", ") : row.error_log}
                        </span>
                        <div className="absolute z-10 invisible group-hover:visible bg-red-900 text-white text-xs rounded py-2 px-3 bottom-full mb-1 left-0 w-64">
                          {Array.isArray(row.error_log) ? row.error_log.join(", ") : row.error_log}
                        </div>
                      </div>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span className="font-mono text-xs bg-yellow-50 text-yellow-800 px-2 py-1 rounded">
                      {row.batch_id || '—'}
                    </span>
                  </td>

                  {/* CSV data columns - using bracket notation */}
                  {csvHeaders.map(header => (
                    <td key={header} className="px-4 py-3 text-sm text-gray-900">
                      {formatCellValue(row[header], header)}
                    </td>
                  ))}
                </tr>
              );
            })}
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