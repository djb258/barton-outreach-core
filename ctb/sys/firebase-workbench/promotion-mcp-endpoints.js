/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-09422FF7
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

class PromotionMCPService {
  constructor() {
    this.doctrineVersion = '1.0.0';
    this.mcpEndpoint = process.env.COMPOSIO_MCP_URL || 'https://backend.composio.dev/api/v1/mcp';
    this.promotionTools = [
      'FIREBASE_READ', 'FIREBASE_WRITE', 'FIREBASE_UPDATE',
      'FIREBASE_QUERY', 'FIREBASE_DELETE', 'FIREBASE_FUNCTION_CALL'
    ];
    this.supportedEntities = ['company', 'person'];
    this.masterTables = ['company_master', 'person_master'];
  }

  generatePromotionPayload(action, data, processId) {
    return {
      tool: action,
      data: {
        ...data,
        processId: processId,
        doctrineVersion: this.doctrineVersion,
        timestamp: new Date().toISOString()
      },
      unique_id: `HEIR-${Date.now()}-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
      process_id: processId,
      orbt_layer: 4,
      blueprint_version: '1.0'
    };
  }

  async validateMasterTableSchema(entityType, record) {
    const requiredFields = {
      company: ['company_name', 'domain', 'industry', 'unique_id'],
      person: ['first_name', 'last_name', 'email', 'unique_id']
    };

    const required = requiredFields[entityType] || [];
    const missing = required.filter(field => !record[field]);

    if (missing.length > 0) {
      throw new Error(`Schema validation failed: Missing required fields: ${missing.join(', ')}`);
    }

    return true;
  }

  async checkDuplicate(entityType, searchField, searchValue, processId) {
    const masterTable = `${entityType}_master`;

    const payload = this.generatePromotionPayload('FIREBASE_QUERY', {
      collection: masterTable,
      where: { [searchField]: searchValue },
      limit: 1
    }, processId);

    try {
      const response = await fetch(`${this.mcpEndpoint}/tool`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      return result.success && result.data && result.data.length > 0 ? result.data[0] : null;

    } catch (error) {
      console.warn(`Duplicate check failed for ${entityType}:`, error.message);
      return null;
    }
  }

  async promoteToMasterTable(entityType, record, processId) {
    const masterTable = `${entityType}_master`;

    await this.validateMasterTableSchema(entityType, record);

    const payload = this.generatePromotionPayload('FIREBASE_WRITE', {
      collection: masterTable,
      data: record
    }, processId);

    const response = await fetch(`${this.mcpEndpoint}/tool`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Master table promotion failed: ${response.statusText}`);
    }

    const result = await response.json();
    if (!result.success) {
      throw new Error(result.error || 'Master table promotion failed');
    }

    return result.data;
  }

  async updateIntakeRecord(entityType, intakeId, promotionData, processId) {
    const intakeTable = `${entityType}_intake_staging`;

    const payload = this.generatePromotionPayload('FIREBASE_UPDATE', {
      collection: intakeTable,
      id: intakeId,
      data: promotionData
    }, processId);

    const response = await fetch(`${this.mcpEndpoint}/tool`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Intake record update failed: ${response.statusText}`);
    }

    const result = await response.json();
    if (!result.success) {
      throw new Error(result.error || 'Intake record update failed');
    }

    return result.data;
  }

  async logPromotion(logData, processId) {
    const payload = this.generatePromotionPayload('FIREBASE_WRITE', {
      collection: 'promotion_log',
      data: logData
    }, processId);

    try {
      const response = await fetch(`${this.mcpEndpoint}/tool`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('Promotion logging failed:', error);
      return false;
    }
  }

  async logAudit(auditData, processId) {
    const payload = this.generatePromotionPayload('FIREBASE_WRITE', {
      collection: 'unified_audit_log',
      data: auditData
    }, processId);

    try {
      const response = await fetch(`${this.mcpEndpoint}/tool`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('Audit logging failed:', error);
      return false;
    }
  }

  async logError(errorData, processId) {
    const payload = this.generatePromotionPayload('FIREBASE_WRITE', {
      collection: 'error_log',
      data: errorData
    }, processId);

    try {
      const response = await fetch(`${this.mcpEndpoint}/tool`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('Error logging failed:', error);
      return false;
    }
  }
}

const PROMOTION_MCP_ENDPOINTS = {
  // Company Promotion Endpoints
  'promoteCompany': {
    name: 'promoteCompany',
    description: 'Promote validated company records to company_master table',
    parameters: {
      type: 'object',
      properties: {
        companyRecords: {
          type: 'array',
          description: 'Array of validated company records to promote',
          items: {
            type: 'object',
            properties: {
              unique_id: { type: 'string', description: 'Intake unique identifier' },
              company_name: { type: 'string', description: 'Company name' },
              domain: { type: 'string', description: 'Company domain' },
              industry: { type: 'string', description: 'Industry classification' },
              address: { type: 'string', description: 'Company address' },
              employees: { type: 'number', description: 'Number of employees' },
              revenue: { type: 'string', description: 'Annual revenue' },
              validation_status: { type: 'string', description: 'Current validation status' }
            },
            required: ['unique_id', 'company_name', 'domain', 'industry']
          }
        },
        processId: {
          type: 'string',
          description: 'Process identifier for tracking'
        }
      },
      required: ['companyRecords']
    },
    returns: {
      type: 'object',
      properties: {
        success: { type: 'boolean' },
        processId: { type: 'string' },
        stats: {
          type: 'object',
          properties: {
            total: { type: 'number' },
            promoted: { type: 'number' },
            failed: { type: 'number' },
            duplicates: { type: 'number' }
          }
        },
        promotedCompanies: { type: 'array' },
        errors: { type: 'array' },
        duration: { type: 'number' },
        timestamp: { type: 'string' }
      }
    }
  },

  // Person Promotion Endpoints
  'promotePerson': {
    name: 'promotePerson',
    description: 'Promote validated person records to person_master table with relationship preservation',
    parameters: {
      type: 'object',
      properties: {
        personRecords: {
          type: 'array',
          description: 'Array of validated person records to promote',
          items: {
            type: 'object',
            properties: {
              unique_id: { type: 'string', description: 'Intake unique identifier' },
              first_name: { type: 'string', description: 'First name' },
              last_name: { type: 'string', description: 'Last name' },
              email: { type: 'string', description: 'Email address' },
              phone: { type: 'string', description: 'Phone number' },
              title: { type: 'string', description: 'Job title' },
              company_unique_id: { type: 'string', description: 'Associated company unique ID' },
              validation_status: { type: 'string', description: 'Current validation status' }
            },
            required: ['unique_id', 'first_name', 'last_name', 'email']
          }
        },
        processId: {
          type: 'string',
          description: 'Process identifier for tracking'
        }
      },
      required: ['personRecords']
    },
    returns: {
      type: 'object',
      properties: {
        success: { type: 'boolean' },
        processId: { type: 'string' },
        stats: {
          type: 'object',
          properties: {
            total: { type: 'number' },
            promoted: { type: 'number' },
            failed: { type: 'number' },
            duplicates: { type: 'number' },
            relationshipsPreserved: { type: 'number' }
          }
        },
        promotedPersons: { type: 'array' },
        errors: { type: 'array' },
        duration: { type: 'number' },
        timestamp: { type: 'string' }
      }
    }
  },

  // Promotion Status Tracking
  'getPromotionStatus': {
    name: 'getPromotionStatus',
    description: 'Get status and logs for a promotion process',
    parameters: {
      type: 'object',
      properties: {
        processId: {
          type: 'string',
          description: 'Process identifier to check status for'
        }
      },
      required: ['processId']
    },
    returns: {
      type: 'object',
      properties: {
        success: { type: 'boolean' },
        processId: { type: 'string' },
        stats: {
          type: 'object',
          properties: {
            total: { type: 'number' },
            promoted: { type: 'number' },
            failed: { type: 'number' }
          }
        },
        logs: { type: 'array' },
        timestamp: { type: 'string' }
      }
    }
  },

  // Master Table Query Endpoints
  'queryMasterTable': {
    name: 'queryMasterTable',
    description: 'Query master tables for promoted records',
    parameters: {
      type: 'object',
      properties: {
        table: {
          type: 'string',
          description: 'Master table to query (company_master or person_master)',
          enum: ['company_master', 'person_master']
        },
        filters: {
          type: 'object',
          description: 'Query filters'
        },
        limit: {
          type: 'number',
          description: 'Maximum number of records to return'
        },
        offset: {
          type: 'number',
          description: 'Number of records to skip'
        }
      },
      required: ['table']
    },
    returns: {
      type: 'object',
      properties: {
        success: { type: 'boolean' },
        data: { type: 'array' },
        total: { type: 'number' },
        timestamp: { type: 'string' }
      }
    }
  },

  // Relationship Query Endpoints
  'getRelationships': {
    name: 'getRelationships',
    description: 'Get company-person relationships from master tables',
    parameters: {
      type: 'object',
      properties: {
        companyId: {
          type: 'string',
          description: 'Company unique ID to find associated persons'
        },
        personId: {
          type: 'string',
          description: 'Person unique ID to find associated company'
        }
      }
    },
    returns: {
      type: 'object',
      properties: {
        success: { type: 'boolean' },
        relationships: {
          type: 'object',
          properties: {
            company: { type: 'object' },
            persons: { type: 'array' }
          }
        },
        timestamp: { type: 'string' }
      }
    }
  }
};

// Validation schema for master table records
const MASTER_TABLE_SCHEMAS = {
  company_master: {
    required: ['unique_id', 'company_name', 'domain', 'industry', 'doctrine_version', 'promoted_at'],
    optional: ['address', 'employees', 'revenue', 'description', 'website', 'phone', 'founded'],
    types: {
      unique_id: 'string',
      company_name: 'string',
      domain: 'string',
      industry: 'string',
      address: 'string',
      employees: 'number',
      revenue: 'string',
      doctrine_version: 'string',
      promoted_at: 'string',
      created_at: 'string',
      updated_at: 'string'
    }
  },
  person_master: {
    required: ['unique_id', 'first_name', 'last_name', 'email', 'doctrine_version', 'promoted_at'],
    optional: ['phone', 'title', 'company_unique_id', 'linkedin_url', 'department'],
    types: {
      unique_id: 'string',
      first_name: 'string',
      last_name: 'string',
      email: 'string',
      phone: 'string',
      title: 'string',
      company_unique_id: 'string',
      doctrine_version: 'string',
      promoted_at: 'string',
      created_at: 'string',
      updated_at: 'string'
    }
  }
};

// Error handling patterns for promotion operations
const PROMOTION_ERROR_PATTERNS = {
  'schema_mismatch': {
    type: 'promotion_failed',
    action: 'log_to_error_log',
    retry: false,
    escalate: true
  },
  'duplicate_detected': {
    type: 'promotion_skipped',
    action: 'log_to_audit_log',
    retry: false,
    escalate: false
  },
  'master_table_write_failed': {
    type: 'promotion_failed',
    action: 'rollback_transaction',
    retry: true,
    escalate: true
  },
  'relationship_validation_failed': {
    type: 'promotion_partial',
    action: 'log_to_error_log',
    retry: false,
    escalate: false
  }
};

export {
  PromotionMCPService,
  PROMOTION_MCP_ENDPOINTS,
  MASTER_TABLE_SCHEMAS,
  PROMOTION_ERROR_PATTERNS
};