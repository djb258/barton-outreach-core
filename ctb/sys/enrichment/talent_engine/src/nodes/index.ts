/**
 * Talent Engine Nodes
 * ===================
 * Hub-and-Spoke Architecture Node Registry
 *
 * All nodes in the talent engine follow a strict processing order:
 *
 * ```
 * COMPANY_HUB (Master Node)
 *       │
 *       ├──────► PEOPLE_NODE (Spoke)
 *       │              │
 *       ├──────► DOL_NODE (Spoke)
 *       │              │
 *       └──────────────┴──────► BIT_NODE (Spoke)
 * ```
 *
 * GOLDEN RULE: No spoke node processes data without a company anchor.
 */

// Company Hub - Master Node
export * from "./company_hub";

// People Node - Spoke
export * from "./people_node";

// DOL Node - Spoke
export * from "./dol_node";

// BIT Node - Spoke
export * from "./bit_node";

// Enrichment Node - Utility (Adapters)
export * from "./enrichment_node";

/**
 * Node Processing Order:
 *
 * Phase 1 - COMPANY_HUB:
 *   1. CompanyFuzzyMatchAgent → Resolve company name
 *   2. CompanyStateAgent → Evaluate identity
 *   3. PatternAgent → Discover email pattern
 *   4. MissingSlotAgent → Check slots
 *
 * Phase 2 - PEOPLE_NODE:
 *   1. PeopleFuzzyMatchAgent → Deduplicate person
 *   2. LinkedInFinderAgent → Find LinkedIn URL
 *   3. PublicScannerAgent → Check accessibility
 *   4. TitleCompanyAgent → Get current title/company
 *   5. MovementHashAgent → Generate movement hash
 *
 * Phase 3 - DOL_NODE:
 *   1. DOLSyncAgent → Fetch Form 5500 filings
 *   2. RenewalParserAgent → Extract renewal dates
 *   3. CarrierNormalizerAgent → Normalize carriers
 *
 * Phase 4 - BIT_NODE:
 *   1. ChurnDetectorAgent → Detect churn patterns
 *   2. RenewalIntentAgent → Analyze renewal timing
 *   3. BITScoreAgent → Calculate composite score
 */
