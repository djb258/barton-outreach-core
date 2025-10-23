export default function AuditLogFilterToolbar({ filters, setFilters, fetchLogs }) {
  const handleChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="flex items-center space-x-4 bg-white p-4 rounded-2xl shadow">
      <input
        type="date"
        value={filters?.date_range?.[0] || ""}
        onChange={e => handleChange("date_range", [e?.target?.value, filters?.date_range?.[1]])}
        className="border rounded p-2"
      />
      <input
        type="date"
        value={filters?.date_range?.[1] || ""}
        onChange={e => handleChange("date_range", [filters?.date_range?.[0], e?.target?.value])}
        className="border rounded p-2"
      />
      <select
        value={filters?.status || "ALL"}
        onChange={e => handleChange("status", e?.target?.value)}
        className="border rounded p-2"
      >
        <option value="ALL">All</option>
        <option value="PROMOTED">PROMOTED</option>
        <option value="FAILED">FAILED</option>
      </select>
      <input
        type="text"
        placeholder="Batch ID"
        value={filters?.batch_id || ""}
        onChange={e => handleChange("batch_id", e?.target?.value)}
        className="border rounded p-2"
      />
      <button 
        onClick={fetchLogs} 
        className="px-4 py-2 bg-blue-600 text-white rounded-lg"
      >
        Apply
      </button>
    </div>
  );
}