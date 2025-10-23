/**
 * Marketing Lead Scoring & Segmentation API
 * Calculates marketing quality scores and segments for promoted records
 *
 * Scoring Factors:
 * - Contact completeness (email, phone, LinkedIn)
 * - Company data richness (industry, size, website)
 * - Job title seniority level
 * - Company engagement potential
 */

import { StandardComposioNeonBridge } from '../utils/standard-composio-neon-bridge';

interface LeadScoringRequest {
  type: 'company' | 'people';
  batch_size?: number;
}

interface LeadScore {
  unique_id: string;
  marketing_score: number;
  segment: 'hot' | 'warm' | 'cold' | 'nurture';
  score_breakdown: {
    contact_completeness: number;
    data_richness: number;
    seniority_score: number;
    engagement_potential: number;
  };
  recommended_actions: string[];
}

interface LeadScoringResponse {
  success: boolean;
  scored_records: LeadScore[];
  segment_distribution: {
    hot: number;
    warm: number;
    cold: number;
    nurture: number;
  };
  recommendations: {
    immediate_outreach: string[];
    nurture_campaign: string[];
    data_enrichment_needed: string[];
  };
}

export default async function handler(req: any, res: any) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const bridge = new StandardComposioNeonBridge();

  try {
    const { type, batch_size = 100 }: LeadScoringRequest = req.body;

    if (!type || !['company', 'people'].includes(type)) {
      return res.status(400).json({
        error: 'Invalid or missing type parameter. Must be "company" or "people"'
      });
    }

    console.log(`[LEAD-SCORING] Scoring ${type} records for marketing`);

    // Get promoted records that need scoring
    const records = await getPromotedRecords(bridge, type, batch_size);

    if (records.length === 0) {
      return res.status(200).json({
        success: true,
        scored_records: [],
        segment_distribution: { hot: 0, warm: 0, cold: 0, nurture: 0 },
        recommendations: {
          immediate_outreach: [],
          nurture_campaign: [],
          data_enrichment_needed: []
        }
      });
    }

    // Score each record
    const scoredRecords: LeadScore[] = [];
    for (const record of records) {
      const score = await calculateLeadScore(record, type);
      scoredRecords.push(score);

      // Update record with marketing score
      await updateMarketingScore(bridge, score.unique_id, type, score);
    }

    // Generate segment distribution
    const segmentDistribution = {
      hot: scoredRecords.filter(r => r.segment === 'hot').length,
      warm: scoredRecords.filter(r => r.segment === 'warm').length,
      cold: scoredRecords.filter(r => r.segment === 'cold').length,
      nurture: scoredRecords.filter(r => r.segment === 'nurture').length
    };

    // Generate marketing recommendations
    const recommendations = generateMarketingRecommendations(scoredRecords);

    const response: LeadScoringResponse = {
      success: true,
      scored_records: scoredRecords,
      segment_distribution: segmentDistribution,
      recommendations
    };

    console.log(`[LEAD-SCORING] Scored ${scoredRecords.length} ${type} records`);
    return res.status(200).json(response);

  } catch (error: any) {
    console.error('[LEAD-SCORING] Scoring failed:', error);
    return res.status(500).json({
      error: 'Lead scoring failed',
      message: error.message
    });
  }
}

/**
 * Get promoted records that need marketing scoring
 */
async function getPromotedRecords(
  bridge: StandardComposioNeonBridge,
  type: string,
  batchSize: number
): Promise<any[]> {
  let query: string;

  if (type === 'company') {
    query = `
      SELECT
        company_unique_id,
        company_name,
        website_url,
        industry,
        employee_count,
        company_phone,
        linkedin_url,
        address_city,
        address_state,
        address_country,
        promoted_from_intake_at
      FROM marketing.company_master
      WHERE marketing_score IS NULL OR marketing_score_updated_at < promoted_from_intake_at
      ORDER BY promoted_from_intake_at DESC
      LIMIT $1
    `;
  } else {
    query = `
      SELECT
        p.unique_id,
        p.company_unique_id,
        p.first_name,
        p.last_name,
        p.title,
        p.seniority,
        p.department,
        p.email,
        p.work_phone_e164,
        p.linkedin_url,
        p.promoted_from_intake_at,
        c.company_name,
        c.industry,
        c.employee_count
      FROM marketing.people_master p
      LEFT JOIN marketing.company_master c ON p.company_unique_id = c.company_unique_id
      WHERE p.marketing_score IS NULL OR p.marketing_score_updated_at < p.promoted_from_intake_at
      ORDER BY p.promoted_from_intake_at DESC
      LIMIT $1
    `;
  }

  const result = await bridge.query(query, [batchSize]);
  return result.rows;
}

/**
 * Calculate comprehensive marketing lead score
 */
async function calculateLeadScore(record: any, type: string): Promise<LeadScore> {
  const uniqueId = type === 'company' ? record.company_unique_id : record.unique_id;

  let contactCompleteness = 0;
  let dataRichness = 0;
  let seniorityScore = 0;
  let engagementPotential = 0;

  if (type === 'company') {
    // Company scoring logic
    contactCompleteness = calculateCompanyContactScore(record);
    dataRichness = calculateCompanyDataScore(record);
    engagementPotential = calculateCompanyEngagementScore(record);
    seniorityScore = 50; // Companies get neutral seniority score
  } else {
    // People scoring logic
    contactCompleteness = calculatePersonContactScore(record);
    dataRichness = calculatePersonDataScore(record);
    seniorityScore = calculateSeniorityScore(record.title, record.seniority);
    engagementPotential = calculatePersonEngagementScore(record);
  }

  const totalScore = Math.round(
    (contactCompleteness + dataRichness + seniorityScore + engagementPotential) / 4
  );

  const segment = determineSegment(totalScore, seniorityScore, contactCompleteness);
  const recommendedActions = generateRecommendedActions(totalScore, contactCompleteness, dataRichness);

  return {
    unique_id: uniqueId,
    marketing_score: totalScore,
    segment,
    score_breakdown: {
      contact_completeness: contactCompleteness,
      data_richness: dataRichness,
      seniority_score: seniorityScore,
      engagement_potential: engagementPotential
    },
    recommended_actions: recommendedActions
  };
}

/**
 * Calculate contact completeness score for people
 */
function calculatePersonContactScore(record: any): number {
  let score = 0;

  if (record.email && record.email.includes('@')) score += 40;
  if (record.work_phone_e164) score += 25;
  if (record.linkedin_url) score += 25;
  if (record.first_name && record.last_name) score += 10;

  return Math.min(score, 100);
}

/**
 * Calculate contact completeness score for companies
 */
function calculateCompanyContactScore(record: any): number {
  let score = 0;

  if (record.website_url) score += 40;
  if (record.company_phone) score += 30;
  if (record.linkedin_url) score += 20;
  if (record.company_name) score += 10;

  return Math.min(score, 100);
}

/**
 * Calculate data richness score for people
 */
function calculatePersonDataScore(record: any): number {
  let score = 0;

  if (record.title) score += 30;
  if (record.department) score += 20;
  if (record.seniority) score += 20;
  if (record.company_name) score += 15;
  if (record.industry) score += 15;

  return Math.min(score, 100);
}

/**
 * Calculate data richness score for companies
 */
function calculateCompanyDataScore(record: any): number {
  let score = 0;

  if (record.industry) score += 30;
  if (record.employee_count && record.employee_count > 0) score += 25;
  if (record.address_city && record.address_state) score += 25;
  if (record.address_country) score += 20;

  return Math.min(score, 100);
}

/**
 * Calculate seniority score based on job title and seniority level
 */
function calculateSeniorityScore(title: string, seniority: string): number {
  if (!title) return 20;

  const titleLower = title.toLowerCase();
  const seniorityLower = (seniority || '').toLowerCase();

  // C-Level and VP titles
  if (titleLower.includes('ceo') || titleLower.includes('cto') || titleLower.includes('cfo') ||
      titleLower.includes('chief') || titleLower.includes('president')) {
    return 100;
  }

  if (titleLower.includes('vp') || titleLower.includes('vice president') ||
      titleLower.includes('director') || seniorityLower.includes('executive')) {
    return 85;
  }

  if (titleLower.includes('manager') || titleLower.includes('head of') ||
      seniorityLower.includes('senior') || seniorityLower.includes('lead')) {
    return 70;
  }

  if (titleLower.includes('coordinator') || titleLower.includes('specialist') ||
      titleLower.includes('analyst') || seniorityLower.includes('mid')) {
    return 50;
  }

  if (titleLower.includes('associate') || titleLower.includes('assistant') ||
      seniorityLower.includes('junior') || seniorityLower.includes('entry')) {
    return 30;
  }

  return 40; // Default score
}

/**
 * Calculate engagement potential score
 */
function calculatePersonEngagementScore(record: any): number {
  let score = 50; // Base score

  // Industry multipliers
  if (record.industry) {
    const industryLower = record.industry.toLowerCase();
    if (industryLower.includes('technology') || industryLower.includes('software') ||
        industryLower.includes('saas')) {
      score += 25;
    } else if (industryLower.includes('finance') || industryLower.includes('healthcare')) {
      score += 15;
    } else if (industryLower.includes('manufacturing') || industryLower.includes('retail')) {
      score += 10;
    }
  }

  // Company size multipliers
  if (record.employee_count) {
    if (record.employee_count >= 1000) score += 20;
    else if (record.employee_count >= 100) score += 15;
    else if (record.employee_count >= 10) score += 10;
  }

  return Math.min(score, 100);
}

function calculateCompanyEngagementScore(record: any): number {
  return calculatePersonEngagementScore(record);
}

/**
 * Determine marketing segment based on scores
 */
function determineSegment(totalScore: number, seniorityScore: number, contactScore: number): 'hot' | 'warm' | 'cold' | 'nurture' {
  if (totalScore >= 80 && seniorityScore >= 70 && contactScore >= 60) {
    return 'hot';
  } else if (totalScore >= 60 && contactScore >= 40) {
    return 'warm';
  } else if (contactScore >= 30) {
    return 'cold';
  } else {
    return 'nurture';
  }
}

/**
 * Generate recommended marketing actions
 */
function generateRecommendedActions(totalScore: number, contactScore: number, dataScore: number): string[] {
  const actions: string[] = [];

  if (totalScore >= 80) {
    actions.push('Immediate outreach - high priority lead');
    actions.push('Personalized email campaign');
  } else if (totalScore >= 60) {
    actions.push('Add to warm lead nurture sequence');
    actions.push('Social media engagement');
  } else {
    actions.push('Data enrichment needed');
    actions.push('Add to long-term nurture campaign');
  }

  if (contactScore < 40) {
    actions.push('Find additional contact information');
  }

  if (dataScore < 50) {
    actions.push('Enrich company and role data');
  }

  return actions;
}

/**
 * Update record with marketing score
 */
async function updateMarketingScore(
  bridge: StandardComposioNeonBridge,
  uniqueId: string,
  type: string,
  score: LeadScore
): Promise<void> {
  const tableName = type === 'company' ? 'marketing.company_master' : 'marketing.people_master';
  const idField = type === 'company' ? 'company_unique_id' : 'unique_id';

  const query = `
    UPDATE ${tableName}
    SET
      marketing_score = $1,
      marketing_segment = $2,
      marketing_score_breakdown = $3,
      recommended_actions = $4,
      marketing_score_updated_at = NOW()
    WHERE ${idField} = $5
  `;

  await bridge.query(query, [
    score.marketing_score,
    score.segment,
    JSON.stringify(score.score_breakdown),
    JSON.stringify(score.recommended_actions),
    uniqueId
  ]);
}

/**
 * Generate overall marketing recommendations
 */
function generateMarketingRecommendations(scoredRecords: LeadScore[]): {
  immediate_outreach: string[];
  nurture_campaign: string[];
  data_enrichment_needed: string[];
} {
  return {
    immediate_outreach: scoredRecords
      .filter(r => r.segment === 'hot')
      .map(r => r.unique_id),
    nurture_campaign: scoredRecords
      .filter(r => r.segment === 'warm' || r.segment === 'cold')
      .map(r => r.unique_id),
    data_enrichment_needed: scoredRecords
      .filter(r => r.score_breakdown.contact_completeness < 40 || r.score_breakdown.data_richness < 50)
      .map(r => r.unique_id)
  };
}