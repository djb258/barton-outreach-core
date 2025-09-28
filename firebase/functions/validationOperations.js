/**
 * Doctrine Spec:
 * - Barton ID: 15.01.02.08.10000.001
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Step 2A Validator Agent Cloud Functions for company/people validation
 * - Input: Company and people documents from intake collections
 * - Output: Validated documents with status updates and error handling
 * - MCP: Firebase (Composio-only validation and updates)
 */

import { onCall } from 'firebase-functions/v2/https';
import { getFirestore } from 'firebase-admin/firestore';
import { logger } from 'firebase-functions';

// Initialize Firestore
const db = getFirestore();

/**
 * Phone number normalization utility
 * Converts phone numbers to E.164 format
 */
class PhoneNormalizer {
  constructor() {
    // Common country codes and patterns
    this.countryPatterns = {
      US: {
        code: '+1',
        pattern: /^(?:\+?1[-.\s]?)?(?:\(?([0-9]{3})\)?[-.\s]?)?([0-9]{3})[-.\s]?([0-9]{4})$/,
        format: (match) => `+1${match[1]}${match[2]}${match[3]}`
      },
      CA: {
        code: '+1',
        pattern: /^(?:\+?1[-.\s]?)?(?:\(?([0-9]{3})\)?[-.\s]?)?([0-9]{3})[-.\s]?([0-9]{4})$/,
        format: (match) => `+1${match[1]}${match[2]}${match[3]}`
      },
      UK: {
        code: '+44',
        pattern: /^(?:\+?44[-.\s]?)?(?:\(?0?([0-9]{2,4})\)?[-.\s]?)?([0-9]{3,8})$/,
        format: (match) => `+44${match[1]}${match[2]}`
      }
    };
  }

  /**
   * Normalize phone number to E.164 format
   */
  normalizePhone(phoneNumber, defaultCountry = 'US') {
    if (!phoneNumber) return null;

    // Clean the input
    const cleaned = phoneNumber.replace(/[^\d+]/g, '');

    // If already in E.164 format, validate and return
    if (cleaned.startsWith('+') && cleaned.length >= 10 && cleaned.length <= 15) {
      return cleaned;
    }

    // Try to match against country patterns
    for (const [country, config] of Object.entries(this.countryPatterns)) {
      const match = phoneNumber.match(config.pattern);
      if (match) {
        try {
          return config.format(match);
        } catch (error) {
          logger.warn(`Phone normalization failed for ${country}:`, error);
        }
      }
    }

    // Default fallback for US numbers
    if (defaultCountry === 'US' && cleaned.length === 10) {
      return `+1${cleaned}`;
    }

    if (defaultCountry === 'US' && cleaned.length === 11 && cleaned.startsWith('1')) {
      return `+${cleaned}`;
    }

    logger.warn('Could not normalize phone number:', phoneNumber);
    return null;
  }

  /**
   * Validate E.164 format
   */
  isValidE164(phoneNumber) {
    if (!phoneNumber) return false;
    return /^\+[1-9]\d{1,14}$/.test(phoneNumber);
  }
}

/**
 * Company validation utility
 */
class CompanyValidator {
  constructor() {
    this.phoneNormalizer = new PhoneNormalizer();
    this.requiredFields = ['company_name', 'website_url', 'phone_number', 'employee_count'];
  }

  /**
   * Validate company document
   */
  async validateCompany(companyDoc) {
    const validationResult = {
      isValid: true,
      errors: [],
      warnings: [],
      normalizedData: { ...companyDoc }
    };

    // Check required fields
    for (const field of this.requiredFields) {
      if (!companyDoc[field] || companyDoc[field] === '') {
        validationResult.isValid = false;
        validationResult.errors.push({
          field: field,
          error: 'required_field_missing',
          message: `Required field '${field}' is missing or empty`
        });
      }
    }

    // Validate and normalize phone number
    if (companyDoc.phone_number) {
      const normalizedPhone = this.phoneNormalizer.normalizePhone(companyDoc.phone_number);
      if (normalizedPhone) {
        validationResult.normalizedData.phone_number = normalizedPhone;
      } else {
        validationResult.isValid = false;
        validationResult.errors.push({
          field: 'phone_number',
          error: 'invalid_phone_format',
          message: 'Phone number could not be normalized to E.164 format'
        });
      }
    }

    // Validate website URL
    if (companyDoc.website_url && !this.isValidURL(companyDoc.website_url)) {
      validationResult.isValid = false;
      validationResult.errors.push({
        field: 'website_url',
        error: 'invalid_url_format',
        message: 'Website URL is not in valid format'
      });
    }

    // Validate employee count
    if (companyDoc.employee_count !== undefined) {
      const employeeCount = parseInt(companyDoc.employee_count);
      if (isNaN(employeeCount) || employeeCount < 0) {
        validationResult.isValid = false;
        validationResult.errors.push({
          field: 'employee_count',
          error: 'invalid_employee_count',
          message: 'Employee count must be a non-negative number'
        });
      } else {
        validationResult.normalizedData.employee_count = employeeCount;
      }
    }

    // Add validation metadata
    validationResult.normalizedData.validation_timestamp = new Date().toISOString();
    validationResult.normalizedData.validation_status = validationResult.isValid ? 'validated' : 'failed';
    validationResult.normalizedData.validation_errors = validationResult.errors;

    return validationResult;
  }

  /**
   * Simple URL validation
   */
  isValidURL(urlString) {
    try {
      const url = new URL(urlString);
      return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (error) {
      return false;
    }
  }
}

/**
 * Person validation utility
 */
class PersonValidator {
  constructor() {
    this.phoneNormalizer = new PhoneNormalizer();
    this.requiredFields = ['first_name', 'last_name'];
  }

  /**
   * Validate person document
   */
  async validatePerson(personDoc) {
    const validationResult = {
      isValid: true,
      errors: [],
      warnings: [],
      normalizedData: { ...personDoc }
    };

    // Check required fields
    for (const field of this.requiredFields) {
      if (!personDoc[field] || personDoc[field] === '') {
        validationResult.isValid = false;
        validationResult.errors.push({
          field: field,
          error: 'required_field_missing',
          message: `Required field '${field}' is missing or empty`
        });
      }
    }

    // Check that either email OR phone is provided
    const hasEmail = personDoc.email && personDoc.email.trim() !== '';
    const hasPhone = personDoc.phone_number && personDoc.phone_number.trim() !== '';

    if (!hasEmail && !hasPhone) {
      validationResult.isValid = false;
      validationResult.errors.push({
        field: 'contact_info',
        error: 'missing_contact_method',
        message: 'Either email or phone number must be provided'
      });
    }

    // Validate email if provided
    if (hasEmail && !this.isValidEmail(personDoc.email)) {
      validationResult.isValid = false;
      validationResult.errors.push({
        field: 'email',
        error: 'invalid_email_format',
        message: 'Email address is not in valid format'
      });
    }

    // Validate and normalize phone number if provided
    if (hasPhone) {
      const normalizedPhone = this.phoneNormalizer.normalizePhone(personDoc.phone_number);
      if (normalizedPhone) {
        validationResult.normalizedData.phone_number = normalizedPhone;
      } else {
        validationResult.isValid = false;
        validationResult.errors.push({
          field: 'phone_number',
          error: 'invalid_phone_format',
          message: 'Phone number could not be normalized to E.164 format'
        });
      }
    }

    // Add validation metadata
    validationResult.normalizedData.validation_timestamp = new Date().toISOString();
    validationResult.normalizedData.validation_status = validationResult.isValid ? 'validated' : 'failed';
    validationResult.normalizedData.validation_errors = validationResult.errors;

    return validationResult;
  }

  /**
   * Email validation
   */
  isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }
}

/**
 * MCP access validation
 */
async function validateMCPAccess(context, operation) {
  // Verify the request comes through Composio MCP
  const auth = context.auth;

  if (!auth || !auth.uid) {
    throw new Error('MCP_ACCESS_DENIED: Authentication required');
  }

  // Check for MCP-specific headers or tokens
  const mcpToken = context.rawRequest?.headers?.['x-composio-key'];
  if (!mcpToken) {
    throw new Error('MCP_ACCESS_DENIED: Composio MCP access required');
  }

  logger.info(`MCP access validated for operation: ${operation}`, {
    uid: auth.uid,
    operation: operation,
    timestamp: new Date().toISOString()
  });
}

/**
 * Create audit log entry
 */
async function createAuditLog(collection, documentId, operation, result, context) {
  const auditEntry = {
    document_id: documentId,
    operation_type: operation,
    timestamp: new Date().toISOString(),
    user_id: context.auth?.uid || 'system',
    mcp_trace: {
      endpoint: 'validation',
      operation: operation,
      result_status: result.isValid ? 'success' : 'failed',
      error_count: result.errors?.length || 0
    },
    validation_result: {
      is_valid: result.isValid,
      error_count: result.errors?.length || 0,
      warning_count: result.warnings?.length || 0
    },
    processed_at: new Date().toISOString()
  };

  try {
    await db.collection(collection).add(auditEntry);
    logger.info(`Audit log created for ${operation}:`, { documentId, collection });
  } catch (error) {
    logger.error('Failed to create audit log:', error);
  }
}

/**
 * Handle validation failure
 */
async function handleValidationFailure(documentData, validationResult, collection) {
  const failedDoc = {
    ...documentData,
    validation_status: 'failed',
    validation_errors: validationResult.errors,
    validation_timestamp: new Date().toISOString(),
    failed_at: new Date().toISOString(),
    retry_count: 0,
    structured_errors: validationResult.errors.map(error => ({
      field: error.field,
      error_code: error.error,
      message: error.message,
      severity: 'error',
      actionable: true
    }))
  };

  try {
    await db.collection('validation_failed').add(failedDoc);
    logger.info(`Document moved to validation_failed collection from ${collection}`);
  } catch (error) {
    logger.error('Failed to move document to validation_failed:', error);
    throw error;
  }
}

/**
 * Cloud Function: Validate Company
 */
export const validateCompany = onCall({
  memory: '512MiB',
  timeoutSeconds: 60,
  maxInstances: 50
}, async (request) => {
  const { data, auth } = request;

  try {
    // Validate MCP access
    await validateMCPAccess(request, 'validateCompany');

    logger.info('Starting company validation:', { companyId: data.company_unique_id });

    // Get company document from intake collection
    const companyDoc = await db.collection('company_raw_intake')
      .doc(data.company_unique_id)
      .get();

    if (!companyDoc.exists) {
      throw new Error(`Company document not found: ${data.company_unique_id}`);
    }

    const companyData = companyDoc.data();

    // Validate the company
    const validator = new CompanyValidator();
    const validationResult = await validator.validateCompany(companyData);

    if (validationResult.isValid) {
      // Update the intake document with validated data
      await db.collection('company_raw_intake')
        .doc(data.company_unique_id)
        .update(validationResult.normalizedData);

      logger.info('Company validation successful:', { companyId: data.company_unique_id });
    } else {
      // Handle validation failure
      await handleValidationFailure(companyData, validationResult, 'company_raw_intake');

      logger.warn('Company validation failed:', {
        companyId: data.company_unique_id,
        errors: validationResult.errors
      });
    }

    // Create audit log
    await createAuditLog('company_audit_log', data.company_unique_id, 'validate_company', validationResult, request);

    return {
      success: true,
      company_unique_id: data.company_unique_id,
      validation_status: validationResult.isValid ? 'validated' : 'failed',
      errors: validationResult.errors,
      warnings: validationResult.warnings,
      processed_at: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Company validation error:', error);

    // Create error audit log
    await createAuditLog('company_audit_log', data.company_unique_id, 'validate_company', {
      isValid: false,
      errors: [{ error: 'system_error', message: error.message }]
    }, request);

    throw error;
  }
});

/**
 * Cloud Function: Validate Person
 */
export const validatePerson = onCall({
  memory: '512MiB',
  timeoutSeconds: 60,
  maxInstances: 50
}, async (request) => {
  const { data, auth } = request;

  try {
    // Validate MCP access
    await validateMCPAccess(request, 'validatePerson');

    logger.info('Starting person validation:', { personId: data.person_unique_id });

    // Get person document from intake collection
    const personDoc = await db.collection('people_raw_intake')
      .doc(data.person_unique_id)
      .get();

    if (!personDoc.exists) {
      throw new Error(`Person document not found: ${data.person_unique_id}`);
    }

    const personData = personDoc.data();

    // Validate the person
    const validator = new PersonValidator();
    const validationResult = await validator.validatePerson(personData);

    if (validationResult.isValid) {
      // Update the intake document with validated data
      await db.collection('people_raw_intake')
        .doc(data.person_unique_id)
        .update(validationResult.normalizedData);

      logger.info('Person validation successful:', { personId: data.person_unique_id });
    } else {
      // Handle validation failure
      await handleValidationFailure(personData, validationResult, 'people_raw_intake');

      logger.warn('Person validation failed:', {
        personId: data.person_unique_id,
        errors: validationResult.errors
      });
    }

    // Create audit log
    await createAuditLog('people_audit_log', data.person_unique_id, 'validate_person', validationResult, request);

    return {
      success: true,
      person_unique_id: data.person_unique_id,
      validation_status: validationResult.isValid ? 'validated' : 'failed',
      errors: validationResult.errors,
      warnings: validationResult.warnings,
      processed_at: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Person validation error:', error);

    // Create error audit log
    await createAuditLog('people_audit_log', data.person_unique_id, 'validate_person', {
      isValid: false,
      errors: [{ error: 'system_error', message: error.message }]
    }, request);

    throw error;
  }
});

/**
 * Export validation utilities for testing
 */
export { PhoneNormalizer, CompanyValidator, PersonValidator };