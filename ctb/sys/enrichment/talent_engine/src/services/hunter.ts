/**
 * Hunter.io Service
 * =================
 * API wrapper for Hunter.io email finding and pattern inference.
 *
 * Endpoints:
 * - GET https://api.hunter.io/v2/domain-search
 * - GET https://api.hunter.io/v2/email-finder
 * - GET https://api.hunter.io/v2/email-verifier
 *
 * Cost: Varies by endpoint, patterns often free with domain search
 */

import { ServiceResponse, EmailPatternData, ServiceConfig } from "./types";

/**
 * Hunter domain search response.
 */
export interface HunterDomainResponse {
  domain: string;
  organization: string;
  pattern: string | null;
  emails: HunterEmail[];
}

export interface HunterEmail {
  value: string;
  type: "personal" | "generic";
  confidence: number;
  first_name: string | null;
  last_name: string | null;
  position: string | null;
}

/**
 * Hunter email finder response.
 */
export interface HunterEmailFinderResponse {
  email: string;
  score: number;
  domain: string;
  first_name: string;
  last_name: string;
  position: string | null;
}

/**
 * Hunter.io service wrapper.
 * Never throws raw errors - always returns ServiceResponse.
 */
export class HunterService {
  private apiKey: string;
  private baseUrl: string;
  private timeout: number;

  constructor(config: ServiceConfig | string) {
    if (typeof config === "string") {
      this.apiKey = config;
      this.baseUrl = "https://api.hunter.io/v2";
      this.timeout = 30000;
    } else {
      this.apiKey = config.apiKey;
      this.baseUrl = config.baseUrl ?? "https://api.hunter.io/v2";
      this.timeout = config.timeout ?? 30000;
    }
  }

  /**
   * Get email pattern for a domain.
   * Endpoint: GET /domain-search
   *
   * @param domain - Company domain (e.g., "acme.com")
   * @returns ServiceResponse with email pattern
   */
  async getEmailPattern(domain: string): Promise<ServiceResponse<EmailPatternData>> {
    try {
      // SCAFFOLDING: Real implementation would call:
      // GET https://api.hunter.io/v2/domain-search?domain={domain}&api_key={apiKey}

      if (!domain) {
        return {
          success: false,
          error: "Domain is required",
          retryable: false,
        };
      }

      // Clean domain
      const cleanDomain = domain.replace(/^(https?:\/\/)?(www\.)?/, "").split("/")[0];

      const response = await this.makeRequest<{ data: HunterDomainResponse }>(
        "GET",
        `/domain-search?domain=${encodeURIComponent(cleanDomain)}`
      );

      if (!response.success || !response.data?.data) {
        return {
          success: false,
          error: response.error ?? "Failed to get email pattern",
          statusCode: response.statusCode,
          retryable: response.retryable ?? true,
        };
      }

      const data = response.data.data;

      // Pattern might be null if Hunter couldn't determine it
      if (!data.pattern) {
        return {
          success: false,
          error: "No email pattern found for domain",
          retryable: false,
        };
      }

      return {
        success: true,
        data: {
          pattern: data.pattern,
          domain: data.domain,
          confidence: 80, // Hunter patterns are generally reliable
        },
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
   * Find email for a specific person at a domain.
   * Endpoint: GET /email-finder
   *
   * @param domain - Company domain
   * @param firstName - Person's first name
   * @param lastName - Person's last name
   * @returns ServiceResponse with found email
   */
  async findEmail(
    domain: string,
    firstName: string,
    lastName: string
  ): Promise<ServiceResponse<{ email: string; confidence: number }>> {
    try {
      // SCAFFOLDING: Real implementation would call:
      // GET https://api.hunter.io/v2/email-finder
      // ?domain={domain}&first_name={firstName}&last_name={lastName}&api_key={apiKey}

      if (!domain || !firstName || !lastName) {
        return {
          success: false,
          error: "Domain, first name, and last name are required",
          retryable: false,
        };
      }

      const cleanDomain = domain.replace(/^(https?:\/\/)?(www\.)?/, "").split("/")[0];

      const params = new URLSearchParams({
        domain: cleanDomain,
        first_name: firstName,
        last_name: lastName,
      });

      const response = await this.makeRequest<{ data: HunterEmailFinderResponse }>(
        "GET",
        `/email-finder?${params.toString()}`
      );

      if (!response.success || !response.data?.data?.email) {
        return {
          success: false,
          error: response.error ?? "Could not find email",
          statusCode: response.statusCode,
          retryable: response.retryable ?? true,
        };
      }

      const data = response.data.data;

      return {
        success: true,
        data: {
          email: data.email,
          confidence: data.score,
        },
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
   * Generate email using pattern and name.
   * This is a local operation using the pattern format.
   *
   * Common patterns:
   * - {first}.{last}@domain.com
   * - {first}{last}@domain.com
   * - {f}{last}@domain.com
   * - {first}@domain.com
   *
   * @param pattern - Email pattern (e.g., "{first}.{last}")
   * @param domain - Company domain
   * @param firstName - Person's first name
   * @param lastName - Person's last name
   * @returns Generated email address
   */
  generateEmailFromPattern(
    pattern: string,
    domain: string,
    firstName: string,
    lastName: string
  ): ServiceResponse<{ email: string }> {
    try {
      if (!pattern || !domain || !firstName || !lastName) {
        return {
          success: false,
          error: "Pattern, domain, first name, and last name are required",
          retryable: false,
        };
      }

      const cleanFirst = firstName.toLowerCase().trim();
      const cleanLast = lastName.toLowerCase().trim();
      const cleanDomain = domain.replace(/^(https?:\/\/)?(www\.)?/, "").split("/")[0];

      // Replace pattern placeholders
      let email = pattern
        .replace(/{first}/g, cleanFirst)
        .replace(/{last}/g, cleanLast)
        .replace(/{f}/g, cleanFirst.charAt(0))
        .replace(/{l}/g, cleanLast.charAt(0))
        .replace(/{fi}/g, cleanFirst.charAt(0))
        .replace(/{li}/g, cleanLast.charAt(0));

      // Ensure domain is appended
      if (!email.includes("@")) {
        email = `${email}@${cleanDomain}`;
      }

      return {
        success: true,
        data: { email },
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error occurred",
        retryable: false,
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
    // Real implementation would include api_key in query params:
    //
    // const separator = endpoint.includes("?") ? "&" : "?";
    // const fullUrl = `${this.baseUrl}${endpoint}${separator}api_key=${this.apiKey}`;
    //
    // const response = await fetch(fullUrl, {
    //   method,
    //   headers: { "Content-Type": "application/json" },
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

    return {
      success: false,
      error: "SCAFFOLDING: API not implemented",
      retryable: false,
    };
  }
}

/**
 * Create a Hunter service instance.
 */
export function createHunterService(apiKey: string): HunterService {
  return new HunterService(apiKey);
}
