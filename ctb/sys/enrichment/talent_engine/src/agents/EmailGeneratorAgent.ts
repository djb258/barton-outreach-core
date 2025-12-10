/**
 * EmailGeneratorAgent
 * ===================
 * Generates and verifies email addresses.
 *
 * Services:
 * - Hunter.io: Generate email from pattern
 * - VitaMail: Verify email deliverability
 *
 * If verification = invalid → return warning.
 */

import { AgentTask, AgentResult, SlotRow } from "../SlotRow";
import {
  HunterService,
  VitaMailService,
  ServiceResponse,
  EmailVerificationData,
} from "../services";
import { withRetry } from "../utils/retry";

/**
 * Agent configuration.
 */
export interface EmailGeneratorConfig {
  hunterApiKey?: string;
  vitamailApiKey?: string;
}

/**
 * EmailGeneratorAgent - Generates and verifies email addresses.
 * Uses Hunter.io for generation and VitaMail for verification.
 */
export class EmailGeneratorAgent {
  private hunterService: HunterService | null = null;
  private vitamailService: VitaMailService | null = null;

  constructor(config?: EmailGeneratorConfig) {
    if (config?.hunterApiKey) {
      this.hunterService = new HunterService(config.hunterApiKey);
    }
    if (config?.vitamailApiKey) {
      this.vitamailService = new VitaMailService(config.vitamailApiKey);
    }
  }

  /**
   * Set the Hunter service (for dependency injection/testing).
   */
  setHunterService(service: HunterService): void {
    this.hunterService = service;
  }

  /**
   * Set the VitaMail service (for dependency injection/testing).
   */
  setVitaMailService(service: VitaMailService): void {
    this.vitamailService = service;
  }

  /**
   * Run the agent to generate and verify an email address.
   *
   * @param task - The agent task to process
   * @param row - The SlotRow to update (optional)
   * @returns AgentResult with generated/verified email
   */
  async run(task: AgentTask, row?: SlotRow): Promise<AgentResult> {
    try {
      const { person_name, company_name, context } = task;
      const emailPattern = context?.email_pattern as string | undefined;
      const domain = context?.domain as string | undefined;

      if (!person_name) {
        return this.createResult(
          task,
          false,
          {},
          "Person name is required for email generation"
        );
      }

      // Parse person name
      const nameParts = this.parsePersonName(person_name);
      if (!nameParts) {
        return this.createResult(
          task,
          false,
          {},
          "Could not parse person name"
        );
      }

      // Get domain (from context or infer from company)
      const companyDomain =
        domain ?? this.inferDomainFromCompany(company_name);

      if (!companyDomain) {
        return this.createResult(
          task,
          false,
          {},
          "Could not determine company domain"
        );
      }

      let generatedEmail: string | null = null;

      // Method 1: Use pattern if available
      if (emailPattern && this.hunterService) {
        const patternResult = this.hunterService.generateEmailFromPattern(
          emailPattern,
          companyDomain,
          nameParts.firstName,
          nameParts.lastName
        );

        if (patternResult.success && patternResult.data?.email) {
          generatedEmail = patternResult.data.email;
        }
      }

      // Method 2: Use Hunter email finder
      if (!generatedEmail) {
        const finderResult = await this.findEmail(
          companyDomain,
          nameParts.firstName,
          nameParts.lastName
        );

        if (finderResult.success && finderResult.data?.email) {
          generatedEmail = finderResult.data.email;
        }
      }

      if (!generatedEmail) {
        return this.createResult(
          task,
          false,
          {},
          "Could not generate email address"
        );
      }

      // Verify the email
      const verificationResult = await this.verifyEmail(generatedEmail);

      const isVerified =
        verificationResult.success &&
        verificationResult.data?.status === "valid";

      // Update row
      if (row) {
        row.update({
          email: generatedEmail,
          email_verified: isVerified,
        });
      }

      // Return result with warning if invalid
      if (!isVerified) {
        return this.createResult(task, true, {
          email: generatedEmail,
          email_verified: false,
          verification_status: verificationResult.data?.status ?? "unknown",
          warning: "Email verification failed - use with caution",
        });
      }

      return this.createResult(task, true, {
        email: generatedEmail,
        email_verified: true,
        verification_status: "valid",
      });
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
      agent_type: "EmailGeneratorAgent",
      slot_row_id: task.slot_row_id,
      success: false,
      data: {},
      error: "Use async run() method for full functionality",
      completed_at: new Date(),
    };
  }

  /**
   * Find email using Hunter.io.
   */
  private async findEmail(
    domain: string,
    firstName: string,
    lastName: string
  ): Promise<ServiceResponse<{ email: string; confidence: number }>> {
    if (!this.hunterService) {
      return { success: false, error: "Hunter service not configured" };
    }

    return withRetry(
      () => this.hunterService!.findEmail(domain, firstName, lastName),
      { retries: 2, delay: 200 }
    );
  }

  /**
   * Verify email using VitaMail.
   */
  private async verifyEmail(
    email: string
  ): Promise<ServiceResponse<EmailVerificationData>> {
    if (!this.vitamailService) {
      // No verification service - return unknown status
      return {
        success: true,
        data: {
          email,
          status: "unknown",
          deliverable: false,
        },
      };
    }

    return withRetry(
      () => this.vitamailService!.verifyEmail(email),
      { retries: 2, delay: 200 }
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
   * Infer domain from company name.
   */
  private inferDomainFromCompany(companyName: string): string | null {
    if (!companyName) return null;

    const cleaned = companyName
      .toLowerCase()
      .replace(/\s+(inc|llc|ltd|corp|co|company|corporation)\.?$/i, "")
      .replace(/[^a-z0-9]/g, "")
      .trim();

    if (!cleaned) return null;

    return `${cleaned}.com`;
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
      agent_type: "EmailGeneratorAgent",
      slot_row_id: task.slot_row_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }
}
