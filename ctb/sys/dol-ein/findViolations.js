/**
 * DOL Subhub — Violation Discovery Module
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Doctrine: /doctrine/ple/DOL_EIN_RESOLUTION.md
 * Schema: /doctrine/schemas/dol_violations-schema.sql
 * Barton ID: 01.04.02.04.22000.5#####
 *
 * PURPOSE:
 *   Discover and match DOL violations to EIN-resolved companies.
 *   This module:
 *   1. Searches DOL violation sources (OSHA, EBSA, WHD, etc.)
 *   2. Matches violations to existing EIN linkages
 *   3. Stores violation facts (append-only)
 *
 * FACT STORAGE ONLY:
 *   ❌ NO scoring
 *   ❌ NO outreach triggers
 *   ❌ NO BIT integration
 *   ✅ Store facts for downstream consumption
 *
 * SOURCES:
 *   - OSHA (Occupational Safety and Health Administration)
 *   - EBSA (Employee Benefits Security Administration)
 *   - WHD (Wage and Hour Division)
 *   - OFCCP (Office of Federal Contract Compliance Programs)
 *
 * ═══════════════════════════════════════════════════════════════════════════
 */

const crypto = require('crypto');

// ═══════════════════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * DOL Subhub Process ID (Barton ID)
 */
const DOL_VIOLATIONS_PROCESS_ID = '01.04.02.04.22000';

/**
 * Source agencies (LOCKED ENUM)
 */
const SOURCE_AGENCIES = {
  OSHA: 'OSHA',
  EBSA: 'EBSA',
  WHD: 'WHD',
  OFCCP: 'OFCCP',
  MSHA: 'MSHA',
  OTHER: 'OTHER'
};

/**
 * Violation severity levels (OSHA standard)
 */
const SEVERITY_LEVELS = {
  WILLFUL: 'WILLFUL',
  SERIOUS: 'SERIOUS',
  OTHER_THAN_SERIOUS: 'OTHER_THAN_SERIOUS',
  REPEAT: 'REPEAT',
  FAILURE_TO_ABATE: 'FAILURE_TO_ABATE',
  UNCLASSIFIED: 'UNCLASSIFIED'
};

/**
 * Violation status
 */
const VIOLATION_STATUS = {
  OPEN: 'OPEN',
  CONTESTED: 'CONTESTED',
  SETTLED: 'SETTLED',
  PAID: 'PAID',
  ABATED: 'ABATED',
  DELETED: 'DELETED',
  UNKNOWN: 'UNKNOWN'
};

/**
 * AIR event types for violations
 */
const VIOLATION_AIR_EVENTS = {
  VIOLATION_DISCOVERED: 'VIOLATION_DISCOVERED',
  VIOLATION_EIN_MATCHED: 'VIOLATION_EIN_MATCHED',
  VIOLATION_EIN_NOT_FOUND: 'VIOLATION_EIN_NOT_FOUND',
  VIOLATION_DUPLICATE: 'VIOLATION_DUPLICATE',
  VIOLATION_BATCH_COMPLETE: 'VIOLATION_BATCH_COMPLETE'
};

/**
 * EIN format validation
 */
const EIN_REGEX = /^\d{2}-\d{7}$/;

// ═══════════════════════════════════════════════════════════════════════════
// VALIDATION FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validate EIN format
 * @param {string} ein - EIN to validate
 * @returns {boolean}
 */
function isValidEIN(ein) {
  return ein && EIN_REGEX.test(ein);
}

/**
 * Validate source agency
 * @param {string} agency - Agency to validate
 * @returns {boolean}
 */
function isValidAgency(agency) {
  return Object.values(SOURCE_AGENCIES).includes(agency);
}

/**
 * Generate hash fingerprint for violation
 * @param {Object} violation - Violation data
 * @returns {string} SHA-256 hash
 */
function generateViolationHash(violation) {
  const hashData = JSON.stringify({
    ein: violation.ein,
    source_agency: violation.source_agency,
    case_number: violation.case_number,
    violation_type: violation.violation_type,
    violation_date: violation.violation_date,
    source_url: violation.source_url
  });
  return crypto.createHash('sha256').update(hashData).digest('hex');
}

// ═══════════════════════════════════════════════════════════════════════════
// VIOLATION DISCOVERY
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Process raw violation data from DOL sources
 *
 * @param {Object} rawViolation - Raw violation from DOL source
 * @param {string} sourceAgency - Source agency (OSHA, EBSA, etc.)
 * @returns {Object} Normalized violation record
 */
function normalizeViolation(rawViolation, sourceAgency) {
  const normalized = {
    // Required fields
    ein: rawViolation.ein || rawViolation.employer_ein || null,
    source_agency: sourceAgency,
    violation_type: rawViolation.violation_type || rawViolation.type || 'UNKNOWN',
    source_url: rawViolation.source_url || rawViolation.url || '',
    discovery_date: new Date().toISOString().split('T')[0],
    
    // Optional fields
    company_unique_id: rawViolation.company_unique_id || null,
    case_number: rawViolation.case_number || rawViolation.activity_nr || null,
    violation_date: rawViolation.violation_date || rawViolation.issuance_date || null,
    
    // Location
    site_name: rawViolation.site_name || rawViolation.estab_name || null,
    site_address: rawViolation.site_address || rawViolation.site_address || null,
    site_city: rawViolation.site_city || rawViolation.city || null,
    site_state: rawViolation.site_state || rawViolation.state || null,
    site_zip: rawViolation.site_zip || rawViolation.zip || null,
    
    // Severity and penalties
    severity: mapSeverity(rawViolation.gravity || rawViolation.violation_type_s),
    penalty_initial: parseFloat(rawViolation.initial_penalty || rawViolation.penalty || 0) || null,
    penalty_current: parseFloat(rawViolation.current_penalty || rawViolation.penalty || 0) || null,
    penalty_paid: parseFloat(rawViolation.penalty_paid || 0) || null,
    status: mapStatus(rawViolation.status || rawViolation.contest_status || 'OPEN'),
    
    // Citation
    citation_id: rawViolation.citation_id || null,
    citation_url: rawViolation.citation_url || null,
    
    // Description
    violation_description: rawViolation.description || rawViolation.standard_desc || null,
    
    // Source tracking
    source_record_id: rawViolation.id || rawViolation.record_id || null
  };
  
  // Generate hash
  normalized.hash_fingerprint = generateViolationHash(normalized);
  
  return normalized;
}

/**
 * Map raw severity to standard enum
 */
function mapSeverity(rawSeverity) {
  if (!rawSeverity) return null;
  
  const severityMap = {
    'W': SEVERITY_LEVELS.WILLFUL,
    'S': SEVERITY_LEVELS.SERIOUS,
    'O': SEVERITY_LEVELS.OTHER_THAN_SERIOUS,
    'R': SEVERITY_LEVELS.REPEAT,
    'U': SEVERITY_LEVELS.UNCLASSIFIED,
    'WILLFUL': SEVERITY_LEVELS.WILLFUL,
    'SERIOUS': SEVERITY_LEVELS.SERIOUS,
    'OTHER': SEVERITY_LEVELS.OTHER_THAN_SERIOUS,
    'REPEAT': SEVERITY_LEVELS.REPEAT,
    'FAILURE TO ABATE': SEVERITY_LEVELS.FAILURE_TO_ABATE
  };
  
  return severityMap[rawSeverity.toUpperCase()] || SEVERITY_LEVELS.UNCLASSIFIED;
}

/**
 * Map raw status to standard enum
 */
function mapStatus(rawStatus) {
  if (!rawStatus) return VIOLATION_STATUS.UNKNOWN;
  
  const statusMap = {
    'OPEN': VIOLATION_STATUS.OPEN,
    'CONTESTED': VIOLATION_STATUS.CONTESTED,
    'SETTLED': VIOLATION_STATUS.SETTLED,
    'PAID': VIOLATION_STATUS.PAID,
    'ABATED': VIOLATION_STATUS.ABATED,
    'DELETED': VIOLATION_STATUS.DELETED,
    'FINAL ORDER': VIOLATION_STATUS.SETTLED,
    'INFORMAL': VIOLATION_STATUS.CONTESTED
  };
  
  return statusMap[rawStatus.toUpperCase()] || VIOLATION_STATUS.UNKNOWN;
}

// ═══════════════════════════════════════════════════════════════════════════
// EIN MATCHING
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Match violation to existing EIN linkage
 *
 * CRITICAL: Violation must link to EXISTING EIN linkage.
 * We do NOT create new EIN linkages from violations.
 *
 * @param {string} violationEIN - EIN from violation record
 * @param {Array} einLinkages - Existing EIN linkages from dol.ein_linkage
 * @returns {Object} { matched: boolean, company_unique_id: string|null, matchType: string }
 */
function matchViolationToEIN(violationEIN, einLinkages) {
  if (!isValidEIN(violationEIN)) {
    return {
      matched: false,
      company_unique_id: null,
      matchType: 'INVALID_EIN'
    };
  }
  
  // Find exact EIN match
  const linkage = einLinkages.find(l => l.ein === violationEIN);
  
  if (linkage) {
    return {
      matched: true,
      company_unique_id: linkage.company_unique_id,
      matchType: 'EXACT_EIN'
    };
  }
  
  return {
    matched: false,
    company_unique_id: null,
    matchType: 'NO_LINKAGE'
  };
}

/**
 * Match violations batch to EIN linkages
 *
 * @param {Array} violations - Normalized violation records
 * @param {Array} einLinkages - Existing EIN linkages
 * @returns {Object} { matched: Array, unmatched: Array, stats: Object }
 */
function matchViolationsBatch(violations, einLinkages) {
  const matched = [];
  const unmatched = [];
  
  for (const violation of violations) {
    const matchResult = matchViolationToEIN(violation.ein, einLinkages);
    
    if (matchResult.matched) {
      matched.push({
        ...violation,
        company_unique_id: matchResult.company_unique_id,
        match_type: matchResult.matchType
      });
    } else {
      unmatched.push({
        ...violation,
        match_type: matchResult.matchType
      });
    }
  }
  
  return {
    matched,
    unmatched,
    stats: {
      total: violations.length,
      matched_count: matched.length,
      unmatched_count: unmatched.length,
      match_rate: violations.length > 0 
        ? (matched.length / violations.length * 100).toFixed(1) + '%'
        : '0%'
    }
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// VIOLATION PROCESSING PIPELINE
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Process violations from DOL source
 *
 * Pipeline:
 * 1. Normalize raw violations
 * 2. Match to existing EIN linkages
 * 3. Return ready-for-insert records
 *
 * @param {Array} rawViolations - Raw violations from DOL source
 * @param {string} sourceAgency - Source agency (OSHA, EBSA, etc.)
 * @param {Array} einLinkages - Existing EIN linkages
 * @param {Object} options - Processing options
 * @returns {Object} Processing result
 */
function processViolations(rawViolations, sourceAgency, einLinkages, options = {}) {
  const {
    requireEINMatch = false,  // If true, only return matched violations
    outreachContextId = null
  } = options;
  
  // Step 1: Validate source agency
  if (!isValidAgency(sourceAgency)) {
    return {
      success: false,
      error: `Invalid source agency: ${sourceAgency}`,
      violations: [],
      stats: null
    };
  }
  
  // Step 2: Normalize violations
  const normalized = rawViolations.map(v => normalizeViolation(v, sourceAgency));
  
  // Step 3: Filter invalid EINs
  const withValidEIN = normalized.filter(v => isValidEIN(v.ein));
  const invalidEINCount = normalized.length - withValidEIN.length;
  
  // Step 4: Match to EIN linkages
  const matchResult = matchViolationsBatch(withValidEIN, einLinkages);
  
  // Step 5: Add outreach context
  const addContext = (violations) => violations.map(v => ({
    ...v,
    outreach_context_id: outreachContextId
  }));
  
  // Step 6: Prepare result
  const result = {
    success: true,
    violations: requireEINMatch 
      ? addContext(matchResult.matched)
      : addContext([...matchResult.matched, ...matchResult.unmatched]),
    matched: addContext(matchResult.matched),
    unmatched: matchResult.unmatched,
    stats: {
      ...matchResult.stats,
      invalid_ein_count: invalidEINCount,
      source_agency: sourceAgency,
      processed_at: new Date().toISOString()
    }
  };
  
  return result;
}

// ═══════════════════════════════════════════════════════════════════════════
// AIR EVENT CREATION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Create AIR event for violation processing
 *
 * @param {string} eventType - Event type from VIOLATION_AIR_EVENTS
 * @param {Object} violation - Violation record
 * @param {Object} context - Additional context
 * @returns {Object} AIR event payload
 */
function createViolationAIREvent(eventType, violation, context = {}) {
  return {
    event_type: eventType,
    event_status: context.status || 'SUCCESS',
    event_message: context.message || `Violation event: ${eventType}`,
    event_payload: {
      ein: violation?.ein,
      source_agency: violation?.source_agency,
      case_number: violation?.case_number,
      severity: violation?.severity,
      company_unique_id: violation?.company_unique_id,
      ...context.payload
    },
    company_unique_id: violation?.company_unique_id || null,
    outreach_context_id: violation?.outreach_context_id || context.outreach_context_id || null,
    created_at: new Date().toISOString()
  };
}

/**
 * Create batch completion AIR event
 *
 * @param {Object} stats - Processing statistics
 * @param {string} sourceAgency - Source agency
 * @param {string} outreachContextId - Context ID
 * @returns {Object} AIR event payload
 */
function createBatchCompleteAIREvent(stats, sourceAgency, outreachContextId = null) {
  return {
    event_type: VIOLATION_AIR_EVENTS.VIOLATION_BATCH_COMPLETE,
    event_status: 'SUCCESS',
    event_message: `Processed ${stats.total} violations from ${sourceAgency}`,
    event_payload: {
      source_agency: sourceAgency,
      total_processed: stats.total,
      matched_count: stats.matched_count,
      unmatched_count: stats.unmatched_count,
      match_rate: stats.match_rate,
      invalid_ein_count: stats.invalid_ein_count || 0
    },
    company_unique_id: null,
    outreach_context_id: outreachContextId,
    created_at: new Date().toISOString()
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// OSHA-SPECIFIC HELPERS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Parse OSHA inspection data
 * Source: https://enforcedata.dol.gov/api/
 *
 * @param {Object} oshaInspection - Raw OSHA inspection record
 * @returns {Array} Normalized violation records
 */
function parseOSHAInspection(oshaInspection) {
  const violations = [];
  
  // OSHA inspections can have multiple violations
  const violationList = oshaInspection.violations || [oshaInspection];
  
  for (const v of violationList) {
    violations.push({
      ein: oshaInspection.ein || null,
      source_agency: SOURCE_AGENCIES.OSHA,
      case_number: oshaInspection.activity_nr,
      violation_type: v.violation_type_s || 'OSHA_GENERAL',
      violation_date: oshaInspection.open_date,
      
      site_name: oshaInspection.estab_name,
      site_address: oshaInspection.site_address,
      site_city: oshaInspection.site_city,
      site_state: oshaInspection.site_state,
      site_zip: oshaInspection.site_zip,
      
      severity: v.gravity,
      penalty_initial: v.initial_penalty,
      penalty_current: v.current_penalty,
      status: oshaInspection.case_status,
      
      violation_description: v.standard_desc,
      source_url: `https://enforcedata.dol.gov/views/inspection/${oshaInspection.activity_nr}`,
      source_record_id: v.citation_id || oshaInspection.activity_nr
    });
  }
  
  return violations;
}

// ═══════════════════════════════════════════════════════════════════════════
// MODULE EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

module.exports = {
  // Constants
  DOL_VIOLATIONS_PROCESS_ID,
  SOURCE_AGENCIES,
  SEVERITY_LEVELS,
  VIOLATION_STATUS,
  VIOLATION_AIR_EVENTS,
  EIN_REGEX,
  
  // Validation
  isValidEIN,
  isValidAgency,
  generateViolationHash,
  
  // Normalization
  normalizeViolation,
  mapSeverity,
  mapStatus,
  
  // EIN Matching
  matchViolationToEIN,
  matchViolationsBatch,
  
  // Pipeline
  processViolations,
  
  // AIR Events
  createViolationAIREvent,
  createBatchCompleteAIREvent,
  
  // Source-specific parsers
  parseOSHAInspection
};
