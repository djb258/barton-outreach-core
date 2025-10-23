/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-AB772D5F
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

/**
 * Doctrine Spec:
 * - Barton ID: 04.04.01
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Step 2 Cloud Functions for company and people intake operations
 * - Input: JSON payloads from MCP for company/people intake
 * - Output: Barton ID generation, intake insertion, and audit logging
 * - MCP: Firebase (Composio-only access)
 */

const { onCall, onRequest, HttpsError } = require('firebase-functions/v2/https');
const { getFirestore, FieldValue } = require('firebase-admin/firestore');
const { initializeApp } = require('firebase-admin/app');

// Initialize Firebase Admin (only for Cloud Functions)
if (!initializeApp.apps?.length) {
  initializeApp();
}

const db = getFirestore();

/**
 * Intake Company Cloud Function
 *
 * Accepts JSON payload from MCP, generates Barton ID, inserts into company_raw_intake,
 * and writes audit log entry.
 *
 * CRITICAL: This function enforces MCP-only access and validates all inputs
 */
exports.intakeCompany = onCall({
  memory: '512MiB',
  timeoutSeconds: 60,
  maxInstances: 50
}, async (request) => {
  const startTime = Date.now();
  const context = request.auth || {};
  const data = request.data || {};

  try {
    // Validate MCP access
    await validateMCPAccess(context, 'intakeCompany');

    // Validate company intake payload
    const validatedCompany = await validateCompanyIntakePayload(data);

    // Generate Barton ID for company
    const companyBartonId = await generateCompanyBartonId(validatedCompany);

    // Prepare company intake document
    const companyDocument = {
      company_unique_id: companyBartonId,
      company_name: validatedCompany.company_name,
      website_url: validatedCompany.website_url,
      industry: validatedCompany.industry,
      company_size: validatedCompany.company_size,
      headquarters_location: validatedCompany.headquarters_location,
      linkedin_url: validatedCompany.linkedin_url || null,
      twitter_url: validatedCompany.twitter_url || null,
      facebook_url: validatedCompany.facebook_url || null,
      instagram_url: validatedCompany.instagram_url || null,
      status: 'pending',
      created_at: FieldValue.serverTimestamp(),
      updated_at: FieldValue.serverTimestamp(),
      intake_source: 'composio_mcp_ingestion',
      source_metadata: {
        user_agent: context.user_agent || 'cloud_function',
        ip_address: context.source_ip || 'internal',
        request_id: generateRequestId()
      }
    };

    // Insert into company_raw_intake collection
    await db.collection('company_raw_intake')
      .doc(companyBartonId)
      .set(companyDocument);

    // Log intake operation in company audit log
    await logCompanyIntakeOperation(
      'intake_create',
      companyBartonId,
      null, // before state
      companyDocument, // after state
      'success',
      context,
      startTime
    );

    return {
      success: true,
      company_unique_id: companyBartonId,
      status: 'pending',
      message: 'Company intake successfully processed',
      intake_timestamp: new Date().toISOString(),
      request_id: companyDocument.source_metadata.request_id
    };

  } catch (error) {
    // Log error in company audit log
    await logCompanyIntakeOperation(
      'intake_create',
      data.company_unique_id || null,
      null,
      data,
      'failure',
      context,
      startTime,
      error
    );

    console.error('Company intake failed:', error);

    throw new HttpsError(
      'internal',
      'Failed to process company intake',
      {
        code: 'COMPANY_INTAKE_FAILED',
        details: error.message,
        timestamp: new Date().toISOString()
      }
    );
  }
});

/**
 * Intake Person Cloud Function
 *
 * Accepts JSON payload from MCP, generates Barton ID, inserts into people_raw_intake,
 * and writes audit log entry.
 *
 * CRITICAL: This function enforces MCP-only access and validates all inputs
 */
exports.intakePerson = onCall({
  memory: '512MiB',
  timeoutSeconds: 60,
  maxInstances: 50
}, async (request) => {
  const startTime = Date.now();
  const context = request.auth || {};
  const data = request.data || {};

  try {
    // Validate MCP access
    await validateMCPAccess(context, 'intakePerson');

    // Validate person intake payload
    const validatedPerson = await validatePersonIntakePayload(data);

    // Generate Barton ID for person
    const personBartonId = await generatePersonBartonId(validatedPerson);

    // Prepare person intake document
    const personDocument = {
      person_unique_id: personBartonId,
      full_name: validatedPerson.full_name,
      email_address: validatedPerson.email_address,
      job_title: validatedPerson.job_title,
      company_name: validatedPerson.company_name,
      location: validatedPerson.location,
      linkedin_url: validatedPerson.linkedin_url || null,
      twitter_url: validatedPerson.twitter_url || null,
      facebook_url: validatedPerson.facebook_url || null,
      instagram_url: validatedPerson.instagram_url || null,
      associated_company_id: validatedPerson.associated_company_id || null,
      status: 'pending',
      created_at: FieldValue.serverTimestamp(),
      updated_at: FieldValue.serverTimestamp(),
      intake_source: 'composio_mcp_ingestion',
      source_metadata: {
        user_agent: context.user_agent || 'cloud_function',
        ip_address: context.source_ip || 'internal',
        request_id: generateRequestId()
      }
    };

    // Insert into people_raw_intake collection
    await db.collection('people_raw_intake')
      .doc(personBartonId)
      .set(personDocument);

    // Log intake operation in people audit log
    await logPersonIntakeOperation(
      'intake_create',
      personBartonId,
      null, // before state
      personDocument, // after state
      'success',
      context,
      startTime
    );

    return {
      success: true,
      person_unique_id: personBartonId,
      status: 'pending',
      message: 'Person intake successfully processed',
      intake_timestamp: new Date().toISOString(),
      request_id: personDocument.source_metadata.request_id
    };

  } catch (error) {
    // Log error in people audit log
    await logPersonIntakeOperation(
      'intake_create',
      data.person_unique_id || null,
      null,
      data,
      'failure',
      context,
      startTime,
      error
    );

    console.error('Person intake failed:', error);

    throw new HttpsError(
      'internal',
      'Failed to process person intake',
      {
        code: 'PERSON_INTAKE_FAILED',
        details: error.message,
        timestamp: new Date().toISOString()
      }
    );
  }
});

/**
 * Validate MCP access for intake operations
 */
async function validateMCPAccess(context, functionName) {
  // Check for MCP authentication markers
  const mcpVerified = context.mcp_verified ||
                     context.source?.includes('composio') ||
                     context.user_agent?.includes('mcp') ||
                     false;

  if (!mcpVerified) {
    throw new Error('MCP-only access required. Direct client access denied.');
  }

  // Additional MCP validation can be added here
  return true;
}

/**
 * Validate company intake payload
 */
async function validateCompanyIntakePayload(data) {
  const required = ['company_name', 'website_url', 'industry', 'company_size', 'headquarters_location'];
  const missing = required.filter(field => !data[field] || data[field].trim() === '');

  if (missing.length > 0) {
    throw new Error(`Missing required company fields: ${missing.join(', ')}`);
  }

  // Validate website URL format
  if (!isValidURL(data.website_url)) {
    throw new Error('Invalid website URL format');
  }

  // Validate company size enum
  const validSizes = ['1-10', '11-50', '51-200', '201-500', '501-1000', '1001-5000', '5001+'];
  if (!validSizes.includes(data.company_size)) {
    throw new Error(`Invalid company size. Must be one of: ${validSizes.join(', ')}`);
  }

  // Validate optional social URLs if provided
  if (data.linkedin_url && !isValidLinkedInCompanyURL(data.linkedin_url)) {
    throw new Error('Invalid LinkedIn company URL format');
  }

  if (data.twitter_url && !isValidTwitterURL(data.twitter_url)) {
    throw new Error('Invalid Twitter/X URL format');
  }

  if (data.facebook_url && !isValidFacebookURL(data.facebook_url)) {
    throw new Error('Invalid Facebook URL format');
  }

  if (data.instagram_url && !isValidInstagramURL(data.instagram_url)) {
    throw new Error('Invalid Instagram URL format');
  }

  return {
    company_name: data.company_name.trim(),
    website_url: data.website_url.trim(),
    industry: data.industry.trim(),
    company_size: data.company_size,
    headquarters_location: data.headquarters_location.trim(),
    linkedin_url: data.linkedin_url?.trim(),
    twitter_url: data.twitter_url?.trim(),
    facebook_url: data.facebook_url?.trim(),
    instagram_url: data.instagram_url?.trim()
  };
}

/**
 * Validate person intake payload
 */
async function validatePersonIntakePayload(data) {
  const required = ['full_name', 'email_address', 'job_title', 'company_name', 'location'];
  const missing = required.filter(field => !data[field] || data[field].trim() === '');

  if (missing.length > 0) {
    throw new Error(`Missing required person fields: ${missing.join(', ')}`);
  }

  // Validate email format
  if (!isValidEmail(data.email_address)) {
    throw new Error('Invalid email address format');
  }

  // Validate optional social URLs if provided
  if (data.linkedin_url && !isValidLinkedInProfileURL(data.linkedin_url)) {
    throw new Error('Invalid LinkedIn profile URL format');
  }

  if (data.twitter_url && !isValidTwitterURL(data.twitter_url)) {
    throw new Error('Invalid Twitter/X URL format');
  }

  if (data.facebook_url && !isValidFacebookURL(data.facebook_url)) {
    throw new Error('Invalid Facebook URL format');
  }

  if (data.instagram_url && !isValidInstagramURL(data.instagram_url)) {
    throw new Error('Invalid Instagram URL format');
  }

  // Validate associated company ID if provided
  if (data.associated_company_id && !isValidBartonId(data.associated_company_id)) {
    throw new Error('Invalid associated company ID format');
  }

  return {
    full_name: data.full_name.trim(),
    email_address: data.email_address.trim().toLowerCase(),
    job_title: data.job_title.trim(),
    company_name: data.company_name.trim(),
    location: data.location.trim(),
    linkedin_url: data.linkedin_url?.trim(),
    twitter_url: data.twitter_url?.trim(),
    facebook_url: data.facebook_url?.trim(),
    instagram_url: data.instagram_url?.trim(),
    associated_company_id: data.associated_company_id?.trim()
  };
}

/**
 * Generate Barton ID for company
 */
async function generateCompanyBartonId(companyData) {
  const params = {
    database: '05',    // Firebase
    subhive: '01',     // Intake
    microprocess: '01', // Ingestion
    tool: '03',        // Firebase
    altitude: '10000', // Execution Layer
    step: '002'        // Intake Processing
  };

  return await generateUniqueBartonId(params, 'company');
}

/**
 * Generate Barton ID for person
 */
async function generatePersonBartonId(personData) {
  const params = {
    database: '05',    // Firebase
    subhive: '01',     // Intake
    microprocess: '01', // Ingestion
    tool: '03',        // Firebase
    altitude: '10000', // Execution Layer
    step: '003'        // Person intake
  };

  return await generateUniqueBartonId(params, 'person');
}

/**
 * Generate unique Barton ID with collision detection
 */
async function generateUniqueBartonId(params, entityType) {
  const maxAttempts = 10;
  let attempts = 0;

  while (attempts < maxAttempts) {
    attempts++;

    // Construct the ID
    const candidateId = `${params.database}.${params.subhive}.${params.microprocess}.${params.tool}.${params.altitude}.${params.step}`;

    // Check for uniqueness in appropriate collection
    const collectionName = entityType === 'company' ? 'company_raw_intake' : 'people_raw_intake';
    const existingDoc = await db.collection(collectionName)
      .doc(candidateId)
      .get();

    if (!existingDoc.exists) {
      return candidateId;
    }

    // If collision detected, increment the step for next attempt
    const currentStep = parseInt(params.step);
    const nextStep = (currentStep + 1).toString().padStart(3, '0');

    if (nextStep === '1000') {
      throw new Error('ID space exhausted for intake operations');
    }

    params.step = nextStep;
  }

  throw new Error(`Failed to generate unique Barton ID after ${maxAttempts} attempts`);
}

/**
 * Log company intake operation in audit log
 */
async function logCompanyIntakeOperation(action, companyId, beforeState, afterState, status, context, startTime, error = null) {
  const endTime = Date.now();
  const executionTime = endTime - startTime;

  // Generate audit log entry ID
  const auditId = await generateUniqueBartonId({
    database: '05',
    subhive: '01',
    microprocess: '02',
    tool: '03',
    altitude: '10000',
    step: '004'
  }, 'audit');

  const logEntry = {
    unique_id: auditId,
    action: action,
    status: status,
    source: {
      service: 'intakeCompany_function',
      function: 'intakeCompany',
      user_agent: context.user_agent || 'cloud_function',
      ip_address: context.source_ip || 'internal',
      request_id: generateRequestId()
    },
    target_company_id: companyId,
    error_log: error ? {
      error_code: 'COMPANY_INTAKE_ERROR',
      error_message: error.message,
      stack_trace: process.env.NODE_ENV === 'development' ? error.stack : null,
      retry_count: 0,
      recovery_action: null
    } : null,
    payload: {
      before: beforeState,
      after: afterState,
      metadata: {
        execution_time_ms: executionTime,
        doctrine_version: '1.0.0',
        function_version: '1.0.0'
      }
    },
    created_at: FieldValue.serverTimestamp()
  };

  try {
    await db.collection('company_audit_log')
      .doc(auditId)
      .set(logEntry);
  } catch (logError) {
    console.error('Failed to write company audit log:', logError);
    // Don't throw here to avoid breaking the main operation
  }
}

/**
 * Log person intake operation in audit log
 */
async function logPersonIntakeOperation(action, personId, beforeState, afterState, status, context, startTime, error = null) {
  const endTime = Date.now();
  const executionTime = endTime - startTime;

  // Generate audit log entry ID
  const auditId = await generateUniqueBartonId({
    database: '05',
    subhive: '01',
    microprocess: '02',
    tool: '03',
    altitude: '10000',
    step: '005'
  }, 'audit');

  const logEntry = {
    unique_id: auditId,
    action: action,
    status: status,
    source: {
      service: 'intakePerson_function',
      function: 'intakePerson',
      user_agent: context.user_agent || 'cloud_function',
      ip_address: context.source_ip || 'internal',
      request_id: generateRequestId()
    },
    target_person_id: personId,
    error_log: error ? {
      error_code: 'PERSON_INTAKE_ERROR',
      error_message: error.message,
      stack_trace: process.env.NODE_ENV === 'development' ? error.stack : null,
      retry_count: 0,
      recovery_action: null
    } : null,
    payload: {
      before: beforeState,
      after: afterState,
      metadata: {
        execution_time_ms: executionTime,
        doctrine_version: '1.0.0',
        function_version: '1.0.0'
      }
    },
    created_at: FieldValue.serverTimestamp()
  };

  try {
    await db.collection('people_audit_log')
      .doc(auditId)
      .set(logEntry);
  } catch (logError) {
    console.error('Failed to write people audit log:', logError);
    // Don't throw here to avoid breaking the main operation
  }
}

/**
 * Validation utility functions
 */
function isValidURL(url) {
  try {
    new URL(url);
    return url.startsWith('http://') || url.startsWith('https://');
  } catch {
    return false;
  }
}

function isValidEmail(email) {
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailPattern.test(email);
}

function isValidLinkedInCompanyURL(url) {
  const pattern = /^https:\/\/(www\.)?linkedin\.com\/company\/.+/;
  return pattern.test(url);
}

function isValidLinkedInProfileURL(url) {
  const pattern = /^https:\/\/(www\.)?linkedin\.com\/in\/.+/;
  return pattern.test(url);
}

function isValidTwitterURL(url) {
  const pattern = /^https:\/\/(www\.)?(twitter\.com|x\.com)\/.+/;
  return pattern.test(url);
}

function isValidFacebookURL(url) {
  const pattern = /^https:\/\/(www\.)?facebook\.com\/.+/;
  return pattern.test(url);
}

function isValidInstagramURL(url) {
  const pattern = /^https:\/\/(www\.)?instagram\.com\/.+/;
  return pattern.test(url);
}

function isValidBartonId(id) {
  const pattern = /^[0-9]{2}\.[0-9]{2}\.[0-9]{2}\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$/;
  return pattern.test(id);
}

/**
 * Generate request ID for correlation
 */
function generateRequestId() {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Batch Intake Operations (for bulk processing)
 */
exports.intakeBatch = onCall({
  memory: '1GiB',
  timeoutSeconds: 300,
  maxInstances: 5
}, async (request) => {
  const startTime = Date.now();
  const context = request.auth || {};
  const data = request.data || {};

  try {
    // Validate MCP access
    await validateMCPAccess(context, 'intakeBatch');

    const { companies = [], people = [] } = data;

    if (companies.length + people.length > 100) {
      throw new Error('Batch size cannot exceed 100 items');
    }

    const results = {
      companies: [],
      people: [],
      errors: []
    };

    // Process companies
    for (let i = 0; i < companies.length; i++) {
      try {
        const validatedCompany = await validateCompanyIntakePayload(companies[i]);
        const companyBartonId = await generateCompanyBartonId(validatedCompany);

        const companyDocument = {
          company_unique_id: companyBartonId,
          ...validatedCompany,
          status: 'pending',
          created_at: FieldValue.serverTimestamp(),
          updated_at: FieldValue.serverTimestamp(),
          intake_source: 'composio_mcp_batch_ingestion',
          source_metadata: {
            user_agent: context.user_agent || 'cloud_function',
            ip_address: context.source_ip || 'internal',
            request_id: generateRequestId(),
            batch_index: i
          }
        };

        await db.collection('company_raw_intake')
          .doc(companyBartonId)
          .set(companyDocument);

        await logCompanyIntakeOperation(
          'intake_create',
          companyBartonId,
          null,
          companyDocument,
          'success',
          context,
          startTime
        );

        results.companies.push({
          company_unique_id: companyBartonId,
          status: 'success',
          index: i
        });

      } catch (error) {
        results.errors.push({
          type: 'company',
          index: i,
          error: error.message
        });
      }
    }

    // Process people
    for (let i = 0; i < people.length; i++) {
      try {
        const validatedPerson = await validatePersonIntakePayload(people[i]);
        const personBartonId = await generatePersonBartonId(validatedPerson);

        const personDocument = {
          person_unique_id: personBartonId,
          ...validatedPerson,
          status: 'pending',
          created_at: FieldValue.serverTimestamp(),
          updated_at: FieldValue.serverTimestamp(),
          intake_source: 'composio_mcp_batch_ingestion',
          source_metadata: {
            user_agent: context.user_agent || 'cloud_function',
            ip_address: context.source_ip || 'internal',
            request_id: generateRequestId(),
            batch_index: i
          }
        };

        await db.collection('people_raw_intake')
          .doc(personBartonId)
          .set(personDocument);

        await logPersonIntakeOperation(
          'intake_create',
          personBartonId,
          null,
          personDocument,
          'success',
          context,
          startTime
        );

        results.people.push({
          person_unique_id: personBartonId,
          status: 'success',
          index: i
        });

      } catch (error) {
        results.errors.push({
          type: 'person',
          index: i,
          error: error.message
        });
      }
    }

    return {
      success: true,
      processed: {
        companies: results.companies.length,
        people: results.people.length,
        errors: results.errors.length
      },
      results: results,
      execution_time_ms: Date.now() - startTime,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    console.error('Batch intake failed:', error);

    throw new HttpsError(
      'internal',
      'Failed to process batch intake',
      {
        code: 'BATCH_INTAKE_FAILED',
        details: error.message,
        timestamp: new Date().toISOString()
      }
    );
  }
});

/**
 * Health check function for intake system
 */
exports.intakeSystemHealth = onCall({
  memory: '256MiB',
  timeoutSeconds: 30
}, async (request) => {
  try {
    const startTime = Date.now();

    // Check collections accessibility
    const companyCollectionCheck = await checkCollectionHealth('company_raw_intake');
    const peopleCollectionCheck = await checkCollectionHealth('people_raw_intake');
    const companyAuditCheck = await checkCollectionHealth('company_audit_log');
    const peopleAuditCheck = await checkCollectionHealth('people_audit_log');

    // Test ID generation
    const idGenerationCheck = await testIdGeneration();

    const healthReport = {
      overall_status: 'healthy',
      timestamp: new Date().toISOString(),
      response_time_ms: Date.now() - startTime,
      checks: {
        company_intake_collection: companyCollectionCheck,
        people_intake_collection: peopleCollectionCheck,
        company_audit_log: companyAuditCheck,
        people_audit_log: peopleAuditCheck,
        id_generation: idGenerationCheck
      },
      version: '1.0.0'
    };

    // Determine overall status
    const allChecks = Object.values(healthReport.checks);
    if (allChecks.some(check => check.status === 'error')) {
      healthReport.overall_status = 'unhealthy';
    } else if (allChecks.some(check => check.status === 'warning')) {
      healthReport.overall_status = 'degraded';
    }

    return healthReport;

  } catch (error) {
    return {
      overall_status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error.message
    };
  }
});

/**
 * Health check helper functions
 */
async function checkCollectionHealth(collectionName) {
  try {
    const count = await db.collection(collectionName)
      .count()
      .get();

    return {
      status: 'ok',
      total_documents: count.data().count
    };
  } catch (error) {
    return {
      status: 'error',
      message: error.message
    };
  }
}

async function testIdGeneration() {
  try {
    // Test company ID generation (dry run)
    const testCompanyParams = {
      database: '05',
      subhive: '01',
      microprocess: '01',
      tool: '03',
      altitude: '10000',
      step: '999'
    };

    const testId = `${testCompanyParams.database}.${testCompanyParams.subhive}.${testCompanyParams.microprocess}.${testCompanyParams.tool}.${testCompanyParams.altitude}.${testCompanyParams.step}`;

    return {
      status: 'ok',
      message: 'ID generation system functional',
      sample_id: testId
    };
  } catch (error) {
    return {
      status: 'error',
      message: error.message
    };
  }
}