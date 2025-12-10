/**
 * Email Verification Adapter
 * ==========================
 * Generic adapter for email verification and deliverability checking.
 * Can be wired to: VitaMail, ZeroBounce, NeverBounce, Hunter, etc.
 */

import {
  AdapterResponse,
  AdapterConfig,
  EmailVerificationResult,
  DEFAULT_ADAPTER_CONFIG,
} from "./types";

/**
 * Email verification configuration.
 */
export interface EmailVerificationConfig extends AdapterConfig {
  /** Check MX records */
  check_mx: boolean;
  /** Check SMTP deliverability */
  check_smtp: boolean;
  /** Detect catch-all domains */
  detect_catch_all: boolean;
}

/**
 * Default email verification configuration.
 */
export const DEFAULT_EMAIL_VERIFICATION_CONFIG: EmailVerificationConfig = {
  ...DEFAULT_ADAPTER_CONFIG,
  check_mx: true,
  check_smtp: true,
  detect_catch_all: true,
};

/**
 * Verify email deliverability.
 *
 * TODO: Wire to real verification API (ZeroBounce, NeverBounce, VitaMail)
 *
 * @param email - Email address to verify
 * @param config - Adapter configuration
 * @returns Promise<AdapterResponse<EmailVerificationResult>>
 */
export async function emailVerificationAdapter(
  email: string,
  config: EmailVerificationConfig = DEFAULT_EMAIL_VERIFICATION_CONFIG
): Promise<AdapterResponse<EmailVerificationResult>> {
  const startTime = Date.now();

  try {
    // Validate email format first
    if (!isValidEmailFormat(email)) {
      return {
        success: true,
        data: {
          email,
          status: "invalid",
          deliverable: false,
          reason: "Invalid email format",
        },
        source: "local",
        latency_ms: Date.now() - startTime,
      };
    }

    // Check for disposable domain
    if (isDisposableDomain(email)) {
      return {
        success: true,
        data: {
          email,
          status: "disposable",
          deliverable: false,
          reason: "Disposable email domain detected",
        },
        source: "local",
        latency_ms: Date.now() - startTime,
      };
    }

    // TODO: Replace with real API call
    // Example vendors: ZeroBounce, NeverBounce, VitaMail

    if (config.mock_mode) {
      return getMockVerificationResult(email, config, startTime);
    }

    // Real implementation placeholder
    // const response = await realVendorApi.verifyEmail({
    //   email: email,
    //   checkMx: config.check_mx,
    //   checkSmtp: config.check_smtp,
    // });

    return {
      success: false,
      error: "Real API not configured. Set mock_mode=true for testing.",
      latency_ms: Date.now() - startTime,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error in email verification",
      latency_ms: Date.now() - startTime,
    };
  }
}

/**
 * Batch verify multiple emails.
 *
 * @param emails - Array of emails to verify
 * @param config - Adapter configuration
 * @returns Promise<AdapterResponse<EmailVerificationResult[]>>
 */
export async function batchEmailVerificationAdapter(
  emails: string[],
  config: EmailVerificationConfig = DEFAULT_EMAIL_VERIFICATION_CONFIG
): Promise<AdapterResponse<EmailVerificationResult[]>> {
  const startTime = Date.now();

  try {
    const results: EmailVerificationResult[] = [];

    for (const email of emails) {
      const result = await emailVerificationAdapter(email, config);
      if (result.success && result.data) {
        results.push(result.data);
      } else {
        results.push({
          email,
          status: "unknown",
          deliverable: false,
          reason: result.error || "Verification failed",
        });
      }
    }

    return {
      success: true,
      data: results,
      source: config.mock_mode ? "mock" : "api",
      cost: results.length * 0.01, // Estimated cost per verification
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
 * Validate email format using regex.
 */
function isValidEmailFormat(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Check if email domain is a known disposable domain.
 */
function isDisposableDomain(email: string): boolean {
  const disposableDomains = [
    "tempmail.com",
    "guerrillamail.com",
    "mailinator.com",
    "throwaway.email",
    "10minutemail.com",
    "temp-mail.org",
    "fakeinbox.com",
    "trashmail.com",
  ];

  const domain = email.split("@")[1]?.toLowerCase();
  return disposableDomains.includes(domain);
}

/**
 * Generate mock verification result.
 */
function getMockVerificationResult(
  email: string,
  config: EmailVerificationConfig,
  startTime: number
): AdapterResponse<EmailVerificationResult> {
  const domain = email.split("@")[1]?.toLowerCase();

  // Known valid domains for testing
  const knownValidDomains = [
    "acme.com",
    "globaltech.com",
    "smithassociates.com",
    "johnsonmfg.com",
    "pacifichealthcare.com",
    "gmail.com",
    "outlook.com",
    "yahoo.com",
  ];

  // Known catch-all domains
  const catchAllDomains = ["company.com", "example.com", "test.com"];

  let status: EmailVerificationResult["status"];
  let deliverable: boolean;
  let reason: string | undefined;

  if (knownValidDomains.includes(domain)) {
    // Simulate 85% valid rate for known domains
    if (Math.random() < 0.85) {
      status = "valid";
      deliverable = true;
    } else {
      status = "invalid";
      deliverable = false;
      reason = "Mailbox does not exist";
    }
  } else if (catchAllDomains.includes(domain)) {
    status = "catch_all";
    deliverable = true;
    reason = "Domain accepts all emails (catch-all)";
  } else {
    // Unknown domain - simulate various outcomes
    const rand = Math.random();
    if (rand < 0.5) {
      status = "valid";
      deliverable = true;
    } else if (rand < 0.75) {
      status = "unknown";
      deliverable = false;
      reason = "Could not verify deliverability";
    } else {
      status = "invalid";
      deliverable = false;
      reason = "Domain does not have valid MX records";
    }
  }

  return {
    success: true,
    data: {
      email,
      status,
      deliverable,
      reason,
    },
    source: "mock",
    cost: 0.01,
    latency_ms: Date.now() - startTime,
  };
}

/**
 * Quick email format validation (no API call).
 *
 * @param email - Email to validate
 * @returns Validation result
 */
export function quickEmailValidation(email: string): {
  valid: boolean;
  reason?: string;
} {
  if (!email || typeof email !== "string") {
    return { valid: false, reason: "Email is required" };
  }

  if (!isValidEmailFormat(email)) {
    return { valid: false, reason: "Invalid email format" };
  }

  if (isDisposableDomain(email)) {
    return { valid: false, reason: "Disposable email domain" };
  }

  const domain = email.split("@")[1];
  if (!domain || domain.length < 4) {
    return { valid: false, reason: "Invalid domain" };
  }

  return { valid: true };
}
