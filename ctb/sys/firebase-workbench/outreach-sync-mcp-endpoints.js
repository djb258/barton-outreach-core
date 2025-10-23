/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-DDAD4BC5
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

class OutreachSyncMCPService {
  constructor() {
    this.doctrineVersion = '1.0.0';
    this.mcpEndpoint = process.env.COMPOSIO_MCP_URL || 'https://backend.composio.dev/api/v1/mcp';
    this.outreachTools = [
      'INSTANTLY_ADD_CONTACT', 'INSTANTLY_GET_CAMPAIGNS', 'INSTANTLY_GET_CONTACT',
      'HEYREACH_ADD_CONTACT', 'HEYREACH_GET_CAMPAIGNS', 'HEYREACH_GET_CONTACT',
      'FIREBASE_READ', 'FIREBASE_WRITE', 'FIREBASE_UPDATE', 'FIREBASE_QUERY'
    ];
    this.supportedPlatforms = ['instantly', 'heyreach'];
  }

  generateSyncPayload(action, data, processId) {
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
      orbt_layer: 6,
      blueprint_version: '1.0'
    };
  }

  async syncToInstantly(contactData, campaignId, processId) {
    const payload = this.generateSyncPayload('INSTANTLY_ADD_CONTACT', {
      campaign_id: campaignId,
      contact: contactData
    }, processId);

    try {
      const response = await fetch(`${this.mcpEndpoint}/tool`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Instantly MCP sync failed: ${response.statusText}`);
      }

      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || 'Instantly sync failed');
      }

      return result.data;

    } catch (error) {
      console.error('Instantly MCP sync failed:', error);
      throw new Error(`Instantly sync error: ${error.message}`);
    }
  }

  async syncToHeyReach(contactData, campaignId, processId) {
    const payload = this.generateSyncPayload('HEYREACH_ADD_CONTACT', {
      campaignId: campaignId,
      contact: contactData
    }, processId);

    try {
      const response = await fetch(`${this.mcpEndpoint}/tool`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`HeyReach MCP sync failed: ${response.statusText}`);
      }

      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || 'HeyReach sync failed');
      }

      return result.data;

    } catch (error) {
      console.error('HeyReach MCP sync failed:', error);
      throw new Error(`HeyReach sync error: ${error.message}`);
    }
  }

  async getCampaigns(platform, processId) {
    const tool = platform === 'instantly' ? 'INSTANTLY_GET_CAMPAIGNS' : 'HEYREACH_GET_CAMPAIGNS';
    const payload = this.generateSyncPayload(tool, {}, processId);

    try {
      const response = await fetch(`${this.mcpEndpoint}/tool`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`${platform} campaigns MCP call failed: ${response.statusText}`);
      }

      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || `${platform} campaigns fetch failed`);
      }

      return result.data.campaigns || result.data || [];

    } catch (error) {
      console.error(`${platform} campaigns MCP call failed:`, error);
      throw new Error(`${platform} campaigns error: ${error.message}`);
    }
  }

  async storeBackReference(referenceData, processId) {
    const payload = this.generateSyncPayload('FIREBASE_WRITE', {
      collection: 'outreach_sync_tracking',
      data: referenceData
    }, processId);

    try {
      const response = await fetch(`${this.mcpEndpoint}/tool`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Back-reference storage failed: ${response.statusText}`);
      }

      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || 'Back-reference storage failed');
      }

      return result.data;

    } catch (error) {
      console.error('Back-reference storage failed:', error);
      throw new Error(`Back-reference error: ${error.message}`);
    }
  }
}

const OUTREACH_SYNC_MCP_ENDPOINTS = {
  // Instantly Sync Endpoints
  'syncToInstantly': {
    name: 'syncToInstantly',
    description: 'Sync promoted contacts to Instantly campaigns via Composio MCP',
    parameters: {
      type: 'object',
      properties: {
        filters: {
          type: 'object',
          description: 'Filters for selecting records from person_master',
          properties: {
            status: { type: 'string', default: 'promoted' },
            limit: { type: 'number', default: 100 }
          }
        },
        campaignId: {
          type: 'string',
          description: 'Instantly campaign ID to add contacts to'
        },
        processId: {
          type: 'string',
          description: 'Process identifier for tracking'
        }
      },
      required: []
    },
    returns: {
      type: 'object',
      properties: {
        success: { type: 'boolean' },
        processId: { type: 'string' },
        platform: { type: 'string', enum: ['instantly'] },
        stats: {
          type: 'object',
          properties: {
            total: { type: 'number' },
            synced: { type: 'number' },
            failed: { type: 'number' },
            skipped: { type: 'number' }
          }
        },
        syncedContacts: { type: 'array' },
        errors: { type: 'array' },
        duration: { type: 'number' },
        timestamp: { type: 'string' }
      }
    }
  },

  // HeyReach Sync Endpoints
  'syncToHeyReach': {
    name: 'syncToHeyReach',
    description: 'Sync promoted contacts to HeyReach campaigns via Composio MCP',
    parameters: {
      type: 'object',
      properties: {
        filters: {
          type: 'object',
          description: 'Filters for selecting records from person_master',
          properties: {
            status: { type: 'string', default: 'promoted' },
            limit: { type: 'number', default: 100 }
          }
        },
        campaignId: {
          type: 'string',
          description: 'HeyReach campaign ID to add contacts to'
        },
        processId: {
          type: 'string',
          description: 'Process identifier for tracking'
        }
      },
      required: []
    },
    returns: {
      type: 'object',
      properties: {
        success: { type: 'boolean' },
        processId: { type: 'string' },
        platform: { type: 'string', enum: ['heyreach'] },
        stats: {
          type: 'object',
          properties: {
            total: { type: 'number' },
            synced: { type: 'number' },
            failed: { type: 'number' },
            skipped: { type: 'number' }
          }
        },
        syncedContacts: { type: 'array' },
        errors: { type: 'array' },
        duration: { type: 'number' },
        timestamp: { type: 'string' }
      }
    }
  },

  // Campaign Management Endpoints
  'getCampaigns': {
    name: 'getCampaigns',
    description: 'Get campaigns from outreach platforms via Composio MCP',
    parameters: {
      type: 'object',
      properties: {
        platform: {
          type: 'string',
          description: 'Outreach platform',
          enum: ['instantly', 'heyreach']
        }
      },
      required: ['platform']
    },
    returns: {
      type: 'object',
      properties: {
        success: { type: 'boolean' },
        platform: { type: 'string' },
        campaigns: { type: 'array' },
        timestamp: { type: 'string' }
      }
    }
  },

  // Sync Status and Tracking Endpoints
  'getSyncStatus': {
    name: 'getSyncStatus',
    description: 'Get sync status and history for a contact',
    parameters: {
      type: 'object',
      properties: {
        contactId: {
          type: 'string',
          description: 'Contact unique ID to check sync status for'
        },
        platform: {
          type: 'string',
          description: 'Optional platform filter',
          enum: ['instantly', 'heyreach']
        }
      },
      required: ['contactId']
    },
    returns: {
      type: 'object',
      properties: {
        success: { type: 'boolean' },
        contactId: { type: 'string' },
        platform: { type: 'string' },
        syncHistory: { type: 'array' },
        timestamp: { type: 'string' }
      }
    }
  },

  // Batch Sync Operations
  'batchSyncContacts': {
    name: 'batchSyncContacts',
    description: 'Batch sync multiple contacts to outreach platforms',
    parameters: {
      type: 'object',
      properties: {
        platform: {
          type: 'string',
          description: 'Target outreach platform',
          enum: ['instantly', 'heyreach']
        },
        contactIds: {
          type: 'array',
          description: 'Array of contact unique IDs to sync',
          items: { type: 'string' }
        },
        campaignId: {
          type: 'string',
          description: 'Campaign ID to add contacts to'
        },
        processId: {
          type: 'string',
          description: 'Process identifier for tracking'
        }
      },
      required: ['platform', 'contactIds', 'campaignId']
    },
    returns: {
      type: 'object',
      properties: {
        success: { type: 'boolean' },
        processId: { type: 'string' },
        platform: { type: 'string' },
        results: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              contactId: { type: 'string' },
              success: { type: 'boolean' },
              campaignId: { type: 'string' },
              externalContactId: { type: 'string' },
              error: { type: 'string' }
            }
          }
        },
        timestamp: { type: 'string' }
      }
    }
  }
};

// Payload mapping schemas for outreach platforms
const OUTREACH_PAYLOAD_SCHEMAS = {
  instantly: {
    contact: {
      required: ['email', 'first_name', 'last_name'],
      optional: ['company_name', 'website', 'position', 'phone', 'linkedin_url', 'industry'],
      custom_fields: {
        contact_unique_id: 'string',
        company_unique_id: 'string',
        doctrine_version: 'string',
        sync_source: 'string'
      }
    },
    response: {
      id: 'string',
      contact_id: 'string',
      campaign_id: 'string',
      status: 'string'
    }
  },
  heyreach: {
    contact: {
      required: ['email', 'firstName', 'lastName'],
      optional: ['jobTitle', 'linkedinUrl', 'phone'],
      company: {
        name: 'string',
        website: 'string',
        industry: 'string',
        address: 'string',
        employeeCount: 'number'
      },
      customData: {
        contactUniqueId: 'string',
        companyUniqueId: 'string',
        doctrineVersion: 'string',
        syncSource: 'string'
      }
    },
    response: {
      id: 'string',
      contactId: 'string',
      campaignId: 'string',
      status: 'string'
    }
  }
};

// Back-reference tracking schema for Neon
const SYNC_TRACKING_SCHEMA = {
  table: 'outreach_sync_tracking',
  fields: {
    unique_id: { type: 'string', primary: true },
    contact_unique_id: { type: 'string', required: true },
    company_unique_id: { type: 'string', optional: true },
    platform: { type: 'string', required: true, enum: ['instantly', 'heyreach'] },
    campaign_id: { type: 'string', required: true },
    external_contact_id: { type: 'string', required: true },
    sync_status: { type: 'string', required: true, enum: ['success', 'failed', 'pending'] },
    last_synced_at: { type: 'string', required: true },
    platform_response: { type: 'string', optional: true },
    created_at: { type: 'string', required: true },
    doctrine_version: { type: 'string', required: true }
  },
  indexes: [
    { fields: ['contact_unique_id'], unique: false },
    { fields: ['platform', 'campaign_id'], unique: false },
    { fields: ['sync_status'], unique: false }
  ]
};

// Error handling patterns for outreach sync operations
const SYNC_ERROR_PATTERNS = {
  'platform_api_failed': {
    type: 'outreach_sync_failed',
    action: 'log_to_error_log',
    retry: true,
    max_retries: 3,
    escalate: true
  },
  'invalid_contact_data': {
    type: 'sync_validation_failed',
    action: 'log_to_error_log',
    retry: false,
    escalate: false
  },
  'campaign_not_found': {
    type: 'campaign_configuration_error',
    action: 'log_to_error_log',
    retry: false,
    escalate: true
  },
  'duplicate_contact': {
    type: 'sync_skipped',
    action: 'log_to_audit_log',
    retry: false,
    escalate: false
  },
  'rate_limit_exceeded': {
    type: 'rate_limit_error',
    action: 'delay_and_retry',
    retry: true,
    delay: 60000,
    escalate: false
  }
};

export {
  OutreachSyncMCPService,
  OUTREACH_SYNC_MCP_ENDPOINTS,
  OUTREACH_PAYLOAD_SCHEMAS,
  SYNC_TRACKING_SCHEMA,
  SYNC_ERROR_PATTERNS
};