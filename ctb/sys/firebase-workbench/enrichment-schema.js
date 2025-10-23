/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-3F056BEE
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * Doctrine Spec:
 * - Barton ID: 04.04.01
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Step 2B Enrichment collection schemas for data enhancement operations
 * - Input: Records requiring enrichment from validation or intake processes
 * - Output: Firestore schema definitions for enrichment jobs and audit logging
 * - MCP: Firebase (Composio-only access for enrichment operations)
 */

// Collection: enrichment_jobs
export const ENRICHMENT_JOBS_SCHEMA = {
  collectionName: 'enrichment_jobs',
  description: 'Queue of records requiring data enrichment with job management',
  accessPattern: 'mcp_only',
  doctrineCompliance: {
    mcp_enforcement: true,
    audit_all_operations: true,
    strict_validation: true,
    batch_processing: true
  },
  schema: {
    // Record identification
    unique_id: {
      type: 'string',
      required: true,
      pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      description: 'Barton ID of the record to be enriched',
      example: '05.01.01.03.10000.002',
      validation: 'Must be valid Barton ID format'
    },

    // Record type classification
    record_type: {
      type: 'string',
      required: true,
      enum: ['company', 'person'],
      description: 'Type of record being enriched',
      example: 'company'
    },

    // Source collection reference
    source_collection: {
      type: 'string',
      required: true,
      enum: ['company_raw_intake', 'people_raw_intake', 'validation_failed'],
      description: 'Source collection where record originated',
      example: 'company_raw_intake'
    },

    // Job status management
    status: {
      type: 'string',
      required: true,
      enum: ['pending', 'processing', 'enriched', 'failed', 'skipped'],
      default: 'pending',
      description: 'Current enrichment job status',
      example: 'pending'
    },

    // Job priority and scheduling
    priority: {
      type: 'string',
      required: false,
      enum: ['low', 'normal', 'high', 'urgent'],
      default: 'normal',
      description: 'Job processing priority'
    },

    scheduled_for: {
      type: 'string',
      required: false,
      format: 'iso8601',
      description: 'When job should be processed (for delayed processing)',
      example: '2024-01-15T10:30:00.000Z'
    },

    // Enrichment requirements
    enrichment_types: {
      type: 'array',
      required: true,
      description: 'Types of enrichment needed for this record',
      items: {
        type: 'string',
        enum: [
          // Company enrichment types
          'normalize_domain',
          'repair_phone',
          'geocode_address',
          'company_size_lookup',
          'industry_classification',
          'social_media_lookup',

          // Person enrichment types
          'infer_slot_type',
          'determine_seniority',
          'normalize_phone',
          'normalize_email',
          'linkedin_lookup',
          'title_standardization'
        ]
      },
      example: ['normalize_domain', 'repair_phone', 'geocode_address']
    },

    // Processing metadata
    retry_count: {
      type: 'number',
      required: true,
      default: 0,
      minimum: 0,
      maximum: 5,
      description: 'Number of enrichment retry attempts'
    },

    max_retries: {
      type: 'number',
      required: false,
      default: 3,
      minimum: 1,
      maximum: 10,
      description: 'Maximum allowed retry attempts'
    },

    // Error tracking
    last_error: {
      type: 'object',
      required: false,
      description: 'Details of the last enrichment error',
      properties: {
        error_code: { type: 'string' },
        error_message: { type: 'string' },
        occurred_at: { type: 'string', format: 'iso8601' },
        enrichment_type: { type: 'string' },
        retry_after: { type: 'string', format: 'iso8601' }
      }
    },

    // Processing history
    processing_history: {
      type: 'array',
      required: false,
      description: 'History of processing attempts',
      items: {
        type: 'object',
        properties: {
          attempt_number: { type: 'number' },
          started_at: { type: 'string', format: 'iso8601' },
          completed_at: { type: 'string', format: 'iso8601' },
          status: { type: 'string', enum: ['processing', 'enriched', 'failed'] },
          enrichment_types_completed: { type: 'array' },
          error_details: { type: 'object' }
        }
      }
    },

    // External service configuration
    enrichment_providers: {
      type: 'object',
      required: false,
      description: 'External services to use for enrichment',
      properties: {
        clearbit: { type: 'boolean', default: false },
        apollo: { type: 'boolean', default: false },
        zoominfo: { type: 'boolean', default: false },
        linkedin: { type: 'boolean', default: false },
        google_places: { type: 'boolean', default: false },
        internal_only: { type: 'boolean', default: true }
      }
    },

    // MCP tracking
    mcp_trace: {
      type: 'object',
      required: true,
      description: 'MCP operation tracking for enrichment job',
      properties: {
        created_via: {
          type: 'string',
          required: true,
          description: 'How this job was created (validation_failure, manual, batch)'
        },
        request_id: {
          type: 'string',
          required: true,
          description: 'Unique request identifier'
        },
        user_id: {
          type: 'string',
          required: true,
          description: 'User/system that initiated enrichment'
        },
        composio_session: {
          type: 'string',
          required: false,
          description: 'Composio session identifier'
        }
      }
    },

    // Timestamps
    created_at: {
      type: 'string',
      required: true,
      format: 'iso8601',
      description: 'When enrichment job was created',
      example: '2024-01-15T10:30:00.000Z'
    },

    started_at: {
      type: 'string',
      required: false,
      format: 'iso8601',
      description: 'When enrichment processing started'
    },

    completed_at: {
      type: 'string',
      required: false,
      format: 'iso8601',
      description: 'When enrichment processing completed'
    },

    updated_at: {
      type: 'string',
      required: true,
      format: 'iso8601',
      description: 'When job was last updated',
      example: '2024-01-15T10:30:00.000Z'
    }
  },

  // Firestore indexes for efficient querying
  indexes: [
    {
      fields: ['status', 'priority', 'created_at'],
      description: 'Query pending jobs by priority'
    },
    {
      fields: ['record_type', 'status'],
      description: 'Query jobs by type and status'
    },
    {
      fields: ['scheduled_for', 'status'],
      description: 'Query scheduled jobs'
    },
    {
      fields: ['source_collection', 'status'],
      description: 'Query by source collection'
    },
    {
      fields: ['retry_count', 'status'],
      description: 'Query failed jobs for retry'
    }
  ],

  // Security rules for MCP-only access
  securityRules: {
    read: 'request.auth != null && request.auth.token.composio_mcp == true',
    write: 'request.auth != null && request.auth.token.composio_mcp == true',
    delete: 'request.auth != null && request.auth.token.composio_mcp == true && resource.data.status in ["enriched", "failed", "skipped"]'
  }
};

// Collection: enrichment_audit_log
export const ENRICHMENT_AUDIT_LOG_SCHEMA = {
  collectionName: 'enrichment_audit_log',
  description: 'Comprehensive audit log for all enrichment operations and changes',
  accessPattern: 'mcp_only',
  doctrineCompliance: {
    mcp_enforcement: true,
    immutable_logs: true,
    complete_audit_trail: true
  },
  schema: {
    // Record identification
    unique_id: {
      type: 'string',
      required: true,
      pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      description: 'Barton ID of the record that was enriched',
      example: '05.01.01.03.10000.002',
      validation: 'Must be valid Barton ID format'
    },

    // Operation details
    action: {
      type: 'string',
      required: true,
      enum: ['enrich', 'retry', 'skip', 'fail', 'queue', 'dequeue'],
      description: 'Type of enrichment action performed',
      example: 'enrich'
    },

    // Record type for categorization
    record_type: {
      type: 'string',
      required: true,
      enum: ['company', 'person'],
      description: 'Type of record being enriched'
    },

    // Enrichment operation details
    enrichment_operation: {
      type: 'object',
      required: true,
      description: 'Details of the enrichment operation performed',
      properties: {
        operation_type: {
          type: 'string',
          required: true,
          enum: [
            'normalize_domain', 'repair_phone', 'geocode_address',
            'company_size_lookup', 'industry_classification', 'social_media_lookup',
            'infer_slot_type', 'determine_seniority', 'normalize_phone',
            'normalize_email', 'linkedin_lookup', 'title_standardization'
          ]
        },
        provider: {
          type: 'string',
          required: false,
          enum: ['internal', 'clearbit', 'apollo', 'zoominfo', 'linkedin', 'google_places']
        },
        confidence_score: {
          type: 'number',
          required: false,
          minimum: 0,
          maximum: 1,
          description: 'Confidence in enrichment result (0-1)'
        }
      }
    },

    // Data change tracking
    before_values: {
      type: 'object',
      required: true,
      description: 'Field values before enrichment',
      validation: 'Must contain original field values'
    },

    after_values: {
      type: 'object',
      required: true,
      description: 'Field values after enrichment',
      validation: 'Must contain updated field values'
    },

    // Change summary
    fields_changed: {
      type: 'array',
      required: true,
      description: 'List of fields that were modified',
      items: {
        type: 'string'
      },
      example: ['website_url', 'phone_number', 'address']
    },

    // Operation result
    status: {
      type: 'string',
      required: true,
      enum: ['success', 'partial_success', 'failed', 'skipped'],
      description: 'Result status of the enrichment operation',
      example: 'success'
    },

    // Error logging
    error_log: {
      type: 'object',
      required: false,
      description: 'Error details if enrichment failed',
      properties: {
        error_code: {
          type: 'string',
          required: true,
          description: 'Standardized error code'
        },
        error_message: {
          type: 'string',
          required: true,
          description: 'Human-readable error message'
        },
        error_type: {
          type: 'string',
          required: true,
          enum: ['validation', 'network', 'api_limit', 'provider_error', 'system_error']
        },
        retry_possible: {
          type: 'boolean',
          required: true,
          description: 'Whether this operation can be retried'
        },
        provider_response: {
          type: 'object',
          required: false,
          description: 'Raw response from external provider (if applicable)'
        }
      }
    },

    // Performance metrics
    performance_metrics: {
      type: 'object',
      required: false,
      description: 'Performance tracking for enrichment operation',
      properties: {
        processing_time_ms: {
          type: 'number',
          description: 'Time taken for enrichment operation in milliseconds'
        },
        api_calls_made: {
          type: 'number',
          description: 'Number of external API calls required'
        },
        data_quality_score: {
          type: 'number',
          minimum: 0,
          maximum: 1,
          description: 'Quality score of enriched data'
        }
      }
    },

    // MCP tracking
    mcp_trace: {
      type: 'object',
      required: true,
      description: 'MCP operation tracking',
      properties: {
        enrichment_endpoint: {
          type: 'string',
          required: true,
          description: 'Enrichment endpoint that processed record'
        },
        enrichment_operation: {
          type: 'string',
          required: true,
          enum: ['enrich_company', 'enrich_person', 'batch_enrich']
        },
        request_id: {
          type: 'string',
          required: true,
          description: 'Unique request identifier'
        },
        user_id: {
          type: 'string',
          required: true,
          description: 'User/system that initiated enrichment'
        },
        composio_session: {
          type: 'string',
          required: false,
          description: 'Composio session identifier'
        }
      }
    },

    // Job reference
    enrichment_job_id: {
      type: 'string',
      required: false,
      description: 'Reference to enrichment_jobs document ID'
    },

    // Timestamps
    created_at: {
      type: 'string',
      required: true,
      format: 'iso8601',
      description: 'When audit log entry was created',
      example: '2024-01-15T10:30:00.000Z'
    },

    operation_started_at: {
      type: 'string',
      required: false,
      format: 'iso8601',
      description: 'When enrichment operation started'
    },

    operation_completed_at: {
      type: 'string',
      required: false,
      format: 'iso8601',
      description: 'When enrichment operation completed'
    }
  },

  // Firestore indexes for audit log queries
  indexes: [
    {
      fields: ['unique_id', 'created_at'],
      description: 'Query audit logs by record ID and time'
    },
    {
      fields: ['action', 'status', 'created_at'],
      description: 'Query by action type and status'
    },
    {
      fields: ['record_type', 'action'],
      description: 'Query by record type and action'
    },
    {
      fields: ['status', 'created_at'],
      description: 'Query by operation status'
    },
    {
      fields: ['enrichment_job_id'],
      description: 'Query logs by job reference'
    }
  ],

  // Security rules for audit log (append-only)
  securityRules: {
    read: 'request.auth != null && request.auth.token.composio_mcp == true',
    write: 'request.auth != null && request.auth.token.composio_mcp == true && request.method == "create"',
    delete: 'false' // Audit logs are immutable
  }
};

// Enrichment type definitions
export const ENRICHMENT_TYPE_DEFINITIONS = {
  // Company enrichment operations
  company: {
    normalize_domain: {
      description: 'Normalize and validate company domain/website URL',
      input_fields: ['website_url'],
      output_fields: ['website_url', 'domain', 'domain_status'],
      providers: ['internal'],
      priority: 'high'
    },
    repair_phone: {
      description: 'Repair and normalize company phone numbers',
      input_fields: ['phone_number'],
      output_fields: ['phone_number', 'phone_country', 'phone_type'],
      providers: ['internal'],
      priority: 'high'
    },
    geocode_address: {
      description: 'Geocode company address for location data',
      input_fields: ['address', 'city', 'state', 'country'],
      output_fields: ['latitude', 'longitude', 'formatted_address', 'timezone'],
      providers: ['google_places'],
      priority: 'normal'
    },
    company_size_lookup: {
      description: 'Determine accurate company size and employee count',
      input_fields: ['company_name', 'domain'],
      output_fields: ['employee_count', 'company_size_category', 'revenue_range'],
      providers: ['clearbit', 'apollo'],
      priority: 'normal'
    },
    industry_classification: {
      description: 'Classify company industry and sector',
      input_fields: ['company_name', 'domain', 'company_description'],
      output_fields: ['industry', 'sector', 'industry_code'],
      providers: ['clearbit'],
      priority: 'low'
    },
    social_media_lookup: {
      description: 'Find company social media profiles',
      input_fields: ['company_name', 'domain'],
      output_fields: ['linkedin_url', 'twitter_url', 'facebook_url'],
      providers: ['clearbit', 'apollo'],
      priority: 'low'
    }
  },

  // Person enrichment operations
  person: {
    infer_slot_type: {
      description: 'Infer person role/slot type based on title and company',
      input_fields: ['job_title', 'company_name'],
      output_fields: ['slot_type', 'role_category', 'department'],
      providers: ['internal'],
      priority: 'high'
    },
    determine_seniority: {
      description: 'Determine seniority level from job title',
      input_fields: ['job_title', 'company_size'],
      output_fields: ['seniority_level', 'management_level', 'years_experience_estimate'],
      providers: ['internal'],
      priority: 'high'
    },
    normalize_phone: {
      description: 'Normalize person phone number to E.164 format',
      input_fields: ['phone_number'],
      output_fields: ['phone_number', 'phone_country', 'phone_type'],
      providers: ['internal'],
      priority: 'high'
    },
    normalize_email: {
      description: 'Validate and normalize email address',
      input_fields: ['email'],
      output_fields: ['email', 'email_domain', 'email_status'],
      providers: ['internal'],
      priority: 'high'
    },
    linkedin_lookup: {
      description: 'Find LinkedIn profile for person',
      input_fields: ['first_name', 'last_name', 'company_name', 'job_title'],
      output_fields: ['linkedin_url', 'linkedin_verified'],
      providers: ['apollo', 'zoominfo'],
      priority: 'normal'
    },
    title_standardization: {
      description: 'Standardize job title to common format',
      input_fields: ['job_title'],
      output_fields: ['standardized_title', 'title_category'],
      providers: ['internal'],
      priority: 'normal'
    }
  }
};

export default {
  ENRICHMENT_JOBS_SCHEMA,
  ENRICHMENT_AUDIT_LOG_SCHEMA,
  ENRICHMENT_TYPE_DEFINITIONS
};