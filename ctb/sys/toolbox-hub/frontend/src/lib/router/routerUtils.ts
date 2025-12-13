/**
 * Generate HEIR ID in format: HEIR-YYYY-MM-SOURCE-NNN
 */
export function generateHeirId(source: string): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const sequence = String(Math.floor(Math.random() * 1000)).padStart(3, '0');
  return `HEIR-${year}-${month}-${source.toUpperCase()}-${sequence}`;
}

/**
 * Generate Process ID in format: PRC-SOURCE-TIMESTAMP
 */
export function generateProcessId(source: string): string {
  const timestamp = Math.floor(Date.now() / 1000);
  return `PRC-${source.toUpperCase()}-${timestamp}`;
}

/**
 * Format duration in milliseconds to human readable string
 */
export function formatDuration(ms?: number): string {
  if (!ms) return 'N/A';
  
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`;
  return `${(ms / 3600000).toFixed(1)}h`;
}

/**
 * Format timestamp to relative time
 */
export function formatRelativeTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  
  const seconds = Math.floor(diffMs / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (seconds < 60) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  
  return date.toLocaleDateString();
}

/**
 * Get status badge color
 */
export function getStatusColor(status: string): string {
  switch (status) {
    case 'completed':
    case 'success':
    case 'active':
      return 'bg-green-500/10 text-green-500 border-green-500/20';
    case 'failed':
    case 'error':
      return 'bg-red-500/10 text-red-500 border-red-500/20';
    case 'running':
    case 'processing':
      return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
    case 'pending':
    case 'queued':
      return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
    default:
      return 'bg-muted text-muted-foreground border-border';
  }
}
