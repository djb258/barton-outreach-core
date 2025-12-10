/**
 * Checklist Logic
 * ===============
 * Layer 2: Slot Completion Checklist Engine
 *
 * Evaluates what pieces are missing from a SlotRow
 * and determines if it's ready for completion.
 */

import { SlotRow } from "../models/SlotRow";

/**
 * Result from checklist evaluation.
 */
export interface ChecklistResult {
  // Missing piece flags
  missing_linkedin: boolean;
  missing_public_flag: boolean;
  missing_pattern: boolean;
  missing_email: boolean;
  missing_title_company: boolean;
  missing_hash: boolean;

  // Aggregates
  total_missing: number;
  total_complete: number;
  completion_percentage: number;

  // Status flags
  ready_for_completion: boolean;
  blocked_by_fuzzy_match: boolean;
  blocked_by_failure: boolean;
}

/**
 * Evaluate the checklist for a SlotRow.
 * Determines what pieces are missing and if the row is ready for completion.
 *
 * @param row - The SlotRow to evaluate
 * @returns ChecklistResult with missing piece flags
 */
export function evaluateChecklist(row: SlotRow): ChecklistResult {
  // Check if blocked by fuzzy match or failure
  const blocked_by_fuzzy_match =
    row.company_name === null || row.fuzzy_match_status !== "MATCHED";
  const blocked_by_failure = row.permanently_failed;

  // Evaluate each checklist item
  const missing_linkedin = row.linkedin_url === null;
  const missing_public_flag = row.public_accessible === null;
  const missing_pattern = row.email_pattern === null;
  const missing_email =
    row.email === null || row.email_verified !== true;
  const missing_title_company =
    row.current_title === null || row.current_company === null;
  const missing_hash = row.movement_hash === null;

  // Count missing and complete items
  const checks = [
    missing_linkedin,
    missing_public_flag,
    missing_pattern,
    missing_email,
    missing_title_company,
    missing_hash,
  ];

  const total_missing = checks.filter(Boolean).length;
  const total_complete = checks.length - total_missing;
  const completion_percentage = Math.round(
    (total_complete / checks.length) * 100
  );

  // Ready for completion if nothing missing and not blocked
  const ready_for_completion =
    total_missing === 0 && !blocked_by_fuzzy_match && !blocked_by_failure;

  return {
    missing_linkedin,
    missing_public_flag,
    missing_pattern,
    missing_email,
    missing_title_company,
    missing_hash,
    total_missing,
    total_complete,
    completion_percentage,
    ready_for_completion,
    blocked_by_fuzzy_match,
    blocked_by_failure,
  };
}

/**
 * Get a summary of missing items as strings.
 *
 * @param checklist - ChecklistResult to summarize
 * @returns Array of missing item names
 */
export function getMissingSummary(checklist: ChecklistResult): string[] {
  const missing: string[] = [];

  if (checklist.missing_linkedin) missing.push("linkedin");
  if (checklist.missing_public_flag) missing.push("public_flag");
  if (checklist.missing_pattern) missing.push("pattern");
  if (checklist.missing_email) missing.push("email");
  if (checklist.missing_title_company) missing.push("title_company");
  if (checklist.missing_hash) missing.push("hash");

  return missing;
}

/**
 * Get the next missing item to process (priority order).
 *
 * Priority:
 * 1. LinkedIn URL
 * 2. Public accessibility flag
 * 3. Email pattern
 * 4. Email generation/verification
 * 5. Title/Company
 * 6. Movement hash
 *
 * @param checklist - ChecklistResult to check
 * @returns Next missing item name or null if complete
 */
export function getNextMissingItem(
  checklist: ChecklistResult
): string | null {
  if (checklist.blocked_by_fuzzy_match) return "fuzzy_match";
  if (checklist.blocked_by_failure) return null; // Permanently blocked
  if (checklist.missing_linkedin) return "linkedin";
  if (checklist.missing_public_flag) return "public_flag";
  if (checklist.missing_pattern) return "pattern";
  if (checklist.missing_email) return "email";
  if (checklist.missing_title_company) return "title_company";
  if (checklist.missing_hash) return "hash";
  return null;
}

/**
 * Map missing item to agent type.
 *
 * @param missingItem - Name of missing item
 * @returns Agent type to handle the missing item
 */
export function mapMissingItemToAgent(
  missingItem: string
): string | null {
  const mapping: Record<string, string> = {
    fuzzy_match: "FuzzyMatchAgent",
    linkedin: "LinkedInFinderAgent",
    public_flag: "PublicScannerAgent",
    pattern: "PatternAgent",
    email: "EmailGeneratorAgent",
    title_company: "TitleCompanyAgent",
    hash: "HashAgent",
  };

  return mapping[missingItem] ?? null;
}

/**
 * Get the agent type needed for a row based on checklist.
 *
 * @param row - SlotRow to check
 * @returns Agent type needed or null if complete
 */
export function getNeededAgent(row: SlotRow): string | null {
  const checklist = evaluateChecklist(row);
  const nextMissing = getNextMissingItem(checklist);

  if (!nextMissing) return null;

  return mapMissingItemToAgent(nextMissing);
}

/**
 * Batch evaluate checklists for multiple rows.
 *
 * @param rows - Array of SlotRows
 * @returns Map of row ID to ChecklistResult
 */
export function batchEvaluateChecklists(
  rows: SlotRow[]
): Map<string, ChecklistResult> {
  const results = new Map<string, ChecklistResult>();

  for (const row of rows) {
    results.set(row.id, evaluateChecklist(row));
  }

  return results;
}

/**
 * Get rows that are ready for completion.
 *
 * @param rows - Array of SlotRows
 * @returns Rows ready for completion
 */
export function getRowsReadyForCompletion(rows: SlotRow[]): SlotRow[] {
  return rows.filter((row) => {
    const checklist = evaluateChecklist(row);
    return checklist.ready_for_completion;
  });
}

/**
 * Get rows that need processing (not complete, not permanently failed).
 *
 * @param rows - Array of SlotRows
 * @returns Rows needing processing
 */
export function getRowsNeedingProcessing(rows: SlotRow[]): SlotRow[] {
  return rows.filter((row) => {
    return !row.slot_complete && !row.permanently_failed;
  });
}
