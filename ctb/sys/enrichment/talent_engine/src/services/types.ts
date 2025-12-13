/**
 * Service Types
 * =============
 * Shared type definitions for all service wrappers.
 */

/**
 * Standardized service response wrapper.
 * All service methods return this format - never raw errors.
 */
export interface ServiceResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  statusCode?: number;
  retryable?: boolean;
}

/**
 * Service endpoint definition.
 */
export interface ServiceEndpoint {
  method: "GET" | "POST" | "PUT" | "DELETE";
  url: string;
  description?: string;
}

/**
 * Common profile data structure.
 */
export interface ProfileData {
  linkedin_url?: string;
  full_name?: string;
  first_name?: string;
  last_name?: string;
  title?: string;
  company?: string;
  email?: string;
  public_accessible?: boolean;
}

/**
 * Email pattern data.
 */
export interface EmailPatternData {
  pattern?: string;
  domain?: string;
  confidence?: number;
}

/**
 * Email verification result.
 */
export interface EmailVerificationData {
  email: string;
  status: "valid" | "invalid" | "unknown" | "catch_all";
  deliverable: boolean;
}

/**
 * Base service configuration.
 */
export interface ServiceConfig {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
}
