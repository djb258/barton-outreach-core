/**
 * PatternAgent
 * ============
 * Discovers email patterns for companies using Hunter.io.
 *
 * Services:
 * - Primary: Hunter.io (domain-search for pattern inference)
 * - No fallback required (patterns are company-specific)
 */

import { AgentTask, AgentResult, SlotRow } from "../SlotRow";
import { HunterService, ServiceResponse, EmailPatternData } from "../services";
import { withRetry } from "../utils/retry";

/**
 * Agent configuration.
 */
export interface PatternAgentConfig {
  hunterApiKey: string;
}

/**
 * Common email patterns as fallback.
 */
const COMMON_PATTERNS = [
  "{first}.{last}",
  "{first}{last}",
  "{f}{last}",
  "{first}_{last}",
  "{first}",
];

/**
 * PatternAgent - Discovers email patterns for companies.
 * Uses Hunter.io for pattern inference.
 */
export class PatternAgent {
  private hunterService: HunterService | null = null;

  constructor(config?: PatternAgentConfig) {
    if (config?.hunterApiKey) {
      this.hunterService = new HunterService(config.hunterApiKey);
    }
  }

  /**
   * Set the Hunter service (for dependency injection/testing).
   */
  setHunterService(service: HunterService): void {
    this.hunterService = service;
  }

  /**
   * Run the agent to discover email pattern for a company.
   *
   * @param task - The agent task to process
   * @param row - The SlotRow to update (optional)
   * @param domain - Company domain (optional, extracted from context)
   * @returns AgentResult with discovered pattern
   */
  async run(
    task: AgentTask,
    row?: SlotRow,
    domain?: string
  ): Promise<AgentResult> {
    try {
      // Extract domain from context or company name
      const companyDomain =
        domain ??
        (task.context?.domain as string) ??
        this.inferDomainFromCompany(task.company_name);

      if (!companyDomain) {
        return this.createResult(
          task,
          false,
          {},
          "Could not determine company domain"
        );
      }

      // Try Hunter.io for pattern
      const result = await this.getPattern(companyDomain);

      if (result.success && result.data?.pattern) {
        const pattern = result.data.pattern;

        if (row) {
          row.update({ email_pattern: pattern });
        }

        return this.createResult(task, true, {
          email_pattern: pattern,
          domain: result.data.domain,
          confidence: result.data.confidence,
          source: "hunter",
        });
      }

      // No pattern found - don't guess, report failure
      return this.createResult(
        task,
        false,
        { attempted_domain: companyDomain },
        "Could not determine email pattern for domain"
      );
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
   * Legacy synchronous run method for backwards compatibility.
   */
  runSync(task: AgentTask): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "PatternAgent",
      slot_row_id: task.slot_row_id,
      success: false,
      data: {},
      error: "Use async run() method for full functionality",
      completed_at: new Date(),
    };
  }

  /**
   * Get email pattern using Hunter.io.
   */
  private async getPattern(
    domain: string
  ): Promise<ServiceResponse<EmailPatternData>> {
    if (!this.hunterService) {
      return { success: false, error: "Hunter service not configured" };
    }

    return withRetry(
      () => this.hunterService!.getEmailPattern(domain),
      { retries: 2, delay: 200 }
    );
  }

  /**
   * Infer domain from company name.
   * Simple heuristic - real implementation would be more sophisticated.
   */
  private inferDomainFromCompany(companyName: string): string | null {
    if (!companyName) return null;

    // Remove common suffixes and normalize
    const cleaned = companyName
      .toLowerCase()
      .replace(/\s+(inc|llc|ltd|corp|co|company|corporation)\.?$/i, "")
      .replace(/[^a-z0-9]/g, "")
      .trim();

    if (!cleaned) return null;

    // Return as .com domain (simple heuristic)
    return `${cleaned}.com`;
  }

  /**
   * Get common patterns for a domain (local fallback).
   * Not used in production - just for testing/reference.
   */
  getCommonPatterns(): string[] {
    return [...COMMON_PATTERNS];
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
      agent_type: "PatternAgent",
      slot_row_id: task.slot_row_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }
}
