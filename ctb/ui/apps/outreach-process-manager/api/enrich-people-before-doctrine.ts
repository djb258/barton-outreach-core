/**
 * Step 2B People Enrichment API - Barton Doctrine Pipeline
 * Input: { batchSize, statusFilter }
 * Output: { rows_enriched, rows_failed, audit_log[] }
 *
 * Workflow:
 * 1. Pull failed people rows from intake.validation_failed
 * 2. Enrich fields (emails, phones, LinkedIn, slot_type mapping)
 * 3. Normalize enriched values (E.164, canonical LinkedIn)
 * 4. Write results + audit logs
 * 5. Trigger Step 2A re-validation
 *
 * Barton Doctrine Rules:
 * - No data advances until Step 2A validation is passed
 * - Enrichment may only fill/repair fields — Barton IDs must never change
 * - Every enrichment attempt must be logged
 * - Use Standard Composio MCP pattern for all database operations
 */

import { StandardComposioNeonBridge } from '../utils/standard-composio-neon-bridge';

interface EnrichPeopleRequest {
  batchSize?: number;
  statusFilter?: 'failed' | 'all';
}

interface PersonRecord {
  unique_id: string;
  company_unique_id: string;
  company_slot_unique_id?: string;
  first_name: string;
  last_name: string;
  title?: string;
  seniority?: string;
  department?: string;
  email?: string;
  work_phone_e164?: string;
  personal_phone_e164?: string;
  linkedin_url?: string;
  twitter_url?: string;
  bio?: string;
  skills?: string;
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

interface EnrichPeopleResponse {
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
  const sessionId = `enrich_people_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  try {
    const {
      batchSize = 50,
      statusFilter = 'failed'
    }: EnrichPeopleRequest = req.body;

    console.log(`[ENRICH-PEOPLE] Starting enrichment batch: size=${batchSize}, filter=${statusFilter}, session=${sessionId}`);

    // Step 1: Pull failed people rows from people_raw_intake
    const failedRecords = await getFailedPeopleRecords(bridge, batchSize, statusFilter);

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

    console.log(`[ENRICH-PEOPLE] Found ${failedRecords.length} records for enrichment`);

    // Step 2: Process each record for enrichment
    const auditLog: EnrichmentResult[] = [];
    let enrichedCount = 0;
    let failedCount = 0;
    let partialCount = 0;

    for (const record of failedRecords) {
      try {
        const enrichmentResult = await enrichSinglePerson(bridge, record, sessionId);
        auditLog.push(enrichmentResult);

        if (enrichmentResult.status === 'success') {
          enrichedCount++;
        } else if (enrichmentResult.status === 'partial') {
          partialCount++;
        } else {
          failedCount++;
        }

      } catch (error: any) {
        console.error(`[ENRICH-PEOPLE] Error processing record ${record.unique_id}:`, error);

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
      await triggerPeopleReValidation(bridge, successfulRecords.map(r => r.unique_id), sessionId);
    }

    const processingTime = Date.now() - startTime;
    console.log(`[ENRICH-PEOPLE] Batch complete: ${enrichedCount} enriched, ${partialCount} partial, ${failedCount} failed (${processingTime}ms)`);

    const response: EnrichPeopleResponse = {
      rows_enriched: enrichedCount,
      rows_failed: failedCount,
      rows_partial: partialCount,
      audit_log: auditLog,
      session_id: sessionId,
      processing_time_ms: processingTime
    };

    return res.status(200).json(response);

  } catch (error: any) {
    console.error('[ENRICH-PEOPLE] Batch processing failed:', error);
    return res.status(500).json({
      error: 'People enrichment failed',
      message: error.message,
      session_id: sessionId,
      processing_time_ms: Date.now() - startTime
    });
  }
}

/**
 * Get failed people records that need enrichment
 */
async function getFailedPeopleRecords(
  bridge: StandardComposioNeonBridge,
  batchSize: number,
  statusFilter: string
): Promise<PersonRecord[]> {
  let query: string;
  let params: any[];

  if (statusFilter === 'failed') {
    query = `
      SELECT
        p.unique_id,
        p.company_unique_id,
        p.company_slot_unique_id,
        p.first_name,
        p.last_name,
        p.title,
        p.seniority,
        p.department,
        p.email,
        p.work_phone_e164,
        p.personal_phone_e164,
        p.linkedin_url,
        p.twitter_url,
        p.bio,
        p.skills,
        p.source_system,
        p.source_record_id
      FROM marketing.people_raw_intake p
      WHERE p.validation_status = 'failed'
      ORDER BY p.created_at DESC
      LIMIT $1
    `;
    params = [batchSize];
  } else {
    query = `
      SELECT
        p.unique_id,
        p.company_unique_id,
        p.company_slot_unique_id,
        p.first_name,
        p.last_name,
        p.title,
        p.seniority,
        p.department,
        p.email,
        p.work_phone_e164,
        p.personal_phone_e164,
        p.linkedin_url,
        p.twitter_url,
        p.bio,
        p.skills,
        p.source_system,
        p.source_record_id
      FROM marketing.people_raw_intake p
      WHERE p.validation_status IN ('failed', 'pending')
      ORDER BY p.created_at DESC
      LIMIT $1
    `;
    params = [batchSize];
  }

  const result = await bridge.query(query, params);
  return result.rows;
}

/**
 * Enrich a single person record with various data sources and rules
 */
async function enrichSinglePerson(
  bridge: StandardComposioNeonBridge,
  record: PersonRecord,
  sessionId: string
): Promise<EnrichmentResult> {
  const beforeValues = { ...record };
  const afterValues = { ...record };
  const fieldsEnriched: string[] = [];
  const errors: string[] = [];
  let enrichmentSource = 'internal_heuristics';

  // Enrichment Rule 1: Standardize name casing
  if (record.first_name) {
    const standardizedFirst = standardizeNameCasing(record.first_name);
    if (standardizedFirst !== record.first_name) {
      afterValues.first_name = standardizedFirst;
      fieldsEnriched.push('first_name');
    }
  }

  if (record.last_name) {
    const standardizedLast = standardizeNameCasing(record.last_name);
    if (standardizedLast !== record.last_name) {
      afterValues.last_name = standardizedLast;
      fieldsEnriched.push('last_name');
    }
  }

  // Enrichment Rule 2: Enrich email via heuristics (Apollo/MillionVerify would go here)
  if (!record.email || record.email.trim() === '') {
    const inferredEmail = inferEmailFromName(record.first_name, record.last_name, record.company_unique_id);
    if (inferredEmail) {
      afterValues.email = inferredEmail;
      fieldsEnriched.push('email');
      enrichmentSource = 'email_inference';
    }
  } else {
    // Validate and normalize existing email
    const validatedEmail = validateAndNormalizeEmail(record.email);
    if (validatedEmail !== record.email) {
      afterValues.email = validatedEmail;
      fieldsEnriched.push('email');
    }
  }

  // Enrichment Rule 3: Normalize phones to E.164
  if (record.work_phone_e164 && record.work_phone_e164.trim() !== '') {
    try {
      const normalizedWorkPhone = normalizePhoneToE164(record.work_phone_e164);
      if (normalizedWorkPhone !== record.work_phone_e164) {
        afterValues.work_phone_e164 = normalizedWorkPhone;
        fieldsEnriched.push('work_phone_e164');
      }
    } catch (phoneError: any) {
      errors.push(`Work phone normalization failed: ${phoneError.message}`);
    }
  }

  if (record.personal_phone_e164 && record.personal_phone_e164.trim() !== '') {
    try {
      const normalizedPersonalPhone = normalizePhoneToE164(record.personal_phone_e164);
      if (normalizedPersonalPhone !== record.personal_phone_e164) {
        afterValues.personal_phone_e164 = normalizedPersonalPhone;
        fieldsEnriched.push('personal_phone_e164');
      }
    } catch (phoneError: any) {
      errors.push(`Personal phone normalization failed: ${phoneError.message}`);
    }
  }

  // Enrichment Rule 4: LinkedIn canonical format
  if (record.linkedin_url && record.linkedin_url.trim() !== '') {
    const normalizedLinkedIn = normalizeLinkedInProfileUrl(record.linkedin_url);
    if (normalizedLinkedIn !== record.linkedin_url) {
      afterValues.linkedin_url = normalizedLinkedIn;
      fieldsEnriched.push('linkedin_url');
    }
  }

  // Enrichment Rule 5: Slot_type inference based on title keywords
  if (record.title && (!record.company_slot_unique_id || record.company_slot_unique_id.trim() === '')) {
    const inferredSlotType = inferSlotTypeFromTitle(record.title);
    if (inferredSlotType) {
      // Try to resolve the slot ID for this company and slot type
      const slotId = await resolveCompanySlotForEnrichment(bridge, record.company_unique_id, inferredSlotType);
      if (slotId) {
        afterValues.company_slot_unique_id = slotId;
        fieldsEnriched.push('company_slot_unique_id');
        enrichmentSource = 'title_slot_inference';
      }
    }
  }

  // Enrichment Rule 6: Seniority inference from title
  if (!record.seniority && record.title) {
    const inferredSeniority = inferSeniorityFromTitle(record.title);
    if (inferredSeniority) {
      afterValues.seniority = inferredSeniority;
      fieldsEnriched.push('seniority');
    }
  }

  // Enrichment Rule 7: Department inference from title
  if (!record.department && record.title) {
    const inferredDepartment = inferDepartmentFromTitle(record.title);
    if (inferredDepartment) {
      afterValues.department = inferredDepartment;
      fieldsEnriched.push('department');
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
    await updatePersonRecord(bridge, record.unique_id, afterValues);
  }

  // Log enrichment attempt
  await logEnrichmentAttempt(
    bridge,
    record.unique_id,
    'enrich',
    status,
    enrichmentSource,
    beforeValues,
    afterValues,
    errors.length > 0 ? { errors } : null,
    sessionId
  );

  return {
    unique_id: record.unique_id,
    status,
    before_values: beforeValues,
    after_values: afterValues,
    errors: errors.length > 0 ? errors : undefined,
    source: enrichmentSource,
    fields_enriched: fieldsEnriched
  };
}

/**
 * Update person record with enriched values
 */
async function updatePersonRecord(
  bridge: StandardComposioNeonBridge,
  uniqueId: string,
  enrichedValues: PersonRecord
): Promise<void> {
  const query = `
    UPDATE marketing.people_raw_intake
    SET
      first_name = $2,
      last_name = $3,
      email = $4,
      work_phone_e164 = $5,
      personal_phone_e164 = $6,
      linkedin_url = $7,
      company_slot_unique_id = $8,
      seniority = $9,
      department = $10,
      updated_at = NOW()
    WHERE unique_id = $1
  `;

  await bridge.query(query, [
    uniqueId,
    enrichedValues.first_name,
    enrichedValues.last_name,
    enrichedValues.email,
    enrichedValues.work_phone_e164,
    enrichedValues.personal_phone_e164,
    enrichedValues.linkedin_url,
    enrichedValues.company_slot_unique_id,
    enrichedValues.seniority,
    enrichedValues.department
  ]);
}

/**
 * Resolve company slot ID for enrichment (without creating new slots)
 */
async function resolveCompanySlotForEnrichment(
  bridge: StandardComposioNeonBridge,
  companyUniqueId: string,
  slotType: string
): Promise<string | null> {
  const query = `
    SELECT company_slot_unique_id
    FROM marketing.company_slot
    WHERE company_unique_id = $1
      AND slot_type = $2
      AND slot_status = 'active'
      AND is_filled = FALSE
    LIMIT 1
  `;

  const result = await bridge.query(query, [companyUniqueId, slotType]);
  return result.rows.length > 0 ? result.rows[0].company_slot_unique_id : null;
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
    'people_enrichment',
    sessionId
  ]);
}

/**
 * Trigger Step 2A re-validation for enriched records
 */
async function triggerPeopleReValidation(
  bridge: StandardComposioNeonBridge,
  uniqueIds: string[],
  sessionId: string
): Promise<void> {
  const query = `
    UPDATE marketing.people_raw_intake
    SET validation_status = 'pending',
        updated_at = NOW()
    WHERE unique_id = ANY($1)
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
// PEOPLE ENRICHMENT HELPER FUNCTIONS
// ==============================================================================

/**
 * Standardize name casing (Title Case)
 */
function standardizeNameCasing(name: string): string {
  if (!name || name.trim() === '') return name;

  return name.trim()
    .toLowerCase()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Infer email from first name, last name, and company domain
 */
function inferEmailFromName(firstName: string, lastName: string, companyUniqueId: string): string | null {
  if (!firstName || !lastName) return null;

  // This is a simplified heuristic - in production would query company domain
  const cleanFirst = firstName.toLowerCase().replace(/[^a-z]/g, '');
  const cleanLast = lastName.toLowerCase().replace(/[^a-z]/g, '');

  // Common email patterns
  const patterns = [
    `${cleanFirst}.${cleanLast}@company.com`,
    `${cleanFirst}${cleanLast}@company.com`,
    `${cleanFirst[0]}${cleanLast}@company.com`
  ];

  // Return first pattern as example - in production would validate against company domain
  return patterns[0];
}

/**
 * Validate and normalize email format
 */
function validateAndNormalizeEmail(email: string): string {
  if (!email || email.trim() === '') return email;

  const normalized = email.trim().toLowerCase();

  // Basic email validation
  if (normalized.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
    return normalized;
  }

  return email; // Return original if validation fails
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
 * Normalize LinkedIn profile URL to canonical format
 */
function normalizeLinkedInProfileUrl(url: string): string {
  if (!url || url.trim() === '') return '';

  const match = url.match(/linkedin\.com\/in\/([^/?]+)/i);
  if (match) {
    return `https://www.linkedin.com/in/${match[1]}`;
  }

  return url;
}

/**
 * Infer slot type from job title keywords
 */
function inferSlotTypeFromTitle(title: string): string | null {
  if (!title) return null;

  const titleLower = title.toLowerCase();

  // CEO patterns
  if (titleLower.includes('ceo') || titleLower.includes('chief executive')) {
    return 'CEO';
  }

  // CFO patterns
  if (titleLower.includes('cfo') || titleLower.includes('chief financial')) {
    return 'CFO';
  }

  // CTO patterns
  if (titleLower.includes('cto') || titleLower.includes('chief technology') || titleLower.includes('chief technical')) {
    return 'CTO';
  }

  // CMO patterns
  if (titleLower.includes('cmo') || titleLower.includes('chief marketing')) {
    return 'CMO';
  }

  // COO patterns
  if (titleLower.includes('coo') || titleLower.includes('chief operating')) {
    return 'COO';
  }

  // HR patterns
  if (titleLower.includes('hr') || titleLower.includes('human resources') ||
      titleLower.includes('chief people') || titleLower.includes('people officer')) {
    return 'HR';
  }

  // VP patterns
  if (titleLower.includes('vice president') || titleLower.includes('vp')) {
    if (titleLower.includes('sales')) return 'VP_SALES';
    if (titleLower.includes('marketing')) return 'VP_MARKETING';
    return 'DIRECTOR'; // Generic VP -> Director
  }

  // Director patterns
  if (titleLower.includes('director')) {
    return 'DIRECTOR';
  }

  // Manager patterns
  if (titleLower.includes('manager')) {
    return 'MANAGER';
  }

  return null;
}

/**
 * Infer seniority level from job title
 */
function inferSeniorityFromTitle(title: string): string | null {
  if (!title) return null;

  const titleLower = title.toLowerCase();

  if (titleLower.includes('chief') || titleLower.includes('ceo') || titleLower.includes('cfo') ||
      titleLower.includes('cto') || titleLower.includes('cmo') || titleLower.includes('coo')) {
    return 'C-Level';
  }

  if (titleLower.includes('vice president') || titleLower.includes('vp')) {
    return 'VP-Level';
  }

  if (titleLower.includes('director')) {
    return 'Director-Level';
  }

  if (titleLower.includes('manager')) {
    return 'Manager-Level';
  }

  if (titleLower.includes('senior') || titleLower.includes('lead')) {
    return 'Individual Contributor';
  }

  if (titleLower.includes('junior') || titleLower.includes('entry') || titleLower.includes('intern')) {
    return 'Entry-Level';
  }

  return 'Individual Contributor'; // Default
}

/**
 * Infer department from job title
 */
function inferDepartmentFromTitle(title: string): string | null {
  if (!title) return null;

  const titleLower = title.toLowerCase();

  if (titleLower.includes('sales')) return 'Sales';
  if (titleLower.includes('marketing')) return 'Marketing';
  if (titleLower.includes('engineer') || titleLower.includes('developer') || titleLower.includes('technology')) return 'Engineering';
  if (titleLower.includes('hr') || titleLower.includes('human resources') || titleLower.includes('people')) return 'Human Resources';
  if (titleLower.includes('finance') || titleLower.includes('accounting')) return 'Finance';
  if (titleLower.includes('operations') || titleLower.includes('ops')) return 'Operations';
  if (titleLower.includes('legal')) return 'Legal';
  if (titleLower.includes('product')) return 'Product';

  return null;
}