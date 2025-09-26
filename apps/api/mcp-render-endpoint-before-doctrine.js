// MCP Server integration for Render deployment
// This bypasses CORS issues by using Composio MCP directly

import { createDefaultConnection } from '../../packages/mcp-clients/dist/factory/client-factory.js';
import { Client } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

// Create MCP connection specifically for render operations
const renderMCP = createDefaultConnection({
  timeout: 45000, // Longer timeout for render operations
  retries: 3,
  service: 'render_deployment'
});

// Direct PostgreSQL client fallback for MCP endpoints
const DATABASE_URL = process.env.NEON_DATABASE_URL || process.env.DATABASE_URL;
const mcpPgClient = new Client({
  connectionString: DATABASE_URL,
  ssl: DATABASE_URL?.includes('neon.tech') ? { rejectUnauthorized: false } : false
});

// Connect to PostgreSQL directly
mcpPgClient.connect().catch(console.error);

// MCP-based render endpoints that bypass CORS
export function setupRenderMCPEndpoints(app) {
  
  // POST /mcp/insert - Direct MCP insertion bypassing CORS
  app.post('/mcp/insert', async (req, res) => {
    try {
      const { records, target_table, batch_id } = req.body;
      
      if (!records || !Array.isArray(records) || records.length === 0) {
        return res.status(400).json({
          success: false,
          error: 'No records provided or invalid format'
        });
      }

      console.log('🔌 MCP Direct Insert:', {
        recordCount: records.length,
        targetTable: target_table,
        batchId: batch_id
      });

      // Try MCP first, fallback to direct PostgreSQL
      let mcpResult;
      try {
        console.log('🔌 Attempting MCP insertion...');
        mcpResult = await renderMCP.executeAction('neon_function_call', {
          function_name: 'intake.f_ingest_company_csv',
          parameters: [
            JSON.stringify(records),
            batch_id || `mcp_batch_${Date.now()}`
          ]
        });
        
        if (mcpResult.success) {
          console.log('✅ MCP insertion succeeded');
          return res.json({
            success: true,
            inserted: mcpResult.data.inserted_count || records.length,
            batch_id: mcpResult.data.batch_id,
            message: mcpResult.data.message || 'Successfully inserted via MCP',
            connection_type: 'MCP_DIRECT'
          });
        } else {
          throw new Error(mcpResult.error || 'MCP insertion failed');
        }
      } catch (mcpError) {
        console.log('❌ MCP failed, falling back to direct PostgreSQL:', mcpError.message);
        
        // Fallback to direct PostgreSQL
        try {
          const finalBatchId = batch_id || `mcp_batch_${Date.now()}`;
          const result = await mcpPgClient.query(`SELECT * FROM intake.f_ingest_company_csv($1, $2)`, [
            JSON.stringify(records),
            finalBatchId
          ]);
          
          console.log('✅ Direct PostgreSQL insertion succeeded');
          res.json({
            success: true,
            inserted: result.rows[0].inserted_count || records.length,
            batch_id: result.rows[0].batch_id || finalBatchId,
            message: result.rows[0].message || 'Successfully inserted via direct PostgreSQL',
            connection_type: 'POSTGRES_DIRECT'
          });
        } catch (pgError) {
          console.error('❌ Direct PostgreSQL also failed:', pgError.message);
          throw pgError;
        }
      }

    } catch (error) {
      console.error('❌ MCP Insert Error:', error);
      res.status(500).json({
        success: false,
        error: 'MCP insertion failed',
        connection_type: 'MCP_DIRECT',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    }
  });

  // POST /mcp/bulk-company - Bulk company insertion via MCP
  app.post('/mcp/bulk-company', async (req, res) => {
    try {
      const { companies, batch_size = 100 } = req.body;
      
      if (!companies || !Array.isArray(companies)) {
        return res.status(400).json({
          success: false,
          error: 'Companies array required'
        });
      }

      console.log(`🔄 MCP Bulk Company Insert: ${companies.length} companies`);

      // Process in batches to avoid timeouts
      const batches = [];
      for (let i = 0; i < companies.length; i += batch_size) {
        batches.push(companies.slice(i, i + batch_size));
      }

      let totalInserted = 0;
      const batchResults = [];

      for (let i = 0; i < batches.length; i++) {
        const batch = batches[i];
        const batchId = `bulk_batch_${Date.now()}_${i}`;

        try {
          const mcpResult = await renderMCP.executeAction('neon_bulk_company_insert', {
            companies: batch,
            batch_id: batchId,
            batch_index: i,
            total_batches: batches.length
          });

          if (mcpResult.success) {
            totalInserted += mcpResult.data.inserted_count || batch.length;
            batchResults.push({
              batch_index: i,
              inserted: mcpResult.data.inserted_count,
              batch_id: batchId
            });
          } else {
            batchResults.push({
              batch_index: i,
              error: mcpResult.error,
              batch_id: batchId
            });
          }
        } catch (batchError) {
          console.error(`❌ Batch ${i} failed:`, batchError.message);
          batchResults.push({
            batch_index: i,
            error: batchError.message,
            batch_id: batchId
          });
        }
      }

      res.json({
        success: true,
        total_companies: companies.length,
        total_inserted: totalInserted,
        batches_processed: batches.length,
        batch_results: batchResults,
        connection_type: 'MCP_BULK'
      });

    } catch (error) {
      console.error('❌ MCP Bulk Insert Error:', error);
      res.status(500).json({
        success: false,
        error: 'MCP bulk insertion failed',
        connection_type: 'MCP_BULK',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    }
  });

  // GET /mcp/health - MCP connection health check
  app.get('/mcp/health', async (req, res) => {
    try {
      const healthResult = await renderMCP.executeAction('neon_health_check', {
        schema: 'intake',
        check_tables: ['company_raw_intake']
      });

      if (healthResult.success) {
        res.json({
          status: 'healthy',
          connection_type: 'MCP_DIRECT',
          timestamp: new Date().toISOString(),
          database_info: healthResult.data,
          mcp_server: 'connected'
        });
      } else {
        throw new Error(healthResult.error);
      }
    } catch (error) {
      res.status(503).json({
        status: 'unhealthy',
        connection_type: 'MCP_DIRECT',
        error: 'MCP health check failed',
        timestamp: new Date().toISOString(),
        details: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    }
  });

  // GET /mcp/table-info - Get intake.company_raw_intake table information
  app.get('/mcp/table-info', async (req, res) => {
    try {
      const tableInfoResult = await renderMCP.executeAction('neon_table_info', {
        schema: 'intake',
        table: 'company_raw_intake'
      });

      if (tableInfoResult.success) {
        res.json({
          success: true,
          table_info: tableInfoResult.data,
          connection_type: 'MCP_DIRECT'
        });
      } else {
        throw new Error(tableInfoResult.error);
      }
    } catch (error) {
      res.status(500).json({
        success: false,
        error: 'Failed to get table info via MCP',
        connection_type: 'MCP_DIRECT',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    }
  });

  console.log('✅ MCP Render endpoints configured:');
  console.log('   • POST /mcp/insert - Direct MCP insertion (no CORS issues)');
  console.log('   • POST /mcp/bulk-company - Bulk company insertion');
  console.log('   • GET /mcp/health - MCP connection health');
  console.log('   • GET /mcp/table-info - Table structure info');
}

export default renderMCP;