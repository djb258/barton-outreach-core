/**
 * Doctrine Spec:
 * - Barton ID: 05.01.03.07.10000.013
 * - Altitude: 10000 (Execution Layer)
 * - Input: attribution record filter parameters
 * - Output: attribution record list and metadata
 * - MCP: Composio (Neon integrated)
 */
/**
 * Attribution Records API - Detailed Attribution Data Retrieval
 * Fetches paginated attribution records with filtering and sorting
 *
 * Endpoints:
 * - GET /api/attribution-records
 */

import { StandardComposioNeonBridge } from '../utils/standard-composio-neon-bridge';

interface AttributionRecord {
  id: number;
  company_unique_id: string;
  company_name?: string;
  person_unique_id?: string;
  person_name?: string;
  outcome: string;
  outcome_reason?: string;
  revenue_amount?: number;
  crm_system: string;
  crm_record_id: string;
  sales_cycle_days?: number;
  touchpoints_to_close?: number;
  actual_close_date?: string;
  expected_close_date?: string;
  attribution_model: string;
  attribution_confidence?: number;
  touchpoint_sequence?: string[];
  lost_to_competitor?: string;
  created_at: string;
}

export default async function handler(req: any, res: any) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const bridge = new StandardComposioNeonBridge();

  try {
    const {
      limit = '50',
      offset = '0',
      sort_by = 'created_at',
      sort_order = 'desc',
      outcome_filter,
      crm_filter,
      date_from,
      date_to,
      min_revenue,
      max_revenue
    } = req.query;

    console.log(`[ATTRIBUTION-RECORDS] Fetching records with filters:`, {
      limit, offset, sort_by, sort_order, outcome_filter, crm_filter
    });

    const records = await getAttributionRecords(bridge, {
      limit: parseInt(limit as string),
      offset: parseInt(offset as string),
      sortBy: sort_by as string,
      sortOrder: sort_order as string,
      outcomeFilter: outcome_filter as string,
      crmFilter: crm_filter as string,
      dateFrom: date_from as string,
      dateTo: date_to as string,
      minRevenue: min_revenue ? parseFloat(min_revenue as string) : undefined,
      maxRevenue: max_revenue ? parseFloat(max_revenue as string) : undefined
    });

    return res.status(200).json({
      success: true,
      data: records.records,
      total_count: records.totalCount,
      page_info: {
        has_next_page: records.hasNextPage,
        has_previous_page: records.hasPreviousPage,
        current_page: Math.floor(parseInt(offset as string) / parseInt(limit as string)) + 1,
        total_pages: Math.ceil(records.totalCount / parseInt(limit as string))
      }
    });

  } catch (error: any) {
    console.error('[ATTRIBUTION-RECORDS] Failed:', error);
    return res.status(500).json({
      error: 'Attribution records fetch failed',
      message: error.message
    });
  }
}

interface FetchOptions {
  limit: number;
  offset: number;
  sortBy: string;
  sortOrder: string;
  outcomeFilter?: string;
  crmFilter?: string;
  dateFrom?: string;
  dateTo?: string;
  minRevenue?: number;
  maxRevenue?: number;
}

interface FetchResult {
  records: AttributionRecord[];
  totalCount: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

/**
 * Fetch attribution records with filtering and pagination
 */
async function getAttributionRecords(
  bridge: StandardComposioNeonBridge,
  options: FetchOptions
): Promise<FetchResult> {
  const {
    limit, offset, sortBy, sortOrder,
    outcomeFilter, crmFilter, dateFrom, dateTo,
    minRevenue, maxRevenue
  } = options;

  // Build WHERE clause with filters
  let whereConditions: string[] = ['1=1'];

  if (outcomeFilter) {
    whereConditions.push(`a.outcome = '${outcomeFilter}'`);
  }

  if (crmFilter) {
    whereConditions.push(`a.crm_system = '${crmFilter}'`);
  }

  if (dateFrom) {
    whereConditions.push(`a.created_at >= '${dateFrom}'`);
  }

  if (dateTo) {
    whereConditions.push(`a.created_at <= '${dateTo} 23:59:59'`);
  }

  if (minRevenue !== undefined) {
    whereConditions.push(`a.revenue_amount >= ${minRevenue}`);
  }

  if (maxRevenue !== undefined) {
    whereConditions.push(`a.revenue_amount <= ${maxRevenue}`);
  }

  const whereClause = whereConditions.join(' AND ');

  // Validate sort fields
  const validSortFields = [
    'created_at', 'outcome', 'revenue_amount', 'crm_system',
    'actual_close_date', 'sales_cycle_days', 'company_unique_id'
  ];
  const validatedSortBy = validSortFields.includes(sortBy) ? sortBy : 'created_at';
  const validatedSortOrder = sortOrder.toLowerCase() === 'asc' ? 'ASC' : 'DESC';

  // Get total count
  const countQuery = `
    SELECT COUNT(*) as total_count
    FROM marketing.closed_loop_attribution a
    WHERE ${whereClause}
  `;

  const countResult = await bridge.query(countQuery);
  const totalCount = parseInt(countResult.rows[0].total_count);

  // Get paginated records with company/person details
  const recordsQuery = `
    SELECT
      a.id,
      a.company_unique_id,
      a.person_unique_id,
      a.outcome,
      a.outcome_reason,
      a.revenue_amount,
      a.crm_system,
      a.crm_record_id,
      a.sales_cycle_days,
      a.touchpoints_to_close,
      a.actual_close_date,
      a.expected_close_date,
      a.attribution_model,
      a.attribution_confidence,
      a.touchpoint_sequence,
      a.lost_to_competitor,
      a.created_at,
      c.company_name,
      p.person_name
    FROM marketing.closed_loop_attribution a
    LEFT JOIN core.company_master_table c ON a.company_unique_id = c.company_unique_id
    LEFT JOIN core.people_master_table p ON a.person_unique_id = p.person_unique_id
    WHERE ${whereClause}
    ORDER BY a.${validatedSortBy} ${validatedSortOrder}
    LIMIT ${limit} OFFSET ${offset}
  `;

  const recordsResult = await bridge.query(recordsQuery);
  const records: AttributionRecord[] = recordsResult.rows.map(row => ({
    id: row.id,
    company_unique_id: row.company_unique_id,
    company_name: row.company_name,
    person_unique_id: row.person_unique_id,
    person_name: row.person_name,
    outcome: row.outcome,
    outcome_reason: row.outcome_reason,
    revenue_amount: row.revenue_amount ? parseFloat(row.revenue_amount) : undefined,
    crm_system: row.crm_system,
    crm_record_id: row.crm_record_id,
    sales_cycle_days: row.sales_cycle_days ? parseInt(row.sales_cycle_days) : undefined,
    touchpoints_to_close: row.touchpoints_to_close ? parseInt(row.touchpoints_to_close) : undefined,
    actual_close_date: row.actual_close_date?.toISOString().split('T')[0],
    expected_close_date: row.expected_close_date?.toISOString().split('T')[0],
    attribution_model: row.attribution_model || 'first_touch',
    attribution_confidence: row.attribution_confidence ? parseFloat(row.attribution_confidence) : undefined,
    touchpoint_sequence: row.touchpoint_sequence ? JSON.parse(row.touchpoint_sequence) : undefined,
    lost_to_competitor: row.lost_to_competitor,
    created_at: row.created_at.toISOString()
  }));

  return {
    records,
    totalCount,
    hasNextPage: offset + limit < totalCount,
    hasPreviousPage: offset > 0
  };
}