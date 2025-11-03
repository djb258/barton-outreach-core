/**
 * Builder.io Data Fetching Utilities
 * Helper functions to fetch API data for use in Builder.io components
 */

import { fetchPhaseStats, fetchRecentErrors, fetchCompanyMaster } from '../services/neon';
import { fetchN8nErrors } from '../services/n8n';
import { listApifyActors } from '../services/apify';

/**
 * Fetch all outreach data for Builder.io
 * Can be used in Builder.io data tab or custom code
 */
export async function fetchOutreachData() {
  try {
    const [phaseStats, neonErrors, companyMaster, n8nErrors, apifyActors] = await Promise.allSettled([
      fetchPhaseStats(),
      fetchRecentErrors(),
      fetchCompanyMaster(50),
      fetchN8nErrors(),
      listApifyActors(),
    ]);

    return {
      phaseStats: phaseStats.status === 'fulfilled' ? phaseStats.value : [],
      neonErrors: neonErrors.status === 'fulfilled' ? neonErrors.value : [],
      companyMaster: companyMaster.status === 'fulfilled' ? companyMaster.value : [],
      n8nErrors: n8nErrors.status === 'fulfilled' ? n8nErrors.value : [],
      apifyActors: apifyActors.status === 'fulfilled' ? apifyActors.value : [],
    };
  } catch (error) {
    console.error('[Builder Data] Error fetching outreach data:', error);
    return {
      phaseStats: [],
      neonErrors: [],
      companyMaster: [],
      n8nErrors: [],
      apifyActors: [],
    };
  }
}

/**
 * Group phase stats by phase name
 */
export function groupPhaseStats(stats: any[]) {
  return stats.reduce((acc, stat) => {
    if (!acc[stat.phase]) {
      acc[stat.phase] = [];
    }
    acc[stat.phase].push(stat);
    return acc;
  }, {} as Record<string, any[]>);
}

/**
 * Calculate total companies from phase stats
 */
export function calculateTotalCompanies(stats: any[]) {
  return stats.reduce((sum, stat) => sum + (stat.count || 0), 0);
}

/**
 * Register data functions with window for Builder.io access
 * This allows you to use these functions in Builder.io custom code
 */
if (typeof window !== 'undefined') {
  (window as any).builderData = {
    fetchOutreachData,
    groupPhaseStats,
    calculateTotalCompanies,
  };
}

export default {
  fetchOutreachData,
  groupPhaseStats,
  calculateTotalCompanies,
};
