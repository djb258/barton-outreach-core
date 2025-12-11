/**
 * PeopleFuzzyMatchAgent
 * =====================
 * People Node: Person Name Fuzzy Matching Agent
 *
 * Matches raw person input to known people within a company context.
 * Similar to CompanyFuzzyMatchAgent but for person-level matching.
 *
 * Hub-and-Spoke Role:
 * - Part of PEOPLE_NODE (spoke)
 * - Requires company anchor from Company Hub
 * - Deduplicates person records within same company
 * - Resolves name variations (Bob vs Robert, etc.)
 *
 * Features:
 * - Person name normalization
 * - Similarity scoring with multiple algorithms
 * - Company context for disambiguation
 * - Title/role hints for better matching
 *
 * TODO: Implement full matching logic
 * TODO: Add nickname resolution (Bob → Robert)
 * TODO: Integrate with existing people_master records
 */

import { AgentResult, SlotRow } from "../../models/SlotRow";
import { createPersonCompanyMismatchFailure } from "../../models/FailureRecord";
import { FailureRouter, globalFailureRouter } from "../../services/FailureRouter";

/**
 * Agent configuration.
 */
export interface PeopleFuzzyMatchAgentConfig {
  /** Minimum score to consider a match */
  min_match_score: number;
  /** Score threshold for automatic acceptance */
  auto_accept_threshold: number;
  /** Maximum candidates to return */
  max_candidates: number;
  /** Enable verbose logging */
  verbose: boolean;
  /** Consider title in matching */
  use_title_hint: boolean;
  /** Consider company in matching */
  require_company_match: boolean;
  /** Minimum employer match score for person_company_valid */
  employer_match_threshold: number;
  /** Enable employer validation (sets person_company_valid) */
  enable_employer_validation: boolean;
  /** Failure router instance */
  failure_router?: FailureRouter;
}

/**
 * Default configuration.
 */
export const DEFAULT_PEOPLE_FUZZY_MATCH_CONFIG: PeopleFuzzyMatchAgentConfig = {
  min_match_score: 60,
  auto_accept_threshold: 90,
  max_candidates: 5,
  verbose: false,
  use_title_hint: true,
  require_company_match: true,
  employer_match_threshold: 0.85, // 85% confidence required for person_company_valid
  enable_employer_validation: true,
};

/**
 * Task for PeopleFuzzyMatchAgent.
 */
export interface PeopleFuzzyMatchTask {
  task_id: string;
  slot_row_id: string;
  raw_person_input: string;
  company_id: string;
  company_name: string;
  title_hint?: string;
  known_people: PersonCandidate[];
}

/**
 * Person candidate for matching.
 */
export interface PersonCandidate {
  person_id: string;
  full_name: string;
  company_id: string;
  company_name: string;
  title?: string;
  email?: string;
  linkedin_url?: string;
}

/**
 * Match result.
 */
export interface PersonMatchResult {
  status: "MATCHED" | "MANUAL_REVIEW" | "UNMATCHED" | "NEW_PERSON";
  matched_person: PersonCandidate | null;
  match_score: number;
  all_candidates: Array<{ person: PersonCandidate; score: number }>;
}

/**
 * Common name variations/nicknames.
 */
const NAME_VARIATIONS: Record<string, string[]> = {
  robert: ["bob", "rob", "bobby", "bert"],
  william: ["will", "bill", "billy", "liam"],
  richard: ["rick", "dick", "rich", "ricky"],
  james: ["jim", "jimmy", "jamie"],
  michael: ["mike", "mikey", "mick"],
  joseph: ["joe", "joey"],
  thomas: ["tom", "tommy"],
  daniel: ["dan", "danny"],
  david: ["dave", "davey"],
  christopher: ["chris", "kit"],
  jennifer: ["jen", "jenny"],
  elizabeth: ["liz", "beth", "betty", "eliza"],
  katherine: ["kate", "kathy", "katie", "kat"],
  margaret: ["maggie", "meg", "peggy", "marge"],
  patricia: ["pat", "patty", "trish"],
  // Add more as needed
};

/**
 * PeopleFuzzyMatchAgent - Matches raw person input to known people.
 *
 * Execution Flow:
 * 1. Normalize input person name
 * 2. Filter candidates by company (if required)
 * 3. Compute similarity scores
 * 4. Check for nickname matches
 * 5. Return best match or NEW_PERSON status
 */
export class PeopleFuzzyMatchAgent {
  private config: PeopleFuzzyMatchAgentConfig;

  constructor(config?: Partial<PeopleFuzzyMatchAgentConfig>) {
    this.config = {
      ...DEFAULT_PEOPLE_FUZZY_MATCH_CONFIG,
      ...config,
    };
  }

  /**
   * Run the person fuzzy match agent.
   */
  async run(task: PeopleFuzzyMatchTask): Promise<AgentResult> {
    try {
      // Validate input
      if (!task.raw_person_input) {
        return this.createResult(task, false, {}, "raw_person_input is required");
      }

      if (!task.company_id || !task.company_name) {
        return this.createResult(task, false, {}, "company_id and company_name are required");
      }

      // Step 1: Normalize input
      const normalizedInput = this.normalizePersonName(task.raw_person_input);

      if (this.config.verbose) {
        console.log(`[PeopleFuzzyMatchAgent] Input: "${task.raw_person_input}" → Normalized: "${normalizedInput}"`);
      }

      // Step 2: Filter candidates by company if required
      let candidates = task.known_people;
      if (this.config.require_company_match) {
        candidates = candidates.filter((p) => p.company_id === task.company_id);
      }

      // No candidates to match against
      if (candidates.length === 0) {
        return this.createResult(task, true, {
          status: "NEW_PERSON",
          matched_person: null,
          match_score: 0,
          all_candidates: [],
          is_new_person: true,
        });
      }

      // Step 3: Find best matches
      const scoredCandidates = this.scoreCandidates(normalizedInput, candidates, task.title_hint);

      // Step 4: Determine result based on best score
      const bestMatch = scoredCandidates[0];
      const matchScore = bestMatch?.score ?? 0;

      if (this.config.verbose) {
        console.log(`[PeopleFuzzyMatchAgent] Best match: "${bestMatch?.person.full_name}" (score: ${matchScore})`);
      }

      // High confidence match
      if (matchScore >= this.config.auto_accept_threshold) {
        return this.createResult(task, true, {
          status: "MATCHED",
          matched_person: bestMatch.person,
          match_score: matchScore,
          all_candidates: scoredCandidates.slice(0, this.config.max_candidates),
          needs_manual_review: false,
        });
      }

      // Medium confidence - needs review
      if (matchScore >= this.config.min_match_score) {
        return this.createResult(task, true, {
          status: "MANUAL_REVIEW",
          matched_person: bestMatch.person,
          match_score: matchScore,
          all_candidates: scoredCandidates.slice(0, this.config.max_candidates),
          needs_manual_review: true,
        });
      }

      // No match found - this is a new person
      return this.createResult(task, true, {
        status: "NEW_PERSON",
        matched_person: null,
        match_score: matchScore,
        all_candidates: scoredCandidates.slice(0, this.config.max_candidates),
        is_new_person: true,
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
   * Normalize a person name for matching.
   */
  normalizePersonName(name: string): string {
    if (!name) return "";

    return name
      .toLowerCase()
      .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()'"]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  /**
   * Score candidates against the input.
   */
  private scoreCandidates(
    normalizedInput: string,
    candidates: PersonCandidate[],
    titleHint?: string
  ): Array<{ person: PersonCandidate; score: number }> {
    const scored: Array<{ person: PersonCandidate; score: number }> = [];

    for (const person of candidates) {
      const normalizedCandidate = this.normalizePersonName(person.full_name);
      let score = this.calculateSimilarity(normalizedInput, normalizedCandidate);

      // Boost score if nickname matches
      const nicknameScore = this.checkNicknameMatch(normalizedInput, normalizedCandidate);
      if (nicknameScore > score) {
        score = nicknameScore;
      }

      // Boost score if title hint matches
      if (this.config.use_title_hint && titleHint && person.title) {
        const titleMatch = person.title.toLowerCase().includes(titleHint.toLowerCase());
        if (titleMatch) {
          score = Math.min(100, score + 10);
        }
      }

      scored.push({ person, score });
    }

    return scored.sort((a, b) => b.score - a.score);
  }

  /**
   * Check if names match via nickname expansion.
   */
  private checkNicknameMatch(input: string, candidate: string): number {
    const inputParts = input.split(/\s+/);
    const candidateParts = candidate.split(/\s+/);

    if (inputParts.length === 0 || candidateParts.length === 0) {
      return 0;
    }

    const inputFirst = inputParts[0];
    const candidateFirst = candidateParts[0];

    // Check if one is a nickname of the other
    for (const [formal, nicknames] of Object.entries(NAME_VARIATIONS)) {
      const allVariants = [formal, ...nicknames];

      const inputMatch = allVariants.includes(inputFirst);
      const candidateMatch = allVariants.includes(candidateFirst);

      if (inputMatch && candidateMatch) {
        // First names match via nickname - check last names
        if (inputParts.length > 1 && candidateParts.length > 1) {
          const inputLast = inputParts.slice(1).join(" ");
          const candidateLast = candidateParts.slice(1).join(" ");
          const lastNameScore = this.calculateSimilarity(inputLast, candidateLast);
          return Math.round((100 + lastNameScore) / 2);
        }
        return 85; // Good match on first name nickname
      }
    }

    return 0;
  }

  /**
   * Calculate similarity score between two strings.
   */
  private calculateSimilarity(input: string, candidate: string): number {
    if (input === candidate) return 100;
    if (!input || !candidate) return 0;

    const levenshteinScore = this.levenshteinSimilarity(input, candidate);
    const jaccardScore = this.jaccardSimilarity(input, candidate);

    return Math.round(levenshteinScore * 0.6 + jaccardScore * 0.4);
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

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: PeopleFuzzyMatchTask,
    success: boolean,
    data: Record<string, unknown>,
    error?: string
  ): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "PeopleFuzzyMatchAgent",
      slot_row_id: task.slot_row_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }

  getConfig(): PeopleFuzzyMatchAgentConfig {
    return { ...this.config };
  }

  updateConfig(config: Partial<PeopleFuzzyMatchAgentConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Run directly on a SlotRow.
   *
   * GOLDEN RULE ENFORCEMENT:
   * 1. If company_valid = false, skip processing entirely
   * 2. Validate employer alignment: compare person's employer to canonical company
   * 3. Set person_company_valid based on employer match score
   *
   * If mismatch → skip_email = true, skip_reason = "Person not matched to canonical company"
   *
   * FAILURE ROUTING:
   * If person_company_valid = false, routes to person_company_mismatch failure bay.
   */
  async runOnRow(row: SlotRow, knownPeople: PersonCandidate[] = []): Promise<SlotRow> {
    const failureRouter = this.config.failure_router || globalFailureRouter;

    // === GOLDEN RULE CHECK ===
    // Check company validation first
    if (row.company_valid === false) {
      const reason = row.company_invalid_reason ?? "Company validation failed";

      if (this.config.verbose) {
        console.log(`[PeopleFuzzyMatchAgent] SKIPPED: company_valid=false for row ${row.id}`);
        console.log(`[PeopleFuzzyMatchAgent] Reason: ${reason}`);
      }

      row.markEmailSkipped(`PeopleFuzzyMatchAgent: ${reason}`);
      return row;
    }

    // Need person name to validate
    if (!row.person_name) {
      if (this.config.verbose) {
        console.log(`[PeopleFuzzyMatchAgent] SKIPPED: No person_name for row ${row.id}`);
      }
      return row;
    }

    // Need company name for validation
    if (!row.company_name) {
      row.markEmailSkipped("PeopleFuzzyMatchAgent: No canonical company name");
      return row;
    }

    // Run fuzzy match if we have known people to match against
    if (knownPeople.length > 0) {
      const task: PeopleFuzzyMatchTask = {
        task_id: `people_fuzzy_${row.id}_${Date.now()}`,
        slot_row_id: row.id,
        raw_person_input: row.person_name,
        company_id: row.company_id,
        company_name: row.company_name,
        title_hint: row.current_title ?? undefined,
        known_people: knownPeople,
      };

      const result = await this.run(task);

      // Store match results on row
      if (result.success && result.data) {
        row.person_match_status = result.data.status as string;
        row.person_match_score = result.data.match_score as number;
      }
    }

    // === EMPLOYER VALIDATION ===
    // If enabled, validate that person's employer matches canonical company
    if (this.config.enable_employer_validation) {
      const employerValidation = this.validateEmployerAlignment(row);

      if (employerValidation.valid) {
        row.setPersonCompanyValid(true, employerValidation.score);

        if (this.config.verbose) {
          console.log(`[PeopleFuzzyMatchAgent] person_company_valid=TRUE for row ${row.id} (score: ${employerValidation.score})`);
        }
      } else {
        row.setPersonCompanyValid(
          false,
          employerValidation.score,
          employerValidation.reason
        );

        // ROUTE TO FAILURE BAY
        const failure = createPersonCompanyMismatchFailure(
          row,
          row.company_name,
          row.current_company || null,
          employerValidation.score,
          this.config.employer_match_threshold,
          employerValidation.reason || "Person employer mismatch"
        );
        await failureRouter.routePersonCompanyMismatch(failure);

        if (this.config.verbose) {
          console.log(`[PeopleFuzzyMatchAgent] person_company_valid=FALSE for row ${row.id}`);
          console.log(`[PeopleFuzzyMatchAgent] Reason: ${employerValidation.reason}`);
          console.log(`[PeopleFuzzyMatchAgent] ROUTED to person_company_mismatch failure bay`);
        }
      }
    }

    row.last_updated = new Date();
    return row;
  }

  /**
   * Get the failure bay for this agent.
   */
  static getFailureBay(): string {
    return "person_company_mismatch";
  }

  /**
   * Validate that person's employer matches canonical company.
   *
   * Uses current_company (scraped) vs company_name (canonical) comparison.
   * Returns validation result with score and reason.
   */
  private validateEmployerAlignment(row: SlotRow): {
    valid: boolean;
    score: number;
    reason?: string;
  } {
    const canonicalCompany = row.company_name || "";
    const scrapedEmployer = row.current_company || "";

    // If we don't have a scraped employer yet, assume valid (will be validated by TitleCompanyAgent)
    if (!scrapedEmployer) {
      return {
        valid: true,
        score: 1.0,
        reason: "No scraped employer yet - pending validation",
      };
    }

    // Calculate employer match score
    const matchScore = this.calculateEmployerMatchScore(scrapedEmployer, canonicalCompany);

    if (matchScore >= this.config.employer_match_threshold) {
      return {
        valid: true,
        score: matchScore,
      };
    }

    return {
      valid: false,
      score: matchScore,
      reason: `Person employer "${scrapedEmployer}" does not match canonical company "${canonicalCompany}" (score: ${(matchScore * 100).toFixed(1)}%)`,
    };
  }

  /**
   * Calculate employer match score using fuzzy matching.
   */
  private calculateEmployerMatchScore(scrapedEmployer: string, canonicalCompany: string): number {
    if (!scrapedEmployer || !canonicalCompany) return 0;

    const normScraped = this.normalizeCompanyName(scrapedEmployer);
    const normCanonical = this.normalizeCompanyName(canonicalCompany);

    // Exact match after normalization
    if (normScraped === normCanonical) return 1.0;

    // Contains check
    if (normScraped.includes(normCanonical) || normCanonical.includes(normScraped)) {
      const longer = Math.max(normScraped.length, normCanonical.length);
      const shorter = Math.min(normScraped.length, normCanonical.length);
      return shorter / longer;
    }

    // Levenshtein-based similarity
    const distance = this.levenshteinDistance(normScraped, normCanonical);
    const maxLen = Math.max(normScraped.length, normCanonical.length);
    if (maxLen === 0) return 0;

    return (maxLen - distance) / maxLen;
  }

  /**
   * Normalize company name for comparison.
   */
  private normalizeCompanyName(name: string): string {
    return name
      .toLowerCase()
      .replace(/\s+(inc|llc|ltd|corp|co|company|corporation|group|holdings)\.?$/i, "")
      .replace(/[^a-z0-9]/g, "")
      .trim();
  }
}
