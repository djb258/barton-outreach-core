/**
 * Apollo Service — FALLBACK ONLY
 * ===============================
 * API wrapper for Apollo.io person enrichment.
 *
 * IMPORTANT: This service is FALLBACK ONLY.
 * - Only run if Proxycurl fails AND cost guard permits
 * - Never call Apollo first
 * - Always soft-fail, never throw
 *
 * Endpoint:
 * - POST https://api.apollo.io/v1/people/search
 *
 * Cost: ~$0.03 per enrichment
 */

import { ServiceResponse, ProfileData, ServiceConfig } from "./types";

/**
 * Apollo person search request.
 */
export interface ApolloSearchRequest {
  q_organization_name?: string;
  q_keywords?: string;
  person_titles?: string[];
  person_name?: string;
  page?: number;
  per_page?: number;
}

/**
 * Apollo person search response.
 */
export interface ApolloSearchResponse {
  people: ApolloPerson[];
  pagination: {
    page: number;
    per_page: number;
    total_entries: number;
    total_pages: number;
  };
}

export interface ApolloPerson {
  id: string;
  first_name: string;
  last_name: string;
  name: string;
  linkedin_url: string | null;
  title: string;
  email: string | null;
  organization: ApolloOrganization | null;
}

export interface ApolloOrganization {
  id: string;
  name: string;
  website_url: string | null;
}

/**
 * Slot type to Apollo title mapping.
 */
const SLOT_TO_TITLES: Record<string, string[]> = {
  CEO: ["Chief Executive Officer", "CEO", "President", "Founder", "Owner"],
  CFO: ["Chief Financial Officer", "CFO", "VP Finance", "Finance Director"],
  HR: ["Chief Human Resources Officer", "CHRO", "VP HR", "HR Director", "Head of HR"],
  BENEFITS: ["Benefits Manager", "Benefits Director", "Benefits Administrator", "Total Rewards"],
};

/**
 * Apollo service wrapper — FALLBACK ONLY.
 * Never throws raw errors - always returns ServiceResponse.
 */
export class ApolloService {
  private apiKey: string;
  private baseUrl: string;
  private timeout: number;

  /**
   * Flag indicating this is a fallback service.
   */
  readonly isFallback = true;

  constructor(config: ServiceConfig | string) {
    if (typeof config === "string") {
      this.apiKey = config;
      this.baseUrl = "https://api.apollo.io/v1";
      this.timeout = 30000;
    } else {
      this.apiKey = config.apiKey;
      this.baseUrl = config.baseUrl ?? "https://api.apollo.io/v1";
      this.timeout = config.timeout ?? 30000;
    }
  }

  /**
   * Enrich person data using Apollo.
   * FALLBACK ONLY: Only call if primary service (Proxycurl) fails.
   *
   * Endpoint: POST /v1/people/search
   *
   * @param companyName - Company name to search within
   * @param slotType - Slot type (CEO, CFO, HR, BENEFITS)
   * @param personName - Optional person name for filtering
   * @returns ServiceResponse with enriched profile data
   */
  async enrichPerson(
    companyName: string,
    slotType: string,
    personName?: string
  ): Promise<ServiceResponse<ProfileData>> {
    try {
      // SCAFFOLDING: Real implementation would call:
      // POST https://api.apollo.io/v1/people/search
      // Body: { q_organization_name, person_titles, person_name }
      // Headers: x-api-key: {apiKey}

      if (!companyName) {
        return {
          success: false,
          error: "Company name is required",
          retryable: false,
        };
      }

      // Get titles for slot type
      const titles = SLOT_TO_TITLES[slotType] ?? [];

      const searchRequest: ApolloSearchRequest = {
        q_organization_name: companyName,
        person_titles: titles.length > 0 ? titles : undefined,
        person_name: personName,
        page: 1,
        per_page: 5, // Only need top matches
      };

      const response = await this.makeRequest<ApolloSearchResponse>(
        "POST",
        "/people/search",
        searchRequest
      );

      if (!response.success || !response.data?.people?.length) {
        return {
          success: false,
          error: response.error ?? "No matching person found",
          statusCode: response.statusCode,
          retryable: response.retryable ?? true,
        };
      }

      // Get best match (first result)
      const person = response.data.people[0];

      // If personName provided, try to find exact match
      if (personName) {
        const exactMatch = response.data.people.find(
          (p) => p.name.toLowerCase() === personName.toLowerCase()
        );
        if (exactMatch) {
          return this.mapPersonToProfile(exactMatch);
        }
      }

      return this.mapPersonToProfile(person);
    } catch (error) {
      // Always soft-fail, never throw
      return {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error occurred",
        retryable: true,
      };
    }
  }

  /**
   * Search for people at a company by role.
   * FALLBACK ONLY.
   *
   * @param companyName - Company name
   * @param titles - Optional title filter
   * @returns ServiceResponse with array of profiles
   */
  async searchPeopleByCompany(
    companyName: string,
    titles?: string[]
  ): Promise<ServiceResponse<ProfileData[]>> {
    try {
      if (!companyName) {
        return {
          success: false,
          error: "Company name is required",
          retryable: false,
        };
      }

      const searchRequest: ApolloSearchRequest = {
        q_organization_name: companyName,
        person_titles: titles,
        page: 1,
        per_page: 10,
      };

      const response = await this.makeRequest<ApolloSearchResponse>(
        "POST",
        "/people/search",
        searchRequest
      );

      if (!response.success || !response.data?.people?.length) {
        return {
          success: false,
          error: response.error ?? "No people found at company",
          statusCode: response.statusCode,
          retryable: response.retryable ?? true,
        };
      }

      const profiles = response.data.people.map((person) => ({
        linkedin_url: person.linkedin_url ?? undefined,
        full_name: person.name,
        first_name: person.first_name,
        last_name: person.last_name,
        title: person.title,
        company: person.organization?.name,
        email: person.email ?? undefined,
      }));

      return {
        success: true,
        data: profiles,
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
   * Map Apollo person to standardized profile.
   */
  private mapPersonToProfile(person: ApolloPerson): ServiceResponse<ProfileData> {
    return {
      success: true,
      data: {
        linkedin_url: person.linkedin_url ?? undefined,
        full_name: person.name,
        first_name: person.first_name,
        last_name: person.last_name,
        title: person.title,
        company: person.organization?.name,
        email: person.email ?? undefined,
      },
      statusCode: 200,
    };
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
    //     "x-api-key": this.apiKey,
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
 * Create an Apollo service instance.
 * Remember: This is FALLBACK ONLY.
 */
export function createApolloService(apiKey: string): ApolloService {
  return new ApolloService(apiKey);
}
