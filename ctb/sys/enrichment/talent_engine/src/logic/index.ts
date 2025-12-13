/**
 * Logic Index
 * ===========
 * Re-exports all logic modules.
 */

// Fuzzy Match
export {
  FuzzyMatchConfig,
  FuzzyMatchResult,
  FuzzyCandidate,
  DEFAULT_FUZZY_CONFIG,
  calculateSimilarity,
  findFuzzyMatches,
  applyFuzzyMatchResult,
  needsFuzzyMatch,
  getRowsNeedingFuzzyMatch,
  processFuzzyMatch,
} from "./fuzzyMatch";

// Checklist
export {
  ChecklistResult,
  evaluateChecklist,
  getMissingSummary,
  getNextMissingItem,
  mapMissingItemToAgent,
  getNeededAgent,
  batchEvaluateChecklists,
  getRowsReadyForCompletion,
  getRowsNeedingProcessing,
} from "./checklist";

// Company Checker
export {
  CompanyCheckerConfig,
  CompanyCheckResult,
  DEFAULT_CHECKER_CONFIG,
  checkCompany,
  batchCheckCompanies,
  getCompaniesNeedingMissingSlotAgent,
  getCompaniesWithMissingMandatorySlots,
  getFullyStaffedCompanies,
  generateCompanySummaryReport,
  getSlotsToCreate,
  createMissingSlotRows,
} from "./companyChecker";

// Fail Manager
export {
  FailureType,
  FailManagerConfig,
  FailureRecord,
  DEFAULT_FAIL_CONFIG,
  FailManager,
  globalFailManager,
} from "./failManager";

// Throttle Manager
export {
  ThrottleConfig,
  DEFAULT_THROTTLE_CONFIG,
  AGENT_THROTTLE_CONFIGS,
  ThrottleManager,
  AgentThrottleRegistry,
  globalThrottleRegistry,
} from "./throttleManager";

// Kill Switch
export {
  KillSwitchState,
  KillRecord,
  DEFAULT_KILL_SWITCH_STATE,
  KillSwitchManager,
  globalKillSwitchManager,
} from "./killSwitch";

// Agent Registry
export {
  AgentInstance,
  AgentMeta,
  AGENT_METADATA,
  AgentRegistry,
  globalAgentRegistry,
} from "./agentRegistry";

// Dispatcher
export {
  DispatcherConfig,
  DEFAULT_DISPATCHER_CONFIG,
  DispatchResult,
  BatchDispatchResult,
  dispatcher,
  batchDispatcher,
  getDispatchStats,
  createDryRunDispatcher,
} from "./dispatcher";
