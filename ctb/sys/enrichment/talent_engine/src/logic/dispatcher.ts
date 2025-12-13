/**
 * Dispatcher Logic
 * ================
 * Main pipeline dispatcher for the Talent Engine.
 * Executes the four-layer architecture in the correct order.
 *
 * Execution Order:
 * 1. Fuzzy Match Check (if company_name === null or fuzzy_match_status === PENDING)
 * 2. Company-Level Slot Check (call evaluateCompanyState, trigger MissingSlotAgent)
 * 3. Slot Checklist (route missing pieces to appropriate agents)
 * 4. Failures (try/catch with FailManager)
 * 5. Completion (mark slot_complete = true when all checklist items pass)
 */

import { SlotRow, AgentType, AgentResult } from "../models/SlotRow";
import { evaluateCompanyState, CompanyStateResult } from "../models/CompanyState";
import { AgentRegistry, globalAgentRegistry, AGENT_METADATA } from "./agentRegistry";
import { AgentThrottleRegistry, globalThrottleRegistry } from "./throttleManager";
import { KillSwitchManager, globalKillSwitchManager } from "./killSwitch";
import { FailManager, globalFailManager } from "./failManager";
import { processFuzzyMatch, DEFAULT_FUZZY_CONFIG } from "./fuzzyMatch";
import { evaluateChecklist, getNeededAgent, ChecklistResult } from "./checklist";
import { checkCompany, createMissingSlotRows, CompanyCheckResult } from "./companyChecker";
import { FuzzyMatchAgent } from "../agents/FuzzyMatchAgent";
import { MissingSlotAgent } from "../agents/MissingSlotAgent";

/**
 * Dispatcher configuration.
 */
export interface DispatcherConfig {
  /** Enable verbose logging */
  verbose: boolean;
  /** Max rows to process per batch */
  batch_size: number;
  /** Continue on errors (vs fail-fast) */
  continue_on_error: boolean;
  /** Enable dry-run mode (no actual agent calls) */
  dry_run: boolean;
}

/**
 * Default dispatcher configuration.
 */
export const DEFAULT_DISPATCHER_CONFIG: DispatcherConfig = {
  verbose: false,
  batch_size: 100,
  continue_on_error: true,
  dry_run: false,
};

/**
 * Dispatch result for a single row.
 */
export interface DispatchResult {
  row_id: string;
  success: boolean;
  step_reached: 1 | 2 | 3 | 4 | 5;
  step_name: string;
  agent_results: AgentResult[];
  error: string | null;
  completed: boolean;
}

/**
 * Batch dispatch result.
 */
export interface BatchDispatchResult {
  total_rows: number;
  processed: number;
  succeeded: number;
  failed: number;
  completed: number;
  results: DispatchResult[];
  company_states: Map<string, CompanyStateResult>;
  new_rows_created: SlotRow[];
}

/**
 * Step names for logging.
 */
const STEP_NAMES: Record<number, string> = {
  1: "Fuzzy Match Check",
  2: "Company-Level Slot Check",
  3: "Slot Checklist Processing",
  4: "Failure Handling",
  5: "Completion Check",
};

/**
 * Main dispatcher function.
 *
 * @param row - The SlotRow to process
 * @param allRows - All rows in the system (for company state evaluation)
 * @param companyMaster - List of known company names
 * @param registry - Agent registry (optional, uses global)
 * @param throttles - Throttle registry (optional, uses global)
 * @param killSwitches - Kill switch manager (optional, uses global)
 * @param failManager - Fail manager (optional, uses global)
 * @param config - Dispatcher configuration
 * @returns DispatchResult
 */
export async function dispatcher(
  row: SlotRow,
  allRows: SlotRow[],
  companyMaster: string[],
  registry: AgentRegistry = globalAgentRegistry,
  throttles: AgentThrottleRegistry = globalThrottleRegistry,
  killSwitches: KillSwitchManager = globalKillSwitchManager,
  failManager: FailManager = globalFailManager,
  config: DispatcherConfig = DEFAULT_DISPATCHER_CONFIG
): Promise<DispatchResult> {
  const result: DispatchResult = {
    row_id: row.id,
    success: false,
    step_reached: 1,
    step_name: STEP_NAMES[1],
    agent_results: [],
    error: null,
    completed: false,
  };

  try {
    // =========================================================================
    // STEP 1: Fuzzy Match Check
    // =========================================================================
    if (config.verbose) console.log(`[Dispatcher] Step 1: Fuzzy Match Check for ${row.id}`);

    if (row.needsFuzzyMatch()) {
      // Check if FuzzyMatchAgent can execute
      const canExec = registry.canExecute("FuzzyMatchAgent");
      if (!canExec.allowed) {
        result.error = canExec.reason;
        return result;
      }

      if (!config.dry_run) {
        const fuzzyAgent = registry.getAgent<FuzzyMatchAgent>("FuzzyMatchAgent");
        if (fuzzyAgent) {
          const rawInput = row.raw_company_input ?? row.company_name ?? "";
          const matchResult = processFuzzyMatch(rawInput, companyMaster, DEFAULT_FUZZY_CONFIG);

          // Apply result to row
          row.fuzzy_match_status = matchResult.status;
          row.fuzzy_match_score = matchResult.match_score;
          row.fuzzy_match_candidates = matchResult.all_candidates;

          if (matchResult.status === "MATCHED" && matchResult.matched_company) {
            row.company_name = matchResult.matched_company;
          }

          registry.recordCall("FuzzyMatchAgent");

          result.agent_results.push({
            task_id: `fuzzy_${row.id}`,
            agent_type: "FuzzyMatchAgent",
            slot_row_id: row.id,
            success: matchResult.status === "MATCHED",
            data: { ...matchResult },
            error: matchResult.status === "UNMATCHED" ? "No match found" : null,
            completed_at: new Date(),
          });
        }
      }

      // If still not matched, cannot proceed
      if (row.fuzzy_match_status !== "MATCHED") {
        result.error = "Fuzzy match failed - cannot proceed without company";
        return result;
      }
    }

    result.step_reached = 2;
    result.step_name = STEP_NAMES[2];

    // =========================================================================
    // STEP 2: Company-Level Slot Check
    // =========================================================================
    if (config.verbose) console.log(`[Dispatcher] Step 2: Company-Level Slot Check for ${row.id}`);

    const companyId = row.company_id ?? `company_${row.company_name?.toLowerCase().replace(/\s+/g, "_")}`;
    const companyName = row.company_name ?? "";

    if (!companyName) {
      result.error = "Company name is required for slot check";
      return result;
    }

    // Get all rows for this company
    const companyRows = allRows.filter((r) => r.company_name === companyName);

    // Check company state
    const companyCheck = checkCompany(companyId, companyName, companyRows);

    // If missing slots and MissingSlotAgent is available, trigger it
    if (companyCheck.should_trigger_missing_slot_agent) {
      const canExec = registry.canExecute("MissingSlotAgent");
      if (canExec.allowed && !config.dry_run) {
        const missingAgent = registry.getAgent<MissingSlotAgent>("MissingSlotAgent");
        if (missingAgent) {
          const missingResult = await missingAgent.run({
            task_id: `missing_${companyId}_${Date.now()}`,
            company_id: companyId,
            company_name: companyName,
            existing_rows: companyRows,
          });

          registry.recordCall("MissingSlotAgent");
          result.agent_results.push(missingResult);
        }
      }
    }

    result.step_reached = 3;
    result.step_name = STEP_NAMES[3];

    // =========================================================================
    // STEP 3: Slot Checklist Processing
    // =========================================================================
    if (config.verbose) console.log(`[Dispatcher] Step 3: Slot Checklist for ${row.id}`);

    // Evaluate what this row is missing
    const checklistResult = evaluateChecklist(row);

    if (!checklistResult.all_complete) {
      // Get the agent needed for the next missing item
      const neededAgent = getNeededAgent(checklistResult);

      if (neededAgent) {
        const canExec = registry.canExecute(neededAgent);

        if (!canExec.allowed) {
          if (config.verbose) {
            console.log(`[Dispatcher] Agent ${neededAgent} blocked: ${canExec.reason}`);
          }
          // Not a fatal error - just can't proceed further right now
        } else if (!config.dry_run) {
          // Get the agent and run it
          const agent = registry.getAgent(neededAgent);

          if (agent && "run" in agent) {
            try {
              // Create task for agent
              const task = {
                task_id: `${neededAgent}_${row.id}_${Date.now()}`,
                slot_row_id: row.id,
                person_name: row.person_name,
                company_name: row.company_name ?? "",
                slot_type: row.slot_type,
                linkedin_url: row.linkedin_url,
                email: row.email,
              };

              // Run agent (type assertion needed due to different task types)
              const agentResult = await (agent as any).run(task, row);
              registry.recordCall(neededAgent);
              result.agent_results.push(agentResult);

              // Handle failure
              if (!agentResult.success && agentResult.error) {
                failManager.recordFailure(row, agentResult);
              }
            } catch (error) {
              const errorMsg = error instanceof Error ? error.message : "Unknown error";
              const agentResult: AgentResult = {
                task_id: `${neededAgent}_${row.id}_${Date.now()}`,
                agent_type: neededAgent,
                slot_row_id: row.id,
                success: false,
                data: {},
                error: errorMsg,
                completed_at: new Date(),
              };
              result.agent_results.push(agentResult);
              failManager.recordFailure(row, agentResult);
            }
          }
        }
      }
    }

    result.step_reached = 4;
    result.step_name = STEP_NAMES[4];

    // =========================================================================
    // STEP 4: Failure Handling
    // =========================================================================
    if (config.verbose) console.log(`[Dispatcher] Step 4: Failure Handling for ${row.id}`);

    // Check if row is permanently failed
    if (row.permanently_failed) {
      result.error = `Row permanently failed: ${row.last_failure_reason}`;
      return result;
    }

    // Check for temporary failures that need retry
    if (row.failure_count > 0 && !row.permanently_failed) {
      // Row has had failures but isn't permanent - it may retry later
      if (config.verbose) {
        console.log(`[Dispatcher] Row ${row.id} has ${row.failure_count} failures, will retry`);
      }
    }

    result.step_reached = 5;
    result.step_name = STEP_NAMES[5];

    // =========================================================================
    // STEP 5: Completion Check
    // =========================================================================
    if (config.verbose) console.log(`[Dispatcher] Step 5: Completion Check for ${row.id}`);

    // Re-evaluate checklist after processing
    const finalChecklist = evaluateChecklist(row);

    if (finalChecklist.all_complete) {
      row.slot_complete = true;
      row.last_updated = new Date();
      result.completed = true;
    }

    result.success = true;
    return result;
  } catch (error) {
    result.error = error instanceof Error ? error.message : "Unknown dispatcher error";
    return result;
  }
}

/**
 * Batch dispatcher for processing multiple rows.
 *
 * @param rows - Array of SlotRows to process
 * @param companyMaster - List of known company names
 * @param registry - Agent registry (optional)
 * @param throttles - Throttle registry (optional)
 * @param killSwitches - Kill switch manager (optional)
 * @param failManager - Fail manager (optional)
 * @param config - Dispatcher configuration
 * @returns BatchDispatchResult
 */
export async function batchDispatcher(
  rows: SlotRow[],
  companyMaster: string[],
  registry: AgentRegistry = globalAgentRegistry,
  throttles: AgentThrottleRegistry = globalThrottleRegistry,
  killSwitches: KillSwitchManager = globalKillSwitchManager,
  failManager: FailManager = globalFailManager,
  config: DispatcherConfig = DEFAULT_DISPATCHER_CONFIG
): Promise<BatchDispatchResult> {
  const batchResult: BatchDispatchResult = {
    total_rows: rows.length,
    processed: 0,
    succeeded: 0,
    failed: 0,
    completed: 0,
    results: [],
    company_states: new Map(),
    new_rows_created: [],
  };

  // Process in batches
  const batches: SlotRow[][] = [];
  for (let i = 0; i < rows.length; i += config.batch_size) {
    batches.push(rows.slice(i, i + config.batch_size));
  }

  for (const batch of batches) {
    for (const row of batch) {
      try {
        const result = await dispatcher(
          row,
          rows,
          companyMaster,
          registry,
          throttles,
          killSwitches,
          failManager,
          config
        );

        batchResult.results.push(result);
        batchResult.processed++;

        if (result.success) {
          batchResult.succeeded++;
        } else {
          batchResult.failed++;
        }

        if (result.completed) {
          batchResult.completed++;
        }
      } catch (error) {
        batchResult.failed++;
        batchResult.processed++;

        if (!config.continue_on_error) {
          throw error;
        }
      }
    }
  }

  // Collect company states
  const companyNames = new Set(rows.map((r) => r.company_name).filter(Boolean) as string[]);
  for (const companyName of companyNames) {
    const companyRows = rows.filter((r) => r.company_name === companyName);
    const companyId = `company_${companyName.toLowerCase().replace(/\s+/g, "_")}`;
    const state = evaluateCompanyState(companyId, companyName, companyRows);
    batchResult.company_states.set(companyName, state);
  }

  return batchResult;
}

/**
 * Get dispatch statistics.
 */
export function getDispatchStats(result: BatchDispatchResult): string {
  const lines: string[] = [
    "=== Dispatch Statistics ===",
    "",
    `Total Rows: ${result.total_rows}`,
    `Processed: ${result.processed}`,
    `Succeeded: ${result.succeeded}`,
    `Failed: ${result.failed}`,
    `Completed (slot_complete=true): ${result.completed}`,
    "",
    `Success Rate: ${((result.succeeded / result.processed) * 100).toFixed(1)}%`,
    `Completion Rate: ${((result.completed / result.processed) * 100).toFixed(1)}%`,
    "",
    `Companies Processed: ${result.company_states.size}`,
  ];

  // Add company summary
  let fullyStaffed = 0;
  for (const state of result.company_states.values()) {
    if (state.is_fully_staffed) fullyStaffed++;
  }
  lines.push(`Fully Staffed Companies: ${fullyStaffed}`);

  return lines.join("\n");
}

/**
 * Create a dry-run dispatcher for testing.
 */
export function createDryRunDispatcher(
  config?: Partial<DispatcherConfig>
): (
  row: SlotRow,
  allRows: SlotRow[],
  companyMaster: string[]
) => Promise<DispatchResult> {
  const dryRunConfig: DispatcherConfig = {
    ...DEFAULT_DISPATCHER_CONFIG,
    dry_run: true,
    verbose: true,
    ...config,
  };

  return (row, allRows, companyMaster) =>
    dispatcher(
      row,
      allRows,
      companyMaster,
      globalAgentRegistry,
      globalThrottleRegistry,
      globalKillSwitchManager,
      globalFailManager,
      dryRunConfig
    );
}
