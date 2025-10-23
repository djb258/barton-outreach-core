/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/archive
Barton ID: 06.01.05
Unique ID: CTB-301FCC10
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';
import { z } from 'zod';
import { createDefaultConnection } from '../../packages/mcp-clients/dist/factory/client-factory.js';
import { PLEOrchestrator } from '../../packages/mcp-clients/dist/clients/ple-orchestrator.js';
import { ApolloIngestClient } from '../../packages/mcp-clients/dist/clients/apollo-ingest-client.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Default connection through Composio MCP - ONLY connection layer
console.log('🎯 API Server: Using Composio MCP as ONLY connection layer');
console.log('   • Database operations: Composio MCP → Neon');
console.log('   • All external services: Composio MCP');
console.log('   • No direct PostgreSQL fallbacks');

const composio = createDefaultConnection({
  timeout: 30000,
  retries: 3
});

// Initialize PLE Orchestrator for complete pipeline
const pleOrchestrator = new PLEOrchestrator({
  batchSize: parseInt(process.env.PLE_BATCH_SIZE) || 50,
  maxRetries: parseInt(process.env.PLE_MAX_RETRIES) || 3,
  timeout: 300000
});

// Initialize Apollo Ingest Client for CSV processing (MCP only)
const apolloIngest = new ApolloIngestClient({
  timeout: 30000,
  retries: 3
});

// Database query function using Composio MCP ONLY
async function executeSecureQuery(query, params = []) {
  try {
    const result = await composio.executeAction('neon_query_secure', {
      query,
      params,
      schema_mode: 'company'
    });
    
    if (result.success) {
      return result.data;
    } else {
      throw new Error(result.error || 'Database query failed');
    }
  } catch (error) {
    console.error('Secure query error:', error);
    throw error;
  }
}

// Database function call using Composio MCP ONLY
async function callDatabaseFunction(functionName, parameters) {
  try {
    console.log('🔌 Executing MCP function call...');
    const mcpResult = await composio.executeAction('neon_function_call', {
      function_name: functionName,
      parameters: parameters
    });
    
    if (mcpResult.success) {
      console.log('✅ MCP function call succeeded');
      return mcpResult;
    } else {
      throw new Error(mcpResult.error || 'MCP function call failed');
    }
  } catch (error) {
    console.error('❌ MCP function call failed:', error.message);
    throw error;
  }
}

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:5173', 'http://localhost:3001'],
  credentials: true
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: { error: 'Too many requests, please try again later.' }
});
app.use('/api/', limiter);

// Logging
app.use(morgan('combined'));

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Validation schemas
const IngestJsonSchema = z.object({
  rows: z.array(z.record(z.any())),
  metadata: z.object({
    source: z.string(),
    timestamp: z.string(),
    count: z.number()
  }).optional()
});

const IngestCsvSchema = z.object({
  csv: z.string(),
  metadata: z.object({
    source: z.string(),
    timestamp: z.string()
  }).optional()
});

const ApolloCsvSchema = z.object({
  csv: z.string().min(1, "CSV content cannot be empty"),
  config: z.object({
    source: z.string().default('api_upload'),
    blueprintId: z.string().default('apollo_csv_import'),
    createdBy: z.string().default('api_user'),
    dataQualityThreshold: z.number().min(0).max(100).default(50)
  }).optional()
});

const PromoteContactsSchema = z.object({
  filter: z.record(z.any()).optional()
});

const ContactsQuerySchema = z.object({
  limit: z.coerce.number().default(50),
  offset: z.coerce.number().default(0),
  search: z.string().optional(),
  source: z.string().optional()
}).refine(data => data.limit <= 1000, { message: "Limit cannot exceed 1000" });

// Health check endpoint - using Composio MCP
app.get('/health', async (req, res) => {
  try {
    // Check Composio MCP connection and database through MCP
    const healthResult = await composio.executeAction('neon_health_check', {
      schema_mode: 'company'
    });
    
    if (healthResult.success) {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: process.env.npm_package_version || '1.0.0',
        database: 'connected via Composio MCP',
        connection_layer: 'Composio MCP',
        schema_mode: 'company'
      });
    } else {
      throw new Error(healthResult.error);
    }
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: 'Composio MCP connection failed',
      connection_layer: 'Composio MCP',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// POST /ingest/json - Secure ingestion through Composio MCP
app.post('/ingest/json', async (req, res) => {
  try {
    const { rows, metadata } = IngestJsonSchema.parse(req.body);
    
    if (!rows || rows.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No data rows provided'
      });
    }

    // Generate batch ID
    const batch_id = `api_batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Use Composio MCP secure ingestion
    const ingestResult = await composio.executeNeonIngest(
      rows,
      metadata?.source || 'api',
      batch_id
    );

    if (ingestResult.success) {
      res.json({
        success: true,
        count: rows.length,
        batch_id,
        message: `Successfully ingested ${rows.length} rows via Composio MCP`,
        connection_layer: 'Composio MCP'
      });
    } else {
      throw new Error(ingestResult.error);
    }

  } catch (error) {
    console.error('Ingest JSON error:', error);
    
    if (error instanceof z.ZodError) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: error.errors
      });
    }

    res.status(500).json({
      success: false,
      error: 'Secure ingestion failed',
      connection_layer: 'Composio MCP',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// POST /insert - Compatible with ingest-companies-people app
app.post('/insert', async (req, res) => {
  try {
    const { records, target_table } = req.body;
    
    if (!records || !Array.isArray(records) || records.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No records provided or invalid format'
      });
    }

    // Use database function for marketing.company_raw_intake with MCP/PostgreSQL fallback
    if (target_table === 'marketing.company_raw_intake') {
      try {
        console.log('🔌 Using Database Function Insert for intake.company_raw_intake');
        console.log(`📊 Records to insert: ${records.length}`);
        
        const batch_id = `api_batch_${Date.now()}`;
        // Try standard Composio PostgreSQL actions first
        let result;
        try {
          console.log('🔌 Attempting standard Composio PostgreSQL action...');
          const composioResult = await composio.executeAction('postgresql_execute_query', {
            query: 'SELECT * FROM intake.f_ingest_company_csv($1, $2)',
            parameters: [JSON.stringify(records), batch_id],
            connection_id: process.env.COMPOSIO_POSTGRES_CONNECTION_ID || 'default'
          });
          
          if (composioResult.success) {
            console.log('✅ Composio PostgreSQL action succeeded');
            result = {
              success: true,
              data: composioResult.data.rows?.[0] || { inserted_count: records.length, batch_id, message: 'Inserted via Composio' },
              via_mcp: true
            };
          } else {
            throw new Error(composioResult.error || 'Composio PostgreSQL action failed');
          }
        } catch (composioError) {
          console.log('❌ Composio failed, using direct function call:', composioError.message);
          result = await callDatabaseFunction('intake.f_ingest_company_csv', [
            JSON.stringify(records),
            batch_id
          ]);
        }
        
        if (result.success) {
          return res.json({
            success: true,
            inserted: result.data.inserted_count || records.length,
            batch_id: result.data.batch_id || batch_id,
            message: result.data.message || 'Successfully inserted company records',
            connection_type: result.via_mcp ? 'MCP_DIRECT' : 'POSTGRES_DIRECT'
          });
        } else {
          throw new Error(result.error || 'Database function call failed');
        }
        
      } catch (error) {
        console.error('❌ Database Insert Error:', error);
        return res.status(500).json({
          success: false,
          error: 'Failed to ingest company data',
          connection_type: 'DATABASE_FUNCTION',
          details: process.env.NODE_ENV === 'development' ? error.message : undefined
        });
      }
    }
    
    // Fallback to original ingestion method for other tables
    const batch_id = `api_batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const ingestResult = await composio.executeNeonIngest(
      records,
      'ingest_app',
      batch_id
    );

    if (ingestResult.success) {
      res.json({
        success: true,
        inserted: records.length,
        batch_id,
        message: `Successfully ingested ${records.length} records`
      });
    } else {
      throw new Error(ingestResult.error);
    }

  } catch (error) {
    console.error('Insert error:', error);
    res.status(500).json({
      success: false,
      error: 'Insert operation failed',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// POST /ingest/csv - Ingest CSV data
app.post('/ingest/csv', async (req, res) => {
  try {
    const { csv, metadata } = IngestCsvSchema.parse(req.body);
    
    if (!csv || csv.trim().length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No CSV data provided'
      });
    }

    // Parse CSV data
    const lines = csv.trim().split('\\n');
    if (lines.length < 2) {
      return res.status(400).json({
        success: false,
        error: 'CSV must contain at least a header and one data row'
      });
    }

    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
    const rows = [];

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''));
      if (values.length === headers.length) {
        const row = {};
        headers.forEach((header, index) => {
          row[header] = values[index];
        });
        rows.push(row);
      }
    }

    if (rows.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No valid data rows found in CSV'
      });
    }

    // Generate batch ID
    const batch_id = `csv_batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Insert rows into staged_data table
    const insertPromises = rows.map(async (row) => {
      return sql`
        INSERT INTO staged_data (
          batch_id,
          source,
          raw_data,
          created_at
        ) VALUES (
          ${batch_id},
          ${metadata?.source || 'csv'},
          ${JSON.stringify(row)},
          NOW()
        )
      `;
    });

    await Promise.all(insertPromises);

    res.json({
      success: true,
      count: rows.length,
      batch_id,
      message: `Successfully ingested ${rows.length} rows from CSV`
    });

  } catch (error) {
    console.error('Ingest CSV error:', error);
    
    if (error instanceof z.ZodError) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: error.errors
      });
    }

    res.status(500).json({
      success: false,
      error: 'Internal server error',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// POST /promote/contacts - Secure promotion through Composio MCP
app.post('/promote/contacts', async (req, res) => {
  try {
    const { filter } = PromoteContactsSchema.parse(req.body);
    
    // Use Composio MCP secure promotion
    const promoteResult = await composio.executeNeonPromote(
      filter ? filter.load_ids : null // Promote specific IDs or all pending
    );

    if (promoteResult.success) {
      res.json({
        success: true,
        promoted_count: promoteResult.data?.promoted_count || 0,
        updated_count: promoteResult.data?.updated_count || 0,
        failed_count: promoteResult.data?.failed_count || 0,
        message: promoteResult.data?.message || 'Promotion completed via Composio MCP',
        connection_layer: 'Composio MCP',
        schema_mode: 'company'
      });
    } else {
      throw new Error(promoteResult.error);
    }

  } catch (error) {
    console.error('Promote contacts error:', error);
    
    if (error instanceof z.ZodError) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: error.errors
      });
    }

    res.status(500).json({
      success: false,
      error: 'Secure promotion failed',
      connection_layer: 'Composio MCP',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// GET /contacts - Retrieve contacts from vault
app.get('/contacts', async (req, res) => {
  try {
    const { limit, offset, search, source } = ContactsQuerySchema.parse(req.query);
    
    let whereConditions = [];
    let params = [];
    
    if (search) {
      whereConditions.push(`(
        name ILIKE $${params.length + 1} OR 
        email ILIKE $${params.length + 1} OR 
        company ILIKE $${params.length + 1}
      )`);
      params.push(`%${search}%`);
    }
    
    if (source) {
      whereConditions.push(`source = $${params.length + 1}`);
      params.push(source);
    }
    
    const whereClause = whereConditions.length > 0 ? 
      `WHERE ${whereConditions.join(' AND ')}` : '';
    
    // Get total count
    const countResult = await sql`
      SELECT COUNT(*) as total FROM contacts
      ${whereClause ? sql.raw(whereClause, params) : sql``}
    `;
    const total = parseInt(countResult[0].total);
    
    // Get contacts
    const contacts = await sql`
      SELECT 
        id,
        email,
        name,
        phone,
        company,
        title,
        source,
        tags,
        custom_fields,
        created_at,
        updated_at
      FROM contacts
      ${whereClause ? sql.raw(whereClause, params) : sql``}
      ORDER BY updated_at DESC
      LIMIT ${limit}
      OFFSET ${offset}
    `;

    res.json({
      contacts,
      total,
      limit,
      offset,
      has_more: offset + contacts.length < total
    });

  } catch (error) {
    console.error('Get contacts error:', error);
    
    if (error instanceof z.ZodError) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: error.errors
      });
    }

    res.status(500).json({
      success: false,
      error: 'Internal server error',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Import and setup outreach endpoints
import { setupOutreachEndpoints } from './outreach-endpoints.js';
setupOutreachEndpoints(app, executeSecureQuery);

// Import and setup MCP render endpoints (bypasses CORS)
import { setupRenderMCPEndpoints } from './mcp-render-endpoint.js';
setupRenderMCPEndpoints(app);

// Default route
app.get('/', (req, res) => {
  res.json({
    name: 'Barton Outreach Core API',
    version: '1.0.0',
    status: 'running',
    endpoints: {
      health: 'GET /health',
      ingest_json: 'POST /ingest/json',
      ingest_csv: 'POST /ingest/csv',
      promote_contacts: 'POST /promote/contacts',
      get_contacts: 'GET /contacts',
      // Outreach endpoints
      outreach_companies: 'GET /api/outreach/companies',
      outreach_contacts: 'GET /api/outreach/contacts',
      outreach_queues: 'GET /api/outreach/queues/{type}',
      process_queue: 'POST /api/outreach/queues/{type}/process'
    }
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found'
  });
});

// ===========================================
// Apollo CSV Ingestion Endpoints (Routes to marketing_apollo_raw)
// ===========================================

// POST /apollo/csv/validate - Validate CSV format before ingestion
app.post('/apollo/csv/validate', async (req, res) => {
  try {
    const { csv } = ApolloCsvSchema.parse(req.body);
    
    console.log('🔍 Validating Apollo CSV format...');
    const validation = await apolloIngest.validateCsvFormat(csv);
    
    if (validation.success) {
      res.json({
        success: true,
        message: 'CSV validation completed',
        validation: validation.data
      });
    } else {
      res.status(400).json({
        success: false,
        error: 'CSV validation failed',
        details: validation.error
      });
    }
  } catch (error) {
    console.error('❌ CSV validation error:', error);
    
    if (error instanceof z.ZodError) {
      return res.status(400).json({
        success: false,
        error: 'Invalid request format',
        details: error.errors
      });
    }

    res.status(500).json({
      success: false,
      error: 'CSV validation failed',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// POST /apollo/csv/ingest - Ingest CSV directly to marketing_apollo_raw
app.post('/apollo/csv/ingest', async (req, res) => {
  try {
    const { csv, config = {} } = ApolloCsvSchema.parse(req.body);
    
    console.log('🚀 Starting Apollo CSV ingestion to marketing_apollo_raw...');
    const result = await apolloIngest.ingestCsvToApollo(csv, {
      batchId: `apollo_${Date.now()}_${Math.random().toString(36).substr(2, 8)}`,
      source: config.source || 'api_upload',
      blueprintId: config.blueprintId || 'apollo_csv_import',
      createdBy: config.createdBy || 'api_user',
      dataQualityThreshold: config.dataQualityThreshold || 50
    });
    
    if (result.success) {
      console.log(`✅ Apollo CSV ingestion completed: ${result.data.inserted_count} records`);
      res.json({
        success: true,
        message: 'Apollo CSV ingested successfully',
        result: result.data,
        metadata: result.metadata,
        target_table: 'marketing.marketing_apollo_raw'
      });
    } else {
      console.error('❌ Apollo CSV ingestion failed:', result.error);
      res.status(500).json({
        success: false,
        error: result.error,
        result: result.data,
        target_table: 'marketing.marketing_apollo_raw'
      });
    }
  } catch (error) {
    console.error('❌ Apollo CSV endpoint error:', error);
    
    if (error instanceof z.ZodError) {
      return res.status(400).json({
        success: false,
        error: 'Invalid request format',
        details: error.errors
      });
    }

    res.status(500).json({
      success: false,
      error: 'Apollo CSV ingestion failed',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// GET /apollo/batch/:batchId/status - Get ingestion batch status
app.get('/apollo/batch/:batchId/status', async (req, res) => {
  try {
    const { batchId } = req.params;
    
    console.log(`📊 Getting Apollo batch status: ${batchId}`);
    const result = await apolloIngest.getIngestionStatus(batchId);
    
    if (result.success) {
      res.json({
        success: true,
        batch_id: batchId,
        status: result.data
      });
    } else {
      res.status(404).json({
        success: false,
        error: 'Batch not found or query failed',
        batch_id: batchId
      });
    }
  } catch (error) {
    console.error('❌ Batch status error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get batch status',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// GET /apollo/batches - List recent ingestion batches
app.get('/apollo/batches', async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 10;
    
    console.log(`📋 Listing Apollo batches (limit: ${limit})`);
    const result = await apolloIngest.listRecentBatches(limit);
    
    if (result.success) {
      res.json({
        success: true,
        batches: result.data,
        limit
      });
    } else {
      res.status(500).json({
        success: false,
        error: 'Failed to list batches'
      });
    }
  } catch (error) {
    console.error('❌ List batches error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to list batches',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// ===========================================
// Complete Pipeline Endpoints (Ingestor → Neon → Apify → PLE → Bit)
// ===========================================

// Execute complete pipeline
app.post('/pipeline/execute', async (req, res) => {
  console.log('🚀 Pipeline execution requested');
  
  try {
    const pipelineConfigSchema = z.object({
      data: z.array(z.object({
        email: z.string().email().optional(),
        name: z.string().optional(),
        company: z.string().optional(),
        website: z.string().url().optional()
      })),
      jobConfig: z.object({
        jobId: z.string().default(() => `pipeline_${Date.now()}`),
        source: z.enum(['csv', 'api', 'manual']).default('api'),
        enableScraping: z.boolean().default(true),
        enablePromotion: z.boolean().default(true),
        enableBitSync: z.boolean().default(false),
        notificationWebhook: z.string().url().optional()
      })
    });

    const { data, jobConfig } = pipelineConfigSchema.parse(req.body);

    console.log(`📊 Pipeline Job: ${jobConfig.jobId}`);
    console.log(`📥 Input Records: ${data.length}`);
    console.log(`🔧 Config: Scraping=${jobConfig.enableScraping}, Promotion=${jobConfig.enablePromotion}, BitSync=${jobConfig.enableBitSync}`);

    // Execute the complete pipeline
    const result = await pleOrchestrator.executePipeline(data, jobConfig);

    if (result.success) {
      console.log('✅ Pipeline execution completed successfully');
      res.json({
        success: true,
        message: 'Pipeline executed successfully',
        result: result.data,
        jobId: jobConfig.jobId
      });
    } else {
      console.error('❌ Pipeline execution failed:', result.error);
      res.status(500).json({
        success: false,
        error: result.error,
        result: result.data,
        jobId: jobConfig.jobId
      });
    }

  } catch (error) {
    console.error('❌ Pipeline endpoint error:', error);
    
    if (error.name === 'ZodError') {
      return res.status(400).json({
        success: false,
        error: 'Invalid request format',
        details: error.errors
      });
    }

    res.status(500).json({
      success: false,
      error: 'Pipeline execution failed',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Pipeline health check
app.get('/pipeline/health', async (req, res) => {
  try {
    const healthResult = await pleOrchestrator.healthCheck();
    
    res.json({
      success: true,
      health: healthResult.data,
      metadata: healthResult.metadata,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Pipeline health check failed:', error);
    res.status(500).json({
      success: false,
      error: 'Health check failed',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Get pipeline status
app.get('/pipeline/status/:jobId', async (req, res) => {
  try {
    const { jobId } = req.params;
    
    // Query job status from database
    const statusQuery = `
      SELECT 
        batch_id,
        COUNT(*) as total_records,
        COUNT(*) FILTER (WHERE status = 'promoted') as promoted_count,
        COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
        COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
        MIN(created_at) as started_at,
        MAX(promoted_at) as completed_at
      FROM intake.raw_loads 
      WHERE batch_id = $1
      GROUP BY batch_id
    `;
    
    const result = await executeSecureQuery(statusQuery, [jobId]);
    
    if (result.rows && result.rows.length > 0) {
      const status = result.rows[0];
      res.json({
        success: true,
        jobId,
        status: {
          total: parseInt(status.total_records),
          promoted: parseInt(status.promoted_count),
          pending: parseInt(status.pending_count),
          failed: parseInt(status.failed_count),
          startedAt: status.started_at,
          completedAt: status.completed_at,
          isComplete: parseInt(status.pending_count) === 0
        }
      });
    } else {
      res.status(404).json({
        success: false,
        error: 'Job not found',
        jobId
      });
    }

  } catch (error) {
    console.error('❌ Pipeline status check failed:', error);
    res.status(500).json({
      success: false,
      error: 'Status check failed',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Global error handler
app.use((error, req, res, next) => {
  console.error('Global error handler:', error);
  
  res.status(500).json({
    success: false,
    error: 'Internal server error',
    details: process.env.NODE_ENV === 'development' ? error.message : undefined
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Barton Outreach Core API running on port ${PORT}`);
  console.log(`🏥 Health check: http://localhost:${PORT}/health`);
  console.log(`📚 API docs: http://localhost:${PORT}/`);
});

export default app;