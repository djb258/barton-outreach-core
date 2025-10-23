/**
 * API Endpoint: /api/validate-step-2
 * Step 2 of Outreach Pipeline - Validator Agent
 * Routes to validation service for processing
 */

import { validateCompanies } from '../services/validator.js';

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({
      error: 'Method not allowed',
      message: 'Only POST requests are accepted',
      step: 2,
      process: 'validation',
      altitude: 10000,
      doctrine: 'STAMPED'
    });
  }

  try {
    // Extract filters from request body
    const { filters = {} } = req.body;
    const {
      batch_id = null,
      limit = 100,
      status = 'pending'
    } = filters;

    console.log(`[VALIDATE-API] Step 2 validation request received:`, {
      batch_id,
      limit,
      status,
      timestamp: new Date().toISOString(),
      user_agent: req.headers['user-agent']
    });

    // Input validation
    if (limit && (isNaN(limit) || limit < 1 || limit > 1000)) {
      return res.status(400).json({
        error: 'Invalid limit',
        message: 'Limit must be a number between 1 and 1000',
        step: 2,
        process: 'validation'
      });
    }

    if (status && !['pending', 'failed', 'all'].includes(status)) {
      return res.status(400).json({
        error: 'Invalid status',
        message: 'Status must be one of: pending, failed, all',
        step: 2,
        process: 'validation'
      });
    }

    // Call validation service
    const validationResult = await validateCompanies({
      batch_id,
      limit,
      status
    });

    console.log(`[VALIDATE-API] Step 2 validation completed successfully:`, {
      rows_validated: validationResult.rows_validated,
      rows_failed: validationResult.rows_failed,
      total_errors: validationResult.errors.length,
      processing_time: Date.now(),
      timestamp: new Date().toISOString()
    });

    return res.status(200).json({
      rows_validated: validationResult.rows_validated,
      rows_failed: validationResult.rows_failed,
      errors: validationResult.errors,
      step: 2,
      process: 'validation',
      altitude: 10000,
      doctrine: 'STAMPED',
      metadata: {
        total_processed: validationResult.rows_validated + validationResult.rows_failed,
        batch_id: batch_id,
        validation_timestamp: new Date().toISOString(),
        filters_applied: { batch_id, limit, status },
        mcp_tool: 'validate',
        source: 'intake.company_raw_intake'
      }
    });

  } catch (error) {
    console.error('[VALIDATE-API] Step 2 validation failed:', {
      error: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString(),
      request_id: req.headers['x-request-id'] || 'unknown'
    });

    return res.status(500).json({
      error: 'Validation process failed',
      message: error.message || 'Internal server error during validation',
      step: 2,
      process: 'validation',
      altitude: 10000,
      doctrine: 'STAMPED',
      metadata: {
        error_timestamp: new Date().toISOString(),
        error_code: 'VALIDATION_FAILURE'
      }
    });
  }
}