/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-E4BD44FC
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

import { onCall, HttpsError } from 'firebase-functions/v2/https';
import { logger } from 'firebase-functions';
import { validateMCPAccess, generateBartonId } from '../utils/doctrineHelpers.js';

class PromotionEngine {
  constructor() {
    this.doctrineVersion = '1.0.0';
    this.supportedTables = ['company_master', 'person_master'];
    this.requiredFields = {
      company: ['company_name', 'domain', 'industry'],
      person: ['first_name', 'last_name', 'email']
    };
  }

  async validateRecord(record, type) {
    const required = this.requiredFields[type] || [];
    const missing = required.filter(field => !record[field] || record[field].toString().trim() === '');

    if (missing.length > 0) {
      throw new Error(`Missing required fields: ${missing.join(', ')}`);
    }

    if (type === 'person' && record.email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(record.email)) {
        throw new Error('Invalid email format');
      }
    }

    if (type === 'company' && record.domain) {
      const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$/;
      if (!domainRegex.test(record.domain)) {
        throw new Error('Invalid domain format');
      }
    }

    return true;
  }

  async checkDuplicates(record, type, mcpTools) {
    const searchField = type === 'company' ? 'domain' : 'email';
    const searchValue = record[searchField];

    if (!searchValue) return null;

    const query = {
      table: `${type}_master`,
      where: { [searchField]: searchValue },
      limit: 1
    };

    try {
      const results = await mcpTools.query(query);
      return results.length > 0 ? results[0] : null;
    } catch (error) {
      logger.warn(`Duplicate check failed for ${type}:`, error.message);
      return null;
    }
  }

  generatePermanentId(type) {
    const prefix = type === 'company' ? 'CMP' : 'PER';
    const timestamp = Date.now().toString().slice(-8);
    const random = Math.random().toString(36).substring(2, 8).toUpperCase();
    return `${prefix}-${timestamp}-${random}`;
  }

  async promoteRecord(record, type, mcpTools, processId) {
    try {
      await this.validateRecord(record, type);

      const duplicate = await this.checkDuplicates(record, type, mcpTools);
      if (duplicate) {
        throw new Error(`Duplicate ${type} found with ${type === 'company' ? 'domain' : 'email'}: ${record[type === 'company' ? 'domain' : 'email']}`);
      }

      const permanentId = this.generatePermanentId(type);
      const currentTime = new Date().toISOString();

      const masterRecord = {
        ...record,
        unique_id: permanentId,
        doctrine_version: this.doctrineVersion,
        promoted_at: currentTime,
        promoted_from_intake: record.intake_unique_id || record.unique_id,
        process_id: processId,
        status: 'active',
        created_at: currentTime,
        updated_at: currentTime
      };

      delete masterRecord.intake_unique_id;

      return masterRecord;

    } catch (error) {
      throw new Error(`Record validation failed: ${error.message}`);
    }
  }
}

class PromotionTransaction {
  constructor(mcpTools, processId) {
    this.mcpTools = mcpTools;
    this.processId = processId;
    this.operations = [];
    this.rollbackOperations = [];
  }

  addOperation(operation, rollback = null) {
    this.operations.push(operation);
    if (rollback) {
      this.rollbackOperations.unshift(rollback);
    }
  }

  async execute() {
    try {
      const results = [];

      for (const operation of this.operations) {
        const result = await operation();
        results.push(result);
      }

      return results;
    } catch (error) {
      await this.rollback();
      throw error;
    }
  }

  async rollback() {
    for (const rollbackOp of this.rollbackOperations) {
      try {
        await rollbackOp();
      } catch (rollbackError) {
        logger.error('Rollback operation failed:', rollbackError);
      }
    }
  }
}

class PromotionLogger {
  constructor(mcpTools, processId) {
    this.mcpTools = mcpTools;
    this.processId = processId;
  }

  async logPromotion(record, type, success, error = null) {
    const logEntry = {
      unique_id: generateBartonId(),
      process_id: this.processId,
      record_type: type,
      record_id: record.unique_id || record.intake_unique_id,
      promoted_id: success ? record.unique_id : null,
      success: success,
      error_message: error ? error.message : null,
      timestamp: new Date().toISOString(),
      doctrine_version: '1.0.0'
    };

    try {
      await this.mcpTools.insert('promotion_log', logEntry);
    } catch (logError) {
      logger.error('Failed to log promotion:', logError);
    }
  }

  async logAudit(action, details) {
    const auditEntry = {
      unique_id: generateBartonId(),
      process_id: this.processId,
      action: action,
      table_name: details.table || 'unknown',
      record_id: details.recordId || 'unknown',
      changes: JSON.stringify(details.changes || {}),
      timestamp: new Date().toISOString(),
      doctrine_version: '1.0.0'
    };

    try {
      await this.mcpTools.insert('unified_audit_log', auditEntry);
    } catch (logError) {
      logger.error('Failed to log audit:', logError);
    }
  }

  async logError(error, context) {
    const errorEntry = {
      unique_id: generateBartonId(),
      process_id: this.processId,
      error_type: 'promotion_failed',
      error_message: error.message,
      context: JSON.stringify(context),
      timestamp: new Date().toISOString(),
      doctrine_version: '1.0.0'
    };

    try {
      await this.mcpTools.insert('error_log', errorEntry);
    } catch (logError) {
      logger.error('Failed to log error:', logError);
    }
  }
}

class MCPTools {
  constructor() {
    this.baseUrl = process.env.COMPOSIO_MCP_URL || 'http://localhost:3001';
    this.tools = [
      'FIREBASE_READ', 'FIREBASE_WRITE', 'FIREBASE_UPDATE',
      'FIREBASE_QUERY', 'FIREBASE_DELETE'
    ];
  }

  async callMCP(tool, data) {
    const payload = {
      tool: tool,
      data: data,
      unique_id: generateBartonId(),
      process_id: data.processId || 'unknown',
      orbt_layer: 4,
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

  async delete(table, id) {
    return await this.callMCP('FIREBASE_DELETE', {
      collection: table,
      id: id
    });
  }
}

export const promoteCompany = onCall({
  memory: '2GiB',
  timeoutSeconds: 600,
  maxInstances: 10
}, async (request) => {
  const { data, auth } = request;
  const startTime = Date.now();
  const processId = data.processId || `promote-company-${Date.now()}`;

  try {
    await validateMCPAccess(request, 'promoteCompany');

    const mcpTools = new MCPTools();
    const promotionEngine = new PromotionEngine();
    const promotionLogger = new PromotionLogger(mcpTools, processId);

    logger.info(`Starting company promotion for process: ${processId}`);

    if (!data.companyRecords || !Array.isArray(data.companyRecords)) {
      throw new HttpsError('invalid-argument', 'companyRecords array is required');
    }

    const results = {
      success: true,
      processId: processId,
      stats: {
        total: data.companyRecords.length,
        promoted: 0,
        failed: 0,
        duplicates: 0
      },
      promotedCompanies: [],
      errors: []
    };

    for (const intakeRecord of data.companyRecords) {
      const transaction = new PromotionTransaction(mcpTools, processId);

      try {
        const masterRecord = await promotionEngine.promoteRecord(intakeRecord, 'company', mcpTools, processId);

        transaction.addOperation(
          async () => await mcpTools.insert('company_master', masterRecord),
          async () => await mcpTools.delete('company_master', masterRecord.unique_id)
        );

        transaction.addOperation(
          async () => await mcpTools.update('company_intake_staging', intakeRecord.unique_id, {
            promotion_status: 'promoted',
            promoted_to: masterRecord.unique_id,
            promoted_at: new Date().toISOString()
          }),
          async () => await mcpTools.update('company_intake_staging', intakeRecord.unique_id, {
            promotion_status: 'validated',
            promoted_to: null,
            promoted_at: null
          })
        );

        await transaction.execute();

        await promotionLogger.logPromotion(masterRecord, 'company', true);
        await promotionLogger.logAudit('company_promoted', {
          table: 'company_master',
          recordId: masterRecord.unique_id,
          changes: { status: 'promoted', from_intake: intakeRecord.unique_id }
        });

        results.promotedCompanies.push(masterRecord);
        results.stats.promoted++;

        logger.info(`Company promoted: ${masterRecord.unique_id}`);

      } catch (error) {
        results.stats.failed++;

        if (error.message.includes('Duplicate')) {
          results.stats.duplicates++;
        }

        await promotionLogger.logPromotion(intakeRecord, 'company', false, error);
        await promotionLogger.logError(error, {
          recordId: intakeRecord.unique_id,
          type: 'company_promotion'
        });

        results.errors.push({
          recordId: intakeRecord.unique_id,
          error: error.message
        });

        logger.error(`Company promotion failed: ${intakeRecord.unique_id}`, error);
      }
    }

    const endTime = Date.now();
    const duration = endTime - startTime;

    logger.info(`Company promotion completed: ${results.stats.promoted}/${results.stats.total} in ${duration}ms`);

    return {
      ...results,
      duration: duration,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Company promotion process failed:', error);
    throw new HttpsError('internal', `Company promotion failed: ${error.message}`);
  }
});

export const promotePerson = onCall({
  memory: '2GiB',
  timeoutSeconds: 600,
  maxInstances: 10
}, async (request) => {
  const { data, auth } = request;
  const startTime = Date.now();
  const processId = data.processId || `promote-person-${Date.now()}`;

  try {
    await validateMCPAccess(request, 'promotePerson');

    const mcpTools = new MCPTools();
    const promotionEngine = new PromotionEngine();
    const promotionLogger = new PromotionLogger(mcpTools, processId);

    logger.info(`Starting person promotion for process: ${processId}`);

    if (!data.personRecords || !Array.isArray(data.personRecords)) {
      throw new HttpsError('invalid-argument', 'personRecords array is required');
    }

    const results = {
      success: true,
      processId: processId,
      stats: {
        total: data.personRecords.length,
        promoted: 0,
        failed: 0,
        duplicates: 0,
        relationshipsPreserved: 0
      },
      promotedPersons: [],
      errors: []
    };

    for (const intakeRecord of data.personRecords) {
      const transaction = new PromotionTransaction(mcpTools, processId);

      try {
        const masterRecord = await promotionEngine.promoteRecord(intakeRecord, 'person', mcpTools, processId);

        if (intakeRecord.company_unique_id) {
          const companyExists = await mcpTools.query({
            table: 'company_master',
            where: { unique_id: intakeRecord.company_unique_id },
            limit: 1
          });

          if (companyExists.length > 0) {
            masterRecord.company_unique_id = intakeRecord.company_unique_id;
            results.stats.relationshipsPreserved++;
          } else {
            logger.warn(`Company relationship not found: ${intakeRecord.company_unique_id}`);
          }
        }

        transaction.addOperation(
          async () => await mcpTools.insert('person_master', masterRecord),
          async () => await mcpTools.delete('person_master', masterRecord.unique_id)
        );

        transaction.addOperation(
          async () => await mcpTools.update('person_intake_staging', intakeRecord.unique_id, {
            promotion_status: 'promoted',
            promoted_to: masterRecord.unique_id,
            promoted_at: new Date().toISOString()
          }),
          async () => await mcpTools.update('person_intake_staging', intakeRecord.unique_id, {
            promotion_status: 'validated',
            promoted_to: null,
            promoted_at: null
          })
        );

        await transaction.execute();

        await promotionLogger.logPromotion(masterRecord, 'person', true);
        await promotionLogger.logAudit('person_promoted', {
          table: 'person_master',
          recordId: masterRecord.unique_id,
          changes: {
            status: 'promoted',
            from_intake: intakeRecord.unique_id,
            company_relationship: masterRecord.company_unique_id || 'none'
          }
        });

        results.promotedPersons.push(masterRecord);
        results.stats.promoted++;

        logger.info(`Person promoted: ${masterRecord.unique_id}`);

      } catch (error) {
        results.stats.failed++;

        if (error.message.includes('Duplicate')) {
          results.stats.duplicates++;
        }

        await promotionLogger.logPromotion(intakeRecord, 'person', false, error);
        await promotionLogger.logError(error, {
          recordId: intakeRecord.unique_id,
          type: 'person_promotion'
        });

        results.errors.push({
          recordId: intakeRecord.unique_id,
          error: error.message
        });

        logger.error(`Person promotion failed: ${intakeRecord.unique_id}`, error);
      }
    }

    const endTime = Date.now();
    const duration = endTime - startTime;

    logger.info(`Person promotion completed: ${results.stats.promoted}/${results.stats.total} in ${duration}ms`);

    return {
      ...results,
      duration: duration,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Person promotion process failed:', error);
    throw new HttpsError('internal', `Person promotion failed: ${error.message}`);
  }
});

export const getPromotionStatus = onCall({
  memory: '1GiB',
  timeoutSeconds: 60
}, async (request) => {
  const { data } = request;

  try {
    await validateMCPAccess(request, 'getPromotionStatus');

    const mcpTools = new MCPTools();
    const processId = data.processId;

    if (!processId) {
      throw new HttpsError('invalid-argument', 'processId is required');
    }

    const promotionLogs = await mcpTools.query({
      table: 'promotion_log',
      where: { process_id: processId },
      orderBy: { timestamp: 'desc' }
    });

    const stats = promotionLogs.reduce((acc, log) => {
      acc.total++;
      if (log.success) {
        acc.promoted++;
      } else {
        acc.failed++;
      }
      return acc;
    }, { total: 0, promoted: 0, failed: 0 });

    return {
      success: true,
      processId: processId,
      stats: stats,
      logs: promotionLogs,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Get promotion status failed:', error);
    throw new HttpsError('internal', `Status check failed: ${error.message}`);
  }
});