/**
 * RenewalParserAgent
 * ==================
 * DOL Node: Benefits Renewal Date Parser
 *
 * Parses Form 5500 filings to extract renewal dates.
 * Critical for BIT (Buyer Intent Tool) timing signals.
 *
 * Hub-and-Spoke Role:
 * - Part of DOL_NODE (spoke)
 * - Receives Form 5500 data from DOLSyncAgent
 * - Provides renewal dates to BIT Node
 * - Enables renewal-window targeting
 *
 * Features:
 * - Plan year extraction
 * - Renewal date calculation
 * - Multi-year trend analysis
 * - Renewal window timing
 *
 * TODO: Add Schedule A parsing for carrier renewal dates
 * TODO: Implement renewal window calculation
 * TODO: Add historical renewal tracking
 */

import { AgentResult } from "../../models/SlotRow";
import { Form5500Filing } from "./DOLSyncAgent";

/**
 * Parsed renewal information.
 */
export interface RenewalInfo {
  company_id: string;
  plan_year_end: string;
  estimated_renewal_date: string;
  renewal_window_start: string;
  renewal_window_end: string;
  days_until_renewal: number;
  in_renewal_window: boolean;
  confidence: number;
}

/**
 * Agent configuration.
 */
export interface RenewalParserAgentConfig {
  /** Enable verbose logging */
  verbose: boolean;
  /** Days before renewal to start window */
  renewal_window_start_days: number;
  /** Days after renewal to end window */
  renewal_window_end_days: number;
  /** Assume plan renews X days after year end */
  renewal_offset_days: number;
}

/**
 * Default configuration.
 */
export const DEFAULT_RENEWAL_PARSER_CONFIG: RenewalParserAgentConfig = {
  verbose: false,
  renewal_window_start_days: 90,
  renewal_window_end_days: 30,
  renewal_offset_days: 0,
};

/**
 * Task for RenewalParserAgent.
 */
export interface RenewalParserTask {
  task_id: string;
  company_id: string;
  company_name: string;
  filings: Form5500Filing[];
}

/**
 * RenewalParserAgent - Extracts renewal dates from Form 5500 filings.
 *
 * Execution Flow:
 * 1. Receive Form 5500 filings from DOLSyncAgent
 * 2. Sort by plan year (most recent first)
 * 3. Extract plan year end date
 * 4. Calculate estimated renewal date
 * 5. Determine renewal window
 * 6. Return renewal information for BIT scoring
 */
export class RenewalParserAgent {
  private config: RenewalParserAgentConfig;

  constructor(config?: Partial<RenewalParserAgentConfig>) {
    this.config = {
      ...DEFAULT_RENEWAL_PARSER_CONFIG,
      ...config,
    };
  }

  /**
   * Run the renewal parser agent.
   */
  async run(task: RenewalParserTask): Promise<AgentResult> {
    try {
      // Validate input
      if (!task.company_id || !task.company_name) {
        return this.createResult(task, false, {}, "company_id and company_name are required");
      }

      if (!task.filings || task.filings.length === 0) {
        return this.createResult(task, true, {
          company_id: task.company_id,
          renewal_info: null,
          reason: "No filings available",
        });
      }

      if (this.config.verbose) {
        console.log(`[RenewalParserAgent] Parsing ${task.filings.length} filings for: ${task.company_name}`);
      }

      // Sort filings by plan year end (most recent first)
      const sortedFilings = [...task.filings].sort(
        (a, b) => b.plan_year_end.localeCompare(a.plan_year_end)
      );

      // Get most recent filing
      const latestFiling = sortedFilings[0];

      // Parse renewal information
      const renewalInfo = this.parseRenewalFromFiling(task.company_id, latestFiling);

      // Determine if currently in renewal window
      renewalInfo.in_renewal_window = this.isInRenewalWindow(renewalInfo);

      return this.createResult(task, true, {
        company_id: task.company_id,
        renewal_info: renewalInfo,
        filings_analyzed: task.filings.length,
        latest_plan_year: latestFiling.plan_year_end,
      });
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
   * Parse renewal info from a single filing.
   */
  private parseRenewalFromFiling(companyId: string, filing: Form5500Filing): RenewalInfo {
    const planYearEnd = new Date(filing.plan_year_end);

    // Calculate next renewal date (next year's plan year end)
    const nextRenewalDate = new Date(planYearEnd);
    nextRenewalDate.setFullYear(nextRenewalDate.getFullYear() + 1);
    nextRenewalDate.setDate(nextRenewalDate.getDate() + this.config.renewal_offset_days);

    // If next renewal is in the past, add another year
    const today = new Date();
    while (nextRenewalDate < today) {
      nextRenewalDate.setFullYear(nextRenewalDate.getFullYear() + 1);
    }

    // Calculate renewal window
    const windowStart = new Date(nextRenewalDate);
    windowStart.setDate(windowStart.getDate() - this.config.renewal_window_start_days);

    const windowEnd = new Date(nextRenewalDate);
    windowEnd.setDate(windowEnd.getDate() + this.config.renewal_window_end_days);

    // Calculate days until renewal
    const daysUntilRenewal = Math.ceil(
      (nextRenewalDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
    );

    return {
      company_id: companyId,
      plan_year_end: filing.plan_year_end,
      estimated_renewal_date: nextRenewalDate.toISOString().split("T")[0],
      renewal_window_start: windowStart.toISOString().split("T")[0],
      renewal_window_end: windowEnd.toISOString().split("T")[0],
      days_until_renewal: daysUntilRenewal,
      in_renewal_window: false, // Set by caller
      confidence: 0.85, // Based on DOL filing data quality
    };
  }

  /**
   * Check if today is within the renewal window.
   */
  private isInRenewalWindow(renewalInfo: RenewalInfo): boolean {
    const today = new Date();
    const windowStart = new Date(renewalInfo.renewal_window_start);
    const windowEnd = new Date(renewalInfo.renewal_window_end);

    return today >= windowStart && today <= windowEnd;
  }

  /**
   * Batch process multiple companies.
   */
  async parseBatch(
    companies: Array<{
      company_id: string;
      company_name: string;
      filings: Form5500Filing[];
    }>
  ): Promise<Map<string, RenewalInfo | null>> {
    const results = new Map<string, RenewalInfo | null>();

    for (const company of companies) {
      const task: RenewalParserTask = {
        task_id: `renewal_${company.company_id}_${Date.now()}`,
        company_id: company.company_id,
        company_name: company.company_name,
        filings: company.filings,
      };

      const result = await this.run(task);
      if (result.success) {
        results.set(company.company_id, result.data?.renewal_info as RenewalInfo | null);
      } else {
        results.set(company.company_id, null);
      }
    }

    return results;
  }

  /**
   * Get companies in renewal window.
   */
  filterInRenewalWindow(renewalInfos: RenewalInfo[]): RenewalInfo[] {
    return renewalInfos.filter((info) => info.in_renewal_window);
  }

  /**
   * Get companies by days until renewal.
   */
  sortByRenewalUrgency(renewalInfos: RenewalInfo[]): RenewalInfo[] {
    return [...renewalInfos].sort((a, b) => a.days_until_renewal - b.days_until_renewal);
  }

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: RenewalParserTask,
    success: boolean,
    data: Record<string, unknown>,
    error?: string
  ): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "RenewalParserAgent",
      slot_row_id: task.company_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }

  getConfig(): RenewalParserAgentConfig {
    return { ...this.config };
  }

  updateConfig(config: Partial<RenewalParserAgentConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
