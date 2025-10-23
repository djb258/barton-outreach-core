/**
 * API Endpoint: /api/enrichment
 * Enrichment Router API - Step 2B of Barton Doctrine Pipeline
 * Handles batch processing of validation failures through handler pipeline
 * Uses Standard Composio MCP Pattern for all database operations
 */

import { processEnrichmentBatch, getEnrichmentStatistics } from '../services/enrichmentRouter.js';
import StandardComposioNeonBridge from './lib/standard-composio-neon-bridge.js';

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') return res.status(200).end();

  try {
    const bridge = new StandardComposioNeonBridge();

    switch (req.method) {
      case 'POST':
        return await handleEnrichmentProcess(req, res, bridge);

      case 'GET':
        return await handleEnrichmentQuery(req, res, bridge);

      default:
        return res.status(405).json({
          error: 'Method not allowed',
          message: 'Only GET and POST requests are accepted',
          supported_methods: ['GET', 'POST']
        });
    }

  } catch (error) {
    console.error('[ENRICHMENT-API] Request failed:', error);
    return res.status(500).json({
      error: 'Internal server error',
      message: error.message,
      altitude: 10000,
      doctrine: 'STAMPED'
    });
  }
}

/**
 * Handle POST requests - Process enrichment batches
 */
async function handleEnrichmentProcess(req, res, bridge) {
  const {
    action = 'process_batch',
    batchSize = 50,
    schemas = ['intake'],
    maxRetries = 3,
    handlerTimeout = 30000,
    priorityLevel = 'normal'
  } = req.body;

  console.log(`[ENRICHMENT-API] Processing ${action} request with batch size ${batchSize}`);

  try {
    switch (action) {
      case 'process_batch':
        const result = await processEnrichmentBatch({
          batchSize: parseInt(batchSize) || 50,
          schemas: Array.isArray(schemas) ? schemas : [schemas],
          maxRetries: parseInt(maxRetries) || 3,
          handlerTimeout: parseInt(handlerTimeout) || 30000,
          priorityLevel
        });

        return res.status(200).json({
          success: true,
          action: 'process_batch',
          data: result,
          metadata: {
            altitude: 10000,
            doctrine: 'STAMPED',
            process_id: 'enrichment_router_step_2b',
            timestamp: new Date().toISOString()
          }
        });

      case 'process_specific':
        return await handleSpecificRecordProcess(req, res, bridge);

      case 'retry_failed':
        return await handleRetryFailedRecords(req, res, bridge);

      default:
        return res.status(400).json({
          error: 'Invalid action',
          message: `Action '${action}' is not supported`,
          supported_actions: ['process_batch', 'process_specific', 'retry_failed']
        });
    }

  } catch (error) {
    console.error('[ENRICHMENT-API] Process request failed:', error);
    return res.status(500).json({
      error: 'Enrichment processing failed',
      message: error.message,
      action: action
    });
  }
}

/**
 * Handle GET requests - Query enrichment data and statistics
 */
async function handleEnrichmentQuery(req, res, bridge) {
  const {
    type = 'statistics',
    record_id,
    error_type,
    status,
    limit = 100,
    offset = 0
  } = req.query;

  console.log(`[ENRICHMENT-API] Querying ${type}`);

  try {
    switch (type) {
      case 'statistics':
        const stats = await getEnrichmentStatistics(bridge);
        return res.status(200).json({
          success: true,
          type: 'statistics',
          data: stats,
          metadata: {
            altitude: 10000,
            doctrine: 'STAMPED'
          }
        });

      case 'failures':
        const failures = await getValidationFailures(bridge, {
          error_type,
          status,
          limit: parseInt(limit) || 100,
          offset: parseInt(offset) || 0
        });
        return res.status(200).json({
          success: true,
          type: 'failures',
          data: failures
        });

      case 'audit_log':
        const auditLog = await getAuditLog(bridge, {
          record_id: record_id ? parseInt(record_id) : null,
          limit: parseInt(limit) || 100,
          offset: parseInt(offset) || 0
        });
        return res.status(200).json({
          success: true,
          type: 'audit_log',
          data: auditLog
        });

      case 'human_queue':
        const humanQueue = await getHumanFirebreakQueue(bridge, {
          status,
          limit: parseInt(limit) || 100,
          offset: parseInt(offset) || 0
        });
        return res.status(200).json({
          success: true,
          type: 'human_queue',
          data: humanQueue
        });

      case 'handlers':
        const handlers = await getHandlerRegistry(bridge);
        return res.status(200).json({
          success: true,
          type: 'handlers',
          data: handlers
        });

      default:
        return res.status(400).json({
          error: 'Invalid query type',
          message: `Query type '${type}' is not supported`,
          supported_types: ['statistics', 'failures', 'audit_log', 'human_queue', 'handlers']
        });
    }

  } catch (error) {
    console.error('[ENRICHMENT-API] Query request failed:', error);
    return res.status(500).json({
      error: 'Enrichment query failed',
      message: error.message,
      type: type
    });
  }
}

/**
 * Process specific records by ID
 */
async function handleSpecificRecordProcess(req, res, bridge) {
  const { record_ids, force_retry = false } = req.body;

  if (!record_ids || !Array.isArray(record_ids)) {
    return res.status(400).json({
      error: 'Invalid input',
      message: 'record_ids must be provided as an array'
    });
  }

  // Fetch specific validation failures
  const query = `
    SELECT * FROM intake.validation_failed
    WHERE record_id = ANY($1)
    ${force_retry ? '' : 'AND status = \'pending\''}
  `;

  const failures = await bridge.query(query, [record_ids]);

  if (failures.rows.length === 0) {
    return res.status(404).json({
      error: 'No records found',
      message: 'No matching validation failures found for the provided record IDs'
    });
  }

  // Process each failure individually
  const results = [];
  for (const failure of failures.rows) {
    try {
      const result = await processEnrichmentBatch({
        batchSize: 1,
        specificRecord: failure
      });
      results.push(result);
    } catch (error) {
      results.push({
        record_id: failure.record_id,
        success: false,
        error: error.message
      });
    }
  }

  return res.status(200).json({
    success: true,
    action: 'process_specific',
    data: {
      processed: results.length,
      results: results
    }
  });
}

/**
 * Retry failed enrichment records
 */
async function handleRetryFailedRecords(req, res, bridge) {
  const { max_attempts = 3, error_types = [], batch_size = 25 } = req.body;

  // Reset failed records for retry
  const resetQuery = `
    UPDATE intake.validation_failed
    SET status = 'pending', attempts = 0
    WHERE status = 'pending'
      AND attempts >= $1
      ${error_types.length ? 'AND error_type = ANY($2)' : ''}
    RETURNING id, record_id, error_type
  `;

  const params = [max_attempts];
  if (error_types.length) params.push(error_types);

  const resetResult = await bridge.query(resetQuery, params);

  if (resetResult.rows.length === 0) {
    return res.status(200).json({
      success: true,
      action: 'retry_failed',
      message: 'No failed records found to retry',
      data: { reset_count: 0, processed: 0 }
    });
  }

  console.log(`[ENRICHMENT-API] Reset ${resetResult.rows.length} failed records for retry`);

  // Process the reset records
  const processResult = await processEnrichmentBatch({
    batchSize: parseInt(batch_size) || 25,
    maxRetries: 1 // Don't retry again immediately
  });

  return res.status(200).json({
    success: true,
    action: 'retry_failed',
    data: {
      reset_count: resetResult.rows.length,
      ...processResult
    }
  });
}

/**
 * Get validation failures with filters
 */
async function getValidationFailures(bridge, options = {}) {
  const { error_type, status, limit, offset } = options;

  let query = `
    SELECT
      vf.*,
      cri.company_name,
      cri.industry,
      cri.website_url
    FROM intake.validation_failed vf
    LEFT JOIN intake.company_raw_intake cri ON vf.record_id = cri.id
    WHERE 1=1
  `;

  const params = [];
  let paramIndex = 1;

  if (error_type) {
    query += ` AND vf.error_type = $${paramIndex}`;
    params.push(error_type);
    paramIndex++;
  }

  if (status) {
    query += ` AND vf.status = $${paramIndex}`;
    params.push(status);
    paramIndex++;
  }

  query += ` ORDER BY vf.created_at DESC LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
  params.push(limit, offset);

  const result = await bridge.query(query, params);

  return {
    failures: result.rows,
    total: result.rows.length,
    limit: limit,
    offset: offset
  };
}

/**
 * Get enrichment audit log
 */
async function getAuditLog(bridge, options = {}) {
  const { record_id, limit, offset } = options;

  let query = `
    SELECT
      val.*,
      vf.error_type,
      vf.error_field,
      cri.company_name
    FROM intake.validation_audit_log val
    LEFT JOIN intake.validation_failed vf ON val.validation_failed_id = vf.id
    LEFT JOIN intake.company_raw_intake cri ON val.record_id = cri.id
    WHERE 1=1
  `;

  const params = [];
  let paramIndex = 1;

  if (record_id) {
    query += ` AND val.record_id = $${paramIndex}`;
    params.push(record_id);
    paramIndex++;
  }

  query += ` ORDER BY val.timestamp DESC LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
  params.push(limit, offset);

  const result = await bridge.query(query, params);

  return {
    audit_entries: result.rows,
    total: result.rows.length,
    limit: limit,
    offset: offset
  };
}

/**
 * Get human firebreak queue
 */
async function getHumanFirebreakQueue(bridge, options = {}) {
  const { status, limit, offset } = options;

  let query = `
    SELECT
      hfq.*,
      cri.company_name,
      cri.industry
    FROM intake.human_firebreak_queue hfq
    LEFT JOIN intake.company_raw_intake cri ON hfq.record_id = cri.id
    WHERE 1=1
  `;

  const params = [];
  let paramIndex = 1;

  if (status) {
    query += ` AND hfq.status = $${paramIndex}`;
    params.push(status);
    paramIndex++;
  }

  query += ` ORDER BY hfq.priority DESC, hfq.created_at ASC LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
  params.push(limit, offset);

  const result = await bridge.query(query, params);

  return {
    queue_entries: result.rows,
    total: result.rows.length,
    limit: limit,
    offset: offset
  };
}

/**
 * Get handler registry information
 */
async function getHandlerRegistry(bridge) {
  const query = `
    SELECT * FROM intake.enrichment_handler_registry
    WHERE enabled = true
    ORDER BY priority_order ASC, handler_name ASC
  `;

  const result = await bridge.query(query);

  return {
    handlers: result.rows,
    total: result.rows.length
  };
}