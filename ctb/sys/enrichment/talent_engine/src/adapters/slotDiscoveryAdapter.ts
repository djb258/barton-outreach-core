/**
 * Slot Discovery Adapter
 * ======================
 * Generic adapter for discovering people in specific roles at a company.
 * Used by MissingSlotAgent to find executives to fill slots.
 * Can be wired to: Apollo, ZoomInfo, LinkedIn Sales Navigator, etc.
 */

import {
  AdapterResponse,
  AdapterConfig,
  SlotDiscoveryResult,
  DEFAULT_ADAPTER_CONFIG,
} from "./types";

/**
 * Slot discovery configuration.
 */
export interface SlotDiscoveryConfig extends AdapterConfig {
  /** Minimum confidence threshold */
  min_confidence: number;
  /** Maximum results per slot type */
  max_results_per_slot: number;
  /** Include contact information */
  include_contact_info: boolean;
}

/**
 * Default slot discovery configuration.
 */
export const DEFAULT_SLOT_DISCOVERY_CONFIG: SlotDiscoveryConfig = {
  ...DEFAULT_ADAPTER_CONFIG,
  min_confidence: 0.7,
  max_results_per_slot: 3,
  include_contact_info: true,
};

/**
 * Slot discovery input.
 */
export interface SlotDiscoveryInput {
  /** Company name */
  company_name: string;
  /** Company domain (helps with accuracy) */
  company_domain?: string;
  /** Slot types to search for */
  slot_types: string[];
  /** Company LinkedIn URL (most reliable) */
  company_linkedin_url?: string;
}

/**
 * Title patterns for each slot type.
 */
const SLOT_TITLE_PATTERNS: Record<string, string[]> = {
  CEO: [
    "Chief Executive Officer",
    "CEO",
    "President",
    "Founder & CEO",
    "Co-Founder & CEO",
    "Managing Director",
    "General Manager",
  ],
  CFO: [
    "Chief Financial Officer",
    "CFO",
    "VP Finance",
    "Vice President of Finance",
    "Finance Director",
    "Controller",
    "Treasurer",
  ],
  HR: [
    "Chief Human Resources Officer",
    "CHRO",
    "VP Human Resources",
    "VP HR",
    "Head of HR",
    "HR Director",
    "Director of Human Resources",
    "People Operations Director",
    "Chief People Officer",
  ],
  BENEFITS: [
    "Benefits Director",
    "Director of Benefits",
    "Benefits Manager",
    "VP Benefits",
    "Head of Benefits",
    "Total Rewards Director",
    "Compensation & Benefits Director",
  ],
};

/**
 * Discover people in specific roles at a company.
 *
 * TODO: Wire to real people search API (Apollo, ZoomInfo, etc.)
 *
 * @param input - Slot discovery parameters
 * @param config - Adapter configuration
 * @returns Promise<AdapterResponse<SlotDiscoveryResult[]>>
 */
export async function slotDiscoveryAdapter(
  input: SlotDiscoveryInput,
  config: SlotDiscoveryConfig = DEFAULT_SLOT_DISCOVERY_CONFIG
): Promise<AdapterResponse<SlotDiscoveryResult[]>> {
  const startTime = Date.now();

  try {
    // Validate input
    if (!input.company_name) {
      return {
        success: false,
        error: "Company name is required",
        latency_ms: Date.now() - startTime,
      };
    }

    if (!input.slot_types || input.slot_types.length === 0) {
      return {
        success: false,
        error: "At least one slot type is required",
        latency_ms: Date.now() - startTime,
      };
    }

    // TODO: Replace with real API call
    // Example vendors: Apollo People Search, ZoomInfo, LinkedIn Sales Navigator

    if (config.mock_mode) {
      return getMockSlotDiscovery(input, config, startTime);
    }

    // Real implementation placeholder
    // const response = await realVendorApi.searchPeopleByRole({
    //   company: input.company_name,
    //   domain: input.company_domain,
    //   titles: getTitlesForSlots(input.slot_types),
    // });

    return {
      success: false,
      error: "Real API not configured. Set mock_mode=true for testing.",
      latency_ms: Date.now() - startTime,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error in slot discovery",
      latency_ms: Date.now() - startTime,
    };
  }
}

/**
 * Generate mock slot discovery results.
 */
function getMockSlotDiscovery(
  input: SlotDiscoveryInput,
  config: SlotDiscoveryConfig,
  startTime: number
): AdapterResponse<SlotDiscoveryResult[]> {
  const results: SlotDiscoveryResult[] = [];

  // Mock first names and last names for generating fake people
  const firstNames = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa"];
  const lastNames = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Davis", "Miller", "Wilson"];

  for (const slotType of input.slot_types) {
    const titles = SLOT_TITLE_PATTERNS[slotType] || [];
    if (titles.length === 0) continue;

    // Simulate finding 0-2 people per slot
    const numResults = Math.floor(Math.random() * 3);

    for (let i = 0; i < numResults && i < config.max_results_per_slot; i++) {
      const firstName = firstNames[Math.floor(Math.random() * firstNames.length)];
      const lastName = lastNames[Math.floor(Math.random() * lastNames.length)];
      const title = titles[Math.floor(Math.random() * Math.min(3, titles.length))];
      const confidence = 0.7 + Math.random() * 0.25; // 70-95%

      if (confidence < config.min_confidence) continue;

      const result: SlotDiscoveryResult = {
        slot_type: slotType,
        person_name: `${firstName} ${lastName}`,
        title,
        linkedin_url: `https://linkedin.com/in/${firstName.toLowerCase()}-${lastName.toLowerCase()}-${Math.random()
          .toString(36)
          .substring(2, 6)}`,
        confidence,
      };

      if (config.include_contact_info && input.company_domain) {
        result.email = `${firstName.toLowerCase()}.${lastName.toLowerCase()}@${input.company_domain}`;
      }

      results.push(result);
    }
  }

  return {
    success: true,
    data: results,
    source: "mock",
    cost: input.slot_types.length * 0.02, // Cost per slot type searched
    latency_ms: Date.now() - startTime,
  };
}

/**
 * Find a single person for a specific slot type.
 *
 * @param companyName - Company name
 * @param slotType - Slot type to find
 * @param companyDomain - Optional company domain
 * @param config - Adapter configuration
 * @returns Promise<AdapterResponse<SlotDiscoveryResult | null>>
 */
export async function findPersonForSlotAdapter(
  companyName: string,
  slotType: string,
  companyDomain?: string,
  config: SlotDiscoveryConfig = DEFAULT_SLOT_DISCOVERY_CONFIG
): Promise<AdapterResponse<SlotDiscoveryResult | null>> {
  const startTime = Date.now();

  const result = await slotDiscoveryAdapter(
    {
      company_name: companyName,
      company_domain: companyDomain,
      slot_types: [slotType],
    },
    config
  );

  if (!result.success) {
    return {
      success: false,
      error: result.error,
      latency_ms: Date.now() - startTime,
    };
  }

  // Return the highest confidence result
  const bestMatch = result.data
    ?.filter((r) => r.slot_type === slotType)
    .sort((a, b) => b.confidence - a.confidence)[0];

  return {
    success: true,
    data: bestMatch || null,
    source: result.source,
    cost: result.cost,
    latency_ms: Date.now() - startTime,
  };
}

/**
 * Get title patterns for a slot type.
 *
 * @param slotType - Slot type
 * @returns Array of title patterns
 */
export function getTitlePatternsForSlot(slotType: string): string[] {
  return SLOT_TITLE_PATTERNS[slotType] || [];
}

/**
 * Determine slot type from a title.
 *
 * @param title - Job title
 * @returns Best matching slot type or null
 */
export function determineSlotTypeFromTitle(title: string): string | null {
  const titleLower = title.toLowerCase();

  // Check each slot type
  for (const [slotType, patterns] of Object.entries(SLOT_TITLE_PATTERNS)) {
    for (const pattern of patterns) {
      if (titleLower.includes(pattern.toLowerCase())) {
        return slotType;
      }
    }
  }

  // Fallback heuristics
  if (titleLower.includes("ceo") || titleLower.includes("chief executive")) {
    return "CEO";
  }
  if (titleLower.includes("cfo") || titleLower.includes("chief financial")) {
    return "CFO";
  }
  if (titleLower.includes("hr") || titleLower.includes("human resource") || titleLower.includes("people")) {
    return "HR";
  }
  if (titleLower.includes("benefit") || titleLower.includes("compensation") || titleLower.includes("total rewards")) {
    return "BENEFITS";
  }

  return null;
}
