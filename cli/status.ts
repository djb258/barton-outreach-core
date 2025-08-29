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