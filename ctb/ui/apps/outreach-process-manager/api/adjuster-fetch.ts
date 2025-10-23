/**
 * Doctrine Spec:
 * - Barton ID: 06.01.01.07.10000.014
 * - Altitude: 10000 (Execution Layer)
 * - Input: adjustment query parameters and filters
 * - Output: failed records requiring human adjustment
 * - MCP: Composio (Neon integrated)
 */
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
  validation_failures: ValidationFailure[];
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
  validation_failures: ValidationFailure[];
  slot_type?: string;
}

interface ValidationFailure {
  error_type: string;
  error_field: string;
  raw_value?: string;
  expected_format?: string;
  attempts: number;
  last_attempt_source?: string;
  status: string;
  fixed_value?: string;
  metadata?: Record<string, any>;
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
 * Pulls from validation_failed table with original intake data
 */
async function fetchFailedCompanyRecords(
  bridge: StandardComposioNeonBridge,
  limit: number
): Promise<CompanyRecord[]> {
  const query = `
    SELECT DISTINCT
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
      c.validation_errors,
      -- Validation failed details
      vf.error_type,
      vf.error_field,
      vf.raw_value,
      vf.expected_format,
      vf.attempts,
      vf.last_attempt_source,
      vf.status as validation_failed_status,
      vf.fixed_value,
      vf.metadata as validation_metadata
    FROM marketing.company_raw_intake c
    INNER JOIN intake.validation_failed vf ON vf.record_id = c.id
    WHERE vf.status IN ('pending', 'escalated', 'human_review')
    ORDER BY vf.updated_at DESC, c.updated_at DESC
    LIMIT $1
  `;

  const result = await bridge.query(query, [limit]);

  // Group by company and collect all validation errors
  const companyMap = new Map();

  for (const row of result.rows) {
    const companyId = row.company_unique_id;

    if (!companyMap.has(companyId)) {
      companyMap.set(companyId, {
        company_unique_id: row.company_unique_id,
        company_name: row.company_name,
        website_url: row.website_url,
        industry: row.industry,
        employee_count: row.employee_count,
        company_phone: row.company_phone,
        address_street: row.address_street,
        address_city: row.address_city,
        address_state: row.address_state,
        address_zip: row.address_zip,
        address_country: row.address_country,
        linkedin_url: row.linkedin_url,
        source_system: row.source_system,
        source_record_id: row.source_record_id,
        validation_status: row.validation_status,
        created_at: row.created_at,
        updated_at: row.updated_at,
        errors: [],
        enrichment_attempts: [],
        validation_failures: []
      });
    }

    const company = companyMap.get(companyId);
    company.validation_failures.push({
      error_type: row.error_type,
      error_field: row.error_field,
      raw_value: row.raw_value,
      expected_format: row.expected_format,
      attempts: row.attempts,
      last_attempt_source: row.last_attempt_source,
      status: row.validation_failed_status,
      fixed_value: row.fixed_value,
      metadata: row.validation_metadata
    });

    // Add error to errors array if not already present
    if (!company.errors.includes(row.error_type)) {
      company.errors.push(row.error_type);
    }
  }

  return Array.from(companyMap.values());
}

/**
 * Fetch failed people records that need manual adjustment
 * Pulls from validation_failed table with original intake data
 */
async function fetchFailedPeopleRecords(
  bridge: StandardComposioNeonBridge,
  limit: number
): Promise<PersonRecord[]> {
  const query = `
    SELECT DISTINCT
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
      cs.slot_type,
      -- Validation failed details
      vf.error_type,
      vf.error_field,
      vf.raw_value,
      vf.expected_format,
      vf.attempts,
      vf.last_attempt_source,
      vf.status as validation_failed_status,
      vf.fixed_value,
      vf.metadata as validation_metadata
    FROM marketing.people_raw_intake p
    LEFT JOIN marketing.company_slot cs ON p.company_slot_unique_id = cs.company_slot_unique_id
    INNER JOIN intake.validation_failed vf ON vf.record_id = p.id
    WHERE vf.status IN ('pending', 'escalated', 'human_review')
    ORDER BY vf.updated_at DESC, p.updated_at DESC
    LIMIT $1
  `;

  const result = await bridge.query(query, [limit]);

  // Group by person and collect all validation errors
  const peopleMap = new Map();

  for (const row of result.rows) {
    const personId = row.unique_id;

    if (!peopleMap.has(personId)) {
      peopleMap.set(personId, {
        unique_id: row.unique_id,
        company_unique_id: row.company_unique_id,
        company_slot_unique_id: row.company_slot_unique_id,
        first_name: row.first_name,
        last_name: row.last_name,
        full_name: row.full_name,
        title: row.title,
        seniority: row.seniority,
        department: row.department,
        email: row.email,
        work_phone_e164: row.work_phone_e164,
        personal_phone_e164: row.personal_phone_e164,
        linkedin_url: row.linkedin_url,
        source_system: row.source_system,
        source_record_id: row.source_record_id,
        validation_status: row.validation_status,
        created_at: row.created_at,
        updated_at: row.updated_at,
        slot_type: row.slot_type,
        errors: [],
        enrichment_attempts: [],
        validation_failures: []
      });
    }

    const person = peopleMap.get(personId);
    person.validation_failures.push({
      error_type: row.error_type,
      error_field: row.error_field,
      raw_value: row.raw_value,
      expected_format: row.expected_format,
      attempts: row.attempts,
      last_attempt_source: row.last_attempt_source,
      status: row.validation_failed_status,
      fixed_value: row.fixed_value,
      metadata: row.validation_metadata
    });

    // Add error to errors array if not already present
    if (!person.errors.includes(row.error_type)) {
      person.errors.push(row.error_type);
    }
  }

  return Array.from(peopleMap.values());
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
  // Get validation failed count from validation_failed table
  const validationFailedQuery = `
    SELECT COUNT(DISTINCT vf.record_id) as count
    FROM intake.validation_failed vf
    JOIN marketing.company_raw_intake c ON vf.record_id = c.id
    WHERE vf.status IN ('pending', 'escalated', 'human_review')
  `;

  // Get enrichment failed count (records that had enrichment attempts but still failed)
  const enrichmentFailedQuery = `
    SELECT COUNT(DISTINCT vf.record_id) as count
    FROM intake.validation_failed vf
    JOIN marketing.company_raw_intake c ON vf.record_id = c.id
    JOIN intake.validation_audit_log val ON val.validation_failed_id = vf.id
    WHERE vf.status IN ('pending', 'escalated', 'human_review')
      AND val.attempt_source IN ('apify', 'abacus', 'auto_fix')
      AND val.result = 'fail'
  `;

  // Ready for adjustment = pending validation failed records
  const readyForAdjustmentQuery = `
    SELECT COUNT(DISTINCT vf.record_id) as count
    FROM intake.validation_failed vf
    JOIN marketing.company_raw_intake c ON vf.record_id = c.id
    WHERE vf.status = 'pending'
  `;

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
  // Get validation failed count from validation_failed table
  const validationFailedQuery = `
    SELECT COUNT(DISTINCT vf.record_id) as count
    FROM intake.validation_failed vf
    JOIN marketing.people_raw_intake p ON vf.record_id = p.id
    WHERE vf.status IN ('pending', 'escalated', 'human_review')
  `;

  // Get enrichment failed count (records that had enrichment attempts but still failed)
  const enrichmentFailedQuery = `
    SELECT COUNT(DISTINCT vf.record_id) as count
    FROM intake.validation_failed vf
    JOIN marketing.people_raw_intake p ON vf.record_id = p.id
    JOIN intake.validation_audit_log val ON val.validation_failed_id = vf.id
    WHERE vf.status IN ('pending', 'escalated', 'human_review')
      AND val.attempt_source IN ('apify', 'abacus', 'auto_fix')
      AND val.result = 'fail'
  `;

  // Ready for adjustment = pending validation failed records
  const readyForAdjustmentQuery = `
    SELECT COUNT(DISTINCT vf.record_id) as count
    FROM intake.validation_failed vf
    JOIN marketing.people_raw_intake p ON vf.record_id = p.id
    WHERE vf.status = 'pending'
  `;

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