/**
 * Doctrine Spec:
 * - Barton ID: 10.01.02.05.10000.001
 * - Altitude: 10000 (Execution Layer)
 * - Input: audit log parameters and metadata
 * - Output: audit log confirmation and tracking
 * - MCP: Composio (Neon integrated)
 */
/**
 * Audit Operations Module - Step 5 Audit Trail Integration
 * Central utility for posting audit logs to unified_audit_log table
 * Enforces Barton Doctrine compliance and standardized logging
 *
 * Functions:
 * - postToAuditLog(): Main audit logging function
 * - validateAuditEntry(): Validates audit data before insertion
 * - generateSessionId(): Creates session identifiers for batch operations
 * - getProcessorMetrics(): Calculates processing time and performance
 */

import { StandardComposioNeonBridge } from './utils/standard-composio-neon-bridge.js';

/**
 * Generate a unique session ID for batch operations
 */
export function generateSessionId(prefix = 'session') {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substr(2, 8);
  return `${prefix}_${timestamp}_${random}`;
}

/**
 * Calculate processing time metrics
 */
export function calculateProcessingTime(startTime) {
  if (!startTime) return null;
  return Date.now() - startTime;
}

/**
 * Validate audit entry data for Barton Doctrine compliance
 */
export function validateAuditEntry(auditData) {
  const errors = [];

  // Required fields validation
  const requiredFields = ['unique_id', 'process_id', 'status', 'actor', 'source', 'action', 'step', 'record_type'];

  for (const field of requiredFields) {
    if (!auditData[field]) {
      errors.push(`Missing required field: ${field}`);
    }
  }

  // Step validation
  const validSteps = ['step_1_ingest', 'step_2_validate', 'step_2b_enrich', 'step_3_adjust', 'step_4_promote'];
  if (auditData.step && !validSteps.includes(auditData.step)) {
    errors.push(`Invalid step: ${auditData.step}. Must be one of: ${validSteps.join(', ')}`);
  }

  // Status validation
  const validStatuses = ['success', 'failed', 'warning', 'pending', 'skipped'];
  if (auditData.status && !validStatuses.includes(auditData.status)) {
    errors.push(`Invalid status: ${auditData.status}. Must be one of: ${validStatuses.join(', ')}`);
  }

  // Record type validation
  const validRecordTypes = ['company', 'people', 'campaign', 'attribution', 'general'];
  if (auditData.record_type && !validRecordTypes.includes(auditData.record_type)) {
    errors.push(`Invalid record_type: ${auditData.record_type}. Must be one of: ${validRecordTypes.join(', ')}`);
  }

  // Actor validation (no anonymous actions)
  if (auditData.actor === 'anonymous' || auditData.actor === '' || auditData.actor === null) {
    errors.push('Actor cannot be anonymous or empty. Must identify the agent/human/system performing the action.');
  }

  // Confidence score validation
  if (auditData.confidence_score !== undefined && auditData.confidence_score !== null) {
    const score = parseFloat(auditData.confidence_score);
    if (isNaN(score) || score < 0 || score > 1) {
      errors.push('Confidence score must be a number between 0.00 and 1.00');
    }
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

/**
 * Main audit logging function - Posts audit entry to unified_audit_log
 *
 * @param {Object} auditData - Audit entry data
 * @param {string} auditData.unique_id - Subject Barton ID (company/person)
 * @param {string} auditData.process_id - Process identifier
 * @param {string} auditData.status - Action status (success, failed, warning, pending, skipped)
 * @param {string} auditData.actor - Who/what performed the action
 * @param {string} auditData.source - Source system/component
 * @param {string} auditData.action - Specific action taken
 * @param {string} auditData.step - Pipeline step
 * @param {string} [auditData.sub_action] - Detailed sub-action
 * @param {string} auditData.record_type - Type of record (company, people, etc.)
 * @param {number} [auditData.record_id] - FK to actual record
 * @param {Object} [auditData.before_values] - State before action
 * @param {Object} [auditData.after_values] - State after action
 * @param {string[]} [auditData.field_changes] - Modified fields
 * @param {Object} [auditData.error_log] - Error details
 * @param {string} [auditData.error_code] - Error classification
 * @param {number} [auditData.retry_count] - Retry attempts
 * @param {number} [auditData.processing_time_ms] - Processing time
 * @param {number} [auditData.confidence_score] - Action confidence
 * @param {string} [auditData.session_id] - Batch/session ID
 * @param {string} [auditData.correlation_id] - Cross-system correlation
 * @param {Object} [options] - Additional options
 * @param {boolean} [options.skipValidation] - Skip validation (use with caution)
 * @param {StandardComposioNeonBridge} [options.bridge] - Custom bridge instance
 * @returns {Promise<Object>} Audit result with audit_id and status
 */
export async function postToAuditLog(auditData, options = {}) {
  const bridge = options.bridge || new StandardComposioNeonBridge();

  try {
    // Validate audit entry unless explicitly skipped
    if (!options.skipValidation) {
      const validation = validateAuditEntry(auditData);
      if (!validation.isValid) {
        console.error('[AUDIT-OPERATIONS] Validation failed:', validation.errors);
        return {
          success: false,
          error: 'Audit entry validation failed',
          details: validation.errors,
          audit_id: null
        };
      }
    }

    // Prepare audit entry with Barton Doctrine defaults
    const auditEntry = {
      unique_id: auditData.unique_id,
      process_id: auditData.process_id,
      status: auditData.status,
      actor: auditData.actor,
      timestamp: new Date().toISOString(),
      source: auditData.source,
      action: auditData.action,
      step: auditData.step,
      sub_action: auditData.sub_action || null,
      record_type: auditData.record_type,
      record_id: auditData.record_id || null,
      before_values: auditData.before_values ? JSON.stringify(auditData.before_values) : null,
      after_values: auditData.after_values ? JSON.stringify(auditData.after_values) : null,
      field_changes: auditData.field_changes || null,
      error_log: auditData.error_log ? JSON.stringify(auditData.error_log) : null,
      error_code: auditData.error_code || null,
      retry_count: auditData.retry_count || 0,
      processing_time_ms: auditData.processing_time_ms || null,
      confidence_score: auditData.confidence_score || null,
      altitude: auditData.altitude || 10000,
      doctrine: auditData.doctrine || 'STAMPED',
      doctrine_version: auditData.doctrine_version || 'v2.1.0',
      session_id: auditData.session_id || null,
      correlation_id: auditData.correlation_id || null
    };

    // Build INSERT query
    const query = `
      INSERT INTO marketing.unified_audit_log (
        unique_id,
        process_id,
        status,
        actor,
        timestamp,
        source,
        action,
        step,
        sub_action,
        record_type,
        record_id,
        before_values,
        after_values,
        field_changes,
        error_log,
        error_code,
        retry_count,
        processing_time_ms,
        confidence_score,
        altitude,
        doctrine,
        doctrine_version,
        session_id,
        correlation_id
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
        $21, $22, $23, $24
      ) RETURNING audit_id, id
    `;

    const params = [
      auditEntry.unique_id,
      auditEntry.process_id,
      auditEntry.status,
      auditEntry.actor,
      auditEntry.timestamp,
      auditEntry.source,
      auditEntry.action,
      auditEntry.step,
      auditEntry.sub_action,
      auditEntry.record_type,
      auditEntry.record_id,
      auditEntry.before_values,
      auditEntry.after_values,
      auditEntry.field_changes,
      auditEntry.error_log,
      auditEntry.error_code,
      auditEntry.retry_count,
      auditEntry.processing_time_ms,
      auditEntry.confidence_score,
      auditEntry.altitude,
      auditEntry.doctrine,
      auditEntry.doctrine_version,
      auditEntry.session_id,
      auditEntry.correlation_id
    ];

    // Execute audit log insertion
    const result = await bridge.query(query, params);

    if (result.rows && result.rows.length > 0) {
      const auditRecord = result.rows[0];

      console.log(`[AUDIT-OPERATIONS] Audit logged successfully: ${auditRecord.audit_id} for ${auditData.unique_id} - ${auditData.action}`);

      return {
        success: true,
        audit_id: auditRecord.audit_id,
        internal_id: auditRecord.id,
        message: 'Audit entry logged successfully',
        step: auditData.step,
        action: auditData.action,
        status: auditData.status
      };
    } else {
      console.error('[AUDIT-OPERATIONS] No result returned from audit log insertion');
      return {
        success: false,
        error: 'No result returned from audit log insertion',
        audit_id: null
      };
    }

  } catch (error) {
    console.error('[AUDIT-OPERATIONS] Failed to post audit log:', error);

    // Log the audit failure to console (meta-audit)
    console.error('[AUDIT-OPERATIONS] Meta-audit: Failed to log action', {
      unique_id: auditData.unique_id,
      action: auditData.action,
      step: auditData.step,
      error: error.message,
      timestamp: new Date().toISOString()
    });

    return {
      success: false,
      error: 'Failed to post audit log',
      details: error.message,
      audit_id: null
    };
  }
}

/**
 * Bulk audit logging function for batch operations
 *
 * @param {Object[]} auditEntries - Array of audit data objects
 * @param {Object} [options] - Additional options
 * @returns {Promise<Object>} Bulk audit result
 */
export async function postBulkAuditLogs(auditEntries, options = {}) {
  const bridge = options.bridge || new StandardComposioNeonBridge();
  const results = {
    success: true,
    total: auditEntries.length,
    successful: 0,
    failed: 0,
    audit_ids: [],
    errors: []
  };

  // Generate a session ID for the bulk operation if not provided
  const sessionId = options.session_id || generateSessionId('bulk_audit');

  for (let i = 0; i < auditEntries.length; i++) {
    const auditData = auditEntries[i];

    // Add session ID to each entry
    auditData.session_id = auditData.session_id || sessionId;

    try {
      const result = await postToAuditLog(auditData, { bridge, ...options });

      if (result.success) {
        results.successful++;
        results.audit_ids.push(result.audit_id);
      } else {
        results.failed++;
        results.errors.push({
          index: i,
          unique_id: auditData.unique_id,
          error: result.error,
          details: result.details
        });
      }
    } catch (error) {
      results.failed++;
      results.errors.push({
        index: i,
        unique_id: auditData.unique_id,
        error: 'Exception during audit logging',
        details: error.message
      });
    }
  }

  // Update overall success status
  results.success = results.failed === 0;

  console.log(`[AUDIT-OPERATIONS] Bulk audit completed: ${results.successful}/${results.total} successful, session: ${sessionId}`);

  return results;
}

/**
 * Audit logging helper for Step 1 (Ingest) operations
 */
export async function auditIngestAction(unique_id, action, status, details = {}) {
  return await postToAuditLog({
    unique_id,
    process_id: details.process_id || 'step_1_ingest',
    status,
    actor: details.actor || 'ingest_system',
    source: details.source || 'data_ingest',
    action,
    step: 'step_1_ingest',
    sub_action: details.sub_action,
    record_type: details.record_type || 'company',
    record_id: details.record_id,
    after_values: details.after_values,
    processing_time_ms: details.processing_time_ms,
    confidence_score: details.confidence_score,
    session_id: details.session_id,
    correlation_id: details.correlation_id
  });
}

/**
 * Audit logging helper for Step 2 (Validate) operations
 */
export async function auditValidateAction(unique_id, action, status, details = {}) {
  return await postToAuditLog({
    unique_id,
    process_id: details.process_id || 'step_2_validate',
    status,
    actor: details.actor || 'validation_system',
    source: details.source || 'data_validator',
    action,
    step: 'step_2_validate',
    sub_action: details.sub_action,
    record_type: details.record_type || 'company',
    record_id: details.record_id,
    before_values: details.before_values,
    after_values: details.after_values,
    field_changes: details.field_changes,
    error_log: details.error_log,
    error_code: details.error_code,
    processing_time_ms: details.processing_time_ms,
    confidence_score: details.confidence_score,
    session_id: details.session_id,
    correlation_id: details.correlation_id
  });
}

/**
 * Audit logging helper for Step 2B (Enrich) operations
 */
export async function auditEnrichAction(unique_id, action, status, details = {}) {
  return await postToAuditLog({
    unique_id,
    process_id: details.process_id || 'step_2b_enrich',
    status,
    actor: details.actor || 'enrichment_system',
    source: details.source || 'data_enricher',
    action,
    step: 'step_2b_enrich',
    sub_action: details.sub_action,
    record_type: details.record_type || 'company',
    record_id: details.record_id,
    before_values: details.before_values,
    after_values: details.after_values,
    field_changes: details.field_changes,
    processing_time_ms: details.processing_time_ms,
    confidence_score: details.confidence_score,
    retry_count: details.retry_count,
    session_id: details.session_id,
    correlation_id: details.correlation_id
  });
}

/**
 * Audit logging helper for Step 3 (Adjust) operations
 */
export async function auditAdjustAction(unique_id, action, status, details = {}) {
  return await postToAuditLog({
    unique_id,
    process_id: details.process_id || 'step_3_adjust',
    status,
    actor: details.actor || 'human_adjuster',
    source: details.source || 'adjuster_console',
    action,
    step: 'step_3_adjust',
    sub_action: details.sub_action,
    record_type: details.record_type || 'company',
    record_id: details.record_id,
    before_values: details.before_values,
    after_values: details.after_values,
    field_changes: details.field_changes,
    processing_time_ms: details.processing_time_ms,
    confidence_score: 1.0, // Human adjustments get full confidence
    session_id: details.session_id,
    correlation_id: details.correlation_id
  });
}

/**
 * Audit logging helper for Step 4 (Promote) operations
 */
export async function auditPromoteAction(unique_id, action, status, details = {}) {
  return await postToAuditLog({
    unique_id,
    process_id: details.process_id || 'step_4_promote',
    status,
    actor: details.actor || 'promotion_system',
    source: details.source || 'promotion_engine',
    action,
    step: 'step_4_promote',
    sub_action: details.sub_action,
    record_type: details.record_type || 'company',
    record_id: details.record_id,
    before_values: details.before_values,
    after_values: details.after_values,
    processing_time_ms: details.processing_time_ms,
    confidence_score: details.confidence_score,
    session_id: details.session_id,
    correlation_id: details.correlation_id
  });
}

/**
 * Get audit trail for a specific record
 */
export async function getAuditTrail(unique_id, options = {}) {
  const bridge = options.bridge || new StandardComposioNeonBridge();

  try {
    const query = `
      SELECT
        audit_id,
        step,
        action,
        sub_action,
        status,
        actor,
        source,
        timestamp,
        processing_time_ms,
        confidence_score,
        field_changes,
        error_log,
        session_id
      FROM marketing.unified_audit_log
      WHERE unique_id = $1
      ORDER BY timestamp DESC
      LIMIT ${options.limit || 100}
    `;

    const result = await bridge.query(query, [unique_id]);

    return {
      success: true,
      unique_id,
      audit_trail: result.rows || [],
      total_entries: result.rows ? result.rows.length : 0
    };

  } catch (error) {
    console.error('[AUDIT-OPERATIONS] Failed to get audit trail:', error);
    return {
      success: false,
      error: 'Failed to retrieve audit trail',
      details: error.message
    };
  }
}

// Default export for convenience
export default {
  postToAuditLog,
  postBulkAuditLogs,
  validateAuditEntry,
  generateSessionId,
  calculateProcessingTime,
  auditIngestAction,
  auditValidateAction,
  auditEnrichAction,
  auditAdjustAction,
  auditPromoteAction,
  getAuditTrail
};