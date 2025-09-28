/**
 * Doctrine Spec:
 * - Barton ID: 08.04.01.07.10000.002
 * - Altitude: 10000 (Execution Layer)
 * - Input: lead scoring feature data and person ID
 * - Output: updated lead score with breakdown
 * - MCP: Composio (Neon integrated)
 */
import type { VercelRequest, VercelResponse } from '@vercel/node';
import ComposioNeonBridge from './lib/composio-neon-bridge.js';

interface LeadScoreUpdateRequest {
  person_unique_id: string;
  features: {
    // Firmographics
    company_size?: number;
    industry?: string;
    geography?: string;
    technology_stack?: string[];

    // Engagement metrics
    email_open_rate?: number;
    email_clicks?: number;
    website_visits?: number;
    content_downloads?: number;

    // Intent signals
    funding_event?: boolean;
    hiring_surge?: boolean;
    tech_adoption?: boolean;
    competitor_research?: boolean;
    pricing_interest?: boolean;

    // Additional features
    marketing_qualified?: boolean;
    sales_qualified?: boolean;
    demo_requested?: boolean;
  };
  trigger_event?: string;
  force_update?: boolean;
}

interface LeadScoreUpdateResponse {
  status: 'success' | 'failed';
  person_unique_id?: string;
  score?: number;
  score_breakdown?: {
    firmographics: number;
    engagement: number;
    intent_signals: number;
    attribution: number;
  };
  model_version?: string;
  lead_temperature?: 'Hot' | 'Warm' | 'Cool' | 'Cold';
  message?: string;
}

export default async function handler(
  req: VercelRequest,
  res: VercelResponse<LeadScoreUpdateResponse>
) {
  // Doctrine enforcement: Only POST method allowed
  if (req.method !== 'POST') {
    return res.status(405).json({
      status: 'failed',
      message: 'Method not allowed. Only POST is permitted by doctrine.'
    });
  }

  try {
    // Initialize MCP bridge for Barton Doctrine compliance
    const mcpBridge = new ComposioNeonBridge();
    await mcpBridge.initialize();

    const {
      person_unique_id,
      features,
      trigger_event = 'manual_update',
      force_update = false
    } = req.body as LeadScoreUpdateRequest;

    // Validate required fields
    if (!person_unique_id || !features) {
      return res.status(400).json({
        status: 'failed',
        message: 'Missing required fields: person_unique_id and features'
      });
    }

    // Validate Barton ID format
    if (!isValidBartonId(person_unique_id)) {
      return res.status(400).json({
        status: 'failed',
        message: 'Invalid Barton ID format for person_unique_id'
      });
    }

    // Get person and company details via MCP
    const personDetails = await getPersonDetails(mcpBridge, person_unique_id);
    if (!personDetails) {
      return res.status(404).json({
        status: 'failed',
        message: `Person ${person_unique_id} not found`
      });
    }

    // Check if recent score exists (within last hour)
    if (!force_update) {
      const recentScore = await getRecentScore(mcpBridge, person_unique_id);
      if (recentScore) {
        return res.status(200).json({
          status: 'success',
          person_unique_id,
          score: recentScore.score,
          score_breakdown: recentScore.score_breakdown,
          model_version: recentScore.model_version,
          lead_temperature: getLeadTemperature(recentScore.score),
          message: 'Returning cached score (less than 1 hour old)'
        });
      }
    }

    // Get current model version via MCP
    const modelVersion = await getCurrentModelVersion(mcpBridge);

    // Calculate scores
    const scoringResult = await calculateScore(
      mcpBridge,
      person_unique_id,
      personDetails.company_unique_id,
      features,
      modelVersion
    );

    // Begin transaction via MCP
    await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
      sql: 'BEGIN',
      mode: 'write'
    });

    try {
      // Get previous score for history tracking
      const previousScoreResult = await mcpBridge.executeNeonOperation('QUERY_ROWS', {
        sql: `SELECT score FROM marketing.ple_lead_scoring WHERE person_unique_id = '${person_unique_id}'`,
        mode: 'read'
      });

      const previousScore = previousScoreResult.success ? previousScoreResult.data.rows[0] : null;

      // Upsert lead scoring record via MCP
      const upsertQuery = `
        INSERT INTO marketing.ple_lead_scoring (
          person_unique_id,
          company_unique_id,
          score,
          score_breakdown,
          model_version,
          model_name,
          firmographics_score,
          engagement_score,
          intent_score,
          attribution_score,
          last_scored_at
        ) VALUES (
          '${person_unique_id}',
          '${personDetails.company_unique_id}',
          ${scoringResult.total_score},
          '${JSON.stringify(scoringResult.breakdown)}',
          '${modelVersion}',
          'ple_standard',
          ${scoringResult.firmographics_score},
          ${scoringResult.engagement_score},
          ${scoringResult.intent_score},
          ${scoringResult.attribution_score},
          NOW()
        )
        ON CONFLICT (person_unique_id) DO UPDATE SET
          score = EXCLUDED.score,
          score_breakdown = EXCLUDED.score_breakdown,
          model_version = EXCLUDED.model_version,
          firmographics_score = EXCLUDED.firmographics_score,
          engagement_score = EXCLUDED.engagement_score,
          intent_score = EXCLUDED.intent_score,
          attribution_score = EXCLUDED.attribution_score,
          last_scored_at = EXCLUDED.last_scored_at,
          updated_at = NOW()
      `;

      await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
        sql: upsertQuery,
        mode: 'write'
      });

      // Insert into scoring history via MCP
      const historyQuery = `
        INSERT INTO marketing.scoring_history (
          person_unique_id,
          company_unique_id,
          score,
          previous_score,
          score_change,
          model_version,
          score_breakdown,
          trigger_event,
          trigger_details,
          scored_at
        ) VALUES (
          '${person_unique_id}',
          '${personDetails.company_unique_id}',
          ${scoringResult.total_score},
          ${previousScore?.score || 'NULL'},
          ${previousScore ? scoringResult.total_score - previousScore.score : 'NULL'},
          '${modelVersion}',
          '${JSON.stringify(scoringResult.breakdown)}',
          '${trigger_event}',
          '${JSON.stringify({ features, timestamp: new Date().toISOString() })}',
          NOW()
        )
      `;

      await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
        sql: historyQuery,
        mode: 'write'
      });

      // Check for threshold triggers
      const triggers = await checkScoreTriggers(
        person_unique_id,
        scoringResult.total_score,
        previousScore?.score
      );

      // If score crossed hot threshold, consider auto-campaign
      if (triggers.includes('hot_threshold_crossed')) {
        const campaignLogQuery = `
          INSERT INTO marketing.campaign_audit_log (
            campaign_id,
            action,
            status,
            details
          ) VALUES (
            'PENDING_${person_unique_id}',
            'create',
            'pending',
            '${JSON.stringify({
              trigger: 'hot_lead_score',
              person_id: person_unique_id,
              score: scoringResult.total_score,
              recommendation: 'Consider PLE campaign'
            })}'
          )
        `;

        await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
          sql: campaignLogQuery,
          mode: 'write'
        });
      }

      // Commit transaction via MCP
      await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
        sql: 'COMMIT',
        mode: 'write'
      });

      // Log success
      console.log(`[Lead Score Update] SUCCESS: Updated score for ${person_unique_id} to ${scoringResult.total_score} via MCP`);

      const leadTemperature = getLeadTemperature(scoringResult.total_score);

      return res.status(200).json({
        status: 'success',
        person_unique_id,
        score: scoringResult.total_score,
        score_breakdown: scoringResult.breakdown,
        model_version: modelVersion,
        lead_temperature: leadTemperature,
        message: `Score updated successfully via MCP. Lead is ${leadTemperature}.`
      });

    } catch (error) {
      // Rollback transaction via MCP
      await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
        sql: 'ROLLBACK',
        mode: 'write'
      });
      throw error;
    }

  } catch (error) {
    console.error('[Lead Score Update] MCP ERROR:', error);

    return res.status(500).json({
      status: 'failed',
      message: 'Failed to update lead score via MCP',
      person_unique_id: req.body.person_unique_id
    });
  }
}

// Helper function to validate Barton ID format
function isValidBartonId(id: string): boolean {
  const bartonIdRegex = /^\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{5}\.\d{3}$/;
  return bartonIdRegex.test(id);
}

// Get person details from database via MCP
async function getPersonDetails(mcpBridge: any, personId: string): Promise<any> {
  try {
    const query = `
      SELECT
        pm.unique_id,
        pm.company_unique_id,
        pm.email,
        cm.company_name,
        cm.industry,
        cm.employee_count
      FROM marketing.people_master pm
      JOIN marketing.company_master cm ON cm.unique_id = pm.company_unique_id
      WHERE pm.unique_id = '${personId}'
    `;

    const result = await mcpBridge.executeNeonOperation('QUERY_ROWS', {
      sql: query,
      mode: 'read'
    });

    return result.success && result.data.rows.length > 0 ? result.data.rows[0] : null;
  } catch (error) {
    console.error('[Get Person Details] MCP Error:', error);
    return null;
  }
}

// Get recent score if exists via MCP
async function getRecentScore(mcpBridge: any, personId: string): Promise<any> {
  try {
    const query = `
      SELECT
        score,
        score_breakdown,
        model_version,
        last_scored_at
      FROM marketing.ple_lead_scoring
      WHERE person_unique_id = '${personId}'
      AND last_scored_at > NOW() - INTERVAL '1 hour'
    `;

    const result = await mcpBridge.executeNeonOperation('QUERY_ROWS', {
      sql: query,
      mode: 'read'
    });

    return result.success && result.data.rows.length > 0 ? result.data.rows[0] : null;
  } catch (error) {
    console.error('[Get Recent Score] MCP Error:', error);
    return null;
  }
}

// Get current active model version via MCP
async function getCurrentModelVersion(mcpBridge: any): Promise<string> {
  try {
    const query = `
      SELECT version
      FROM marketing.scoring_model_versions
      WHERE model_type = 'PLE'
      AND is_active = true
      LIMIT 1
    `;

    const result = await mcpBridge.executeNeonOperation('QUERY_ROWS', {
      sql: query,
      mode: 'read'
    });

    return result.success && result.data.rows.length > 0 ? result.data.rows[0].version : '1.0.0';
  } catch (error) {
    console.error('[Get Model Version] MCP Error:', error);
    return '1.0.0';
  }
}

// Calculate comprehensive lead score (no DB calls, pure calculation)
async function calculateScore(
  mcpBridge: any,
  personId: string,
  companyId: string,
  features: any,
  modelVersion: string
): Promise<any> {
  // Firmographics score (max 30 points)
  let firmographics_score = 0;

  // Company size scoring
  if (features.company_size) {
    if (features.company_size >= 1000) firmographics_score += 10;
    else if (features.company_size >= 100) firmographics_score += 7;
    else if (features.company_size >= 10) firmographics_score += 4;
  }

  // Industry scoring
  const highValueIndustries = ['SaaS', 'Technology', 'Finance', 'Healthcare', 'Enterprise Software'];
  if (features.industry && highValueIndustries.includes(features.industry)) {
    firmographics_score += 10;
  } else if (features.industry) {
    firmographics_score += 5;
  }

  // Geography scoring
  if (features.geography === 'North America') firmographics_score += 7;
  else if (features.geography === 'Europe') firmographics_score += 5;
  else if (features.geography) firmographics_score += 3;

  // Technology stack scoring
  if (features.technology_stack?.length > 5) firmographics_score += 3;

  // Cap firmographics at 30
  firmographics_score = Math.min(30, firmographics_score);

  // Engagement score (max 25 points)
  let engagement_score = 0;

  if (features.email_open_rate) {
    engagement_score += Math.min(10, features.email_open_rate * 0.25);
  }

  if (features.email_clicks) {
    engagement_score += Math.min(5, features.email_clicks * 2);
  }

  if (features.website_visits) {
    engagement_score += Math.min(7, features.website_visits * 0.5);
  }

  if (features.content_downloads) {
    engagement_score += Math.min(3, features.content_downloads * 1.5);
  }

  // Cap engagement at 25
  engagement_score = Math.min(25, engagement_score);

  // Intent signals score (max 36 points)
  let intent_score = 0;

  if (features.funding_event) intent_score += 12;
  if (features.hiring_surge) intent_score += 10;
  if (features.tech_adoption) intent_score += 8;
  if (features.competitor_research) intent_score += 10;
  if (features.pricing_interest) intent_score += 12;
  if (features.demo_requested) intent_score += 15;

  // Cap intent at 36
  intent_score = Math.min(36, intent_score);

  // Attribution score from historical data (max 9 points) via MCP
  let attribution_score = 0;

  try {
    const attributionQuery = `
      SELECT
        COUNT(*) FILTER (WHERE outcome = 'closed_won') as wins,
        COUNT(*) FILTER (WHERE outcome = 'qualified') as qualified,
        COUNT(*) as total
      FROM marketing.attribution_feedback
      WHERE person_unique_id = '${personId}'
      AND outcome_date > NOW() - INTERVAL '6 months'
    `;

    const attributionResult = await mcpBridge.executeNeonOperation('QUERY_ROWS', {
      sql: attributionQuery,
      mode: 'read'
    });

    if (attributionResult.success && attributionResult.data.rows.length > 0) {
      const { wins, qualified, total } = attributionResult.data.rows[0];
      if (wins > 0) attribution_score += wins * 3;
      if (qualified > 0) attribution_score += qualified * 1.5;
    }
  } catch (error) {
    console.error('[Attribution Score] MCP Error:', error);
  }

  // Cap attribution at 9
  attribution_score = Math.min(9, attribution_score);

  // Calculate total score
  const total_score = Math.min(100,
    firmographics_score +
    engagement_score +
    intent_score +
    attribution_score
  );

  return {
    total_score: Math.round(total_score),
    firmographics_score: Math.round(firmographics_score),
    engagement_score: Math.round(engagement_score),
    intent_score: Math.round(intent_score),
    attribution_score: Math.round(attribution_score),
    breakdown: {
      firmographics: Math.round(firmographics_score),
      engagement: Math.round(engagement_score),
      intent_signals: Math.round(intent_score),
      attribution: Math.round(attribution_score)
    }
  };
}

// Check for score-based triggers
async function checkScoreTriggers(
  personId: string,
  newScore: number,
  previousScore?: number
): Promise<string[]> {
  const triggers: string[] = [];

  // Hot lead threshold
  if (newScore >= 85) {
    if (!previousScore || previousScore < 85) {
      triggers.push('hot_threshold_crossed');
    }
  }

  // Warm lead threshold
  if (newScore >= 70 && newScore < 85) {
    if (previousScore && previousScore < 70) {
      triggers.push('warm_threshold_crossed');
    }
  }

  // Significant score increase
  if (previousScore && (newScore - previousScore) >= 20) {
    triggers.push('significant_increase');
  }

  // MQL threshold
  if (newScore >= 65 && (!previousScore || previousScore < 65)) {
    triggers.push('mql_threshold');
  }

  return triggers;
}

// Get lead temperature based on score
function getLeadTemperature(score: number): 'Hot' | 'Warm' | 'Cool' | 'Cold' {
  if (score >= 85) return 'Hot';
  if (score >= 70) return 'Warm';
  if (score >= 50) return 'Cool';
  return 'Cold';
}