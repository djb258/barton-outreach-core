/**
 * SlotRow Data Model
 * ==================
 * Core data structure for the Talent Engine slot-completion pipeline.
 *
 * A SlotRow represents: Company + Slot (CEO/CFO/HR/Benefits) + Person
 * Each slot must complete a checklist before exiting the pipeline.
 *
 * Hub-and-Spoke Architecture:
 * - COMPANY_HUB: FuzzyMatch, CompanyState, Pattern, MissingSlot, EmailGenerator
 * - PEOPLE_NODE: LinkedInFinder, PublicScanner, TitleCompany, MovementHash, PeopleFuzzyMatch
 * - DOL_NODE: DOLSync, RenewalParser, CarrierNormalizer
 * - BIT_NODE: BITScore, ChurnDetector, RenewalIntent
 *
 * VALIDATION FLAGS (Golden Rule Enforcement):
 * - company_valid: Set by CompanyFuzzyMatchAgent when canonical match succeeds
 * - person_company_valid: Set by TitleCompanyAgent when person's employer matches
 * - skip_email: Set by dispatcher or agents when email generation should be skipped
 *
 * IF company_valid = false OR person_company_valid = false:
 *   → Email generation and verification are DISABLED
 */

/**
 * Valid slot types for company positions.
 */
export type SlotType = "CEO" | "CFO" | "HR" | "BENEFITS";

/**
 * All slot types as an array.
 */
export const ALL_SLOT_TYPES: SlotType[] = ["CEO", "CFO", "HR", "BENEFITS"];

/**
 * Agent types that can process slot rows.
 */
export type AgentType =
  | "FuzzyMatchAgent"
  | "CompanyFuzzyMatchAgent"
  | "CompanyStateAgent"
  | "LinkedInFinderAgent"
  | "PublicScannerAgent"
  | "PatternAgent"
  | "EmailGeneratorAgent"
  | "TitleCompanyAgent"
  | "HashAgent"
  | "MovementHashAgent"
  | "MissingSlotAgent"
  | "PeopleFuzzyMatchAgent"
  | "DOLSyncAgent"
  | "RenewalParserAgent"
  | "CarrierNormalizerAgent"
  | "BITScoreAgent"
  | "ChurnDetectorAgent"
  | "RenewalIntentAgent";

/**
 * Default per-slot cost limit in USD.
 */
export const DEFAULT_SLOT_COST_LIMIT = 0.10;

/**
 * Fuzzy match status for intake processing.
 */
export type FuzzyMatchStatus =
  | "PENDING"      // Not yet matched
  | "MATCHED"      // Successfully matched to company master
  | "UNMATCHED"    // Could not find match
  | "MANUAL_REVIEW"; // Requires human review

/**
 * Core SlotRow class representing a slot-completion pipeline row.
 */
export class SlotRow {
  // Identity fields
  id: string;
  company_name: string | null;
  company_id: string | null;
  slot_type: SlotType;
  person_name: string | null;

  // Fuzzy matching fields
  raw_company_input: string | null;
  fuzzy_match_status: FuzzyMatchStatus;
  fuzzy_match_score: number | null;
  fuzzy_match_candidates: string[];

  // LinkedIn fields
  linkedin_url: string | null;
  public_accessible: boolean | null;

  // Email fields
  email: string | null;
  email_pattern: string | null;
  email_verified: boolean | null;

  // Position fields
  current_title: string | null;
  current_company: string | null;

  // Movement tracking
  movement_hash: string | null;

  // === VALIDATION FLAGS (Golden Rule Enforcement) ===
  // Inherited from CompanyState - set by CompanyFuzzyMatchAgent
  company_valid: boolean;
  company_invalid_reason: string | null;

  // Set by TitleCompanyAgent - person's employer matches canonical company
  person_company_valid: boolean;
  person_company_match_score: number | null;

  // Skip email generation flag - set by dispatcher or agents
  skip_email: boolean;
  skip_reason: string | null;

  // Completion status
  slot_complete: boolean;
  last_updated: Date;

  // Cost tracking fields
  slot_cost_accumulated: number;
  slot_cost_limit: number;

  // Failure tracking
  failure_count: number;
  last_failure_reason: string | null;
  permanently_failed: boolean;

  constructor(init: Partial<SlotRow> & { id: string; slot_type: SlotType }) {
    // Identity
    this.id = init.id;
    this.company_name = init.company_name ?? null;
    this.company_id = init.company_id ?? null;
    this.slot_type = init.slot_type;
    this.person_name = init.person_name ?? null;

    // Fuzzy matching
    this.raw_company_input = init.raw_company_input ?? null;
    this.fuzzy_match_status = init.fuzzy_match_status ?? "PENDING";
    this.fuzzy_match_score = init.fuzzy_match_score ?? null;
    this.fuzzy_match_candidates = init.fuzzy_match_candidates ?? [];

    // LinkedIn
    this.linkedin_url = init.linkedin_url ?? null;
    this.public_accessible = init.public_accessible ?? null;

    // Email
    this.email = init.email ?? null;
    this.email_pattern = init.email_pattern ?? null;
    this.email_verified = init.email_verified ?? null;

    // Position
    this.current_title = init.current_title ?? null;
    this.current_company = init.current_company ?? null;

    // Movement
    this.movement_hash = init.movement_hash ?? null;

    // Validation flags (Golden Rule)
    this.company_valid = init.company_valid ?? false; // Default to false until validated
    this.company_invalid_reason = init.company_invalid_reason ?? null;
    this.person_company_valid = init.person_company_valid ?? false; // Default to false until validated
    this.person_company_match_score = init.person_company_match_score ?? null;
    this.skip_email = init.skip_email ?? false;
    this.skip_reason = init.skip_reason ?? null;

    // Completion
    this.slot_complete = init.slot_complete ?? false;
    this.last_updated = init.last_updated ?? new Date();

    // Cost tracking
    this.slot_cost_accumulated = init.slot_cost_accumulated ?? 0;
    this.slot_cost_limit = init.slot_cost_limit ?? DEFAULT_SLOT_COST_LIMIT;

    // Failure tracking
    this.failure_count = init.failure_count ?? 0;
    this.last_failure_reason = init.last_failure_reason ?? null;
    this.permanently_failed = init.permanently_failed ?? false;
  }

  /**
   * Update the row and set last_updated timestamp.
   */
  update(fields: Partial<SlotRow>): void {
    Object.assign(this, fields);
    this.last_updated = new Date();
  }

  /**
   * Check if row needs fuzzy matching.
   */
  needsFuzzyMatch(): boolean {
    return (
      this.company_name === null &&
      this.raw_company_input !== null &&
      this.fuzzy_match_status === "PENDING"
    );
  }

  /**
   * Check if row is ready for slot completion processing.
   */
  isReadyForSlotProcessing(): boolean {
    return (
      this.company_name !== null &&
      this.fuzzy_match_status === "MATCHED" &&
      !this.slot_complete &&
      !this.permanently_failed
    );
  }

  /**
   * Check if email generation is allowed based on validation flags.
   * GOLDEN RULE: Both company and person must be valid.
   */
  isEmailGenerationAllowed(): boolean {
    return (
      this.company_valid === true &&
      this.person_company_valid === true &&
      this.skip_email === false &&
      this.email_pattern !== null
    );
  }

  /**
   * Mark email as skipped with reason.
   */
  markEmailSkipped(reason: string): void {
    this.skip_email = true;
    this.skip_reason = reason;
    this.last_updated = new Date();
  }

  /**
   * Set company validation status.
   */
  setCompanyValid(valid: boolean, reason?: string): void {
    this.company_valid = valid;
    this.company_invalid_reason = valid ? null : (reason ?? "Company validation failed");
    this.last_updated = new Date();

    // If company is invalid, also skip email
    if (!valid) {
      this.markEmailSkipped(reason ?? "Company validation failed");
    }
  }

  /**
   * Set person-company validation status.
   */
  setPersonCompanyValid(valid: boolean, matchScore?: number, reason?: string): void {
    this.person_company_valid = valid;
    this.person_company_match_score = matchScore ?? null;
    this.last_updated = new Date();

    // If person-company match is invalid, also skip email
    if (!valid) {
      this.markEmailSkipped(reason ?? "Person not matched to canonical company");
    }
  }

  /**
   * Get validation status summary.
   */
  getValidationSummary(): {
    company_valid: boolean;
    person_company_valid: boolean;
    skip_email: boolean;
    skip_reason: string | null;
    email_allowed: boolean;
  } {
    return {
      company_valid: this.company_valid,
      person_company_valid: this.person_company_valid,
      skip_email: this.skip_email,
      skip_reason: this.skip_reason,
      email_allowed: this.isEmailGenerationAllowed(),
    };
  }

  /**
   * Mark row as failed with reason.
   */
  markFailed(reason: string, permanent: boolean = false): void {
    this.failure_count++;
    this.last_failure_reason = reason;
    this.permanently_failed = permanent;
    this.last_updated = new Date();
  }

  /**
   * Reset failure state (for manual retry).
   */
  resetFailure(): void {
    this.failure_count = 0;
    this.last_failure_reason = null;
    this.permanently_failed = false;
    this.last_updated = new Date();
  }
}

/**
 * Task sent to an agent for processing.
 */
export interface AgentTask {
  task_id: string;
  agent_type: AgentType;
  slot_row_id: string;
  company_name: string | null;
  company_id: string | null;
  slot_type: SlotType;
  person_name: string | null;
  linkedin_url: string | null;
  context: Record<string, unknown>;
  created_at: Date;
}

/**
 * Result returned by an agent after processing.
 */
export interface AgentResult {
  task_id: string;
  agent_type: AgentType;
  slot_row_id: string;
  success: boolean;
  data: Record<string, unknown>;
  error: string | null;
  completed_at: Date;
}

/**
 * Dispatcher result status.
 */
export type DispatchStatus =
  | "ROUTED"
  | "THROTTLED"
  | "KILLED"
  | "COMPLETED"
  | "NO_ACTION"
  | "COST_EXCEEDED"
  | "FAILED"
  | "FUZZY_MATCH_NEEDED"
  | "MISSING_SLOTS_DETECTED";

/**
 * Result from dispatcher routing.
 */
export interface DispatchResult {
  status: DispatchStatus;
  agent_type: AgentType | null;
  task: AgentTask | null;
  reason: string;
  cost_incurred?: number;
  lanes_activated?: string[];
}
