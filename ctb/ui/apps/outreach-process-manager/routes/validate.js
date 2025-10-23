/**
 * Express Route: /api/validate
 * Step 2 of Outreach Pipeline - Validator Agent
 * Validates company data from intake.company_raw_intake via Composio MCP
 */

import { validateCompanies } from '../services/validator.js';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({
      error: 'Method not allowed',
      message: 'Only POST requests are accepted',
      step: 2,
      process: 'validation'
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

    console.log(`[VALIDATOR] Step 2 validation started:`, {
      batch_id,
      limit,
      status,
      timestamp: new Date().toISOString()
    });

    // Call validation service
    const validationResult = await validateCompanies({
      batch_id,
      limit,
      status
    });

    console.log(`[VALIDATOR] Step 2 validation completed:`, {
      rows_validated: validationResult.rows_validated,
      rows_failed: validationResult.rows_failed,
      total_errors: validationResult.errors.length,
      timestamp: new Date().toISOString()
    });

    return res.status(200).json({
      rows_validated: validationResult.rows_validated,
      rows_failed: validationResult.rows_failed,
      errors: validationResult.errors,
      step: 2,
      process: 'validation',
      metadata: {
        total_processed: validationResult.rows_validated + validationResult.rows_failed,
        batch_id: batch_id,
        validation_timestamp: new Date().toISOString(),
        filters_applied: { batch_id, limit, status }
      }
    });

  } catch (error) {
    console.error('[VALIDATOR] Step 2 validation failed:', {
      error: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    });

    return res.status(500).json({
      error: 'Validation process failed',
      message: error.message || 'Internal server error during validation',
      step: 2,
      process: 'validation'
    });
  }
}