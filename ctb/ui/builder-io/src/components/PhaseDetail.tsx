/**
 * Phase Detail Component
 * Expandable detailed view of a pipeline phase with Apify integration
 */

import { useState } from 'react';
import type { PhaseStats } from '../services/neon';
import { runApifyActor } from '../services/apify';
import PhaseCard from './PhaseCard';

interface PhaseDetailProps {
  phase: string;
  stats: PhaseStats[];
  apifyActorId?: string;
}

export default function PhaseDetail({ phase, stats, apifyActorId }: PhaseDetailProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handleRunApify = async () => {
    if (!apifyActorId) {
      alert('No Apify actor configured for this phase');
      return;
    }

    setIsRunning(true);
    setResult(null);

    try {
      const data = await runApifyActor(apifyActorId);
      setResult(`Success! Apify actor completed.`);
      console.log('Apify result:', data);
    } catch (error) {
      setResult(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error('Apify error:', error);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Phase Card */}
      <PhaseCard phase={phase} stats={stats} />

      {/* Apify Integration */}
      {apifyActorId && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h4 className="text-lg font-semibold text-gray-800 mb-4">
            Apify Integration
          </h4>
          <p className="text-sm text-gray-600 mb-4">
            Run Apify actor: <code className="bg-gray-100 px-2 py-1 rounded">{apifyActorId}</code>
          </p>
          <button
            onClick={handleRunApify}
            disabled={isRunning}
            className={`px-6 py-3 rounded-lg font-semibold text-white transition-colors ${
              isRunning
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700'
            }`}
          >
            {isRunning ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Running...
              </span>
            ) : (
              'Run Apify Actor'
            )}
          </button>
          {result && (
            <div
              className={`mt-4 p-4 rounded-lg ${
                result.startsWith('Success')
                  ? 'bg-green-50 border border-green-200 text-green-800'
                  : 'bg-red-50 border border-red-200 text-red-800'
              }`}
            >
              {result}
            </div>
          )}
        </div>
      )}

      {/* Detailed Stats Table */}
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h4 className="text-lg font-semibold text-gray-800 mb-4">Detailed Statistics</h4>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Count
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Updated
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {stats.map((stat, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900 capitalize">{stat.status}</td>
                  <td className="px-4 py-3 text-sm font-semibold text-gray-900">{stat.count}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {stat.last_updated ? new Date(stat.last_updated).toLocaleString() : 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
