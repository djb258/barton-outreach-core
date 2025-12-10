/**
 * LinkedInFinderAgent
 * ===================
 * Finds LinkedIn URLs for people using Proxycurl with Apollo fallback.
 *
 * Services:
 * - Primary: Proxycurl (resolve LinkedIn URL)
 * - Fallback: Apollo (if Proxycurl fails AND cost guard permits)
 */

import { AgentTask, AgentResult, SlotRow } from "../SlotRow";
import { ProxycurlService, ApolloService, ServiceResponse, ProfileData } from "../services";
import { withRetry } from "../utils/retry";
import { CostGuard } from "../costGuard";
import { agentCosts } from "../costs";

/**
 * Agent configuration.
 */
export interface LinkedInFinderConfig {
  proxycurlApiKey: string;
  apolloApiKey?: string;
  enableApolloFallback?: boolean;
}

/**
 * Agent result with extended data.
 */
export interface LinkedInFinderResult {
  updatedRow: SlotRow;
  warning?: string;
  source?: "proxycurl" | "apollo";
}

/**
 * LinkedInFinderAgent - Finds LinkedIn URLs for people.
 * Uses Proxycurl as primary with Apollo fallback.
 */
export class LinkedInFinderAgent {
  private proxycurlService: ProxycurlService | null = null;
  private apolloService: ApolloService | null = null;
  private enableApolloFallback: boolean;

  constructor(config?: LinkedInFinderConfig) {
    if (config?.proxycurlApiKey) {
      this.proxycurlService = new ProxycurlService(config.proxycurlApiKey);
    }
    if (config?.apolloApiKey) {
      this.apolloService = new ApolloService(config.apolloApiKey);
    }
    this.enableApolloFallback = config?.enableApolloFallback ?? true;
  }

  /**
   * Set the Proxycurl service (for dependency injection/testing).
   */
  setProxycurlService(service: ProxycurlService): void {
    this.proxycurlService = service;
  }

  /**
   * Set the Apollo service (for dependency injection/testing).
   */
  setApolloService(service: ApolloService): void {
    this.apolloService = service;
  }

  /**
   * Check if Apollo fallback is allowed.
   * Considers: enabled flag, cost guard, and service availability.
   */
  apolloFallbackAllowed(costGuard?: CostGuard): boolean {
    if (!this.enableApolloFallback) return false;
    if (!this.apolloService) return false;

    // Check cost guard if provided
    if (costGuard) {
      const apolloCost = agentCosts.TitleCompanyAgent; // Apollo uses similar cost
      if (!costGuard.canSpend(apolloCost)) {
        return false;
      }
    }

    return true;
  }

  /**
   * Run the agent to find a LinkedIn URL.
   *
   * @param task - The agent task to process
   * @param row - The SlotRow to update (optional, for direct row updates)
   * @param costGuard - Optional cost guard for fallback decisions
   * @returns AgentResult with found LinkedIn URL
   */
  async run(
    task: AgentTask,
    row?: SlotRow,
    costGuard?: CostGuard
  ): Promise<AgentResult> {
    const startTime = new Date();

    try {
      // Extract person info from task
      const { person_name, company_name, slot_type, linkedin_url } = task;

      // If we already have a LinkedIn URL, just verify it
      if (linkedin_url) {
        const result = await this.verifyExistingUrl(linkedin_url);
        if (result.success && result.data) {
          if (row) {
            row.update({ linkedin_url: result.data.linkedin_url });
          }
          return this.createResult(task, true, {
            linkedin_url: result.data.linkedin_url,
            source: "proxycurl",
          });
        }
      }

      // Parse person name
      const nameParts = this.parsePersonName(person_name);
      if (!nameParts) {
        return this.createResult(task, false, {}, "Person name is required");
      }

      // Try Proxycurl first
      const proxycurlResult = await this.tryProxycurl(nameParts, company_name);

      if (proxycurlResult.success && proxycurlResult.data?.linkedin_url) {
        if (row) {
          row.update({ linkedin_url: proxycurlResult.data.linkedin_url });
        }
        return this.createResult(task, true, {
          linkedin_url: proxycurlResult.data.linkedin_url,
          source: "proxycurl",
        });
      }

      // Proxycurl failed → try Apollo (fallback)
      if (this.apolloFallbackAllowed(costGuard)) {
        const apolloResult = await this.tryApollo(company_name, slot_type, person_name);

        if (apolloResult.success && apolloResult.data?.linkedin_url) {
          if (row) {
            row.update({ linkedin_url: apolloResult.data.linkedin_url });
          }
          return this.createResult(task, true, {
            linkedin_url: apolloResult.data.linkedin_url,
            source: "apollo",
          });
        }
      }

      // Both failed
      return this.createResult(
        task,
        false,
        {},
        "LinkedInFinder could not resolve LinkedIn URL"
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
    // Return stub result for sync calls
    return {
      task_id: task.task_id,
      agent_type: "LinkedInFinderAgent",
      slot_row_id: task.slot_row_id,
      success: false,
      data: {},
      error: "Use async run() method for full functionality",
      completed_at: new Date(),
    };
  }

  /**
   * Verify an existing LinkedIn URL using Proxycurl.
   */
  private async verifyExistingUrl(
    linkedinUrl: string
  ): Promise<ServiceResponse<ProfileData>> {
    if (!this.proxycurlService) {
      return { success: false, error: "Proxycurl service not configured" };
    }

    return withRetry(
      () => this.proxycurlService!.getLinkedInProfile(linkedinUrl),
      { retries: 2, delay: 200 }
    );
  }

  /**
   * Try to find LinkedIn URL using Proxycurl.
   */
  private async tryProxycurl(
    nameParts: { firstName: string; lastName: string },
    companyName: string
  ): Promise<ServiceResponse<{ linkedin_url: string }>> {
    if (!this.proxycurlService) {
      return { success: false, error: "Proxycurl service not configured" };
    }

    return withRetry(
      () =>
        this.proxycurlService!.resolveLinkedInUrl(
          nameParts.firstName,
          nameParts.lastName,
          companyName
        ),
      { retries: 2, delay: 200 }
    );
  }

  /**
   * Try to find LinkedIn URL using Apollo (FALLBACK ONLY).
   */
  private async tryApollo(
    companyName: string,
    slotType: string,
    personName?: string | null
  ): Promise<ServiceResponse<ProfileData>> {
    if (!this.apolloService) {
      return { success: false, error: "Apollo service not configured" };
    }

    return withRetry(
      () =>
        this.apolloService!.enrichPerson(
          companyName,
          slotType,
          personName ?? undefined
        ),
      { retries: 1, delay: 300 }
    );
  }

  /**
   * Parse person name into first and last name parts.
   */
  private parsePersonName(
    name: string | null
  ): { firstName: string; lastName: string } | null {
    if (!name) return null;

    const parts = name.trim().split(/\s+/);
    if (parts.length < 2) {
      return { firstName: parts[0], lastName: parts[0] };
    }

    return {
      firstName: parts[0],
      lastName: parts.slice(1).join(" "),
    };
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
      agent_type: "LinkedInFinderAgent",
      slot_row_id: task.slot_row_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }
}
