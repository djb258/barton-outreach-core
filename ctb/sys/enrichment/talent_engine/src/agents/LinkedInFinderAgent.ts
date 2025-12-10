/**
 * LinkedInFinderAgent
 * ===================
 * STUB - Finds LinkedIn URLs for people.
 * Implementation will be added in a future prompt.
 */

import { AgentTask, AgentResult } from "../SlotRow";

export class LinkedInFinderAgent {
  /**
   * Run the agent to find a LinkedIn URL.
   * STUB - Does not perform real API calls.
   *
   * @param task - The agent task to process
   * @returns AgentResult (stub implementation)
   */
  run(task: AgentTask): AgentResult {
    // STUB: Return empty result
    return {
      task_id: task.task_id,
      agent_type: "LinkedInFinderAgent",
      slot_row_id: task.slot_row_id,
      success: false,
      data: {},
      error: "STUB: Not implemented",
      completed_at: new Date(),
    };
  }
}
