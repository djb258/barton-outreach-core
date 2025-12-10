/**
 * Dispatcher
 * ==========
 * Routes SlotRows to the correct agent based on checklist evaluation.
 * Respects throttle limits and kill switches.
 */

import { SlotRow, AgentTask, AgentType, DispatchResult } from "./SlotRow";
import { evaluateChecklist, ChecklistResult } from "./checklist";
import { ThrottleManager } from "./throttle";
import { KillSwitchManager } from "./killswitch";

/**
 * Generate a unique task ID.
 */
function generateTaskId(): string {
  return `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Create an AgentTask from a SlotRow.
 */
function createTask(row: SlotRow, agentType: AgentType): AgentTask {
  return {
    task_id: generateTaskId(),
    agent_type: agentType,
    slot_row_id: row.id,
    company_name: row.company_name,
    slot_type: row.slot_type,
    person_name: row.person_name,
    linkedin_url: row.linkedin_url,
    context: {
      email_pattern: row.email_pattern,
      current_title: row.current_title,
      current_company: row.current_company,
    },
    created_at: new Date(),
  };
}

/**
 * Determine which agent should handle the row based on checklist.
 * Returns the first missing piece in priority order.
 *
 * Priority order:
 * 1. LinkedInFinderAgent (if missing_linkedin)
 * 2. PublicScannerAgent (if missing_public_flag)
 * 3. PatternAgent (if missing_pattern)
 * 4. EmailGeneratorAgent (if missing_email)
 * 5. TitleCompanyAgent (if missing_title_company)
 * 6. HashAgent (if missing_hash)
 *
 * @param checklist - Result from evaluateChecklist
 * @returns AgentType or null if no agent needed
 */
function determineAgent(checklist: ChecklistResult): AgentType | null {
  if (checklist.missing_linkedin) return "LinkedInFinderAgent";
  if (checklist.missing_public_flag) return "PublicScannerAgent";
  if (checklist.missing_pattern) return "PatternAgent";
  if (checklist.missing_email) return "EmailGeneratorAgent";
  if (checklist.missing_title_company) return "TitleCompanyAgent";
  if (checklist.missing_hash) return "HashAgent";
  return null;
}

/**
 * Dispatch a SlotRow to the appropriate agent.
 *
 * Process:
 * 1. Evaluate checklist
 * 2. If ready_for_completion -> mark complete and return
 * 3. Determine which agent is needed
 * 4. Check kill switch for that agent
 * 5. Check throttle limits
 * 6. If all checks pass -> route to agent
 *
 * @param row - The SlotRow to dispatch
 * @param throttle - ThrottleManager instance
 * @param killSwitch - KillSwitchManager instance
 * @returns DispatchResult with status and task info
 */
export function dispatcher(
  row: SlotRow,
  throttle: ThrottleManager,
  killSwitch: KillSwitchManager
): DispatchResult {
  // Step 1: Evaluate checklist
  const checklist = evaluateChecklist(row);

  // Step 2: Check if ready for completion
  if (checklist.ready_for_completion) {
    row.slot_complete = true;
    row.last_updated = new Date();
    return {
      status: "COMPLETED",
      agent_type: null,
      task: null,
      reason: "All checklist items complete - slot marked complete",
    };
  }

  // Step 3: Determine which agent is needed
  const agentType = determineAgent(checklist);

  if (!agentType) {
    // No agent needed but not ready for completion
    // This shouldn't happen but handle gracefully
    return {
      status: "NO_ACTION",
      agent_type: null,
      task: null,
      reason: "No agent determined but not ready for completion",
    };
  }

  // Step 4: Check kill switch
  if (killSwitch.isKilled(agentType)) {
    return {
      status: "KILLED",
      agent_type: agentType,
      task: null,
      reason: `Kill switch active for ${agentType}`,
    };
  }

  // Step 5: Check throttle
  if (throttle.isThrottled()) {
    return {
      status: "THROTTLED",
      agent_type: agentType,
      task: null,
      reason: `Throttle limit exceeded: ${throttle.getStatusString()}`,
    };
  }

  // Step 6: Create task and route to agent
  const task = createTask(row, agentType);

  // Record the call in throttle
  throttle.recordCall();

  return {
    status: "ROUTED",
    agent_type: agentType,
    task: task,
    reason: `Routed to ${agentType}`,
  };
}

/**
 * Batch dispatch multiple rows.
 *
 * @param rows - Array of SlotRows to dispatch
 * @param throttle - ThrottleManager instance
 * @param killSwitch - KillSwitchManager instance
 * @returns Array of DispatchResults
 */
export function batchDispatch(
  rows: SlotRow[],
  throttle: ThrottleManager,
  killSwitch: KillSwitchManager
): DispatchResult[] {
  return rows.map((row) => dispatcher(row, throttle, killSwitch));
}

/**
 * Get dispatch summary for a batch of results.
 */
export function getDispatchSummary(results: DispatchResult[]): Record<string, number> {
  const summary: Record<string, number> = {
    ROUTED: 0,
    THROTTLED: 0,
    KILLED: 0,
    COMPLETED: 0,
    NO_ACTION: 0,
  };

  for (const result of results) {
    summary[result.status]++;
  }

  return summary;
}
