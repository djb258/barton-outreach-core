export default function AuditLogResultsTable({ logs, loading }) {
  if (loading) return <p className="text-center py-4">Loading audit logs...</p>;

  if (!logs || logs.length === 0) {
    return (
      <div className="bg-white p-8 rounded-2xl shadow text-center">
        <p className="text-gray-500">No audit log entries found</p>
      </div>
    );
  }

  const getStatusColor = (status) => {
    const statusLower = status?.toLowerCase();
    switch (statusLower) {
      case "success":
      case "completed":
      case "promoted":
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
      case "promoted":
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

  const getSourceBadge = (source) => {
    switch (source) {
      case "promotion":
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
            📊 Promotion
          </span>
        );
      case "scrape-log":
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            🕷️ Scraping
          </span>
        );
      case "validation":
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            ✅ Validation
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            ❓ {source || 'Unknown'}
          </span>
        );
    }
  };

  const getAltitudeBadge = (altitude) => {
    const altitudeNum = parseInt(altitude);
    if (altitudeNum === 10000) {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
          🛰️ 10K
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
        {altitude || '—'}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-2xl shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              {/* Doctrine metadata columns (pinned) */}
              <th className="sticky left-0 z-10 px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-100 border-r">
                Unique ID
              </th>
              <th className="sticky left-[160px] z-10 px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-100 border-r">
                Process ID
              </th>
              <th className="sticky left-[320px] z-10 px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-100 border-r">
                Altitude
              </th>

              {/* Audit log columns */}
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                Timestamp
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                Source
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                Error Log
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                Batch ID
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {logs?.map((log, index) => {
              const rowKey = log?.log_id || log?.unique_id || index;

              return (
                <tr key={rowKey} className="hover:bg-gray-50">
                  {/* Doctrine columns (pinned) */}
                  <td className="sticky left-0 z-10 px-4 py-3 text-sm bg-white border-r">
                    <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                      {log.unique_id || '—'}
                    </span>
                  </td>
                  <td className="sticky left-[160px] z-10 px-4 py-3 text-sm bg-white border-r">
                    <span className="font-medium text-blue-800 bg-blue-50 px-2 py-1 rounded text-xs">
                      {log.process_id || '—'}
                    </span>
                  </td>
                  <td className="sticky left-[320px] z-10 px-4 py-3 text-sm bg-white border-r">
                    {getAltitudeBadge(log.altitude)}
                  </td>

                  {/* Audit log columns */}
                  <td className="px-4 py-3 text-sm">
                    <span className="font-mono text-xs">
                      {log.timestamp ? new Date(log.timestamp).toLocaleString() : '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {getSourceBadge(log.source)}
                  </td>
                  <td className={`px-4 py-3 text-sm ${getStatusColor(log.status)}`}>
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium">
                      {getStatusBadge(log.status)} {log.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {log.error_log ? (
                      <div className="group relative">
                        <span className="truncate cursor-help text-red-600 block max-w-xs">
                          {Array.isArray(log.error_log) ? log.error_log.join(", ") : log.error_log}
                        </span>
                        <div className="absolute z-10 invisible group-hover:visible bg-red-900 text-white text-xs rounded py-2 px-3 bottom-full mb-1 left-0 w-64">
                          {Array.isArray(log.error_log) ? log.error_log.join(", ") : log.error_log}
                        </div>
                      </div>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span className="font-mono text-xs bg-yellow-50 text-yellow-800 px-2 py-1 rounded">
                      {log.batch_id || '—'}
                    </span>
                  </td>
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
            Total Records: <strong>{logs.length}</strong>
          </span>
          <span>
            Unified Audit Trail: <strong>STAMPED Doctrine</strong>
          </span>
        </div>
      </div>
    </div>
  );
}