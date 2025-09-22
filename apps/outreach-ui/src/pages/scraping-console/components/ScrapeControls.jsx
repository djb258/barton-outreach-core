export default function ScrapeControls({ onRefresh, onDownload, onBackToAuditLog }) {
  return (
    <div className="flex items-center gap-4">
      <button 
        onClick={onRefresh} 
        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
      >
        🔄 Refresh Data
      </button>
      
      <button 
        onClick={onDownload} 
        className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors text-sm font-medium"
      >
        📥 Download JSON
      </button>
      
      <button 
        onClick={onBackToAuditLog} 
        className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors text-sm font-medium"
      >
        ← Back to Audit Log Console
      </button>
    </div>
  );
}