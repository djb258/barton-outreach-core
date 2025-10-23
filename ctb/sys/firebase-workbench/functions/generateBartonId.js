/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-93752FE2
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

/**
 * Doctrine Spec:
 * - Barton ID: 04.04.01
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Cloud Function for Barton ID generation with uniqueness enforcement
 * - Input: ID generation parameters and context
 * - Output: Unique Barton ID with audit logging
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
 * Generate Barton ID Cloud Function
 *
 * Format: [database].[subhive].[microprocess].[tool].[altitude].[step]
 * Example: 05.01.01.03.10000.001
 *
 * CRITICAL: This function enforces uniqueness and logs every generation
 */
exports.generateBartonId = onCall({
  memory: '256MiB',
  timeoutSeconds: 30,
  maxInstances: 100
}, async (request) => {
  const startTime = Date.now();
  const context = request.auth || {};
  const data = request.data || {};

  try {
    // Validate input parameters
    const validatedParams = await validateGenerationParams(data);

    // Get current doctrine configuration
    const doctrineConfig = await getCurrentDoctrineConfig();

    // Generate unique Barton ID
    const bartonId = await generateUniqueId(validatedParams, doctrineConfig);

    // Register the ID in the registry
    await registerBartonId(bartonId, validatedParams, context);

    // Log the generation in audit trail
    await logIdGeneration(bartonId, validatedParams, context, 'success', startTime);

    return {
      success: true,
      barton_id: bartonId.id,
      components: bartonId.components,
      doctrine_version: doctrineConfig.doctrine_version,
      generation_timestamp: new Date().toISOString(),
      request_id: generateRequestId()
    };

  } catch (error) {
    // Log error in audit trail
    await logIdGeneration(null, data, context, 'failure', startTime, error);

    console.error('Barton ID generation failed:', error);

    throw new HttpsError(
      'internal',
      'Failed to generate Barton ID',
      {
        code: 'GENERATION_FAILED',
        details: error.message,
        timestamp: new Date().toISOString()
      }
    );
  }
});

/**
 * Validate generation parameters
 */
async function validateGenerationParams(params) {
  const required = ['database', 'subhive', 'microprocess', 'tool', 'altitude', 'step'];
  const missing = required.filter(field => !params[field]);

  if (missing.length > 0) {
    throw new Error(`Missing required parameters: ${missing.join(', ')}`);
  }

  // Validate format of each component
  const patterns = {
    database: /^[0-9]{2}$/,
    subhive: /^[0-9]{2}$/,
    microprocess: /^[0-9]{2}$/,
    tool: /^[0-9]{2}$/,
    altitude: /^[0-9]{5}$/,
    step: /^[0-9]{3}$/
  };

  for (const [field, pattern] of Object.entries(patterns)) {
    if (!pattern.test(params[field])) {
      throw new Error(`Invalid format for ${field}: ${params[field]}`);
    }
  }

  return {
    database: params.database,
    subhive: params.subhive,
    microprocess: params.microprocess,
    tool: params.tool,
    altitude: params.altitude,
    step: params.step,
    context: params.context || {},
    metadata: params.metadata || {}
  };
}

/**
 * Get current doctrine configuration
 */
async function getCurrentDoctrineConfig() {
  try {
    const configSnapshot = await db.collection('doctrine_config')
      .orderBy('created_at', 'desc')
      .limit(1)
      .get();

    if (configSnapshot.empty) {
      // Return default configuration if none exists
      return {
        doctrine_version: '1.0.0',
        id_format: 'NN.NN.NN.NN.NNNNN.NNN',
        enforcement: {
          strict_validation: true,
          version_locking: true
        }
      };
    }

    return configSnapshot.docs[0].data();
  } catch (error) {
    console.error('Failed to get doctrine config:', error);
    throw new Error('Unable to retrieve doctrine configuration');
  }
}

/**
 * Generate unique Barton ID with collision detection
 */
async function generateUniqueId(params, doctrineConfig) {
  const maxAttempts = 10;
  let attempts = 0;

  while (attempts < maxAttempts) {
    attempts++;

    // Construct the ID
    const idComponents = {
      database: params.database,
      subhive: params.subhive,
      microprocess: params.microprocess,
      tool: params.tool,
      altitude: params.altitude,
      step: params.step
    };

    const candidateId = `${idComponents.database}.${idComponents.subhive}.${idComponents.microprocess}.${idComponents.tool}.${idComponents.altitude}.${idComponents.step}`;

    // Check for uniqueness in registry
    const existingId = await db.collection('barton_id_registry')
      .doc(candidateId)
      .get();

    if (!existingId.exists) {
      return {
        id: candidateId,
        components: idComponents,
        attempt: attempts
      };
    }

    // If collision detected, increment the step for next attempt
    const currentStep = parseInt(params.step);
    const nextStep = (currentStep + 1).toString().padStart(3, '0');

    if (nextStep === '1000') {
      // If we've exhausted all steps, increment microprocess
      const currentMicroprocess = parseInt(params.microprocess);
      const nextMicroprocess = (currentMicroprocess + 1).toString().padStart(2, '0');

      if (nextMicroprocess === '100') {
        throw new Error('ID space exhausted for given parameters');
      }

      params.microprocess = nextMicroprocess;
      params.step = '001';
    } else {
      params.step = nextStep;
    }
  }

  throw new Error(`Failed to generate unique ID after ${maxAttempts} attempts`);
}

/**
 * Register Barton ID in the registry
 */
async function registerBartonId(bartonId, params, context) {
  const registryDoc = {
    barton_id: bartonId.id,
    components: bartonId.components,
    generation_info: {
      generated_by: 'generateBartonId_function',
      generation_method: 'cloud_function',
      doctrine_version: '1.0.0',
      request_context: {
        user_id: context.uid || 'anonymous',
        source_ip: context.source_ip || 'unknown',
        user_agent: context.user_agent || 'cloud_function',
        request_metadata: params.metadata
      },
      generation_attempts: bartonId.attempt
    },
    usage_tracking: {
      assigned_to: params.context.assigned_to || 'unassigned',
      collection: params.context.target_collection || null,
      document_path: params.context.document_path || null,
      status: 'active'
    },
    created_at: FieldValue.serverTimestamp(),
    updated_at: FieldValue.serverTimestamp()
  };

  await db.collection('barton_id_registry')
    .doc(bartonId.id)
    .set(registryDoc);

  return registryDoc;
}

/**
 * Log ID generation in global audit log
 */
async function logIdGeneration(bartonId, params, context, status, startTime, error = null) {
  const endTime = Date.now();
  const executionTime = endTime - startTime;

  // Generate audit log entry ID (self-referential)
  const auditId = `15.01.02.07.10000.${Date.now().toString().slice(-3)}`;

  const logEntry = {
    unique_id: auditId,
    action: 'id_generation',
    status: status,
    source: {
      service: 'generateBartonId_function',
      function: 'generateBartonId',
      user_agent: context.user_agent || 'cloud_function',
      ip_address: context.source_ip || 'internal',
      request_id: generateRequestId()
    },
    context: {
      target_collection: 'barton_id_registry',
      operation_type: 'create',
      execution_time_ms: executionTime,
      generated_id: bartonId?.id || null,
      input_parameters: params
    },
    error_log: error ? {
      error_code: 'GENERATION_ERROR',
      error_message: error.message,
      stack_trace: process.env.NODE_ENV === 'development' ? error.stack : null,
      retry_count: 0,
      recovery_action: null
    } : null,
    payload: {
      before: null,
      after: bartonId ? {
        barton_id: bartonId.id,
        components: bartonId.components
      } : null,
      metadata: {
        doctrine_version: '1.0.0',
        function_version: '1.0.0'
      }
    },
    compliance: {
      doctrine_version: '1.0.0',
      mcp_verified: true,
      altitude_validated: true,
      id_format_valid: bartonId ? true : false
    },
    created_at: FieldValue.serverTimestamp(),
    updated_at: FieldValue.serverTimestamp(),
    expires_at: new Date(Date.now() + (365 * 24 * 60 * 60 * 1000)) // 1 year retention
  };

  try {
    await db.collection('global_audit_log')
      .doc(auditId)
      .set(logEntry);
  } catch (logError) {
    console.error('Failed to write audit log:', logError);
    // Don't throw here to avoid breaking the main operation
  }
}

/**
 * Generate request ID for correlation
 */
function generateRequestId() {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Batch Barton ID generation function
 * For bulk operations requiring multiple IDs
 */
exports.generateBartonIdBatch = onCall({
  memory: '512MiB',
  timeoutSeconds: 60,
  maxInstances: 10
}, async (request) => {
  const startTime = Date.now();
  const context = request.auth || {};
  const data = request.data || {};

  try {
    const { count = 1, template, metadata = {} } = data;

    if (count > 100) {
      throw new Error('Batch size cannot exceed 100 IDs');
    }

    const doctrineConfig = await getCurrentDoctrineConfig();
    const generatedIds = [];
    const errors = [];

    for (let i = 0; i < count; i++) {
      try {
        const params = {
          ...template,
          step: (parseInt(template.step) + i).toString().padStart(3, '0'),
          metadata: { ...metadata, batch_index: i }
        };

        const validatedParams = await validateGenerationParams(params);
        const bartonId = await generateUniqueId(validatedParams, doctrineConfig);
        await registerBartonId(bartonId, validatedParams, context);

        generatedIds.push({
          barton_id: bartonId.id,
          components: bartonId.components,
          index: i
        });

      } catch (error) {
        errors.push({
          index: i,
          error: error.message
        });
      }
    }

    // Log batch operation
    await logBatchGeneration(generatedIds, errors, context, startTime);

    return {
      success: true,
      generated_count: generatedIds.length,
      error_count: errors.length,
      ids: generatedIds,
      errors: errors,
      doctrine_version: doctrineConfig.doctrine_version,
      generation_timestamp: new Date().toISOString()
    };

  } catch (error) {
    console.error('Batch ID generation failed:', error);

    throw new HttpsError(
      'internal',
      'Failed to generate batch Barton IDs',
      {
        code: 'BATCH_GENERATION_FAILED',
        details: error.message,
        timestamp: new Date().toISOString()
      }
    );
  }
});

/**
 * Log batch generation operation
 */
async function logBatchGeneration(generatedIds, errors, context, startTime) {
  const endTime = Date.now();
  const executionTime = endTime - startTime;
  const auditId = `15.01.02.07.10000.${Date.now().toString().slice(-3)}`;

  const logEntry = {
    unique_id: auditId,
    action: 'id_generation',
    status: errors.length === 0 ? 'success' : 'warning',
    source: {
      service: 'generateBartonIdBatch_function',
      function: 'generateBartonIdBatch',
      user_agent: context.user_agent || 'cloud_function',
      ip_address: context.source_ip || 'internal',
      request_id: generateRequestId()
    },
    context: {
      target_collection: 'barton_id_registry',
      operation_type: 'batch_create',
      execution_time_ms: executionTime,
      batch_size: generatedIds.length + errors.length,
      success_count: generatedIds.length,
      error_count: errors.length
    },
    payload: {
      after: {
        generated_ids: generatedIds.map(id => id.barton_id),
        errors: errors
      },
      metadata: {
        doctrine_version: '1.0.0',
        function_version: '1.0.0'
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
    console.error('Failed to write batch audit log:', logError);
  }
}

/**
 * Health check function for Barton ID generation system
 */
exports.bartonIdSystemHealth = onCall({
  memory: '256MiB',
  timeoutSeconds: 30
}, async (request) => {
  try {
    const startTime = Date.now();

    // Check doctrine configuration
    const configCheck = await checkDoctrineConfig();

    // Check registry accessibility
    const registryCheck = await checkRegistry();

    // Check audit log
    const auditCheck = await checkAuditLog();

    // Test ID generation
    const generationCheck = await testIdGeneration();

    const healthReport = {
      overall_status: 'healthy',
      timestamp: new Date().toISOString(),
      response_time_ms: Date.now() - startTime,
      checks: {
        doctrine_config: configCheck,
        id_registry: registryCheck,
        audit_log: auditCheck,
        id_generation: generationCheck
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
async function checkDoctrineConfig() {
  try {
    const config = await getCurrentDoctrineConfig();
    return {
      status: 'ok',
      doctrine_version: config.doctrine_version,
      enforcement_enabled: config.enforcement?.strict_validation
    };
  } catch (error) {
    return {
      status: 'error',
      message: error.message
    };
  }
}

async function checkRegistry() {
  try {
    const count = await db.collection('barton_id_registry')
      .count()
      .get();

    return {
      status: 'ok',
      total_ids: count.data().count
    };
  } catch (error) {
    return {
      status: 'error',
      message: error.message
    };
  }
}

async function checkAuditLog() {
  try {
    const recentLogs = await db.collection('global_audit_log')
      .orderBy('created_at', 'desc')
      .limit(1)
      .get();

    return {
      status: 'ok',
      latest_log: recentLogs.empty ? null : recentLogs.docs[0].data().created_at
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
    // This is just a dry run test, doesn't actually generate
    const testParams = {
      database: '99',
      subhive: '99',
      microprocess: '99',
      tool: '99',
      altitude: '10000',
      step: '999'
    };

    await validateGenerationParams(testParams);

    return {
      status: 'ok',
      message: 'Generation system functional'
    };
  } catch (error) {
    return {
      status: 'error',
      message: error.message
    };
  }
}