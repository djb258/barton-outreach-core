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
import { createPersonCompanyMismatchFailure } from "../../models/FailureRecord";
import { FailureRouter, globalFailureRouter } from "../../services/FailureRouter";

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
  /** Minimum confidence threshold for person-company match */
  person_company_match_threshold: number;
  /** Failure router instance */
  failure_router?: FailureRouter;
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
  person_company_match_threshold: 0.85, // 85% confidence required
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
   *
   * SETS PERSON_COMPANY_VALID FLAG:
   * After retrieving current title/company, compares the scraped employer
   * to the canonical company_name on the row.
   *
   * - If match >= threshold (85%): person_company_valid = true
   * - If match < threshold: person_company_valid = false, skip_email = true
   *
   * GOLDEN RULE: Email generation requires person_company_valid = true
   *
   * FAILURE ROUTING:
   * If person_company_valid = false, routes to person_company_mismatch failure bay.
   */
  async runOnRow(row: SlotRow): Promise<SlotRow> {
    const failureRouter = this.config.failure_router || globalFailureRouter;

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

    const result = await this.run(task, row);

    // === SET PERSON_COMPANY_VALID FLAG ===
    if (result.success && result.data.current_company) {
      const scrapedCompany = result.data.current_company as string;
      const canonicalCompany = row.company_name || "";

      // Compare scraped employer to canonical company
      const matchScore = this.calculateCompanyMatchScore(scrapedCompany, canonicalCompany);

      if (matchScore >= this.config.person_company_match_threshold) {
        // Person's employer matches canonical company
        row.setPersonCompanyValid(true, matchScore);

        if (this.config.verbose) {
          console.log(`[TitleCompanyAgent] person_company_valid=TRUE for row ${row.id} (score: ${matchScore})`);
        }
      } else {
        // Person's employer does NOT match canonical company
        const reason = `Person employer "${scrapedCompany}" does not match canonical company "${canonicalCompany}" (score: ${matchScore})`;
        row.setPersonCompanyValid(false, matchScore, reason);

        // ROUTE TO FAILURE BAY
        const failure = createPersonCompanyMismatchFailure(
          row,
          canonicalCompany,
          scrapedCompany,
          matchScore,
          this.config.person_company_match_threshold,
          reason
        );
        await failureRouter.routePersonCompanyMismatch(failure);

        if (this.config.verbose) {
          console.log(`[TitleCompanyAgent] person_company_valid=FALSE for row ${row.id}`);
          console.log(`[TitleCompanyAgent] Scraped: "${scrapedCompany}" vs Canonical: "${canonicalCompany}" (score: ${matchScore})`);
          console.log(`[TitleCompanyAgent] ROUTED to person_company_mismatch failure bay`);
        }
      }
    } else if (!result.success) {
      // Could not retrieve employment info - cannot validate
      const reason = "Could not retrieve current employer for validation";
      row.setPersonCompanyValid(false, 0, reason);

      // ROUTE TO FAILURE BAY
      const failure = createPersonCompanyMismatchFailure(
        row,
        row.company_name || "",
        null,
        0,
        this.config.person_company_match_threshold,
        reason
      );
      await failureRouter.routePersonCompanyMismatch(failure);

      if (this.config.verbose) {
        console.log(`[TitleCompanyAgent] person_company_valid=FALSE (no data) for row ${row.id}`);
        console.log(`[TitleCompanyAgent] ROUTED to person_company_mismatch failure bay`);
      }
    }

    return row;
  }

  /**
   * Get the failure bay for this agent.
   */
  static getFailureBay(): string {
    return "person_company_mismatch";
  }

  /**
   * Calculate similarity score between scraped company and canonical company.
   */
  private calculateCompanyMatchScore(scrapedCompany: string, canonicalCompany: string): number {
    if (!scrapedCompany || !canonicalCompany) return 0;

    const normScraped = this.normalizeCompanyName(scrapedCompany);
    const normCanonical = this.normalizeCompanyName(canonicalCompany);

    // Exact match after normalization
    if (normScraped === normCanonical) return 1.0;

    // Contains check
    if (normScraped.includes(normCanonical) || normCanonical.includes(normScraped)) {
      const longer = Math.max(normScraped.length, normCanonical.length);
      const shorter = Math.min(normScraped.length, normCanonical.length);
      return shorter / longer;
    }

    // Levenshtein-based similarity
    const distance = this.levenshteinDistance(normScraped, normCanonical);
    const maxLen = Math.max(normScraped.length, normCanonical.length);
    if (maxLen === 0) return 0;

    return (maxLen - distance) / maxLen;
  }

  /**
   * Calculate Levenshtein distance between two strings.
   */
  private levenshteinDistance(a: string, b: string): number {
    const matrix: number[][] = [];

    for (let i = 0; i <= b.length; i++) {
      matrix[i] = [i];
    }
    for (let j = 0; j <= a.length; j++) {
      matrix[0][j] = j;
    }

    for (let i = 1; i <= b.length; i++) {
      for (let j = 1; j <= a.length; j++) {
        if (b.charAt(i - 1) === a.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j] + 1
          );
        }
      }
    }

    return matrix[b.length][a.length];
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
