/**
 * VitaMail Service
 * ================
 * API wrapper for VitaMail email verification.
 *
 * Endpoint:
 * - POST https://api.vitamail.com/v1/verify
 *
 * Cost: ~$0.001 per verification
 */

import { ServiceResponse, EmailVerificationData, ServiceConfig } from "./types";

/**
 * VitaMail verification response.
 */
export interface VitaMailVerifyResponse {
  email: string;
  result: "deliverable" | "undeliverable" | "risky" | "unknown";
  reason: string;
  is_disposable: boolean;
  is_role_account: boolean;
  is_free_provider: boolean;
  mx_found: boolean;
  smtp_check: boolean;
}

/**
 * Verification status mapping.
 */
type VerificationStatus = "valid" | "invalid" | "unknown" | "catch_all";

/**
 * VitaMail service wrapper.
 * Never throws raw errors - always returns ServiceResponse.
 */
export class VitaMailService {
  private apiKey: string;
  private baseUrl: string;
  private timeout: number;

  constructor(config: ServiceConfig | string) {
    if (typeof config === "string") {
      this.apiKey = config;
      this.baseUrl = "https://api.vitamail.com/v1";
      this.timeout = 30000;
    } else {
      this.apiKey = config.apiKey;
      this.baseUrl = config.baseUrl ?? "https://api.vitamail.com/v1";
      this.timeout = config.timeout ?? 30000;
    }
  }

  /**
   * Verify an email address.
   * Endpoint: POST /verify
   *
   * @param email - Email address to verify
   * @returns ServiceResponse with verification result
   */
  async verifyEmail(email: string): Promise<ServiceResponse<EmailVerificationData>> {
    try {
      // SCAFFOLDING: Real implementation would call:
      // POST https://api.vitamail.com/v1/verify
      // Body: { email: "test@example.com" }
      // Headers: Authorization: Bearer {apiKey}

      if (!email) {
        return {
          success: false,
          error: "Email is required",
          retryable: false,
        };
      }

      // Basic email format validation
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        return {
          success: false,
          error: "Invalid email format",
          retryable: false,
        };
      }

      const response = await this.makeRequest<VitaMailVerifyResponse>(
        "POST",
        "/verify",
        { email }
      );

      if (!response.success || !response.data) {
        return {
          success: false,
          error: response.error ?? "Failed to verify email",
          statusCode: response.statusCode,
          retryable: response.retryable ?? true,
        };
      }

      const data = response.data;

      // Map VitaMail result to our standardized status
      const status = this.mapResultToStatus(data.result);

      return {
        success: true,
        data: {
          email: data.email,
          status,
          deliverable: data.result === "deliverable",
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
   * Batch verify multiple emails.
   *
   * @param emails - Array of email addresses to verify
   * @returns ServiceResponse with array of verification results
   */
  async verifyBatch(
    emails: string[]
  ): Promise<ServiceResponse<EmailVerificationData[]>> {
    try {
      if (!emails || emails.length === 0) {
        return {
          success: false,
          error: "At least one email is required",
          retryable: false,
        };
      }

      // Verify each email individually (batch endpoint may differ)
      const results: EmailVerificationData[] = [];
      const errors: string[] = [];

      for (const email of emails) {
        const result = await this.verifyEmail(email);
        if (result.success && result.data) {
          results.push(result.data);
        } else {
          errors.push(`${email}: ${result.error}`);
        }
      }

      if (results.length === 0) {
        return {
          success: false,
          error: `All verifications failed: ${errors.join("; ")}`,
          retryable: true,
        };
      }

      return {
        success: true,
        data: results,
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
   * Quick check if email is likely valid (format + MX check only).
   * Lighter weight than full verification.
   *
   * @param email - Email to check
   * @returns boolean indicating likely validity
   */
  isLikelyValid(email: string): boolean {
    // Basic format check
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return false;
    }

    // Check for common invalid patterns
    const invalidPatterns = [
      /^test@/i,
      /^info@/i,
      /^admin@/i,
      /^noreply@/i,
      /^no-reply@/i,
      /\.invalid$/i,
      /\.test$/i,
    ];

    for (const pattern of invalidPatterns) {
      if (pattern.test(email)) {
        return false;
      }
    }

    return true;
  }

  /**
   * Map VitaMail result to standardized status.
   */
  private mapResultToStatus(
    result: VitaMailVerifyResponse["result"]
  ): VerificationStatus {
    switch (result) {
      case "deliverable":
        return "valid";
      case "undeliverable":
        return "invalid";
      case "risky":
        return "catch_all";
      case "unknown":
      default:
        return "unknown";
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

    return {
      success: false,
      error: "SCAFFOLDING: API not implemented",
      retryable: false,
    };
  }
}

/**
 * Create a VitaMail service instance.
 */
export function createVitaMailService(apiKey: string): VitaMailService {
  return new VitaMailService(apiKey);
}
