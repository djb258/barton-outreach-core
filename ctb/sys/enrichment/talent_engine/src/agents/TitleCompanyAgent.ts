/**
 * TitleCompanyAgent
 * =================
 * Retrieves current title and company from LinkedIn profiles.
 *
 * Services:
 * - Primary: Proxycurl (title/company fields)
 * - Fallback: Apollo (if Proxycurl fails)
 */

import { AgentTask, AgentResult, SlotRow } from "../SlotRow";
import { ProxycurlService, ApolloService, ServiceResponse, ProfileData } from "../services";
import { withRetry } from "../utils/retry";
import { CostGuard } from "../costGuard";
import { agentCosts } from "../costs";

/**
 * Agent configuration.
 */
export interface TitleCompanyConfig {
  proxycurlApiKey: string;
  apolloApiKey?: string;
  enableApolloFallback?: boolean;
}

/**
 * TitleCompanyAgent - Retrieves current title and company from LinkedIn.
 * Uses Proxycurl as primary with Apollo fallback.
 */
export class TitleCompanyAgent {
  private proxycurlService: ProxycurlService | null = null;
  private apolloService: ApolloService | null = null;
  private enableApolloFallback: boolean;

  constructor(config?: TitleCompanyConfig) {
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
   */
  apolloFallbackAllowed(costGuard?: CostGuard): boolean {
    if (!this.enableApolloFallback) return false;
    if (!this.apolloService) return false;

    if (costGuard) {
      const apolloCost = agentCosts.TitleCompanyAgent;
      if (!costGuard.canSpend(apolloCost)) {
        return false;
      }
    }

    return true;
  }

  /**
   * Run the agent to retrieve current title and company.
   *
   * @param task - The agent task to process
   * @param row - The SlotRow to update (optional)
   * @param costGuard - Optional cost guard for fallback decisions
   * @returns AgentResult with title and company info
   */
  async run(
    task: AgentTask,
    row?: SlotRow,
    costGuard?: CostGuard
  ): Promise<AgentResult> {
    try {
      const { linkedin_url, person_name, company_name, slot_type } = task;

      // Need LinkedIn URL for Proxycurl
      if (!linkedin_url) {
        // No LinkedIn URL - try Apollo directly if available
        if (this.apolloFallbackAllowed(costGuard)) {
          return this.tryApolloPath(task, row, company_name, slot_type, person_name);
        }

        return this.createResult(
          task,
          false,
          {},
          "LinkedIn URL is required for title/company lookup"
        );
      }

      // Try Proxycurl first
      const proxycurlResult = await this.getProfileFromProxycurl(linkedin_url);

      if (
        proxycurlResult.success &&
        proxycurlResult.data &&
        (proxycurlResult.data.title || proxycurlResult.data.company)
      ) {
        if (row) {
          row.update({
            current_title: proxycurlResult.data.title ?? null,
            current_company: proxycurlResult.data.company ?? null,
          });
        }

        return this.createResult(task, true, {
          current_title: proxycurlResult.data.title,
          current_company: proxycurlResult.data.company,
          source: "proxycurl",
        });
      }

      // Proxycurl failed → try Apollo (fallback)
      if (this.apolloFallbackAllowed(costGuard)) {
        return this.tryApolloPath(task, row, company_name, slot_type, person_name);
      }

      // Both failed
      return this.createResult(
        task,
        false,
        {},
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
   * Legacy synchronous run method for backwards compatibility.
   */
  runSync(task: AgentTask): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "TitleCompanyAgent",
      slot_row_id: task.slot_row_id,
      success: false,
      data: {},
      error: "Use async run() method for full functionality",
      completed_at: new Date(),
    };
  }

  /**
   * Try Apollo path for title/company lookup.
   */
  private async tryApolloPath(
    task: AgentTask,
    row: SlotRow | undefined,
    companyName: string,
    slotType: string,
    personName: string | null
  ): Promise<AgentResult> {
    const apolloResult = await this.getProfileFromApollo(
      companyName,
      slotType,
      personName
    );

    if (
      apolloResult.success &&
      apolloResult.data &&
      (apolloResult.data.title || apolloResult.data.company)
    ) {
      if (row) {
        row.update({
          current_title: apolloResult.data.title ?? null,
          current_company: apolloResult.data.company ?? null,
        });
      }

      return this.createResult(task, true, {
        current_title: apolloResult.data.title,
        current_company: apolloResult.data.company,
        source: "apollo",
      });
    }

    return this.createResult(
      task,
      false,
      {},
      "Could not retrieve title/company from Apollo"
    );
  }

  /**
   * Get profile from Proxycurl.
   */
  private async getProfileFromProxycurl(
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
   * Get profile from Apollo (FALLBACK ONLY).
   */
  private async getProfileFromApollo(
    companyName: string,
    slotType: string,
    personName: string | null
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
      agent_type: "TitleCompanyAgent",
      slot_row_id: task.slot_row_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }
}
