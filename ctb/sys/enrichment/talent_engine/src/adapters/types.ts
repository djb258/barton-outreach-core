/**
 * Adapter Types
 * =============
 * Common types used across all tool adapters.
 * These provide vendor-agnostic interfaces for enrichment operations.
 */

/**
 * Generic adapter response wrapper.
 */
export interface AdapterResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  source?: string;
  cached?: boolean;
  cost?: number;
  latency_ms?: number;
}

/**
 * Company search result.
 */
export interface CompanySearchResult {
  company_name: string;
  domain?: string;
  industry?: string;
  employee_count?: number;
  linkedin_url?: string;
  confidence: number;
}

/**
 * Person search result.
 */
export interface PersonSearchResult {
  full_name: string;
  title?: string;
  company?: string;
  linkedin_url?: string;
  email?: string;
  confidence: number;
}

/**
 * LinkedIn profile data.
 */
export interface LinkedInProfileData {
  linkedin_url: string;
  full_name?: string;
  headline?: string;
  title?: string;
  company?: string;
  location?: string;
  public_accessible?: boolean;
  profile_picture_url?: string;
}

/**
 * Email pattern data.
 */
export interface EmailPatternData {
  domain: string;
  pattern: string;
  confidence: number;
  examples?: string[];
}

/**
 * Email verification result.
 */
export interface EmailVerificationResult {
  email: string;
  status: "valid" | "invalid" | "unknown" | "catch_all" | "disposable";
  deliverable: boolean;
  reason?: string;
}

/**
 * Person employment lookup result.
 */
export interface PersonEmploymentData {
  full_name: string;
  current_title?: string;
  current_company?: string;
  previous_titles?: string[];
  previous_companies?: string[];
  linkedin_url?: string;
  email?: string;
}

/**
 * Slot discovery result (finding people in roles).
 */
export interface SlotDiscoveryResult {
  slot_type: string;
  person_name?: string;
  title?: string;
  linkedin_url?: string;
  email?: string;
  confidence: number;
}

/**
 * Profile accessibility result.
 */
export interface ProfileAccessibilityResult {
  linkedin_url: string;
  public_accessible: boolean;
  requires_login: boolean;
  profile_exists: boolean;
}

/**
 * Adapter configuration options.
 */
export interface AdapterConfig {
  /** Enable mock mode (no real API calls) */
  mock_mode: boolean;
  /** Timeout in milliseconds */
  timeout_ms: number;
  /** Number of retries */
  max_retries: number;
  /** Delay between retries */
  retry_delay_ms: number;
}

/**
 * Default adapter configuration.
 */
export const DEFAULT_ADAPTER_CONFIG: AdapterConfig = {
  mock_mode: true,
  timeout_ms: 30000,
  max_retries: 3,
  retry_delay_ms: 1000,
};
