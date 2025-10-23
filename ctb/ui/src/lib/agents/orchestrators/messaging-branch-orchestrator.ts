/**
 * Branch 2 Orchestrator - Messaging Branch
 * 
 * Steps: PersonaResolve→Draft→Personalize→PolicyGate→Ready
 * Queues: messaging.compose_queue, messaging.approval_queue
 * Neon Targets: messaging.outbox_draft, messaging.outbox_personalized, messaging.outbox_ready, messaging.template_performance
 */

import { GlobalDatabaseAgent } from '../global-database-agent';

export interface MessagingConfig {
  persona_rules?: {
    industry_mapping?: Record<string, string>;
    role_tone?: Record<string, string>;
    company_size_factors?: Record<string, number>;
  };
  template_settings?: {
    default_template_id?: string;
    personalization_depth?: 'basic' | 'enhanced' | 'deep';
    max_message_length?: number;
  };
  policy_gates?: {
    require_approval?: boolean;
    forbidden_words?: string[];
    compliance_checks?: string[];
  };
  batch_size?: number;
}

export interface MessagingStatus {
  stage: 'persona_resolve' | 'draft' | 'personalize' | 'policy_gate' | 'ready' | 'completed';
  people_processed: number;
  total_people: number;
  messages_drafted: number;
  messages_personalized: number;
  messages_approved: number;
  messages_rejected: number;
  errors: string[];
  current_batch?: number;
}

export class MessagingBranchOrchestrator {
  private databaseAgent: GlobalDatabaseAgent;
  private llmAgent: any; // Will be injected
  private templateEngine: any;
  private policyChecker: any;
  
  private currentStatus: MessagingStatus;
  private processingConfig: MessagingConfig = {};

  constructor(databaseAgent: GlobalDatabaseAgent) {
    this.databaseAgent = databaseAgent;
    this.currentStatus = {
      stage: 'persona_resolve',
      people_processed: 0,
      total_people: 0,
      messages_drafted: 0,
      messages_personalized: 0,
      messages_approved: 0,
      messages_rejected: 0,
      errors: []
    };
  }

  // ============================================
  // Dependency Injection
  // ============================================

  injectDependencies(agents: {
    llmAgent?: any;
    templateEngine?: any;
    policyChecker?: any;
  }): void {
    this.llmAgent = agents.llmAgent;
    this.templateEngine = agents.templateEngine;
    this.policyChecker = agents.policyChecker;
    console.log('✅ Messaging Branch dependencies injected');
  }

  // ============================================
  // Main Execution Flow
  // ============================================

  async execute(config?: MessagingConfig): Promise<void> {
    this.processingConfig = { ...this.processingConfig, ...config };

    try {
      console.log('🚀 Starting Messaging Branch workflow...');
      
      // Step 1: Persona & Tone Resolve
      await this.executePersonaResolve();
      
      // Step 2: Message Draft
      await this.executeMessageDraft();
      
      // Step 3: Personalization
      await this.executePersonalization();
      
      // Step 4: Policy Gate
      await this.executePolicyGate();
      
      // Step 5: Ready
      await this.executeReady();

      this.currentStatus.stage = 'completed';
      console.log('✅ Messaging Branch workflow completed');

    } catch (error) {
      this.currentStatus.errors.push(error instanceof Error ? error.message : 'Unknown error');
      console.error('❌ Messaging Branch workflow failed:', error);
      throw error;
    }
  }

  // ============================================
  // Step 1: Persona & Tone Resolve
  // ============================================

  private async executePersonaResolve(): Promise<void> {
    this.currentStatus.stage = 'persona_resolve';
    console.log('👤 Step 1: Persona & Tone Resolve');

    try {
      // Get people from compose queue
      const queuedPeople = await this.databaseAgent.execute({
        id: `get-queued-people-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'messaging',
        table: 'compose_queue',
        operation: 'select',
        where: { status: 'queued' }
      });

      const people = queuedPeople.returned_data || [];
      this.currentStatus.total_people = people.length;

      console.log(`📊 Resolving personas for ${people.length} people`);

      // Process in batches
      const batchSize = this.processingConfig.batch_size || 25;
      for (let i = 0; i < people.length; i += batchSize) {
        const batch = people.slice(i, i + batchSize);
        await this.processPersonaBatch(batch);
        
        this.currentStatus.people_processed += batch.length;
        console.log(`📈 Persona progress: ${this.currentStatus.people_processed}/${this.currentStatus.total_people}`);
      }

      console.log('✅ Persona resolution completed');
    } catch (error) {
      throw new Error(`Persona resolution failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async processPersonaBatch(batch: any[]): Promise<void> {
    for (const person of batch) {
      try {
        // Get person details with company info
        const personDetails = await this.databaseAgent.execute({
          id: `get-person-${person.person_id}`,
          connection_name: 'marketing',
          database: 'Marketing DB',
          schema: 'people',
          table: 'marketing_people',
          operation: 'select',
          where: { id: person.person_id }
        });

        const personData = personDetails.returned_data?.[0];
        if (!personData) continue;

        // Resolve persona based on role, industry, company size
        const persona = await this.resolvePersona(personData);

        // Update compose queue with persona info
        await this.databaseAgent.execute({
          id: `update-persona-${person.id}`,
          connection_name: 'marketing',
          database: 'Marketing DB',
          schema: 'messaging',
          table: 'compose_queue',
          operation: 'update',
          data: {
            persona_type: persona.type,
            tone_style: persona.tone,
            industry_context: persona.industry_context,
            status: 'persona_resolved',
            updated_at: new Date().toISOString()
          },
          where: { id: person.id }
        });

      } catch (error) {
        console.error(`❌ Persona resolution failed for person ${person.person_id}:`, error);
        
        // Mark as error in queue
        await this.databaseAgent.execute({
          id: `persona-error-${person.id}`,
          connection_name: 'marketing',
          database: 'Marketing DB',
          schema: 'messaging',
          table: 'compose_queue',
          operation: 'update',
          data: {
            status: 'error',
            error_details: error instanceof Error ? error.message : 'Unknown error',
            updated_at: new Date().toISOString()
          },
          where: { id: person.id }
        });
      }
    }
  }

  private async resolvePersona(personData: any): Promise<any> {
    // Get company details for context
    const companyDetails = await this.databaseAgent.execute({
      id: `get-company-${personData.company_id}`,
      connection_name: 'marketing',
      database: 'Marketing DB',
      schema: 'company',
      table: 'marketing_company',
      operation: 'select',
      where: { id: personData.company_id }
    });

    const company = companyDetails.returned_data?.[0] || {};

    // Apply persona rules
    const rules = this.processingConfig.persona_rules || {};
    
    return {
      type: this.mapPersonaType(personData.role_type, company.industry),
      tone: rules.role_tone?.[personData.role_type] || 'professional',
      industry_context: rules.industry_mapping?.[company.industry] || 'general',
      company_size_factor: rules.company_size_factors?.[this.getCompanySizeCategory(company.employee_count)] || 1.0
    };
  }

  private mapPersonaType(roleType: string, industry: string): string {
    // Simple mapping logic - would be more sophisticated in production
    const mapping: Record<string, string> = {
      'CEO': 'executive',
      'CFO': 'financial_leader',
      'HR': 'people_leader',
      'CTO': 'tech_leader'
    };
    return mapping[roleType] || 'professional';
  }

  private getCompanySizeCategory(employeeCount: number): string {
    if (employeeCount < 50) return 'small';
    if (employeeCount < 500) return 'medium';
    return 'large';
  }

  // ============================================
  // Step 2: Message Draft
  // ============================================

  private async executeMessageDraft(): Promise<void> {
    this.currentStatus.stage = 'draft';
    console.log('✍️ Step 2: Message Draft');

    try {
      // Get people with resolved personas
      const resolvedPeople = await this.databaseAgent.execute({
        id: `get-resolved-people-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'messaging',
        table: 'compose_queue',
        operation: 'select',
        where: { status: 'persona_resolved' }
      });

      const people = resolvedPeople.returned_data || [];
      console.log(`📝 Drafting messages for ${people.length} people`);

      // Process in smaller batches for LLM calls
      const batchSize = this.processingConfig.batch_size || 10;
      for (let i = 0; i < people.length; i += batchSize) {
        const batch = people.slice(i, i + batchSize);
        await this.processDraftBatch(batch);
        
        this.currentStatus.messages_drafted += batch.length;
        console.log(`📈 Draft progress: ${this.currentStatus.messages_drafted}/${people.length}`);
      }

      console.log('✅ Message drafting completed');
    } catch (error) {
      throw new Error(`Message drafting failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async processDraftBatch(batch: any[]): Promise<void> {
    for (const queueItem of batch) {
      try {
        let messageContent;

        if (this.llmAgent) {
          // Use LLM agent for message generation
          messageContent = await this.llmAgent.generateMessage({
            persona_type: queueItem.persona_type,
            tone_style: queueItem.tone_style,
            industry_context: queueItem.industry_context,
            template_id: this.processingConfig.template_settings?.default_template_id
          });
        } else if (this.templateEngine) {
          // Use template engine
          messageContent = await this.templateEngine.processTemplate({
            template_id: 'default_outreach',
            variables: {
              persona: queueItem.persona_type,
              tone: queueItem.tone_style,
              industry: queueItem.industry_context
            }
          });
        } else {
          // Fallback to basic template
          messageContent = this.generateBasicMessage(queueItem);
        }

        // Insert into outbox_draft
        await this.databaseAgent.execute({
          id: `insert-draft-${queueItem.id}`,
          connection_name: 'marketing',
          database: 'Marketing DB',
          schema: 'messaging',
          table: 'outbox_draft',
          operation: 'insert',
          data: {
            person_id: queueItem.person_id,
            compose_queue_id: queueItem.id,
            message_content: messageContent.content,
            template_id: messageContent.template_id,
            persona_type: queueItem.persona_type,
            tone_style: queueItem.tone_style,
            created_at: new Date().toISOString(),
            status: 'drafted'
          }
        });

        // Update compose queue
        await this.databaseAgent.execute({
          id: `update-drafted-${queueItem.id}`,
          connection_name: 'marketing',
          database: 'Marketing DB',
          schema: 'messaging',
          table: 'compose_queue',
          operation: 'update',
          data: {
            status: 'drafted',
            updated_at: new Date().toISOString()
          },
          where: { id: queueItem.id }
        });

      } catch (error) {
        console.error(`❌ Drafting failed for queue item ${queueItem.id}:`, error);
        this.currentStatus.errors.push(`Draft error: ${error instanceof Error ? error.message : 'Unknown'}`);
      }
    }
  }

  private generateBasicMessage(queueItem: any): any {
    // Fallback basic message generation
    const templates: Record<string, string> = {
      'executive': 'Hi {name}, I wanted to reach out regarding opportunities for {company}...',
      'financial_leader': 'Hi {name}, I have some insights that might be valuable for {company}\'s financial planning...',
      'people_leader': 'Hi {name}, I\'d love to discuss how we can support {company}\'s team growth...',
      'default': 'Hi {name}, I hope this message finds you well...'
    };

    const template = templates[queueItem.persona_type] || templates.default;
    
    return {
      content: template,
      template_id: 'basic_fallback'
    };
  }

  // ============================================
  // Step 3: Personalization
  // ============================================

  private async executePersonalization(): Promise<void> {
    this.currentStatus.stage = 'personalize';
    console.log('🎨 Step 3: Personalization');

    try {
      // Get drafted messages
      const draftedMessages = await this.databaseAgent.execute({
        id: `get-drafted-messages-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'messaging',
        table: 'outbox_draft',
        operation: 'select',
        where: { status: 'drafted' }
      });

      const messages = draftedMessages.returned_data || [];
      console.log(`🎯 Personalizing ${messages.length} messages`);

      const batchSize = this.processingConfig.batch_size || 15;
      for (let i = 0; i < messages.length; i += batchSize) {
        const batch = messages.slice(i, i + batchSize);
        await this.processPersonalizationBatch(batch);
        
        this.currentStatus.messages_personalized += batch.length;
        console.log(`📈 Personalization progress: ${this.currentStatus.messages_personalized}/${messages.length}`);
      }

      console.log('✅ Personalization completed');
    } catch (error) {
      throw new Error(`Personalization failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async processPersonalizationBatch(batch: any[]): Promise<void> {
    for (const draft of batch) {
      try {
        // Get person and company details for personalization
        const personData = await this.getPersonWithCompany(draft.person_id);
        
        let personalizedContent;
        if (this.llmAgent) {
          // Use LLM for advanced personalization
          personalizedContent = await this.llmAgent.personalizeMessage({
            base_content: draft.message_content,
            person_name: personData.full_name,
            company_name: personData.company_name,
            industry: personData.industry,
            personalization_depth: this.processingConfig.template_settings?.personalization_depth || 'basic'
          });
        } else {
          // Basic string replacement personalization
          personalizedContent = this.basicPersonalization(draft.message_content, personData);
        }

        // Insert into outbox_personalized
        await this.databaseAgent.execute({
          id: `insert-personalized-${draft.id}`,
          connection_name: 'marketing',
          database: 'Marketing DB',
          schema: 'messaging',
          table: 'outbox_personalized',
          operation: 'insert',
          data: {
            draft_id: draft.id,
            person_id: draft.person_id,
            personalized_content: personalizedContent,
            personalization_data: JSON.stringify({
              person_name: personData.full_name,
              company_name: personData.company_name,
              industry: personData.industry
            }),
            created_at: new Date().toISOString(),
            status: 'personalized'
          }
        });

        // Update draft status
        await this.databaseAgent.execute({
          id: `update-personalized-${draft.id}`,
          connection_name: 'marketing',
          database: 'Marketing DB',
          schema: 'messaging',
          table: 'outbox_draft',
          operation: 'update',
          data: {
            status: 'personalized',
            updated_at: new Date().toISOString()
          },
          where: { id: draft.id }
        });

      } catch (error) {
        console.error(`❌ Personalization failed for draft ${draft.id}:`, error);
        this.currentStatus.errors.push(`Personalization error: ${error instanceof Error ? error.message : 'Unknown'}`);
      }
    }
  }

  private async getPersonWithCompany(personId: string): Promise<any> {
    // This would typically be a JOIN query, but we'll do it in steps for clarity
    const personResult = await this.databaseAgent.execute({
      id: `get-person-details-${personId}`,
      connection_name: 'marketing',
      database: 'Marketing DB',
      schema: 'people',
      table: 'marketing_people',
      operation: 'select',
      where: { id: personId }
    });

    const person = personResult.returned_data?.[0];
    if (!person) throw new Error(`Person ${personId} not found`);

    const companyResult = await this.databaseAgent.execute({
      id: `get-company-details-${person.company_id}`,
      connection_name: 'marketing',
      database: 'Marketing DB',
      schema: 'company',
      table: 'marketing_company',
      operation: 'select',
      where: { id: person.company_id }
    });

    const company = companyResult.returned_data?.[0] || {};

    return {
      ...person,
      company_name: company.company_name,
      industry: company.industry
    };
  }

  private basicPersonalization(template: string, personData: any): string {
    return template
      .replace(/{name}/g, personData.first_name || personData.full_name || 'there')
      .replace(/{company}/g, personData.company_name || 'your company')
      .replace(/{industry}/g, personData.industry || 'your industry');
  }

  // ============================================
  // Step 4: Policy Gate
  // ============================================

  private async executePolicyGate(): Promise<void> {
    this.currentStatus.stage = 'policy_gate';
    console.log('🛡️ Step 4: Policy Gate');

    try {
      // Get personalized messages
      const personalizedMessages = await this.databaseAgent.execute({
        id: `get-personalized-messages-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'messaging',
        table: 'outbox_personalized',
        operation: 'select',
        where: { status: 'personalized' }
      });

      const messages = personalizedMessages.returned_data || [];
      console.log(`🔍 Checking policy compliance for ${messages.length} messages`);

      for (const message of messages) {
        try {
          const policyResult = await this.checkPolicyCompliance(message);
          
          if (policyResult.approved) {
            // Move to ready
            await this.approveMessage(message);
            this.currentStatus.messages_approved++;
          } else {
            // Reject or queue for manual approval
            await this.rejectMessage(message, policyResult.reasons);
            this.currentStatus.messages_rejected++;
          }

        } catch (error) {
          console.error(`❌ Policy check failed for message ${message.id}:`, error);
          this.currentStatus.errors.push(`Policy error: ${error instanceof Error ? error.message : 'Unknown'}`);
        }
      }

      console.log(`✅ Policy gate completed: ${this.currentStatus.messages_approved} approved, ${this.currentStatus.messages_rejected} rejected`);
    } catch (error) {
      throw new Error(`Policy gate failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async checkPolicyCompliance(message: any): Promise<{ approved: boolean; reasons: string[] }> {
    const reasons: string[] = [];
    const policyGates = this.processingConfig.policy_gates || {};

    // Check message length
    const maxLength = this.processingConfig.template_settings?.max_message_length || 500;
    if (message.personalized_content.length > maxLength) {
      reasons.push(`Message too long: ${message.personalized_content.length} > ${maxLength} characters`);
    }

    // Check forbidden words
    const forbiddenWords = policyGates.forbidden_words || [];
    for (const word of forbiddenWords) {
      if (message.personalized_content.toLowerCase().includes(word.toLowerCase())) {
        reasons.push(`Contains forbidden word: ${word}`);
      }
    }

    // Use policy checker agent if available
    if (this.policyChecker) {
      try {
        const agentResult = await this.policyChecker.checkCompliance({
          content: message.personalized_content,
          checks: policyGates.compliance_checks || []
        });
        
        if (!agentResult.compliant) {
          reasons.push(...agentResult.violations);
        }
      } catch (error) {
        console.error('Policy checker agent failed:', error);
        reasons.push('Policy checker unavailable - manual review required');
      }
    }

    // Require manual approval if configured
    if (policyGates.require_approval && reasons.length === 0) {
      reasons.push('Manual approval required by policy');
    }

    return {
      approved: reasons.length === 0,
      reasons
    };
  }

  private async approveMessage(message: any): Promise<void> {
    // Insert into outbox_ready
    await this.databaseAgent.execute({
      id: `insert-ready-${message.id}`,
      connection_name: 'marketing',
      database: 'Marketing DB',
      schema: 'messaging',
      table: 'outbox_ready',
      operation: 'insert',
      data: {
        personalized_id: message.id,
        person_id: message.person_id,
        final_content: message.personalized_content,
        approved_at: new Date().toISOString(),
        status: 'ready'
      }
    });

    // Update personalized status
    await this.databaseAgent.execute({
      id: `update-approved-${message.id}`,
      connection_name: 'marketing',
      database: 'Marketing DB',
      schema: 'messaging',
      table: 'outbox_personalized',
      operation: 'update',
      data: {
        status: 'approved',
        updated_at: new Date().toISOString()
      },
      where: { id: message.id }
    });
  }

  private async rejectMessage(message: any, reasons: string[]): Promise<void> {
    // Add to approval queue if manual review needed
    await this.databaseAgent.execute({
      id: `queue-approval-${message.id}`,
      connection_name: 'marketing',
      database: 'Marketing DB',
      schema: 'messaging',
      table: 'approval_queue',
      operation: 'insert',
      data: {
        personalized_id: message.id,
        person_id: message.person_id,
        content: message.personalized_content,
        rejection_reasons: JSON.stringify(reasons),
        status: 'pending_review',
        created_at: new Date().toISOString()
      }
    });

    // Update personalized status
    await this.databaseAgent.execute({
      id: `update-rejected-${message.id}`,
      connection_name: 'marketing',
      database: 'Marketing DB',
      schema: 'messaging',
      table: 'outbox_personalized',
      operation: 'update',
      data: {
        status: 'rejected',
        rejection_reasons: JSON.stringify(reasons),
        updated_at: new Date().toISOString()
      },
      where: { id: message.id }
    });
  }

  // ============================================
  // Step 5: Ready
  // ============================================

  private async executeReady(): Promise<void> {
    this.currentStatus.stage = 'ready';
    console.log('🚀 Step 5: Ready for Delivery');

    try {
      // Get approved messages from outbox_ready
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
      console.log(`📤 ${messages.length} messages ready for delivery`);

      // Update template performance metrics
      await this.updateTemplatePerformance(messages);

      // Mark compose queue items as completed
      for (const message of messages) {
        await this.databaseAgent.execute({
          id: `complete-compose-${message.person_id}`,
          connection_name: 'marketing',
          database: 'Marketing DB',
          schema: 'messaging',
          table: 'compose_queue',
          operation: 'update',
          data: {
            status: 'completed',
            completed_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          },
          where: { person_id: message.person_id, status: 'drafted' }
        });
      }

      console.log('✅ Messages ready for delivery branch');
    } catch (error) {
      throw new Error(`Ready stage failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async updateTemplatePerformance(messages: any[]): Promise<void> {
    // Group by template and calculate metrics
    const templateMetrics: Record<string, any> = {};

    for (const message of messages) {
      // Get draft info to find template
      const draftResult = await this.databaseAgent.execute({
        id: `get-draft-${message.personalized_id}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'messaging',
        table: 'outbox_draft',
        operation: 'select',
        where: { id: message.personalized_id }
      });

      const draft = draftResult.returned_data?.[0];
      if (!draft) continue;

      const templateId = draft.template_id;
      if (!templateMetrics[templateId]) {
        templateMetrics[templateId] = {
          template_id: templateId,
          messages_generated: 0,
          approval_rate: 0,
          avg_length: 0,
          total_length: 0
        };
      }

      templateMetrics[templateId].messages_generated++;
      templateMetrics[templateId].total_length += message.final_content.length;
    }

    // Calculate averages and upsert performance records
    for (const [templateId, metrics] of Object.entries(templateMetrics)) {
      const avgLength = metrics.total_length / metrics.messages_generated;
      const approvalRate = (this.currentStatus.messages_approved / (this.currentStatus.messages_approved + this.currentStatus.messages_rejected)) * 100;

      await this.databaseAgent.execute({
        id: `upsert-template-perf-${templateId}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'messaging',
        table: 'template_performance',
        operation: 'upsert',
        data: {
          template_id: templateId,
          messages_generated: metrics.messages_generated,
          approval_rate: approvalRate,
          avg_message_length: avgLength,
          last_updated: new Date().toISOString()
        }
      });
    }
  }

  // ============================================
  // Public Interface
  // ============================================

  getId(): string {
    return 'barton-messaging-orchestrator';
  }

  getStatus(): MessagingStatus {
    return { ...this.currentStatus };
  }

  async receiveMessage(message: any): Promise<void> {
    console.log(`📨 Messaging Branch received message: ${message.message_type} from ${message.from_branch}`);
    
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

  async pause(): Promise<void> {
    console.log('⏸️ Messaging Branch Orchestrator paused');
  }

  async resume(): Promise<void> {
    console.log('▶️ Messaging Branch Orchestrator resumed');
  }
}

export function createMessagingBranchOrchestrator(databaseAgent: GlobalDatabaseAgent): MessagingBranchOrchestrator {
  return new MessagingBranchOrchestrator(databaseAgent);
}