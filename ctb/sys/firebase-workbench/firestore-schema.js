/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-B9D03D29
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * Doctrine Spec:
 * - Barton ID: 04.04.01
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Firestore schema definitions for Barton Doctrine Step 1
 * - Input: Schema validation requirements
 * - Output: Structured collection definitions
 * - MCP: Firebase (Composio-only access)
 */

/**
 * FIRESTORE SCHEMA DEFINITIONS - BARTON DOCTRINE STEP 1
 * =====================================================
 *
 * CRITICAL: All access must be via Composio MCP only
 * No direct Firestore SDK usage allowed
 */

// Collection: doctrine_config
export const DOCTRINE_CONFIG_SCHEMA = {
  collectionName: 'doctrine_config',
  description: 'Stores Barton Doctrine rules and configuration',
  accessPattern: 'mcp_only',

  // Document structure
  schema: {
    // Core doctrine configuration
    doctrine_version: {
      type: 'string',
      required: true,
      pattern: '^\\d+\\.\\d+\\.\\d+$',
      description: 'Semantic version of Barton Doctrine (e.g., "1.0.0")',
      example: '1.0.0'
    },

    // Barton ID format specification
    id_format: {
      type: 'string',
      required: true,
      pattern: '^NN\\.NN\\.NN\\.NN\\.NNNNN\\.NNN$',
      description: 'Template for Barton ID format',
      example: 'NN.NN.NN.NN.NNNNN.NNN'
    },

    // ID component definitions
    id_components: {
      type: 'object',
      required: true,
      properties: {
        database: {
          type: 'object',
          description: 'Database identifier codes',
          properties: {
            pattern: '^[0-9]{2}$',
            codes: {
              type: 'object',
              example: {
                '01': 'primary_postgres',
                '02': 'analytics_warehouse',
                '03': 'cache_redis',
                '04': 'firebase_realtime',
                '05': 'firebase_firestore'
              }
            }
          }
        },
        subhive: {
          type: 'object',
          description: 'Subhive/department codes',
          properties: {
            pattern: '^[0-9]{2}$',
            codes: {
              type: 'object',
              example: {
                '01': 'intake',
                '02': 'processing',
                '03': 'vault',
                '04': 'outreach',
                '05': 'analytics'
              }
            }
          }
        },
        microprocess: {
          type: 'object',
          description: 'Microprocess/service codes',
          properties: {
            pattern: '^[0-9]{2}$',
            codes: {
              type: 'object',
              example: {
                '01': 'ingestion',
                '02': 'validation',
                '03': 'enrichment',
                '04': 'scoring',
                '05': 'promotion'
              }
            }
          }
        },
        tool: {
          type: 'object',
          description: 'Tool/technology codes',
          properties: {
            pattern: '^[0-9]{2}$',
            codes: {
              type: 'object',
              example: {
                '01': 'postgres',
                '02': 'redis',
                '03': 'firebase',
                '04': 'composio',
                '05': 'neon',
                '06': 'vercel',
                '07': 'custom'
              }
            }
          }
        },
        altitude: {
          type: 'object',
          description: 'Processing altitude levels',
          properties: {
            pattern: '^[0-9]{5}$',
            codes: {
              type: 'object',
              example: {
                '10000': 'execution_layer',
                '20000': 'orchestration_layer',
                '30000': 'business_logic_layer',
                '40000': 'presentation_layer',
                '50000': 'user_interface_layer'
              }
            }
          }
        },
        step: {
          type: 'object',
          description: 'Process step sequence',
          properties: {
            pattern: '^[0-9]{3}$',
            codes: {
              type: 'object',
              example: {
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
          }
        }
      }
    },

    // Altitude level definitions
    altitude_codes: {
      type: 'object',
      required: true,
      properties: {
        '10000': {
          type: 'object',
          properties: {
            name: { type: 'string', example: 'Execution Layer' },
            description: { type: 'string', example: 'Direct data operations and API calls' },
            permissions: { type: 'array', example: ['read', 'write', 'delete'] }
          }
        },
        '20000': {
          type: 'object',
          properties: {
            name: { type: 'string', example: 'Orchestration Layer' },
            description: { type: 'string', example: 'Service coordination and workflow management' },
            permissions: { type: 'array', example: ['read', 'write', 'orchestrate'] }
          }
        },
        '30000': {
          type: 'object',
          properties: {
            name: { type: 'string', example: 'Business Logic Layer' },
            description: { type: 'string', example: 'Business rules and decision making' },
            permissions: { type: 'array', example: ['read', 'validate', 'decide'] }
          }
        }
      }
    },

    // Version control
    schema_version: {
      type: 'string',
      required: true,
      description: 'Schema version for migration tracking',
      example: '1.0.0'
    },

    // Enforcement settings
    enforcement: {
      type: 'object',
      required: true,
      properties: {
        strict_validation: {
          type: 'boolean',
          default: true,
          description: 'Enforce strict Barton ID validation'
        },
        mcp_only: {
          type: 'boolean',
          default: true,
          description: 'Require MCP-only access patterns'
        },
        audit_all_operations: {
          type: 'boolean',
          default: true,
          description: 'Log all operations to audit trail'
        },
        version_locking: {
          type: 'boolean',
          default: true,
          description: 'Lock IDs to specific doctrine versions'
        }
      }
    },

    // Metadata
    created_at: {
      type: 'timestamp',
      required: true,
      description: 'Document creation timestamp'
    },
    updated_at: {
      type: 'timestamp',
      required: true,
      description: 'Last update timestamp'
    },
    created_by: {
      type: 'string',
      required: true,
      description: 'Service or user that created this configuration'
    },
    barton_id: {
      type: 'string',
      required: true,
      pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      description: 'Barton ID of this configuration document'
    }
  },

  // Collection-level configuration
  settings: {
    read_time: 'strong_consistency',
    write_concern: 'majority',
    indexes: [
      { fields: ['doctrine_version'], unique: true },
      { fields: ['created_at'], order: 'desc' },
      { fields: ['barton_id'], unique: true }
    ]
  }
};

// Collection: global_audit_log
export const GLOBAL_AUDIT_LOG_SCHEMA = {
  collectionName: 'global_audit_log',
  description: 'Captures ALL Barton Doctrine events and operations',
  accessPattern: 'mcp_only',

  schema: {
    // Unique identifier
    unique_id: {
      type: 'string',
      required: true,
      pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      description: 'Barton ID for this audit log entry',
      indexed: true
    },

    // Action details
    action: {
      type: 'string',
      required: true,
      enum: [
        'id_generation',
        'migration',
        'validation',
        'enrichment',
        'promotion',
        'configuration_update',
        'schema_change',
        'access_attempt',
        'error_occurrence',
        'system_health_check'
      ],
      description: 'Type of action being logged'
    },

    // Operation status
    status: {
      type: 'string',
      required: true,
      enum: ['success', 'failure', 'warning', 'info'],
      description: 'Result status of the operation'
    },

    // Source identification
    source: {
      type: 'object',
      required: true,
      properties: {
        service: {
          type: 'string',
          required: true,
          description: 'Service that initiated the action'
        },
        function: {
          type: 'string',
          description: 'Specific function or method'
        },
        user_agent: {
          type: 'string',
          description: 'User agent or client identifier'
        },
        ip_address: {
          type: 'string',
          description: 'Source IP address if applicable'
        },
        request_id: {
          type: 'string',
          description: 'Request correlation ID'
        }
      }
    },

    // Operation context
    context: {
      type: 'object',
      properties: {
        target_collection: {
          type: 'string',
          description: 'Target Firestore collection'
        },
        target_document: {
          type: 'string',
          description: 'Target document ID'
        },
        operation_type: {
          type: 'string',
          enum: ['create', 'read', 'update', 'delete', 'query'],
          description: 'CRUD operation type'
        },
        data_size: {
          type: 'number',
          description: 'Size of data processed (bytes)'
        },
        execution_time_ms: {
          type: 'number',
          description: 'Operation execution time in milliseconds'
        }
      }
    },

    // Error information
    error_log: {
      type: 'object',
      properties: {
        error_code: {
          type: 'string',
          description: 'Standardized error code'
        },
        error_message: {
          type: 'string',
          description: 'Human-readable error message'
        },
        stack_trace: {
          type: 'string',
          description: 'Technical stack trace (dev only)'
        },
        retry_count: {
          type: 'number',
          description: 'Number of retry attempts'
        },
        recovery_action: {
          type: 'string',
          description: 'Action taken to recover from error'
        }
      }
    },

    // Data payload (for significant operations)
    payload: {
      type: 'object',
      description: 'Operation-specific data (sanitized)',
      properties: {
        before: {
          type: 'object',
          description: 'Data state before operation'
        },
        after: {
          type: 'object',
          description: 'Data state after operation'
        },
        metadata: {
          type: 'object',
          description: 'Additional operation metadata'
        }
      }
    },

    // Compliance tracking
    compliance: {
      type: 'object',
      properties: {
        doctrine_version: {
          type: 'string',
          description: 'Barton Doctrine version in effect'
        },
        mcp_verified: {
          type: 'boolean',
          description: 'Verified as MCP-only access'
        },
        altitude_validated: {
          type: 'boolean',
          description: 'Altitude level validation passed'
        },
        id_format_valid: {
          type: 'boolean',
          description: 'Barton ID format validation result'
        }
      }
    },

    // Timestamps
    created_at: {
      type: 'timestamp',
      required: true,
      description: 'When the event occurred'
    },
    updated_at: {
      type: 'timestamp',
      required: true,
      description: 'Last update to this log entry'
    },

    // Retention
    expires_at: {
      type: 'timestamp',
      description: 'When this log entry should be archived/deleted'
    }
  },

  settings: {
    read_time: 'eventual_consistency',
    write_concern: 'majority',
    ttl_field: 'expires_at',
    indexes: [
      { fields: ['unique_id'], unique: true },
      { fields: ['action', 'status'] },
      { fields: ['created_at'], order: 'desc' },
      { fields: ['source.service'] },
      { fields: ['compliance.doctrine_version'] },
      { fields: ['expires_at'] }
    ]
  }
};

// Collection: barton_id_registry
export const BARTON_ID_REGISTRY_SCHEMA = {
  collectionName: 'barton_id_registry',
  description: 'Registry of all generated Barton IDs for uniqueness enforcement',
  accessPattern: 'mcp_only',

  schema: {
    barton_id: {
      type: 'string',
      required: true,
      pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      description: 'The Barton ID itself'
    },

    components: {
      type: 'object',
      required: true,
      properties: {
        database: { type: 'string', pattern: '^[0-9]{2}$' },
        subhive: { type: 'string', pattern: '^[0-9]{2}$' },
        microprocess: { type: 'string', pattern: '^[0-9]{2}$' },
        tool: { type: 'string', pattern: '^[0-9]{2}$' },
        altitude: { type: 'string', pattern: '^[0-9]{5}$' },
        step: { type: 'string', pattern: '^[0-9]{3}$' }
      }
    },

    generation_info: {
      type: 'object',
      required: true,
      properties: {
        generated_by: { type: 'string', description: 'Service that generated this ID' },
        generation_method: { type: 'string', description: 'Method used for generation' },
        doctrine_version: { type: 'string', description: 'Doctrine version at time of generation' },
        request_context: { type: 'object', description: 'Context when ID was requested' }
      }
    },

    usage_tracking: {
      type: 'object',
      properties: {
        assigned_to: { type: 'string', description: 'What this ID is assigned to' },
        collection: { type: 'string', description: 'Firestore collection using this ID' },
        document_path: { type: 'string', description: 'Full document path' },
        status: {
          type: 'string',
          enum: ['active', 'retired', 'reserved'],
          default: 'active'
        }
      }
    },

    created_at: { type: 'timestamp', required: true },
    updated_at: { type: 'timestamp', required: true }
  },

  settings: {
    read_time: 'strong_consistency',
    write_concern: 'majority',
    indexes: [
      { fields: ['barton_id'], unique: true },
      { fields: ['components.database', 'components.subhive'] },
      { fields: ['generation_info.doctrine_version'] },
      { fields: ['usage_tracking.status'] },
      { fields: ['created_at'], order: 'desc' }
    ]
  }
};

// Export all schemas
export const DOCTRINE_SCHEMAS = {
  doctrine_config: DOCTRINE_CONFIG_SCHEMA,
  global_audit_log: GLOBAL_AUDIT_LOG_SCHEMA,
  barton_id_registry: BARTON_ID_REGISTRY_SCHEMA
};

// Schema validation functions
export const validateDocumentSchema = (collectionName, document) => {
  const schema = DOCTRINE_SCHEMAS[collectionName];
  if (!schema) {
    throw new Error(`Unknown collection: ${collectionName}`);
  }

  // Implement validation logic here
  // This would validate the document against the schema
  return {
    valid: true,
    errors: []
  };
};

// Default doctrine configuration
export const DEFAULT_DOCTRINE_CONFIG = {
  doctrine_version: '1.0.0',
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
  created_by: 'barton_doctrine_system',
  barton_id: '05.01.01.03.10000.001'
};