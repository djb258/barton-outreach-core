/**
 * Company Hub Node
 * ================
 * MASTER NODE of the Hub-and-Spoke Architecture
 *
 * All data must anchor to a company before being processed by spoke nodes.
 * Company Hub is responsible for:
 * - Company identity resolution (fuzzy matching)
 * - Domain and email pattern discovery
 * - Slot definition and tracking
 * - Gating access to downstream nodes
 *
 * Node Agents:
 * - CompanyFuzzyMatchAgent: Resolves raw company input to canonical names
 * - CompanyStateAgent: Evaluates company readiness for downstream processing
 * - PatternAgent: Discovers email patterns for company domains
 * - EmailGeneratorAgent: Generates verified email addresses
 * - MissingSlotAgent: Detects and triggers discovery for empty slots
 */

// Company Fuzzy Match Agent
export {
  CompanyFuzzyMatchAgent,
  CompanyFuzzyMatchAgentConfig,
  CompanyFuzzyMatchTask,
  DEFAULT_COMPANY_FUZZY_MATCH_CONFIG,
} from "./CompanyFuzzyMatchAgent";

// Company State Agent (NEW - Hub Coordinator)
export {
  CompanyStateAgent,
  CompanyStateAgentConfig,
  CompanyStateTask,
  CompanyStateEvaluation,
  CompanyIdentityStatus,
  CompanyReadiness,
  DEFAULT_COMPANY_STATE_CONFIG,
} from "./CompanyStateAgent";

// Pattern Agent
export {
  PatternAgent,
  PatternAgentConfig,
  PatternTask,
  DEFAULT_PATTERN_AGENT_CONFIG,
} from "./PatternAgent";

// Email Generator Agent
export {
  EmailGeneratorAgent,
  EmailGeneratorConfig,
  EmailGeneratorTask,
  DEFAULT_EMAIL_GENERATOR_CONFIG,
} from "./EmailGeneratorAgent";

// Missing Slot Agent
export {
  MissingSlotAgent,
  MissingSlotAgentConfig,
  MissingSlotTask,
  MissingSlotResult,
  DEFAULT_MISSING_SLOT_CONFIG,
} from "./MissingSlotAgent";

/**
 * Company Hub Node Processing Order:
 *
 * 1. CompanyFuzzyMatchAgent → Resolve company name
 * 2. CompanyStateAgent → Evaluate identity completeness
 * 3. PatternAgent → Discover email pattern (if missing)
 * 4. MissingSlotAgent → Check slot completeness
 * 5. (Route to People Node for slot discovery)
 * 6. EmailGeneratorAgent → Generate emails for discovered people
 */
