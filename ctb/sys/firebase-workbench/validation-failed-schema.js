/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-566BBF69
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * Doctrine Spec:
 * - Barton ID: 04.04.01
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Step 2A validation_failed collection schema for handling validation failures
 * - Input: Failed validation documents from company/people intake
 * - Output: Structured error handling for adjuster/enrichment processes
 * - MCP: Firebase (Composio-only access for validation failures)
 */

// Collection: validation_failed
export const VALIDATION_FAILED_SCHEMA = {
  collectionName: 'validation_failed',
  description: 'Documents that failed validation in Step 2A with structured error handling',
  accessPattern: 'mcp_only',
  doctrineCompliance: {
    mcp_enforcement: true,
    audit_all_operations: true,
    strict_validation: true,
    error_categorization: true
  },
  schema: {
    // Original document identifier
    original_id: {
      type: 'string',
      required: true,
      description: 'Original Barton ID from intake collection',
      example: '05.01.01.03.10000.002',
      validation: 'Must be valid Barton ID'
    },

    // Document type identification
    document_type: {
      type: 'string',
      required: true,
      enum: ['company', 'person'],
      description: 'Type of document that failed validation',
      example: 'company'
    },

    // Original collection reference
    source_collection: {
      type: 'string',
      required: true,
      enum: ['company_raw_intake', 'people_raw_intake'],
      description: 'Source collection where document originated',
      example: 'company_raw_intake'
    },

    // Validation failure metadata
    validation_status: {
      type: 'string',
      required: true,
      enum: ['failed'],
      description: 'Validation status (always failed for this collection)',
      example: 'failed'
    },

    validation_timestamp: {
      type: 'string',
      required: true,
      format: 'iso8601',
      description: 'When validation was attempted',
      example: '2024-01-15T10:30:00.000Z'
    },

    failed_at: {
      type: 'string',
      required: true,
      format: 'iso8601',
      description: 'When document was moved to failed collection',
      example: '2024-01-15T10:30:05.000Z'
    },

    // Structured error handling
    validation_errors: {
      type: 'array',
      required: true,
      description: 'Array of validation errors that caused failure',
      items: {
        type: 'object',
        properties: {
          field: {
            type: 'string',
            required: true,
            description: 'Field that failed validation'
          },
          error: {
            type: 'string',
            required: true,
            description: 'Error code for the validation failure'
          },
          message: {
            type: 'string',
            required: true,
            description: 'Human-readable error message'
          }
        }
      },
      example: [
        {
          field: 'phone_number',
          error: 'invalid_phone_format',
          message: 'Phone number could not be normalized to E.164 format'
        }
      ]
    },

    // Enhanced error categorization for adjuster
    structured_errors: {
      type: 'array',
      required: true,
      description: 'Categorized errors for automated adjuster processing',
      items: {
        type: 'object',
        properties: {
          field: {
            type: 'string',
            required: true,
            description: 'Field that failed validation'
          },
          error_code: {
            type: 'string',
            required: true,
            description: 'Standardized error code'
          },
          message: {
            type: 'string',
            required: true,
            description: 'Error message'
          },
          severity: {
            type: 'string',
            required: true,
            enum: ['error', 'warning', 'critical'],
            description: 'Error severity level'
          },
          actionable: {
            type: 'boolean',
            required: true,
            description: 'Whether error can be automatically fixed'
          },
          suggested_action: {
            type: 'string',
            required: false,
            description: 'Suggested remediation action'
          },
          enrichment_required: {
            type: 'boolean',
            required: false,
            default: false,
            description: 'Whether external enrichment is needed'
          }
        }
      },
      example: [
        {
          field: 'phone_number',
          error_code: 'INVALID_PHONE_FORMAT',
          message: 'Phone number could not be normalized to E.164 format',
          severity: 'error',
          actionable: true,
          suggested_action: 'normalize_phone_number',
          enrichment_required: false
        }
      ]
    },

    // Retry and processing metadata
    retry_count: {
      type: 'number',
      required: true,
      default: 0,
      minimum: 0,
      description: 'Number of validation retry attempts',
      example: 0
    },

    retry_history: {
      type: 'array',
      required: false,
      description: 'History of retry attempts',
      items: {
        type: 'object',
        properties: {
          attempt_number: { type: 'number' },
          attempted_at: { type: 'string', format: 'iso8601' },
          result: { type: 'string', enum: ['failed', 'skipped'] },
          errors: { type: 'array' }
        }
      }
    },

    // Adjuster processing status
    adjuster_status: {
      type: 'string',
      required: false,
      enum: ['pending', 'processing', 'completed', 'failed', 'skipped'],
      default: 'pending',
      description: 'Status of automated adjuster processing',
      example: 'pending'
    },

    adjuster_processed_at: {
      type: 'string',
      required: false,
      format: 'iso8601',
      description: 'When adjuster processed this document'
    },

    adjuster_actions: {
      type: 'array',
      required: false,
      description: 'Actions taken by automated adjuster',
      items: {
        type: 'object',
        properties: {
          action: { type: 'string' },
          field: { type: 'string' },
          old_value: { type: 'string' },
          new_value: { type: 'string' },
          timestamp: { type: 'string', format: 'iso8601' },
          success: { type: 'boolean' }
        }
      }
    },

    // Enrichment requirements
    enrichment_needed: {
      type: 'boolean',
      required: false,
      default: false,
      description: 'Whether external data enrichment is required'
    },

    enrichment_sources: {
      type: 'array',
      required: false,
      description: 'External sources needed for enrichment',
      items: {
        type: 'string',
        enum: ['clearbit', 'linkedin', 'zoominfo', 'apollo', 'manual']
      },
      example: ['clearbit', 'linkedin']
    },

    // Document resolution
    resolution_status: {
      type: 'string',
      required: false,
      enum: ['unresolved', 'auto_fixed', 'enriched', 'manual_review', 'discarded'],
      default: 'unresolved',
      description: 'Final resolution status of the failed document'
    },

    resolved_at: {
      type: 'string',
      required: false,
      format: 'iso8601',
      description: 'When document was resolved'
    },

    resolved_by: {
      type: 'string',
      required: false,
      description: 'Who or what resolved the document (system/user_id)'
    },

    // Original document data (preserved for reference)
    original_data: {
      type: 'object',
      required: true,
      description: 'Complete original document data from intake',
      validation: 'Must contain all original fields'
    },

    // MCP tracking
    mcp_trace: {
      type: 'object',
      required: true,
      description: 'MCP operation tracking',
      properties: {
        validator_endpoint: {
          type: 'string',
          required: true,
          description: 'Validation endpoint that processed document'
        },
        validation_operation: {
          type: 'string',
          required: true,
          enum: ['validate_company', 'validate_person']
        },
        request_id: {
          type: 'string',
          required: true,
          description: 'Unique request identifier'
        },
        user_id: {
          type: 'string',
          required: true,
          description: 'User/system that initiated validation'
        }
      }
    },

    // Timestamps
    created_at: {
      type: 'string',
      required: true,
      format: 'iso8601',
      description: 'When document was created in failed collection',
      example: '2024-01-15T10:30:05.000Z'
    },

    updated_at: {
      type: 'string',
      required: true,
      format: 'iso8601',
      description: 'When document was last updated',
      example: '2024-01-15T10:30:05.000Z'
    }
  },

  // Firestore indexes for efficient querying
  indexes: [
    {
      fields: ['document_type', 'validation_status'],
      description: 'Query failed documents by type'
    },
    {
      fields: ['adjuster_status', 'failed_at'],
      description: 'Query documents pending adjuster processing'
    },
    {
      fields: ['enrichment_needed', 'resolution_status'],
      description: 'Query documents needing enrichment'
    },
    {
      fields: ['source_collection', 'failed_at'],
      description: 'Query by source collection and failure time'
    },
    {
      fields: ['retry_count', 'failed_at'],
      description: 'Query documents by retry attempts'
    }
  ],

  // Security rules for MCP-only access
  securityRules: {
    read: 'request.auth != null && request.auth.token.composio_mcp == true',
    write: 'request.auth != null && request.auth.token.composio_mcp == true',
    delete: 'request.auth != null && request.auth.token.composio_mcp == true && resource.data.resolution_status == "discarded"'
  }
};

// Error code definitions for structured error handling
export const VALIDATION_ERROR_CODES = {
  // Company validation errors
  COMPANY_NAME_MISSING: {
    code: 'COMPANY_NAME_MISSING',
    severity: 'error',
    actionable: false,
    enrichment_sources: ['clearbit', 'apollo']
  },
  WEBSITE_URL_MISSING: {
    code: 'WEBSITE_URL_MISSING',
    severity: 'error',
    actionable: false,
    enrichment_sources: ['clearbit', 'apollo']
  },
  WEBSITE_URL_INVALID: {
    code: 'WEBSITE_URL_INVALID',
    severity: 'error',
    actionable: true,
    suggested_action: 'normalize_url'
  },
  PHONE_NUMBER_MISSING: {
    code: 'PHONE_NUMBER_MISSING',
    severity: 'error',
    actionable: false,
    enrichment_sources: ['clearbit', 'apollo', 'zoominfo']
  },
  PHONE_NUMBER_INVALID: {
    code: 'PHONE_NUMBER_INVALID',
    severity: 'error',
    actionable: true,
    suggested_action: 'normalize_phone_number'
  },
  EMPLOYEE_COUNT_MISSING: {
    code: 'EMPLOYEE_COUNT_MISSING',
    severity: 'warning',
    actionable: false,
    enrichment_sources: ['clearbit', 'linkedin']
  },
  EMPLOYEE_COUNT_INVALID: {
    code: 'EMPLOYEE_COUNT_INVALID',
    severity: 'error',
    actionable: true,
    suggested_action: 'normalize_employee_count'
  },

  // Person validation errors
  FIRST_NAME_MISSING: {
    code: 'FIRST_NAME_MISSING',
    severity: 'error',
    actionable: false,
    enrichment_sources: ['linkedin', 'apollo']
  },
  LAST_NAME_MISSING: {
    code: 'LAST_NAME_MISSING',
    severity: 'error',
    actionable: false,
    enrichment_sources: ['linkedin', 'apollo']
  },
  EMAIL_MISSING: {
    code: 'EMAIL_MISSING',
    severity: 'warning',
    actionable: false,
    enrichment_sources: ['linkedin', 'apollo', 'zoominfo']
  },
  EMAIL_INVALID: {
    code: 'EMAIL_INVALID',
    severity: 'error',
    actionable: true,
    suggested_action: 'validate_email_format'
  },
  CONTACT_INFO_MISSING: {
    code: 'CONTACT_INFO_MISSING',
    severity: 'error',
    actionable: false,
    enrichment_sources: ['linkedin', 'apollo']
  },

  // System errors
  SYSTEM_ERROR: {
    code: 'SYSTEM_ERROR',
    severity: 'critical',
    actionable: false,
    suggested_action: 'manual_review'
  }
};

export default { VALIDATION_FAILED_SCHEMA, VALIDATION_ERROR_CODES };