/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-33968D8F
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

import { onCall, HttpsError } from 'firebase-functions/v2/https';
import { logger } from 'firebase-functions';
import { validateMCPAccess, generateBartonId } from '../utils/doctrineHelpers.js';

class OutreachPayloadMapper {
  constructor() {
    this.doctrineVersion = '1.0.0';
    this.supportedPlatforms = ['instantly', 'heyreach'];
  }

  mapToInstantlyPayload(person, company = null) {
    const basePayload = {
      email: person.email,
      first_name: person.first_name,
      last_name: person.last_name,
      company_name: company?.company_name || '',
      website: company?.domain || '',
      industry: company?.industry || '',
      custom_fields: {
        contact_unique_id: person.unique_id,
        company_unique_id: company?.unique_id || '',
        doctrine_version: this.doctrineVersion,
        sync_source: 'barton_doctrine_step6'
      }
    };

    if (person.title) basePayload.position = person.title;
    if (person.phone) basePayload.phone = person.phone;
    if (person.linkedin_url) basePayload.linkedin_url = person.linkedin_url;
    if (company?.address) basePayload.company_address = company.address;
    if (company?.employees) basePayload.company_size = company.employees;

    return basePayload;
  }

  mapToHeyReachPayload(person, company = null) {
    const basePayload = {
      contact: {
        email: person.email,
        firstName: person.first_name,
        lastName: person.last_name,
        jobTitle: person.title || '',
        linkedinUrl: person.linkedin_url || '',
        phone: person.phone || ''
      },
      company: {
        name: company?.company_name || '',
        website: company?.domain || '',
        industry: company?.industry || '',
        address: company?.address || '',
        employeeCount: company?.employees || null
      },
      customData: {
        contactUniqueId: person.unique_id,
        companyUniqueId: company?.unique_id || '',
        doctrineVersion: this.doctrineVersion,
        syncSource: 'barton_doctrine_step6'
      }
    };

    return basePayload;
  }

  mapSyncResponse(platform, response, person, company = null) {
    const baseMapping = {
      platform: platform,
      contact_unique_id: person.unique_id,
      company_unique_id: company?.unique_id || '',
      sync_status: 'success',
      last_synced_at: new Date().toISOString(),
      doctrine_version: this.doctrineVersion
    };

    if (platform === 'instantly') {
      return {
        ...baseMapping,
        campaign_id: response.campaign_id || response.id,
        external_contact_id: response.contact_id || response.id,
        platform_response: JSON.stringify(response)
      };
    }

    if (platform === 'heyreach') {
      return {
        ...baseMapping,
        campaign_id: response.campaignId || response.id,
        external_contact_id: response.contactId || response.id,
        platform_response: JSON.stringify(response)
      };
    }

    return baseMapping;
  }
}

class InstantlyMCPClient {
  constructor(mcpTools) {
    this.mcpTools = mcpTools;
    this.defaultCampaignId = process.env.INSTANTLY_DEFAULT_CAMPAIGN_ID;
  }

  async addContactToCampaign(payload, campaignId = null, processId) {
    const targetCampaignId = campaignId || this.defaultCampaignId;

    if (!targetCampaignId) {
      throw new Error('Instantly campaign ID not specified');
    }

    const mcpPayload = {
      tool: 'INSTANTLY_ADD_CONTACT',
      data: {
        campaign_id: targetCampaignId,
        contact: payload,
        processId: processId
      },
      unique_id: generateBartonId(),
      process_id: processId,
      orbt_layer: 6,
      blueprint_version: '1.0'
    };

    try {
      const response = await fetch(`${this.mcpTools.baseUrl}/tool`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mcpPayload)
      });

      if (!response.ok) {
        throw new Error(`Instantly MCP call failed: ${response.statusText}`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(`Instantly MCP error: ${result.error || 'Unknown error'}`);
      }

      return {
        success: true,
        campaign_id: targetCampaignId,
        contact_id: result.data.id || result.data.contact_id,
        platform_response: result.data
      };

    } catch (error) {
      logger.error('Instantly MCP call failed:', error);
      throw new Error(`Instantly sync failed: ${error.message}`);
    }
  }

  async getCampaigns(processId) {
    const mcpPayload = {
      tool: 'INSTANTLY_GET_CAMPAIGNS',
      data: { processId: processId },
      unique_id: generateBartonId(),
      process_id: processId,
      orbt_layer: 6,
      blueprint_version: '1.0'
    };

    try {
      const response = await fetch(`${this.mcpTools.baseUrl}/tool`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mcpPayload)
      });

      if (!response.ok) {
        throw new Error(`Instantly campaigns MCP call failed: ${response.statusText}`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(`Instantly campaigns MCP error: ${result.error || 'Unknown error'}`);
      }

      return result.data.campaigns || [];

    } catch (error) {
      logger.error('Instantly campaigns MCP call failed:', error);
      throw new Error(`Failed to fetch Instantly campaigns: ${error.message}`);
    }
  }
}

class HeyReachMCPClient {
  constructor(mcpTools) {
    this.mcpTools = mcpTools;
    this.defaultCampaignId = process.env.HEYREACH_DEFAULT_CAMPAIGN_ID;
  }

  async addContactToCampaign(payload, campaignId = null, processId) {
    const targetCampaignId = campaignId || this.defaultCampaignId;

    if (!targetCampaignId) {
      throw new Error('HeyReach campaign ID not specified');
    }

    const mcpPayload = {
      tool: 'HEYREACH_ADD_CONTACT',
      data: {
        campaignId: targetCampaignId,
        contact: payload,
        processId: processId
      },
      unique_id: generateBartonId(),
      process_id: processId,
      orbt_layer: 6,
      blueprint_version: '1.0'
    };

    try {
      const response = await fetch(`${this.mcpTools.baseUrl}/tool`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mcpPayload)
      });

      if (!response.ok) {
        throw new Error(`HeyReach MCP call failed: ${response.statusText}`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(`HeyReach MCP error: ${result.error || 'Unknown error'}`);
      }

      return {
        success: true,
        campaign_id: targetCampaignId,
        contact_id: result.data.id || result.data.contactId,
        platform_response: result.data
      };

    } catch (error) {
      logger.error('HeyReach MCP call failed:', error);
      throw new Error(`HeyReach sync failed: ${error.message}`);
    }
  }

  async getCampaigns(processId) {
    const mcpPayload = {
      tool: 'HEYREACH_GET_CAMPAIGNS',
      data: { processId: processId },
      unique_id: generateBartonId(),
      process_id: processId,
      orbt_layer: 6,
      blueprint_version: '1.0'
    };

    try {
      const response = await fetch(`${this.mcpTools.baseUrl}/tool`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mcpPayload)
      });

      if (!response.ok) {
        throw new Error(`HeyReach campaigns MCP call failed: ${response.statusText}`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(`HeyReach campaigns MCP error: ${result.error || 'Unknown error'}`);
      }

      return result.data.campaigns || result.data || [];

    } catch (error) {
      logger.error('HeyReach campaigns MCP call failed:', error);
      throw new Error(`Failed to fetch HeyReach campaigns: ${error.message}`);
    }
  }
}

class OutreachSyncLogger {
  constructor(mcpTools, processId) {
    this.mcpTools = mcpTools;
    this.processId = processId;
  }

  async logSyncEvent(platform, action, contactId, success, error = null, details = {}) {
    const logEntry = {
      unique_id: generateBartonId(),
      process_id: this.processId,
      platform: platform,
      action: action,
      contact_unique_id: contactId,
      success: success,
      error_message: error ? error.message : null,
      details: JSON.stringify(details),
      timestamp: new Date().toISOString(),
      doctrine_version: '1.0.0'
    };

    try {
      await this.mcpTools.insert('unified_audit_log', logEntry);
    } catch (logError) {
      logger.error('Failed to log sync event:', logError);
    }
  }

  async logError(error, context) {
    const errorEntry = {
      unique_id: generateBartonId(),
      process_id: this.processId,
      error_type: 'outreach_sync_failed',
      error_message: error.message,
      context: JSON.stringify(context),
      timestamp: new Date().toISOString(),
      doctrine_version: '1.0.0'
    };

    try {
      await this.mcpTools.insert('error_log', errorEntry);
    } catch (logError) {
      logger.error('Failed to log sync error:', logError);
    }
  }
}

class NeonBackReferenceManager {
  constructor(mcpTools) {
    this.mcpTools = mcpTools;
    this.tableName = 'outreach_sync_tracking';
  }

  async storeSyncReference(syncData) {
    const referenceEntry = {
      unique_id: generateBartonId(),
      contact_unique_id: syncData.contact_unique_id,
      company_unique_id: syncData.company_unique_id,
      platform: syncData.platform,
      campaign_id: syncData.campaign_id,
      external_contact_id: syncData.external_contact_id,
      sync_status: syncData.sync_status,
      last_synced_at: syncData.last_synced_at,
      platform_response: syncData.platform_response,
      created_at: new Date().toISOString(),
      doctrine_version: syncData.doctrine_version
    };

    try {
      await this.mcpTools.insert(this.tableName, referenceEntry);
      return referenceEntry.unique_id;
    } catch (error) {
      logger.error('Failed to store sync reference:', error);
      throw new Error(`Back-reference storage failed: ${error.message}`);
    }
  }

  async updateSyncStatus(contactId, platform, status, details = {}) {
    try {
      const existingRecords = await this.mcpTools.query({
        table: this.tableName,
        where: {
          contact_unique_id: contactId,
          platform: platform
        },
        orderBy: { created_at: 'desc' },
        limit: 1
      });

      if (existingRecords.length > 0) {
        await this.mcpTools.update(this.tableName, existingRecords[0].unique_id, {
          sync_status: status,
          last_synced_at: new Date().toISOString(),
          details: JSON.stringify(details)
        });
      }
    } catch (error) {
      logger.error('Failed to update sync status:', error);
    }
  }

  async getSyncHistory(contactId, platform = null) {
    const whereClause = { contact_unique_id: contactId };
    if (platform) whereClause.platform = platform;

    try {
      return await this.mcpTools.query({
        table: this.tableName,
        where: whereClause,
        orderBy: { created_at: 'desc' }
      });
    } catch (error) {
      logger.error('Failed to get sync history:', error);
      return [];
    }
  }
}

class MCPTools {
  constructor() {
    this.baseUrl = process.env.COMPOSIO_MCP_URL || 'http://localhost:3001';
  }

  async callMCP(tool, data) {
    const payload = {
      tool: tool,
      data: data,
      unique_id: generateBartonId(),
      process_id: data.processId || 'unknown',
      orbt_layer: 6,
      blueprint_version: '1.0'
    };

    const response = await fetch(`${this.baseUrl}/tool`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`MCP call failed: ${response.statusText}`);
    }

    const result = await response.json();
    if (!result.success) {
      throw new Error(result.error || 'MCP operation failed');
    }

    return result.data;
  }

  async query(queryParams) {
    return await this.callMCP('FIREBASE_QUERY', queryParams);
  }

  async insert(table, record) {
    return await this.callMCP('FIREBASE_WRITE', {
      collection: table,
      data: record
    });
  }

  async update(table, id, updates) {
    return await this.callMCP('FIREBASE_UPDATE', {
      collection: table,
      id: id,
      data: updates
    });
  }
}

export const syncToInstantly = onCall({
  memory: '2GiB',
  timeoutSeconds: 600,
  maxInstances: 10
}, async (request) => {
  const { data, auth } = request;
  const startTime = Date.now();
  const processId = data.processId || `sync-instantly-${Date.now()}`;

  try {
    await validateMCPAccess(request, 'syncToInstantly');

    const mcpTools = new MCPTools();
    const payloadMapper = new OutreachPayloadMapper();
    const instantlyClient = new InstantlyMCPClient(mcpTools);
    const syncLogger = new OutreachSyncLogger(mcpTools, processId);
    const neonManager = new NeonBackReferenceManager(mcpTools);

    logger.info(`Starting Instantly sync for process: ${processId}`);

    const filters = data.filters || { status: 'promoted' };
    const campaignId = data.campaignId || null;

    const promotedPersons = await mcpTools.query({
      table: 'person_master',
      where: filters,
      limit: data.limit || 100
    });

    logger.info(`Found ${promotedPersons.length} promoted persons for Instantly sync`);

    const results = {
      success: true,
      processId: processId,
      platform: 'instantly',
      stats: {
        total: promotedPersons.length,
        synced: 0,
        failed: 0,
        skipped: 0
      },
      syncedContacts: [],
      errors: []
    };

    for (const person of promotedPersons) {
      try {
        let company = null;
        if (person.company_unique_id) {
          const companyResults = await mcpTools.query({
            table: 'company_master',
            where: { unique_id: person.company_unique_id },
            limit: 1
          });
          company = companyResults.length > 0 ? companyResults[0] : null;
        }

        const instantlyPayload = payloadMapper.mapToInstantlyPayload(person, company);

        const syncResponse = await instantlyClient.addContactToCampaign(instantlyPayload, campaignId, processId);

        const backReference = payloadMapper.mapSyncResponse('instantly', syncResponse, person, company);
        const referenceId = await neonManager.storeSyncReference(backReference);

        await syncLogger.logSyncEvent('instantly', 'contact_sync', person.unique_id, true, null, {
          campaignId: syncResponse.campaign_id,
          contactId: syncResponse.contact_id,
          referenceId: referenceId
        });

        results.syncedContacts.push({
          contact_unique_id: person.unique_id,
          company_unique_id: person.company_unique_id,
          campaign_id: syncResponse.campaign_id,
          external_contact_id: syncResponse.contact_id,
          reference_id: referenceId
        });

        results.stats.synced++;

        logger.info(`Instantly sync successful for contact: ${person.unique_id}`);

      } catch (error) {
        results.stats.failed++;

        await syncLogger.logSyncEvent('instantly', 'contact_sync', person.unique_id, false, error);
        await syncLogger.logError(error, {
          contactId: person.unique_id,
          platform: 'instantly',
          action: 'contact_sync'
        });

        results.errors.push({
          contact_unique_id: person.unique_id,
          error: error.message
        });

        logger.error(`Instantly sync failed for contact: ${person.unique_id}`, error);
      }
    }

    const endTime = Date.now();
    const duration = endTime - startTime;

    logger.info(`Instantly sync completed: ${results.stats.synced}/${results.stats.total} in ${duration}ms`);

    return {
      ...results,
      duration: duration,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Instantly sync process failed:', error);
    throw new HttpsError('internal', `Instantly sync failed: ${error.message}`);
  }
});

export const syncToHeyReach = onCall({
  memory: '2GiB',
  timeoutSeconds: 600,
  maxInstances: 10
}, async (request) => {
  const { data, auth } = request;
  const startTime = Date.now();
  const processId = data.processId || `sync-heyreach-${Date.now()}`;

  try {
    await validateMCPAccess(request, 'syncToHeyReach');

    const mcpTools = new MCPTools();
    const payloadMapper = new OutreachPayloadMapper();
    const heyreachClient = new HeyReachMCPClient(mcpTools);
    const syncLogger = new OutreachSyncLogger(mcpTools, processId);
    const neonManager = new NeonBackReferenceManager(mcpTools);

    logger.info(`Starting HeyReach sync for process: ${processId}`);

    const filters = data.filters || { status: 'promoted' };
    const campaignId = data.campaignId || null;

    const promotedPersons = await mcpTools.query({
      table: 'person_master',
      where: filters,
      limit: data.limit || 100
    });

    logger.info(`Found ${promotedPersons.length} promoted persons for HeyReach sync`);

    const results = {
      success: true,
      processId: processId,
      platform: 'heyreach',
      stats: {
        total: promotedPersons.length,
        synced: 0,
        failed: 0,
        skipped: 0
      },
      syncedContacts: [],
      errors: []
    };

    for (const person of promotedPersons) {
      try {
        let company = null;
        if (person.company_unique_id) {
          const companyResults = await mcpTools.query({
            table: 'company_master',
            where: { unique_id: person.company_unique_id },
            limit: 1
          });
          company = companyResults.length > 0 ? companyResults[0] : null;
        }

        const heyreachPayload = payloadMapper.mapToHeyReachPayload(person, company);

        const syncResponse = await heyreachClient.addContactToCampaign(heyreachPayload, campaignId, processId);

        const backReference = payloadMapper.mapSyncResponse('heyreach', syncResponse, person, company);
        const referenceId = await neonManager.storeSyncReference(backReference);

        await syncLogger.logSyncEvent('heyreach', 'contact_sync', person.unique_id, true, null, {
          campaignId: syncResponse.campaign_id,
          contactId: syncResponse.contact_id,
          referenceId: referenceId
        });

        results.syncedContacts.push({
          contact_unique_id: person.unique_id,
          company_unique_id: person.company_unique_id,
          campaign_id: syncResponse.campaign_id,
          external_contact_id: syncResponse.contact_id,
          reference_id: referenceId
        });

        results.stats.synced++;

        logger.info(`HeyReach sync successful for contact: ${person.unique_id}`);

      } catch (error) {
        results.stats.failed++;

        await syncLogger.logSyncEvent('heyreach', 'contact_sync', person.unique_id, false, error);
        await syncLogger.logError(error, {
          contactId: person.unique_id,
          platform: 'heyreach',
          action: 'contact_sync'
        });

        results.errors.push({
          contact_unique_id: person.unique_id,
          error: error.message
        });

        logger.error(`HeyReach sync failed for contact: ${person.unique_id}`, error);
      }
    }

    const endTime = Date.now();
    const duration = endTime - startTime;

    logger.info(`HeyReach sync completed: ${results.stats.synced}/${results.stats.total} in ${duration}ms`);

    return {
      ...results,
      duration: duration,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('HeyReach sync process failed:', error);
    throw new HttpsError('internal', `HeyReach sync failed: ${error.message}`);
  }
});

export const getSyncStatus = onCall({
  memory: '1GiB',
  timeoutSeconds: 60
}, async (request) => {
  const { data } = request;

  try {
    await validateMCPAccess(request, 'getSyncStatus');

    const mcpTools = new MCPTools();
    const neonManager = new NeonBackReferenceManager(mcpTools);

    const contactId = data.contactId;
    const platform = data.platform || null;

    if (!contactId) {
      throw new HttpsError('invalid-argument', 'contactId is required');
    }

    const syncHistory = await neonManager.getSyncHistory(contactId, platform);

    return {
      success: true,
      contactId: contactId,
      platform: platform,
      syncHistory: syncHistory,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Get sync status failed:', error);
    throw new HttpsError('internal', `Sync status check failed: ${error.message}`);
  }
});

export const getCampaigns = onCall({
  memory: '1GiB',
  timeoutSeconds: 60
}, async (request) => {
  const { data } = request;

  try {
    await validateMCPAccess(request, 'getCampaigns');

    const platform = data.platform;

    if (!platform || !['instantly', 'heyreach'].includes(platform)) {
      throw new HttpsError('invalid-argument', 'Valid platform (instantly or heyreach) is required');
    }

    let campaigns = [];

    const mcpTools = new MCPTools();
    const processId = `get-campaigns-${platform}-${Date.now()}`;

    if (platform === 'instantly') {
      const instantlyClient = new InstantlyMCPClient(mcpTools);
      campaigns = await instantlyClient.getCampaigns(processId);
    } else if (platform === 'heyreach') {
      const heyreachClient = new HeyReachMCPClient(mcpTools);
      campaigns = await heyreachClient.getCampaigns(processId);
    }

    return {
      success: true,
      platform: platform,
      campaigns: campaigns,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error(`Get ${data.platform} campaigns failed:`, error);
    throw new HttpsError('internal', `Failed to fetch campaigns: ${error.message}`);
  }
});