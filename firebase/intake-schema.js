/**
 * Doctrine Spec:
 * - Barton ID: 15.01.02.07.10000.002
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Step 2 Intake collections schema definitions for Barton Doctrine compliance
 * - Input: Company and people intake data requirements
 * - Output: Firestore schema definitions for intake and audit collections
 * - MCP: Firebase (Composio-only access)
 */

// Collection: company_raw_intake
export const COMPANY_RAW_INTAKE_SCHEMA = {
  collectionName: 'company_raw_intake',
  description: 'Raw company intake data with Barton ID compliance',
  accessPattern: 'mcp_only',
  doctrineCompliance: {
    mcp_enforcement: true,
    audit_all_operations: true,
    strict_validation: true
  },
  schema: {
    // Barton ID (required)
    company_unique_id: {
      type: 'string',
      required: true,
      pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      description: 'Barton ID for company entity',
      example: '05.01.01.03.10000.002',
      validation: 'Must follow Barton Doctrine ID format'
    },

    // Required company fields
    company_name: {
      type: 'string',
      required: true,
      minLength: 1,
      maxLength: 500,
      description: 'Company legal or common name',
      example: 'Acme Corporation',
      validation: 'Cannot be null or empty'
    },

    website_url: {
      type: 'string',
      required: true,
      pattern: '^https?:\\/\\/.+',
      description: 'Company primary website URL',
      example: 'https://acmecorp.com',
      validation: 'Must be valid HTTP/HTTPS URL'
    },

    industry: {
      type: 'string',
      required: true,
      minLength: 1,
      maxLength: 200,
      description: 'Company industry classification',
      example: 'Software Development',
      validation: 'Cannot be null or empty'
    },

    company_size: {
      type: 'string',
      required: true,
      enum: ['1-10', '11-50', '51-200', '201-500', '501-1000', '1001-5000', '5001+'],
      description: 'Employee count range',
      example: '51-200',
      validation: 'Must be one of predefined ranges'
    },

    headquarters_location: {
      type: 'string',
      required: true,
      minLength: 1,
      maxLength: 200,
      description: 'Company headquarters location',
      example: 'San Francisco, CA, USA',
      validation: 'Cannot be null or empty'
    },

    // Optional social media fields (nullable)
    linkedin_url: {
      type: 'string',
      required: false,
      nullable: true,
      pattern: '^https:\\/\\/(www\\.)?linkedin\\.com\\/company\\/.+',
      description: 'Company LinkedIn page URL',
      example: 'https://linkedin.com/company/acme-corp',
      validation: 'Must be valid LinkedIn company URL if provided'
    },

    twitter_url: {
      type: 'string',
      required: false,
      nullable: true,
      pattern: '^https:\\/\\/(www\\.)?(twitter\\.com|x\\.com)\\/.+',
      description: 'Company X (Twitter) profile URL',
      example: 'https://x.com/acmecorp',
      validation: 'Must be valid X/Twitter URL if provided'
    },

    facebook_url: {
      type: 'string',
      required: false,
      nullable: true,
      pattern: '^https:\\/\\/(www\\.)?facebook\\.com\\/.+',
      description: 'Company Facebook page URL',
      example: 'https://facebook.com/acmecorp',
      validation: 'Must be valid Facebook URL if provided'
    },

    instagram_url: {
      type: 'string',
      required: false,
      nullable: true,
      pattern: '^https:\\/\\/(www\\.)?instagram\\.com\\/.+',
      description: 'Company Instagram profile URL',
      example: 'https://instagram.com/acmecorp',
      validation: 'Must be valid Instagram URL if provided'
    },

    // Status and metadata fields
    status: {
      type: 'string',
      required: true,
      enum: ['pending', 'validated', 'failed'],
      default: 'pending',
      description: 'Processing status of intake record',
      validation: 'Must be one of: pending, validated, failed'
    },

    created_at: {
      type: 'timestamp',
      required: true,
      description: 'Record creation timestamp',
      example: '2025-09-28T20:00:00.000Z',
      validation: 'Auto-generated server timestamp'
    },

    updated_at: {
      type: 'timestamp',
      required: true,
      description: 'Record last update timestamp',
      example: '2025-09-28T20:00:00.000Z',
      validation: 'Auto-updated on changes'
    },

    // Source tracking
    intake_source: {
      type: 'string',
      required: true,
      description: 'Source of the intake data',
      example: 'composio_mcp_ingestion',
      validation: 'Must indicate data source'
    },

    source_metadata: {
      type: 'object',
      required: false,
      description: 'Additional metadata about data source',
      properties: {
        user_agent: { type: 'string' },
        ip_address: { type: 'string' },
        request_id: { type: 'string' }
      }
    }
  },

  // Firestore indexes
  indexes: [
    { fields: ['company_unique_id'], unique: true },
    { fields: ['status', 'created_at'] },
    { fields: ['company_name', 'status'] },
    { fields: ['website_url'], unique: true },
    { fields: ['created_at', 'status'] },
    { fields: ['intake_source', 'created_at'] }
  ],

  // Security rules (MCP-only)
  securityRules: {
    read: 'mcp_only',
    write: 'mcp_only',
    create: 'mcp_only',
    update: 'mcp_only',
    delete: 'mcp_only'
  }
};

// Collection: people_raw_intake
export const PEOPLE_RAW_INTAKE_SCHEMA = {
  collectionName: 'people_raw_intake',
  description: 'Raw people intake data with Barton ID compliance',
  accessPattern: 'mcp_only',
  doctrineCompliance: {
    mcp_enforcement: true,
    audit_all_operations: true,
    strict_validation: true
  },
  schema: {
    // Barton ID (required)
    person_unique_id: {
      type: 'string',
      required: true,
      pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      description: 'Barton ID for person entity',
      example: '05.01.01.03.10000.003',
      validation: 'Must follow Barton Doctrine ID format'
    },

    // Required person fields
    full_name: {
      type: 'string',
      required: true,
      minLength: 1,
      maxLength: 300,
      description: 'Person full name',
      example: 'John Smith',
      validation: 'Cannot be null or empty'
    },

    email_address: {
      type: 'string',
      required: true,
      pattern: '^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$',
      description: 'Person primary email address',
      example: 'john.smith@acmecorp.com',
      validation: 'Must be valid email format'
    },

    job_title: {
      type: 'string',
      required: true,
      minLength: 1,
      maxLength: 200,
      description: 'Person job title or role',
      example: 'Senior Software Engineer',
      validation: 'Cannot be null or empty'
    },

    company_name: {
      type: 'string',
      required: true,
      minLength: 1,
      maxLength: 500,
      description: 'Company where person works',
      example: 'Acme Corporation',
      validation: 'Cannot be null or empty'
    },

    location: {
      type: 'string',
      required: true,
      minLength: 1,
      maxLength: 200,
      description: 'Person work location',
      example: 'San Francisco, CA, USA',
      validation: 'Cannot be null or empty'
    },

    // Optional social media fields (nullable)
    linkedin_url: {
      type: 'string',
      required: false,
      nullable: true,
      pattern: '^https:\\/\\/(www\\.)?linkedin\\.com\\/in\\/.+',
      description: 'Person LinkedIn profile URL',
      example: 'https://linkedin.com/in/johnsmith',
      validation: 'Must be valid LinkedIn profile URL if provided'
    },

    twitter_url: {
      type: 'string',
      required: false,
      nullable: true,
      pattern: '^https:\\/\\/(www\\.)?(twitter\\.com|x\\.com)\\/.+',
      description: 'Person X (Twitter) profile URL',
      example: 'https://x.com/johnsmith',
      validation: 'Must be valid X/Twitter URL if provided'
    },

    facebook_url: {
      type: 'string',
      required: false,
      nullable: true,
      pattern: '^https:\\/\\/(www\\.)?facebook\\.com\\/.+',
      description: 'Person Facebook profile URL',
      example: 'https://facebook.com/johnsmith',
      validation: 'Must be valid Facebook URL if provided'
    },

    instagram_url: {
      type: 'string',
      required: false,
      nullable: true,
      pattern: '^https:\\/\\/(www\\.)?instagram\\.com\\/.+',
      description: 'Person Instagram profile URL',
      example: 'https://instagram.com/johnsmith',
      validation: 'Must be valid Instagram URL if provided'
    },

    // Status and metadata fields
    status: {
      type: 'string',
      required: true,
      enum: ['pending', 'validated', 'failed'],
      default: 'pending',
      description: 'Processing status of intake record',
      validation: 'Must be one of: pending, validated, failed'
    },

    created_at: {
      type: 'timestamp',
      required: true,
      description: 'Record creation timestamp',
      example: '2025-09-28T20:00:00.000Z',
      validation: 'Auto-generated server timestamp'
    },

    updated_at: {
      type: 'timestamp',
      required: true,
      description: 'Record last update timestamp',
      example: '2025-09-28T20:00:00.000Z',
      validation: 'Auto-updated on changes'
    },

    // Source tracking
    intake_source: {
      type: 'string',
      required: true,
      description: 'Source of the intake data',
      example: 'composio_mcp_ingestion',
      validation: 'Must indicate data source'
    },

    source_metadata: {
      type: 'object',
      required: false,
      description: 'Additional metadata about data source',
      properties: {
        user_agent: { type: 'string' },
        ip_address: { type: 'string' },
        request_id: { type: 'string' }
      }
    },

    // Optional association with company
    associated_company_id: {
      type: 'string',
      required: false,
      nullable: true,
      pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      description: 'Barton ID of associated company if known',
      example: '05.01.01.03.10000.002',
      validation: 'Must be valid Barton ID if provided'
    }
  },

  // Firestore indexes
  indexes: [
    { fields: ['person_unique_id'], unique: true },
    { fields: ['status', 'created_at'] },
    { fields: ['email_address'], unique: true },
    { fields: ['full_name', 'status'] },
    { fields: ['company_name', 'status'] },
    { fields: ['created_at', 'status'] },
    { fields: ['intake_source', 'created_at'] },
    { fields: ['associated_company_id', 'created_at'] }
  ],

  // Security rules (MCP-only)
  securityRules: {
    read: 'mcp_only',
    write: 'mcp_only',
    create: 'mcp_only',
    update: 'mcp_only',
    delete: 'mcp_only'
  }
};

// Collection: company_audit_log
export const COMPANY_AUDIT_LOG_SCHEMA = {
  collectionName: 'company_audit_log',
  description: 'Audit log for company intake operations',
  accessPattern: 'mcp_only',
  doctrineCompliance: {
    mcp_enforcement: true,
    audit_all_operations: true,
    strict_validation: true
  },
  schema: {
    unique_id: {
      type: 'string',
      required: true,
      pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      description: 'Barton ID for audit log entry',
      example: '05.01.02.03.10000.004',
      validation: 'Must follow Barton Doctrine ID format'
    },

    action: {
      type: 'string',
      required: true,
      enum: ['intake_create', 'intake_update', 'intake_validate', 'intake_fail', 'intake_delete'],
      description: 'Action performed on company intake',
      validation: 'Must be valid intake action type'
    },

    status: {
      type: 'string',
      required: true,
      enum: ['success', 'failure', 'warning'],
      description: 'Result status of the operation',
      validation: 'Must indicate operation outcome'
    },

    source: {
      type: 'object',
      required: true,
      properties: {
        service: {
          type: 'string',
          required: true,
          description: 'Service that performed the action',
          example: 'intakeCompany_function'
        },
        function: {
          type: 'string',
          required: true,
          description: 'Function that performed the action',
          example: 'intakeCompany'
        },
        user_agent: {
          type: 'string',
          required: false,
          description: 'User agent of the request'
        },
        ip_address: {
          type: 'string',
          required: false,
          description: 'IP address of the request source'
        },
        request_id: {
          type: 'string',
          required: true,
          description: 'Unique request identifier'
        }
      }
    },

    target_company_id: {
      type: 'string',
      required: true,
      pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      description: 'Barton ID of the company being processed',
      validation: 'Must be valid company Barton ID'
    },

    error_log: {
      type: 'object',
      required: false,
      nullable: true,
      properties: {
        error_code: { type: 'string' },
        error_message: { type: 'string' },
        stack_trace: { type: 'string' },
        retry_count: { type: 'number' },
        recovery_action: { type: 'string' }
      },
      description: 'Error details if operation failed'
    },

    payload: {
      type: 'object',
      required: true,
      properties: {
        before: {
          type: 'object',
          nullable: true,
          description: 'State before operation'
        },
        after: {
          type: 'object',
          nullable: true,
          description: 'State after operation'
        },
        metadata: {
          type: 'object',
          description: 'Additional operation metadata'
        }
      }
    },

    created_at: {
      type: 'timestamp',
      required: true,
      description: 'Audit log entry creation timestamp',
      validation: 'Auto-generated server timestamp'
    }
  },

  // Firestore indexes
  indexes: [
    { fields: ['unique_id'], unique: true },
    { fields: ['target_company_id', 'created_at'] },
    { fields: ['action', 'created_at'] },
    { fields: ['status', 'created_at'] },
    { fields: ['created_at'] }
  ],

  // Security rules (MCP-only)
  securityRules: {
    read: 'mcp_only',
    write: 'mcp_only',
    create: 'mcp_only',
    update: 'deny_all',
    delete: 'deny_all'
  }
};

// Collection: people_audit_log
export const PEOPLE_AUDIT_LOG_SCHEMA = {
  collectionName: 'people_audit_log',
  description: 'Audit log for people intake operations',
  accessPattern: 'mcp_only',
  doctrineCompliance: {
    mcp_enforcement: true,
    audit_all_operations: true,
    strict_validation: true
  },
  schema: {
    unique_id: {
      type: 'string',
      required: true,
      pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      description: 'Barton ID for audit log entry',
      example: '05.01.02.03.10000.005',
      validation: 'Must follow Barton Doctrine ID format'
    },

    action: {
      type: 'string',
      required: true,
      enum: ['intake_create', 'intake_update', 'intake_validate', 'intake_fail', 'intake_delete'],
      description: 'Action performed on person intake',
      validation: 'Must be valid intake action type'
    },

    status: {
      type: 'string',
      required: true,
      enum: ['success', 'failure', 'warning'],
      description: 'Result status of the operation',
      validation: 'Must indicate operation outcome'
    },

    source: {
      type: 'object',
      required: true,
      properties: {
        service: {
          type: 'string',
          required: true,
          description: 'Service that performed the action',
          example: 'intakePerson_function'
        },
        function: {
          type: 'string',
          required: true,
          description: 'Function that performed the action',
          example: 'intakePerson'
        },
        user_agent: {
          type: 'string',
          required: false,
          description: 'User agent of the request'
        },
        ip_address: {
          type: 'string',
          required: false,
          description: 'IP address of the request source'
        },
        request_id: {
          type: 'string',
          required: true,
          description: 'Unique request identifier'
        }
      }
    },

    target_person_id: {
      type: 'string',
      required: true,
      pattern: '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$',
      description: 'Barton ID of the person being processed',
      validation: 'Must be valid person Barton ID'
    },

    error_log: {
      type: 'object',
      required: false,
      nullable: true,
      properties: {
        error_code: { type: 'string' },
        error_message: { type: 'string' },
        stack_trace: { type: 'string' },
        retry_count: { type: 'number' },
        recovery_action: { type: 'string' }
      },
      description: 'Error details if operation failed'
    },

    payload: {
      type: 'object',
      required: true,
      properties: {
        before: {
          type: 'object',
          nullable: true,
          description: 'State before operation'
        },
        after: {
          type: 'object',
          nullable: true,
          description: 'State after operation'
        },
        metadata: {
          type: 'object',
          description: 'Additional operation metadata'
        }
      }
    },

    created_at: {
      type: 'timestamp',
      required: true,
      description: 'Audit log entry creation timestamp',
      validation: 'Auto-generated server timestamp'
    }
  },

  // Firestore indexes
  indexes: [
    { fields: ['unique_id'], unique: true },
    { fields: ['target_person_id', 'created_at'] },
    { fields: ['action', 'created_at'] },
    { fields: ['status', 'created_at'] },
    { fields: ['created_at'] }
  ],

  // Security rules (MCP-only)
  securityRules: {
    read: 'mcp_only',
    write: 'mcp_only',
    create: 'mcp_only',
    update: 'deny_all',
    delete: 'deny_all'
  }
};

// Combined Step 2 schema exports
export const STEP_2_SCHEMAS = {
  company_raw_intake: COMPANY_RAW_INTAKE_SCHEMA,
  people_raw_intake: PEOPLE_RAW_INTAKE_SCHEMA,
  company_audit_log: COMPANY_AUDIT_LOG_SCHEMA,
  people_audit_log: PEOPLE_AUDIT_LOG_SCHEMA
};

// Default intake status values
export const INTAKE_STATUS = {
  PENDING: 'pending',
  VALIDATED: 'validated',
  FAILED: 'failed'
};

// Intake action types for audit logs
export const INTAKE_ACTIONS = {
  CREATE: 'intake_create',
  UPDATE: 'intake_update',
  VALIDATE: 'intake_validate',
  FAIL: 'intake_fail',
  DELETE: 'intake_delete'
};

// Schema validation function
export const validateIntakeDocument = (collectionName, document) => {
  const schema = STEP_2_SCHEMAS[collectionName];
  if (!schema) {
    throw new Error(`Schema not found for collection: ${collectionName}`);
  }

  const errors = [];
  const warnings = [];

  // Validate required fields
  Object.entries(schema.schema).forEach(([fieldName, fieldConfig]) => {
    if (fieldConfig.required && (document[fieldName] === undefined || document[fieldName] === null)) {
      if (!fieldConfig.nullable) {
        errors.push(`Required field missing: ${fieldName}`);
      }
    }

    // Validate patterns
    if (document[fieldName] && fieldConfig.pattern) {
      const pattern = new RegExp(fieldConfig.pattern);
      if (!pattern.test(document[fieldName])) {
        errors.push(`Invalid format for ${fieldName}: ${document[fieldName]}`);
      }
    }

    // Validate enums
    if (document[fieldName] && fieldConfig.enum) {
      if (!fieldConfig.enum.includes(document[fieldName])) {
        errors.push(`Invalid value for ${fieldName}: ${document[fieldName]}. Must be one of: ${fieldConfig.enum.join(', ')}`);
      }
    }

    // Validate string lengths
    if (document[fieldName] && fieldConfig.type === 'string') {
      if (fieldConfig.minLength && document[fieldName].length < fieldConfig.minLength) {
        errors.push(`${fieldName} too short. Minimum length: ${fieldConfig.minLength}`);
      }
      if (fieldConfig.maxLength && document[fieldName].length > fieldConfig.maxLength) {
        errors.push(`${fieldName} too long. Maximum length: ${fieldConfig.maxLength}`);
      }
    }
  });

  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
};

export default STEP_2_SCHEMAS;