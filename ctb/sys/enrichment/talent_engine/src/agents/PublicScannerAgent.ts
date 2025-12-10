/**
 * PublicScannerAgent
 * ==================
 * Scans LinkedIn profiles to determine public accessibility.
 *
 * Services:
 * - Primary: Proxycurl (public_profile field)
 * - Fallback: Treat missing as "private"
 */

import { AgentTask, AgentResult, SlotRow } from "../SlotRow";
import { ProxycurlService, ServiceResponse } from "../services";
import { withRetry } from "../utils/retry";

/**
 * Agent configuration.
 */
export interface PublicScannerConfig {
  proxycurlApiKey: string;
}

/**
 * PublicScannerAgent - Determines if LinkedIn profiles are publicly accessible.
 * Uses Proxycurl to check profile accessibility.
 */
export class PublicScannerAgent {
  private proxycurlService: ProxycurlService | null = null;

  constructor(config?: PublicScannerConfig) {
    if (config?.proxycurlApiKey) {
      this.proxycurlService = new ProxycurlService(config.proxycurlApiKey);
    }
  }

  /**
   * Set the Proxycurl service (for dependency injection/testing).
   */
  setProxycurlService(service: ProxycurlService): void {
    this.proxycurlService = service;
  }

  /**
   * Run the agent to scan a LinkedIn profile for public accessibility.
   *
   * @param task - The agent task to process
   * @param row - The SlotRow to update (optional)
   * @returns AgentResult with accessibility status
   */
  async run(task: AgentTask, row?: SlotRow): Promise<AgentResult> {
    try {
      const { linkedin_url } = task;

      if (!linkedin_url) {
        return this.createResult(
          task,
          false,
          { public_accessible: false },
          "LinkedIn URL is required for public scan"
        );
      }

      // Try to check accessibility via Proxycurl
      const result = await this.checkAccessibility(linkedin_url);

      if (result.success && result.data) {
        const isPublic = result.data.public_accessible;

        if (row) {
          row.update({ public_accessible: isPublic });
        }

        return this.createResult(task, true, {
          public_accessible: isPublic,
          source: "proxycurl",
        });
      }

      // Fallback: Treat missing/failed as private
      // This is safer than assuming public
      if (row) {
        row.update({ public_accessible: false });
      }

      return this.createResult(task, true, {
        public_accessible: false,
        source: "fallback",
        note: "Could not verify, assuming private",
      });
    } catch (error) {
      // On error, default to private (conservative)
      if (row) {
        row.update({ public_accessible: false });
      }

      return this.createResult(
        task,
        false,
        { public_accessible: false },
        error instanceof Error ? error.message : "Unknown error occurred"
      );
    }
  }

  /**
   * Legacy synchronous run method for backwards compatibility.
   */
  runSync(task: AgentTask): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "PublicScannerAgent",
      slot_row_id: task.slot_row_id,
      success: false,
      data: {},
      error: "Use async run() method for full functionality",
      completed_at: new Date(),
    };
  }

  /**
   * Check profile accessibility using Proxycurl.
   */
  private async checkAccessibility(
    linkedinUrl: string
  ): Promise<ServiceResponse<{ public_accessible: boolean }>> {
    if (!this.proxycurlService) {
      return { success: false, error: "Proxycurl service not configured" };
    }

    return withRetry(
      () => this.proxycurlService!.checkPublicAccessibility(linkedinUrl),
      { retries: 2, delay: 200 }
    );
  }

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: AgentTask,
    success: boolean,
    data: Record<string, unknown>,
    error?: string
  ): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "PublicScannerAgent",
      slot_row_id: task.slot_row_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }
}
