/**
 * Doctrine Spec:
 * - Barton ID: 99.99.99.07.14292.720
 * - Altitude: 10000 (Execution Layer)
 * - Input: data query parameters and filters
 * - Output: database records and metadata
 * - MCP: Composio (Neon integrated)
 */
/**
 * API Endpoint: /api/promote (Extended for Promotion Console)
 * Vercel-ready serverless promotion orchestration
 * Handles complete promotion workflow with slot creation and audit logging
 */

import ComposioNeonBridge from './lib/composio-neon-bridge.js';
import BartonDoctrineUtils from './utils/barton-doctrine.js';

export default async function handler(req, res) {
  // Only accept POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({
      error: 'Method not allowed',
      message: 'Only POST requests are accepted',
      altitude: 10000,
      doctrine: 'STAMPED'
    });
  }

  const startTime = Date.now();
  const bridge = new ComposioNeonBridge();

  try {
    // Extract request parameters
    const {
      filters = { validated: true },
      batch_size = 100,
      include_audit = true,
      force_promotion = false
    } = req.body;

    console.log('[PROMOTE] Starting promotion with filters:', filters);

    // Initialize response structure
    const response = {
      rows_promoted: 0,
      rows_failed: 0,
      promotion_timestamp: new Date().toISOString(),
      promoted_unique_ids: [],
      failed_rows: [],
      altitude: 10000,
      doctrine: 'STAMPED',
      process_metadata: {
        process_id: BartonDoctrineUtils.generateProcessId('PROMOTE'),
        started_at: new Date().toISOString(),
        batch_size,
        doctrine_version: process.env.DOCTRINE_HASH || 'STAMPED_v2.1.0'
      }
    };

    // Step 1: Fetch validated rows from staging table via Composio MCP
    console.log('[PROMOTE] Fetching validated rows from staging table');

    const fetchQuery = buildPromotionQuery(filters);
    const fetchResult = await bridge.executeNeonOperation('QUERY_ROWS', {
      sql: fetchQuery,
      limit: batch_size,
      return_metadata: true
    });

    if (!fetchResult.success) {
      throw new Error(`Failed to fetch promotion candidates: ${fetchResult.error}`);
    }

    const candidateRows = fetchResult.data?.rows || [];
    console.log(`[PROMOTE] Found ${candidateRows.length} candidates for promotion`);

    if (candidateRows.length === 0) {
      return res.status(200).json({
        ...response,
        message: 'No validated rows found for promotion',
        completed_at: new Date().toISOString()
      });
    }

    // Step 2: Process each row through promotion pipeline
    const promotionResults = [];
    const auditEntries = [];

    for (const row of candidateRows) {
      const promotionResult = await promoteCompanyRecord(bridge, row, response.process_metadata.process_id);
      promotionResults.push(promotionResult);

      if (promotionResult.success) {
        response.rows_promoted++;
        response.promoted_unique_ids.push(promotionResult.unique_id);

        // Create audit entry for successful promotion
        auditEntries.push(createAuditEntry('promotion_success', {
          unique_id: promotionResult.unique_id,
          company_name: row.company_name,
          slot_id: promotionResult.slot_id,
          process_id: response.process_metadata.process_id
        }));
      } else {
        response.rows_failed++;
        response.failed_rows.push({
          unique_id: row.unique_id,
          company_name: row.company_name || 'Unknown',
          errors: promotionResult.errors
        });

        // Create audit entry for failed promotion
        auditEntries.push(createAuditEntry('promotion_failed', {
          unique_id: row.unique_id,
          company_name: row.company_name,
          errors: promotionResult.errors,
          process_id: response.process_metadata.process_id
        }));
      }
    }

    // Step 3: Bulk update staging table with promotion status
    console.log('[PROMOTE] Updating staging table with promotion status');

    const updateResult = await bulkUpdatePromotionStatus(bridge, promotionResults);

    if (!updateResult.success) {
      console.error('[PROMOTE] Warning: Failed to update staging table:', updateResult.error);
    }

    // Step 4: Write audit log via Composio MCP
    if (include_audit && auditEntries.length > 0) {
      const auditResult = await writeAuditLog(bridge, auditEntries, response.process_metadata.process_id);

      if (auditResult.success) {
        response.audit_log_url = `/logs/company_promotion_log_${new Date().toISOString().split('T')[0].replace(/-/g, '')}.json`;
        response.audit_log_id = auditResult.log_id;
      }
    }

    // Step 5: Finalize response metadata
    response.process_metadata.completed_at = new Date().toISOString();
    response.process_metadata.total_processing_time_ms = Date.now() - startTime;
    response.process_metadata.performance_grade = BartonDoctrineUtils.getPerformanceGrade(
      response.process_metadata.total_processing_time_ms
    );

    // Add STAMPED compliance
    response.stamped_metadata = {
      source: 'promotion_middleware',
      timestamp: response.promotion_timestamp,
      actor: 'composio_mcp_orchestrator',
      method: 'stamped_promotion_pipeline',
      process: response.process_metadata.process_id,
      environment: process.env.NODE_ENV || 'production',
      data: {
        promoted_count: response.rows_promoted,
        failed_count: response.rows_failed,
        batch_size
      }
    };

    console.log(`[PROMOTE] Promotion complete: ${response.rows_promoted} promoted, ${response.rows_failed} failed`);

    return res.status(200).json({
      success: response.rows_promoted > 0,
      ...response
    });

  } catch (error) {
    console.error('[PROMOTE] Critical error:', error);

    return res.status(500).json({
      success: false,
      error: 'Promotion failed',
      message: error.message,
      rows_promoted: 0,
      rows_failed: 0,
      promotion_timestamp: new Date().toISOString(),
      promoted_unique_ids: [],
      failed_rows: [],
      altitude: 10000,
      doctrine: 'STAMPED',
      process_metadata: {
        process_id: BartonDoctrineUtils.generateProcessId('PROMOTE_ERROR'),
        error_timestamp: new Date().toISOString(),
        error_details: {
          message: error.message,
          stack: error.stack
        }
      }
    });
  }
}

/**
 * Promote a single company record through the complete pipeline
 */
async function promoteCompanyRecord(bridge, row, processId) {
  const result = {
    unique_id: row.unique_id,
    success: false,
    errors: [],
    slot_id: null,
    promotion_metadata: {}
  };

  try {
    // Step 1: Insert into company master table
    const insertResult = await insertIntoMasterTable(bridge, row, processId);

    if (!insertResult.success) {
      result.errors.push('master_table_insert_failed');
      return result;
    }

    // Step 2: Create company slot
    const slotResult = await createCompanySlot(bridge, row, processId);

    if (!slotResult.success) {
      result.errors.push('slot_creation_failed');
      // Continue with promotion even if slot creation fails (non-critical)
    } else {
      result.slot_id = slotResult.slot_id;
    }

    // Step 3: Initialize company metadata
    const metadataResult = await initializeCompanyMetadata(bridge, row, processId);

    if (!metadataResult.success) {
      result.errors.push('metadata_initialization_failed');
      // Continue with promotion (non-critical)
    }

    // Step 4: Trigger post-promotion webhooks/notifications
    const notificationResult = await triggerPromotionNotifications(bridge, row, processId);

    if (!notificationResult.success) {
      result.errors.push('notification_failed');
      // Continue with promotion (non-critical)
    }

    // Promotion successful if master table insert succeeded
    result.success = insertResult.success;
    result.promotion_metadata = {
      master_table_id: insertResult.id,
      slot_id: result.slot_id,
      metadata_initialized: metadataResult.success,
      notifications_sent: notificationResult.success,
      promotion_timestamp: new Date().toISOString()
    };

    return result;

  } catch (error) {
    console.error(`[PROMOTE] Error promoting record ${row.unique_id}:`, error);
    result.errors.push('promotion_system_error');
    result.system_error = error.message;
    return result;
  }
}

/**
 * Insert company record into master table
 */
async function insertIntoMasterTable(bridge, row, processId) {
  try {
    const promotedRow = {
      ...row,
      unique_id: row.unique_id,
      process_id: processId,
      altitude: 'production',
      promoted_at: new Date().toISOString(),
      promotion_source: 'staging_promotion',
      status: 'active'
    };

    const insertSQL = `
      INSERT INTO marketing.company (
        unique_id, company_name, industry, contact_email, contact_phone,
        address, website_url, employee_count, revenue, description,
        process_id, altitude, promoted_at, promotion_source, status,
        created_at, updated_at
      ) VALUES (
        '${promotedRow.unique_id}',
        '${sanitizeSQL(promotedRow.company_name)}',
        '${sanitizeSQL(promotedRow.industry)}',
        '${sanitizeSQL(promotedRow.contact_email)}',
        '${sanitizeSQL(promotedRow.contact_phone)}',
        '${sanitizeSQL(promotedRow.address)}',
        '${sanitizeSQL(promotedRow.website_url)}',
        ${promotedRow.employee_count || 'NULL'},
        ${promotedRow.revenue || 'NULL'},
        '${sanitizeSQL(promotedRow.description || '')}',
        '${processId}',
        'production',
        NOW(),
        'staging_promotion',
        'active',
        NOW(),
        NOW()
      )
      ON CONFLICT (unique_id) DO UPDATE SET
        updated_at = NOW(),
        promotion_source = 'staging_promotion_update'
      RETURNING id, unique_id
    `;

    const result = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: insertSQL,
      mode: 'write',
      return_type: 'rows'
    });

    if (result.success && result.data?.rows?.length > 0) {
      return {
        success: true,
        id: result.data.rows[0].id,
        unique_id: result.data.rows[0].unique_id
      };
    }

    return { success: false, error: 'Insert failed - no rows returned' };

  } catch (error) {
    console.error('[PROMOTE] Master table insert error:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Create company slot for the promoted company
 */
async function createCompanySlot(bridge, row, processId) {
  try {
    const slotId = BartonDoctrineUtils.generateUniqueId('SLOT');

    const slotSQL = `
      INSERT INTO marketing.company_slots (
        slot_id, company_unique_id, slot_type, slot_status,
        process_id, created_at, metadata
      ) VALUES (
        '${slotId}',
        '${row.unique_id}',
        'company_slot',
        'active',
        '${processId}',
        NOW(),
        '${JSON.stringify({
          company_name: row.company_name,
          industry: row.industry,
          promotion_source: 'staging'
        }).replace(/'/g, "''")}'
      )
      RETURNING slot_id
    `;

    const result = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: slotSQL,
      mode: 'write',
      return_type: 'rows'
    });

    if (result.success && result.data?.rows?.length > 0) {
      return {
        success: true,
        slot_id: result.data.rows[0].slot_id
      };
    }

    return { success: false, error: 'Slot creation failed' };

  } catch (error) {
    console.error('[PROMOTE] Slot creation error:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Initialize company metadata tables
 */
async function initializeCompanyMetadata(bridge, row, processId) {
  try {
    const metadataSQL = `
      INSERT INTO marketing.company_metadata (
        company_unique_id, metadata_type, metadata_value,
        process_id, created_at
      ) VALUES
      ('${row.unique_id}', 'promotion_details', '${JSON.stringify({
        promoted_from: 'staging',
        promotion_timestamp: new Date().toISOString(),
        validation_status: 'validated'
      }).replace(/'/g, "''")}', '${processId}', NOW()),
      ('${row.unique_id}', 'contact_preferences', '${JSON.stringify({
        email_consent: true,
        phone_consent: true,
        marketing_consent: false
      }).replace(/'/g, "''")}', '${processId}', NOW())
    `;

    const result = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: metadataSQL,
      mode: 'write'
    });

    return { success: result.success };

  } catch (error) {
    console.error('[PROMOTE] Metadata initialization error:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Trigger promotion notifications
 */
async function triggerPromotionNotifications(bridge, row, processId) {
  try {
    // Log notification trigger
    const notificationSQL = `
      INSERT INTO marketing.system_notifications (
        notification_type, target_id, message, process_id,
        status, created_at
      ) VALUES (
        'company_promoted',
        '${row.unique_id}',
        'Company ${sanitizeSQL(row.company_name)} successfully promoted to production',
        '${processId}',
        'pending',
        NOW()
      )
    `;

    const result = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: notificationSQL,
      mode: 'write'
    });

    return { success: result.success };

  } catch (error) {
    console.error('[PROMOTE] Notification trigger error:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Write audit log entries
 */
async function writeAuditLog(bridge, auditEntries, processId) {
  try {
    const logId = BartonDoctrineUtils.generateUniqueId('AUDIT');

    const auditSQL = `
      INSERT INTO marketing.company_promotion_log (
        log_id, process_id, audit_entries, entry_count,
        created_at, log_type
      ) VALUES (
        '${logId}',
        '${processId}',
        '${JSON.stringify(auditEntries).replace(/'/g, "''")}',
        ${auditEntries.length},
        NOW(),
        'promotion_batch'
      )
      RETURNING log_id
    `;

    const result = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: auditSQL,
      mode: 'write',
      return_type: 'rows'
    });

    if (result.success && result.data?.rows?.length > 0) {
      return {
        success: true,
        log_id: result.data.rows[0].log_id
      };
    }

    return { success: false, error: 'Audit log creation failed' };

  } catch (error) {
    console.error('[PROMOTE] Audit log error:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Create audit entry
 */
function createAuditEntry(action, data) {
  return {
    audit_id: BartonDoctrineUtils.generateUniqueId('AUDIT'),
    action,
    timestamp: new Date().toISOString(),
    actor: 'promotion_middleware',
    details: data,
    doctrine_version: process.env.DOCTRINE_HASH || 'STAMPED_v2.1.0'
  };
}

/**
 * Build promotion query with filters
 */
function buildPromotionQuery(filters) {
  let whereClause = "WHERE validated = true AND (promoted IS NULL OR promoted = false)";

  if (filters.batch_id) {
    whereClause += ` AND batch_id = '${filters.batch_id}'`;
  }

  if (filters.industry) {
    whereClause += ` AND industry = '${sanitizeSQL(filters.industry)}'`;
  }

  if (filters.employee_count_min) {
    whereClause += ` AND employee_count >= ${filters.employee_count_min}`;
  }

  return `
    SELECT *
    FROM marketing.company_raw_intake
    ${whereClause}
    ORDER BY validation_timestamp ASC
  `;
}

/**
 * Bulk update promotion status in staging table
 */
async function bulkUpdatePromotionStatus(bridge, promotionResults) {
  try {
    const successfulPromotions = promotionResults.filter(r => r.success);
    const failedPromotions = promotionResults.filter(r => !r.success);

    if (successfulPromotions.length > 0) {
      const successIds = successfulPromotions.map(r => `'${r.unique_id}'`).join(', ');
      const successSQL = `
        UPDATE marketing.company_raw_intake
        SET
          promoted = true,
          promotion_timestamp = NOW(),
          promotion_status = 'completed'
        WHERE unique_id IN (${successIds})
      `;

      await bridge.executeNeonOperation('EXECUTE_SQL', {
        sql: successSQL,
        mode: 'write'
      });
    }

    if (failedPromotions.length > 0) {
      const failedIds = failedPromotions.map(r => `'${r.unique_id}'`).join(', ');
      const failedSQL = `
        UPDATE marketing.company_raw_intake
        SET
          promoted = false,
          promotion_status = 'failed',
          promotion_errors = '${JSON.stringify(failedPromotions.reduce((acc, r) => {
            acc[r.unique_id] = r.errors;
            return acc;
          }, {})).replace(/'/g, "''")}'
        WHERE unique_id IN (${failedIds})
      `;

      await bridge.executeNeonOperation('EXECUTE_SQL', {
        sql: failedSQL,
        mode: 'write'
      });
    }

    return { success: true };

  } catch (error) {
    console.error('[PROMOTE] Bulk update error:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Write audit log entry to marketing.company_promotion_log
 */
async function writeAuditLog(bridge, auditEntries, processId) {
  try {
    const logId = BartonDoctrineUtils.generateUniqueId('LOG');
    const batchId = processId.split('_')[1] || new Date().toISOString().split('T')[0];

    // Group entries by unique_id for individual row tracking
    const entriesGrouped = auditEntries.reduce((acc, entry) => {
      const key = entry.unique_id || 'batch_operation';
      if (!acc[key]) acc[key] = [];
      acc[key].push(entry);
      return acc;
    }, {});

    const insertPromises = Object.entries(entriesGrouped).map(async ([uniqueId, entries]) => {
      const isFailure = entries.some(e => e.action === 'promotion_failed');
      const errorLog = isFailure ?
        entries.filter(e => e.action === 'promotion_failed').map(e => e.details.errors).flat() :
        [];

      const individualLogId = BartonDoctrineUtils.generateUniqueId('ROWLOG');

      const insertSQL = `
        INSERT INTO marketing.company_promotion_log (
          log_id, process_id, batch_id, unique_id, company_name,
          promotion_status, error_log, audit_entries, entry_count,
          log_type, altitude, doctrine, doctrine_version,
          source_system, actor, method, environment, created_at
        ) VALUES (
          '${individualLogId}',
          '${processId}',
          '${batchId}',
          '${uniqueId}',
          '${sanitizeSQL(entries[0]?.details?.company_name || 'Unknown')}',
          '${isFailure ? 'FAILED' : 'PROMOTED'}',
          '${JSON.stringify(errorLog).replace(/'/g, "''")}',
          '${JSON.stringify(entries).replace(/'/g, "''")}',
          ${entries.length},
          'promotion_audit',
          10000,
          'STAMPED',
          '${process.env.DOCTRINE_HASH || 'v2.1.0'}',
          'outreach_process_manager',
          'api_promote_endpoint',
          'composio_mcp_promotion',
          '${process.env.NODE_ENV || 'production'}',
          NOW()
        )
        RETURNING log_id
      `;

      return bridge.executeNeonOperation('EXECUTE_SQL', {
        sql: insertSQL,
        mode: 'write',
        return_type: 'rows'
      });
    });

    const results = await Promise.all(insertPromises);
    const successfulLogs = results.filter(r => r.success);

    console.log(`[AUDIT] Created ${successfulLogs.length} individual audit log entries`);

    return {
      success: successfulLogs.length > 0,
      log_id: logId,
      individual_logs_created: successfulLogs.length,
      total_entries: auditEntries.length
    };

  } catch (error) {
    console.error('[AUDIT] Failed to write audit log:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Create audit entry for promotion activity
 */
function createAuditEntry(action, details) {
  return {
    action,
    timestamp: new Date().toISOString(),
    unique_id: details.unique_id,
    details: {
      company_name: details.company_name || 'Unknown',
      errors: details.errors || [],
      process_id: details.process_id,
      slot_id: details.slot_id || null,
      metadata: details.metadata || {}
    },
    stamped: {
      source: 'promotion_audit',
      timestamp: new Date().toISOString(),
      actor: 'api_promote_endpoint',
      method: 'individual_row_tracking',
      process: details.process_id,
      environment: process.env.NODE_ENV || 'production',
      data: details
    }
  };
}

/**
 * Sanitize SQL input
 */
function sanitizeSQL(input) {
  if (!input) return '';
  return input.toString().replace(/'/g, "''");
}