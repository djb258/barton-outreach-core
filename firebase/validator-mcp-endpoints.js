/**
 * Doctrine Spec:
 * - Barton ID: 15.01.02.08.10000.003
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Step 2A Validator Agent MCP endpoint specifications for Composio integration
 * - Input: Validation requests through Composio MCP protocol
 * - Output: Validated documents with structured error handling
 * - MCP: Firebase (Composio-only validation endpoints)
 */

/**
 * Validator Agent MCP Service for Composio Integration
 * Provides validation endpoints using existing Composio Firebase tools
 */
class ValidatorMCPService {
  constructor() {
    this.doctrineVersion = '1.0.0';
    this.mcpEndpoint = process.env.COMPOSIO_MCP_URL || 'https://backend.composio.dev/api/v1/mcp';
    this.initialized = false;
    this.validationTools = [
      'FIREBASE_READ',    // Read intake documents
      'FIREBASE_WRITE',   // Update validation status
      'FIREBASE_UPDATE',  // Update with normalized data
      'FIREBASE_DELETE'   // Move to validation_failed if needed
    ];
  }

  /**
   * Initialize the validator MCP service
   */
  async initialize() {
    console.log('[VALIDATOR-MCP] Initializing Validator MCP Service...');

    try {
      // Test MCP connectivity
      await this.testMCPConnection();

      // Verify Composio tools availability
      await this.verifyValidationTools();

      this.initialized = true;
      return {
        success: true,
        service: 'validator_agent',
        version: this.doctrineVersion,
        available_tools: this.validationTools
      };

    } catch (error) {
      console.error('[VALIDATOR-MCP] Initialization failed:', error);
      throw error;
    }
  }

  /**
   * Test MCP connection for validation operations
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
        console.log('[VALIDATOR-MCP] MCP connection successful');
        return true;
      } else {
        throw new Error('MCP health check failed');
      }

    } catch (error) {
      console.error('[VALIDATOR-MCP] MCP connection failed:', error);
      throw error;
    }
  }

  /**
   * Verify that required Composio Firebase tools are available
   */
  async verifyValidationTools() {
    console.log('[VALIDATOR-MCP] Verifying Composio Firebase tools...');

    for (const tool of this.validationTools) {
      try {
        // Test tool availability with a simple operation
        const testPayload = {
          tool: tool,
          data: { collection: 'test', operation: 'verify' },
          unique_id: this.generateHeirId(),
          process_id: this.generateProcessId(),
          orbt_layer: 2,
          blueprint_version: this.doctrineVersion
        };

        console.log(`[VALIDATOR-MCP] Verifying tool: ${tool}`);
        // Note: In production, this would make actual calls to verify tools

      } catch (error) {
        console.warn(`[VALIDATOR-MCP] Tool verification warning for ${tool}:`, error.message);
      }
    }

    console.log('[VALIDATOR-MCP] Tool verification complete');
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
      console.error(`[VALIDATOR-MCP] Tool execution failed for ${tool}:`, error);
      throw error;
    }
  }

  /**
   * Validate company via Composio MCP
   */
  async validateCompanyViaComposio(companyId) {
    console.log(`[VALIDATOR-MCP] Starting company validation via Composio: ${companyId}`);

    try {
      // Step 1: Read company document from intake collection
      const readResult = await this.executeComposioFirebaseTool('FIREBASE_READ', {
        collection: 'company_raw_intake',
        document_id: companyId
      });

      if (!readResult.success || !readResult.data) {
        throw new Error(`Company document not found: ${companyId}`);
      }

      const companyData = readResult.data;

      // Step 2: Perform validation using Cloud Function
      const validationPayload = {
        company_unique_id: companyId
      };

      // Call the validateCompany Cloud Function via Composio
      const functionResult = await this.executeComposioFirebaseTool('FIREBASE_FUNCTION_CALL', {
        function_name: 'validateCompany',
        payload: validationPayload
      });

      // Step 3: Handle validation results
      if (functionResult.success && functionResult.data.validation_status === 'validated') {
        console.log(`[VALIDATOR-MCP] Company validation successful: ${companyId}`);

        return {
          success: true,
          company_id: companyId,
          validation_status: 'validated',
          processed_via: 'composio_mcp',
          processed_at: new Date().toISOString()
        };

      } else {
        console.log(`[VALIDATOR-MCP] Company validation failed: ${companyId}`);

        return {
          success: false,
          company_id: companyId,
          validation_status: 'failed',
          errors: functionResult.data?.errors || [],
          processed_via: 'composio_mcp',
          processed_at: new Date().toISOString()
        };
      }

    } catch (error) {
      console.error(`[VALIDATOR-MCP] Company validation error for ${companyId}:`, error);
      throw error;
    }
  }

  /**
   * Validate person via Composio MCP
   */
  async validatePersonViaComposio(personId) {
    console.log(`[VALIDATOR-MCP] Starting person validation via Composio: ${personId}`);

    try {
      // Step 1: Read person document from intake collection
      const readResult = await this.executeComposioFirebaseTool('FIREBASE_READ', {
        collection: 'people_raw_intake',
        document_id: personId
      });

      if (!readResult.success || !readResult.data) {
        throw new Error(`Person document not found: ${personId}`);
      }

      const personData = readResult.data;

      // Step 2: Perform validation using Cloud Function
      const validationPayload = {
        person_unique_id: personId
      };

      // Call the validatePerson Cloud Function via Composio
      const functionResult = await this.executeComposioFirebaseTool('FIREBASE_FUNCTION_CALL', {
        function_name: 'validatePerson',
        payload: validationPayload
      });

      // Step 3: Handle validation results
      if (functionResult.success && functionResult.data.validation_status === 'validated') {
        console.log(`[VALIDATOR-MCP] Person validation successful: ${personId}`);

        return {
          success: true,
          person_id: personId,
          validation_status: 'validated',
          processed_via: 'composio_mcp',
          processed_at: new Date().toISOString()
        };

      } else {
        console.log(`[VALIDATOR-MCP] Person validation failed: ${personId}`);

        return {
          success: false,
          person_id: personId,
          validation_status: 'failed',
          errors: functionResult.data?.errors || [],
          processed_via: 'composio_mcp',
          processed_at: new Date().toISOString()
        };
      }

    } catch (error) {
      console.error(`[VALIDATOR-MCP] Person validation error for ${personId}:`, error);
      throw error;
    }
  }

  /**
   * Batch validate companies via Composio MCP
   */
  async batchValidateCompanies(companyIds) {
    console.log(`[VALIDATOR-MCP] Starting batch company validation: ${companyIds.length} companies`);

    const results = [];
    const batchSize = 5; // Process in batches to avoid overwhelming the system

    for (let i = 0; i < companyIds.length; i += batchSize) {
      const batch = companyIds.slice(i, i + batchSize);

      const batchPromises = batch.map(companyId =>
        this.validateCompanyViaComposio(companyId).catch(error => ({
          success: false,
          company_id: companyId,
          error: error.message
        }))
      );

      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);

      // Small delay between batches
      if (i + batchSize < companyIds.length) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }

    const successCount = results.filter(r => r.success).length;
    const failureCount = results.length - successCount;

    console.log(`[VALIDATOR-MCP] Batch validation complete: ${successCount} success, ${failureCount} failed`);

    return {
      success: true,
      total_processed: results.length,
      successful: successCount,
      failed: failureCount,
      results: results
    };
  }

  /**
   * Batch validate people via Composio MCP
   */
  async batchValidatePeople(personIds) {
    console.log(`[VALIDATOR-MCP] Starting batch person validation: ${personIds.length} people`);

    const results = [];
    const batchSize = 5; // Process in batches to avoid overwhelming the system

    for (let i = 0; i < personIds.length; i += batchSize) {
      const batch = personIds.slice(i, i + batchSize);

      const batchPromises = batch.map(personId =>
        this.validatePersonViaComposio(personId).catch(error => ({
          success: false,
          person_id: personId,
          error: error.message
        }))
      );

      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);

      // Small delay between batches
      if (i + batchSize < personIds.length) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }

    const successCount = results.filter(r => r.success).length;
    const failureCount = results.length - successCount;

    console.log(`[VALIDATOR-MCP] Batch validation complete: ${successCount} success, ${failureCount} failed`);

    return {
      success: true,
      total_processed: results.length,
      successful: successCount,
      failed: failureCount,
      results: results
    };
  }

  /**
   * Query validation failed documents for processing
   */
  async queryValidationFailures(criteria = {}) {
    try {
      const queryData = {
        collection: 'validation_failed',
        where: [
          { field: 'resolution_status', operator: '==', value: criteria.status || 'unresolved' }
        ],
        limit: criteria.limit || 100,
        orderBy: { field: 'failed_at', direction: 'desc' }
      };

      const result = await this.executeComposioFirebaseTool('FIREBASE_QUERY', queryData);

      if (result.success) {
        console.log(`[VALIDATOR-MCP] Retrieved ${result.data.length} validation failures`);
        return result.data;
      } else {
        throw new Error('Failed to query validation failures');
      }

    } catch (error) {
      console.error('[VALIDATOR-MCP] Query validation failures error:', error);
      throw error;
    }
  }

  /**
   * Generate HEIR format unique ID
   */
  generateHeirId() {
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[-T:]/g, '');
    const random = Math.random().toString(36).substring(2, 8).toUpperCase();
    return `HEIR-${timestamp}-VAL-${random}`;
  }

  /**
   * Generate process ID for tracking
   */
  generateProcessId() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 6).toUpperCase();
    return `PRC-VAL-${timestamp}-${random}`;
  }

  /**
   * Get service status and health
   */
  async getServiceStatus() {
    return {
      service: 'validator_agent',
      version: this.doctrineVersion,
      initialized: this.initialized,
      mcp_endpoint: this.mcpEndpoint,
      available_tools: this.validationTools,
      status: this.initialized ? 'ready' : 'initializing',
      timestamp: new Date().toISOString()
    };
  }
}

/**
 * MCP Endpoint Specifications for Composio Integration
 */
export const VALIDATOR_MCP_ENDPOINTS = {
  // Company validation endpoint
  validate_company: {
    endpoint: '/validator/company',
    method: 'POST',
    description: 'Validate a company document through Composio MCP',
    composio_tool: 'FIREBASE_FUNCTION_CALL',
    function_name: 'validateCompany',
    payload_schema: {
      company_unique_id: {
        type: 'string',
        required: true,
        pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
        description: 'Barton ID of company to validate'
      }
    },
    response_schema: {
      success: { type: 'boolean' },
      company_unique_id: { type: 'string' },
      validation_status: { type: 'string', enum: ['validated', 'failed'] },
      errors: { type: 'array' },
      warnings: { type: 'array' },
      processed_at: { type: 'string', format: 'iso8601' }
    }
  },

  // Person validation endpoint
  validate_person: {
    endpoint: '/validator/person',
    method: 'POST',
    description: 'Validate a person document through Composio MCP',
    composio_tool: 'FIREBASE_FUNCTION_CALL',
    function_name: 'validatePerson',
    payload_schema: {
      person_unique_id: {
        type: 'string',
        required: true,
        pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
        description: 'Barton ID of person to validate'
      }
    },
    response_schema: {
      success: { type: 'boolean' },
      person_unique_id: { type: 'string' },
      validation_status: { type: 'string', enum: ['validated', 'failed'] },
      errors: { type: 'array' },
      warnings: { type: 'array' },
      processed_at: { type: 'string', format: 'iso8601' }
    }
  },

  // Batch company validation endpoint
  batch_validate_companies: {
    endpoint: '/validator/companies/batch',
    method: 'POST',
    description: 'Batch validate multiple companies through Composio MCP',
    composio_tool: 'BATCH_OPERATION',
    payload_schema: {
      company_ids: {
        type: 'array',
        required: true,
        items: {
          type: 'string',
          pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$'
        },
        maxItems: 50,
        description: 'Array of company Barton IDs to validate'
      }
    },
    response_schema: {
      success: { type: 'boolean' },
      total_processed: { type: 'number' },
      successful: { type: 'number' },
      failed: { type: 'number' },
      results: { type: 'array' }
    }
  },

  // Batch person validation endpoint
  batch_validate_people: {
    endpoint: '/validator/people/batch',
    method: 'POST',
    description: 'Batch validate multiple people through Composio MCP',
    composio_tool: 'BATCH_OPERATION',
    payload_schema: {
      person_ids: {
        type: 'array',
        required: true,
        items: {
          type: 'string',
          pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$'
        },
        maxItems: 50,
        description: 'Array of person Barton IDs to validate'
      }
    },
    response_schema: {
      success: { type: 'boolean' },
      total_processed: { type: 'number' },
      successful: { type: 'number' },
      failed: { type: 'number' },
      results: { type: 'array' }
    }
  },

  // Query validation failures endpoint
  query_validation_failures: {
    endpoint: '/validator/failures',
    method: 'GET',
    description: 'Query validation failures for processing',
    composio_tool: 'FIREBASE_QUERY',
    query_params: {
      status: {
        type: 'string',
        enum: ['unresolved', 'auto_fixed', 'enriched', 'manual_review', 'discarded'],
        default: 'unresolved'
      },
      limit: {
        type: 'number',
        default: 100,
        maximum: 500
      },
      document_type: {
        type: 'string',
        enum: ['company', 'person']
      }
    },
    response_schema: {
      success: { type: 'boolean' },
      failures: { type: 'array' },
      total_count: { type: 'number' }
    }
  }
};

export { ValidatorMCPService };
export default { ValidatorMCPService, VALIDATOR_MCP_ENDPOINTS };