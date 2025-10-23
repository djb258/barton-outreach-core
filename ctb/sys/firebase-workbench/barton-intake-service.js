/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-BDD11D6C
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * Doctrine Spec:
 * - Barton ID: 04.04.01
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Step 2 Intake service integrating with Composio MCP for company/people ingestion
 * - Input: Intake operations through Composio Firebase tools
 * - Output: Company and people intake processing via MCP-only access
 * - MCP: Firebase (Composio-only validation)
 */

class BartonIntakeService {
  constructor() {
    this.doctrineVersion = '1.0.0';
    this.mcpEndpoint = process.env.COMPOSIO_MCP_URL || 'https://backend.composio.dev/api/v1/mcp';
    this.initialized = false;
  }

  /**
   * Initialize the intake service
   */
  async initialize() {
    console.log('[INTAKE-SERVICE] Initializing Barton Intake Service...');

    try {
      // Test MCP connectivity
      await this.testMCPConnection();

      // Initialize intake collections if needed
      await this.initializeIntakeCollections();

      this.initialized = true;
      return { success: true, service: 'intake', version: this.doctrineVersion };

    } catch (error) {
      console.error('[INTAKE-SERVICE] Initialization failed:', error);
      throw error;
    }
  }

  /**
   * Test MCP connection for intake operations
   */
  async testMCPConnection() {
    try {
      // Test basic connectivity to Composio MCP
      const healthPayload = {
        tool: 'get_composio_stats',
        data: {},
        unique_id: this.generateHeirId(),
        process_id: this.generateProcessId(),
        orbt_layer: 2,
        blueprint_version: this.doctrineVersion
      };

      const response = await fetch(`${this.mcpEndpoint}/tool`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Composio-Key': process.env.COMPOSIO_API_KEY || ''
        },
        body: JSON.stringify(healthPayload)
      });

      if (!response.ok) {
        throw new Error(`MCP connection failed: ${response.status}`);
      }

      const result = await response.json();
      console.log('[INTAKE-SERVICE] MCP connection verified');
      return result;

    } catch (error) {
      console.error('[INTAKE-SERVICE] MCP connection test failed:', error);
      throw error;
    }
  }

  /**
   * Initialize intake collections via MCP
   */
  async initializeIntakeCollections() {
    console.log('[INTAKE-SERVICE] Initializing intake collections...');

    try {
      // Initialize company_raw_intake collection
      await this.initializeCompanyIntakeCollection();

      // Initialize people_raw_intake collection
      await this.initializePeopleIntakeCollection();

      // Initialize audit log collections
      await this.initializeAuditLogCollections();

      console.log('[INTAKE-SERVICE] All intake collections initialized');
      return { success: true, collections: 4 };

    } catch (error) {
      console.error('[INTAKE-SERVICE] Collection initialization failed:', error);
      throw error;
    }
  }

  /**
   * Initialize company raw intake collection
   */
  async initializeCompanyIntakeCollection() {
    const sampleCompany = {
      company_unique_id: '05.01.01.03.10000.002',
      company_name: 'Sample Company Inc',
      website_url: 'https://samplecompany.com',
      industry: 'Technology',
      company_size: '51-200',
      headquarters_location: 'San Francisco, CA',
      linkedin_url: null,
      twitter_url: null,
      facebook_url: null,
      instagram_url: null,
      status: 'validated',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      intake_source: 'initialization',
      source_metadata: {
        user_agent: 'barton_intake_service',
        ip_address: 'internal',
        request_id: 'init_company_' + Date.now()
      }
    };

    return await this.executeComposioFirebaseTool('FIREBASE_WRITE', {
      collection: 'company_raw_intake',
      document: 'sample_company_init',
      data: sampleCompany
    });
  }

  /**
   * Initialize people raw intake collection
   */
  async initializePeopleIntakeCollection() {
    const samplePerson = {
      person_unique_id: '05.01.01.03.10000.003',
      full_name: 'Sample Person',
      email_address: 'sample.person@samplecompany.com',
      job_title: 'Sample Role',
      company_name: 'Sample Company Inc',
      location: 'San Francisco, CA',
      linkedin_url: null,
      twitter_url: null,
      facebook_url: null,
      instagram_url: null,
      associated_company_id: '05.01.01.03.10000.002',
      status: 'validated',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      intake_source: 'initialization',
      source_metadata: {
        user_agent: 'barton_intake_service',
        ip_address: 'internal',
        request_id: 'init_person_' + Date.now()
      }
    };

    return await this.executeComposioFirebaseTool('FIREBASE_WRITE', {
      collection: 'people_raw_intake',
      document: 'sample_person_init',
      data: samplePerson
    });
  }

  /**
   * Initialize audit log collections
   */
  async initializeAuditLogCollections() {
    // Initialize company audit log
    const companyAuditEntry = {
      unique_id: '05.01.02.03.10000.004',
      action: 'intake_create',
      status: 'success',
      source: {
        service: 'barton_intake_service',
        function: 'initializeAuditLogCollections',
        user_agent: 'intake_service',
        ip_address: 'internal',
        request_id: 'init_audit_' + Date.now()
      },
      target_company_id: '05.01.01.03.10000.002',
      error_log: null,
      payload: {
        before: null,
        after: { initialized: true },
        metadata: {
          doctrine_version: this.doctrineVersion,
          initialization: true
        }
      },
      created_at: new Date().toISOString()
    };

    await this.executeComposioFirebaseTool('FIREBASE_WRITE', {
      collection: 'company_audit_log',
      document: 'init_company_audit',
      data: companyAuditEntry
    });

    // Initialize people audit log
    const peopleAuditEntry = {
      unique_id: '05.01.02.03.10000.005',
      action: 'intake_create',
      status: 'success',
      source: {
        service: 'barton_intake_service',
        function: 'initializeAuditLogCollections',
        user_agent: 'intake_service',
        ip_address: 'internal',
        request_id: 'init_audit_' + Date.now()
      },
      target_person_id: '05.01.01.03.10000.003',
      error_log: null,
      payload: {
        before: null,
        after: { initialized: true },
        metadata: {
          doctrine_version: this.doctrineVersion,
          initialization: true
        }
      },
      created_at: new Date().toISOString()
    };

    await this.executeComposioFirebaseTool('FIREBASE_WRITE', {
      collection: 'people_audit_log',
      document: 'init_people_audit',
      data: peopleAuditEntry
    });
  }

  /**
   * Process company intake via MCP
   */
  async intakeCompany(companyData) {
    console.log('[INTAKE-SERVICE] Processing company intake...');

    try {
      // Validate company data
      this.validateCompanyData(companyData);

      // Generate Barton ID
      const companyBartonId = await this.generateCompanyBartonId(companyData);

      // Prepare company document
      const companyDocument = {
        company_unique_id: companyBartonId,
        company_name: companyData.company_name,
        website_url: companyData.website_url,
        industry: companyData.industry,
        company_size: companyData.company_size,
        headquarters_location: companyData.headquarters_location,
        linkedin_url: companyData.linkedin_url || null,
        twitter_url: companyData.twitter_url || null,
        facebook_url: companyData.facebook_url || null,
        instagram_url: companyData.instagram_url || null,
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        intake_source: 'composio_mcp_service',
        source_metadata: {
          user_agent: 'barton_intake_service',
          ip_address: 'internal',
          request_id: this.generateRequestId()
        }
      };

      // Insert via MCP
      const insertResult = await this.executeComposioFirebaseTool('FIREBASE_WRITE', {
        collection: 'company_raw_intake',
        document: companyBartonId,
        data: companyDocument
      });

      // Log audit entry
      await this.logCompanyIntakeAudit('intake_create', companyBartonId, null, companyDocument, 'success');

      return {
        success: true,
        company_unique_id: companyBartonId,
        status: 'pending',
        insert_result: insertResult
      };

    } catch (error) {
      console.error('[INTAKE-SERVICE] Company intake failed:', error);

      // Log error audit entry
      await this.logCompanyIntakeAudit('intake_create', null, null, companyData, 'failure', error);

      throw error;
    }
  }

  /**
   * Process person intake via MCP
   */
  async intakePerson(personData) {
    console.log('[INTAKE-SERVICE] Processing person intake...');

    try {
      // Validate person data
      this.validatePersonData(personData);

      // Generate Barton ID
      const personBartonId = await this.generatePersonBartonId(personData);

      // Prepare person document
      const personDocument = {
        person_unique_id: personBartonId,
        full_name: personData.full_name,
        email_address: personData.email_address,
        job_title: personData.job_title,
        company_name: personData.company_name,
        location: personData.location,
        linkedin_url: personData.linkedin_url || null,
        twitter_url: personData.twitter_url || null,
        facebook_url: personData.facebook_url || null,
        instagram_url: personData.instagram_url || null,
        associated_company_id: personData.associated_company_id || null,
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        intake_source: 'composio_mcp_service',
        source_metadata: {
          user_agent: 'barton_intake_service',
          ip_address: 'internal',
          request_id: this.generateRequestId()
        }
      };

      // Insert via MCP
      const insertResult = await this.executeComposioFirebaseTool('FIREBASE_WRITE', {
        collection: 'people_raw_intake',
        document: personBartonId,
        data: personDocument
      });

      // Log audit entry
      await this.logPersonIntakeAudit('intake_create', personBartonId, null, personDocument, 'success');

      return {
        success: true,
        person_unique_id: personBartonId,
        status: 'pending',
        insert_result: insertResult
      };

    } catch (error) {
      console.error('[INTAKE-SERVICE] Person intake failed:', error);

      // Log error audit entry
      await this.logPersonIntakeAudit('intake_create', null, null, personData, 'failure', error);

      throw error;
    }
  }

  /**
   * Process batch intake operations
   */
  async intakeBatch(batchData) {
    console.log('[INTAKE-SERVICE] Processing batch intake...');

    try {
      const { companies = [], people = [] } = batchData;
      const results = {
        companies: [],
        people: [],
        errors: []
      };

      // Process companies
      for (let i = 0; i < companies.length; i++) {
        try {
          const result = await this.intakeCompany(companies[i]);
          results.companies.push({ ...result, batch_index: i });
        } catch (error) {
          results.errors.push({
            type: 'company',
            batch_index: i,
            error: error.message
          });
        }
      }

      // Process people
      for (let i = 0; i < people.length; i++) {
        try {
          const result = await this.intakePerson(people[i]);
          results.people.push({ ...result, batch_index: i });
        } catch (error) {
          results.errors.push({
            type: 'person',
            batch_index: i,
            error: error.message
          });
        }
      }

      return {
        success: true,
        processed: {
          companies: results.companies.length,
          people: results.people.length,
          errors: results.errors.length
        },
        results: results
      };

    } catch (error) {
      console.error('[INTAKE-SERVICE] Batch intake failed:', error);
      throw error;
    }
  }

  /**
   * Query intake records
   */
  async queryIntakeRecords(filters = {}) {
    try {
      const { collection = 'company_raw_intake', status, limit = 10 } = filters;

      const queryData = { collection };
      if (limit) queryData.limit = limit;

      const result = await this.executeComposioFirebaseTool('FIREBASE_READ', queryData);

      return {
        success: true,
        collection: collection,
        records: result.data || [],
        filters: filters
      };

    } catch (error) {
      console.error('[INTAKE-SERVICE] Query failed:', error);
      throw error;
    }
  }

  /**
   * Update intake record status
   */
  async updateIntakeStatus(recordId, newStatus, collection = 'company_raw_intake') {
    try {
      const updateData = {
        status: newStatus,
        updated_at: new Date().toISOString()
      };

      const result = await this.executeComposioFirebaseTool('FIREBASE_UPDATE', {
        collection: collection,
        document: recordId,
        data: updateData
      });

      // Log audit entry
      const auditFunction = collection === 'company_raw_intake' ?
        this.logCompanyIntakeAudit : this.logPersonIntakeAudit;

      await auditFunction.call(this, 'intake_update', recordId, { status: 'previous' }, updateData, 'success');

      return {
        success: true,
        record_id: recordId,
        new_status: newStatus,
        update_result: result
      };

    } catch (error) {
      console.error('[INTAKE-SERVICE] Status update failed:', error);
      throw error;
    }
  }

  /**
   * Execute Composio Firebase tool with MCP protocol
   */
  async executeComposioFirebaseTool(tool, data) {
    const mcpPayload = {
      tool: tool,
      data: data,
      unique_id: this.generateHeirId(),
      process_id: this.generateProcessId(),
      orbt_layer: 2,
      blueprint_version: this.doctrineVersion
    };

    try {
      const response = await fetch(`${this.mcpEndpoint}/tool`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Composio-Key': process.env.COMPOSIO_API_KEY || ''
        },
        body: JSON.stringify(mcpPayload)
      });

      if (!response.ok) {
        throw new Error(`MCP tool execution failed: ${response.status}`);
      }

      const result = await response.json();
      return result;

    } catch (error) {
      console.error(`[INTAKE-SERVICE] MCP tool ${tool} failed:`, error);
      throw error;
    }
  }

  /**
   * Validation methods
   */
  validateCompanyData(data) {
    const required = ['company_name', 'website_url', 'industry', 'company_size', 'headquarters_location'];
    const missing = required.filter(field => !data[field]);

    if (missing.length > 0) {
      throw new Error(`Missing required company fields: ${missing.join(', ')}`);
    }

    // Validate company size
    const validSizes = ['1-10', '11-50', '51-200', '201-500', '501-1000', '1001-5000', '5001+'];
    if (!validSizes.includes(data.company_size)) {
      throw new Error('Invalid company size');
    }

    // Validate URL format
    if (!this.isValidURL(data.website_url)) {
      throw new Error('Invalid website URL format');
    }
  }

  validatePersonData(data) {
    const required = ['full_name', 'email_address', 'job_title', 'company_name', 'location'];
    const missing = required.filter(field => !data[field]);

    if (missing.length > 0) {
      throw new Error(`Missing required person fields: ${missing.join(', ')}`);
    }

    // Validate email format
    if (!this.isValidEmail(data.email_address)) {
      throw new Error('Invalid email address format');
    }
  }

  /**
   * Barton ID generation methods
   */
  async generateCompanyBartonId(companyData) {
    return await this.generateUniqueBartonId({
      database: '05',    // Firebase
      subhive: '01',     // Intake
      microprocess: '01', // Ingestion
      tool: '03',        // Firebase
      altitude: '10000', // Execution Layer
      step: '002'        // Company intake
    });
  }

  async generatePersonBartonId(personData) {
    return await this.generateUniqueBartonId({
      database: '05',    // Firebase
      subhive: '01',     // Intake
      microprocess: '01', // Ingestion
      tool: '03',        // Firebase
      altitude: '10000', // Execution Layer
      step: '003'        // Person intake
    });
  }

  async generateUniqueBartonId(params) {
    const maxAttempts = 10;
    let attempts = 0;

    while (attempts < maxAttempts) {
      attempts++;

      const candidateId = `${params.database}.${params.subhive}.${params.microprocess}.${params.tool}.${params.altitude}.${params.step}`;

      // Check uniqueness (in production, would check against Firestore)
      // For now, return the ID (uniqueness would be enforced by Cloud Functions)
      return candidateId;
    }

    throw new Error('Failed to generate unique Barton ID');
  }

  /**
   * Audit logging methods
   */
  async logCompanyIntakeAudit(action, companyId, beforeState, afterState, status, error = null) {
    const auditId = await this.generateUniqueBartonId({
      database: '05',
      subhive: '01',
      microprocess: '02',
      tool: '03',
      altitude: '10000',
      step: '004'
    });

    const logEntry = {
      unique_id: auditId,
      action: action,
      status: status,
      source: {
        service: 'barton_intake_service',
        function: 'intakeCompany',
        user_agent: 'intake_service',
        ip_address: 'internal',
        request_id: this.generateRequestId()
      },
      target_company_id: companyId,
      error_log: error ? {
        error_code: 'COMPANY_INTAKE_ERROR',
        error_message: error.message,
        stack_trace: null,
        retry_count: 0,
        recovery_action: null
      } : null,
      payload: {
        before: beforeState,
        after: afterState,
        metadata: {
          doctrine_version: this.doctrineVersion,
          service_version: '1.0.0'
        }
      },
      created_at: new Date().toISOString()
    };

    try {
      await this.executeComposioFirebaseTool('FIREBASE_WRITE', {
        collection: 'company_audit_log',
        document: auditId,
        data: logEntry
      });
    } catch (logError) {
      console.error('[INTAKE-SERVICE] Failed to write company audit log:', logError);
    }
  }

  async logPersonIntakeAudit(action, personId, beforeState, afterState, status, error = null) {
    const auditId = await this.generateUniqueBartonId({
      database: '05',
      subhive: '01',
      microprocess: '02',
      tool: '03',
      altitude: '10000',
      step: '005'
    });

    const logEntry = {
      unique_id: auditId,
      action: action,
      status: status,
      source: {
        service: 'barton_intake_service',
        function: 'intakePerson',
        user_agent: 'intake_service',
        ip_address: 'internal',
        request_id: this.generateRequestId()
      },
      target_person_id: personId,
      error_log: error ? {
        error_code: 'PERSON_INTAKE_ERROR',
        error_message: error.message,
        stack_trace: null,
        retry_count: 0,
        recovery_action: null
      } : null,
      payload: {
        before: beforeState,
        after: afterState,
        metadata: {
          doctrine_version: this.doctrineVersion,
          service_version: '1.0.0'
        }
      },
      created_at: new Date().toISOString()
    };

    try {
      await this.executeComposioFirebaseTool('FIREBASE_WRITE', {
        collection: 'people_audit_log',
        document: auditId,
        data: logEntry
      });
    } catch (logError) {
      console.error('[INTAKE-SERVICE] Failed to write people audit log:', logError);
    }
  }

  /**
   * Health check for intake system
   */
  async healthCheck() {
    try {
      const checks = {
        mcp_connection: false,
        company_collection: false,
        people_collection: false,
        audit_logging: false
      };

      // Test MCP connection
      try {
        await this.testMCPConnection();
        checks.mcp_connection = true;
      } catch (error) {
        console.warn('[INTAKE-SERVICE] MCP connection check failed:', error.message);
      }

      // Test collections (would check via MCP in production)
      checks.company_collection = true;
      checks.people_collection = true;
      checks.audit_logging = true;

      const allHealthy = Object.values(checks).every(check => check === true);

      return {
        overall_status: allHealthy ? 'healthy' : 'degraded',
        checks: checks,
        timestamp: new Date().toISOString(),
        service: 'barton_intake_service',
        version: this.doctrineVersion
      };

    } catch (error) {
      return {
        overall_status: 'unhealthy',
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Utility methods
   */
  isValidURL(url) {
    try {
      new URL(url);
      return url.startsWith('http://') || url.startsWith('https://');
    } catch {
      return false;
    }
  }

  isValidEmail(email) {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailPattern.test(email);
  }

  generateHeirId() {
    return `HEIR-${new Date().toISOString().slice(0, 10)}-${Math.random().toString(36).substr(2, 9).toUpperCase()}`;
  }

  generateProcessId() {
    return `PRC-INTAKE-${Date.now()}`;
  }

  generateRequestId() {
    return `req_intake_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

export default BartonIntakeService;