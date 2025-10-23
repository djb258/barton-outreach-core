/**
 * Doctrine Spec:
 * - Barton ID: 03.01.01.07.10000.003
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Error log endpoint for Control Tower
 * - Query Target: shq.master_error_log
 */

import express from 'express';
import sql from '../../utils/neonClient.js';

const router = express.Router();

/**
 * GET /neon/errors
 * Returns error feed for Control Tower with pagination and filtering
 *
 * Query params:
 * - limit: Number of records (default: 100, max: 1000)
 * - offset: Pagination offset (default: 0)
 * - severity: Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
 * - agent_id: Filter by agent
 * - resolved: Filter by resolution status (true/false)
 * - source: Filter by source system
 *
 * Response format:
 * {
 *   success: boolean,
 *   data: Array<ErrorRecord>,
 *   pagination: { limit, offset, total, hasMore }
 * }
 */
router.get('/errors', async (req, res) => {
  try {
    console.log('🚨 Fetching error log...');

    // Parse and validate query parameters
    const limit = Math.min(parseInt(req.query.limit) || 100, 1000);
    const offset = parseInt(req.query.offset) || 0;
    const severity = req.query.severity?.toUpperCase();
    const agentId = req.query.agent_id;
    const resolved = req.query.resolved;
    const source = req.query.source;

    // Build dynamic WHERE clause
    const conditions = [];
    const params = {};

    if (severity && ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].includes(severity)) {
      conditions.push(`severity = '${severity}'`);
    }

    if (agentId) {
      conditions.push(`agent_id = '${agentId}'`);
    }

    if (resolved !== undefined) {
      if (resolved === 'true') {
        conditions.push('resolved_at IS NOT NULL');
      } else if (resolved === 'false') {
        conditions.push('resolved_at IS NULL');
      }
    }

    if (source) {
      conditions.push(`context->>'source' = '${source}'`);
    }

    const whereClause = conditions.length > 0
      ? `WHERE ${conditions.join(' AND ')}`
      : '';

    // Get total count
    const countResult = await sql`
      SELECT COUNT(*)::int as total
      FROM shq.master_error_log
      ${sql.unsafe(whereClause)}
    `;

    const total = countResult[0]?.total || 0;

    // Get error records
    const errors = await sql`
      SELECT
        error_id,
        occurred_at,
        resolved_at,
        process_id,
        blueprint_id,
        agent_id,
        stage,
        severity,
        error_type,
        message,
        escalation_level,
        escalated_at,
        resolution_method,
        occurrence_count,
        pattern_id,
        context
      FROM shq.master_error_log
      ${sql.unsafe(whereClause)}
      ORDER BY occurred_at DESC
      LIMIT ${limit}
      OFFSET ${offset}
    `;

    res.json({
      success: true,
      data: errors.map(error => ({
        errorId: error.error_id,
        occurredAt: error.occurred_at,
        resolvedAt: error.resolved_at,
        processId: error.process_id,
        blueprintId: error.blueprint_id,
        agentId: error.agent_id,
        stage: error.stage,
        severity: error.severity,
        errorType: error.error_type,
        message: error.message,
        escalationLevel: error.escalation_level,
        escalatedAt: error.escalated_at,
        resolutionMethod: error.resolution_method,
        occurrenceCount: error.occurrence_count,
        patternId: error.pattern_id,
        context: error.context,
        isResolved: error.resolved_at !== null
      })),
      pagination: {
        limit,
        offset,
        total,
        hasMore: offset + errors.length < total,
        returned: errors.length
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('❌ Error log fetch error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch error log',
      source: 'neon',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

/**
 * GET /neon/errors/:errorId
 * Get detailed information about a specific error
 */
router.get('/errors/:errorId', async (req, res) => {
  try {
    const { errorId } = req.params;
    console.log(`🔍 Fetching error details for: ${errorId}`);

    const errorDetails = await sql`
      SELECT
        e.*,
        p.pattern_id,
        p.error_signature,
        p.known_solution,
        p.auto_resolution_available,
        p.occurrence_count as pattern_occurrence_count
      FROM shq.master_error_log e
      LEFT JOIN shq.error_patterns p ON e.pattern_id = p.pattern_id
      WHERE e.error_id = ${errorId}
    `;

    if (errorDetails.length === 0) {
      return res.status(404).json({
        success: false,
        error: 'Error not found',
        errorId
      });
    }

    // Get resolution attempts
    const attempts = await sql`
      SELECT
        attempt_id,
        resolution_method,
        attempted_by,
        attempted_at,
        success,
        duration_seconds,
        outcome_message
      FROM shq.error_resolution_attempts
      WHERE error_id = ${errorId}
      ORDER BY attempted_at DESC
    `;

    const error = errorDetails[0];

    res.json({
      success: true,
      data: {
        errorId: error.error_id,
        occurredAt: error.occurred_at,
        resolvedAt: error.resolved_at,
        processId: error.process_id,
        blueprintId: error.blueprint_id,
        planId: error.plan_id,
        planVersion: error.plan_version,
        agentId: error.agent_id,
        stage: error.stage,
        severity: error.severity,
        errorType: error.error_type,
        message: error.message,
        stacktrace: error.stacktrace,
        hdoSnapshot: error.hdo_snapshot,
        context: error.context,
        escalationLevel: error.escalation_level,
        escalatedAt: error.escalated_at,
        escalationReason: error.escalation_reason,
        resolutionMethod: error.resolution_method,
        resolutionNotes: error.resolution_notes,
        resolvedBy: error.resolved_by,
        occurrenceCount: error.occurrence_count,
        firstOccurredAt: error.first_occurred_at,
        pattern: error.pattern_id ? {
          patternId: error.pattern_id,
          signature: error.error_signature,
          knownSolution: error.known_solution,
          autoResolutionAvailable: error.auto_resolution_available,
          totalOccurrences: error.pattern_occurrence_count
        } : null,
        resolutionAttempts: attempts.map(attempt => ({
          attemptId: attempt.attempt_id,
          method: attempt.resolution_method,
          attemptedBy: attempt.attempted_by,
          attemptedAt: attempt.attempted_at,
          success: attempt.success,
          durationSeconds: attempt.duration_seconds,
          outcomeMessage: attempt.outcome_message
        }))
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('❌ Error details fetch error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch error details',
      source: 'neon',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

export default router;
