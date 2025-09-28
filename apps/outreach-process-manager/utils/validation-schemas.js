/**
 * Validation Schemas and Rules for Company Data - Step 2A Barton Doctrine
 * Version-locked validation for core columns only
 * Version: 1.0.0 - Updated for Step 2A scope
 */

/**
 * Step 2A Core Column Validation - ONLY validates specified columns
 * DO NOT validate: facebook_url, twitter_url, sic_codes, founded_year
 */
export function validateCompanySchema(record) {
  const result = {
    success: true,
    field: null,
    message: null,
    normalizedData: {},
    errors: []
  };

  // 1. company → must not be null/empty
  if (!record.company || record.company.toString().trim().length === 0) {
    result.errors.push({
      field: 'company',
      error: 'Company name is required and cannot be empty',
      error_type: 'missing_company',
      expected_format: 'Non-empty string'
    });
  } else if (record.company.toString().trim().length < 2) {
    result.errors.push({
      field: 'company',
      error: 'Company name must be at least 2 characters',
      error_type: 'company_too_short',
      expected_format: 'String with minimum 2 characters'
    });
  } else {
    result.normalizedData.company = record.company.toString().trim();
  }

  // 2. company_name_for_emails → optional, but if present cannot be empty
  if (record.company_name_for_emails !== null && record.company_name_for_emails !== undefined && record.company_name_for_emails !== '') {
    if (typeof record.company_name_for_emails !== 'string' || record.company_name_for_emails.trim().length === 0) {
      result.errors.push({
        field: 'company_name_for_emails',
        error: 'Company name for emails cannot be empty if provided',
        error_type: 'empty_company_name_for_emails',
        expected_format: 'Non-empty string or null'
      });
    } else {
      result.normalizedData.company_name_for_emails = record.company_name_for_emails.trim();
    }
  }

  // 3. num_employees → must be integer, between 1 and 100,000
  if (!record.num_employees) {
    result.errors.push({
      field: 'num_employees',
      error: 'Number of employees is required',
      error_type: 'missing_num_employees',
      expected_format: 'Integer between 1 and 100,000'
    });
  } else {
    const employeeCount = parseEmployeeCount(record.num_employees);
    if (employeeCount === null || employeeCount < 1 || employeeCount > 100000) {
      result.errors.push({
        field: 'num_employees',
        error: 'Number of employees must be integer between 1 and 100,000',
        error_type: 'invalid_num_employees',
        expected_format: 'Integer between 1 and 100,000'
      });
    } else {
      result.normalizedData.num_employees = employeeCount;
    }
  }

  // 4. industry → optional, but if present cannot be empty
  if (record.industry !== null && record.industry !== undefined && record.industry !== '') {
    if (typeof record.industry !== 'string' || record.industry.trim().length === 0) {
      result.errors.push({
        field: 'industry',
        error: 'Industry cannot be empty if provided',
        error_type: 'empty_industry',
        expected_format: 'Non-empty string or null'
      });
    } else {
      result.normalizedData.industry = record.industry.trim();
    }
  }

  // 5. website → must be a valid URL, must include domain
  if (!record.website || !isValidUrl(record.website)) {
    result.errors.push({
      field: 'website',
      error: 'Website is required and must be a valid URL with domain',
      error_type: 'invalid_website',
      expected_format: 'Valid URL with domain (http/https)'
    });
  } else {
    result.normalizedData.website = record.website;
  }

  // 6. company_linkedin_url → optional, but if present must contain "linkedin.com"
  if (record.company_linkedin_url !== null && record.company_linkedin_url !== undefined && record.company_linkedin_url !== '') {
    if (!record.company_linkedin_url.toLowerCase().includes('linkedin.com')) {
      result.errors.push({
        field: 'company_linkedin_url',
        error: 'LinkedIn URL must contain "linkedin.com"',
        error_type: 'invalid_linkedin_domain',
        expected_format: 'Valid LinkedIn URL containing "linkedin.com"'
      });
    } else if (!isValidUrl(record.company_linkedin_url)) {
      result.errors.push({
        field: 'company_linkedin_url',
        error: 'LinkedIn URL must be a valid URL format',
        error_type: 'invalid_linkedin_format',
        expected_format: 'Valid LinkedIn URL containing "linkedin.com"'
      });
    } else {
      result.normalizedData.company_linkedin_url = record.company_linkedin_url;
    }
  }

  // 7. Address fields → must not be null
  const addressFields = [
    { field: 'company_street', name: 'Company Street' },
    { field: 'company_city', name: 'Company City' },
    { field: 'company_state', name: 'Company State' },
    { field: 'company_country', name: 'Company Country' },
    { field: 'company_address', name: 'Company Address' }
  ];

  for (const { field, name } of addressFields) {
    if (!record[field] || record[field].toString().trim().length === 0) {
      result.errors.push({
        field: field,
        error: `${name} is required and cannot be empty`,
        error_type: `missing_${field}`,
        expected_format: 'Non-empty string'
      });
    } else {
      result.normalizedData[field] = record[field].toString().trim();
    }
  }

  // 8. company_postal_code → must be present, basic alphanumeric check
  if (!record.company_postal_code || record.company_postal_code.toString().trim().length === 0) {
    result.errors.push({
      field: 'company_postal_code',
      error: 'Postal code is required',
      error_type: 'missing_postal_code',
      expected_format: 'Alphanumeric postal code'
    });
  } else {
    const postal = record.company_postal_code.toString().trim();
    if (!/^[A-Za-z0-9\s\-]+$/.test(postal)) {
      result.errors.push({
        field: 'company_postal_code',
        error: 'Postal code must be alphanumeric (letters, numbers, spaces, hyphens only)',
        error_type: 'invalid_postal_code_format',
        expected_format: 'Alphanumeric postal code'
      });
    } else {
      result.normalizedData.company_postal_code = postal;
    }
  }

  // 9. company_phone → must be present, numeric digits (allow +, -, () formatting)
  if (!record.company_phone || record.company_phone.toString().trim().length === 0) {
    result.errors.push({
      field: 'company_phone',
      error: 'Company phone is required',
      error_type: 'missing_phone',
      expected_format: 'Phone number with digits (may include +, -, (), spaces)'
    });
  } else {
    const phone = record.company_phone.toString().trim();
    const digits = phone.replace(/[^\d]/g, '');

    if (digits.length < 7) {
      result.errors.push({
        field: 'company_phone',
        error: 'Phone number must contain at least 7 digits',
        error_type: 'phone_too_short',
        expected_format: 'Phone number with at least 7 digits'
      });
    } else if (digits.length > 15) {
      result.errors.push({
        field: 'company_phone',
        error: 'Phone number cannot contain more than 15 digits',
        error_type: 'phone_too_long',
        expected_format: 'Phone number with maximum 15 digits'
      });
    } else if (!/^[\d\s\+\-\(\)\.x]+$/.test(phone)) {
      result.errors.push({
        field: 'company_phone',
        error: 'Phone number contains invalid characters',
        error_type: 'invalid_phone_characters',
        expected_format: 'Phone number with digits and standard formatting (+, -, (), spaces, x)'
      });
    } else {
      result.normalizedData.company_phone = phone;
    }
  }

  // Set overall validation result
  result.success = result.errors.length === 0;
  if (!result.success) {
    result.field = result.errors[0].field;
    result.message = result.errors[0].error;
  }

  return result;
}

/**
 * Step 2A Core Column Validation Functions
 * These functions are excluded from Step 2A scope - kept for compatibility
 */

/**
 * Validate URL format with comprehensive checks
 */
export function isValidUrl(urlString) {
  if (!urlString || typeof urlString !== 'string') {
    return false;
  }

  try {
    const url = new URL(urlString.trim());

    // Must be HTTP or HTTPS
    if (url.protocol !== 'http:' && url.protocol !== 'https:') {
      return false;
    }

    // Must have a valid hostname
    if (!url.hostname || url.hostname.length === 0) {
      return false;
    }

    // Basic domain validation
    if (!url.hostname.includes('.')) {
      return false;
    }

    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Normalize state name/code to 2-letter US state code
 */
export function normalizeStateCode(state) {
  if (!state) return null;

  const stateStr = state.toString().trim().toLowerCase();

  // If already 2-letter code, validate it
  if (stateStr.length === 2) {
    const upperCode = stateStr.toUpperCase();
    return US_STATES[upperCode] ? upperCode : null;
  }

  // Map full state names to codes
  const stateMapping = {
    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
    'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
    'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
    'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
    'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
    'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
    'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
    'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
    'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
    'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
    'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
    'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
    'wisconsin': 'WI', 'wyoming': 'WY', 'district of columbia': 'DC'
  };

  return stateMapping[stateStr] || null;
}

/**
 * Parse employee count - Step 2A requirements: integer between 1 and 100,000
 */
export function parseEmployeeCount(employeeStr) {
  if (!employeeStr) return null;

  const str = employeeStr.toString().trim().toLowerCase();

  // Reject common invalid formats
  const invalidPatterns = [
    '+', '-', 'n/a', 'unknown', 'range', 'varies',
    'tbd', 'to be determined', '~', 'approximately',
    'about', 'circa', 'roughly', 'around'
  ];

  for (const pattern of invalidPatterns) {
    if (str.includes(pattern)) {
      return null;
    }
  }

  // Remove common formatting characters
  const cleanStr = str.replace(/[,\s]/g, '');

  const parsed = parseInt(cleanStr);

  // Step 2A: Must be valid integer between 1 and 100,000
  if (isNaN(parsed) || parsed < 1 || parsed > 100000) {
    return null;
  }

  return parsed;
}

/**
 * Valid US state codes for validation
 */
const US_STATES = {
  'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
  'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
  'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
  'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
  'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
  'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
  'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
  'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
  'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
  'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
  'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
  'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
  'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
};

/**
 * Regex patterns for additional validation
 */
export const VALIDATION_PATTERNS = {
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  phone: /^\+?[\d\s\-\(\)]{10,}$/,
  url: /^https?:\/\/.+\..+/i,
  linkedin: /linkedin\.com\/(?:company\/|in\/)/i,
  twitter: /(twitter\.com|x\.com)\//i,
  facebook: /facebook\.com\//i
};