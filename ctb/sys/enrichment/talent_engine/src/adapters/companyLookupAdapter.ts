/**
 * Company Lookup Adapter
 * ======================
 * Generic adapter for external company search/lookup.
 * Can be wired to: Clearbit, Apollo, LinkedIn Sales Navigator, etc.
 */

import {
  AdapterResponse,
  AdapterConfig,
  CompanySearchResult,
  DEFAULT_ADAPTER_CONFIG,
} from "./types";

/**
 * Adapter configuration specific to company lookup.
 */
export interface CompanyLookupConfig extends AdapterConfig {
  /** Minimum confidence threshold to return results */
  min_confidence: number;
  /** Maximum results to return */
  max_results: number;
}

/**
 * Default company lookup configuration.
 */
export const DEFAULT_COMPANY_LOOKUP_CONFIG: CompanyLookupConfig = {
  ...DEFAULT_ADAPTER_CONFIG,
  min_confidence: 0.6,
  max_results: 5,
};

/**
 * Company lookup input parameters.
 */
export interface CompanyLookupInput {
  /** Raw company name to search for */
  query: string;
  /** Optional domain hint */
  domain_hint?: string;
  /** Optional industry hint */
  industry_hint?: string;
  /** Optional location hint */
  location_hint?: string;
}

/**
 * External company lookup adapter.
 *
 * TODO: Wire to real vendor API (Clearbit, Apollo, etc.)
 *
 * @param input - Company lookup parameters
 * @param config - Adapter configuration
 * @returns Promise<AdapterResponse<CompanySearchResult[]>>
 */
export async function externalCompanyLookupAdapter(
  input: CompanyLookupInput,
  config: CompanyLookupConfig = DEFAULT_COMPANY_LOOKUP_CONFIG
): Promise<AdapterResponse<CompanySearchResult[]>> {
  const startTime = Date.now();

  try {
    // TODO: Replace with real API call
    // Example vendors: Clearbit Company API, Apollo Company Search, ZoomInfo

    if (config.mock_mode) {
      // Return mock data for testing
      return getMockCompanyResults(input, config, startTime);
    }

    // Real implementation placeholder
    // const response = await realVendorApi.searchCompanies({
    //   query: input.query,
    //   domain: input.domain_hint,
    //   industry: input.industry_hint,
    //   location: input.location_hint,
    // });

    return {
      success: false,
      error: "Real API not configured. Set mock_mode=true for testing.",
      latency_ms: Date.now() - startTime,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error in company lookup",
      latency_ms: Date.now() - startTime,
    };
  }
}

/**
 * Generate mock company results for testing.
 */
function getMockCompanyResults(
  input: CompanyLookupInput,
  config: CompanyLookupConfig,
  startTime: number
): AdapterResponse<CompanySearchResult[]> {
  const query = input.query.toLowerCase();

  // Simulated company database
  const mockCompanies: CompanySearchResult[] = [
    {
      company_name: "Acme Corporation",
      domain: "acme.com",
      industry: "Technology",
      employee_count: 500,
      linkedin_url: "https://linkedin.com/company/acme-corporation",
      confidence: query.includes("acme") ? 0.95 : 0.3,
    },
    {
      company_name: "Global Tech Industries",
      domain: "globaltech.com",
      industry: "Technology",
      employee_count: 2500,
      linkedin_url: "https://linkedin.com/company/global-tech-industries",
      confidence: query.includes("global") || query.includes("tech") ? 0.85 : 0.2,
    },
    {
      company_name: "Smith & Associates",
      domain: "smithassociates.com",
      industry: "Consulting",
      employee_count: 150,
      linkedin_url: "https://linkedin.com/company/smith-associates",
      confidence: query.includes("smith") ? 0.90 : 0.15,
    },
    {
      company_name: "Johnson Manufacturing",
      domain: "johnsonmfg.com",
      industry: "Manufacturing",
      employee_count: 1200,
      linkedin_url: "https://linkedin.com/company/johnson-manufacturing",
      confidence: query.includes("johnson") ? 0.88 : 0.1,
    },
    {
      company_name: "Pacific Healthcare Group",
      domain: "pacifichealthcare.com",
      industry: "Healthcare",
      employee_count: 3500,
      linkedin_url: "https://linkedin.com/company/pacific-healthcare-group",
      confidence: query.includes("pacific") || query.includes("health") ? 0.82 : 0.1,
    },
  ];

  // Filter and sort by confidence
  const results = mockCompanies
    .filter((c) => c.confidence >= config.min_confidence)
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, config.max_results);

  return {
    success: true,
    data: results,
    source: "mock",
    cached: false,
    cost: 0,
    latency_ms: Date.now() - startTime,
  };
}

/**
 * Lookup company by domain.
 *
 * TODO: Wire to domain enrichment API
 *
 * @param domain - Company domain
 * @param config - Adapter configuration
 * @returns Promise<AdapterResponse<CompanySearchResult>>
 */
export async function companyByDomainAdapter(
  domain: string,
  config: AdapterConfig = DEFAULT_ADAPTER_CONFIG
): Promise<AdapterResponse<CompanySearchResult>> {
  const startTime = Date.now();

  try {
    if (config.mock_mode) {
      // Mock domain lookup
      const domainLower = domain.toLowerCase().replace(/^www\./, "");

      const mockDomainMap: Record<string, CompanySearchResult> = {
        "acme.com": {
          company_name: "Acme Corporation",
          domain: "acme.com",
          industry: "Technology",
          employee_count: 500,
          confidence: 1.0,
        },
        "globaltech.com": {
          company_name: "Global Tech Industries",
          domain: "globaltech.com",
          industry: "Technology",
          employee_count: 2500,
          confidence: 1.0,
        },
      };

      const result = mockDomainMap[domainLower];

      if (result) {
        return {
          success: true,
          data: result,
          source: "mock",
          latency_ms: Date.now() - startTime,
        };
      }

      return {
        success: false,
        error: `No company found for domain: ${domain}`,
        latency_ms: Date.now() - startTime,
      };
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
