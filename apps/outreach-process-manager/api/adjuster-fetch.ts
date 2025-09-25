/**
 * Step 3 Adjuster Fetch API - Barton Doctrine Pipeline
 * Input: { type: "company" | "people", limit?: 50 }
 * Returns: Failed rows with original data, validation errors, and enrichment attempts
 *
 * Barton Doctrine Rules:
 * - Can only operate on rows that failed Step 2A validation
 * - Must show rows that could not be fixed by Step 2B enrichment
 * - Uses Standard Composio MCP pattern for all database operations
 * - Provides complete context for human adjustment decisions
 */

import { StandardComposioNeonBridge } from '../utils/standard-composio-neon-bridge';

interface AdjusterFetchRequest {
  type: 'company' | 'people';
  limit?: number;
}

interface CompanyRecord {
  company_unique_id: string;
  company_name: string;
  website_url?: string;
  industry?: string;
  employee_count?: number;
  company_phone?: string;
  address_street?: string;
  address_city?: string;
  address_state?: string;
  address_zip?: string;
  address_country?: string;
  linkedin_url?: string;
  source_system?: string;
  source_record_id?: string;
  validation_status: string;
  created_at: string;
  updated_at: string;
  errors: string[];
  enrichment_attempts: EnrichmentAttempt[];
}

interface PersonRecord {
  unique_id: string;
  company_unique_id: string;
  company_slot_unique_id?: string;
  first_name: string;
  last_name: string;
  full_name: string;
  title?: string;
  seniority?: string;
  department?: string;
  email?: string;
  work_phone_e164?: string;
  personal_phone_e164?: string;
  linkedin_url?: string;
  source_system?: string;
  source_record_id?: string;
  validation_status: string;
  created_at: string;
  updated_at: string;
  errors: string[];
  enrichment_attempts: EnrichmentAttempt[];
  slot_type?: string;
}

interface EnrichmentAttempt {
  action: string;
  status: string;
  source: string;
  before_values?: Record<string, any>;
  after_values?: Record<string, any>;
  error_log?: Record<string, any>;
  created_at: string;
  fields_enriched?: string[];
}

interface AdjusterFetchResponse {
  success: boolean;
  type: string;
  records: (CompanyRecord | PersonRecord)[];
  total_failed: number;
  needs_adjustment: number;
  summary: {
    validation_failed: number;
    enrichment_failed: number;
    ready_for_adjustment: number;
  };
}

export default async function handler(req: any, res: any) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const bridge = new StandardComposioNeonBridge();

  try {
    const { type = 'company', limit = 50 } = req.query;

    if (!['company', 'people'].includes(type)) {
      return res.status(400).json({
        error: 'Invalid type parameter. Must be "company" or "people"'
      });
    }

    console.log(`[ADJUSTER-FETCH] Fetching ${type} records for adjustment (limit: ${limit})`);

    let records: (CompanyRecord | PersonRecord)[] = [];
    let summary;

    if (type === 'company') {
      records = await fetchFailedCompanyRecords(bridge, parseInt(limit));
      summary = await getCompanySummary(bridge);
    } else {
      records = await fetchFailedPeopleRecords(bridge, parseInt(limit));
      summary = await getPeopleSummary(bridge);
    }

    // Get enrichment attempts for all records
    for (const record of records) {
      const uniqueId = type === 'company'
        ? (record as CompanyRecord).company_unique_id
        : (record as PersonRecord).unique_id;

      record.enrichment_attempts = await getEnrichmentAttempts(bridge, uniqueId);
    }

    const response: AdjusterFetchResponse = {
      success: true,
      type,
      records,
      total_failed: summary.validation_failed,
      needs_adjustment: summary.ready_for_adjustment,
      summary
    };

    console.log(`[ADJUSTER-FETCH] Retrieved ${records.length} ${type} records needing adjustment`);
    return res.status(200).json(response);

  } catch (error: any) {
    console.error('[ADJUSTER-FETCH] Failed to fetch records:', error);
    return res.status(500).json({
      error: 'Failed to fetch adjuster records',
      message: error.message
    });
  }
}

/**
 * Fetch failed company records that need manual adjustment
 */
async function fetchFailedCompanyRecords(
  bridge: StandardComposioNeonBridge,
  limit: number
): Promise<CompanyRecord[]> {
  const query = `
    SELECT
      c.company_unique_id,
      c.company_name,
      c.website_url,
      c.industry,
      c.employee_count,
      c.company_phone,
      c.address_street,
      c.address_city,
      c.address_state,
      c.address_zip,
      c.address_country,
      c.linkedin_url,
      c.source_system,
      c.source_record_id,
      c.validation_status,
      c.created_at,
      c.updated_at,
      c.validation_errors
    FROM marketing.company_raw_intake c
    WHERE c.validation_status = 'failed'
    ORDER BY c.updated_at DESC
    LIMIT $1
  `;

  const result = await bridge.query(query, [limit]);

  return result.rows.map(row => ({
    ...row,
    errors: parseValidationErrors(row.validation_errors),
    enrichment_attempts: [] // Will be populated separately
  }));
}

/**
 * Fetch failed people records that need manual adjustment
 */
async function fetchFailedPeopleRecords(
  bridge: StandardComposioNeonBridge,
  limit: number
): Promise<PersonRecord[]> {
  const query = `
    SELECT
      p.unique_id,
      p.company_unique_id,
      p.company_slot_unique_id,
      p.first_name,
      p.last_name,
      p.full_name,
      p.title,
      p.seniority,
      p.department,
      p.email,
      p.work_phone_e164,
      p.personal_phone_e164,
      p.linkedin_url,
      p.source_system,
      p.source_record_id,
      p.validation_status,
      p.created_at,
      p.updated_at,
      p.validation_errors,
      cs.slot_type
    FROM marketing.people_raw_intake p
    LEFT JOIN marketing.company_slot cs ON p.company_slot_unique_id = cs.company_slot_unique_id
    WHERE p.validation_status = 'failed'
    ORDER BY p.updated_at DESC
    LIMIT $1
  `;

  const result = await bridge.query(query, [limit]);

  return result.rows.map(row => ({
    ...row,
    errors: parseValidationErrors(row.validation_errors),
    enrichment_attempts: [] // Will be populated separately
  }));
}

/**
 * Get enrichment attempts for a specific record
 */
async function getEnrichmentAttempts(
  bridge: StandardComposioNeonBridge,
  uniqueId: string
): Promise<EnrichmentAttempt[]> {
  const query = `
    SELECT
      e.action,
      e.status,
      e.source,
      e.before_values,
      e.after_values,
      e.error_log,
      e.created_at
    FROM intake.enrichment_audit_log e
    WHERE e.unique_id = $1
    ORDER BY e.created_at DESC
    LIMIT 10
  `;

  const result = await bridge.query(query, [uniqueId]);

  return result.rows.map(row => ({
    action: row.action,
    status: row.status,
    source: row.source,
    before_values: row.before_values,
    after_values: row.after_values,
    error_log: row.error_log,
    created_at: row.created_at,
    fields_enriched: row.after_values && row.before_values
      ? Object.keys(row.after_values).filter(key =>
          row.after_values[key] !== row.before_values[key]
        )
      : []
  }));
}

/**
 * Get company adjustment summary statistics
 */
async function getCompanySummary(
  bridge: StandardComposioNeonBridge
): Promise<{
  validation_failed: number;
  enrichment_failed: number;
  ready_for_adjustment: number;
}> {
  // Get validation failed count
  const validationFailedQuery = `
    SELECT COUNT(*) as count
    FROM marketing.company_raw_intake
    WHERE validation_status = 'failed'
  `;

  // Get enrichment failed count (records that had enrichment attempts but still failed)
  const enrichmentFailedQuery = `
    SELECT COUNT(DISTINCT e.unique_id) as count
    FROM intake.enrichment_audit_log e
    JOIN marketing.company_raw_intake c ON e.unique_id = c.company_unique_id
    WHERE e.unique_id LIKE '04.04.01.%'
      AND c.validation_status = 'failed'
      AND e.action = 'enrich'
      AND e.status IN ('failed', 'partial')
  `;

  // Ready for adjustment = failed records (regardless of enrichment status)
  const readyForAdjustmentQuery = validationFailedQuery;

  const [validationResult, enrichmentResult, readyResult] = await Promise.all([
    bridge.query(validationFailedQuery),
    bridge.query(enrichmentFailedQuery),
    bridge.query(readyForAdjustmentQuery)
  ]);

  return {
    validation_failed: parseInt(validationResult.rows[0].count),
    enrichment_failed: parseInt(enrichmentResult.rows[0].count),
    ready_for_adjustment: parseInt(readyResult.rows[0].count)
  };
}

/**
 * Get people adjustment summary statistics
 */
async function getPeopleSummary(
  bridge: StandardComposioNeonBridge
): Promise<{
  validation_failed: number;
  enrichment_failed: number;
  ready_for_adjustment: number;
}> {
  // Get validation failed count
  const validationFailedQuery = `
    SELECT COUNT(*) as count
    FROM marketing.people_raw_intake
    WHERE validation_status = 'failed'
  `;

  // Get enrichment failed count (records that had enrichment attempts but still failed)
  const enrichmentFailedQuery = `
    SELECT COUNT(DISTINCT e.unique_id) as count
    FROM intake.enrichment_audit_log e
    JOIN marketing.people_raw_intake p ON e.unique_id = p.unique_id
    WHERE e.unique_id LIKE '04.04.02.%'
      AND p.validation_status = 'failed'
      AND e.action = 'enrich'
      AND e.status IN ('failed', 'partial')
  `;

  // Ready for adjustment = failed records (regardless of enrichment status)
  const readyForAdjustmentQuery = validationFailedQuery;

  const [validationResult, enrichmentResult, readyResult] = await Promise.all([
    bridge.query(validationFailedQuery),
    bridge.query(enrichmentFailedQuery),
    bridge.query(readyForAdjustmentQuery)
  ]);

  return {
    validation_failed: parseInt(validationResult.rows[0].count),
    enrichment_failed: parseInt(enrichmentResult.rows[0].count),
    ready_for_adjustment: parseInt(readyResult.rows[0].count)
  };
}

/**
 * Parse validation errors from JSON field
 */
function parseValidationErrors(validationErrors: any): string[] {
  if (!validationErrors) return [];

  try {
    if (typeof validationErrors === 'string') {
      const parsed = JSON.parse(validationErrors);
      return Array.isArray(parsed) ? parsed : [parsed];
    }

    if (Array.isArray(validationErrors)) {
      return validationErrors;
    }

    if (typeof validationErrors === 'object') {
      return Object.values(validationErrors).flat();
    }

    return [validationErrors.toString()];
  } catch (error) {
    console.warn('Failed to parse validation errors:', error);
    return ['Error parsing validation messages'];
  }
}