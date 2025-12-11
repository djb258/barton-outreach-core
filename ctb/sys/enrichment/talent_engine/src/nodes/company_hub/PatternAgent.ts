/**
 * PatternAgent
 * ============
 * Company Hub Node: Email Pattern Discovery Agent
 *
 * Discovers email patterns for companies using generic adapter.
 *
 * Hub-and-Spoke Role:
 * - Part of COMPANY_HUB (master node)
 * - Provides email pattern for People Node email generation
 * - Must complete before EmailGeneratorAgent can run
 *
 * Features:
 * - Primary adapter for email pattern discovery
 * - Domain inference from company name
 * - Pattern confidence scoring
 * - Fallback to common patterns when API fails
 */

import { AgentResult, SlotRow } from "../../models/SlotRow";
import {
  emailPatternAdapter,
  EmailPatternConfig,
  DEFAULT_EMAIL_PATTERN_CONFIG,
  COMMON_EMAIL_PATTERNS,
} from "../../adapters";
import { createEmailPatternFailure } from "../../models/FailureRecord";
import { FailureRouter, globalFailureRouter } from "../../services/FailureRouter";

/**
 * Agent configuration.
 */
export interface PatternAgentConfig extends EmailPatternConfig {
  /** Enable verbose logging */
  verbose: boolean;
  /** Use common patterns as fallback when API fails */
  use_fallback_patterns: boolean;
  /** Minimum confidence to accept pattern */
  min_confidence: number;
  /** Failure router instance */
  failure_router?: FailureRouter;
}

/**
 * Default configuration.
 */
export const DEFAULT_PATTERN_AGENT_CONFIG: PatternAgentConfig = {
  ...DEFAULT_EMAIL_PATTERN_CONFIG,
  verbose: false,
  use_fallback_patterns: true,
  min_confidence: 0.5,
};

/**
 * Task for PatternAgent.
 */
export interface PatternTask {
  task_id: string;
  slot_row_id: string;
  company_name: string;
  company_domain?: string;
}

/**
 * PatternAgent - Discovers email patterns for companies.
 *
 * Execution Flow:
 * 1. Get domain (from task or infer from company name)
 * 2. Call emailPatternAdapter to discover pattern
 * 3. If success → return pattern with confidence
 * 4. If fail and use_fallback_patterns → return most common pattern
 * 5. If fail and no fallback → return error
 */
export class PatternAgent {
  private config: PatternAgentConfig;

  constructor(config?: Partial<PatternAgentConfig>) {
    this.config = {
      ...DEFAULT_PATTERN_AGENT_CONFIG,
      ...config,
    };
  }

  /**
   * Run the agent to discover email pattern for a company.
   */
  async run(task: PatternTask, row?: SlotRow): Promise<AgentResult> {
    try {
      // Validate input
      if (!task.company_name && !task.company_domain) {
        return this.createResult(
          task,
          false,
          {},
          "Company name or domain is required"
        );
      }

      // Get domain (from task or infer from company name)
      const domain = task.company_domain ?? this.inferDomainFromCompany(task.company_name);

      if (!domain) {
        return this.createResult(
          task,
          false,
          {},
          "Could not determine company domain"
        );
      }

      if (this.config.verbose) {
        console.log(`[PatternAgent] Discovering pattern for domain: ${domain}`);
      }

      // Try to discover pattern via adapter
      const result = await emailPatternAdapter(domain, this.config);

      if (result.success && result.data) {
        const pattern = result.data.pattern;
        const confidence = result.data.confidence;

        // Check confidence threshold
        if (confidence >= this.config.min_confidence) {
          if (row) {
            row.email_pattern = pattern;
            row.last_updated = new Date();
          }

          return this.createResult(task, true, {
            email_pattern: pattern,
            domain: result.data.domain,
            confidence,
            sample_emails: result.data.sample_emails,
            source: result.source || "adapter",
            cost: result.cost || 0,
          });
        }

        // Low confidence - try fallback
        if (this.config.verbose) {
          console.log(`[PatternAgent] Low confidence (${confidence}), trying fallback`);
        }
      }

      // Fallback: Use common patterns
      if (this.config.use_fallback_patterns) {
        const fallbackPattern = this.getMostCommonPattern();

        if (this.config.verbose) {
          console.log(`[PatternAgent] Using fallback pattern: ${fallbackPattern}`);
        }

        if (row) {
          row.email_pattern = fallbackPattern;
          row.last_updated = new Date();
        }

        return this.createResult(task, true, {
          email_pattern: fallbackPattern,
          domain,
          confidence: 0.3,
          source: "fallback",
          warning: "Pattern from fallback - verify before use",
        });
      }

      // No pattern found and no fallback
      return this.createResult(
        task,
        false,
        { attempted_domain: domain },
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
   * Run directly on a SlotRow.
   *
   * GOLDEN RULE ENFORCEMENT:
   * If company_valid = false, pattern discovery is SKIPPED.
   * Email generation cannot proceed without a valid company.
   *
   * FAILURE ROUTING:
   * If pattern discovery fails and no fallback, routes to email_pattern_failures bay.
   */
  async runOnRow(row: SlotRow): Promise<SlotRow> {
    const failureRouter = this.config.failure_router || globalFailureRouter;

    // === GOLDEN RULE CHECK ===
    if (row.company_valid === false) {
      const reason = row.company_invalid_reason ?? "Company validation failed";

      if (this.config.verbose) {
        console.log(`[PatternAgent] SKIPPED: company_valid=false for row ${row.id}`);
        console.log(`[PatternAgent] Reason: ${reason}`);
      }

      row.markEmailSkipped(`PatternAgent: ${reason}`);
      return row;
    }

    if (!row.company_name) {
      row.markEmailSkipped("PatternAgent: No company name");
      return row;
    }

    const task: PatternTask = {
      task_id: `pattern_${row.id}_${Date.now()}`,
      slot_row_id: row.id,
      company_name: row.company_name,
      company_domain: (row as any).company_domain ?? undefined,
    };

    const result = await this.run(task, row);

    // Route to failure bay if pattern discovery failed
    if (!result.success) {
      const reason = result.error || "Could not determine email pattern";
      const attemptedSources = ["adapter"];
      if (this.config.use_fallback_patterns) {
        attemptedSources.push("fallback");
      }

      // ROUTE TO FAILURE BAY
      const failure = createEmailPatternFailure(
        row,
        row.company_name,
        (row as any).company_domain || null,
        attemptedSources,
        this.config.use_fallback_patterns,
        reason
      );
      await failureRouter.routeEmailPatternFailure(failure);

      if (this.config.verbose) {
        console.log(`[PatternAgent] FAILED for row ${row.id}: ${reason}`);
        console.log(`[PatternAgent] ROUTED to email_pattern_failures bay`);
      }
    }

    return row;
  }

  /**
   * Get the failure bay for this agent.
   */
  static getFailureBay(): string {
    return "email_pattern_failures";
  }

  /**
   * Infer domain from company name.
   */
  private inferDomainFromCompany(companyName: string): string | null {
    if (!companyName) return null;

    const cleaned = companyName
      .toLowerCase()
      .replace(/\s+(inc|llc|ltd|corp|co|company|corporation|group|holdings)\.?$/i, "")
      .replace(/[^a-z0-9]/g, "")
      .trim();

    if (!cleaned) return null;

    return `${cleaned}.com`;
  }

  /**
   * Get the most common email pattern.
   */
  private getMostCommonPattern(): string {
    return COMMON_EMAIL_PATTERNS[0] || "{first}.{last}";
  }

  /**
   * Get all common patterns.
   */
  getCommonPatterns(): string[] {
    return [...COMMON_EMAIL_PATTERNS];
  }

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: PatternTask,
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

  /**
   * Get current configuration.
   */
  getConfig(): PatternAgentConfig {
    return { ...this.config };
  }

  /**
   * Update configuration.
   */
  updateConfig(config: Partial<PatternAgentConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
