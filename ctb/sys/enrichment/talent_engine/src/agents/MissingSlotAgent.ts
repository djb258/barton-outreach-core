/**
 * MissingSlotAgent
 * ================
 * Layer 4: Missing Slot Trigger Agent
 *
 * Responsible for detecting and creating missing slots for a company.
 * Triggered when company-level check reveals missing required slots.
 */

import { AgentResult, SlotRow, SlotType, ALL_SLOT_TYPES } from "../models/SlotRow";
import { CompanyStateResult, evaluateCompanyState } from "../models/CompanyState";
import {
  CompanyCheckResult,
  checkCompany,
  createMissingSlotRows,
  CompanyCheckerConfig,
  DEFAULT_CHECKER_CONFIG,
} from "../logic/companyChecker";

/**
 * Agent configuration.
 */
export interface MissingSlotAgentConfig extends CompanyCheckerConfig {
  /** Enable detailed logging */
  verbose?: boolean;
  /** Auto-create placeholder rows for missing slots */
  auto_create_rows?: boolean;
}

/**
 * Default configuration.
 */
export const DEFAULT_MISSING_SLOT_CONFIG: MissingSlotAgentConfig = {
  ...DEFAULT_CHECKER_CONFIG,
  verbose: false,
  auto_create_rows: true,
};

/**
 * Task specific to MissingSlotAgent.
 */
export interface MissingSlotTask {
  task_id: string;
  company_id: string;
  company_name: string;
  existing_rows: SlotRow[];
}

/**
 * Result from MissingSlotAgent.
 */
export interface MissingSlotResult {
  company_id: string;
  company_name: string;
  check_result: CompanyCheckResult;
  created_rows: SlotRow[];
  slots_to_fill: SlotType[];
}

/**
 * MissingSlotAgent - Detects and handles missing slots for companies.
 *
 * Execution Flow:
 * 1. Receive company state from dispatcher
 * 2. Evaluate which slots are missing (CEO, CFO, HR, BENEFITS)
 * 3. If auto_create_rows: create placeholder SlotRows for missing slots
 * 4. Return list of slots needing work
 */
export class MissingSlotAgent {
  private config: MissingSlotAgentConfig;

  constructor(config?: Partial<MissingSlotAgentConfig>) {
    this.config = {
      ...DEFAULT_MISSING_SLOT_CONFIG,
      ...config,
    };
  }

  /**
   * Run the missing slot agent on a task.
   *
   * @param task - The missing slot task to process
   * @returns AgentResult with missing slot detection outcome
   */
  async run(task: MissingSlotTask): Promise<AgentResult> {
    try {
      // Validate input
      if (!task.company_id || !task.company_name) {
        return this.createResult(task, false, {}, "company_id and company_name are required");
      }

      // Check company state
      const checkResult = checkCompany(
        task.company_id,
        task.company_name,
        task.existing_rows,
        this.config
      );

      // Skip if company should be skipped
      if (checkResult.skip_reason) {
        return this.createResult(task, true, {
          skipped: true,
          skip_reason: checkResult.skip_reason,
          company_state: checkResult.state,
        });
      }

      // Create placeholder rows if configured
      let createdRows: SlotRow[] = [];
      if (this.config.auto_create_rows && checkResult.should_trigger_missing_slot_agent) {
        createdRows = createMissingSlotRows(checkResult);
      }

      const result: MissingSlotResult = {
        company_id: task.company_id,
        company_name: task.company_name,
        check_result: checkResult,
        created_rows: createdRows,
        slots_to_fill: checkResult.state.missing_slots,
      };

      return this.createResult(task, true, {
        ...result,
        missing_count: checkResult.state.missing_slots.length,
        filled_count: checkResult.state.filled_slots.length,
        is_fully_staffed: checkResult.state.is_fully_staffed,
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
   * Run directly on company state (legacy interface).
   *
   * @param companyState - The company state to process
   * @returns MissingSlotResult
   */
  async runOnState(companyState: CompanyStateResult): Promise<MissingSlotResult> {
    const checkResult: CompanyCheckResult = {
      company_id: companyState.company_id,
      company_name: companyState.company_name,
      state: companyState,
      missing_mandatory_slots: this.config.mandatory_slots.filter((slot) =>
        companyState.missing_slots.includes(slot)
      ),
      should_trigger_missing_slot_agent: companyState.missing_slots.length > 0,
      skip_reason: companyState.is_fully_staffed ? "Company is fully staffed" : null,
    };

    let createdRows: SlotRow[] = [];
    if (this.config.auto_create_rows && checkResult.should_trigger_missing_slot_agent) {
      createdRows = createMissingSlotRows(checkResult);
    }

    return {
      company_id: companyState.company_id,
      company_name: companyState.company_name,
      check_result: checkResult,
      created_rows: createdRows,
      slots_to_fill: companyState.missing_slots,
    };
  }

  /**
   * Batch process multiple companies.
   *
   * @param companies - Array of company tasks
   * @returns Array of MissingSlotResults
   */
  async runBatch(
    companies: { company_id: string; company_name: string; rows: SlotRow[] }[]
  ): Promise<MissingSlotResult[]> {
    const results: MissingSlotResult[] = [];

    for (const company of companies) {
      const task: MissingSlotTask = {
        task_id: `missing_slot_${company.company_id}_${Date.now()}`,
        company_id: company.company_id,
        company_name: company.company_name,
        existing_rows: company.rows,
      };

      const agentResult = await this.run(task);

      if (agentResult.success && agentResult.data) {
        results.push({
          company_id: company.company_id,
          company_name: company.company_name,
          check_result: agentResult.data.check_result as CompanyCheckResult,
          created_rows: agentResult.data.created_rows as SlotRow[],
          slots_to_fill: agentResult.data.slots_to_fill as SlotType[],
        });
      }
    }

    return results;
  }

  /**
   * Check a single company and return missing slots.
   *
   * @param companyId - Company ID
   * @param companyName - Company name
   * @param rows - Existing rows for this company
   * @returns Array of missing slot types
   */
  getMissingSlots(companyId: string, companyName: string, rows: SlotRow[]): SlotType[] {
    const checkResult = checkCompany(companyId, companyName, rows, this.config);
    return checkResult.state.missing_slots;
  }

  /**
   * Legacy synchronous run method for backwards compatibility.
   */
  runSync(task: MissingSlotTask): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "MissingSlotAgent",
      slot_row_id: task.company_id,
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
    task: MissingSlotTask,
    success: boolean,
    data: Record<string, unknown>,
    error?: string
  ): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "MissingSlotAgent",
      slot_row_id: task.company_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }

  /**
   * Get current configuration.
   */
  getConfig(): MissingSlotAgentConfig {
    return { ...this.config };
  }

  /**
   * Update configuration.
   */
  updateConfig(config: Partial<MissingSlotAgentConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
