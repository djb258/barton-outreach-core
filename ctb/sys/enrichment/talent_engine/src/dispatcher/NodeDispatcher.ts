/**
 * NodeDispatcher
 * ==============
 * Hub-and-Spoke Node Routing Engine
 *
 * Central dispatcher that routes processing through nodes in the correct order:
 * Company Hub → People Node → DOL Node → BIT Node
 *
 * Features:
 * - Node-based routing (replaces layer-based dispatcher)
 * - Kill switches per node
 * - Throttle management
 * - Cost tracking and budgeting
 * - FailManager integration
 * - Parallel and sequential execution modes
 *
 * Architecture:
 * ```
 *                    ┌─────────────────┐
 *                    │  NodeDispatcher │
 *                    └────────┬────────┘
 *                             │
 *         ┌───────────────────┼───────────────────┐
 *         │                   │                   │
 *         ▼                   ▼                   ▼
 * ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
 * │  COMPANY_HUB  │──▶│  PEOPLE_NODE  │──▶│   DOL_NODE    │
 * │   (Phase 1)   │   │   (Phase 2)   │   │   (Phase 3)   │
 * └───────────────┘   └───────────────┘   └───────────────┘
 *                             │                   │
 *                             └─────────┬─────────┘
 *                                       ▼
 *                             ┌───────────────┐
 *                             │   BIT_NODE    │
 *                             │   (Phase 4)   │
 *                             └───────────────┘
 * ```
 */

import { SlotRow, AgentResult, SlotType } from "../models/SlotRow";
import { CompanyStateResult } from "../models/CompanyState";
import {
  FailureRouter,
  globalFailureRouter,
  FailureStatistics,
  ResumeJob,
  ExecutionContext,
} from "../services/FailureRouter";
import { FailureNode, FailureAgentType } from "../models/FailureRecord";
import {
  ThrottleManagerV2,
  globalThrottleManager,
  ThrottleCheckResult,
} from "../services/ThrottleManagerV2";
import {
  VENDOR_BUDGETS,
  AGENT_VENDOR_MAP,
  AGENT_COST_ESTIMATES,
  getVendorForAgent,
  getCostForAgent,
} from "../config/vendor_budgets";
import {
  validateDependencies,
  DependencyValidationError,
  DEPENDENCY_GRAPH,
} from "../config/dependency_graph";

// Import node agents
import {
  CompanyFuzzyMatchAgent,
  CompanyStateAgent,
  PatternAgent,
  MissingSlotAgent,
  EmailGeneratorAgent,
} from "../nodes/company_hub";

import {
  LinkedInFinderAgent,
  PublicScannerAgent,
  TitleCompanyAgent,
  MovementHashAgent,
  PeopleFuzzyMatchAgent,
} from "../nodes/people_node";

import {
  DOLSyncAgent,
  RenewalParserAgent,
  CarrierNormalizerAgent,
  Form5500Filing,
} from "../nodes/dol_node";

import {
  BITScoreAgent,
  ChurnDetectorAgent,
  RenewalIntentAgent,
  IntentSignals,
  MovementEvent,
} from "../nodes/bit_node";

/**
 * Node identifiers.
 */
export type NodeId = "COMPANY_HUB" | "PEOPLE_NODE" | "DOL_NODE" | "BIT_NODE";

/**
 * Node status.
 */
export type NodeStatus = "IDLE" | "RUNNING" | "COMPLETED" | "FAILED" | "KILLED";

/**
 * Kill switch configuration.
 */
export interface KillSwitches {
  COMPANY_HUB: boolean;
  PEOPLE_NODE: boolean;
  DOL_NODE: boolean;
  BIT_NODE: boolean;
}

/**
 * Throttle configuration.
 */
export interface ThrottleConfig {
  /** Requests per minute per node */
  requests_per_minute: number;
  /** Concurrent requests per node */
  max_concurrent: number;
  /** Delay between requests (ms) */
  delay_ms: number;
}

/**
 * Cost tracking.
 */
export interface CostTracker {
  COMPANY_HUB: number;
  PEOPLE_NODE: number;
  DOL_NODE: number;
  BIT_NODE: number;
  total: number;
}

/**
 * Node execution result.
 */
export interface NodeExecutionResult {
  node_id: NodeId;
  status: NodeStatus;
  started_at: Date;
  completed_at: Date | null;
  records_processed: number;
  records_failed: number;
  records_skipped: number;
  cost_incurred: number;
  errors: string[];
  results: AgentResult[];
  /** Validation tracking */
  validation_summary?: ValidationSummary;
}

/**
 * Validation summary for tracking Golden Rule enforcement.
 */
export interface ValidationSummary {
  company_valid: boolean;
  company_invalid_reason: string | null;
  people_validated: number;
  people_valid: number;
  people_invalid: number;
  emails_generated: number;
  emails_skipped: number;
  skip_reasons: Record<string, number>;
}

/**
 * Resume execution result.
 */
export interface ResumeExecutionResult {
  success: boolean;
  jobId: string;
  failureId: string;
  sourceBay: string;
  resumeNode: string;
  resumeAgent: string;
  nodeResults: NodeExecutionResult[];
  error?: string;
  completedAt: Date | null;
}

/**
 * Dispatcher configuration.
 */
export interface NodeDispatcherConfig {
  /** Enable verbose logging */
  verbose: boolean;
  /** Kill switches per node */
  kill_switches: KillSwitches;
  /** Throttle config per node */
  throttle: Record<NodeId, ThrottleConfig>;
  /** Maximum cost budget */
  max_cost_budget: number;
  /** Enable parallel execution where possible */
  enable_parallel: boolean;
  /** Retry failed operations */
  retry_on_failure: boolean;
  /** Max retries */
  max_retries: number;
  /** Mock mode for testing */
  mock_mode: boolean;
  /** Failure router for routing failures to Neon tables */
  failure_router?: FailureRouter;
  /** Throttle manager for vendor-level rate/cost limiting */
  throttle_manager?: ThrottleManagerV2;
  /** Enable dependency graph enforcement */
  enforce_dependencies?: boolean;
}

/**
 * Default throttle configuration.
 */
const DEFAULT_THROTTLE: ThrottleConfig = {
  requests_per_minute: 60,
  max_concurrent: 5,
  delay_ms: 100,
};

/**
 * Default dispatcher configuration.
 */
export const DEFAULT_NODE_DISPATCHER_CONFIG: NodeDispatcherConfig = {
  verbose: false,
  kill_switches: {
    COMPANY_HUB: false,
    PEOPLE_NODE: false,
    DOL_NODE: false,
    BIT_NODE: false,
  },
  throttle: {
    COMPANY_HUB: { ...DEFAULT_THROTTLE },
    PEOPLE_NODE: { ...DEFAULT_THROTTLE, requests_per_minute: 30 }, // LinkedIn rate limited
    DOL_NODE: { ...DEFAULT_THROTTLE, requests_per_minute: 120 }, // DOL API friendly
    BIT_NODE: { ...DEFAULT_THROTTLE, requests_per_minute: 1000 }, // Local computation
  },
  max_cost_budget: 10.0,
  enable_parallel: true,
  retry_on_failure: true,
  max_retries: 3,
  mock_mode: true,
  enforce_dependencies: true,
};

/**
 * NodeDispatcher - Hub-and-Spoke Routing Engine
 *
 * Routes records through nodes in the correct sequence:
 * 1. COMPANY_HUB: Resolve company identity, discover patterns
 * 2. PEOPLE_NODE: Enrich person data, detect movement
 * 3. DOL_NODE: Sync DOL data, parse renewals
 * 4. BIT_NODE: Calculate intent scores
 */
export class NodeDispatcher {
  private config: NodeDispatcherConfig;
  private costTracker: CostTracker;
  private nodeStatus: Record<NodeId, NodeStatus>;
  private failureRouter: FailureRouter;
  private throttleManager: ThrottleManagerV2;
  private completedAgents: Set<string> = new Set();

  // Node agents
  private companyFuzzyMatchAgent: CompanyFuzzyMatchAgent;
  private companyStateAgent: CompanyStateAgent;
  private patternAgent: PatternAgent;
  private missingSlotAgent: MissingSlotAgent;
  private emailGeneratorAgent: EmailGeneratorAgent;

  private linkedInFinderAgent: LinkedInFinderAgent;
  private publicScannerAgent: PublicScannerAgent;
  private titleCompanyAgent: TitleCompanyAgent;
  private movementHashAgent: MovementHashAgent;
  private peopleFuzzyMatchAgent: PeopleFuzzyMatchAgent;

  private dolSyncAgent: DOLSyncAgent;
  private renewalParserAgent: RenewalParserAgent;
  private carrierNormalizerAgent: CarrierNormalizerAgent;

  private bitScoreAgent: BITScoreAgent;
  private churnDetectorAgent: ChurnDetectorAgent;
  private renewalIntentAgent: RenewalIntentAgent;

  constructor(config?: Partial<NodeDispatcherConfig>) {
    this.config = {
      ...DEFAULT_NODE_DISPATCHER_CONFIG,
      ...config,
    };

    this.costTracker = {
      COMPANY_HUB: 0,
      PEOPLE_NODE: 0,
      DOL_NODE: 0,
      BIT_NODE: 0,
      total: 0,
    };

    this.nodeStatus = {
      COMPANY_HUB: "IDLE",
      PEOPLE_NODE: "IDLE",
      DOL_NODE: "IDLE",
      BIT_NODE: "IDLE",
    };

    // Initialize failure router (use provided or global instance)
    this.failureRouter = this.config.failure_router || globalFailureRouter;

    // Initialize throttle manager (use provided or global instance)
    this.throttleManager = this.config.throttle_manager || globalThrottleManager;

    // Load vendor budget rules into throttle manager
    for (const vendor in VENDOR_BUDGETS) {
      this.throttleManager.setRule(vendor, VENDOR_BUDGETS[vendor]);
    }

    // Initialize agents with mock_mode from config and failure_router
    const mockConfig = { mock_mode: this.config.mock_mode };

    // Company Hub agents (with failure routing)
    this.companyFuzzyMatchAgent = new CompanyFuzzyMatchAgent({
      external_config: mockConfig,
      failure_router: this.failureRouter,
    });
    this.companyStateAgent = new CompanyStateAgent();
    this.patternAgent = new PatternAgent({
      ...mockConfig,
      failure_router: this.failureRouter,
    });
    this.missingSlotAgent = new MissingSlotAgent({
      discovery_config: mockConfig,
    });
    this.emailGeneratorAgent = new EmailGeneratorAgent({
      pattern_config: mockConfig,
      verification_config: mockConfig,
      failure_router: this.failureRouter,
    });

    // People Node agents (with failure routing)
    this.linkedInFinderAgent = new LinkedInFinderAgent({
      primary_config: mockConfig,
      fallback_config: mockConfig,
      failure_router: this.failureRouter,
    });
    this.publicScannerAgent = new PublicScannerAgent(mockConfig);
    this.titleCompanyAgent = new TitleCompanyAgent({
      linkedin_config: mockConfig,
      employment_config: mockConfig,
      failure_router: this.failureRouter,
    });
    this.movementHashAgent = new MovementHashAgent();
    this.peopleFuzzyMatchAgent = new PeopleFuzzyMatchAgent({
      failure_router: this.failureRouter,
    });

    // DOL Node agents
    this.dolSyncAgent = new DOLSyncAgent(mockConfig);
    this.renewalParserAgent = new RenewalParserAgent();
    this.carrierNormalizerAgent = new CarrierNormalizerAgent();

    // BIT Node agents
    this.bitScoreAgent = new BITScoreAgent();
    this.churnDetectorAgent = new ChurnDetectorAgent();
    this.renewalIntentAgent = new RenewalIntentAgent();
  }

  /**
   * Process a single company through all nodes.
   */
  async processCompany(
    companyId: string,
    companyName: string,
    slots: SlotRow[],
    companyMaster: string[]
  ): Promise<{
    company_hub: NodeExecutionResult;
    people_node: NodeExecutionResult;
    dol_node: NodeExecutionResult;
    bit_node: NodeExecutionResult;
  }> {
    // Check cost budget
    if (this.costTracker.total >= this.config.max_cost_budget) {
      throw new Error("Cost budget exceeded");
    }

    const results = {
      company_hub: await this.executeCompanyHub(companyId, companyName, slots, companyMaster),
      people_node: await this.executePeopleNode(companyId, companyName, slots),
      dol_node: await this.executeDOLNode(companyId, companyName),
      bit_node: await this.executeBITNode(companyId, companyName, slots),
    };

    return results;
  }

  /**
   * Execute Company Hub node.
   *
   * GOLDEN RULE: Sets company_valid flag that gates all downstream processing.
   * If fuzzy match fails → company_valid = false → no email generation.
   */
  private async executeCompanyHub(
    companyId: string,
    companyName: string,
    slots: SlotRow[],
    companyMaster: string[]
  ): Promise<NodeExecutionResult> {
    const nodeId: NodeId = "COMPANY_HUB";
    const result = this.createNodeResult(nodeId);

    // Initialize validation summary
    result.validation_summary = {
      company_valid: false,
      company_invalid_reason: null,
      people_validated: 0,
      people_valid: 0,
      people_invalid: 0,
      emails_generated: 0,
      emails_skipped: 0,
      skip_reasons: {},
    };

    // Check kill switch
    if (this.config.kill_switches.COMPANY_HUB) {
      result.status = "KILLED";
      return result;
    }

    this.nodeStatus.COMPANY_HUB = "RUNNING";

    try {
      // 1. Fuzzy match company name (SETS company_valid FLAG)
      if (this.config.verbose) {
        console.log(`[NodeDispatcher] COMPANY_HUB: Fuzzy matching "${companyName}"`);
      }

      const fuzzyResult = await this.companyFuzzyMatchAgent.run({
        task_id: `fuzzy_${companyId}`,
        slot_row_id: companyId,
        raw_company_input: companyName,
        company_master: companyMaster,
      });
      result.results.push(fuzzyResult);
      result.records_processed++;

      // Capture company validation status
      const matchStatus = fuzzyResult.data?.status as string;
      const companyValid = matchStatus === "MATCHED";
      result.validation_summary.company_valid = companyValid;

      if (!companyValid) {
        const reason = matchStatus === "MANUAL_REVIEW"
          ? `Manual review required (score: ${fuzzyResult.data?.match_score})`
          : `Company not found in master list (best score: ${fuzzyResult.data?.match_score})`;
        result.validation_summary.company_invalid_reason = reason;

        if (this.config.verbose) {
          console.log(`[NodeDispatcher] COMPANY_HUB: company_valid=FALSE - ${reason}`);
        }

        // Mark all slots as company invalid
        for (const slot of slots) {
          slot.setCompanyValid(false, reason);
        }
      } else {
        if (this.config.verbose) {
          console.log(`[NodeDispatcher] COMPANY_HUB: company_valid=TRUE - matched to "${fuzzyResult.data?.matched_company}"`);
        }

        // Mark all slots as company valid
        for (const slot of slots) {
          slot.setCompanyValid(true);
          slot.company_name = fuzzyResult.data?.matched_company as string || slot.company_name;
        }
      }

      // 2. Evaluate company state
      const stateResult = await this.companyStateAgent.run({
        task_id: `state_${companyId}`,
        company_id: companyId,
        company_name: companyName,
        existing_rows: slots,
      });
      result.results.push(stateResult);

      // 3. Discover email pattern (ONLY if company is valid)
      if (companyValid) {
        const patternResult = await this.patternAgent.run({
          task_id: `pattern_${companyId}`,
          slot_row_id: companyId,
          company_name: companyName,
        });
        result.results.push(patternResult);
        this.trackCost(nodeId, patternResult.data?.cost as number || 0);

        // Apply pattern to all slots
        if (patternResult.success && patternResult.data?.email_pattern) {
          const pattern = patternResult.data.email_pattern as string;
          for (const slot of slots) {
            slot.email_pattern = pattern;
          }
        }
      } else {
        if (this.config.verbose) {
          console.log(`[NodeDispatcher] COMPANY_HUB: SKIPPING pattern discovery - company_valid=false`);
        }
        result.records_skipped++;
      }

      // 4. Check missing slots (ONLY if company is valid)
      if (companyValid) {
        const missingResult = await this.missingSlotAgent.run({
          task_id: `missing_${companyId}`,
          company_id: companyId,
          company_name: companyName,
          existing_rows: slots,
        });
        result.results.push(missingResult);
        this.trackCost(nodeId, missingResult.data?.total_discovery_cost as number || 0);
      } else {
        if (this.config.verbose) {
          console.log(`[NodeDispatcher] COMPANY_HUB: SKIPPING missing slot check - company_valid=false`);
        }
        result.records_skipped++;
      }

      result.status = "COMPLETED";
      result.completed_at = new Date();
    } catch (error) {
      result.status = "FAILED";
      result.errors.push(error instanceof Error ? error.message : "Unknown error");
      result.records_failed++;
    }

    this.nodeStatus.COMPANY_HUB = result.status;
    return result;
  }

  /**
   * Execute People Node.
   *
   * GOLDEN RULE: Checks company_valid before processing.
   * Sets person_company_valid via TitleCompanyAgent.
   * Validates employer alignment before email generation.
   */
  private async executePeopleNode(
    companyId: string,
    companyName: string,
    slots: SlotRow[]
  ): Promise<NodeExecutionResult> {
    const nodeId: NodeId = "PEOPLE_NODE";
    const result = this.createNodeResult(nodeId);

    // Initialize validation summary
    result.validation_summary = {
      company_valid: true,
      company_invalid_reason: null,
      people_validated: 0,
      people_valid: 0,
      people_invalid: 0,
      emails_generated: 0,
      emails_skipped: 0,
      skip_reasons: {},
    };

    // Check kill switch
    if (this.config.kill_switches.PEOPLE_NODE) {
      result.status = "KILLED";
      return result;
    }

    // Check if Company Hub completed
    if (this.nodeStatus.COMPANY_HUB !== "COMPLETED") {
      result.status = "FAILED";
      result.errors.push("Company Hub must complete before People Node");
      return result;
    }

    // === GOLDEN RULE CHECK ===
    // Check if ANY slot has company_valid = false
    const hasInvalidCompany = slots.some(s => s.company_valid === false);
    if (hasInvalidCompany) {
      const invalidSlot = slots.find(s => s.company_valid === false);
      const reason = invalidSlot?.company_invalid_reason ?? "Company validation failed";

      if (this.config.verbose) {
        console.log(`[NodeDispatcher] PEOPLE_NODE: SKIPPING all processing - company_valid=false`);
        console.log(`[NodeDispatcher] PEOPLE_NODE: Reason: ${reason}`);
      }

      result.validation_summary.company_valid = false;
      result.validation_summary.company_invalid_reason = reason;
      result.records_skipped = slots.length;

      // Track skip reason
      result.validation_summary.skip_reasons["company_invalid"] = slots.length;

      result.status = "COMPLETED";
      result.completed_at = new Date();
      this.nodeStatus.PEOPLE_NODE = result.status;
      return result;
    }

    this.nodeStatus.PEOPLE_NODE = "RUNNING";

    try {
      // Process each slot with a person
      for (const slot of slots.filter((s) => s.person_name)) {
        await this.throttle(nodeId);

        if (this.config.verbose) {
          console.log(`[NodeDispatcher] PEOPLE_NODE: Processing ${slot.person_name}`);
        }

        // 1. Find LinkedIn URL
        const linkedInResult = await this.linkedInFinderAgent.runOnRow(slot);
        result.records_processed++;

        // 2. Check public accessibility
        if (slot.linkedin_url) {
          await this.publicScannerAgent.runOnRow(slot);
        }

        // 3. Get title/company (SETS person_company_valid FLAG)
        await this.titleCompanyAgent.runOnRow(slot);
        result.validation_summary.people_validated++;

        // Track person validation result
        if (slot.person_company_valid === true) {
          result.validation_summary.people_valid++;
          if (this.config.verbose) {
            console.log(`[NodeDispatcher] PEOPLE_NODE: person_company_valid=TRUE for ${slot.person_name}`);
          }
        } else if (slot.person_company_valid === false) {
          result.validation_summary.people_invalid++;
          if (this.config.verbose) {
            console.log(`[NodeDispatcher] PEOPLE_NODE: person_company_valid=FALSE for ${slot.person_name}`);
          }
        }

        // 4. Generate movement hash
        await this.movementHashAgent.runOnRow(slot);

        // 5. Generate email (ONLY if all validations pass)
        if (slot.isEmailGenerationAllowed()) {
          await this.emailGeneratorAgent.runOnRow(slot);

          if (slot.email) {
            result.validation_summary.emails_generated++;
            if (this.config.verbose) {
              console.log(`[NodeDispatcher] PEOPLE_NODE: Email generated for ${slot.person_name}: ${slot.email}`);
            }
          }
        } else {
          result.validation_summary.emails_skipped++;
          const skipReason = slot.skip_reason || "validation_failed";
          result.validation_summary.skip_reasons[skipReason] =
            (result.validation_summary.skip_reasons[skipReason] || 0) + 1;

          if (this.config.verbose) {
            console.log(`[NodeDispatcher] PEOPLE_NODE: Email SKIPPED for ${slot.person_name}`);
            console.log(`[NodeDispatcher] PEOPLE_NODE: Skip reason: ${slot.skip_reason}`);
          }
        }

        this.trackCost(nodeId, this.linkedInFinderAgent.getTotalCost());
        this.linkedInFinderAgent.resetCost();
      }

      result.status = "COMPLETED";
      result.completed_at = new Date();
    } catch (error) {
      result.status = "FAILED";
      result.errors.push(error instanceof Error ? error.message : "Unknown error");
      result.records_failed++;
    }

    this.nodeStatus.PEOPLE_NODE = result.status;
    return result;
  }

  /**
   * Execute DOL Node.
   */
  private async executeDOLNode(
    companyId: string,
    companyName: string
  ): Promise<NodeExecutionResult> {
    const nodeId: NodeId = "DOL_NODE";
    const result = this.createNodeResult(nodeId);

    // Check kill switch
    if (this.config.kill_switches.DOL_NODE) {
      result.status = "KILLED";
      return result;
    }

    this.nodeStatus.DOL_NODE = "RUNNING";

    try {
      // 1. Sync DOL data
      const syncResult = await this.dolSyncAgent.run({
        task_id: `dol_sync_${companyId}`,
        company_id: companyId,
        company_name: companyName,
        sync_type: "single_company",
      });
      result.results.push(syncResult);
      result.records_processed++;

      // 2. Parse renewals if we got filings
      if (syncResult.success && syncResult.data?.filings) {
        const filings = syncResult.data.filings as Form5500Filing[];
        const renewalResult = await this.renewalParserAgent.run({
          task_id: `renewal_${companyId}`,
          company_id: companyId,
          company_name: companyName,
          filings,
        });
        result.results.push(renewalResult);
      }

      result.status = "COMPLETED";
      result.completed_at = new Date();
    } catch (error) {
      result.status = "FAILED";
      result.errors.push(error instanceof Error ? error.message : "Unknown error");
      result.records_failed++;
    }

    this.nodeStatus.DOL_NODE = result.status;
    return result;
  }

  /**
   * Execute BIT Node.
   */
  private async executeBITNode(
    companyId: string,
    companyName: string,
    slots: SlotRow[]
  ): Promise<NodeExecutionResult> {
    const nodeId: NodeId = "BIT_NODE";
    const result = this.createNodeResult(nodeId);

    // Check kill switch
    if (this.config.kill_switches.BIT_NODE) {
      result.status = "KILLED";
      return result;
    }

    this.nodeStatus.BIT_NODE = "RUNNING";

    try {
      // Build movement events from slots
      const movementEvents: MovementEvent[] = slots
        .filter((s) => s.movement_detected)
        .map((s) => ({
          slot_type: s.slot_type as SlotType,
          person_name: s.person_name || "",
          previous_company: null,
          current_company: s.current_company,
          previous_title: null,
          current_title: s.current_title,
          detected_at: s.last_updated || new Date(),
          movement_type: "company_change" as const,
        }));

      // 1. Detect churn
      const churnResult = await this.churnDetectorAgent.run({
        task_id: `churn_${companyId}`,
        company_id: companyId,
        company_name: companyName,
        movement_events: movementEvents,
      });
      result.results.push(churnResult);

      // 2. Get renewal intent (need renewal info from DOL node)
      // For now, pass null - in real implementation, would get from DOL results
      const renewalIntentResult = await this.renewalIntentAgent.run({
        task_id: `renewal_intent_${companyId}`,
        company_id: companyId,
        company_name: companyName,
        renewal_info: null,
      });
      result.results.push(renewalIntentResult);

      // 3. Calculate BIT score
      const signals: IntentSignals = {
        movement_detected: movementEvents.length > 0,
        days_until_renewal: null,
        in_renewal_window: false,
        job_postings_count: 0,
        news_mentions_count: 0,
        website_activity_score: 0,
        competitor_carrier: false,
        employee_count: 500, // Default, would come from company data
      };

      const bitResult = await this.bitScoreAgent.run({
        task_id: `bit_${companyId}`,
        company_id: companyId,
        company_name: companyName,
        signals,
      });
      result.results.push(bitResult);
      result.records_processed++;

      result.status = "COMPLETED";
      result.completed_at = new Date();
    } catch (error) {
      result.status = "FAILED";
      result.errors.push(error instanceof Error ? error.message : "Unknown error");
      result.records_failed++;
    }

    this.nodeStatus.BIT_NODE = result.status;
    return result;
  }

  /**
   * Create empty node result.
   */
  private createNodeResult(nodeId: NodeId): NodeExecutionResult {
    return {
      node_id: nodeId,
      status: "IDLE",
      started_at: new Date(),
      completed_at: null,
      records_processed: 0,
      records_failed: 0,
      records_skipped: 0,
      cost_incurred: 0,
      errors: [],
      results: [],
    };
  }

  /**
   * Track cost for a node.
   */
  private trackCost(nodeId: NodeId, cost: number): void {
    this.costTracker[nodeId] += cost;
    this.costTracker.total += cost;
  }

  /**
   * Apply throttling.
   */
  private async throttle(nodeId: NodeId): Promise<void> {
    const config = this.config.throttle[nodeId];
    if (config.delay_ms > 0) {
      await new Promise((resolve) => setTimeout(resolve, config.delay_ms));
    }
  }

  /**
   * Validate agent dependencies before execution.
   * Returns true if dependencies are met, false if agent should be skipped.
   */
  validateAgentDependencies(
    nodeName: string,
    agentName: string,
    row: SlotRow
  ): { allowed: boolean; missing: string[] } {
    // If dependency enforcement is disabled, allow all
    if (!this.config.enforce_dependencies) {
      return { allowed: true, missing: [] };
    }

    // Get completed agents from the row or instance tracking
    const completedAgents = Array.from(this.completedAgents);

    // Also include row-level completion tracking if available
    const rowCompletedAgents = (row as any).completedAgents || [];
    const allCompleted = [...new Set([...completedAgents, ...rowCompletedAgents])];

    const result = validateDependencies(nodeName, agentName, allCompleted);

    if (this.config.verbose && !result.valid) {
      console.log(
        `[NodeDispatcher] DEPENDENCY CHECK: ${agentName} blocked - missing: [${result.missing.join(", ")}]`
      );
    }

    return { allowed: result.valid, missing: result.missing };
  }

  /**
   * Mark an agent as completed (for dependency tracking).
   */
  markAgentCompleted(agentName: string, row: SlotRow): void {
    this.completedAgents.add(agentName);

    // Also track on the row
    (row as any).completedAgents = (row as any).completedAgents || [];
    if (!(row as any).completedAgents.includes(agentName)) {
      (row as any).completedAgents.push(agentName);
    }

    if (this.config.verbose) {
      console.log(`[NodeDispatcher] Agent completed: ${agentName}`);
    }
  }

  /**
   * Check vendor throttle before agent execution.
   * Returns true if allowed, false if blocked by throttle.
   */
  async checkVendorThrottle(
    agentName: string,
    row: SlotRow
  ): Promise<{ allowed: boolean; reason?: string; waitMs?: number }> {
    const vendor = getVendorForAgent(agentName);
    const cost = getCostForAgent(agentName);

    // Check if vendor is allowed
    const isAllowed = this.throttleManager.isAllowed(vendor, cost);

    if (!isAllowed) {
      // Get detailed check for wait time
      const checkResult = this.throttleManager.check(vendor as any, cost);

      if (this.config.verbose) {
        console.log(
          `[NodeDispatcher] THROTTLE BLOCKED: ${agentName} (vendor: ${vendor}, reason: ${checkResult.reason})`
        );
      }

      // Record the blocked call
      this.throttleManager.recordBlocked(
        vendor as any,
        agentName,
        cost,
        checkResult.reason!
      );

      // Route to failure bay
      await this.failureRouter.routeError(
        new Error(`Throttle blocked: ${checkResult.reason}`),
        agentName as FailureAgentType,
        {
          node: this.failureRouter.getExecutionContext()?.currentNode,
          slotRow: row,
          slotRowId: row.id,
          metadata: {
            vendor,
            cost,
            throttle_reason: checkResult.reason,
            wait_ms: checkResult.wait_ms,
          },
        }
      );

      return {
        allowed: false,
        reason: checkResult.reason,
        waitMs: checkResult.wait_ms,
      };
    }

    return { allowed: true };
  }

  /**
   * Record agent execution to throttle manager.
   */
  recordAgentExecution(agentName: string): void {
    const vendor = getVendorForAgent(agentName);
    const cost = getCostForAgent(agentName);

    this.throttleManager.record(vendor as any, agentName, cost);
  }

  /**
   * Execute an agent with dependency and throttle checks.
   */
  async executeAgentWithChecks<T>(
    nodeName: string,
    agentName: string,
    row: SlotRow,
    executeFn: () => Promise<T>
  ): Promise<{ success: boolean; result?: T; skipped: boolean; error?: string }> {
    // 1. Check dependencies
    const depCheck = this.validateAgentDependencies(nodeName, agentName, row);
    if (!depCheck.allowed) {
      return {
        success: false,
        skipped: true,
        error: `Missing dependencies: [${depCheck.missing.join(", ")}]`,
      };
    }

    // 2. Check vendor throttle
    const throttleCheck = await this.checkVendorThrottle(agentName, row);
    if (!throttleCheck.allowed) {
      return {
        success: false,
        skipped: false,
        error: `Throttled: ${throttleCheck.reason} (wait: ${throttleCheck.waitMs}ms)`,
      };
    }

    try {
      // 3. Execute the agent
      const result = await executeFn();

      // 4. Record execution and mark completed
      this.recordAgentExecution(agentName);
      this.markAgentCompleted(agentName, row);

      return { success: true, result, skipped: false };
    } catch (error) {
      // Report failure to throttle manager for backoff
      const vendor = getVendorForAgent(agentName);
      this.throttleManager.reportFailure(vendor as any);

      return {
        success: false,
        skipped: false,
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  }

  /**
   * Get throttle manager instance.
   */
  getThrottleManager(): ThrottleManagerV2 {
    return this.throttleManager;
  }

  /**
   * Get completed agents list.
   */
  getCompletedAgents(): string[] {
    return Array.from(this.completedAgents);
  }

  /**
   * Reset completed agents (for new processing run).
   */
  resetCompletedAgents(): void {
    this.completedAgents.clear();
  }

  /**
   * Get vendor diagnostics.
   */
  getVendorDiagnostics(vendor?: string): Record<string, any> {
    if (vendor) {
      return this.throttleManager.getDiagnostics(vendor as any);
    }
    return this.throttleManager.getDiagnostics();
  }

  /**
   * Check if a specific agent can run (dependencies + throttle).
   */
  async canAgentRun(
    nodeName: string,
    agentName: string,
    row: SlotRow
  ): Promise<{ canRun: boolean; reason?: string }> {
    // Check dependencies first
    const depCheck = this.validateAgentDependencies(nodeName, agentName, row);
    if (!depCheck.allowed) {
      return {
        canRun: false,
        reason: `Dependencies not met: [${depCheck.missing.join(", ")}]`,
      };
    }

    // Check throttle
    const vendor = getVendorForAgent(agentName);
    const cost = getCostForAgent(agentName);
    const throttleAllowed = this.throttleManager.isAllowed(vendor, cost);

    if (!throttleAllowed) {
      const checkResult = this.throttleManager.check(vendor as any, cost);
      return {
        canRun: false,
        reason: `Throttled: ${checkResult.reason}`,
      };
    }

    return { canRun: true };
  }

  /**
   * Kill a specific node.
   */
  killNode(nodeId: NodeId): void {
    this.config.kill_switches[nodeId] = true;
    this.nodeStatus[nodeId] = "KILLED";
  }

  /**
   * Enable a killed node.
   */
  enableNode(nodeId: NodeId): void {
    this.config.kill_switches[nodeId] = false;
    this.nodeStatus[nodeId] = "IDLE";
  }

  /**
   * Get current node status.
   */
  getNodeStatus(): Record<NodeId, NodeStatus> {
    return { ...this.nodeStatus };
  }

  /**
   * Get cost tracker.
   */
  getCostTracker(): CostTracker {
    return { ...this.costTracker };
  }

  /**
   * Reset cost tracker.
   */
  resetCostTracker(): void {
    this.costTracker = {
      COMPANY_HUB: 0,
      PEOPLE_NODE: 0,
      DOL_NODE: 0,
      BIT_NODE: 0,
      total: 0,
    };
  }

  /**
   * Get configuration.
   */
  getConfig(): NodeDispatcherConfig {
    return { ...this.config };
  }

  /**
   * Update configuration.
   */
  updateConfig(config: Partial<NodeDispatcherConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Get failure statistics from the router.
   */
  getFailureStatistics(): FailureStatistics {
    return this.failureRouter.getStatistics();
  }

  /**
   * Generate failure report.
   */
  generateFailureReport(): string {
    return this.failureRouter.generateReport();
  }

  /**
   * Check if there are any failures.
   */
  hasFailures(): boolean {
    return this.failureRouter.hasFailures();
  }

  /**
   * Get the failure router instance.
   */
  getFailureRouter(): FailureRouter {
    return this.failureRouter;
  }

  /**
   * Get combined validation summary from all node results.
   */
  getValidationSummary(results: {
    company_hub: NodeExecutionResult;
    people_node: NodeExecutionResult;
    dol_node: NodeExecutionResult;
    bit_node: NodeExecutionResult;
  }): ValidationSummary {
    const companyHubSummary = results.company_hub.validation_summary;
    const peopleNodeSummary = results.people_node.validation_summary;

    return {
      company_valid: companyHubSummary?.company_valid ?? false,
      company_invalid_reason: companyHubSummary?.company_invalid_reason ?? null,
      people_validated: peopleNodeSummary?.people_validated ?? 0,
      people_valid: peopleNodeSummary?.people_valid ?? 0,
      people_invalid: peopleNodeSummary?.people_invalid ?? 0,
      emails_generated: peopleNodeSummary?.emails_generated ?? 0,
      emails_skipped: peopleNodeSummary?.emails_skipped ?? 0,
      skip_reasons: peopleNodeSummary?.skip_reasons ?? {},
    };
  }

  /**
   * Generate validation report for logging/auditing.
   */
  generateValidationReport(
    companyId: string,
    companyName: string,
    results: {
      company_hub: NodeExecutionResult;
      people_node: NodeExecutionResult;
      dol_node: NodeExecutionResult;
      bit_node: NodeExecutionResult;
    }
  ): string {
    const summary = this.getValidationSummary(results);
    const lines: string[] = [];

    lines.push("=".repeat(60));
    lines.push(`VALIDATION REPORT: ${companyName} (${companyId})`);
    lines.push("=".repeat(60));
    lines.push("");

    // Company Validation
    lines.push("COMPANY VALIDATION");
    lines.push("-".repeat(40));
    lines.push(`  Status: ${summary.company_valid ? "✅ VALID" : "❌ INVALID"}`);
    if (!summary.company_valid) {
      lines.push(`  Reason: ${summary.company_invalid_reason}`);
    }
    lines.push("");

    // People Validation
    lines.push("PEOPLE VALIDATION");
    lines.push("-".repeat(40));
    lines.push(`  Validated: ${summary.people_validated}`);
    lines.push(`  Valid:     ${summary.people_valid}`);
    lines.push(`  Invalid:   ${summary.people_invalid}`);
    lines.push("");

    // Email Generation
    lines.push("EMAIL GENERATION");
    lines.push("-".repeat(40));
    lines.push(`  Generated: ${summary.emails_generated}`);
    lines.push(`  Skipped:   ${summary.emails_skipped}`);
    lines.push("");

    // Skip Reasons Breakdown
    if (Object.keys(summary.skip_reasons).length > 0) {
      lines.push("SKIP REASONS BREAKDOWN");
      lines.push("-".repeat(40));
      for (const [reason, count] of Object.entries(summary.skip_reasons)) {
        lines.push(`  ${reason}: ${count}`);
      }
      lines.push("");
    }

    // Node Status
    lines.push("NODE STATUS");
    lines.push("-".repeat(40));
    lines.push(`  COMPANY_HUB:  ${results.company_hub.status}`);
    lines.push(`  PEOPLE_NODE:  ${results.people_node.status}`);
    lines.push(`  DOL_NODE:     ${results.dol_node.status}`);
    lines.push(`  BIT_NODE:     ${results.bit_node.status}`);
    lines.push("");

    // Cost Summary
    lines.push("COST SUMMARY");
    lines.push("-".repeat(40));
    lines.push(`  Total: $${this.costTracker.total.toFixed(4)}`);
    lines.push("");

    // Failure Summary (Garage → Bays)
    const failureStats = this.getFailureStatistics();
    if (failureStats.total_failures > 0) {
      lines.push("FAILURE ROUTING (GARAGE → BAYS)");
      lines.push("-".repeat(40));
      lines.push(`  Total Failures:   ${failureStats.total_failures}`);
      lines.push(`  Pending Repairs:  ${failureStats.pending_repairs}`);
      lines.push("");
      lines.push("  By Bay:");
      for (const [bay, count] of Object.entries(failureStats.by_bay)) {
        if (count > 0) {
          lines.push(`    ${bay}: ${count}`);
        }
      }
      lines.push("");
      lines.push("  By Agent:");
      for (const [agent, count] of Object.entries(failureStats.by_agent)) {
        if (count > 0) {
          lines.push(`    ${agent}: ${count}`);
        }
      }
      lines.push("");
    }

    lines.push("=".repeat(60));

    return lines.join("\n");
  }

  /**
   * Resume execution from a specific node and agent.
   *
   * This method enables the repair → resume workflow:
   * 1. Failure is fixed (via UI/CLI/API)
   * 2. A resume job is created
   * 3. This method executes from the resume point
   *
   * @param row - SlotRow to process (original or fixed)
   * @param resumeNode - Node to start from
   * @param resumeAgent - Agent to start from within the node (optional)
   * @param companyMaster - Company master list for fuzzy matching
   */
  async runWithResume(
    row: SlotRow,
    resumeNode: FailureNode,
    resumeAgent?: FailureAgentType,
    companyMaster: string[] = []
  ): Promise<ResumeExecutionResult> {
    const result: ResumeExecutionResult = {
      success: false,
      jobId: `resume_exec_${Date.now()}`,
      failureId: row.id,
      sourceBay: "agent_failures",
      resumeNode,
      resumeAgent: resumeAgent || "Unknown",
      nodeResults: [],
      completedAt: null,
    };

    if (this.config.verbose) {
      console.log(`[NodeDispatcher] RESUME: Starting from ${resumeNode}/${resumeAgent}`);
      console.log(`[NodeDispatcher] RESUME: SlotRow ID: ${row.id}`);
    }

    try {
      // Set execution context for failure tracking
      this.failureRouter.setExecutionContext(
        resumeNode,
        resumeAgent || "Unknown",
        row.id
      );

      // Execute nodes starting from resume point
      const nodeOrder: FailureNode[] = ["COMPANY_HUB", "PEOPLE_NODE", "DOL_NODE", "BIT_NODE"];
      const startIndex = nodeOrder.indexOf(resumeNode);

      if (startIndex === -1) {
        throw new Error(`Invalid resume node: ${resumeNode}`);
      }

      // Get company info from slot row
      const companyId = row.company_id;
      const companyName = row.company_name || "";

      // Execute each node from resume point onwards
      for (let i = startIndex; i < nodeOrder.length; i++) {
        const currentNode = nodeOrder[i];

        // Update execution context
        this.failureRouter.setExecutionContext(currentNode, "Unknown", row.id);

        let nodeResult: NodeExecutionResult;

        switch (currentNode) {
          case "COMPANY_HUB":
            // If resuming from a specific agent within COMPANY_HUB
            nodeResult = await this.executeCompanyHubFromAgent(
              companyId,
              companyName,
              [row],
              companyMaster,
              i === startIndex ? resumeAgent : undefined
            );
            break;

          case "PEOPLE_NODE":
            nodeResult = await this.executePeopleNodeFromAgent(
              companyId,
              companyName,
              [row],
              i === startIndex ? resumeAgent : undefined
            );
            break;

          case "DOL_NODE":
            nodeResult = await this.executeDOLNode(companyId, companyName);
            break;

          case "BIT_NODE":
            nodeResult = await this.executeBITNode(companyId, companyName, [row]);
            break;

          default:
            throw new Error(`Unknown node: ${currentNode}`);
        }

        result.nodeResults.push(nodeResult);

        // Stop if node failed (unless it's an optional node)
        if (nodeResult.status === "FAILED" && currentNode !== "DOL_NODE") {
          result.error = `Node ${currentNode} failed: ${nodeResult.errors.join(", ")}`;
          return result;
        }
      }

      // All nodes completed successfully
      result.success = true;
      result.completedAt = new Date();

      if (this.config.verbose) {
        console.log(`[NodeDispatcher] RESUME: Completed successfully`);
      }
    } catch (error) {
      result.error = error instanceof Error ? error.message : "Unknown error";
      if (this.config.verbose) {
        console.error(`[NodeDispatcher] RESUME: Failed - ${result.error}`);
      }
    } finally {
      this.failureRouter.clearExecutionContext();
    }

    return result;
  }

  /**
   * Execute Company Hub from a specific agent (for resume).
   */
  private async executeCompanyHubFromAgent(
    companyId: string,
    companyName: string,
    slots: SlotRow[],
    companyMaster: string[],
    startAgent?: FailureAgentType
  ): Promise<NodeExecutionResult> {
    // If no specific agent, run full node
    if (!startAgent) {
      return this.executeCompanyHub(companyId, companyName, slots, companyMaster);
    }

    const nodeId: NodeId = "COMPANY_HUB";
    const result = this.createNodeResult(nodeId);

    // Initialize validation summary
    result.validation_summary = {
      company_valid: slots[0]?.company_valid ?? false,
      company_invalid_reason: slots[0]?.company_invalid_reason ?? null,
      people_validated: 0,
      people_valid: 0,
      people_invalid: 0,
      emails_generated: 0,
      emails_skipped: 0,
      skip_reasons: {},
    };

    if (this.config.kill_switches.COMPANY_HUB) {
      result.status = "KILLED";
      return result;
    }

    this.nodeStatus.COMPANY_HUB = "RUNNING";

    try {
      const agentOrder: FailureAgentType[] = [
        "CompanyFuzzyMatchAgent",
        "PatternAgent",
        "MissingSlotAgent",
        "EmailGeneratorAgent",
      ];

      const startIndex = agentOrder.indexOf(startAgent);
      if (startIndex === -1) {
        // Unknown agent in this node, run full node
        return this.executeCompanyHub(companyId, companyName, slots, companyMaster);
      }

      // Update context and execute from start agent
      for (let i = startIndex; i < agentOrder.length; i++) {
        const agent = agentOrder[i];
        this.failureRouter.setExecutionContext("COMPANY_HUB", agent, slots[0]?.id);

        if (this.config.verbose) {
          console.log(`[NodeDispatcher] COMPANY_HUB RESUME: Executing ${agent}`);
        }

        switch (agent) {
          case "CompanyFuzzyMatchAgent":
            const fuzzyResult = await this.companyFuzzyMatchAgent.run({
              task_id: `fuzzy_${companyId}`,
              slot_row_id: companyId,
              raw_company_input: companyName,
              company_master: companyMaster,
            });
            result.results.push(fuzzyResult);
            result.records_processed++;

            const matchStatus = fuzzyResult.data?.status as string;
            const companyValid = matchStatus === "MATCHED";
            result.validation_summary!.company_valid = companyValid;

            for (const slot of slots) {
              slot.setCompanyValid(companyValid, companyValid ? undefined : `Match status: ${matchStatus}`);
              if (companyValid && fuzzyResult.data?.matched_company) {
                slot.company_name = fuzzyResult.data.matched_company as string;
              }
            }
            break;

          case "PatternAgent":
            if (result.validation_summary!.company_valid || slots[0]?.company_valid) {
              const patternResult = await this.patternAgent.run({
                task_id: `pattern_${companyId}`,
                slot_row_id: companyId,
                company_name: companyName,
              });
              result.results.push(patternResult);
              this.trackCost(nodeId, patternResult.data?.cost as number || 0);

              if (patternResult.success && patternResult.data?.email_pattern) {
                for (const slot of slots) {
                  slot.email_pattern = patternResult.data.email_pattern as string;
                }
              }
            }
            break;

          case "MissingSlotAgent":
            if (result.validation_summary!.company_valid || slots[0]?.company_valid) {
              const missingResult = await this.missingSlotAgent.run({
                task_id: `missing_${companyId}`,
                company_id: companyId,
                company_name: companyName,
                existing_rows: slots,
              });
              result.results.push(missingResult);
            }
            break;

          case "EmailGeneratorAgent":
            // Email generation typically happens in People Node
            break;
        }
      }

      result.status = "COMPLETED";
      result.completed_at = new Date();
    } catch (error) {
      result.status = "FAILED";
      result.errors.push(error instanceof Error ? error.message : "Unknown error");
      result.records_failed++;
    }

    this.nodeStatus.COMPANY_HUB = result.status;
    return result;
  }

  /**
   * Execute People Node from a specific agent (for resume).
   */
  private async executePeopleNodeFromAgent(
    companyId: string,
    companyName: string,
    slots: SlotRow[],
    startAgent?: FailureAgentType
  ): Promise<NodeExecutionResult> {
    // If no specific agent, run full node
    if (!startAgent) {
      return this.executePeopleNode(companyId, companyName, slots);
    }

    const nodeId: NodeId = "PEOPLE_NODE";
    const result = this.createNodeResult(nodeId);

    result.validation_summary = {
      company_valid: slots[0]?.company_valid ?? true,
      company_invalid_reason: slots[0]?.company_invalid_reason ?? null,
      people_validated: 0,
      people_valid: 0,
      people_invalid: 0,
      emails_generated: 0,
      emails_skipped: 0,
      skip_reasons: {},
    };

    if (this.config.kill_switches.PEOPLE_NODE) {
      result.status = "KILLED";
      return result;
    }

    // Golden Rule check
    if (!slots[0]?.company_valid) {
      result.validation_summary.company_valid = false;
      result.records_skipped = slots.length;
      result.status = "COMPLETED";
      result.completed_at = new Date();
      return result;
    }

    this.nodeStatus.PEOPLE_NODE = "RUNNING";

    try {
      const agentOrder: FailureAgentType[] = [
        "LinkedInFinderAgent",
        "PublicScannerAgent",
        "TitleCompanyAgent",
        "PeopleFuzzyMatchAgent",
        "MovementHashAgent",
        "EmailGeneratorAgent",
      ];

      const startIndex = agentOrder.indexOf(startAgent);
      if (startIndex === -1) {
        return this.executePeopleNode(companyId, companyName, slots);
      }

      for (const slot of slots.filter((s) => s.person_name)) {
        await this.throttle(nodeId);

        for (let i = startIndex; i < agentOrder.length; i++) {
          const agent = agentOrder[i];
          this.failureRouter.setExecutionContext("PEOPLE_NODE", agent, slot.id);

          if (this.config.verbose) {
            console.log(`[NodeDispatcher] PEOPLE_NODE RESUME: Executing ${agent} for ${slot.person_name}`);
          }

          switch (agent) {
            case "LinkedInFinderAgent":
              await this.linkedInFinderAgent.runOnRow(slot);
              result.records_processed++;
              break;

            case "PublicScannerAgent":
              if (slot.linkedin_url) {
                await this.publicScannerAgent.runOnRow(slot);
              }
              break;

            case "TitleCompanyAgent":
              await this.titleCompanyAgent.runOnRow(slot);
              result.validation_summary!.people_validated++;
              if (slot.person_company_valid === true) {
                result.validation_summary!.people_valid++;
              } else if (slot.person_company_valid === false) {
                result.validation_summary!.people_invalid++;
              }
              break;

            case "PeopleFuzzyMatchAgent":
              await this.peopleFuzzyMatchAgent.runOnRow(slot);
              break;

            case "MovementHashAgent":
              await this.movementHashAgent.runOnRow(slot);
              break;

            case "EmailGeneratorAgent":
              if (slot.isEmailGenerationAllowed()) {
                await this.emailGeneratorAgent.runOnRow(slot);
                if (slot.email) {
                  result.validation_summary!.emails_generated++;
                }
              } else {
                result.validation_summary!.emails_skipped++;
                const skipReason = slot.skip_reason || "validation_failed";
                result.validation_summary!.skip_reasons[skipReason] =
                  (result.validation_summary!.skip_reasons[skipReason] || 0) + 1;
              }
              break;
          }
        }
      }

      result.status = "COMPLETED";
      result.completed_at = new Date();
    } catch (error) {
      result.status = "FAILED";
      result.errors.push(error instanceof Error ? error.message : "Unknown error");
      result.records_failed++;
    }

    this.nodeStatus.PEOPLE_NODE = result.status;
    return result;
  }

  /**
   * Process a resume job from the failure router.
   */
  async processResumeJob(
    job: ResumeJob,
    companyMaster: string[] = []
  ): Promise<ResumeExecutionResult> {
    // Mark job as in progress
    this.failureRouter.updateResumeJobStatus(job.id, "in_progress");

    // Convert slot row data to SlotRow if needed
    const slotData = job.slotRow as Record<string, unknown>;
    const row = new SlotRow(
      slotData.id as string,
      slotData.company_id as string,
      slotData.slot_type as SlotType,
      slotData.person_name as string | null,
      slotData.linkedin_url as string | null,
      slotData.email as string | null
    );

    // Copy over any additional properties
    if (slotData.company_name) row.company_name = slotData.company_name as string;
    if (slotData.email_pattern) row.email_pattern = slotData.email_pattern as string;
    if (slotData.company_valid !== undefined) row.company_valid = slotData.company_valid as boolean;

    // Execute resume
    const result = await this.runWithResume(
      row,
      job.resumeNode,
      job.resumeAgent,
      companyMaster
    );

    // Update job status based on result
    if (result.success) {
      this.failureRouter.updateResumeJobStatus(job.id, "completed");
    } else {
      this.failureRouter.updateResumeJobStatus(job.id, "failed");
    }

    return {
      ...result,
      jobId: job.id,
      failureId: job.failureId,
      sourceBay: job.sourceBay,
    };
  }

  /**
   * Process all pending resume jobs.
   */
  async processAllResumeJobs(
    companyMaster: string[] = []
  ): Promise<ResumeExecutionResult[]> {
    const results: ResumeExecutionResult[] = [];
    const pendingJobs = this.failureRouter.getPendingResumeJobs();

    if (this.config.verbose) {
      console.log(`[NodeDispatcher] Processing ${pendingJobs.length} pending resume jobs`);
    }

    for (const job of pendingJobs) {
      const result = await this.processResumeJob(job, companyMaster);
      results.push(result);

      // Apply throttling between jobs
      await this.throttle("COMPANY_HUB");
    }

    return results;
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
    return this.failureRouter.getResumeQueueStats();
  }

  // ============================================================================
  // CLI RUNNER INTERFACE
  // ============================================================================

  /**
   * Run dispatcher in a specific mode for CLI integration.
   *
   * This method is called by run_talent_engine.js to process records
   * based on the mode specified from the Python pipeline.
   *
   * Modes:
   * - pattern: Discover email pattern for a company (PatternAgent)
   * - generate_email: Generate email for a person (EmailGeneratorAgent)
   * - verify: Verify an email address (EmailVerificationAgent)
   * - enrich: Full enrichment through all nodes
   */
  async run(
    row: Record<string, any>,
    mode: string
  ): Promise<Record<string, any>> {
    switch (mode) {
      case "pattern":
        return this.runPatternMode(row);

      case "generate_email":
        return this.runGenerateEmailMode(row);

      case "verify":
        return this.runVerifyMode(row);

      case "enrich":
        return this.runEnrichMode(row);

      default:
        throw new Error(`Unknown mode: ${mode}`);
    }
  }

  /**
   * Pattern discovery mode - find email pattern for a company.
   */
  private async runPatternMode(
    row: Record<string, any>
  ): Promise<Record<string, any>> {
    const { company_id, company_name, domain } = row;

    if (!domain) {
      return {
        company_id,
        email_pattern: null,
        pattern_confidence: 0,
        source: "talent_engine",
        status: "no_domain",
      };
    }

    try {
      // Check throttle before calling agent
      const throttleCheck = await this.checkVendorThrottle("PatternAgent", row as any);
      if (!throttleCheck.allowed) {
        return {
          company_id,
          email_pattern: null,
          pattern_confidence: 0,
          source: "talent_engine",
          status: "throttled",
          throttle_reason: throttleCheck.reason,
        };
      }

      // Run pattern agent
      const result = await this.patternAgent.run({
        task_id: `pattern_${company_id}`,
        slot_row_id: company_id,
        company_domain: domain,
        company_name,
      });

      // Record the call
      this.recordAgentExecution("PatternAgent");

      return {
        company_id,
        email_pattern: result.data?.email_pattern || null,
        pattern_confidence: result.data?.confidence || 0,
        source: "talent_engine",
        status: result.success ? "success" : "failed",
        error: result.error,
      };
    } catch (err: any) {
      return {
        company_id,
        email_pattern: null,
        pattern_confidence: 0,
        source: "talent_engine",
        status: "error",
        error: err.message,
      };
    }
  }

  /**
   * Email generation mode - generate email for a person.
   */
  private async runGenerateEmailMode(
    row: Record<string, any>
  ): Promise<Record<string, any>> {
    const { person_id, first_name, last_name, full_name, domain, email_pattern } = row;

    if (!domain || !email_pattern) {
      return {
        person_id,
        email: null,
        pattern_used: null,
        confidence: 0,
        variants: [],
        status: "missing_data",
      };
    }

    try {
      // Check throttle
      const throttleCheck = await this.checkVendorThrottle("EmailGeneratorAgent", row as any);
      if (!throttleCheck.allowed) {
        return {
          person_id,
          email: null,
          pattern_used: null,
          confidence: 0,
          variants: [],
          status: "throttled",
          throttle_reason: throttleCheck.reason,
        };
      }

      // Build person name from parts or use full_name
      let personName = full_name;
      if (!personName && (first_name || last_name)) {
        personName = `${first_name || ""} ${last_name || ""}`.trim();
      }

      // Run email generator agent
      const result = await this.emailGeneratorAgent.run({
        task_id: `email_${person_id}`,
        slot_row_id: person_id,
        person_name: personName,
        company_name: row.company_name || domain.split(".")[0],
        company_domain: domain,
        email_pattern: email_pattern,
      });

      // Record the call
      this.recordAgentExecution("EmailGeneratorAgent");

      return {
        person_id,
        email: result.data?.email || null,
        pattern_used: email_pattern,
        confidence: result.data?.confidence || 0,
        variants: result.data?.variants || [],
        status: result.success ? "success" : "failed",
        error: result.error,
      };
    } catch (err: any) {
      return {
        person_id,
        email: null,
        pattern_used: null,
        confidence: 0,
        variants: [],
        status: "error",
        error: err.message,
      };
    }
  }

  /**
   * Email verification mode - verify an email address.
   */
  private async runVerifyMode(
    row: Record<string, any>
  ): Promise<Record<string, any>> {
    const { person_id, email } = row;

    if (!email) {
      return {
        person_id,
        is_valid: false,
        status: "no_email",
        mx_records: [],
      };
    }

    try {
      // Check throttle
      const throttleCheck = await this.checkVendorThrottle("EmailVerificationAgent", row as any);
      if (!throttleCheck.allowed) {
        return {
          person_id,
          is_valid: false,
          status: "throttled",
          mx_records: [],
          throttle_reason: throttleCheck.reason,
        };
      }

      // Basic syntax validation
      const syntaxPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
      if (!syntaxPattern.test(email)) {
        return {
          person_id,
          is_valid: false,
          status: "invalid_syntax",
          mx_records: [],
        };
      }

      // In mock mode, simulate MX check based on domain
      if (this.config.mock_mode) {
        const domain = email.split("@")[1];
        const isValid = domain.includes(".") && domain.split(".").pop()!.length >= 2;
        return {
          person_id,
          is_valid: isValid,
          status: isValid ? "valid" : "no_mx",
          mx_records: isValid ? [`mail.${domain}`] : [],
        };
      }

      // Record the call
      this.recordAgentExecution("EmailVerificationAgent");

      // Real verification would happen here via EmailVerificationAgent
      // For now, return basic syntax check result
      return {
        person_id,
        is_valid: true,
        status: "valid",
        mx_records: [],
      };
    } catch (err: any) {
      return {
        person_id,
        is_valid: false,
        status: "error",
        mx_records: [],
        error: err.message,
      };
    }
  }

  /**
   * Full enrichment mode - run through all nodes.
   */
  private async runEnrichMode(
    row: Record<string, any>
  ): Promise<Record<string, any>> {
    const { company_id, company_name, domain, slots = [] } = row;

    // Convert raw slot data to SlotRow instances if needed
    const slotRows: SlotRow[] = slots.map((s: any) =>
      s instanceof SlotRow ? s : new SlotRow(s)
    );

    // Process through all nodes
    const result = await this.processCompany(
      company_id,
      company_name,
      slotRows,
      [] // company_master would be loaded separately
    );

    return {
      company_id,
      company_name,
      domain,
      results: result,
      status: "complete",
    };
  }
}
