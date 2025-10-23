/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/cli
Barton ID: 04.04.14
Unique ID: CTB-54E4A7FB
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

// FILE: cli/kickoff.ts (Run a workflow manually for testing)
import { bootOrchestration, shutdownOrchestration, getSystemStatus } from '../server/start-orchestrators';

async function run() {
  console.log('🚀 Booting orchestration system...');
  const master = await bootOrchestration();
  
  // Get workflow type from command line args or env
  const workflowType = process.argv[2] || process.env.WORKFLOW_TYPE || 'lead_only';
  
  // Validate workflow type
  const validWorkflows = ['full_pipeline', 'lead_only', 'messaging_only', 'custom'];
  if (!validWorkflows.includes(workflowType)) {
    console.error(`❌ Invalid workflow type: ${workflowType}`);
    console.log(`Valid options: ${validWorkflows.join(', ')}`);
    process.exit(1);
  }

  // Configuration from environment or defaults
  const config = {
    blueprint_id: process.env.BLUEPRINT_ID ?? 'PLE-001',
    unique_id: process.env.LEAD_UNIQUE_ID ?? '04.01.01.04.20000.003',
    company_id: process.env.TEST_COMPANY_ID ?? 'cmp_12345',
    batch_size: Number(process.env.BATCH_SIZE) || 50,
    csv_file_path: process.env.CSV_FILE_PATH,
    
    // Lead processing config
    role_requirements: {
      ceo: process.env.INCLUDE_CEO !== 'false',
      cfo: process.env.INCLUDE_CFO !== 'false', 
      hr: process.env.INCLUDE_HR !== 'false'
    },
    
    // Validation settings
    validation_settings: {
      provider: process.env.VALIDATION_PROVIDER || 'MillionVerifier',
      confidence_threshold: Number(process.env.VALIDATION_THRESHOLD) || 0.8
    },
    
    // Rate limits for delivery
    rate_limits: {
      email_per_hour: Number(process.env.EMAIL_RATE_LIMIT) || 100,
      linkedin_per_hour: Number(process.env.LINKEDIN_RATE_LIMIT) || 50
    }
  };

  console.log(`📋 Configuration:`, {
    workflow: workflowType,
    blueprint_id: config.blueprint_id,
    unique_id: config.unique_id,
    batch_size: config.batch_size,
    csv_file: config.csv_file_path || 'none'
  });

  try {
    // Show initial status
    const initialStatus = getSystemStatus();
    console.log(`🔄 Initial system status: ${initialStatus.overall_status}`);
    
    // Execute workflow
    console.log(`🎯 Starting ${workflowType} workflow...`);
    const startTime = Date.now();
    
    await master.executeWorkflow(workflowType as any, config);
    
    const duration = Date.now() - startTime;
    console.log(`✅ Workflow '${workflowType}' completed in ${duration}ms`);
    
    // Show final status
    const finalStatus = getSystemStatus();
    console.log(`📊 Final system status:`, {
      overall_status: finalStatus.overall_status,
      overall_progress: finalStatus.overall_progress,
      branches: finalStatus.branches.map(b => ({
        id: b.branch_id,
        status: b.status,
        progress: b.progress_percentage
      }))
    });
    
  } catch (error) {
    console.error(`❌ Workflow '${workflowType}' failed:`, error);
    
    // Show error status
    const errorStatus = getSystemStatus();
    console.log(`🚨 System status after error:`, {
      overall_status: errorStatus.overall_status,
      error_branches: errorStatus.branches.filter(b => b.status === 'error')
    });
    
    throw error;
  } finally {
    // Always shutdown gracefully
    console.log('🛑 Shutting down orchestration system...');
    await shutdownOrchestration();
    console.log('✅ Shutdown complete');
  }
}

// Handle CLI arguments and help
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  console.log(`
🚀 Barton Outreach Core - Workflow CLI

Usage: npm run kickoff [workflow_type]

Workflow Types:
  full_pipeline  - Complete lead → messaging → delivery pipeline
  lead_only      - Lead ingestion, canonicalization, and validation only
  messaging_only - Message composition and approval only
  custom         - Custom workflow with advanced configuration

Environment Variables:
  WORKFLOW_TYPE=lead_only           # Default workflow if not specified
  BLUEPRINT_ID=PLE-001              # Process blueprint identifier
  LEAD_UNIQUE_ID=04.01.01.04.20000.003  # Unique process step ID
  TEST_COMPANY_ID=cmp_12345         # Test company ID
  BATCH_SIZE=50                     # Processing batch size
  CSV_FILE_PATH=/path/to/leads.csv  # CSV file for lead ingestion
  
  INCLUDE_CEO=true                  # Include CEO role slots
  INCLUDE_CFO=true                  # Include CFO role slots  
  INCLUDE_HR=true                   # Include HR role slots
  
  VALIDATION_PROVIDER=MillionVerifier  # Email validation provider
  VALIDATION_THRESHOLD=0.8          # Validation confidence threshold
  
  EMAIL_RATE_LIMIT=100              # Emails per hour limit
  LINKEDIN_RATE_LIMIT=50            # LinkedIn messages per hour limit

Examples:
  npm run kickoff lead_only
  npm run kickoff full_pipeline
  BATCH_SIZE=25 npm run kickoff messaging_only
  `);
  process.exit(0);
}

run().catch((e) => {
  console.error('❌ CLI execution failed:', e);
  process.exit(1);
});