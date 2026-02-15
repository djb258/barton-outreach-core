/**
 * DOL EIN Resolution Pipeline - Validation Module
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Doctrine: /doctrine/ple/DOL_EIN_RESOLUTION.md
 * Schema: /doctrine/schemas/dol_ein_linkage-schema.sql
 * Barton ID: 01.04.02.04.22000
 *
 * EXPLICIT SCOPE (EIN Resolution ONLY):
 *   ✅ EIN ↔ company_unique_id linkage
 *   ✅ Identity gate validation (FAIL HARD)
 *   ✅ EIN format validation
 *   ✅ Hash fingerprint generation
 *   ✅ AIR event logging
 *   ✅ DUAL-WRITE: AIR + shq.error_master (canonical error table)
 *
 * FAILURE ROUTING DOCTRINE:
 *   Every FAIL HARD condition MUST write to BOTH:
 *   1. AIR event log (truth / audit)
 *   2. shq.error_master (operations / triage)
 *
 *   AIR is authoritative; shq_error_log is operational.
 *
 * EXPLICIT NON-GOALS (REMOVED):
 *   ❌ NO buyer intent scoring
 *   ❌ NO BIT event creation
 *   ❌ NO OSHA/EEOC tracking
 *   ❌ NO Slack/Salesforce/Grafana integration
 *   ❌ NO outreach triggers
 *   ❌ NO retries
 *   ❌ NO alerts
 *   ❌ NO dashboards
 *
 * ═══════════════════════════════════════════════════════════════════════════
 */

const crypto = require('crypto');

// ═══════════════════════════════════════════════════════════════════════════
// CONSTANTS (LOCKED ENUM - DO NOT MODIFY)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * DOL Subhub Process ID (Barton ID)
 */
const DOL_PROCESS_ID = '01.04.02.04.22000';

/**
 * Source system identifier for error_master
 */
const SOURCE_SYSTEM = 'DOL_EIN_SUBHUB';

/**
 * Subhub identifier
 */
const SUBHUB = 'DOL_EIN';

/**
 * Severity level for FAIL HARD conditions
 * CANONICAL VALUE - DO NOT CHANGE
 */
const SEVERITY_HARD_FAIL = 'HARD_FAIL';

/**
 * EIN format validation
 * Format: XX-XXXXXXX (9 digits with hyphen)
 */
const EIN_REGEX = /^\d{2}-\d{7}$/;

/**
 * Valid DOL source types per doctrine
 */
const VALID_SOURCES = [
  'DOL_FORM_5500',
  'EBSA_FILING',
  'DOL_EFAST2',
  'DOL_MANUAL_VERIFIED'
];

/**
 * AIR Event Types per doctrine (LOCKED ENUM)
 * Maps exactly to FAIL HARD conditions
 */
const AIR_EVENT_TYPES = {
  IDENTITY_GATE_FAILED: 'IDENTITY_GATE_FAILED',
  MULTI_EIN_FOUND: 'MULTI_EIN_FOUND',
  EIN_MISMATCH: 'EIN_MISMATCH',
  FILING_TTL_EXCEEDED: 'FILING_TTL_EXCEEDED',
  SOURCE_UNAVAILABLE: 'SOURCE_UNAVAILABLE',
  CROSS_CONTEXT_CONTAMINATION: 'CROSS_CONTEXT_CONTAMINATION',
  EIN_FORMAT_INVALID: 'EIN_FORMAT_INVALID',
  HASH_VERIFICATION_FAILED: 'HASH_VERIFICATION_FAILED',
  COMPANY_TARGET_NOT_PASS: 'COMPANY_TARGET_NOT_PASS',
  DOL_FILING_NOT_CONFIRMED: 'DOL_FILING_NOT_CONFIRMED',  // Fuzzy found candidates but deterministic rejected all
  LINKAGE_SUCCESS: 'LINKAGE_SUCCESS'
};

/**
 * Company Target Status (EXECUTION GATE)
 * DOL CANNOT run unless company_target_status = PASS
 */
const COMPANY_TARGET_STATUS = {
  PASS: 'PASS',
  FAIL: 'FAIL',
  PENDING: 'PENDING'
};

/**
 * EIN Resolution Gate Error Code
 * DOL CANNOT run unless ein IS NOT NULL
 */
const EIN_RESOLUTION_GATE_ERROR = 'EIN_NOT_RESOLVED_PRE_DOL';

/**
 * AIR Event Status
 */
const AIR_STATUS = {
  SUCCESS: 'SUCCESS',
  FAILED: 'FAILED',
  ABORTED: 'ABORTED'
};

// ═══════════════════════════════════════════════════════════════════════════
// DATABASE WRITE FUNCTIONS (STUBS - IMPLEMENT WITH YOUR DB CLIENT)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Write AIR event to dol.air_log
 * MUST be called before shq_error_log write
 *
 * @param {Object} airEvent - AIR event payload
 * @returns {Promise<string>} air_event_id
 */
async function writeAIREvent(airEvent) {
  // IMPLEMENTATION: Use your database client (e.g., pg, neon, composio)
  // INSERT INTO dol.air_log (...)
  // RETURN air_log_id
  
  // Stub: Generate placeholder ID
  const airEventId = `01.04.02.04.22000.9${String(Date.now() % 100).padStart(2, '0')}`;
  
  console.log('[AIR] Event logged:', {
    air_event_id: airEventId,
    event_type: airEvent.event_type,
    event_status: airEvent.event_status
  });
  
  return airEventId;
}

/**
 * Write error to shq.error_master (CANONICAL error table)
 * MUST be called after AIR write
 *
 * CANONICAL Error Write Contract:
 *   - error_id (generated)
 *   - process_id = '01.04.02.04.22000'
 *   - agent_name = 'DOL_EIN_SUBHUB'
 *   - severity = 'HARD_FAIL'
 *   - source_system = 'DOL_EIN_SUBHUB'
 *   - air_event_id (FK / reference)
 *   - created_at
 *
 * NOTE: shq_error_log is DEPRECATED. Use shq.error_master only.
 *
 * @param {Object} errorData - Error data
 * @param {string} airEventId - Reference to AIR event
 * @returns {Promise<string>} error_id
 */
async function writeErrorMaster(errorData, airEventId) {
  // IMPLEMENTATION: Use your database client
  // INSERT INTO shq.error_master (...)
  // NOTE: shq_error_log is DEPRECATED - do not use
  
  const errorId = crypto.randomUUID();
  
  const errorRecord = {
    error_id: errorId,
    occurred_at: new Date().toISOString(),
    process_id: DOL_PROCESS_ID,
    agent_id: SOURCE_SYSTEM,
    severity: SEVERITY_HARD_FAIL,  // CANONICAL: 'HARD_FAIL'
    error_type: errorData.error_code,
    message: `[${errorData.error_code}] ${errorData.message}`,
    context: JSON.stringify({
      air_event_id: airEventId,
      subhub: SUBHUB,
      source_system: SOURCE_SYSTEM,
      company_unique_id: errorData.company_unique_id,
      outreach_context_id: errorData.outreach_context_id,
      payload: errorData.payload
    }),
    created_at: new Date().toISOString()
  };
  
  console.log('[shq.error_master] Error logged:', {
    error_id: errorId,
    process_id: DOL_PROCESS_ID,
    severity: SEVERITY_HARD_FAIL,
    error_type: errorData.error_code,
    air_event_id: airEventId
  });
  
  return errorId;
}

// ═══════════════════════════════════════════════════════════════════════════
// CENTRALIZED FAIL HARD FUNCTION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * CENTRALIZED FAIL HARD HANDLER
 *
 * This is the SINGLE function that handles all abort paths.
 * Implements dual-write: AIR (authoritative) + shq_error_log (operational)
 *
 * Sequence:
 *   1. Emit AIR event (truth/audit)
 *   2. Write to shq_error_log (operations/triage)
 *   3. Return failure result (terminates execution)
 *
 * No retries. No fallback. No swallowing errors.
 *
 * @param {string} errorCode - Error code from AIR_EVENT_TYPES enum
 * @param {string} message - Human-readable error message
 * @param {Object} context - Context object with company_unique_id, outreach_context_id, etc.
 * @returns {Promise<Object>} Failure result with airEvent and errorRecord
 */
async function failHard(errorCode, message, context = {}) {
  const {
    company_unique_id = null,
    outreach_context_id = null,
    identityGatePassed = false,
    identityAnchors = {},
    payload = {}
  } = context;

  // Step 1: Create AIR event
  const airEvent = {
    event_type: errorCode,
    event_status: AIR_STATUS.ABORTED,
    event_message: message,
    event_payload: payload,
    identity_gate_passed: identityGatePassed,
    identity_anchors_present: identityAnchors,
    company_unique_id,
    outreach_context_id,
    created_at: new Date().toISOString()
  };

  // Step 2: Write to AIR (authoritative - MUST succeed before error_master)
  const airEventId = await writeAIREvent(airEvent);

  // Step 3: Write to shq_error_log (operational - AFTER AIR)
  const errorId = await writeErrorMaster({
    error_code: errorCode,
    message,
    company_unique_id,
    outreach_context_id,
    payload
  }, airEventId);

  // Step 4: Return failure result (terminates execution)
  return {
    success: false,
    error_code: errorCode,
    air_event_id: airEventId,
    error_id: errorId,
    airEvent,
    message
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// EXECUTION GATE: COMPANY TARGET → DOL EIN
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validate Company Target status (EXECUTION GATE)
 *
 * CANONICAL EXECUTION ORDER:
 *   Company Target (PASS) → DOL Subhub — EIN Resolution
 *
 * DOL MUST NOT RUN unless Company Target has completed successfully.
 *
 * If Company Target is:
 *   - FAIL → DOL must not run
 *   - PENDING → DOL must not run
 *   - Missing → FAIL HARD
 *
 * This gate MUST occur BEFORE any DOL source access.
 *
 * @param {string} companyTargetStatus - Status from Company Target ('PASS', 'FAIL', 'PENDING', or null/undefined)
 * @returns {Object} { isValid: boolean, failureReason: string|null }
 */
function validateCompanyTargetGate(companyTargetStatus) {
  // Missing status = FAIL HARD
  if (companyTargetStatus === null || companyTargetStatus === undefined) {
    return {
      isValid: false,
      failureReason: 'COMPANY_TARGET_STATUS_MISSING: Company Target must complete before DOL EIN can execute'
    };
  }

  // Only PASS allows DOL to proceed
  if (companyTargetStatus !== COMPANY_TARGET_STATUS.PASS) {
    return {
      isValid: false,
      failureReason: `COMPANY_TARGET_NOT_PASS: Company Target status is '${companyTargetStatus}', must be 'PASS' for DOL EIN to execute`
    };
  }

  return {
    isValid: true,
    failureReason: null
  };
}

/**
 * EXECUTION GATE: EIN Resolution (CRITICAL)
 *
 * DOL Subhub execution requires:
 *   - ein IS NOT NULL
 *   - company_target_status = PASS
 *
 * CANONICAL RULE:
 *   Fuzzy matching to attach EIN ↔ company_unique_id is allowed ONLY in
 *   Company Target / Identity Resolution.
 *   The DOL Subhub requires a LOCKED EIN and must NEVER see fuzzy logic.
 *
 * If violated:
 *   - Emit AIR
 *   - Write to shq.error_master
 *   - Abort execution
 *
 * No fallback logic.
 *
 * @param {string|null} ein - EIN from Company Target (must be resolved)
 * @param {string} companyTargetStatus - Status from Company Target
 * @returns {Object} { isValid: boolean, failureReason: string|null, gateType: string }
 */
function validateEINResolutionGate(ein, companyTargetStatus) {
  // Gate 1: Company Target must be PASS
  const companyGate = validateCompanyTargetGate(companyTargetStatus);
  if (!companyGate.isValid) {
    return {
      isValid: false,
      failureReason: companyGate.failureReason,
      gateType: 'COMPANY_TARGET_GATE'
    };
  }

  // Gate 2: EIN must be resolved (NOT NULL)
  if (ein === null || ein === undefined || (typeof ein === 'string' && !ein.trim())) {
    return {
      isValid: false,
      failureReason: 'EIN_NOT_RESOLVED: EIN must be resolved by Company Target before DOL can execute. Route to ENRICHMENT.',
      gateType: 'EIN_RESOLUTION_GATE'
    };
  }

  // Gate 3: EIN must be valid format
  if (!EIN_REGEX.test(ein)) {
    return {
      isValid: false,
      failureReason: `EIN_FORMAT_INVALID: EIN '${ein}' does not match required format XX-XXXXXXX`,
      gateType: 'EIN_FORMAT_GATE'
    };
  }

  return {
    isValid: true,
    failureReason: null,
    gateType: 'PASS'
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// VALIDATION FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validate identity gate requirements
 * FAIL HARD if any requirement is missing
 *
 * Required:
 *   - company_unique_id (sovereign, immutable)
 *   - outreach_context_id
 *   - state
 *   - At least one identity anchor: company_domain OR linkedin_company_url
 *
 * @param {Object} params - Identity gate parameters
 * @returns {Object} { isValid: boolean, failureReason: string|null, identityAnchors: Object }
 */
function validateIdentityGate(params) {
  const {
    company_unique_id,
    outreach_context_id,
    state,
    company_domain,
    linkedin_company_url
  } = params;

  const identityAnchors = {
    company_domain: Boolean(company_domain && company_domain.trim()),
    linkedin_company_url: Boolean(linkedin_company_url && linkedin_company_url.trim())
  };

  const hasAnchor = identityAnchors.company_domain || identityAnchors.linkedin_company_url;

  // Check required fields
  if (!company_unique_id || !company_unique_id.trim()) {
    return {
      isValid: false,
      failureReason: 'MISSING: company_unique_id (sovereign, immutable)',
      identityAnchors
    };
  }

  if (!outreach_context_id || !outreach_context_id.trim()) {
    return {
      isValid: false,
      failureReason: 'MISSING: outreach_context_id',
      identityAnchors
    };
  }

  if (!state || !state.trim()) {
    return {
      isValid: false,
      failureReason: 'MISSING: state',
      identityAnchors
    };
  }

  if (!hasAnchor) {
    return {
      isValid: false,
      failureReason: 'MISSING: at least one identity anchor (company_domain OR linkedin_company_url)',
      identityAnchors
    };
  }

  return {
    isValid: true,
    failureReason: null,
    identityAnchors
  };
}

/**
 * Validate EIN format
 * Format: XX-XXXXXXX (9 digits with hyphen)
 *
 * @param {string} ein - EIN to validate
 * @returns {Object} { isValid: boolean, failureReason: string|null }
 */
function validateEINFormat(ein) {
  if (!ein) {
    return {
      isValid: false,
      failureReason: 'EIN is null or empty'
    };
  }

  if (!EIN_REGEX.test(ein)) {
    return {
      isValid: false,
      failureReason: `EIN format invalid. Expected: XX-XXXXXXX. Received: ${ein}`
    };
  }

  return {
    isValid: true,
    failureReason: null
  };
}

/**
 * Validate source type per doctrine
 *
 * @param {string} source - Source type to validate
 * @returns {Object} { isValid: boolean, failureReason: string|null }
 */
function validateSource(source) {
  if (!VALID_SOURCES.includes(source)) {
    return {
      isValid: false,
      failureReason: `Invalid source: ${source}. Valid sources: ${VALID_SOURCES.join(', ')}`
    };
  }

  return {
    isValid: true,
    failureReason: null
  };
}

/**
 * Validate filing year against TTL
 * Default TTL: 3 years
 *
 * @param {number} filingYear - Year of the filing
 * @param {number} ttlYears - TTL in years (default: 3)
 * @returns {Object} { isValid: boolean, failureReason: string|null }
 */
function validateFilingTTL(filingYear, ttlYears = 3) {
  const currentYear = new Date().getFullYear();
  const age = currentYear - filingYear;

  if (age > ttlYears) {
    return {
      isValid: false,
      failureReason: `Filing year ${filingYear} exceeds TTL of ${ttlYears} years (age: ${age} years)`
    };
  }

  return {
    isValid: true,
    failureReason: null
  };
}

/**
 * Generate SHA-256 hash fingerprint for document
 *
 * @param {Buffer|string} content - Document content to hash
 * @returns {string} SHA-256 hash (lowercase hex)
 */
function generateHashFingerprint(content) {
  return crypto.createHash('sha256').update(content).digest('hex');
}

/**
 * Validate hash fingerprint format
 *
 * @param {string} hash - Hash to validate
 * @returns {Object} { isValid: boolean, failureReason: string|null }
 */
function validateHashFingerprint(hash) {
  if (!hash) {
    return {
      isValid: false,
      failureReason: 'Hash fingerprint is null or empty'
    };
  }

  if (!/^[a-f0-9]{64}$/.test(hash)) {
    return {
      isValid: false,
      failureReason: 'Invalid SHA-256 hash fingerprint format'
    };
  }

  return {
    isValid: true,
    failureReason: null
  };
}

/**
 * Create AIR event payload (for success case)
 *
 * @param {string} eventType - AIR event type
 * @param {string} eventStatus - AIR event status
 * @param {string} message - Event message
 * @param {Object} params - Additional parameters
 * @returns {Object} AIR event payload
 */
function createAIREvent(eventType, eventStatus, message, params = {}) {
  return {
    event_type: eventType,
    event_status: eventStatus,
    event_message: message,
    event_payload: params.payload || {},
    identity_gate_passed: params.identityGatePassed || false,
    identity_anchors_present: params.identityAnchors || {},
    company_unique_id: params.company_unique_id || null,
    outreach_context_id: params.outreach_context_id || null,
    created_at: new Date().toISOString()
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN PIPELINE - USES CENTRALIZED failHard()
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Complete EIN linkage validation pipeline
 * Implements FAIL HARD doctrine with DUAL-WRITE
 *
 * CANONICAL EXECUTION ORDER:
 *   Company Target (PASS) → DOL Subhub — EIN Resolution
 *
 * All abort paths use centralized failHard() function that:
 *   1. Emits AIR event (authoritative)
 *   2. Writes to shq.error_master (operational)
 *   3. Terminates execution
 *
 * @param {Object} params - Linkage parameters
 * @returns {Promise<Object>} Validation result with dual-write confirmation
 */
async function validateEINLinkage(params) {
  const {
    company_unique_id,
    outreach_context_id,
    company_target_status,  // REQUIRED: Must be 'PASS' for DOL to execute
    state,
    company_domain,
    linkedin_company_url,
    ein,
    source,
    source_url,
    filing_year,
    hash_fingerprint,
    filing_ttl_years = 3
  } = params;

  // ─────────────────────────────────────────────────────────────────────────
  // Step 0: COMBINED EXECUTION GATE (CRITICAL - BEFORE ANY DOL ACCESS)
  // ─────────────────────────────────────────────────────────────────────────
  // DOL execution requires BOTH:
  //   - company_target_status = PASS
  //   - ein IS NOT NULL (resolved by Company Target)
  //
  // Fuzzy matching is allowed ONLY in Company Target.
  // DOL must NEVER see fuzzy logic.
  // This gate occurs BEFORE any DOL source access.
  const executionGateResult = validateEINResolutionGate(ein, company_target_status);
  if (!executionGateResult.isValid) {
    const errorCode = executionGateResult.gateType === 'COMPANY_TARGET_GATE'
      ? AIR_EVENT_TYPES.COMPANY_TARGET_NOT_PASS
      : AIR_EVENT_TYPES.EIN_FORMAT_INVALID;

    return failHard(
      errorCode,
      executionGateResult.failureReason,
      {
        company_unique_id,
        outreach_context_id,
        identityGatePassed: false,
        identityAnchors: {},
        payload: {
          company_target_status,
          ein,
          gate_type: executionGateResult.gateType,
          remediation_required: executionGateResult.gateType === 'EIN_RESOLUTION_GATE' ? 'ENRICHMENT' : null
        }
      }
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Step 1: Identity Gate Validation (FAIL HARD)
  // ─────────────────────────────────────────────────────────────────────────
  const gateResult = validateIdentityGate({
    company_unique_id,
    outreach_context_id,
    state,
    company_domain,
    linkedin_company_url
  });

  if (!gateResult.isValid) {
    return failHard(
      AIR_EVENT_TYPES.IDENTITY_GATE_FAILED,
      gateResult.failureReason,
      {
        company_unique_id,
        outreach_context_id,
        identityGatePassed: false,
        identityAnchors: gateResult.identityAnchors,
        payload: { state, company_domain, linkedin_company_url }
      }
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Step 2: EIN Format Validation (FAIL HARD)
  // ─────────────────────────────────────────────────────────────────────────
  const einResult = validateEINFormat(ein);
  if (!einResult.isValid) {
    return failHard(
      AIR_EVENT_TYPES.EIN_FORMAT_INVALID,
      einResult.failureReason,
      {
        company_unique_id,
        outreach_context_id,
        identityGatePassed: true,
        identityAnchors: gateResult.identityAnchors,
        payload: { ein }
      }
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Step 3: Source Validation (FAIL HARD)
  // ─────────────────────────────────────────────────────────────────────────
  const sourceResult = validateSource(source);
  if (!sourceResult.isValid) {
    return failHard(
      AIR_EVENT_TYPES.SOURCE_UNAVAILABLE,
      sourceResult.failureReason,
      {
        company_unique_id,
        outreach_context_id,
        identityGatePassed: true,
        identityAnchors: gateResult.identityAnchors,
        payload: { source }
      }
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Step 4: Filing TTL Validation (FAIL HARD)
  // ─────────────────────────────────────────────────────────────────────────
  const ttlResult = validateFilingTTL(filing_year, filing_ttl_years);
  if (!ttlResult.isValid) {
    return failHard(
      AIR_EVENT_TYPES.FILING_TTL_EXCEEDED,
      ttlResult.failureReason,
      {
        company_unique_id,
        outreach_context_id,
        identityGatePassed: true,
        identityAnchors: gateResult.identityAnchors,
        payload: { filing_year, ttl_years: filing_ttl_years }
      }
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Step 5: Hash Fingerprint Validation (FAIL HARD)
  // ─────────────────────────────────────────────────────────────────────────
  const hashResult = validateHashFingerprint(hash_fingerprint);
  if (!hashResult.isValid) {
    return failHard(
      AIR_EVENT_TYPES.HASH_VERIFICATION_FAILED,
      hashResult.failureReason,
      {
        company_unique_id,
        outreach_context_id,
        identityGatePassed: true,
        identityAnchors: gateResult.identityAnchors,
        payload: { hash_fingerprint }
      }
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // All validations passed - return success
  // Success ONLY writes to AIR (no error_master write for success)
  // ─────────────────────────────────────────────────────────────────────────
  const successAirEvent = createAIREvent(
    AIR_EVENT_TYPES.LINKAGE_SUCCESS,
    AIR_STATUS.SUCCESS,
    `EIN linkage validated: ${ein}`,
    {
      identityGatePassed: true,
      identityAnchors: gateResult.identityAnchors,
      company_unique_id,
      outreach_context_id,
      payload: { ein, source, filing_year }
    }
  );

  const airEventId = await writeAIREvent(successAirEvent);

  return {
    success: true,
    air_event_id: airEventId,
    validatedData: {
      company_unique_id,
      outreach_context_id,
      ein,
      source,
      source_url,
      filing_year,
      hash_fingerprint
    },
    airEvent: successAirEvent
  };
}

/**
 * Additional FAIL HARD functions for external kill switches
 * Use these when detecting conditions outside the main validation flow
 */

/**
 * FAIL HARD: Multiple EINs found for company
 */
async function failHardMultiEIN(company_unique_id, outreach_context_id, existingEIN, newEIN, identityAnchors = {}) {
  return failHard(
    AIR_EVENT_TYPES.MULTI_EIN_FOUND,
    `Multiple EINs found: existing=${existingEIN}, new=${newEIN}`,
    {
      company_unique_id,
      outreach_context_id,
      identityGatePassed: true,
      identityAnchors,
      payload: { existing_ein: existingEIN, new_ein: newEIN }
    }
  );
}

/**
 * FAIL HARD: EIN mismatch across filings
 */
async function failHardEINMismatch(company_unique_id, outreach_context_id, expectedEIN, foundEIN, identityAnchors = {}) {
  return failHard(
    AIR_EVENT_TYPES.EIN_MISMATCH,
    `EIN mismatch: expected=${expectedEIN}, found=${foundEIN}`,
    {
      company_unique_id,
      outreach_context_id,
      identityGatePassed: true,
      identityAnchors,
      payload: { expected_ein: expectedEIN, found_ein: foundEIN }
    }
  );
}

/**
 * FAIL HARD: Cross-context contamination detected
 */
async function failHardCrossContext(company_unique_id, outreach_context_id, detectedContext, identityAnchors = {}) {
  return failHard(
    AIR_EVENT_TYPES.CROSS_CONTEXT_CONTAMINATION,
    `Cross-context contamination: expected=${outreach_context_id}, detected=${detectedContext}`,
    {
      company_unique_id,
      outreach_context_id,
      identityGatePassed: true,
      identityAnchors,
      payload: { expected_context: outreach_context_id, detected_context: detectedContext }
    }
  );
}

/**
 * FAIL HARD: Filing not confirmed after fuzzy discovery
 *
 * Triggered when:
 *   - Fuzzy matching found candidate filings
 *   - Deterministic checks rejected ALL candidates
 *
 * This is NOT an EIN failure — it's a filing discovery failure.
 * The EIN is already locked from Company Target.
 *
 * @param {string} company_unique_id
 * @param {string} outreach_context_id
 * @param {string} resolvedEIN - The locked EIN from Company Target
 * @param {Array} rejectedCandidates - Candidates that failed deterministic checks
 * @param {Object} searchMetadata - Fuzzy search metadata
 */
async function failHardFilingNotConfirmed(company_unique_id, outreach_context_id, resolvedEIN, rejectedCandidates = [], searchMetadata = {}) {
  return failHard(
    AIR_EVENT_TYPES.DOL_FILING_NOT_CONFIRMED,
    `Fuzzy discovery found ${rejectedCandidates.length} candidate(s) but deterministic validation rejected all. EIN: ${resolvedEIN}`,
    {
      company_unique_id,
      outreach_context_id,
      identityGatePassed: true,
      identityAnchors: {},
      payload: {
        resolved_ein: resolvedEIN,
        candidates_found: rejectedCandidates.length,
        rejected_candidates: rejectedCandidates.slice(0, 5), // Top 5 for debugging
        search_metadata: searchMetadata,
        failure_type: 'FILING_DISCOVERY'
      }
    }
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MODULE EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

module.exports = {
  // Constants (LOCKED ENUM - CANONICAL)
  DOL_PROCESS_ID,
  SOURCE_SYSTEM,
  SUBHUB,
  SEVERITY_HARD_FAIL,  // CANONICAL: 'HARD_FAIL'
  EIN_REGEX,
  VALID_SOURCES,
  AIR_EVENT_TYPES,
  AIR_STATUS,
  COMPANY_TARGET_STATUS,  // EXECUTION GATE
  EIN_RESOLUTION_GATE_ERROR,  // EIN NOT NULL gate

  // Centralized FAIL HARD handler
  failHard,

  // Execution Gates (Company Target → DOL)
  validateCompanyTargetGate,
  validateEINResolutionGate,  // CRITICAL: ein IS NOT NULL + company_target_status = PASS

  // Validation functions
  validateIdentityGate,
  validateEINFormat,
  validateSource,
  validateFilingTTL,
  validateHashFingerprint,

  // Utility functions
  generateHashFingerprint,
  createAIREvent,

  // Database write functions (stubs - implement with your DB client)
  // NOTE: Writes to shq.error_master (shq_error_log is DEPRECATED)
  writeAIREvent,
  writeErrorMaster,

  // Main pipeline
  validateEINLinkage,

  // Additional FAIL HARD functions
  failHardMultiEIN,
  failHardEINMismatch,
  failHardCrossContext,
  failHardFilingNotConfirmed  // DOL_FILING_NOT_CONFIRMED - fuzzy found but deterministic rejected
};
