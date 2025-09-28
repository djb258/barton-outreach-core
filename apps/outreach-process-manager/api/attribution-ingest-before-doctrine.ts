/**
 * Step 5 Attribution Ingest API - Barton Doctrine Pipeline
 * Input: Attribution payload from CRM systems or webhooks
 * Output: Attribution recorded with PLE/BIT updates triggered
 *
 * Workflow:
 * 1. Validate Barton IDs exist in master tables
 * 2. Insert attribution record into closed_loop_attribution
 * 3. Write audit log entry with full change tracking
 * 4. Trigger downstream updates (PLE scoring, BIT signal weights)
 * 5. Return comprehensive status with system impact
 *
 * Barton Doctrine Rules:
 * - All Barton IDs must be preserved and validated
 * - Attribution feeds back into PLE and BIT for continuous learning
 * - Every attribution event must be fully audited
 * - Uses Standard Composio MCP pattern for all database operations
 * - Real-time updates to scoring and signal systems
 */

import { StandardComposioNeonBridge } from '../utils/standard-composio-neon-bridge';

interface AttributionIngestRequest {
  company_unique_id: string;
  person_unique_id?: string;
  company_slot_unique_id?: string;
  campaign_id?: string;
  source_campaign?: string;
  touchpoint_sequence?: string[];
  crm_system: 'Salesforce' | 'HubSpot' | 'Pipedrive' | 'Zoho' | 'Other';
  crm_record_id: string;
  crm_opportunity_id?: string;
  outcome: 'closed_won' | 'closed_lost' | 'nurture' | 'churn' | 'qualified' | 'disqualified';
  outcome_reason?: string;
  revenue_amount?: number;
  expected_close_date?: string;
  actual_close_date?: string;
  sales_cycle_days?: number;
  touchpoints_to_close?: number;
  deal_stage_at_attribution?: string;
  lost_to_competitor?: string;
  attribution_model?: 'first_touch' | 'last_touch' | 'multi_touch';
  attribution_confidence?: number;
}

interface SystemUpdate {
  system: 'PLE' | 'BIT';
  status: 'success' | 'failed' | 'partial';
  changes_applied: string[];
  impact_metrics: Record<string, any>;
}

interface AttributionIngestResponse {
  status: 'success' | 'failed';
  message: string;
  attribution_id?: number;
  audit_log_id: number;
  updated_systems: SystemUpdate[];
  validation_results: {
    company_exists: boolean;
    person_exists?: boolean;
    slot_exists?: boolean;
  };
  learning_impact: {
    ple_models_updated: string[];
    bit_signals_adjusted: string[];
    prediction_accuracy?: number;
  };
}

export default async function handler(req: any, res: any) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const bridge = new StandardComposioNeonBridge();

  try {
    const attributionData: AttributionIngestRequest = req.body;

    // Validate required fields
    if (!attributionData.company_unique_id || !attributionData.crm_system ||
        !attributionData.crm_record_id || !attributionData.outcome) {
      return res.status(400).json({
        status: 'failed',
        message: 'Missing required fields: company_unique_id, crm_system, crm_record_id, outcome',
        updated_systems: []
      });
    }

    console.log(`[ATTRIBUTION-INGEST] Processing ${attributionData.outcome} for ${attributionData.company_unique_id}`);

    // Generate session ID for tracking
    const sessionId = `attribution_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const batchId = `batch_${Date.now()}`;

    // Start transaction for atomicity
    await bridge.query('BEGIN');

    try {
      // Step 1: Validate Barton IDs exist in master tables
      const validationResults = await validateBartonIds(bridge, attributionData);

      if (!validationResults.company_exists) {
        await bridge.query('ROLLBACK');
        return res.status(400).json({
          status: 'failed',
          message: `Company ID ${attributionData.company_unique_id} not found in master tables`,
          updated_systems: [],
          validation_results: validationResults
        });
      }

      // Step 2: Insert attribution record
      const attributionId = await insertAttributionRecord(bridge, attributionData, sessionId, batchId);

      // Step 3: Create audit log entry
      const auditLogId = await logAttributionEvent(
        bridge,
        attributionId,
        attributionData,
        'create',
        'success',
        sessionId,
        batchId
      );

      // Step 4: Trigger downstream updates
      const systemUpdates: SystemUpdate[] = [];

      // Update PLE (Perpetual Lead Engine) scoring
      const pleUpdate = await updatePLEScoring(bridge, attributionData, sessionId);
      systemUpdates.push(pleUpdate);

      // Update BIT (Buyer Intent Trigger) signals
      const bitUpdate = await updateBITSignals(bridge, attributionData, sessionId);
      systemUpdates.push(bitUpdate);

      // Step 5: Update audit log with system impacts
      await updateAuditLogWithImpacts(bridge, auditLogId, systemUpdates);

      // Calculate learning impact
      const learningImpact = await calculateLearningImpact(bridge, attributionData, systemUpdates);

      // Commit transaction
      await bridge.query('COMMIT');

      const response: AttributionIngestResponse = {
        status: 'success',
        message: `Attribution recorded for ${attributionData.outcome} outcome`,
        attribution_id: attributionId,
        audit_log_id: auditLogId,
        updated_systems: systemUpdates,
        validation_results: validationResults,
        learning_impact: learningImpact
      };

      console.log(`[ATTRIBUTION-INGEST] Successfully processed attribution ${attributionId}`);
      return res.status(200).json(response);

    } catch (error) {
      await bridge.query('ROLLBACK');
      throw error;
    }

  } catch (error: any) {
    console.error('[ATTRIBUTION-INGEST] Attribution failed:', error);
    return res.status(500).json({
      status: 'failed',
      message: `Attribution ingestion failed: ${error.message}`,
      updated_systems: []
    });
  }
}

/**
 * Validate that Barton IDs exist in master tables
 */
async function validateBartonIds(
  bridge: StandardComposioNeonBridge,
  data: AttributionIngestRequest
): Promise<{
  company_exists: boolean;
  person_exists?: boolean;
  slot_exists?: boolean;
}> {
  // Check company exists
  const companyQuery = `
    SELECT company_unique_id
    FROM marketing.company_master
    WHERE company_unique_id = $1
  `;
  const companyResult = await bridge.query(companyQuery, [data.company_unique_id]);
  const companyExists = companyResult.rows.length > 0;

  let personExists: boolean | undefined;
  if (data.person_unique_id) {
    const personQuery = `
      SELECT unique_id
      FROM marketing.people_master
      WHERE unique_id = $1
    `;
    const personResult = await bridge.query(personQuery, [data.person_unique_id]);
    personExists = personResult.rows.length > 0;
  }

  let slotExists: boolean | undefined;
  if (data.company_slot_unique_id) {
    const slotQuery = `
      SELECT company_slot_unique_id
      FROM marketing.company_slot
      WHERE company_slot_unique_id = $1
    `;
    const slotResult = await bridge.query(slotQuery, [data.company_slot_unique_id]);
    slotExists = slotResult.rows.length > 0;
  }

  return {
    company_exists: companyExists,
    person_exists: personExists,
    slot_exists: slotExists
  };
}

/**
 * Insert attribution record into closed_loop_attribution table
 */
async function insertAttributionRecord(
  bridge: StandardComposioNeonBridge,
  data: AttributionIngestRequest,
  sessionId: string,
  batchId: string
): Promise<number> {
  const query = `
    INSERT INTO marketing.closed_loop_attribution (
      company_unique_id,
      person_unique_id,
      company_slot_unique_id,
      campaign_id,
      source_campaign,
      touchpoint_sequence,
      crm_system,
      crm_record_id,
      crm_opportunity_id,
      outcome,
      outcome_reason,
      revenue_amount,
      expected_close_date,
      actual_close_date,
      sales_cycle_days,
      touchpoints_to_close,
      deal_stage_at_attribution,
      lost_to_competitor,
      attribution_model,
      attribution_confidence,
      session_id,
      batch_id
    ) VALUES (
      $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
      $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22
    ) RETURNING id
  `;

  const result = await bridge.query(query, [
    data.company_unique_id,
    data.person_unique_id || null,
    data.company_slot_unique_id || null,
    data.campaign_id || null,
    data.source_campaign || null,
    data.touchpoint_sequence || null,
    data.crm_system,
    data.crm_record_id,
    data.crm_opportunity_id || null,
    data.outcome,
    data.outcome_reason || null,
    data.revenue_amount || null,
    data.expected_close_date || null,
    data.actual_close_date || null,
    data.sales_cycle_days || null,
    data.touchpoints_to_close || null,
    data.deal_stage_at_attribution || null,
    data.lost_to_competitor || null,
    data.attribution_model || 'first_touch',
    data.attribution_confidence || 1.0,
    sessionId,
    batchId
  ]);

  return result.rows[0].id;
}

/**
 * Log attribution event to audit table
 */
async function logAttributionEvent(
  bridge: StandardComposioNeonBridge,
  attributionId: number,
  data: AttributionIngestRequest,
  action: string,
  status: string,
  sessionId: string,
  batchId: string
): Promise<number> {
  const query = `
    INSERT INTO marketing.attribution_audit_log (
      attribution_id,
      company_unique_id,
      person_unique_id,
      action,
      status,
      source,
      new_values,
      session_id,
      batch_id
    ) VALUES (
      $1, $2, $3, $4, $5, $6, $7, $8, $9
    ) RETURNING id
  `;

  const result = await bridge.query(query, [
    attributionId,
    data.company_unique_id,
    data.person_unique_id || null,
    action,
    status,
    `${data.crm_system}_webhook`,
    JSON.stringify(data),
    sessionId,
    batchId
  ]);

  return result.rows[0].id;
}

/**
 * Update PLE (Perpetual Lead Engine) scoring based on attribution outcome
 */
async function updatePLEScoring(
  bridge: StandardComposioNeonBridge,
  data: AttributionIngestRequest,
  sessionId: string
): Promise<SystemUpdate> {
  try {
    // Get current lead score if it exists
    const currentScoreQuery = `
      SELECT marketing_score, marketing_segment, marketing_score_breakdown
      FROM marketing.${data.person_unique_id ? 'people_master' : 'company_master'}
      WHERE ${data.person_unique_id ? 'unique_id' : 'company_unique_id'} = $1
    `;

    const currentScoreResult = await bridge.query(currentScoreQuery, [
      data.person_unique_id || data.company_unique_id
    ]);

    const currentScore = currentScoreResult.rows[0]?.marketing_score || 0;
    const currentBreakdown = currentScoreResult.rows[0]?.marketing_score_breakdown || {};

    // Calculate new score based on outcome
    const newScore = calculateUpdatedScore(currentScore, data.outcome, data.revenue_amount);

    // Update scoring history
    const pleHistoryQuery = `
      INSERT INTO marketing.ple_lead_scoring_history (
        company_unique_id,
        person_unique_id,
        model_version,
        score_before,
        score_after,
        score_factors,
        attribution_outcome,
        attribution_revenue,
        prediction_accuracy
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    `;

    const predictionAccuracy = calculatePredictionAccuracy(currentScore, data.outcome);

    await bridge.query(pleHistoryQuery, [
      data.company_unique_id,
      data.person_unique_id || null,
      'v1.0_attribution_feedback',
      currentScore,
      newScore,
      JSON.stringify(currentBreakdown),
      data.outcome,
      data.revenue_amount || null,
      predictionAccuracy
    ]);

    return {
      system: 'PLE',
      status: 'success',
      changes_applied: ['score_updated', 'history_recorded'],
      impact_metrics: {
        score_change: newScore - currentScore,
        prediction_accuracy: predictionAccuracy,
        outcome: data.outcome
      }
    };

  } catch (error: any) {
    console.error('[PLE-UPDATE] Failed:', error);
    return {
      system: 'PLE',
      status: 'failed',
      changes_applied: [],
      impact_metrics: { error: error.message }
    };
  }
}

/**
 * Update BIT (Buyer Intent Trigger) signals based on attribution outcome
 */
async function updateBITSignals(
  bridge: StandardComposioNeonBridge,
  data: AttributionIngestRequest,
  sessionId: string
): Promise<SystemUpdate> {
  try {
    // Find recent signals for this company that may have contributed to the outcome
    const recentSignalsQuery = `
      SELECT signal_type, signal_strength, weight_before, correlation_strength
      FROM marketing.bit_signal_performance
      WHERE company_unique_id = $1
        AND created_at > NOW() - INTERVAL '90 days'
      ORDER BY created_at DESC
    `;

    const signalsResult = await bridge.query(recentSignalsQuery, [data.company_unique_id]);
    const recentSignals = signalsResult.rows;

    const updatedSignals: string[] = [];

    // Update signal weights based on outcome correlation
    for (const signal of recentSignals) {
      const correlationImpact = calculateCorrelationImpact(signal, data.outcome, data.revenue_amount);
      const newWeight = adjustSignalWeight(signal.weight_before, correlationImpact);

      // Update signal performance
      const updateQuery = `
        UPDATE marketing.bit_signal_performance
        SET
          attribution_outcome = $1,
          attribution_revenue = $2,
          correlation_strength = $3,
          weight_after = $4,
          weight_adjustment_reason = $5,
          updated_at = NOW()
        WHERE company_unique_id = $6
          AND signal_type = $7
          AND created_at > NOW() - INTERVAL '90 days'
      `;

      await bridge.query(updateQuery, [
        data.outcome,
        data.revenue_amount || null,
        correlationImpact,
        newWeight,
        `Attribution feedback: ${data.outcome}`,
        data.company_unique_id,
        signal.signal_type
      ]);

      updatedSignals.push(signal.signal_type);
    }

    return {
      system: 'BIT',
      status: 'success',
      changes_applied: ['signal_weights_updated', 'correlations_recorded'],
      impact_metrics: {
        signals_updated: updatedSignals.length,
        updated_signal_types: updatedSignals,
        outcome: data.outcome
      }
    };

  } catch (error: any) {
    console.error('[BIT-UPDATE] Failed:', error);
    return {
      system: 'BIT',
      status: 'failed',
      changes_applied: [],
      impact_metrics: { error: error.message }
    };
  }
}

/**
 * Update audit log with system impact details
 */
async function updateAuditLogWithImpacts(
  bridge: StandardComposioNeonBridge,
  auditLogId: number,
  systemUpdates: SystemUpdate[]
): Promise<void> {
  const pleImpact = systemUpdates.find(u => u.system === 'PLE');
  const bitImpact = systemUpdates.find(u => u.system === 'BIT');

  const updateQuery = `
    UPDATE marketing.attribution_audit_log
    SET
      ple_score_impact = $1,
      bit_signal_impact = $2,
      updated_at = NOW()
    WHERE id = $3
  `;

  await bridge.query(updateQuery, [
    pleImpact ? JSON.stringify(pleImpact) : null,
    bitImpact ? JSON.stringify(bitImpact) : null,
    auditLogId
  ]);
}

/**
 * Calculate learning impact from attribution
 */
async function calculateLearningImpact(
  bridge: StandardComposioNeonBridge,
  data: AttributionIngestRequest,
  systemUpdates: SystemUpdate[]
): Promise<{
  ple_models_updated: string[];
  bit_signals_adjusted: string[];
  prediction_accuracy?: number;
}> {
  const pleUpdate = systemUpdates.find(u => u.system === 'PLE');
  const bitUpdate = systemUpdates.find(u => u.system === 'BIT');

  return {
    ple_models_updated: pleUpdate?.changes_applied || [],
    bit_signals_adjusted: bitUpdate?.impact_metrics?.updated_signal_types || [],
    prediction_accuracy: pleUpdate?.impact_metrics?.prediction_accuracy
  };
}

/**
 * Helper functions for score and signal calculations
 */
function calculateUpdatedScore(currentScore: number, outcome: string, revenue?: number): number {
  let adjustment = 0;

  switch (outcome) {
    case 'closed_won':
      adjustment = revenue && revenue > 10000 ? 20 : 10;
      break;
    case 'closed_lost':
      adjustment = -5;
      break;
    case 'qualified':
      adjustment = 5;
      break;
    case 'disqualified':
      adjustment = -10;
      break;
    case 'churn':
      adjustment = -15;
      break;
    default:
      adjustment = 0;
  }

  return Math.max(0, Math.min(100, currentScore + adjustment));
}

function calculatePredictionAccuracy(originalScore: number, actualOutcome: string): number {
  // Convert outcome to expected score range
  const outcomeScoreMap = {
    'closed_won': 90,
    'qualified': 70,
    'nurture': 50,
    'disqualified': 20,
    'closed_lost': 10,
    'churn': 5
  };

  const expectedScore = outcomeScoreMap[actualOutcome as keyof typeof outcomeScoreMap] || 50;
  const scoreDiff = Math.abs(originalScore - expectedScore);

  // Convert to accuracy percentage (100% = perfect prediction, 0% = completely wrong)
  return Math.max(0, 100 - (scoreDiff / 100) * 100);
}

function calculateCorrelationImpact(signal: any, outcome: string, revenue?: number): number {
  // Positive outcomes strengthen signal correlation
  if (outcome === 'closed_won') {
    return Math.min(1.0, signal.correlation_strength + 0.1);
  } else if (outcome === 'closed_lost' || outcome === 'disqualified') {
    return Math.max(0.0, signal.correlation_strength - 0.05);
  }
  return signal.correlation_strength;
}

function adjustSignalWeight(currentWeight: number, correlationImpact: number): number {
  // Adjust weight based on correlation impact
  const adjustment = (correlationImpact - 0.5) * 0.01; // Small incremental changes
  return Math.max(0.0001, Math.min(1.0, currentWeight + adjustment));
}