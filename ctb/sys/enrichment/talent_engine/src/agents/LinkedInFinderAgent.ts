/**
 * LinkedInFinderAgent
 * ===================
 * Finds LinkedIn URLs for people using generic adapter with fallback support.
 *
 * Features:
 * - Primary adapter for LinkedIn URL resolution
 * - Fallback adapter when primary fails
 * - Name parsing and normalization
 * - Existing URL verification
 * - Cost-aware fallback decisions
 */

import { AgentTask, AgentResult, SlotRow } from "../models/SlotRow";
import {
  linkedInResolverAdapter,
  linkedInProfileAdapter,
  LinkedInResolverConfig,
  DEFAULT_LINKEDIN_RESOLVER_CONFIG,
  LinkedInProfileData,
  AdapterResponse,
  AdapterConfig,
  DEFAULT_ADAPTER_CONFIG,
} from "../adapters";

/**
 * Agent configuration.
 */
export interface LinkedInFinderConfig {
  /** Enable fallback adapter */
  enable_fallback: boolean;
  /** Primary adapter config */
  primary_config: Partial<LinkedInResolverConfig>;
  /** Fallback adapter config */
  fallback_config: Partial<LinkedInResolverConfig>;
  /** Enable verbose logging */
  verbose: boolean;
  /** Maximum cost for fallback */
  max_fallback_cost: number;
}

/**
 * Default agent configuration.
 */
export const DEFAULT_LINKEDIN_FINDER_CONFIG: LinkedInFinderConfig = {
  enable_fallback: true,
  primary_config: {
    mock_mode: true,
    timeout_ms: 30000,
  },
  fallback_config: {
    mock_mode: true,
    timeout_ms: 30000,
  },
  verbose: false,
  max_fallback_cost: 0.50,
};

/**
 * Task for LinkedInFinderAgent.
 */
export interface LinkedInFinderTask {
  task_id: string;
  slot_row_id: string;
  person_name: string | null;
  company_name: string;
  slot_type: string;
  linkedin_url?: string | null;
  company_domain?: string;
}

/**
 * LinkedInFinderAgent - Finds LinkedIn URLs for people.
 *
 * Execution Flow:
 * 1. If existing URL provided → verify it
 * 2. Parse person name into first/last
 * 3. Try primary adapter (linkedInResolverAdapter)
 * 4. If primary fails and fallback enabled → try fallback
 * 5. Return result or error
 */
export class LinkedInFinderAgent {
  private config: LinkedInFinderConfig;
  private totalCostIncurred: number = 0;

  constructor(config?: Partial<LinkedInFinderConfig>) {
    this.config = {
      ...DEFAULT_LINKEDIN_FINDER_CONFIG,
      ...config,
    };
  }

  /**
   * Run the agent to find a LinkedIn URL.
   *
   * @param task - The agent task to process
   * @param row - Optional SlotRow to update directly
   * @returns AgentResult with found LinkedIn URL
   */
  async run(task: LinkedInFinderTask, row?: SlotRow): Promise<AgentResult> {
    try {
      // Validate input
      if (!task.person_name && !task.linkedin_url) {
        return this.createResult(task, false, {}, "Person name or existing LinkedIn URL required");
      }

      if (!task.company_name) {
        return this.createResult(task, false, {}, "Company name is required");
      }

      // Step 1: If we have an existing URL, verify it
      if (task.linkedin_url) {
        if (this.config.verbose) {
          console.log(`[LinkedInFinderAgent] Verifying existing URL: ${task.linkedin_url}`);
        }

        const verifyResult = await this.verifyExistingUrl(task.linkedin_url);
        if (verifyResult.success && verifyResult.data) {
          if (row) {
            row.linkedin_url = verifyResult.data.linkedin_url;
            row.last_updated = new Date();
          }
          return this.createResult(task, true, {
            linkedin_url: verifyResult.data.linkedin_url,
            full_name: verifyResult.data.full_name,
            public_accessible: verifyResult.data.public_accessible,
            source: "verified",
            cost: verifyResult.cost || 0,
          });
        }
      }

      // Step 2: Parse person name
      const nameParts = this.parsePersonName(task.person_name);
      if (!nameParts) {
        return this.createResult(task, false, {}, "Could not parse person name");
      }

      if (this.config.verbose) {
        console.log(`[LinkedInFinderAgent] Resolving: ${nameParts.firstName} ${nameParts.lastName} at ${task.company_name}`);
      }

      // Step 3: Try primary adapter
      const primaryResult = await this.tryPrimaryAdapter(nameParts, task);

      if (primaryResult.success && primaryResult.data?.linkedin_url) {
        this.totalCostIncurred += primaryResult.cost || 0;

        if (row) {
          row.linkedin_url = primaryResult.data.linkedin_url;
          row.last_updated = new Date();
        }

        return this.createResult(task, true, {
          linkedin_url: primaryResult.data.linkedin_url,
          full_name: primaryResult.data.full_name,
          title: primaryResult.data.title,
          company: primaryResult.data.company,
          public_accessible: primaryResult.data.public_accessible,
          source: "primary",
          cost: primaryResult.cost || 0,
        });
      }

      // Step 4: Try fallback if enabled and within cost budget
      if (this.config.enable_fallback && this.canUseFallback()) {
        if (this.config.verbose) {
          console.log(`[LinkedInFinderAgent] Primary failed, trying fallback...`);
        }

        const fallbackResult = await this.tryFallbackAdapter(nameParts, task);

        if (fallbackResult.success && fallbackResult.data?.linkedin_url) {
          this.totalCostIncurred += fallbackResult.cost || 0;

          if (row) {
            row.linkedin_url = fallbackResult.data.linkedin_url;
            row.last_updated = new Date();
          }

          return this.createResult(task, true, {
            linkedin_url: fallbackResult.data.linkedin_url,
            full_name: fallbackResult.data.full_name,
            title: fallbackResult.data.title,
            company: fallbackResult.data.company,
            public_accessible: fallbackResult.data.public_accessible,
            source: "fallback",
            cost: fallbackResult.cost || 0,
          });
        }
      }

      // Step 5: All attempts failed
      return this.createResult(
        task,
        false,
        { attempted_sources: ["primary", this.config.enable_fallback ? "fallback" : null].filter(Boolean) },
        "Could not resolve LinkedIn URL"
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
   */
  async runOnRow(row: SlotRow): Promise<SlotRow> {
    const task: LinkedInFinderTask = {
      task_id: `linkedin_${row.id}_${Date.now()}`,
      slot_row_id: row.id,
      person_name: row.person_name,
      company_name: row.company_name || "",
      slot_type: row.slot_type,
      linkedin_url: row.linkedin_url,
    };

    await this.run(task, row);
    return row;
  }

  /**
   * Verify an existing LinkedIn URL.
   */
  private async verifyExistingUrl(
    linkedinUrl: string
  ): Promise<AdapterResponse<LinkedInProfileData>> {
    const config: LinkedInResolverConfig = {
      ...DEFAULT_LINKEDIN_RESOLVER_CONFIG,
      ...this.config.primary_config,
    };

    return linkedInProfileAdapter(linkedinUrl, config);
  }

  /**
   * Try the primary adapter.
   */
  private async tryPrimaryAdapter(
    nameParts: { firstName: string; lastName: string },
    task: LinkedInFinderTask
  ): Promise<AdapterResponse<LinkedInProfileData>> {
    const config: LinkedInResolverConfig = {
      ...DEFAULT_LINKEDIN_RESOLVER_CONFIG,
      ...this.config.primary_config,
    };

    return linkedInResolverAdapter(
      {
        first_name: nameParts.firstName,
        last_name: nameParts.lastName,
        company_name: task.company_name,
        company_domain: task.company_domain,
        title_hint: task.slot_type,
      },
      config
    );
  }

  /**
   * Try the fallback adapter.
   */
  private async tryFallbackAdapter(
    nameParts: { firstName: string; lastName: string },
    task: LinkedInFinderTask
  ): Promise<AdapterResponse<LinkedInProfileData>> {
    const config: LinkedInResolverConfig = {
      ...DEFAULT_LINKEDIN_RESOLVER_CONFIG,
      ...this.config.fallback_config,
    };

    // TODO: In real implementation, this would use a different vendor
    // For now, it uses the same adapter with different config
    return linkedInResolverAdapter(
      {
        first_name: nameParts.firstName,
        last_name: nameParts.lastName,
        company_name: task.company_name,
        company_domain: task.company_domain,
        title_hint: task.slot_type,
      },
      config
    );
  }

  /**
   * Check if fallback can be used within cost budget.
   */
  private canUseFallback(): boolean {
    return this.totalCostIncurred < this.config.max_fallback_cost;
  }

  /**
   * Parse person name into first and last name parts.
   */
  private parsePersonName(
    name: string | null
  ): { firstName: string; lastName: string } | null {
    if (!name) return null;

    const cleanName = name.trim();
    if (!cleanName) return null;

    const parts = cleanName.split(/\s+/);

    if (parts.length === 1) {
      // Single name - use as both first and last
      return { firstName: parts[0], lastName: parts[0] };
    }

    // First part is first name, rest is last name
    return {
      firstName: parts[0],
      lastName: parts.slice(1).join(" "),
    };
  }

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: LinkedInFinderTask,
    success: boolean,
    data: Record<string, unknown>,
    error?: string
  ): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "LinkedInFinderAgent",
      slot_row_id: task.slot_row_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }

  /**
   * Get total cost incurred.
   */
  getTotalCost(): number {
    return this.totalCostIncurred;
  }

  /**
   * Reset cost tracking.
   */
  resetCost(): void {
    this.totalCostIncurred = 0;
  }

  /**
   * Get current configuration.
   */
  getConfig(): LinkedInFinderConfig {
    return { ...this.config };
  }

  /**
   * Update configuration.
   */
  updateConfig(config: Partial<LinkedInFinderConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
