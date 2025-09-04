import React from 'react';
import { OutreachManifest } from '@/lib/outreach/types';

interface OutreachOverviewProps {
  manifest: OutreachManifest;
}

export function OutreachOverview({ manifest }: OutreachOverviewProps) {
  const calculateOverallProgress = () => {
    let totalDone = 0;
    let totalWip = 0;
    let totalStages = 0;

    Object.values(manifest.buckets).forEach(bucket => {
      if (bucket) {
        bucket.stages.forEach(stage => {
          totalStages++;
          if (stage.status === 'done') totalDone++;
          if (stage.status === 'wip') totalWip++;
        });
      }
    });

    const percentage = totalStages > 0 ? ((totalDone + totalWip * 0.5) / totalStages) * 100 : 0;
    return { percentage, done: totalDone, wip: totalWip, total: totalStages };
  };

  const progress = calculateOverallProgress();

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'done':
        return '✅';
      case 'wip':
        return '🔄';
      default:
        return '⭕';
    }
  };

  const getDotColorIcon = (color: string) => {
    switch (color) {
      case 'green':
        return '🟢';
      case 'yellow':
        return '🟡';
      case 'red':
        return '🔴';
      default:
        return '⚫';
    }
  };

  return (
    <div className="outreach-overview">
      {/* Header Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Companies</h3>
          <div className="stat-value">{manifest.stats?.total_companies || 0}</div>
          <div className="stat-subtitle">Total tracked</div>
        </div>
        <div className="stat-card">
          <h3>Contacts</h3>
          <div className="stat-value">{manifest.stats?.verified_contacts || 0}</div>
          <div className="stat-subtitle">Verified emails</div>
        </div>
        <div className="stat-card">
          <h3>Campaigns</h3>
          <div className="stat-value">{manifest.stats?.active_campaigns || 0}</div>
          <div className="stat-subtitle">Currently active</div>
        </div>
        <div className="stat-card">
          <h3>Queue Items</h3>
          <div className="stat-value">{manifest.stats?.queue_items || 0}</div>
          <div className="stat-subtitle">Pending processing</div>
        </div>
      </div>

      {/* Overall Progress */}
      <div className="progress-card">
        <h3>Overall Progress</h3>
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${progress.percentage}%` }}
          />
        </div>
        <div className="progress-stats">
          <span>✅ {progress.done} done</span>
          <span>🔄 {progress.wip} in progress</span>
          <span>⭕ {progress.total - progress.done - progress.wip} todo</span>
        </div>
      </div>

      {/* Buckets Overview */}
      <div className="buckets-grid">
        {Object.entries(manifest.buckets).map(([key, bucket]) => {
          if (!bucket) return null;
          
          const bucketProgress = bucket.progress || {
            done: bucket.stages.filter(s => s.status === 'done').length,
            wip: bucket.stages.filter(s => s.status === 'wip').length,
            todo: bucket.stages.filter(s => s.status === 'todo').length,
            total: bucket.stages.length,
          };

          return (
            <div key={key} className="bucket-card">
              <h4>{bucket.name}</h4>
              <div className="bucket-progress">
                {bucketProgress.done}/{bucketProgress.total} completed
              </div>
              <div className="bucket-stages">
                {bucket.stages.map(stage => (
                  <div key={stage.id} className={`stage-item ${stage.status}`}>
                    <span className="stage-icon">{getStatusIcon(stage.status)}</span>
                    <span className="stage-name">{stage.name}</span>
                    {stage.queue_count && stage.queue_count > 0 && (
                      <span className="queue-badge">{stage.queue_count}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <style jsx>{`
        .outreach-overview {
          padding: 24px;
          max-width: 1200px;
          margin: 0 auto;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 20px;
          margin-bottom: 30px;
        }

        .stat-card {
          background: white;
          padding: 24px;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          text-align: center;
        }

        .stat-card h3 {
          margin: 0 0 12px 0;
          color: #64748b;
          font-size: 0.9em;
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .stat-value {
          font-size: 2.5em;
          font-weight: 700;
          color: #1e293b;
          line-height: 1;
          margin-bottom: 8px;
        }

        .stat-subtitle {
          color: #64748b;
          font-size: 0.85em;
        }

        .progress-card {
          background: white;
          padding: 30px;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          margin-bottom: 30px;
        }

        .progress-card h3 {
          margin: 0 0 20px 0;
          color: #1e293b;
          font-size: 1.3em;
        }

        .progress-bar {
          width: 100%;
          height: 24px;
          background: #e2e8f0;
          border-radius: 12px;
          overflow: hidden;
          margin-bottom: 16px;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #10b981, #059669);
          transition: width 0.3s ease;
        }

        .progress-stats {
          display: flex;
          justify-content: space-between;
          font-size: 0.9em;
          color: #64748b;
        }

        .buckets-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
          gap: 24px;
        }

        .bucket-card {
          background: white;
          padding: 24px;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .bucket-card h4 {
          margin: 0 0 16px 0;
          color: #1e293b;
          font-size: 1.2em;
        }

        .bucket-progress {
          color: #64748b;
          font-size: 0.9em;
          margin-bottom: 20px;
        }

        .bucket-stages {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .stage-item {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 12px;
          border-radius: 8px;
          transition: all 0.2s ease;
        }

        .stage-item.todo {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
        }

        .stage-item.wip {
          background: #fef3c7;
          border: 1px solid #f59e0b;
        }

        .stage-item.done {
          background: #dcfce7;
          border: 1px solid #10b981;
        }

        .stage-icon {
          font-size: 1.1em;
        }

        .stage-name {
          flex: 1;
          font-weight: 500;
          color: #1e293b;
        }

        .queue-badge {
          background: #667eea;
          color: white;
          padding: 4px 8px;
          border-radius: 12px;
          font-size: 0.75em;
          font-weight: 600;
        }

        @media (max-width: 768px) {
          .outreach-overview {
            padding: 16px;
          }

          .stats-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
          }

          .buckets-grid {
            grid-template-columns: 1fr;
            gap: 16px;
          }

          .progress-stats {
            flex-direction: column;
            gap: 8px;
          }
        }
      `}</style>
    </div>
  );
}