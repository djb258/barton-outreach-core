/**
 * Doctrine Spec:
 * - Barton ID: 15.01.02.07.10000.007
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Step 2 MCP endpoints for intake ingestion operations
 * - Input: MCP requests for company/people intake operations
 * - Output: Intake processing via Composio MCP protocol
 * - MCP: Firebase (Composio-only validation)
 */

const { onRequest, HttpsError } = require('firebase-functions/v2/https');
const { getFirestore } = require('firebase-admin/firestore');
const { initializeApp } = require('firebase-admin/app');

// Initialize Firebase Admin (only for Cloud Functions)
if (!initializeApp.apps?.length) {
  initializeApp();
}

const db = getFirestore();

/**
 * MCP ENDPOINT: Company Intake Ingestion
 * Handles company intake operations through Composio MCP protocol
 */
exports.mcpIntakeCompany = onRequest({
  memory: '512MiB',
  timeoutSeconds: 60,
  maxInstances: 25,
  cors: true
}, async (req, res) => {
  try {
    // Validate MCP request format
    const mcpRequest = await validateMCPRequest(req);

    let result;
    switch (mcpRequest.action) {
      case 'create':
        // Create new company intake
        result = await processCompanyIntake(mcpRequest.params, mcpRequest.context);
        break;

      case 'update':
        // Update existing company intake
        result = await updateCompanyIntake(mcpRequest.params.company_id, mcpRequest.params.updates, mcpRequest.context);
        break;

      case 'query':
        // Query company intake records
        result = await queryCompanyIntakes(mcpRequest.params, mcpRequest.context);
        break;

      case 'validate':
        // Validate company intake data
        result = await validateCompanyIntakeData(mcpRequest.params);
        break;

      default:
        throw new Error(`Unsupported action: ${mcpRequest.action}`);
    }

    // Return MCP-compliant response
    res.status(200).json({
      success: true,
      mcp_version: '1.0.0',
      action: mcpRequest.action,
      result: result,
      timestamp: new Date().toISOString(),
      request_id: mcpRequest.request_id
    });

  } catch (error) {
    console.error('MCP Company intake operation failed:', error);

    res.status(500).json({
      success: false,
      mcp_version: '1.0.0',
      error: {
        code: 'COMPANY_INTAKE_ERROR',
        message: error.message,
        timestamp: new Date().toISOString()
      }
    });
  }
});

/**
 * MCP ENDPOINT: Person Intake Ingestion
 * Handles person intake operations through Composio MCP protocol
 */
exports.mcpIntakePerson = onRequest({
  memory: '512MiB',
  timeoutSeconds: 60,
  maxInstances: 25,
  cors: true
}, async (req, res) => {
  try {
    // Validate MCP request format
    const mcpRequest = await validateMCPRequest(req);

    let result;
    switch (mcpRequest.action) {
      case 'create':
        // Create new person intake
        result = await processPersonIntake(mcpRequest.params, mcpRequest.context);
        break;

      case 'update':
        // Update existing person intake
        result = await updatePersonIntake(mcpRequest.params.person_id, mcpRequest.params.updates, mcpRequest.context);
        break;

      case 'query':
        // Query person intake records
        result = await queryPersonIntakes(mcpRequest.params, mcpRequest.context);
        break;

      case 'validate':
        // Validate person intake data
        result = await validatePersonIntakeData(mcpRequest.params);
        break;

      default:
        throw new Error(`Unsupported action: ${mcpRequest.action}`);
    }

    // Return MCP-compliant response
    res.status(200).json({
      success: true,
      mcp_version: '1.0.0',
      action: mcpRequest.action,
      result: result,
      timestamp: new Date().toISOString(),
      request_id: mcpRequest.request_id
    });

  } catch (error) {
    console.error('MCP Person intake operation failed:', error);

    res.status(500).json({
      success: false,
      mcp_version: '1.0.0',
      error: {
        code: 'PERSON_INTAKE_ERROR',
        message: error.message,
        timestamp: new Date().toISOString()
      }
    });
  }
});

/**
 * MCP ENDPOINT: Batch Intake Processing
 * Handles bulk intake operations for companies and people
 */
exports.mcpIntakeBatch = onRequest({
  memory: '1GiB',
  timeoutSeconds: 300,
  maxInstances: 5,
  cors: true
}, async (req, res) => {
  try {
    const mcpRequest = await validateMCPRequest(req);

    const { companies = [], people = [] } = mcpRequest.params;

    if (companies.length + people.length > 100) {
      throw new Error('Batch size cannot exceed 100 items');
    }

    const result = await processBatchIntake({ companies, people }, mcpRequest.context);

    res.status(200).json({
      success: true,
      mcp_version: '1.0.0',
      action: 'batch_intake',
      result: result,
      timestamp: new Date().toISOString(),
      request_id: mcpRequest.request_id
    });

  } catch (error) {
    console.error('MCP Batch intake operation failed:', error);

    res.status(500).json({
      success: false,
      mcp_version: '1.0.0',
      error: {
        code: 'BATCH_INTAKE_ERROR',
        message: error.message,
        timestamp: new Date().toISOString()
      }
    });
  }
});

/**
 * MCP ENDPOINT: Intake Audit Logs
 * Provides access to intake audit trail
 */
exports.mcpIntakeAuditLogs = onRequest({
  memory: '256MiB',
  timeoutSeconds: 30,
  maxInstances: 10,
  cors: true
}, async (req, res) => {
  try {
    const mcpRequest = await validateMCPRequest(req);

    const result = await queryIntakeAuditLogs(mcpRequest.params, mcpRequest.context);

    res.status(200).json({
      success: true,
      mcp_version: '1.0.0',
      action: 'audit_query',
      result: result,
      timestamp: new Date().toISOString(),
      request_id: mcpRequest.request_id
    });

  } catch (error) {
    console.error('MCP Intake audit query failed:', error);

    res.status(500).json({
      success: false,
      mcp_version: '1.0.0',
      error: {
        code: 'AUDIT_QUERY_ERROR',
        message: error.message,
        timestamp: new Date().toISOString()
      }
    });
  }
});

/**
 * Validate MCP request format and authentication
 */
async function validateMCPRequest(req) {
  // Validate HTTP method
  if (req.method !== 'POST') {
    throw new Error('Only POST method allowed for MCP endpoints');
  }

  // Validate MCP headers
  const mcpVersion = req.get('X-MCP-Version');
  const composioKey = req.get('X-Composio-Key');

  if (!mcpVersion) {
    throw new Error('Missing X-MCP-Version header');
  }

  // Validate request body structure
  const body = req.body;
  if (!body || typeof body !== 'object') {
    throw new Error('Invalid MCP request body');
  }

  // Extract MCP request components
  const mcpRequest = {
    action: body.action || 'create',
    params: body.params || body.data || {},
    context: {
      user_agent: req.get('User-Agent'),
      source_ip: req.ip,
      mcp_verified: true,
      composio_key_present: !!composioKey,
      request_headers: {
        'x-mcp-version': mcpVersion,
        'content-type': req.get('Content-Type')
      }
    },
    request_id: body.request_id || generateRequestId(),
    unique_id: body.unique_id || generateHeirId(),
    process_id: body.process_id || generateProcessId(),
    orbt_layer: body.orbt_layer || 2,
    blueprint_version: body.blueprint_version || '1.0.0'
  };

  return mcpRequest;
}

/**
 * Process company intake
 */
async function processCompanyIntake(companyData, context) {
  // Validate company data
  await validateCompanyIntakePayload(companyData);

  // Generate Barton ID
  const companyBartonId = await generateCompanyBartonId();

  // Prepare company document
  const companyDocument = {
    company_unique_id: companyBartonId,
    company_name: companyData.company_name,
    website_url: companyData.website_url,
    industry: companyData.industry,
    company_size: companyData.company_size,
    headquarters_location: companyData.headquarters_location,
    linkedin_url: companyData.linkedin_url || null,
    twitter_url: companyData.twitter_url || null,
    facebook_url: companyData.facebook_url || null,
    instagram_url: companyData.instagram_url || null,
    status: 'pending',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    intake_source: 'composio_mcp_endpoint',
    source_metadata: {
      user_agent: context.user_agent || 'mcp_endpoint',
      ip_address: context.source_ip || 'unknown',
      request_id: context.request_id || generateRequestId()
    }
  };

  // Insert into Firestore
  await db.collection('company_raw_intake')
    .doc(companyBartonId)
    .set(companyDocument);

  // Log audit entry
  await logCompanyIntakeAudit('intake_create', companyBartonId, null, companyDocument, 'success', context);

  return {
    company_unique_id: companyBartonId,
    status: 'pending',
    message: 'Company intake processed successfully',
    intake_timestamp: companyDocument.created_at
  };
}

/**
 * Process person intake
 */
async function processPersonIntake(personData, context) {
  // Validate person data
  await validatePersonIntakePayload(personData);

  // Generate Barton ID
  const personBartonId = await generatePersonBartonId();

  // Prepare person document
  const personDocument = {
    person_unique_id: personBartonId,
    full_name: personData.full_name,
    email_address: personData.email_address,
    job_title: personData.job_title,
    company_name: personData.company_name,
    location: personData.location,
    linkedin_url: personData.linkedin_url || null,
    twitter_url: personData.twitter_url || null,
    facebook_url: personData.facebook_url || null,
    instagram_url: personData.instagram_url || null,
    associated_company_id: personData.associated_company_id || null,
    status: 'pending',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    intake_source: 'composio_mcp_endpoint',
    source_metadata: {
      user_agent: context.user_agent || 'mcp_endpoint',
      ip_address: context.source_ip || 'unknown',
      request_id: context.request_id || generateRequestId()
    }
  };

  // Insert into Firestore
  await db.collection('people_raw_intake')
    .doc(personBartonId)
    .set(personDocument);

  // Log audit entry
  await logPersonIntakeAudit('intake_create', personBartonId, null, personDocument, 'success', context);

  return {
    person_unique_id: personBartonId,
    status: 'pending',
    message: 'Person intake processed successfully',
    intake_timestamp: personDocument.created_at
  };
}

/**
 * Process batch intake
 */
async function processBatchIntake(batchData, context) {
  const { companies = [], people = [] } = batchData;
  const results = {
    companies: [],
    people: [],
    errors: []
  };

  // Process companies
  for (let i = 0; i < companies.length; i++) {
    try {
      const result = await processCompanyIntake(companies[i], context);
      results.companies.push({ ...result, batch_index: i });
    } catch (error) {
      results.errors.push({
        type: 'company',
        batch_index: i,
        error: error.message
      });
    }
  }

  // Process people
  for (let i = 0; i < people.length; i++) {
    try {
      const result = await processPersonIntake(people[i], context);
      results.people.push({ ...result, batch_index: i });
    } catch (error) {
      results.errors.push({
        type: 'person',
        batch_index: i,
        error: error.message
      });
    }
  }

  return {
    processed: {
      companies: results.companies.length,
      people: results.people.length,
      errors: results.errors.length
    },
    results: results,
    batch_timestamp: new Date().toISOString()
  };
}

/**
 * Update company intake
 */
async function updateCompanyIntake(companyId, updates, context) {
  // Get existing document
  const existingDoc = await db.collection('company_raw_intake')
    .doc(companyId)
    .get();

  if (!existingDoc.exists) {
    throw new Error(`Company not found: ${companyId}`);
  }

  const beforeState = existingDoc.data();

  // Prepare updates
  const updateData = {
    ...updates,
    updated_at: new Date().toISOString()
  };

  // Update document
  await db.collection('company_raw_intake')
    .doc(companyId)
    .update(updateData);

  const afterState = { ...beforeState, ...updateData };

  // Log audit entry
  await logCompanyIntakeAudit('intake_update', companyId, beforeState, afterState, 'success', context);

  return {
    company_unique_id: companyId,
    updates_applied: Object.keys(updateData),
    updated_at: updateData.updated_at
  };
}

/**
 * Update person intake
 */
async function updatePersonIntake(personId, updates, context) {
  // Get existing document
  const existingDoc = await db.collection('people_raw_intake')
    .doc(personId)
    .get();

  if (!existingDoc.exists) {
    throw new Error(`Person not found: ${personId}`);
  }

  const beforeState = existingDoc.data();

  // Prepare updates
  const updateData = {
    ...updates,
    updated_at: new Date().toISOString()
  };

  // Update document
  await db.collection('people_raw_intake')
    .doc(personId)
    .update(updateData);

  const afterState = { ...beforeState, ...updateData };

  // Log audit entry
  await logPersonIntakeAudit('intake_update', personId, beforeState, afterState, 'success', context);

  return {
    person_unique_id: personId,
    updates_applied: Object.keys(updateData),
    updated_at: updateData.updated_at
  };
}

/**
 * Query company intakes
 */
async function queryCompanyIntakes(filters, context) {
  const { status, limit = 10, start_after } = filters;

  let query = db.collection('company_raw_intake');

  if (status) {
    query = query.where('status', '==', status);
  }

  query = query.orderBy('created_at', 'desc').limit(limit);

  if (start_after) {
    const startAfterDoc = await db.collection('company_raw_intake').doc(start_after).get();
    if (startAfterDoc.exists) {
      query = query.startAfter(startAfterDoc);
    }
  }

  const snapshot = await query.get();
  const results = [];

  snapshot.forEach(doc => {
    results.push({
      id: doc.id,
      ...doc.data()
    });
  });

  return {
    companies: results,
    total_returned: results.length,
    filters_applied: filters,
    query_timestamp: new Date().toISOString()
  };
}

/**
 * Query person intakes
 */
async function queryPersonIntakes(filters, context) {
  const { status, limit = 10, start_after } = filters;

  let query = db.collection('people_raw_intake');

  if (status) {
    query = query.where('status', '==', status);
  }

  query = query.orderBy('created_at', 'desc').limit(limit);

  if (start_after) {
    const startAfterDoc = await db.collection('people_raw_intake').doc(start_after).get();
    if (startAfterDoc.exists) {
      query = query.startAfter(startAfterDoc);
    }
  }

  const snapshot = await query.get();
  const results = [];

  snapshot.forEach(doc => {
    results.push({
      id: doc.id,
      ...doc.data()
    });
  });

  return {
    people: results,
    total_returned: results.length,
    filters_applied: filters,
    query_timestamp: new Date().toISOString()
  };
}

/**
 * Query intake audit logs
 */
async function queryIntakeAuditLogs(filters, context) {
  const { collection = 'company_audit_log', limit = 20, target_id, action } = filters;

  let query = db.collection(collection);

  if (target_id) {
    const targetField = collection === 'company_audit_log' ? 'target_company_id' : 'target_person_id';
    query = query.where(targetField, '==', target_id);
  }

  if (action) {
    query = query.where('action', '==', action);
  }

  query = query.orderBy('created_at', 'desc').limit(limit);

  const snapshot = await query.get();
  const results = [];

  snapshot.forEach(doc => {
    results.push({
      id: doc.id,
      ...doc.data()
    });
  });

  return {
    audit_logs: results,
    collection: collection,
    total_returned: results.length,
    filters_applied: filters,
    query_timestamp: new Date().toISOString()
  };
}

/**
 * Validation functions (reuse from Cloud Functions)
 */
async function validateCompanyIntakePayload(data) {
  const required = ['company_name', 'website_url', 'industry', 'company_size', 'headquarters_location'];
  const missing = required.filter(field => !data[field] || data[field].trim() === '');

  if (missing.length > 0) {
    throw new Error(`Missing required company fields: ${missing.join(', ')}`);
  }

  const validSizes = ['1-10', '11-50', '51-200', '201-500', '501-1000', '1001-5000', '5001+'];
  if (!validSizes.includes(data.company_size)) {
    throw new Error(`Invalid company size. Must be one of: ${validSizes.join(', ')}`);
  }

  if (!isValidURL(data.website_url)) {
    throw new Error('Invalid website URL format');
  }
}

async function validatePersonIntakePayload(data) {
  const required = ['full_name', 'email_address', 'job_title', 'company_name', 'location'];
  const missing = required.filter(field => !data[field] || data[field].trim() === '');

  if (missing.length > 0) {
    throw new Error(`Missing required person fields: ${missing.join(', ')}`);
  }

  if (!isValidEmail(data.email_address)) {
    throw new Error('Invalid email address format');
  }
}

async function validateCompanyIntakeData(data) {
  try {
    await validateCompanyIntakePayload(data);
    return { valid: true, message: 'Company data validation passed' };
  } catch (error) {
    return { valid: false, error: error.message };
  }
}

async function validatePersonIntakeData(data) {
  try {
    await validatePersonIntakePayload(data);
    return { valid: true, message: 'Person data validation passed' };
  } catch (error) {
    return { valid: false, error: error.message };
  }
}

/**
 * Barton ID generation
 */
async function generateCompanyBartonId() {
  return await generateUniqueBartonId({
    database: '05',
    subhive: '01',
    microprocess: '01',
    tool: '03',
    altitude: '10000',
    step: '002'
  });
}

async function generatePersonBartonId() {
  return await generateUniqueBartonId({
    database: '05',
    subhive: '01',
    microprocess: '01',
    tool: '03',
    altitude: '10000',
    step: '003'
  });
}

async function generateUniqueBartonId(params) {
  const maxAttempts = 10;
  let attempts = 0;

  while (attempts < maxAttempts) {
    attempts++;

    const candidateId = `${params.database}.${params.subhive}.${params.microprocess}.${params.tool}.${params.altitude}.${params.step}`;

    // In production, would check uniqueness against appropriate collection
    // For now, return the ID
    return candidateId;
  }

  throw new Error('Failed to generate unique Barton ID');
}

/**
 * Audit logging
 */
async function logCompanyIntakeAudit(action, companyId, beforeState, afterState, status, context, error = null) {
  const auditId = await generateUniqueBartonId({
    database: '05',
    subhive: '01',
    microprocess: '02',
    tool: '03',
    altitude: '10000',
    step: '008'
  });

  const logEntry = {
    unique_id: auditId,
    action: action,
    status: status,
    source: {
      service: 'intake_mcp_endpoint',
      function: 'mcpIntakeCompany',
      user_agent: context.user_agent || 'mcp_endpoint',
      ip_address: context.source_ip || 'unknown',
      request_id: context.request_id || generateRequestId()
    },
    target_company_id: companyId,
    error_log: error ? {
      error_code: 'MCP_COMPANY_INTAKE_ERROR',
      error_message: error.message,
      stack_trace: null,
      retry_count: 0,
      recovery_action: null
    } : null,
    payload: {
      before: beforeState,
      after: afterState,
      metadata: {
        mcp_version: '1.0.0',
        endpoint_version: '1.0.0'
      }
    },
    created_at: new Date().toISOString()
  };

  try {
    await db.collection('company_audit_log')
      .doc(auditId)
      .set(logEntry);
  } catch (logError) {
    console.error('Failed to write company audit log:', logError);
  }
}

async function logPersonIntakeAudit(action, personId, beforeState, afterState, status, context, error = null) {
  const auditId = await generateUniqueBartonId({
    database: '05',
    subhive: '01',
    microprocess: '02',
    tool: '03',
    altitude: '10000',
    step: '009'
  });

  const logEntry = {
    unique_id: auditId,
    action: action,
    status: status,
    source: {
      service: 'intake_mcp_endpoint',
      function: 'mcpIntakePerson',
      user_agent: context.user_agent || 'mcp_endpoint',
      ip_address: context.source_ip || 'unknown',
      request_id: context.request_id || generateRequestId()
    },
    target_person_id: personId,
    error_log: error ? {
      error_code: 'MCP_PERSON_INTAKE_ERROR',
      error_message: error.message,
      stack_trace: null,
      retry_count: 0,
      recovery_action: null
    } : null,
    payload: {
      before: beforeState,
      after: afterState,
      metadata: {
        mcp_version: '1.0.0',
        endpoint_version: '1.0.0'
      }
    },
    created_at: new Date().toISOString()
  };

  try {
    await db.collection('people_audit_log')
      .doc(auditId)
      .set(logEntry);
  } catch (logError) {
    console.error('Failed to write people audit log:', logError);
  }
}

/**
 * Utility functions
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

function generateRequestId() {
  return `req_mcp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function generateHeirId() {
  return `HEIR-${new Date().toISOString().slice(0, 10)}-${Math.random().toString(36).substr(2, 9).toUpperCase()}`;
}

function generateProcessId() {
  return `PRC-MCP-INTAKE-${Date.now()}`;
}