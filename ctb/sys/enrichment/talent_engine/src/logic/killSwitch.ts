/**
 * Kill Switch Logic
 * =================
 * Emergency stop mechanism for agents.
 * Allows disabling specific agents without stopping the entire pipeline.
 */

import { AgentType } from "../models/SlotRow";

/**
 * Kill switch state for all agents.
 */
export interface KillSwitchState {
  FuzzyMatchAgent: boolean;
  LinkedInFinderAgent: boolean;
  PublicScannerAgent: boolean;
  PatternAgent: boolean;
  EmailGeneratorAgent: boolean;
  TitleCompanyAgent: boolean;
  HashAgent: boolean;
  MissingSlotAgent: boolean;
}

/**
 * Default kill switch state (all active).
 */
export const DEFAULT_KILL_SWITCH_STATE: KillSwitchState = {
  FuzzyMatchAgent: false,
  LinkedInFinderAgent: false,
  PublicScannerAgent: false,
  PatternAgent: false,
  EmailGeneratorAgent: false,
  TitleCompanyAgent: false,
  HashAgent: false,
  MissingSlotAgent: false,
};

/**
 * Kill reason record.
 */
export interface KillRecord {
  agent_type: AgentType;
  killed_at: Date;
  killed_by: string;
  reason: string;
}

/**
 * KillSwitchManager class for controlling agent states.
 */
export class KillSwitchManager {
  private state: KillSwitchState;
  private killRecords: Map<AgentType, KillRecord>;

  constructor(initialState?: Partial<KillSwitchState>) {
    this.state = { ...DEFAULT_KILL_SWITCH_STATE, ...initialState };
    this.killRecords = new Map();
  }

  /**
   * Check if an agent is killed.
   */
  isKilled(agentType: AgentType): boolean {
    return this.state[agentType] === true;
  }

  /**
   * Check if an agent is active.
   */
  isActive(agentType: AgentType): boolean {
    return !this.isKilled(agentType);
  }

  /**
   * Kill an agent.
   */
  kill(agentType: AgentType, reason: string = "Manual kill", killedBy: string = "system"): void {
    this.state[agentType] = true;

    this.killRecords.set(agentType, {
      agent_type: agentType,
      killed_at: new Date(),
      killed_by: killedBy,
      reason,
    });
  }

  /**
   * Revive an agent.
   */
  revive(agentType: AgentType): void {
    this.state[agentType] = false;
    this.killRecords.delete(agentType);
  }

  /**
   * Kill all agents.
   */
  killAll(reason: string = "Emergency stop", killedBy: string = "system"): void {
    for (const agentType of Object.keys(this.state) as AgentType[]) {
      this.kill(agentType, reason, killedBy);
    }
  }

  /**
   * Revive all agents.
   */
  reviveAll(): void {
    for (const agentType of Object.keys(this.state) as AgentType[]) {
      this.revive(agentType);
    }
  }

  /**
   * Get all killed agents.
   */
  getKilledAgents(): AgentType[] {
    const killed: AgentType[] = [];
    for (const [agentType, isKilled] of Object.entries(this.state)) {
      if (isKilled) {
        killed.push(agentType as AgentType);
      }
    }
    return killed;
  }

  /**
   * Get all active agents.
   */
  getActiveAgents(): AgentType[] {
    const active: AgentType[] = [];
    for (const [agentType, isKilled] of Object.entries(this.state)) {
      if (!isKilled) {
        active.push(agentType as AgentType);
      }
    }
    return active;
  }

  /**
   * Get kill record for an agent.
   */
  getKillRecord(agentType: AgentType): KillRecord | null {
    return this.killRecords.get(agentType) ?? null;
  }

  /**
   * Get all kill records.
   */
  getAllKillRecords(): KillRecord[] {
    return Array.from(this.killRecords.values());
  }

  /**
   * Get current state.
   */
  getState(): KillSwitchState {
    return { ...this.state };
  }

  /**
   * Get status string.
   */
  getStatusString(): string {
    const killed = this.getKilledAgents();
    if (killed.length === 0) {
      return "Kill Switches: All agents active";
    }
    return `Kill Switches: ${killed.length} killed (${killed.join(", ")})`;
  }

  /**
   * Check if any agent is killed.
   */
  hasKilledAgents(): boolean {
    return this.getKilledAgents().length > 0;
  }

  /**
   * Reset to default state.
   */
  reset(): void {
    this.state = { ...DEFAULT_KILL_SWITCH_STATE };
    this.killRecords.clear();
  }
}

/**
 * Global kill switch manager instance.
 */
export const globalKillSwitchManager = new KillSwitchManager();
