/**
 * Vendor Budget Configuration
 * ===========================
 * Defines cost guardrails and rate limits for external vendor APIs.
 *
 * These budgets protect against:
 * - Runaway API costs
 * - Rate limit violations
 * - Vendor overuse
 *
 * Load these rules into ThrottleManagerV2 at initialization.
 */

import { ThrottleRule, VendorId } from "../services/ThrottleManagerV2";

/**
 * Vendor budget rules for production use.
 */
export const VENDOR_BUDGETS: Record<string, ThrottleRule> = {
  // ScraperAPI - Web scraping service
  scraper_api: {
    max_cost_per_day: 5.0,
    max_calls_per_minute: 60,
    max_calls_per_hour: 1000,
    cooldown_ms: 500,
    exponential_backoff: true,
    max_backoff_multiplier: 4,
  },

  // Clay - Data enrichment platform
  clay: {
    max_cost_per_day: 10.0,
    max_calls_per_minute: 30,
    max_calls_per_hour: 500,
    cooldown_ms: 1000,
    exponential_backoff: true,
    max_backoff_multiplier: 8,
  },

  // LinkedIn Scraper - Profile data (VERY SENSITIVE)
  linkedin_scraper: {
    max_calls_per_minute: 8,
    max_calls_per_hour: 150,
    max_calls_per_day: 500,
    max_cost_per_day: 25.0,
    cooldown_ms: 2000,
    exponential_backoff: true,
    max_backoff_multiplier: 16,
  },

  // Email Verification - Deliverability checking
  email_verification: {
    max_cost_per_day: 3.0,
    max_calls_per_hour: 500,
    max_calls_per_day: 5000,
    cooldown_ms: 200,
    exponential_backoff: false,
  },

  // Proxycurl - LinkedIn enrichment
  proxycurl: {
    max_calls_per_minute: 30,
    max_calls_per_hour: 500,
    max_calls_per_day: 5000,
    max_cost_per_hour: 25.0,
    max_cost_per_day: 100.0,
    cooldown_ms: 2000,
    exponential_backoff: true,
    max_backoff_multiplier: 8,
  },

  // Hunter.io - Email finding
  hunter: {
    max_calls_per_minute: 60,
    max_calls_per_hour: 1000,
    max_calls_per_day: 10000,
    max_cost_per_hour: 10.0,
    max_cost_per_day: 50.0,
    cooldown_ms: 1000,
    exponential_backoff: true,
    max_backoff_multiplier: 4,
  },

  // VitaMail - Email verification
  vitamail: {
    max_calls_per_minute: 100,
    max_calls_per_hour: 2000,
    max_calls_per_day: 20000,
    max_cost_per_hour: 5.0,
    max_cost_per_day: 25.0,
    cooldown_ms: 500,
    exponential_backoff: false,
  },

  // Apollo - Fallback enrichment (EXPENSIVE)
  apollo: {
    max_calls_per_minute: 20,
    max_calls_per_hour: 200,
    max_calls_per_day: 1000,
    max_cost_per_hour: 15.0,
    max_cost_per_day: 75.0,
    cooldown_ms: 3000,
    exponential_backoff: true,
    max_backoff_multiplier: 16,
  },

  // Firecrawl - Web scraping
  firecrawl: {
    max_calls_per_minute: 50,
    max_calls_per_hour: 500,
    max_calls_per_day: 5000,
    max_cost_per_hour: 10.0,
    max_cost_per_day: 50.0,
    cooldown_ms: 1000,
    exponential_backoff: true,
    max_backoff_multiplier: 4,
  },

  // Apify - Actor execution (EXPENSIVE PER CALL)
  apify: {
    max_calls_per_minute: 10,
    max_calls_per_hour: 100,
    max_calls_per_day: 500,
    max_cost_per_hour: 20.0,
    max_cost_per_day: 100.0,
    cooldown_ms: 5000,
    exponential_backoff: true,
    max_backoff_multiplier: 8,
  },

  // OpenAI - LLM calls
  openai: {
    max_calls_per_minute: 100,
    max_calls_per_hour: 3000,
    max_calls_per_day: 50000,
    max_cost_per_hour: 50.0,
    max_cost_per_day: 200.0,
    cooldown_ms: 1000,
    exponential_backoff: true,
    max_backoff_multiplier: 4,
  },

  // Anthropic - LLM calls
  anthropic: {
    max_calls_per_minute: 50,
    max_calls_per_hour: 1000,
    max_calls_per_day: 10000,
    max_cost_per_hour: 100.0,
    max_cost_per_day: 500.0,
    cooldown_ms: 2000,
    exponential_backoff: true,
    max_backoff_multiplier: 4,
  },

  // DOL API - Department of Labor (FREE but rate limited)
  dol_api: {
    max_calls_per_minute: 120,
    max_calls_per_hour: 5000,
    max_calls_per_day: 50000,
    cooldown_ms: 500,
    exponential_backoff: false,
  },

  // LinkedIn direct (MOST SENSITIVE)
  linkedin: {
    max_calls_per_minute: 5,
    max_calls_per_hour: 50,
    max_calls_per_day: 200,
    max_cost_per_hour: 5.0,
    max_cost_per_day: 25.0,
    cooldown_ms: 10000,
    exponential_backoff: true,
    max_backoff_multiplier: 32,
  },

  // Mock vendor (for testing)
  mock: {
    max_calls_per_minute: 10000,
    max_calls_per_hour: 100000,
    max_calls_per_day: 1000000,
    cooldown_ms: 0,
    exponential_backoff: false,
  },

  // Internal operations (no limits)
  internal: {
    max_calls_per_minute: 10000,
    max_calls_per_hour: 100000,
    max_calls_per_day: 1000000,
    cooldown_ms: 0,
    exponential_backoff: false,
  },
};

/**
 * Agent to vendor mapping.
 * Maps each agent to its primary vendor for throttling.
 */
export const AGENT_VENDOR_MAP: Record<string, VendorId | string> = {
  // Company Hub agents
  CompanyFuzzyMatchAgent: "internal",
  PatternAgent: "hunter",
  EmailGeneratorAgent: "hunter",
  EmailVerificationAgent: "vitamail",

  // People Node agents
  PeopleFuzzyMatchAgent: "internal",
  TitleCompanyAgent: "proxycurl",
  LinkedInFinderAgent: "proxycurl",
  PublicScannerAgent: "proxycurl",

  // DOL Node agents
  DOLSyncAgent: "dol_api",

  // BIT Node agents
  BITScoreAgent: "internal",
  ChurnDetectorAgent: "internal",
  MovementHashAgent: "internal",

  // Slot agents
  MissingSlotAgent: "apollo",

  // Hash agents
  HashAgent: "internal",
};

/**
 * Agent cost estimates (per call).
 * Used for budget forecasting and throttle calculations.
 */
export const AGENT_COST_ESTIMATES: Record<string, number> = {
  // Company Hub agents
  CompanyFuzzyMatchAgent: 0.0, // Free (internal)
  PatternAgent: 0.005, // Hunter domain search
  EmailGeneratorAgent: 0.002, // Email generation
  EmailVerificationAgent: 0.001, // VitaMail verification

  // People Node agents
  PeopleFuzzyMatchAgent: 0.0, // Free (internal)
  TitleCompanyAgent: 0.01, // Proxycurl profile
  LinkedInFinderAgent: 0.01, // Proxycurl search
  PublicScannerAgent: 0.005, // Proxycurl light

  // DOL Node agents
  DOLSyncAgent: 0.0, // Free (government API)

  // BIT Node agents
  BITScoreAgent: 0.0, // Free (internal)
  ChurnDetectorAgent: 0.0, // Free (internal)
  MovementHashAgent: 0.0, // Free (internal)

  // Slot agents
  MissingSlotAgent: 0.02, // Apollo search (expensive)

  // Hash agents
  HashAgent: 0.0, // Free (internal)
};

/**
 * Get vendor for an agent.
 */
export function getVendorForAgent(agentName: string): VendorId | string {
  return AGENT_VENDOR_MAP[agentName] || "internal";
}

/**
 * Get cost estimate for an agent.
 */
export function getCostForAgent(agentName: string): number {
  return AGENT_COST_ESTIMATES[agentName] || 0.0;
}

/**
 * Global daily budget cap (all vendors combined).
 */
export const GLOBAL_DAILY_BUDGET = 500.0;

/**
 * Emergency stop threshold (% of daily budget).
 * When reached, all non-essential agents stop.
 */
export const EMERGENCY_STOP_THRESHOLD = 0.9; // 90%

/**
 * Cost categories for reporting.
 */
export const COST_CATEGORIES = {
  enrichment: ["proxycurl", "hunter", "apollo", "vitamail"],
  scraping: ["firecrawl", "apify", "scraper_api", "linkedin_scraper"],
  llm: ["openai", "anthropic"],
  free: ["dol_api", "internal", "mock"],
};

/**
 * Get total daily budget for a category.
 */
export function getCategoryBudget(category: keyof typeof COST_CATEGORIES): number {
  const vendors = COST_CATEGORIES[category];
  return vendors.reduce((sum, vendor) => {
    const budget = VENDOR_BUDGETS[vendor]?.max_cost_per_day || 0;
    return sum + budget;
  }, 0);
}
