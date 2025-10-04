/**
 * History Layer Integration with Existing Pipeline Steps
 * Doctrine Spec:
 * - Barton ID: 99.99.99.07.XXXXX.XXX
 * - Altitude: 10000 (Integration Layer)
 * - Purpose: Integrate history tracking with scraping, enrichment, and validation steps
 * - MCP: All operations through Composio tools
 */

import { onCall } from 'firebase-functions/v2/https';
import HistoryMCPClient from '../../apps/outreach-process-manager/api/lib/history-mcp-client.js';
import HistoryDeduplication from '../../apps/outreach-process-manager/api/lib/history-deduplication.js';
import { HistoryValidator } from '../history-schema.js';

/**
 * Pre-scraping check: Determine if field needs scraping based on history
 */
export const checkPreScraping = onCall({
  memory: '512MiB',
  timeoutSeconds: 60
}, async (request) => {
  try {
    await validateMCPAccess(request, 'checkPreScraping');

    const { entityId, field, entityType = 'company', hoursThreshold = 24 } = request.data;

    if (!entityId || !field) {
      throw new Error('entityId and field are required');
    }

    const deduplication = new HistoryDeduplication();
    const skipDecision = await deduplication.shouldSkipScraping(
      entityId, field, entityType, hoursThreshold
    );

    return {
      success: true,
      shouldSkip: skipDecision.skip,
      reason: skipDecision.reason,
      details: skipDecision.details,
      timestamp: new Date().toISOString(),
      metadata: {
        entity_id: entityId,
        field: field,
        entity_type: entityType,
        hours_threshold: hoursThreshold
      }
    };

  } catch (error) {
    console.error('Pre-scraping check error:', error);
    return {
      success: false,
      error: error.message,
      shouldSkip: false, // Default to allowing scraping on error
      reason: 'error_occurred'
    };
  }
});

/**
 * Post-scraping integration: Save discovered data to history
 */
export const recordScrapingResults = onCall({
  memory: '1GiB',
  timeoutSeconds: 180
}, async (request) => {
  try {
    await validateMCPAccess(request, 'recordScrapingResults');

    const { results, processId, sessionId } = request.data;

    if (!results || !Array.isArray(results)) {
      throw new Error('results array is required');
    }

    const historyClient = new HistoryMCPClient();
    const recordedEntries = [];
    const errors = [];

    for (const result of results) {
      try {
        const { entityId, entityType, field, value, source, metadata = {} } = result;

        if (!entityId || !field || !value || !source) {
          errors.push({
            result: result,
            error: 'Missing required fields: entityId, field, value, source'
          });
          continue;
        }

        // Calculate confidence score
        const confidenceScore = historyClient.calculateConfidenceScore(source, metadata.validation || {});

        // Record history entry
        let recordResult;
        if (entityType === 'person') {
          recordResult = await historyClient.addPersonHistoryEntry(
            entityId, field, value, source, {
              confidenceScore,
              processId,
              sessionId,
              metadata: {
                ...metadata,
                scraping_timestamp: new Date().toISOString(),
                pipeline_step: 'scraping'
              }
            }
          );
        } else {
          recordResult = await historyClient.addCompanyHistoryEntry(
            entityId, field, value, source, {
              confidenceScore,
              processId,
              sessionId,
              metadata: {
                ...metadata,
                scraping_timestamp: new Date().toISOString(),
                pipeline_step: 'scraping'
              }
            }
          );
        }

        if (recordResult.success) {
          recordedEntries.push({
            entity_id: entityId,
            field: field,
            value: value,
            source: source,
            confidence_score: confidenceScore,
            history_id: recordResult.data?.id
          });
        } else {
          errors.push({
            result: result,
            error: `Failed to record history: ${recordResult.error}`
          });
        }

      } catch (entryError) {
        errors.push({
          result: result,
          error: entryError.message
        });
      }
    }

    return {
      success: true,
      recorded_count: recordedEntries.length,
      error_count: errors.length,
      recorded_entries: recordedEntries,
      errors: errors,
      timestamp: new Date().toISOString(),
      metadata: {
        process_id: processId,
        session_id: sessionId,
        total_results: results.length
      }
    };

  } catch (error) {
    console.error('Recording scraping results error:', error);
    return {
      success: false,
      error: error.message,
      recorded_count: 0
    };
  }
});

/**
 * Enrichment integration: Check existing values before enrichment
 */
export const checkPreEnrichment = onCall({
  memory: '512MiB',
  timeoutSeconds: 60
}, async (request) => {
  try {
    await validateMCPAccess(request, 'checkPreEnrichment');

    const { entityId, fields, entityType = 'company' } = request.data;

    if (!entityId || !fields || !Array.isArray(fields)) {
      throw new Error('entityId and fields array are required');
    }

    const deduplication = new HistoryDeduplication();
    const fieldChecks = [];

    for (const field of fields) {
      try {
        // Get latest value for this field
        const latestValue = await deduplication.historyClient.getLatestFieldValue(
          entityId, field, entityType
        );

        if (latestValue.success && latestValue.data) {
          const confidence = parseFloat(latestValue.data.confidence_score);
          const shouldEnrich = confidence < 0.9; // Enrich if confidence is below 90%

          fieldChecks.push({
            field: field,
            has_value: true,
            current_value: latestValue.data.value_found,
            confidence: confidence,
            source: latestValue.data.source,
            should_enrich: shouldEnrich,
            last_updated: latestValue.data.timestamp_found
          });
        } else {
          fieldChecks.push({
            field: field,
            has_value: false,
            should_enrich: true,
            reason: 'no_existing_value'
          });
        }
      } catch (fieldError) {
        fieldChecks.push({
          field: field,
          error: fieldError.message,
          should_enrich: true, // Default to enriching on error
          reason: 'check_failed'
        });
      }
    }

    return {
      success: true,
      field_checks: fieldChecks,
      total_fields: fields.length,
      needs_enrichment: fieldChecks.filter(f => f.should_enrich).length,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    console.error('Pre-enrichment check error:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

/**
 * Validation integration: Record validation results in history
 */
export const recordValidationResults = onCall({
  memory: '1GiB',
  timeoutSeconds: 120
}, async (request) => {
  try {
    await validateMCPAccess(request, 'recordValidationResults');

    const { validationResults, processId, sessionId } = request.data;

    if (!validationResults || !Array.isArray(validationResults)) {
      throw new Error('validationResults array is required');
    }

    const historyClient = new HistoryMCPClient();
    const recordedValidations = [];
    const errors = [];

    for (const validation of validationResults) {
      try {
        const { entityId, entityType, field, originalValue, validatedValue, validationStatus, validationSource } = validation;

        // Only record if validation changed the value or provided new confidence
        if (validatedValue && validatedValue !== originalValue) {
          const recordResult = entityType === 'person'
            ? await historyClient.addPersonHistoryEntry(
                entityId, field, validatedValue, validationSource, {
                  processId,
                  sessionId,
                  previousValue: originalValue,
                  changeReason: 'verification',
                  confidenceScore: validationStatus === 'verified' ? 1.0 : 0.5,
                  metadata: {
                    validation_status: validationStatus,
                    validation_timestamp: new Date().toISOString(),
                    pipeline_step: 'validation'
                  }
                }
              )
            : await historyClient.addCompanyHistoryEntry(
                entityId, field, validatedValue, validationSource, {
                  processId,
                  sessionId,
                  previousValue: originalValue,
                  changeReason: 'verification',
                  confidenceScore: validationStatus === 'verified' ? 1.0 : 0.5,
                  metadata: {
                    validation_status: validationStatus,
                    validation_timestamp: new Date().toISOString(),
                    pipeline_step: 'validation'
                  }
                }
              );

          if (recordResult.success) {
            recordedValidations.push({
              entity_id: entityId,
              field: field,
              original_value: originalValue,
              validated_value: validatedValue,
              status: validationStatus,
              history_id: recordResult.data?.id
            });
          } else {
            errors.push({
              validation: validation,
              error: `Failed to record validation: ${recordResult.error}`
            });
          }
        }

      } catch (validationError) {
        errors.push({
          validation: validation,
          error: validationError.message
        });
      }
    }

    return {
      success: true,
      recorded_count: recordedValidations.length,
      error_count: errors.length,
      recorded_validations: recordedValidations,
      errors: errors,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    console.error('Recording validation results error:', error);
    return {
      success: false,
      error: error.message,
      recorded_count: 0
    };
  }
});

/**
 * Deduplication service: Get recommended value for a field
 */
export const getFieldRecommendation = onCall({
  memory: '512MiB',
  timeoutSeconds: 60
}, async (request) => {
  try {
    await validateMCPAccess(request, 'getFieldRecommendation');

    const { entityId, field, entityType = 'company' } = request.data;

    if (!entityId || !field) {
      throw new Error('entityId and field are required');
    }

    const deduplication = new HistoryDeduplication();
    const recommendation = await deduplication.deduplicateFieldValues(entityId, field, entityType);

    return {
      success: true,
      recommendation: recommendation.recommendation,
      suggested_value: recommendation.suggested_value,
      confidence: recommendation.confidence,
      message: recommendation.message,
      alternatives: recommendation.alternatives,
      analysis: recommendation.analysis,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    console.error('Field recommendation error:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

/**
 * History analytics: Get discovery stats for reporting
 */
export const getDiscoveryAnalytics = onCall({
  memory: '512MiB',
  timeoutSeconds: 60
}, async (request) => {
  try {
    await validateMCPAccess(request, 'getDiscoveryAnalytics');

    const { entityId, entityType = 'company', daysBack = 30 } = request.data;

    if (!entityId) {
      throw new Error('entityId is required');
    }

    const historyClient = new HistoryMCPClient();
    const stats = await historyClient.getDiscoveryStats(entityId, entityType, daysBack);

    return {
      success: true,
      analytics: stats.data,
      timestamp: new Date().toISOString(),
      metadata: {
        entity_id: entityId,
        entity_type: entityType,
        days_analyzed: daysBack
      }
    };

  } catch (error) {
    console.error('Discovery analytics error:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

/**
 * Bulk history operations for pipeline efficiency
 */
export const bulkRecordHistory = onCall({
  memory: '2GiB',
  timeoutSeconds: 300
}, async (request) => {
  try {
    await validateMCPAccess(request, 'bulkRecordHistory');

    const { entries, entityType = 'company', processId, sessionId } = request.data;

    if (!entries || !Array.isArray(entries)) {
      throw new Error('entries array is required');
    }

    const historyClient = new HistoryMCPClient();

    // Validate all entries first
    const validEntries = [];
    const validationErrors = [];

    for (const entry of entries) {
      const validation = entityType === 'person'
        ? HistoryValidator.validatePersonHistoryEntry(entry)
        : HistoryValidator.validateCompanyHistoryEntry(entry);

      if (validation.isValid) {
        validEntries.push({
          ...entry,
          process_id: processId,
          session_id: sessionId
        });
      } else {
        validationErrors.push({
          entry: entry,
          errors: validation.errors
        });
      }
    }

    // Batch record valid entries
    let recordResult = { success: true, data: { recorded_count: 0 } };
    if (validEntries.length > 0) {
      recordResult = await historyClient.batchAddHistoryEntries(validEntries, entityType);
    }

    return {
      success: true,
      total_entries: entries.length,
      valid_entries: validEntries.length,
      recorded_count: recordResult.data?.recorded_count || 0,
      validation_errors: validationErrors.length,
      errors: validationErrors,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    console.error('Bulk record history error:', error);
    return {
      success: false,
      error: error.message,
      recorded_count: 0
    };
  }
});

/**
 * Helper function to validate MCP access
 */
async function validateMCPAccess(request, operation) {
  // Validate that request comes through proper MCP channels
  const auth = request.auth;
  if (!auth) {
    throw new Error('Unauthorized: MCP access required');
  }

  // Log operation for audit trail
  console.log(`History operation: ${operation}`, {
    uid: auth.uid,
    timestamp: new Date().toISOString(),
    operation: operation
  });

  return true;
}

export default {
  checkPreScraping,
  recordScrapingResults,
  checkPreEnrichment,
  recordValidationResults,
  getFieldRecommendation,
  getDiscoveryAnalytics,
  bulkRecordHistory
};