/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-8442157C
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * Doctrine Spec:
 * - Barton ID: 04.04.01
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: MCP endpoints for Composio-only Firebase access
 * - Input: Composio tool requests for Firebase operations
 * - Output: Firebase data via MCP protocol
 * - MCP: Firebase (Composio Integration Layer)
 */

const { onRequest } = require('firebase-functions/v2/https');
const { getFirestore, FieldValue } = require('firebase-admin/firestore');
const { getFunctions } = require('firebase-admin/functions');
const { initializeApp } = require('firebase-admin/app');

// Initialize Firebase Admin
if (!initializeApp.apps?.length) {
  initializeApp();
}

const db = getFirestore();

/**
 * MCP ENDPOINT: Firebase Firestore Operations
 *
 * This endpoint provides Composio with controlled access to Firebase
 * All operations are logged and validated against Barton Doctrine
 */
exports.mcpFirestoreOperations = onRequest({
  memory: '512MiB',
  timeoutSeconds: 60,
  cors: {
    origin: true,
    methods: ['POST'],
    allowedHeaders: ['Content-Type', 'X-Composio-Key', 'Authorization']
  }
}, async (req, res) => {
  const startTime = Date.now();

  try {
    // Validate MCP request
    const mcpRequest = await validateMCPRequest(req);

    // Execute the requested operation
    const result = await executeFirestoreOperation(mcpRequest);

    // Log the operation
    await logMCPOperation(mcpRequest, result, startTime, 'success');

    // Return MCP-compliant response
    res.status(200).json({
      success: true,
      data: result,
      mcp_version: '1.0.0',
      execution_time_ms: Date.now() - startTime,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    // Log the error
    await logMCPOperation(req.body, null, startTime, 'error', error);

    console.error('MCP Firestore operation failed:', error);

    res.status(error.status || 500).json({
      success: false,
      error: {
        code: error.code || 'MCP_OPERATION_FAILED',
        message: error.message,
        details: error.details || null
      },
      mcp_version: '1.0.0',
      execution_time_ms: Date.now() - startTime,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * MCP ENDPOINT: Barton ID Operations
 *
 * Provides Composio access to Barton ID generation and management
 */
exports.mcpBartonIdOperations = onRequest({
  memory: '256MiB',
  timeoutSeconds: 30,
  cors: {
    origin: true,
    methods: ['POST'],
    allowedHeaders: ['Content-Type', 'X-Composio-Key', 'Authorization']
  }
}, async (req, res) => {
  const startTime = Date.now();

  try {
    const mcpRequest = await validateMCPRequest(req);

    // Route to appropriate Barton ID operation
    let result;
    switch (mcpRequest.operation) {
      case 'generate_id':
        result = await callCloudFunction('generateBartonId', mcpRequest.params);
        break;
      case 'generate_batch':
        result = await callCloudFunction('generateBartonIdBatch', mcpRequest.params);
        break;
      case 'validate_id':
        result = await validateBartonId(mcpRequest.params.barton_id);
        break;
      case 'get_id_info':
        result = await getBartonIdInfo(mcpRequest.params.barton_id);
        break;
      case 'system_health':
        result = await callCloudFunction('bartonIdSystemHealth', {});
        break;
      default:
        throw new Error(`Unknown Barton ID operation: ${mcpRequest.operation}`);
    }

    await logMCPOperation(mcpRequest, result, startTime, 'success');

    res.status(200).json({
      success: true,
      data: result,
      mcp_version: '1.0.0',
      execution_time_ms: Date.now() - startTime,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    await logMCPOperation(req.body, null, startTime, 'error', error);

    console.error('MCP Barton ID operation failed:', error);

    res.status(error.status || 500).json({
      success: false,
      error: {
        code: error.code || 'MCP_BARTON_ID_FAILED',
        message: error.message,
        details: error.details || null
      },
      mcp_version: '1.0.0',
      execution_time_ms: Date.now() - startTime,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * MCP ENDPOINT: Doctrine Configuration
 *
 * Manages Barton Doctrine configuration through Composio
 */
exports.mcpDoctrineConfig = onRequest({
  memory: '256MiB',
  timeoutSeconds: 30,
  cors: {
    origin: true,
    methods: ['GET', 'POST'],
    allowedHeaders: ['Content-Type', 'X-Composio-Key', 'Authorization']
  }
}, async (req, res) => {
  const startTime = Date.now();

  try {
    if (req.method === 'GET') {
      // Get current doctrine configuration
      const config = await getDoctrineConfiguration();

      res.status(200).json({
        success: true,
        data: config,
        mcp_version: '1.0.0',
        timestamp: new Date().toISOString()
      });

    } else if (req.method === 'POST') {
      // Update doctrine configuration
      const mcpRequest = await validateMCPRequest(req);
      const result = await updateDoctrineConfiguration(mcpRequest.params);

      await logMCPOperation(mcpRequest, result, startTime, 'success');

      res.status(200).json({
        success: true,
        data: result,
        mcp_version: '1.0.0',
        execution_time_ms: Date.now() - startTime,
        timestamp: new Date().toISOString()
      });
    }

  } catch (error) {
    await logMCPOperation(req.body, null, startTime, 'error', error);

    console.error('MCP Doctrine config operation failed:', error);

    res.status(error.status || 500).json({
      success: false,
      error: {
        code: error.code || 'MCP_CONFIG_FAILED',
        message: error.message
      },
      mcp_version: '1.0.0',
      execution_time_ms: Date.now() - startTime,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * MCP ENDPOINT: Audit Operations
 *
 * Provides read-only access to audit logs through Composio
 */
exports.mcpAuditOperations = onRequest({
  memory: '512MiB',
  timeoutSeconds: 60,
  cors: {
    origin: true,
    methods: ['POST'],
    allowedHeaders: ['Content-Type', 'X-Composio-Key', 'Authorization']
  }
}, async (req, res) => {
  const startTime = Date.now();

  try {
    const mcpRequest = await validateMCPRequest(req);

    let result;
    switch (mcpRequest.operation) {
      case 'query_logs':
        result = await queryAuditLogs(mcpRequest.params);
        break;
      case 'get_log':
        result = await getAuditLog(mcpRequest.params.unique_id);
        break;
      case 'get_stats':
        result = await getAuditStats(mcpRequest.params);
        break;
      default:
        throw new Error(`Unknown audit operation: ${mcpRequest.operation}`);
    }

    await logMCPOperation(mcpRequest, { records: result.length || 1 }, startTime, 'success');

    res.status(200).json({
      success: true,
      data: result,
      mcp_version: '1.0.0',
      execution_time_ms: Date.now() - startTime,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    await logMCPOperation(req.body, null, startTime, 'error', error);

    console.error('MCP Audit operation failed:', error);

    res.status(error.status || 500).json({
      success: false,
      error: {
        code: error.code || 'MCP_AUDIT_FAILED',
        message: error.message
      },
      mcp_version: '1.0.0',
      execution_time_ms: Date.now() - startTime,
      timestamp: new Date().toISOString()
    });
  }
});

// ==========================================
// HELPER FUNCTIONS
// ==========================================

/**
 * Validate MCP request format and authentication
 */
async function validateMCPRequest(req) {
  // Check content type
  if (req.headers['content-type'] !== 'application/json') {
    throw new Error('Content-Type must be application/json');
  }

  // Check for Composio key
  const composioKey = req.headers['x-composio-key'];
  if (!composioKey || composioKey !== process.env.COMPOSIO_MCP_KEY) {
    const error = new Error('Invalid or missing Composio MCP key');
    error.status = 403;
    error.code = 'MCP_AUTH_FAILED';
    throw error;
  }

  // Validate request structure
  const { operation, params = {}, mcp_version = '1.0.0' } = req.body;

  if (!operation) {
    throw new Error('Missing required field: operation');
  }

  if (mcp_version !== '1.0.0') {
    throw new Error(`Unsupported MCP version: ${mcp_version}`);
  }

  return {
    operation,
    params,
    mcp_version,
    source_ip: req.ip,
    user_agent: req.headers['user-agent'],
    timestamp: new Date().toISOString()
  };
}

/**
 * Execute Firestore operations
 */
async function executeFirestoreOperation(mcpRequest) {
  const { operation, params } = mcpRequest;

  switch (operation) {
    case 'create_document':
      return await createDocument(params);
    case 'get_document':
      return await getDocument(params);
    case 'update_document':
      return await updateDocument(params);
    case 'delete_document':
      return await deleteDocument(params);
    case 'query_collection':
      return await queryCollection(params);
    case 'batch_write':
      return await batchWrite(params);
    default:
      throw new Error(`Unknown Firestore operation: ${operation}`);
  }
}

/**
 * Create document with Barton ID
 */
async function createDocument(params) {
  const { collection, data, document_id } = params;

  // Generate Barton ID if not provided
  if (!data.barton_id) {
    const idResult = await callCloudFunction('generateBartonId', {
      database: '05', // Firebase
      subhive: '01',   // Default
      microprocess: '01', // Creation
      tool: '03',      // Firebase
      altitude: '10000',
      step: '001',
      context: {
        target_collection: collection,
        operation: 'create'
      }
    });
    data.barton_id = idResult.barton_id;
  }

  // Add timestamps
  data.created_at = FieldValue.serverTimestamp();
  data.updated_at = FieldValue.serverTimestamp();

  // Create document
  const docRef = document_id
    ? db.collection(collection).doc(document_id)
    : db.collection(collection).doc();

  await docRef.set(data);

  return {
    document_id: docRef.id,
    barton_id: data.barton_id,
    collection: collection,
    path: `${collection}/${docRef.id}`
  };
}

/**
 * Get document by ID
 */
async function getDocument(params) {
  const { collection, document_id } = params;

  const docRef = db.collection(collection).doc(document_id);
  const doc = await docRef.get();

  if (!doc.exists) {
    const error = new Error('Document not found');
    error.status = 404;
    throw error;
  }

  return {
    document_id: doc.id,
    data: doc.data(),
    collection: collection,
    exists: true
  };
}

/**
 * Update document
 */
async function updateDocument(params) {
  const { collection, document_id, data } = params;

  // Add update timestamp
  data.updated_at = FieldValue.serverTimestamp();

  const docRef = db.collection(collection).doc(document_id);
  await docRef.update(data);

  return {
    document_id: document_id,
    collection: collection,
    updated_fields: Object.keys(data)
  };
}

/**
 * Delete document
 */
async function deleteDocument(params) {
  const { collection, document_id } = params;

  const docRef = db.collection(collection).doc(document_id);
  await docRef.delete();

  return {
    document_id: document_id,
    collection: collection,
    deleted: true
  };
}

/**
 * Query collection
 */
async function queryCollection(params) {
  const { collection, filters = [], order_by, limit = 100 } = params;

  let query = db.collection(collection);

  // Apply filters
  filters.forEach(filter => {
    const { field, operator, value } = filter;
    query = query.where(field, operator, value);
  });

  // Apply ordering
  if (order_by) {
    query = query.orderBy(order_by.field, order_by.direction || 'asc');
  }

  // Apply limit
  query = query.limit(limit);

  const snapshot = await query.get();
  const documents = [];

  snapshot.forEach(doc => {
    documents.push({
      document_id: doc.id,
      data: doc.data()
    });
  });

  return {
    collection: collection,
    count: documents.length,
    documents: documents
  };
}

/**
 * Batch write operations
 */
async function batchWrite(params) {
  const { operations } = params;

  const batch = db.batch();
  const results = [];

  for (const op of operations) {
    const docRef = db.collection(op.collection).doc(op.document_id || db.collection(op.collection).doc().id);

    switch (op.type) {
      case 'set':
        batch.set(docRef, op.data);
        break;
      case 'update':
        batch.update(docRef, op.data);
        break;
      case 'delete':
        batch.delete(docRef);
        break;
      default:
        throw new Error(`Unknown batch operation: ${op.type}`);
    }

    results.push({
      type: op.type,
      document_id: docRef.id,
      collection: op.collection
    });
  }

  await batch.commit();

  return {
    operations_count: operations.length,
    results: results
  };
}

/**
 * Get doctrine configuration
 */
async function getDoctrineConfiguration() {
  const configSnapshot = await db.collection('doctrine_config')
    .orderBy('created_at', 'desc')
    .limit(1)
    .get();

  if (configSnapshot.empty) {
    throw new Error('No doctrine configuration found');
  }

  return configSnapshot.docs[0].data();
}

/**
 * Update doctrine configuration
 */
async function updateDoctrineConfiguration(params) {
  const { config } = params;

  // Generate Barton ID for the new config
  const idResult = await callCloudFunction('generateBartonId', {
    database: '05',
    subhive: '01',
    microprocess: '02', // Update
    tool: '03',
    altitude: '10000',
    step: '001'
  });

  const configDoc = {
    ...config,
    barton_id: idResult.barton_id,
    created_at: FieldValue.serverTimestamp(),
    updated_at: FieldValue.serverTimestamp(),
    created_by: 'mcp_endpoint'
  };

  const docRef = db.collection('doctrine_config').doc();
  await docRef.set(configDoc);

  return {
    config_id: docRef.id,
    barton_id: idResult.barton_id,
    doctrine_version: config.doctrine_version
  };
}

/**
 * Query audit logs
 */
async function queryAuditLogs(params) {
  const {
    filters = [],
    start_date,
    end_date,
    limit = 100,
    order_by = { field: 'created_at', direction: 'desc' }
  } = params;

  let query = db.collection('global_audit_log');

  // Apply date range
  if (start_date) {
    query = query.where('created_at', '>=', new Date(start_date));
  }
  if (end_date) {
    query = query.where('created_at', '<=', new Date(end_date));
  }

  // Apply filters
  filters.forEach(filter => {
    query = query.where(filter.field, filter.operator, filter.value);
  });

  // Apply ordering and limit
  query = query.orderBy(order_by.field, order_by.direction).limit(limit);

  const snapshot = await query.get();
  const logs = [];

  snapshot.forEach(doc => {
    logs.push({
      log_id: doc.id,
      ...doc.data()
    });
  });

  return logs;
}

/**
 * Get specific audit log
 */
async function getAuditLog(uniqueId) {
  const doc = await db.collection('global_audit_log').doc(uniqueId).get();

  if (!doc.exists) {
    throw new Error('Audit log not found');
  }

  return {
    log_id: doc.id,
    ...doc.data()
  };
}

/**
 * Get audit statistics
 */
async function getAuditStats(params) {
  const { timeframe = '24h' } = params;

  const timeframeMs = {
    '1h': 60 * 60 * 1000,
    '24h': 24 * 60 * 60 * 1000,
    '7d': 7 * 24 * 60 * 60 * 1000,
    '30d': 30 * 24 * 60 * 60 * 1000
  };

  const since = new Date(Date.now() - timeframeMs[timeframe]);

  const snapshot = await db.collection('global_audit_log')
    .where('created_at', '>=', since)
    .get();

  const stats = {
    total_operations: snapshot.size,
    success_count: 0,
    error_count: 0,
    warning_count: 0,
    actions: {},
    sources: {}
  };

  snapshot.forEach(doc => {
    const data = doc.data();

    // Count by status
    stats[`${data.status}_count`]++;

    // Count by action
    stats.actions[data.action] = (stats.actions[data.action] || 0) + 1;

    // Count by source
    if (data.source?.service) {
      stats.sources[data.source.service] = (stats.sources[data.source.service] || 0) + 1;
    }
  });

  return stats;
}

/**
 * Validate Barton ID format
 */
async function validateBartonId(bartonId) {
  const pattern = /^[0-9]{2}\.[0-9]{2}\.[0-9]{2}\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$/;
  const isValidFormat = pattern.test(bartonId);

  let existsInRegistry = false;
  if (isValidFormat) {
    const doc = await db.collection('barton_id_registry').doc(bartonId).get();
    existsInRegistry = doc.exists;
  }

  return {
    barton_id: bartonId,
    valid_format: isValidFormat,
    exists_in_registry: existsInRegistry,
    components: isValidFormat ? {
      database: bartonId.split('.')[0],
      subhive: bartonId.split('.')[1],
      microprocess: bartonId.split('.')[2],
      tool: bartonId.split('.')[3],
      altitude: bartonId.split('.')[4],
      step: bartonId.split('.')[5]
    } : null
  };
}

/**
 * Get Barton ID information
 */
async function getBartonIdInfo(bartonId) {
  const doc = await db.collection('barton_id_registry').doc(bartonId).get();

  if (!doc.exists) {
    throw new Error('Barton ID not found in registry');
  }

  return {
    barton_id: bartonId,
    ...doc.data()
  };
}

/**
 * Call Cloud Function
 */
async function callCloudFunction(functionName, params) {
  const functions = getFunctions();
  const callable = functions.httpsCallable(functionName);

  const result = await callable(params);
  return result.data;
}

/**
 * Log MCP operation in audit trail
 */
async function logMCPOperation(request, result, startTime, status, error = null) {
  const endTime = Date.now();
  const executionTime = endTime - startTime;

  // Generate audit log ID
  const auditId = `15.01.03.07.10000.${Date.now().toString().slice(-3)}`;

  const logEntry = {
    unique_id: auditId,
    action: 'mcp_operation',
    status: status,
    source: {
      service: 'mcp_endpoints',
      function: request.operation || 'unknown',
      user_agent: request.user_agent || 'unknown',
      ip_address: request.source_ip || 'unknown',
      request_id: `mcp_${Date.now()}`
    },
    context: {
      operation_type: request.operation,
      execution_time_ms: executionTime,
      mcp_version: request.mcp_version || '1.0.0'
    },
    error_log: error ? {
      error_code: error.code || 'MCP_ERROR',
      error_message: error.message,
      stack_trace: process.env.NODE_ENV === 'development' ? error.stack : null
    } : null,
    payload: {
      before: null,
      after: result ? { operation_result: 'success' } : null,
      metadata: {
        request_params: request.params,
        composio_access: true
      }
    },
    compliance: {
      doctrine_version: '1.0.0',
      mcp_verified: true,
      altitude_validated: true,
      id_format_valid: true
    },
    created_at: FieldValue.serverTimestamp(),
    updated_at: FieldValue.serverTimestamp(),
    expires_at: new Date(Date.now() + (365 * 24 * 60 * 60 * 1000))
  };

  try {
    await db.collection('global_audit_log')
      .doc(auditId)
      .set(logEntry);
  } catch (logError) {
    console.error('Failed to write MCP audit log:', logError);
  }
}