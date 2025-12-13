/**
 * DOL Node
 * ========
 * SPOKE NODE for Department of Labor data integration
 *
 * Provides Form 5500 filing data anchored to companies from Company Hub.
 * DOL Node is responsible for:
 * - Form 5500 filing synchronization
 * - Renewal date extraction
 * - Carrier name normalization
 * - EIN-to-company matching
 *
 * Node Agents:
 * - DOLSyncAgent: Synchronizes Form 5500 data from DOL ERISA
 * - RenewalParserAgent: Extracts plan renewal dates
 * - CarrierNormalizerAgent: Normalizes carrier names from Schedule A
 */

// DOL Sync Agent
export {
  DOLSyncAgent,
  DOLSyncAgentConfig,
  DOLSyncTask,
  Form5500Filing,
  DEFAULT_DOL_SYNC_CONFIG,
} from "./DOLSyncAgent";

// Renewal Parser Agent
export {
  RenewalParserAgent,
  RenewalParserAgentConfig,
  RenewalParserTask,
  RenewalInfo,
  DEFAULT_RENEWAL_PARSER_CONFIG,
} from "./RenewalParserAgent";

// Carrier Normalizer Agent
export {
  CarrierNormalizerAgent,
  CarrierNormalizerAgentConfig,
  CarrierNormalizerTask,
  ScheduleACarrier,
  NormalizedCarrier,
  CarrierType,
  DEFAULT_CARRIER_NORMALIZER_CONFIG,
} from "./CarrierNormalizerAgent";

/**
 * DOL Node Processing Order:
 *
 * 1. DOLSyncAgent → Fetch Form 5500 filings
 * 2. RenewalParserAgent → Extract renewal dates
 * 3. CarrierNormalizerAgent → Normalize carrier names
 * 4. (Renewal dates feed BIT Node for scoring)
 * 5. (Carrier data enables competitive analysis)
 */
