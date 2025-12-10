/**
 * Agent Registry
 * ==============
 * Exports all agent stubs for the Talent Engine.
 */

// Layer 1: Fuzzy Match Agent
export { FuzzyMatchAgent, FuzzyMatchAgentConfig, FuzzyMatchTask } from "./FuzzyMatchAgent";

// Layer 4: Missing Slot Agent
export {
  MissingSlotAgent,
  MissingSlotAgentConfig,
  MissingSlotTask,
  MissingSlotResult,
  DEFAULT_MISSING_SLOT_CONFIG,
} from "./MissingSlotAgent";

// Slot Processing Agents
export { LinkedInFinderAgent } from "./LinkedInFinderAgent";
export { PublicScannerAgent } from "./PublicScannerAgent";
export { PatternAgent } from "./PatternAgent";
export { EmailGeneratorAgent } from "./EmailGeneratorAgent";
export { TitleCompanyAgent } from "./TitleCompanyAgent";
export { HashAgent } from "./HashAgent";
