/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/ops
Barton ID: 04.04.13
Unique ID: CTB-B85E88A9
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

/**
 * Barton Doctrine Neon Writer - Complete Data Access Layer
 * Full CRUD operations with Barton ID compliance and MCP-first execution
 * ALL operations through Composio MCP - NO direct database connections
 */

import dotenv from 'dotenv';
import { postToAuditLog } from './auditLogger.js';

dotenv.config();

const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn';
const NEON_CONNECTION_ID = process.env.NEON_CONNECTION_ID || 'neon_barton_outreach';
const BATCH_SIZE = 100; // Insert rows in batches for efficiency
const MAX_RETRIES = 3;
const INITIAL_RETRY_DELAY = 1000; // ms
const STRICT_MODE = process.env.NEON_STRICT_MODE === 'true';

/**
 * Generate Barton-compliant unique ID for operations
 */
function generateOperationId() {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substr(2, 8).toUpperCase();
  return `NEON-${timestamp}-${random}`;
}

/**
 * Sleep utility for retry backoff
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry with exponential backoff
 */
async function retryWithBackoff(fn, operation, maxRetries = MAX_RETRIES) {
  let lastError;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      if (attempt < maxRetries - 1) {
        const delay = INITIAL_RETRY_DELAY * Math.pow(2, attempt);
        console.warn(`⚠️ ${operation} failed (attempt ${attempt + 1}/${maxRetries}), retrying in ${delay}ms...`);
        await sleep(delay);
      }
    }
  }

  throw lastError;
}

/**
 * Validate Barton ID format against patterns
 */
function validateBartonId(id) {
  if (!id) return false;

  // Check for basic Barton ID patterns
  const bartonPattern = /^\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{5}\.\d{3}$/;
  const extendedPattern = /^\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{5}\.\d+\.\d+\.[A-Z0-9]+$/;
  const shortPattern = /^(CMP|PER|CNT|AUDIT|NEON|HIST)-/;

  return bartonPattern.test(id) || extendedPattern.test(id) || shortPattern.test(id);
}

/**
 * Validate against shq_process_key_reference
 */
async function validateAgainstProcessReference(uniqueId, processId) {
  try {
    const query = `
      SELECT COUNT(*) as valid_count
      FROM marketing.shq_process_key_reference
      WHERE process_name = $1
      OR process_id = $1
      LIMIT 1
    `;

    const result = await executeQuery(query, [processId], {
      operation: 'process_validation',
      skipAudit: true
    });

    return result.rows && result.rows[0]?.valid_count > 0;
  } catch (error) {
    console.warn('Could not validate against process reference:', error.message);
    return true; // Allow if validation fails
  }
}

/**
 * Ensure Barton ID compliance for all rows
 */
async function enforceBartonCompliance(rows, tableName, options = {}) {
  const validatedRows = [];
  const errors = [];

  for (const [index, row] of rows.entries()) {
    try {
      // Check for required Barton ID fields based on table
      if (tableName.includes('contact') || tableName.includes('person')) {
        if (!row.contact_unique_id || !validateBartonId(row.contact_unique_id)) {
          throw new Error(`Invalid or missing contact_unique_id: ${row.contact_unique_id}`);
        }
        if (row.company_unique_id && !validateBartonId(row.company_unique_id)) {
          throw new Error(`Invalid company_unique_id: ${row.company_unique_id}`);
        }
      }

      if (tableName.includes('company')) {
        if (!row.company_unique_id || !validateBartonId(row.company_unique_id)) {
          throw new Error(`Invalid or missing company_unique_id: ${row.company_unique_id}`);
        }
      }

      if (tableName.includes('audit')) {
        if (!row.unique_id || !validateBartonId(row.unique_id)) {
          throw new Error(`Invalid or missing unique_id: ${row.unique_id}`);
        }
      }

      // Ensure process tracking fields
      if (!row.unique_id) {
        row.unique_id = generateOperationId();
      }
      if (!row.process_id) {
        row.process_id = 'neon-writer';
      }
      if (!row.timestamp && !row.created_at) {
        row.timestamp = new Date().toISOString();
      }

      // Validate against process reference if strict mode
      if (options.strictMode && row.process_id) {
        const isValid = await validateAgainstProcessReference(row.unique_id, row.process_id);
        if (!isValid) {
          throw new Error(`Process ID not found in shq_process_key_reference: ${row.process_id}`);
        }
      }

      validatedRows.push(row);
    } catch (validationError) {
      errors.push({
        row_index: index,
        error: validationError.message,
        row: row
      });

      if (options.strictMode || STRICT_MODE) {
        throw new Error(`Row ${index} validation failed: ${validationError.message}`);
      }

      console.warn(`⚠️ Row ${index} validation failed: ${validationError.message}`);
    }
  }

  return {
    validatedRows,
    errors,
    skippedCount: errors.length
  };
}

/**
 * Execute MCP query with retry logic
 */
async function executeMCPOperation(tool, params, metadata = {}) {
  const mcpPayload = {
    tool: `neon.${tool}`,
    params: {
      connection_id: NEON_CONNECTION_ID,
      database: "defaultdb",
      ...params
    },
    metadata: {
      unique_id: metadata.unique_id || generateOperationId(),
      process_id: metadata.process_id || "neon-writer",
      orbt_layer: metadata.altitude || 10000,
      timestamp: new Date().toISOString(),
      ...metadata
    }
  };

  const operation = `MCP ${tool}`;

  return await retryWithBackoff(async () => {
    const response = await fetch('http://localhost:3001/tool', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Composio-Api-Key': COMPOSIO_API_KEY
      },
      body: JSON.stringify(mcpPayload)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Composio MCP ${tool} failed: ${response.statusText} - ${errorText}`);
    }

    const result = await response.json();

    if (!result.success && !result.data) {
      throw new Error(result.error || `Unknown MCP error for ${tool}`);
    }

    return result;
  }, operation);
}

/**
 * Parse schema.table notation
 */
function parseTableName(tableName) {
  if (tableName.includes('.')) {
    const [schema, table] = tableName.split('.');
    return { schema, table };
  }
  return { schema: 'public', table: tableName };
}

/**
 * Execute raw query through MCP
 */
async function executeQuery(query, params = [], options = {}) {
  try {
    const result = await executeMCPOperation('query', {
      query: query,
      params: params
    }, {
      operation: options.operation || 'query',
      unique_id: options.unique_id,
      process_id: options.process_id
    });

    if (!options.skipAudit) {
      await postToAuditLog({
        unique_id: options.unique_id || generateOperationId(),
        process_id: options.process_id || 'neon-query',
        status: 'Success',
        source: 'neon-writer',
        operation_type: 'query',
        query_length: query.length
      }, { skipRetry: true });
    }

    return {
      success: true,
      rows: result.data || [],
      row_count: result.data?.length || 0
    };
  } catch (error) {
    if (!options.skipAudit) {
      await postToAuditLog({
        unique_id: options.unique_id || generateOperationId(),
        process_id: options.process_id || 'neon-query',
        status: 'Failed',
        source: 'neon-writer',
        operation_type: 'query',
        error: error.message
      }, { skipRetry: true });
    }

    console.error(`❌ Query execution failed:`, error);
    throw error;
  }
}

/**
 * Insert rows with batching and error handling
 */
export async function insertRows(tableName, rows, options = {}) {
  if (!rows || rows.length === 0) {
    console.log(`⚠️ No rows to insert into ${tableName}`);
    return {
      success: true,
      inserted_count: 0,
      batches: 0
    };
  }

  console.log(`📤 Inserting ${rows.length} rows into Neon table ${tableName}`);

  const operationId = options.unique_id || generateOperationId();

  // Audit start
  await postToAuditLog({
    unique_id: operationId,
    process_id: options.process_id || 'neon-insert',
    status: 'Pending',
    source: 'neon-writer',
    operation_type: 'insert',
    table_name: tableName,
    record_count: rows.length
  }, { skipRetry: true });

  try {
    // Enforce Barton compliance
    const validation = await enforceBartonCompliance(rows, tableName, options);
    const validatedRows = validation.validatedRows;

    if (validatedRows.length === 0) {
      throw new Error('No valid rows after Barton compliance check');
    }

    const { schema, table } = parseTableName(tableName);
    const results = {
      success: true,
      inserted_count: 0,
      failed_count: 0,
      batches: 0,
      errors: validation.errors,
      inserted_ids: []
    };

    // Process in batches
    const batches = [];
    for (let i = 0; i < validatedRows.length; i += BATCH_SIZE) {
      batches.push(validatedRows.slice(i, i + BATCH_SIZE));
    }

    console.log(`🔄 Processing ${batches.length} batches of up to ${BATCH_SIZE} rows each`);

    for (const [index, batch] of batches.entries()) {
      try {
        const batchResult = await executeMCPOperation('insert_rows', {
          schema: schema,
          table: table,
          rows: batch,
          on_conflict: options.on_conflict || "do_nothing",
          returning: options.returning || ["unique_id", "contact_unique_id", "company_unique_id"].filter(col =>
            batch[0] && batch[0][col] !== undefined
          )
        }, {
          batch_number: index + 1,
          total_batches: batches.length,
          unique_id: `${operationId}.batch.${index + 1}`,
          process_id: options.process_id
        });

        results.batches++;
        results.inserted_count += batchResult.data?.length || batch.length;

        if (batchResult.data && Array.isArray(batchResult.data)) {
          results.inserted_ids.push(...batchResult.data.map(r =>
            r.unique_id || r.contact_unique_id || r.company_unique_id
          ));
        }

        console.log(`✅ Batch ${index + 1}/${batches.length} inserted successfully (${batch.length} rows)`);

      } catch (batchError) {
        console.error(`❌ Batch ${index + 1} failed:`, batchError.message);
        results.failed_count += batch.length;
        results.errors.push({
          batch: index + 1,
          error: batchError.message,
          rows_affected: batch.length
        });

        if (options.strictMode || STRICT_MODE) {
          results.success = false;
          throw batchError;
        }
      }
    }

    // Audit success
    await postToAuditLog({
      unique_id: operationId,
      process_id: options.process_id || 'neon-insert',
      status: 'Success',
      source: 'neon-writer',
      operation_type: 'insert',
      table_name: tableName,
      record_count: rows.length,
      inserted_count: results.inserted_count,
      failed_count: results.failed_count
    }, { skipRetry: true });

    console.log(`✅ Insert complete: ${results.inserted_count}/${rows.length} rows inserted into ${tableName}`);
    return results;

  } catch (error) {
    // Audit failure
    await postToAuditLog({
      unique_id: operationId,
      process_id: options.process_id || 'neon-insert',
      status: 'Failed',
      source: 'neon-writer',
      operation_type: 'insert',
      table_name: tableName,
      error: error.message
    }, { skipRetry: true });

    console.error(`❌ Insert failed for ${tableName}:`, error);
    throw error;
  }
}

/**
 * Update rows with conditions
 */
export async function updateRows(tableName, conditions, updates, options = {}) {
  console.log(`📝 Updating rows in Neon table ${tableName}`);

  const operationId = options.unique_id || generateOperationId();
  const { schema, table } = parseTableName(tableName);

  // Audit start
  await postToAuditLog({
    unique_id: operationId,
    process_id: options.process_id || 'neon-update',
    status: 'Pending',
    source: 'neon-writer',
    operation_type: 'update',
    table_name: tableName
  }, { skipRetry: true });

  try {
    const result = await executeMCPOperation('update_rows', {
      schema: schema,
      table: table,
      updates: updates,
      where: conditions,
      returning: options.returning || ["*"]
    }, {
      unique_id: operationId,
      process_id: options.process_id
    });

    const updatedCount = result.data?.length || 0;

    // Audit success
    await postToAuditLog({
      unique_id: operationId,
      process_id: options.process_id || 'neon-update',
      status: 'Success',
      source: 'neon-writer',
      operation_type: 'update',
      table_name: tableName,
      updated_count: updatedCount
    }, { skipRetry: true });

    console.log(`✅ Updated ${updatedCount} rows in ${tableName}`);

    return {
      success: true,
      updated_count: updatedCount,
      data: result.data
    };

  } catch (error) {
    // Audit failure
    await postToAuditLog({
      unique_id: operationId,
      process_id: options.process_id || 'neon-update',
      status: 'Failed',
      source: 'neon-writer',
      operation_type: 'update',
      table_name: tableName,
      error: error.message
    }, { skipRetry: true });

    console.error(`❌ Update failed for ${tableName}:`, error);
    throw error;
  }
}

/**
 * Upsert rows (insert or update on conflict)
 */
export async function upsertRows(tableName, rows, conflictKeys, options = {}) {
  console.log(`🔄 Upserting ${rows.length} rows into Neon table ${tableName}`);

  const operationId = options.unique_id || generateOperationId();

  // Enforce Barton compliance
  const validation = await enforceBartonCompliance(rows, tableName, options);
  const validatedRows = validation.validatedRows;

  const { schema, table } = parseTableName(tableName);

  // Audit start
  await postToAuditLog({
    unique_id: operationId,
    process_id: options.process_id || 'neon-upsert',
    status: 'Pending',
    source: 'neon-writer',
    operation_type: 'upsert',
    table_name: tableName,
    record_count: validatedRows.length
  }, { skipRetry: true });

  try {
    const result = await executeMCPOperation('upsert_rows', {
      schema: schema,
      table: table,
      rows: validatedRows,
      conflict_columns: conflictKeys,
      update_columns: options.update_columns || "all",
      returning: options.returning || ["*"]
    }, {
      unique_id: operationId,
      process_id: options.process_id
    });

    const upsertedCount = result.data?.length || 0;

    // Audit success
    await postToAuditLog({
      unique_id: operationId,
      process_id: options.process_id || 'neon-upsert',
      status: 'Success',
      source: 'neon-writer',
      operation_type: 'upsert',
      table_name: tableName,
      upserted_count: upsertedCount
    }, { skipRetry: true });

    console.log(`✅ Upserted ${upsertedCount} rows in ${tableName}`);

    return {
      success: true,
      upserted_count: upsertedCount,
      data: result.data,
      validation_errors: validation.errors
    };

  } catch (error) {
    // Audit failure
    await postToAuditLog({
      unique_id: operationId,
      process_id: options.process_id || 'neon-upsert',
      status: 'Failed',
      source: 'neon-writer',
      operation_type: 'upsert',
      table_name: tableName,
      error: error.message
    }, { skipRetry: true });

    console.error(`❌ Upsert failed for ${tableName}:`, error);
    throw error;
  }
}

/**
 * Delete rows with conditions
 */
export async function deleteRows(tableName, conditions, options = {}) {
  console.log(`🗑️ Deleting rows from Neon table ${tableName}`);

  const operationId = options.unique_id || generateOperationId();
  const { schema, table } = parseTableName(tableName);

  // Audit start
  await postToAuditLog({
    unique_id: operationId,
    process_id: options.process_id || 'neon-delete',
    status: 'Pending',
    source: 'neon-writer',
    operation_type: 'delete',
    table_name: tableName
  }, { skipRetry: true });

  try {
    const result = await executeMCPOperation('delete_rows', {
      schema: schema,
      table: table,
      where: conditions,
      returning: options.returning || ["*"]
    }, {
      unique_id: operationId,
      process_id: options.process_id
    });

    const deletedCount = result.data?.length || 0;

    // Audit success
    await postToAuditLog({
      unique_id: operationId,
      process_id: options.process_id || 'neon-delete',
      status: 'Success',
      source: 'neon-writer',
      operation_type: 'delete',
      table_name: tableName,
      deleted_count: deletedCount
    }, { skipRetry: true });

    console.log(`✅ Deleted ${deletedCount} rows from ${tableName}`);

    return {
      success: true,
      deleted_count: deletedCount,
      data: result.data
    };

  } catch (error) {
    // Audit failure
    await postToAuditLog({
      unique_id: operationId,
      process_id: options.process_id || 'neon-delete',
      status: 'Failed',
      source: 'neon-writer',
      operation_type: 'delete',
      table_name: tableName,
      error: error.message
    }, { skipRetry: true });

    console.error(`❌ Delete failed for ${tableName}:`, error);
    throw error;
  }
}

/**
 * Query rows with conditions and options
 */
export async function queryRows(tableName, conditions = {}, options = {}) {
  console.log(`🔍 Querying rows from Neon table ${tableName}`);

  const operationId = options.unique_id || generateOperationId();
  const { schema, table } = parseTableName(tableName);

  // Build WHERE clause from conditions
  const whereClause = Object.keys(conditions).length > 0
    ? Object.keys(conditions).map((key, index) => `${key} = $${index + 1}`).join(' AND ')
    : '1=1';

  const params = Object.values(conditions);

  const query = `
    SELECT ${options.select || '*'}
    FROM ${schema}.${table}
    WHERE ${whereClause}
    ${options.orderBy ? `ORDER BY ${options.orderBy}` : ''}
    ${options.limit ? `LIMIT ${options.limit}` : ''}
    ${options.offset ? `OFFSET ${options.offset}` : ''}
  `;

  try {
    const result = await executeQuery(query, params, {
      operation: 'query_rows',
      unique_id: operationId,
      process_id: options.process_id
    });

    console.log(`✅ Query returned ${result.row_count} rows from ${tableName}`);

    return result;

  } catch (error) {
    console.error(`❌ Query failed for ${tableName}:`, error);
    throw error;
  }
}

/**
 * Get table statistics
 */
export async function getTableStats(tableName, options = {}) {
  const { schema, table } = parseTableName(tableName);

  const query = `
    SELECT
      COUNT(*) as row_count,
      pg_size_pretty(pg_total_relation_size($1::regclass)) as total_size,
      pg_size_pretty(pg_relation_size($1::regclass)) as table_size,
      pg_size_pretty(pg_indexes_size($1::regclass)) as indexes_size
    FROM ${schema}.${table}
    LIMIT 1
  `;

  try {
    const result = await executeQuery(query, [`${schema}.${table}`], {
      operation: 'table_stats',
      process_id: options.process_id
    });

    return result.rows[0] || {
      row_count: 0,
      total_size: '0 bytes',
      table_size: '0 bytes',
      indexes_size: '0 bytes'
    };
  } catch (error) {
    console.error(`Failed to get stats for ${tableName}:`, error);
    return { row_count: 0, error: error.message };
  }
}

/**
 * Validate table exists
 */
export async function validateTableExists(tableName, options = {}) {
  const { schema, table } = parseTableName(tableName);

  const query = `
    SELECT EXISTS (
      SELECT FROM information_schema.tables
      WHERE table_schema = $1
      AND table_name = $2
    ) as exists
  `;

  try {
    const result = await executeQuery(query, [schema, table], {
      operation: 'table_validation',
      process_id: options.process_id,
      skipAudit: true
    });

    return result.rows[0]?.exists === true;
  } catch (error) {
    console.error(`Failed to validate table ${tableName}:`, error);
    return false;
  }
}

/**
 * CLI runner for testing
 */
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);

  // Parse CLI arguments
  const parseArg = (name) => {
    const arg = args.find(a => a.startsWith(`--${name}=`));
    return arg ? arg.split('=')[1] : null;
  };

  const tableName = parseArg('table') || 'marketing.contact_verification';
  const operation = parseArg('operation') || 'query';
  const limit = parseInt(parseArg('limit') || '10');

  console.log('\n🏁 Starting Neon Writer CLI Test');
  console.log('─'.repeat(50));
  console.log(`📊 Table: ${tableName}`);
  console.log(`⚙️ Operation: ${operation}`);
  console.log(`📏 Limit: ${limit}`);

  try {
    switch (operation) {
      case 'query':
        const queryResult = await queryRows(tableName, {}, { limit });
        console.log(`\n✅ Query successful: ${queryResult.row_count} rows found`);
        if (queryResult.rows.length > 0) {
          console.log('Sample row:', queryResult.rows[0]);
        }
        break;

      case 'stats':
        const stats = await getTableStats(tableName);
        console.log('\n📊 Table Statistics:');
        console.log(stats);
        break;

      case 'validate':
        const exists = await validateTableExists(tableName);
        console.log(`\n${exists ? '✅' : '❌'} Table ${tableName} ${exists ? 'exists' : 'does not exist'}`);
        break;

      default:
        console.error(`❌ Unknown operation: ${operation}`);
        console.log('Available operations: query, stats, validate');
        process.exit(1);
    }

    process.exit(0);
  } catch (error) {
    console.error('\n💥 CLI test failed:', error.message);
    process.exit(1);
  }
}

// Legacy function names for backward compatibility
export const insertIntoNeon = insertRows;
export const queryFromNeon = executeQuery;
export const updateInNeon = updateRows;
export const upsertIntoNeon = upsertRows;
export const deleteFromNeon = deleteRows;

export default {
  insertRows,
  updateRows,
  upsertRows,
  deleteRows,
  queryRows,
  executeQuery,
  getTableStats,
  validateTableExists,
  // Legacy exports
  insertIntoNeon: insertRows,
  queryFromNeon: executeQuery,
  updateInNeon: updateRows,
  upsertIntoNeon: upsertRows,
  deleteFromNeon: deleteRows
};