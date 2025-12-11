/**
 * CompanyFuzzyMatchAgent
 * ======================
 * Company Hub Node: Fuzzy Matching Agent
 *
 * Responsible for matching raw company input to known company names.
 * Runs BEFORE any other processing - no slot work should happen
 * until company_name is resolved.
 *
 * Hub-and-Spoke Role:
 * - Part of COMPANY_HUB (master node)
 * - All other nodes depend on company resolution
 * - Must complete before People, DOL, or BIT nodes can process
 *
 * Features:
 * - String normalization (lowercase, strip punctuation, remove LLC/Inc/etc.)
 * - Similarity scoring with multiple algorithms
 * - Fallback to external company lookup when local match fails
 */

import { AgentResult, SlotRow } from "../../models/SlotRow";
import { createCompanyFuzzyFailure } from "../../models/FailureRecord";
import {
  FuzzyMatchConfig,
  FuzzyMatchResult,
  FuzzyCandidate,
  DEFAULT_FUZZY_CONFIG,
} from "../../logic/fuzzyMatch";
import {
  externalCompanyLookupAdapter,
  CompanyLookupConfig,
  DEFAULT_COMPANY_LOOKUP_CONFIG,
} from "../../adapters/companyLookupAdapter";
import { FailureRouter, globalFailureRouter } from "../../services/FailureRouter";

/**
 * Agent configuration.
 */
export interface CompanyFuzzyMatchAgentConfig extends FuzzyMatchConfig {
  /** Enable detailed logging */
  verbose?: boolean;
  /** Enable external lookup fallback */
  enable_external_fallback?: boolean;
  /** External lookup adapter config */
  external_config?: Partial<CompanyLookupConfig>;
  /** Failure router instance */
  failure_router?: FailureRouter;
}

/**
 * Default agent configuration.
 */
export const DEFAULT_COMPANY_FUZZY_MATCH_CONFIG: CompanyFuzzyMatchAgentConfig = {
  ...DEFAULT_FUZZY_CONFIG,
  verbose: false,
  enable_external_fallback: true,
  external_config: {
    mock_mode: true,
    min_confidence: 0.7,
  },
};

/**
 * Task specific to CompanyFuzzyMatchAgent.
 */
export interface CompanyFuzzyMatchTask {
  task_id: string;
  slot_row_id: string;
  raw_company_input: string;
  company_master: string[];
}

/**
 * Company suffixes to strip during normalization.
 */
const COMPANY_SUFFIXES = [
  "inc",
  "incorporated",
  "corp",
  "corporation",
  "llc",
  "llp",
  "ltd",
  "limited",
  "co",
  "company",
  "plc",
  "gmbh",
  "ag",
  "sa",
  "nv",
  "bv",
  "pty",
  "pvt",
  "holdings",
  "group",
  "international",
  "intl",
  "associates",
  "partners",
  "services",
  "solutions",
  "technologies",
  "tech",
  "enterprises",
];

/**
 * CompanyFuzzyMatchAgent - Matches raw company input to known companies.
 *
 * Execution Flow:
 * 1. Normalize input string (lowercase, strip punctuation, remove LLC/Inc/etc.)
 * 2. Compute similarity score against canonical list
 * 3. If score >= auto_accept_threshold → accept
 * 4. If score >= min_match_score but < auto_accept → manual review
 * 5. If score < min_match_score → call external lookup adapter
 * 6. If external lookup fails → UNMATCHED
 */
export class CompanyFuzzyMatchAgent {
  private config: CompanyFuzzyMatchAgentConfig;

  constructor(config?: Partial<CompanyFuzzyMatchAgentConfig>) {
    this.config = {
      ...DEFAULT_COMPANY_FUZZY_MATCH_CONFIG,
      ...config,
    };
  }

  /**
   * Run the fuzzy match agent.
   *
   * @param task - The fuzzy match task to process
   * @returns AgentResult with match outcome
   */
  async run(task: CompanyFuzzyMatchTask): Promise<AgentResult> {
    try {
      // Validate input
      if (!task.raw_company_input) {
        return this.createResult(task, false, {}, "raw_company_input is required");
      }

      if (!task.company_master || task.company_master.length === 0) {
        return this.createResult(task, false, {}, "company_master list is empty");
      }

      // Step 1: Normalize input
      const normalizedInput = this.normalizeCompanyName(task.raw_company_input);

      if (this.config.verbose) {
        console.log(`[CompanyFuzzyMatchAgent] Input: "${task.raw_company_input}" → Normalized: "${normalizedInput}"`);
      }

      // Step 2: Find best matches in canonical list
      const candidates = this.findCandidates(normalizedInput, task.company_master);

      // Step 3: Determine result based on best score
      const bestCandidate = candidates[0];
      const matchScore = bestCandidate?.score ?? 0;

      if (this.config.verbose) {
        console.log(`[CompanyFuzzyMatchAgent] Best match: "${bestCandidate?.company}" (score: ${matchScore})`);
      }

      // High confidence match
      if (matchScore >= this.config.auto_accept_threshold) {
        return this.createResult(task, true, {
          status: "MATCHED",
          matched_company: bestCandidate.company,
          match_score: matchScore,
          all_candidates: candidates,
          needs_manual_review: false,
          match_method: "local",
        });
      }

      // Medium confidence - needs review
      if (matchScore >= this.config.min_match_score) {
        return this.createResult(task, true, {
          status: "MANUAL_REVIEW",
          matched_company: bestCandidate.company,
          match_score: matchScore,
          all_candidates: candidates,
          needs_manual_review: true,
          match_method: "local",
        });
      }

      // Step 5: Low confidence - try external lookup
      if (this.config.enable_external_fallback) {
        const externalResult = await this.tryExternalLookup(task.raw_company_input, task.company_master);

        if (externalResult) {
          return this.createResult(task, true, {
            status: externalResult.status,
            matched_company: externalResult.matched_company,
            match_score: externalResult.match_score,
            all_candidates: externalResult.all_candidates,
            needs_manual_review: externalResult.status === "MANUAL_REVIEW",
            match_method: "external",
          });
        }
      }

      // Step 6: No match found
      return this.createResult(task, false, {
        status: "UNMATCHED",
        matched_company: null,
        match_score: matchScore,
        all_candidates: candidates,
        needs_manual_review: false,
        match_method: "none",
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
   * Normalize a company name for matching.
   */
  normalizeCompanyName(name: string): string {
    if (!name) return "";

    let normalized = name
      .toLowerCase()
      .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()'"]/g, " ")
      .replace(/\s+/g, " ")
      .trim();

    for (const suffix of COMPANY_SUFFIXES) {
      const suffixPattern = new RegExp(`\\b${suffix}\\b\\.?$`, "i");
      normalized = normalized.replace(suffixPattern, "").trim();
    }

    normalized = normalized.replace(/[\s.]+$/, "");

    return normalized;
  }

  /**
   * Find candidate matches in the company master list.
   */
  findCandidates(normalizedInput: string, companyMaster: string[]): FuzzyCandidate[] {
    const candidates: FuzzyCandidate[] = [];

    for (const company of companyMaster) {
      const normalizedCompany = this.normalizeCompanyName(company);
      const score = this.calculateSimilarity(normalizedInput, normalizedCompany);

      if (score >= this.config.min_match_score * 0.5) {
        candidates.push({
          company,
          score,
          normalized: normalizedCompany,
        });
      }
    }

    return candidates.sort((a, b) => b.score - a.score).slice(0, this.config.max_candidates);
  }

  /**
   * Calculate similarity score between two strings.
   */
  calculateSimilarity(input: string, candidate: string): number {
    if (input === candidate) return 100;
    if (!input || !candidate) return 0;

    const levenshteinScore = this.levenshteinSimilarity(input, candidate);
    const jaccardScore = this.jaccardSimilarity(input, candidate);
    const containsScore = this.containsSimilarity(input, candidate);
    const prefixScore = this.prefixSimilarity(input, candidate);

    const weightedScore =
      levenshteinScore * 0.4 +
      jaccardScore * 0.3 +
      containsScore * 0.2 +
      prefixScore * 0.1;

    return Math.round(weightedScore);
  }

  private levenshteinSimilarity(a: string, b: string): number {
    const distance = this.levenshteinDistance(a, b);
    const maxLength = Math.max(a.length, b.length);
    if (maxLength === 0) return 100;
    return ((maxLength - distance) / maxLength) * 100;
  }

  private levenshteinDistance(a: string, b: string): number {
    const matrix: number[][] = [];

    for (let i = 0; i <= b.length; i++) {
      matrix[i] = [i];
    }
    for (let j = 0; j <= a.length; j++) {
      matrix[0][j] = j;
    }

    for (let i = 1; i <= b.length; i++) {
      for (let j = 1; j <= a.length; j++) {
        if (b.charAt(i - 1) === a.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j] + 1
          );
        }
      }
    }

    return matrix[b.length][a.length];
  }

  private jaccardSimilarity(a: string, b: string): number {
    const tokensA = new Set(a.split(/\s+/));
    const tokensB = new Set(b.split(/\s+/));

    const intersection = new Set([...tokensA].filter((x) => tokensB.has(x)));
    const union = new Set([...tokensA, ...tokensB]);

    if (union.size === 0) return 0;
    return (intersection.size / union.size) * 100;
  }

  private containsSimilarity(a: string, b: string): number {
    if (a.includes(b)) return (b.length / a.length) * 100;
    if (b.includes(a)) return (a.length / b.length) * 100;
    return 0;
  }

  private prefixSimilarity(a: string, b: string): number {
    let matchLen = 0;
    const minLen = Math.min(a.length, b.length);

    for (let i = 0; i < minLen; i++) {
      if (a[i] === b[i]) {
        matchLen++;
      } else {
        break;
      }
    }

    if (minLen === 0) return 0;
    return (matchLen / minLen) * 100;
  }

  /**
   * Try external company lookup when local match fails.
   */
  private async tryExternalLookup(
    rawInput: string,
    companyMaster: string[]
  ): Promise<FuzzyMatchResult | null> {
    try {
      const externalConfig: CompanyLookupConfig = {
        ...DEFAULT_COMPANY_LOOKUP_CONFIG,
        ...this.config.external_config,
      };

      const response = await externalCompanyLookupAdapter(
        { query: rawInput },
        externalConfig
      );

      if (!response.success || !response.data || response.data.length === 0) {
        return null;
      }

      for (const externalCompany of response.data) {
        const normalizedExternal = this.normalizeCompanyName(externalCompany.company_name);

        for (const masterCompany of companyMaster) {
          const normalizedMaster = this.normalizeCompanyName(masterCompany);
          const similarity = this.calculateSimilarity(normalizedExternal, normalizedMaster);

          if (similarity >= this.config.auto_accept_threshold) {
            return {
              status: "MATCHED",
              matched_company: masterCompany,
              match_score: similarity,
              all_candidates: [
                {
                  company: masterCompany,
                  score: similarity,
                  normalized: normalizedMaster,
                },
              ],
            };
          }

          if (similarity >= this.config.min_match_score) {
            return {
              status: "MANUAL_REVIEW",
              matched_company: masterCompany,
              match_score: similarity,
              all_candidates: [
                {
                  company: masterCompany,
                  score: similarity,
                  normalized: normalizedMaster,
                },
              ],
            };
          }
        }
      }

      return null;
    } catch (error) {
      if (this.config.verbose) {
        console.error(`[CompanyFuzzyMatchAgent] External lookup failed: ${error}`);
      }
      return null;
    }
  }

  /**
   * Run fuzzy match directly on a SlotRow.
   *
   * SETS COMPANY_VALID FLAG:
   * - On MATCHED: company_valid = true
   * - On MANUAL_REVIEW: company_valid = false (requires human approval)
   * - On UNMATCHED: company_valid = false
   *
   * GOLDEN RULE: If company_valid = false, downstream email processing is DISABLED.
   *
   * FAILURE ROUTING:
   * - On MANUAL_REVIEW or UNMATCHED: Routes to company_fuzzy_failures table
   * - Failure bay: company_fuzzy_failures
   */
  async runOnRow(row: SlotRow, companyMaster: string[]): Promise<SlotRow> {
    const failureRouter = this.config.failure_router || globalFailureRouter;

    if (!row.needsFuzzyMatch()) {
      return row;
    }

    const rawInput = row.raw_company_input ?? row.company_name ?? "";

    if (!rawInput) {
      row.fuzzy_match_status = "UNMATCHED";
      // SET COMPANY_VALID = FALSE: No company input provided
      row.setCompanyValid(false, "No company input provided");

      // ROUTE TO FAILURE BAY
      const failure = createCompanyFuzzyFailure(
        row,
        rawInput,
        null,
        0,
        "UNMATCHED",
        [],
        "No company input provided"
      );
      await failureRouter.routeCompanyFuzzyFailure(failure);

      if (this.config.verbose) {
        console.log(`[CompanyFuzzyMatchAgent] ROUTED TO BAY: company_fuzzy_failures (no input)`);
      }

      return row;
    }

    const result = await this.run({
      task_id: `fuzzy_${row.id}_${Date.now()}`,
      slot_row_id: row.id,
      raw_company_input: rawInput,
      company_master: companyMaster,
    });

    row.fuzzy_match_status = result.data.status as any;
    row.fuzzy_match_score = result.data.match_score as number;
    row.fuzzy_match_candidates = result.data.all_candidates as FuzzyCandidate[];

    if (result.data.status === "MATCHED" && result.data.matched_company) {
      row.company_name = result.data.matched_company as string;

      // SET COMPANY_VALID = TRUE: Successful match to canonical company
      row.setCompanyValid(true);

      if (this.config.verbose) {
        console.log(`[CompanyFuzzyMatchAgent] company_valid=TRUE for row ${row.id}`);
      }
    } else if (result.data.status === "MANUAL_REVIEW") {
      // SET COMPANY_VALID = FALSE: Requires human review before proceeding
      const reason = `Manual review required (score: ${result.data.match_score})`;
      row.setCompanyValid(false, reason);

      // ROUTE TO FAILURE BAY
      const candidates = (result.data.all_candidates as FuzzyCandidate[]) || [];
      const failure = createCompanyFuzzyFailure(
        row,
        rawInput,
        result.data.matched_company as string || null,
        result.data.match_score as number,
        "MANUAL_REVIEW",
        candidates.map((c) => ({ company: c.company, score: c.score })),
        reason
      );
      await failureRouter.routeCompanyFuzzyFailure(failure);

      if (this.config.verbose) {
        console.log(`[CompanyFuzzyMatchAgent] company_valid=FALSE (manual review) for row ${row.id}`);
        console.log(`[CompanyFuzzyMatchAgent] ROUTED TO BAY: company_fuzzy_failures`);
      }
    } else {
      // SET COMPANY_VALID = FALSE: No match found
      const reason = `Company not found in master list (best score: ${result.data.match_score})`;
      row.setCompanyValid(false, reason);

      // ROUTE TO FAILURE BAY
      const candidates = (result.data.all_candidates as FuzzyCandidate[]) || [];
      const failure = createCompanyFuzzyFailure(
        row,
        rawInput,
        candidates[0]?.company || null,
        result.data.match_score as number,
        "UNMATCHED",
        candidates.map((c) => ({ company: c.company, score: c.score })),
        reason
      );
      await failureRouter.routeCompanyFuzzyFailure(failure);

      if (this.config.verbose) {
        console.log(`[CompanyFuzzyMatchAgent] company_valid=FALSE (unmatched) for row ${row.id}`);
        console.log(`[CompanyFuzzyMatchAgent] ROUTED TO BAY: company_fuzzy_failures`);
      }
    }

    row.last_updated = new Date();

    return row;
  }

  /**
   * Get failure bay for this agent.
   */
  static getFailureBay(): string {
    return "company_fuzzy_failures";
  }

  /**
   * Batch process multiple rows.
   */
  async runBatch(rows: SlotRow[], companyMaster: string[]): Promise<SlotRow[]> {
    const results: SlotRow[] = [];

    for (const row of rows) {
      const processed = await this.runOnRow(row, companyMaster);
      results.push(processed);
    }

    return results;
  }

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: CompanyFuzzyMatchTask,
    success: boolean,
    data: Record<string, unknown>,
    error?: string
  ): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "CompanyFuzzyMatchAgent",
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
  getConfig(): CompanyFuzzyMatchAgentConfig {
    return { ...this.config };
  }

  /**
   * Update configuration.
   */
  updateConfig(config: Partial<CompanyFuzzyMatchAgentConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
