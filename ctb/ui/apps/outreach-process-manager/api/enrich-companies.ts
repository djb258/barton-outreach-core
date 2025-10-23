/**
 * Doctrine Spec:
 * - Barton ID: 07.01.02.07.10000.017
 * - Altitude: 10000 (Execution Layer)
 * - Input: company IDs and enrichment parameters
 * - Output: enriched company data and validation
 * - MCP: Composio (Neon integrated)
 */
/**
 * Step 2B Company Enrichment API - Barton Doctrine Pipeline
 * Input: { batchSize, statusFilter }
 * Output: { rows_enriched, rows_failed, audit_log[] }
 *
 * Workflow:
 * 1. Pull failed company rows from intake.validation_failed
 * 2. Apply enrichment rules (website, phone normalization, LinkedIn, employee_count)
 * 3. Write enriched values and log attempts in enrichment_audit_log
 * 4. Trigger Step 2A re-validation
 *
 * Barton Doctrine Rules:
 * - No data advances until Step 2A validation is passed
 * - Enrichment may only fill/repair fields — Barton IDs must never change
 * - Every enrichment attempt must be logged
 * - Use Standard Composio MCP pattern for all database operations
 */

import { StandardComposioNeonBridge } from '../utils/standard-composio-neon-bridge';

interface EnrichCompaniesRequest {
  batchSize?: number;
  statusFilter?: 'failed' | 'all';
}

interface CompanyRecord {
  unique_id: string;
  company_unique_id: string;
  company_name: string;
  website_url?: string;
  company_phone?: string;
  address_street?: string;
  address_city?: string;
  address_state?: string;
  address_zip?: string;
  address_country?: string;
  linkedin_url?: string;
  employee_count?: number;
  industry?: string;
  source_system?: string;
  source_record_id?: string;
}

interface EnrichmentResult {
  unique_id: string;
  status: 'success' | 'failed' | 'partial';
  before_values: Record<string, any>;
  after_values: Record<string, any>;
  errors?: string[];
  source: string;
  fields_enriched: string[];
}

interface EnrichCompaniesResponse {
  rows_enriched: number;
  rows_failed: number;
  rows_partial: number;
  audit_log: EnrichmentResult[];
  session_id: string;
  processing_time_ms: number;
}

export default async function handler(req: any, res: any) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const bridge = new StandardComposioNeonBridge();
  const startTime = Date.now();
  const sessionId = `enrich_companies_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  try {
    const {
      batchSize = 50,
      statusFilter = 'failed'
    }: EnrichCompaniesRequest = req.body;

    console.log(`[ENRICH-COMPANIES] Starting enrichment batch: size=${batchSize}, filter=${statusFilter}, session=${sessionId}`);

    // Step 1: Pull failed company rows from validation_failed or company_raw_intake
    const failedRecords = await getFailedCompanyRecords(bridge, batchSize, statusFilter);

    if (failedRecords.length === 0) {
      return res.status(200).json({
        rows_enriched: 0,
        rows_failed: 0,
        rows_partial: 0,
        audit_log: [],
        session_id: sessionId,
        processing_time_ms: Date.now() - startTime,
        message: 'No records found requiring enrichment'
      });
    }

    console.log(`[ENRICH-COMPANIES] Found ${failedRecords.length} records for enrichment`);

    // Step 2: Process each record for enrichment
    const auditLog: EnrichmentResult[] = [];
    let enrichedCount = 0;
    let failedCount = 0;
    let partialCount = 0;

    for (const record of failedRecords) {
      try {
        const enrichmentResult = await enrichSingleCompany(bridge, record, sessionId);
        auditLog.push(enrichmentResult);

        if (enrichmentResult.status === 'success') {
          enrichedCount++;
        } else if (enrichmentResult.status === 'partial') {
          partialCount++;
        } else {
          failedCount++;
        }

      } catch (error: any) {
        console.error(`[ENRICH-COMPANIES] Error processing record ${record.unique_id}:`, error);

        const failedResult: EnrichmentResult = {
          unique_id: record.unique_id,
          status: 'failed',
          before_values: {},
          after_values: {},
          errors: [`Processing error: ${error.message}`],
          source: 'enrichment_processor',
          fields_enriched: []
        };

        auditLog.push(failedResult);
        failedCount++;

        // Log failure to audit table
        await logEnrichmentAttempt(bridge, record.unique_id, 'enrich', 'failed',
          'enrichment_processor', {}, {}, { error: error.message }, sessionId);
      }
    }

    // Step 3: Trigger re-validation for successfully enriched records
    const successfulRecords = auditLog.filter(r => r.status === 'success' || r.status === 'partial');
    if (successfulRecords.length > 0) {
      await triggerCompanyReValidation(bridge, successfulRecords.map(r => r.unique_id), sessionId);
    }

    const processingTime = Date.now() - startTime;
    console.log(`[ENRICH-COMPANIES] Batch complete: ${enrichedCount} enriched, ${partialCount} partial, ${failedCount} failed (${processingTime}ms)`);

    const response: EnrichCompaniesResponse = {
      rows_enriched: enrichedCount,
      rows_failed: failedCount,
      rows_partial: partialCount,
      audit_log: auditLog,
      session_id: sessionId,
      processing_time_ms: processingTime
    };

    return res.status(200).json(response);

  } catch (error: any) {
    console.error('[ENRICH-COMPANIES] Batch processing failed:', error);
    return res.status(500).json({
      error: 'Company enrichment failed',
      message: error.message,
      session_id: sessionId,
      processing_time_ms: Date.now() - startTime
    });
  }
}

/**
 * Get failed company records that need enrichment
 */
async function getFailedCompanyRecords(
  bridge: StandardComposioNeonBridge,
  batchSize: number,
  statusFilter: string
): Promise<CompanyRecord[]> {
  // Try to get from validation_failed first, then company_raw_intake with failed status
  let query: string;
  let params: any[];

  if (statusFilter === 'failed') {
    query = `
      SELECT DISTINCT
        cr.company_unique_id as unique_id,
        cr.company_unique_id,
        cr.company_name,
        cr.website_url,
        cr.company_phone,
        cr.address_street,
        cr.address_city,
        cr.address_state,
        cr.address_zip,
        cr.address_country,
        cr.linkedin_url,
        cr.employee_count,
        cr.industry,
        cr.source_system,
        cr.source_record_id
      FROM marketing.company_raw_intake cr
      WHERE cr.validation_status = 'failed'
      ORDER BY cr.created_at DESC
      LIMIT $1
    `;
    params = [batchSize];
  } else {
    // Get all records for enrichment
    query = `
      SELECT DISTINCT
        cr.company_unique_id as unique_id,
        cr.company_unique_id,
        cr.company_name,
        cr.website_url,
        cr.company_phone,
        cr.address_street,
        cr.address_city,
        cr.address_state,
        cr.address_zip,
        cr.address_country,
        cr.linkedin_url,
        cr.employee_count,
        cr.industry,
        cr.source_system,
        cr.source_record_id
      FROM marketing.company_raw_intake cr
      WHERE cr.validation_status IN ('failed', 'pending')
      ORDER BY cr.created_at DESC
      LIMIT $1
    `;
    params = [batchSize];
  }

  const result = await bridge.query(query, params);
  return result.rows;
}

/**
 * Enrich a single company record with various data sources and rules
 */
async function enrichSingleCompany(
  bridge: StandardComposioNeonBridge,
  record: CompanyRecord,
  sessionId: string
): Promise<EnrichmentResult> {
  const beforeValues = { ...record };
  const afterValues = { ...record };
  const fieldsEnriched: string[] = [];
  const errors: string[] = [];
  let enrichmentSource = 'internal_heuristics';

  // Enrichment Rule 1: Repair/verify domain + website
  if (!record.website_url || record.website_url.trim() === '') {
    const inferredWebsite = inferWebsiteFromName(record.company_name);
    if (inferredWebsite) {
      afterValues.website_url = inferredWebsite;
      fieldsEnriched.push('website_url');
    }
  } else {
    // Normalize existing website URL
    const normalizedWebsite = normalizeWebsiteUrl(record.website_url);
    if (normalizedWebsite !== record.website_url) {
      afterValues.website_url = normalizedWebsite;
      fieldsEnriched.push('website_url');
    }
  }

  // Enrichment Rule 2: Normalize company_phone to E.164
  if (record.company_phone && record.company_phone.trim() !== '') {
    try {
      const normalizedPhone = normalizePhoneToE164(record.company_phone);
      if (normalizedPhone !== record.company_phone) {
        afterValues.company_phone = normalizedPhone;
        fieldsEnriched.push('company_phone');
      }
    } catch (phoneError: any) {
      errors.push(`Phone normalization failed: ${phoneError.message}`);
    }
  }

  // Enrichment Rule 3: Geocode/standardize address if incomplete
  if (record.address_city && !record.address_state) {
    const inferredState = inferStateFromCity(record.address_city);
    if (inferredState) {
      afterValues.address_state = inferredState;
      fieldsEnriched.push('address_state');
    }
  }

  // Set default country if missing
  if (!record.address_country || record.address_country.trim() === '') {
    afterValues.address_country = 'USA';
    fieldsEnriched.push('address_country');
  }

  // Enrichment Rule 4: LinkedIn canonical format
  if (record.linkedin_url && record.linkedin_url.trim() !== '') {
    const normalizedLinkedIn = normalizeLinkedInUrl(record.linkedin_url);
    if (normalizedLinkedIn !== record.linkedin_url) {
      afterValues.linkedin_url = normalizedLinkedIn;
      fieldsEnriched.push('linkedin_url');
    }
  }

  // Enrichment Rule 5: Employee_count inference
  if (!record.employee_count || record.employee_count === 0) {
    const inferredCount = inferEmployeeCount(record.company_name, record.industry);
    if (inferredCount > 0) {
      afterValues.employee_count = inferredCount;
      fieldsEnriched.push('employee_count');
    }
  }

  // Determine enrichment status
  let status: 'success' | 'failed' | 'partial';
  if (fieldsEnriched.length === 0 && errors.length === 0) {
    status = 'failed';
    errors.push('No enrichment opportunities found');
  } else if (errors.length > 0 && fieldsEnriched.length > 0) {
    status = 'partial';
  } else if (fieldsEnriched.length > 0) {
    status = 'success';
  } else {
    status = 'failed';
  }

  // Update the record if enrichments were made
  if (fieldsEnriched.length > 0) {
    await updateCompanyRecord(bridge, record.company_unique_id, afterValues);
  }

  // Log enrichment attempt
  await logEnrichmentAttempt(
    bridge,
    record.company_unique_id,
    'enrich',
    status,
    enrichmentSource,
    beforeValues,
    afterValues,
    errors.length > 0 ? { errors } : null,
    sessionId
  );

  return {
    unique_id: record.company_unique_id,
    status,
    before_values: beforeValues,
    after_values: afterValues,
    errors: errors.length > 0 ? errors : undefined,
    source: enrichmentSource,
    fields_enriched: fieldsEnriched
  };
}

/**
 * Update company record with enriched values
 */
async function updateCompanyRecord(
  bridge: StandardComposioNeonBridge,
  companyUniqueId: string,
  enrichedValues: CompanyRecord
): Promise<void> {
  const query = `
    UPDATE marketing.company_raw_intake
    SET
      website_url = $2,
      company_phone = $3,
      address_state = $4,
      address_country = $5,
      linkedin_url = $6,
      employee_count = $7,
      updated_at = NOW()
    WHERE company_unique_id = $1
  `;

  await bridge.query(query, [
    companyUniqueId,
    enrichedValues.website_url,
    enrichedValues.company_phone,
    enrichedValues.address_state,
    enrichedValues.address_country,
    enrichedValues.linkedin_url,
    enrichedValues.employee_count
  ]);
}

/**
 * Log enrichment attempt to audit table
 */
async function logEnrichmentAttempt(
  bridge: StandardComposioNeonBridge,
  uniqueId: string,
  action: string,
  status: string,
  source: string,
  beforeValues: any,
  afterValues: any,
  errorLog: any,
  sessionId: string
): Promise<void> {
  const query = `
    SELECT log_enrichment_attempt($1, $2, $3, $4, $5, $6, $7, $8, $9) as audit_id
  `;

  await bridge.query(query, [
    uniqueId,
    action,
    status,
    source,
    beforeValues ? JSON.stringify(beforeValues) : null,
    afterValues ? JSON.stringify(afterValues) : null,
    errorLog ? JSON.stringify(errorLog) : null,
    'company_enrichment',
    sessionId
  ]);
}

/**
 * Trigger Step 2A re-validation for enriched records
 */
async function triggerCompanyReValidation(
  bridge: StandardComposioNeonBridge,
  uniqueIds: string[],
  sessionId: string
): Promise<void> {
  const query = `
    UPDATE marketing.company_raw_intake
    SET validation_status = 'pending',
        updated_at = NOW()
    WHERE company_unique_id = ANY($1)
  `;

  await bridge.query(query, [uniqueIds]);

  // Log re-validation trigger
  for (const uniqueId of uniqueIds) {
    await logEnrichmentAttempt(
      bridge,
      uniqueId,
      're-validate',
      'success',
      'enrichment_trigger',
      null,
      { validation_status: 'pending' },
      null,
      sessionId
    );
  }
}

// ==============================================================================
// ENRICHMENT HELPER FUNCTIONS
// ==============================================================================

/**
 * Infer website from company name
 */
function inferWebsiteFromName(companyName: string): string | null {
  if (!companyName || companyName.trim() === '') return null;

  // Simple heuristic: convert company name to potential domain
  const cleanName = companyName
    .toLowerCase()
    .replace(/[^a-zA-Z0-9\s]/g, '')
    .replace(/\s+/g, '')
    .replace(/(inc|corp|ltd|llc|company|co)$/g, '');

  if (cleanName.length > 2 && cleanName.length < 30) {
    return `https://${cleanName}.com`;
  }

  return null;
}

/**
 * Normalize website URL to canonical format
 */
function normalizeWebsiteUrl(url: string): string {
  if (!url || url.trim() === '') return '';

  let normalized = url.trim().toLowerCase();

  // Add protocol if missing
  if (!normalized.startsWith('http://') && !normalized.startsWith('https://')) {
    normalized = 'https://' + normalized;
  }

  // Remove trailing slash
  normalized = normalized.replace(/\/$/, '');

  return normalized;
}

/**
 * Normalize phone to E.164 format
 */
function normalizePhoneToE164(phone: string): string {
  if (!phone || phone.trim() === '') return '';

  // Remove all non-digit characters except +
  const cleaned = phone.replace(/[^\d+]/g, '');

  // Handle US numbers
  if (cleaned.match(/^\d{10}$/)) {
    return `+1${cleaned}`;
  }

  if (cleaned.match(/^1\d{10}$/)) {
    return `+${cleaned}`;
  }

  if (cleaned.startsWith('+') && cleaned.match(/^\+[1-9]\d{1,15}$/)) {
    return cleaned;
  }

  throw new Error(`Invalid phone format: ${phone}`);
}

/**
 * Infer state from city name (simple heuristic)
 */
function inferStateFromCity(city: string): string | null {
  const cityStateMap: Record<string, string> = {
    'new york': 'NY',
    'los angeles': 'CA',
    'chicago': 'IL',
    'houston': 'TX',
    'phoenix': 'AZ',
    'philadelphia': 'PA',
    'san antonio': 'TX',
    'san diego': 'CA',
    'dallas': 'TX',
    'san jose': 'CA',
    'austin': 'TX',
    'jacksonville': 'FL',
    'fort worth': 'TX',
    'columbus': 'OH',
    'charlotte': 'NC',
    'san francisco': 'CA',
    'indianapolis': 'IN',
    'seattle': 'WA',
    'denver': 'CO',
    'boston': 'MA',
    'atlanta': 'GA',
    'miami': 'FL'
  };

  const normalizedCity = city.toLowerCase().trim();
  return cityStateMap[normalizedCity] || null;
}

/**
 * Normalize LinkedIn URL to canonical format
 */
function normalizeLinkedInUrl(url: string): string {
  if (!url || url.trim() === '') return '';

  const match = url.match(/linkedin\.com\/company\/([^/?]+)/i);
  if (match) {
    return `https://www.linkedin.com/company/${match[1]}`;
  }

  return url;
}

/**
 * Infer employee count based on company characteristics
 */
function inferEmployeeCount(companyName: string, industry?: string): number {
  // Simple heuristics based on company name patterns and industry
  if (!companyName) return 0;

  const name = companyName.toLowerCase();

  if (name.includes('enterprise') || name.includes('corporation')) {
    return 1000;
  }

  if (name.includes('group') || name.includes('holdings')) {
    return 500;
  }

  if (name.includes('partners') || name.includes('associates')) {
    return 100;
  }

  // Industry-based inference
  if (industry) {
    const industryLower = industry.toLowerCase();
    if (industryLower.includes('technology')) return 200;
    if (industryLower.includes('healthcare')) return 150;
    if (industryLower.includes('finance')) return 300;
  }

  return 50; // Default small company size
}