/**
 * Validation Rules Service - Step 2A Barton Doctrine Pipeline
 * Version-locked validation rules for intake.company_raw_intake
 * Uses Standard Composio MCP Pattern for all database operations
 *
 * Version: 1.0.0
 * Last Updated: 2025-01-24
 * Doctrine: STAMPED (Altitude: 10000)
 */

/**
 * VALIDATION RULE VERSION LOCK
 * These rules are version-locked for traceability and compliance
 */
export const VALIDATION_RULES_VERSION = '1.0.0';
export const VALIDATION_RULES_UPDATED = '2025-01-24T00:00:00Z';
export const BARTON_DOCTRINE = {
  altitude: 10000,
  doctrine: 'STAMPED',
  process_step: '2A_validation'
};

/**
 * Core validation rules for company data intake
 * Only validates columns specified in Step 2A scope
 */
export const VALIDATION_COLUMNS = [
  'company',
  'company_name_for_emails',
  'num_employees',
  'industry',
  'website',
  'company_linkedin_url',
  'company_street',
  'company_city',
  'company_state',
  'company_country',
  'company_postal_code',
  'company_address',
  'company_phone'
];

/**
 * Validate company name (required field)
 */
export function validateCompany(value) {
  if (!value || typeof value !== 'string') {
    return {
      valid: false,
      error: 'Company name is required and must be a string',
      error_type: 'missing_company',
      expected_format: 'Non-empty string'
    };
  }

  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return {
      valid: false,
      error: 'Company name cannot be empty or whitespace only',
      error_type: 'empty_company',
      expected_format: 'Non-empty string'
    };
  }

  if (trimmed.length < 2) {
    return {
      valid: false,
      error: 'Company name must be at least 2 characters',
      error_type: 'company_too_short',
      expected_format: 'String with minimum 2 characters'
    };
  }

  return { valid: true, normalized: trimmed };
}

/**
 * Validate company name for emails (optional field)
 */
export function validateCompanyNameForEmails(value) {
  // Optional field - null/undefined is valid
  if (value === null || value === undefined || value === '') {
    return { valid: true, normalized: null };
  }

  if (typeof value !== 'string') {
    return {
      valid: false,
      error: 'Company name for emails must be a string',
      error_type: 'invalid_company_name_for_emails_type',
      expected_format: 'String or null'
    };
  }

  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return {
      valid: false,
      error: 'Company name for emails cannot be empty if provided',
      error_type: 'empty_company_name_for_emails',
      expected_format: 'Non-empty string or null'
    };
  }

  return { valid: true, normalized: trimmed };
}

/**
 * Validate number of employees
 */
export function validateNumEmployees(value) {
  // Handle null/undefined
  if (value === null || value === undefined || value === '') {
    return {
      valid: false,
      error: 'Number of employees is required',
      error_type: 'missing_num_employees',
      expected_format: 'Integer between 1 and 100,000'
    };
  }

  // Convert to number if string
  let numValue;
  if (typeof value === 'string') {
    // Remove common formatting characters
    const cleaned = value.replace(/[,\s]/g, '');
    numValue = parseInt(cleaned, 10);
  } else if (typeof value === 'number') {
    numValue = Math.floor(value);
  } else {
    return {
      valid: false,
      error: 'Number of employees must be a number',
      error_type: 'invalid_num_employees_type',
      expected_format: 'Integer between 1 and 100,000'
    };
  }

  if (isNaN(numValue)) {
    return {
      valid: false,
      error: 'Number of employees must be a valid integer',
      error_type: 'invalid_num_employees_format',
      expected_format: 'Integer between 1 and 100,000'
    };
  }

  if (numValue < 1) {
    return {
      valid: false,
      error: 'Number of employees must be at least 1',
      error_type: 'num_employees_too_low',
      expected_format: 'Integer between 1 and 100,000'
    };
  }

  if (numValue > 100000) {
    return {
      valid: false,
      error: 'Number of employees cannot exceed 100,000',
      error_type: 'num_employees_too_high',
      expected_format: 'Integer between 1 and 100,000'
    };
  }

  return { valid: true, normalized: numValue };
}

/**
 * Validate industry (optional field)
 */
export function validateIndustry(value) {
  // Optional field - null/undefined is valid
  if (value === null || value === undefined || value === '') {
    return { valid: true, normalized: null };
  }

  if (typeof value !== 'string') {
    return {
      valid: false,
      error: 'Industry must be a string',
      error_type: 'invalid_industry_type',
      expected_format: 'String or null'
    };
  }

  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return {
      valid: false,
      error: 'Industry cannot be empty if provided',
      error_type: 'empty_industry',
      expected_format: 'Non-empty string or null'
    };
  }

  return { valid: true, normalized: trimmed };
}

/**
 * Validate website URL
 */
export function validateWebsite(value) {
  if (!value || typeof value !== 'string') {
    return {
      valid: false,
      error: 'Website is required and must be a string',
      error_type: 'missing_website',
      expected_format: 'Valid URL with domain (http/https)'
    };
  }

  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return {
      valid: false,
      error: 'Website cannot be empty',
      error_type: 'empty_website',
      expected_format: 'Valid URL with domain (http/https)'
    };
  }

  // Basic URL validation
  let url = trimmed;

  // Add protocol if missing
  if (!url.match(/^https?:\/\//i)) {
    url = 'https://' + url;
  }

  try {
    const urlObj = new URL(url);

    // Must have a domain
    if (!urlObj.hostname || urlObj.hostname.length < 3) {
      return {
        valid: false,
        error: 'Website must include a valid domain',
        error_type: 'invalid_website_domain',
        expected_format: 'Valid URL with domain (http/https)'
      };
    }

    // Must have at least one dot (basic domain check)
    if (!urlObj.hostname.includes('.')) {
      return {
        valid: false,
        error: 'Website domain must include a TLD (e.g., .com)',
        error_type: 'invalid_website_tld',
        expected_format: 'Valid URL with domain (http/https)'
      };
    }

    return { valid: true, normalized: url };

  } catch (error) {
    return {
      valid: false,
      error: 'Website must be a valid URL',
      error_type: 'invalid_website_format',
      expected_format: 'Valid URL with domain (http/https)'
    };
  }
}

/**
 * Validate LinkedIn URL (optional field)
 */
export function validateCompanyLinkedinUrl(value) {
  // Optional field - null/undefined is valid
  if (value === null || value === undefined || value === '') {
    return { valid: true, normalized: null };
  }

  if (typeof value !== 'string') {
    return {
      valid: false,
      error: 'LinkedIn URL must be a string',
      error_type: 'invalid_linkedin_url_type',
      expected_format: 'Valid LinkedIn URL or null'
    };
  }

  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return {
      valid: false,
      error: 'LinkedIn URL cannot be empty if provided',
      error_type: 'empty_linkedin_url',
      expected_format: 'Valid LinkedIn URL or null'
    };
  }

  // Must contain linkedin.com
  if (!trimmed.toLowerCase().includes('linkedin.com')) {
    return {
      valid: false,
      error: 'LinkedIn URL must contain "linkedin.com"',
      error_type: 'invalid_linkedin_domain',
      expected_format: 'Valid LinkedIn URL containing "linkedin.com"'
    };
  }

  // Basic URL validation for LinkedIn
  let url = trimmed;
  if (!url.match(/^https?:\/\//i)) {
    url = 'https://' + url;
  }

  try {
    new URL(url);
    return { valid: true, normalized: url };
  } catch (error) {
    return {
      valid: false,
      error: 'LinkedIn URL must be a valid URL format',
      error_type: 'invalid_linkedin_format',
      expected_format: 'Valid LinkedIn URL containing "linkedin.com"'
    };
  }
}

/**
 * Validate address field (required)
 */
export function validateAddressField(value, fieldName) {
  if (!value || typeof value !== 'string') {
    return {
      valid: false,
      error: `${fieldName} is required and must be a string`,
      error_type: `missing_${fieldName.toLowerCase().replace(/\s+/g, '_')}`,
      expected_format: 'Non-empty string'
    };
  }

  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return {
      valid: false,
      error: `${fieldName} cannot be empty`,
      error_type: `empty_${fieldName.toLowerCase().replace(/\s+/g, '_')}`,
      expected_format: 'Non-empty string'
    };
  }

  return { valid: true, normalized: trimmed };
}

/**
 * Validate postal code
 */
export function validateCompanyPostalCode(value) {
  if (!value || typeof value !== 'string') {
    return {
      valid: false,
      error: 'Postal code is required and must be a string',
      error_type: 'missing_postal_code',
      expected_format: 'Alphanumeric postal code'
    };
  }

  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return {
      valid: false,
      error: 'Postal code cannot be empty',
      error_type: 'empty_postal_code',
      expected_format: 'Alphanumeric postal code'
    };
  }

  // Basic alphanumeric check (allows spaces and hyphens for international codes)
  if (!/^[A-Za-z0-9\s\-]+$/.test(trimmed)) {
    return {
      valid: false,
      error: 'Postal code must be alphanumeric (letters, numbers, spaces, hyphens only)',
      error_type: 'invalid_postal_code_format',
      expected_format: 'Alphanumeric postal code'
    };
  }

  return { valid: true, normalized: trimmed };
}

/**
 * Validate phone number
 */
export function validateCompanyPhone(value) {
  if (!value || typeof value !== 'string') {
    return {
      valid: false,
      error: 'Company phone is required and must be a string',
      error_type: 'missing_phone',
      expected_format: 'Phone number with digits (may include +, -, (), spaces)'
    };
  }

  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return {
      valid: false,
      error: 'Company phone cannot be empty',
      error_type: 'empty_phone',
      expected_format: 'Phone number with digits (may include +, -, (), spaces)'
    };
  }

  // Extract digits from phone number
  const digits = trimmed.replace(/[^\d]/g, '');

  if (digits.length < 7) {
    return {
      valid: false,
      error: 'Phone number must contain at least 7 digits',
      error_type: 'phone_too_short',
      expected_format: 'Phone number with at least 7 digits'
    };
  }

  if (digits.length > 15) {
    return {
      valid: false,
      error: 'Phone number cannot contain more than 15 digits',
      error_type: 'phone_too_long',
      expected_format: 'Phone number with maximum 15 digits'
    };
  }

  // Allow only digits and common phone formatting characters
  if (!/^[\d\s\+\-\(\)\.x]+$/.test(trimmed)) {
    return {
      valid: false,
      error: 'Phone number contains invalid characters',
      error_type: 'invalid_phone_characters',
      expected_format: 'Phone number with digits and standard formatting (+, -, (), spaces, x)'
    };
  }

  return { valid: true, normalized: trimmed };
}

/**
 * Main validation function - validates all required columns
 */
export function validateCompanyRecord(record) {
  const errors = [];
  const normalized = {};

  // Validate each required field
  const validations = [
    { field: 'company', validator: validateCompany },
    { field: 'company_name_for_emails', validator: validateCompanyNameForEmails },
    { field: 'num_employees', validator: validateNumEmployees },
    { field: 'industry', validator: validateIndustry },
    { field: 'website', validator: validateWebsite },
    { field: 'company_linkedin_url', validator: validateCompanyLinkedinUrl },
    { field: 'company_street', validator: (val) => validateAddressField(val, 'Company Street') },
    { field: 'company_city', validator: (val) => validateAddressField(val, 'Company City') },
    { field: 'company_state', validator: (val) => validateAddressField(val, 'Company State') },
    { field: 'company_country', validator: (val) => validateAddressField(val, 'Company Country') },
    { field: 'company_postal_code', validator: validateCompanyPostalCode },
    { field: 'company_address', validator: (val) => validateAddressField(val, 'Company Address') },
    { field: 'company_phone', validator: validateCompanyPhone }
  ];

  // Run all validations
  for (const { field, validator } of validations) {
    try {
      const result = validator(record[field]);

      if (result.valid) {
        if (result.normalized !== undefined) {
          normalized[field] = result.normalized;
        }
      } else {
        errors.push({
          field: field,
          error: result.error,
          error_type: result.error_type,
          expected_format: result.expected_format,
          raw_value: record[field]
        });
      }
    } catch (validationError) {
      errors.push({
        field: field,
        error: `Validation function failed: ${validationError.message}`,
        error_type: 'validation_function_error',
        expected_format: 'Valid data',
        raw_value: record[field]
      });
    }
  }

  return {
    valid: errors.length === 0,
    errors: errors,
    normalized: normalized,
    metadata: {
      validation_rules_version: VALIDATION_RULES_VERSION,
      validation_timestamp: new Date().toISOString(),
      fields_validated: VALIDATION_COLUMNS.length,
      ...BARTON_DOCTRINE
    }
  };
}

/**
 * Get validation rules metadata for audit purposes
 */
export function getValidationRulesMetadata() {
  return {
    version: VALIDATION_RULES_VERSION,
    updated: VALIDATION_RULES_UPDATED,
    columns_validated: VALIDATION_COLUMNS,
    barton_doctrine: BARTON_DOCTRINE,
    rule_count: VALIDATION_COLUMNS.length
  };
}