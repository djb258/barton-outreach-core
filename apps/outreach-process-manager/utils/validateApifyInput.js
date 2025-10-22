/**
 * Apify Input Validation Utility
 *
 * Sanitizes and throttles Apify actor inputs before sending to Composio MCP.
 * Enforces per-run limits to prevent budget overruns and API abuse.
 *
 * Purpose:
 * - Prevent excessive API costs
 * - Enforce domain/lead limits
 * - Calculate estimated costs
 * - Sanitize timeout values
 * - Provide safety guardrails
 *
 * Integration:
 * - Call before posting to Composio MCP
 * - Throws errors if limits exceeded
 * - Returns sanitized input with estimated_cost
 *
 * @module validateApifyInput
 */

/**
 * Validates and sanitizes Apify actor input parameters
 *
 * @param {Object} input - Apify actor input object
 * @param {string} input.actorId - Apify actor ID (e.g., "code_crafter~leads-finder")
 * @param {Object} input.runInput - Actor-specific run parameters
 * @param {string[]} [input.runInput.company_domain] - Array of company domains
 * @param {number} [input.runInput.max_leads] - Maximum leads to fetch
 * @param {number} [input.runInput.timeout] - Timeout in seconds
 *
 * @returns {Object} Sanitized input with estimated_cost field added
 *
 * @throws {Error} If domain count exceeds MAX_DOMAINS
 * @throws {Error} If estimated cost exceeds MAX_EST_COST
 *
 * @example
 * const input = {
 *   actorId: "code_crafter~leads-finder",
 *   runInput: {
 *     company_domain: ["advantage.tech", "valleyhealth.org"],
 *     max_leads: 100,
 *     timeout: 180
 *   }
 * };
 *
 * const sanitized = validateApifyInput(input);
 * // Returns: { ...input, estimated_cost: 0.22 }
 */
export function validateApifyInput(input) {
  // Per-run limits for cost governance and safety
  const limits = {
    MAX_DOMAINS: 50,        // Maximum company domains per run
    MAX_LEADS: 500,         // Maximum leads to fetch per run
    MAX_TIMEOUT: 300,       // Maximum timeout (5 minutes)
    MAX_EST_COST: 1.50      // Maximum estimated cost per run ($1.50)
  };

  // Validate domain count
  const domainCount = input.runInput.company_domain?.length || 0;
  if (domainCount > limits.MAX_DOMAINS) {
    throw new Error(
      `Too many domains (${domainCount}) – max ${limits.MAX_DOMAINS}. ` +
      `Split into multiple runs to stay within limits.`
    );
  }

  // Sanitize max_leads (cap at limit, don't throw)
  if (input.runInput.max_leads > limits.MAX_LEADS) {
    console.warn(
      `⚠️  max_leads (${input.runInput.max_leads}) exceeds limit. ` +
      `Capping at ${limits.MAX_LEADS}.`
    );
    input.runInput.max_leads = limits.MAX_LEADS;
  }

  // Sanitize timeout (cap at limit, don't throw)
  if (input.runInput.timeout > limits.MAX_TIMEOUT) {
    console.warn(
      `⚠️  timeout (${input.runInput.timeout}s) exceeds limit. ` +
      `Capping at ${limits.MAX_TIMEOUT}s.`
    );
    input.runInput.timeout = limits.MAX_TIMEOUT;
  }

  // Calculate estimated cost
  // Formula: (leads × $0.002 per lead) + $0.02 base cost
  // Example: 100 leads = (100 × 0.002) + 0.02 = $0.22
  const maxLeads = input.runInput.max_leads || 0;
  const estCost = (maxLeads * 0.002) + 0.02;

  // Validate estimated cost
  if (estCost > limits.MAX_EST_COST) {
    throw new Error(
      `Estimated cost $${estCost.toFixed(2)} exceeds limit $${limits.MAX_EST_COST}. ` +
      `Reduce max_leads or split into multiple runs.`
    );
  }

  // Return sanitized input with estimated_cost
  return {
    ...input,
    estimated_cost: parseFloat(estCost.toFixed(2))
  };
}

/**
 * Validates LinkedIn profile scraper input
 *
 * @param {Object} input - LinkedIn scraper input
 * @param {string[]} input.runInput.linkedinUrls - Array of LinkedIn profile URLs
 * @param {number} [input.runInput.maxProfiles] - Maximum profiles to scrape
 *
 * @returns {Object} Sanitized input with estimated_cost
 *
 * @example
 * const input = {
 *   actorId: "apify~linkedin-profile-scraper",
 *   runInput: {
 *     linkedinUrls: ["https://linkedin.com/in/johndoe", ...],
 *     maxProfiles: 2000
 *   }
 * };
 *
 * const sanitized = validateLinkedInScraperInput(input);
 */
export function validateLinkedInScraperInput(input) {
  const limits = {
    MAX_PROFILES: 2000,     // Maximum profiles per run
    MAX_TIMEOUT: 600,       // Maximum timeout (10 minutes)
    MAX_EST_COST: 5.00      // Maximum estimated cost per run ($5.00)
  };

  // Validate profile count
  const profileCount = input.runInput.linkedinUrls?.length || 0;
  if (profileCount > limits.MAX_PROFILES) {
    throw new Error(
      `Too many LinkedIn URLs (${profileCount}) – max ${limits.MAX_PROFILES}. ` +
      `Split into multiple runs to stay within limits.`
    );
  }

  // Sanitize maxProfiles
  if (input.runInput.maxProfiles > limits.MAX_PROFILES) {
    console.warn(
      `⚠️  maxProfiles (${input.runInput.maxProfiles}) exceeds limit. ` +
      `Capping at ${limits.MAX_PROFILES}.`
    );
    input.runInput.maxProfiles = limits.MAX_PROFILES;
  }

  // Sanitize timeout
  if (input.runInput.timeout > limits.MAX_TIMEOUT) {
    console.warn(
      `⚠️  timeout (${input.runInput.timeout}s) exceeds limit. ` +
      `Capping at ${limits.MAX_TIMEOUT}s.`
    );
    input.runInput.timeout = limits.MAX_TIMEOUT;
  }

  // Calculate estimated cost
  // Formula: (profiles × $0.0015 per profile) + $0.05 base cost
  const maxProfiles = input.runInput.maxProfiles || profileCount;
  const estCost = (maxProfiles * 0.0015) + 0.05;

  // Validate estimated cost
  if (estCost > limits.MAX_EST_COST) {
    throw new Error(
      `Estimated cost $${estCost.toFixed(2)} exceeds limit $${limits.MAX_EST_COST}. ` +
      `Reduce profile count or split into multiple runs.`
    );
  }

  return {
    ...input,
    estimated_cost: parseFloat(estCost.toFixed(2))
  };
}

/**
 * Gets validation limits for display or configuration
 *
 * @returns {Object} Current validation limits
 *
 * @example
 * const limits = getValidationLimits();
 * console.log(`Max domains per run: ${limits.leads_finder.MAX_DOMAINS}`);
 */
export function getValidationLimits() {
  return {
    leads_finder: {
      MAX_DOMAINS: 50,
      MAX_LEADS: 500,
      MAX_TIMEOUT: 300,
      MAX_EST_COST: 1.50,
      COST_PER_LEAD: 0.002,
      BASE_COST: 0.02
    },
    linkedin_scraper: {
      MAX_PROFILES: 2000,
      MAX_TIMEOUT: 600,
      MAX_EST_COST: 5.00,
      COST_PER_PROFILE: 0.0015,
      BASE_COST: 0.05
    }
  };
}

/**
 * Estimates cost for a given input without validation
 *
 * @param {string} actorType - Actor type ("leads_finder" or "linkedin_scraper")
 * @param {number} itemCount - Number of items (leads or profiles)
 *
 * @returns {number} Estimated cost in USD
 *
 * @example
 * const cost = estimateCost("leads_finder", 100);
 * console.log(`Estimated cost: $${cost}`); // "$0.22"
 */
export function estimateCost(actorType, itemCount) {
  const limits = getValidationLimits();

  if (actorType === 'leads_finder') {
    return parseFloat(
      ((itemCount * limits.leads_finder.COST_PER_LEAD) + limits.leads_finder.BASE_COST).toFixed(2)
    );
  } else if (actorType === 'linkedin_scraper') {
    return parseFloat(
      ((itemCount * limits.linkedin_scraper.COST_PER_PROFILE) + limits.linkedin_scraper.BASE_COST).toFixed(2)
    );
  }

  throw new Error(`Unknown actor type: ${actorType}`);
}

/**
 * Calculates batch size for splitting large runs
 *
 * @param {number} totalItems - Total items to process
 * @param {number} maxPerRun - Maximum items per run
 *
 * @returns {Object} Batch information
 * @returns {number} returns.batchCount - Number of batches needed
 * @returns {number} returns.itemsPerBatch - Items in each batch
 * @returns {number} returns.lastBatchItems - Items in final batch
 *
 * @example
 * const batches = calculateBatchSize(1200, 500);
 * // Returns: { batchCount: 3, itemsPerBatch: 500, lastBatchItems: 200 }
 */
export function calculateBatchSize(totalItems, maxPerRun) {
  const batchCount = Math.ceil(totalItems / maxPerRun);
  const itemsPerBatch = maxPerRun;
  const lastBatchItems = totalItems % maxPerRun || maxPerRun;

  return {
    batchCount,
    itemsPerBatch,
    lastBatchItems,
    totalEstimatedCost: estimateCost('leads_finder', totalItems)
  };
}

// Export all validation functions
export default {
  validateApifyInput,
  validateLinkedInScraperInput,
  getValidationLimits,
  estimateCost,
  calculateBatchSize
};
