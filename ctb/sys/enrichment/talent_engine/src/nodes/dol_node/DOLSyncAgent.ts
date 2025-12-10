/**
 * DOLSyncAgent
 * ============
 * DOL Node: Department of Labor Data Sync Agent
 *
 * Synchronizes Form 5500 filings from DOL ERISA database.
 * Primary source of benefits plan and renewal intelligence.
 *
 * Hub-and-Spoke Role:
 * - Part of DOL_NODE (spoke)
 * - Requires company anchor (EIN matching) from Company Hub
 * - Provides renewal dates to BIT Node for intent scoring
 * - Feeds carrier data to CarrierNormalizerAgent
 *
 * Features:
 * - Form 5500 filing sync
 * - Schedule A parsing
 * - EIN-to-company matching
 * - Historical filing tracking
 *
 * TODO: Implement DOL ERISA API integration
 * TODO: Add EIN matching logic
 * TODO: Integrate with existing dol_form_5500 tables
 */

import { AgentResult } from "../../models/SlotRow";

/**
 * Form 5500 filing record.
 */
export interface Form5500Filing {
  ack_id: string;
  ein: string;
  plan_name: string;
  sponsor_name: string;
  plan_year_begin: string;
  plan_year_end: string;
  total_participants: number;
  total_assets: number;
  plan_type: string;
  filing_status: string;
  received_date: string;
}

/**
 * Agent configuration.
 */
export interface DOLSyncAgentConfig {
  /** Enable verbose logging */
  verbose: boolean;
  /** Mock mode for testing */
  mock_mode: boolean;
  /** DOL API endpoint */
  api_endpoint: string;
  /** Maximum filings per sync */
  max_filings_per_sync: number;
  /** Sync historical years (0 = current only) */
  historical_years: number;
  /** EIN matching confidence threshold */
  ein_match_threshold: number;
}

/**
 * Default configuration.
 */
export const DEFAULT_DOL_SYNC_CONFIG: DOLSyncAgentConfig = {
  verbose: false,
  mock_mode: true,
  api_endpoint: "https://www.efast.dol.gov/portal/app/disseminate",
  max_filings_per_sync: 100,
  historical_years: 3,
  ein_match_threshold: 0.95,
};

/**
 * Task for DOLSyncAgent.
 */
export interface DOLSyncTask {
  task_id: string;
  company_id: string;
  company_name: string;
  ein?: string;
  sync_type: "full" | "incremental" | "single_company";
}

/**
 * DOLSyncAgent - Synchronizes DOL Form 5500 data.
 *
 * Execution Flow:
 * 1. Receive sync request (full, incremental, or single company)
 * 2. Query DOL ERISA database
 * 3. Match filings to companies via EIN
 * 4. Parse filing data
 * 5. Return matched filings for storage
 */
export class DOLSyncAgent {
  private config: DOLSyncAgentConfig;

  constructor(config?: Partial<DOLSyncAgentConfig>) {
    this.config = {
      ...DEFAULT_DOL_SYNC_CONFIG,
      ...config,
    };
  }

  /**
   * Run the DOL sync agent.
   */
  async run(task: DOLSyncTask): Promise<AgentResult> {
    try {
      // Validate input
      if (!task.company_id || !task.company_name) {
        return this.createResult(task, false, {}, "company_id and company_name are required");
      }

      if (this.config.verbose) {
        console.log(`[DOLSyncAgent] Syncing DOL data for: ${task.company_name}`);
      }

      // Mock mode: Return sample data
      if (this.config.mock_mode) {
        const mockFilings = this.generateMockFilings(task);
        return this.createResult(task, true, {
          filings: mockFilings,
          filings_count: mockFilings.length,
          sync_type: task.sync_type,
          ein_matched: task.ein ? true : false,
          source: "mock",
        });
      }

      // TODO: Real DOL API integration
      // 1. Query DOL ERISA API
      // 2. Filter by EIN if provided
      // 3. Parse Form 5500 and Schedule A data
      // 4. Match to company via EIN

      return this.createResult(task, false, {}, "Real DOL API integration not yet implemented");
    } catch (error) {
      return this.createResult(
        task,
        false,
        {},
        error instanceof Error ? error.message : "Unknown error occurred"
      );
    }
  }

  /**
   * Generate mock filings for testing.
   */
  private generateMockFilings(task: DOLSyncTask): Form5500Filing[] {
    const currentYear = new Date().getFullYear();
    const filings: Form5500Filing[] = [];

    for (let i = 0; i <= this.config.historical_years; i++) {
      const year = currentYear - i;
      filings.push({
        ack_id: `ACK-${task.company_id}-${year}`,
        ein: task.ein || `XX-XXXXXXX`,
        plan_name: `${task.company_name} Employee Benefits Plan`,
        sponsor_name: task.company_name,
        plan_year_begin: `${year}-01-01`,
        plan_year_end: `${year}-12-31`,
        total_participants: Math.floor(Math.random() * 1000) + 100,
        total_assets: Math.floor(Math.random() * 10000000) + 1000000,
        plan_type: "HEALTH",
        filing_status: "FILED",
        received_date: `${year + 1}-03-15`,
      });
    }

    return filings;
  }

  /**
   * Sync all companies (batch operation).
   */
  async syncAll(
    companies: Array<{ company_id: string; company_name: string; ein?: string }>
  ): Promise<Map<string, Form5500Filing[]>> {
    const results = new Map<string, Form5500Filing[]>();

    for (const company of companies) {
      const task: DOLSyncTask = {
        task_id: `dol_sync_${company.company_id}_${Date.now()}`,
        company_id: company.company_id,
        company_name: company.company_name,
        ein: company.ein,
        sync_type: "single_company",
      };

      const result = await this.run(task);
      if (result.success && result.data?.filings) {
        results.set(company.company_id, result.data.filings as Form5500Filing[]);
      }
    }

    return results;
  }

  /**
   * Get latest filing for a company.
   */
  async getLatestFiling(
    companyId: string,
    companyName: string,
    ein?: string
  ): Promise<Form5500Filing | null> {
    const task: DOLSyncTask = {
      task_id: `dol_latest_${companyId}_${Date.now()}`,
      company_id: companyId,
      company_name: companyName,
      ein,
      sync_type: "single_company",
    };

    const result = await this.run(task);
    if (result.success && result.data?.filings) {
      const filings = result.data.filings as Form5500Filing[];
      return filings.sort((a, b) => b.plan_year_end.localeCompare(a.plan_year_end))[0] || null;
    }

    return null;
  }

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: DOLSyncTask,
    success: boolean,
    data: Record<string, unknown>,
    error?: string
  ): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "DOLSyncAgent",
      slot_row_id: task.company_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }

  getConfig(): DOLSyncAgentConfig {
    return { ...this.config };
  }

  updateConfig(config: Partial<DOLSyncAgentConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
