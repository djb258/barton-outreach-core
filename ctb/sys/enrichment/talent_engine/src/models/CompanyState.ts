/**
 * CompanyState Data Model
 * =======================
 * Represents the slot-fill state for a single company.
 * Used by the Company-Level Missing-Slot Detection layer.
 */

import { SlotType, ALL_SLOT_TYPES, SlotRow } from "./SlotRow";

/**
 * Status of a single slot for a company.
 */
export type SlotStatus =
  | "FILLED"      // Slot has a complete row
  | "IN_PROGRESS" // Slot has a row but not complete
  | "MISSING"     // No row exists for this slot
  | "FAILED";     // Row exists but permanently failed

/**
 * Individual slot state within a company.
 */
export interface SlotState {
  slot_type: SlotType;
  status: SlotStatus;
  slot_row_id: string | null;
  person_name: string | null;
  completion_percentage: number;
}

/**
 * Company-level state tracking all slots.
 *
 * VALIDATION FLAGS:
 * - company_valid: true only if CompanyFuzzyMatchAgent successfully matched
 * - reason_invalid: explanation if company_valid is false
 *
 * GOLDEN RULE: If company_valid = false, NO downstream processing occurs.
 */
export class CompanyState {
  company_id: string;
  company_name: string;
  slots: Map<SlotType, SlotState>;
  last_evaluated: Date;

  // === VALIDATION FLAGS ===
  company_valid: boolean;
  reason_invalid: string | null;

  // Company metadata from fuzzy match
  canonical_company_name: string | null;
  domain: string | null;
  email_pattern: string | null;
  fuzzy_match_score: number | null;

  constructor(company_id: string, company_name: string) {
    this.company_id = company_id;
    this.company_name = company_name;
    this.slots = new Map();
    this.last_evaluated = new Date();

    // Validation flags - default to false until validated
    this.company_valid = false;
    this.reason_invalid = null;

    // Company metadata
    this.canonical_company_name = null;
    this.domain = null;
    this.email_pattern = null;
    this.fuzzy_match_score = null;

    // Initialize all slots as MISSING
    for (const slotType of ALL_SLOT_TYPES) {
      this.slots.set(slotType, {
        slot_type: slotType,
        status: "MISSING",
        slot_row_id: null,
        person_name: null,
        completion_percentage: 0,
      });
    }
  }

  /**
   * Set company as valid after successful fuzzy match.
   */
  setValid(
    canonicalName: string,
    matchScore: number,
    domain?: string,
    pattern?: string
  ): void {
    this.company_valid = true;
    this.reason_invalid = null;
    this.canonical_company_name = canonicalName;
    this.fuzzy_match_score = matchScore;
    this.domain = domain ?? null;
    this.email_pattern = pattern ?? null;
    this.last_evaluated = new Date();
  }

  /**
   * Set company as invalid with reason.
   */
  setInvalid(reason: string): void {
    this.company_valid = false;
    this.reason_invalid = reason;
    this.last_evaluated = new Date();
  }

  /**
   * Check if company can proceed to email generation.
   * GOLDEN RULE: Must have valid company + domain + pattern.
   */
  canGenerateEmails(): boolean {
    return (
      this.company_valid === true &&
      this.domain !== null &&
      this.email_pattern !== null
    );
  }

  /**
   * Update a slot's state from a SlotRow.
   */
  updateSlotFromRow(row: SlotRow): void {
    const slotState: SlotState = {
      slot_type: row.slot_type,
      slot_row_id: row.id,
      person_name: row.person_name,
      status: this.determineSlotStatus(row),
      completion_percentage: this.calculateCompletionPercentage(row),
    };

    this.slots.set(row.slot_type, slotState);
    this.last_evaluated = new Date();
  }

  /**
   * Determine slot status from row state.
   */
  private determineSlotStatus(row: SlotRow): SlotStatus {
    if (row.permanently_failed) {
      return "FAILED";
    }
    if (row.slot_complete) {
      return "FILLED";
    }
    return "IN_PROGRESS";
  }

  /**
   * Calculate completion percentage for a row.
   * Based on checklist items filled.
   */
  private calculateCompletionPercentage(row: SlotRow): number {
    const checks = [
      row.linkedin_url !== null,
      row.public_accessible !== null,
      row.email_pattern !== null,
      row.email !== null && row.email_verified === true,
      row.current_title !== null && row.current_company !== null,
      row.movement_hash !== null,
    ];

    const filled = checks.filter(Boolean).length;
    return Math.round((filled / checks.length) * 100);
  }

  /**
   * Get all missing slots.
   */
  getMissingSlots(): SlotType[] {
    const missing: SlotType[] = [];
    for (const [slotType, state] of this.slots) {
      if (state.status === "MISSING") {
        missing.push(slotType);
      }
    }
    return missing;
  }

  /**
   * Get all slots that are in progress.
   */
  getInProgressSlots(): SlotType[] {
    const inProgress: SlotType[] = [];
    for (const [slotType, state] of this.slots) {
      if (state.status === "IN_PROGRESS") {
        inProgress.push(slotType);
      }
    }
    return inProgress;
  }

  /**
   * Get all filled slots.
   */
  getFilledSlots(): SlotType[] {
    const filled: SlotType[] = [];
    for (const [slotType, state] of this.slots) {
      if (state.status === "FILLED") {
        filled.push(slotType);
      }
    }
    return filled;
  }

  /**
   * Get all failed slots.
   */
  getFailedSlots(): SlotType[] {
    const failed: SlotType[] = [];
    for (const [slotType, state] of this.slots) {
      if (state.status === "FAILED") {
        failed.push(slotType);
      }
    }
    return failed;
  }

  /**
   * Check if company has all slots filled.
   */
  isFullyStaffed(): boolean {
    for (const state of this.slots.values()) {
      if (state.status !== "FILLED") {
        return false;
      }
    }
    return true;
  }

  /**
   * Get overall company completion percentage.
   */
  getOverallCompletion(): number {
    let totalPercentage = 0;
    for (const state of this.slots.values()) {
      totalPercentage += state.completion_percentage;
    }
    return Math.round(totalPercentage / ALL_SLOT_TYPES.length);
  }

  /**
   * Get a summary string of company state.
   */
  getSummary(): string {
    const filled = this.getFilledSlots().length;
    const inProgress = this.getInProgressSlots().length;
    const missing = this.getMissingSlots().length;
    const failed = this.getFailedSlots().length;

    return `${this.company_name}: ${filled} filled, ${inProgress} in-progress, ${missing} missing, ${failed} failed (${this.getOverallCompletion()}% complete)`;
  }
}

/**
 * Result from company state evaluation.
 */
export interface CompanyStateResult {
  company_id: string;
  company_name: string;
  state: CompanyState;
  missing_slots: SlotType[];
  in_progress_slots: SlotType[];
  filled_slots: SlotType[];
  failed_slots: SlotType[];
  is_fully_staffed: boolean;
  overall_completion: number;
  needs_missing_slot_agent: boolean;

  // Validation results
  company_valid: boolean;
  reason_invalid: string | null;
  can_generate_emails: boolean;
}

/**
 * Evaluate company state from slot rows.
 */
export function evaluateCompanyState(
  company_id: string,
  company_name: string,
  rows: SlotRow[]
): CompanyStateResult {
  const state = new CompanyState(company_id, company_name);

  // Update state from all rows for this company
  for (const row of rows) {
    if (row.company_id === company_id || row.company_name === company_name) {
      state.updateSlotFromRow(row);

      // Inherit company_valid from the first row that has been validated
      if (row.company_valid !== undefined) {
        state.company_valid = row.company_valid;
        state.reason_invalid = row.company_invalid_reason ?? null;
      }
    }
  }

  const missingSlots = state.getMissingSlots();

  return {
    company_id,
    company_name,
    state,
    missing_slots: missingSlots,
    in_progress_slots: state.getInProgressSlots(),
    filled_slots: state.getFilledSlots(),
    failed_slots: state.getFailedSlots(),
    is_fully_staffed: state.isFullyStaffed(),
    overall_completion: state.getOverallCompletion(),
    needs_missing_slot_agent: missingSlots.length > 0,

    // Validation results
    company_valid: state.company_valid,
    reason_invalid: state.reason_invalid,
    can_generate_emails: state.canGenerateEmails(),
  };
}
