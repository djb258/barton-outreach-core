/**
 * Doctrine Spec:
 * - Barton ID: 99.99.99.07.92414.038
 * - Altitude: 10000 (Execution Layer)
 * - Input: data query parameters and filters
 * - Output: database records and metadata
 * - MCP: Composio (Neon integrated)
 */
/**
 * Validation Configuration for STAMPED Doctrine
 * Defines validation rules, MCP endpoints, and doctrine compliance
 */

export const VALIDATION_CONFIG = {
  // Environment configuration
  env: {
    composio_api_key: process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn',
    composio_base_url: process.env.COMPOSIO_BASE_URL || 'https://backend.composio.dev',
    neon_connection_id: process.env.NEON_CONNECTION_ID || 'neon_barton_outreach',
    doctrine_hash: process.env.DOCTRINE_HASH || 'STAMPED_v2.1.0',
    millionverify_api_key: process.env.MILLIONVERIFY_API_KEY,
    apify_api_token: process.env.APIFY_API_TOKEN
  },

  // STAMPED Doctrine Schema
  stamped_schema: {
    version: '2.1.0',
    doctrine: 'STAMPED',
    altitude: 10000,
    required_fields: [
      'company_name',
      'industry',
      'contact_email',
      'contact_phone',
      'address',
      'website_url',
      'employee_count'
    ],
    optional_fields: [
      'revenue',
      'description',
      'founded_year',
      'linkedin_url',
      'social_media'
    ],
    field_validation: {
      company_name: {
        type: 'string',
        min_length: 2,
        max_length: 200,
        pattern: /^[a-zA-Z0-9\s\.\-\&,]+$/
      },
      industry: {
        type: 'enum',
        values: [
          'Technology', 'Healthcare', 'Finance', 'Manufacturing',
          'Retail', 'Education', 'Real Estate', 'Transportation',
          'Energy', 'Media', 'Consulting', 'Agriculture',
          'Construction', 'Entertainment', 'Government', 'Other'
        ]
      },
      contact_email: {
        type: 'email',
        pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        blacklist_domains: ['test.com', 'example.com', 'fake.com']
      },
      contact_phone: {
        type: 'phone',
        pattern: /^[\+]?[1-9][\d]{0,15}$/,
        format: 'international'
      },
      website_url: {
        type: 'url',
        require_https: false,
        check_reachable: true
      },
      employee_count: {
        type: 'integer',
        min: 1,
        max: 1000000
      },
      revenue: {
        type: 'number',
        min: 0,
        max: 1000000000000
      }
    }
  },

  // MCP Tool Mappings
  mcp_tools: {
    neon: {
      query_rows: 'NEON_QUERY_ROWS',
      execute_sql: 'NEON_EXECUTE_SQL',
      insert_rows: 'NEON_INSERT_ROWS',
      update_rows: 'NEON_UPDATE_ROWS'
    },
    enrichment: {
      millionverify: 'MILLIONVERIFY_VALIDATE_EMAIL',
      apify_company: 'APIFY_EXTRACT_COMPANY_DATA',
      clearbit: 'CLEARBIT_ENRICH_COMPANY'
    },
    validation: {
      phone_validator: 'TWILIO_PHONE_LOOKUP',
      website_checker: 'PINGDOM_WEBSITE_CHECK'
    }
  },

  // Validation Rules by Priority
  validation_pipeline: [
    {
      name: 'schema_validation',
      priority: 1,
      required: true,
      description: 'Validate against STAMPED schema requirements'
    },
    {
      name: 'dedupe_check',
      priority: 2,
      required: true,
      description: 'Check for duplicates in master company table'
    },
    {
      name: 'email_validation',
      priority: 3,
      required: false,
      mcp_tool: 'millionverify',
      timeout: 5000,
      description: 'Validate email deliverability'
    },
    {
      name: 'phone_validation',
      priority: 4,
      required: false,
      mcp_tool: 'phone_validator',
      timeout: 3000,
      description: 'Validate phone number format and carrier'
    },
    {
      name: 'website_check',
      priority: 5,
      required: false,
      mcp_tool: 'website_checker',
      timeout: 10000,
      description: 'Check website accessibility and SSL'
    },
    {
      name: 'data_enrichment',
      priority: 6,
      required: false,
      mcp_tool: 'apify_company',
      timeout: 15000,
      description: 'Enrich missing company data'
    }
  ],

  // Error Categories and Codes
  error_categories: {
    schema_errors: [
      'missing_required_field',
      'invalid_field_format',
      'field_length_violation',
      'invalid_enum_value'
    ],
    business_rule_errors: [
      'duplicate_company',
      'invalid_employee_range',
      'invalid_revenue_range',
      'blacklisted_domain'
    ],
    validation_errors: [
      'email_undeliverable',
      'phone_invalid',
      'website_unreachable',
      'social_media_invalid'
    ],
    system_errors: [
      'mcp_timeout',
      'mcp_unavailable',
      'database_error',
      'validation_system_error'
    ]
  },

  // Performance Thresholds
  performance: {
    max_processing_time_ms: 30000,
    max_rows_per_batch: 1000,
    mcp_timeout_default: 10000,
    retry_attempts: 3,
    grade_thresholds: {
      'A+': 100,
      'A': 500,
      'B': 1000,
      'C': 3000,
      'D': 5000,
      'F': 30000
    }
  },

  // Doctrine Compliance Settings
  doctrine_compliance: {
    require_unique_id: true,
    require_process_id: true,
    require_altitude: true,
    require_timestamp: true,
    stamped_fields: {
      source: 'validation_middleware',
      timestamp: 'auto_generated',
      actor: 'composio_mcp_orchestrator',
      method: 'stamped_validation_pipeline',
      process: 'auto_generated',
      environment: process.env.NODE_ENV || 'production',
      data: 'validation_metadata'
    }
  }
};

export default VALIDATION_CONFIG;