/**
 * Auto-Fix Handler Service
 * Step 2B of Barton Doctrine Pipeline - Automatic data correction
 * Handles quick corrections: formatting, normalization, pattern fixes
 * Uses Standard Composio MCP Pattern for all database operations
 */

import StandardComposioNeonBridge from '../api/lib/standard-composio-neon-bridge.js';
import { normalizeStateCode, isValidUrl, parseEmployeeCount } from '../utils/validation-schemas.js';

/**
 * Main auto-fix handler - attempts to fix validation failures
 */
export async function processAutoFix(validationFailureRecord) {
  const startTime = Date.now();

  try {
    console.log(`[AUTO-FIX] Processing ${validationFailureRecord.error_type} for record ${validationFailureRecord.record_id}`);

    const fixResult = await applyAutoFix(validationFailureRecord);

    const processingTime = Date.now() - startTime;

    return {
      success: fixResult.success,
      originalValue: validationFailureRecord.raw_value,
      fixedValue: fixResult.fixedValue,
      confidence: fixResult.confidence,
      processingTime,
      method: fixResult.method,
      metadata: {
        error_type: validationFailureRecord.error_type,
        error_field: validationFailureRecord.error_field,
        handler: 'auto_fix',
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    };

  } catch (error) {
    console.error('[AUTO-FIX] Processing failed:', error);
    return {
      success: false,
      error: error.message,
      processingTime: Date.now() - startTime,
      metadata: {
        error_type: validationFailureRecord.error_type,
        handler: 'auto_fix'
      }
    };
  }
}

/**
 * Apply appropriate fix based on error type
 */
async function applyAutoFix(record) {
  const { error_type, error_field, raw_value } = record;

  switch (error_type) {
    case 'missing_state':
    case 'invalid_state':
    case 'bad_state_format':
      return fixStateValue(raw_value, error_field);

    case 'invalid_url':
    case 'missing_protocol':
    case 'bad_url_format':
      return fixUrlValue(raw_value, error_field);

    case 'bad_phone_format':
    case 'invalid_phone':
      return fixPhoneValue(raw_value, error_field);

    case 'invalid_employee_count':
    case 'bad_employee_format':
      return fixEmployeeCountValue(raw_value, error_field);

    case 'missing_https':
      return fixHttpsProtocol(raw_value, error_field);

    case 'extra_whitespace':
    case 'formatting_issue':
      return fixFormattingIssues(raw_value, error_field);

    case 'case_sensitivity':
      return fixCaseIssues(raw_value, error_field);

    default:
      return {
        success: false,
        error: `No auto-fix handler for error type: ${error_type}`,
        confidence: 0.0
      };
  }
}

/**
 * Fix state-related validation failures
 */
function fixStateValue(rawValue, field) {
  if (!rawValue) {
    return {
      success: false,
      error: 'Cannot fix null/empty state value',
      confidence: 0.0
    };
  }

  const normalizedState = normalizeStateCode(rawValue.toString().trim());

  if (normalizedState) {
    return {
      success: true,
      fixedValue: normalizedState,
      confidence: 0.9,
      method: 'state_normalization',
      details: {
        original: rawValue,
        normalized: normalizedState,
        pattern: 'US_state_code'
      }
    };
  }

  return {
    success: false,
    error: `Could not normalize state: ${rawValue}`,
    confidence: 0.0
  };
}

/**
 * Fix URL validation failures
 */
function fixUrlValue(rawValue, field) {
  if (!rawValue) {
    return {
      success: false,
      error: 'Cannot fix null/empty URL',
      confidence: 0.0
    };
  }

  let url = rawValue.toString().trim();

  // Remove common prefixes that aren't protocols
  url = url.replace(/^(www\.|http\/\/|https\/\/)/i, '');

  // Add https protocol if missing
  if (!url.match(/^https?:\/\//i)) {
    url = 'https://' + url;
  }

  // Fix double protocols
  url = url.replace(/^(https?):\/\/(https?):\/\//i, '$1://');

  // Validate the fixed URL
  if (isValidUrl(url)) {
    return {
      success: true,
      fixedValue: url,
      confidence: 0.85,
      method: 'url_protocol_fix',
      details: {
        original: rawValue,
        fixed: url,
        changes: ['added_protocol', 'normalized_format']
      }
    };
  }

  return {
    success: false,
    error: `Could not fix URL: ${rawValue}`,
    confidence: 0.0
  };
}

/**
 * Fix phone number validation failures
 */
function fixPhoneValue(rawValue, field) {
  if (!rawValue) {
    return {
      success: false,
      error: 'Cannot fix null/empty phone',
      confidence: 0.0
    };
  }

  let phone = rawValue.toString().trim();

  // Remove common formatting characters
  phone = phone.replace(/[\s\-\(\)\+\.]/g, '');

  // Add US country code if missing and looks like US number
  if (phone.length === 10 && /^\d{10}$/.test(phone)) {
    phone = '1' + phone;
  }

  // Format as E.164 if it looks valid
  if (phone.length === 11 && phone.startsWith('1') && /^\d{11}$/.test(phone)) {
    const formattedPhone = `+${phone}`;

    return {
      success: true,
      fixedValue: formattedPhone,
      confidence: 0.8,
      method: 'phone_normalization',
      details: {
        original: rawValue,
        cleaned: phone,
        formatted: formattedPhone,
        format: 'E164'
      }
    };
  }

  return {
    success: false,
    error: `Could not normalize phone: ${rawValue}`,
    confidence: 0.0
  };
}

/**
 * Fix employee count validation failures
 */
function fixEmployeeCountValue(rawValue, field) {
  if (!rawValue) {
    return {
      success: false,
      error: 'Cannot fix null/empty employee count',
      confidence: 0.0
    };
  }

  const parsedCount = parseEmployeeCount(rawValue.toString());

  if (parsedCount !== null) {
    return {
      success: true,
      fixedValue: parsedCount.toString(),
      confidence: 0.9,
      method: 'employee_count_parsing',
      details: {
        original: rawValue,
        parsed: parsedCount,
        format: 'integer'
      }
    };
  }

  return {
    success: false,
    error: `Could not parse employee count: ${rawValue}`,
    confidence: 0.0
  };
}

/**
 * Fix HTTPS protocol issues
 */
function fixHttpsProtocol(rawValue, field) {
  if (!rawValue) {
    return {
      success: false,
      error: 'Cannot fix null/empty URL for HTTPS upgrade',
      confidence: 0.0
    };
  }

  let url = rawValue.toString().trim();

  if (url.startsWith('http://')) {
    const httpsUrl = url.replace(/^http:\/\//, 'https://');

    return {
      success: true,
      fixedValue: httpsUrl,
      confidence: 0.7, // Lower confidence as HTTPS might not be supported
      method: 'https_protocol_upgrade',
      details: {
        original: rawValue,
        upgraded: httpsUrl,
        change: 'http_to_https'
      }
    };
  }

  return {
    success: false,
    error: `URL does not use HTTP protocol: ${rawValue}`,
    confidence: 0.0
  };
}

/**
 * Fix general formatting issues
 */
function fixFormattingIssues(rawValue, field) {
  if (!rawValue) {
    return {
      success: false,
      error: 'Cannot fix null/empty value',
      confidence: 0.0
    };
  }

  let fixed = rawValue.toString();
  const changes = [];

  // Trim whitespace
  const trimmed = fixed.trim();
  if (trimmed !== fixed) {
    fixed = trimmed;
    changes.push('trimmed_whitespace');
  }

  // Remove extra spaces
  const spacesFixed = fixed.replace(/\s+/g, ' ');
  if (spacesFixed !== fixed) {
    fixed = spacesFixed;
    changes.push('normalized_spaces');
  }

  // Remove common unwanted characters
  const cleanedFixed = fixed.replace(/[""'']/g, '"').replace(/[–—]/g, '-');
  if (cleanedFixed !== fixed) {
    fixed = cleanedFixed;
    changes.push('normalized_characters');
  }

  if (changes.length > 0) {
    return {
      success: true,
      fixedValue: fixed,
      confidence: 0.95,
      method: 'formatting_cleanup',
      details: {
        original: rawValue,
        fixed: fixed,
        changes: changes
      }
    };
  }

  return {
    success: false,
    error: 'No formatting issues found',
    confidence: 0.0
  };
}

/**
 * Fix case sensitivity issues
 */
function fixCaseIssues(rawValue, field) {
  if (!rawValue) {
    return {
      success: false,
      error: 'Cannot fix null/empty value',
      confidence: 0.0
    };
  }

  const original = rawValue.toString();
  let fixed = original;

  // Apply field-specific case fixes
  if (field && field.toLowerCase().includes('name')) {
    // Title case for names
    fixed = original.toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
  } else if (field && field.toLowerCase().includes('email')) {
    // Lowercase for emails
    fixed = original.toLowerCase();
  } else if (field && field.toLowerCase().includes('state')) {
    // Uppercase for state codes
    fixed = original.toUpperCase();
  } else {
    // Default: title case
    fixed = original.toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
  }

  if (fixed !== original) {
    return {
      success: true,
      fixedValue: fixed,
      confidence: 0.8,
      method: 'case_normalization',
      details: {
        original: original,
        fixed: fixed,
        field_type: field,
        case_applied: field ? 'field_specific' : 'title_case'
      }
    };
  }

  return {
    success: false,
    error: 'No case issues found',
    confidence: 0.0
  };
}

/**
 * Get auto-fix capabilities for error types
 */
export function getAutoFixCapabilities() {
  return {
    supported_error_types: [
      'missing_state',
      'invalid_state',
      'bad_state_format',
      'invalid_url',
      'missing_protocol',
      'bad_url_format',
      'bad_phone_format',
      'invalid_phone',
      'invalid_employee_count',
      'bad_employee_format',
      'missing_https',
      'extra_whitespace',
      'formatting_issue',
      'case_sensitivity'
    ],
    confidence_ranges: {
      state_normalization: [0.8, 0.9],
      url_protocol_fix: [0.7, 0.9],
      phone_normalization: [0.7, 0.8],
      employee_count_parsing: [0.85, 0.95],
      https_protocol_upgrade: [0.6, 0.8],
      formatting_cleanup: [0.9, 0.98],
      case_normalization: [0.7, 0.85]
    },
    processing_speed: 'fast', // < 100ms typical
    cost: 'free',
    metadata: {
      handler_type: 'auto_fix',
      altitude: 10000,
      doctrine: 'STAMPED'
    }
  };
}

/**
 * Test auto-fix handler with sample data
 */
export async function testAutoFixHandler() {
  const testCases = [
    {
      error_type: 'invalid_state',
      error_field: 'company_state',
      raw_value: 'california',
      record_id: 999
    },
    {
      error_type: 'invalid_url',
      error_field: 'website_url',
      raw_value: 'www.example.com',
      record_id: 998
    },
    {
      error_type: 'bad_phone_format',
      error_field: 'company_phone',
      raw_value: '(555) 123-4567',
      record_id: 997
    },
    {
      error_type: 'extra_whitespace',
      error_field: 'company_name',
      raw_value: '  Test Company   LLC  ',
      record_id: 996
    }
  ];

  console.log('[AUTO-FIX] Running test cases...');
  const results = [];

  for (const testCase of testCases) {
    const result = await processAutoFix(testCase);
    results.push({
      input: testCase,
      output: result
    });
    console.log(`[AUTO-FIX] ${testCase.error_type}: ${result.success ? '✅' : '❌'} ${result.fixedValue || result.error}`);
  }

  return results;
}