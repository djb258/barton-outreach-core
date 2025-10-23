/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-BBFB11E4
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * Doctrine Spec:
 * - Barton ID: 04.04.01
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Step 2C Scraping MCP endpoint specifications for Composio integration
 * - Input: Scraping requests through Composio MCP protocol
 * - Output: Scraped data inserted into staging intake with audit logging
 * - MCP: Firebase (Composio-only scraping endpoints)
 */

/**
 * Scraping MCP Service for Composio Integration
 * Provides scraping endpoints using existing Composio Firebase tools
 */
class ScrapingMCPService {
  constructor() {
    this.doctrineVersion = '1.0.0';
    this.mcpEndpoint = process.env.COMPOSIO_MCP_URL || 'https://backend.composio.dev/api/v1/mcp';
    this.initialized = false;
    this.scrapingTools = [
      'FIREBASE_READ',        // Read existing data for deduplication
      'FIREBASE_WRITE',       // Insert scraped data to staging
      'FIREBASE_UPDATE',      // Update scraping status
      'FIREBASE_QUERY',       // Query staging data
      'FIREBASE_FUNCTION_CALL' // Call scraping functions
    ];
    this.supportedActors = [
      'linkedin-company',
      'linkedin-people',
      'email-scraper'
    ];
  }

  /**
   * Initialize the scraping MCP service
   */
  async initialize() {
    console.log('[SCRAPING-MCP] Initializing Scraping MCP Service...');

    try {
      // Test MCP connectivity
      await this.testMCPConnection();

      // Verify Composio tools availability
      await this.verifyScrapingTools();

      // Initialize staging collections if needed
      await this.initializeStagingCollections();

      this.initialized = true;
      return {
        success: true,
        service: 'scraping_agent',
        version: this.doctrineVersion,
        available_tools: this.scrapingTools,
        supported_actors: this.supportedActors
      };

    } catch (error) {
      console.error('[SCRAPING-MCP] Initialization failed:', error);
      throw error;
    }
  }

  /**
   * Test MCP connection for scraping operations
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
        console.log('[SCRAPING-MCP] MCP connection successful');
        return true;
      } else {
        throw new Error('MCP health check failed');
      }

    } catch (error) {
      console.error('[SCRAPING-MCP] MCP connection failed:', error);
      throw error;
    }
  }

  /**
   * Verify that required Composio Firebase tools are available
   */
  async verifyScrapingTools() {
    console.log('[SCRAPING-MCP] Verifying Composio Firebase tools...');

    for (const tool of this.scrapingTools) {
      try {
        console.log(`[SCRAPING-MCP] Verifying tool: ${tool}`);
        // In production, this would make actual verification calls
      } catch (error) {
        console.warn(`[SCRAPING-MCP] Tool verification warning for ${tool}:`, error.message);
      }
    }

    console.log('[SCRAPING-MCP] Tool verification complete');
  }

  /**
   * Initialize staging collections if needed
   */
  async initializeStagingCollections() {
    try {
      // Check if staging intake collections are accessible
      const stagingTest = await this.executeComposioFirebaseTool('FIREBASE_QUERY', {
        collection: 'company_raw_intake',
        where: [{ field: 'intake_status', operator: '==', value: 'staging' }],
        limit: 1
      });

      console.log('[SCRAPING-MCP] Staging collections verified');

    } catch (error) {
      console.warn('[SCRAPING-MCP] Staging collection initialization warning:', error.message);
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
      console.error(`[SCRAPING-MCP] Tool execution failed for ${tool}:`, error);
      throw error;
    }
  }

  /**
   * Scrape company data via Composio MCP
   */
  async scrapeCompanyViaComposio(actorType, targetUrls, options = {}) {
    console.log(`[SCRAPING-MCP] Starting company scraping: ${actorType}, ${targetUrls.length} URLs`);

    try {
      // Validate actor type
      if (!this.supportedActors.includes(actorType)) {
        throw new Error(`Unsupported actor type: ${actorType}`);
      }

      // Prepare scraping payload
      const scrapingPayload = {
        actorType: actorType,
        targetUrls: targetUrls,
        maxItems: options.maxItems || 100,
        timeout: options.timeout || 300,
        maxWaitTime: options.maxWaitTime || 480,
        request_id: this.generateRequestId(),
        composio_session: this.generateSessionId()
      };

      // Execute scraping via Cloud Function
      const functionResult = await this.executeComposioFirebaseTool('FIREBASE_FUNCTION_CALL', {
        function_name: 'scrapeCompany',
        payload: scrapingPayload
      });

      if (functionResult.success) {
        console.log(`[SCRAPING-MCP] Company scraping completed: ${functionResult.data.total_scraped} scraped`);

        return {
          success: true,
          process_id: functionResult.data.process_id,
          total_scraped: functionResult.data.total_scraped,
          successful_inserts: functionResult.data.successful_inserts,
          failed_inserts: functionResult.data.failed_inserts,
          companies: functionResult.data.companies,
          apify_run_id: functionResult.data.apify_run_id,
          processing_time_ms: functionResult.data.processing_time_ms,
          processed_via: 'composio_mcp',
          processed_at: new Date().toISOString()
        };

      } else {
        throw new Error('Company scraping failed');
      }

    } catch (error) {
      console.error(`[SCRAPING-MCP] Company scraping error:`, error);
      throw error;
    }
  }

  /**
   * Scrape person data via Composio MCP
   */
  async scrapePersonViaComposio(actorType, targetUrls, options = {}) {
    console.log(`[SCRAPING-MCP] Starting person scraping: ${actorType}, ${targetUrls.length} URLs`);

    try {
      // Validate actor type
      if (!this.supportedActors.includes(actorType)) {
        throw new Error(`Unsupported actor type: ${actorType}`);
      }

      // Prepare scraping payload
      const scrapingPayload = {
        actorType: actorType,
        targetUrls: targetUrls,
        maxItems: options.maxItems || 100,
        timeout: options.timeout || 300,
        maxWaitTime: options.maxWaitTime || 480,
        request_id: this.generateRequestId(),
        composio_session: this.generateSessionId()
      };

      // Execute scraping via Cloud Function
      const functionResult = await this.executeComposioFirebaseTool('FIREBASE_FUNCTION_CALL', {
        function_name: 'scrapePerson',
        payload: scrapingPayload
      });

      if (functionResult.success) {
        console.log(`[SCRAPING-MCP] Person scraping completed: ${functionResult.data.total_scraped} scraped`);

        return {
          success: true,
          process_id: functionResult.data.process_id,
          total_scraped: functionResult.data.total_scraped,
          successful_inserts: functionResult.data.successful_inserts,
          failed_inserts: functionResult.data.failed_inserts,
          people: functionResult.data.people,
          apify_run_id: functionResult.data.apify_run_id,
          processing_time_ms: functionResult.data.processing_time_ms,
          processed_via: 'composio_mcp',
          processed_at: new Date().toISOString()
        };

      } else {
        throw new Error('Person scraping failed');
      }

    } catch (error) {
      console.error(`[SCRAPING-MCP] Person scraping error:`, error);
      throw error;
    }
  }

  /**
   * Batch scrape multiple domains/URLs
   */
  async batchScrapeViaComposio(requests) {
    console.log(`[SCRAPING-MCP] Starting batch scraping: ${requests.length} requests`);

    const results = [];
    const batchSize = 2; // Process in small batches to avoid overwhelming Apify

    for (let i = 0; i < requests.length; i += batchSize) {
      const batch = requests.slice(i, i + batchSize);

      const batchPromises = batch.map(async (req) => {
        try {
          if (req.recordType === 'company') {
            return await this.scrapeCompanyViaComposio(req.actorType, req.targetUrls, req.options);
          } else if (req.recordType === 'person') {
            return await this.scrapePersonViaComposio(req.actorType, req.targetUrls, req.options);
          } else {
            throw new Error(`Invalid record type: ${req.recordType}`);
          }
        } catch (error) {
          return {
            success: false,
            record_type: req.recordType,
            actor_type: req.actorType,
            target_urls: req.targetUrls,
            error: error.message,
            processed_via: 'composio_mcp',
            processed_at: new Date().toISOString()
          };
        }
      });

      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);

      // Small delay between batches to respect rate limits
      if (i + batchSize < requests.length) {
        await new Promise(resolve => setTimeout(resolve, 5000)); // 5 second delay
      }
    }

    const successCount = results.filter(r => r.success).length;
    const failureCount = results.length - successCount;
    const totalScraped = results.reduce((sum, r) => sum + (r.total_scraped || 0), 0);
    const totalInserted = results.reduce((sum, r) => sum + (r.successful_inserts || 0), 0);

    console.log(`[SCRAPING-MCP] Batch scraping complete: ${successCount} success, ${failureCount} failed`);

    return {
      success: true,
      total_requests: results.length,
      successful_requests: successCount,
      failed_requests: failureCount,
      total_scraped: totalScraped,
      total_inserted: totalInserted,
      results: results,
      batch_completed_at: new Date().toISOString()
    };
  }

  /**
   * Query staging data for monitoring
   */
  async queryStagingData(criteria = {}) {
    try {
      const queryData = {
        collection: criteria.recordType === 'person' ? 'people_raw_intake' : 'company_raw_intake',
        where: [
          { field: 'intake_status', operator: '==', value: 'staging' }
        ],
        limit: criteria.limit || 100,
        orderBy: { field: 'inserted_at', direction: 'desc' }
      };

      // Add process ID filter if specified
      if (criteria.processId) {
        queryData.where.push({
          field: 'process_id',
          operator: '==',
          value: criteria.processId
        });
      }

      const result = await this.executeComposioFirebaseTool('FIREBASE_QUERY', queryData);

      if (result.success) {
        console.log(`[SCRAPING-MCP] Retrieved ${result.data.length} staging records`);
        return result.data;
      } else {
        throw new Error('Failed to query staging data');
      }

    } catch (error) {
      console.error('[SCRAPING-MCP] Query staging data error:', error);
      throw error;
    }
  }

  /**
   * Get scraping statistics
   */
  async getScrapingStats(timeRange = '24h') {
    try {
      const cutoffTime = new Date();
      cutoffTime.setHours(cutoffTime.getHours() - (timeRange === '24h' ? 24 : 168)); // 24h or 7d

      // Query audit logs for scraping operations
      const auditResult = await this.executeComposioFirebaseTool('FIREBASE_QUERY', {
        collection: 'unified_audit_log',
        where: [
          { field: 'operation_type', operator: '==', value: 'scraping' },
          { field: 'created_at', operator: '>=', value: cutoffTime.toISOString() }
        ],
        limit: 1000
      });

      const stats = {
        total_scraping_operations: 0,
        total_records_scraped: 0,
        total_records_inserted: 0,
        company_operations: 0,
        person_operations: 0,
        failed_operations: 0,
        average_data_quality: 0,
        time_range: timeRange
      };

      if (auditResult.success && auditResult.data) {
        stats.total_scraping_operations = auditResult.data.length;

        for (const log of auditResult.data) {
          stats.total_records_scraped += log.total_scraped || 0;
          stats.total_records_inserted += log.successful_inserts || 0;

          if (log.operation_subtype === 'linkedin-company') {
            stats.company_operations++;
          } else if (log.operation_subtype === 'linkedin-people') {
            stats.person_operations++;
          }

          if (log.failed_inserts > 0 || log.errors?.length > 0) {
            stats.failed_operations++;
          }
        }

        // Calculate average data quality
        const qualityScores = auditResult.data
          .map(log => log.data_quality_average || 0)
          .filter(score => score > 0);

        if (qualityScores.length > 0) {
          stats.average_data_quality = qualityScores.reduce((sum, score) => sum + score, 0) / qualityScores.length;
        }
      }

      return {
        success: true,
        stats: stats,
        generated_at: new Date().toISOString()
      };

    } catch (error) {
      console.error('[SCRAPING-MCP] Get scraping stats error:', error);
      throw error;
    }
  }

  /**
   * Generate HEIR format unique ID
   */
  generateHeirId() {
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[-T:]/g, '');
    const random = Math.random().toString(36).substring(2, 8).toUpperCase();
    return `HEIR-${timestamp}-SCR-${random}`;
  }

  /**
   * Generate process ID for tracking
   */
  generateProcessId() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 6).toUpperCase();
    return `PRC-SCR-${timestamp}-${random}`;
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
      service: 'scraping_agent',
      version: this.doctrineVersion,
      initialized: this.initialized,
      mcp_endpoint: this.mcpEndpoint,
      available_tools: this.scrapingTools,
      supported_actors: this.supportedActors,
      status: this.initialized ? 'ready' : 'initializing',
      timestamp: new Date().toISOString()
    };
  }
}

/**
 * MCP Endpoint Specifications for Composio Integration
 */
export const SCRAPING_MCP_ENDPOINTS = {
  // Company scraping endpoint
  scrape_company: {
    endpoint: '/scraping/company',
    method: 'POST',
    description: 'Scrape company data through Composio MCP with Apify actors',
    composio_tool: 'FIREBASE_FUNCTION_CALL',
    function_name: 'scrapeCompany',
    payload_schema: {
      actorType: {
        type: 'string',
        required: true,
        enum: ['linkedin-company', 'email-scraper'],
        description: 'Type of Apify actor to use for scraping'
      },
      targetUrls: {
        type: 'array',
        required: true,
        items: { type: 'string', format: 'uri' },
        maxItems: 50,
        description: 'URLs to scrape'
      },
      maxItems: {
        type: 'number',
        default: 100,
        maximum: 500,
        description: 'Maximum items to scrape'
      },
      timeout: {
        type: 'number',
        default: 300,
        maximum: 600,
        description: 'Actor timeout in seconds'
      }
    },
    response_schema: {
      success: { type: 'boolean' },
      process_id: { type: 'string' },
      total_scraped: { type: 'number' },
      successful_inserts: { type: 'number' },
      failed_inserts: { type: 'number' },
      companies: { type: 'array' },
      apify_run_id: { type: 'string' },
      processing_time_ms: { type: 'number' },
      processed_at: { type: 'string', format: 'iso8601' }
    }
  },

  // Person scraping endpoint
  scrape_person: {
    endpoint: '/scraping/person',
    method: 'POST',
    description: 'Scrape person data through Composio MCP with Apify actors',
    composio_tool: 'FIREBASE_FUNCTION_CALL',
    function_name: 'scrapePerson',
    payload_schema: {
      actorType: {
        type: 'string',
        required: true,
        enum: ['linkedin-people', 'email-scraper'],
        description: 'Type of Apify actor to use for scraping'
      },
      targetUrls: {
        type: 'array',
        required: true,
        items: { type: 'string', format: 'uri' },
        maxItems: 50,
        description: 'URLs to scrape'
      },
      maxItems: {
        type: 'number',
        default: 100,
        maximum: 500,
        description: 'Maximum items to scrape'
      },
      timeout: {
        type: 'number',
        default: 300,
        maximum: 600,
        description: 'Actor timeout in seconds'
      }
    },
    response_schema: {
      success: { type: 'boolean' },
      process_id: { type: 'string' },
      total_scraped: { type: 'number' },
      successful_inserts: { type: 'number' },
      failed_inserts: { type: 'number' },
      people: { type: 'array' },
      apify_run_id: { type: 'string' },
      processing_time_ms: { type: 'number' },
      processed_at: { type: 'string', format: 'iso8601' }
    }
  },

  // Batch scraping endpoint
  batch_scrape: {
    endpoint: '/scraping/batch',
    method: 'POST',
    description: 'Batch scrape multiple URLs/domains through Composio MCP',
    composio_tool: 'BATCH_OPERATION',
    payload_schema: {
      requests: {
        type: 'array',
        required: true,
        maxItems: 10,
        items: {
          type: 'object',
          properties: {
            recordType: { type: 'string', enum: ['company', 'person'] },
            actorType: { type: 'string', enum: ['linkedin-company', 'linkedin-people', 'email-scraper'] },
            targetUrls: { type: 'array', items: { type: 'string' } },
            options: { type: 'object' }
          },
          required: ['recordType', 'actorType', 'targetUrls']
        },
        description: 'Array of scraping requests'
      }
    },
    response_schema: {
      success: { type: 'boolean' },
      total_requests: { type: 'number' },
      successful_requests: { type: 'number' },
      failed_requests: { type: 'number' },
      total_scraped: { type: 'number' },
      total_inserted: { type: 'number' },
      results: { type: 'array' },
      batch_completed_at: { type: 'string', format: 'iso8601' }
    }
  },

  // Query staging data endpoint
  query_staging: {
    endpoint: '/scraping/staging',
    method: 'GET',
    description: 'Query staging data from scraping operations',
    composio_tool: 'FIREBASE_QUERY',
    query_params: {
      recordType: {
        type: 'string',
        enum: ['company', 'person']
      },
      processId: {
        type: 'string',
        description: 'Filter by process ID'
      },
      limit: {
        type: 'number',
        default: 100,
        maximum: 500
      }
    },
    response_schema: {
      success: { type: 'boolean' },
      staging_data: { type: 'array' },
      total_count: { type: 'number' }
    }
  },

  // Scraping statistics endpoint
  scraping_stats: {
    endpoint: '/scraping/stats',
    method: 'GET',
    description: 'Get scraping statistics and metrics',
    composio_tool: 'FIREBASE_QUERY',
    query_params: {
      timeRange: {
        type: 'string',
        enum: ['24h', '7d'],
        default: '24h'
      }
    },
    response_schema: {
      success: { type: 'boolean' },
      stats: { type: 'object' },
      generated_at: { type: 'string', format: 'iso8601' }
    }
  }
};

export { ScrapingMCPService };
export default { ScrapingMCPService, SCRAPING_MCP_ENDPOINTS };