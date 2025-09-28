/**
 * Doctrine Spec:
 * - Barton ID: 10.01.03.08.10000.001
 * - Altitude: 10000 (Execution Layer)
 * - Input: error data and analysis parameters
 * - Output: structured feedback reports and recommendations
 * - MCP: Composio (Neon integrated)
 */
/**
 * Feedback Loop Operations Module - Step 8 Continuous Improvement
 * Central utility for analyzing error patterns and generating feedback reports
 * Closes the loop for pipeline optimization and process improvement
 *
 * Functions:
 * - analyzeErrorPatterns(): Main error pattern analysis
 * - generateFeedbackReport(): Create structured feedback reports
 * - tagRecurringErrors(): Identify and tag error patterns
 * - calculateTrends(): Analyze error trends over time
 * - generateRecommendations(): Create actionable improvement suggestions
 */

import { StandardComposioNeonBridge } from './utils/standard-composio-neon-bridge.js';

/**
 * Generate a unique session ID for feedback analysis
 */
export function generateFeedbackSessionId(prefix = 'feedback') {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substr(2, 8);
  return `${prefix}_${timestamp}_${random}`;
}

/**
 * Calculate processing time metrics
 */
export function calculateAnalysisTime(startTime) {
  if (!startTime) return null;
  return Date.now() - startTime;
}

/**
 * Analyze error patterns from error_log and validation_failed tables
 *
 * @param {Object} options - Analysis options
 * @param {Date} [options.startDate] - Analysis period start
 * @param {Date} [options.endDate] - Analysis period end
 * @param {string[]} [options.recordTypes] - Record types to analyze
 * @param {string} [options.analysisDepth] - Analysis depth (basic, standard, deep)
 * @param {StandardComposioNeonBridge} [options.bridge] - Custom bridge instance
 * @returns {Promise<Object>} Error pattern analysis results
 */
export async function analyzeErrorPatterns(options = {}) {
  const bridge = options.bridge || new StandardComposioNeonBridge();
  const startTime = Date.now();

  try {
    // Set default analysis period (last 7 days)
    const endDate = options.endDate || new Date();
    const startDate = options.startDate || new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000);
    const recordTypes = options.recordTypes || ['company', 'people'];
    const analysisDepth = options.analysisDepth || 'standard';

    console.log(`[FEEDBACK-LOOP] Analyzing error patterns from ${startDate.toISOString()} to ${endDate.toISOString()}`);

    // Analyze validation failures
    const validationAnalysis = await analyzeValidationFailures(bridge, startDate, endDate, recordTypes);

    // Analyze audit log errors
    const auditLogAnalysis = await analyzeAuditLogErrors(bridge, startDate, endDate, recordTypes);

    // Analyze enrichment failures
    const enrichmentAnalysis = await analyzeEnrichmentFailures(bridge, startDate, endDate, recordTypes);

    // Identify recurring patterns
    const recurringPatterns = await identifyRecurringPatterns(bridge, startDate, endDate, recordTypes);

    // Calculate trends if deep analysis requested
    let trends = {};
    if (analysisDepth === 'deep') {
      trends = await calculateErrorTrends(bridge, startDate, endDate, recordTypes);
    }

    const analysisResult = {
      analysis_metadata: {
        period_start: startDate.toISOString(),
        period_end: endDate.toISOString(),
        record_types: recordTypes,
        analysis_depth: analysisDepth,
        processing_time_ms: calculateAnalysisTime(startTime),
        generated_at: new Date().toISOString()
      },
      validation_failures: validationAnalysis,
      audit_log_errors: auditLogAnalysis,
      enrichment_failures: enrichmentAnalysis,
      recurring_patterns: recurringPatterns,
      trends: trends,
      summary: {
        total_errors: validationAnalysis.total_count + auditLogAnalysis.total_count + enrichmentAnalysis.total_count,
        most_common_error: recurringPatterns.most_frequent?.error_type || 'none',
        error_categories: Object.keys(recurringPatterns.by_category || {}),
        recommendation_priority: calculatePriority(validationAnalysis, auditLogAnalysis, enrichmentAnalysis)
      }
    };

    console.log(`[FEEDBACK-LOOP] Error pattern analysis complete: ${analysisResult.summary.total_errors} errors analyzed`);
    return analysisResult;

  } catch (error) {
    console.error('[FEEDBACK-LOOP] Error pattern analysis failed:', error);
    throw new Error(`Failed to analyze error patterns: ${error.message}`);
  }
}

/**
 * Analyze validation failures from validation_failed table
 */
async function analyzeValidationFailures(bridge, startDate, endDate, recordTypes) {
  const query = `
    SELECT
      vf.error_type,
      vf.error_field,
      vf.status,
      COUNT(*) as occurrence_count,
      COUNT(DISTINCT vf.record_id) as affected_records,
      AVG(vf.attempts) as avg_attempts,
      MAX(vf.last_attempt_at) as last_seen,
      MIN(vf.created_at) as first_seen,
      ARRAY_AGG(DISTINCT vf.last_attempt_source) as attempt_sources,
      COUNT(CASE WHEN vf.status = 'fixed' THEN 1 END) as resolved_count,
      COUNT(CASE WHEN vf.status = 'escalated' THEN 1 END) as escalated_count
    FROM intake.validation_failed vf
    WHERE vf.created_at BETWEEN $1 AND $2
    GROUP BY vf.error_type, vf.error_field, vf.status
    ORDER BY occurrence_count DESC
  `;

  const result = await bridge.query(query, [startDate.toISOString(), endDate.toISOString()]);

  const analysis = {
    total_count: result.rows.reduce((sum, row) => sum + parseInt(row.occurrence_count), 0),
    unique_error_types: [...new Set(result.rows.map(row => row.error_type))],
    by_error_type: {},
    by_field: {},
    by_status: {},
    resolution_rate: 0
  };

  // Group by error type
  result.rows.forEach(row => {
    if (!analysis.by_error_type[row.error_type]) {
      analysis.by_error_type[row.error_type] = {
        total_occurrences: 0,
        affected_records: 0,
        fields: new Set(),
        avg_attempts: 0,
        resolution_rate: 0
      };
    }

    const errorData = analysis.by_error_type[row.error_type];
    errorData.total_occurrences += parseInt(row.occurrence_count);
    errorData.affected_records += parseInt(row.affected_records);
    errorData.fields.add(row.error_field);
    errorData.avg_attempts = Math.max(errorData.avg_attempts, parseFloat(row.avg_attempts));

    if (row.status === 'fixed') {
      errorData.resolution_rate = parseFloat(row.resolved_count) / parseFloat(row.occurrence_count);
    }
  });

  // Convert Sets to Arrays for JSON serialization
  Object.keys(analysis.by_error_type).forEach(errorType => {
    analysis.by_error_type[errorType].fields = Array.from(analysis.by_error_type[errorType].fields);
  });

  // Calculate overall resolution rate
  const totalResolved = result.rows.reduce((sum, row) => sum + parseInt(row.resolved_count || 0), 0);
  analysis.resolution_rate = analysis.total_count > 0 ? totalResolved / analysis.total_count : 0;

  return analysis;
}

/**
 * Analyze audit log errors from unified_audit_log table
 */
async function analyzeAuditLogErrors(bridge, startDate, endDate, recordTypes) {
  const query = `
    SELECT
      ual.step,
      ual.action,
      ual.source,
      ual.actor,
      COUNT(*) as error_count,
      COUNT(DISTINCT ual.unique_id) as affected_records,
      AVG(ual.processing_time_ms) as avg_processing_time,
      EXTRACT(EPOCH FROM (MAX(ual.timestamp) - MIN(ual.timestamp))) as time_span_seconds,
      ARRAY_AGG(DISTINCT ual.error_code) FILTER (WHERE ual.error_code IS NOT NULL) as error_codes,
      COUNT(CASE WHEN ual.retry_count > 0 THEN 1 END) as retried_count
    FROM marketing.unified_audit_log ual
    WHERE ual.timestamp BETWEEN $1 AND $2
      AND ual.status = 'failed'
      AND ual.record_type = ANY($3)
    GROUP BY ual.step, ual.action, ual.source, ual.actor
    ORDER BY error_count DESC
  `;

  const result = await bridge.query(query, [
    startDate.toISOString(),
    endDate.toISOString(),
    recordTypes
  ]);

  const analysis = {
    total_count: result.rows.reduce((sum, row) => sum + parseInt(row.error_count), 0),
    by_step: {},
    by_action: {},
    by_source: {},
    performance_issues: [],
    retry_patterns: {}
  };

  result.rows.forEach(row => {
    // Group by step
    if (!analysis.by_step[row.step]) {
      analysis.by_step[row.step] = { error_count: 0, actions: new Set() };
    }
    analysis.by_step[row.step].error_count += parseInt(row.error_count);
    analysis.by_step[row.step].actions.add(row.action);

    // Group by action
    if (!analysis.by_action[row.action]) {
      analysis.by_action[row.action] = { error_count: 0, avg_processing_time: 0 };
    }
    analysis.by_action[row.action].error_count += parseInt(row.error_count);
    analysis.by_action[row.action].avg_processing_time = parseFloat(row.avg_processing_time);

    // Identify performance issues (>5 second average processing time)
    if (parseFloat(row.avg_processing_time) > 5000) {
      analysis.performance_issues.push({
        step: row.step,
        action: row.action,
        source: row.source,
        avg_processing_time_ms: parseFloat(row.avg_processing_time),
        error_count: parseInt(row.error_count)
      });
    }

    // Track retry patterns
    const retryRate = parseInt(row.retried_count) / parseInt(row.error_count);
    if (retryRate > 0.3) { // More than 30% retry rate
      analysis.retry_patterns[`${row.step}_${row.action}`] = {
        retry_rate: retryRate,
        total_errors: parseInt(row.error_count),
        retried_errors: parseInt(row.retried_count)
      };
    }
  });

  // Convert Sets to Arrays
  Object.keys(analysis.by_step).forEach(step => {
    analysis.by_step[step].actions = Array.from(analysis.by_step[step].actions);
  });

  return analysis;
}

/**
 * Analyze enrichment failures from enrichment_audit_log
 */
async function analyzeEnrichmentFailures(bridge, startDate, endDate, recordTypes) {
  const query = `
    SELECT
      eal.action,
      eal.status,
      eal.source,
      COUNT(*) as failure_count,
      COUNT(DISTINCT eal.unique_id) as affected_records,
      AVG(eal.processing_time_ms) as avg_processing_time,
      AVG(eal.confidence_score) as avg_confidence,
      ARRAY_AGG(DISTINCT eal.fields_enriched) FILTER (WHERE eal.fields_enriched IS NOT NULL) as fields_attempted
    FROM intake.enrichment_audit_log eal
    WHERE eal.created_at BETWEEN $1 AND $2
      AND eal.status IN ('failed', 'partial')
      AND eal.unique_id LIKE ANY($3)
    GROUP BY eal.action, eal.status, eal.source
    ORDER BY failure_count DESC
  `;

  const likePatterns = recordTypes.map(type =>
    type === 'company' ? '04.04.01.%' : '04.04.02.%'
  );

  const result = await bridge.query(query, [
    startDate.toISOString(),
    endDate.toISOString(),
    likePatterns
  ]);

  const analysis = {
    total_count: result.rows.reduce((sum, row) => sum + parseInt(row.failure_count), 0),
    by_source: {},
    by_action: {},
    low_confidence_sources: [],
    slow_sources: []
  };

  result.rows.forEach(row => {
    // Group by source
    if (!analysis.by_source[row.source]) {
      analysis.by_source[row.source] = {
        failure_count: 0,
        avg_confidence: 0,
        avg_processing_time: 0,
        actions: new Set()
      };
    }
    const sourceData = analysis.by_source[row.source];
    sourceData.failure_count += parseInt(row.failure_count);
    sourceData.avg_confidence = parseFloat(row.avg_confidence);
    sourceData.avg_processing_time = parseFloat(row.avg_processing_time);
    sourceData.actions.add(row.action);

    // Track low confidence sources (< 0.5 confidence)
    if (parseFloat(row.avg_confidence) < 0.5) {
      analysis.low_confidence_sources.push({
        source: row.source,
        action: row.action,
        confidence: parseFloat(row.avg_confidence),
        failure_count: parseInt(row.failure_count)
      });
    }

    // Track slow sources (> 10 second average)
    if (parseFloat(row.avg_processing_time) > 10000) {
      analysis.slow_sources.push({
        source: row.source,
        action: row.action,
        avg_processing_time_ms: parseFloat(row.avg_processing_time),
        failure_count: parseInt(row.failure_count)
      });
    }
  });

  // Convert Sets to Arrays
  Object.keys(analysis.by_source).forEach(source => {
    analysis.by_source[source].actions = Array.from(analysis.by_source[source].actions);
  });

  return analysis;
}

/**
 * Identify recurring error patterns across all data sources
 */
async function identifyRecurringPatterns(bridge, startDate, endDate, recordTypes) {
  // Get error frequency across all sources
  const patterns = {
    most_frequent: null,
    by_category: {},
    temporal_patterns: {},
    correlation_analysis: {}
  };

  // Analyze validation error frequencies
  const validationQuery = `
    SELECT
      error_type,
      COUNT(*) as frequency,
      COUNT(DISTINCT record_id) as unique_records,
      MIN(created_at) as first_occurrence,
      MAX(created_at) as last_occurrence
    FROM intake.validation_failed
    WHERE created_at BETWEEN $1 AND $2
    GROUP BY error_type
    HAVING COUNT(*) >= 5  -- Only consider patterns with 5+ occurrences
    ORDER BY frequency DESC
  `;

  const validationResult = await bridge.query(validationQuery, [
    startDate.toISOString(),
    endDate.toISOString()
  ]);

  if (validationResult.rows.length > 0) {
    patterns.most_frequent = {
      error_type: validationResult.rows[0].error_type,
      frequency: parseInt(validationResult.rows[0].frequency),
      unique_records: parseInt(validationResult.rows[0].unique_records),
      source: 'validation_failed'
    };

    // Categorize errors
    validationResult.rows.forEach(row => {
      const category = categorizeError(row.error_type);
      if (!patterns.by_category[category]) {
        patterns.by_category[category] = [];
      }
      patterns.by_category[category].push({
        error_type: row.error_type,
        frequency: parseInt(row.frequency),
        unique_records: parseInt(row.unique_records)
      });
    });
  }

  return patterns;
}

/**
 * Calculate error trends over time
 */
async function calculateErrorTrends(bridge, startDate, endDate, recordTypes) {
  const trends = {
    daily_trends: {},
    weekly_trends: {},
    error_type_trends: {}
  };

  // Daily error count trends
  const dailyQuery = `
    SELECT
      DATE(created_at) as error_date,
      error_type,
      COUNT(*) as daily_count
    FROM intake.validation_failed
    WHERE created_at BETWEEN $1 AND $2
    GROUP BY DATE(created_at), error_type
    ORDER BY error_date DESC, daily_count DESC
  `;

  const dailyResult = await bridge.query(dailyQuery, [
    startDate.toISOString(),
    endDate.toISOString()
  ]);

  dailyResult.rows.forEach(row => {
    const date = row.error_date;
    if (!trends.daily_trends[date]) {
      trends.daily_trends[date] = { total: 0, by_type: {} };
    }
    trends.daily_trends[date].total += parseInt(row.daily_count);
    trends.daily_trends[date].by_type[row.error_type] = parseInt(row.daily_count);
  });

  return trends;
}

/**
 * Categorize error types for analysis
 */
function categorizeError(errorType) {
  const categories = {
    'data_quality': ['missing_state', 'invalid_state', 'bad_phone_format', 'invalid_phone'],
    'url_validation': ['invalid_url', 'bad_url_format', 'missing_protocol', 'website_not_found'],
    'social_media': ['invalid_linkedin', 'missing_linkedin', 'linkedin_not_found'],
    'system_issues': ['enrichment_timeout', 'api_rate_limits', 'db_connection_error'],
    'format_issues': ['bad_csv_format', 'complex_validation_failure'],
    'business_data': ['missing_ein', 'missing_permit', 'missing_revenue']
  };

  for (const [category, errors] of Object.entries(categories)) {
    if (errors.some(error => errorType.includes(error))) {
      return category;
    }
  }

  return 'uncategorized';
}

/**
 * Calculate overall priority based on error analysis
 */
function calculatePriority(validationAnalysis, auditLogAnalysis, enrichmentAnalysis) {
  const totalErrors = validationAnalysis.total_count + auditLogAnalysis.total_count + enrichmentAnalysis.total_count;

  if (totalErrors > 1000) return 'critical';
  if (totalErrors > 500) return 'high';
  if (totalErrors > 100) return 'medium';
  return 'low';
}

/**
 * Generate structured feedback report
 *
 * @param {Object} errorAnalysis - Results from analyzeErrorPatterns()
 * @param {Object} options - Report options
 * @returns {Promise<Object>} Generated feedback report
 */
export async function generateFeedbackReport(errorAnalysis, options = {}) {
  const bridge = options.bridge || new StandardComposioNeonBridge();
  const startTime = Date.now();

  try {
    const reportId = await generateReportId(bridge);
    const reportName = options.reportName || `Error Analysis Report - ${new Date().toISOString().split('T')[0]}`;
    const reportType = options.reportType || 'weekly';
    const generatedBy = options.generatedBy || 'feedback_system';

    // Generate recommendations based on error analysis
    const recommendations = await generateRecommendations(errorAnalysis);

    // Create human-readable summary
    const executiveSummary = generateExecutiveSummary(errorAnalysis, recommendations);
    const detailedFindings = generateDetailedFindings(errorAnalysis);

    // Tag patterns
    const tags = await tagErrorPatterns(errorAnalysis, bridge);

    const feedbackReport = {
      report_id: reportId,
      report_name: reportName,
      report_type: reportType,
      report_period_start: errorAnalysis.analysis_metadata.period_start,
      report_period_end: errorAnalysis.analysis_metadata.period_end,
      generated_by: generatedBy,
      generation_trigger: options.trigger || 'scheduled_analysis',
      data_sources: ['unified_audit_log', 'validation_failed', 'enrichment_audit_log'],
      record_types: errorAnalysis.analysis_metadata.record_types,
      total_records_analyzed: calculateTotalRecords(errorAnalysis),
      analysis_depth: errorAnalysis.analysis_metadata.analysis_depth,

      // Error pattern analysis
      error_patterns: errorAnalysis,
      recurring_errors: errorAnalysis.recurring_patterns,
      error_trends: errorAnalysis.trends,
      critical_issues: identifyCriticalIssues(errorAnalysis),

      // Performance metrics
      total_errors_found: errorAnalysis.summary.total_errors,
      error_categories_count: errorAnalysis.summary.error_categories.length,

      // Actionable insights
      recommendations: recommendations,
      quick_wins: recommendations.immediate || [],
      long_term_improvements: recommendations.strategic || [],

      // Human-readable report
      executive_summary: executiveSummary,
      detailed_findings: detailedFindings,
      methodology_notes: generateMethodologyNotes(errorAnalysis),

      // Tags and metadata
      tags: tags,
      priority_level: errorAnalysis.summary.recommendation_priority,
      follow_up_required: shouldRequireFollowUp(errorAnalysis),
      follow_up_by: calculateFollowUpDate(errorAnalysis.summary.recommendation_priority),

      // Status
      status: 'generated',

      // Barton Doctrine
      altitude: 10000,
      doctrine: 'STAMPED',
      doctrine_version: 'v2.1.0',
      session_id: options.sessionId || generateFeedbackSessionId(),
      correlation_id: options.correlationId
    };

    console.log(`[FEEDBACK-LOOP] Generated feedback report: ${reportId} with ${errorAnalysis.summary.total_errors} errors analyzed`);
    return feedbackReport;

  } catch (error) {
    console.error('[FEEDBACK-LOOP] Failed to generate feedback report:', error);
    throw new Error(`Failed to generate feedback report: ${error.message}`);
  }
}

/**
 * Save feedback report to database
 */
export async function saveFeedbackReport(report, options = {}) {
  const bridge = options.bridge || new StandardComposioNeonBridge();

  try {
    const query = `
      INSERT INTO marketing.feedback_reports (
        report_id, report_name, report_type, report_period_start, report_period_end,
        generated_by, generation_trigger, data_sources, record_types, total_records_analyzed,
        analysis_depth, error_patterns, recurring_errors, error_trends, critical_issues,
        total_errors_found, error_categories_count, recommendations, quick_wins,
        long_term_improvements, executive_summary, detailed_findings, methodology_notes,
        tags, priority_level, follow_up_required, follow_up_by, status,
        altitude, doctrine, doctrine_version, session_id, correlation_id
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
        $21, $22, $23, $24, $25, $26, $27, $28, $29, $30,
        $31, $32, $33
      ) RETURNING id
    `;

    const params = [
      report.report_id,
      report.report_name,
      report.report_type,
      report.report_period_start,
      report.report_period_end,
      report.generated_by,
      report.generation_trigger,
      report.data_sources,
      report.record_types,
      report.total_records_analyzed,
      report.analysis_depth,
      JSON.stringify(report.error_patterns),
      JSON.stringify(report.recurring_errors),
      JSON.stringify(report.error_trends),
      JSON.stringify(report.critical_issues),
      report.total_errors_found,
      report.error_categories_count,
      JSON.stringify(report.recommendations),
      report.quick_wins,
      report.long_term_improvements,
      report.executive_summary,
      report.detailed_findings,
      report.methodology_notes,
      report.tags,
      report.priority_level,
      report.follow_up_required,
      report.follow_up_by,
      report.status,
      report.altitude,
      report.doctrine,
      report.doctrine_version,
      report.session_id,
      report.correlation_id
    ];

    const result = await bridge.query(query, params);

    if (result.rows && result.rows.length > 0) {
      console.log(`[FEEDBACK-LOOP] Saved feedback report to database: ${report.report_id}`);
      return {
        success: true,
        report_id: report.report_id,
        internal_id: result.rows[0].id,
        message: 'Feedback report saved successfully'
      };
    } else {
      throw new Error('No result returned from database insertion');
    }

  } catch (error) {
    console.error('[FEEDBACK-LOOP] Failed to save feedback report:', error);
    throw new Error(`Failed to save feedback report: ${error.message}`);
  }
}

/**
 * Helper functions for report generation
 */

async function generateReportId(bridge) {
  // Use database function to generate Barton ID
  const result = await bridge.query('SELECT generate_barton_id() as report_id');
  return result.rows[0].report_id;
}

async function generateRecommendations(errorAnalysis) {
  const recommendations = {
    immediate: [],
    short_term: [],
    strategic: []
  };

  // Immediate fixes based on validation failures
  if (errorAnalysis.validation_failures.total_count > 0) {
    const topErrors = Object.entries(errorAnalysis.validation_failures.by_error_type)
      .sort((a, b) => b[1].total_occurrences - a[1].total_occurrences)
      .slice(0, 3);

    topErrors.forEach(([errorType, data]) => {
      if (errorType.includes('phone')) {
        recommendations.immediate.push('Implement phone number validation and E.164 formatting in data ingestion');
      } else if (errorType.includes('url')) {
        recommendations.immediate.push('Add URL protocol validation and auto-correction in preprocessing');
      } else if (errorType.includes('state')) {
        recommendations.immediate.push('Create state code normalization lookup table for address validation');
      }
    });
  }

  // Performance recommendations
  if (errorAnalysis.audit_log_errors.performance_issues.length > 0) {
    recommendations.short_term.push('Optimize slow-performing operations identified in audit log');
    recommendations.short_term.push('Implement caching for frequently accessed validation rules');
  }

  // Strategic improvements
  if (errorAnalysis.summary.total_errors > 500) {
    recommendations.strategic.push('Implement machine learning-based error prediction and prevention');
    recommendations.strategic.push('Develop automated data quality scoring system');
  }

  return recommendations;
}

function generateExecutiveSummary(errorAnalysis, recommendations) {
  const totalErrors = errorAnalysis.summary.total_errors;
  const period = `${errorAnalysis.analysis_metadata.period_start.split('T')[0]} to ${errorAnalysis.analysis_metadata.period_end.split('T')[0]}`;

  return `During the period ${period}, the system processed data with ${totalErrors} total errors identified across validation, enrichment, and processing stages. ` +
    `The most common error pattern was ${errorAnalysis.summary.most_common_error}, indicating potential improvements in data quality processes. ` +
    `${recommendations.immediate.length} immediate fixes and ${recommendations.strategic.length} strategic improvements have been identified. ` +
    `Priority level: ${errorAnalysis.summary.recommendation_priority}.`;
}

function generateDetailedFindings(errorAnalysis) {
  let findings = "DETAILED ERROR ANALYSIS FINDINGS:\n\n";

  findings += `1. VALIDATION FAILURES (${errorAnalysis.validation_failures.total_count} total):\n`;
  Object.entries(errorAnalysis.validation_failures.by_error_type).forEach(([errorType, data]) => {
    findings += `   - ${errorType}: ${data.total_occurrences} occurrences affecting ${data.affected_records} records\n`;
  });

  findings += `\n2. AUDIT LOG ERRORS (${errorAnalysis.audit_log_errors.total_count} total):\n`;
  Object.entries(errorAnalysis.audit_log_errors.by_step).forEach(([step, data]) => {
    findings += `   - ${step}: ${data.error_count} errors in actions: ${data.actions.join(', ')}\n`;
  });

  if (errorAnalysis.audit_log_errors.performance_issues.length > 0) {
    findings += `\n3. PERFORMANCE ISSUES:\n`;
    errorAnalysis.audit_log_errors.performance_issues.forEach(issue => {
      findings += `   - ${issue.step}/${issue.action}: ${Math.round(issue.avg_processing_time_ms)}ms average\n`;
    });
  }

  return findings;
}

function generateMethodologyNotes(errorAnalysis) {
  return `Analysis conducted using ${errorAnalysis.analysis_metadata.analysis_depth} depth methodology. ` +
    `Data sources included: ${errorAnalysis.analysis_metadata.record_types.join(', ')} records. ` +
    `Processing time: ${errorAnalysis.analysis_metadata.processing_time_ms}ms. ` +
    `Error pattern recognition based on frequency analysis and temporal correlation.`;
}

async function tagErrorPatterns(errorAnalysis, bridge) {
  const tags = [];

  // Add automatic tags based on error patterns
  if (errorAnalysis.validation_failures.total_count > 100) {
    tags.push('high_validation_failure_rate');
  }

  if (errorAnalysis.audit_log_errors.performance_issues.length > 0) {
    tags.push('performance_issues_detected');
  }

  if (errorAnalysis.enrichment_failures.low_confidence_sources.length > 0) {
    tags.push('low_confidence_enrichment');
  }

  // Add error category tags
  Object.keys(errorAnalysis.recurring_patterns.by_category || {}).forEach(category => {
    tags.push(`error_category_${category}`);
  });

  return tags;
}

function identifyCriticalIssues(errorAnalysis) {
  const critical = {};

  // System-level issues
  if (errorAnalysis.audit_log_errors.total_count > errorAnalysis.validation_failures.total_count * 0.5) {
    critical.system_stability = {
      severity: 'high',
      description: 'High ratio of system errors compared to validation errors',
      impact: 'Processing reliability',
      recommended_action: 'Investigate system stability and error handling'
    };
  }

  // Data quality issues
  if (errorAnalysis.validation_failures.resolution_rate < 0.3) {
    critical.data_quality = {
      severity: 'medium',
      description: 'Low validation error resolution rate',
      impact: 'Data completeness and accuracy',
      recommended_action: 'Improve validation rules and error handling workflows'
    };
  }

  return critical;
}

function calculateTotalRecords(errorAnalysis) {
  // Estimate based on error data - this would be more accurate with additional queries
  return Math.max(
    errorAnalysis.validation_failures.total_count,
    errorAnalysis.audit_log_errors.total_count,
    errorAnalysis.enrichment_failures.total_count
  ) * 10; // Rough estimate
}

function shouldRequireFollowUp(errorAnalysis) {
  return errorAnalysis.summary.recommendation_priority === 'critical' ||
         errorAnalysis.summary.recommendation_priority === 'high';
}

function calculateFollowUpDate(priority) {
  const now = new Date();
  switch (priority) {
    case 'critical':
      return new Date(now.getTime() + 24 * 60 * 60 * 1000); // 1 day
    case 'high':
      return new Date(now.getTime() + 3 * 24 * 60 * 60 * 1000); // 3 days
    case 'medium':
      return new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000); // 1 week
    default:
      return new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000); // 2 weeks
  }
}

/**
 * Get recent feedback reports
 */
export async function getRecentFeedbackReports(options = {}) {
  const bridge = options.bridge || new StandardComposioNeonBridge();
  const limit = options.limit || 10;

  try {
    const query = `
      SELECT * FROM marketing.recent_feedback_reports
      ORDER BY created_at DESC
      LIMIT $1
    `;

    const result = await bridge.query(query, [limit]);

    return {
      success: true,
      reports: result.rows || [],
      total: result.rows ? result.rows.length : 0
    };

  } catch (error) {
    console.error('[FEEDBACK-LOOP] Failed to get recent reports:', error);
    return {
      success: false,
      error: 'Failed to retrieve recent feedback reports',
      reports: [],
      total: 0
    };
  }
}

/**
 * Get error pattern trends
 */
export async function getErrorPatternTrends(options = {}) {
  const bridge = options.bridge || new StandardComposioNeonBridge();

  try {
    const query = `
      SELECT * FROM marketing.error_pattern_trends
      ORDER BY occurrence_count DESC, last_seen DESC
    `;

    const result = await bridge.query(query);

    return {
      success: true,
      trends: result.rows || [],
      total: result.rows ? result.rows.length : 0
    };

  } catch (error) {
    console.error('[FEEDBACK-LOOP] Failed to get error trends:', error);
    return {
      success: false,
      error: 'Failed to retrieve error pattern trends',
      trends: [],
      total: 0
    };
  }
}

// Default export for convenience
export default {
  analyzeErrorPatterns,
  generateFeedbackReport,
  saveFeedbackReport,
  getRecentFeedbackReports,
  getErrorPatternTrends,
  generateFeedbackSessionId,
  calculateAnalysisTime
};