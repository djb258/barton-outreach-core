// NEW FILE: cli/trigger.ts
import { bootOrchestration, shutdownOrchestration } from '../server/start-orchestrators';

(async () => {
  try {
    console.log('🚀 Booting orchestration...');
    const master = await bootOrchestration();
    
    const type = process.argv[2] || 'lead_only'; // full_pipeline | lead_only | messaging_only | delivery_only
    const batch = Number(process.env.BATCH_SIZE || 25);
    
    console.log(`📋 Triggering ${type} workflow (batch=${batch})`);
    
    await master.executeWorkflow(type, {
      batch_size: batch,
      blueprint_id: process.env.BLUEPRINT_ID ?? 'PLE-001',
      unique_id: process.env.LEAD_UNIQUE_ID ?? '04.01.01.04.20000.003',
      csv_file_path: process.env.CSV_FILE_PATH, // optional
    });
    
    console.log(`✅ [trigger] completed ${type} (batch=${batch})`);
  } catch (error) {
    console.error('❌ Trigger failed:', error);
    process.exit(1);
  } finally {
    console.log('🛑 Shutting down...');
    await shutdownOrchestration();
  }
})();