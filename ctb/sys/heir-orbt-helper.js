/**
 * HEIR/ORBT Helper - Barton Outreach Core
 * Pulled from: imo-creator global-config.yaml
 * Last Synced: 2025-11-07
 *
 * Purpose: Generate HEIR IDs and ORBT payloads for Composio MCP integration
 */

// HEIR/ORBT Configuration from global-config.yaml
const HEIR_ORBT_CONFIG = {
  enabled: true,
  heir_format: 'HEIR-YYYY-MM-SYSTEM-MODE-VN',
  process_id_format: 'PRC-SYSTEM-EPOCHTIMESTAMP',
  orbt_layers: {
    1: 'Infrastructure',
    2: 'Integration',
    3: 'Application',
    4: 'Presentation'
  },
  blueprint_version: '1.0',
  payload_format_required: true
};

/**
 * Generate HEIR ID
 * Format: HEIR-YYYY-MM-SYSTEM-MODE-VN
 *
 * @param {string} system - System identifier (e.g., 'ENRICH', 'SYNC', 'AUDIT')
 * @param {string} mode - Mode identifier (e.g., 'AUTO', 'MANUAL', 'BATCH')
 * @param {number} version - Version number (default: 1)
 * @returns {string} HEIR ID
 *
 * Example: HEIR-2025-11-ENRICH-AUTO-01
 */
function generateHeirId(system, mode, version = 1) {
  const date = new Date();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const versionStr = String(version).padStart(2, '0');

  return `HEIR-${year}-${month}-${system.toUpperCase()}-${mode.toUpperCase()}-${versionStr}`;
}

/**
 * Generate Process ID
 * Format: PRC-SYSTEM-EPOCHTIMESTAMP
 *
 * @param {string} system - System identifier
 * @returns {string} Process ID
 *
 * Example: PRC-ENRICH-1699392000123
 */
function generateProcessId(system) {
  const timestamp = Date.now();
  return `PRC-${system.toUpperCase()}-${timestamp}`;
}

/**
 * Create ORBT Payload for Composio MCP
 *
 * @param {string} tool - Tool name (e.g., 'manage_connected_account', 'trigger_workflow')
 * @param {object} data - Tool-specific data
 * @param {string} system - System identifier
 * @param {string} mode - Mode identifier
 * @param {number} orbt_layer - ORBT layer (1-4)
 * @param {object} options - Additional options
 * @returns {object} Complete ORBT payload
 *
 * Example:
 * createORBTPayload('manage_connected_account', { action: 'list' }, 'AUDIT', 'AUTO', 2)
 */
function createORBTPayload(tool, data, system, mode, orbt_layer, options = {}) {
  if (!HEIR_ORBT_CONFIG.enabled) {
    throw new Error('HEIR/ORBT system is disabled in global config');
  }

  if (HEIR_ORBT_CONFIG.payload_format_required && !tool) {
    throw new Error('Tool name is required when payload_format_required is true');
  }

  if (orbt_layer < 1 || orbt_layer > 4) {
    throw new Error(`Invalid ORBT layer: ${orbt_layer}. Must be 1-4.`);
  }

  const heir_id = generateHeirId(system, mode, options.version || 1);
  const process_id = generateProcessId(system);

  return {
    tool,
    data,
    unique_id: heir_id,
    process_id,
    orbt_layer,
    orbt_layer_name: HEIR_ORBT_CONFIG.orbt_layers[orbt_layer],
    blueprint_version: HEIR_ORBT_CONFIG.blueprint_version,
    timestamp: new Date().toISOString(),
    system,
    mode,
    ...options.extra_fields
  };
}

/**
 * Validate ORBT Payload
 *
 * @param {object} payload - ORBT payload to validate
 * @returns {boolean} True if valid
 * @throws {Error} If invalid
 */
function validateORBTPayload(payload) {
  const required_fields = [
    'tool',
    'data',
    'unique_id',
    'process_id',
    'orbt_layer',
    'blueprint_version'
  ];

  for (const field of required_fields) {
    if (!(field in payload)) {
      throw new Error(`Missing required field in ORBT payload: ${field}`);
    }
  }

  // Validate HEIR ID format
  const heirRegex = /^HEIR-\d{4}-\d{2}-[A-Z]+-[A-Z]+-\d{2}$/;
  if (!heirRegex.test(payload.unique_id)) {
    throw new Error(`Invalid HEIR ID format: ${payload.unique_id}`);
  }

  // Validate Process ID format
  const procRegex = /^PRC-[A-Z]+-\d+$/;
  if (!procRegex.test(payload.process_id)) {
    throw new Error(`Invalid Process ID format: ${payload.process_id}`);
  }

  // Validate ORBT layer
  if (payload.orbt_layer < 1 || payload.orbt_layer > 4) {
    throw new Error(`Invalid ORBT layer: ${payload.orbt_layer}`);
  }

  return true;
}

/**
 * Convenience functions for common operations
 */

// Enrichment operations (ORBT Layer 2 - Integration)
function createEnrichmentPayload(tool, data, mode = 'AUTO') {
  return createORBTPayload(tool, data, 'ENRICH', mode, 2);
}

// Sync operations (ORBT Layer 2 - Integration)
function createSyncPayload(tool, data, mode = 'AUTO') {
  return createORBTPayload(tool, data, 'SYNC', mode, 2);
}

// Audit operations (ORBT Layer 1 - Infrastructure)
function createAuditPayload(tool, data, mode = 'MANUAL') {
  return createORBTPayload(tool, data, 'AUDIT', mode, 1);
}

// Database operations (ORBT Layer 1 - Infrastructure)
function createDatabasePayload(tool, data, mode = 'AUTO') {
  return createORBTPayload(tool, data, 'DATABASE', mode, 1);
}

// API operations (ORBT Layer 3 - Application)
function createAPIPayload(tool, data, mode = 'AUTO') {
  return createORBTPayload(tool, data, 'API', mode, 3);
}

// UI operations (ORBT Layer 4 - Presentation)
function createUIPayload(tool, data, mode = 'USER') {
  return createORBTPayload(tool, data, 'UI', mode, 4);
}

/**
 * Example Composio MCP call with ORBT payload
 */
async function callComposioMCP(payload, composio_url = 'http://localhost:3001/tool') {
  validateORBTPayload(payload);

  const response = await fetch(composio_url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${process.env.COMPOSIO_API_KEY || ''}`
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Composio MCP call failed: ${response.statusText}`);
  }

  return response.json();
}

module.exports = {
  HEIR_ORBT_CONFIG,
  generateHeirId,
  generateProcessId,
  createORBTPayload,
  validateORBTPayload,
  createEnrichmentPayload,
  createSyncPayload,
  createAuditPayload,
  createDatabasePayload,
  createAPIPayload,
  createUIPayload,
  callComposioMCP
};
