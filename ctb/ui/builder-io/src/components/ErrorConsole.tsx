/**
 * Error Console Component
 * Displays recent errors from both Neon database and n8n workflows
 */

import { useEffect, useState } from 'react';
import { fetchRecentErrors } from '../services/neon';
import type { RecentError } from '../services/neon';
import { fetchN8nErrors } from '../services/n8n';
import type { N8nExecution } from '../services/n8n';

export default function ErrorConsole() {
  const [neonErrors, setNeonErrors] = useState<RecentError[]>([]);
  const [n8nErrors, setN8nErrors] = useState<N8nExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'neon' | 'n8n'>('neon');

  useEffect(() => {
    loadErrors();
    const interval = setInterval(loadErrors, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadErrors = async () => {
    try {
      // Fetch with individual error handling so one failure doesn't block both
      let neonData: RecentError[] = [];
      let n8nData: N8nExecution[] = [];

      try {
        neonData = await fetchRecentErrors();
      } catch (error) {
        console.error('Failed to load Neon errors:', error);
      }

      try {
        n8nData = await fetchN8nErrors();
      } catch (error) {
        console.error('Failed to load n8n errors:', error);
      }

      setNeonErrors(neonData);
      setN8nErrors(n8nData);
    } catch (error) {
      console.error('Failed to load errors:', error);
      setNeonErrors([]);
      setN8nErrors([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('neon')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'neon'
              ? 'text-red-600 border-b-2 border-red-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Neon Errors
          <span className="ml-2 px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">
            {neonErrors.length}
          </span>
        </button>
        <button
          onClick={() => setActiveTab('n8n')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'n8n'
              ? 'text-red-600 border-b-2 border-red-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          n8n Errors
          <span className="ml-2 px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">
            {n8nErrors.length}
          </span>
        </button>
      </div>

      {/* Error Lists */}
      <div className="max-h-96 overflow-y-auto">
        {activeTab === 'neon' ? (
          <div className="space-y-3">
            {neonErrors.length === 0 ? (
              <p className="text-center text-gray-500 py-8">No Neon errors found</p>
            ) : (
              neonErrors.map((error) => (
                <div
                  key={error.error_id}
                  className="bg-red-50 border border-red-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="px-2 py-1 bg-red-600 text-white text-xs font-medium rounded">
                          {error.phase}
                        </span>
                        <span className="px-2 py-1 bg-gray-200 text-gray-700 text-xs font-medium rounded">
                          {error.error_type}
                        </span>
                      </div>
                      <p className="text-sm text-gray-800 mb-2 font-mono">
                        {error.error_message}
                      </p>
                      {error.company_id && (
                        <p className="text-xs text-gray-600">
                          Company: <span className="font-medium">{error.company_id}</span>
                        </p>
                      )}
                    </div>
                    <span className="text-xs text-gray-500 whitespace-nowrap ml-4">
                      {new Date(error.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {n8nErrors.length === 0 ? (
              <p className="text-center text-gray-500 py-8">No n8n errors found</p>
            ) : (
              n8nErrors.map((execution) => (
                <div
                  key={execution.id}
                  className="bg-orange-50 border border-orange-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="px-2 py-1 bg-orange-600 text-white text-xs font-medium rounded">
                          Workflow
                        </span>
                        {execution.workflowName && (
                          <span className="text-sm font-semibold text-gray-800">
                            {execution.workflowName}
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-gray-600 space-y-1">
                        <p>
                          ID: <span className="font-mono">{execution.id}</span>
                        </p>
                        <p>
                          Workflow ID: <span className="font-mono">{execution.workflowId}</span>
                        </p>
                        <p>
                          Mode: <span className="font-medium">{execution.mode}</span>
                        </p>
                      </div>
                    </div>
                    <div className="text-right ml-4">
                      <p className="text-xs text-gray-500 mb-1">Started</p>
                      <p className="text-xs text-gray-700 whitespace-nowrap">
                        {new Date(execution.startedAt).toLocaleString()}
                      </p>
                      {execution.stoppedAt && (
                        <>
                          <p className="text-xs text-gray-500 mt-2 mb-1">Stopped</p>
                          <p className="text-xs text-gray-700 whitespace-nowrap">
                            {new Date(execution.stoppedAt).toLocaleString()}
                          </p>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Refresh Button */}
      <div className="flex justify-end pt-4 border-t border-gray-200">
        <button
          onClick={loadErrors}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Refresh Errors
        </button>
      </div>
    </div>
  );
}
