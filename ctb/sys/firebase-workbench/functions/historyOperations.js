/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-F31BAF8A
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

import { onCall, HttpsError } from 'firebase-functions/v2/https';
import { logger } from 'firebase-functions';
import { validateMCPAccess, generateBartonId } from '../utils/doctrineHelpers.js';
import { HistoryValidator, HistoryUtils } from '../history-schema.js';

/**
 * History Layer Operations for Barton Doctrine Pipeline
 *
 * Purpose: Track data discovery provenance to prevent redundant enrichment/scraping
 * and maintain complete audit trail of when, where, and what information was found.
 */

class HistoryTracker {
  constructor(mcpTools) {
    this.mcpTools = mcpTools;
    this.doctrineVersion = '1.0.0';
  }

  async addHistoryEntry(type, entry) {
    // Validate entry based on type
    const validation = type === 'company'
      ? HistoryValidator.validateCompanyHistoryEntry(entry)
      : HistoryValidator.validatePersonHistoryEntry(entry);

    if (!validation.isValid) {
      throw new Error(`History entry validation failed: ${validation.errors.join(', ')}`);
    }

    // Format entry with defaults
    const formattedEntry = HistoryUtils.formatHistoryEntry(entry, type);

    // Add unique ID for tracking
    formattedEntry.history_id = HistoryUtils.generateHistoryId();
    formattedEntry.doctrine_version = this.doctrineVersion;

    // Store in Firestore via MCP
    const collection = type === 'company' ? 'company_history' : 'person_history';

    try {
      await this.mcpTools.writeToFirestore(collection, formattedEntry);

      // Also store in Neon vault for permanent record
      await this.storeInNeonVault(type, formattedEntry);

      return formattedEntry.history_id;
    } catch (error) {
      logger.error(`Failed to add ${type} history entry:`, error);
      throw new Error(`History storage failed: ${error.message}`);
    }
  }

  async storeInNeonVault(type, entry) {
    const tableName = type === 'company' ? 'company_history' : 'person_history';
    const idField = type === 'company' ? 'company_unique_id' : 'person_unique_id';

    const neonEntry = {
      [idField]: entry[`${type}_id`],
      field: entry.field,
      value_found: entry.value_found,
      source: entry.source,
      timestamp_found: new Date(entry.timestamp_found.seconds * 1000).toISOString(),
      confidence_score: entry.confidence_score,
      process_id: entry.process_id,
      session_id: entry.session_id,
      previous_value: entry.previous_value,
      change_reason: entry.change_reason,
      metadata: JSON.stringify(entry.metadata || {})
    };

    await this.mcpTools.insertToNeon(tableName, neonEntry);
  }

  async getLatestHistory(entityId, field, type) {
    const collection = type === 'company' ? 'company_history' : 'person_history';
    const idField = `${type}_id`;

    try {
      const query = {
        collection: collection,
        where: {
          [idField]: entityId,
          field: field
        },
        orderBy: { timestamp_found: 'desc' },
        limit: 1
      };

      const results = await this.mcpTools.queryFirestore(query);
      return results.length > 0 ? results[0] : null;
    } catch (error) {
      logger.error(`Failed to get latest history for ${type} ${entityId}, field ${field}:`, error);
      return null;
    }
  }

  async hasFieldBeenDiscovered(entityId, field, type, maxAge = 7 * 24 * 60 * 60 * 1000) {
    const latestHistory = await this.getLatestHistory(entityId, field, type);

    if (!latestHistory) return false;

    const ageMs = Date.now() - (latestHistory.timestamp_found.seconds * 1000);
    return ageMs <= maxAge;
  }

  async getHistoryTimeline(entityId, type, limit = 50) {
    const collection = type === 'company' ? 'company_history' : 'person_history';
    const idField = `${type}_id`;

    try {
      const query = {
        collection: collection,
        where: { [idField]: entityId },
        orderBy: { timestamp_found: 'desc' },
        limit: limit
      };

      return await this.mcpTools.queryFirestore(query);
    } catch (error) {
      logger.error(`Failed to get history timeline for ${type} ${entityId}:`, error);
      return [];
    }
  }

  async getSourceHistory(source, startTime, endTime, type = null) {
    const collections = type ? [`${type}_history`] : ['company_history', 'person_history'];
    const allHistory = [];

    for (const collection of collections) {
      try {
        const query = {
          collection: collection,
          where: {
            source: source,
            timestamp_found: {
              '>=': startTime,
              '<=': endTime
            }
          },
          orderBy: { timestamp_found: 'desc' }
        };

        const results = await this.mcpTools.queryFirestore(query);
        allHistory.push(...results.map(r => ({ ...r, entity_type: collection.replace('_history', '') })));
      } catch (error) {
        logger.error(`Failed to get source history from ${collection}:`, error);
      }
    }

    return allHistory;
  }

  async detectDuplicateFindings(entityId, field, value, type) {
    const existingHistory = await this.getLatestHistory(entityId, field, type);

    if (!existingHistory) return false;

    // Check if the value is essentially the same
    const normalizedNew = String(value).trim().toLowerCase();
    const normalizedExisting = String(existingHistory.value_found).trim().toLowerCase();

    return normalizedNew === normalizedExisting;
  }

  async updateConfidenceScore(historyId, newScore, reason) {
    try {
      // Update in both Firestore and Neon
      const updateData = {
        confidence_score: newScore,
        confidence_update_reason: reason,
        confidence_updated_at: new Date().toISOString()
      };

      // Update Firestore - try both collections
      for (const collection of ['company_history', 'person_history']) {
        try {
          await this.mcpTools.updateFirestore(collection, historyId, updateData);
          break; // If successful, exit loop
        } catch (error) {
          // Continue to next collection if not found
        }
      }

      // Update Neon vault
      await this.mcpTools.updateNeon('company_history', { history_id: historyId }, updateData);
      await this.mcpTools.updateNeon('person_history', { history_id: historyId }, updateData);

      return true;
    } catch (error) {
      logger.error(`Failed to update confidence score for history ${historyId}:`, error);
      return false;
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
      process_id: data.processId || 'history',
      orbt_layer: 8, // History layer
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

  async writeToFirestore(collection, data) {
    return await this.callMCP('FIREBASE_WRITE', {
      collection: collection,
      data: data
    });
  }

  async queryFirestore(queryParams) {
    return await this.callMCP('FIREBASE_QUERY', queryParams);
  }

  async updateFirestore(collection, docId, updates) {
    return await this.callMCP('FIREBASE_UPDATE', {
      collection: collection,
      id: docId,
      data: updates
    });
  }

  async insertToNeon(table, data) {
    return await this.callMCP('NEON_INSERT', {
      table: table,
      data: data
    });
  }

  async updateNeon(table, where, updates) {
    return await this.callMCP('NEON_UPDATE', {
      table: table,
      where: where,
      data: updates
    });
  }
}

// Cloud Function: Add Company History Entry
export const addCompanyHistoryEntry = onCall({
  memory: '1GiB',
  timeoutSeconds: 300
}, async (request) => {
  const { data } = request;

  try {
    await validateMCPAccess(request, 'addCompanyHistoryEntry');

    const mcpTools = new MCPTools();
    const historyTracker = new HistoryTracker(mcpTools);

    const entry = {
      company_id: data.companyId,
      field: data.field,
      value_found: data.value,
      source: data.source,
      confidence_score: data.confidenceScore,
      process_id: data.processId,
      session_id: data.sessionId,
      previous_value: data.previousValue,
      change_reason: data.changeReason,
      metadata: data.metadata
    };

    // Check for duplicates if requested
    if (data.preventDuplicates) {
      const isDuplicate = await historyTracker.detectDuplicateFindings(
        data.companyId,
        data.field,
        data.value,
        'company'
      );

      if (isDuplicate) {
        return {
          success: true,
          duplicate: true,
          message: 'Value already exists with same content',
          timestamp: new Date().toISOString()
        };
      }
    }

    const historyId = await historyTracker.addHistoryEntry('company', entry);

    logger.info(`Company history entry added: ${historyId} for ${data.companyId}:${data.field}`);

    return {
      success: true,
      historyId: historyId,
      duplicate: false,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Add company history entry failed:', error);
    throw new HttpsError('internal', `Failed to add company history: ${error.message}`);
  }
});

// Cloud Function: Add Person History Entry
export const addPersonHistoryEntry = onCall({
  memory: '1GiB',
  timeoutSeconds: 300
}, async (request) => {
  const { data } = request;

  try {
    await validateMCPAccess(request, 'addPersonHistoryEntry');

    const mcpTools = new MCPTools();
    const historyTracker = new HistoryTracker(mcpTools);

    const entry = {
      person_id: data.personId,
      field: data.field,
      value_found: data.value,
      source: data.source,
      confidence_score: data.confidenceScore,
      process_id: data.processId,
      session_id: data.sessionId,
      previous_value: data.previousValue,
      change_reason: data.changeReason,
      related_company_id: data.relatedCompanyId,
      metadata: data.metadata
    };

    // Check for duplicates if requested
    if (data.preventDuplicates) {
      const isDuplicate = await historyTracker.detectDuplicateFindings(
        data.personId,
        data.field,
        data.value,
        'person'
      );

      if (isDuplicate) {
        return {
          success: true,
          duplicate: true,
          message: 'Value already exists with same content',
          timestamp: new Date().toISOString()
        };
      }
    }

    const historyId = await historyTracker.addHistoryEntry('person', entry);

    logger.info(`Person history entry added: ${historyId} for ${data.personId}:${data.field}`);

    return {
      success: true,
      historyId: historyId,
      duplicate: false,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Add person history entry failed:', error);
    throw new HttpsError('internal', `Failed to add person history: ${error.message}`);
  }
});

// Cloud Function: Get Latest History
export const getLatestHistory = onCall({
  memory: '1GiB',
  timeoutSeconds: 300
}, async (request) => {
  const { data } = request;

  try {
    await validateMCPAccess(request, 'getLatestHistory');

    if (!data.entityId || !data.field || !data.type) {
      throw new HttpsError('invalid-argument', 'entityId, field, and type are required');
    }

    const mcpTools = new MCPTools();
    const historyTracker = new HistoryTracker(mcpTools);

    const latestHistory = await historyTracker.getLatestHistory(
      data.entityId,
      data.field,
      data.type
    );

    return {
      success: true,
      history: latestHistory,
      hasHistory: !!latestHistory,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Get latest history failed:', error);
    throw new HttpsError('internal', `Failed to get latest history: ${error.message}`);
  }
});

// Cloud Function: Check if Field Discovered Recently
export const checkFieldDiscovered = onCall({
  memory: '1GiB',
  timeoutSeconds: 300
}, async (request) => {
  const { data } = request;

  try {
    await validateMCPAccess(request, 'checkFieldDiscovered');

    if (!data.entityId || !data.field || !data.type) {
      throw new HttpsError('invalid-argument', 'entityId, field, and type are required');
    }

    const mcpTools = new MCPTools();
    const historyTracker = new HistoryTracker(mcpTools);

    const maxAge = data.maxAgeMs || (7 * 24 * 60 * 60 * 1000); // Default 7 days
    const wasDiscovered = await historyTracker.hasFieldBeenDiscovered(
      data.entityId,
      data.field,
      data.type,
      maxAge
    );

    const latestHistory = await historyTracker.getLatestHistory(
      data.entityId,
      data.field,
      data.type
    );

    return {
      success: true,
      wasDiscovered: wasDiscovered,
      latestHistory: latestHistory,
      maxAgeMs: maxAge,
      shouldSkipEnrichment: wasDiscovered,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Check field discovered failed:', error);
    throw new HttpsError('internal', `Failed to check field discovery: ${error.message}`);
  }
});

// Cloud Function: Get History Timeline
export const getHistoryTimeline = onCall({
  memory: '1GiB',
  timeoutSeconds: 300
}, async (request) => {
  const { data } = request;

  try {
    await validateMCPAccess(request, 'getHistoryTimeline');

    if (!data.entityId || !data.type) {
      throw new HttpsError('invalid-argument', 'entityId and type are required');
    }

    const mcpTools = new MCPTools();
    const historyTracker = new HistoryTracker(mcpTools);

    const timeline = await historyTracker.getHistoryTimeline(
      data.entityId,
      data.type,
      data.limit || 50
    );

    return {
      success: true,
      timeline: timeline,
      entityId: data.entityId,
      entityType: data.type,
      entryCount: timeline.length,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Get history timeline failed:', error);
    throw new HttpsError('internal', `Failed to get history timeline: ${error.message}`);
  }
});

// Cloud Function: Get Source History Report
export const getSourceHistoryReport = onCall({
  memory: '2GiB',
  timeoutSeconds: 300
}, async (request) => {
  const { data } = request;

  try {
    await validateMCPAccess(request, 'getSourceHistoryReport');

    if (!data.source || !data.startTime || !data.endTime) {
      throw new HttpsError('invalid-argument', 'source, startTime, and endTime are required');
    }

    const mcpTools = new MCPTools();
    const historyTracker = new HistoryTracker(mcpTools);

    const startTime = new Date(data.startTime);
    const endTime = new Date(data.endTime);

    const sourceHistory = await historyTracker.getSourceHistory(
      data.source,
      startTime,
      endTime,
      data.type
    );

    // Generate summary statistics
    const stats = {
      totalEntries: sourceHistory.length,
      companyEntries: sourceHistory.filter(h => h.entity_type === 'company').length,
      personEntries: sourceHistory.filter(h => h.entity_type === 'person').length,
      uniqueFields: [...new Set(sourceHistory.map(h => h.field))],
      averageConfidence: sourceHistory.reduce((sum, h) => sum + h.confidence_score, 0) / sourceHistory.length || 0,
      timeRange: { startTime: startTime.toISOString(), endTime: endTime.toISOString() }
    };

    return {
      success: true,
      source: data.source,
      history: sourceHistory,
      stats: stats,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Get source history report failed:', error);
    throw new HttpsError('internal', `Failed to get source history report: ${error.message}`);
  }
});

// Cloud Function: Batch Add History Entries
export const batchAddHistoryEntries = onCall({
  memory: '2GiB',
  timeoutSeconds: 600
}, async (request) => {
  const { data } = request;

  try {
    await validateMCPAccess(request, 'batchAddHistoryEntries');

    if (!data.entries || !Array.isArray(data.entries)) {
      throw new HttpsError('invalid-argument', 'entries array is required');
    }

    const mcpTools = new MCPTools();
    const historyTracker = new HistoryTracker(mcpTools);

    const results = {
      success: true,
      processId: data.processId || `batch-history-${Date.now()}`,
      stats: {
        total: data.entries.length,
        successful: 0,
        failed: 0,
        duplicates: 0
      },
      errors: [],
      historyIds: []
    };

    for (const entry of data.entries) {
      try {
        // Check for duplicates if requested
        if (data.preventDuplicates) {
          const isDuplicate = await historyTracker.detectDuplicateFindings(
            entry.entityId,
            entry.field,
            entry.value,
            entry.type
          );

          if (isDuplicate) {
            results.stats.duplicates++;
            continue;
          }
        }

        const historyEntry = {
          [`${entry.type}_id`]: entry.entityId,
          field: entry.field,
          value_found: entry.value,
          source: entry.source,
          confidence_score: entry.confidenceScore,
          process_id: results.processId,
          session_id: entry.sessionId,
          previous_value: entry.previousValue,
          change_reason: entry.changeReason,
          metadata: entry.metadata
        };

        if (entry.type === 'person' && entry.relatedCompanyId) {
          historyEntry.related_company_id = entry.relatedCompanyId;
        }

        const historyId = await historyTracker.addHistoryEntry(entry.type, historyEntry);
        results.historyIds.push(historyId);
        results.stats.successful++;

      } catch (error) {
        results.stats.failed++;
        results.errors.push({
          entityId: entry.entityId,
          field: entry.field,
          error: error.message
        });
      }
    }

    logger.info(`Batch history operation completed: ${results.stats.successful}/${results.stats.total} successful`);

    return {
      ...results,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Batch add history entries failed:', error);
    throw new HttpsError('internal', `Failed to batch add history entries: ${error.message}`);
  }
});