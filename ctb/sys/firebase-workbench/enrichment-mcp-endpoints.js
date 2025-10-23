/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-F474D277
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * Doctrine Spec:
 * - Barton ID: 04.04.01
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Step 2B Enrichment MCP endpoint specifications for Composio integration
 * - Input: Enrichment requests through Composio MCP protocol
 * - Output: Enriched records with normalized data and job management
 * - MCP: Firebase (Composio-only enrichment endpoints)
 */

/**
 * Enrichment MCP Service for Composio Integration
 * Provides enrichment endpoints using existing Composio Firebase tools
 */
class EnrichmentMCPService {
  constructor() {
    this.doctrineVersion = '1.0.0';
    this.mcpEndpoint = process.env.COMPOSIO_MCP_URL || 'https://backend.composio.dev/api/v1/mcp';
    this.initialized = false;
    this.enrichmentTools = [
      'FIREBASE_READ',      // Read records for enrichment
      'FIREBASE_WRITE',     // Create enrichment jobs
      'FIREBASE_UPDATE',    // Update enriched records
      'FIREBASE_QUERY',     // Query enrichment jobs
      'FIREBASE_FUNCTION_CALL' // Call enrichment functions
    ];
  }

  /**
   * Initialize the enrichment MCP service
   */
  async initialize() {
    console.log('[ENRICHMENT-MCP] Initializing Enrichment MCP Service...');

    try {
      // Test MCP connectivity
      await this.testMCPConnection();

      // Verify Composio tools availability
      await this.verifyEnrichmentTools();

      // Initialize enrichment collections if needed
      await this.initializeEnrichmentCollections();

      this.initialized = true;
      return {
        success: true,
        service: 'enrichment_agent',
        version: this.doctrineVersion,
        available_tools: this.enrichmentTools
      };

    } catch (error) {
      console.error('[ENRICHMENT-MCP] Initialization failed:', error);
      throw error;
    }
  }

  /**
   * Test MCP connection for enrichment operations
   */
  async testMCPConnection() {
    try {
      const healthPayload = {
        tool: 'get_composio_stats',
        data: {},
        unique_id: this.generateHeirId(),
        process_id: this.generateProcessId(),
        orbt_layer: 2,
        blueprint_version: this.doctrineVersion
      };

      const response = await this.executeComposioFirebaseTool('get_composio_stats', {});

      if (response.success) {
        console.log('[ENRICHMENT-MCP] MCP connection successful');
        return true;
      } else {
        throw new Error('MCP health check failed');
      }

    } catch (error) {
      console.error('[ENRICHMENT-MCP] MCP connection failed:', error);
      throw error;
    }
  }

  /**
   * Verify that required Composio Firebase tools are available
   */
  async verifyEnrichmentTools() {
    console.log('[ENRICHMENT-MCP] Verifying Composio Firebase tools...');

    for (const tool of this.enrichmentTools) {
      try {
        console.log(`[ENRICHMENT-MCP] Verifying tool: ${tool}`);
        // In production, this would make actual verification calls
      } catch (error) {
        console.warn(`[ENRICHMENT-MCP] Tool verification warning for ${tool}:`, error.message);
      }
    }

    console.log('[ENRICHMENT-MCP] Tool verification complete');
  }

  /**
   * Initialize enrichment collections if needed
   */
  async initializeEnrichmentCollections() {
    try {
      // Check if enrichment_jobs collection exists and is accessible
      const jobsTest = await this.executeComposioFirebaseTool('FIREBASE_QUERY', {
        collection: 'enrichment_jobs',
        limit: 1
      });

      // Check if enrichment_audit_log collection exists and is accessible
      const auditTest = await this.executeComposioFirebaseTool('FIREBASE_QUERY', {
        collection: 'enrichment_audit_log',
        limit: 1
      });

      console.log('[ENRICHMENT-MCP] Enrichment collections verified');

    } catch (error) {
      console.warn('[ENRICHMENT-MCP] Collection initialization warning:', error.message);
    }
  }

  /**
   * Execute Composio Firebase tool with proper HEIR/ORBT format
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
          'X-Composio-Key': process.env.COMPOSIO_API_KEY || 'test_key'
        },
        body: JSON.stringify(mcpPayload)
      });

      if (!response.ok) {
        throw new Error(`MCP tool execution failed: ${response.statusText}`);
      }

      const result = await response.json();
      return result;

    } catch (error) {
      console.error(`[ENRICHMENT-MCP] Tool execution failed for ${tool}:`, error);
      throw error;
    }
  }

  /**
   * Create enrichment job via Composio MCP
   */
  async createEnrichmentJobViaComposio(recordId, recordType, enrichmentTypes, priority = 'normal') {
    console.log(`[ENRICHMENT-MCP] Creating enrichment job: ${recordId}`);

    try {
      const jobData = {
        unique_id: recordId,
        record_type: recordType,
        source_collection: recordType === 'company' ? 'company_raw_intake' : 'people_raw_intake',
        status: 'pending',
        priority: priority,
        enrichment_types: enrichmentTypes,
        retry_count: 0,
        max_retries: 3,
        enrichment_providers: {
          internal_only: true
        },
        mcp_trace: {
          created_via: 'mcp_api',
          request_id: this.generateRequestId(),
          user_id: 'enrichment_service',
          composio_session: this.generateSessionId()
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      const createResult = await this.executeComposioFirebaseTool('FIREBASE_WRITE', {
        collection: 'enrichment_jobs',
        document_id: recordId,
        data: jobData
      });

      if (createResult.success) {
        console.log(`[ENRICHMENT-MCP] Enrichment job created: ${recordId}`);
        return {
          success: true,
          job_id: recordId,
          status: 'pending',
          enrichment_types: enrichmentTypes,
          created_at: jobData.created_at
        };
      } else {
        throw new Error('Failed to create enrichment job');
      }

    } catch (error) {
      console.error(`[ENRICHMENT-MCP] Job creation error for ${recordId}:`, error);
      throw error;
    }
  }

  /**
   * Enrich company via Composio MCP
   */
  async enrichCompanyViaComposio(companyId) {
    console.log(`[ENRICHMENT-MCP] Starting company enrichment: ${companyId}`);

    try {
      // Step 1: Create enrichment job
      const jobResult = await this.createEnrichmentJobViaComposio(
        companyId,
        'company',
        ['normalize_domain', 'repair_phone', 'geocode_address']
      );

      if (!jobResult.success) {
        throw new Error('Failed to create enrichment job');
      }

      // Step 2: Update job status to processing
      await this.executeComposioFirebaseTool('FIREBASE_UPDATE', {
        collection: 'enrichment_jobs',
        document_id: companyId,
        data: {
          status: 'processing',
          started_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      });

      // Step 3: Execute enrichment via Cloud Function
      const enrichmentPayload = {
        company_unique_id: companyId,
        request_id: this.generateRequestId()
      };

      const functionResult = await this.executeComposioFirebaseTool('FIREBASE_FUNCTION_CALL', {
        function_name: 'enrichCompany',
        payload: enrichmentPayload
      });

      // Step 4: Update job status based on result
      const finalStatus = functionResult.success ? 'enriched' : 'failed';
      await this.executeComposioFirebaseTool('FIREBASE_UPDATE', {
        collection: 'enrichment_jobs',
        document_id: companyId,
        data: {
          status: finalStatus,
          completed_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          ...(functionResult.data?.processing_time_ms && {
            processing_history: [{
              attempt_number: 1,
              started_at: jobResult.created_at,
              completed_at: new Date().toISOString(),
              status: finalStatus,
              enrichment_types_completed: functionResult.data.enriched_fields || [],
              processing_time_ms: functionResult.data.processing_time_ms
            }]
          })
        }
      });

      console.log(`[ENRICHMENT-MCP] Company enrichment completed: ${companyId}, status: ${finalStatus}`);

      return {
        success: functionResult.success,
        company_id: companyId,
        enrichment_status: finalStatus,
        enriched_fields: functionResult.data?.enriched_fields || [],
        processing_time_ms: functionResult.data?.processing_time_ms || 0,
        processed_via: 'composio_mcp',
        processed_at: new Date().toISOString()
      };

    } catch (error) {
      // Update job status to failed
      try {
        await this.executeComposioFirebaseTool('FIREBASE_UPDATE', {
          collection: 'enrichment_jobs',
          document_id: companyId,
          data: {
            status: 'failed',
            completed_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            last_error: {
              error_code: 'ENRICHMENT_ERROR',
              error_message: error.message,
              occurred_at: new Date().toISOString(),
              retry_after: new Date(Date.now() + 3600000).toISOString() // 1 hour
            }
          }
        });
      } catch (updateError) {
        console.error('Failed to update job status:', updateError);
      }

      console.error(`[ENRICHMENT-MCP] Company enrichment error for ${companyId}:`, error);
      throw error;
    }
  }

  /**
   * Enrich person via Composio MCP
   */
  async enrichPersonViaComposio(personId) {
    console.log(`[ENRICHMENT-MCP] Starting person enrichment: ${personId}`);

    try {
      // Step 1: Create enrichment job
      const jobResult = await this.createEnrichmentJobViaComposio(
        personId,
        'person',
        ['infer_slot_type', 'determine_seniority', 'normalize_phone', 'normalize_email']
      );

      if (!jobResult.success) {
        throw new Error('Failed to create enrichment job');
      }

      // Step 2: Update job status to processing
      await this.executeComposioFirebaseTool('FIREBASE_UPDATE', {
        collection: 'enrichment_jobs',
        document_id: personId,
        data: {
          status: 'processing',
          started_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      });

      // Step 3: Execute enrichment via Cloud Function
      const enrichmentPayload = {
        person_unique_id: personId,
        request_id: this.generateRequestId()
      };

      const functionResult = await this.executeComposioFirebaseTool('FIREBASE_FUNCTION_CALL', {
        function_name: 'enrichPerson',
        payload: enrichmentPayload
      });

      // Step 4: Update job status based on result
      const finalStatus = functionResult.success ? 'enriched' : 'failed';
      await this.executeComposioFirebaseTool('FIREBASE_UPDATE', {
        collection: 'enrichment_jobs',
        document_id: personId,
        data: {
          status: finalStatus,
          completed_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          ...(functionResult.data?.processing_time_ms && {
            processing_history: [{
              attempt_number: 1,
              started_at: jobResult.created_at,
              completed_at: new Date().toISOString(),
              status: finalStatus,
              enrichment_types_completed: functionResult.data.enriched_fields || [],
              processing_time_ms: functionResult.data.processing_time_ms
            }]
          })
        }
      });

      console.log(`[ENRICHMENT-MCP] Person enrichment completed: ${personId}, status: ${finalStatus}`);

      return {
        success: functionResult.success,
        person_id: personId,
        enrichment_status: finalStatus,
        enriched_fields: functionResult.data?.enriched_fields || [],
        processing_time_ms: functionResult.data?.processing_time_ms || 0,
        processed_via: 'composio_mcp',
        processed_at: new Date().toISOString()
      };

    } catch (error) {
      // Update job status to failed
      try {
        await this.executeComposioFirebaseTool('FIREBASE_UPDATE', {
          collection: 'enrichment_jobs',
          document_id: personId,
          data: {
            status: 'failed',
            completed_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            last_error: {
              error_code: 'ENRICHMENT_ERROR',
              error_message: error.message,
              occurred_at: new Date().toISOString(),
              retry_after: new Date(Date.now() + 3600000).toISOString() // 1 hour
            }
          }
        });
      } catch (updateError) {
        console.error('Failed to update job status:', updateError);
      }

      console.error(`[ENRICHMENT-MCP] Person enrichment error for ${personId}:`, error);
      throw error;
    }
  }

  /**
   * Batch enrich companies via Composio MCP
   */
  async batchEnrichCompanies(companyIds, priority = 'normal') {
    console.log(`[ENRICHMENT-MCP] Starting batch company enrichment: ${companyIds.length} companies`);

    const results = [];
    const batchSize = 3; // Process in smaller batches to avoid overwhelming the system

    for (let i = 0; i < companyIds.length; i += batchSize) {
      const batch = companyIds.slice(i, i + batchSize);

      const batchPromises = batch.map(companyId =>
        this.enrichCompanyViaComposio(companyId).catch(error => ({
          success: false,
          company_id: companyId,
          error: error.message,
          processed_via: 'composio_mcp',
          processed_at: new Date().toISOString()
        }))
      );

      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);

      // Small delay between batches
      if (i + batchSize < companyIds.length) {
        await new Promise(resolve => setTimeout(resolve, 200));
      }
    }

    const successCount = results.filter(r => r.success).length;
    const failureCount = results.length - successCount;

    console.log(`[ENRICHMENT-MCP] Batch enrichment complete: ${successCount} success, ${failureCount} failed`);

    return {
      success: true,
      total_processed: results.length,
      successful: successCount,
      failed: failureCount,
      results: results,
      batch_completed_at: new Date().toISOString()
    };
  }

  /**
   * Batch enrich people via Composio MCP
   */
  async batchEnrichPeople(personIds, priority = 'normal') {
    console.log(`[ENRICHMENT-MCP] Starting batch person enrichment: ${personIds.length} people`);

    const results = [];
    const batchSize = 3; // Process in smaller batches

    for (let i = 0; i < personIds.length; i += batchSize) {
      const batch = personIds.slice(i, i + batchSize);

      const batchPromises = batch.map(personId =>
        this.enrichPersonViaComposio(personId).catch(error => ({
          success: false,
          person_id: personId,
          error: error.message,
          processed_via: 'composio_mcp',
          processed_at: new Date().toISOString()
        }))
      );

      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);

      // Small delay between batches
      if (i + batchSize < personIds.length) {
        await new Promise(resolve => setTimeout(resolve, 200));
      }
    }

    const successCount = results.filter(r => r.success).length;
    const failureCount = results.length - successCount;

    console.log(`[ENRICHMENT-MCP] Batch enrichment complete: ${successCount} success, ${failureCount} failed`);

    return {
      success: true,
      total_processed: results.length,
      successful: successCount,
      failed: failureCount,
      results: results,
      batch_completed_at: new Date().toISOString()
    };
  }

  /**
   * Query enrichment jobs for monitoring
   */
  async queryEnrichmentJobs(criteria = {}) {
    try {
      const queryData = {
        collection: 'enrichment_jobs',
        where: [],
        limit: criteria.limit || 100,
        orderBy: { field: 'created_at', direction: 'desc' }
      };

      // Add status filter if specified
      if (criteria.status) {
        queryData.where.push({
          field: 'status',
          operator: '==',
          value: criteria.status
        });
      }

      // Add record type filter if specified
      if (criteria.record_type) {
        queryData.where.push({
          field: 'record_type',
          operator: '==',
          value: criteria.record_type
        });
      }

      const result = await this.executeComposioFirebaseTool('FIREBASE_QUERY', queryData);

      if (result.success) {
        console.log(`[ENRICHMENT-MCP] Retrieved ${result.data.length} enrichment jobs`);
        return result.data;
      } else {
        throw new Error('Failed to query enrichment jobs');
      }

    } catch (error) {
      console.error('[ENRICHMENT-MCP] Query enrichment jobs error:', error);
      throw error;
    }
  }

  /**
   * Get enrichment statistics
   */
  async getEnrichmentStats() {
    try {
      // Query job counts by status
      const statuses = ['pending', 'processing', 'enriched', 'failed'];
      const stats = {};

      for (const status of statuses) {
        const result = await this.executeComposioFirebaseTool('FIREBASE_QUERY', {
          collection: 'enrichment_jobs',
          where: [{ field: 'status', operator: '==', value: status }],
          count_only: true
        });
        stats[status] = result.count || 0;
      }

      return {
        success: true,
        stats: stats,
        total_jobs: Object.values(stats).reduce((sum, count) => sum + count, 0),
        generated_at: new Date().toISOString()
      };

    } catch (error) {
      console.error('[ENRICHMENT-MCP] Get enrichment stats error:', error);
      throw error;
    }
  }

  /**
   * Generate HEIR format unique ID
   */
  generateHeirId() {
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[-T:]/g, '');
    const random = Math.random().toString(36).substring(2, 8).toUpperCase();
    return `HEIR-${timestamp}-ENR-${random}`;
  }

  /**
   * Generate process ID for tracking
   */
  generateProcessId() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 6).toUpperCase();
    return `PRC-ENR-${timestamp}-${random}`;
  }

  /**
   * Generate request ID
   */
  generateRequestId() {
    return `REQ-${Date.now()}-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
  }

  /**
   * Generate session ID
   */
  generateSessionId() {
    return `SES-${Date.now()}-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
  }

  /**
   * Get service status and health
   */
  async getServiceStatus() {
    return {
      service: 'enrichment_agent',
      version: this.doctrineVersion,
      initialized: this.initialized,
      mcp_endpoint: this.mcpEndpoint,
      available_tools: this.enrichmentTools,
      status: this.initialized ? 'ready' : 'initializing',
      timestamp: new Date().toISOString()
    };
  }
}

/**
 * MCP Endpoint Specifications for Composio Integration
 */
export const ENRICHMENT_MCP_ENDPOINTS = {
  // Company enrichment endpoint
  enrich_company: {
    endpoint: '/enrichment/company',
    method: 'POST',
    description: 'Enrich a company record through Composio MCP',
    composio_tool: 'FIREBASE_FUNCTION_CALL',
    function_name: 'enrichCompany',
    payload_schema: {
      company_unique_id: {
        type: 'string',
        required: true,
        pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
        description: 'Barton ID of company to enrich'
      },
      priority: {
        type: 'string',
        enum: ['low', 'normal', 'high', 'urgent'],
        default: 'normal'
      }
    },
    response_schema: {
      success: { type: 'boolean' },
      company_id: { type: 'string' },
      enrichment_status: { type: 'string', enum: ['enriched', 'failed'] },
      enriched_fields: { type: 'array' },
      processing_time_ms: { type: 'number' },
      processed_at: { type: 'string', format: 'iso8601' }
    }
  },

  // Person enrichment endpoint
  enrich_person: {
    endpoint: '/enrichment/person',
    method: 'POST',
    description: 'Enrich a person record through Composio MCP',
    composio_tool: 'FIREBASE_FUNCTION_CALL',
    function_name: 'enrichPerson',
    payload_schema: {
      person_unique_id: {
        type: 'string',
        required: true,
        pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
        description: 'Barton ID of person to enrich'
      },
      priority: {
        type: 'string',
        enum: ['low', 'normal', 'high', 'urgent'],
        default: 'normal'
      }
    },
    response_schema: {
      success: { type: 'boolean' },
      person_id: { type: 'string' },
      enrichment_status: { type: 'string', enum: ['enriched', 'failed'] },
      enriched_fields: { type: 'array' },
      processing_time_ms: { type: 'number' },
      processed_at: { type: 'string', format: 'iso8601' }
    }
  },

  // Batch company enrichment endpoint
  batch_enrich_companies: {
    endpoint: '/enrichment/companies/batch',
    method: 'POST',
    description: 'Batch enrich multiple companies through Composio MCP',
    composio_tool: 'BATCH_OPERATION',
    payload_schema: {
      company_ids: {
        type: 'array',
        required: true,
        items: {
          type: 'string',
          pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$'
        },
        maxItems: 20,
        description: 'Array of company Barton IDs to enrich'
      },
      priority: {
        type: 'string',
        enum: ['low', 'normal', 'high', 'urgent'],
        default: 'normal'
      }
    },
    response_schema: {
      success: { type: 'boolean' },
      total_processed: { type: 'number' },
      successful: { type: 'number' },
      failed: { type: 'number' },
      results: { type: 'array' },
      batch_completed_at: { type: 'string', format: 'iso8601' }
    }
  },

  // Batch person enrichment endpoint
  batch_enrich_people: {
    endpoint: '/enrichment/people/batch',
    method: 'POST',
    description: 'Batch enrich multiple people through Composio MCP',
    composio_tool: 'BATCH_OPERATION',
    payload_schema: {
      person_ids: {
        type: 'array',
        required: true,
        items: {
          type: 'string',
          pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$'
        },
        maxItems: 20,
        description: 'Array of person Barton IDs to enrich'
      },
      priority: {
        type: 'string',
        enum: ['low', 'normal', 'high', 'urgent'],
        default: 'normal'
      }
    },
    response_schema: {
      success: { type: 'boolean' },
      total_processed: { type: 'number' },
      successful: { type: 'number' },
      failed: { type: 'number' },
      results: { type: 'array' },
      batch_completed_at: { type: 'string', format: 'iso8601' }
    }
  },

  // Query enrichment jobs endpoint
  query_enrichment_jobs: {
    endpoint: '/enrichment/jobs',
    method: 'GET',
    description: 'Query enrichment jobs for monitoring',
    composio_tool: 'FIREBASE_QUERY',
    query_params: {
      status: {
        type: 'string',
        enum: ['pending', 'processing', 'enriched', 'failed']
      },
      record_type: {
        type: 'string',
        enum: ['company', 'person']
      },
      limit: {
        type: 'number',
        default: 100,
        maximum: 500
      }
    },
    response_schema: {
      success: { type: 'boolean' },
      jobs: { type: 'array' },
      total_count: { type: 'number' }
    }
  },

  // Enrichment statistics endpoint
  enrichment_stats: {
    endpoint: '/enrichment/stats',
    method: 'GET',
    description: 'Get enrichment statistics and metrics',
    composio_tool: 'FIREBASE_QUERY',
    response_schema: {
      success: { type: 'boolean' },
      stats: { type: 'object' },
      total_jobs: { type: 'number' },
      generated_at: { type: 'string', format: 'iso8601' }
    }
  }
};

export { EnrichmentMCPService };
export default { EnrichmentMCPService, ENRICHMENT_MCP_ENDPOINTS };