/**
 * Adapters Index
 * ==============
 * Re-exports all tool adapters for the Talent Engine.
 *
 * These adapters provide vendor-agnostic interfaces for enrichment operations.
 * Each adapter can be wired to different vendors without changing agent logic.
 */

// Types
export {
  AdapterResponse,
  AdapterConfig,
  CompanySearchResult,
  PersonSearchResult,
  LinkedInProfileData,
  EmailPatternData,
  EmailVerificationResult,
  PersonEmploymentData,
  SlotDiscoveryResult,
  ProfileAccessibilityResult,
  DEFAULT_ADAPTER_CONFIG,
} from "./types";

// Company Lookup Adapter
export {
  CompanyLookupConfig,
  CompanyLookupInput,
  DEFAULT_COMPANY_LOOKUP_CONFIG,
  externalCompanyLookupAdapter,
  companyByDomainAdapter,
} from "./companyLookupAdapter";

// LinkedIn Resolver Adapter
export {
  LinkedInResolverConfig,
  LinkedInResolutionInput,
  DEFAULT_LINKEDIN_RESOLVER_CONFIG,
  linkedInResolverAdapter,
  linkedInProfileAdapter,
  linkedInAccessibilityAdapter,
} from "./linkedInResolverAdapter";

// Email Pattern Adapter
export {
  EmailPatternConfig,
  DEFAULT_EMAIL_PATTERN_CONFIG,
  COMMON_EMAIL_PATTERNS,
  emailPatternAdapter,
  generateEmailFromPattern,
  emailFinderAdapter,
} from "./emailPatternAdapter";

// Email Verification Adapter
export {
  EmailVerificationConfig,
  DEFAULT_EMAIL_VERIFICATION_CONFIG,
  emailVerificationAdapter,
  batchEmailVerificationAdapter,
  quickEmailValidation,
} from "./emailVerificationAdapter";

// Person Employment Adapter
export {
  PersonEmploymentConfig,
  PersonEmploymentInput,
  DEFAULT_PERSON_EMPLOYMENT_CONFIG,
  personEmploymentLookupAdapter,
  detectEmploymentMovement,
} from "./personEmploymentAdapter";

// Slot Discovery Adapter
export {
  SlotDiscoveryConfig,
  SlotDiscoveryInput,
  DEFAULT_SLOT_DISCOVERY_CONFIG,
  slotDiscoveryAdapter,
  findPersonForSlotAdapter,
  getTitlePatternsForSlot,
  determineSlotTypeFromTitle,
} from "./slotDiscoveryAdapter";
