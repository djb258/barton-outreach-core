/**
 * Talent Engine
 * =============
 * Slot-completion pipeline for the Talent Flow system.
 *
 * A SlotRow = Company + Slot (CEO/CFO/HR/Benefits) + Person
 *
 * Components:
 * - SlotRow: Core data model
 * - Checklist: Evaluates missing pieces
 * - Dispatcher: Routes rows to agents
 * - Throttle: Rate limiting
 * - KillSwitch: Agent blocking
 * - Agents: Processing stubs (to be implemented)
 */

// Data Models
export {
  SlotRow,
  SlotType,
  AgentType,
  AgentTask,
  AgentResult,
  ThrottleState,
  KillSwitchState,
  DispatchStatus,
  DispatchResult,
} from "./SlotRow";

// Checklist
export {
  evaluateChecklist,
  getMissingSummary,
  ChecklistResult,
} from "./checklist";

// Dispatcher
export {
  dispatcher,
  batchDispatch,
  getDispatchSummary,
} from "./dispatcher";

// Throttle
export {
  ThrottleManager,
  DEFAULT_THROTTLE_CONFIG,
} from "./throttle";

// Kill Switch
export {
  KillSwitchManager,
  DEFAULT_KILL_SWITCH_STATE,
} from "./killswitch";

// Agents
export {
  LinkedInFinderAgent,
  PublicScannerAgent,
  PatternAgent,
  EmailGeneratorAgent,
  TitleCompanyAgent,
  HashAgent,
} from "./agents";
