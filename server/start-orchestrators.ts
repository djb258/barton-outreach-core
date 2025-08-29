// FILE: server/start-orchestrators.ts
import { createBartonMasterOrchestrator } from '@/lib/agents/orchestrators/master-orchestrator';
import { createLeadBranchOrchestrator } from '@/lib/agents/orchestrators/lead-branch-orchestrator';
import { createMessagingBranchOrchestrator } from '@/lib/agents/orchestrators/messaging-branch-orchestrator';
import { createDeliveryBranchOrchestrator } from '@/lib/agents/orchestrators/delivery-branch-orchestrator';
import { GlobalDatabaseAgent } from '@/lib/agents/global-database-agent';

import { neonPool } from '@/lib/neon';                 // pooled Neon client (RLS-enabled service user)
import { queue } from '@/lib/queue';                   // lead/send/reply queue adapters
import { apify } from '@/lib/apify';                   // Apify SDK wrapper
import { deliverySdk } from '@/lib/delivery';          // Instantly/HeyReach wrapper
import { validator } from '@/lib/validator';           // Validator service client
import { keyRef } from '@/lib/shq_process_key_reference'; // Barton ID lookup (read-only)

let __MASTER__: any | null = null;

export async function bootOrchestration() {
  if (__MASTER__) return __MASTER__;

  // Guard: required env
  const required = ['NEON_DATABASE_URL'];
  for (const k of required) if (!process.env[k]) throw new Error(`Missing env: ${k}`);

  // Initialize shared database agent
  const databaseAgent = new GlobalDatabaseAgent();

  // Create master orchestrator (no dependencies needed in constructor)
  const master = createBartonMasterOrchestrator();

  // Create branch orchestrators with proper database agent dependencies
  const lead = createLeadBranchOrchestrator();
  lead.injectDependencies({
    databaseAgent,
    apifyAgent: apify,
    validationAgent: validator
  });

  const messaging = createMessagingBranchOrchestrator(databaseAgent);
  // Optional: inject LLM and template dependencies if available
  // messaging.injectDependencies({ llmAgent, templateEngine, policyChecker });

  const delivery = createDeliveryBranchOrchestrator(databaseAgent);
  delivery.injectDependencies({
    instantlyAgent: deliverySdk?.instantly,
    heyreachAgent: deliverySdk?.heyreach
  });

  // Register branch orchestrators with master
  master.registerBranchOrchestrator('lead', lead);
  master.registerBranchOrchestrator('messaging', messaging);
  master.registerBranchOrchestrator('delivery', delivery);

  // Optional: emit heartbeat on boot if method exists
  try {
    const masterStatus = master.getProjectStatus();
    console.log('🚀 Orchestration system booted:', {
      overall_status: masterStatus.overall_status,
      total_branches: masterStatus.branches.length
    });
  } catch (error) {
    console.warn('⚠️ Could not get initial master status:', error);
  }

  __MASTER__ = master;
  (global as any).__MASTER__ = master; // expose for webhooks
  return master;
}

export function getMasterOrchestrator() {
  if (!__MASTER__) throw new Error('Master orchestrator not booted yet. Call bootOrchestration() first.');
  return __MASTER__;
}

// Utility function to execute workflows
export async function executeWorkflow(
  workflowType: 'full_pipeline' | 'lead_only' | 'messaging_only' | 'custom',
  config?: any
) {
  const master = getMasterOrchestrator();
  return await master.executeWorkflow(workflowType, config);
}

// Utility function to get system status
export function getSystemStatus() {
  const master = getMasterOrchestrator();
  return master.getProjectStatus();
}

// Graceful shutdown
export async function shutdownOrchestration() {
  if (__MASTER__) {
    await __MASTER__.shutdown();
    __MASTER__ = null;
    (global as any).__MASTER__ = null;
    console.log('✅ Orchestration system shutdown complete');
  }
}