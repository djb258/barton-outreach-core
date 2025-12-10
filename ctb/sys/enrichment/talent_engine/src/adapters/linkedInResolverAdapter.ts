/**
 * LinkedIn Resolver Adapter
 * =========================
 * Generic adapter for LinkedIn URL resolution and profile lookup.
 * Can be wired to: Proxycurl, Apollo, RocketReach, etc.
 */

import {
  AdapterResponse,
  AdapterConfig,
  LinkedInProfileData,
  DEFAULT_ADAPTER_CONFIG,
} from "./types";

/**
 * LinkedIn resolver configuration.
 */
export interface LinkedInResolverConfig extends AdapterConfig {
  /** Include profile picture in results */
  include_picture: boolean;
  /** Include full profile details */
  include_details: boolean;
}

/**
 * Default LinkedIn resolver configuration.
 */
export const DEFAULT_LINKEDIN_RESOLVER_CONFIG: LinkedInResolverConfig = {
  ...DEFAULT_ADAPTER_CONFIG,
  include_picture: false,
  include_details: true,
};

/**
 * LinkedIn resolution input.
 */
export interface LinkedInResolutionInput {
  /** Person's first name */
  first_name: string;
  /** Person's last name */
  last_name: string;
  /** Company name (helps narrow down) */
  company_name?: string;
  /** Company domain (alternative identifier) */
  company_domain?: string;
  /** Title hint */
  title_hint?: string;
}

/**
 * Resolve LinkedIn URL from person + company info.
 *
 * TODO: Wire to real vendor API (Proxycurl, Apollo, RocketReach)
 *
 * @param input - Resolution input parameters
 * @param config - Adapter configuration
 * @returns Promise<AdapterResponse<LinkedInProfileData>>
 */
export async function linkedInResolverAdapter(
  input: LinkedInResolutionInput,
  config: LinkedInResolverConfig = DEFAULT_LINKEDIN_RESOLVER_CONFIG
): Promise<AdapterResponse<LinkedInProfileData>> {
  const startTime = Date.now();

  try {
    // TODO: Replace with real API call
    // Example vendors: Proxycurl Person Lookup, Apollo People Search

    if (config.mock_mode) {
      return getMockLinkedInResolution(input, startTime);
    }

    // Real implementation placeholder
    // const response = await realVendorApi.resolveLinkedIn({
    //   firstName: input.first_name,
    //   lastName: input.last_name,
    //   company: input.company_name,
    // });

    return {
      success: false,
      error: "Real API not configured. Set mock_mode=true for testing.",
      latency_ms: Date.now() - startTime,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error in LinkedIn resolution",
      latency_ms: Date.now() - startTime,
    };
  }
}

/**
 * Get LinkedIn profile data from URL.
 *
 * TODO: Wire to profile scraping API
 *
 * @param linkedinUrl - LinkedIn profile URL
 * @param config - Adapter configuration
 * @returns Promise<AdapterResponse<LinkedInProfileData>>
 */
export async function linkedInProfileAdapter(
  linkedinUrl: string,
  config: LinkedInResolverConfig = DEFAULT_LINKEDIN_RESOLVER_CONFIG
): Promise<AdapterResponse<LinkedInProfileData>> {
  const startTime = Date.now();

  try {
    if (config.mock_mode) {
      return getMockLinkedInProfile(linkedinUrl, startTime);
    }

    // TODO: Real implementation
    return {
      success: false,
      error: "Real API not configured",
      latency_ms: Date.now() - startTime,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error",
      latency_ms: Date.now() - startTime,
    };
  }
}

/**
 * Generate mock LinkedIn resolution result.
 */
function getMockLinkedInResolution(
  input: LinkedInResolutionInput,
  startTime: number
): AdapterResponse<LinkedInProfileData> {
  const { first_name, last_name, company_name, title_hint } = input;

  // Simulate ~80% success rate
  if (Math.random() < 0.2 && !company_name) {
    return {
      success: false,
      error: "Could not resolve LinkedIn URL without company context",
      source: "mock",
      latency_ms: Date.now() - startTime,
    };
  }

  // Generate mock LinkedIn URL
  const slug = `${first_name.toLowerCase()}-${last_name.toLowerCase()}-${Math.random()
    .toString(36)
    .substring(2, 8)}`;

  const mockProfile: LinkedInProfileData = {
    linkedin_url: `https://linkedin.com/in/${slug}`,
    full_name: `${first_name} ${last_name}`,
    headline: title_hint
      ? `${title_hint} at ${company_name || "Company"}`
      : `Professional at ${company_name || "Company"}`,
    title: title_hint || "Executive",
    company: company_name || "Unknown Company",
    location: "United States",
    public_accessible: Math.random() > 0.3, // 70% public
  };

  return {
    success: true,
    data: mockProfile,
    source: "mock",
    cost: 0.05, // Simulated cost
    latency_ms: Date.now() - startTime,
  };
}

/**
 * Generate mock LinkedIn profile data.
 */
function getMockLinkedInProfile(
  linkedinUrl: string,
  startTime: number
): AdapterResponse<LinkedInProfileData> {
  // Extract name from URL if possible
  const urlMatch = linkedinUrl.match(/linkedin\.com\/in\/([^\/\?]+)/);
  const slug = urlMatch ? urlMatch[1] : "unknown-user";
  const nameParts = slug.split("-").slice(0, 2);

  const mockProfile: LinkedInProfileData = {
    linkedin_url: linkedinUrl,
    full_name: nameParts.map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join(" "),
    headline: "Professional",
    title: "Executive",
    company: "Company",
    location: "United States",
    public_accessible: Math.random() > 0.3,
  };

  return {
    success: true,
    data: mockProfile,
    source: "mock",
    cost: 0.03,
    latency_ms: Date.now() - startTime,
  };
}

/**
 * Check if a LinkedIn profile is publicly accessible.
 *
 * TODO: Wire to profile accessibility checker
 *
 * @param linkedinUrl - LinkedIn profile URL
 * @param config - Adapter configuration
 * @returns Promise<AdapterResponse<{ public_accessible: boolean }>>
 */
export async function linkedInAccessibilityAdapter(
  linkedinUrl: string,
  config: AdapterConfig = DEFAULT_ADAPTER_CONFIG
): Promise<AdapterResponse<{ public_accessible: boolean; profile_exists: boolean }>> {
  const startTime = Date.now();

  try {
    if (config.mock_mode) {
      // Simulate accessibility check
      const isPublic = Math.random() > 0.3; // 70% public

      return {
        success: true,
        data: {
          public_accessible: isPublic,
          profile_exists: true,
        },
        source: "mock",
        latency_ms: Date.now() - startTime,
      };
    }

    return {
      success: false,
      error: "Real API not configured",
      latency_ms: Date.now() - startTime,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error",
      latency_ms: Date.now() - startTime,
    };
  }
}
