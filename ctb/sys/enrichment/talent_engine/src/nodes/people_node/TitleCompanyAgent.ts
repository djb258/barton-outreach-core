/**
 * TitleCompanyAgent
 * =================
 * People Node: Title and Company Retrieval Agent
 *
 * Retrieves current title and company from LinkedIn profiles using adapters.
 *
 * Hub-and-Spoke Role:
 * - Part of PEOPLE_NODE (spoke)
 * - Requires LinkedIn URL from LinkedInFinderAgent
 * - Feeds data to MovementHashAgent for change detection
 * - Movement signals feed BIT Node
 *
 * Features:
 * - Primary adapter for LinkedIn profile data
 * - Employment movement detection
 * - Fallback to person employment lookup
 * - Cost-aware fallback decisions
 */

import { AgentResult, SlotRow } from "../../models/SlotRow";
import {
  linkedInProfileAdapter,
  personEmploymentLookupAdapter,
  LinkedInResolverConfig,
  PersonEmploymentConfig,
  DEFAULT_LINKEDIN_RESOLVER_CONFIG,
  DEFAULT_PERSON_EMPLOYMENT_CONFIG,
} from "../../adapters";

/**
 * Agent configuration.
 */
export interface TitleCompanyConfig {
  /** LinkedIn profile adapter config */
  linkedin_config: Partial<LinkedInResolverConfig>;
  /** Person employment adapter config */
  employment_config: Partial<PersonEmploymentConfig>;
  /** Enable employment lookup fallback */
  enable_fallback: boolean;
  /** Enable verbose logging */
  verbose: boolean;
  /** Maximum cost for fallback */
  max_fallback_cost: number;
}

/**
 * Default configuration.
 */
export const DEFAULT_TITLE_COMPANY_CONFIG: TitleCompanyConfig = {
  linkedin_config: { mock_mode: true },
  employment_config: { mock_mode: true },
  enable_fallback: true,
  verbose: false,
  max_fallback_cost: 0.50,
};

/**
 * Task for TitleCompanyAgent.
 */
export interface TitleCompanyTask {
  task_id: string;
  slot_row_id: string;
  linkedin_url: string | null;
  person_name: string | null;
  company_name: string;
  slot_type: string;
  previous_title?: string;
  previous_company?: string;
}

/**
 * TitleCompanyAgent - Retrieves current title and company.
 *
 * Execution Flow:
 * 1. If LinkedIn URL provided → call linkedInProfileAdapter
 * 2. If success → extract title/company
 * 3. If fail and fallback enabled → try personEmploymentLookupAdapter
 * 4. Compare with previous values → detect movement
 * 5. Return result with movement flag
 */
export class TitleCompanyAgent {
  private config: TitleCompanyConfig;
  private totalCostIncurred: number = 0;

  constructor(config?: Partial<TitleCompanyConfig>) {
    this.config = {
      ...DEFAULT_TITLE_COMPANY_CONFIG,
      ...config,
    };
  }

  /**
   * Run the agent to retrieve current title and company.
   */
  async run(task: TitleCompanyTask, row?: SlotRow): Promise<AgentResult> {
    try {
      // Need either LinkedIn URL or person name
      if (!task.linkedin_url && !task.person_name) {
        return this.createResult(
          task,
          false,
          {},
          "LinkedIn URL or person name is required"
        );
      }

      if (this.config.verbose) {
        console.log(`[TitleCompanyAgent] Looking up: ${task.person_name || task.linkedin_url}`);
      }

      // Method 1: LinkedIn Profile (if URL available)
      if (task.linkedin_url) {
        const linkedinConfig: LinkedInResolverConfig = {
          ...DEFAULT_LINKEDIN_RESOLVER_CONFIG,
          ...this.config.linkedin_config,
        };

        const profileResult = await linkedInProfileAdapter(task.linkedin_url, linkedinConfig);

        if (profileResult.success && profileResult.data) {
          this.totalCostIncurred += profileResult.cost || 0;

          const currentTitle = profileResult.data.title;
          const currentCompany = profileResult.data.company;

          // Detect movement
          const movement = this.detectMovement(
            task.previous_title,
            task.previous_company,
            currentTitle ?? null,
            currentCompany ?? null
          );

          if (row) {
            row.current_title = currentTitle ?? null;
            row.current_company = currentCompany ?? null;
            row.movement_detected = movement.detected;
            row.last_updated = new Date();
          }

          return this.createResult(task, true, {
            current_title: currentTitle,
            current_company: currentCompany,
            full_name: profileResult.data.full_name,
            public_accessible: profileResult.data.public_accessible,
            movement_detected: movement.detected,
            movement_type: movement.type,
            source: "linkedin_profile",
            cost: profileResult.cost || 0,
          });
        }

        if (this.config.verbose) {
          console.log(`[TitleCompanyAgent] LinkedIn lookup failed: ${profileResult.error}`);
        }
      }

      // Method 2: Person Employment Lookup (fallback)
      if (this.config.enable_fallback && this.canUseFallback()) {
        if (this.config.verbose) {
          console.log(`[TitleCompanyAgent] Trying employment lookup fallback`);
        }

        const employmentConfig: PersonEmploymentConfig = {
          ...DEFAULT_PERSON_EMPLOYMENT_CONFIG,
          ...this.config.employment_config,
        };

        const employmentResult = await personEmploymentLookupAdapter(
          {
            full_name: task.person_name || "",
            company_name: task.company_name,
            linkedin_url: task.linkedin_url ?? undefined,
          },
          employmentConfig
        );

        if (employmentResult.success && employmentResult.data) {
          this.totalCostIncurred += employmentResult.cost || 0;

          const currentTitle = employmentResult.data.current_title;
          const currentCompany = employmentResult.data.current_company;

          // Detect movement
          const movement = this.detectMovement(
            task.previous_title,
            task.previous_company,
            currentTitle ?? null,
            currentCompany ?? null
          );

          if (row) {
            row.current_title = currentTitle ?? null;
            row.current_company = currentCompany ?? null;
            row.linkedin_url = employmentResult.data.linkedin_url ?? row.linkedin_url;
            row.movement_detected = movement.detected;
            row.last_updated = new Date();
          }

          return this.createResult(task, true, {
            current_title: currentTitle,
            current_company: currentCompany,
            linkedin_url: employmentResult.data.linkedin_url,
            employment_history: employmentResult.data.employment_history,
            movement_detected: movement.detected,
            movement_type: movement.type,
            source: "employment_lookup",
            cost: employmentResult.cost || 0,
          });
        }
      }

      // Both methods failed
      return this.createResult(
        task,
        false,
        { attempted_sources: ["linkedin_profile", this.config.enable_fallback ? "employment_lookup" : null].filter(Boolean) },
        "Could not retrieve title/company information"
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
    if (!row.linkedin_url && !row.person_name) {
      return row;
    }

    const task: TitleCompanyTask = {
      task_id: `title_${row.id}_${Date.now()}`,
      slot_row_id: row.id,
      linkedin_url: row.linkedin_url,
      person_name: row.person_name,
      company_name: row.company_name || "",
      slot_type: row.slot_type,
      previous_title: row.current_title ?? undefined,
      previous_company: row.current_company ?? undefined,
    };

    await this.run(task, row);
    return row;
  }

  /**
   * Detect employment movement between old and new values.
   */
  private detectMovement(
    previousTitle: string | null | undefined,
    previousCompany: string | null | undefined,
    currentTitle: string | null,
    currentCompany: string | null
  ): { detected: boolean; type: string | null } {
    // No previous data - can't detect movement
    if (!previousTitle && !previousCompany) {
      return { detected: false, type: null };
    }

    // Company changed
    if (previousCompany && currentCompany) {
      const prevNorm = this.normalizeCompanyName(previousCompany);
      const currNorm = this.normalizeCompanyName(currentCompany);

      if (prevNorm !== currNorm) {
        return { detected: true, type: "company_change" };
      }
    }

    // Title changed (same company)
    if (previousTitle && currentTitle) {
      const prevNorm = previousTitle.toLowerCase().trim();
      const currNorm = currentTitle.toLowerCase().trim();

      if (prevNorm !== currNorm) {
        return { detected: true, type: "title_change" };
      }
    }

    return { detected: false, type: null };
  }

  /**
   * Normalize company name for comparison.
   */
  private normalizeCompanyName(name: string): string {
    return name
      .toLowerCase()
      .replace(/\s+(inc|llc|ltd|corp|co|company|corporation|group|holdings)\.?$/i, "")
      .replace(/[^a-z0-9]/g, "")
      .trim();
  }

  /**
   * Check if fallback can be used within cost budget.
   */
  private canUseFallback(): boolean {
    return this.totalCostIncurred < this.config.max_fallback_cost;
  }

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: TitleCompanyTask,
    success: boolean,
    data: Record<string, unknown>,
    error?: string
  ): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "TitleCompanyAgent",
      slot_row_id: task.slot_row_id,
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

  getConfig(): TitleCompanyConfig {
    return { ...this.config };
  }

  updateConfig(config: Partial<TitleCompanyConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
