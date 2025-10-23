/**
 * Validator Agent Service - Step 2A of Barton Doctrine Pipeline
 * Core column validation for intake.company_raw_intake
 * Uses Standard Composio MCP Pattern for all database operations
 * Version: 1.0.0 - Step 2A Core Validation Only
 */

import StandardComposioNeonBridge from '../api/lib/standard-composio-neon-bridge.js';
import { validateCompanySchema } from '../utils/validation-schemas.js';

/**
 * Step 2A Validator Agent - validates core columns only
 * Queries rows where status = 'pending', validates core columns, updates status
 */
export async function validateCompanies({ batchSize = 100, statusFilter = 'pending' } = {}) {
  const bridge = new StandardComposioNeonBridge();

  try {
    console.log(`[STEP-2A-VALIDATOR] Starting core column validation (batch size: ${batchSize})`);

    // 1. Query rows where status = 'pending'
    const pendingRecords = await fetchPendingRecords(bridge, batchSize, statusFilter);

    if (pendingRecords.length === 0) {
      return {
        success: true,
        rows_validated: 0,
        rows_failed: 0,
        message: 'No pending records found for validation',
        metadata: {
          altitude: 10000,
          doctrine: 'STAMPED',
          process_step: '2A_validation'
        }
      };
    }

    console.log(`[STEP-2A-VALIDATOR] Processing ${pendingRecords.length} records for core column validation`);

    // 2. Validate each record against core column rules
    const validationResults = [];
    let validatedCount = 0;
    let failedCount = 0;

    for (const record of pendingRecords) {
      const result = await validateSingleRecord(bridge, record);
      validationResults.push(result);

      if (result.isValid) {
        validatedCount++;
      } else {
        failedCount++;
      }
    }

    console.log(`[STEP-2A-VALIDATOR] Validation complete: ${validatedCount} validated, ${failedCount} failed`);

    return {
      success: true,
      rows_validated: validatedCount,
      rows_failed: failedCount,
      total_processed: validationResults.length,
      results: validationResults,
      metadata: {
        altitude: 10000,
        doctrine: 'STAMPED',
        process_step: '2A_validation',
        timestamp: new Date().toISOString()
      }
    };

  } catch (error) {
    console.error('[STEP-2A-VALIDATOR] Validation process error:', error);
    throw new Error(`Step 2A validation failed: ${error.message}`);
  }
}

/**
 * Fetch pending records from intake.company_raw_intake where status = 'pending'
 */
async function fetchPendingRecords(bridge, batchSize, statusFilter) {
  const query = `
    SELECT
      id,
      company,
      company_name_for_emails,
      num_employees,
      industry,
      website,
      company_linkedin_url,
      company_street,
      company_city,
      company_state,
      company_country,
      company_postal_code,
      company_address,
      company_phone,
      status,
      created_at
    FROM intake.company_raw_intake
    WHERE status = $1
    ORDER BY created_at ASC
    LIMIT $2
  `;

  console.log(`[STEP-2A-VALIDATOR] Fetching pending records with status '${statusFilter}'`);

  try {
    const result = await bridge.query(query, [statusFilter, batchSize]);
    return result.rows || [];
  } catch (error) {
    console.error('[STEP-2A-VALIDATOR] Failed to fetch pending records:', error);
    throw new Error(`Failed to fetch pending records: ${error.message}`);
  }
}

/**
 * Validate a single record against Step 2A core column rules
 */
async function validateSingleRecord(bridge, record) {
  const validationResult = {
    record_id: record.id,
    isValid: true,
    errors: [],
    normalizedData: {}
  };

  try {
    console.log(`[STEP-2A-VALIDATOR] Validating record ${record.id}`);

    // Use Step 2A validation schema (core columns only)
    const validation = validateCompanySchema(record);

    if (!validation.success) {
      validationResult.isValid = false;
      validationResult.errors = validation.errors;

      // Update status to 'failed' and log each validation failure
      await updateRecordStatus(bridge, record.id, 'failed');

      // Insert validation failures into intake.validation_failed
      for (const error of validation.errors) {
        await insertValidationFailure(bridge, record.id, error);
      }

      console.log(`[STEP-2A-VALIDATOR] Record ${record.id} validation FAILED:`, validation.errors.length, 'errors');
    } else {
      // All checks passed - update status to 'validated'
      await updateRecordStatus(bridge, record.id, 'validated', validation.normalizedData);
      validationResult.normalizedData = validation.normalizedData;

      console.log(`[STEP-2A-VALIDATOR] Record ${record.id} validation PASSED`);
    }

    // Log validation attempt to audit log
    await logValidationAttempt(bridge, record, validationResult);

    return validationResult;

  } catch (error) {
    console.error(`[STEP-2A-VALIDATOR] Error validating record ${record.id}:`, error);

    validationResult.isValid = false;
    validationResult.errors = [{
      field: 'system_error',
      error: `Validation system error: ${error.message}`,
      error_type: 'validation_system_error',
      expected_format: 'Valid data'
    }];

    return validationResult;
  }
}

/**
 * Update record status in intake.company_raw_intake
 */
async function updateRecordStatus(bridge, recordId, status, normalizedData = null) {
  try {
    let query;
    let params;

    if (status === 'validated' && normalizedData) {
      // Update with normalized data if validation passed
      const setClause = Object.keys(normalizedData)
        .map((key, index) => `${key} = $${index + 3}`)
        .join(', ');

      query = `
        UPDATE intake.company_raw_intake
        SET status = $1, updated_at = NOW()${setClause ? ', ' + setClause : ''}
        WHERE id = $2
      `;

      params = [status, recordId, ...Object.values(normalizedData)];
    } else {
      // Simple status update
      query = `
        UPDATE intake.company_raw_intake
        SET status = $1, updated_at = NOW()
        WHERE id = $2
      `;

      params = [status, recordId];
    }

    await bridge.query(query, params);
    console.log(`[STEP-2A-VALIDATOR] Updated record ${recordId} status to '${status}'`);

  } catch (error) {
    console.error(`[STEP-2A-VALIDATOR] Failed to update record ${recordId} status:`, error);
    throw error;
  }
}

/**
 * Insert validation failure into intake.validation_failed
 */
async function insertValidationFailure(bridge, recordId, error) {
  const query = `
    INSERT INTO intake.validation_failed (
      record_id, error_type, error_field, raw_value, expected_format,
      attempts, status, metadata, created_at
    ) VALUES (
      $1, $2, $3, $4, $5, 0, 'pending', $6, NOW()
    )
    ON CONFLICT (record_id, error_type, error_field)
    DO UPDATE SET
      attempts = intake.validation_failed.attempts + 1,
      updated_at = NOW(),
      metadata = $6
  `;

  const metadata = {
    altitude: 10000,
    doctrine: 'STAMPED',
    process_step: '2A_validation',
    validation_timestamp: new Date().toISOString()
  };

  try {
    await bridge.query(query, [
      recordId,
      error.error_type,
      error.field,
      error.raw_value || null,
      error.expected_format,
      JSON.stringify(metadata)
    ]);

    console.log(`[STEP-2A-VALIDATOR] Logged validation failure for record ${recordId}: ${error.error_type}`);

  } catch (insertError) {
    console.error(`[STEP-2A-VALIDATOR] Failed to log validation failure:`, insertError);
    // Don't fail validation if failure logging fails
  }
}

/**
 * Log validation attempt to intake.validation_audit_log
 */
async function logValidationAttempt(bridge, record, validationResult) {
  const query = `
    INSERT INTO intake.validation_audit_log (
      record_id, error_type, error_field, attempt_source, result,
      original_value, enriched_value, details, processing_time_ms,
      confidence_score, barton_metadata, timestamp
    ) VALUES (
      $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW()
    )
  `;

  const bartonMetadata = {
    altitude: 10000,
    doctrine: 'STAMPED',
    process_id: 'validator_step_2a',
    company_name: record.company || record.company_name_for_emails,
    validation_timestamp: new Date().toISOString()
  };

  try {
    await bridge.query(query, [
      record.id,
      validationResult.isValid ? 'validation_complete' : 'validation_failed',
      validationResult.isValid ? 'all_fields' : (validationResult.errors[0]?.field || 'unknown'),
      'validator_step_2a',
      validationResult.isValid ? 'success' : 'fail',
      record.company || record.company_name_for_emails,
      validationResult.isValid ? 'validated' : null,
      JSON.stringify({
        errors: validationResult.errors,
        normalized_data: validationResult.normalizedData
      }),
      50, // Processing time estimate
      validationResult.isValid ? 1.0 : 0.0,
      JSON.stringify(bartonMetadata)
    ]);

    console.log(`[STEP-2A-VALIDATOR] Logged audit entry for record ${record.id}`);

  } catch (error) {
    console.error(`[STEP-2A-VALIDATOR] Failed to log audit entry:`, error);
    // Don't fail validation if audit logging fails
  }
}