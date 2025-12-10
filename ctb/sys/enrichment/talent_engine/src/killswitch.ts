/**
 * Kill Switch Manager
 * ===================
 * Manages kill switches for individual agents.
 * When a kill switch is true, that agent is blocked entirely.
 */

import { KillSwitchState, AgentType } from "./SlotRow";

/**
 * Default kill switch state (all agents enabled).
 */
export const DEFAULT_KILL_SWITCH_STATE: KillSwitchState = {
  LinkedInFinderAgent: false,
  PublicScannerAgent: false,
  PatternAgent: false,
  EmailGeneratorAgent: false,
  TitleCompanyAgent: false,
  HashAgent: false,
};

/**
 * KillSwitchManager handles agent-level kill switches.
 */
export class KillSwitchManager {
  private state: KillSwitchState;

  constructor(initialState?: Partial<KillSwitchState>) {
    this.state = {
      ...DEFAULT_KILL_SWITCH_STATE,
      ...initialState,
    };
  }

  /**
   * Check if a specific agent is killed (blocked).
   * @param agentType - The agent to check
   * @returns true if the agent is killed (blocked)
   */
  isKilled(agentType: AgentType): boolean {
    return this.state[agentType] === true;
  }

  /**
   * Kill (block) a specific agent.
   * @param agentType - The agent to kill
   */
  kill(agentType: AgentType): void {
    this.state[agentType] = true;
  }

  /**
   * Revive (unblock) a specific agent.
   * @param agentType - The agent to revive
   */
  revive(agentType: AgentType): void {
    this.state[agentType] = false;
  }

  /**
   * Kill all agents.
   */
  killAll(): void {
    this.state.LinkedInFinderAgent = true;
    this.state.PublicScannerAgent = true;
    this.state.PatternAgent = true;
    this.state.EmailGeneratorAgent = true;
    this.state.TitleCompanyAgent = true;
    this.state.HashAgent = true;
  }

  /**
   * Revive all agents.
   */
  reviveAll(): void {
    this.state.LinkedInFinderAgent = false;
    this.state.PublicScannerAgent = false;
    this.state.PatternAgent = false;
    this.state.EmailGeneratorAgent = false;
    this.state.TitleCompanyAgent = false;
    this.state.HashAgent = false;
  }

  /**
   * Get current kill switch state.
   */
  getState(): KillSwitchState {
    return { ...this.state };
  }

  /**
   * Get list of killed agents.
   */
  getKilledAgents(): AgentType[] {
    const killed: AgentType[] = [];
    if (this.state.LinkedInFinderAgent) killed.push("LinkedInFinderAgent");
    if (this.state.PublicScannerAgent) killed.push("PublicScannerAgent");
    if (this.state.PatternAgent) killed.push("PatternAgent");
    if (this.state.EmailGeneratorAgent) killed.push("EmailGeneratorAgent");
    if (this.state.TitleCompanyAgent) killed.push("TitleCompanyAgent");
    if (this.state.HashAgent) killed.push("HashAgent");
    return killed;
  }

  /**
   * Get list of active agents.
   */
  getActiveAgents(): AgentType[] {
    const active: AgentType[] = [];
    if (!this.state.LinkedInFinderAgent) active.push("LinkedInFinderAgent");
    if (!this.state.PublicScannerAgent) active.push("PublicScannerAgent");
    if (!this.state.PatternAgent) active.push("PatternAgent");
    if (!this.state.EmailGeneratorAgent) active.push("EmailGeneratorAgent");
    if (!this.state.TitleCompanyAgent) active.push("TitleCompanyAgent");
    if (!this.state.HashAgent) active.push("HashAgent");
    return active;
  }
}
