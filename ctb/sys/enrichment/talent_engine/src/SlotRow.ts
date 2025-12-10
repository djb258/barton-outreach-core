/**
 * SlotRow Data Model
 * ==================
 * Core data structure for the Talent Engine slot-completion pipeline.
 *
 * A SlotRow represents: Company + Slot (CEO/CFO/HR/Benefits) + Person
 * Each slot must complete a checklist before exiting the pipeline.
 */

/**
 * Valid slot types for company positions.
 */
export type SlotType = "CEO" | "CFO" | "HR" | "BENEFITS";

/**
 * Agent types that can process slot rows.
 */
export type AgentType =
  | "LinkedInFinderAgent"
  | "PublicScannerAgent"
  | "PatternAgent"
  | "EmailGeneratorAgent"
  | "TitleCompanyAgent"
  | "HashAgent";

/**
 * Core SlotRow class representing a slot-completion pipeline row.
 */
export class SlotRow {
  id: string;
  company_name: string;
  slot_type: SlotType;
  person_name: string | null;
  linkedin_url: string | null;
  public_accessible: boolean | null;
  email: string | null;
  email_pattern: string | null;
  email_verified: boolean | null;
  current_title: string | null;
  current_company: string | null;
  movement_hash: string | null;
  slot_complete: boolean;
  last_updated: Date;

  constructor(init: Partial<SlotRow> & { id: string; company_name: string; slot_type: SlotType }) {
    this.id = init.id;
    this.company_name = init.company_name;
    this.slot_type = init.slot_type;
    this.person_name = init.person_name ?? null;
    this.linkedin_url = init.linkedin_url ?? null;
    this.public_accessible = init.public_accessible ?? null;
    this.email = init.email ?? null;
    this.email_pattern = init.email_pattern ?? null;
    this.email_verified = init.email_verified ?? null;
    this.current_title = init.current_title ?? null;
    this.current_company = init.current_company ?? null;
    this.movement_hash = init.movement_hash ?? null;
    this.slot_complete = init.slot_complete ?? false;
    this.last_updated = init.last_updated ?? new Date();
  }

  /**
   * Update the row and set last_updated timestamp.
   */
  update(fields: Partial<SlotRow>): void {
    Object.assign(this, fields);
    this.last_updated = new Date();
  }
}

/**
 * Task sent to an agent for processing.
 */
export interface AgentTask {
  task_id: string;
  agent_type: AgentType;
  slot_row_id: string;
  company_name: string;
  slot_type: SlotType;
  person_name: string | null;
  linkedin_url: string | null;
  context: Record<string, unknown>;
  created_at: Date;
}

/**
 * Result returned by an agent after processing.
 */
export interface AgentResult {
  task_id: string;
  agent_type: AgentType;
  slot_row_id: string;
  success: boolean;
  data: Record<string, unknown>;
  error: string | null;
  completed_at: Date;
}

/**
 * State for throttle tracking.
 */
export interface ThrottleState {
  max_calls_per_minute: number;
  max_calls_per_day: number;
  calls_this_minute: number;
  calls_today: number;
  last_reset_minute: Date;
  last_reset_day: Date;
}

/**
 * State for kill switches per agent.
 */
export interface KillSwitchState {
  LinkedInFinderAgent: boolean;
  PublicScannerAgent: boolean;
  PatternAgent: boolean;
  EmailGeneratorAgent: boolean;
  TitleCompanyAgent: boolean;
  HashAgent: boolean;
}

/**
 * Dispatcher result status.
 */
export type DispatchStatus =
  | "ROUTED"
  | "THROTTLED"
  | "KILLED"
  | "COMPLETED"
  | "NO_ACTION";

/**
 * Result from dispatcher routing.
 */
export interface DispatchResult {
  status: DispatchStatus;
  agent_type: AgentType | null;
  task: AgentTask | null;
  reason: string;
}
