/**
 * Agent Registry
 * ==============
 * Exports all enrichment agents for the Talent Engine.
 * All agents use the adapter pattern for vendor-agnostic operation.
 */

// Layer 1: Fuzzy Match Agent
export {
  FuzzyMatchAgent,
  FuzzyMatchAgentConfig,
  FuzzyMatchTask,
  DEFAULT_FUZZY_MATCH_AGENT_CONFIG,
} from "./FuzzyMatchAgent";

// Layer 4: Missing Slot Agent
export {
  MissingSlotAgent,
  MissingSlotAgentConfig,
  MissingSlotTask,
  MissingSlotResult,
  DEFAULT_MISSING_SLOT_CONFIG,
} from "./MissingSlotAgent";

// LinkedIn Agents
export {
  LinkedInFinderAgent,
  LinkedInFinderConfig,
  LinkedInFinderTask,
  DEFAULT_LINKEDIN_FINDER_CONFIG,
} from "./LinkedInFinderAgent";

export {
  PublicScannerAgent,
  PublicScannerConfig,
  PublicScannerTask,
  DEFAULT_PUBLIC_SCANNER_CONFIG,
} from "./PublicScannerAgent";

// Email Agents
export {
  PatternAgent,
  PatternAgentConfig,
  PatternTask,
  DEFAULT_PATTERN_AGENT_CONFIG,
} from "./PatternAgent";

export {
  EmailGeneratorAgent,
  EmailGeneratorConfig,
  EmailGeneratorTask,
  DEFAULT_EMAIL_GENERATOR_CONFIG,
} from "./EmailGeneratorAgent";

// Profile Agents
export {
  TitleCompanyAgent,
  TitleCompanyConfig,
  TitleCompanyTask,
  DEFAULT_TITLE_COMPANY_CONFIG,
} from "./TitleCompanyAgent";

// Utility Agents
export {
  HashAgent,
  HashAgentConfig,
  HashTask,
  HashAlgorithm,
  DEFAULT_HASH_AGENT_CONFIG,
} from "./HashAgent";
