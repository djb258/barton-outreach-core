/**
 * FailureRouter
 * =============
 * Routes failed records to dedicated Neon failure tables (Garage → Bays model).
 *
 * Each agent has a dedicated "bay" (failure table):
 * - CompanyFuzzyMatchAgent → company_fuzzy_failures
 * - TitleCompanyAgent → person_company_mismatch
 * - PatternAgent → email_pattern_failures
 * - EmailGeneratorAgent → email_generation_failures
 * - LinkedInFinderAgent → linkedin_resolution_failures
 * - MissingSlotAgent → slot_discovery_failures
 * - DOLSyncAgent → dol_sync_failures
 * - Others → agent_failures (catch-all)
 *
 * Features:
 * - Automatic routing based on agent type
 * - Full row serialization for debugging
 * - In-memory fallback when Neon is unavailable
 * - Failure statistics and reporting
 * - Repair workflow support
 */

import {
  FailureBay,
  FailureNode,
  FailureAgentType,
  FailureRecord,
  FailureRoutingResult,
  FailureErrorType,
  CompanyFuzzyFailure,
  PersonCompanyMismatchFailure,
  EmailPatternFailure,
  EmailGenerationFailure,
  LinkedInResolutionFailure,
  SlotDiscoveryFailure,
  DOLSyncFailure,
  AgentFailure,
  ResumePoint,
  getFailureBayForAgent,
  getResumePointForBay,
  serializeSlotRow,
  FAILURE_RESUME_POINTS,
} from "../models/FailureRecord";
import { SlotRow } from "../models/SlotRow";
import { ThrottleError, isThrottleError, getFailureBayForThrottleError } from "./ThrottleError";
import { VendorId } from "./ThrottleManagerV2";

/**
 * Execution context for failure tracking.
 */
export interface ExecutionContext {
  /** Current node being executed */
  currentNode: FailureNode;
  /** Last agent that ran */
  lastAgent: FailureAgentType;
  /** Slot row being processed */
  slotRowId?: string;
  /** Timestamp when context started */
  startedAt: Date;
}

/**
 * Repair request for fixing and rerunning failures.
 */
export interface RepairRequest {
  /** Failure ID to repair */
  failureId: string;
  /** Bay containing the failure */
  bay: FailureBay;
  /** Fixed slot row data (optional) */
  fixedSlotRow?: Record<string, unknown>;
  /** Repair notes */
  notes?: string;
}

/**
 * Resume job for re-processing.
 */
export interface ResumeJob {
  /** Job ID */
  id: string;
  /** Failure ID being resumed */
  failureId: string;
  /** Bay the failure came from */
  sourceBay: FailureBay;
  /** Node to resume from */
  resumeNode: FailureNode;
  /** Agent to resume from */
  resumeAgent: FailureAgentType;
  /** Fixed slot row data */
  slotRow: SlotRow | Record<string, unknown>;
  /** Created timestamp */
  createdAt: Date;
  /** Status */
  status: "pending" | "in_progress" | "completed" | "failed";
  /** Attempt number */
  attempt: number;
}

/**
 * FailureRouter configuration.
 */
export interface FailureRouterConfig {
  /** Enable Neon persistence */
  enable_neon: boolean;
  /** Neon connection string */
  neon_connection_string?: string;
  /** Enable verbose logging */
  verbose: boolean;
  /** Schema name */
  schema: string;
  /** In-memory fallback when Neon unavailable */
  enable_memory_fallback: boolean;
  /** Maximum in-memory failures to store */
  max_memory_failures: number;
}

/**
 * Default configuration.
 */
export const DEFAULT_FAILURE_ROUTER_CONFIG: FailureRouterConfig = {
  enable_neon: false, // Start with in-memory for testing
  verbose: false,
  schema: "marketing",
  enable_memory_fallback: true,
  max_memory_failures: 10000,
};

/**
 * Failure statistics.
 */
export interface FailureStatistics {
  total_failures: number;
  by_bay: Record<FailureBay, number>;
  by_node: Record<FailureNode, number>;
  by_agent: Record<string, number>;
  by_error_type: Record<FailureErrorType, number>;
  by_vendor: Record<string, number>;
  throttle_failures: number;
  cost_failures: number;
  pending_repairs: number;
  last_failure_at: Date | null;
}

/**
 * FailureRouter - Routes failures to appropriate Neon tables.
 */
export class FailureRouter {
  private config: FailureRouterConfig;

  // In-memory storage (fallback or testing mode)
  private memoryStore: Map<FailureBay, FailureRecord[]> = new Map();

  // Resume job queue
  private resumeQueue: ResumeJob[] = [];

  // Statistics tracking
  private stats: FailureStatistics;

  // Current execution context
  private executionContext: ExecutionContext | null = null;

  // Neon client placeholder (would use pg or neon-serverless in production)
  private neonClient: any = null;

  constructor(config?: Partial<FailureRouterConfig>) {
    this.config = {
      ...DEFAULT_FAILURE_ROUTER_CONFIG,
      ...config,
    };

    // Initialize memory store for each bay
    this.initializeMemoryStore();

    // Initialize statistics
    this.stats = {
      total_failures: 0,
      by_bay: {} as Record<FailureBay, number>,
      by_node: {} as Record<FailureNode, number>,
      by_agent: {},
      by_error_type: {} as Record<FailureErrorType, number>,
      by_vendor: {},
      throttle_failures: 0,
      cost_failures: 0,
      pending_repairs: 0,
      last_failure_at: null,
    };

    if (this.config.verbose) {
      console.log("[FailureRouter] Initialized with config:", this.config);
    }
  }

  /**
   * Set the current execution context.
   * Call this when entering a node/agent.
   */
  setExecutionContext(node: FailureNode, agent: FailureAgentType, slotRowId?: string): void {
    this.executionContext = {
      currentNode: node,
      lastAgent: agent,
      slotRowId,
      startedAt: new Date(),
    };

    if (this.config.verbose) {
      console.log(`[FailureRouter] Context set: ${node} / ${agent}`);
    }
  }

  /**
   * Clear the execution context.
   */
  clearExecutionContext(): void {
    this.executionContext = null;
  }

  /**
   * Get the current execution context.
   */
  getExecutionContext(): ExecutionContext | null {
    return this.executionContext ? { ...this.executionContext } : null;
  }

  /**
   * Get the resume point for a failure bay.
   */
  getResumePoint(bay: FailureBay): ResumePoint {
    return getResumePointForBay(bay);
  }

  /**
   * Initialize memory store for all bays.
   */
  private initializeMemoryStore(): void {
    const bays: FailureBay[] = [
      "company_fuzzy_failures",
      "person_company_mismatch",
      "email_pattern_failures",
      "email_generation_failures",
      "linkedin_resolution_failures",
      "slot_discovery_failures",
      "dol_sync_failures",
      "agent_failures",
    ];

    for (const bay of bays) {
      this.memoryStore.set(bay, []);
    }
  }

  /**
   * Route a company fuzzy match failure.
   */
  async routeCompanyFuzzyFailure(
    failure: CompanyFuzzyFailure
  ): Promise<FailureRoutingResult> {
    return this.routeFailure("company_fuzzy_failures", failure, "CompanyFuzzyMatchAgent");
  }

  /**
   * Route a person-company mismatch failure.
   */
  async routePersonCompanyMismatch(
    failure: PersonCompanyMismatchFailure
  ): Promise<FailureRoutingResult> {
    return this.routeFailure("person_company_mismatch", failure, "TitleCompanyAgent");
  }

  /**
   * Route an email pattern failure.
   */
  async routeEmailPatternFailure(
    failure: EmailPatternFailure
  ): Promise<FailureRoutingResult> {
    return this.routeFailure("email_pattern_failures", failure, "PatternAgent");
  }

  /**
   * Route an email generation failure.
   */
  async routeEmailGenerationFailure(
    failure: EmailGenerationFailure
  ): Promise<FailureRoutingResult> {
    return this.routeFailure("email_generation_failures", failure, "EmailGeneratorAgent");
  }

  /**
   * Route a LinkedIn resolution failure.
   */
  async routeLinkedInResolutionFailure(
    failure: LinkedInResolutionFailure
  ): Promise<FailureRoutingResult> {
    return this.routeFailure("linkedin_resolution_failures", failure, "LinkedInFinderAgent");
  }

  /**
   * Route a slot discovery failure.
   */
  async routeSlotDiscoveryFailure(
    failure: SlotDiscoveryFailure
  ): Promise<FailureRoutingResult> {
    return this.routeFailure("slot_discovery_failures", failure, "MissingSlotAgent");
  }

  /**
   * Route a DOL sync failure.
   */
  async routeDOLSyncFailure(
    failure: DOLSyncFailure
  ): Promise<FailureRoutingResult> {
    return this.routeFailure("dol_sync_failures", failure, "DOLSyncAgent");
  }

  /**
   * Route a generic agent failure.
   */
  async routeAgentFailure(
    failure: AgentFailure
  ): Promise<FailureRoutingResult> {
    return this.routeFailure("agent_failures", failure, failure.agent_type);
  }

  /**
   * Auto-route failure based on agent type.
   */
  async autoRoute(
    agentType: string,
    failure: FailureRecord
  ): Promise<FailureRoutingResult> {
    const bay = getFailureBayForAgent(agentType);
    return this.routeFailure(bay, failure, agentType);
  }

  /**
   * Route a throttle error to the appropriate failure bay.
   */
  async routeThrottleError(
    error: ThrottleError,
    slotRow?: SlotRow | Record<string, unknown>
  ): Promise<FailureRoutingResult> {
    const bay = getFailureBayForThrottleError(error);
    const agentType = error.agentType || "Unknown";

    const failure: AgentFailure = {
      node_id: error.node || "COMPANY_HUB",
      agent_type: agentType,
      slot_row_id: error.slotRowId || null,
      slot_row: slotRow || null,
      task_id: null,
      error_type: this.mapThrottleCodeToErrorType(error.code),
      stack_trace: error.stack || null,
      metadata: error.toFailureData(),
      reason: error.message,
    };

    // Track throttle-specific stats
    this.stats.by_vendor[error.vendor] = (this.stats.by_vendor[error.vendor] || 0) + 1;

    if (["RATE_LIMIT", "COST_LIMIT", "BUDGET_EXCEEDED", "COOLDOWN_ACTIVE"].includes(error.code)) {
      this.stats.throttle_failures++;
    }

    if (["COST_LIMIT", "BUDGET_EXCEEDED", "COMPANY_BUDGET_EXCEEDED"].includes(error.code)) {
      this.stats.cost_failures++;
    }

    return this.routeFailure(bay, failure, agentType);
  }

  /**
   * Route any error (auto-detects throttle errors).
   */
  async routeError(
    error: Error,
    agentType: FailureAgentType,
    options?: {
      node?: FailureNode;
      slotRow?: SlotRow | Record<string, unknown>;
      slotRowId?: string;
      taskId?: string;
      metadata?: Record<string, unknown>;
    }
  ): Promise<FailureRoutingResult> {
    // Handle throttle errors specially
    if (isThrottleError(error)) {
      return this.routeThrottleError(error, options?.slotRow);
    }

    // Handle generic errors
    const failure: AgentFailure = {
      node_id: options?.node || this.executionContext?.currentNode || "COMPANY_HUB",
      agent_type: agentType,
      slot_row_id: options?.slotRowId || null,
      slot_row: options?.slotRow || null,
      task_id: options?.taskId || null,
      error_type: "unknown",
      stack_trace: error.stack || null,
      metadata: options?.metadata || {},
      reason: error.message,
    };

    return this.autoRoute(agentType, failure);
  }

  /**
   * Map throttle error code to FailureErrorType.
   */
  private mapThrottleCodeToErrorType(code: string): FailureErrorType {
    const mapping: Record<string, FailureErrorType> = {
      RATE_LIMIT: "rate_limit",
      COST_LIMIT: "cost_limit",
      BUDGET_EXCEEDED: "budget_exceeded",
      CIRCUIT_BREAKER: "circuit_breaker",
      COOLDOWN_ACTIVE: "cooldown",
      VENDOR_DISABLED: "vendor_disabled",
      COMPANY_BUDGET_EXCEEDED: "budget_exceeded",
      THROTTLE_BLOCKED: "throttle",
    };
    return mapping[code] || "unknown";
  }

  /**
   * Core routing method.
   */
  private async routeFailure(
    bay: FailureBay,
    failure: FailureRecord,
    agentType: string
  ): Promise<FailureRoutingResult> {
    try {
      // Add timestamp
      (failure as any).created_at = new Date();

      // Generate ID if not present
      if (!(failure as any).id) {
        (failure as any).id = this.generateId();
      }

      // Serialize SlotRow if present
      if ((failure as any).slot_row && typeof (failure as any).slot_row !== "object") {
        (failure as any).slot_row = serializeSlotRow((failure as any).slot_row);
      }

      // Add execution context tracking
      const resumePoint = getResumePointForBay(bay);
      (failure as any).resume_node = this.executionContext?.currentNode || resumePoint.resume_node;
      (failure as any).resume_agent = this.executionContext?.lastAgent || resumePoint.resume_agent;
      (failure as any).resolved = false;
      (failure as any).attempts = 0;

      if (this.config.verbose) {
        console.log(`[FailureRouter] Routing to bay: ${bay}`);
        console.log(`[FailureRouter] Agent: ${agentType}`);
        console.log(`[FailureRouter] Resume: ${(failure as any).resume_node} / ${(failure as any).resume_agent}`);
        console.log(`[FailureRouter] Reason: ${failure.reason}`);
      }

      // Extract error type from failure if present
      const errorType = (failure as any).error_type as FailureErrorType | undefined;

      // Try Neon first
      if (this.config.enable_neon && this.neonClient) {
        try {
          const recordId = await this.insertToNeon(bay, failure);
          this.updateStats(bay, agentType, errorType);
          return { success: true, bay, record_id: recordId };
        } catch (neonError) {
          if (this.config.verbose) {
            console.error(`[FailureRouter] Neon insert failed:`, neonError);
          }
          // Fall through to memory fallback
        }
      }

      // Memory fallback
      if (this.config.enable_memory_fallback) {
        this.insertToMemory(bay, failure);
        this.updateStats(bay, agentType, errorType);
        return { success: true, bay, record_id: (failure as any).id };
      }

      return { success: false, bay, error: "No storage available" };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "Unknown error";
      if (this.config.verbose) {
        console.error(`[FailureRouter] Routing failed:`, errorMsg);
      }
      return { success: false, bay, error: errorMsg };
    }
  }

  /**
   * Insert failure to Neon database.
   */
  private async insertToNeon(bay: FailureBay, failure: FailureRecord): Promise<string> {
    // This would use the actual Neon client in production
    // For now, throw to trigger memory fallback
    throw new Error("Neon client not initialized");
  }

  /**
   * Insert failure to memory store.
   */
  private insertToMemory(bay: FailureBay, failure: FailureRecord): void {
    const bayStore = this.memoryStore.get(bay) || [];

    // Trim if exceeding max
    if (bayStore.length >= this.config.max_memory_failures) {
      bayStore.shift(); // Remove oldest
    }

    bayStore.push(failure);
    this.memoryStore.set(bay, bayStore);
  }

  /**
   * Update statistics.
   */
  private updateStats(bay: FailureBay, agentType: string, errorType?: FailureErrorType): void {
    this.stats.total_failures++;
    this.stats.by_bay[bay] = (this.stats.by_bay[bay] || 0) + 1;
    this.stats.by_agent[agentType] = (this.stats.by_agent[agentType] || 0) + 1;
    this.stats.pending_repairs++;
    this.stats.last_failure_at = new Date();

    // Track error type if provided
    if (errorType) {
      this.stats.by_error_type[errorType] = (this.stats.by_error_type[errorType] || 0) + 1;
    }

    // Infer node from agent type
    const nodeMap: Record<string, FailureNode> = {
      CompanyFuzzyMatchAgent: "COMPANY_HUB",
      PatternAgent: "COMPANY_HUB",
      EmailGeneratorAgent: "COMPANY_HUB",
      MissingSlotAgent: "COMPANY_HUB",
      TitleCompanyAgent: "PEOPLE_NODE",
      PeopleFuzzyMatchAgent: "PEOPLE_NODE",
      LinkedInFinderAgent: "PEOPLE_NODE",
      PublicScannerAgent: "PEOPLE_NODE",
      MovementHashAgent: "PEOPLE_NODE",
      DOLSyncAgent: "DOL_NODE",
      BITScoreAgent: "BIT_NODE",
    };
    const node = nodeMap[agentType] || "COMPANY_HUB";
    this.stats.by_node[node] = (this.stats.by_node[node] || 0) + 1;
  }

  /**
   * Generate a unique ID.
   */
  private generateId(): string {
    return `fail_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get failures from a specific bay.
   */
  getFailures(bay: FailureBay): FailureRecord[] {
    return [...(this.memoryStore.get(bay) || [])];
  }

  /**
   * Get all failures across all bays.
   */
  getAllFailures(): Map<FailureBay, FailureRecord[]> {
    return new Map(this.memoryStore);
  }

  /**
   * Get unrepaired failures from a bay.
   */
  getUnrepairedFailures(bay: FailureBay): FailureRecord[] {
    const failures = this.memoryStore.get(bay) || [];
    return failures.filter((f) => !(f as any).repaired_at);
  }

  /**
   * Mark a failure as repaired (legacy method - use markResolved instead).
   * @deprecated Use markResolved instead
   */
  markRepaired(bay: FailureBay, failureId: string, notes?: string): boolean {
    return this.markResolved(bay, failureId, notes);
  }

  /**
   * Mark a failure as resolved.
   */
  markResolved(bay: FailureBay, failureId: string, notes?: string): boolean {
    const failures = this.memoryStore.get(bay) || [];
    const failure = failures.find((f) => (f as any).id === failureId);

    if (failure) {
      (failure as any).resolved = true;
      (failure as any).resolved_at = new Date();
      (failure as any).repaired_at = new Date(); // Legacy field
      (failure as any).repair_notes = notes || null;
      this.stats.pending_repairs--;
      return true;
    }

    return false;
  }

  /**
   * Get a failure by ID from any bay.
   */
  getFailureById(failureId: string): { failure: FailureRecord; bay: FailureBay } | null {
    for (const [bay, failures] of this.memoryStore) {
      const failure = failures.find((f) => (f as any).id === failureId);
      if (failure) {
        return { failure, bay };
      }
    }
    return null;
  }

  /**
   * Update fixed_slot_row for a failure (pre-resume fix).
   */
  updateFixedSlotRow(
    bay: FailureBay,
    failureId: string,
    fixedSlotRow: Record<string, unknown>
  ): boolean {
    const failures = this.memoryStore.get(bay) || [];
    const failure = failures.find((f) => (f as any).id === failureId);

    if (failure) {
      (failure as any).fixed_slot_row = fixedSlotRow;
      return true;
    }

    return false;
  }

  /**
   * Increment attempt count for a failure.
   */
  incrementAttempt(bay: FailureBay, failureId: string): number {
    const failures = this.memoryStore.get(bay) || [];
    const failure = failures.find((f) => (f as any).id === failureId);

    if (failure) {
      (failure as any).attempts = ((failure as any).attempts || 0) + 1;
      (failure as any).last_attempt_at = new Date();
      return (failure as any).attempts;
    }

    return -1;
  }

  /**
   * Create a resume job from a failure.
   */
  createResumeJob(
    bay: FailureBay,
    failureId: string,
    fixedSlotRow?: Record<string, unknown>
  ): ResumeJob | null {
    const failures = this.memoryStore.get(bay) || [];
    const failure = failures.find((f) => (f as any).id === failureId);

    if (!failure) {
      return null;
    }

    const resumePoint = getResumePointForBay(bay);
    const slotRow = fixedSlotRow || (failure as any).fixed_slot_row || (failure as any).slot_row;

    if (!slotRow) {
      return null;
    }

    const job: ResumeJob = {
      id: `resume_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      failureId,
      sourceBay: bay,
      resumeNode: (failure as any).resume_node || resumePoint.resume_node,
      resumeAgent: (failure as any).resume_agent || resumePoint.resume_agent,
      slotRow,
      createdAt: new Date(),
      status: "pending",
      attempt: ((failure as any).attempts || 0) + 1,
    };

    this.resumeQueue.push(job);
    this.incrementAttempt(bay, failureId);

    if (this.config.verbose) {
      console.log(`[FailureRouter] Resume job created: ${job.id}`);
      console.log(`[FailureRouter] Resume from: ${job.resumeNode} / ${job.resumeAgent}`);
    }

    return job;
  }

  /**
   * Get pending resume jobs.
   */
  getPendingResumeJobs(): ResumeJob[] {
    return this.resumeQueue.filter((j) => j.status === "pending");
  }

  /**
   * Get next pending resume job.
   */
  getNextResumeJob(): ResumeJob | null {
    return this.resumeQueue.find((j) => j.status === "pending") || null;
  }

  /**
   * Update resume job status.
   */
  updateResumeJobStatus(
    jobId: string,
    status: ResumeJob["status"]
  ): boolean {
    const job = this.resumeQueue.find((j) => j.id === jobId);
    if (job) {
      job.status = status;

      // If completed, mark the original failure as resolved
      if (status === "completed") {
        this.markResolved(job.sourceBay, job.failureId, `Resolved via resume job ${jobId}`);
      }

      return true;
    }
    return false;
  }

  /**
   * Get unresolved failures from a bay.
   */
  getUnresolvedFailures(bay: FailureBay): FailureRecord[] {
    const failures = this.memoryStore.get(bay) || [];
    return failures.filter((f) => !(f as any).resolved);
  }

  /**
   * Get all unresolved failures across all bays.
   */
  getAllUnresolvedFailures(): Map<FailureBay, FailureRecord[]> {
    const result = new Map<FailureBay, FailureRecord[]>();
    for (const [bay, failures] of this.memoryStore) {
      const unresolved = failures.filter((f) => !(f as any).resolved);
      if (unresolved.length > 0) {
        result.set(bay, unresolved);
      }
    }
    return result;
  }

  /**
   * Get failures that can be resumed (have slot_row or fixed_slot_row).
   */
  getResumableFailures(bay: FailureBay): FailureRecord[] {
    const failures = this.memoryStore.get(bay) || [];
    return failures.filter(
      (f) => !(f as any).resolved && ((f as any).slot_row || (f as any).fixed_slot_row)
    );
  }

  /**
   * Get resume queue statistics.
   */
  getResumeQueueStats(): {
    total: number;
    pending: number;
    in_progress: number;
    completed: number;
    failed: number;
  } {
    return {
      total: this.resumeQueue.length,
      pending: this.resumeQueue.filter((j) => j.status === "pending").length,
      in_progress: this.resumeQueue.filter((j) => j.status === "in_progress").length,
      completed: this.resumeQueue.filter((j) => j.status === "completed").length,
      failed: this.resumeQueue.filter((j) => j.status === "failed").length,
    };
  }

  /**
   * Get failure statistics.
   */
  getStatistics(): FailureStatistics {
    return { ...this.stats };
  }

  /**
   * Generate failure report.
   */
  generateReport(): string {
    const lines: string[] = [];

    lines.push("=".repeat(60));
    lines.push("FAILURE ROUTING REPORT (GARAGE → BAYS)");
    lines.push("=".repeat(60));
    lines.push("");

    lines.push("SUMMARY");
    lines.push("-".repeat(40));
    lines.push(`  Total Failures:   ${this.stats.total_failures}`);
    lines.push(`  Pending Repairs:  ${this.stats.pending_repairs}`);
    lines.push(`  Throttle Failures: ${this.stats.throttle_failures}`);
    lines.push(`  Cost Failures:    ${this.stats.cost_failures}`);
    lines.push(`  Last Failure:     ${this.stats.last_failure_at?.toISOString() || "N/A"}`);
    lines.push("");

    lines.push("FAILURES BY BAY");
    lines.push("-".repeat(40));
    for (const [bay, count] of Object.entries(this.stats.by_bay)) {
      if (count > 0) {
        lines.push(`  ${bay}: ${count}`);
      }
    }
    lines.push("");

    lines.push("FAILURES BY NODE");
    lines.push("-".repeat(40));
    for (const [node, count] of Object.entries(this.stats.by_node)) {
      if (count > 0) {
        lines.push(`  ${node}: ${count}`);
      }
    }
    lines.push("");

    lines.push("FAILURES BY AGENT");
    lines.push("-".repeat(40));
    for (const [agent, count] of Object.entries(this.stats.by_agent)) {
      if (count > 0) {
        lines.push(`  ${agent}: ${count}`);
      }
    }
    lines.push("");

    lines.push("FAILURES BY ERROR TYPE");
    lines.push("-".repeat(40));
    for (const [errorType, count] of Object.entries(this.stats.by_error_type)) {
      if (count > 0) {
        lines.push(`  ${errorType}: ${count}`);
      }
    }
    lines.push("");

    lines.push("FAILURES BY VENDOR");
    lines.push("-".repeat(40));
    for (const [vendor, count] of Object.entries(this.stats.by_vendor)) {
      if (count > 0) {
        lines.push(`  ${vendor}: ${count}`);
      }
    }
    lines.push("");

    lines.push("=".repeat(60));

    return lines.join("\n");
  }

  /**
   * Export failures to JSON.
   */
  exportToJSON(): string {
    const data: Record<string, FailureRecord[]> = {};
    for (const [bay, failures] of this.memoryStore) {
      data[bay] = failures;
    }
    return JSON.stringify(data, null, 2);
  }

  /**
   * Export failures to CSV (for a specific bay).
   */
  exportToCSV(bay: FailureBay): string {
    const failures = this.memoryStore.get(bay) || [];
    if (failures.length === 0) {
      return "";
    }

    // Get headers from first record
    const headers = Object.keys(failures[0]).filter(
      (k) => !["slot_row", "candidates", "metadata", "api_response", "validation_flags"].includes(k)
    );

    const rows = failures.map((f) =>
      headers.map((h) => {
        const val = (f as any)[h];
        if (val === null || val === undefined) return "";
        if (typeof val === "object") return JSON.stringify(val);
        return String(val);
      })
    );

    return [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
  }

  /**
   * Clear all failures (for testing).
   */
  clear(): void {
    this.initializeMemoryStore();
    this.resumeQueue = [];
    this.executionContext = null;
    this.stats = {
      total_failures: 0,
      by_bay: {} as Record<FailureBay, number>,
      by_node: {} as Record<FailureNode, number>,
      by_agent: {},
      by_error_type: {} as Record<FailureErrorType, number>,
      by_vendor: {},
      throttle_failures: 0,
      cost_failures: 0,
      pending_repairs: 0,
      last_failure_at: null,
    };
  }

  /**
   * Get throttle-specific statistics.
   */
  getThrottleStatistics(): {
    throttle_failures: number;
    cost_failures: number;
    by_vendor: Record<string, number>;
    by_error_type: Record<string, number>;
  } {
    return {
      throttle_failures: this.stats.throttle_failures,
      cost_failures: this.stats.cost_failures,
      by_vendor: { ...this.stats.by_vendor },
      by_error_type: { ...this.stats.by_error_type },
    };
  }

  /**
   * Clear resume queue (for testing).
   */
  clearResumeQueue(): void {
    this.resumeQueue = [];
  }

  /**
   * Get bay count.
   */
  getBayCount(bay: FailureBay): number {
    return (this.memoryStore.get(bay) || []).length;
  }

  /**
   * Check if router has any failures.
   */
  hasFailures(): boolean {
    return this.stats.total_failures > 0;
  }

  /**
   * Get configuration.
   */
  getConfig(): FailureRouterConfig {
    return { ...this.config };
  }

  /**
   * Update configuration.
   */
  updateConfig(config: Partial<FailureRouterConfig>): void {
    this.config = { ...this.config, ...config };
  }
}

/**
 * Global failure router instance.
 */
export const globalFailureRouter = new FailureRouter();
