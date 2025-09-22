export default function AuditLogSummaryCard({ logs, meta }) {
  const promoted = logs?.filter(l => l?.status === "PROMOTED")?.length || 0;
  const failed = logs?.filter(l => l?.status === "FAILED")?.length || 0;
  const latestTs = logs?.length > 0 ? logs?.[0]?.promotion_timestamp : "N/A";

  return (
    <div className="grid grid-cols-3 gap-4 bg-white p-4 rounded-2xl shadow">
      <div>
        <p className="text-sm text-gray-500">PROMOTED ✅</p>
        <p className="text-lg font-bold">{promoted}</p>
      </div>
      <div>
        <p className="text-sm text-gray-500">FAILED ❌</p>
        <p className="text-lg font-bold">{failed}</p>
      </div>
      <div>
        <p className="text-sm text-gray-500">Doctrine Version</p>
        <p className="text-lg font-bold">{meta?.doctrine_version || "-"}</p>
        <p className="text-xs text-gray-400">Latest: {latestTs}</p>
      </div>
    </div>
  );
}