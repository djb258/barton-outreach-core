import { useEffect, useState } from 'react';
import AccordionItem from './components/AccordionItem';
import PhaseCard from './components/PhaseCard';
import PhaseDetail from './components/PhaseDetail';
import ErrorConsole from './components/ErrorConsole';
import { fetchPhaseStats } from './services/neon';
import type { PhaseStats } from './services/neon';
import './App.css';

function AppDefault() {
  const [phaseStats, setPhaseStats] = useState<PhaseStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  console.log('AppDefault rendering...');

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const stats = await fetchPhaseStats();
      setPhaseStats(stats);
      setError(null);
    } catch (err) {
      console.error('Error loading phase stats:', err);
      // Use sample data as fallback when API is unavailable
      const sampleData: PhaseStats[] = [
        { phase: 'Company Discovery', status: 'completed', count: 245, last_updated: new Date().toISOString() },
        { phase: 'Company Discovery', status: 'processing', count: 18, last_updated: new Date().toISOString() },
        { phase: 'Company Discovery', status: 'pending', count: 37, last_updated: new Date().toISOString() },
        { phase: 'People Enrichment', status: 'completed', count: 156, last_updated: new Date().toISOString() },
        { phase: 'People Enrichment', status: 'processing', count: 12, last_updated: new Date().toISOString() },
        { phase: 'People Enrichment', status: 'pending', count: 52, last_updated: new Date().toISOString() },
        { phase: 'Email Validation', status: 'completed', count: 89, last_updated: new Date().toISOString() },
        { phase: 'Email Validation', status: 'processing', count: 8, last_updated: new Date().toISOString() },
        { phase: 'Email Validation', status: 'pending', count: 23, last_updated: new Date().toISOString() },
      ];
      setPhaseStats(sampleData);
      setError('Note: Using sample data (backend API not available)');
    } finally {
      setLoading(false);
    }
  };

  // Group stats by phase
  const groupedStats = phaseStats.reduce((acc, stat) => {
    if (!acc[stat.phase]) {
      acc[stat.phase] = [];
    }
    acc[stat.phase].push(stat);
    return acc;
  }, {} as Record<string, PhaseStats[]>);

  const phases = Object.keys(groupedStats);
  const totalCompanies = phaseStats.reduce((sum, stat) => sum + stat.count, 0);

  // Apify actor mappings for each phase (customize these)
  const apifyActors: Record<string, string> = {
    'Company Discovery': 'apify/actor-id-1',
    'People Enrichment': 'apify/actor-id-2',
    'Email Validation': 'apify/actor-id-3',
    // Add more phase -> actor mappings as needed
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', backgroundColor: 'white', padding: '40px', borderRadius: '8px' }}>
          <div style={{ width: '50px', height: '50px', border: '4px solid #4f46e5', borderRightColor: 'transparent', borderRadius: '50%', margin: '0 auto 20px', animation: 'spin 1s linear infinite' }}></div>
          <p style={{ color: '#666', fontSize: '18px' }}>Loading Outreach Command Center...</p>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-lg border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Outreach Command Center
              </h1>
              <p className="text-gray-600 mt-1">
                Pipeline monitoring and management dashboard
              </p>
            </div>
            <div className="text-right">
              <div className="text-4xl font-bold text-indigo-600">{totalCompanies}</div>
              <div className="text-sm text-gray-600">Total Companies</div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 bg-blue-50 border border-blue-200 text-blue-800 px-6 py-4 rounded-lg">
            <p className="font-semibold">ℹ️ Info:</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* System Overview Accordion */}
        <AccordionItem title="System Overview" defaultOpen={true} badge={phases.length}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {phases.map((phase) => (
              <PhaseCard
                key={phase}
                phase={phase}
                stats={groupedStats[phase]}
              />
            ))}
          </div>
        </AccordionItem>

        {/* Error Console Accordion */}
        <AccordionItem title="Error Console" badge="Alert">
          <ErrorConsole />
        </AccordionItem>

        {/* Individual Phase Details */}
        {phases.map((phase) => {
          const phaseStatsList = groupedStats[phase];
          const totalCount = phaseStatsList.reduce((sum, stat) => sum + stat.count, 0);

          return (
            <AccordionItem
              key={phase}
              title={`${phase} Details`}
              badge={totalCount}
            >
              <PhaseDetail
                phase={phase}
                stats={phaseStatsList}
                apifyActorId={apifyActors[phase]}
              />
            </AccordionItem>
          );
        })}

        {/* Refresh Footer */}
        <div className="mt-8 text-center">
          <button
            onClick={loadData}
            className="inline-flex items-center gap-2 px-6 py-3 bg-white text-indigo-600 border-2 border-indigo-600 rounded-lg font-semibold hover:bg-indigo-600 hover:text-white transition-colors shadow-md"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Refresh All Data
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-4 text-center text-gray-600 text-sm">
          <p>Barton Outreach Core &copy; 2025 | Powered by Neon, n8n & Apify</p>
        </div>
      </footer>
    </div>
  );
}

export default AppDefault;
