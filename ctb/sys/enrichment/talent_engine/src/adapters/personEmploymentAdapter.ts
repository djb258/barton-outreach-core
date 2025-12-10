/**
 * Person Employment Adapter
 * =========================
 * Generic adapter for looking up person employment history and current position.
 * Can be wired to: Apollo, Proxycurl, ZoomInfo, etc.
 */

import {
  AdapterResponse,
  AdapterConfig,
  PersonEmploymentData,
  DEFAULT_ADAPTER_CONFIG,
} from "./types";

/**
 * Person employment lookup configuration.
 */
export interface PersonEmploymentConfig extends AdapterConfig {
  /** Include employment history */
  include_history: boolean;
  /** Max history entries to return */
  max_history_entries: number;
}

/**
 * Default person employment configuration.
 */
export const DEFAULT_PERSON_EMPLOYMENT_CONFIG: PersonEmploymentConfig = {
  ...DEFAULT_ADAPTER_CONFIG,
  include_history: true,
  max_history_entries: 5,
};

/**
 * Person employment lookup input.
 */
export interface PersonEmploymentInput {
  /** Person's full name */
  full_name?: string;
  /** Person's first name */
  first_name?: string;
  /** Person's last name */
  last_name?: string;
  /** LinkedIn URL (most reliable identifier) */
  linkedin_url?: string;
  /** Current company (helps disambiguation) */
  company_name?: string;
  /** Email (alternative identifier) */
  email?: string;
}

/**
 * Lookup person employment data.
 *
 * TODO: Wire to real people data API (Apollo, Proxycurl, ZoomInfo)
 *
 * @param input - Person lookup parameters
 * @param config - Adapter configuration
 * @returns Promise<AdapterResponse<PersonEmploymentData>>
 */
export async function personEmploymentLookupAdapter(
  input: PersonEmploymentInput,
  config: PersonEmploymentConfig = DEFAULT_PERSON_EMPLOYMENT_CONFIG
): Promise<AdapterResponse<PersonEmploymentData>> {
  const startTime = Date.now();

  try {
    // Validate input
    if (!input.linkedin_url && !input.full_name && !(input.first_name && input.last_name)) {
      return {
        success: false,
        error: "At least one identifier required: linkedin_url, full_name, or first_name + last_name",
        latency_ms: Date.now() - startTime,
      };
    }

    // TODO: Replace with real API call
    // Example vendors: Apollo Person Enrichment, Proxycurl Profile API

    if (config.mock_mode) {
      return getMockPersonEmployment(input, config, startTime);
    }

    // Real implementation placeholder
    // const response = await realVendorApi.enrichPerson({
    //   linkedinUrl: input.linkedin_url,
    //   name: input.full_name,
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
      error: error instanceof Error ? error.message : "Unknown error in employment lookup",
      latency_ms: Date.now() - startTime,
    };
  }
}

/**
 * Generate mock person employment data.
 */
function getMockPersonEmployment(
  input: PersonEmploymentInput,
  config: PersonEmploymentConfig,
  startTime: number
): AdapterResponse<PersonEmploymentData> {
  // Extract name
  let fullName = input.full_name;
  if (!fullName && input.first_name && input.last_name) {
    fullName = `${input.first_name} ${input.last_name}`;
  }
  if (!fullName && input.linkedin_url) {
    // Try to extract from URL
    const match = input.linkedin_url.match(/linkedin\.com\/in\/([^\/\?]+)/);
    if (match) {
      const parts = match[1].split("-").slice(0, 2);
      fullName = parts.map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join(" ");
    }
  }

  if (!fullName) {
    return {
      success: false,
      error: "Could not determine person name",
      latency_ms: Date.now() - startTime,
    };
  }

  // Mock executive titles based on context
  const titles = [
    "Chief Executive Officer",
    "Chief Financial Officer",
    "VP of Human Resources",
    "Director of Benefits",
    "Chief Operating Officer",
    "Senior Vice President",
    "Managing Director",
  ];

  const companies = input.company_name
    ? [input.company_name]
    : ["Acme Corporation", "Global Tech Industries", "Smith & Associates"];

  const currentTitle = titles[Math.floor(Math.random() * titles.length)];
  const currentCompany = companies[0];

  const mockData: PersonEmploymentData = {
    full_name: fullName,
    current_title: currentTitle,
    current_company: currentCompany,
    linkedin_url:
      input.linkedin_url ||
      `https://linkedin.com/in/${fullName.toLowerCase().replace(/\s+/g, "-")}`,
  };

  if (config.include_history) {
    mockData.previous_titles = titles.slice(1, config.max_history_entries);
    mockData.previous_companies = [
      "Previous Corp",
      "Former Inc",
      "Old Company LLC",
    ].slice(0, config.max_history_entries - 1);
  }

  // Simulate email if company is known
  if (input.company_name) {
    const nameParts = fullName.toLowerCase().split(" ");
    const domain = input.company_name.toLowerCase().replace(/[^a-z]/g, "") + ".com";
    mockData.email = `${nameParts[0]}.${nameParts[nameParts.length - 1]}@${domain}`;
  }

  return {
    success: true,
    data: mockData,
    source: "mock",
    cost: 0.05,
    latency_ms: Date.now() - startTime,
  };
}

/**
 * Detect employment movement (job change).
 *
 * @param previousData - Previous employment data
 * @param currentData - Current employment data
 * @returns Movement detection result
 */
export function detectEmploymentMovement(
  previousData: PersonEmploymentData,
  currentData: PersonEmploymentData
): {
  movement_detected: boolean;
  movement_type?: "title_change" | "company_change" | "both";
  details?: string;
} {
  const titleChanged =
    previousData.current_title !== currentData.current_title &&
    previousData.current_title !== undefined &&
    currentData.current_title !== undefined;

  const companyChanged =
    previousData.current_company !== currentData.current_company &&
    previousData.current_company !== undefined &&
    currentData.current_company !== undefined;

  if (!titleChanged && !companyChanged) {
    return { movement_detected: false };
  }

  let movement_type: "title_change" | "company_change" | "both";
  let details: string;

  if (titleChanged && companyChanged) {
    movement_type = "both";
    details = `Changed from ${previousData.current_title} at ${previousData.current_company} to ${currentData.current_title} at ${currentData.current_company}`;
  } else if (companyChanged) {
    movement_type = "company_change";
    details = `Moved from ${previousData.current_company} to ${currentData.current_company}`;
  } else {
    movement_type = "title_change";
    details = `Changed role from ${previousData.current_title} to ${currentData.current_title}`;
  }

  return {
    movement_detected: true,
    movement_type,
    details,
  };
}
