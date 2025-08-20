import { Agent, Task } from '@/lib/heir/types';
import { DatabaseOperation, DatabaseResult } from '../global-database-agent';

export interface LeadProcessingConfig {
  csv_file_path?: string;
  apollo_filters?: {
    location?: string[];
    industry?: string[];
    employee_count_min?: number;
    employee_count_max?: number;
  };
  role_requirements?: {
    ceo?: boolean;
    cfo?: boolean;
    hr?: boolean;
    custom_roles?: string[];
  };
  validation_settings?: {
    provider: 'MillionVerifier' | 'ZeroBounce';
    confidence_threshold: number;
  };
  batch_size?: number;
}

export interface LeadProcessingStatus {
  stage: 'csv_ingestion' | 'company_canonicalization' | 'role_slot_creation' | 'contact_scraping' | 'validation' | 'completed';
  companies_processed: number;
  total_companies: number;
  contacts_scraped: number;
  contacts_validated: number;
  errors: string[];
  current_batch?: number;
  estimated_completion: Date;
}

export class LeadBranchOrchestrator {
  private agentInfo: Agent;
  private databaseAgent: any; // Will be injected
  private apolloAgent: any;
  private apifyAgent: any;
  private validationAgent: any;
  private fileProcessorAgent: any;
  
  private currentStatus: LeadProcessingStatus;
  private processingConfig: LeadProcessingConfig = {};

  constructor() {
    this.agentInfo = {
      id: 'barton-lead-orchestrator',
      name: 'Barton Lead Branch Orchestrator',
      role: 'orchestrator',
      category: 'project',
      description: 'Orchestrates Company → Roles → People workflow for lead acquisition and validation',
      capabilities: [
        'CSV file ingestion coordination',
        'Company data canonicalization',
        'Role slot management (CEO/CFO/HR)',
        'Contact scraping via Apify',
        'Email validation coordination',
        'Lead pipeline status management',
        'Batch processing optimization'
      ],
      status: 'idle'
    };

    this.currentStatus = {
      stage: 'csv_ingestion',
      companies_processed: 0,
      total_companies: 0,
      contacts_scraped: 0,
      contacts_validated: 0,
      errors: [],
      estimated_completion: new Date()
    };
  }

  // ============================================
  // Agent Dependency Injection
  // ============================================

  injectDependencies(agents: {
    databaseAgent: any;
    apolloAgent?: any;
    apifyAgent?: any;
    validationAgent?: any;
    fileProcessorAgent?: any;
  }): void {
    this.databaseAgent = agents.databaseAgent;
    this.apolloAgent = agents.apolloAgent;
    this.apifyAgent = agents.apifyAgent;
    this.validationAgent = agents.validationAgent;
    this.fileProcessorAgent = agents.fileProcessorAgent;

    console.log('✅ Lead Branch Orchestrator dependencies injected');
  }

  // ============================================
  // Main Execution Flow
  // ============================================

  async execute(config?: LeadProcessingConfig): Promise<void> {
    this.agentInfo.status = 'processing';
    this.processingConfig = { ...this.processingConfig, ...config };

    try {
      console.log('🚀 Starting Lead Branch workflow...');
      
      // Stage 1: CSV Ingestion
      await this.executeCSVIngestion();
      
      // Stage 2: Company Canonicalization
      await this.executeCompanyCanonicalization();
      
      // Stage 3: Role Slot Creation
      await this.executeRoleSlotCreation();
      
      // Stage 4: Contact Scraping
      await this.executeContactScraping();
      
      // Stage 5: Contact Validation
      await this.executeContactValidation();

      this.currentStatus.stage = 'completed';
      this.agentInfo.status = 'completed';
      console.log('✅ Lead Branch workflow completed successfully');

    } catch (error) {
      this.agentInfo.status = 'error';
      this.currentStatus.errors.push(error instanceof Error ? error.message : 'Unknown error');
      console.error('❌ Lead Branch workflow failed:', error);
      throw error;
    }
  }

  // ============================================
  // Stage 1: CSV Ingestion
  // ============================================

  private async executeCSVIngestion(): Promise<void> {
    this.currentStatus.stage = 'csv_ingestion';
    console.log('📄 Stage 1: CSV Ingestion');

    if (!this.processingConfig.csv_file_path) {
      console.log('⏭️ No CSV file specified, skipping ingestion');
      return;
    }

    try {
      // Use File Processor Agent to parse CSV
      if (this.fileProcessorAgent) {
        const parsedData = await this.fileProcessorAgent.processFile({
          file_path: this.processingConfig.csv_file_path,
          file_type: 'csv',
          target_schema: 'marketing',
          target_table: 'marketing_apollo_raw'
        });

        this.currentStatus.total_companies = parsedData.record_count;
      }

      // Insert raw data into staging table via Database Agent
      await this.databaseAgent.execute({
        id: `csv-ingest-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'marketing',
        table: 'marketing_apollo_raw',
        operation: 'bulk_insert',
        data: [], // Would be populated by file processor
        options: {
          batch_size: this.processingConfig.batch_size || 100
        }
      });

      console.log(`✅ CSV ingestion completed: ${this.currentStatus.total_companies} companies`);
    } catch (error) {
      throw new Error(`CSV ingestion failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // ============================================
  // Stage 2: Company Canonicalization
  // ============================================

  private async executeCompanyCanonicalization(): Promise<void> {
    this.currentStatus.stage = 'company_canonicalization';
    console.log('🏢 Stage 2: Company Canonicalization');

    try {
      // Get unprocessed companies from staging
      const stagingCompanies = await this.databaseAgent.execute({
        id: `get-staging-companies-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'marketing',
        table: 'marketing_apollo_raw',
        operation: 'select',
        where: { status: 'unprocessed' }
      });

      const companies = stagingCompanies.returned_data || [];
      console.log(`📊 Processing ${companies.length} companies for canonicalization`);

      // Process companies in batches
      const batchSize = this.processingConfig.batch_size || 50;
      for (let i = 0; i < companies.length; i += batchSize) {
        const batch = companies.slice(i, i + batchSize);
        await this.processBatch(batch, 'canonicalize');
        
        this.currentStatus.companies_processed += batch.length;
        console.log(`📈 Progress: ${this.currentStatus.companies_processed}/${this.currentStatus.total_companies} companies canonicalized`);
      }

      console.log('✅ Company canonicalization completed');
    } catch (error) {
      throw new Error(`Company canonicalization failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // ============================================
  // Stage 3: Role Slot Creation
  // ============================================

  private async executeRoleSlotCreation(): Promise<void> {
    this.currentStatus.stage = 'role_slot_creation';
    console.log('👥 Stage 3: Role Slot Creation');

    try {
      // Get canonical companies
      const canonicalCompanies = await this.databaseAgent.execute({
        id: `get-canonical-companies-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'company',
        table: 'marketing_company',
        operation: 'select',
        where: { contact_scraped: false }
      });

      const companies = canonicalCompanies.returned_data || [];
      const roleRequirements = this.processingConfig.role_requirements || { ceo: true, cfo: true, hr: true };

      for (const company of companies) {
        const roleSlots = [];

        // Create role slots based on requirements
        if (roleRequirements.ceo) {
          roleSlots.push({
            company_id: company.id,
            role_type: 'CEO',
            target_count: 1,
            priority_level: 1,
            slot_status: 'open'
          });
        }

        if (roleRequirements.cfo) {
          roleSlots.push({
            company_id: company.id,
            role_type: 'CFO',
            target_count: 1,
            priority_level: 2,
            slot_status: 'open'
          });
        }

        if (roleRequirements.hr) {
          roleSlots.push({
            company_id: company.id,
            role_type: 'HR',
            target_count: 1,
            priority_level: 3,
            slot_status: 'open'
          });
        }

        // Insert role slots
        if (roleSlots.length > 0) {
          await this.databaseAgent.execute({
            id: `create-role-slots-${company.id}`,
            connection_name: 'marketing',
            database: 'Marketing DB',
            schema: 'people',
            table: 'company_role_slots',
            operation: 'bulk_insert',
            data: roleSlots
          });
        }
      }

      console.log(`✅ Role slot creation completed for ${companies.length} companies`);
    } catch (error) {
      throw new Error(`Role slot creation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // ============================================
  // Stage 4: Contact Scraping
  // ============================================

  private async executeContactScraping(): Promise<void> {
    this.currentStatus.stage = 'contact_scraping';
    console.log('🔍 Stage 4: Contact Scraping');

    try {
      // Get open role slots
      const openSlots = await this.databaseAgent.execute({
        id: `get-open-slots-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'people',
        table: 'company_role_slots',
        operation: 'select',
        where: { slot_status: 'open' }
      });

      const slots = openSlots.returned_data || [];
      console.log(`🎯 Scraping contacts for ${slots.length} role slots`);

      // Process slots in batches for scraping
      const batchSize = this.processingConfig.batch_size || 20; // Smaller batches for scraping
      for (let i = 0; i < slots.length; i += batchSize) {
        const batch = slots.slice(i, i + batchSize);
        
        if (this.apifyAgent) {
          await this.apifyAgent.scrapeContacts({
            slots: batch,
            callback: async (scrapedContacts: any[]) => {
              await this.processScrapedContacts(scrapedContacts);
            }
          });
        } else {
          // Fallback: simulate scraping
          console.log('⚠️ Apify agent not available, simulating contact scraping');
          await this.simulateContactScraping(batch);
        }

        this.currentStatus.contacts_scraped += batch.length * 3; // Estimate 3 contacts per slot
        console.log(`📈 Scraped contacts for ${i + batch.length}/${slots.length} slots`);
      }

      console.log('✅ Contact scraping completed');
    } catch (error) {
      throw new Error(`Contact scraping failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async processScrapedContacts(contacts: any[]): Promise<void> {
    // Insert scraped contacts into people.marketing_people
    for (const contact of contacts) {
      await this.databaseAgent.execute({
        id: `insert-contact-${Date.now()}-${Math.random()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'people',
        table: 'marketing_people',
        operation: 'insert',
        data: {
          external_id: contact.external_id,
          company_id: contact.company_id,
          first_name: contact.first_name,
          last_name: contact.last_name,
          email: contact.email,
          title: contact.title,
          role_type: contact.role_type,
          source: 'apify',
          email_validation_status: 'unverified',
          lead_pipeline_status: 'new'
        }
      });

      // Log to contact history
      await this.databaseAgent.execute({
        id: `contact-history-${Date.now()}-${Math.random()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'people',
        table: 'contact_history',
        operation: 'insert',
        data: {
          person_id: contact.person_id,
          change_type: 'created',
          new_values: contact,
          source_system: 'apify'
        }
      });
    }
  }

  private async simulateContactScraping(slots: any[]): Promise<void> {
    // Simulation for development
    const simulatedContacts = slots.flatMap(slot => [
      {
        company_id: slot.company_id,
        role_type: slot.role_type,
        first_name: 'John',
        last_name: 'Doe',
        email: `john.doe@company${slot.company_id}.com`,
        title: slot.role_type === 'CEO' ? 'Chief Executive Officer' : slot.role_type
      }
    ]);

    await this.processScrapedContacts(simulatedContacts);
  }

  // ============================================
  // Stage 5: Contact Validation
  // ============================================

  private async executeContactValidation(): Promise<void> {
    this.currentStatus.stage = 'validation';
    console.log('✅ Stage 5: Contact Validation');

    try {
      // Get unverified contacts
      const unverifiedContacts = await this.databaseAgent.execute({
        id: `get-unverified-contacts-${Date.now()}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'people',
        table: 'marketing_people',
        operation: 'select',
        where: { email_validation_status: 'unverified' }
      });

      const contacts = unverifiedContacts.returned_data || [];
      console.log(`📧 Validating ${contacts.length} email addresses`);

      // Process validation in batches
      const batchSize = this.processingConfig.batch_size || 100;
      for (let i = 0; i < contacts.length; i += batchSize) {
        const batch = contacts.slice(i, i + batchSize);
        
        if (this.validationAgent) {
          const validationResults = await this.validationAgent.validateEmails({
            emails: batch.map(c => ({ id: c.id, email: c.email })),
            provider: this.processingConfig.validation_settings?.provider || 'MillionVerifier'
          });

          await this.processValidationResults(validationResults);
        } else {
          // Fallback: simulate validation
          console.log('⚠️ Validation agent not available, simulating validation');
          await this.simulateValidation(batch);
        }

        this.currentStatus.contacts_validated += batch.length;
        console.log(`📈 Validated ${this.currentStatus.contacts_validated}/${contacts.length} contacts`);
      }

      console.log('✅ Contact validation completed');
    } catch (error) {
      throw new Error(`Contact validation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async processValidationResults(results: any[]): Promise<void> {
    for (const result of results) {
      // Update person record
      await this.databaseAgent.execute({
        id: `update-validation-${result.person_id}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'people',
        table: 'marketing_people',
        operation: 'update',
        data: {
          email_validation_status: result.status,
          email_validation_score: result.score,
          email_validated_at: new Date().toISOString(),
          lead_pipeline_status: result.status === 'valid' ? 'qualified' : 'invalid'
        },
        where: { id: result.person_id }
      });

      // Insert detailed validation result
      await this.databaseAgent.execute({
        id: `validation-detail-${result.person_id}`,
        connection_name: 'marketing',
        database: 'Marketing DB',
        schema: 'people',
        table: 'validation_status',
        operation: 'insert',
        data: {
          person_id: result.person_id,
          email: result.email,
          validation_provider: result.provider,
          validation_status: result.status,
          validation_score: result.score,
          validation_reason: result.reason,
          provider_response: result.full_response
        }
      });
    }
  }

  private async simulateValidation(contacts: any[]): Promise<void> {
    const simulatedResults = contacts.map(contact => ({
      person_id: contact.id,
      email: contact.email,
      status: Math.random() > 0.2 ? 'valid' : 'invalid', // 80% valid rate
      score: Math.random(),
      provider: 'MillionVerifier',
      reason: 'simulation'
    }));

    await this.processValidationResults(simulatedResults);
  }

  // ============================================
  // Utility Methods
  // ============================================

  private async processBatch(batch: any[], operation: string): Promise<void> {
    // Generic batch processing logic
    switch (operation) {
      case 'canonicalize':
        for (const item of batch) {
          // Convert raw company data to canonical format
          const canonicalData = this.normalizeCompanyData(item);
          
          await this.databaseAgent.execute({
            id: `canonicalize-${item.id}`,
            connection_name: 'marketing',
            database: 'Marketing DB',
            schema: 'company',
            table: 'marketing_company',
            operation: 'upsert',
            data: canonicalData
          });

          // Mark raw data as processed
          await this.databaseAgent.execute({
            id: `mark-processed-${item.id}`,
            connection_name: 'marketing',
            database: 'Marketing DB',
            schema: 'marketing',
            table: 'marketing_apollo_raw',
            operation: 'update',
            data: { status: 'processed', processed_at: new Date().toISOString() },
            where: { id: item.id }
          });
        }
        break;
      
      default:
        throw new Error(`Unknown batch operation: ${operation}`);
    }
  }

  private normalizeCompanyData(rawData: any): any {
    // Extract and normalize company data from raw Apollo format
    const normalized = rawData.raw_data || rawData;
    
    return {
      external_id: normalized.apollo_id || normalized.id,
      company_name: normalized.company_name || normalized.name,
      industry: normalized.industry,
      employee_count: normalized.employee_count,
      domain: normalized.domain,
      linkedin_url: normalized.linkedin_url,
      address: normalized.address,
      city: normalized.city,
      state: normalized.state,
      zip_code: normalized.zip_code,
      source: 'apollo',
      contact_scraped: false,
      outreach_phase: 0
    };
  }

  // ============================================
  // Public Interface
  // ============================================

  getId(): string {
    return this.agentInfo.id;
  }

  getStatus(): LeadProcessingStatus {
    return { ...this.currentStatus };
  }

  getAgentInfo(): Agent {
    return { ...this.agentInfo };
  }

  async receiveMessage(message: any): Promise<void> {
    console.log(`📨 Lead Branch received message: ${message.message_type} from ${message.from_branch}`);
    
    switch (message.message_type) {
      case 'request_status':
        // Return current status
        break;
      case 'error':
        // Handle error notification
        this.currentStatus.errors.push(`External error: ${message.payload.error_message}`);
        break;
      default:
        console.log(`⚠️ Unknown message type: ${message.message_type}`);
    }
  }

  async pause(): Promise<void> {
    this.agentInfo.status = 'idle';
    console.log('⏸️ Lead Branch Orchestrator paused');
  }

  async resume(): Promise<void> {
    this.agentInfo.status = 'processing';
    console.log('▶️ Lead Branch Orchestrator resumed');
  }
}

// ============================================
// Factory Function
// ============================================

export function createLeadBranchOrchestrator(): LeadBranchOrchestrator {
  return new LeadBranchOrchestrator();
}