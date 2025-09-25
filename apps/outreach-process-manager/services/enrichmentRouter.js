/**
 * Enrichment Router Service
 * Step 2B of Barton Doctrine Pipeline - Main Orchestrator
 * Routes validation failures to appropriate handlers: Auto-Fix → Apify → Abacus → Human
 * Uses Standard Composio MCP Pattern for all database operations
 */

import StandardComposioNeonBridge from '../api/lib/standard-composio-neon-bridge.js';
import { processAutoFix, getAutoFixCapabilities } from './autoFixHandler.js';
import { processApifyEnrichment, getApifyCapabilities } from './apifyHandler.js';
import { processAbacusEscalation, shouldEscalateToAbacus, getAbacusCapabilities } from './abacusHandler.js';

/**
 * Main enrichment router - processes batches of validation failures
 */
export async function processEnrichmentBatch(options = {}) {
  const {
    batchSize = 50,
    schemas = ['intake'],
    maxRetries = 3,
    handlerTimeout = 30000,
    priorityLevel = 'normal'
  } = options;

  const bridge = new StandardComposioNeonBridge();
  const startTime = Date.now();

  try {
    console.log(`[ENRICHMENT-ROUTER] Starting batch processing (size: ${batchSize})`);

    // Fetch pending validation failures
    const validationFailures = await fetchPendingFailures(bridge, batchSize, schemas);

    if (validationFailures.length === 0) {
      console.log('[ENRICHMENT-ROUTER] No pending validation failures found');
      return {
        success: true,
        processed: 0,
        message: 'No pending validation failures',
        processingTime: Date.now() - startTime
      };
    }

    console.log(`[ENRICHMENT-ROUTER] Found ${validationFailures.length} pending failures`);

    // Process each validation failure
    const results = {
      total: validationFailures.length,
      successful: 0,
      failed: 0,
      escalated: 0,
      details: []
    };

    for (const failure of validationFailures) {
      try {
        const result = await processValidationFailure(bridge, failure, { maxRetries, handlerTimeout });

        results.details.push({
          record_id: failure.record_id,
          error_type: failure.error_type,
          ...result
        });

        if (result.success) {
          results.successful++;
        } else if (result.escalated) {
          results.escalated++;
        } else {
          results.failed++;
        }

      } catch (error) {
        console.error(`[ENRICHMENT-ROUTER] Failed to process record ${failure.record_id}:`, error);
        results.failed++;
        results.details.push({
          record_id: failure.record_id,
          error_type: failure.error_type,
          success: false,
          error: error.message
        });
      }
    }

    const processingTime = Date.now() - startTime;

    console.log(`[ENRICHMENT-ROUTER] Batch complete: ${results.successful} success, ${results.failed} failed, ${results.escalated} escalated (${processingTime}ms)`);

    return {
      success: true,
      ...results,
      processingTime,
      metadata: {
        batch_size: batchSize,
        schemas: schemas,
        altitude: 10000,
        doctrine: 'STAMPED',
        timestamp: new Date().toISOString()
      }
    };

  } catch (error) {
    console.error('[ENRICHMENT-ROUTER] Batch processing failed:', error);
    throw new Error(`Enrichment batch processing failed: ${error.message}`);
  }
}

/**
 * Process a single validation failure through the handler pipeline
 */
async function processValidationFailure(bridge, validationFailure, options = {}) {
  const { maxRetries, handlerTimeout } = options;
  const { record_id, error_type, error_field, raw_value } = validationFailure;

  console.log(`[ENRICHMENT-ROUTER] Processing ${error_type} for record ${record_id}`);

  // Fetch company context data for enrichment
  const companyData = await fetchCompanyContext(bridge, record_id);

  // Determine handler execution order
  const handlerPipeline = determineHandlerPipeline(validationFailure);

  for (const handlerType of handlerPipeline) {
    try {
      console.log(`[ENRICHMENT-ROUTER] Trying ${handlerType} handler for record ${record_id}`);

      let handlerResult;
      let processingContext = {
        previousHandlers: handlerPipeline.slice(0, handlerPipeline.indexOf(handlerType)),
        currentAttempt: validationFailure.attempts + 1
      };

      // Call appropriate handler
      switch (handlerType) {
        case 'auto_fix':
          handlerResult = await processAutoFix(validationFailure);
          break;

        case 'apify':
          handlerResult = await processApifyEnrichment(validationFailure, companyData);
          break;

        case 'abacus':
          handlerResult = await processAbacusEscalation(validationFailure, companyData, processingContext);
          break;

        default:
          throw new Error(`Unknown handler type: ${handlerType}`);
      }

      // Log attempt to audit log
      await logEnrichmentAttempt(bridge, validationFailure, handlerType, handlerResult);

      // Update validation failure record
      await updateValidationFailure(bridge, validationFailure, handlerType, handlerResult);

      // If successful, validate and potentially re-run validator
      if (handlerResult.success && handlerResult.fixedValue) {
        const validationResult = await validateEnrichedData(bridge, validationFailure, handlerResult.fixedValue);

        if (validationResult.valid) {
          // Mark as fixed and update main record
          await markValidationFixed(bridge, validationFailure, handlerResult);

          console.log(`[ENRICHMENT-ROUTER] Successfully fixed ${error_type} for record ${record_id} using ${handlerType}`);

          return {
            success: true,
            handler: handlerType,
            originalValue: raw_value,
            fixedValue: handlerResult.fixedValue,
            confidence: handlerResult.confidence,
            metadata: handlerResult.metadata
          };
        } else {
          console.log(`[ENRICHMENT-ROUTER] Fixed value still fails validation for record ${record_id}`);
        }
      }

    } catch (error) {
      console.error(`[ENRICHMENT-ROUTER] ${handlerType} handler failed for record ${record_id}:`, error);

      // Log failed attempt
      await logEnrichmentAttempt(bridge, validationFailure, handlerType, {
        success: false,
        error: error.message,
        processingTime: 0
      });
    }
  }

  // All handlers failed - escalate to human
  console.log(`[ENRICHMENT-ROUTER] All handlers failed for record ${record_id}, escalating to human review`);

  const escalationResult = await escalateToHumanReview(bridge, validationFailure, {
    handlersAttempted: handlerPipeline,
    reason: 'All automated handlers failed'
  });

  return {
    success: false,
    escalated: true,
    escalation_id: escalationResult.escalation_id,
    reason: 'Escalated to human review'
  };
}

/**
 * Fetch pending validation failures from database
 */
async function fetchPendingFailures(bridge, batchSize, schemas) {
  const schemaFilter = schemas.map(s => `'${s}'`).join(',');

  const query = `
    SELECT vf.*, cri.company_name
    FROM intake.validation_failed vf
    LEFT JOIN intake.company_raw_intake cri ON vf.record_id = cri.id
    WHERE vf.status = 'pending'
      AND vf.attempts < 3
    ORDER BY vf.created_at ASC
    LIMIT $1
  `;

  try {
    const result = await bridge.query(query, [batchSize]);
    return result.rows || [];
  } catch (error) {
    console.error('[ENRICHMENT-ROUTER] Failed to fetch pending failures:', error);
    throw new Error(`Failed to fetch pending validation failures: ${error.message}`);
  }
}

/**
 * Fetch company context data for enrichment
 */
async function fetchCompanyContext(bridge, recordId) {
  const query = `
    SELECT
      company_name, company, industry, website_url, website,
      company_city, company_state, company_address,
      num_employees, founded_year, company_linkedin_url,
      company_phone, annual_revenue
    FROM intake.company_raw_intake
    WHERE id = $1
  `;

  try {
    const result = await bridge.query(query, [recordId]);
    return result.rows?.[0] || {};
  } catch (error) {
    console.error(`[ENRICHMENT-ROUTER] Failed to fetch company context for record ${recordId}:`, error);
    return {};
  }
}

/**
 * Determine which handlers to try and in what order
 */
function determineHandlerPipeline(validationFailure) {
  const { error_type, attempts } = validationFailure;

  // Get handler capabilities
  const autoFixCaps = getAutoFixCapabilities();
  const apifyCaps = getApifyCapabilities();

  let pipeline = [];

  // Auto-fix first for supported error types (fast and free)
  if (autoFixCaps.supported_error_types.includes(error_type)) {
    pipeline.push('auto_fix');
  }

  // Apify second for data discovery needs
  if (apifyCaps.supported_error_types.includes(error_type)) {
    pipeline.push('apify');
  }

  // Abacus for complex cases or after multiple failures
  if (attempts >= 1 || shouldEscalateToAbacus(validationFailure).shouldEscalate) {
    pipeline.push('abacus');
  }

  // If no specific handlers, try them all in order
  if (pipeline.length === 0) {
    pipeline = ['auto_fix', 'apify', 'abacus'];
  }

  return pipeline;
}

/**
 * Log enrichment attempt to audit log
 */
async function logEnrichmentAttempt(bridge, validationFailure, handlerType, handlerResult) {
  const query = `
    INSERT INTO intake.validation_audit_log (
      record_id, error_type, error_field, attempt_source, result,
      original_value, enriched_value, details, processing_time_ms,
      confidence_score, validation_failed_id, barton_metadata
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
  `;

  const params = [
    validationFailure.record_id,
    validationFailure.error_type,
    validationFailure.error_field,
    handlerType,
    handlerResult.success ? 'success' : 'fail',
    validationFailure.raw_value,
    handlerResult.fixedValue || handlerResult.enrichedValue,
    JSON.stringify({
      method: handlerResult.method,
      confidence: handlerResult.confidence,
      error: handlerResult.error,
      metadata: handlerResult.metadata
    }),
    handlerResult.processingTime,
    handlerResult.confidence,
    validationFailure.id,
    JSON.stringify({
      altitude: 10000,
      doctrine: 'STAMPED',
      process_id: 'enrichment_router_step_2b',
      handler_type: handlerType
    })
  ];

  try {
    await bridge.query(query, params);
  } catch (error) {
    console.error('[ENRICHMENT-ROUTER] Failed to log enrichment attempt:', error);
  }
}

/**
 * Update validation failure record with attempt details
 */
async function updateValidationFailure(bridge, validationFailure, handlerType, handlerResult) {
  const query = `
    UPDATE intake.validation_failed
    SET
      attempts = attempts + 1,
      last_attempt_source = $2,
      last_attempt_at = NOW(),
      metadata = metadata || $3
    WHERE id = $1
  `;

  const metadata = {
    [`${handlerType}_attempt`]: {
      timestamp: new Date().toISOString(),
      success: handlerResult.success,
      confidence: handlerResult.confidence,
      processing_time: handlerResult.processingTime
    }
  };

  try {
    await bridge.query(query, [validationFailure.id, handlerType, JSON.stringify(metadata)]);
  } catch (error) {
    console.error('[ENRICHMENT-ROUTER] Failed to update validation failure:', error);
  }
}

/**
 * Validate enriched data meets requirements
 */
async function validateEnrichedData(bridge, validationFailure, enrichedValue) {
  // Simple validation - in production this would call the main validator
  if (!enrichedValue || enrichedValue.toString().trim() === '') {
    return { valid: false, reason: 'Empty value' };
  }

  // Field-specific validation
  const { error_field, error_type } = validationFailure;

  if (error_field === 'company_state' && enrichedValue.length !== 2) {
    return { valid: false, reason: 'State code must be 2 characters' };
  }

  if (error_field.includes('url') && !enrichedValue.startsWith('http')) {
    return { valid: false, reason: 'URL must start with http/https' };
  }

  return { valid: true };
}

/**
 * Mark validation as fixed and update main record
 */
async function markValidationFixed(bridge, validationFailure, handlerResult) {
  const updateValidation = `
    UPDATE intake.validation_failed
    SET
      status = 'fixed',
      fixed_value = $2,
      metadata = metadata || $3
    WHERE id = $1
  `;

  const updateMainRecord = `
    UPDATE intake.company_raw_intake
    SET ${validationFailure.error_field} = $2
    WHERE id = $1
  `;

  try {
    await bridge.query(updateValidation, [
      validationFailure.id,
      handlerResult.fixedValue,
      JSON.stringify({
        fixed_by: handlerResult.metadata?.handler || 'enrichment_router',
        fixed_at: new Date().toISOString(),
        confidence: handlerResult.confidence
      })
    ]);

    await bridge.query(updateMainRecord, [
      validationFailure.record_id,
      handlerResult.fixedValue
    ]);

  } catch (error) {
    console.error('[ENRICHMENT-ROUTER] Failed to mark validation as fixed:', error);
  }
}

/**
 * Escalate to human firebreak queue
 */
async function escalateToHumanReview(bridge, validationFailure, escalationContext) {
  const query = `
    INSERT INTO intake.human_firebreak_queue (
      record_id, error_type, error_field, raw_value,
      attempts_made, handlers_tried, escalation_reason,
      priority, validation_failed_id, metadata
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    RETURNING id
  `;

  const params = [
    validationFailure.record_id,
    validationFailure.error_type,
    validationFailure.error_field,
    validationFailure.raw_value,
    validationFailure.attempts,
    escalationContext.handlersAttempted,
    escalationContext.reason,
    'normal',
    validationFailure.id,
    JSON.stringify({
      escalated_at: new Date().toISOString(),
      altitude: 10000,
      doctrine: 'STAMPED'
    })
  ];

  try {
    const result = await bridge.query(query, params);
    const escalationId = result.rows[0].id;

    // Update validation failure status
    await bridge.query(
      'UPDATE intake.validation_failed SET status = $1 WHERE id = $2',
      ['escalated', validationFailure.id]
    );

    return { escalation_id: escalationId };
  } catch (error) {
    console.error('[ENRICHMENT-ROUTER] Failed to escalate to human review:', error);
    throw error;
  }
}

/**
 * Get enrichment router statistics
 */
export async function getEnrichmentStatistics(bridge) {
  const queries = {
    totalFailures: 'SELECT COUNT(*) as count FROM intake.validation_failed',
    pendingFailures: 'SELECT COUNT(*) as count FROM intake.validation_failed WHERE status = \'pending\'',
    fixedFailures: 'SELECT COUNT(*) as count FROM intake.validation_failed WHERE status = \'fixed\'',
    escalatedFailures: 'SELECT COUNT(*) as count FROM intake.validation_failed WHERE status = \'escalated\'',
    recentAttempts: `
      SELECT attempt_source, result, COUNT(*) as count
      FROM intake.validation_audit_log
      WHERE timestamp > NOW() - INTERVAL '24 hours'
      GROUP BY attempt_source, result
    `,
    handlerSuccess: `
      SELECT
        attempt_source,
        COUNT(*) as total_attempts,
        COUNT(*) FILTER (WHERE result = 'success') as successful,
        ROUND(AVG(confidence_score)::numeric, 2) as avg_confidence,
        ROUND(AVG(processing_time_ms)::numeric, 0) as avg_processing_time
      FROM intake.validation_audit_log
      GROUP BY attempt_source
    `
  };

  try {
    const results = {};

    for (const [key, query] of Object.entries(queries)) {
      const result = await bridge.query(query);
      results[key] = result.rows;
    }

    return {
      success: true,
      statistics: results,
      metadata: {
        generated_at: new Date().toISOString(),
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    };

  } catch (error) {
    console.error('[ENRICHMENT-ROUTER] Failed to get statistics:', error);
    throw new Error(`Failed to get enrichment statistics: ${error.message}`);
  }
}