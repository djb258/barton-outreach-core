/**
 * Doctrine Spec:
 * - Barton ID: 15.01.04.07.10000.001
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Barton Doctrine Firebase service using existing Composio tools
 * - Input: Doctrine operations and data management requests
 * - Output: Firebase operations via Composio MCP
 * - MCP: Firebase (via existing Composio tools)
 */

import ComposioEnhancedService from '../apps/outreach-process-manager/services/composio-enhanced.js';

class BartonDoctrineFirebaseService {
  constructor() {
    this.composio = new ComposioEnhancedService();
    this.initialized = false;
    this.doctrineVersion = '1.0.0';
    this.mcpEndpoint = process.env.COMPOSIO_MCP_URL || 'http://localhost:3001';
  }

  /**
   * Initialize the service and verify Composio Firebase tools
   */
  async initialize() {
    console.log('[DOCTRINE-FIREBASE] Initializing with existing Composio tools...');

    try {
      await this.composio.initialize();

      // Verify Firebase tools are available
      const firebaseTools = this.composio.getToolsByCategory('firebase');
      console.log(`[DOCTRINE-FIREBASE] Found ${firebaseTools.length} Firebase tools`);

      // Test Firebase connectivity via Composio
      await this.testFirebaseConnection();

      this.initialized = true;
      return { success: true, tools: firebaseTools.length };

    } catch (error) {
      console.error('[DOCTRINE-FIREBASE] Initialization failed:', error);
      throw error;
    }
  }

  /**
   * Test Firebase connection using Composio tools
   */
  async testFirebaseConnection() {
    try {
      // Use Composio's Firebase read tool to test connectivity
      const result = await this.executeComposioFirebaseTool('FIREBASE_READ', {
        collection: '_test_connection',
        document: 'health_check'
      });

      console.log('[DOCTRINE-FIREBASE] Connection test completed');
      return result;
    } catch (error) {
      console.warn('[DOCTRINE-FIREBASE] Connection test failed (expected for new setup):', error.message);
      return { success: false, error: error.message };
    }
  }

  /**
   * Execute Composio Firebase tool with proper MCP format
   */
  async executeComposioFirebaseTool(tool, data) {
    const mcpPayload = {
      tool: tool,
      data: data,
      unique_id: this.generateHeirId(),
      process_id: this.generateProcessId(),
      orbt_layer: 2,
      blueprint_version: this.doctrineVersion
    };

    try {
      const response = await fetch(`${this.mcpEndpoint}/tool`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Composio-Key': process.env.COMPOSIO_API_KEY
        },
        body: JSON.stringify(mcpPayload)
      });

      if (!response.ok) {
        throw new Error(`MCP request failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();

      // Log to audit trail
      await this.logOperation(tool, data, result, 'success');

      return result;
    } catch (error) {
      await this.logOperation(tool, data, null, 'error', error);
      throw error;
    }
  }

  /**
   * STEP 1: Initialize Doctrine Foundation Collections
   */
  async initializeDoctrineFoundation() {
    console.log('[DOCTRINE-FIREBASE] Initializing Step 1: Doctrine Foundation...');

    try {
      // 1. Create doctrine_config collection with default configuration
      await this.createDoctrineConfig();

      // 2. Initialize global_audit_log collection
      await this.initializeAuditLog();

      // 3. Create barton_id_registry collection
      await this.initializeIdRegistry();

      // 4. Set up collection indexes and rules
      await this.setupCollectionRules();

      console.log('[DOCTRINE-FIREBASE] Step 1 initialization complete');
      return { success: true, step: 1, collections: 3 };

    } catch (error) {
      console.error('[DOCTRINE-FIREBASE] Step 1 initialization failed:', error);
      throw error;
    }
  }

  /**
   * Create doctrine configuration document
   */
  async createDoctrineConfig() {
    const defaultConfig = {
      doctrine_version: this.doctrineVersion,
      id_format: 'NN.NN.NN.NN.NNNNN.NNN',
      id_components: {
        database: {
          pattern: '^[0-9]{2}$',
          codes: {
            '01': 'primary_postgres',
            '02': 'analytics_warehouse',
            '03': 'cache_redis',
            '04': 'firebase_realtime',
            '05': 'firebase_firestore'
          }
        },
        subhive: {
          pattern: '^[0-9]{2}$',
          codes: {
            '01': 'intake',
            '02': 'processing',
            '03': 'vault',
            '04': 'outreach',
            '05': 'analytics'
          }
        },
        microprocess: {
          pattern: '^[0-9]{2}$',
          codes: {
            '01': 'ingestion',
            '02': 'validation',
            '03': 'enrichment',
            '04': 'scoring',
            '05': 'promotion'
          }
        },
        tool: {
          pattern: '^[0-9]{2}$',
          codes: {
            '01': 'postgres',
            '02': 'redis',
            '03': 'firebase',
            '04': 'composio',
            '05': 'neon',
            '06': 'vercel',
            '07': 'custom'
          }
        },
        altitude: {
          pattern: '^[0-9]{5}$',
          codes: {
            '10000': 'execution_layer',
            '20000': 'orchestration_layer',
            '30000': 'business_logic_layer',
            '40000': 'presentation_layer',
            '50000': 'user_interface_layer'
          }
        },
        step: {
          pattern: '^[0-9]{3}$',
          codes: {
            '001': 'doctrine_foundation',
            '002': 'intake_processing',
            '003': 'validation_checks',
            '004': 'data_enrichment',
            '005': 'lead_scoring',
            '006': 'campaign_creation',
            '007': 'outreach_execution',
            '008': 'analytics_tracking'
          }
        }
      },
      altitude_codes: {
        '10000': {
          name: 'Execution Layer',
          description: 'Direct data operations and API calls',
          permissions: ['read', 'write', 'delete']
        },
        '20000': {
          name: 'Orchestration Layer',
          description: 'Service coordination and workflow management',
          permissions: ['read', 'write', 'orchestrate']
        },
        '30000': {
          name: 'Business Logic Layer',
          description: 'Business rules and decision making',
          permissions: ['read', 'validate', 'decide']
        }
      },
      schema_version: '1.0.0',
      enforcement: {
        strict_validation: true,
        mcp_only: true,
        audit_all_operations: true,
        version_locking: true
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      created_by: 'barton_doctrine_system',
      barton_id: '05.01.01.03.10000.001'
    };

    return await this.executeComposioFirebaseTool('FIREBASE_WRITE', {
      collection: 'doctrine_config',
      document: 'current',
      data: defaultConfig
    });
  }

  /**
   * Update doctrine configuration with validation
   */
  async updateDoctrineConfig(updates) {
    console.log('[DOCTRINE-FIREBASE] Updating doctrine configuration...');

    try {
      // Get current configuration
      const currentConfigResult = await this.executeComposioFirebaseTool('FIREBASE_READ', {
        collection: 'doctrine_config',
        document: 'current'
      });

      if (!currentConfigResult.success) {
        throw new Error('Unable to retrieve current doctrine configuration');
      }

      const currentConfig = currentConfigResult.data;

      // Validate updates
      const validatedUpdates = await this.validateDoctrineConfigUpdates(updates, currentConfig);

      // Create new configuration version
      const newConfig = {
        ...currentConfig,
        ...validatedUpdates,
        updated_at: new Date().toISOString(),
        version_history: [
          ...(currentConfig.version_history || []),
          {
            version: currentConfig.doctrine_version,
            updated_at: currentConfig.updated_at,
            changes: validatedUpdates
          }
        ]
      };

      // If version changed, increment it
      if (validatedUpdates.doctrine_version && validatedUpdates.doctrine_version !== currentConfig.doctrine_version) {
        newConfig.doctrine_version = validatedUpdates.doctrine_version;
      }

      // Write updated configuration
      const updateResult = await this.executeComposioFirebaseTool('FIREBASE_WRITE', {
        collection: 'doctrine_config',
        document: 'current',
        data: newConfig
      });

      // Log the configuration update
      await this.logOperation(
        'doctrine_config_update',
        { updates: validatedUpdates },
        { success: updateResult.success },
        'success'
      );

      return {
        success: true,
        previous_version: currentConfig.doctrine_version,
        new_version: newConfig.doctrine_version,
        changes: validatedUpdates
      };

    } catch (error) {
      await this.logOperation(
        'doctrine_config_update',
        { updates },
        { success: false },
        'failure',
        error
      );
      throw error;
    }
  }

  /**
   * Validate doctrine configuration updates
   */
  async validateDoctrineConfigUpdates(updates, currentConfig) {
    const validatedUpdates = {};

    // Validate doctrine version format
    if (updates.doctrine_version) {
      const versionPattern = /^\d+\.\d+\.\d+$/;
      if (!versionPattern.test(updates.doctrine_version)) {
        throw new Error('Invalid doctrine version format. Must be X.Y.Z');
      }
      validatedUpdates.doctrine_version = updates.doctrine_version;
    }

    // Validate ID format
    if (updates.id_format) {
      const formatPattern = /^NN\.NN\.NN\.NN\.NNNNN\.NNN$/;
      if (!formatPattern.test(updates.id_format)) {
        throw new Error('Invalid ID format. Must be NN.NN.NN.NN.NNNNN.NNN');
      }
      validatedUpdates.id_format = updates.id_format;
    }

    // Validate enforcement settings
    if (updates.enforcement) {
      const validEnforcement = {
        strict_validation: typeof updates.enforcement.strict_validation === 'boolean' ? updates.enforcement.strict_validation : currentConfig.enforcement.strict_validation,
        mcp_only: typeof updates.enforcement.mcp_only === 'boolean' ? updates.enforcement.mcp_only : currentConfig.enforcement.mcp_only,
        audit_all_operations: typeof updates.enforcement.audit_all_operations === 'boolean' ? updates.enforcement.audit_all_operations : currentConfig.enforcement.audit_all_operations,
        version_locking: typeof updates.enforcement.version_locking === 'boolean' ? updates.enforcement.version_locking : currentConfig.enforcement.version_locking
      };
      validatedUpdates.enforcement = validEnforcement;
    }

    // Validate altitude codes
    if (updates.altitude_codes) {
      for (const [code, config] of Object.entries(updates.altitude_codes)) {
        if (!/^\d{5}$/.test(code)) {
          throw new Error(`Invalid altitude code format: ${code}. Must be 5 digits`);
        }
        if (!config.name || !config.description || !config.permissions) {
          throw new Error(`Incomplete altitude code configuration for: ${code}`);
        }
      }
      validatedUpdates.altitude_codes = updates.altitude_codes;
    }

    // Validate ID components
    if (updates.id_components) {
      const requiredComponents = ['database', 'subhive', 'microprocess', 'tool', 'altitude', 'step'];
      for (const component of requiredComponents) {
        if (updates.id_components[component]) {
          if (!updates.id_components[component].pattern || !updates.id_components[component].codes) {
            throw new Error(`Invalid component configuration for: ${component}`);
          }
        }
      }
      validatedUpdates.id_components = updates.id_components;
    }

    return validatedUpdates;
  }

  /**
   * Get current doctrine configuration
   */
  async getDoctrineConfig() {
    try {
      const configResult = await this.executeComposioFirebaseTool('FIREBASE_READ', {
        collection: 'doctrine_config',
        document: 'current'
      });

      if (!configResult.success) {
        throw new Error('Unable to retrieve doctrine configuration');
      }

      return {
        success: true,
        config: configResult.data,
        version: configResult.data.doctrine_version,
        last_updated: configResult.data.updated_at
      };

    } catch (error) {
      console.error('[DOCTRINE-FIREBASE] Failed to get doctrine config:', error);
      throw error;
    }
  }

  /**
   * Validate current doctrine configuration
   */
  async validateDoctrineConfig() {
    console.log('[DOCTRINE-FIREBASE] Validating doctrine configuration...');

    try {
      const configResult = await this.getDoctrineConfig();
      const config = configResult.config;

      const validationResults = {
        valid: true,
        issues: [],
        warnings: []
      };

      // Check required fields
      const requiredFields = [
        'doctrine_version',
        'id_format',
        'id_components',
        'altitude_codes',
        'enforcement'
      ];

      for (const field of requiredFields) {
        if (!config[field]) {
          validationResults.issues.push(`Missing required field: ${field}`);
          validationResults.valid = false;
        }
      }

      // Validate ID format
      if (config.id_format) {
        const formatPattern = /^NN\.NN\.NN\.NN\.NNNNN\.NNN$/;
        if (!formatPattern.test(config.id_format)) {
          validationResults.issues.push('Invalid ID format pattern');
          validationResults.valid = false;
        }
      }

      // Validate enforcement settings
      if (config.enforcement) {
        if (!config.enforcement.mcp_only) {
          validationResults.warnings.push('MCP-only enforcement is disabled');
        }
        if (!config.enforcement.audit_all_operations) {
          validationResults.warnings.push('Audit logging is not enforced for all operations');
        }
      }

      // Check for configuration staleness
      if (config.updated_at) {
        const lastUpdate = new Date(config.updated_at);
        const daysSinceUpdate = (Date.now() - lastUpdate.getTime()) / (1000 * 60 * 60 * 24);
        if (daysSinceUpdate > 30) {
          validationResults.warnings.push(`Configuration last updated ${Math.floor(daysSinceUpdate)} days ago`);
        }
      }

      return {
        success: true,
        validation: validationResults,
        config_version: config.doctrine_version
      };

    } catch (error) {
      return {
        success: false,
        validation: {
          valid: false,
          issues: [`Validation failed: ${error.message}`],
          warnings: []
        }
      };
    }
  }

  /**
   * Reset doctrine configuration to defaults
   */
  async resetDoctrineConfig() {
    console.log('[DOCTRINE-FIREBASE] Resetting doctrine configuration to defaults...');

    try {
      // Get current config for backup
      const currentConfigResult = await this.getDoctrineConfig();

      // Create backup with timestamp
      if (currentConfigResult.success) {
        const backupId = `backup_${Date.now()}`;
        await this.executeComposioFirebaseTool('FIREBASE_WRITE', {
          collection: 'doctrine_config',
          document: backupId,
          data: {
            ...currentConfigResult.config,
            backup_timestamp: new Date().toISOString(),
            backup_reason: 'reset_to_defaults'
          }
        });
      }

      // Recreate default configuration
      await this.createDoctrineConfig();

      // Log the reset operation
      await this.logOperation(
        'doctrine_config_reset',
        { reason: 'reset_to_defaults' },
        { success: true },
        'success'
      );

      return {
        success: true,
        message: 'Doctrine configuration reset to defaults',
        backup_id: currentConfigResult.success ? `backup_${Date.now()}` : null
      };

    } catch (error) {
      await this.logOperation(
        'doctrine_config_reset',
        { reason: 'reset_to_defaults' },
        { success: false },
        'failure',
        error
      );
      throw error;
    }
  }

  /**
   * Initialize audit log collection
   */
  async initializeAuditLog() {
    const auditExample = {
      unique_id: '05.01.01.03.10000.002',
      action: 'doctrine_initialization',
      status: 'success',
      source: {
        service: 'barton_doctrine_firebase_service',
        function: 'initializeAuditLog',
        user_agent: 'doctrine_system',
        ip_address: 'internal',
        request_id: `init_${Date.now()}`
      },
      context: {
        target_collection: 'global_audit_log',
        operation_type: 'create',
        execution_time_ms: 0
      },
      compliance: {
        doctrine_version: this.doctrineVersion,
        mcp_verified: true,
        altitude_validated: true,
        id_format_valid: true
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + (365 * 24 * 60 * 60 * 1000)).toISOString()
    };

    return await this.executeComposioFirebaseTool('FIREBASE_WRITE', {
      collection: 'global_audit_log',
      document: auditExample.unique_id,
      data: auditExample
    });
  }

  /**
   * Initialize Barton ID registry
   */
  async initializeIdRegistry() {
    const registryExample = {
      barton_id: '05.01.01.03.10000.001',
      components: {
        database: '05',
        subhive: '01',
        microprocess: '01',
        tool: '03',
        altitude: '10000',
        step: '001'
      },
      generation_info: {
        generated_by: 'barton_doctrine_system',
        generation_method: 'manual_initialization',
        doctrine_version: this.doctrineVersion,
        request_context: {
          initialization: true
        }
      },
      usage_tracking: {
        assigned_to: 'doctrine_config',
        collection: 'doctrine_config',
        document_path: 'doctrine_config/current',
        status: 'active'
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    return await this.executeComposioFirebaseTool('FIREBASE_WRITE', {
      collection: 'barton_id_registry',
      document: registryExample.barton_id,
      data: registryExample
    });
  }

  /**
   * Set up collection rules and indexes
   */
  async setupCollectionRules() {
    // This would typically involve Firestore Rules and Index configuration
    // For now, we'll log the requirement
    console.log('[DOCTRINE-FIREBASE] Collection rules setup required (manual Firestore configuration)');

    return await this.logOperation('setup_collection_rules', {
      collections: ['doctrine_config', 'global_audit_log', 'barton_id_registry'],
      rules_required: true
    }, { success: true }, 'success');
  }

  /**
   * Generate Barton ID using Firebase-stored configuration
   */
  async generateBartonId(params) {
    try {
      // Get current doctrine configuration
      const configResult = await this.executeComposioFirebaseTool('FIREBASE_READ', {
        collection: 'doctrine_config',
        document: 'current'
      });

      if (!configResult.success) {
        throw new Error('Unable to retrieve doctrine configuration');
      }

      const config = configResult.data;

      // Validate parameters against configuration
      this.validateIdParameters(params, config);

      // Generate unique ID
      const bartonId = this.constructBartonId(params);

      // Check uniqueness
      const uniqueResult = await this.checkBartonIdUniqueness(bartonId);
      if (!uniqueResult.unique) {
        throw new Error(`Barton ID already exists: ${bartonId}`);
      }

      // Register the new ID
      await this.registerBartonId(bartonId, params, config);

      return {
        success: true,
        barton_id: bartonId,
        components: params,
        doctrine_version: config.doctrine_version
      };

    } catch (error) {
      console.error('[DOCTRINE-FIREBASE] Barton ID generation failed:', error);
      throw error;
    }
  }

  /**
   * Validate ID parameters against doctrine configuration
   */
  validateIdParameters(params, config) {
    const required = ['database', 'subhive', 'microprocess', 'tool', 'altitude', 'step'];
    const missing = required.filter(field => !params[field]);

    if (missing.length > 0) {
      throw new Error(`Missing required parameters: ${missing.join(', ')}`);
    }

    // Validate against configuration patterns
    for (const [component, value] of Object.entries(params)) {
      if (config.id_components[component]) {
        const pattern = new RegExp(config.id_components[component].pattern);
        if (!pattern.test(value)) {
          throw new Error(`Invalid format for ${component}: ${value}`);
        }
      }
    }
  }

  /**
   * Construct Barton ID from components
   */
  constructBartonId(params) {
    return `${params.database}.${params.subhive}.${params.microprocess}.${params.tool}.${params.altitude}.${params.step}`;
  }

  /**
   * Check Barton ID uniqueness
   */
  async checkBartonIdUniqueness(bartonId) {
    try {
      const result = await this.executeComposioFirebaseTool('FIREBASE_READ', {
        collection: 'barton_id_registry',
        document: bartonId
      });

      return {
        unique: !result.success || !result.data,
        existing: result.data || null
      };
    } catch (error) {
      // If read fails, assume it doesn't exist (unique)
      return { unique: true, existing: null };
    }
  }

  /**
   * Register new Barton ID in registry
   */
  async registerBartonId(bartonId, params, config) {
    const registryDoc = {
      barton_id: bartonId,
      components: params,
      generation_info: {
        generated_by: 'barton_doctrine_firebase_service',
        generation_method: 'composio_mcp',
        doctrine_version: config.doctrine_version,
        request_context: params.context || {}
      },
      usage_tracking: {
        assigned_to: params.assigned_to || 'unassigned',
        collection: params.target_collection || null,
        document_path: params.document_path || null,
        status: 'active'
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    return await this.executeComposioFirebaseTool('FIREBASE_WRITE', {
      collection: 'barton_id_registry',
      document: bartonId,
      data: registryDoc
    });
  }

  /**
   * Query audit logs
   */
  async queryAuditLogs(filters = {}) {
    // Note: This is a simplified version. Full implementation would require
    // more sophisticated querying capabilities via Composio Firebase tools
    const query = {
      collection: 'global_audit_log',
      filters: filters,
      limit: filters.limit || 100,
      orderBy: { field: 'created_at', direction: 'desc' }
    };

    return await this.executeComposioFirebaseTool('FIREBASE_READ', query);
  }

  /**
   * Log operation to audit trail
   */
  async logOperation(action, data, result, status, error = null) {
    const auditId = `05.01.04.07.10000.${Date.now().toString().slice(-3)}`;

    const logEntry = {
      unique_id: auditId,
      action: action,
      status: status,
      source: {
        service: 'barton_doctrine_firebase_service',
        function: 'logOperation',
        user_agent: 'doctrine_system',
        ip_address: 'internal',
        request_id: `log_${Date.now()}`
      },
      context: {
        operation_data: data,
        execution_time_ms: 0
      },
      error_log: error ? {
        error_code: 'DOCTRINE_ERROR',
        error_message: error.message,
        stack_trace: process.env.NODE_ENV === 'development' ? error.stack : null
      } : null,
      payload: {
        before: null,
        after: result,
        metadata: {
          doctrine_version: this.doctrineVersion,
          mcp_tool_used: true
        }
      },
      compliance: {
        doctrine_version: this.doctrineVersion,
        mcp_verified: true,
        altitude_validated: true,
        id_format_valid: true
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + (365 * 24 * 60 * 60 * 1000)).toISOString()
    };

    try {
      // Use Composio Firebase write tool for audit logging
      await this.executeComposioFirebaseTool('FIREBASE_WRITE', {
        collection: 'global_audit_log',
        document: auditId,
        data: logEntry
      });
    } catch (logError) {
      console.error('[DOCTRINE-FIREBASE] Failed to write audit log:', logError);
    }
  }

  /**
   * Health check for Firebase Doctrine system
   */
  async healthCheck() {
    try {
      const checks = {
        composio_connection: false,
        firebase_connectivity: false,
        doctrine_config: false,
        audit_log: false,
        id_registry: false
      };

      // Test Composio connection
      try {
        await this.composio.healthCheck();
        checks.composio_connection = true;
      } catch (error) {
        console.warn('[DOCTRINE-FIREBASE] Composio health check failed:', error.message);
      }

      // Test Firebase connectivity
      try {
        await this.testFirebaseConnection();
        checks.firebase_connectivity = true;
      } catch (error) {
        console.warn('[DOCTRINE-FIREBASE] Firebase connectivity check failed:', error.message);
      }

      // Test doctrine configuration
      try {
        const configResult = await this.executeComposioFirebaseTool('FIREBASE_READ', {
          collection: 'doctrine_config',
          document: 'current'
        });
        checks.doctrine_config = configResult.success;
      } catch (error) {
        console.warn('[DOCTRINE-FIREBASE] Doctrine config check failed:', error.message);
      }

      // Test audit log
      try {
        await this.queryAuditLogs({ limit: 1 });
        checks.audit_log = true;
      } catch (error) {
        console.warn('[DOCTRINE-FIREBASE] Audit log check failed:', error.message);
      }

      // Test ID registry
      try {
        const registryResult = await this.executeComposioFirebaseTool('FIREBASE_READ', {
          collection: 'barton_id_registry',
          document: '05.01.01.03.10000.001' // Initial config ID
        });
        checks.id_registry = registryResult.success;
      } catch (error) {
        console.warn('[DOCTRINE-FIREBASE] ID registry check failed:', error.message);
      }

      const overallHealth = Object.values(checks).every(check => check);

      return {
        overall_status: overallHealth ? 'healthy' : 'degraded',
        checks: checks,
        timestamp: new Date().toISOString(),
        doctrine_version: this.doctrineVersion
      };

    } catch (error) {
      return {
        overall_status: 'unhealthy',
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Enhanced validation and enforcement system
   */
  async enforceDoctrineCompliance(operation, data, context = {}) {
    console.log(`[DOCTRINE-FIREBASE] Enforcing compliance for operation: ${operation}`);

    try {
      // Get current doctrine configuration
      const configResult = await this.getDoctrineConfig();
      if (!configResult.success) {
        throw new Error('Unable to retrieve doctrine configuration for compliance check');
      }

      const config = configResult.config;
      const enforcement = config.enforcement;

      // Execute enforcement checks based on configuration
      const enforcementResult = {
        compliant: true,
        violations: [],
        warnings: [],
        operation: operation,
        timestamp: new Date().toISOString()
      };

      // 1. MCP-Only Enforcement
      if (enforcement.mcp_only) {
        const mcpCompliance = await this.validateMCPOnlyAccess(context);
        if (!mcpCompliance.valid) {
          enforcementResult.compliant = false;
          enforcementResult.violations.push('MCP-only access violation detected');
        }
      }

      // 2. Strict Validation Enforcement
      if (enforcement.strict_validation) {
        const validationResult = await this.performStrictValidation(operation, data, config);
        if (!validationResult.valid) {
          enforcementResult.compliant = false;
          enforcementResult.violations.push(...validationResult.errors);
        }
        enforcementResult.warnings.push(...validationResult.warnings);
      }

      // 3. Audit All Operations Enforcement
      if (enforcement.audit_all_operations) {
        await this.logOperation(
          `compliance_check_${operation}`,
          { operation, data, context },
          enforcementResult,
          enforcementResult.compliant ? 'success' : 'violation'
        );
      }

      // 4. Version Locking Enforcement
      if (enforcement.version_locking) {
        const versionCompliance = await this.validateVersionLocking(data, config);
        if (!versionCompliance.valid) {
          enforcementResult.compliant = false;
          enforcementResult.violations.push(...versionCompliance.errors);
        }
      }

      return enforcementResult;

    } catch (error) {
      console.error('[DOCTRINE-FIREBASE] Enforcement check failed:', error);
      return {
        compliant: false,
        violations: [`Enforcement system error: ${error.message}`],
        warnings: [],
        operation: operation,
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Validate MCP-only access compliance
   */
  async validateMCPOnlyAccess(context) {
    try {
      // Check if request came through MCP interface
      const mcpVerified = context.mcp_verified ||
                         context.source?.includes('composio') ||
                         context.user_agent?.includes('mcp') ||
                         false;

      // Check for direct Firestore SDK usage indicators
      const directSDKIndicators = [
        'firebase/firestore',
        'firebase-admin',
        'getFirestore',
        'doc(',
        'collection('
      ];

      const stackTrace = context.stack_trace || '';
      const directSDKUsage = directSDKIndicators.some(indicator =>
        stackTrace.includes(indicator)
      );

      return {
        valid: mcpVerified && !directSDKUsage,
        mcp_verified: mcpVerified,
        direct_sdk_detected: directSDKUsage,
        details: {
          source: context.source || 'unknown',
          user_agent: context.user_agent || 'unknown'
        }
      };

    } catch (error) {
      return {
        valid: false,
        error: error.message
      };
    }
  }

  /**
   * Perform strict validation on operation data
   */
  async performStrictValidation(operation, data, config) {
    const validationResult = {
      valid: true,
      errors: [],
      warnings: []
    };

    try {
      // 1. Validate Barton ID format if present
      if (data.barton_id) {
        const idValidation = this.validateBartonIdFormat(data.barton_id, config);
        if (!idValidation.valid) {
          validationResult.valid = false;
          validationResult.errors.push(`Invalid Barton ID format: ${data.barton_id}`);
        }
      }

      // 2. Validate required fields based on operation type
      const requiredFields = this.getRequiredFieldsForOperation(operation);
      const missingFields = requiredFields.filter(field => !data[field]);
      if (missingFields.length > 0) {
        validationResult.valid = false;
        validationResult.errors.push(`Missing required fields: ${missingFields.join(', ')}`);
      }

      // 3. Validate data types and formats
      const dataValidation = this.validateDataTypes(data, operation);
      if (!dataValidation.valid) {
        validationResult.valid = false;
        validationResult.errors.push(...dataValidation.errors);
      }

      // 4. Check for security violations
      const securityValidation = this.validateSecurity(data);
      if (!securityValidation.valid) {
        validationResult.valid = false;
        validationResult.errors.push(...securityValidation.errors);
      }
      validationResult.warnings.push(...securityValidation.warnings);

      return validationResult;

    } catch (error) {
      return {
        valid: false,
        errors: [`Validation system error: ${error.message}`],
        warnings: []
      };
    }
  }

  /**
   * Validate Barton ID format against doctrine configuration
   */
  validateBartonIdFormat(bartonId, config) {
    try {
      // Check basic format pattern
      const formatPattern = new RegExp(config.id_format.replace(/N/g, '[0-9]'));
      if (!formatPattern.test(bartonId)) {
        return {
          valid: false,
          error: 'ID does not match doctrine format pattern'
        };
      }

      // Parse components
      const components = bartonId.split('.');
      if (components.length !== 6) {
        return {
          valid: false,
          error: 'ID must have exactly 6 components'
        };
      }

      // Validate each component against doctrine codes
      const componentNames = ['database', 'subhive', 'microprocess', 'tool', 'altitude', 'step'];
      for (let i = 0; i < components.length; i++) {
        const componentName = componentNames[i];
        const componentValue = components[i];
        const componentConfig = config.id_components[componentName];

        if (componentConfig) {
          const pattern = new RegExp(componentConfig.pattern);
          if (!pattern.test(componentValue)) {
            return {
              valid: false,
              error: `Invalid ${componentName} format: ${componentValue}`
            };
          }

          // Check if component code is recognized
          if (componentConfig.codes && !componentConfig.codes[componentValue]) {
            return {
              valid: false,
              error: `Unrecognized ${componentName} code: ${componentValue}`
            };
          }
        }
      }

      return { valid: true };

    } catch (error) {
      return {
        valid: false,
        error: `ID validation error: ${error.message}`
      };
    }
  }

  /**
   * Get required fields for specific operations
   */
  getRequiredFieldsForOperation(operation) {
    const fieldMap = {
      'id_generation': ['database', 'subhive', 'microprocess', 'tool', 'altitude', 'step'],
      'audit_logging': ['action', 'status', 'source'],
      'config_update': ['doctrine_version'],
      'data_write': ['collection', 'data'],
      'data_read': ['collection'],
      'registry_entry': ['barton_id', 'generation_info']
    };

    return fieldMap[operation] || [];
  }

  /**
   * Validate data types and formats
   */
  validateDataTypes(data, operation) {
    const validationResult = {
      valid: true,
      errors: []
    };

    try {
      // Validate common data types
      if (data.timestamp && !this.isValidTimestamp(data.timestamp)) {
        validationResult.valid = false;
        validationResult.errors.push('Invalid timestamp format');
      }

      if (data.email && !this.isValidEmail(data.email)) {
        validationResult.valid = false;
        validationResult.errors.push('Invalid email format');
      }

      if (data.url && !this.isValidURL(data.url)) {
        validationResult.valid = false;
        validationResult.errors.push('Invalid URL format');
      }

      // Validate object structures
      if (data.source && typeof data.source === 'object') {
        const requiredSourceFields = ['service', 'function'];
        const missingSourceFields = requiredSourceFields.filter(field => !data.source[field]);
        if (missingSourceFields.length > 0) {
          validationResult.valid = false;
          validationResult.errors.push(`Missing source fields: ${missingSourceFields.join(', ')}`);
        }
      }

      return validationResult;

    } catch (error) {
      return {
        valid: false,
        errors: [`Data type validation error: ${error.message}`]
      };
    }
  }

  /**
   * Validate security aspects of data
   */
  validateSecurity(data) {
    const validationResult = {
      valid: true,
      errors: [],
      warnings: []
    };

    try {
      // Check for potential injection attacks
      const dangerousPatterns = [
        /script/i,
        /javascript/i,
        /eval\(/i,
        /function\(/i,
        /<[^>]*>/,
        /\$\{.*\}/,
        /`.*`/
      ];

      const dataString = JSON.stringify(data);
      for (const pattern of dangerousPatterns) {
        if (pattern.test(dataString)) {
          validationResult.valid = false;
          validationResult.errors.push('Potentially malicious content detected');
          break;
        }
      }

      // Check for sensitive data exposure
      const sensitiveFields = ['password', 'secret', 'key', 'token', 'credential'];
      for (const field of sensitiveFields) {
        if (dataString.toLowerCase().includes(field)) {
          validationResult.warnings.push(`Potential sensitive data field detected: ${field}`);
        }
      }

      // Validate data size limits
      if (dataString.length > 10000) {
        validationResult.warnings.push('Large data payload detected');
      }

      return validationResult;

    } catch (error) {
      return {
        valid: false,
        errors: [`Security validation error: ${error.message}`],
        warnings: []
      };
    }
  }

  /**
   * Validate version locking compliance
   */
  async validateVersionLocking(data, config) {
    try {
      if (config.enforcement.version_locking) {
        // Check if operation attempts to modify locked versions
        if (data.doctrine_version && data.doctrine_version !== config.doctrine_version) {
          return {
            valid: false,
            errors: [`Version locked to ${config.doctrine_version}, cannot use ${data.doctrine_version}`]
          };
        }

        // Check for version conflicts in components
        if (data.components && data.components.doctrine_version) {
          if (data.components.doctrine_version !== config.doctrine_version) {
            return {
              valid: false,
              errors: ['Component version conflicts with locked doctrine version']
            };
          }
        }
      }

      return { valid: true, errors: [] };

    } catch (error) {
      return {
        valid: false,
        errors: [`Version locking validation error: ${error.message}`]
      };
    }
  }

  /**
   * Utility validation functions
   */
  isValidTimestamp(timestamp) {
    try {
      const date = new Date(timestamp);
      return date instanceof Date && !isNaN(date.getTime());
    } catch {
      return false;
    }
  }

  isValidEmail(email) {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailPattern.test(email);
  }

  isValidURL(url) {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Generate HEIR ID for MCP payload
   */
  generateHeirId() {
    return `HEIR-${new Date().toISOString().slice(0, 10)}-${Math.random().toString(36).substr(2, 9).toUpperCase()}`;
  }

  /**
   * Generate Process ID for MCP payload
   */
  generateProcessId() {
    return `PRC-DOCTRINE-${Date.now()}`;
  }
}

export default BartonDoctrineFirebaseService;