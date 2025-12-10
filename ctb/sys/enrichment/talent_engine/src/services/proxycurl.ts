/**
 * Proxycurl Service
 * =================
 * API wrapper for Proxycurl LinkedIn enrichment.
 *
 * Endpoints:
 * - GET https://nubela.co/proxycurl/api/v2/linkedin
 * - GET https://nubela.co/proxycurl/api/linkedin/profile/resolve
 *
 * Cost: ~$0.01 per call
 */

import { ServiceResponse, ProfileData, ServiceConfig } from "./types";

/**
 * Proxycurl-specific profile response.
 */
export interface ProxycurlProfile {
  linkedin_url: string;
  full_name: string;
  first_name: string;
  last_name: string;
  headline: string;
  occupation: string;
  summary: string;
  country: string;
  city: string;
  experiences: ProxycurlExperience[];
  public_identifier: string;
}

export interface ProxycurlExperience {
  title: string;
  company: string;
  company_linkedin_profile_url: string;
  starts_at: { day: number; month: number; year: number } | null;
  ends_at: { day: number; month: number; year: number } | null;
}

/**
 * Proxycurl service wrapper.
 * Never throws raw errors - always returns ServiceResponse.
 */
export class ProxycurlService {
  private apiKey: string;
  private baseUrl: string;
  private timeout: number;

  constructor(config: ServiceConfig | string) {
    if (typeof config === "string") {
      this.apiKey = config;
      this.baseUrl = "https://nubela.co/proxycurl/api";
      this.timeout = 30000;
    } else {
      this.apiKey = config.apiKey;
      this.baseUrl = config.baseUrl ?? "https://nubela.co/proxycurl/api";
      this.timeout = config.timeout ?? 30000;
    }
  }

  /**
   * Get LinkedIn profile by URL.
   * Endpoint: GET /v2/linkedin
   *
   * @param linkedinUrl - Full LinkedIn profile URL
   * @returns ServiceResponse with profile data
   */
  async getLinkedInProfile(linkedinUrl: string): Promise<ServiceResponse<ProfileData>> {
    try {
      // SCAFFOLDING: Real implementation would call:
      // GET https://nubela.co/proxycurl/api/v2/linkedin?url={linkedinUrl}
      // Headers: Authorization: Bearer {apiKey}

      // Validate input
      if (!linkedinUrl || !linkedinUrl.includes("linkedin.com")) {
        return {
          success: false,
          error: "Invalid LinkedIn URL provided",
          retryable: false,
        };
      }

      // Placeholder for actual API call
      const response = await this.makeRequest<ProxycurlProfile>(
        "GET",
        `/v2/linkedin?url=${encodeURIComponent(linkedinUrl)}`
      );

      if (!response.success || !response.data) {
        return {
          success: false,
          error: response.error ?? "Failed to fetch LinkedIn profile",
          statusCode: response.statusCode,
          retryable: response.retryable ?? true,
        };
      }

      // Transform to standardized format
      const profile = response.data;
      const currentJob = profile.experiences?.[0];

      return {
        success: true,
        data: {
          linkedin_url: profile.linkedin_url,
          full_name: profile.full_name,
          first_name: profile.first_name,
          last_name: profile.last_name,
          title: currentJob?.title ?? profile.headline,
          company: currentJob?.company ?? undefined,
          public_accessible: true, // If we got data, it's public
        },
        statusCode: 200,
      };
    } catch (error) {
      // Never throw - always return ServiceResponse
      return {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error occurred",
        retryable: true,
      };
    }
  }

  /**
   * Resolve LinkedIn profile URL from name and company.
   * Endpoint: GET /linkedin/profile/resolve
   *
   * @param firstName - Person's first name
   * @param lastName - Person's last name
   * @param companyName - Company name for disambiguation
   * @returns ServiceResponse with resolved LinkedIn URL
   */
  async resolveLinkedInUrl(
    firstName: string,
    lastName: string,
    companyName?: string
  ): Promise<ServiceResponse<{ linkedin_url: string }>> {
    try {
      // SCAFFOLDING: Real implementation would call:
      // GET https://nubela.co/proxycurl/api/linkedin/profile/resolve
      // ?first_name={firstName}&last_name={lastName}&company_domain={domain}

      if (!firstName || !lastName) {
        return {
          success: false,
          error: "First name and last name are required",
          retryable: false,
        };
      }

      const params = new URLSearchParams({
        first_name: firstName,
        last_name: lastName,
      });

      if (companyName) {
        params.set("company_name", companyName);
      }

      const response = await this.makeRequest<{ url: string }>(
        "GET",
        `/linkedin/profile/resolve?${params.toString()}`
      );

      if (!response.success || !response.data?.url) {
        return {
          success: false,
          error: response.error ?? "Could not resolve LinkedIn URL",
          statusCode: response.statusCode,
          retryable: response.retryable ?? true,
        };
      }

      return {
        success: true,
        data: { linkedin_url: response.data.url },
        statusCode: 200,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error occurred",
        retryable: true,
      };
    }
  }

  /**
   * Check if a LinkedIn profile is publicly accessible.
   * Uses a lightweight endpoint to verify accessibility.
   *
   * @param linkedinUrl - LinkedIn profile URL to check
   * @returns ServiceResponse with accessibility status
   */
  async checkPublicAccessibility(
    linkedinUrl: string
  ): Promise<ServiceResponse<{ public_accessible: boolean }>> {
    try {
      if (!linkedinUrl) {
        return {
          success: false,
          error: "LinkedIn URL is required",
          retryable: false,
        };
      }

      // Use the profile endpoint but with minimal fields
      const response = await this.getLinkedInProfile(linkedinUrl);

      if (response.success && response.data) {
        return {
          success: true,
          data: { public_accessible: true },
          statusCode: 200,
        };
      }

      // If we get a 404 or similar, profile is private/not found
      if (response.statusCode === 404) {
        return {
          success: true,
          data: { public_accessible: false },
          statusCode: 200,
        };
      }

      return {
        success: false,
        error: response.error ?? "Could not determine accessibility",
        retryable: response.retryable ?? true,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error occurred",
        retryable: true,
      };
    }
  }

  /**
   * Internal method to make API requests.
   * SCAFFOLDING: Would use fetch/axios in real implementation.
   */
  private async makeRequest<T>(
    method: "GET" | "POST",
    endpoint: string,
    body?: unknown
  ): Promise<ServiceResponse<T>> {
    // SCAFFOLDING ONLY - No actual API calls
    // Real implementation would be:
    //
    // const response = await fetch(`${this.baseUrl}${endpoint}`, {
    //   method,
    //   headers: {
    //     "Authorization": `Bearer ${this.apiKey}`,
    //     "Content-Type": "application/json",
    //   },
    //   body: body ? JSON.stringify(body) : undefined,
    //   signal: AbortSignal.timeout(this.timeout),
    // });
    //
    // if (!response.ok) {
    //   return {
    //     success: false,
    //     error: `HTTP ${response.status}: ${response.statusText}`,
    //     statusCode: response.status,
    //     retryable: response.status >= 500 || response.status === 429,
    //   };
    // }
    //
    // return {
    //   success: true,
    //   data: await response.json(),
    //   statusCode: response.status,
    // };

    // Return mock failure for scaffolding
    return {
      success: false,
      error: "SCAFFOLDING: API not implemented",
      retryable: false,
    };
  }
}

/**
 * Create a Proxycurl service instance.
 */
export function createProxycurlService(apiKey: string): ProxycurlService {
  return new ProxycurlService(apiKey);
}
