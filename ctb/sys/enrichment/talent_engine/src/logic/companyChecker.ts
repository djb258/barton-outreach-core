/**
 * Company Checker Logic
 * =====================
 * Layer 3: Company-Level Missing-Slot Detection
 *
 * Evaluates company state to detect missing slots
 * and triggers MissingSlotAgent when needed.
 */

import { SlotRow, SlotType, ALL_SLOT_TYPES } from "../models/SlotRow";
import {
  CompanyState,
  CompanyStateResult,
  evaluateCompanyState,
} from "../models/CompanyState";

/**
 * Company checker configuration.
 */
export interface CompanyCheckerConfig {
  /** Minimum slots that should be filled (0-4) */
  min_slots_required: number;
  /** Slots that are mandatory for all companies */
  mandatory_slots: SlotType[];
  /** Skip companies with all slots failed */
  skip_all_failed: boolean;
}

/**
 * Default company checker configuration.
 */
export const DEFAULT_CHECKER_CONFIG: CompanyCheckerConfig = {
  min_slots_required: 1,
  mandatory_slots: ["CEO"], // At minimum, need CEO
  skip_all_failed: true,
};

/**
 * Result from company check.
 */
export interface CompanyCheckResult {
  company_id: string;
  company_name: string;
  state: CompanyStateResult;
  missing_mandatory_slots: SlotType[];
  should_trigger_missing_slot_agent: boolean;
  skip_reason: string | null;
}

/**
 * Check a single company's slot state.
 *
 * @param company_id - Company ID
 * @param company_name - Company name
 * @param rows - All slot rows
 * @param config - Checker configuration
 * @returns CompanyCheckResult
 */
export function checkCompany(
  company_id: string,
  company_name: string,
  rows: SlotRow[],
  config: CompanyCheckerConfig = DEFAULT_CHECKER_CONFIG
): CompanyCheckResult {
  // Evaluate company state from rows
  const state = evaluateCompanyState(company_id, company_name, rows);

  // Check for missing mandatory slots
  const missing_mandatory_slots = config.mandatory_slots.filter(
    (slot) => state.missing_slots.includes(slot)
  );

  // Determine if we should skip this company
  let skip_reason: string | null = null;

  if (config.skip_all_failed && state.failed_slots.length === ALL_SLOT_TYPES.length) {
    skip_reason = "All slots permanently failed";
  }

  if (state.is_fully_staffed) {
    skip_reason = "Company is fully staffed";
  }

  // Determine if we should trigger missing slot agent
  const should_trigger_missing_slot_agent =
    skip_reason === null &&
    (state.missing_slots.length > 0 || missing_mandatory_slots.length > 0);

  return {
    company_id,
    company_name,
    state,
    missing_mandatory_slots,
    should_trigger_missing_slot_agent,
    skip_reason,
  };
}

/**
 * Batch check all companies from rows.
 *
 * @param rows - All slot rows
 * @param companyMaster - List of known companies
 * @param config - Checker configuration
 * @returns Array of CompanyCheckResults
 */
export function batchCheckCompanies(
  rows: SlotRow[],
  companyMaster: string[],
  config: CompanyCheckerConfig = DEFAULT_CHECKER_CONFIG
): CompanyCheckResult[] {
  const results: CompanyCheckResult[] = [];

  // Group rows by company
  const companyGroups = new Map<string, SlotRow[]>();

  for (const row of rows) {
    if (row.company_name) {
      const existing = companyGroups.get(row.company_name) ?? [];
      existing.push(row);
      companyGroups.set(row.company_name, existing);
    }
  }

  // Check each company
  for (const company_name of companyMaster) {
    const companyRows = companyGroups.get(company_name) ?? [];
    const company_id = `company_${company_name.toLowerCase().replace(/\s+/g, "_")}`;

    results.push(checkCompany(company_id, company_name, companyRows, config));
  }

  return results;
}

/**
 * Get companies that need missing slot agent.
 *
 * @param checkResults - Array of CompanyCheckResults
 * @returns Companies needing missing slot agent
 */
export function getCompaniesNeedingMissingSlotAgent(
  checkResults: CompanyCheckResult[]
): CompanyCheckResult[] {
  return checkResults.filter((r) => r.should_trigger_missing_slot_agent);
}

/**
 * Get companies with missing mandatory slots.
 *
 * @param checkResults - Array of CompanyCheckResults
 * @returns Companies with missing mandatory slots
 */
export function getCompaniesWithMissingMandatorySlots(
  checkResults: CompanyCheckResult[]
): CompanyCheckResult[] {
  return checkResults.filter((r) => r.missing_mandatory_slots.length > 0);
}

/**
 * Get fully staffed companies.
 *
 * @param checkResults - Array of CompanyCheckResults
 * @returns Fully staffed companies
 */
export function getFullyStaffedCompanies(
  checkResults: CompanyCheckResult[]
): CompanyCheckResult[] {
  return checkResults.filter((r) => r.state.is_fully_staffed);
}

/**
 * Generate a summary report of company states.
 *
 * @param checkResults - Array of CompanyCheckResults
 * @returns Summary string
 */
export function generateCompanySummaryReport(
  checkResults: CompanyCheckResult[]
): string {
  const lines: string[] = ["=== Company State Summary ===", ""];

  let fullyStaffed = 0;
  let needsWork = 0;
  let skipped = 0;

  for (const result of checkResults) {
    if (result.state.is_fully_staffed) {
      fullyStaffed++;
    } else if (result.skip_reason) {
      skipped++;
    } else {
      needsWork++;
    }
  }

  lines.push(`Total Companies: ${checkResults.length}`);
  lines.push(`Fully Staffed: ${fullyStaffed}`);
  lines.push(`Needs Work: ${needsWork}`);
  lines.push(`Skipped: ${skipped}`);
  lines.push("");

  // Detail for companies needing work
  const needingWork = checkResults.filter(
    (r) => !r.state.is_fully_staffed && !r.skip_reason
  );

  if (needingWork.length > 0) {
    lines.push("--- Companies Needing Work ---");
    for (const result of needingWork) {
      const missing = result.state.missing_slots.join(", ") || "none";
      const inProgress = result.state.in_progress_slots.join(", ") || "none";
      lines.push(
        `  ${result.company_name}: Missing=[${missing}], InProgress=[${inProgress}]`
      );
    }
    lines.push("");
  }

  return lines.join("\n");
}

/**
 * Get slots that need to be created for a company.
 *
 * @param result - CompanyCheckResult
 * @returns Array of slot types to create
 */
export function getSlotsToCreate(result: CompanyCheckResult): SlotType[] {
  return result.state.missing_slots;
}

/**
 * Create placeholder SlotRows for missing slots.
 *
 * @param result - CompanyCheckResult
 * @returns Array of new SlotRows (unpersisted)
 */
export function createMissingSlotRows(result: CompanyCheckResult): SlotRow[] {
  const newRows: SlotRow[] = [];

  for (const slotType of result.state.missing_slots) {
    const row = new SlotRow({
      id: `${result.company_id}_${slotType}_${Date.now()}`,
      company_name: result.company_name,
      company_id: result.company_id,
      slot_type: slotType,
      fuzzy_match_status: "MATCHED", // Already matched
    });

    newRows.push(row);
  }

  return newRows;
}
