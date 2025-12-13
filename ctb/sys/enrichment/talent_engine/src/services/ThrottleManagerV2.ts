/**
 * ThrottleManagerV2
 * =================
 * Global throttling and cost governance system for the Talent Engine.
 *
 * Prevents:
 * - Runaway retries
 * - Vendor overuse
 * - Uncontrolled API spend
 *
 * Features:
 * - Per-vendor rate limits (calls per minute/hour/day)
 * - Per-vendor cost limits ($ per minute/hour/day)
 * - Global budget caps
 * - Automatic cooldown with exponential backoff
 * - Integration with failure routing system
 * - Real-time diagnostics and reporting
 *
 * Usage:
 * ```typescript
 * const throttle = new ThrottleManagerV2({
 *   global_budget: 100.0,
 *   vendors: {
 *     proxycurl: { max_calls_per_minute: 30, max_cost_per_hour: 10.0 },
 *     hunter: { max_calls_per_minute: 60, max_cost_per_day: 50.0 },
 *   },
 * });
 *
 * // Check before API call
 * const allowed = await throttle.checkAndConsume("proxycurl", 0.01);
 * if (!allowed.permitted) {
 *   // Handle throttle - route to failure bay
 * }
 * ```
 */

/**
 * Throttle rule configuration for a vendor.
 */
export interface ThrottleRule {
  /** Maximum calls per minute */
  max_calls_per_minute?: number;
  /** Maximum calls per hour */
  max_calls_per_hour?: number;
  /** Maximum calls per day */
  max_calls_per_day?: number;

  /** Maximum cost per minute ($) */
  max_cost_per_minute?: number;
  /** Maximum cost per hour ($) */
  max_cost_per_hour?: number;
  /** Maximum cost per day ($) */
  max_cost_per_day?: number;

  /** Cooldown period after hitting limit (ms) */
  cooldown_ms?: number;
  /** Enable exponential backoff */
  exponential_backoff?: boolean;
  /** Maximum backoff multiplier */
  max_backoff_multiplier?: number;
}

/**
 * Vendor identifiers.
 */
export type VendorId =
  | "proxycurl"
  | "hunter"
  | "vitamail"
  | "apollo"
  | "firecrawl"
  | "apify"
  | "openai"
  | "anthropic"
  | "dol_api"
  | "linkedin"
  | "mock"
  | "internal";

/**
 * Throttle check result.
 */
export interface ThrottleCheckResult {
  /** Whether the call is permitted */
  permitted: boolean;
  /** Reason if not permitted */
  reason?: ThrottleBlockReason;
  /** Wait time before retry (ms) */
  wait_ms?: number;
  /** Current usage stats */
  usage?: VendorUsage;
  /** Vendor that was checked */
  vendor: VendorId;
  /** Cost that would be incurred */
  cost: number;
}

/**
 * Reasons why a call might be blocked.
 */
export type ThrottleBlockReason =
  | "rate_limit_minute"
  | "rate_limit_hour"
  | "rate_limit_day"
  | "cost_limit_minute"
  | "cost_limit_hour"
  | "cost_limit_day"
  | "global_budget_exceeded"
  | "vendor_disabled"
  | "cooldown_active"
  | "circuit_breaker_open";

/**
 * Vendor usage statistics.
 */
export interface VendorUsage {
  /** Calls in current minute window */
  calls_this_minute: number;
  /** Calls in current hour window */
  calls_this_hour: number;
  /** Calls in current day window */
  calls_this_day: number;
  /** Cost in current minute window ($) */
  cost_this_minute: number;
  /** Cost in current hour window ($) */
  cost_this_hour: number;
  /** Cost in current day window ($) */
  cost_this_day: number;
  /** Total calls all time */
  total_calls: number;
  /** Total cost all time ($) */
  total_cost: number;
  /** Last call timestamp */
  last_call_at: Date | null;
  /** Current cooldown end time (if active) */
  cooldown_until: Date | null;
  /** Current backoff multiplier */
  backoff_multiplier: number;
  /** Consecutive failures */
  consecutive_failures: number;
}

/**
 * Call history entry for diagnostics.
 */
export interface CallEntry {
  /** Vendor identifier */
  vendor: VendorId;
  /** Agent that made the call */
  agent: string;
  /** Cost of the call */
  cost: number;
  /** Timestamp of the call */
  timestamp: number;
  /** Whether call was permitted */
  permitted: boolean;
  /** Block reason if not permitted */
  blockReason?: ThrottleBlockReason;
}

/**
 * Time window for tracking.
 */
interface TimeWindow {
  start: Date;
  calls: number;
  cost: number;
}

/**
 * Internal vendor state.
 */
interface VendorState {
  rule: ThrottleRule;
  usage: VendorUsage;
  minute_window: TimeWindow;
  hour_window: TimeWindow;
  day_window: TimeWindow;
  enabled: boolean;
  circuit_breaker_open: boolean;
  circuit_breaker_failures: number;
  circuit_breaker_threshold: number;
}

/**
 * ThrottleManagerV2 configuration.
 */
export interface ThrottleManagerV2Config {
  /** Global budget cap ($) */
  global_budget: number;
  /** Vendor-specific rules */
  vendors: Partial<Record<VendorId, ThrottleRule>>;
  /** Default rule for unspecified vendors */
  default_rule?: ThrottleRule;
  /** Enable verbose logging */
  verbose?: boolean;
  /** Circuit breaker threshold (consecutive failures) */
  circuit_breaker_threshold?: number;
  /** Circuit breaker reset time (ms) */
  circuit_breaker_reset_ms?: number;
  /** Maximum call history entries to keep */
  max_history_entries?: number;
  /** Custom rules to merge with defaults */
  rules?: Partial<Record<VendorId, ThrottleRule>>;
}

/**
 * Default throttle rules by vendor.
 */
export const DEFAULT_VENDOR_RULES: Record<VendorId, ThrottleRule> = {
  proxycurl: {
    max_calls_per_minute: 30,
    max_calls_per_hour: 500,
    max_calls_per_day: 5000,
    max_cost_per_hour: 25.0,
    max_cost_per_day: 100.0,
    cooldown_ms: 2000,
    exponential_backoff: true,
    max_backoff_multiplier: 8,
  },
  hunter: {
    max_calls_per_minute: 60,
    max_calls_per_hour: 1000,
    max_calls_per_day: 10000,
    max_cost_per_hour: 10.0,
    max_cost_per_day: 50.0,
    cooldown_ms: 1000,
    exponential_backoff: true,
    max_backoff_multiplier: 4,
  },
  vitamail: {
    max_calls_per_minute: 100,
    max_calls_per_hour: 2000,
    max_calls_per_day: 20000,
    max_cost_per_hour: 5.0,
    max_cost_per_day: 25.0,
    cooldown_ms: 500,
    exponential_backoff: false,
  },
  apollo: {
    max_calls_per_minute: 20,
    max_calls_per_hour: 200,
    max_calls_per_day: 1000,
    max_cost_per_hour: 15.0,
    max_cost_per_day: 75.0,
    cooldown_ms: 3000,
    exponential_backoff: true,
    max_backoff_multiplier: 16,
  },
  firecrawl: {
    max_calls_per_minute: 50,
    max_calls_per_hour: 500,
    max_calls_per_day: 5000,
    max_cost_per_hour: 10.0,
    max_cost_per_day: 50.0,
    cooldown_ms: 1000,
  },
  apify: {
    max_calls_per_minute: 10,
    max_calls_per_hour: 100,
    max_calls_per_day: 500,
    max_cost_per_hour: 20.0,
    max_cost_per_day: 100.0,
    cooldown_ms: 5000,
    exponential_backoff: true,
    max_backoff_multiplier: 8,
  },
  openai: {
    max_calls_per_minute: 100,
    max_calls_per_hour: 3000,
    max_calls_per_day: 50000,
    max_cost_per_hour: 50.0,
    max_cost_per_day: 200.0,
    cooldown_ms: 1000,
  },
  anthropic: {
    max_calls_per_minute: 50,
    max_calls_per_hour: 1000,
    max_calls_per_day: 10000,
    max_cost_per_hour: 100.0,
    max_cost_per_day: 500.0,
    cooldown_ms: 2000,
  },
  dol_api: {
    max_calls_per_minute: 120,
    max_calls_per_hour: 5000,
    max_calls_per_day: 50000,
    max_cost_per_hour: 0, // Free API
    max_cost_per_day: 0,
    cooldown_ms: 500,
  },
  linkedin: {
    max_calls_per_minute: 5,
    max_calls_per_hour: 50,
    max_calls_per_day: 200,
    max_cost_per_hour: 5.0,
    max_cost_per_day: 25.0,
    cooldown_ms: 10000,
    exponential_backoff: true,
    max_backoff_multiplier: 32,
  },
  mock: {
    max_calls_per_minute: 10000,
    max_calls_per_hour: 100000,
    max_calls_per_day: 1000000,
    cooldown_ms: 0,
  },
  internal: {
    max_calls_per_minute: 10000,
    max_calls_per_hour: 100000,
    max_calls_per_day: 1000000,
    cooldown_ms: 0,
  },
};

/**
 * Default configuration.
 */
export const DEFAULT_THROTTLE_CONFIG: ThrottleManagerV2Config = {
  global_budget: 500.0,
  vendors: DEFAULT_VENDOR_RULES,
  verbose: false,
  circuit_breaker_threshold: 5,
  circuit_breaker_reset_ms: 60000,
};

/**
 * ThrottleManagerV2 - Global throttling and cost governance.
 */
export class ThrottleManagerV2 {
  private config: ThrottleManagerV2Config;
  private vendorStates: Map<VendorId, VendorState> = new Map();
  private globalCost: number = 0;
  private globalCalls: number = 0;
  private startTime: Date = new Date();
  private callHistory: CallEntry[] = [];
  private maxHistoryEntries: number = 1000;

  constructor(config?: Partial<ThrottleManagerV2Config>) {
    this.config = {
      ...DEFAULT_THROTTLE_CONFIG,
      ...config,
      vendors: {
        ...DEFAULT_VENDOR_RULES,
        ...config?.vendors,
        ...config?.rules, // Merge custom rules
      },
    };

    this.maxHistoryEntries = config?.max_history_entries || 1000;

    // Initialize vendor states
    this.initializeVendorStates();

    if (this.config.verbose) {
      console.log("[ThrottleManagerV2] Initialized with config:", {
        global_budget: this.config.global_budget,
        vendors: Object.keys(this.config.vendors),
      });
    }
  }

  /**
   * Initialize vendor states.
   */
  private initializeVendorStates(): void {
    const allVendors: VendorId[] = [
      "proxycurl", "hunter", "vitamail", "apollo", "firecrawl",
      "apify", "openai", "anthropic", "dol_api", "linkedin", "mock", "internal",
    ];

    for (const vendor of allVendors) {
      const rule = this.config.vendors[vendor] || this.config.default_rule || {};
      this.vendorStates.set(vendor, this.createVendorState(rule));
    }
  }

  /**
   * Create initial vendor state.
   */
  private createVendorState(rule: ThrottleRule): VendorState {
    const now = new Date();
    return {
      rule,
      usage: {
        calls_this_minute: 0,
        calls_this_hour: 0,
        calls_this_day: 0,
        cost_this_minute: 0,
        cost_this_hour: 0,
        cost_this_day: 0,
        total_calls: 0,
        total_cost: 0,
        last_call_at: null,
        cooldown_until: null,
        backoff_multiplier: 1,
        consecutive_failures: 0,
      },
      minute_window: { start: now, calls: 0, cost: 0 },
      hour_window: { start: now, calls: 0, cost: 0 },
      day_window: { start: now, calls: 0, cost: 0 },
      enabled: true,
      circuit_breaker_open: false,
      circuit_breaker_failures: 0,
      circuit_breaker_threshold: this.config.circuit_breaker_threshold || 5,
    };
  }

  /**
   * Check if a call is permitted and consume quota if so.
   */
  async checkAndConsume(vendor: VendorId, cost: number = 0): Promise<ThrottleCheckResult> {
    const state = this.vendorStates.get(vendor);
    if (!state) {
      return {
        permitted: false,
        reason: "vendor_disabled",
        vendor,
        cost,
      };
    }

    // Refresh time windows
    this.refreshWindows(state);

    // Check all limits
    const blockReason = this.checkLimits(state, cost);
    if (blockReason) {
      const waitMs = this.calculateWaitTime(state, blockReason);

      if (this.config.verbose) {
        console.log(`[ThrottleManagerV2] BLOCKED: ${vendor} - ${blockReason} (wait: ${waitMs}ms)`);
      }

      return {
        permitted: false,
        reason: blockReason,
        wait_ms: waitMs,
        usage: { ...state.usage },
        vendor,
        cost,
      };
    }

    // Consume quota
    this.consumeQuota(state, cost);

    if (this.config.verbose) {
      console.log(`[ThrottleManagerV2] PERMITTED: ${vendor} (cost: $${cost.toFixed(4)})`);
    }

    return {
      permitted: true,
      usage: { ...state.usage },
      vendor,
      cost,
    };
  }

  /**
   * Check without consuming (peek).
   */
  check(vendor: VendorId, cost: number = 0): ThrottleCheckResult {
    const state = this.vendorStates.get(vendor);
    if (!state) {
      return {
        permitted: false,
        reason: "vendor_disabled",
        vendor,
        cost,
      };
    }

    // Refresh time windows
    this.refreshWindows(state);

    // Check all limits
    const blockReason = this.checkLimits(state, cost);
    if (blockReason) {
      return {
        permitted: false,
        reason: blockReason,
        wait_ms: this.calculateWaitTime(state, blockReason),
        usage: { ...state.usage },
        vendor,
        cost,
      };
    }

    return {
      permitted: true,
      usage: { ...state.usage },
      vendor,
      cost,
    };
  }

  /**
   * Refresh time windows if needed.
   */
  private refreshWindows(state: VendorState): void {
    const now = new Date();

    // Minute window (60 seconds)
    if (now.getTime() - state.minute_window.start.getTime() >= 60000) {
      state.minute_window = { start: now, calls: 0, cost: 0 };
      state.usage.calls_this_minute = 0;
      state.usage.cost_this_minute = 0;
    }

    // Hour window (3600 seconds)
    if (now.getTime() - state.hour_window.start.getTime() >= 3600000) {
      state.hour_window = { start: now, calls: 0, cost: 0 };
      state.usage.calls_this_hour = 0;
      state.usage.cost_this_hour = 0;
    }

    // Day window (86400 seconds)
    if (now.getTime() - state.day_window.start.getTime() >= 86400000) {
      state.day_window = { start: now, calls: 0, cost: 0 };
      state.usage.calls_this_day = 0;
      state.usage.cost_this_day = 0;
    }

    // Check cooldown expiry
    if (state.usage.cooldown_until && now >= state.usage.cooldown_until) {
      state.usage.cooldown_until = null;
    }
  }

  /**
   * Check all limits.
   */
  private checkLimits(state: VendorState, cost: number): ThrottleBlockReason | null {
    const { rule, usage } = state;

    // Check if vendor is disabled
    if (!state.enabled) {
      return "vendor_disabled";
    }

    // Check circuit breaker
    if (state.circuit_breaker_open) {
      return "circuit_breaker_open";
    }

    // Check cooldown
    if (usage.cooldown_until && new Date() < usage.cooldown_until) {
      return "cooldown_active";
    }

    // Check global budget
    if (this.globalCost + cost > this.config.global_budget) {
      return "global_budget_exceeded";
    }

    // Rate limits
    if (rule.max_calls_per_minute && usage.calls_this_minute >= rule.max_calls_per_minute) {
      return "rate_limit_minute";
    }
    if (rule.max_calls_per_hour && usage.calls_this_hour >= rule.max_calls_per_hour) {
      return "rate_limit_hour";
    }
    if (rule.max_calls_per_day && usage.calls_this_day >= rule.max_calls_per_day) {
      return "rate_limit_day";
    }

    // Cost limits
    if (rule.max_cost_per_minute && usage.cost_this_minute + cost > rule.max_cost_per_minute) {
      return "cost_limit_minute";
    }
    if (rule.max_cost_per_hour && usage.cost_this_hour + cost > rule.max_cost_per_hour) {
      return "cost_limit_hour";
    }
    if (rule.max_cost_per_day && usage.cost_this_day + cost > rule.max_cost_per_day) {
      return "cost_limit_day";
    }

    return null;
  }

  /**
   * Calculate wait time for blocked request.
   */
  private calculateWaitTime(state: VendorState, reason: ThrottleBlockReason): number {
    const { rule, usage } = state;
    const now = new Date();

    switch (reason) {
      case "rate_limit_minute":
        return Math.max(0, 60000 - (now.getTime() - state.minute_window.start.getTime()));

      case "rate_limit_hour":
        return Math.max(0, 3600000 - (now.getTime() - state.hour_window.start.getTime()));

      case "rate_limit_day":
        return Math.max(0, 86400000 - (now.getTime() - state.day_window.start.getTime()));

      case "cost_limit_minute":
        return Math.max(0, 60000 - (now.getTime() - state.minute_window.start.getTime()));

      case "cost_limit_hour":
        return Math.max(0, 3600000 - (now.getTime() - state.hour_window.start.getTime()));

      case "cost_limit_day":
        return Math.max(0, 86400000 - (now.getTime() - state.day_window.start.getTime()));

      case "cooldown_active":
        return usage.cooldown_until
          ? Math.max(0, usage.cooldown_until.getTime() - now.getTime())
          : rule.cooldown_ms || 1000;

      case "circuit_breaker_open":
        return this.config.circuit_breaker_reset_ms || 60000;

      case "global_budget_exceeded":
        return 86400000; // Wait until budget reset (manual)

      case "vendor_disabled":
        return Infinity;

      default:
        return rule.cooldown_ms || 1000;
    }
  }

  /**
   * Consume quota after successful check.
   */
  private consumeQuota(state: VendorState, cost: number): void {
    const { usage } = state;

    // Update call counts
    usage.calls_this_minute++;
    usage.calls_this_hour++;
    usage.calls_this_day++;
    usage.total_calls++;

    state.minute_window.calls++;
    state.hour_window.calls++;
    state.day_window.calls++;

    // Update costs
    usage.cost_this_minute += cost;
    usage.cost_this_hour += cost;
    usage.cost_this_day += cost;
    usage.total_cost += cost;

    state.minute_window.cost += cost;
    state.hour_window.cost += cost;
    state.day_window.cost += cost;

    // Update global
    this.globalCost += cost;
    this.globalCalls++;

    // Update timestamp
    usage.last_call_at = new Date();

    // Reset consecutive failures on success
    usage.consecutive_failures = 0;
    usage.backoff_multiplier = 1;
  }

  /**
   * Report a failure (for backoff and circuit breaker).
   */
  reportFailure(vendor: VendorId): void {
    const state = this.vendorStates.get(vendor);
    if (!state) return;

    const { usage, rule } = state;

    // Increment failure count
    usage.consecutive_failures++;
    state.circuit_breaker_failures++;

    // Apply exponential backoff
    if (rule.exponential_backoff) {
      const maxMultiplier = rule.max_backoff_multiplier || 8;
      usage.backoff_multiplier = Math.min(usage.backoff_multiplier * 2, maxMultiplier);
    }

    // Set cooldown
    const cooldownMs = (rule.cooldown_ms || 1000) * usage.backoff_multiplier;
    usage.cooldown_until = new Date(Date.now() + cooldownMs);

    // Check circuit breaker
    if (state.circuit_breaker_failures >= state.circuit_breaker_threshold) {
      state.circuit_breaker_open = true;

      // Schedule circuit breaker reset
      setTimeout(() => {
        state.circuit_breaker_open = false;
        state.circuit_breaker_failures = 0;
      }, this.config.circuit_breaker_reset_ms || 60000);

      if (this.config.verbose) {
        console.log(`[ThrottleManagerV2] CIRCUIT BREAKER OPEN: ${vendor}`);
      }
    }

    if (this.config.verbose) {
      console.log(`[ThrottleManagerV2] Failure reported: ${vendor} (consecutive: ${usage.consecutive_failures}, cooldown: ${cooldownMs}ms)`);
    }
  }

  /**
   * Report a success (reset failure counters).
   */
  reportSuccess(vendor: VendorId): void {
    const state = this.vendorStates.get(vendor);
    if (!state) return;

    state.usage.consecutive_failures = 0;
    state.usage.backoff_multiplier = 1;
    state.circuit_breaker_failures = Math.max(0, state.circuit_breaker_failures - 1);
  }

  /**
   * Disable a vendor.
   */
  disableVendor(vendor: VendorId): void {
    const state = this.vendorStates.get(vendor);
    if (state) {
      state.enabled = false;
      if (this.config.verbose) {
        console.log(`[ThrottleManagerV2] Vendor disabled: ${vendor}`);
      }
    }
  }

  /**
   * Enable a vendor.
   */
  enableVendor(vendor: VendorId): void {
    const state = this.vendorStates.get(vendor);
    if (state) {
      state.enabled = true;
      if (this.config.verbose) {
        console.log(`[ThrottleManagerV2] Vendor enabled: ${vendor}`);
      }
    }
  }

  /**
   * Simple isAllowed check (convenience method).
   * Returns true if call is permitted, false if blocked.
   */
  isAllowed(vendor: VendorId | string, cost: number = 0): boolean {
    const vendorId = vendor as VendorId;
    const state = this.vendorStates.get(vendorId);
    if (!state) return false;

    this.refreshWindows(state);
    const blockReason = this.checkLimits(state, cost);
    return blockReason === null;
  }

  /**
   * Set or update a rule for a vendor (convenience method).
   */
  setRule(vendor: VendorId | string, rule: ThrottleRule): void {
    const vendorId = vendor as VendorId;
    let state = this.vendorStates.get(vendorId);

    if (!state) {
      // Create new vendor state
      state = this.createVendorState(rule);
      this.vendorStates.set(vendorId, state);
    } else {
      // Merge with existing rule
      state.rule = { ...state.rule, ...rule };
    }

    if (this.config.verbose) {
      console.log(`[ThrottleManagerV2] Rule set for ${vendor}:`, rule);
    }
  }

  /**
   * Record a call after it happens (for history tracking).
   * Use this instead of checkAndConsume if you manage throttling externally.
   */
  record(vendor: VendorId | string, agent: string, cost: number): void {
    const vendorId = vendor as VendorId;
    const state = this.vendorStates.get(vendorId);

    if (state) {
      this.refreshWindows(state);
      this.consumeQuota(state, cost);
    }

    // Add to history
    const entry: CallEntry = {
      vendor: vendorId,
      agent,
      cost,
      timestamp: Date.now(),
      permitted: true,
    };

    this.callHistory.push(entry);

    // Trim history if needed
    if (this.callHistory.length > this.maxHistoryEntries) {
      this.callHistory = this.callHistory.slice(-this.maxHistoryEntries);
    }

    if (this.config.verbose) {
      console.log(`[ThrottleManagerV2] Recorded: ${vendor}/${agent} ($${cost.toFixed(4)})`);
    }
  }

  /**
   * Record a blocked call to history.
   */
  recordBlocked(vendor: VendorId | string, agent: string, cost: number, reason: ThrottleBlockReason): void {
    const entry: CallEntry = {
      vendor: vendor as VendorId,
      agent,
      cost,
      timestamp: Date.now(),
      permitted: false,
      blockReason: reason,
    };

    this.callHistory.push(entry);

    // Trim history if needed
    if (this.callHistory.length > this.maxHistoryEntries) {
      this.callHistory = this.callHistory.slice(-this.maxHistoryEntries);
    }
  }

  /**
   * Get call history.
   */
  getHistory(options?: {
    vendor?: VendorId;
    agent?: string;
    since?: number;
    limit?: number;
  }): CallEntry[] {
    let history = [...this.callHistory];

    if (options?.vendor) {
      history = history.filter((e) => e.vendor === options.vendor);
    }
    if (options?.agent) {
      history = history.filter((e) => e.agent === options.agent);
    }
    if (options?.since) {
      history = history.filter((e) => e.timestamp >= options.since);
    }
    if (options?.limit) {
      history = history.slice(-options.limit);
    }

    return history;
  }

  /**
   * Get diagnostics for a vendor or all vendors.
   */
  getDiagnostics(vendor?: VendorId | string): {
    vendor?: string;
    enabled: boolean;
    circuitBreakerOpen: boolean;
    cooldownActive: boolean;
    cooldownUntil: Date | null;
    consecutiveFailures: number;
    backoffMultiplier: number;
    usage: {
      minute: { calls: number; cost: number; limit?: number; costLimit?: number };
      hour: { calls: number; cost: number; limit?: number; costLimit?: number };
      day: { calls: number; cost: number; limit?: number; costLimit?: number };
      total: { calls: number; cost: number };
    };
    recentCalls: CallEntry[];
  } | Record<string, any> {
    if (vendor) {
      const vendorId = vendor as VendorId;
      const state = this.vendorStates.get(vendorId);
      if (!state) {
        return { error: `Unknown vendor: ${vendor}` };
      }

      this.refreshWindows(state);
      const { usage, rule } = state;

      return {
        vendor: vendorId,
        enabled: state.enabled,
        circuitBreakerOpen: state.circuit_breaker_open,
        cooldownActive: usage.cooldown_until !== null && new Date() < usage.cooldown_until,
        cooldownUntil: usage.cooldown_until,
        consecutiveFailures: usage.consecutive_failures,
        backoffMultiplier: usage.backoff_multiplier,
        usage: {
          minute: {
            calls: usage.calls_this_minute,
            cost: usage.cost_this_minute,
            limit: rule.max_calls_per_minute,
            costLimit: rule.max_cost_per_minute,
          },
          hour: {
            calls: usage.calls_this_hour,
            cost: usage.cost_this_hour,
            limit: rule.max_calls_per_hour,
            costLimit: rule.max_cost_per_hour,
          },
          day: {
            calls: usage.calls_this_day,
            cost: usage.cost_this_day,
            limit: rule.max_calls_per_day,
            costLimit: rule.max_cost_per_day,
          },
          total: {
            calls: usage.total_calls,
            cost: usage.total_cost,
          },
        },
        recentCalls: this.getHistory({ vendor: vendorId, limit: 10 }),
      };
    }

    // Return all vendor diagnostics
    const result: Record<string, any> = {
      global: this.getGlobalStats(),
      vendors: {},
    };

    for (const [v] of this.vendorStates) {
      result.vendors[v] = this.getDiagnostics(v);
    }

    return result;
  }

  /**
   * Get usage for a vendor.
   */
  getVendorUsage(vendor: VendorId): VendorUsage | null {
    const state = this.vendorStates.get(vendor);
    if (!state) return null;

    this.refreshWindows(state);
    return { ...state.usage };
  }

  /**
   * Get usage for all vendors.
   */
  getAllUsage(): Record<VendorId, VendorUsage> {
    const result: Partial<Record<VendorId, VendorUsage>> = {};

    for (const [vendor, state] of this.vendorStates) {
      this.refreshWindows(state);
      result[vendor] = { ...state.usage };
    }

    return result as Record<VendorId, VendorUsage>;
  }

  /**
   * Get global statistics.
   */
  getGlobalStats(): {
    total_calls: number;
    total_cost: number;
    budget_remaining: number;
    budget_used_percent: number;
    uptime_ms: number;
    vendors_enabled: number;
    vendors_disabled: number;
    circuit_breakers_open: number;
  } {
    let enabledCount = 0;
    let disabledCount = 0;
    let circuitBreakersOpen = 0;

    for (const state of this.vendorStates.values()) {
      if (state.enabled) enabledCount++;
      else disabledCount++;
      if (state.circuit_breaker_open) circuitBreakersOpen++;
    }

    return {
      total_calls: this.globalCalls,
      total_cost: this.globalCost,
      budget_remaining: this.config.global_budget - this.globalCost,
      budget_used_percent: (this.globalCost / this.config.global_budget) * 100,
      uptime_ms: Date.now() - this.startTime.getTime(),
      vendors_enabled: enabledCount,
      vendors_disabled: disabledCount,
      circuit_breakers_open: circuitBreakersOpen,
    };
  }

  /**
   * Update vendor rule.
   */
  updateVendorRule(vendor: VendorId, rule: Partial<ThrottleRule>): void {
    const state = this.vendorStates.get(vendor);
    if (state) {
      state.rule = { ...state.rule, ...rule };
      if (this.config.verbose) {
        console.log(`[ThrottleManagerV2] Rule updated: ${vendor}`, rule);
      }
    }
  }

  /**
   * Update global budget.
   */
  updateGlobalBudget(budget: number): void {
    this.config.global_budget = budget;
    if (this.config.verbose) {
      console.log(`[ThrottleManagerV2] Global budget updated: $${budget}`);
    }
  }

  /**
   * Reset all counters (for testing or daily reset).
   */
  reset(): void {
    this.globalCost = 0;
    this.globalCalls = 0;
    this.startTime = new Date();

    for (const [vendor, state] of this.vendorStates) {
      this.vendorStates.set(vendor, this.createVendorState(state.rule));
    }

    if (this.config.verbose) {
      console.log("[ThrottleManagerV2] Reset complete");
    }
  }

  /**
   * Reset a specific vendor.
   */
  resetVendor(vendor: VendorId): void {
    const state = this.vendorStates.get(vendor);
    if (state) {
      this.vendorStates.set(vendor, this.createVendorState(state.rule));
      if (this.config.verbose) {
        console.log(`[ThrottleManagerV2] Vendor reset: ${vendor}`);
      }
    }
  }

  /**
   * Wait for throttle to clear (async helper).
   */
  async waitForClearance(vendor: VendorId, cost: number = 0, maxWaitMs: number = 60000): Promise<ThrottleCheckResult> {
    const startTime = Date.now();

    while (Date.now() - startTime < maxWaitMs) {
      const result = await this.checkAndConsume(vendor, cost);
      if (result.permitted) {
        return result;
      }

      const waitTime = Math.min(result.wait_ms || 1000, maxWaitMs - (Date.now() - startTime));
      if (waitTime <= 0) break;

      await new Promise((resolve) => setTimeout(resolve, waitTime));
    }

    // Final check
    return this.check(vendor, cost);
  }

  /**
   * Generate diagnostic report.
   */
  generateReport(): string {
    const lines: string[] = [];
    const stats = this.getGlobalStats();

    lines.push("=".repeat(70));
    lines.push("THROTTLE MANAGER V2 - DIAGNOSTIC REPORT");
    lines.push("=".repeat(70));
    lines.push("");

    lines.push("GLOBAL STATUS");
    lines.push("-".repeat(50));
    lines.push(`  Total Calls:         ${stats.total_calls}`);
    lines.push(`  Total Cost:          $${stats.total_cost.toFixed(4)}`);
    lines.push(`  Budget Remaining:    $${stats.budget_remaining.toFixed(4)}`);
    lines.push(`  Budget Used:         ${stats.budget_used_percent.toFixed(1)}%`);
    lines.push(`  Uptime:              ${Math.round(stats.uptime_ms / 1000)}s`);
    lines.push(`  Vendors Enabled:     ${stats.vendors_enabled}`);
    lines.push(`  Vendors Disabled:    ${stats.vendors_disabled}`);
    lines.push(`  Circuit Breakers:    ${stats.circuit_breakers_open} open`);
    lines.push("");

    lines.push("VENDOR STATUS");
    lines.push("-".repeat(50));

    for (const [vendor, state] of this.vendorStates) {
      this.refreshWindows(state);
      const { usage, rule } = state;

      if (usage.total_calls === 0 && !state.circuit_breaker_open) continue;

      const status = !state.enabled
        ? "DISABLED"
        : state.circuit_breaker_open
        ? "CIRCUIT OPEN"
        : usage.cooldown_until
        ? "COOLDOWN"
        : "ACTIVE";

      lines.push(`  ${vendor.toUpperCase()}`);
      lines.push(`    Status: ${status}`);
      lines.push(`    Calls: ${usage.calls_this_minute}/min, ${usage.calls_this_hour}/hr, ${usage.calls_this_day}/day`);
      lines.push(`    Cost:  $${usage.cost_this_minute.toFixed(4)}/min, $${usage.cost_this_hour.toFixed(4)}/hr, $${usage.cost_this_day.toFixed(4)}/day`);
      lines.push(`    Total: ${usage.total_calls} calls, $${usage.total_cost.toFixed(4)}`);

      if (rule.max_calls_per_minute) {
        const pctUsed = (usage.calls_this_minute / rule.max_calls_per_minute) * 100;
        lines.push(`    Rate Limit (min): ${usage.calls_this_minute}/${rule.max_calls_per_minute} (${pctUsed.toFixed(0)}%)`);
      }

      lines.push("");
    }

    lines.push("=".repeat(70));

    return lines.join("\n");
  }

  /**
   * Get configuration.
   */
  getConfig(): ThrottleManagerV2Config {
    return { ...this.config };
  }
}

/**
 * Global throttle manager instance.
 */
export const globalThrottleManager = new ThrottleManagerV2();

/**
 * Create a throttle manager with custom config.
 */
export function createThrottleManager(config?: Partial<ThrottleManagerV2Config>): ThrottleManagerV2 {
  return new ThrottleManagerV2(config);
}
