/**
 * MissingSlotAgent
 * ================
 * Company Hub Node: Missing Slot Detection Agent
 *
 * Responsible for detecting and filling missing slots for a company.
 * Uses slot discovery adapter to find executives for empty positions.
 *
 * Hub-and-Spoke Role:
 * - Part of COMPANY_HUB (master node)
 * - Triggers People Node discovery when slots are empty
 * - Defines which executive roles need filling
 *
 * Features:
 * - Company-level slot completeness check
 * - Automatic slot discovery via adapter
 * - Placeholder row creation for missing slots
 * - Configurable mandatory slots
 */

import { AgentResult, SlotRow, SlotType, createSlotRow } from "../../models/SlotRow";
import { CompanyStateResult, evaluateCompanyState } from "../../models/CompanyState";
import {
  checkCompany,
  CompanyCheckResult,
  CompanyCheckerConfig,
  DEFAULT_CHECKER_CONFIG,
} from "../../logic/companyChecker";
import {
  slotDiscoveryAdapter,
  SlotDiscoveryConfig,
  DEFAULT_SLOT_DISCOVERY_CONFIG,
  SlotDiscoveryResult,
} from "../../adapters";

/**
 * Agent configuration.
 */
export interface MissingSlotAgentConfig extends CompanyCheckerConfig {
  /** Enable detailed logging */
  verbose: boolean;
  /** Auto-create placeholder rows for missing slots */
  auto_create_rows: boolean;
  /** Auto-fill slots via discovery adapter */
  auto_fill_slots: boolean;
  /** Slot discovery adapter config */
  discovery_config: Partial<SlotDiscoveryConfig>;
  /** Maximum cost for slot discovery */
  max_discovery_cost: number;
}

/**
 * Default configuration.
 */
export const DEFAULT_MISSING_SLOT_CONFIG: MissingSlotAgentConfig = {
  ...DEFAULT_CHECKER_CONFIG,
  verbose: false,
  auto_create_rows: true,
  auto_fill_slots: true,
  discovery_config: { mock_mode: true },
  max_discovery_cost: 1.00,
};

/**
 * Task specific to MissingSlotAgent.
 */
export interface MissingSlotTask {
  task_id: string;
  company_id: string;
  company_name: string;
  company_domain?: string;
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
  discovered_people: SlotDiscoveryResult[];
  slots_to_fill: SlotType[];
}

/**
 * MissingSlotAgent - Detects and handles missing slots for companies.
 *
 * Execution Flow:
 * 1. Receive company state from dispatcher
 * 2. Evaluate which slots are missing (CEO, CFO, HR, BENEFITS)
 * 3. If auto_fill_slots → call slotDiscoveryAdapter to find people
 * 4. If auto_create_rows → create SlotRows for discovered or placeholder data
 * 5. Return list of slots that still need work
 */
export class MissingSlotAgent {
  private config: MissingSlotAgentConfig;
  private totalCostIncurred: number = 0;

  constructor(config?: Partial<MissingSlotAgentConfig>) {
    this.config = {
      ...DEFAULT_MISSING_SLOT_CONFIG,
      ...config,
    };
  }

  /**
   * Run the missing slot agent on a task.
   */
  async run(task: MissingSlotTask): Promise<AgentResult> {
    try {
      // Validate input
      if (!task.company_id || !task.company_name) {
        return this.createResult(task, false, {}, "company_id and company_name are required");
      }

      if (this.config.verbose) {
        console.log(`[MissingSlotAgent] Checking slots for: ${task.company_name}`);
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

      // No missing slots
      if (!checkResult.should_trigger_missing_slot_agent) {
        return this.createResult(task, true, {
          company_id: task.company_id,
          company_name: task.company_name,
          missing_count: 0,
          filled_count: checkResult.state.filled_slots.length,
          is_fully_staffed: true,
        });
      }

      const missingSlots = checkResult.state.missing_slots;
      let discoveredPeople: SlotDiscoveryResult[] = [];
      let createdRows: SlotRow[] = [];

      // Auto-fill slots via discovery adapter
      if (this.config.auto_fill_slots && this.canContinueDiscovery()) {
        if (this.config.verbose) {
          console.log(`[MissingSlotAgent] Discovering people for slots: ${missingSlots.join(", ")}`);
        }

        const discoveryConfig: SlotDiscoveryConfig = {
          ...DEFAULT_SLOT_DISCOVERY_CONFIG,
          ...this.config.discovery_config,
        };

        const discoveryResult = await slotDiscoveryAdapter(
          {
            company_name: task.company_name,
            company_domain: task.company_domain,
            slot_types: missingSlots,
          },
          discoveryConfig
        );

        if (discoveryResult.success && discoveryResult.data) {
          this.totalCostIncurred += discoveryResult.cost || 0;
          discoveredPeople = discoveryResult.data;

          if (this.config.verbose) {
            console.log(`[MissingSlotAgent] Discovered ${discoveredPeople.length} people`);
          }
        }
      }

      // Create rows for discovered or missing slots
      if (this.config.auto_create_rows) {
        createdRows = this.createRowsForMissingSlots(
          task.company_id,
          task.company_name,
          missingSlots,
          discoveredPeople
        );
      }

      // Determine which slots still need work
      const filledByDiscovery = discoveredPeople.map((p) => p.slot_type);
      const slotsStillMissing = missingSlots.filter(
        (slot) => !filledByDiscovery.includes(slot)
      );

      const result: MissingSlotResult = {
        company_id: task.company_id,
        company_name: task.company_name,
        check_result: checkResult,
        created_rows: createdRows,
        discovered_people: discoveredPeople,
        slots_to_fill: slotsStillMissing,
      };

      return this.createResult(task, true, {
        ...result,
        missing_count: missingSlots.length,
        filled_count: checkResult.state.filled_slots.length,
        discovered_count: discoveredPeople.length,
        still_missing_count: slotsStillMissing.length,
        is_fully_staffed: slotsStillMissing.length === 0,
        total_discovery_cost: this.totalCostIncurred,
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
   * Create SlotRows for missing slots.
   */
  private createRowsForMissingSlots(
    companyId: string,
    companyName: string,
    missingSlots: SlotType[],
    discoveredPeople: SlotDiscoveryResult[]
  ): SlotRow[] {
    const createdRows: SlotRow[] = [];

    const discoveredBySlot = new Map<string, SlotDiscoveryResult>();
    for (const person of discoveredPeople) {
      const existing = discoveredBySlot.get(person.slot_type);
      if (!existing || person.confidence > existing.confidence) {
        discoveredBySlot.set(person.slot_type, person);
      }
    }

    for (const slotType of missingSlots) {
      const discovered = discoveredBySlot.get(slotType);

      if (discovered) {
        const row = createSlotRow({
          company_id: companyId,
          company_name: companyName,
          slot_type: slotType,
          person_name: discovered.person_name,
          linkedin_url: discovered.linkedin_url ?? null,
          email: discovered.email ?? null,
          current_title: discovered.title ?? null,
        });
        createdRows.push(row);
      } else {
        const row = createSlotRow({
          company_id: companyId,
          company_name: companyName,
          slot_type: slotType,
          person_name: null,
        });
        createdRows.push(row);
      }
    }

    return createdRows;
  }

  /**
   * Check if discovery can continue within cost budget.
   */
  private canContinueDiscovery(): boolean {
    return this.totalCostIncurred < this.config.max_discovery_cost;
  }

  /**
   * Run directly on company state.
   */
  async runOnState(companyState: CompanyStateResult): Promise<MissingSlotResult> {
    const task: MissingSlotTask = {
      task_id: `missing_slot_${companyState.company_id}_${Date.now()}`,
      company_id: companyState.company_id,
      company_name: companyState.company_name,
      existing_rows: companyState.rows,
    };

    const result = await this.run(task);

    if (result.success && result.data) {
      return {
        company_id: companyState.company_id,
        company_name: companyState.company_name,
        check_result: result.data.check_result as CompanyCheckResult,
        created_rows: result.data.created_rows as SlotRow[],
        discovered_people: result.data.discovered_people as SlotDiscoveryResult[],
        slots_to_fill: result.data.slots_to_fill as SlotType[],
      };
    }

    return {
      company_id: companyState.company_id,
      company_name: companyState.company_name,
      check_result: {
        company_id: companyState.company_id,
        company_name: companyState.company_name,
        state: companyState,
        missing_mandatory_slots: companyState.missing_slots.filter((s) =>
          this.config.mandatory_slots.includes(s)
        ),
        should_trigger_missing_slot_agent: companyState.missing_slots.length > 0,
        skip_reason: null,
      },
      created_rows: [],
      discovered_people: [],
      slots_to_fill: companyState.missing_slots,
    };
  }

  /**
   * Batch process multiple companies.
   */
  async runBatch(
    companies: { company_id: string; company_name: string; company_domain?: string; rows: SlotRow[] }[]
  ): Promise<MissingSlotResult[]> {
    const results: MissingSlotResult[] = [];

    for (const company of companies) {
      const task: MissingSlotTask = {
        task_id: `missing_slot_${company.company_id}_${Date.now()}`,
        company_id: company.company_id,
        company_name: company.company_name,
        company_domain: company.company_domain,
        existing_rows: company.rows,
      };

      const agentResult = await this.run(task);

      if (agentResult.success && agentResult.data) {
        results.push({
          company_id: company.company_id,
          company_name: company.company_name,
          check_result: agentResult.data.check_result as CompanyCheckResult,
          created_rows: agentResult.data.created_rows as SlotRow[],
          discovered_people: agentResult.data.discovered_people as SlotDiscoveryResult[],
          slots_to_fill: agentResult.data.slots_to_fill as SlotType[],
        });
      }
    }

    return results;
  }

  /**
   * Check a single company and return missing slots.
   */
  getMissingSlots(companyId: string, companyName: string, rows: SlotRow[]): SlotType[] {
    const checkResult = checkCompany(companyId, companyName, rows, this.config);
    return checkResult.state.missing_slots;
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

  getTotalCost(): number {
    return this.totalCostIncurred;
  }

  resetCost(): void {
    this.totalCostIncurred = 0;
  }

  getConfig(): MissingSlotAgentConfig {
    return { ...this.config };
  }

  updateConfig(config: Partial<MissingSlotAgentConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
