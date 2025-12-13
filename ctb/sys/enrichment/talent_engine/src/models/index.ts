/**
 * Models Index
 * ============
 * Re-exports all data models.
 */

export {
  SlotRow,
  SlotType,
  ALL_SLOT_TYPES,
  AgentType,
  AgentTask,
  AgentResult,
  DispatchStatus,
  DispatchResult,
  FuzzyMatchStatus,
  DEFAULT_SLOT_COST_LIMIT,
  createSlotRow,
} from "./SlotRow";

export {
  CompanyState,
  CompanyStateResult,
  SlotStatus,
  SlotState,
  evaluateCompanyState,
} from "./CompanyState";

export {
  AgentEventLog,
  AgentEvent,
  AgentEventType,
  EventSeverity,
  EmailSkipReason,
  EmailSkippedPayload,
  CompanyValidatedPayload,
  PersonValidatedPayload,
  globalEventLog,
} from "./AgentEventLog";

export {
  FailureBay,
  FailureNode,
  FailureAgentType,
  FailureErrorType,
  BaseFailureRecord,
  CompanyFuzzyFailure,
  PersonCompanyMismatchFailure,
  EmailPatternFailure,
  EmailGenerationFailure,
  LinkedInResolutionFailure,
  SlotDiscoveryFailure,
  DOLSyncFailure,
  AgentFailure,
  FailureRecord,
  FailureRoutingResult,
  ResumePoint,
  AGENT_FAILURE_BAY_MAP,
  FAILURE_RESUME_POINTS,
  getFailureBayForAgent,
  getResumePointForBay,
  createCompanyFuzzyFailure,
  createPersonCompanyMismatchFailure,
  createEmailPatternFailure,
  createEmailGenerationFailure,
  createLinkedInResolutionFailure,
  createSlotDiscoveryFailure,
  createDOLSyncFailure,
  createAgentFailure,
  serializeSlotRow,
} from "./FailureRecord";
