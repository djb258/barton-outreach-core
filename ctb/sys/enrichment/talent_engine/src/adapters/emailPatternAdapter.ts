/**
 * Email Pattern Adapter
 * =====================
 * Generic adapter for email pattern discovery and derivation.
 * Can be wired to: Hunter.io, Clearbit, custom pattern databases, etc.
 */

import {
  AdapterResponse,
  AdapterConfig,
  EmailPatternData,
  DEFAULT_ADAPTER_CONFIG,
} from "./types";

/**
 * Email pattern adapter configuration.
 */
export interface EmailPatternConfig extends AdapterConfig {
  /** Minimum confidence threshold */
  min_confidence: number;
  /** Include example emails if available */
  include_examples: boolean;
}

/**
 * Default email pattern configuration.
 */
export const DEFAULT_EMAIL_PATTERN_CONFIG: EmailPatternConfig = {
  ...DEFAULT_ADAPTER_CONFIG,
  min_confidence: 0.5,
  include_examples: true,
};

/**
 * Common email patterns in order of prevalence.
 */
export const COMMON_EMAIL_PATTERNS = [
  "{first}.{last}",      // john.doe
  "{first}{last}",       // johndoe
  "{f}{last}",           // jdoe
  "{first}_{last}",      // john_doe
  "{first}",             // john
  "{last}.{first}",      // doe.john
  "{f}.{last}",          // j.doe
  "{first}{l}",          // johnd
  "{last}",              // doe
  "{first}-{last}",      // john-doe
];

/**
 * Derive email pattern for a domain.
 *
 * TODO: Wire to real pattern discovery API (Hunter.io, etc.)
 *
 * @param domain - Company domain
 * @param config - Adapter configuration
 * @returns Promise<AdapterResponse<EmailPatternData>>
 */
export async function emailPatternAdapter(
  domain: string,
  config: EmailPatternConfig = DEFAULT_EMAIL_PATTERN_CONFIG
): Promise<AdapterResponse<EmailPatternData>> {
  const startTime = Date.now();

  try {
    // TODO: Replace with real API call
    // Example vendors: Hunter.io Domain Search, Clearbit

    if (config.mock_mode) {
      return getMockEmailPattern(domain, config, startTime);
    }

    // Real implementation placeholder
    // const response = await realVendorApi.getEmailPattern({
    //   domain: domain,
    // });

    return {
      success: false,
      error: "Real API not configured. Set mock_mode=true for testing.",
      latency_ms: Date.now() - startTime,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error in email pattern lookup",
      latency_ms: Date.now() - startTime,
    };
  }
}

/**
 * Generate mock email pattern result.
 */
function getMockEmailPattern(
  domain: string,
  config: EmailPatternConfig,
  startTime: number
): AdapterResponse<EmailPatternData> {
  const domainLower = domain.toLowerCase().replace(/^www\./, "");

  // Simulated pattern database
  const mockPatternDatabase: Record<string, EmailPatternData> = {
    "acme.com": {
      domain: "acme.com",
      pattern: "{first}.{last}",
      confidence: 0.95,
      examples: ["john.doe@acme.com", "jane.smith@acme.com"],
    },
    "globaltech.com": {
      domain: "globaltech.com",
      pattern: "{f}{last}",
      confidence: 0.88,
      examples: ["jdoe@globaltech.com", "msmith@globaltech.com"],
    },
    "smithassociates.com": {
      domain: "smithassociates.com",
      pattern: "{first}_{last}",
      confidence: 0.82,
      examples: ["john_doe@smithassociates.com"],
    },
    "johnsonmfg.com": {
      domain: "johnsonmfg.com",
      pattern: "{first}{last}",
      confidence: 0.90,
      examples: ["johndoe@johnsonmfg.com"],
    },
    "pacifichealthcare.com": {
      domain: "pacifichealthcare.com",
      pattern: "{first}.{last}",
      confidence: 0.92,
      examples: ["john.doe@pacifichealthcare.com"],
    },
  };

  // Check if we have a known pattern
  const knownPattern = mockPatternDatabase[domainLower];
  if (knownPattern) {
    return {
      success: true,
      data: config.include_examples
        ? knownPattern
        : { ...knownPattern, examples: undefined },
      source: "mock",
      cost: 0.01,
      latency_ms: Date.now() - startTime,
    };
  }

  // Generate a random pattern for unknown domains
  const randomPattern = COMMON_EMAIL_PATTERNS[Math.floor(Math.random() * 3)]; // Top 3 most common
  const mockData: EmailPatternData = {
    domain: domainLower,
    pattern: randomPattern,
    confidence: 0.6 + Math.random() * 0.2, // 60-80% confidence
    examples: config.include_examples
      ? [`example${randomPattern.replace(/[{}]/g, "")}@${domainLower}`]
      : undefined,
  };

  return {
    success: true,
    data: mockData,
    source: "mock",
    cost: 0.01,
    latency_ms: Date.now() - startTime,
  };
}

/**
 * Generate email from pattern.
 *
 * @param pattern - Email pattern (e.g., "{first}.{last}")
 * @param domain - Company domain
 * @param firstName - Person's first name
 * @param lastName - Person's last name
 * @returns Generated email address
 */
export function generateEmailFromPattern(
  pattern: string,
  domain: string,
  firstName: string,
  lastName: string
): string {
  const cleanFirst = firstName.toLowerCase().replace(/[^a-z]/g, "");
  const cleanLast = lastName.toLowerCase().replace(/[^a-z]/g, "");

  let email = pattern
    .replace(/{first}/g, cleanFirst)
    .replace(/{last}/g, cleanLast)
    .replace(/{f}/g, cleanFirst.charAt(0))
    .replace(/{l}/g, cleanLast.charAt(0));

  return `${email}@${domain.toLowerCase().replace(/^www\./, "")}`;
}

/**
 * Find email using pattern + verification.
 *
 * TODO: Wire to email finder API
 *
 * @param domain - Company domain
 * @param firstName - First name
 * @param lastName - Last name
 * @param config - Adapter configuration
 * @returns Promise<AdapterResponse<{ email: string; confidence: number }>>
 */
export async function emailFinderAdapter(
  domain: string,
  firstName: string,
  lastName: string,
  config: AdapterConfig = DEFAULT_ADAPTER_CONFIG
): Promise<AdapterResponse<{ email: string; confidence: number }>> {
  const startTime = Date.now();

  try {
    if (config.mock_mode) {
      // First get the pattern
      const patternResult = await emailPatternAdapter(domain, {
        ...DEFAULT_EMAIL_PATTERN_CONFIG,
        mock_mode: true,
      });

      if (!patternResult.success || !patternResult.data) {
        return {
          success: false,
          error: "Could not determine email pattern for domain",
          latency_ms: Date.now() - startTime,
        };
      }

      // Generate email from pattern
      const email = generateEmailFromPattern(
        patternResult.data.pattern,
        domain,
        firstName,
        lastName
      );

      return {
        success: true,
        data: {
          email,
          confidence: patternResult.data.confidence,
        },
        source: "mock",
        cost: 0.02,
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
