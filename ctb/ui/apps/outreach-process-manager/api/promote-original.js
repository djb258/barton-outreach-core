/**
 * API Endpoint: /api/promote
 * Handles data promotion from raw_intake to production tables
 * Triggers slot creation and ensures data integrity through Composio MCP
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
    // Extract filter parameters from request body
    const {
      filter = { validated: true },
      sourceTable = 'marketing.company_raw_intake',
      targetTable = 'marketing.company',
      limit = 1000,
      metadata = {}
    } = req.body;

    console.log(`[PROMOTE] Starting promotion from ${sourceTable} to ${targetTable}`);
    console.log(`[PROMOTE] Filter:`, filter);

    // Initialize response structure
    const response = {
      rows_promoted: 0,
      promotion_timestamp: new Date().toISOString(),
      promoted_unique_ids: [],
      slot_creation_triggered: false,
      barton_doctrine: {
        process_id: mcpClient.generateProcessId(),
        altitude: 'promotion_layer',
        source_altitude: 'raw_intake',
        target_altitude: 'production',
        timestamp: new Date().toISOString()
      },
      promotion_details: {
        source_table: sourceTable,
        target_table: targetTable,
        filter_applied: filter
      }
    };

    // Step 1: Query eligible rows for promotion
    console.log('[PROMOTE] Querying eligible rows for promotion');

    let eligibleRows = [];
    try {
      const queryResult = await mcpClient.queryRows(
        sourceTable,
        filter,
        limit
      );

      if (queryResult.success && queryResult.data) {
        eligibleRows = queryResult.data.rows || [];
        console.log(`[PROMOTE] Found ${eligibleRows.length} eligible rows`);
      } else {
        console.log('[PROMOTE] No eligible rows found');
        return res.status(200).json({
          success: true,
          message: 'No rows eligible for promotion',
          ...response
        });
      }
    } catch (queryError) {
      console.error('[PROMOTE] Query error:', queryError);
      throw new Error(`Failed to query eligible rows: ${queryError.message}`);
    }

    // Step 2: Promote rows through Composio MCP
    if (eligibleRows.length > 0) {
      console.log(`[PROMOTE] Promoting ${eligibleRows.length} rows`);

      try {
        const promoteResult = await mcpClient.promoteRows(
          sourceTable,
          targetTable,
          filter
        );

        if (promoteResult.success) {
          // Extract promoted row information
          const promotedData = promoteResult.data || {};

          response.rows_promoted = promotedData.rowsPromoted || eligibleRows.length;
          response.promoted_unique_ids = promotedData.promotedIds ||
            eligibleRows.map(row => row.unique_id || mcpClient.generateUniqueId());

          // Check if slot creation was triggered
          response.slot_creation_triggered = promotedData.slotCreationTriggered || false;

          console.log(`[PROMOTE] Successfully promoted ${response.rows_promoted} rows`);

          // Step 3: Trigger slot creation if configured
          if (response.slot_creation_triggered) {
            console.log('[PROMOTE] Slot creation triggers activated');

            response.slot_details = {
              slots_created: promotedData.slotsCreated || response.rows_promoted,
              slot_type: 'company_slot',
              slot_status: 'active',
              creation_timestamp: new Date().toISOString()
            };
          }

          // Step 4: Update Barton Doctrine metadata
          response.barton_doctrine.promotion_complete = true;
          response.barton_doctrine.completion_timestamp = new Date().toISOString();
          response.barton_doctrine.total_processing_time_ms =
            new Date(response.barton_doctrine.completion_timestamp) -
            new Date(response.barton_doctrine.timestamp);

          // Step 5: Add audit trail
          response.audit_trail = {
            promoted_by: 'middle_layer_orchestration',
            promotion_method: 'composio_mcp_neon',
            source_filter: filter,
            promotion_timestamp: response.promotion_timestamp,
            verification_status: 'pending_verification'
          };

        } else {
          throw new Error('Promotion failed through MCP');
        }
      } catch (promoteError) {
        console.error('[PROMOTE] Promotion error:', promoteError);
        throw new Error(`Failed to promote rows: ${promoteError.message}`);
      }
    }

    // Step 6: Verify promotion success (optional verification step)
    if (response.rows_promoted > 0) {
      console.log('[PROMOTE] Verifying promotion success');

      try {
        const verifyResult = await mcpClient.queryRows(
          targetTable,
          { unique_id: { $in: response.promoted_unique_ids.slice(0, 10) } },
          10
        );

        if (verifyResult.success && verifyResult.data) {
          const verifiedCount = verifyResult.data.rows?.length || 0;
          response.verification = {
            verified: verifiedCount > 0,
            sample_verified_count: verifiedCount,
            verification_timestamp: new Date().toISOString()
          };

          if (response.audit_trail) {
            response.audit_trail.verification_status =
              verifiedCount > 0 ? 'verified' : 'verification_failed';
          }
        }
      } catch (verifyError) {
        console.error('[PROMOTE] Verification error (non-critical):', verifyError);
        // Non-critical error, continue
      }
    }

    // Return success response
    console.log('[PROMOTE] Process complete, returning response');

    return res.status(200).json({
      success: response.rows_promoted > 0,
      ...response
    });

  } catch (error) {
    console.error('[PROMOTE] Critical error:', error);

    return res.status(500).json({
      success: false,
      error: 'Internal server error',
      message: error.message,
      rows_promoted: 0,
      promotion_timestamp: new Date().toISOString(),
      promoted_unique_ids: [],
      slot_creation_triggered: false,
      barton_doctrine: {
        process_id: new Date().getTime().toString(),
        altitude: 'promotion_layer_error',
        timestamp: new Date().toISOString(),
        error: error.message
      }
    });
  }
}