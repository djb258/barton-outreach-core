/**
 * History MCP Client for Data Provenance Tracking
 * Doctrine Spec:
 * - Barton ID: 99.99.99.07.XXXXX.XXX
 * - Altitude: 10000 (History Layer)
 * - Input: field discovery events and metadata
 * - Output: history tracking and deduplication decisions
 * - MCP: Composio (Firebase + Neon integrated)
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

class HistoryMCPClient {
  constructor() {
    this.mcpServerPath = path.join(process.cwd(), 'mcp-servers', 'github-composio-server.js');
    this.composioApiKey = process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn';
    this.neonConnectionId = process.env.NEON_CONNECTION_ID || 'neon_barton_outreach';
    this.firebaseProjectId = process.env.FIREBASE_PROJECT_ID || 'barton-outreach-core';
  }

  /**
   * Execute Composio MCP command for history operations
   */
  async executeMCPCommand(tool, params) {
    try {
      const mcpRequest = {
        tool: `history.${tool}`,
        params: {
          connectionId: this.neonConnectionId,
          firebaseProject: this.firebaseProjectId,
          ...params
        },
        metadata: {
          timestamp: new Date().toISOString(),
          processId: this.generateProcessId(),
          altitude: 'history_layer',
          unique_id: this.generateBartonId()
        }
      };

      const response = await this.callMCPServer(mcpRequest);
      return response;
    } catch (error) {
      console.error(`History MCP Command Error (${tool}):`, error);
      throw new Error(`Failed to execute history MCP command ${tool}: ${error.message}`);
    }
  }

  /**
   * Call MCP server with request (would connect to actual MCP server in production)
   */
  async callMCPServer(request) {
    // Production implementation would use actual MCP protocol
    return {
      success: true,
      data: request.params,
      metadata: request.metadata,
      tool: request.tool
    };
  }

  /**
   * Add company history entry through MCP (dual storage: Firebase + Neon)
   */
  async addCompanyHistoryEntry(companyId, field, value, source, options = {}) {
    const historyEntry = {
      company_id: companyId,
      field: field,
      value_found: value,
      source: source,
      confidence_score: options.confidenceScore || 1.0,
      process_id: options.processId || this.generateProcessId(),
      session_id: options.sessionId,
      previous_value: options.previousValue,
      change_reason: options.changeReason || 'initial_discovery',
      metadata: options.metadata || {}
    };

    const params = {
      table: 'company_history.discovery_log',
      collection: 'company_history',
      entry: historyEntry,
      dualWrite: true, // Write to both Firebase and Neon
      deduplicationCheck: true
    };

    return await this.executeMCPCommand('add_company_entry', params);
  }

  /**
   * Add person history entry through MCP (dual storage: Firebase + Neon)
   */
  async addPersonHistoryEntry(personId, field, value, source, options = {}) {
    const historyEntry = {
      person_id: personId,
      field: field,
      value_found: value,
      source: source,
      confidence_score: options.confidenceScore || 1.0,
      process_id: options.processId || this.generateProcessId(),
      session_id: options.sessionId,
      previous_value: options.previousValue,
      change_reason: options.changeReason || 'initial_discovery',
      related_company_id: options.relatedCompanyId,
      metadata: options.metadata || {}
    };

    const params = {
      table: 'person_history.discovery_log',
      collection: 'person_history',
      entry: historyEntry,
      dualWrite: true, // Write to both Firebase and Neon
      deduplicationCheck: true
    };

    return await this.executeMCPCommand('add_person_entry', params);
  }

  /**
   * Check if field was discovered recently to avoid redundant scraping
   */
  async checkFieldDiscovered(entityId, field, entityType = 'company', hoursThreshold = 24) {
    const params = {
      entity_id: entityId,
      field: field,
      entity_type: entityType, // 'company' or 'person'
      hours_threshold: hoursThreshold,
      source: 'firebase' // Check Firebase first for speed
    };

    return await this.executeMCPCommand('check_field_discovered', params);
  }

  /**
   * Get latest discovered value for a field
   */
  async getLatestFieldValue(entityId, field, entityType = 'company') {
    const params = {
      entity_id: entityId,
      field: field,
      entity_type: entityType,
      include_metadata: true
    };

    return await this.executeMCPCommand('get_latest_value', params);
  }

  /**
   * Get history timeline for an entity
   */
  async getHistoryTimeline(entityId, entityType = 'company', options = {}) {
    const params = {
      entity_id: entityId,
      entity_type: entityType,
      field: options.field, // Optional field filter
      limit: options.limit || 50,
      source: options.source, // Optional source filter
      include_metadata: true
    };

    return await this.executeMCPCommand('get_history_timeline', params);
  }

  /**
   * Batch add multiple history entries (for bulk operations)
   */
  async batchAddHistoryEntries(entries, entityType = 'company') {
    const params = {
      entity_type: entityType,
      entries: entries.map(entry => ({
        ...entry,
        unique_id: this.generateBartonId(),
        process_id: entry.process_id || this.generateProcessId(),
        confidence_score: entry.confidence_score || 1.0,
        change_reason: entry.change_reason || 'initial_discovery'
      })),
      dualWrite: true,
      batchSize: 100
    };

    return await this.executeMCPCommand('batch_add_entries', params);
  }

  /**
   * Get discovery statistics for analysis
   */
  async getDiscoveryStats(entityId, entityType = 'company', daysBack = 30) {
    const params = {
      entity_id: entityId,
      entity_type: entityType,
      days_back: daysBack,
      include_source_breakdown: true,
      include_confidence_analysis: true
    };

    return await this.executeMCPCommand('get_discovery_stats', params);
  }

  /**
   * Deduplicate values and return recommendation
   */
  async deduplicateFieldValues(entityId, field, entityType = 'company') {
    const params = {
      entity_id: entityId,
      field: field,
      entity_type: entityType,
      confidence_threshold: 0.8,
      include_reasoning: true
    };

    return await this.executeMCPCommand('deduplicate_values', params);
  }

  /**
   * Get source reliability report
   */
  async getSourceReliabilityReport(source, daysBack = 30) {
    const params = {
      source: source,
      days_back: daysBack,
      include_confidence_breakdown: true,
      include_verification_stats: true
    };

    return await this.executeMCPCommand('get_source_report', params);
  }

  /**
   * Archive old history entries to Neon vault
   */
  async archiveToVault(daysOld = 90) {
    const params = {
      days_old: daysOld,
      archive_to_neon: true,
      cleanup_firebase: true,
      verify_archive: true
    };

    return await this.executeMCPCommand('archive_to_vault', params);
  }

  /**
   * Validate history entry before insertion
   */
  async validateHistoryEntry(entry, entityType = 'company') {
    const params = {
      entry: entry,
      entity_type: entityType,
      validation_rules: {
        check_required_fields: true,
        check_field_enum: true,
        check_source_enum: true,
        check_confidence_range: true,
        check_id_format: true
      }
    };

    return await this.executeMCPCommand('validate_entry', params);
  }

  /**
   * Generate Barton ID for history entries
   */
  generateBartonId() {
    const timestamp = Date.now();
    const segment1 = String(timestamp % 100).padStart(2, '0');
    const segment2 = String((timestamp >> 8) % 100).padStart(2, '0');
    const segment3 = String(Math.floor(Math.random() * 100)).padStart(2, '0');
    const segment4 = '07'; // Database record designation
    const segment5 = String(Math.floor(Math.random() * 100000)).padStart(5, '0');
    const segment6 = String(Math.floor(Math.random() * 1000)).padStart(3, '0');

    return `${segment1}.${segment2}.${segment3}.${segment4}.${segment5}.${segment6}`;
  }

  /**
   * Generate process ID for tracking
   */
  generateProcessId() {
    return `HIST-${Date.now()}-${Math.random().toString(36).substr(2, 5).toUpperCase()}`;
  }

  /**
   * Calculate confidence score based on source and validation
   */
  calculateConfidenceScore(source, validationResults = {}) {
    const sourceConfidence = {
      'manual_input': 1.0,
      'csv_import': 0.9,
      'apollo': 0.95,
      'clearbit': 0.9,
      'linkedin_scraper': 0.85,
      'apify': 0.8,
      'hunter_io': 0.85,
      'millionverify': 0.9,
      'enrichment_api': 0.75,
      'web_scraper': 0.7,
      'api_integration': 0.8
    };

    let baseScore = sourceConfidence[source] || 0.5;

    // Adjust based on validation results
    if (validationResults.email_verified === true) baseScore += 0.1;
    if (validationResults.phone_verified === true) baseScore += 0.1;
    if (validationResults.domain_verified === true) baseScore += 0.05;

    return Math.min(baseScore, 1.0);
  }

  /**
   * Format validation errors for debugging
   */
  formatValidationErrors(validationResult) {
    if (!validationResult || !validationResult.errors) {
      return [];
    }

    return validationResult.errors.map(error => ({
      field: error.field,
      message: error.message,
      severity: error.severity || 'error',
      code: error.code,
      suggested_fix: error.suggested_fix
    }));
  }

  /**
   * Check system health for history operations
   */
  async checkSystemHealth() {
    const params = {
      check_firebase_connection: true,
      check_neon_connection: true,
      check_mcp_server: true,
      check_recent_operations: true
    };

    return await this.executeMCPCommand('system_health', params);
  }
}

export default HistoryMCPClient;