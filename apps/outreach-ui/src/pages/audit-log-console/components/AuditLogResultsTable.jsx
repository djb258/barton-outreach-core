export default function AuditLogResultsTable({ logs, loading }) {
  if (loading) return <p>Loading...</p>;

  return (
    <table className="w-full border-collapse border border-gray-200">
      <thead className="bg-gray-50">
        <tr>
          <th className="border p-2">Timestamp</th>
          <th className="border p-2">Unique ID</th>
          <th className="border p-2">Process ID</th>
          <th className="border p-2">Status</th>
          <th className="border p-2">Error Log</th>
          <th className="border p-2">Batch ID</th>
        </tr>
      </thead>
      <tbody>
        {logs?.map(log => (
          <tr key={log?.log_id}>
            <td className="border p-2">{log?.promotion_timestamp}</td>
            <td className="border p-2">{log?.promoted_unique_id}</td>
            <td className="border p-2">{log?.process_id}</td>
            <td className={`border p-2 ${log?.status === "PROMOTED" ? "text-green-600" : "text-red-600"}`}>
              {log?.status}
            </td>
            <td className="border p-2">
              {log?.error_log ? log?.error_log?.join(", ") : "-"}
            </td>
            <td className="border p-2">{log?.batch_id}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}