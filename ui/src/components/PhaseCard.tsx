/**
 * Phase Card Component
 * Displays summary metrics for a pipeline phase
 */

import type { PhaseStats } from '../services/neon';

interface PhaseCardProps {
  phase: string;
  stats: PhaseStats[];
}

export default function PhaseCard({ phase, stats }: PhaseCardProps) {
  const total = stats.reduce((sum, stat) => sum + stat.count, 0);

  const statusColors: Record<string, string> = {
    completed: 'bg-green-500',
    processing: 'bg-yellow-500',
    pending: 'bg-blue-500',
    failed: 'bg-red-500',
    default: 'bg-gray-500'
  };

  return (
    <div className="bg-gradient-to-br from-white to-gray-50 p-6 rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-gray-800">{phase}</h3>
        <span className="text-3xl font-bold text-indigo-600">{total}</span>
      </div>

      <div className="space-y-2">
        {stats.map((stat, index) => (
          <div key={index} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span
                className={`w-3 h-3 rounded-full ${
                  statusColors[stat.status] || statusColors.default
                }`}
              />
              <span className="text-sm text-gray-600 capitalize">{stat.status}</span>
            </div>
            <span className="text-sm font-semibold text-gray-800">{stat.count}</span>
          </div>
        ))}
      </div>

      {stats.length > 0 && stats[0].last_updated && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Last updated: {new Date(stats[0].last_updated).toLocaleString()}
          </p>
        </div>
      )}
    </div>
  );
}
