/**
 * DOL Subhub — Fuzzy Filing Discovery (Candidate Lookup ONLY)
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Doctrine: /doctrine/ple/DOL_EIN_RESOLUTION.md
 * Barton ID: 01.04.02.04.22000
 *
 * FUZZY MATCHING BOUNDARY (ABSOLUTE):
 *   Fuzzy matching is allowed ONLY to locate candidate Form 5500 filings.
 *   It must NEVER:
 *     ❌ Attach an EIN
 *     ❌ Resolve company identity
 *     ❌ Decide truth
 *     ❌ Write data
 *
 *   Fuzzy output = CANDIDATE SET ONLY
 *
 * PURPOSE:
 *   Match company identity anchors against Form 5500 filing sponsor names
 *   to identify CANDIDATE filings for inspection. Sponsor names are often
 *   inconsistent (e.g., "Acme Corp" vs "ACME CORPORATION INC").
 *
 * EXECUTION FLOW:
 *   Company Target (PASS, EIN locked)
 *           ↓
 *   DOL Subhub
 *     ├─ fuzzy → candidate filings (THIS MODULE)
 *     ├─ deterministic validation (ein_validator.js)
 *           ├─ PASS → append-only write
 *           └─ FAIL → error_master + AIR (DOL_FILING_NOT_CONFIRMED)
 *
 * ═══════════════════════════════════════════════════════════════════════════
 */

// ═══════════════════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Minimum similarity score to include as candidate
 * Lower threshold than Company Target because we validate deterministically
 */
const MIN_CANDIDATE_SCORE = 0.60;

/**
 * Maximum number of candidates to return
 */
const MAX_CANDIDATES = 10;

/**
 * Fuzzy match methods
 */
const FUZZY_METHOD = {
  TOKEN_SET: 'token_set',
  LEVENSHTEIN: 'levenshtein',
  TRIGRAM: 'trigram'
};

// ═══════════════════════════════════════════════════════════════════════════
// FUZZY MATCHING UTILITIES
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Normalize string for comparison
 * - Lowercase
 * - Remove common suffixes (Inc, LLC, Corp, etc.)
 * - Remove punctuation
 * - Collapse whitespace
 *
 * @param {string} str - String to normalize
 * @returns {string} Normalized string
 */
function normalizeCompanyName(str) {
  if (!str) return '';
  
  return str
    .toLowerCase()
    .replace(/\b(inc|llc|ltd|corp|corporation|company|co|plc|lp|llp|pllc|pc|pa|na|n\.a\.)\b\.?/gi, '')
    .replace(/[^\w\s]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Tokenize string into word set
 * @param {string} str - String to tokenize
 * @returns {Set<string>} Set of tokens
 */
function tokenize(str) {
  const normalized = normalizeCompanyName(str);
  return new Set(normalized.split(' ').filter(t => t.length > 1));
}

/**
 * Calculate Jaccard similarity (token set)
 * @param {Set<string>} setA - First token set
 * @param {Set<string>} setB - Second token set
 * @returns {number} Similarity score 0-1
 */
function jaccardSimilarity(setA, setB) {
  if (setA.size === 0 && setB.size === 0) return 1;
  if (setA.size === 0 || setB.size === 0) return 0;
  
  const intersection = new Set([...setA].filter(x => setB.has(x)));
  const union = new Set([...setA, ...setB]);
  
  return intersection.size / union.size;
}

/**
 * Calculate Levenshtein distance
 * @param {string} a - First string
 * @param {string} b - Second string
 * @returns {number} Edit distance
 */
function levenshteinDistance(a, b) {
  const matrix = [];
  
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
          matrix[i - 1][j - 1] + 1, // substitution
          matrix[i][j - 1] + 1,     // insertion
          matrix[i - 1][j] + 1      // deletion
        );
      }
    }
  }
  
  return matrix[b.length][a.length];
}

/**
 * Calculate Levenshtein similarity (normalized)
 * @param {string} a - First string
 * @param {string} b - Second string
 * @returns {number} Similarity score 0-1
 */
function levenshteinSimilarity(a, b) {
  const normalizedA = normalizeCompanyName(a);
  const normalizedB = normalizeCompanyName(b);
  
  if (normalizedA === normalizedB) return 1;
  if (normalizedA.length === 0 || normalizedB.length === 0) return 0;
  
  const distance = levenshteinDistance(normalizedA, normalizedB);
  const maxLength = Math.max(normalizedA.length, normalizedB.length);
  
  return 1 - (distance / maxLength);
}

/**
 * Calculate token set similarity (Jaccard with tokenization)
 * @param {string} a - First string
 * @param {string} b - Second string
 * @returns {number} Similarity score 0-1
 */
function tokenSetSimilarity(a, b) {
  const tokensA = tokenize(a);
  const tokensB = tokenize(b);
  
  return jaccardSimilarity(tokensA, tokensB);
}

/**
 * Calculate combined similarity score
 * Weighted average of token set and Levenshtein
 *
 * @param {string} a - First string
 * @param {string} b - Second string
 * @returns {number} Combined similarity score 0-1
 */
function combinedSimilarity(a, b) {
  const tokenScore = tokenSetSimilarity(a, b);
  const levenScore = levenshteinSimilarity(a, b);
  
  // Token set weighted higher for company name matching
  return (tokenScore * 0.6) + (levenScore * 0.4);
}

// ═══════════════════════════════════════════════════════════════════════════
// CANDIDATE FILING DISCOVERY (MAIN FUNCTION)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Find candidate Form 5500 filings using fuzzy matching
 *
 * FUZZY MATCHING IS FOR DISCOVERY ONLY:
 *   - Returns ranked candidates with scores
 *   - Does NOT return a decision
 *   - Does NOT attach EIN
 *   - Does NOT resolve identity
 *
 * Matches identity anchors against filing sponsor/plan names.
 *
 * @param {Object} identityAnchors - Company identity anchors
 * @param {string} identityAnchors.company_name - Primary company name (REQUIRED)
 * @param {string} [identityAnchors.company_domain] - Company domain (optional)
 * @param {string} [identityAnchors.linkedin_company_name] - LinkedIn name (optional)
 * @param {Array} filingCorpus - Array of Form 5500 filings to search
 * @param {Object} [options] - Search options
 * @param {number} [options.minScore=0.60] - Minimum score threshold
 * @param {number} [options.maxCandidates=10] - Maximum candidates to return
 * @param {string} [options.method='token_set'] - Fuzzy method
 * @returns {Object} { candidates: Array, searchMetadata: Object }
 */
function findCandidateFilings(identityAnchors, filingCorpus, options = {}) {
  const {
    company_name,
    company_domain = null,
    linkedin_company_name = null
  } = identityAnchors;

  const {
    minScore = MIN_CANDIDATE_SCORE,
    maxCandidates = MAX_CANDIDATES,
    method = FUZZY_METHOD.TOKEN_SET
  } = options;

  // Validate required input
  if (!company_name || !company_name.trim()) {
    return {
      candidates: [],
      searchMetadata: {
        error: 'MISSING_COMPANY_NAME',
        message: 'company_name is required for filing discovery'
      }
    };
  }

  if (!filingCorpus || !Array.isArray(filingCorpus) || filingCorpus.length === 0) {
    return {
      candidates: [],
      searchMetadata: {
        error: 'EMPTY_CORPUS',
        message: 'Filing corpus is empty or invalid'
      }
    };
  }

  // Build search terms from identity anchors
  const searchTerms = [
    { term: company_name, weight: 1.0, source: 'company_name' }
  ];

  if (linkedin_company_name && linkedin_company_name.trim()) {
    searchTerms.push({ term: linkedin_company_name, weight: 0.9, source: 'linkedin_company_name' });
  }

  // Extract company name from domain if available
  if (company_domain && company_domain.trim()) {
    const domainName = company_domain.replace(/^www\./, '').split('.')[0];
    if (domainName.length > 2) {
      searchTerms.push({ term: domainName, weight: 0.7, source: 'company_domain' });
    }
  }

  // Score each filing
  const scoredFilings = [];

  for (const filing of filingCorpus) {
    const filingId = filing.filing_id || filing.id;
    const sponsorName = filing.plan_sponsor_name || filing.sponsor_name || '';
    const planName = filing.plan_name || '';
    const sponsorEIN = filing.sponsor_ein || filing.ein || null;
    const filingYear = filing.filing_year || filing.year || null;

    // Skip filings without sponsor name
    if (!sponsorName.trim()) continue;

    // Calculate best score across all search terms and target fields
    let bestScore = 0;
    let bestMatch = null;

    for (const searchTerm of searchTerms) {
      // Match against sponsor name
      const sponsorScore = combinedSimilarity(searchTerm.term, sponsorName) * searchTerm.weight;
      if (sponsorScore > bestScore) {
        bestScore = sponsorScore;
        bestMatch = {
          searchTerm: searchTerm.term,
          matchedField: 'plan_sponsor_name',
          matchedValue: sponsorName
        };
      }

      // Match against plan name (often contains company name)
      if (planName) {
        const planScore = combinedSimilarity(searchTerm.term, planName) * searchTerm.weight * 0.85;
        if (planScore > bestScore) {
          bestScore = planScore;
          bestMatch = {
            searchTerm: searchTerm.term,
            matchedField: 'plan_name',
            matchedValue: planName
          };
        }
      }
    }

    // Include if above threshold
    if (bestScore >= minScore) {
      scoredFilings.push({
        filing_id: filingId,
        score: Math.round(bestScore * 100) / 100,
        sponsor_name: sponsorName,
        sponsor_ein: sponsorEIN,
        plan_name: planName,
        filing_year: filingYear,
        match_details: bestMatch
      });
    }
  }

  // Sort by score descending
  scoredFilings.sort((a, b) => b.score - a.score);

  // Return top candidates
  const candidates = scoredFilings.slice(0, maxCandidates);

  return {
    candidates,
    searchMetadata: {
      total_filings_searched: filingCorpus.length,
      candidates_found: candidates.length,
      min_score_threshold: minScore,
      search_terms: searchTerms.map(t => ({ term: t.term, source: t.source })),
      fuzzy_method: method,
      timestamp: new Date().toISOString()
    }
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// DETERMINISTIC VALIDATION (CRITICAL - POST-FUZZY)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validate candidate filings deterministically
 *
 * DETERMINISTIC CHECKS (ALL MUST PASS):
 *   1. EIN in filing MUST exactly match resolved EIN
 *   2. Filing year must pass TTL
 *   3. Plan sponsor EIN (if present) must match
 *
 * If NO candidate passes: FAIL HARD with DOL_FILING_NOT_CONFIRMED
 *
 * @param {Array} candidates - Candidates from fuzzy discovery
 * @param {string} resolvedEIN - EIN resolved by Company Target (LOCKED)
 * @param {number} filingTTLYears - Maximum filing age in years
 * @returns {Object} { confirmed: Object|null, rejected: Array, allFailed: boolean }
 */
function validateCandidatesDeterministic(candidates, resolvedEIN, filingTTLYears = 3) {
  if (!candidates || candidates.length === 0) {
    return {
      confirmed: null,
      rejected: [],
      allFailed: true,
      failReason: 'NO_CANDIDATES'
    };
  }

  if (!resolvedEIN || !/^\d{2}-\d{7}$/.test(resolvedEIN)) {
    return {
      confirmed: null,
      rejected: candidates,
      allFailed: true,
      failReason: 'INVALID_RESOLVED_EIN'
    };
  }

  const currentYear = new Date().getFullYear();
  const rejected = [];
  let confirmed = null;

  for (const candidate of candidates) {
    const reasons = [];

    // Check 1: EIN exact match (CRITICAL)
    if (candidate.sponsor_ein !== resolvedEIN) {
      reasons.push({
        check: 'EIN_MISMATCH',
        expected: resolvedEIN,
        found: candidate.sponsor_ein
      });
    }

    // Check 2: Filing TTL
    if (candidate.filing_year) {
      const age = currentYear - candidate.filing_year;
      if (age > filingTTLYears) {
        reasons.push({
          check: 'TTL_EXCEEDED',
          filing_year: candidate.filing_year,
          age_years: age,
          max_ttl: filingTTLYears
        });
      }
    }

    // If any check failed, reject
    if (reasons.length > 0) {
      rejected.push({
        filing_id: candidate.filing_id,
        fuzzy_score: candidate.score,
        rejection_reasons: reasons
      });
    } else if (!confirmed) {
      // First candidate that passes all checks is confirmed
      confirmed = {
        filing_id: candidate.filing_id,
        sponsor_ein: candidate.sponsor_ein,
        sponsor_name: candidate.sponsor_name,
        plan_name: candidate.plan_name,
        filing_year: candidate.filing_year,
        fuzzy_score: candidate.score,
        validation_status: 'CONFIRMED'
      };
    }
  }

  return {
    confirmed,
    rejected,
    allFailed: confirmed === null,
    failReason: confirmed === null ? 'ALL_CANDIDATES_REJECTED' : null
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// MODULE EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

module.exports = {
  // Constants
  MIN_CANDIDATE_SCORE,
  MAX_CANDIDATES,
  FUZZY_METHOD,

  // Utility functions
  normalizeCompanyName,
  tokenize,
  jaccardSimilarity,
  levenshteinDistance,
  levenshteinSimilarity,
  tokenSetSimilarity,
  combinedSimilarity,

  // Main functions
  findCandidateFilings,
  validateCandidatesDeterministic
};
