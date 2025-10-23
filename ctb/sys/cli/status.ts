/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/cli
Barton ID: 04.04.14
Unique ID: CTB-E209FE2B
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

// NEW FILE: cli/status.ts
import { bootOrchestration, shutdownOrchestration } from '../server/start-orchestrators';

(async () => {
  try {
    const master = await bootOrchestration();
    const status = master.getProjectStatus?.();
    console.log(JSON.stringify(status ?? { overall_status: 'unknown' }, null, 2));
  } catch (error) {
    console.error('❌ Status check failed:', error);
    console.log(JSON.stringify({ overall_status: 'error', error: error instanceof Error ? error.message : 'Unknown error' }, null, 2));
    process.exit(1);
  } finally {
    await shutdownOrchestration();
  }
})();