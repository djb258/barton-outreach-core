/**
 * Throttle Manager Logic
 * ======================
 * Rate limiting for API calls in the pipeline.
 * Supports per-minute and per-day limits.
 */

import { AgentType } from "../models/SlotRow";

/**
 * Throttle configuration.
 */
export interface ThrottleConfig {
  max_calls_per_minute: number;
  max_calls_per_day: number;
}

/**
 * Default throttle configuration.
 */
export const DEFAULT_THROTTLE_CONFIG: ThrottleConfig = {
  max_calls_per_minute: 60,
  max_calls_per_day: 10000,
};

/**
 * Per-agent throttle configuration.
 */
export const AGENT_THROTTLE_CONFIGS: Record<AgentType, ThrottleConfig> = {
  FuzzyMatchAgent: { max_calls_per_minute: 100, max_calls_per_day: 50000 },
  LinkedInFinderAgent: { max_calls_per_minute: 30, max_calls_per_day: 500 },
  PublicScannerAgent: { max_calls_per_minute: 30, max_calls_per_day: 500 },
  PatternAgent: { max_calls_per_minute: 60, max_calls_per_day: 5000 },
  EmailGeneratorAgent: { max_calls_per_minute: 60, max_calls_per_day: 5000 },
  TitleCompanyAgent: { max_calls_per_minute: 30, max_calls_per_day: 500 },
  HashAgent: { max_calls_per_minute: 1000, max_calls_per_day: 100000 },
  MissingSlotAgent: { max_calls_per_minute: 100, max_calls_per_day: 10000 },
};

/**
 * ThrottleManager class for rate limiting.
 */
export class ThrottleManager {
  max_calls_per_minute: number;
  max_calls_per_day: number;
  calls_this_minute: number;
  calls_today: number;
  last_reset_minute: Date;
  last_reset_day: Date;

  constructor(config: ThrottleConfig = DEFAULT_THROTTLE_CONFIG) {
    this.max_calls_per_minute = config.max_calls_per_minute;
    this.max_calls_per_day = config.max_calls_per_day;
    this.calls_this_minute = 0;
    this.calls_today = 0;
    this.last_reset_minute = new Date();
    this.last_reset_day = new Date();
  }

  /**
   * Reset counters if time windows have elapsed.
   */
  private resetIfNeeded(): void {
    const now = new Date();

    // Reset per-minute counter
    const minuteElapsed = now.getTime() - this.last_reset_minute.getTime();
    if (minuteElapsed >= 60000) {
      this.calls_this_minute = 0;
      this.last_reset_minute = now;
    }

    // Reset per-day counter
    const dayElapsed = now.getTime() - this.last_reset_day.getTime();
    if (dayElapsed >= 86400000) {
      this.calls_today = 0;
      this.last_reset_day = now;
    }
  }

  /**
   * Check if currently throttled.
   */
  isThrottled(): boolean {
    this.resetIfNeeded();
    return (
      this.calls_this_minute >= this.max_calls_per_minute ||
      this.calls_today >= this.max_calls_per_day
    );
  }

  /**
   * Record a call.
   */
  recordCall(): void {
    this.resetIfNeeded();
    this.calls_this_minute++;
    this.calls_today++;
  }

  /**
   * Get remaining calls this minute.
   */
  getRemainingThisMinute(): number {
    this.resetIfNeeded();
    return Math.max(0, this.max_calls_per_minute - this.calls_this_minute);
  }

  /**
   * Get remaining calls today.
   */
  getRemainingToday(): number {
    this.resetIfNeeded();
    return Math.max(0, this.max_calls_per_day - this.calls_today);
  }

  /**
   * Get time until minute reset (ms).
   */
  getTimeUntilMinuteReset(): number {
    const elapsed = Date.now() - this.last_reset_minute.getTime();
    return Math.max(0, 60000 - elapsed);
  }

  /**
   * Get time until day reset (ms).
   */
  getTimeUntilDayReset(): number {
    const elapsed = Date.now() - this.last_reset_day.getTime();
    return Math.max(0, 86400000 - elapsed);
  }

  /**
   * Get throttle reason if throttled.
   */
  getThrottleReason(): string | null {
    this.resetIfNeeded();

    if (this.calls_this_minute >= this.max_calls_per_minute) {
      return `Per-minute limit reached (${this.calls_this_minute}/${this.max_calls_per_minute})`;
    }

    if (this.calls_today >= this.max_calls_per_day) {
      return `Per-day limit reached (${this.calls_today}/${this.max_calls_per_day})`;
    }

    return null;
  }

  /**
   * Get status string.
   */
  getStatusString(): string {
    this.resetIfNeeded();
    return `Throttle: ${this.calls_this_minute}/${this.max_calls_per_minute} per-min, ${this.calls_today}/${this.max_calls_per_day} per-day`;
  }

  /**
   * Reset all counters (for testing).
   */
  reset(): void {
    const now = new Date();
    this.calls_this_minute = 0;
    this.calls_today = 0;
    this.last_reset_minute = now;
    this.last_reset_day = now;
  }
}

/**
 * Per-agent throttle managers.
 */
export class AgentThrottleRegistry {
  private throttles: Map<AgentType, ThrottleManager>;

  constructor() {
    this.throttles = new Map();

    // Initialize throttles for each agent
    for (const [agentType, config] of Object.entries(AGENT_THROTTLE_CONFIGS)) {
      this.throttles.set(agentType as AgentType, new ThrottleManager(config));
    }
  }

  /**
   * Get throttle for an agent.
   */
  getThrottle(agentType: AgentType): ThrottleManager {
    let throttle = this.throttles.get(agentType);
    if (!throttle) {
      throttle = new ThrottleManager(DEFAULT_THROTTLE_CONFIG);
      this.throttles.set(agentType, throttle);
    }
    return throttle;
  }

  /**
   * Check if an agent is throttled.
   */
  isAgentThrottled(agentType: AgentType): boolean {
    return this.getThrottle(agentType).isThrottled();
  }

  /**
   * Record a call for an agent.
   */
  recordAgentCall(agentType: AgentType): void {
    this.getThrottle(agentType).recordCall();
  }

  /**
   * Get throttle status for all agents.
   */
  getAllStatus(): Record<string, string> {
    const status: Record<string, string> = {};
    for (const [agentType, throttle] of this.throttles) {
      status[agentType] = throttle.getStatusString();
    }
    return status;
  }

  /**
   * Reset all throttles (for testing).
   */
  resetAll(): void {
    for (const throttle of this.throttles.values()) {
      throttle.reset();
    }
  }
}

/**
 * Global throttle registry instance.
 */
export const globalThrottleRegistry = new AgentThrottleRegistry();
