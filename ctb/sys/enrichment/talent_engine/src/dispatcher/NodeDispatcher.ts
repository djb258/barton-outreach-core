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
  cost_incurred: number;
  errors: string[];
  results: AgentResult[];
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

    // Initialize agents with mock_mode from config
    const mockConfig = { mock_mode: this.config.mock_mode };

    // Company Hub agents
    this.companyFuzzyMatchAgent = new CompanyFuzzyMatchAgent({
      external_config: mockConfig,
    });
    this.companyStateAgent = new CompanyStateAgent();
    this.patternAgent = new PatternAgent(mockConfig);
    this.missingSlotAgent = new MissingSlotAgent({
      discovery_config: mockConfig,
    });
    this.emailGeneratorAgent = new EmailGeneratorAgent({
      pattern_config: mockConfig,
      verification_config: mockConfig,
    });

    // People Node agents
    this.linkedInFinderAgent = new LinkedInFinderAgent({
      primary_config: mockConfig,
      fallback_config: mockConfig,
    });
    this.publicScannerAgent = new PublicScannerAgent(mockConfig);
    this.titleCompanyAgent = new TitleCompanyAgent({
      linkedin_config: mockConfig,
      employment_config: mockConfig,
    });
    this.movementHashAgent = new MovementHashAgent();
    this.peopleFuzzyMatchAgent = new PeopleFuzzyMatchAgent();

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
   */
  private async executeCompanyHub(
    companyId: string,
    companyName: string,
    slots: SlotRow[],
    companyMaster: string[]
  ): Promise<NodeExecutionResult> {
    const nodeId: NodeId = "COMPANY_HUB";
    const result = this.createNodeResult(nodeId);

    // Check kill switch
    if (this.config.kill_switches.COMPANY_HUB) {
      result.status = "KILLED";
      return result;
    }

    this.nodeStatus.COMPANY_HUB = "RUNNING";

    try {
      // 1. Fuzzy match company name
      const fuzzyResult = await this.companyFuzzyMatchAgent.run({
        task_id: `fuzzy_${companyId}`,
        slot_row_id: companyId,
        raw_company_input: companyName,
        company_master: companyMaster,
      });
      result.results.push(fuzzyResult);
      result.records_processed++;

      // 2. Evaluate company state
      const stateResult = await this.companyStateAgent.run({
        task_id: `state_${companyId}`,
        company_id: companyId,
        company_name: companyName,
        existing_rows: slots,
      });
      result.results.push(stateResult);

      // 3. Discover email pattern
      const patternResult = await this.patternAgent.run({
        task_id: `pattern_${companyId}`,
        slot_row_id: companyId,
        company_name: companyName,
      });
      result.results.push(patternResult);
      this.trackCost(nodeId, patternResult.data?.cost as number || 0);

      // 4. Check missing slots
      const missingResult = await this.missingSlotAgent.run({
        task_id: `missing_${companyId}`,
        company_id: companyId,
        company_name: companyName,
        existing_rows: slots,
      });
      result.results.push(missingResult);
      this.trackCost(nodeId, missingResult.data?.total_discovery_cost as number || 0);

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
   */
  private async executePeopleNode(
    companyId: string,
    companyName: string,
    slots: SlotRow[]
  ): Promise<NodeExecutionResult> {
    const nodeId: NodeId = "PEOPLE_NODE";
    const result = this.createNodeResult(nodeId);

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

    this.nodeStatus.PEOPLE_NODE = "RUNNING";

    try {
      // Process each slot with a person
      for (const slot of slots.filter((s) => s.person_name)) {
        await this.throttle(nodeId);

        // 1. Find LinkedIn URL
        const linkedInResult = await this.linkedInFinderAgent.runOnRow(slot);
        result.records_processed++;

        // 2. Check public accessibility
        if (slot.linkedin_url) {
          await this.publicScannerAgent.runOnRow(slot);
        }

        // 3. Get title/company
        await this.titleCompanyAgent.runOnRow(slot);

        // 4. Generate movement hash
        await this.movementHashAgent.runOnRow(slot);

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
}
