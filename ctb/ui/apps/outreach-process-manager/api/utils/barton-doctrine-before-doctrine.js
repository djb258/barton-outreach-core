/**
 * Barton Doctrine Utilities
 * Handles unique_id, process_id, and altitude metadata
 * Ensures compliance with STAMPED doctrine
 */

class BartonDoctrineUtils {
  /**
   * Generate unique ID with BTN prefix
   */
  static generateUniqueId(prefix = 'BTN') {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substr(2, 9).toUpperCase();
    return `${prefix}_${timestamp}_${random}`;
  }

  /**
   * Generate process ID for tracking
   */
  static generateProcessId(type = 'PROC') {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substr(2, 5).toUpperCase();
    const date = new Date().toISOString().split('T')[0].replace(/-/g, '');
    return `${type}_${date}_${timestamp}_${random}`;
  }

  /**
   * Generate step ID for sub-processes
   */
  static generateStepId(processId, stepName) {
    const random = Math.random().toString(36).substr(2, 4).toUpperCase();
    return `${processId}_${stepName.toUpperCase()}_${random}`;
  }

  /**
   * Get altitude level based on data state
   */
  static getAltitude(stage) {
    const altitudes = {
      'raw': 'ground_level',
      'raw_intake': 'low_altitude',
      'validated': 'mid_altitude',
      'production': 'high_altitude',
      'promoted': 'cruising_altitude',
      'archived': 'stratosphere'
    };

    return altitudes[stage] || 'unknown_altitude';
  }

  /**
   * Create Barton Doctrine metadata object
   */
  static createMetadata(options = {}) {
    const processId = options.processId || this.generateProcessId();

    return {
      unique_id: options.uniqueId || this.generateUniqueId(),
      process_id: processId,
      altitude: options.altitude || this.getAltitude('raw'),
      timestamp: new Date().toISOString(),
      source: options.source || 'middle_layer',
      version: options.version || '1.0.0',
      doctrine_compliant: true,
      stamped: {
        s: options.source || 'system',           // Source
        t: new Date().toISOString(),             // Timestamp
        a: options.actor || 'orchestrator',      // Actor
        m: options.method || 'composio_mcp',     // Method
        p: processId,                             // Process
        e: options.environment || 'production',   // Environment
        d: options.data || {}                     // Data
      }
    };
  }

  /**
   * Validate Barton Doctrine compliance
   */
  static validateCompliance(data) {
    const required = ['unique_id', 'process_id', 'altitude', 'timestamp'];
    const missing = [];

    required.forEach(field => {
      if (!data[field]) {
        missing.push(field);
      }
    });

    return {
      compliant: missing.length === 0,
      missing_fields: missing,
      validation_timestamp: new Date().toISOString()
    };
  }

  /**
   * Add tracking metadata to rows
   */
  static addTrackingToRows(rows, processId) {
    return rows.map((row, index) => ({
      ...row,
      unique_id: row.unique_id || this.generateUniqueId(),
      process_id: processId,
      row_index: index,
      ingestion_timestamp: new Date().toISOString(),
      altitude: this.getAltitude('raw_intake'),
      doctrine_metadata: this.createMetadata({
        processId,
        source: 'csv_import',
        altitude: 'raw_intake'
      })
    }));
  }

  /**
   * Generate audit trail entry
   */
  static createAuditEntry(action, data = {}) {
    return {
      audit_id: this.generateUniqueId('AUDIT'),
      action,
      timestamp: new Date().toISOString(),
      process_id: data.processId || this.generateProcessId(),
      actor: data.actor || 'system',
      details: data.details || {},
      altitude: data.altitude || 'audit_layer',
      success: data.success !== false,
      error: data.error || null
    };
  }

  /**
   * Calculate processing metrics
   */
  static calculateMetrics(startTime, endTime = Date.now()) {
    const duration = endTime - startTime;

    return {
      processing_time_ms: duration,
      processing_time_seconds: (duration / 1000).toFixed(2),
      performance_grade: this.getPerformanceGrade(duration)
    };
  }

  /**
   * Get performance grade based on processing time
   */
  static getPerformanceGrade(durationMs) {
    if (durationMs < 100) return 'A+';
    if (durationMs < 500) return 'A';
    if (durationMs < 1000) return 'B';
    if (durationMs < 3000) return 'C';
    if (durationMs < 5000) return 'D';
    return 'F';
  }

  /**
   * Create response with full Barton Doctrine metadata
   */
  static createDoctrineResponse(data, options = {}) {
    const processId = options.processId || this.generateProcessId();
    const startTime = options.startTime || Date.now();

    return {
      ...data,
      barton_doctrine: {
        process_id: processId,
        unique_id: this.generateUniqueId('RESP'),
        altitude: options.altitude || 'middle_layer',
        timestamp: new Date().toISOString(),
        ...this.calculateMetrics(startTime),
        compliance: this.validateCompliance(data),
        stamped: this.createMetadata({
          processId,
          altitude: options.altitude
        }).stamped
      }
    };
  }
}

export default BartonDoctrineUtils;