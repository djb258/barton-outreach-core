/**
 * Schema Registry API Routes
 * Handles schema scanning, syncing, and metadata management
 * Uses Standard Composio MCP Pattern for all database operations
 */

import { scanSchemas, getSchemaStatistics, scanTableStructure } from '../services/schemaScanner.js';
import StandardComposioNeonBridge from '../api/lib/standard-composio-neon-bridge.js';

/**
 * POST /api/schema/sync
 * Scans database schemas and syncs metadata to registry
 */
export async function syncSchemaRegistry(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const bridge = new StandardComposioNeonBridge();

  try {
    console.log(`[SCHEMA-REGISTRY] Starting schema sync operation`);

    // 1. Scan all schemas
    const scanResult = await scanSchemas();

    if (!scanResult.success) {
      throw new Error('Schema scan failed');
    }

    // 2. Upsert into registry table
    const syncStats = await upsertSchemaMetadata(bridge, scanResult.data);

    // 3. Log the sync operation
    await logSchemaOperation(bridge, {
      operation: 'sync',
      change_summary: `Synced ${scanResult.data.length} columns from ${scanResult.metadata.schemas_scanned.length} schemas`,
      metadata: {
        ...scanResult.metadata,
        sync_stats: syncStats
      }
    });

    console.log(`[SCHEMA-REGISTRY] Schema sync completed successfully`);

    return res.status(200).json({
      success: true,
      message: 'Schema registry synchronized successfully',
      data: {
        columns_processed: scanResult.data.length,
        schemas_scanned: scanResult.metadata.schemas_scanned,
        sync_statistics: syncStats
      },
      metadata: {
        sync_timestamp: new Date().toISOString(),
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    });

  } catch (error) {
    console.error('[SCHEMA-REGISTRY] Sync operation failed:', error);

    // Log the failed operation
    try {
      await logSchemaOperation(bridge, {
        operation: 'sync_failed',
        change_summary: `Schema sync failed: ${error.message}`,
        metadata: { error: error.message }
      });
    } catch (logError) {
      console.error('[SCHEMA-REGISTRY] Failed to log sync failure:', logError);
    }

    return res.status(500).json({
      error: 'Schema sync failed',
      message: error.message,
      altitude: 10000,
      doctrine: 'STAMPED'
    });

  } finally {
    await bridge.close();
  }
}

/**
 * GET /api/schema/statistics
 * Returns schema statistics and metadata
 */
export async function getSchemaRegistryStatistics(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();

  try {
    console.log(`[SCHEMA-REGISTRY] Generating statistics`);

    const stats = await getSchemaStatistics();

    return res.status(200).json({
      success: true,
      data: stats.data,
      metadata: {
        ...stats.metadata,
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    });

  } catch (error) {
    console.error('[SCHEMA-REGISTRY] Statistics generation failed:', error);
    return res.status(500).json({
      error: 'Failed to generate statistics',
      message: error.message
    });
  }
}

/**
 * GET /api/schema/table/:schema/:table
 * Returns detailed structure for a specific table
 */
export async function getTableStructure(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();

  const { schema, table } = req.params;

  try {
    console.log(`[SCHEMA-REGISTRY] Getting table structure for ${schema}.${table}`);

    const structure = await scanTableStructure(schema, table);

    return res.status(200).json({
      success: true,
      data: structure.data,
      metadata: {
        ...structure.metadata,
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    });

  } catch (error) {
    console.error(`[SCHEMA-REGISTRY] Failed to get table structure for ${schema}.${table}:`, error);
    return res.status(500).json({
      error: 'Failed to get table structure',
      message: error.message
    });
  }
}

/**
 * GET /api/schema/registry
 * Returns current registry contents with optional filtering
 */
export async function getRegistryContents(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();

  const bridge = new StandardComposioNeonBridge();

  try {
    const { schema, table, limit = 1000 } = req.query;

    console.log(`[SCHEMA-REGISTRY] Fetching registry contents`);

    let whereConditions = [];
    let params = [];

    if (schema) {
      whereConditions.push(`schema_name = $${params.length + 1}`);
      params.push(schema);
    }

    if (table) {
      whereConditions.push(`table_name = $${params.length + 1}`);
      params.push(table);
    }

    const whereClause = whereConditions.length > 0
      ? `WHERE ${whereConditions.join(' AND ')}`
      : '';

    const sql = `
      SELECT
        schema_name,
        table_name,
        column_name,
        data_type,
        is_nullable,
        column_default,
        is_primary_key,
        is_foreign_key,
        doctrine_tag,
        last_updated
      FROM shq.schema_registry
      ${whereClause}
      ORDER BY schema_name, table_name, ordinal_position
      LIMIT $${params.length + 1}
    `;

    params.push(parseInt(limit));

    const result = await bridge.executeSQL(sql, params);

    if (!result.success) {
      throw new Error(`Failed to fetch registry contents: ${result.error}`);
    }

    return res.status(200).json({
      success: true,
      data: result.data.rows,
      metadata: {
        total_rows: result.data.rows.length,
        filters: { schema, table, limit },
        fetched_at: new Date().toISOString(),
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    });

  } catch (error) {
    console.error('[SCHEMA-REGISTRY] Failed to fetch registry contents:', error);
    return res.status(500).json({
      error: 'Failed to fetch registry contents',
      message: error.message
    });
  } finally {
    await bridge.close();
  }
}

/**
 * Helper function: Upsert schema metadata into registry
 */
async function upsertSchemaMetadata(bridge, schemaData) {
  console.log(`[SCHEMA-REGISTRY] Upserting ${schemaData.length} metadata records`);

  const upsertPromises = schemaData.map(async (record) => {
    const sql = `
      INSERT INTO shq.schema_registry (
        schema_name, table_name, column_name, data_type,
        is_nullable, column_default, max_length, numeric_precision, numeric_scale,
        ordinal_position, is_primary_key, is_foreign_key, constraint_name, table_type,
        last_updated
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW())
      ON CONFLICT (schema_name, table_name, column_name)
      DO UPDATE SET
        data_type = EXCLUDED.data_type,
        is_nullable = EXCLUDED.is_nullable,
        column_default = EXCLUDED.column_default,
        max_length = EXCLUDED.max_length,
        numeric_precision = EXCLUDED.numeric_precision,
        numeric_scale = EXCLUDED.numeric_scale,
        ordinal_position = EXCLUDED.ordinal_position,
        is_primary_key = EXCLUDED.is_primary_key,
        is_foreign_key = EXCLUDED.is_foreign_key,
        constraint_name = EXCLUDED.constraint_name,
        table_type = EXCLUDED.table_type,
        last_updated = NOW()
    `;

    const params = [
      record.schema, record.table, record.column, record.type,
      record.nullable, record.default_value, record.max_length,
      record.precision, record.scale, record.position,
      record.primary_key, record.foreign_key, record.constraint_name, record.table_type
    ];

    return await bridge.executeSQL(sql, params);
  });

  const results = await Promise.all(upsertPromises);

  const successCount = results.filter(r => r.success).length;
  const failureCount = results.filter(r => !r.success).length;

  console.log(`[SCHEMA-REGISTRY] Upsert completed: ${successCount} success, ${failureCount} failures`);

  return {
    total_processed: schemaData.length,
    successful_upserts: successCount,
    failed_upserts: failureCount
  };
}

/**
 * Helper function: Log schema operations to audit log
 */
async function logSchemaOperation(bridge, { operation, schema_name, table_name, column_name, change_summary, metadata }) {
  const sql = `
    INSERT INTO shq.schema_audit_log (
      operation, schema_name, table_name, column_name, change_summary, metadata
    ) VALUES ($1, $2, $3, $4, $5, $6::jsonb)
  `;

  const params = [
    operation,
    schema_name || null,
    table_name || null,
    column_name || null,
    change_summary,
    JSON.stringify(metadata || {})
  ];

  return await bridge.executeSQL(sql, params);
}