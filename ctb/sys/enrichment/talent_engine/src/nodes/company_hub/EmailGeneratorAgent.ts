/**
 * EmailGeneratorAgent
 * ===================
 * Company Hub Node: Email Generation Agent
 *
 * Generates and verifies email addresses using generic adapters.
 *
 * Hub-and-Spoke Role:
 * - Part of COMPANY_HUB (master node)
 * - Uses pattern from PatternAgent + person data from People Node
 * - Provides verified emails back to People Node
 *
 * Features:
 * - Generate email from pattern + name + domain
 * - Verify email deliverability
 * - Multi-pattern generation when single pattern fails
 * - Cost-aware verification decisions
 */

import { AgentResult, SlotRow } from "../../models/SlotRow";
import {
  generateEmailFromPattern,
  emailFinderAdapter,
  emailVerificationAdapter,
  quickEmailValidation,
  EmailPatternConfig,
  EmailVerificationConfig,
  DEFAULT_EMAIL_PATTERN_CONFIG,
  DEFAULT_EMAIL_VERIFICATION_CONFIG,
  COMMON_EMAIL_PATTERNS,
} from "../../adapters";

/**
 * Agent configuration.
 */
export interface EmailGeneratorConfig {
  /** Pattern adapter config */
  pattern_config: Partial<EmailPatternConfig>;
  /** Verification adapter config */
  verification_config: Partial<EmailVerificationConfig>;
  /** Enable email verification */
  enable_verification: boolean;
  /** Try multiple patterns if first fails verification */
  try_multiple_patterns: boolean;
  /** Maximum patterns to try */
  max_patterns_to_try: number;
  /** Enable verbose logging */
  verbose: boolean;
}

/**
 * Default configuration.
 */
export const DEFAULT_EMAIL_GENERATOR_CONFIG: EmailGeneratorConfig = {
  pattern_config: { mock_mode: true },
  verification_config: { mock_mode: true },
  enable_verification: true,
  try_multiple_patterns: true,
  max_patterns_to_try: 3,
  verbose: false,
};

/**
 * Task for EmailGeneratorAgent.
 */
export interface EmailGeneratorTask {
  task_id: string;
  slot_row_id: string;
  person_name: string | null;
  company_name: string;
  company_domain?: string;
  email_pattern?: string;
}

/**
 * EmailGeneratorAgent - Generates and verifies email addresses.
 *
 * Execution Flow:
 * 1. Parse person name into first/last
 * 2. Get domain (from task or infer)
 * 3. If pattern provided → generate email from pattern
 * 4. If no pattern → try emailFinderAdapter
 * 5. Optionally verify email
 * 6. If verification fails and try_multiple_patterns → try next pattern
 * 7. Return best email found (with verification status)
 */
export class EmailGeneratorAgent {
  private config: EmailGeneratorConfig;

  constructor(config?: Partial<EmailGeneratorConfig>) {
    this.config = {
      ...DEFAULT_EMAIL_GENERATOR_CONFIG,
      ...config,
    };
  }

  /**
   * Run the agent to generate and verify an email address.
   */
  async run(task: EmailGeneratorTask, row?: SlotRow): Promise<AgentResult> {
    try {
      // Validate input
      if (!task.person_name) {
        return this.createResult(
          task,
          false,
          {},
          "Person name is required for email generation"
        );
      }

      // Parse person name
      const nameParts = this.parsePersonName(task.person_name);
      if (!nameParts) {
        return this.createResult(
          task,
          false,
          {},
          "Could not parse person name"
        );
      }

      // Get domain
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
        console.log(`[EmailGeneratorAgent] Generating email for ${nameParts.firstName} ${nameParts.lastName} @ ${domain}`);
      }

      // Patterns to try
      const patternsToTry = this.getPatternsToTry(task.email_pattern);
      let bestEmail: string | null = null;
      let bestResult: {
        email: string;
        verified: boolean;
        verification_status: string;
        source: string;
        cost: number;
      } | null = null;

      // Method 1: Generate from patterns
      for (const pattern of patternsToTry) {
        const email = generateEmailFromPattern(
          pattern,
          domain,
          nameParts.firstName,
          nameParts.lastName
        );

        // Quick format validation
        const quickCheck = quickEmailValidation(email);
        if (!quickCheck.valid) {
          if (this.config.verbose) {
            console.log(`[EmailGeneratorAgent] Pattern ${pattern} produced invalid email: ${email}`);
          }
          continue;
        }

        // Full verification if enabled
        if (this.config.enable_verification) {
          const verifyConfig: EmailVerificationConfig = {
            ...DEFAULT_EMAIL_VERIFICATION_CONFIG,
            ...this.config.verification_config,
          };

          const verifyResult = await emailVerificationAdapter(email, verifyConfig);

          if (verifyResult.success && verifyResult.data) {
            const isValid = verifyResult.data.status === "valid" ||
                           verifyResult.data.status === "catch_all";

            if (isValid) {
              if (row) {
                row.email = email;
                row.email_verified = true;
                row.last_updated = new Date();
              }

              return this.createResult(task, true, {
                email,
                email_verified: true,
                verification_status: verifyResult.data.status,
                pattern_used: pattern,
                source: "pattern_generation",
                cost: verifyResult.cost || 0,
              });
            }

            if (!bestResult || verifyResult.data.status !== "invalid") {
              bestEmail = email;
              bestResult = {
                email,
                verified: false,
                verification_status: verifyResult.data.status,
                source: "pattern_generation",
                cost: verifyResult.cost || 0,
              };
            }

            if (this.config.try_multiple_patterns) {
              if (this.config.verbose) {
                console.log(`[EmailGeneratorAgent] Email ${email} verification: ${verifyResult.data.status}, trying next pattern`);
              }
              continue;
            }
          }
        } else {
          if (row) {
            row.email = email;
            row.email_verified = false;
            row.last_updated = new Date();
          }

          return this.createResult(task, true, {
            email,
            email_verified: false,
            verification_status: "not_verified",
            pattern_used: pattern,
            source: "pattern_generation",
            warning: "Email not verified - verification disabled",
          });
        }
      }

      // Method 2: Try email finder adapter
      if (this.config.verbose) {
        console.log(`[EmailGeneratorAgent] Pattern generation exhausted, trying email finder`);
      }

      const patternConfig: EmailPatternConfig = {
        ...DEFAULT_EMAIL_PATTERN_CONFIG,
        ...this.config.pattern_config,
      };

      const finderResult = await emailFinderAdapter(
        domain,
        nameParts.firstName,
        nameParts.lastName,
        patternConfig
      );

      if (finderResult.success && finderResult.data?.email) {
        const email = finderResult.data.email;
        const confidence = finderResult.data.confidence;

        if (row) {
          row.email = email;
          row.email_verified = confidence >= 0.9;
          row.last_updated = new Date();
        }

        return this.createResult(task, true, {
          email,
          email_verified: confidence >= 0.9,
          verification_status: confidence >= 0.9 ? "high_confidence" : "low_confidence",
          confidence,
          source: "email_finder",
          cost: finderResult.cost || 0,
        });
      }

      // Return best unverified email if we have one
      if (bestEmail && bestResult) {
        if (row) {
          row.email = bestEmail;
          row.email_verified = false;
          row.last_updated = new Date();
        }

        return this.createResult(task, true, {
          ...bestResult,
          warning: "Email verification failed - use with caution",
        });
      }

      // Nothing worked
      return this.createResult(
        task,
        false,
        { attempted_domain: domain },
        "Could not generate valid email address"
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
    if (!row.person_name || !row.company_name) {
      return row;
    }

    const task: EmailGeneratorTask = {
      task_id: `email_${row.id}_${Date.now()}`,
      slot_row_id: row.id,
      person_name: row.person_name,
      company_name: row.company_name,
      company_domain: row.company_domain ?? undefined,
      email_pattern: row.email_pattern ?? undefined,
    };

    await this.run(task, row);
    return row;
  }

  /**
   * Get patterns to try.
   */
  private getPatternsToTry(taskPattern?: string): string[] {
    const patterns: string[] = [];

    if (taskPattern) {
      patterns.push(taskPattern);
    }

    for (const pattern of COMMON_EMAIL_PATTERNS) {
      if (!patterns.includes(pattern)) {
        patterns.push(pattern);
      }
      if (patterns.length >= this.config.max_patterns_to_try) {
        break;
      }
    }

    return patterns;
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
      .replace(/\s+(inc|llc|ltd|corp|co|company|corporation|group|holdings)\.?$/i, "")
      .replace(/[^a-z0-9]/g, "")
      .trim();

    if (!cleaned) return null;

    return `${cleaned}.com`;
  }

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: EmailGeneratorTask,
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

  /**
   * Get current configuration.
   */
  getConfig(): EmailGeneratorConfig {
    return { ...this.config };
  }

  /**
   * Update configuration.
   */
  updateConfig(config: Partial<EmailGeneratorConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
