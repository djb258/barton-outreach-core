/**
 * Overall Orchestrator - Barton Outreach Core
 * 
 * Coordinates cross-branch flow, enforces guardrails, manages retries/DLQ, emits heartbeats.
 * Verifies all step unique_id mappings exist in shq_process_key_reference.
 */

import { GlobalDatabaseAgent, DatabaseOperation } from '../global-database-agent';

export interface WebhookEvent {
  type: 'ingest_done' | 'scrape_done' | 'validate_done' | 'message_ready' | 'send_result' | 'reply_event';
  payload: any;
  source_branch: string;
  timestamp: string;
  unique_id: string;
  process_id: string;
}

export interface QueueTransition {
  queue_name: string;
  record_id: string;
  from_status: string;
  to_status: string;
  unique_id: string;
  process_id: string;
  error_details?: string;
}

export interface ProcessKeyReference {
  unique_id: string;
  process_id: string;
  blueprint_version_hash: string;
  human_description: string;
  branch_id: string;
  step_name: string;
  created_at: string;
}

export class OverallOrchestrator {
  private databaseAgent: GlobalDatabaseAgent;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private processKeyCache: Map<string, ProcessKeyReference> = new Map();
  private retryQueue: WebhookEvent[] = [];
  private deadLetterQueue: WebhookEvent[] = [];

  constructor(databaseAgent: GlobalDatabaseAgent) {
    this.databaseAgent = databaseAgent;
  }

  // ============================================
  // Initialization & Registry Enforcement
  // ============================================

  async initialize(): Promise<void> {
    console.log('🚀 Initializing Overall Orchestrator...');
    
    // Load process key reference cache
    await this.loadProcessKeyReference();
    
    // Start heartbeat emission
    this.startHeartbeatEmission();
    
    // Verify queue schemas exist
    await this.verifyQueueSchemas();
    
    console.log('✅ Overall Orchestrator initialized');
  }

  private async loadProcessKeyReference(): Promise<void> {
    try {
      const result = await this.databaseAgent.execute({
        id: `load-process-keys-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'shq',
        table: 'process_key_reference',
        operation: 'select'
      });

      if (!result.success) {
        throw new Error('Failed to load process key reference');
      }

      // Cache all process keys
      this.processKeyCache.clear();
      (result.returned_data || []).forEach((row: ProcessKeyReference) => {
        this.processKeyCache.set(row.unique_id, row);
      });

      console.log(`📚 Loaded ${this.processKeyCache.size} process key mappings`);
    } catch (error) {
      console.error('❌ Failed to load process key reference:', error);
      throw new Error('CRITICAL: Cannot operate without process key reference');
    }
  }

  private async verifyQueueSchemas(): Promise<void> {
    const requiredQueues = [
      'outreach.lead_queue',
      'messaging.compose_queue',
      'messaging.approval_queue',
      'delivery.send_queue',
      'delivery.reply_queue'
    ];

    for (const queueName of requiredQueues) {
      const [schema, table] = queueName.split('.');
      
      try {
        await this.databaseAgent.execute({
          id: `verify-queue-${table}`,
          connection_name: 'marketing',
          database: 'Marketing DB',
          schema,
          table,
          operation: 'select',
          options: { return_data: false }
        });
      } catch (error) {
        console.error(`❌ Queue ${queueName} not accessible:`, error);
        throw new Error(`CRITICAL: Required queue ${queueName} not available`);
      }
    }

    console.log('✅ All required queues verified');
  }

  // ============================================
  // Webhook Event Processing
  // ============================================

  async processWebhookEvent(event: WebhookEvent): Promise<void> {
    console.log(`📨 Processing webhook: ${event.type} from ${event.source_branch}`);

    try {
      // Verify unique_id exists in process key reference
      await this.enforceProcessKeyMapping(event.unique_id, event.process_id);

      // Route event to appropriate handler
      switch (event.type) {
        case 'ingest_done':
          await this.handleIngestDone(event);
          break;
        case 'scrape_done':
          await this.handleScrapeDone(event);
          break;
        case 'validate_done':
          await this.handleValidateDone(event);
          break;
        case 'message_ready':
          await this.handleMessageReady(event);
          break;
        case 'send_result':
          await this.handleSendResult(event);
          break;
        case 'reply_event':
          await this.handleReplyEvent(event);
          break;
        default:
          throw new Error(`Unknown webhook event type: ${event.type}`);
      }

      // Emit heartbeat for successful processing
      await this.emitHeartbeat('webhook_processed', {
        event_type: event.type,
        source_branch: event.source_branch,
        unique_id: event.unique_id
      });

    } catch (error) {
      console.error(`❌ Webhook processing failed:`, error);
      await this.handleEventError(event, error);
    }
  }

  private async enforceProcessKeyMapping(uniqueId: string, processId: string): Promise<void> {
    const processKey = this.processKeyCache.get(uniqueId);
    
    if (!processKey) {
      const errorMsg = `UNMAPPED UNIQUE_ID: ${uniqueId} not found in shq_process_key_reference. ` +
        `ACTION REQUIRED: Insert mapping for process_id="${processId}" before proceeding.`;
      
      await this.logMasterError('process_key_unmapped', errorMsg, {
        unique_id: uniqueId,
        process_id: processId,
        available_keys: Array.from(this.processKeyCache.keys()).slice(0, 10) // Show first 10 for debugging
      });
      
      throw new Error(errorMsg);
    }

    // Verify process_id matches if provided
    if (processKey.process_id !== processId) {
      const errorMsg = `PROCESS_ID MISMATCH: ${uniqueId} maps to "${processKey.process_id}" but event has "${processId}"`;
      await this.logMasterError('process_id_mismatch', errorMsg, { unique_id: uniqueId, expected: processKey.process_id, actual: processId });
      throw new Error(errorMsg);
    }

    console.log(`✅ Process key verified: ${uniqueId} → ${processKey.human_description}`);
  }

  // ============================================
  // Event Handlers
  // ============================================

  private async handleIngestDone(event: WebhookEvent): Promise<void> {
    // Transition lead_queue items to 'queued' for canonicalization
    await this.transitionQueueStatus(
      'outreach.lead_queue',
      event.payload.record_ids || [],
      'ingesting',
      'queued',
      event.unique_id,
      event.process_id
    );

    // Trigger Branch1 orchestrator
    await this.triggerBranchOrchestrator('branch1', 'canonicalize', {
      source_event: event,
      record_ids: event.payload.record_ids
    });
  }

  private async handleScrapeDone(event: WebhookEvent): Promise<void> {
    // Transition lead_queue items to 'validating'
    await this.transitionQueueStatus(
      'outreach.lead_queue',
      event.payload.slot_ids || [],
      'scraping',
      'validating',
      event.unique_id,
      event.process_id
    );

    // Trigger validation in Branch1
    await this.triggerBranchOrchestrator('branch1', 'validate', {
      source_event: event,
      slot_ids: event.payload.slot_ids,
      scraped_contacts: event.payload.contacts
    });
  }

  private async handleValidateDone(event: WebhookEvent): Promise<void> {
    if (event.payload.success) {
      // Move to messaging queue
      await this.transitionQueueStatus(
        'messaging.compose_queue',
        event.payload.person_ids || [],
        'pending',
        'queued',
        event.unique_id,
        event.process_id
      );

      // Trigger Branch2 orchestrator
      await this.triggerBranchOrchestrator('branch2', 'persona_resolve', {
        source_event: event,
        person_ids: event.payload.person_ids
      });
    } else {
      // Mark as failed in lead queue
      await this.transitionQueueStatus(
        'outreach.lead_queue',
        event.payload.person_ids || [],
        'validating',
        'error',
        event.unique_id,
        event.process_id,
        event.payload.error_details
      );
    }
  }

  private async handleMessageReady(event: WebhookEvent): Promise<void> {
    // Move to delivery queue
    await this.transitionQueueStatus(
      'delivery.send_queue',
      event.payload.message_ids || [],
      'pending',
      'queued',
      event.unique_id,
      event.process_id
    );

    // Trigger Branch3 orchestrator
    await this.triggerBranchOrchestrator('branch3', 'channel_map', {
      source_event: event,
      message_ids: event.payload.message_ids
    });
  }

  private async handleSendResult(event: WebhookEvent): Promise<void> {
    if (event.payload.success) {
      await this.transitionQueueStatus(
        'delivery.send_queue',
        event.payload.message_ids || [],
        'sending',
        'sent',
        event.unique_id,
        event.process_id
      );
    } else {
      await this.transitionQueueStatus(
        'delivery.send_queue',
        event.payload.message_ids || [],
        'sending',
        'error',
        event.unique_id,
        event.process_id,
        event.payload.error_details
      );

      // Add to retry queue if retryable
      if (event.payload.retryable) {
        this.addToRetryQueue(event);
      } else {
        this.addToDeadLetterQueue(event);
      }
    }
  }

  private async handleReplyEvent(event: WebhookEvent): Promise<void> {
    // Add to reply processing queue
    await this.transitionQueueStatus(
      'delivery.reply_queue',
      [event.payload.reply_id],
      'pending',
      'queued',
      event.unique_id,
      event.process_id
    );

    // Trigger reply processing in Branch3
    await this.triggerBranchOrchestrator('branch3', 'parse_reply', {
      source_event: event,
      reply_data: event.payload
    });
  }

  // ============================================
  // Queue Management
  // ============================================

  private async transitionQueueStatus(
    queueName: string,
    recordIds: string[],
    fromStatus: string,
    toStatus: string,
    uniqueId: string,
    processId: string,
    errorDetails?: string
  ): Promise<void> {
    const [schema, table] = queueName.split('.');

    for (const recordId of recordIds) {
      try {
        const updateData: any = {
          status: toStatus,
          updated_at: new Date().toISOString(),
          unique_id: uniqueId,
          process_id: processId
        };

        if (errorDetails) {
          updateData.error_details = errorDetails;
          updateData.error_count = 'error_count + 1'; // SQL expression
        }

        await this.databaseAgent.execute({
          id: `queue-transition-${recordId}`,
          connection_name: 'marketing',
          database: 'Marketing DB',
          schema,
          table,
          operation: 'update',
          data: updateData,
          where: { 
            id: recordId,
            status: fromStatus 
          }
        });

        console.log(`🔄 Queue transition: ${queueName}[${recordId}] ${fromStatus} → ${toStatus}`);
      } catch (error) {
        await this.logMasterError('queue_transition_failed', 
          `Failed to transition ${queueName}[${recordId}] from ${fromStatus} to ${toStatus}`,
          { queue: queueName, record_id: recordId, from_status: fromStatus, to_status: toStatus, error }
        );
      }
    }
  }

  // ============================================
  // Branch Orchestrator Coordination
  // ============================================

  private async triggerBranchOrchestrator(branchId: string, action: string, payload: any): Promise<void> {
    // This would typically send a message to the specific branch orchestrator
    // For now, we'll log the trigger
    console.log(`🎯 Triggering ${branchId} orchestrator: ${action}`, {
      payload_size: JSON.stringify(payload).length,
      timestamp: new Date().toISOString()
    });

    // In a real implementation, this might:
    // - Send to a message queue
    // - Call a REST endpoint
    // - Invoke a function directly
    // - Publish to an event bus
  }

  // ============================================
  // Error Handling & Retry Logic
  // ============================================

  private async handleEventError(event: WebhookEvent, error: any): Promise<void> {
    await this.logMasterError('webhook_processing_failed', 
      `Failed to process ${event.type} from ${event.source_branch}`,
      { 
        event, 
        error_message: error instanceof Error ? error.message : 'Unknown error',
        stack_trace: error instanceof Error ? error.stack : undefined
      }
    );

    // Determine if retryable
    if (this.isRetryableError(error)) {
      this.addToRetryQueue(event);
    } else {
      this.addToDeadLetterQueue(event);
    }
  }

  private isRetryableError(error: any): boolean {
    const retryableErrors = [
      'connection timeout',
      'temporary network error',
      'rate limit exceeded',
      'service unavailable'
    ];

    const errorMessage = error instanceof Error ? error.message.toLowerCase() : String(error).toLowerCase();
    return retryableErrors.some(retryable => errorMessage.includes(retryable));
  }

  private addToRetryQueue(event: WebhookEvent): void {
    this.retryQueue.push({
      ...event,
      timestamp: new Date().toISOString() // Update timestamp for retry
    });
    console.log(`🔄 Added to retry queue: ${event.type} from ${event.source_branch}`);
  }

  private addToDeadLetterQueue(event: WebhookEvent): void {
    this.deadLetterQueue.push(event);
    console.log(`💀 Added to dead letter queue: ${event.type} from ${event.source_branch}`);
  }

  async processRetryQueue(): Promise<void> {
    const retryBatch = this.retryQueue.splice(0, 10); // Process 10 at a time
    
    for (const event of retryBatch) {
      try {
        await this.processWebhookEvent(event);
        console.log(`✅ Retry successful: ${event.type}`);
      } catch (error) {
        console.error(`❌ Retry failed: ${event.type}`, error);
        this.addToDeadLetterQueue(event);
      }
    }
  }

  // ============================================
  // Logging & Heartbeats
  // ============================================

  private async logMasterError(errorType: string, message: string, details: any): Promise<void> {
    try {
      await this.databaseAgent.execute({
        id: `master-error-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'shq',
        table: 'master_error_log',
        operation: 'insert',
        data: {
          agent_id: 'overall-orchestrator',
          error_type: errorType,
          error_message: message,
          error_details: JSON.stringify(details),
          unique_id: details.unique_id || null,
          process_id: details.process_id || null,
          created_at: new Date().toISOString()
        }
      });
    } catch (logError) {
      console.error('❌ Failed to log to master_error_log:', logError);
    }
  }

  private startHeartbeatEmission(): void {
    this.heartbeatInterval = setInterval(async () => {
      await this.emitHeartbeat('orchestrator_alive', {
        retry_queue_size: this.retryQueue.length,
        dead_letter_queue_size: this.deadLetterQueue.length,
        process_key_cache_size: this.processKeyCache.size
      });
    }, 30000); // Every 30 seconds
  }

  private async emitHeartbeat(heartbeatType: string, payload: any): Promise<void> {
    try {
      await this.databaseAgent.execute({
        id: `heartbeat-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'shq',
        table: 'heartbeat_log',
        operation: 'insert',
        data: {
          agent_id: 'overall-orchestrator',
          heartbeat_type: heartbeatType,
          payload: JSON.stringify(payload),
          timestamp: new Date().toISOString(),
          blueprint_version_hash: 'v1.0.0'
        }
      });
    } catch (error) {
      console.error('❌ Failed to emit heartbeat:', error);
    }
  }

  // ============================================
  // Public Interface
  // ============================================

  async getStatus(): Promise<any> {
    return {
      agent_id: 'overall-orchestrator',
      status: 'active',
      process_keys_loaded: this.processKeyCache.size,
      retry_queue_size: this.retryQueue.length,
      dead_letter_queue_size: this.deadLetterQueue.length,
      last_heartbeat: new Date().toISOString()
    };
  }

  async shutdown(): Promise<void> {
    console.log('🛑 Shutting down Overall Orchestrator...');
    
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }

    // Final heartbeat
    await this.emitHeartbeat('orchestrator_shutdown', {
      final_retry_queue_size: this.retryQueue.length,
      final_dead_letter_size: this.deadLetterQueue.length
    });

    console.log('✅ Overall Orchestrator shutdown complete');
  }

  // Debug methods
  getProcessKeyCache(): Map<string, ProcessKeyReference> {
    return new Map(this.processKeyCache);
  }

  getRetryQueue(): WebhookEvent[] {
    return [...this.retryQueue];
  }

  getDeadLetterQueue(): WebhookEvent[] {
    return [...this.deadLetterQueue];
  }
}