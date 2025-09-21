/**
 * API Endpoint: /api/validate
 * Vercel-ready serverless validation endpoint
 * Validates company records against STAMPED doctrine through Composio MCP
 */

import ComposioNeonBridge from './lib/composio-neon-bridge.js';
import BartonDoctrineUtils from './utils/barton-doctrine.js';

// STAMPED Doctrine Schema Definition
const STAMPED_SCHEMA = {
  required_fields: [
    'company_name', 'industry', 'contact_email', 'contact_phone',
    'address', 'website_url', 'employee_count'
  ],
  field_types: {
    company_name: 'string',
    industry: 'string',
    contact_email: 'email',
    contact_phone: 'phone',
    website_url: 'url',
    employee_count: 'number',
    revenue: 'number'
  },
  business_rules: {
    min_employee_count: 1,
    max_employee_count: 1000000,
    valid_industries: [
      'Technology', 'Healthcare', 'Finance', 'Manufacturing',
      'Retail', 'Education', 'Real Estate', 'Transportation',
      'Energy', 'Media', 'Consulting', 'Other'
    ]
  }
};

export default async function handler(req, res) {
  // Only accept POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({
      error: 'Method not allowed',
      message: 'Only POST requests are accepted',
      doctrine: 'STAMPED',
      altitude: 10000
    });
  }

  const startTime = Date.now();
  const bridge = new ComposioNeonBridge();

  try {
    // Extract request parameters
    const {
      batch_id = null,
      filters = { validated: null },
      limit = 1000
    } = req.body;

    console.log(`[VALIDATE] Starting validation for batch: ${batch_id || 'latest'}`);

    // Initialize response structure
    const response = {
      rows_validated: 0,
      rows_failed: 0,
      results: [],
      altitude: 10000,
      doctrine: 'STAMPED',
      process_metadata: {
        batch_id: batch_id || await getLatestBatchId(bridge),
        process_id: BartonDoctrineUtils.generateProcessId('VALIDATE'),
        started_at: new Date().toISOString(),
        composio_session: await bridge.initialize()
      }
    };

    // Step 1: Fetch rows from marketing.company_raw_intake via Composio MCP
    console.log('[VALIDATE] Fetching rows from raw intake table');

    const fetchQuery = buildFetchQuery(response.process_metadata.batch_id, filters);
    const fetchResult = await bridge.executeNeonOperation('QUERY_ROWS', {
      sql: fetchQuery,
      limit,
      return_metadata: true
    });

    if (!fetchResult.success) {
      throw new Error(`Failed to fetch rows: ${fetchResult.error}`);
    }

    const rawRows = fetchResult.data?.rows || [];
    console.log(`[VALIDATE] Retrieved ${rawRows.length} rows for validation`);

    if (rawRows.length === 0) {
      return res.status(200).json({
        ...response,
        message: 'No rows found matching criteria',
        completed_at: new Date().toISOString()
      });
    }

    // Step 2: Process each row through validation pipeline
    for (const row of rawRows) {
      const validationResult = await validateSingleRow(bridge, row);
      response.results.push(validationResult);

      if (validationResult.validated) {
        response.rows_validated++;
      } else {
        response.rows_failed++;
      }
    }

    // Step 3: Bulk update staging table with validation results
    console.log('[VALIDATE] Updating staging table with validation results');

    const updateResult = await bulkUpdateValidationResults(bridge, response.results);

    if (!updateResult.success) {
      console.error('[VALIDATE] Warning: Failed to update staging table:', updateResult.error);
    }

    // Step 4: Finalize response with doctrine metadata
    response.process_metadata.completed_at = new Date().toISOString();
    response.process_metadata.total_processing_time_ms = Date.now() - startTime;
    response.process_metadata.performance_grade = BartonDoctrineUtils.getPerformanceGrade(
      response.process_metadata.total_processing_time_ms
    );

    console.log(`[VALIDATE] Validation complete: ${response.rows_validated} passed, ${response.rows_failed} failed`);

    return res.status(200).json({
      success: true,
      ...response
    });

  } catch (error) {
    console.error('[VALIDATE] Critical error:', error);

    return res.status(500).json({
      success: false,
      error: 'Validation failed',
      message: error.message,
      rows_validated: 0,
      rows_failed: 0,
      results: [],
      altitude: 10000,
      doctrine: 'STAMPED',
      process_metadata: {
        process_id: BartonDoctrineUtils.generateProcessId('VALIDATE_ERROR'),
        error_timestamp: new Date().toISOString(),
        error_details: {
          message: error.message,
          stack: error.stack
        }
      }
    });
  }
}

/**
 * Validate a single row against STAMPED doctrine
 */
async function validateSingleRow(bridge, row) {
  const validationResult = {
    unique_id: row.unique_id || BartonDoctrineUtils.generateUniqueId(),
    process_id: 'Validate Company Record',
    company_name: row.company_name || 'Unknown',
    validated: true,
    errors: [],
    enrichment_applied: false,
    dedupe_status: 'unique'
  };

  try {
    // Step 1: STAMPED Schema Validation
    const schemaErrors = validateSTAMPEDSchema(row);
    validationResult.errors.push(...schemaErrors);

    // Step 2: Dedupe check against company master table
    const dedupeResult = await checkDedupe(bridge, row);
    if (!dedupeResult.unique) {
      validationResult.errors.push('duplicate_company');
      validationResult.dedupe_status = 'duplicate';
      validationResult.duplicate_of = dedupeResult.duplicate_id;
    }

    // Step 3: Email validation via MillionVerify MCP
    if (row.contact_email && !validationResult.errors.includes('missing_email')) {
      const emailValidation = await validateEmailMCP(bridge, row.contact_email);
      if (!emailValidation.valid) {
        validationResult.errors.push('invalid_email');
        validationResult.email_validation = emailValidation;
      }
    }

    // Step 4: Enrichment via Apify MCP (if needed)
    if (shouldEnrich(row)) {
      const enrichmentResult = await enrichCompanyData(bridge, row);
      if (enrichmentResult.success) {
        validationResult.enrichment_applied = true;
        validationResult.enriched_fields = enrichmentResult.fields;
      }
    }

    // Final validation status
    validationResult.validated = validationResult.errors.length === 0;

    return validationResult;

  } catch (error) {
    console.error(`[VALIDATE] Error validating row ${row.unique_id}:`, error);
    return {
      ...validationResult,
      validated: false,
      errors: ['validation_system_error'],
      system_error: error.message
    };
  }
}

/**
 * Validate row against STAMPED doctrine schema
 */
function validateSTAMPEDSchema(row) {
  const errors = [];

  // Check required fields
  STAMPED_SCHEMA.required_fields.forEach(field => {
    if (!row[field] || row[field].toString().trim() === '') {
      errors.push(`missing_${field}`);
    }
  });

  // Check field types and formats
  Object.entries(STAMPED_SCHEMA.field_types).forEach(([field, expectedType]) => {
    const value = row[field];
    if (value && !validateFieldType(value, expectedType)) {
      errors.push(`invalid_${field}_format`);
    }
  });

  // Check business rules
  if (row.employee_count) {
    const empCount = parseInt(row.employee_count);
    if (empCount < STAMPED_SCHEMA.business_rules.min_employee_count ||
        empCount > STAMPED_SCHEMA.business_rules.max_employee_count) {
      errors.push('invalid_employee_count_range');
    }
  }

  if (row.industry && !STAMPED_SCHEMA.business_rules.valid_industries.includes(row.industry)) {
    errors.push('invalid_industry');
  }

  return errors;
}

/**
 * Check for duplicates via Composio MCP
 */
async function checkDedupe(bridge, row) {
  try {
    const dedupeQuery = `
      SELECT unique_id, company_name, website_url
      FROM marketing.company
      WHERE LOWER(company_name) = LOWER('${row.company_name?.replace(/'/g, "''")}')
         OR website_url = '${row.website_url?.replace(/'/g, "''")}'
      LIMIT 1
    `;

    const result = await bridge.executeNeonOperation('QUERY_ROWS', {
      sql: dedupeQuery
    });

    if (result.success && result.data?.rows?.length > 0) {
      return {
        unique: false,
        duplicate_id: result.data.rows[0].unique_id,
        duplicate_name: result.data.rows[0].company_name
      };
    }

    return { unique: true };
  } catch (error) {
    console.error('[VALIDATE] Dedupe check error:', error);
    return { unique: true, error: error.message };
  }
}

/**
 * Validate email via MillionVerify MCP
 */
async function validateEmailMCP(bridge, email) {
  try {
    // Call MillionVerify through Composio MCP
    const result = await bridge.executeNeonOperation('MILLIONVERIFY_VALIDATE', {
      email,
      timeout: 5000
    });

    if (result.success) {
      return {
        valid: result.data?.result === 'ok',
        quality_score: result.data?.quality_score || 0,
        provider: result.data?.provider
      };
    }

    return { valid: true, note: 'validation_unavailable' };
  } catch (error) {
    console.error('[VALIDATE] Email validation error:', error);
    return { valid: true, error: error.message };
  }
}

/**
 * Enrich company data via Apify MCP
 */
async function enrichCompanyData(bridge, row) {
  try {
    if (!row.website_url) return { success: false, reason: 'no_website' };

    const result = await bridge.executeNeonOperation('APIFY_ENRICH_COMPANY', {
      website_url: row.website_url,
      company_name: row.company_name
    });

    if (result.success && result.data) {
      return {
        success: true,
        fields: {
          enriched_industry: result.data.industry,
          enriched_employee_count: result.data.employee_count,
          enriched_revenue: result.data.revenue,
          social_media: result.data.social_profiles
        }
      };
    }

    return { success: false, reason: 'enrichment_failed' };
  } catch (error) {
    console.error('[VALIDATE] Enrichment error:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Determine if row needs enrichment
 */
function shouldEnrich(row) {
  const missingFields = ['industry', 'employee_count', 'revenue'].filter(
    field => !row[field] || row[field].toString().trim() === ''
  );
  return missingFields.length > 0 && row.website_url;
}

/**
 * Validate field type
 */
function validateFieldType(value, expectedType) {
  switch (expectedType) {
    case 'email':
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
    case 'phone':
      return /^[\+]?[1-9][\d]{0,15}$/.test(value.replace(/\D/g, ''));
    case 'url':
      try { new URL(value); return true; } catch { return false; }
    case 'number':
      return !isNaN(value) && isFinite(value);
    case 'string':
      return typeof value === 'string' && value.length > 0;
    default:
      return true;
  }
}

/**
 * Get latest batch ID from database
 */
async function getLatestBatchId(bridge) {
  try {
    const result = await bridge.executeNeonOperation('QUERY_ROWS', {
      sql: `
        SELECT DISTINCT batch_id
        FROM marketing.company_raw_intake
        ORDER BY created_at DESC
        LIMIT 1
      `
    });

    return result.data?.rows?.[0]?.batch_id || new Date().toISOString().split('T')[0] + '-001';
  } catch (error) {
    return new Date().toISOString().split('T')[0] + '-001';
  }
}

/**
 * Build fetch query with filters
 */
function buildFetchQuery(batchId, filters) {
  let whereClause = `WHERE batch_id = '${batchId}'`;

  if (filters.validated === true) {
    whereClause += ` AND validated = true`;
  } else if (filters.validated === false) {
    whereClause += ` AND validated = false`;
  }

  return `
    SELECT *
    FROM marketing.company_raw_intake
    ${whereClause}
    ORDER BY created_at DESC
  `;
}

/**
 * Bulk update validation results in staging table
 */
async function bulkUpdateValidationResults(bridge, results) {
  try {
    const updateCases = results.map(result => `
      WHEN unique_id = '${result.unique_id}' THEN
        validated = ${result.validated},
        error_log = '${JSON.stringify(result.errors).replace(/'/g, "''")}'
    `).join('\n');

    const updateSQL = `
      UPDATE marketing.company_raw_intake
      SET
        validated = CASE ${updateCases} END,
        error_log = CASE ${updateCases} END,
        validation_timestamp = NOW()
      WHERE unique_id IN (${results.map(r => `'${r.unique_id}'`).join(', ')})
    `;

    return await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: updateSQL,
      mode: 'write'
    });
  } catch (error) {
    console.error('[VALIDATE] Bulk update error:', error);
    return { success: false, error: error.message };
  }
}