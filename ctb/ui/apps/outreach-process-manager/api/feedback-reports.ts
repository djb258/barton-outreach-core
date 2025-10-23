/**
 * Doctrine Spec:
 * - Barton ID: 99.99.99.08.14292.720
 * - Altitude: 10000 (Execution Layer)
 * - Input: feedback report requests and management operations
 * - Output: feedback reports, pattern analysis, and operation results
 * - MCP: Composio (Neon integrated)
 */
/**
 * Step 8 Feedback Loop API - Barton Doctrine Pipeline
 * Input: { action: "generate" | "list" | "get" | "update", ...params }
 * Output: Feedback reports, error pattern analysis, and management results
 *
 * Workflow:
 * 1. Generate: Create new feedback reports using feedbackLoopOperations
 * 2. List: Retrieve existing reports with filters
 * 3. Get: Fetch specific report details
 * 4. Update: Modify report status or actions
 *
 * Barton Doctrine Rules:
 * - All operations logged to unified_audit_log
 * - Session tracking for all feedback operations
 * - Uses Standard Composio MCP pattern for all database operations
 * - Error pattern analysis follows standardized tagging system
 * - Reports include actionable recommendations with priority scoring
 */

import { composioRequest } from '../utils/composio-client.js';
import { generateSessionId, calculateProcessingTime } from './auditOperations.js';

interface FeedbackReportRequest {
  action: 'generate' | 'list' | 'get' | 'update' | 'patterns';
  timeframe_days?: number;
  report_type?: 'validation_errors' | 'enrichment_gaps' | 'data_quality' | 'full_analysis';
  analysis_depth?: 'summary' | 'detailed' | 'comprehensive';
  report_id?: string;
  status?: string;
  filters?: {
    error_category?: string;
    source_system?: string;
    created_after?: string;
    created_before?: string;
  };
}

interface FeedbackReportResponse {
  success: boolean;
  data?: any;
  message?: string;
  session_id: string;
  processing_time_ms: number;
  audit_log_id?: number;
}

export default async function handler(req: any, res: any) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const sessionId = generateSessionId('feedback_reports');
  const startTime = Date.now();

  try {
    const {
      action,
      timeframe_days = 7,
      report_type = 'full_analysis',
      analysis_depth = 'detailed',
      report_id,
      status,
      filters = {}
    }: FeedbackReportRequest = req.body;

    if (!action || !['generate', 'list', 'get', 'update', 'patterns'].includes(action)) {
      return res.status(400).json({
        success: false,
        message: 'Invalid or missing action parameter. Must be "generate", "list", "get", "update", or "patterns"',
        session_id: sessionId,
        processing_time_ms: calculateProcessingTime(startTime)
      });
    }

    console.log(`[FEEDBACK-REPORTS] Starting ${action} operation (session: ${sessionId})`);

    // Prepare Composio request payload
    const composioPayload = {
      tool: 'feedback_loop_operations',
      data: {
        action,
        timeframe_days,
        report_type,
        analysis_depth,
        report_id,
        status,
        filters,
        session_id: sessionId
      },
      unique_id: `HEIR-2025-09-FEEDBACK-${Date.now()}`,
      process_id: 'step_8_feedback_loop',
      orbt_layer: 10000,
      blueprint_version: '1.0'
    };

    console.log(`[FEEDBACK-REPORTS] Sending to Composio MCP:`, composioPayload);

    // Execute via Composio MCP
    const result = await composioRequest(composioPayload);

    if (!result.success) {
      throw new Error(`Composio operation failed: ${result.error || 'Unknown error'}`);
    }

    // Log to unified audit trail via Composio
    const auditPayload = {
      tool: 'audit_operations',
      data: {
        entity_type: 'feedback_reports',
        entity_id: result.data?.report_id || 'bulk_operation',
        action: `feedback_${action}`,
        status: 'success',
        source: 'feedback_reports_api',
        details: {
          action,
          timeframe_days,
          report_type,
          analysis_depth,
          filters,
          result_summary: result.data?.summary || {}
        },
        altitude: 10000,
        process_id: 'step_8_feedback_loop',
        session_id: sessionId
      },
      unique_id: `HEIR-2025-09-AUDIT-${Date.now()}`,
      process_id: 'step_8_feedback_loop',
      orbt_layer: 10000,
      blueprint_version: '1.0'
    };

    const auditResult = await composioRequest(auditPayload);

    const response: FeedbackReportResponse = {
      success: true,
      data: result.data,
      session_id: sessionId,
      processing_time_ms: calculateProcessingTime(startTime),
      audit_log_id: auditResult.data?.audit_log_id
    };

    console.log(`[FEEDBACK-REPORTS] ${action} completed successfully (session: ${sessionId})`);
    return res.status(200).json(response);

  } catch (error: any) {
    console.error('[FEEDBACK-REPORTS] Operation failed:', error);

    // Log error to unified audit trail via Composio
    try {
      const errorAuditPayload = {
        tool: 'audit_operations',
        data: {
          entity_type: 'feedback_reports',
          entity_id: 'error_operation',
          action: 'feedback_operation_failed',
          status: 'failed',
          source: 'feedback_reports_api',
          details: {
            error_message: error.message,
            error_stack: error.stack,
            request_body: req.body
          },
          altitude: 10000,
          process_id: 'step_8_feedback_loop',
          session_id: sessionId
        },
        unique_id: `HEIR-2025-09-ERROR-${Date.now()}`,
        process_id: 'step_8_feedback_loop',
        orbt_layer: 10000,
        blueprint_version: '1.0'
      };

      await composioRequest(errorAuditPayload);
    } catch (auditError) {
      console.error('[FEEDBACK-REPORTS] Failed to log error to audit trail:', auditError);
    }

    return res.status(500).json({
      success: false,
      message: 'Feedback report operation failed',
      error: error.message,
      session_id: sessionId,
      processing_time_ms: calculateProcessingTime(startTime)
    });
  }
}