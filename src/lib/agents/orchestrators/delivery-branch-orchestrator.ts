/**
 * Branch 3 Orchestrator - Delivery Branch
 * 
 * Steps: ChannelMap→RateGuard→Send→Track→ReplyRoute
 * Queues: delivery.send_queue, delivery.reply_queue
 * Neon Targets: delivery.channel_map, delivery.events, delivery.reply_inbox, shq_guardrails
 */

import { GlobalDatabaseAgent } from '../global-database-agent';

export interface DeliveryConfig {
  channel_preferences?: {
    email_priority: number;
    linkedin_priority: number;
    fallback_channel: 'email' | 'linkedin';
  };
  rate_limits?: {
    email_per_hour: number;
    linkedin_per_hour: number;
    daily_limit: number;
    burst_limit: number;
  };
  provider_settings?: {
    instantly_config?: any;
    heyreach_config?: any;
  };
  tracking_settings?: {
    enable_open_tracking: boolean;
    enable_click_tracking: boolean;
    enable_reply_tracking: boolean;
  };
  batch_size?: number;
}

export interface DeliveryStatus {
  stage: 'channel_map' | 'rate_guard' | 'send' | 'track' | 'reply_route' | 'completed';
  messages_processed: number;
  total_messages: number;
  emails_sent: number;
  linkedin_sent: number;
  delivery_failures: number;
  opens_tracked: number;
  clicks_tracked: number;
  replies_received: number;
  errors: string[];
  current_batch?: number;
}

export class DeliveryBranchOrchestrator {
  private databaseAgent: GlobalDatabaseAgent;
  private instantlyAgent: any; // Will be injected
  private heyreachAgent: any;
  private rateLimiter: any;
  private emailParser: any;
  
  private currentStatus: DeliveryStatus;
  private processingConfig: DeliveryConfig = {};
  private rateLimitCounters: Map<string, number> = new Map();

  constructor(databaseAgent: GlobalDatabaseAgent) {
    this.databaseAgent = databaseAgent;
    this.currentStatus = {
      stage: 'channel_map',
      messages_processed: 0,
      total_messages: 0,
      emails_sent: 0,
      linkedin_sent: 0,
      delivery_failures: 0,
      opens_tracked: 0,
      clicks_tracked: 0,
      replies_received: 0,
      errors: []
    };
  }

  // ============================================
  // Dependency Injection
  // ============================================

  injectDependencies(agents: {
    instantlyAgent?: any;
    heyreachAgent?: any;
    rateLimiter?: any;
    emailParser?: any;
  }): void {
    this.instantlyAgent = agents.instantlyAgent;
    this.heyreachAgent = agents.heyreachAgent;
    this.rateLimiter = agents.rateLimiter;
    this.emailParser = agents.emailParser;
    console.log('✅ Delivery Branch dependencies injected');
  }

  // ============================================
  // Main Execution Flow
  // ============================================

  async execute(config?: DeliveryConfig): Promise<void> {
    this.processingConfig = { ...this.processingConfig, ...config };

    try {
      console.log('🚀 Starting Delivery Branch workflow...');
      
      // Step 1: Channel Mapping
      await this.executeChannelMapping();
      
      // Step 2: Rate Guardrails
      await this.executeRateGuardrails();
      
      // Step 3: Send & Track
      await this.executeSendAndTrack();
      
      // Step 4: Reply Routing
      await this.executeReplyRouting();

      this.currentStatus.stage = 'completed';
      console.log('✅ Delivery Branch workflow completed');

    } catch (error) {
      this.currentStatus.errors.push(error instanceof Error ? error.message : 'Unknown error');
      console.error('❌ Delivery Branch workflow failed:', error);
      throw error;
    }
  }

  // ============================================
  // Step 1: Channel Mapping
  // ============================================

  private async executeChannelMapping(): Promise<void> {
    this.currentStatus.stage = 'channel_map';
    console.log('🗺️ Step 1: Channel Mapping');

    try {
      // Get ready messages from messaging branch
      const readyMessages = await this.databaseAgent.execute({
        id: `get-ready-messages-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'messaging',
        table: 'outbox_ready',
        operation: 'select',
        where: { status: 'ready' }
      });

      const messages = readyMessages.returned_data || [];
      this.currentStatus.total_messages = messages.length;

      console.log(`📍 Mapping channels for ${messages.length} messages`);

      // Process in batches
      const batchSize = this.processingConfig.batch_size || 50;
      for (let i = 0; i < messages.length; i += batchSize) {
        const batch = messages.slice(i, i + batchSize);
        await this.processChannelMappingBatch(batch);
        
        this.currentStatus.messages_processed += batch.length;
        console.log(`📈 Channel mapping progress: ${this.currentStatus.messages_processed}/${this.currentStatus.total_messages}`);
      }

      console.log('✅ Channel mapping completed');
    } catch (error) {
      throw new Error(`Channel mapping failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async processChannelMappingBatch(batch: any[]): Promise<void> {
    for (const message of batch) {
      try {
        // Get person contact information
        const personData = await this.getPersonContactInfo(message.person_id);
        
        // Determine best channel
        const channelMapping = await this.determineOptimalChannel(personData);

        // Insert channel mapping
        await this.databaseAgent.execute({
          id: `insert-channel-map-${message.id}`,
          connection_name: 'marketing',
          database: 'Marketing DB',
          schema: 'delivery',
          table: 'channel_map',
          operation: 'insert',
          data: {
            message_id: message.id,
            person_id: message.person_id,
            primary_channel: channelMapping.primary,
            fallback_channel: channelMapping.fallback,
            email_address: personData.email,
            linkedin_url: personData.linkedin_url,
            channel_priority_score: channelMapping.score,
            created_at: new Date().toISOString(),
            status: 'mapped'
          }
        });

        // Add to send queue
        await this.databaseAgent.execute({
          id: `queue-send-${message.id}`,
          connection_name: 'marketing',
          database: 'Marketing DB',
          schema: 'delivery',
          table: 'send_queue',
          operation: 'insert',
          data: {
            message_id: message.id,
            person_id: message.person_id,
            channel: channelMapping.primary,
            priority: channelMapping.priority,
            content: message.final_content,
            scheduled_at: new Date().toISOString(),
            status: 'queued'
          }
        });

      } catch (error) {
        console.error(`❌ Channel mapping failed for message ${message.id}:`, error);
        this.currentStatus.errors.push(`Channel mapping error: ${error instanceof Error ? error.message : 'Unknown'}`);
      }
    }
  }

  private async getPersonContactInfo(personId: string): Promise<any> {
    const result = await this.databaseAgent.execute({
      id: `get-person-contact-${personId}`,
      connection_name: 'marketing',
      database: 'Marketing DB',
      schema: 'people',
      table: 'marketing_people',
      operation: 'select',
      where: { id: personId }
    });

    const person = result.returned_data?.[0];
    if (!person) throw new Error(`Person ${personId} not found`);
    
    return person;
  }

  private async determineOptimalChannel(personData: any): Promise<any> {
    const preferences = this.processingConfig.channel_preferences || {
      email_priority: 1,
      linkedin_priority: 2,
      fallback_channel: 'email'
    };

    let primaryChannel = 'email';
    let score = 0;

    // Email preference and validation
    if (personData.email && personData.email_validation_status === 'valid') {
      score += preferences.email_priority * 10;
      primaryChannel = 'email';
    }

    // LinkedIn preference
    if (personData.linkedin_url) {
      const linkedinScore = preferences.linkedin_priority * 8;
      if (linkedinScore > score) {
        primaryChannel = 'linkedin';
        score = linkedinScore;
      }
    }

    return {
      primary: primaryChannel,
      fallback: preferences.fallback_channel,
      score: score,
      priority: score > 15 ? 'high' : score > 8 ? 'medium' : 'low'
    };
  }

  // ============================================
  // Step 2: Rate Guardrails
  // ============================================

  private async executeRateGuardrails(): Promise<void> {
    this.currentStatus.stage = 'rate_guard';
    console.log('🛡️ Step 2: Rate Guardrails');

    try {
      // Get queued sends
      const queuedSends = await this.databaseAgent.execute({
        id: `get-queued-sends-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'delivery',
        table: 'send_queue',
        operation: 'select',
        where: { status: 'queued' }
      });

      const sends = queuedSends.returned_data || [];
      console.log(`⚖️ Applying rate limits to ${sends.length} queued sends`);

      // Load rate limit settings
      await this.loadRateLimitSettings();

      // Process sends with rate limiting
      for (const send of sends) {
        const canSend = await this.checkRateLimit(send.channel);
        
        if (canSend) {
          // Update to ready_to_send
          await this.databaseAgent.execute({
            id: `approve-send-${send.id}`,
            connection_name: 'marketing',
            database: 'Marketing DB',
            schema: 'delivery',
            table: 'send_queue',
            operation: 'update',
            data: {
              status: 'ready_to_send',
              approved_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            },
            where: { id: send.id }
          });

          // Increment rate counter
          this.incrementRateCounter(send.channel);
        } else {
          // Delay send
          const delayMinutes = await this.calculateDelay(send.channel);
          const scheduledTime = new Date(Date.now() + delayMinutes * 60 * 1000);

          await this.databaseAgent.execute({
            id: `delay-send-${send.id}`,
            connection_name: 'marketing',
            database: 'Marketing DB',
            schema: 'delivery',
            table: 'send_queue',
            operation: 'update',
            data: {
              status: 'rate_limited',
              scheduled_at: scheduledTime.toISOString(),
              delay_reason: 'rate_limit_exceeded',
              updated_at: new Date().toISOString()
            },
            where: { id: send.id }
          });
        }
      }

      console.log('✅ Rate guardrails applied');
    } catch (error) {
      throw new Error(`Rate guardrails failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async loadRateLimitSettings(): Promise<void> {
    try {
      const settings = await this.databaseAgent.execute({
        id: `get-rate-limits-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'shq',
        table: 'guardrails',
        operation: 'select'
      });

      // Process rate limit settings from database
      (settings.returned_data || []).forEach((setting: any) => {
        if (setting.setting_type === 'rate_limit') {
          this.rateLimitCounters.set(setting.setting_key, setting.current_count || 0);
        }
      });
    } catch (error) {
      console.warn('⚠️ Could not load rate limits from database, using defaults');
      // Initialize with defaults
      this.rateLimitCounters.set('email_hourly', 0);
      this.rateLimitCounters.set('linkedin_hourly', 0);
      this.rateLimitCounters.set('daily_total', 0);
    }
  }

  private async checkRateLimit(channel: string): Promise<boolean> {
    const limits = this.processingConfig.rate_limits || {
      email_per_hour: 100,
      linkedin_per_hour: 50,
      daily_limit: 1000,
      burst_limit: 10
    };

    const currentHour = new Date().getHours();
    const emailCount = this.rateLimitCounters.get(`email_hourly_${currentHour}`) || 0;
    const linkedinCount = this.rateLimitCounters.get(`linkedin_hourly_${currentHour}`) || 0;
    const dailyCount = this.rateLimitCounters.get('daily_total') || 0;

    if (channel === 'email' && emailCount >= limits.email_per_hour) return false;
    if (channel === 'linkedin' && linkedinCount >= limits.linkedin_per_hour) return false;
    if (dailyCount >= limits.daily_limit) return false;

    return true;
  }

  private incrementRateCounter(channel: string): void {
    const currentHour = new Date().getHours();
    const hourlyKey = `${channel}_hourly_${currentHour}`;
    
    this.rateLimitCounters.set(hourlyKey, (this.rateLimitCounters.get(hourlyKey) || 0) + 1);
    this.rateLimitCounters.set('daily_total', (this.rateLimitCounters.get('daily_total') || 0) + 1);
  }

  private async calculateDelay(channel: string): Promise<number> {
    // Simple delay calculation - in production this would be more sophisticated
    const baseDelays: Record<string, number> = {
      'email': 15, // 15 minutes
      'linkedin': 30 // 30 minutes
    };
    
    return baseDelays[channel] || 60;
  }

  // ============================================
  // Step 3: Send & Track
  // ============================================

  private async executeSendAndTrack(): Promise<void> {
    this.currentStatus.stage = 'send';
    console.log('📤 Step 3: Send & Track');

    try {
      // Get approved sends
      const approvedSends = await this.databaseAgent.execute({
        id: `get-approved-sends-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'delivery',
        table: 'send_queue',
        operation: 'select',
        where: { status: 'ready_to_send' }
      });

      const sends = approvedSends.returned_data || [];
      console.log(`📨 Sending ${sends.length} messages`);

      // Process sends by channel
      const emailSends = sends.filter(s => s.channel === 'email');
      const linkedinSends = sends.filter(s => s.channel === 'linkedin');

      // Send emails via Instantly
      if (emailSends.length > 0) {
        await this.processEmailSends(emailSends);
      }

      // Send LinkedIn messages via HeyReach
      if (linkedinSends.length > 0) {
        await this.processLinkedInSends(linkedinSends);
      }

      console.log(`✅ Sent ${this.currentStatus.emails_sent} emails, ${this.currentStatus.linkedin_sent} LinkedIn messages`);
    } catch (error) {
      throw new Error(`Send & Track failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async processEmailSends(sends: any[]): Promise<void> {
    for (const send of sends) {
      try {
        let sendResult;
        
        if (this.instantlyAgent) {
          // Use Instantly agent
          sendResult = await this.instantlyAgent.sendEmail({
            to: send.email_address,
            subject: this.extractSubject(send.content),
            content: send.content,
            tracking: this.processingConfig.tracking_settings
          });
        } else {
          // Simulate send
          sendResult = this.simulateEmailSend(send);
        }

        if (sendResult.success) {
          // Log successful send
          await this.logDeliveryEvent(send, 'sent', sendResult);
          this.currentStatus.emails_sent++;

          // Update send queue
          await this.databaseAgent.execute({
            id: `mark-sent-${send.id}`,
            connection_name: 'marketing',
            database: 'Marketing DB',
            schema: 'delivery',
            table: 'send_queue',
            operation: 'update',
            data: {
              status: 'sent',
              sent_at: new Date().toISOString(),
              external_id: sendResult.external_id,
              tracking_id: sendResult.tracking_id,
              updated_at: new Date().toISOString()
            },
            where: { id: send.id }
          });
        } else {
          throw new Error(sendResult.error || 'Unknown send failure');
        }

      } catch (error) {
        console.error(`❌ Email send failed for ${send.id}:`, error);
        await this.handleSendFailure(send, error);
        this.currentStatus.delivery_failures++;
      }
    }
  }

  private async processLinkedInSends(sends: any[]): Promise<void> {
    for (const send of sends) {
      try {
        let sendResult;
        
        if (this.heyreachAgent) {
          // Use HeyReach agent
          sendResult = await this.heyreachAgent.sendMessage({
            linkedin_url: send.linkedin_url,
            content: send.content,
            tracking: this.processingConfig.tracking_settings
          });
        } else {
          // Simulate send
          sendResult = this.simulateLinkedInSend(send);
        }

        if (sendResult.success) {
          // Log successful send
          await this.logDeliveryEvent(send, 'sent', sendResult);
          this.currentStatus.linkedin_sent++;

          // Update send queue
          await this.databaseAgent.execute({
            id: `mark-linkedin-sent-${send.id}`,
            connection_name: 'marketing',
            database: 'Marketing DB',
            schema: 'delivery',
            table: 'send_queue',
            operation: 'update',
            data: {
              status: 'sent',
              sent_at: new Date().toISOString(),
              external_id: sendResult.external_id,
              updated_at: new Date().toISOString()
            },
            where: { id: send.id }
          });
        } else {
          throw new Error(sendResult.error || 'Unknown send failure');
        }

      } catch (error) {
        console.error(`❌ LinkedIn send failed for ${send.id}:`, error);
        await this.handleSendFailure(send, error);
        this.currentStatus.delivery_failures++;
      }
    }
  }

  private extractSubject(content: string): string {
    // Simple subject extraction - in production this would be more sophisticated
    const lines = content.split('\n');
    return lines[0].substring(0, 50) + '...';
  }

  private simulateEmailSend(send: any): any {
    return {
      success: Math.random() > 0.1, // 90% success rate
      external_id: `email_${Date.now()}_${Math.random()}`,
      tracking_id: `track_${Date.now()}`,
      error: Math.random() > 0.9 ? 'Simulated failure' : null
    };
  }

  private simulateLinkedInSend(send: any): any {
    return {
      success: Math.random() > 0.15, // 85% success rate
      external_id: `linkedin_${Date.now()}_${Math.random()}`,
      error: Math.random() > 0.85 ? 'Simulated LinkedIn failure' : null
    };
  }

  private async logDeliveryEvent(send: any, eventType: string, result: any): Promise<void> {
    await this.databaseAgent.execute({
      id: `log-event-${send.id}-${eventType}`,
      connection_name: 'marketing',
      database: 'Marketing DB',
      schema: 'delivery',
      table: 'events',
      operation: 'insert',
      data: {
        message_id: send.message_id,
        person_id: send.person_id,
        event_type: eventType,
        channel: send.channel,
        external_id: result.external_id,
        tracking_id: result.tracking_id,
        event_data: JSON.stringify(result),
        timestamp: new Date().toISOString()
      }
    });
  }

  private async handleSendFailure(send: any, error: any): Promise<void> {
    // Update send queue with failure
    await this.databaseAgent.execute({
      id: `mark-failed-${send.id}`,
      connection_name: 'marketing',
      database: 'Marketing DB',
      schema: 'delivery',
      table: 'send_queue',
      operation: 'update',
      data: {
        status: 'failed',
        error_details: error instanceof Error ? error.message : 'Unknown error',
        failed_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      where: { id: send.id }
    });

    // Log failure event
    await this.logDeliveryEvent(send, 'failed', {
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }

  // ============================================
  // Step 4: Reply Routing
  // ============================================

  private async executeReplyRouting(): Promise<void> {
    this.currentStatus.stage = 'reply_route';
    console.log('📥 Step 4: Reply Routing');

    try {
      // Get new replies from reply_queue
      const newReplies = await this.databaseAgent.execute({
        id: `get-new-replies-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'delivery',
        table: 'reply_queue',
        operation: 'select',
        where: { status: 'queued' }
      });

      const replies = newReplies.returned_data || [];
      console.log(`📨 Processing ${replies.length} replies`);

      for (const reply of replies) {
        try {
          // Parse reply content
          const parsedReply = await this.parseReply(reply);

          // Insert into reply_inbox
          await this.databaseAgent.execute({
            id: `insert-reply-${reply.id}`,
            connection_name: 'marketing',
            database: 'Marketing DB',
            schema: 'delivery',
            table: 'reply_inbox',
            operation: 'insert',
            data: {
              original_message_id: reply.message_id,
              person_id: reply.person_id,
              channel: reply.channel,
              raw_content: reply.content,
              parsed_content: parsedReply.parsed_content,
              sentiment: parsedReply.sentiment,
              intent: parsedReply.intent,
              requires_response: parsedReply.requires_response,
              priority: parsedReply.priority,
              received_at: reply.received_at,
              processed_at: new Date().toISOString(),
              status: 'processed'
            }
          });

          // Update reply queue
          await this.databaseAgent.execute({
            id: `process-reply-${reply.id}`,
            connection_name: 'marketing',
            database: 'Marketing DB',
            schema: 'delivery',
            table: 'reply_queue',
            operation: 'update',
            data: {
              status: 'processed',
              processed_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            },
            where: { id: reply.id }
          });

          // Log reply event
          await this.logDeliveryEvent(reply, 'reply_received', parsedReply);
          this.currentStatus.replies_received++;

        } catch (error) {
          console.error(`❌ Reply processing failed for ${reply.id}:`, error);
          this.currentStatus.errors.push(`Reply processing error: ${error instanceof Error ? error.message : 'Unknown'}`);
        }
      }

      console.log(`✅ Processed ${this.currentStatus.replies_received} replies`);
    } catch (error) {
      throw new Error(`Reply routing failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async parseReply(reply: any): Promise<any> {
    if (this.emailParser) {
      return await this.emailParser.parseReply({
        content: reply.content,
        channel: reply.channel
      });
    }

    // Basic parsing fallback
    const content = reply.content.toLowerCase();
    
    return {
      parsed_content: reply.content,
      sentiment: content.includes('interest') || content.includes('yes') ? 'positive' : 
                content.includes('not interested') || content.includes('no') ? 'negative' : 'neutral',
      intent: content.includes('schedule') || content.includes('call') ? 'meeting_request' :
              content.includes('unsubscribe') || content.includes('remove') ? 'unsubscribe' :
              content.includes('more info') ? 'information_request' : 'general',
      requires_response: !content.includes('unsubscribe') && !content.includes('not interested'),
      priority: content.includes('urgent') || content.includes('asap') ? 'high' : 
               content.includes('schedule') ? 'medium' : 'low'
    };
  }

  // ============================================
  // Public Interface
  // ============================================

  getId(): string {
    return 'barton-delivery-orchestrator';
  }

  getStatus(): DeliveryStatus {
    return { ...this.currentStatus };
  }

  async receiveMessage(message: any): Promise<void> {
    console.log(`📨 Delivery Branch received message: ${message.message_type} from ${message.from_branch}`);
    
    switch (message.message_type) {
      case 'request_status':
        break;
      case 'error':
        this.currentStatus.errors.push(`External error: ${message.payload.error_message}`);
        break;
      default:
        console.log(`⚠️ Unknown message type: ${message.message_type}`);
    }
  }

  async processWebhookEvent(eventType: string, payload: any): Promise<void> {
    console.log(`🪝 Processing webhook: ${eventType}`);

    switch (eventType) {
      case 'email_opened':
        await this.handleEmailOpened(payload);
        break;
      case 'email_clicked':
        await this.handleEmailClicked(payload);
        break;
      case 'email_replied':
        await this.handleEmailReplied(payload);
        break;
      case 'linkedin_replied':
        await this.handleLinkedInReplied(payload);
        break;
      default:
        console.log(`⚠️ Unknown webhook event: ${eventType}`);
    }
  }

  private async handleEmailOpened(payload: any): Promise<void> {
    await this.logDeliveryEvent(payload, 'opened', payload);
    this.currentStatus.opens_tracked++;
  }

  private async handleEmailClicked(payload: any): Promise<void> {
    await this.logDeliveryEvent(payload, 'clicked', payload);
    this.currentStatus.clicks_tracked++;
  }

  private async handleEmailReplied(payload: any): Promise<void> {
    // Add to reply queue
    await this.databaseAgent.execute({
      id: `queue-email-reply-${Date.now()}`,
      connection_name: 'marketing',
      database: 'Marketing DB',
      schema: 'delivery',
      table: 'reply_queue',
      operation: 'insert',
      data: {
        message_id: payload.message_id,
        person_id: payload.person_id,
        channel: 'email',
        content: payload.content,
        received_at: payload.timestamp || new Date().toISOString(),
        status: 'queued'
      }
    });
  }

  private async handleLinkedInReplied(payload: any): Promise<void> {
    // Add to reply queue
    await this.databaseAgent.execute({
      id: `queue-linkedin-reply-${Date.now()}`,
      connection_name: 'marketing',
      database: 'Marketing DB',
      schema: 'delivery',
      table: 'reply_queue',
      operation: 'insert',
      data: {
        message_id: payload.message_id,
        person_id: payload.person_id,
        channel: 'linkedin',
        content: payload.content,
        received_at: payload.timestamp || new Date().toISOString(),
        status: 'queued'
      }
    });
  }

  async pause(): Promise<void> {
    console.log('⏸️ Delivery Branch Orchestrator paused');
  }

  async resume(): Promise<void> {
    console.log('▶️ Delivery Branch Orchestrator resumed');
  }
}

export function createDeliveryBranchOrchestrator(databaseAgent: GlobalDatabaseAgent): DeliveryBranchOrchestrator {
  return new DeliveryBranchOrchestrator(databaseAgent);
}