/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/firebase-workbench
Barton ID: 04.04.01
Unique ID: CTB-83FD2B7E
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

import { onCall, HttpsError } from 'firebase-functions/v2/https';
import { logger } from 'firebase-functions';
import { validateMCPAccess, generateBartonId } from '../utils/doctrineHelpers.js';

class PipelineMetricsCollector {
  constructor(mcpTools) {
    this.mcpTools = mcpTools;
    this.doctrineVersion = '1.0.0';
    this.pipelineStages = [
      'ingested', 'validated', 'enriched', 'scraped',
      'adjusted', 'promoted', 'synced'
    ];
    this.stageTableMapping = {
      ingested: ['company_intake_staging', 'person_intake_staging'],
      validated: ['company_intake_staging', 'person_intake_staging'],
      enriched: ['company_intake_staging', 'person_intake_staging'],
      scraped: ['company_intake_staging', 'person_intake_staging'],
      adjusted: ['company_intake_staging', 'person_intake_staging'],
      promoted: ['company_master', 'person_master'],
      synced: ['outreach_sync_tracking']
    };
  }

  async getStageCount(stage, timeRange = '24h') {
    const tables = this.stageTableMapping[stage] || [];
    let totalCount = 0;

    const timeFilter = this.buildTimeFilter(timeRange);

    try {
      for (const table of tables) {
        let query = { table: table };

        if (stage === 'promoted') {
          query.where = { status: 'active', ...timeFilter };
        } else if (stage === 'synced') {
          query.where = { sync_status: 'success', ...timeFilter };
        } else {
          const statusField = this.getStatusField(stage);
          query.where = { [statusField]: stage, ...timeFilter };
        }

        const results = await this.mcpTools.query(query);
        totalCount += results.length;
      }

      return totalCount;
    } catch (error) {
      logger.error(`Failed to get count for stage ${stage}:`, error);
      return 0;
    }
  }

  async getAllStageCounts(timeRange = '24h') {
    const stageCounts = {};

    for (const stage of this.pipelineStages) {
      stageCounts[stage] = await this.getStageCount(stage, timeRange);
    }

    return stageCounts;
  }

  getStatusField(stage) {
    const statusFieldMap = {
      ingested: 'intake_status',
      validated: 'validation_status',
      enriched: 'enrichment_status',
      scraped: 'scraping_status',
      adjusted: 'adjustment_status'
    };
    return statusFieldMap[stage] || 'status';
  }

  buildTimeFilter(timeRange) {
    const now = new Date();
    let startTime;

    switch (timeRange) {
      case '1h':
        startTime = new Date(now.getTime() - 60 * 60 * 1000);
        break;
      case '24h':
        startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        break;
      case '7d':
        startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      default:
        startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    }

    return {
      created_at: { '>=': startTime.toISOString() }
    };
  }
}

class ErrorMetricsAnalyzer {
  constructor(mcpTools) {
    this.mcpTools = mcpTools;
    this.errorTables = ['error_log', 'unified_audit_log'];
  }

  async getErrorRates(timeRange = '24h', groupBy = 'hour') {
    const timeFilter = this.buildTimeFilter(timeRange);
    const errorRates = [];

    try {
      const errors = await this.mcpTools.query({
        table: 'error_log',
        where: timeFilter,
        orderBy: { timestamp: 'asc' }
      });

      const groupedErrors = this.groupErrorsByTime(errors, groupBy);

      for (const [timeKey, errorCount] of Object.entries(groupedErrors)) {
        const totalProcessed = await this.getTotalProcessedForPeriod(timeKey, groupBy);
        const errorRate = totalProcessed > 0 ? (errorCount / totalProcessed) * 100 : 0;

        errorRates.push({
          timestamp: timeKey,
          errorCount: errorCount,
          totalProcessed: totalProcessed,
          errorRate: parseFloat(errorRate.toFixed(2))
        });
      }

      return errorRates;
    } catch (error) {
      logger.error('Failed to calculate error rates:', error);
      return [];
    }
  }

  async getErrorDistribution(timeRange = '24h') {
    const timeFilter = this.buildTimeFilter(timeRange);

    try {
      const errors = await this.mcpTools.query({
        table: 'error_log',
        where: timeFilter
      });

      const distribution = {};
      errors.forEach(error => {
        const errorType = error.error_type || 'unknown';
        distribution[errorType] = (distribution[errorType] || 0) + 1;
      });

      return Object.entries(distribution).map(([type, count]) => ({
        errorType: type,
        count: count,
        percentage: parseFloat(((count / errors.length) * 100).toFixed(2))
      }));
    } catch (error) {
      logger.error('Failed to get error distribution:', error);
      return [];
    }
  }

  async getResolutionTimes(timeRange = '24h') {
    const timeFilter = this.buildTimeFilter(timeRange);

    try {
      const auditLogs = await this.mcpTools.query({
        table: 'unified_audit_log',
        where: {
          ...timeFilter,
          action: { in: ['error_resolved', 'retry_success', 'manual_fix'] }
        },
        orderBy: { timestamp: 'desc' }
      });

      const resolutionTimes = [];

      for (const log of auditLogs) {
        const processId = log.process_id;

        const originalError = await this.mcpTools.query({
          table: 'error_log',
          where: { process_id: processId },
          orderBy: { timestamp: 'asc' },
          limit: 1
        });

        if (originalError.length > 0) {
          const errorTime = new Date(originalError[0].timestamp);
          const resolvedTime = new Date(log.timestamp);
          const resolutionTimeMs = resolvedTime.getTime() - errorTime.getTime();

          resolutionTimes.push({
            processId: processId,
            errorType: originalError[0].error_type,
            errorTime: errorTime.toISOString(),
            resolvedTime: resolvedTime.toISOString(),
            resolutionTimeMs: resolutionTimeMs,
            resolutionTimeHours: parseFloat((resolutionTimeMs / (1000 * 60 * 60)).toFixed(2))
          });
        }
      }

      return resolutionTimes;
    } catch (error) {
      logger.error('Failed to calculate resolution times:', error);
      return [];
    }
  }

  groupErrorsByTime(errors, groupBy) {
    const grouped = {};

    errors.forEach(error => {
      const timestamp = new Date(error.timestamp);
      let timeKey;

      switch (groupBy) {
        case 'hour':
          timeKey = `${timestamp.getFullYear()}-${String(timestamp.getMonth() + 1).padStart(2, '0')}-${String(timestamp.getDate()).padStart(2, '0')} ${String(timestamp.getHours()).padStart(2, '0')}:00`;
          break;
        case 'day':
          timeKey = `${timestamp.getFullYear()}-${String(timestamp.getMonth() + 1).padStart(2, '0')}-${String(timestamp.getDate()).padStart(2, '0')}`;
          break;
        default:
          timeKey = timestamp.toISOString().substring(0, 13) + ':00:00Z';
      }

      grouped[timeKey] = (grouped[timeKey] || 0) + 1;
    });

    return grouped;
  }

  async getTotalProcessedForPeriod(timeKey, groupBy) {
    try {
      let startTime, endTime;

      if (groupBy === 'hour') {
        startTime = new Date(timeKey);
        endTime = new Date(startTime.getTime() + 60 * 60 * 1000);
      } else {
        startTime = new Date(timeKey);
        endTime = new Date(startTime.getTime() + 24 * 60 * 60 * 1000);
      }

      const auditLogs = await this.mcpTools.query({
        table: 'unified_audit_log',
        where: {
          timestamp: {
            '>=': startTime.toISOString(),
            '<': endTime.toISOString()
          }
        }
      });

      return auditLogs.length;
    } catch (error) {
      return 0;
    }
  }

  buildTimeFilter(timeRange) {
    const now = new Date();
    let startTime;

    switch (timeRange) {
      case '1h':
        startTime = new Date(now.getTime() - 60 * 60 * 1000);
        break;
      case '24h':
        startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        break;
      case '7d':
        startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      default:
        startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    }

    return {
      timestamp: { '>=': startTime.toISOString() }
    };
  }
}

class AuditTimelineBuilder {
  constructor(mcpTools) {
    this.mcpTools = mcpTools;
    this.eventPriority = {
      'error': 5,
      'warning': 4,
      'promotion': 3,
      'sync': 2,
      'info': 1
    };
  }

  async getAuditTimeline(timeRange = '24h', limit = 100, eventTypes = null) {
    const timeFilter = this.buildTimeFilter(timeRange);

    try {
      let query = {
        table: 'unified_audit_log',
        where: timeFilter,
        orderBy: { timestamp: 'desc' },
        limit: limit
      };

      if (eventTypes && eventTypes.length > 0) {
        query.where.action = { in: eventTypes };
      }

      const auditLogs = await this.mcpTools.query(query);

      return auditLogs.map(log => this.formatTimelineEvent(log));
    } catch (error) {
      logger.error('Failed to build audit timeline:', error);
      return [];
    }
  }

  formatTimelineEvent(log) {
    const eventType = this.categorizeEvent(log.action);
    const severity = this.getSeverity(log.action, log);

    return {
      id: log.unique_id,
      timestamp: log.timestamp,
      action: log.action,
      type: eventType,
      severity: severity,
      processId: log.process_id,
      tableName: log.table_name,
      recordId: log.record_id,
      description: this.generateDescription(log),
      details: this.parseDetails(log),
      duration: this.calculateEventDuration(log)
    };
  }

  categorizeEvent(action) {
    const eventTypeMap = {
      'company_promoted': 'promotion',
      'person_promoted': 'promotion',
      'contact_sync': 'sync',
      'enrichment_completed': 'enrichment',
      'scraping_completed': 'scraping',
      'validation_completed': 'validation',
      'intake_created': 'intake',
      'error_logged': 'error',
      'process_started': 'process',
      'process_completed': 'process'
    };

    return eventTypeMap[action] || 'info';
  }

  getSeverity(action, log) {
    if (action.includes('error') || action.includes('failed')) return 'error';
    if (action.includes('warning') || action.includes('retry')) return 'warning';
    if (action.includes('promoted') || action.includes('sync')) return 'success';
    return 'info';
  }

  generateDescription(log) {
    const actionDescriptions = {
      'company_promoted': `Company ${log.record_id} promoted to master table`,
      'person_promoted': `Person ${log.record_id} promoted to master table`,
      'contact_sync': `Contact ${log.record_id} synced to outreach platform`,
      'enrichment_completed': `Enrichment completed for ${log.record_id}`,
      'scraping_completed': `Scraping completed for ${log.record_id}`,
      'validation_completed': `Validation completed for ${log.record_id}`,
      'intake_created': `New intake record created: ${log.record_id}`,
      'error_logged': `Error occurred in process ${log.process_id}`,
      'process_started': `Process ${log.process_id} started`,
      'process_completed': `Process ${log.process_id} completed`
    };

    return actionDescriptions[log.action] || `${log.action} performed on ${log.record_id}`;
  }

  parseDetails(log) {
    try {
      return log.changes ? JSON.parse(log.changes) : {};
    } catch (error) {
      return { raw: log.changes };
    }
  }

  calculateEventDuration(log) {
    if (log.details && log.details.duration) {
      return log.details.duration;
    }
    return null;
  }

  buildTimeFilter(timeRange) {
    const now = new Date();
    let startTime;

    switch (timeRange) {
      case '1h':
        startTime = new Date(now.getTime() - 60 * 60 * 1000);
        break;
      case '24h':
        startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        break;
      case '7d':
        startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      default:
        startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    }

    return {
      timestamp: { '>=': startTime.toISOString() }
    };
  }
}

class ThroughputAnalyzer {
  constructor(mcpTools) {
    this.mcpTools = mcpTools;
  }

  async calculateThroughput(timeRange = '24h', granularity = 'hour') {
    const throughputData = [];
    const timeFilter = this.buildTimeFilter(timeRange);

    try {
      const auditLogs = await this.mcpTools.query({
        table: 'unified_audit_log',
        where: timeFilter,
        orderBy: { timestamp: 'asc' }
      });

      const groupedLogs = this.groupLogsByTime(auditLogs, granularity);

      for (const [timeKey, logs] of Object.entries(groupedLogs)) {
        const throughputMetrics = this.calculatePeriodThroughput(logs);

        throughputData.push({
          timestamp: timeKey,
          ...throughputMetrics
        });
      }

      return throughputData;
    } catch (error) {
      logger.error('Failed to calculate throughput:', error);
      return [];
    }
  }

  groupLogsByTime(logs, granularity) {
    const grouped = {};

    logs.forEach(log => {
      const timestamp = new Date(log.timestamp);
      let timeKey;

      switch (granularity) {
        case 'hour':
          timeKey = `${timestamp.getFullYear()}-${String(timestamp.getMonth() + 1).padStart(2, '0')}-${String(timestamp.getDate()).padStart(2, '0')} ${String(timestamp.getHours()).padStart(2, '0')}:00`;
          break;
        case 'day':
          timeKey = `${timestamp.getFullYear()}-${String(timestamp.getMonth() + 1).padStart(2, '0')}-${String(timestamp.getDate()).padStart(2, '0')}`;
          break;
        default:
          timeKey = timestamp.toISOString().substring(0, 13) + ':00:00Z';
      }

      if (!grouped[timeKey]) grouped[timeKey] = [];
      grouped[timeKey].push(log);
    });

    return grouped;
  }

  calculatePeriodThroughput(logs) {
    const metrics = {
      totalEvents: logs.length,
      ingested: 0,
      validated: 0,
      enriched: 0,
      scraped: 0,
      promoted: 0,
      synced: 0,
      errors: 0
    };

    logs.forEach(log => {
      const action = log.action;

      if (action.includes('intake_created')) metrics.ingested++;
      if (action.includes('validation_completed')) metrics.validated++;
      if (action.includes('enrichment_completed')) metrics.enriched++;
      if (action.includes('scraping_completed')) metrics.scraped++;
      if (action.includes('promoted')) metrics.promoted++;
      if (action.includes('sync')) metrics.synced++;
      if (action.includes('error')) metrics.errors++;
    });

    return metrics;
  }

  buildTimeFilter(timeRange) {
    const now = new Date();
    let startTime;

    switch (timeRange) {
      case '1h':
        startTime = new Date(now.getTime() - 60 * 60 * 1000);
        break;
      case '24h':
        startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        break;
      case '7d':
        startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      default:
        startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    }

    return {
      timestamp: { '>=': startTime.toISOString() }
    };
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
      process_id: data.processId || 'metrics',
      orbt_layer: 7,
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
}

export const getPipelineMetrics = onCall({
  memory: '2GiB',
  timeoutSeconds: 300
}, async (request) => {
  const { data } = request;

  try {
    await validateMCPAccess(request, 'getPipelineMetrics');

    const mcpTools = new MCPTools();
    const metricsCollector = new PipelineMetricsCollector(mcpTools);
    const timeRange = data.timeRange || '24h';

    logger.info(`Collecting pipeline metrics for time range: ${timeRange}`);

    const stageCounts = await metricsCollector.getAllStageCounts(timeRange);

    return {
      success: true,
      timeRange: timeRange,
      stageCounts: stageCounts,
      totalRecords: Object.values(stageCounts).reduce((sum, count) => sum + count, 0),
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Get pipeline metrics failed:', error);
    throw new HttpsError('internal', `Pipeline metrics failed: ${error.message}`);
  }
});

export const getErrorMetrics = onCall({
  memory: '2GiB',
  timeoutSeconds: 300
}, async (request) => {
  const { data } = request;

  try {
    await validateMCPAccess(request, 'getErrorMetrics');

    const mcpTools = new MCPTools();
    const errorAnalyzer = new ErrorMetricsAnalyzer(mcpTools);
    const timeRange = data.timeRange || '24h';
    const groupBy = data.groupBy || 'hour';

    logger.info(`Collecting error metrics for time range: ${timeRange}`);

    const [errorRates, errorDistribution, resolutionTimes] = await Promise.all([
      errorAnalyzer.getErrorRates(timeRange, groupBy),
      errorAnalyzer.getErrorDistribution(timeRange),
      errorAnalyzer.getResolutionTimes(timeRange)
    ]);

    const averageResolutionTime = resolutionTimes.length > 0
      ? resolutionTimes.reduce((sum, rt) => sum + rt.resolutionTimeHours, 0) / resolutionTimes.length
      : 0;

    return {
      success: true,
      timeRange: timeRange,
      errorRates: errorRates,
      errorDistribution: errorDistribution,
      resolutionTimes: resolutionTimes,
      averageResolutionTimeHours: parseFloat(averageResolutionTime.toFixed(2)),
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Get error metrics failed:', error);
    throw new HttpsError('internal', `Error metrics failed: ${error.message}`);
  }
});

export const getAuditTimeline = onCall({
  memory: '2GiB',
  timeoutSeconds: 300
}, async (request) => {
  const { data } = request;

  try {
    await validateMCPAccess(request, 'getAuditTimeline');

    const mcpTools = new MCPTools();
    const timelineBuilder = new AuditTimelineBuilder(mcpTools);
    const timeRange = data.timeRange || '24h';
    const limit = data.limit || 100;
    const eventTypes = data.eventTypes || null;

    logger.info(`Building audit timeline for time range: ${timeRange}`);

    const timeline = await timelineBuilder.getAuditTimeline(timeRange, limit, eventTypes);

    return {
      success: true,
      timeRange: timeRange,
      timeline: timeline,
      eventCount: timeline.length,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Get audit timeline failed:', error);
    throw new HttpsError('internal', `Audit timeline failed: ${error.message}`);
  }
});

export const getThroughputMetrics = onCall({
  memory: '2GiB',
  timeoutSeconds: 300
}, async (request) => {
  const { data } = request;

  try {
    await validateMCPAccess(request, 'getThroughputMetrics');

    const mcpTools = new MCPTools();
    const throughputAnalyzer = new ThroughputAnalyzer(mcpTools);
    const timeRange = data.timeRange || '24h';
    const granularity = data.granularity || 'hour';

    logger.info(`Calculating throughput metrics for time range: ${timeRange}`);

    const throughputData = await throughputAnalyzer.calculateThroughput(timeRange, granularity);

    const totalThroughput = throughputData.reduce((sum, period) => ({
      totalEvents: sum.totalEvents + period.totalEvents,
      ingested: sum.ingested + period.ingested,
      validated: sum.validated + period.validated,
      enriched: sum.enriched + period.enriched,
      scraped: sum.scraped + period.scraped,
      promoted: sum.promoted + period.promoted,
      synced: sum.synced + period.synced,
      errors: sum.errors + period.errors
    }), {
      totalEvents: 0, ingested: 0, validated: 0, enriched: 0,
      scraped: 0, promoted: 0, synced: 0, errors: 0
    });

    return {
      success: true,
      timeRange: timeRange,
      granularity: granularity,
      throughputData: throughputData,
      totalThroughput: totalThroughput,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Get throughput metrics failed:', error);
    throw new HttpsError('internal', `Throughput metrics failed: ${error.message}`);
  }
});

export const getDashboardSummary = onCall({
  memory: '2GiB',
  timeoutSeconds: 300
}, async (request) => {
  const { data } = request;

  try {
    await validateMCPAccess(request, 'getDashboardSummary');

    const mcpTools = new MCPTools();
    const metricsCollector = new PipelineMetricsCollector(mcpTools);
    const errorAnalyzer = new ErrorMetricsAnalyzer(mcpTools);
    const timeRange = data.timeRange || '24h';

    logger.info(`Collecting dashboard summary for time range: ${timeRange}`);

    const [stageCounts, errorDistribution] = await Promise.all([
      metricsCollector.getAllStageCounts(timeRange),
      errorAnalyzer.getErrorDistribution(timeRange)
    ]);

    const totalRecords = Object.values(stageCounts).reduce((sum, count) => sum + count, 0);
    const totalErrors = errorDistribution.reduce((sum, error) => sum + error.count, 0);
    const errorRate = totalRecords > 0 ? (totalErrors / totalRecords) * 100 : 0;

    const pipelineHealth = this.calculatePipelineHealth(stageCounts, errorRate);

    return {
      success: true,
      timeRange: timeRange,
      summary: {
        totalRecords: totalRecords,
        totalErrors: totalErrors,
        errorRate: parseFloat(errorRate.toFixed(2)),
        pipelineHealth: pipelineHealth,
        stageCounts: stageCounts
      },
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Get dashboard summary failed:', error);
    throw new HttpsError('internal', `Dashboard summary failed: ${error.message}`);
  }
});

function calculatePipelineHealth(stageCounts, errorRate) {
  const totalProcessed = stageCounts.synced || 0;
  const totalIngested = stageCounts.ingested || 0;

  const completionRate = totalIngested > 0 ? (totalProcessed / totalIngested) * 100 : 0;

  let health = 'excellent';
  if (errorRate > 10 || completionRate < 50) health = 'poor';
  else if (errorRate > 5 || completionRate < 75) health = 'fair';
  else if (errorRate > 2 || completionRate < 90) health = 'good';

  return {
    status: health,
    completionRate: parseFloat(completionRate.toFixed(2)),
    errorRate: errorRate
  };
}