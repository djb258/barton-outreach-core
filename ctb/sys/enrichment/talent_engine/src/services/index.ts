/**
 * Services Index
 * ==============
 * Re-exports all service wrappers for easy importing.
 */

// Types
export {
  ServiceResponse,
  ServiceEndpoint,
  ProfileData,
  EmailPatternData,
  EmailVerificationData,
  ServiceConfig,
} from "./types";

// Proxycurl
export {
  ProxycurlService,
  ProxycurlProfile,
  ProxycurlExperience,
  createProxycurlService,
} from "./proxycurl";

// Hunter.io
export {
  HunterService,
  HunterDomainResponse,
  HunterEmail,
  HunterEmailFinderResponse,
  createHunterService,
} from "./hunter";

// VitaMail
export {
  VitaMailService,
  VitaMailVerifyResponse,
  createVitaMailService,
} from "./vitamail";

// Apollo (FALLBACK ONLY)
export {
  ApolloService,
  ApolloSearchRequest,
  ApolloSearchResponse,
  ApolloPerson,
  ApolloOrganization,
  createApolloService,
} from "./apollo";
