/**
 * PatternAgent
 * ============
 * STUB - Discovers email patterns for companies.
 * Implementation will be added in a future prompt.
 */

import { AgentTask, AgentResult } from "../SlotRow";

export class PatternAgent {
  /**
   * Run the agent to discover email pattern for a company.
   * STUB - Does not perform real API calls.
   *
   * @param task - The agent task to process
   * @returns AgentResult (stub implementation)
   */
  run(task: AgentTask): AgentResult {
    // STUB: Return empty result
    return {
      task_id: task.task_id,
      agent_type: "PatternAgent",
      slot_row_id: task.slot_row_id,
      success: false,
      data: {},
      error: "STUB: Not implemented",
      completed_at: new Date(),
    };
  }
}
