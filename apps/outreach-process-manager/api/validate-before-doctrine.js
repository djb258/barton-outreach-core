/**
 * API Endpoint: /api/validate
 * Step 2A Validator Agent - Core column validation for Barton Doctrine Pipeline
 * Validates intake.company_raw_intake using Standard Composio MCP Pattern
 */

import { validateCompanies } from '../services/validator.js';
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
        return await handleValidationProcess(req, res, bridge);

      case 'GET':
        return await handleValidationQuery(req, res, bridge);

      default:
        return res.status(405).json({
          error: 'Method not allowed',
          message: 'Only GET and POST requests are accepted',
          supported_methods: ['GET', 'POST'],
          altitude: 10000,
          doctrine: 'STAMPED'
        });
    }

  } catch (error) {
    console.error('[STEP-2A-API] Request failed:', error);
    return res.status(500).json({
      error: 'Internal server error',
      message: error.message,
      altitude: 10000,
      doctrine: 'STAMPED',
      process_step: '2A_validation'
    });
  }
}

/**
 * Handle POST requests - Run validation batch
 */
async function handleValidationProcess(req, res, bridge) {
  const {
    batchSize = 100,
    statusFilter = 'pending'
  } = req.body;

  console.log(`[STEP-2A-API] Processing validation batch (size: ${batchSize}, status: ${statusFilter})`);

  try {
    const result = await validateCompanies({
      batchSize: parseInt(batchSize) || 100,
      statusFilter: statusFilter
    });

    return res.status(200).json({
      success: true,
      action: 'validate_batch',
      data: result,
      metadata: {
        altitude: 10000,
        doctrine: 'STAMPED',
        process_step: '2A_validation',
        timestamp: new Date().toISOString()
      }
    });

  } catch (error) {
    console.error('[STEP-2A-API] Validation process failed:', error);
    return res.status(500).json({
      error: 'Validation process failed',
      message: error.message,
      action: 'validate_batch'
    });
  }
}

/**
 * Handle GET requests - Query validation status and results
 */
async function handleValidationQuery(req, res, bridge) {
  const {
    type = 'status',
    status,
    limit = 100,
    offset = 0
  } = req.query;

  console.log(`[STEP-2A-API] Querying ${type}`);

  try {
    switch (type) {
      case 'status':
        const statusData = await getValidationStatus(bridge);
        return res.status(200).json({
          success: true,
          type: 'status',
          data: statusData
        });

      case 'failed':
        const failedRecords = await getFailedValidations(bridge, {
          status,
          limit: parseInt(limit) || 100,
          offset: parseInt(offset) || 0
        });
        return res.status(200).json({
          success: true,
          type: 'failed',
          data: failedRecords
        });

      case 'records':
        const records = await getValidationRecords(bridge, {
          status,
          limit: parseInt(limit) || 100,
          offset: parseInt(offset) || 0
        });
        return res.status(200).json({
          success: true,
          type: 'records',
          data: records
        });

      default:
        return res.status(400).json({
          error: 'Invalid query type',
          message: `Query type '${type}' is not supported`,
          supported_types: ['status', 'failed', 'records']
        });
    }

  } catch (error) {
    console.error('[STEP-2A-API] Query request failed:', error);
    return res.status(500).json({
      error: 'Validation query failed',
      message: error.message,
      type: type
    });
  }
}

/**
 * Get validation status overview
 */
async function getValidationStatus(bridge) {
  const queries = {
    totalRecords: 'SELECT COUNT(*) as count FROM intake.company_raw_intake',
    pendingRecords: 'SELECT COUNT(*) as count FROM intake.company_raw_intake WHERE status = \'pending\'',
    validatedRecords: 'SELECT COUNT(*) as count FROM intake.company_raw_intake WHERE status = \'validated\'',
    failedRecords: 'SELECT COUNT(*) as count FROM intake.company_raw_intake WHERE status = \'failed\'',
    recentValidations: `
      SELECT
        DATE(created_at) as validation_date,
        status,
        COUNT(*) as count
      FROM intake.company_raw_intake
      WHERE created_at > NOW() - INTERVAL '7 days'
      GROUP BY DATE(created_at), status
      ORDER BY validation_date DESC
    `
  };

  try {
    const results = {};

    for (const [key, query] of Object.entries(queries)) {
      const result = await bridge.query(query);
      results[key] = result.rows;
    }

    return {
      overview: {
        total: results.totalRecords[0]?.count || 0,
        pending: results.pendingRecords[0]?.count || 0,
        validated: results.validatedRecords[0]?.count || 0,
        failed: results.failedRecords[0]?.count || 0
      },
      recent_activity: results.recentValidations,
      metadata: {
        generated_at: new Date().toISOString(),
        altitude: 10000,
        doctrine: 'STAMPED',
        process_step: '2A_validation'
      }
    };

  } catch (error) {
    console.error('[STEP-2A-API] Failed to get validation status:', error);
    throw new Error(`Failed to get validation status: ${error.message}`);
  }
}

/**
 * Get failed validation records with error details
 */
async function getFailedValidations(bridge, options = {}) {
  const { status, limit, offset } = options;

  let query = `
    SELECT
      vf.record_id,
      vf.error_type,
      vf.error_field,
      vf.raw_value,
      vf.expected_format,
      vf.attempts,
      vf.created_at,
      cri.company,
      cri.company_name_for_emails,
      cri.status as record_status
    FROM intake.validation_failed vf
    LEFT JOIN intake.company_raw_intake cri ON vf.record_id = cri.id
    WHERE 1=1
  `;

  const params = [];
  let paramIndex = 1;

  if (status) {
    query += ` AND vf.status = $${paramIndex}`;
    params.push(status);
    paramIndex++;
  }

  query += ` ORDER BY vf.created_at DESC LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
  params.push(limit, offset);

  try {
    const result = await bridge.query(query, params);

    return {
      failed_validations: result.rows,
      total: result.rows.length,
      limit: limit,
      offset: offset,
      metadata: {
        query_timestamp: new Date().toISOString(),
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    };

  } catch (error) {
    console.error('[STEP-2A-API] Failed to get failed validations:', error);
    throw new Error(`Failed to get failed validations: ${error.message}`);
  }
}

/**
 * Get validation records with optional status filter
 */
async function getValidationRecords(bridge, options = {}) {
  const { status, limit, offset } = options;

  let query = `
    SELECT
      id,
      company,
      company_name_for_emails,
      num_employees,
      industry,
      website,
      company_linkedin_url,
      company_city,
      company_state,
      company_country,
      status,
      created_at,
      updated_at
    FROM intake.company_raw_intake
    WHERE 1=1
  `;

  const params = [];
  let paramIndex = 1;

  if (status) {
    query += ` AND status = $${paramIndex}`;
    params.push(status);
    paramIndex++;
  }

  query += ` ORDER BY updated_at DESC, created_at DESC LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
  params.push(limit, offset);

  try {
    const result = await bridge.query(query, params);

    return {
      records: result.rows,
      total: result.rows.length,
      limit: limit,
      offset: offset,
      status_filter: status,
      metadata: {
        query_timestamp: new Date().toISOString(),
        altitude: 10000,
        doctrine: 'STAMPED',
        process_step: '2A_validation'
      }
    };

  } catch (error) {
    console.error('[STEP-2A-API] Failed to get validation records:', error);
    throw new Error(`Failed to get validation records: ${error.message}`);
  }
}