import React from 'react';
import PhaseGroup from '../../components/doctrine/PhaseGroup';
import { Step } from '../../types';
import { useDoctrineSteps } from '../../hooks/useDoctrineSteps';
import demoProcesses from '../../data/demo_processes.json';

interface ProcessDetailViewProps {
  microprocess_id?: string;
  blueprint_id?: string;
  useDemoData?: boolean;
}

/**
 * ProcessDetailView - Main view for Doctrine Tracker
 * Groups processes by altitude and displays in hierarchical view
 * Supports both dynamic MCP data fetching and demo data fallback
 * Demonstrates Barton Doctrine compliance visualization
 */
const ProcessDetailView: React.FC<ProcessDetailViewProps> = ({
  microprocess_id,
  blueprint_id,
  useDemoData = false
}) => {
  // Fetch data from MCP server unless using demo data
  const {
    steps: mcpSteps,
    loading,
    error,
    stepsByAltitude,
    totalSteps
  } = useDoctrineSteps({
    microprocess_id: useDemoData ? undefined : microprocess_id,
    blueprint_id: useDemoData ? undefined : blueprint_id
  });

  // Use demo data if specified or if MCP fetch fails
  const demoData: Step[] = demoProcesses as Step[];
  const processes: Step[] = useDemoData || (error && mcpSteps.length === 0) ? demoData : mcpSteps;

  // Loading state
  if (loading && !useDemoData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-lg font-semibold text-gray-900">Loading Doctrine Steps...</h2>
          <p className="text-sm text-gray-600 mt-2">Fetching from MCP server</p>
        </div>
      </div>
    );
  }

  // Error state (with demo data fallback)
  if (error && !useDemoData && processes.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-red-500 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">MCP Connection Error</h2>
          <p className="text-sm text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  // Group processes by altitude
  const groupedProcesses = processes.reduce((groups, process) => {
    const altitude = process.altitude;
    if (!groups[altitude]) {
      groups[altitude] = [];
    }
    groups[altitude].push(process);
    return groups;
  }, {} as Record<number, Step[]>);

  // Sort altitudes in descending order (Vision -> Category -> Execution)
  const sortedAltitudes = Object.keys(groupedProcesses)
    .map(Number)
    .sort((a, b) => b - a);

  // Get altitude title
  const getAltitudeTitle = (altitude: number): string => {
    switch (altitude) {
      case 30000:
        return 'Vision Phase - Strategic Planning';
      case 20000:
        return 'Category Phase - Process Definition';
      case 10000:
        return 'Execution Phase - Implementation';
      default:
        return `Altitude ${altitude} - Custom Phase`;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Barton Doctrine Tracker
              </h1>
              <p className="mt-1 text-sm text-gray-600">
                Process orchestration with altitude-based organization and MCP integration
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                <span className="font-medium">{processes.length}</span> total processes
              </div>
              <div className="flex items-center space-x-2">
                {useDemoData || (error && mcpSteps.length === 0) ? (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    📄 Demo Data
                  </span>
                ) : (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    🔗 Live MCP Data
                  </span>
                )}
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  Builder.io Compatible
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Altitude Legend */}
        <div className="mb-8 bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Barton Doctrine Altitude System</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center space-x-3">
              <div className="w-4 h-4 bg-red-500 rounded"></div>
              <div>
                <div className="font-medium text-red-800">30,000 ft - Vision</div>
                <div className="text-sm text-gray-600">Strategic planning and blueprint design</div>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-4 h-4 bg-yellow-500 rounded"></div>
              <div>
                <div className="font-medium text-yellow-800">20,000 ft - Category</div>
                <div className="text-sm text-gray-600">Process definition and validation</div>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-4 h-4 bg-green-500 rounded"></div>
              <div>
                <div className="font-medium text-green-800">10,000 ft - Execution</div>
                <div className="text-sm text-gray-600">Implementation and data operations</div>
              </div>
            </div>
          </div>
        </div>

        {/* Process Groups by Altitude */}
        <div className="space-y-6">
          {sortedAltitudes.map((altitude) => (
            <PhaseGroup
              key={altitude}
              altitude={altitude}
              title={getAltitudeTitle(altitude)}
              steps={groupedProcesses[altitude]}
            />
          ))}
        </div>

        {/* Empty State */}
        {processes.length === 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <div className="text-gray-400 mb-4">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No processes found</h3>
            <p className="text-gray-600">Import your process data or create new processes to get started.</p>
          </div>
        )}

        {/* Footer */}
        <div className="mt-12 pt-8 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div>
              Barton Doctrine Tracker v1.0 - MCP Integration Ready
            </div>
            <div className="flex items-center space-x-4">
              <span>✅ Builder.io Compatible</span>
              <span>🔗 MCP Enabled</span>
              <span>📊 Altitude Organized</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProcessDetailView;