/**
 * HashAgent
 * =========
 * STUB - Generates movement hash for tracking changes.
 * Implementation will be added in a future prompt.
 */

import { AgentTask, AgentResult } from "../SlotRow";

export class HashAgent {
  /**
   * Run the agent to generate a movement hash.
   * STUB - Does not perform real API calls.
   *
   * @param task - The agent task to process
   * @returns AgentResult (stub implementation)
   */
  run(task: AgentTask): AgentResult {
    // STUB: Return empty result
    return {
      task_id: task.task_id,
      agent_type: "HashAgent",
      slot_row_id: task.slot_row_id,
      success: false,
      data: {},
      error: "STUB: Not implemented",
      completed_at: new Date(),
    };
  }
}
