/**
 * Fuzzy Match Logic
 * =================
 * Layer 1: Fuzzy Matching Intake Step
 *
 * Handles matching raw company input to the company master list.
 * Uses fuzzy string matching to find best candidates.
 */

import { SlotRow, FuzzyMatchStatus } from "../models/SlotRow";

/**
 * Fuzzy match configuration.
 */
export interface FuzzyMatchConfig {
  /** Minimum score to consider a match (0-100) */
  min_match_score: number;
  /** Score threshold for auto-accept (0-100) */
  auto_accept_threshold: number;
  /** Maximum candidates to return */
  max_candidates: number;
}

/**
 * Default fuzzy match configuration.
 */
export const DEFAULT_FUZZY_CONFIG: FuzzyMatchConfig = {
  min_match_score: 60,
  auto_accept_threshold: 90,
  max_candidates: 5,
};

/**
 * Fuzzy match candidate result.
 */
export interface FuzzyCandidate {
  company_name: string;
  score: number;
  matched_on: string[];
}

/**
 * Result from fuzzy matching operation.
 */
export interface FuzzyMatchResult {
  status: FuzzyMatchStatus;
  best_match: string | null;
  best_score: number | null;
  candidates: FuzzyCandidate[];
  needs_review: boolean;
}

/**
 * Calculate similarity score between two strings.
 * STUB: In production, use rapidfuzz or similar library.
 *
 * @param a - First string
 * @param b - Second string
 * @returns Similarity score 0-100
 */
export function calculateSimilarity(a: string, b: string): number {
  if (!a || !b) return 0;

  const s1 = a.toLowerCase().trim();
  const s2 = b.toLowerCase().trim();

  if (s1 === s2) return 100;

  // Simple Levenshtein-based similarity (stub)
  const longer = s1.length > s2.length ? s1 : s2;
  const shorter = s1.length > s2.length ? s2 : s1;

  if (longer.length === 0) return 100;

  // Check if one contains the other
  if (longer.includes(shorter)) {
    return Math.round((shorter.length / longer.length) * 100);
  }

  // Simple character overlap score
  const set1 = new Set(s1.split(""));
  const set2 = new Set(s2.split(""));
  const intersection = new Set([...set1].filter((x) => set2.has(x)));
  const union = new Set([...set1, ...set2]);

  return Math.round((intersection.size / union.size) * 100);
}

/**
 * Find fuzzy matches for a raw company input against master list.
 *
 * @param rawInput - Raw company name input
 * @param companyMaster - List of known company names
 * @param config - Fuzzy match configuration
 * @returns FuzzyMatchResult with candidates
 */
export function findFuzzyMatches(
  rawInput: string,
  companyMaster: string[],
  config: FuzzyMatchConfig = DEFAULT_FUZZY_CONFIG
): FuzzyMatchResult {
  if (!rawInput) {
    return {
      status: "UNMATCHED",
      best_match: null,
      best_score: null,
      candidates: [],
      needs_review: false,
    };
  }

  const candidates: FuzzyCandidate[] = [];

  // Score against all companies in master
  for (const company of companyMaster) {
    const score = calculateSimilarity(rawInput, company);

    if (score >= config.min_match_score) {
      candidates.push({
        company_name: company,
        score,
        matched_on: ["name_similarity"],
      });
    }
  }

  // Sort by score descending
  candidates.sort((a, b) => b.score - a.score);

  // Limit to max candidates
  const topCandidates = candidates.slice(0, config.max_candidates);

  // Determine status
  if (topCandidates.length === 0) {
    return {
      status: "UNMATCHED",
      best_match: null,
      best_score: null,
      candidates: [],
      needs_review: false,
    };
  }

  const bestCandidate = topCandidates[0];

  // Auto-accept if above threshold
  if (bestCandidate.score >= config.auto_accept_threshold) {
    return {
      status: "MATCHED",
      best_match: bestCandidate.company_name,
      best_score: bestCandidate.score,
      candidates: topCandidates,
      needs_review: false,
    };
  }

  // Needs manual review
  return {
    status: "MANUAL_REVIEW",
    best_match: bestCandidate.company_name,
    best_score: bestCandidate.score,
    candidates: topCandidates,
    needs_review: true,
  };
}

/**
 * Apply fuzzy match result to a SlotRow.
 *
 * @param row - SlotRow to update
 * @param result - FuzzyMatchResult to apply
 */
export function applyFuzzyMatchResult(
  row: SlotRow,
  result: FuzzyMatchResult
): void {
  row.fuzzy_match_status = result.status;
  row.fuzzy_match_score = result.best_score;
  row.fuzzy_match_candidates = result.candidates.map((c) => c.company_name);

  if (result.status === "MATCHED" && result.best_match) {
    row.company_name = result.best_match;
  }

  row.last_updated = new Date();
}

/**
 * Check if a row needs fuzzy matching.
 *
 * @param row - SlotRow to check
 * @returns true if row needs fuzzy matching
 */
export function needsFuzzyMatch(row: SlotRow): boolean {
  return (
    row.company_name === null &&
    row.raw_company_input !== null &&
    row.fuzzy_match_status === "PENDING"
  );
}

/**
 * Get all rows that need fuzzy matching.
 *
 * @param rows - Array of SlotRows
 * @returns Rows that need fuzzy matching
 */
export function getRowsNeedingFuzzyMatch(rows: SlotRow[]): SlotRow[] {
  return rows.filter(needsFuzzyMatch);
}

/**
 * Process fuzzy matching for a single row.
 *
 * @param row - SlotRow to process
 * @param companyMaster - Company master list
 * @param config - Fuzzy match configuration
 * @returns FuzzyMatchResult
 */
export function processFuzzyMatch(
  row: SlotRow,
  companyMaster: string[],
  config: FuzzyMatchConfig = DEFAULT_FUZZY_CONFIG
): FuzzyMatchResult {
  if (!needsFuzzyMatch(row)) {
    return {
      status: row.fuzzy_match_status,
      best_match: row.company_name,
      best_score: row.fuzzy_match_score,
      candidates: row.fuzzy_match_candidates.map((name) => ({
        company_name: name,
        score: 0,
        matched_on: [],
      })),
      needs_review: row.fuzzy_match_status === "MANUAL_REVIEW",
    };
  }

  const result = findFuzzyMatches(
    row.raw_company_input!,
    companyMaster,
    config
  );

  applyFuzzyMatchResult(row, result);

  return result;
}
