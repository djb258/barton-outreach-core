export default function AuditLogControls({ onRefresh, onDownload }) {
  const handleBackToPromotion = () => {
    window.location.href = "/promotion-console";
  };

  return (
    <div className="flex space-x-4">
      <button 
        onClick={onRefresh} 
        className="px-4 py-2 bg-green-600 text-white rounded-lg"
      >
        Refresh Logs
      </button>
      <button 
        onClick={onDownload} 
        className="px-4 py-2 bg-gray-600 text-white rounded-lg"
      >
        Download JSON
      </button>
      <button 
        onClick={handleBackToPromotion}
        className="px-4 py-2 bg-yellow-600 text-white rounded-lg"
      >
        Back to Promotion Console
      </button>
    </div>
  );
}