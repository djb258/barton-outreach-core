/**
 * Doctrine Spec:
 * - Barton ID: 99.99.99.07.14292.720
 * - Altitude: 10000 (Execution Layer)
 * - Input: data query parameters and filters
 * - Output: database records and metadata
 * - MCP: Composio (Neon integrated)
 */
/**
 * Step 4 Promotion Console API - Barton Doctrine Pipeline
 * Input: { type: "company" | "people", batchSize?: 100, filter?: {} }
 * Output: Promotion results with success/failure counts and details
 *
 * Workflow:
 * 1. Select rows with validation_status='passed' from intake tables
 * 2. Copy validated rows into company_master or people_master
 * 3. Log promotion into audit logs with action='promote'
 * 4. Update intake row status → 'promoted'
 *
 * Barton Doctrine Rules:
 * - Only validated records can be promoted
 * - Barton IDs must remain intact during promotion
 * - All promotions logged to audit tables with full metadata
 * - Uses Standard Composio MCP pattern for all database operations
 * - Batch processing with rollback on failure
 */

import { StandardComposioNeonBridge } from '../utils/standard-composio-neon-bridge';
import { auditPromoteAction, generateSessionId, calculateProcessingTime } from './auditOperations.js';

interface PromoteRequest {
  type: 'company' | 'people';
  batchSize?: number;
  filter?: {
    source_system?: string;
    created_after?: string;
    created_before?: string;
  };
}

interface PromotionDetail {
  unique_id: string;
  status: 'success' | 'failed';
  error?: string;
  audit_log_id?: number;
}

interface PromoteResponse {
  success: boolean;
  rows_promoted: number;
  rows_failed: number;
  promotion_timestamp: string;
  batch_id: string;
  details: PromotionDetail[];
  summary: {
    total_eligible: number;
    promotion_success_rate: number;
  };
}

export default async function handler(req: any, res: any) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const bridge = new StandardComposioNeonBridge();

  try {
    const {
      type,
      batchSize = 100,
      filter = {}
    }: PromoteRequest = req.body;

    if (!type || !['company', 'people'].includes(type)) {
      return res.status(400).json({
        error: 'Invalid or missing type parameter. Must be "company" or "people"'
      });
    }

    console.log(`[PROMOTE] Starting ${type} promotion batch (size: ${batchSize})`);

    // Generate batch ID for tracking
    const batchId = `promotion_${type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Start transaction for atomicity
    await bridge.query('BEGIN');

    try {
      // Step 1: Get eligible records for promotion
      const eligibleRecords = await getEligibleRecords(bridge, type, batchSize, filter);

      if (eligibleRecords.length === 0) {
        await bridge.query('COMMIT');
        return res.status(200).json({
          success: true,
          rows_promoted: 0,
          rows_failed: 0,
          promotion_timestamp: new Date().toISOString(),
          batch_id: batchId,
          details: [],
          summary: {
            total_eligible: 0,
            promotion_success_rate: 100
          }
        });
      }

      // Step 2: Process promotions
      const promotionDetails: PromotionDetail[] = [];
      let successCount = 0;
      let failureCount = 0;

      for (const record of eligibleRecords) {
        try {
          const uniqueId = type === 'company' ? record.company_unique_id : record.unique_id;

          // Step 2a: Copy record to master table
          await copyToMasterTable(bridge, type, record);

          // Step 2b: Log promotion in audit table
          const auditLogId = await logPromotion(bridge, type, record, batchId);

          // Step 2c: Update intake record status
          await updateIntakeStatus(bridge, type, uniqueId, 'promoted', auditLogId);

          promotionDetails.push({
            unique_id: uniqueId,
            status: 'success',
            audit_log_id: auditLogId
          });

          successCount++;
          console.log(`[PROMOTE] Successfully promoted ${uniqueId}`);

        } catch (error: any) {
          const uniqueId = type === 'company' ? record.company_unique_id : record.unique_id;
          console.error(`[PROMOTE] Failed to promote ${uniqueId}:`, error);

          promotionDetails.push({
            unique_id: uniqueId,
            status: 'failed',
            error: error.message
          });

          failureCount++;
        }
      }

      // Commit transaction if we have any successes
      if (successCount > 0 && failureCount === 0) {
        await bridge.query('COMMIT');
        console.log(`[PROMOTE] Batch completed successfully: ${successCount} promoted, ${failureCount} failed`);
      } else if (failureCount > 0) {
        // Rollback on any failures to maintain data consistency
        await bridge.query('ROLLBACK');
        console.log(`[PROMOTE] Batch rolled back due to failures: ${failureCount} failed`);

        return res.status(500).json({
          success: false,
          rows_promoted: 0,
          rows_failed: failureCount,
          promotion_timestamp: new Date().toISOString(),
          batch_id: batchId,
          details: promotionDetails,
          summary: {
            total_eligible: eligibleRecords.length,
            promotion_success_rate: 0
          },
          error: 'Batch promotion failed and was rolled back'
        });
      } else {
        await bridge.query('COMMIT');
      }

      const response: PromoteResponse = {
        success: true,
        rows_promoted: successCount,
        rows_failed: failureCount,
        promotion_timestamp: new Date().toISOString(),
        batch_id: batchId,
        details: promotionDetails,
        summary: {
          total_eligible: eligibleRecords.length,
          promotion_success_rate: eligibleRecords.length > 0 ? (successCount / eligibleRecords.length) * 100 : 100
        }
      };

      return res.status(200).json(response);

    } catch (error) {
      await bridge.query('ROLLBACK');
      throw error;
    }

  } catch (error: any) {
    console.error('[PROMOTE] Promotion failed:', error);
    return res.status(500).json({
      error: 'Promotion failed',
      message: error.message
    });
  }
}

/**
 * Get records eligible for promotion (validation_status = 'passed')
 */
async function getEligibleRecords(
  bridge: StandardComposioNeonBridge,
  type: string,
  batchSize: number,
  filter: any
): Promise<any[]> {
  let query: string;
  let params: any[] = [batchSize];

  if (type === 'company') {
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
        created_at
      FROM marketing.company_raw_intake
      WHERE validation_status = 'passed'
        AND (promotion_status IS NULL OR promotion_status != 'promoted')
    `;

    // Add filters
    if (filter.source_system) {
      query += ` AND source_system = $${params.length + 1}`;
      params.push(filter.source_system);
    }
    if (filter.created_after) {
      query += ` AND created_at >= $${params.length + 1}`;
      params.push(filter.created_after);
    }
    if (filter.created_before) {
      query += ` AND created_at <= $${params.length + 1}`;
      params.push(filter.created_before);
    }

    query += ` ORDER BY created_at ASC LIMIT $1`;

  } else {
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
        created_at
      FROM marketing.people_raw_intake
      WHERE validation_status = 'passed'
        AND (promotion_status IS NULL OR promotion_status != 'promoted')
    `;

    // Add filters
    if (filter.source_system) {
      query += ` AND source_system = $${params.length + 1}`;
      params.push(filter.source_system);
    }
    if (filter.created_after) {
      query += ` AND created_at >= $${params.length + 1}`;
      params.push(filter.created_after);
    }
    if (filter.created_before) {
      query += ` AND created_at <= $${params.length + 1}`;
      params.push(filter.created_before);
    }

    query += ` ORDER BY created_at ASC LIMIT $1`;
  }

  const result = await bridge.query(query, params);
  return result.rows;
}

/**
 * Copy validated record to master table
 */
async function copyToMasterTable(
  bridge: StandardComposioNeonBridge,
  type: string,
  record: any
): Promise<void> {
  if (type === 'company') {
    const query = `
      INSERT INTO marketing.company_master (
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
        promoted_from_intake_at
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, NOW()
      )
      ON CONFLICT (company_unique_id) DO UPDATE SET
        company_name = EXCLUDED.company_name,
        website_url = EXCLUDED.website_url,
        industry = EXCLUDED.industry,
        employee_count = EXCLUDED.employee_count,
        company_phone = EXCLUDED.company_phone,
        address_street = EXCLUDED.address_street,
        address_city = EXCLUDED.address_city,
        address_state = EXCLUDED.address_state,
        address_zip = EXCLUDED.address_zip,
        address_country = EXCLUDED.address_country,
        linkedin_url = EXCLUDED.linkedin_url,
        facebook_url = EXCLUDED.facebook_url,
        twitter_url = EXCLUDED.twitter_url,
        sic_codes = EXCLUDED.sic_codes,
        founded_year = EXCLUDED.founded_year,
        keywords = EXCLUDED.keywords,
        description = EXCLUDED.description,
        updated_at = NOW()
    `;

    await bridge.query(query, [
      record.company_unique_id,
      record.company_name,
      record.website_url,
      record.industry,
      record.employee_count,
      record.company_phone,
      record.address_street,
      record.address_city,
      record.address_state,
      record.address_zip,
      record.address_country,
      record.linkedin_url,
      record.facebook_url,
      record.twitter_url,
      record.sic_codes,
      record.founded_year,
      record.keywords,
      record.description,
      record.source_system,
      record.source_record_id
    ]);

  } else {
    const query = `
      INSERT INTO marketing.people_master (
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
        promoted_from_intake_at
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, NOW()
      )
      ON CONFLICT (unique_id) DO UPDATE SET
        company_unique_id = EXCLUDED.company_unique_id,
        company_slot_unique_id = EXCLUDED.company_slot_unique_id,
        first_name = EXCLUDED.first_name,
        last_name = EXCLUDED.last_name,
        title = EXCLUDED.title,
        seniority = EXCLUDED.seniority,
        department = EXCLUDED.department,
        email = EXCLUDED.email,
        work_phone_e164 = EXCLUDED.work_phone_e164,
        personal_phone_e164 = EXCLUDED.personal_phone_e164,
        linkedin_url = EXCLUDED.linkedin_url,
        twitter_url = EXCLUDED.twitter_url,
        facebook_url = EXCLUDED.facebook_url,
        bio = EXCLUDED.bio,
        skills = EXCLUDED.skills,
        education = EXCLUDED.education,
        certifications = EXCLUDED.certifications,
        updated_at = NOW()
    `;

    await bridge.query(query, [
      record.unique_id,
      record.company_unique_id,
      record.company_slot_unique_id,
      record.first_name,
      record.last_name,
      record.title,
      record.seniority,
      record.department,
      record.email,
      record.work_phone_e164,
      record.personal_phone_e164,
      record.linkedin_url,
      record.twitter_url,
      record.facebook_url,
      record.bio,
      record.skills,
      record.education,
      record.certifications,
      record.source_system,
      record.source_record_id
    ]);
  }
}

/**
 * Log promotion to appropriate audit log
 */
async function logPromotion(
  bridge: StandardComposioNeonBridge,
  type: string,
  record: any,
  batchId: string
): Promise<number> {
  const sessionId = `promotion_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  if (type === 'company') {
    const query = `
      INSERT INTO marketing.company_audit_log (
        company_unique_id,
        action,
        status,
        source,
        new_values,
        altitude,
        process_id,
        session_id,
        batch_id
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9
      ) RETURNING id
    `;

    const result = await bridge.query(query, [
      record.company_unique_id,
      'promote',
      'success',
      'promotion_console',
      JSON.stringify({
        target_table: 'company_master',
        promotion_timestamp: new Date().toISOString(),
        source_intake_record: record
      }),
      10000,
      'step_4_promotion',
      sessionId,
      batchId
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
        new_values,
        altitude,
        process_id,
        session_id,
        batch_id
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
      ) RETURNING id
    `;

    const result = await bridge.query(query, [
      record.unique_id,
      record.company_unique_id,
      record.company_slot_unique_id,
      'promote',
      'success',
      'promotion_console',
      JSON.stringify({
        target_table: 'people_master',
        promotion_timestamp: new Date().toISOString(),
        source_intake_record: record
      }),
      10000,
      'step_4_promotion',
      sessionId,
      batchId
    ]);

    return result.rows[0].id;
  }
}

/**
 * Update intake record status to 'promoted'
 */
async function updateIntakeStatus(
  bridge: StandardComposioNeonBridge,
  type: string,
  uniqueId: string,
  status: string,
  auditLogId: number
): Promise<void> {
  if (type === 'company') {
    const query = `
      UPDATE marketing.company_raw_intake
      SET
        promotion_status = $1,
        promotion_audit_log_id = $2,
        updated_at = NOW()
      WHERE company_unique_id = $3
    `;
    await bridge.query(query, [status, auditLogId, uniqueId]);

  } else {
    const query = `
      UPDATE marketing.people_raw_intake
      SET
        promotion_status = $1,
        promotion_audit_log_id = $2,
        updated_at = NOW()
      WHERE unique_id = $3
    `;
    await bridge.query(query, [status, auditLogId, uniqueId]);
  }
}