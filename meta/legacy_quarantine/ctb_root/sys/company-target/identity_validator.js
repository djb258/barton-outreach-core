/**
 * Company Target — Identity Resolution Validator
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Doctrine: /doctrine/ple/COMPANY_TARGET_IDENTITY.md
 * Barton ID: 01.04.02.04.21000
 *
 * PURPOSE:
 *   Identity resolution for companies, including EIN fuzzy matching.
 *   If EIN cannot be resolved, record is routed for ENRICHMENT remediation.
 *   DOL Subhub requires a LOCKED EIN and must NEVER see fuzzy logic.
 *
 * CANONICAL RULE:
 *   Fuzzy matching to attach EIN ↔ company_unique_id is allowed ONLY in
 *   Company Target / Identity Resolution.
 *   The DOL Subhub requires a locked EIN and must NEVER see fuzzy logic.
 *
 * FAILURE ROUTING:
 *   If Company Target cannot fuzzy-resolve an EIN:
 *   - Record MUST NOT proceed to DOL
 *   - MUST be written to shq.error_master for enrichment remediation
 *   - This is a PRE-DOL failure, not a DOL error
 *
 * ═══════════════════════════════════════════════════════════════════════════
 */

const crypto = require('crypto');

// ═══════════════════════════════════════════════════════════════════════════
// CONSTANTS (LOCKED)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Company Target Process ID (Barton ID)
 */
const COMPANY_TARGET_PROCESS_ID = '01.04.02.04.21000';

/**
 * Agent name for error_master
 */
const AGENT_NAME = 'COMPANY_TARGET';

/**
 * Handoff target for EIN resolution failures
 */
const HANDOFF_TARGET = 'DOL_EIN';

/**
 * Source system identifier
 */
const SOURCE_SYSTEM = 'COMPANY_TARGET';

/**
 * Severity level for FAIL HARD conditions
 * CANONICAL VALUE - DO NOT CHANGE
 */
const SEVERITY_HARD_FAIL = 'HARD_FAIL';

/**
 * Remediation type for EIN resolution failures
 */
const REMEDIATION_ENRICHMENT = 'ENRICHMENT';

/**
 * Company Target Status outcomes
 */
const COMPANY_TARGET_STATUS = {
  PASS: 'PASS',
  FAIL: 'FAIL',
  PENDING: 'PENDING'
};

/**
 * EIN format validation
 * Format: XX-XXXXXXX (9 digits with hyphen)
 */
const EIN_REGEX = /^\d{2}-\d{7}$/;

/**
 * Error codes (LOCKED ENUM)
 */
const ERROR_CODES = {
  EIN_NOT_RESOLVED: 'EIN_NOT_RESOLVED',
  IDENTITY_GATE_FAILED: 'IDENTITY_GATE_FAILED',
  FUZZY_MATCH_AMBIGUOUS: 'FUZZY_MATCH_AMBIGUOUS',
  COMPANY_NOT_FOUND: 'COMPANY_NOT_FOUND'
};

/**
 * Fuzzy match methods (for enrichment payload)
 */
const FUZZY_METHODS = {
  TOKEN_SET: 'token_set',
  LEVENSHTEIN: 'levenshtein',
  JARO_WINKLER: 'jaro_winkler',
  EXACT: 'exact'
};

/**
 * Default confidence threshold for fuzzy matching
 */
const DEFAULT_CONFIDENCE_THRESHOLD = 0.85;

// ═══════════════════════════════════════════════════════════════════════════
// DATABASE WRITE FUNCTIONS (STUBS)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Write AIR event to air_log
 * @param {Object} airEvent - AIR event payload
 * @returns {Promise<string>} air_event_id
 */
async function writeAIREvent(airEvent) {
  // IMPLEMENTATION: Use your database client
  const airEventId = `01.04.02.04.21000.9${String(Date.now() % 100).padStart(2, '0')}`;
  
  console.log('[AIR] Event logged:', {
    air_event_id: airEventId,
    event_type: airEvent.event_type,
    event_status: airEvent.event_status
  });
  
  return airEventId;
}

/**
 * Write error to shq.error_master (CANONICAL error table)
 * MANDATORY FOR ENRICHMENT ROUTING
 *
 * Required Fields:
 *   - process_id = Company Target process_id
 *   - error_code = EIN_NOT_RESOLVED
 *   - severity = HARD_FAIL
 *   - agent_name = COMPANY_TARGET
 *   - handoff_target = DOL_EIN
 *   - remediation_required = ENRICHMENT
 *   - company_unique_id
 *   - outreach_context_id
 *   - created_at
 *
 * @param {Object} errorData - Error data
 * @param {string} airEventId - Reference to AIR event
 * @returns {Promise<string>} error_id
 */
async function writeErrorMaster(errorData, airEventId) {
  const errorId = crypto.randomUUID();
  
  const errorRecord = {
    error_id: errorId,
    occurred_at: new Date().toISOString(),
    process_id: COMPANY_TARGET_PROCESS_ID,
    agent_name: AGENT_NAME,
    severity: SEVERITY_HARD_FAIL,
    source_system: SOURCE_SYSTEM,
    error_type: errorData.error_code,
    handoff_target: HANDOFF_TARGET,
    remediation_required: errorData.remediation_required || REMEDIATION_ENRICHMENT,
    message: `[${errorData.error_code}] ${errorData.message}`,
    context: JSON.stringify({
      air_event_id: airEventId,
      company_unique_id: errorData.company_unique_id,
      outreach_context_id: errorData.outreach_context_id,
      payload: errorData.payload
    }),
    company_unique_id: errorData.company_unique_id,
    outreach_context_id: errorData.outreach_context_id,
    created_at: new Date().toISOString()
  };
  
  console.log('[shq.error_master] Error logged (ENRICHMENT ROUTING):', {
    error_id: errorId,
    process_id: COMPANY_TARGET_PROCESS_ID,
    agent_name: AGENT_NAME,
    severity: SEVERITY_HARD_FAIL,
    error_type: errorData.error_code,
    handoff_target: HANDOFF_TARGET,
    remediation_required: errorData.remediation_required,
    air_event_id: airEventId
  });
  
  return errorId;
}

// ═══════════════════════════════════════════════════════════════════════════
// CENTRALIZED FAIL HARD: EIN_NOT_RESOLVED
// ═══════════════════════════════════════════════════════════════════════════

/**
 * FAIL HARD: EIN_NOT_RESOLVED
 *
 * This failure occurs when:
 *   - Fuzzy match returns zero candidates above threshold, OR
 *   - Candidates exist but none meet confidence requirements
 *
 * Routing:
 *   - Writes to shq.error_master for ENRICHMENT remediation
 *   - DOL execution is BLOCKED (company_target_status = FAIL)
 *
 * No retries inside Company Target.
 *
 * @param {Object} context - Context with company data and fuzzy results
 * @returns {Promise<Object>} Failure result
 */
async function failHardEINNotResolved(context) {
  const {
    company_unique_id,
    outreach_context_id,
    company_name,
    company_domain = null,
    linkedin_company_url = null,
    state,
    fuzzy_candidates = [],
    fuzzy_method = FUZZY_METHODS.TOKEN_SET,
    threshold_used = DEFAULT_CONFIDENCE_THRESHOLD
  } = context;

  const message = fuzzy_candidates.length === 0
    ? `No EIN candidates found via fuzzy match for company: ${company_name}`
    : `No EIN candidates met confidence threshold (${threshold_used}) for company: ${company_name}`;

  // Create AIR event
  const airEvent = {
    event_type: ERROR_CODES.EIN_NOT_RESOLVED,
    event_status: 'ABORTED',
    event_message: message,
    company_unique_id,
    outreach_context_id,
    created_at: new Date().toISOString()
  };

  // Step 1: Write to AIR (authoritative)
  const airEventId = await writeAIREvent(airEvent);

  // Step 2: Build enrichment payload (REQUIRED)
  const enrichmentPayload = {
    company_name,
    company_domain,
    linkedin_company_url,
    state,
    fuzzy_candidates: fuzzy_candidates.slice(0, 10).map(c => ({
      ein: c.ein,
      company_name: c.company_name,
      score: c.score
    })),
    fuzzy_method,
    threshold_used
  };

  // Step 3: Write to shq.error_master (operational + enrichment routing)
  const errorId = await writeErrorMaster({
    error_code: ERROR_CODES.EIN_NOT_RESOLVED,
    message,
    company_unique_id,
    outreach_context_id,
    remediation_required: REMEDIATION_ENRICHMENT,
    payload: enrichmentPayload
  }, airEventId);

  // Step 4: Return failure result (company_target_status = FAIL)
  return {
    success: false,
    company_target_status: COMPANY_TARGET_STATUS.FAIL,
    error_code: ERROR_CODES.EIN_NOT_RESOLVED,
    air_event_id: airEventId,
    error_id: errorId,
    message,
    remediation_required: REMEDIATION_ENRICHMENT,
    handoff_target: HANDOFF_TARGET
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// FUZZY MATCH VALIDATION (ISOLATED TO COMPANY TARGET ONLY)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * FUZZY MATCH BOUNDARY ENFORCEMENT
 *
 * This function is the ONLY place fuzzy matching is allowed.
 * ❌ No fuzzy logic in: ctb/sys/dol-ein/*
 * ❌ No fuzzy logic in: analytics.v_5500_*
 * ✅ Fuzzy logic exists ONLY in: Company Target identity resolution
 *
 * @param {Array} candidates - EIN candidates from fuzzy search
 * @param {number} threshold - Confidence threshold
 * @returns {Object} { resolved: boolean, ein: string|null, confidence: number }
 */
function evaluateFuzzyCandidates(candidates, threshold = DEFAULT_CONFIDENCE_THRESHOLD) {
  if (!candidates || candidates.length === 0) {
    return {
      resolved: false,
      ein: null,
      confidence: 0,
      reason: 'ZERO_CANDIDATES'
    };
  }

  // Sort by score descending
  const sorted = [...candidates].sort((a, b) => b.score - a.score);
  const best = sorted[0];

  // Check if best candidate meets threshold
  if (best.score < threshold) {
    return {
      resolved: false,
      ein: null,
      confidence: best.score,
      reason: 'BELOW_THRESHOLD',
      best_candidate: best
    };
  }

  // Check for ambiguity (multiple candidates at similar scores)
  const closeCompetitors = sorted.filter(c => c.score >= threshold && c.score >= best.score - 0.05);
  if (closeCompetitors.length > 1) {
    return {
      resolved: false,
      ein: null,
      confidence: best.score,
      reason: 'AMBIGUOUS_MATCH',
      competitors: closeCompetitors
    };
  }

  // SUCCESS: Single clear winner above threshold
  return {
    resolved: true,
    ein: best.ein,
    confidence: best.score,
    reason: 'RESOLVED'
  };
}

/**
 * Validate EIN format
 * @param {string} ein - EIN to validate
 * @returns {boolean}
 */
function isValidEINFormat(ein) {
  return ein && EIN_REGEX.test(ein);
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN PIPELINE: COMPANY TARGET IDENTITY RESOLUTION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Execute Company Target identity resolution
 *
 * This is the ONLY place EIN fuzzy matching is allowed.
 * If EIN cannot be resolved, record routes to ENRICHMENT.
 * DOL Subhub execution is BLOCKED until EIN is resolved.
 *
 * @param {Object} params - Company data
 * @returns {Promise<Object>} Resolution result
 */
async function resolveCompanyIdentity(params) {
  const {
    company_unique_id,
    outreach_context_id,
    company_name,
    company_domain,
    linkedin_company_url,
    state,
    ein = null,  // May already be resolved
    fuzzy_candidates = [],  // From external fuzzy search
    fuzzy_method = FUZZY_METHODS.TOKEN_SET,
    threshold = DEFAULT_CONFIDENCE_THRESHOLD
  } = params;

  // ─────────────────────────────────────────────────────────────────────────
  // Step 1: Identity Gate Validation
  // ─────────────────────────────────────────────────────────────────────────
  if (!company_unique_id || !company_unique_id.trim()) {
    return failHardEINNotResolved({
      ...params,
      error_code: ERROR_CODES.IDENTITY_GATE_FAILED,
      message: 'MISSING: company_unique_id'
    });
  }

  if (!company_name || !company_name.trim()) {
    return failHardEINNotResolved({
      ...params,
      error_code: ERROR_CODES.IDENTITY_GATE_FAILED,
      message: 'MISSING: company_name'
    });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Step 2: Check if EIN is already resolved
  // ─────────────────────────────────────────────────────────────────────────
  if (ein && isValidEINFormat(ein)) {
    // EIN already resolved - PASS to DOL
    const airEvent = {
      event_type: 'EIN_ALREADY_RESOLVED',
      event_status: 'SUCCESS',
      event_message: `EIN already resolved: ${ein}`,
      company_unique_id,
      outreach_context_id,
      created_at: new Date().toISOString()
    };

    const airEventId = await writeAIREvent(airEvent);

    return {
      success: true,
      company_target_status: COMPANY_TARGET_STATUS.PASS,
      ein,
      ein_resolved: true,
      air_event_id: airEventId
    };
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Step 3: Evaluate fuzzy candidates (ONLY PLACE THIS HAPPENS)
  // ─────────────────────────────────────────────────────────────────────────
  const fuzzyResult = evaluateFuzzyCandidates(fuzzy_candidates, threshold);

  if (fuzzyResult.resolved && isValidEINFormat(fuzzyResult.ein)) {
    // EIN resolved via fuzzy match - PASS to DOL
    const airEvent = {
      event_type: 'EIN_FUZZY_RESOLVED',
      event_status: 'SUCCESS',
      event_message: `EIN resolved via fuzzy match: ${fuzzyResult.ein} (confidence: ${fuzzyResult.confidence})`,
      company_unique_id,
      outreach_context_id,
      created_at: new Date().toISOString()
    };

    const airEventId = await writeAIREvent(airEvent);

    return {
      success: true,
      company_target_status: COMPANY_TARGET_STATUS.PASS,
      ein: fuzzyResult.ein,
      ein_resolved: true,
      resolution_method: 'FUZZY',
      fuzzy_method,
      confidence: fuzzyResult.confidence,
      air_event_id: airEventId
    };
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Step 4: FAIL HARD - EIN_NOT_RESOLVED
  // Route to ENRICHMENT remediation
  // ─────────────────────────────────────────────────────────────────────────
  return failHardEINNotResolved({
    company_unique_id,
    outreach_context_id,
    company_name,
    company_domain,
    linkedin_company_url,
    state,
    fuzzy_candidates,
    fuzzy_method,
    threshold_used: threshold
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// MODULE EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

module.exports = {
  // Constants (LOCKED)
  COMPANY_TARGET_PROCESS_ID,
  AGENT_NAME,
  HANDOFF_TARGET,
  SOURCE_SYSTEM,
  SEVERITY_HARD_FAIL,
  REMEDIATION_ENRICHMENT,
  COMPANY_TARGET_STATUS,
  EIN_REGEX,
  ERROR_CODES,
  FUZZY_METHODS,
  DEFAULT_CONFIDENCE_THRESHOLD,

  // Core functions
  resolveCompanyIdentity,
  failHardEINNotResolved,
  evaluateFuzzyCandidates,
  isValidEINFormat,

  // Database stubs
  writeAIREvent,
  writeErrorMaster
};
