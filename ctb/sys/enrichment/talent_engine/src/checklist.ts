/**
 * Checklist Evaluator
 * ===================
 * Evaluates a SlotRow to determine what pieces are missing
 * and whether the row is ready for completion.
 */

import { SlotRow } from "./SlotRow";

/**
 * Result of checklist evaluation.
 */
export interface ChecklistResult {
  missing_linkedin: boolean;
  missing_public_flag: boolean;
  missing_email: boolean;
  missing_pattern: boolean;
  missing_title_company: boolean;
  missing_hash: boolean;
  ready_for_completion: boolean;
}

/**
 * Evaluate a SlotRow to determine missing pieces.
 *
 * ready_for_completion = true only if ALL of these are present:
 * - person_name
 * - linkedin_url
 * - public_accessible !== null
 * - current_title
 * - current_company
 * - email
 * - email_verified === true
 * - movement_hash
 *
 * @param row - The SlotRow to evaluate
 * @returns ChecklistResult with missing flags and completion status
 */
export function evaluateChecklist(row: SlotRow): ChecklistResult {
  // Check individual missing pieces
  const missing_linkedin = !row.linkedin_url;
  const missing_public_flag = row.public_accessible === null;
  const missing_email = !row.email || row.email_verified !== true;
  const missing_pattern = !row.email_pattern;
  const missing_title_company = !row.current_title || !row.current_company;
  const missing_hash = !row.movement_hash;

  // Ready for completion requires ALL pieces present
  const ready_for_completion =
    !!row.person_name &&
    !!row.linkedin_url &&
    row.public_accessible !== null &&
    !!row.current_title &&
    !!row.current_company &&
    !!row.email &&
    row.email_verified === true &&
    !!row.movement_hash;

  return {
    missing_linkedin,
    missing_public_flag,
    missing_email,
    missing_pattern,
    missing_title_company,
    missing_hash,
    ready_for_completion,
  };
}

/**
 * Get a human-readable summary of what's missing.
 *
 * @param result - ChecklistResult from evaluateChecklist
 * @returns Array of missing item descriptions
 */
export function getMissingSummary(result: ChecklistResult): string[] {
  const missing: string[] = [];

  if (result.missing_linkedin) missing.push("LinkedIn URL");
  if (result.missing_public_flag) missing.push("Public Accessibility Flag");
  if (result.missing_email) missing.push("Verified Email");
  if (result.missing_pattern) missing.push("Email Pattern");
  if (result.missing_title_company) missing.push("Title/Company");
  if (result.missing_hash) missing.push("Movement Hash");

  return missing;
}
