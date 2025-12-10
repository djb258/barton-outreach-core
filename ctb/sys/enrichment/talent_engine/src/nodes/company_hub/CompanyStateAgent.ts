/**
 * CompanyStateAgent
 * =================
 * Company Hub Node: Company State Evaluation Agent
 *
 * Evaluates overall company state and readiness for downstream processing.
 * Central coordinator for Company Hub operations.
 *
 * Hub-and-Spoke Role:
 * - MASTER AGENT of COMPANY_HUB
 * - Evaluates company identity completeness
 * - Gates access to People, DOL, and BIT nodes
 * - Ensures hub anchor exists before spoke processing
 *
 * Features:
 * - Company identity validation (company_id, domain, email_pattern)
 * - Slot completeness evaluation
 * - Readiness scoring for downstream nodes
 * - State transition management
 *
 * TODO: Implement full state machine logic
 * TODO: Add company identity enrichment triggers
 * TODO: Integrate with Neon database for persistence
 */

import { AgentResult, SlotRow, SlotType, ALL_SLOT_TYPES } from "../../models/SlotRow";
import { CompanyStateResult, evaluateCompanyState } from "../../models/CompanyState";

/**
 * Company identity status.
 */
export type CompanyIdentityStatus =
  | "COMPLETE"       // All identity fields present
  | "PARTIAL"        // Some identity fields missing
  | "MISSING"        // No identity data
  | "INVALID";       // Identity data invalid

/**
 * Company readiness level for downstream processing.
 */
export type CompanyReadiness =
  | "READY"          // Ready for all downstream nodes
  | "PARTIAL"        // Ready for some nodes
  | "BLOCKED"        // Cannot proceed to any node
  | "NEEDS_REVIEW";  // Manual review required

/**
 * Agent configuration.
 */
export interface CompanyStateAgentConfig {
  /** Enable verbose logging */
  verbose: boolean;
  /** Required fields for COMPLETE identity status */
  required_identity_fields: string[];
  /** Required fields for PARTIAL identity status */
  partial_identity_fields: string[];
  /** Minimum slot fill rate for READY status (0-1) */
  min_slot_fill_rate: number;
  /** Slot types to consider for readiness */
  readiness_slot_types: SlotType[];
}

/**
 * Default configuration.
 */
export const DEFAULT_COMPANY_STATE_CONFIG: CompanyStateAgentConfig = {
  verbose: false,
  required_identity_fields: ["company_id", "company_name", "domain", "email_pattern"],
  partial_identity_fields: ["company_id", "company_name"],
  min_slot_fill_rate: 0.5, // 50% slots filled for READY
  readiness_slot_types: ALL_SLOT_TYPES,
};

/**
 * Task for CompanyStateAgent.
 */
export interface CompanyStateTask {
  task_id: string;
  company_id: string;
  company_name: string;
  company_domain?: string | null;
  email_pattern?: string | null;
  existing_rows: SlotRow[];
}

/**
 * Result from CompanyStateAgent.
 */
export interface CompanyStateEvaluation {
  company_id: string;
  company_name: string;
  identity_status: CompanyIdentityStatus;
  readiness: CompanyReadiness;
  slot_fill_rate: number;
  filled_slots: SlotType[];
  missing_slots: SlotType[];
  identity_gaps: string[];
  downstream_gates: {
    people_node: boolean;
    dol_node: boolean;
    bit_node: boolean;
  };
  recommendations: string[];
}

/**
 * CompanyStateAgent - Evaluates company state for hub-and-spoke routing.
 *
 * Execution Flow:
 * 1. Validate company identity fields
 * 2. Evaluate slot completeness
 * 3. Calculate readiness score
 * 4. Determine downstream node gates
 * 5. Generate recommendations for missing data
 */
export class CompanyStateAgent {
  private config: CompanyStateAgentConfig;

  constructor(config?: Partial<CompanyStateAgentConfig>) {
    this.config = {
      ...DEFAULT_COMPANY_STATE_CONFIG,
      ...config,
    };
  }

  /**
   * Run the company state evaluation.
   */
  async run(task: CompanyStateTask): Promise<AgentResult> {
    try {
      // Validate input
      if (!task.company_id || !task.company_name) {
        return this.createResult(task, false, {}, "company_id and company_name are required");
      }

      if (this.config.verbose) {
        console.log(`[CompanyStateAgent] Evaluating state for: ${task.company_name}`);
      }

      // Step 1: Evaluate identity status
      const identityStatus = this.evaluateIdentityStatus(task);
      const identityGaps = this.getIdentityGaps(task);

      // Step 2: Evaluate slot completeness
      const slotState = evaluateCompanyState(task.company_id, task.company_name, task.existing_rows);
      const slotFillRate = this.calculateSlotFillRate(slotState);

      // Step 3: Calculate readiness
      const readiness = this.calculateReadiness(identityStatus, slotFillRate);

      // Step 4: Determine downstream gates
      const downstreamGates = this.evaluateDownstreamGates(identityStatus, slotFillRate, task);

      // Step 5: Generate recommendations
      const recommendations = this.generateRecommendations(
        identityStatus,
        identityGaps,
        slotState.missing_slots,
        readiness
      );

      const evaluation: CompanyStateEvaluation = {
        company_id: task.company_id,
        company_name: task.company_name,
        identity_status: identityStatus,
        readiness,
        slot_fill_rate: slotFillRate,
        filled_slots: slotState.filled_slots,
        missing_slots: slotState.missing_slots,
        identity_gaps: identityGaps,
        downstream_gates: downstreamGates,
        recommendations,
      };

      return this.createResult(task, true, evaluation);
    } catch (error) {
      return this.createResult(
        task,
        false,
        {},
        error instanceof Error ? error.message : "Unknown error occurred"
      );
    }
  }

  /**
   * Evaluate company identity status.
   */
  private evaluateIdentityStatus(task: CompanyStateTask): CompanyIdentityStatus {
    const hasRequired = this.config.required_identity_fields.every((field) => {
      const value = (task as Record<string, unknown>)[field];
      return value !== null && value !== undefined && value !== "";
    });

    if (hasRequired) {
      return "COMPLETE";
    }

    const hasPartial = this.config.partial_identity_fields.every((field) => {
      const value = (task as Record<string, unknown>)[field];
      return value !== null && value !== undefined && value !== "";
    });

    if (hasPartial) {
      return "PARTIAL";
    }

    return "MISSING";
  }

  /**
   * Get list of missing identity fields.
   */
  private getIdentityGaps(task: CompanyStateTask): string[] {
    const gaps: string[] = [];

    for (const field of this.config.required_identity_fields) {
      const value = (task as Record<string, unknown>)[field];
      if (value === null || value === undefined || value === "") {
        gaps.push(field);
      }
    }

    return gaps;
  }

  /**
   * Calculate slot fill rate.
   */
  private calculateSlotFillRate(slotState: CompanyStateResult): number {
    const relevantSlots = this.config.readiness_slot_types;
    const filledCount = slotState.filled_slots.filter((s) => relevantSlots.includes(s)).length;
    return filledCount / relevantSlots.length;
  }

  /**
   * Calculate overall readiness.
   */
  private calculateReadiness(
    identityStatus: CompanyIdentityStatus,
    slotFillRate: number
  ): CompanyReadiness {
    // BLOCKED if identity is missing
    if (identityStatus === "MISSING" || identityStatus === "INVALID") {
      return "BLOCKED";
    }

    // READY if identity complete and slots filled
    if (identityStatus === "COMPLETE" && slotFillRate >= this.config.min_slot_fill_rate) {
      return "READY";
    }

    // PARTIAL if identity partial or low slot fill
    if (identityStatus === "PARTIAL" || slotFillRate < this.config.min_slot_fill_rate) {
      return "PARTIAL";
    }

    return "NEEDS_REVIEW";
  }

  /**
   * Evaluate which downstream nodes can be accessed.
   */
  private evaluateDownstreamGates(
    identityStatus: CompanyIdentityStatus,
    slotFillRate: number,
    task: CompanyStateTask
  ): { people_node: boolean; dol_node: boolean; bit_node: boolean } {
    // People Node: Requires company_id and company_name
    const peopleNodeGate = identityStatus !== "MISSING" && identityStatus !== "INVALID";

    // DOL Node: Requires company_id (for EIN matching)
    const dolNodeGate = identityStatus !== "MISSING" && identityStatus !== "INVALID";

    // BIT Node: Requires company anchor + some slots filled
    const bitNodeGate =
      identityStatus === "COMPLETE" ||
      (identityStatus === "PARTIAL" && slotFillRate > 0);

    return {
      people_node: peopleNodeGate,
      dol_node: dolNodeGate,
      bit_node: bitNodeGate,
    };
  }

  /**
   * Generate recommendations for improving company state.
   */
  private generateRecommendations(
    identityStatus: CompanyIdentityStatus,
    identityGaps: string[],
    missingSlots: SlotType[],
    readiness: CompanyReadiness
  ): string[] {
    const recommendations: string[] = [];

    // Identity recommendations
    if (identityGaps.includes("domain")) {
      recommendations.push("Run domain discovery to find company website");
    }
    if (identityGaps.includes("email_pattern")) {
      recommendations.push("Run PatternAgent to discover email pattern");
    }

    // Slot recommendations
    if (missingSlots.length > 0) {
      recommendations.push(`Discover executives for missing slots: ${missingSlots.join(", ")}`);
    }

    // Readiness recommendations
    if (readiness === "BLOCKED") {
      recommendations.push("CRITICAL: Company identity must be established before processing");
    }
    if (readiness === "PARTIAL") {
      recommendations.push("Complete company identity for full downstream access");
    }

    return recommendations;
  }

  /**
   * Quick check if company can proceed to a specific node.
   */
  canProceedToNode(
    task: CompanyStateTask,
    targetNode: "people" | "dol" | "bit"
  ): boolean {
    const identityStatus = this.evaluateIdentityStatus(task);
    const slotState = evaluateCompanyState(task.company_id, task.company_name, task.existing_rows);
    const slotFillRate = this.calculateSlotFillRate(slotState);
    const gates = this.evaluateDownstreamGates(identityStatus, slotFillRate, task);

    switch (targetNode) {
      case "people":
        return gates.people_node;
      case "dol":
        return gates.dol_node;
      case "bit":
        return gates.bit_node;
      default:
        return false;
    }
  }

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: CompanyStateTask,
    success: boolean,
    data: Record<string, unknown>,
    error?: string
  ): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "CompanyStateAgent",
      slot_row_id: task.company_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }

  /**
   * Get current configuration.
   */
  getConfig(): CompanyStateAgentConfig {
    return { ...this.config };
  }

  /**
   * Update configuration.
   */
  updateConfig(config: Partial<CompanyStateAgentConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
