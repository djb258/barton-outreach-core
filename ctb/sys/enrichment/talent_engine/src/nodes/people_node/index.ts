/**
 * People Node
 * ===========
 * SPOKE NODE for person-level enrichment
 *
 * All people must be anchored to a company from Company Hub.
 * People Node is responsible for:
 * - LinkedIn profile discovery and verification
 * - Title and company retrieval
 * - Movement detection via hash comparison
 * - Person deduplication within companies
 *
 * Node Agents:
 * - LinkedInFinderAgent: Discovers LinkedIn URLs for people
 * - PublicScannerAgent: Checks LinkedIn profile accessibility
 * - TitleCompanyAgent: Retrieves current title and company
 * - MovementHashAgent: Generates hashes for change detection
 * - PeopleFuzzyMatchAgent: Deduplicates person records
 */

// LinkedIn Finder Agent
export {
  LinkedInFinderAgent,
  LinkedInFinderConfig,
  LinkedInFinderTask,
  DEFAULT_LINKEDIN_FINDER_CONFIG,
} from "./LinkedInFinderAgent";

// Public Scanner Agent
export {
  PublicScannerAgent,
  PublicScannerConfig,
  PublicScannerTask,
  DEFAULT_PUBLIC_SCANNER_CONFIG,
} from "./PublicScannerAgent";

// Title Company Agent
export {
  TitleCompanyAgent,
  TitleCompanyConfig,
  TitleCompanyTask,
  DEFAULT_TITLE_COMPANY_CONFIG,
} from "./TitleCompanyAgent";

// Movement Hash Agent (formerly HashAgent)
export {
  MovementHashAgent,
  MovementHashAgentConfig,
  MovementHashTask,
  HashAlgorithm,
  DEFAULT_MOVEMENT_HASH_CONFIG,
} from "./MovementHashAgent";

// People Fuzzy Match Agent (NEW)
export {
  PeopleFuzzyMatchAgent,
  PeopleFuzzyMatchAgentConfig,
  PeopleFuzzyMatchTask,
  PersonCandidate,
  PersonMatchResult,
  DEFAULT_PEOPLE_FUZZY_MATCH_CONFIG,
} from "./PeopleFuzzyMatchAgent";

/**
 * People Node Processing Order:
 *
 * 1. PeopleFuzzyMatchAgent → Deduplicate/match person
 * 2. LinkedInFinderAgent → Find LinkedIn URL
 * 3. PublicScannerAgent → Check profile accessibility
 * 4. TitleCompanyAgent → Get current title/company
 * 5. MovementHashAgent → Generate movement hash
 * 6. (Movement signals feed BIT Node)
 */
