/**
 * FuzzyMatchAgent
 * ===============
 * Layer 1: Fuzzy Matching Intake Agent
 *
 * Responsible for matching raw company input to known company names.
 * Runs BEFORE any other processing - no slot work should happen
 * until company_name is resolved.
 */

import { AgentTask, AgentResult, SlotRow } from "../models/SlotRow";
import {
  FuzzyMatchConfig,
  FuzzyMatchResult,
  DEFAULT_FUZZY_CONFIG,
  processFuzzyMatch,
} from "../logic/fuzzyMatch";

/**
 * Agent configuration.
 */
export interface FuzzyMatchAgentConfig extends FuzzyMatchConfig {
  /** Enable detailed logging */
  verbose?: boolean;
}

/**
 * Task specific to FuzzyMatchAgent.
 */
export interface FuzzyMatchTask {
  task_id: string;
  slot_row_id: string;
  raw_company_input: string;
  company_master: string[];
}

/**
 * FuzzyMatchAgent - Matches raw company input to known companies.
 *
 * Execution Flow:
 * 1. Receive row with raw_company_input
 * 2. Search companyMaster for closest match
 * 3. If score >= auto_accept_threshold: auto-accept
 * 4. If score >= min_match_score but < auto_accept: manual review
 * 5. If score < min_match_score: UNMATCHED (fail this row)
 */
export class FuzzyMatchAgent {
  private config: FuzzyMatchAgentConfig;

  constructor(config?: Partial<FuzzyMatchAgentConfig>) {
    this.config = {
      ...DEFAULT_FUZZY_CONFIG,
      verbose: false,
      ...config,
    };
  }

  /**
   * Run the fuzzy match agent.
   *
   * @param task - The fuzzy match task to process
   * @returns AgentResult with match outcome
   */
  async run(task: FuzzyMatchTask): Promise<AgentResult> {
    const startTime = new Date();

    try {
      // Validate input
      if (!task.raw_company_input) {
        return this.createResult(task, false, {}, "raw_company_input is required");
      }

      if (!task.company_master || task.company_master.length === 0) {
        return this.createResult(task, false, {}, "company_master list is empty");
      }

      // Perform fuzzy matching
      const matchResult = processFuzzyMatch(
        task.raw_company_input,
        task.company_master,
        this.config
      );

      // Determine success based on match status
      const success = matchResult.status === "MATCHED";

      return this.createResult(task, success, {
        status: matchResult.status,
        matched_company: matchResult.matched_company,
        match_score: matchResult.match_score,
        all_candidates: matchResult.all_candidates,
        needs_manual_review: matchResult.status === "MANUAL_REVIEW",
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
   * Run fuzzy match directly on a SlotRow.
   *
   * @param row - The SlotRow to process
   * @param companyMaster - List of known company names
   * @returns Updated SlotRow
   */
  async runOnRow(row: SlotRow, companyMaster: string[]): Promise<SlotRow> {
    // Check if row needs fuzzy matching
    if (!row.needsFuzzyMatch()) {
      return row;
    }

    const rawInput = row.raw_company_input ?? row.company_name ?? "";

    if (!rawInput) {
      row.fuzzy_match_status = "UNMATCHED";
      return row;
    }

    // Process the match
    const matchResult = processFuzzyMatch(rawInput, companyMaster, this.config);

    // Apply result to row
    row.fuzzy_match_status = matchResult.status;
    row.fuzzy_match_score = matchResult.match_score;
    row.fuzzy_match_candidates = matchResult.all_candidates;

    if (matchResult.status === "MATCHED" && matchResult.matched_company) {
      row.company_name = matchResult.matched_company;
    }

    row.last_updated = new Date();

    return row;
  }

  /**
   * Batch process multiple rows.
   *
   * @param rows - Array of SlotRows to process
   * @param companyMaster - List of known company names
   * @returns Array of processed SlotRows
   */
  async runBatch(rows: SlotRow[], companyMaster: string[]): Promise<SlotRow[]> {
    const results: SlotRow[] = [];

    for (const row of rows) {
      const processed = await this.runOnRow(row, companyMaster);
      results.push(processed);
    }

    return results;
  }

  /**
   * Legacy synchronous run method for backwards compatibility.
   */
  runSync(task: FuzzyMatchTask): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "FuzzyMatchAgent",
      slot_row_id: task.slot_row_id,
      success: false,
      data: {},
      error: "Use async run() method for full functionality",
      completed_at: new Date(),
    };
  }

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: FuzzyMatchTask,
    success: boolean,
    data: Record<string, unknown>,
    error?: string
  ): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "FuzzyMatchAgent",
      slot_row_id: task.slot_row_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }

  /**
   * Get current configuration.
   */
  getConfig(): FuzzyMatchAgentConfig {
    return { ...this.config };
  }

  /**
   * Update configuration.
   */
  updateConfig(config: Partial<FuzzyMatchAgentConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
