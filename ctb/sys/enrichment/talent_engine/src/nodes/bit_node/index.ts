/**
 * BIT Node
 * ========
 * SPOKE NODE for Buyer Intent Tool scoring
 *
 * Calculates buyer intent scores from multiple signal sources.
 * BIT Node is responsible for:
 * - Composite intent score calculation
 * - Executive churn pattern detection
 * - Renewal window intent analysis
 * - Outreach prioritization
 *
 * Node Agents:
 * - BITScoreAgent: Calculates composite buyer intent scores
 * - ChurnDetectorAgent: Detects executive turnover patterns
 * - RenewalIntentAgent: Analyzes renewal timing for intent signals
 */

// BIT Score Agent
export {
  BITScoreAgent,
  BITScoreAgentConfig,
  BITScoreTask,
  IntentSignals,
  BITScoreResult,
  BITScoreTier,
  DEFAULT_BIT_SCORE_CONFIG,
} from "./BITScoreAgent";

// Churn Detector Agent
export {
  ChurnDetectorAgent,
  ChurnDetectorAgentConfig,
  ChurnDetectorTask,
  MovementEvent,
  ChurnAnalysis,
  ChurnRiskLevel,
  DEFAULT_CHURN_DETECTOR_CONFIG,
} from "./ChurnDetectorAgent";

// Renewal Intent Agent
export {
  RenewalIntentAgent,
  RenewalIntentAgentConfig,
  RenewalIntentTask,
  RenewalIntentSignal,
  RenewalUrgency,
  DEFAULT_RENEWAL_INTENT_CONFIG,
} from "./RenewalIntentAgent";

/**
 * BIT Node Processing Order:
 *
 * 1. ChurnDetectorAgent → Analyze movement events
 * 2. RenewalIntentAgent → Analyze renewal timing
 * 3. BITScoreAgent → Calculate composite score
 * 4. (Scores feed Outreach Node for prioritization)
 */
