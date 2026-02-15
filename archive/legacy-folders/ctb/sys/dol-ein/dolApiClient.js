/**
 * DOL Open Data API Client
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Doctrine: /doctrine/ple/DOL_EIN_RESOLUTION.md
 * API Docs: https://data.dol.gov/get-started
 *
 * PURPOSE:
 *   Production API client for DOL Open Data Portal (data.dol.gov)
 *   Handles authentication, rate limiting, and pagination.
 *
 * SOURCES SUPPORTED:
 *   - EBSA OCATS (Employee Benefits Security Administration)
 *   - OSHA Inspections (Occupational Safety)
 *   - WHD (Wage and Hour Division)
 *   - MSHA (Mine Safety and Health)
 *
 * AUTHENTICATION:
 *   Requires DOL_API_KEY from Doppler (env var)
 *
 * ═══════════════════════════════════════════════════════════════════════════
 */

// ═══════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * API Key from Doppler
 * NEVER hardcode - always from environment
 */
const DOL_API_KEY = process.env.DOL_API_KEY;

/**
 * API Base URLs
 */
const API_ENDPOINTS = {
  // Production API
  BASE: 'https://apiprod.dol.gov/v4',
  
  // Datasets
  EBSA_OCATS: '/ebsa/ocats',        // Employee Benefits violations
  OSHA_INSPECTION: '/osha/inspection',
  OSHA_VIOLATION: '/osha/violation',
  WHD_WHISARD: '/whd/whisard',      // Wage & Hour violations
  MSHA_MINE: '/msha/mineinfo',
  MSHA_VIOLATIONS: '/msha/violations',
  
  // Legacy enforcedata (may still be needed for some datasets)
  LEGACY_BASE: 'https://enforcedata.dol.gov/api'
};

/**
 * Rate limiting configuration
 */
const RATE_LIMIT = {
  MAX_REQUESTS_PER_SECOND: 5,
  RETRY_AFTER_MS: 1000,
  MAX_RETRIES: 3
};

/**
 * Default query parameters
 */
const DEFAULT_PARAMS = {
  limit: 100,
  offset: 0
};

/**
 * Target states for violation discovery (Mid-Atlantic / Appalachian focus)
 * 
 * Canonical list - 8 states:
 *   WV - West Virginia
 *   VA - Virginia
 *   PA - Pennsylvania
 *   MD - Maryland
 *   OH - Ohio
 *   KY - Kentucky
 *   DE - Delaware
 *   NC - North Carolina
 */
const TARGET_STATES = ['WV', 'VA', 'PA', 'MD', 'OH', 'KY', 'DE', 'NC'];

// ═══════════════════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validate API key is present
 * @throws {Error} if DOL_API_KEY is not set
 */
function validateApiKey() {
  if (!DOL_API_KEY) {
    throw new Error(
      'DOL_API_KEY is not set. Add it to Doppler or set as environment variable.'
    );
  }
}

/**
 * Build URL with query parameters
 * @param {string} endpoint - API endpoint path
 * @param {Object} params - Query parameters
 * @returns {string} Full URL with parameters
 */
function buildUrl(endpoint, params = {}) {
  const url = new URL(`${API_ENDPOINTS.BASE}${endpoint}`);
  
  // Add API key as query parameter (DOL API style)
  url.searchParams.set('X-API-KEY', DOL_API_KEY);
  
  // Add other parameters
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.set(key, value);
    }
  });
  
  return url.toString();
}

/**
 * Sleep for rate limiting
 * @param {number} ms - Milliseconds to sleep
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Make API request with retry logic
 * @param {string} url - Full URL to request
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>} API response
 */
async function fetchWithRetry(url, options = {}) {
  let lastError;
  
  for (let attempt = 1; attempt <= RATE_LIMIT.MAX_RETRIES; attempt++) {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Accept': 'application/json',
          'User-Agent': 'BartonOutreach/1.0 (contact@barton.com)',
          ...options.headers
        }
      });
      
      // Handle rate limiting
      if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After') || RATE_LIMIT.RETRY_AFTER_MS / 1000;
        console.warn(`Rate limited. Waiting ${retryAfter}s before retry ${attempt}/${RATE_LIMIT.MAX_RETRIES}`);
        await sleep(retryAfter * 1000);
        continue;
      }
      
      // Handle other errors
      if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(`DOL API error ${response.status}: ${errorBody}`);
      }
      
      return await response.json();
      
    } catch (error) {
      lastError = error;
      console.error(`DOL API request failed (attempt ${attempt}/${RATE_LIMIT.MAX_RETRIES}):`, error.message);
      
      if (attempt < RATE_LIMIT.MAX_RETRIES) {
        await sleep(RATE_LIMIT.RETRY_AFTER_MS * attempt);
      }
    }
  }
  
  throw lastError;
}

// ═══════════════════════════════════════════════════════════════════════════
// EBSA OCATS (Employee Benefits Security Administration)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * EBSA OCATS Dataset Fields:
 * - plan_ein: Employer EIN (XX-XXXXXXX format)
 * - plan_name: Name of the employee benefit plan
 * - plan_admin_name: Plan administrator name
 * - plan_admin_ein: Administrator EIN
 * - plan_state: State code
 * - case_type_code: Type of case (DEFICIENT, LATE, NON_FILER, etc.)
 * - civil_penalty_amt: Civil penalty amount
 * - plan_yr_dte: Plan year date
 * - ack_id: Acknowledgment ID (links to Form 5500)
 */

/**
 * Fetch EBSA OCATS violations (deficient filers, late filers, etc.)
 * 
 * @param {Object} filters - Query filters
 * @param {Array<string>} filters.states - State codes to filter (default: TARGET_STATES)
 * @param {number|Array<number>} filters.years - Plan year(s) to filter (e.g., 2023 or [2022, 2023, 2024])
 * @param {string} filters.caseType - Case type filter (DEFICIENT, LATE, NON_FILER)
 * @param {number} filters.minPenalty - Minimum penalty amount
 * @param {number} filters.limit - Results per page (default: 100)
 * @param {number} filters.offset - Pagination offset (default: 0)
 * @returns {Promise<Object>} { records: Array, metadata: Object }
 */
async function fetchEBSAOCATS(filters = {}) {
  validateApiKey();
  
  const {
    states = TARGET_STATES,
    years = null,
    caseType = null,
    minPenalty = null,
    limit = DEFAULT_PARAMS.limit,
    offset = DEFAULT_PARAMS.offset
  } = filters;
  
  // Build filter object for DOL API
  const filterObject = {};
  
  // State filter (IN clause)
  if (states && states.length > 0) {
    filterObject.plan_state = { '$in': states };
  }
  
  // Year filter - filter by plan_yr_dte (plan year date)
  // Format: YYYY-MM-DD, we filter by year portion
  if (years) {
    const yearArray = Array.isArray(years) ? years : [years];
    
    if (yearArray.length === 1) {
      // Single year - use range filter
      const year = yearArray[0];
      filterObject.plan_yr_dte = {
        '$gte': `${year}-01-01`,
        '$lte': `${year}-12-31`
      };
    } else {
      // Multiple years - need to handle differently
      // DOL API may not support OR on dates, so we'll filter client-side
      // For now, use the range from min to max year
      const minYear = Math.min(...yearArray);
      const maxYear = Math.max(...yearArray);
      filterObject.plan_yr_dte = {
        '$gte': `${minYear}-01-01`,
        '$lte': `${maxYear}-12-31`
      };
    }
  }
  
  // Case type filter
  if (caseType) {
    filterObject.case_type_code = caseType;
  }
  
  // Minimum penalty filter
  if (minPenalty) {
    filterObject.civil_penalty_amt = { '$gte': minPenalty };
  }
  
  const params = {
    limit,
    offset,
    // DOL API uses filter_object as JSON string
    filter_object: Object.keys(filterObject).length > 0 
      ? JSON.stringify(filterObject) 
      : undefined
  };
  
  const url = buildUrl(API_ENDPOINTS.EBSA_OCATS, params);
  
  const yearList = years ? (Array.isArray(years) ? years : [years]) : null;
  const yearStr = yearList ? yearList.join(',') : 'all';
  console.log(`Fetching EBSA OCATS: states=${states.join(',')}, years=${yearStr}, limit=${limit}, offset=${offset}`);
  
  const response = await fetchWithRetry(url);
  
  return {
    records: response.data || response || [],
    metadata: {
      source: 'EBSA_OCATS',
      total: response.total || response.length || 0,
      states,
      years: yearList || 'all',
      limit,
      offset,
      fetched_at: new Date().toISOString()
    }
  };
}

/**
 * Normalize EBSA OCATS record to standard violation format
 * 
 * @param {Object} record - Raw EBSA OCATS record
 * @returns {Object} Normalized violation record
 */
function normalizeEBSARecord(record) {
  // Extract year from plan_yr_dte (format: YYYY-MM-DD)
  const planYear = record.plan_yr_dte 
    ? parseInt(record.plan_yr_dte.substring(0, 4), 10) 
    : null;
  
  return {
    // Required fields
    ein: record.plan_ein || record.plan_admin_ein,
    source_agency: 'EBSA',
    violation_type: mapEBSACaseType(record.case_type_code),
    violation_date: record.plan_yr_dte || null,
    
    // Year (extracted for easy filtering)
    plan_year: planYear,
    
    // Case identification
    case_number: record.ack_id || record.id || null,
    case_type: record.case_type_code,
    
    // Plan info
    plan_name: record.plan_name,
    plan_ein: record.plan_ein,
    
    // Company info (for matching)
    employer_name: record.plan_admin_name || record.plan_name,
    employer_ein: record.plan_admin_ein,
    
    // Location
    site_state: record.plan_state,
    
    // Penalties
    penalty_initial: parseFloat(record.civil_penalty_amt) || null,
    penalty_current: parseFloat(record.civil_penalty_amt) || null,
    
    // Status (EBSA cases are typically OPEN until resolved)
    status: record.case_status || 'OPEN',
    
    // Description
    violation_description: `${record.case_type_code}: ${record.plan_name}`,
    
    // Source tracking
    source_url: `https://data.dol.gov/ebsa/ocats?plan_ein=${record.plan_ein}`,
    source_record_id: record.id || record.ack_id,
    
    // Raw data for audit
    raw_data: record
  };
}

/**
 * Map EBSA case type codes to standard violation types
 */
function mapEBSACaseType(caseCode) {
  const caseMap = {
    'DEFICIENT': 'EBSA_DEFICIENT_FILER',
    'DEFICIENT_FILER': 'EBSA_DEFICIENT_FILER',
    'LATE': 'EBSA_LATE_FILER',
    'LATE_FILER': 'EBSA_LATE_FILER',
    'NON_FILER': 'EBSA_NON_FILER',
    'NON-FILER': 'EBSA_NON_FILER',
    'DELINQUENT': 'EBSA_DELINQUENT',
    'PENALTY': 'EBSA_PENALTY_ASSESSMENT'
  };
  
  return caseMap[caseCode?.toUpperCase()] || 'EBSA_OTHER';
}

// ═══════════════════════════════════════════════════════════════════════════
// OSHA (Occupational Safety and Health Administration)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Fetch OSHA inspections
 * 
 * @param {Object} filters - Query filters
 * @param {Array<string>} filters.states - State codes
 * @param {string} filters.startDate - Start date (YYYY-MM-DD)
 * @param {string} filters.endDate - End date (YYYY-MM-DD)
 * @param {number} filters.limit - Results per page
 * @param {number} filters.offset - Pagination offset
 * @returns {Promise<Object>} { records: Array, metadata: Object }
 */
async function fetchOSHAInspections(filters = {}) {
  validateApiKey();
  
  const {
    states = TARGET_STATES,
    startDate = null,
    endDate = null,
    limit = DEFAULT_PARAMS.limit,
    offset = DEFAULT_PARAMS.offset
  } = filters;
  
  const filterObject = {};
  
  if (states && states.length > 0) {
    filterObject.site_state = { '$in': states };
  }
  
  if (startDate) {
    filterObject.open_date = filterObject.open_date || {};
    filterObject.open_date['$gte'] = startDate;
  }
  
  if (endDate) {
    filterObject.open_date = filterObject.open_date || {};
    filterObject.open_date['$lte'] = endDate;
  }
  
  const params = {
    limit,
    offset,
    filter_object: Object.keys(filterObject).length > 0 
      ? JSON.stringify(filterObject) 
      : undefined
  };
  
  const url = buildUrl(API_ENDPOINTS.OSHA_INSPECTION, params);
  
  console.log(`Fetching OSHA Inspections: states=${states.join(',')}, limit=${limit}`);
  
  const response = await fetchWithRetry(url);
  
  return {
    records: response.data || response || [],
    metadata: {
      source: 'OSHA_INSPECTION',
      total: response.total || response.length || 0,
      limit,
      offset,
      fetched_at: new Date().toISOString()
    }
  };
}

/**
 * Fetch OSHA violations by inspection
 * 
 * @param {string} activityNr - OSHA Activity Number
 * @returns {Promise<Object>} { records: Array, metadata: Object }
 */
async function fetchOSHAViolations(activityNr) {
  validateApiKey();
  
  const filterObject = {
    activity_nr: activityNr
  };
  
  const params = {
    limit: 1000, // Get all violations for this inspection
    filter_object: JSON.stringify(filterObject)
  };
  
  const url = buildUrl(API_ENDPOINTS.OSHA_VIOLATION, params);
  
  const response = await fetchWithRetry(url);
  
  return {
    records: response.data || response || [],
    metadata: {
      source: 'OSHA_VIOLATION',
      activity_nr: activityNr,
      fetched_at: new Date().toISOString()
    }
  };
}

/**
 * Normalize OSHA inspection to standard violation format
 */
function normalizeOSHARecord(record) {
  return {
    ein: record.ein || null,
    source_agency: 'OSHA',
    violation_type: 'OSHA_INSPECTION',
    violation_date: record.open_date,
    
    case_number: record.activity_nr,
    
    employer_name: record.estab_name,
    
    site_name: record.estab_name,
    site_address: record.site_address,
    site_city: record.site_city,
    site_state: record.site_state,
    site_zip: record.site_zip,
    
    penalty_initial: parseFloat(record.total_penalty) || null,
    penalty_current: parseFloat(record.total_penalty) || null,
    
    status: record.case_status || 'OPEN',
    
    violation_description: record.insp_desc || `OSHA Inspection at ${record.estab_name}`,
    
    source_url: `https://enforcedata.dol.gov/views/inspection/${record.activity_nr}`,
    source_record_id: record.activity_nr,
    
    raw_data: record
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// PAGINATED FETCH (All Records)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Fetch all records with pagination
 * 
 * @param {Function} fetchFn - Fetch function to use (fetchEBSAOCATS, fetchOSHAInspections, etc.)
 * @param {Object} filters - Filters to pass to fetch function
 * @param {Object} options - Pagination options
 * @param {number} options.maxRecords - Maximum records to fetch (default: 10000)
 * @param {number} options.pageSize - Records per page (default: 100)
 * @param {Function} options.onProgress - Progress callback (current, total)
 * @returns {Promise<Object>} { records: Array, metadata: Object }
 */
async function fetchAllPaginated(fetchFn, filters = {}, options = {}) {
  const {
    maxRecords = 10000,
    pageSize = 100,
    onProgress = null
  } = options;
  
  const allRecords = [];
  let offset = 0;
  let hasMore = true;
  
  while (hasMore && allRecords.length < maxRecords) {
    const result = await fetchFn({
      ...filters,
      limit: pageSize,
      offset
    });
    
    allRecords.push(...result.records);
    
    if (onProgress) {
      onProgress(allRecords.length, result.metadata.total);
    }
    
    // Check if there are more records
    hasMore = result.records.length === pageSize && allRecords.length < result.metadata.total;
    offset += pageSize;
    
    // Rate limit between pages
    if (hasMore) {
      await sleep(200);
    }
  }
  
  return {
    records: allRecords,
    metadata: {
      total_fetched: allRecords.length,
      max_records: maxRecords,
      fetched_at: new Date().toISOString()
    }
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// HIGH-LEVEL DISCOVERY FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Discover EBSA violations (401k, health plans, ERISA)
 * 
 * This is the main entry point for EBSA violation discovery.
 * 
 * @param {Object} options - Discovery options
 * @param {Array<string>} options.states - Target states (default: Mid-Atlantic)
 * @param {number|Array<number>} options.years - Plan year(s) to filter
 * @param {string} options.caseType - Case type filter (DEFICIENT, LATE, NON_FILER)
 * @param {number} options.minPenalty - Minimum penalty amount
 * @param {number} options.maxRecords - Maximum records to fetch
 * @returns {Promise<Object>} Discovery result with normalized violations
 */
async function discoverEBSAViolations(options = {}) {
  const {
    states = TARGET_STATES,
    years = null,
    caseType = null,
    minPenalty = null,
    maxRecords = 5000
  } = options;
  
  const yearStr = years ? (Array.isArray(years) ? years.join(', ') : years) : 'all';
  console.log(`Starting EBSA violation discovery for states: ${states.join(', ')}, years: ${yearStr}`);
  
  const result = await fetchAllPaginated(
    fetchEBSAOCATS,
    { states, years, caseType, minPenalty },
    { 
      maxRecords,
      onProgress: (current, total) => {
        console.log(`EBSA progress: ${current}/${total} records`);
      }
    }
  );
  
  // Normalize all records
  const normalized = result.records.map(normalizeEBSARecord);
  
  return {
    violations: normalized,
    raw_records: result.records,
    metadata: {
      source: 'EBSA_OCATS',
      states,
      years: years || 'all',
      caseType: caseType || 'all',
      ...result.metadata
    }
  };
}

/**
 * Discover EBSA violations by state and year
 * 
 * Convenience function for the common use case of pulling
 * violations for specific states and years.
 * 
 * @param {string} state - Single state code (e.g., 'PA')
 * @param {number} year - Plan year (e.g., 2023)
 * @param {Object} options - Additional options
 * @returns {Promise<Object>} Discovery result
 * 
 * @example
 * // Get all PA violations from 2023
 * const result = await discoverEBSAByStateYear('PA', 2023);
 * 
 * // Get OH violations from 2023 with penalties over $1000
 * const result = await discoverEBSAByStateYear('OH', 2023, { minPenalty: 1000 });
 */
async function discoverEBSAByStateYear(state, year, options = {}) {
  const {
    caseType = null,
    minPenalty = null,
    maxRecords = 10000
  } = options;
  
  console.log(`\n═══════════════════════════════════════════════════════════════`);
  console.log(`EBSA Violations: ${state} / ${year}`);
  console.log(`═══════════════════════════════════════════════════════════════`);
  
  return discoverEBSAViolations({
    states: [state],
    years: year,
    caseType,
    minPenalty,
    maxRecords
  });
}

/**
 * Discover EBSA violations for multiple state+year combinations
 * 
 * @param {Array<{state: string, year: number}>} stateYearPairs - Array of state/year combinations
 * @param {Object} options - Additional options
 * @returns {Promise<Object>} Combined discovery result
 * 
 * @example
 * const result = await discoverEBSAMultiStateYear([
 *   { state: 'PA', year: 2023 },
 *   { state: 'PA', year: 2024 },
 *   { state: 'OH', year: 2023 },
 * ]);
 */
async function discoverEBSAMultiStateYear(stateYearPairs, options = {}) {
  const allViolations = [];
  const allRawRecords = [];
  const results = [];
  
  console.log(`\n═══════════════════════════════════════════════════════════════`);
  console.log(`EBSA Multi-State/Year Discovery`);
  console.log(`Combinations: ${stateYearPairs.length}`);
  console.log(`═══════════════════════════════════════════════════════════════`);
  
  for (const { state, year } of stateYearPairs) {
    console.log(`\n→ Processing: ${state} / ${year}`);
    
    const result = await discoverEBSAByStateYear(state, year, options);
    
    allViolations.push(...result.violations);
    allRawRecords.push(...result.raw_records);
    results.push({
      state,
      year,
      count: result.violations.length,
      metadata: result.metadata
    });
    
    // Rate limit between requests
    await sleep(500);
  }
  
  // Deduplicate by hash (in case of overlapping results)
  const seen = new Set();
  const uniqueViolations = allViolations.filter(v => {
    const key = `${v.ein}-${v.case_number}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  
  console.log(`\n═══════════════════════════════════════════════════════════════`);
  console.log(`Discovery Complete`);
  console.log(`  Total Raw: ${allViolations.length}`);
  console.log(`  Unique: ${uniqueViolations.length}`);
  console.log(`═══════════════════════════════════════════════════════════════\n`);
  
  return {
    violations: uniqueViolations,
    raw_records: allRawRecords,
    by_state_year: results,
    metadata: {
      source: 'EBSA_OCATS',
      combinations: stateYearPairs,
      total_fetched: allViolations.length,
      unique_count: uniqueViolations.length,
      fetched_at: new Date().toISOString()
    }
  };
}

/**
 * Discover OSHA violations
 * 
 * @param {Object} options - Discovery options
 * @param {Array<string>} options.states - Target states
 * @param {string} options.startDate - Start date (YYYY-MM-DD)
 * @param {number} options.maxRecords - Maximum records
 * @returns {Promise<Object>} Discovery result
 */
async function discoverOSHAViolations(options = {}) {
  const {
    states = TARGET_STATES,
    startDate = null,
    maxRecords = 5000
  } = options;
  
  console.log(`Starting OSHA violation discovery for states: ${states.join(', ')}`);
  
  const result = await fetchAllPaginated(
    fetchOSHAInspections,
    { states, startDate },
    { 
      maxRecords,
      onProgress: (current, total) => {
        console.log(`OSHA progress: ${current}/${total} records`);
      }
    }
  );
  
  // Normalize all records
  const normalized = result.records.map(normalizeOSHARecord);
  
  return {
    violations: normalized,
    raw_records: result.records,
    metadata: {
      source: 'OSHA_INSPECTION',
      states,
      ...result.metadata
    }
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// HEALTH CHECK
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Test API connectivity and authentication
 * 
 * @returns {Promise<Object>} Health check result
 */
async function healthCheck() {
  try {
    validateApiKey();
    
    // Try a minimal request
    const result = await fetchEBSAOCATS({ limit: 1, states: ['PA'] });
    
    return {
      status: 'OK',
      api_key_valid: true,
      test_record_count: result.records.length,
      checked_at: new Date().toISOString()
    };
    
  } catch (error) {
    return {
      status: 'ERROR',
      api_key_valid: false,
      error: error.message,
      checked_at: new Date().toISOString()
    };
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// MODULE EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

module.exports = {
  // Configuration
  API_ENDPOINTS,
  TARGET_STATES,
  
  // EBSA (Employee Benefits)
  fetchEBSAOCATS,
  normalizeEBSARecord,
  discoverEBSAViolations,
  discoverEBSAByStateYear,      // NEW: Single state + year
  discoverEBSAMultiStateYear,   // NEW: Multiple state/year combos
  
  // OSHA (Workplace Safety)
  fetchOSHAInspections,
  fetchOSHAViolations,
  normalizeOSHARecord,
  discoverOSHAViolations,
  
  // Utilities
  fetchAllPaginated,
  healthCheck,
  validateApiKey
};
