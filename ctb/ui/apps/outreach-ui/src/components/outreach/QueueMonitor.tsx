import React, { useState, useEffect } from 'react';
import { OutreachQueue } from '@/lib/outreach/types';

interface QueueStats {
  company_urls: number;
  profile_urls: number;
  mv_batch: number;
  total: number;
}

export function QueueMonitor() {
  const [queues, setQueues] = useState<OutreachQueue[]>([]);
  const [stats, setStats] = useState<QueueStats>({ company_urls: 0, profile_urls: 0, mv_batch: 0, total: 0 });
  const [processing, setProcessing] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  useEffect(() => {
    loadQueues();
    
    let interval: NodeJS.Timeout | null = null;
    if (autoRefresh) {
      interval = setInterval(() => {
        loadQueues();
      }, 10000); // Refresh every 10 seconds
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const loadQueues = async () => {
    if (loading) return;
    
    setLoading(true);
    try {
      // Load queue data from the zero wandering scraper views
      const [companyUrlsRes, profileUrlsRes, mvBatchRes] = await Promise.all([
        fetch('/api/outreach/queues/company-urls'),
        fetch('/api/outreach/queues/profile-urls'),
        fetch('/api/outreach/queues/mv-batch'),
      ]);

      const companyUrls = companyUrlsRes.ok ? await companyUrlsRes.json() : [];
      const profileUrls = profileUrlsRes.ok ? await profileUrlsRes.json() : [];
      const mvBatch = mvBatchRes.ok ? await mvBatchRes.json() : [];

      // Combine all queue items
      const allQueues: OutreachQueue[] = [
        ...companyUrls.map((item: any, index: number) => ({
          id: `company-${item.company_id}-${index}`,
          type: 'company_urls' as const,
          company_id: item.company_id,
          url: item.url,
          kind: item.kind,
          priority: 1,
          status: 'pending' as const,
          created_at: new Date().toISOString(),
        })),
        ...profileUrls.map((item: any, index: number) => ({
          id: `profile-${item.contact_id}-${index}`,
          type: 'profile_urls' as const,
          company_id: item.company_id,
          url: item.url,
          kind: item.kind,
          priority: 2,
          status: 'pending' as const,
          created_at: new Date().toISOString(),
        })),
        ...mvBatch.map((item: any, index: number) => ({
          id: `mv-${item.contact_id}-${index}`,
          type: 'mv_batch' as const,
          company_id: item.company_id,
          priority: 3,
          status: 'pending' as const,
          created_at: new Date().toISOString(),
        })),
      ];

      setQueues(allQueues);
      
      // Calculate stats
      const newStats = {
        company_urls: companyUrls.length,
        profile_urls: profileUrls.length,
        mv_batch: mvBatch.length,
        total: companyUrls.length + profileUrls.length + mvBatch.length,
      };
      setStats(newStats);
      setLastUpdated(new Date());

    } catch (error) {
      console.error('Error loading queues:', error);
    } finally {
      setLoading(false);
    }
  };

  const processQueue = async (queueType: string, limit: number = 10) => {
    if (processing[queueType]) return;

    setProcessing(prev => ({ ...prev, [queueType]: true }));

    try {
      const response = await fetch(`/api/outreach/queues/${queueType}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ limit }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log(`✅ Processed ${result.processed} items from ${queueType} queue`);
        
        // Refresh the queues after processing
        await loadQueues();
      } else {
        throw new Error(`Failed to process ${queueType} queue: ${response.statusText}`);
      }
    } catch (error) {
      console.error(`Error processing ${queueType} queue:`, error);
    } finally {
      setProcessing(prev => ({ ...prev, [queueType]: false }));
    }
  };

  const getQueueTypeIcon = (type: string) => {
    switch (type) {
      case 'company_urls': return '🏢';
      case 'profile_urls': return '👤';
      case 'mv_batch': return '✉️';
      default: return '📋';
    }
  };

  const getQueueTypeLabel = (type: string) => {
    switch (type) {
      case 'company_urls': return 'Company URL Scraping';
      case 'profile_urls': return 'Profile URL Scraping';
      case 'mv_batch': return 'Email Verification';
      default: return type;
    }
  };

  const getProcessingStatus = (type: string) => {
    if (processing[type]) return 'Processing...';
    const count = queues.filter(q => q.type === type).length;
    return count > 0 ? `${count} items` : 'Empty';
  };

  return (
    <div className="queue-monitor">
      <div className="monitor-header">
        <h2>Queue Monitor</h2>
        <div className="header-controls">
          <div className="last-updated">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </div>
          <label className="auto-refresh">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh
          </label>
          <button onClick={loadQueues} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Queue Stats */}
      <div className="stats-grid">
        <div className="stat-card company">
          <div className="stat-icon">🏢</div>
          <div className="stat-info">
            <div className="stat-value">{stats.company_urls}</div>
            <div className="stat-label">Company URLs</div>
          </div>
          <button
            className="process-btn"
            onClick={() => processQueue('company_urls', 5)}
            disabled={stats.company_urls === 0 || processing.company_urls}
          >
            {processing.company_urls ? '⏳' : '▶️'}
          </button>
        </div>

        <div className="stat-card profile">
          <div className="stat-icon">👤</div>
          <div className="stat-info">
            <div className="stat-value">{stats.profile_urls}</div>
            <div className="stat-label">Profile URLs</div>
          </div>
          <button
            className="process-btn"
            onClick={() => processQueue('profile_urls', 10)}
            disabled={stats.profile_urls === 0 || processing.profile_urls}
          >
            {processing.profile_urls ? '⏳' : '▶️'}
          </button>
        </div>

        <div className="stat-card verification">
          <div className="stat-icon">✉️</div>
          <div className="stat-info">
            <div className="stat-value">{stats.mv_batch}</div>
            <div className="stat-label">Email Verification</div>
          </div>
          <button
            className="process-btn"
            onClick={() => processQueue('mv_batch', 20)}
            disabled={stats.mv_batch === 0 || processing.mv_batch}
          >
            {processing.mv_batch ? '⏳' : '▶️'}
          </button>
        </div>

        <div className="stat-card total">
          <div className="stat-icon">📊</div>
          <div className="stat-info">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">Total Items</div>
          </div>
          <button
            className="process-btn process-all"
            onClick={() => {
              processQueue('company_urls', 5);
              processQueue('profile_urls', 10);
              processQueue('mv_batch', 20);
            }}
            disabled={stats.total === 0 || Object.values(processing).some(Boolean)}
          >
            {Object.values(processing).some(Boolean) ? '⏳' : '🚀'}
          </button>
        </div>
      </div>

      {/* Queue Details */}
      <div className="queue-details">
        <h3>Queue Status</h3>
        <div className="queue-list">
          {['company_urls', 'profile_urls', 'mv_batch'].map(type => (
            <div key={type} className={`queue-item ${processing[type] ? 'processing' : ''}`}>
              <div className="queue-info">
                <span className="queue-icon">{getQueueTypeIcon(type)}</span>
                <div className="queue-text">
                  <div className="queue-name">{getQueueTypeLabel(type)}</div>
                  <div className="queue-status">{getProcessingStatus(type)}</div>
                </div>
              </div>
              
              <div className="queue-actions">
                {processing[type] && (
                  <div className="processing-indicator">
                    <div className="spinner"></div>
                  </div>
                )}
                <button
                  onClick={() => processQueue(type, 10)}
                  disabled={processing[type] || queues.filter(q => q.type === type).length === 0}
                  className="process-queue-btn"
                >
                  Process
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      {queues.length > 0 && (
        <div className="recent-activity">
          <h3>Recent Queue Items</h3>
          <div className="activity-list">
            {queues.slice(0, 10).map(item => (
              <div key={item.id} className="activity-item">
                <span className="activity-icon">{getQueueTypeIcon(item.type)}</span>
                <div className="activity-details">
                  <div className="activity-type">{getQueueTypeLabel(item.type)}</div>
                  <div className="activity-info">
                    {item.url ? `URL: ${item.url.substring(0, 50)}...` : `Company ID: ${item.company_id}`}
                  </div>
                </div>
                <div className="activity-priority">
                  Priority: {item.priority}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <style jsx>{`
        .queue-monitor {
          padding: 24px;
          max-width: 1200px;
          margin: 0 auto;
        }

        .monitor-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 30px;
          flex-wrap: wrap;
          gap: 20px;
        }

        .monitor-header h2 {
          margin: 0;
          color: #1e293b;
          font-size: 1.8em;
        }

        .header-controls {
          display: flex;
          align-items: center;
          gap: 20px;
        }

        .last-updated {
          font-size: 0.9em;
          color: #6b7280;
        }

        .auto-refresh {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.9em;
          color: #374151;
          cursor: pointer;
        }

        .auto-refresh input {
          margin: 0;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
          margin-bottom: 40px;
        }

        .stat-card {
          background: white;
          padding: 24px;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          display: flex;
          align-items: center;
          gap: 16px;
          transition: all 0.3s ease;
        }

        .stat-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }

        .stat-card.company { border-left: 4px solid #3b82f6; }
        .stat-card.profile { border-left: 4px solid #10b981; }
        .stat-card.verification { border-left: 4px solid #f59e0b; }
        .stat-card.total { border-left: 4px solid #8b5cf6; }

        .stat-icon {
          font-size: 2.5em;
        }

        .stat-info {
          flex: 1;
        }

        .stat-value {
          font-size: 2em;
          font-weight: 700;
          color: #1e293b;
          line-height: 1;
          margin-bottom: 4px;
        }

        .stat-label {
          font-size: 0.9em;
          color: #6b7280;
          font-weight: 500;
        }

        .process-btn {
          padding: 12px;
          border: none;
          border-radius: 50%;
          background: #667eea;
          color: white;
          cursor: pointer;
          font-size: 1.2em;
          width: 44px;
          height: 44px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s ease;
        }

        .process-btn:hover:not(:disabled) {
          background: #5a6fd8;
          transform: scale(1.1);
        }

        .process-btn:disabled {
          background: #d1d5db;
          cursor: not-allowed;
          transform: none;
        }

        .process-btn.process-all {
          background: #10b981;
        }

        .process-btn.process-all:hover:not(:disabled) {
          background: #059669;
        }

        .queue-details,
        .recent-activity {
          background: white;
          padding: 24px;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          margin-bottom: 24px;
        }

        .queue-details h3,
        .recent-activity h3 {
          margin: 0 0 20px 0;
          color: #1e293b;
          font-size: 1.3em;
        }

        .queue-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .queue-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          transition: all 0.3s ease;
        }

        .queue-item:hover {
          border-color: #667eea;
          background: #f8faff;
        }

        .queue-item.processing {
          background: #fef3c7;
          border-color: #f59e0b;
        }

        .queue-info {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .queue-icon {
          font-size: 1.5em;
        }

        .queue-name {
          font-weight: 600;
          color: #1e293b;
          margin-bottom: 2px;
        }

        .queue-status {
          font-size: 0.9em;
          color: #6b7280;
        }

        .queue-actions {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .processing-indicator {
          display: flex;
          align-items: center;
        }

        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid #f59e0b;
          border-top: 2px solid transparent;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .process-queue-btn {
          padding: 8px 16px;
          border: none;
          border-radius: 6px;
          background: #667eea;
          color: white;
          cursor: pointer;
          font-size: 0.9em;
          font-weight: 500;
          transition: all 0.2s ease;
        }

        .process-queue-btn:hover:not(:disabled) {
          background: #5a6fd8;
        }

        .process-queue-btn:disabled {
          background: #d1d5db;
          cursor: not-allowed;
        }

        .activity-list {
          max-height: 300px;
          overflow-y: auto;
        }

        .activity-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          border-bottom: 1px solid #f3f4f6;
        }

        .activity-item:last-child {
          border-bottom: none;
        }

        .activity-icon {
          font-size: 1.2em;
        }

        .activity-details {
          flex: 1;
        }

        .activity-type {
          font-weight: 500;
          color: #374151;
          margin-bottom: 2px;
        }

        .activity-info {
          font-size: 0.85em;
          color: #6b7280;
        }

        .activity-priority {
          font-size: 0.8em;
          color: #9ca3af;
        }

        button {
          border: none;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        button:disabled {
          cursor: not-allowed;
        }

        @media (max-width: 768px) {
          .queue-monitor {
            padding: 16px;
          }

          .monitor-header {
            flex-direction: column;
            align-items: stretch;
          }

          .header-controls {
            flex-wrap: wrap;
            justify-content: space-between;
          }

          .stats-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
          }

          .queue-item {
            flex-direction: column;
            align-items: stretch;
            gap: 12px;
          }

          .queue-actions {
            justify-content: flex-end;
          }
        }
      `}</style>
    </div>
  );
}