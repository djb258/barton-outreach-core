/**
 * Doctrine Spec:
 * - Barton ID: 06.01.02.07.10000.015
 * - Altitude: 10000 (Execution Layer)
 * - Input: adjusted record data and validation
 * - Output: save confirmation and promotion status
 * - MCP: Composio (Neon integrated)
 */
/**
 * Step 3 Adjuster Save API - Barton Doctrine Pipeline
 * Input: { unique_id, updated_fields }
 * Output: { status: "success" | "failed", errors: [] }
 *
 * Workflow:
 * 1. Fetch current row values
 * 2. Compare with updated_fields
 * 3. Log changes to audit log (before_values, new_values)
 * 4. Apply updates to intake row
 * 5. Trigger Step 2A re-validation
 *
 * Barton Doctrine Rules:
 * - Barton IDs must remain intact — only data fields can be adjusted
 * - All edits logged with before/after values in audit tables
 * - Uses Standard Composio MCP pattern for all database operations
 * - Automatically triggers re-validation after adjustment
 */

import { StandardComposioNeonBridge } from '../utils/standard-composio-neon-bridge';
import { auditAdjustAction, generateSessionId, calculateProcessingTime } from './auditOperations.js';

interface AdjusterSaveRequest {
  unique_id: string;
  updated_fields: Record<string, any>;
  record_type?: 'company' | 'people'; // Auto-detected from unique_id if not provided
}

interface AdjusterSaveResponse {
  status: 'success' | 'failed';
  errors: string[];
  changes_applied: string[];
  validation_triggered: boolean;
  audit_log_id?: number;
  revalidation_result?: {
    status: string;
    errors: string[];
  };
}

export default async function handler(req: any, res: any) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const bridge = new StandardComposioNeonBridge();
  const startTime = Date.now();
  const sessionId = generateSessionId('adjust_record');

  try {
    const {
      unique_id,
      updated_fields,
      record_type
    }: AdjusterSaveRequest = req.body;

    if (!unique_id || !updated_fields) {
      return res.status(400).json({
        status: 'failed',
        errors: ['unique_id and updated_fields are required'],
        changes_applied: [],
        validation_triggered: false
      });
    }

    // Detect record type from Barton ID format if not provided
    const detectedType = record_type || detectRecordType(unique_id);

    if (!['company', 'people'].includes(detectedType)) {
      return res.status(400).json({
        status: 'failed',
        errors: ['Invalid record type or unique_id format'],
        changes_applied: [],
        validation_triggered: false
      });
    }

    console.log(`[ADJUSTER-SAVE] Processing ${detectedType} adjustment for ${unique_id}`);

    // Audit: Log adjustment start
    await auditAdjustAction(
      unique_id,
      'start_adjustment',
      'pending',
      {
        source: 'adjuster_console',
        actor: 'human_adjuster',
        session_id: sessionId,
        record_type: detectedType,
        before_values: { fields_to_change: Object.keys(updated_fields) }
      }
    );

    // Step 1: Fetch current row values
    const currentRecord = await fetchCurrentRecord(bridge, unique_id, detectedType);

    if (!currentRecord) {
      return res.status(404).json({
        status: 'failed',
        errors: [`${detectedType} record not found: ${unique_id}`],
        changes_applied: [],
        validation_triggered: false
      });
    }

    // Step 2: Compare with updated_fields and identify changes
    const { changedFields, beforeValues, afterValues } = identifyChanges(currentRecord, updated_fields);

    if (changedFields.length === 0) {
      return res.status(200).json({
        status: 'success',
        errors: [],
        changes_applied: [],
        validation_triggered: false,
        message: 'No changes detected'
      });
    }

    // Step 3: Log changes to audit log
    const auditLogId = await logAdjustmentChanges(
      bridge,
      unique_id,
      detectedType,
      beforeValues,
      afterValues,
      changedFields
    );

    // Step 3b: Log adjustment in validation_audit_log for the specific validation failures
    await logValidationAdjustments(
      bridge,
      unique_id,
      detectedType,
      beforeValues,
      afterValues,
      changedFields
    );

    // Step 4: Apply updates to intake row
    await applyUpdatesToRecord(bridge, unique_id, detectedType, updated_fields);

    // Step 5: Trigger Step 2A re-validation
    const revalidationResult = await triggerReValidation(bridge, unique_id, detectedType);

    const response: AdjusterSaveResponse = {
      status: 'success',
      errors: [],
      changes_applied: changedFields,
      validation_triggered: true,
      audit_log_id: auditLogId,
      revalidation_result: revalidationResult
    };

    console.log(`[ADJUSTER-SAVE] Successfully adjusted ${unique_id}: ${changedFields.join(', ')}`);

    // Audit: Log successful adjustment completion
    await auditAdjustAction(
      unique_id,
      'complete_adjustment',
      'success',
      {
        source: 'adjuster_console',
        actor: 'human_adjuster',
        session_id: sessionId,
        record_type: detectedType,
        before_values: beforeValues,
        after_values: afterValues,
        field_changes: changedFields,
        processing_time_ms: calculateProcessingTime(startTime),
        confidence_score: 1.0 // Human adjustments get full confidence
      }
    );

    return res.status(200).json(response);

  } catch (error: any) {
    console.error('[ADJUSTER-SAVE] Adjustment failed:', error);
    return res.status(500).json({
      status: 'failed',
      errors: [`Adjustment failed: ${error.message}`],
      changes_applied: [],
      validation_triggered: false
    });
  }
}

/**
 * Detect record type from Barton ID format
 * 04.04.01.XX.XXXXX.XXX = company
 * 04.04.02.XX.XXXXX.XXX = people
 */
function detectRecordType(uniqueId: string): string {
  if (uniqueId.startsWith('04.04.01.')) {
    return 'company';
  } else if (uniqueId.startsWith('04.04.02.')) {
    return 'people';
  }
  return 'unknown';
}

/**
 * Fetch current record values for comparison
 */
async function fetchCurrentRecord(
  bridge: StandardComposioNeonBridge,
  uniqueId: string,
  recordType: string
): Promise<Record<string, any> | null> {
  let query: string;
  let idField: string;

  if (recordType === 'company') {
    idField = 'company_unique_id';
    query = `
      SELECT
        company_unique_id,
        company_name,
        website_url,
        industry,
        employee_count,
        company_phone,
        address_street,
        address_city,
        address_state,
        address_zip,
        address_country,
        linkedin_url,
        facebook_url,
        twitter_url,
        sic_codes,
        founded_year,
        keywords,
        description,
        source_system,
        source_record_id,
        validation_status
      FROM marketing.company_raw_intake
      WHERE company_unique_id = $1
    `;
  } else {
    idField = 'unique_id';
    query = `
      SELECT
        unique_id,
        company_unique_id,
        company_slot_unique_id,
        first_name,
        last_name,
        title,
        seniority,
        department,
        email,
        work_phone_e164,
        personal_phone_e164,
        linkedin_url,
        twitter_url,
        facebook_url,
        bio,
        skills,
        education,
        certifications,
        source_system,
        source_record_id,
        validation_status
      FROM marketing.people_raw_intake
      WHERE unique_id = $1
    `;
  }

  const result = await bridge.query(query, [uniqueId]);
  return result.rows.length > 0 ? result.rows[0] : null;
}

/**
 * Identify changes between current record and updated fields
 */
function identifyChanges(
  currentRecord: Record<string, any>,
  updatedFields: Record<string, any>
): {
  changedFields: string[];
  beforeValues: Record<string, any>;
  afterValues: Record<string, any>;
} {
  const changedFields: string[] = [];
  const beforeValues: Record<string, any> = {};
  const afterValues: Record<string, any> = {};

  for (const [field, newValue] of Object.entries(updatedFields)) {
    // Skip Barton ID fields - they cannot be changed
    if (field.includes('unique_id') && field !== 'company_slot_unique_id') {
      continue;
    }

    const currentValue = currentRecord[field];

    // Check if value actually changed
    if (currentValue !== newValue) {
      changedFields.push(field);
      beforeValues[field] = currentValue;
      afterValues[field] = newValue;
    }
  }

  return { changedFields, beforeValues, afterValues };
}

/**
 * Log adjustment changes to appropriate audit log
 */
async function logAdjustmentChanges(
  bridge: StandardComposioNeonBridge,
  uniqueId: string,
  recordType: string,
  beforeValues: Record<string, any>,
  afterValues: Record<string, any>,
  changedFields: string[]
): Promise<number> {
  const sessionId = `adjuster_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  if (recordType === 'company') {
    const query = `
      INSERT INTO marketing.company_audit_log (
        company_unique_id,
        action,
        status,
        source,
        previous_values,
        new_values,
        altitude,
        process_id,
        session_id
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9
      ) RETURNING id
    `;

    const result = await bridge.query(query, [
      uniqueId,
      'update',
      'success',
      'adjuster_console',
      JSON.stringify(beforeValues),
      JSON.stringify(afterValues),
      10000,
      'step_3_adjuster',
      sessionId
    ]);

    return result.rows[0].id;

  } else {
    const query = `
      INSERT INTO marketing.people_audit_log (
        unique_id,
        company_unique_id,
        company_slot_unique_id,
        action,
        status,
        source,
        previous_values,
        new_values,
        altitude,
        process_id,
        session_id
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
      ) RETURNING id
    `;

    // Get company linkage for people records
    const linkageQuery = `
      SELECT company_unique_id, company_slot_unique_id
      FROM marketing.people_raw_intake
      WHERE unique_id = $1
    `;
    const linkageResult = await bridge.query(linkageQuery, [uniqueId]);
    const linkage = linkageResult.rows[0] || {};

    const result = await bridge.query(query, [
      uniqueId,
      linkage.company_unique_id,
      linkage.company_slot_unique_id,
      'update',
      'success',
      'adjuster_console',
      JSON.stringify(beforeValues),
      JSON.stringify(afterValues),
      10000,
      'step_3_adjuster',
      sessionId
    ]);

    return result.rows[0].id;
  }
}

/**
 * Log adjustment changes in validation_audit_log for affected validation failures
 */
async function logValidationAdjustments(
  bridge: StandardComposioNeonBridge,
  uniqueId: string,
  recordType: string,
  beforeValues: Record<string, any>,
  afterValues: Record<string, any>,
  changedFields: string[]
): Promise<void> {
  try {
    // Get the record ID first
    let recordIdQuery: string;
    if (recordType === 'company') {
      recordIdQuery = `
        SELECT id FROM marketing.company_raw_intake
        WHERE company_unique_id = $1
      `;
    } else {
      recordIdQuery = `
        SELECT id FROM marketing.people_raw_intake
        WHERE unique_id = $1
      `;
    }

    const recordResult = await bridge.query(recordIdQuery, [uniqueId]);
    if (recordResult.rows.length === 0) return;

    const recordId = recordResult.rows[0].id;

    // Get validation failures that might be affected by these field changes
    const validationFailuresQuery = `
      SELECT id, error_field, error_type
      FROM intake.validation_failed
      WHERE record_id = $1
        AND status IN ('pending', 'escalated', 'human_review')
        AND error_field = ANY($2)
    `;

    const failuresResult = await bridge.query(validationFailuresQuery, [
      recordId,
      changedFields
    ]);

    // Log adjustment for each affected validation failure
    for (const failure of failuresResult.rows) {
      const adjustmentQuery = `
        INSERT INTO intake.validation_audit_log (
          record_id,
          error_type,
          error_field,
          attempt_source,
          result,
          original_value,
          enriched_value,
          details,
          confidence_score,
          barton_metadata,
          validation_failed_id
        ) VALUES (
          $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
        )
      `;

      const details = {
        adjustment_type: 'human_manual',
        before_value: beforeValues[failure.error_field],
        after_value: afterValues[failure.error_field],
        changed_fields: changedFields,
        session_id: `adjuster_${Date.now()}`,
        user_source: 'adjuster_console'
      };

      await bridge.query(adjustmentQuery, [
        recordId,
        failure.error_type,
        failure.error_field,
        'human',
        'success', // Assuming manual adjustment is successful
        beforeValues[failure.error_field] || null,
        afterValues[failure.error_field] || null,
        JSON.stringify(details),
        1.00, // Human adjustment gets full confidence
        JSON.stringify({
          altitude: 10000,
          doctrine: 'STAMPED',
          process_id: 'step_3_adjuster',
          unique_id: uniqueId
        }),
        failure.id
      ]);

      // Update the validation_failed record status to 'fixed' if value was corrected
      if (afterValues[failure.error_field]) {
        await bridge.query(`
          UPDATE intake.validation_failed
          SET status = 'fixed',
              fixed_value = $1,
              last_attempt_source = 'human',
              last_attempt_at = NOW(),
              updated_at = NOW()
          WHERE id = $2
        `, [afterValues[failure.error_field], failure.id]);
      }
    }

  } catch (error) {
    console.error('Failed to log validation adjustments:', error);
    // Don't throw - this is logging, shouldn't break the main flow
  }
}

/**
 * Apply updates to the intake record
 */
async function applyUpdatesToRecord(
  bridge: StandardComposioNeonBridge,
  uniqueId: string,
  recordType: string,
  updatedFields: Record<string, any>
): Promise<void> {
  // Filter out Barton ID fields (except company_slot_unique_id which is allowed)
  const allowedFields = { ...updatedFields };
  delete allowedFields.unique_id;
  delete allowedFields.company_unique_id;

  if (Object.keys(allowedFields).length === 0) {
    return; // No valid fields to update
  }

  if (recordType === 'company') {
    // Build dynamic UPDATE query for companies
    const setClause = Object.keys(allowedFields)
      .map((field, index) => `${field} = $${index + 2}`)
      .join(', ');

    const query = `
      UPDATE marketing.company_raw_intake
      SET ${setClause}, updated_at = NOW()
      WHERE company_unique_id = $1
    `;

    const params = [uniqueId, ...Object.values(allowedFields)];
    await bridge.query(query, params);

  } else {
    // Build dynamic UPDATE query for people
    const setClause = Object.keys(allowedFields)
      .map((field, index) => `${field} = $${index + 2}`)
      .join(', ');

    const query = `
      UPDATE marketing.people_raw_intake
      SET ${setClause}, updated_at = NOW()
      WHERE unique_id = $1
    `;

    const params = [uniqueId, ...Object.values(allowedFields)];
    await bridge.query(query, params);
  }
}

/**
 * Trigger Step 2A re-validation after adjustment and move to intake if valid
 */
async function triggerReValidation(
  bridge: StandardComposioNeonBridge,
  uniqueId: string,
  recordType: string
): Promise<{
  status: string;
  errors: string[];
}> {
  try {
    // Check if all validation failures for this record are now fixed
    let recordIdQuery: string;
    if (recordType === 'company') {
      recordIdQuery = `
        SELECT id FROM marketing.company_raw_intake
        WHERE company_unique_id = $1
      `;
    } else {
      recordIdQuery = `
        SELECT id FROM marketing.people_raw_intake
        WHERE unique_id = $1
      `;
    }

    const recordResult = await bridge.query(recordIdQuery, [uniqueId]);
    if (recordResult.rows.length === 0) {
      return { status: 'failed', errors: ['Record not found'] };
    }

    const recordId = recordResult.rows[0].id;

    // Check if there are any pending validation failures
    const pendingFailuresQuery = `
      SELECT COUNT(*) as count
      FROM intake.validation_failed
      WHERE record_id = $1
        AND status IN ('pending', 'escalated', 'human_review')
    `;

    const pendingResult = await bridge.query(pendingFailuresQuery, [recordId]);
    const pendingCount = parseInt(pendingResult.rows[0].count);

    if (pendingCount === 0) {
      // All validation issues are resolved - move to validated status
      if (recordType === 'company') {
        await bridge.query(`
          UPDATE marketing.company_raw_intake
          SET validation_status = 'validated', updated_at = NOW()
          WHERE company_unique_id = $1
        `, [uniqueId]);
      } else {
        await bridge.query(`
          UPDATE marketing.people_raw_intake
          SET validation_status = 'validated', updated_at = NOW()
          WHERE unique_id = $1
        `, [uniqueId]);
      }

      return {
        status: 'validated_and_ready',
        errors: []
      };
    } else {
      // Still have pending issues - set to pending for re-validation
      if (recordType === 'company') {
        await bridge.query(`
          UPDATE marketing.company_raw_intake
          SET validation_status = 'pending', updated_at = NOW()
          WHERE company_unique_id = $1
        `, [uniqueId]);
      } else {
        await bridge.query(`
          UPDATE marketing.people_raw_intake
          SET validation_status = 'pending', updated_at = NOW()
          WHERE unique_id = $1
        `, [uniqueId]);
      }

      return {
        status: 'triggered_revalidation',
        errors: []
      };
    }

  } catch (error: any) {
    console.error('Failed to trigger re-validation:', error);
    return {
      status: 'failed',
      errors: [`Re-validation trigger failed: ${error.message}`]
    };
  }
}