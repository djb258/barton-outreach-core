/**
 * Agent Registry Logic
 * ====================
 * Central registry for all agents in the Talent Engine.
 * Provides agent lookup, instantiation, and configuration.
 */

import { AgentType } from "../models/SlotRow";
import { FuzzyMatchAgent } from "../agents/FuzzyMatchAgent";
import { MissingSlotAgent } from "../agents/MissingSlotAgent";
import { LinkedInFinderAgent } from "../agents/LinkedInFinderAgent";
import { PublicScannerAgent } from "../agents/PublicScannerAgent";
import { PatternAgent } from "../agents/PatternAgent";
import { EmailGeneratorAgent } from "../agents/EmailGeneratorAgent";
import { TitleCompanyAgent } from "../agents/TitleCompanyAgent";
import { HashAgent } from "../agents/HashAgent";
import { ThrottleManager, AgentThrottleRegistry, globalThrottleRegistry } from "./throttleManager";
import { KillSwitchManager, globalKillSwitchManager } from "./killSwitch";

/**
 * Agent instance types.
 */
export type AgentInstance =
  | FuzzyMatchAgent
  | MissingSlotAgent
  | LinkedInFinderAgent
  | PublicScannerAgent
  | PatternAgent
  | EmailGeneratorAgent
  | TitleCompanyAgent
  | HashAgent;

/**
 * Agent metadata.
 */
export interface AgentMeta {
  type: AgentType;
  layer: 1 | 2 | 3 | 4;
  description: string;
  requires_company_match: boolean;
  cost_per_call: number;
}

/**
 * Agent metadata registry.
 */
export const AGENT_METADATA: Record<AgentType, AgentMeta> = {
  FuzzyMatchAgent: {
    type: "FuzzyMatchAgent",
    layer: 1,
    description: "Matches raw company input to known companies",
    requires_company_match: false,
    cost_per_call: 0,
  },
  LinkedInFinderAgent: {
    type: "LinkedInFinderAgent",
    layer: 2,
    description: "Finds LinkedIn URLs using Proxycurl/Apollo",
    requires_company_match: true,
    cost_per_call: 0.05,
  },
  PublicScannerAgent: {
    type: "PublicScannerAgent",
    layer: 2,
    description: "Scans public sources for contact info",
    requires_company_match: true,
    cost_per_call: 0.03,
  },
  PatternAgent: {
    type: "PatternAgent",
    layer: 2,
    description: "Discovers email patterns using Hunter.io",
    requires_company_match: true,
    cost_per_call: 0.01,
  },
  EmailGeneratorAgent: {
    type: "EmailGeneratorAgent",
    layer: 2,
    description: "Generates emails using pattern + VitaMail verification",
    requires_company_match: true,
    cost_per_call: 0.02,
  },
  TitleCompanyAgent: {
    type: "TitleCompanyAgent",
    layer: 2,
    description: "Enriches title and company data via Apollo",
    requires_company_match: true,
    cost_per_call: 0.10,
  },
  HashAgent: {
    type: "HashAgent",
    layer: 2,
    description: "Generates MD5 hashes for deduplication",
    requires_company_match: true,
    cost_per_call: 0,
  },
  MissingSlotAgent: {
    type: "MissingSlotAgent",
    layer: 4,
    description: "Detects and creates missing slots for companies",
    requires_company_match: true,
    cost_per_call: 0,
  },
};

/**
 * Agent Registry class.
 */
export class AgentRegistry {
  private agents: Map<AgentType, AgentInstance>;
  private throttleRegistry: AgentThrottleRegistry;
  private killSwitchManager: KillSwitchManager;

  constructor(
    throttleRegistry?: AgentThrottleRegistry,
    killSwitchManager?: KillSwitchManager
  ) {
    this.agents = new Map();
    this.throttleRegistry = throttleRegistry ?? globalThrottleRegistry;
    this.killSwitchManager = killSwitchManager ?? globalKillSwitchManager;

    // Initialize default agents
    this.initializeDefaultAgents();
  }

  /**
   * Initialize default agent instances.
   */
  private initializeDefaultAgents(): void {
    this.agents.set("FuzzyMatchAgent", new FuzzyMatchAgent());
    this.agents.set("MissingSlotAgent", new MissingSlotAgent());
    this.agents.set("LinkedInFinderAgent", new LinkedInFinderAgent());
    this.agents.set("PublicScannerAgent", new PublicScannerAgent());
    this.agents.set("PatternAgent", new PatternAgent());
    this.agents.set("EmailGeneratorAgent", new EmailGeneratorAgent());
    this.agents.set("TitleCompanyAgent", new TitleCompanyAgent());
    this.agents.set("HashAgent", new HashAgent());
  }

  /**
   * Get an agent by type.
   */
  getAgent<T extends AgentInstance>(agentType: AgentType): T | null {
    return (this.agents.get(agentType) as T) ?? null;
  }

  /**
   * Register a custom agent instance.
   */
  registerAgent(agentType: AgentType, agent: AgentInstance): void {
    this.agents.set(agentType, agent);
  }

  /**
   * Check if an agent can be executed (not killed, not throttled).
   */
  canExecute(agentType: AgentType): { allowed: boolean; reason: string | null } {
    // Check kill switch
    if (this.killSwitchManager.isKilled(agentType)) {
      const record = this.killSwitchManager.getKillRecord(agentType);
      return {
        allowed: false,
        reason: `Agent ${agentType} is killed: ${record?.reason ?? "unknown"}`,
      };
    }

    // Check throttle
    if (this.throttleRegistry.isAgentThrottled(agentType)) {
      const throttle = this.throttleRegistry.getThrottle(agentType);
      return {
        allowed: false,
        reason: throttle.getThrottleReason() ?? `Agent ${agentType} is throttled`,
      };
    }

    return { allowed: true, reason: null };
  }

  /**
   * Record an agent call for throttling.
   */
  recordCall(agentType: AgentType): void {
    this.throttleRegistry.recordAgentCall(agentType);
  }

  /**
   * Get metadata for an agent.
   */
  getMeta(agentType: AgentType): AgentMeta {
    return AGENT_METADATA[agentType];
  }

  /**
   * Get all agents for a specific layer.
   */
  getAgentsByLayer(layer: 1 | 2 | 3 | 4): AgentType[] {
    return Object.entries(AGENT_METADATA)
      .filter(([_, meta]) => meta.layer === layer)
      .map(([type, _]) => type as AgentType);
  }

  /**
   * Get all active (not killed) agents.
   */
  getActiveAgents(): AgentType[] {
    return Array.from(this.agents.keys()).filter((type) =>
      this.killSwitchManager.isActive(type)
    );
  }

  /**
   * Get all available agent types.
   */
  getAllAgentTypes(): AgentType[] {
    return Array.from(this.agents.keys());
  }

  /**
   * Get status summary for all agents.
   */
  getStatusSummary(): Record<AgentType, { active: boolean; throttled: boolean; reason: string | null }> {
    const summary: Record<string, { active: boolean; throttled: boolean; reason: string | null }> = {};

    for (const agentType of this.agents.keys()) {
      const canExec = this.canExecute(agentType);
      summary[agentType] = {
        active: this.killSwitchManager.isActive(agentType),
        throttled: this.throttleRegistry.isAgentThrottled(agentType),
        reason: canExec.reason,
      };
    }

    return summary as Record<AgentType, { active: boolean; throttled: boolean; reason: string | null }>;
  }

  /**
   * Get total estimated cost for a set of agents.
   */
  estimateCost(agentTypes: AgentType[]): number {
    return agentTypes.reduce((sum, type) => {
      return sum + (AGENT_METADATA[type]?.cost_per_call ?? 0);
    }, 0);
  }

  /**
   * Reset the registry (for testing).
   */
  reset(): void {
    this.agents.clear();
    this.initializeDefaultAgents();
    this.throttleRegistry.resetAll();
    this.killSwitchManager.reset();
  }
}

/**
 * Global agent registry instance.
 */
export const globalAgentRegistry = new AgentRegistry();
