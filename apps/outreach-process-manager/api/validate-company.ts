/**
 * API Endpoint: /api/validate-company
 * Validator Agent for Company Master File JSON → marketing.company_raw_intake
 * Enforces Barton Doctrine 6-part unique_id + audit logging requirements
 *
 * Input: Master File JSON from Mapping App or staging
 * Output: JSON { rows_validated, rows_failed, details[] }
 *
 * Barton Doctrine Enforcement:
 * - Generate company_unique_id for each record
 * - Enforce required fields per doctrine minimums
 * - Normalize company_phone → E.164 format
 * - Write valid rows → company_raw_intake
 * - Write audit entry → company_audit_log
 * - Auto-generate CEO/CFO/HR slots via trigger
 */

import { NextApiRequest, NextApiResponse } from 'next';
import StandardComposioNeonBridge from './lib/standard-composio-neon-bridge.js';

// ==============================================================================
// BARTON DOCTRINE: Tool Code Mapping
// ==============================================================================

const TOOL_CODES = {
  neon: '04',      // Direct Neon inserts
  apify: '07',     // Apify scraping
  dbeaver: '08'    // DBeaver CSV bulk import
} as const;

type ToolCode = keyof typeof TOOL_CODES;

// ==============================================================================
// TYPESCRIPT INTERFACES
// ==============================================================================

/**
 * Company Master File JSON Structure (Input)
 * This comes from Mapping App, Apollo, or staging CSV
 */
interface CompanyMasterRecord {
  company_name: string;
  website_url: string;
  industry: string;
  employee_count: number | string;
  company_phone: string;
  linkedin_url?: string;
  facebook_url?: string;
  x_url?: string;
  keywords?: string;
  seo_description?: string;
  address_street: string;
  address_city: string;
  address_state: string;
  address_zip: string;
  address_country: string;
  source_system?: string;
  source_record_id?: string;
}

interface CompanyMasterFile {
  companies: CompanyMasterRecord[];
  metadata?: {
    tool_source?: ToolCode;
    batch_id?: string;
    uploaded_by?: string;
    total_records?: number;
  };
}

/**
 * Validation Result Structure (Output)
 */
interface ValidationResult {
  record_index: number;
  company_unique_id?: string;
  company_name: string;
  status: 'success' | 'failed';
  errors: string[];
  warnings: string[];
  normalized_data?: Partial<CompanyMasterRecord>;
}

interface APIResponse {
  success: boolean;
  rows_validated: number;
  rows_failed: number;
  total_processed: number;
  details: ValidationResult[];
  metadata: {
    batch_id: string;
    processing_time_ms: number;
    tool_code: string;
    altitude: number;
    doctrine: string;
    timestamp: string;
  };
  error?: string;
}

// ==============================================================================
// MAIN API HANDLER
// ==============================================================================

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<APIResponse>
) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({
      success: false,
      rows_validated: 0,
      rows_failed: 0,
      total_processed: 0,
      details: [],
      error: 'Method not allowed. Only POST requests accepted.',
      metadata: {
        batch_id: '',
        processing_time_ms: 0,
        tool_code: '04',
        altitude: 10000,
        doctrine: 'STAMPED',
        timestamp: new Date().toISOString()
      }
    });
  }

  const startTime = Date.now();
  const bridge = new StandardComposioNeonBridge();

  try {
    console.log('[VALIDATE-COMPANY] Starting company validation process');

    // Parse and validate input
    const masterFile = req.body as CompanyMasterFile;

    if (!masterFile.companies || !Array.isArray(masterFile.companies)) {
      throw new Error('Invalid input: companies array is required');
    }

    if (masterFile.companies.length === 0) {
      throw new Error('Invalid input: companies array cannot be empty');
    }

    // Determine tool source
    const toolSource = masterFile.metadata?.tool_source || 'neon';
    const toolCode = TOOL_CODES[toolSource];

    const batchId = masterFile.metadata?.batch_id ||
      `company_batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    console.log(`[VALIDATE-COMPANY] Processing ${masterFile.companies.length} companies (batch: ${batchId}, tool: ${toolSource})`);

    // Validate each company record
    const validationResults: ValidationResult[] = [];
    let validatedCount = 0;
    let failedCount = 0;

    for (let i = 0; i < masterFile.companies.length; i++) {
      const record = masterFile.companies[i];

      try {
        const result = await validateSingleCompany(bridge, record, i, toolCode, batchId);
        validationResults.push(result);

        if (result.status === 'success') {
          validatedCount++;
        } else {
          failedCount++;
        }

      } catch (error) {
        console.error(`[VALIDATE-COMPANY] Critical error processing record ${i}:`, error);

        validationResults.push({
          record_index: i,
          company_name: record.company_name || 'Unknown',
          status: 'failed',
          errors: [`System error: ${error.message}`],
          warnings: []
        });
        failedCount++;
      }
    }

    const processingTime = Date.now() - startTime;

    console.log(`[VALIDATE-COMPANY] Batch complete: ${validatedCount} validated, ${failedCount} failed (${processingTime}ms)`);

    return res.status(200).json({
      success: true,
      rows_validated: validatedCount,
      rows_failed: failedCount,
      total_processed: validationResults.length,
      details: validationResults,
      metadata: {
        batch_id: batchId,
        processing_time_ms: processingTime,
        tool_code: toolCode,
        altitude: 10000,
        doctrine: 'STAMPED',
        timestamp: new Date().toISOString()
      }
    });

  } catch (error) {
    console.error('[VALIDATE-COMPANY] Process failed:', error);

    return res.status(500).json({
      success: false,
      rows_validated: 0,
      rows_failed: 0,
      total_processed: 0,
      details: [],
      error: error.message,
      metadata: {
        batch_id: '',
        processing_time_ms: Date.now() - startTime,
        tool_code: '04',
        altitude: 10000,
        doctrine: 'STAMPED',
        timestamp: new Date().toISOString()
      }
    });
  }
}

// ==============================================================================
// SINGLE COMPANY VALIDATION
// ==============================================================================

/**
 * Validate and process a single company record
 * Enforces all Barton Doctrine requirements
 */
async function validateSingleCompany(
  bridge: StandardComposioNeonBridge,
  record: CompanyMasterRecord,
  recordIndex: number,
  toolCode: string,
  batchId: string
): Promise<ValidationResult> {

  const result: ValidationResult = {
    record_index: recordIndex,
    company_name: record.company_name || 'Unknown',
    status: 'success',
    errors: [],
    warnings: [],
    normalized_data: {}
  };

  try {
    // Step 1: Generate Barton unique_id
    const companyUniqueId = await generateBartonId(bridge, toolCode);
    result.company_unique_id = companyUniqueId;

    // Step 2: Validate required fields
    const validation = validateRequiredFields(record);
    if (!validation.valid) {
      result.status = 'failed';
      result.errors.push(...validation.errors);

      // Still log the failure for audit trail
      await logAuditEntry(bridge, companyUniqueId, 'validate', 'failed',
        'field_validation_errors', { errors: validation.errors }, batchId);

      return result;
    }

    // Step 3: Normalize data
    const normalized = normalizeCompanyData(record);
    result.normalized_data = normalized.data;
    result.warnings.push(...normalized.warnings);

    // Step 4: Insert into company_raw_intake
    await insertCompanyRecord(bridge, companyUniqueId, normalized.data, batchId);

    // Step 5: Log successful validation
    await logAuditEntry(bridge, companyUniqueId, 'insert', 'success',
      'company_validator', { record_index: recordIndex, batch_id: batchId }, batchId);

    console.log(`[VALIDATE-COMPANY] Successfully processed: ${result.company_name} (${companyUniqueId})`);

    return result;

  } catch (error) {
    console.error(`[VALIDATE-COMPANY] Error processing record ${recordIndex}:`, error);

    result.status = 'failed';
    result.errors.push(`Processing error: ${error.message}`);

    // Log the error if we have a company ID
    if (result.company_unique_id) {
      try {
        await logAuditEntry(bridge, result.company_unique_id, 'validate', 'failed',
          'system_error', { error: error.message, record_index: recordIndex }, batchId);
      } catch (logError) {
        console.error('[VALIDATE-COMPANY] Failed to log error:', logError);
      }
    }

    return result;
  }
}

// ==============================================================================
// BARTON ID GENERATION
// ==============================================================================

/**
 * Generate 6-part Barton unique ID for company
 * Calls database function to ensure proper sequencing
 */
async function generateBartonId(bridge: StandardComposioNeonBridge, toolCode: string): Promise<string> {
  const query = 'SELECT generate_company_barton_id($1) as barton_id';

  try {
    const result = await bridge.query(query, [toolCode]);

    if (!result.rows || result.rows.length === 0) {
      throw new Error('Failed to generate Barton ID: No result returned');
    }

    const bartonId = result.rows[0].barton_id;

    if (!bartonId || typeof bartonId !== 'string') {
      throw new Error('Failed to generate Barton ID: Invalid result format');
    }

    console.log(`[VALIDATE-COMPANY] Generated Barton ID: ${bartonId}`);
    return bartonId;

  } catch (error) {
    console.error('[VALIDATE-COMPANY] Barton ID generation failed:', error);
    throw new Error(`Barton ID generation failed: ${error.message}`);
  }
}

// ==============================================================================
// FIELD VALIDATION
// ==============================================================================

/**
 * Validate required fields per Barton Doctrine minimums
 * Enforces strict validation rules for company intake
 */
function validateRequiredFields(record: CompanyMasterRecord): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // Required fields validation
  if (!record.company_name || record.company_name.trim().length === 0) {
    errors.push('company_name is required and cannot be empty');
  }

  if (!record.website_url || record.website_url.trim().length === 0) {
    errors.push('website_url is required and cannot be empty');
  } else {
    // Basic URL validation
    try {
      new URL(record.website_url);
    } catch {
      errors.push('website_url must be a valid URL');
    }
  }

  if (!record.industry || record.industry.trim().length === 0) {
    errors.push('industry is required and cannot be empty');
  }

  if (!record.employee_count) {
    errors.push('employee_count is required');
  } else {
    const empCount = typeof record.employee_count === 'string'
      ? parseInt(record.employee_count)
      : record.employee_count;

    if (isNaN(empCount) || empCount <= 0 || empCount > 10000000) {
      errors.push('employee_count must be a valid integer between 1 and 10,000,000');
    }
  }

  if (!record.company_phone || record.company_phone.trim().length === 0) {
    errors.push('company_phone is required and cannot be empty');
  }

  // Address validation
  const addressFields = [
    'address_street', 'address_city', 'address_state', 'address_zip', 'address_country'
  ];

  for (const field of addressFields) {
    if (!record[field] || record[field].trim().length === 0) {
      errors.push(`${field} is required and cannot be empty`);
    }
  }

  return { valid: errors.length === 0, errors };
}

// ==============================================================================
// DATA NORMALIZATION
// ==============================================================================

/**
 * Normalize company data for database storage
 * Handles phone number E.164 conversion and field sanitization
 */
function normalizeCompanyData(record: CompanyMasterRecord): {
  data: CompanyMasterRecord;
  warnings: string[]
} {
  const warnings: string[] = [];
  const normalized = { ...record };

  // Normalize company_phone to E.164 format
  try {
    normalized.company_phone = normalizePhoneToE164(record.company_phone);
  } catch (error) {
    warnings.push(`Phone normalization warning: ${error.message}`);
    // Keep original if normalization fails - let database validation catch it
  }

  // Normalize employee_count to integer
  if (typeof normalized.employee_count === 'string') {
    normalized.employee_count = parseInt(normalized.employee_count);
  }

  // Trim string fields
  const stringFields = [
    'company_name', 'website_url', 'industry', 'linkedin_url',
    'facebook_url', 'x_url', 'keywords', 'seo_description',
    'address_street', 'address_city', 'address_state', 'address_zip', 'address_country'
  ];

  for (const field of stringFields) {
    if (normalized[field] && typeof normalized[field] === 'string') {
      normalized[field] = normalized[field].trim();
    }
  }

  // Ensure website has protocol
  if (normalized.website_url && !normalized.website_url.match(/^https?:\/\//)) {
    normalized.website_url = `https://${normalized.website_url}`;
    warnings.push('Added https:// protocol to website_url');
  }

  return { data: normalized, warnings };
}

/**
 * Convert phone number to E.164 format
 * Handles US numbers primarily, expandable for international
 */
function normalizePhoneToE164(phone: string): string {
  if (!phone) {
    throw new Error('Phone number is required');
  }

  // Remove all non-digit characters
  const digits = phone.replace(/\D/g, '');

  // US number handling
  if (digits.length === 10) {
    return `+1${digits}`;
  }

  if (digits.length === 11 && digits.startsWith('1')) {
    return `+${digits}`;
  }

  // Already in E.164 format
  if (phone.startsWith('+')) {
    return phone;
  }

  // Default: assume US if no country code
  if (digits.length >= 10) {
    const last10 = digits.slice(-10);
    return `+1${last10}`;
  }

  throw new Error(`Invalid phone number format: ${phone}`);
}

// ==============================================================================
// DATABASE OPERATIONS
// ==============================================================================

/**
 * Insert validated company record into marketing.company_raw_intake
 * Triggers will auto-generate CEO/CFO/HR slots
 */
async function insertCompanyRecord(
  bridge: StandardComposioNeonBridge,
  companyUniqueId: string,
  data: CompanyMasterRecord,
  batchId: string
): Promise<void> {

  const query = `
    INSERT INTO marketing.company_raw_intake (
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
      facebook_url,
      x_url,
      linkedin_url,
      keywords,
      seo_description,
      source_system,
      source_record_id,
      validation_status,
      altitude,
      process_step
    ) VALUES (
      $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21
    )
  `;

  const params = [
    companyUniqueId,
    data.company_name,
    data.website_url,
    data.industry,
    data.employee_count,
    data.company_phone,
    data.address_street,
    data.address_city,
    data.address_state,
    data.address_zip,
    data.address_country,
    data.facebook_url || null,
    data.x_url || null,
    data.linkedin_url || null,
    data.keywords || null,
    data.seo_description || null,
    data.source_system || 'company_validator',
    data.source_record_id || batchId,
    'validated',
    10000,
    'company_intake_validation'
  ];

  try {
    await bridge.query(query, params);
    console.log(`[VALIDATE-COMPANY] Inserted company: ${companyUniqueId}`);
  } catch (error) {
    console.error(`[VALIDATE-COMPANY] Failed to insert company ${companyUniqueId}:`, error);
    throw new Error(`Database insert failed: ${error.message}`);
  }
}

/**
 * Log audit entry to marketing.company_audit_log
 * Required for Barton Doctrine compliance
 */
async function logAuditEntry(
  bridge: StandardComposioNeonBridge,
  companyUniqueId: string,
  action: string,
  status: string,
  source: string,
  metadata: any,
  sessionId: string
): Promise<void> {

  const query = `
    INSERT INTO marketing.company_audit_log (
      company_unique_id,
      action,
      status,
      source,
      error_log,
      new_values,
      altitude,
      process_id,
      session_id
    ) VALUES (
      $1, $2, $3, $4, $5, $6, $7, $8, $9
    )
  `;

  const params = [
    companyUniqueId,
    action,
    status,
    source,
    status === 'failed' ? JSON.stringify(metadata) : null,
    status === 'success' ? JSON.stringify(metadata) : null,
    10000,
    'company_validator_api',
    sessionId
  ];

  try {
    await bridge.query(query, params);
  } catch (error) {
    console.error(`[VALIDATE-COMPANY] Failed to log audit entry for ${companyUniqueId}:`, error);
    // Don't throw - audit logging failures shouldn't break the main process
  }
}