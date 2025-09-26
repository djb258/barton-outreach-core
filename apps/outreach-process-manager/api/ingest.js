/**
 * Doctrine Spec:
 * - Barton ID: 99.99.99.07.61757.251
 * - Altitude: 10000 (Execution Layer)
 * - Input: API request parameters
 * - Output: API response data
 * - MCP: Composio (Neon integrated)
 */
/**
 * API Endpoint: /api/ingest
 * Handles CSV data ingestion through Composio MCP → Neon
 * Middle layer orchestration for Outreach Process Manager
 */

import ComposioMCPClient from './lib/composio-mcp-client.js';

export default async function handler(req, res) {
  // Only accept POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({
      error: 'Method not allowed',
      message: 'Only POST requests are accepted'
    });
  }

  const mcpClient = new ComposioMCPClient();

  try {
    // Extract CSV rows from request body
    const { rows, metadata = {} } = req.body;

    if (!rows || !Array.isArray(rows) || rows.length === 0) {
      return res.status(400).json({
        error: 'Invalid request',
        message: 'Request must include an array of rows'
      });
    }

    // Initialize response tracking
    const response = {
      rows_ingested: 0,
      rows_validated: 0,
      rows_failed: 0,
      error_log: [],
      step_unique_ids: [],
      barton_doctrine: {
        process_id: mcpClient.generateProcessId(),
        altitude: 'middle_layer',
        timestamp: new Date().toISOString()
      }
    };

    // Step 1: Insert rows into raw_intake table through Composio MCP
    console.log(`[INGEST] Processing ${rows.length} rows for ingestion`);

    try {
      const insertResult = await mcpClient.insertRows(
        'marketing.company_raw_intake',
        rows
      );

      if (insertResult.success) {
        response.rows_ingested = rows.length;

        // Extract unique IDs from inserted rows
        if (insertResult.data && insertResult.data.rows) {
          response.step_unique_ids = insertResult.data.rows.map(r => r.unique_id);
        }

        console.log(`[INGEST] Successfully ingested ${response.rows_ingested} rows`);
      } else {
        throw new Error('Failed to insert rows through MCP');
      }
    } catch (insertError) {
      console.error('[INGEST] Insert error:', insertError);
      response.error_log.push({
        step: 'insert',
        error: insertError.message,
        timestamp: new Date().toISOString()
      });
      response.rows_failed = rows.length;
    }

    // Step 2: Validate schema against STAMPED doctrine
    if (response.rows_ingested > 0) {
      console.log('[INGEST] Validating against STAMPED doctrine');

      try {
        const validationResult = await mcpClient.validateSchema(
          'marketing.company_raw_intake',
          rows
        );

        if (validationResult.success) {
          // Count validated vs failed rows
          const validationData = validationResult.data || {};
          const errors = mcpClient.formatValidationErrors(validationData);

          if (errors.length === 0) {
            response.rows_validated = response.rows_ingested;
            console.log('[INGEST] All rows passed validation');
          } else {
            // Calculate validated rows (those without errors)
            const rowsWithErrors = new Set(errors.map(e => e.row));
            response.rows_validated = response.rows_ingested - rowsWithErrors.size;
            response.rows_failed = rowsWithErrors.size;

            // Add validation errors to error log
            errors.forEach(error => {
              response.error_log.push({
                step: 'validation',
                row: error.row,
                field: error.field,
                message: error.message,
                severity: error.severity,
                doctrine_violation: error.doctrine_violation,
                timestamp: new Date().toISOString()
              });
            });

            console.log(`[INGEST] Validation complete: ${response.rows_validated} passed, ${response.rows_failed} failed`);
          }
        } else {
          throw new Error('Schema validation failed');
        }
      } catch (validationError) {
        console.error('[INGEST] Validation error:', validationError);
        response.error_log.push({
          step: 'validation',
          error: validationError.message,
          timestamp: new Date().toISOString()
        });
      }
    }

    // Step 3: Update metadata for tracking
    response.barton_doctrine.completion_timestamp = new Date().toISOString();
    response.barton_doctrine.total_processing_time_ms =
      new Date(response.barton_doctrine.completion_timestamp) -
      new Date(response.barton_doctrine.timestamp);

    // Return response to Rocket.new UI
    console.log('[INGEST] Process complete, returning response');

    return res.status(200).json({
      success: response.rows_ingested > 0,
      ...response
    });

  } catch (error) {
    console.error('[INGEST] Critical error:', error);

    return res.status(500).json({
      success: false,
      error: 'Internal server error',
      message: error.message,
      rows_ingested: 0,
      rows_validated: 0,
      rows_failed: req.body.rows?.length || 0,
      error_log: [{
        step: 'critical',
        error: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString()
      }],
      step_unique_ids: [],
      barton_doctrine: {
        process_id: new Date().getTime().toString(),
        altitude: 'middle_layer_error',
        timestamp: new Date().toISOString()
      }
    });
  }
}