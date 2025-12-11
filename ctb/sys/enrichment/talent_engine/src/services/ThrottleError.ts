/**
 * ThrottleError
 * =============
 * Error types for throttling and cost governance.
 *
 * Provides:
 * - Typed error classes for throttle blocks
 * - Integration with failure routing system
 * - Automatic retry scheduling
 * - Cooldown management
 *
 * Error Types:
 * - RateLimitError: Call count exceeded
 * - CostLimitError: Spend limit exceeded
 * - BudgetExceededError: Global budget exceeded
 * - CircuitBreakerError: Too many failures
 * - VendorDisabledError: Vendor has been disabled
 */

import { FailureBay, FailureAgentType, FailureNode } from "../models/FailureRecord";
import { ThrottleBlockReason, VendorId, VendorUsage } from "./ThrottleManagerV2";

/**
 * Base throttle error.
 */
export class ThrottleError extends Error {
  /** Error code for categorization */
  readonly code: string;
  /** Vendor that was throttled */
  readonly vendor: VendorId;
  /** Reason for throttle */
  readonly reason: ThrottleBlockReason;
  /** Wait time before retry (ms) */
  readonly waitMs: number;
  /** Whether this error is retryable */
  readonly retryable: boolean;
  /** Suggested failure bay for routing */
  readonly failureBay: FailureBay;
  /** Current usage stats */
  readonly usage?: VendorUsage;
  /** Timestamp when throttle was triggered */
  readonly timestamp: Date;
  /** Agent that triggered the error */
  readonly agentType?: FailureAgentType;
  /** Node where error occurred */
  readonly node?: FailureNode;
  /** Associated slot row ID */
  readonly slotRowId?: string;

  constructor(
    message: string,
    options: {
      code: string;
      vendor: VendorId;
      reason: ThrottleBlockReason;
      waitMs: number;
      retryable?: boolean;
      failureBay?: FailureBay;
      usage?: VendorUsage;
      agentType?: FailureAgentType;
      node?: FailureNode;
      slotRowId?: string;
    }
  ) {
    super(message);
    this.name = "ThrottleError";
    this.code = options.code;
    this.vendor = options.vendor;
    this.reason = options.reason;
    this.waitMs = options.waitMs;
    this.retryable = options.retryable ?? true;
    this.failureBay = options.failureBay || "agent_failures";
    this.usage = options.usage;
    this.timestamp = new Date();
    this.agentType = options.agentType;
    this.node = options.node;
    this.slotRowId = options.slotRowId;

    // Ensure prototype chain is correct
    Object.setPrototypeOf(this, ThrottleError.prototype);
  }

  /**
   * Get retry-after date.
   */
  getRetryAfter(): Date {
    return new Date(this.timestamp.getTime() + this.waitMs);
  }

  /**
   * Check if enough time has passed to retry.
   */
  canRetryNow(): boolean {
    return Date.now() >= this.getRetryAfter().getTime();
  }

  /**
   * Get remaining wait time (ms).
   */
  getRemainingWait(): number {
    return Math.max(0, this.getRetryAfter().getTime() - Date.now());
  }

  /**
   * Convert to failure record data.
   */
  toFailureData(): Record<string, unknown> {
    return {
      error_type: this.code,
      vendor: this.vendor,
      reason: this.reason,
      wait_ms: this.waitMs,
      retryable: this.retryable,
      timestamp: this.timestamp.toISOString(),
      retry_after: this.getRetryAfter().toISOString(),
      usage: this.usage,
      agent_type: this.agentType,
      node: this.node,
      slot_row_id: this.slotRowId,
    };
  }

  /**
   * Convert to JSON.
   */
  toJSON(): Record<string, unknown> {
    return {
      name: this.name,
      message: this.message,
      ...this.toFailureData(),
    };
  }
}

/**
 * Rate limit error (call count exceeded).
 */
export class RateLimitError extends ThrottleError {
  /** Which time window was exceeded */
  readonly window: "minute" | "hour" | "day";
  /** Current call count */
  readonly currentCalls: number;
  /** Maximum allowed calls */
  readonly maxCalls: number;

  constructor(
    vendor: VendorId,
    window: "minute" | "hour" | "day",
    currentCalls: number,
    maxCalls: number,
    waitMs: number,
    options?: {
      usage?: VendorUsage;
      agentType?: FailureAgentType;
      node?: FailureNode;
      slotRowId?: string;
    }
  ) {
    const reason: ThrottleBlockReason = `rate_limit_${window}` as ThrottleBlockReason;

    super(
      `Rate limit exceeded for ${vendor}: ${currentCalls}/${maxCalls} calls per ${window}`,
      {
        code: "RATE_LIMIT",
        vendor,
        reason,
        waitMs,
        retryable: true,
        failureBay: "agent_failures",
        ...options,
      }
    );

    this.name = "RateLimitError";
    this.window = window;
    this.currentCalls = currentCalls;
    this.maxCalls = maxCalls;

    Object.setPrototypeOf(this, RateLimitError.prototype);
  }
}

/**
 * Cost limit error (spend limit exceeded).
 */
export class CostLimitError extends ThrottleError {
  /** Which time window was exceeded */
  readonly window: "minute" | "hour" | "day";
  /** Current cost */
  readonly currentCost: number;
  /** Maximum allowed cost */
  readonly maxCost: number;
  /** Attempted spend amount */
  readonly attemptedAmount: number;

  constructor(
    vendor: VendorId,
    window: "minute" | "hour" | "day",
    currentCost: number,
    maxCost: number,
    attemptedAmount: number,
    waitMs: number,
    options?: {
      usage?: VendorUsage;
      agentType?: FailureAgentType;
      node?: FailureNode;
      slotRowId?: string;
    }
  ) {
    const reason: ThrottleBlockReason = `cost_limit_${window}` as ThrottleBlockReason;

    super(
      `Cost limit exceeded for ${vendor}: $${currentCost.toFixed(4)}/$${maxCost.toFixed(4)} per ${window}`,
      {
        code: "COST_LIMIT",
        vendor,
        reason,
        waitMs,
        retryable: true,
        failureBay: "agent_failures",
        ...options,
      }
    );

    this.name = "CostLimitError";
    this.window = window;
    this.currentCost = currentCost;
    this.maxCost = maxCost;
    this.attemptedAmount = attemptedAmount;

    Object.setPrototypeOf(this, CostLimitError.prototype);
  }
}

/**
 * Global budget exceeded error.
 */
export class BudgetExceededError extends ThrottleError {
  /** Current total spend */
  readonly currentSpend: number;
  /** Total budget */
  readonly budget: number;
  /** Budget type (daily/weekly/monthly/global) */
  readonly budgetType: string;

  constructor(
    budgetType: string,
    currentSpend: number,
    budget: number,
    options?: {
      vendor?: VendorId;
      agentType?: FailureAgentType;
      node?: FailureNode;
      slotRowId?: string;
    }
  ) {
    super(
      `${budgetType} budget exceeded: $${currentSpend.toFixed(2)}/$${budget.toFixed(2)}`,
      {
        code: "BUDGET_EXCEEDED",
        vendor: options?.vendor || "internal",
        reason: "global_budget_exceeded",
        waitMs: 86400000, // Wait until budget reset
        retryable: false,
        failureBay: "agent_failures",
        ...options,
      }
    );

    this.name = "BudgetExceededError";
    this.budgetType = budgetType;
    this.currentSpend = currentSpend;
    this.budget = budget;

    Object.setPrototypeOf(this, BudgetExceededError.prototype);
  }
}

/**
 * Circuit breaker error (too many consecutive failures).
 */
export class CircuitBreakerError extends ThrottleError {
  /** Number of consecutive failures */
  readonly failureCount: number;
  /** Threshold that triggered the breaker */
  readonly threshold: number;
  /** Time until circuit resets */
  readonly resetMs: number;

  constructor(
    vendor: VendorId,
    failureCount: number,
    threshold: number,
    resetMs: number,
    options?: {
      usage?: VendorUsage;
      agentType?: FailureAgentType;
      node?: FailureNode;
      slotRowId?: string;
    }
  ) {
    super(
      `Circuit breaker open for ${vendor}: ${failureCount} consecutive failures (threshold: ${threshold})`,
      {
        code: "CIRCUIT_BREAKER",
        vendor,
        reason: "circuit_breaker_open",
        waitMs: resetMs,
        retryable: true,
        failureBay: "agent_failures",
        ...options,
      }
    );

    this.name = "CircuitBreakerError";
    this.failureCount = failureCount;
    this.threshold = threshold;
    this.resetMs = resetMs;

    Object.setPrototypeOf(this, CircuitBreakerError.prototype);
  }
}

/**
 * Vendor disabled error.
 */
export class VendorDisabledError extends ThrottleError {
  /** Reason vendor was disabled */
  readonly disableReason?: string;

  constructor(
    vendor: VendorId,
    disableReason?: string,
    options?: {
      agentType?: FailureAgentType;
      node?: FailureNode;
      slotRowId?: string;
    }
  ) {
    super(
      `Vendor ${vendor} is disabled${disableReason ? `: ${disableReason}` : ""}`,
      {
        code: "VENDOR_DISABLED",
        vendor,
        reason: "vendor_disabled",
        waitMs: Infinity,
        retryable: false,
        failureBay: "agent_failures",
        ...options,
      }
    );

    this.name = "VendorDisabledError";
    this.disableReason = disableReason;

    Object.setPrototypeOf(this, VendorDisabledError.prototype);
  }
}

/**
 * Cooldown active error.
 */
export class CooldownActiveError extends ThrottleError {
  /** When cooldown started */
  readonly cooldownStarted: Date;
  /** When cooldown ends */
  readonly cooldownEnds: Date;
  /** Current backoff multiplier */
  readonly backoffMultiplier: number;

  constructor(
    vendor: VendorId,
    cooldownEnds: Date,
    backoffMultiplier: number,
    options?: {
      usage?: VendorUsage;
      agentType?: FailureAgentType;
      node?: FailureNode;
      slotRowId?: string;
    }
  ) {
    const waitMs = Math.max(0, cooldownEnds.getTime() - Date.now());

    super(
      `Cooldown active for ${vendor}: wait ${Math.round(waitMs / 1000)}s (backoff: ${backoffMultiplier}x)`,
      {
        code: "COOLDOWN_ACTIVE",
        vendor,
        reason: "cooldown_active",
        waitMs,
        retryable: true,
        failureBay: "agent_failures",
        ...options,
      }
    );

    this.name = "CooldownActiveError";
    this.cooldownStarted = new Date(cooldownEnds.getTime() - waitMs);
    this.cooldownEnds = cooldownEnds;
    this.backoffMultiplier = backoffMultiplier;

    Object.setPrototypeOf(this, CooldownActiveError.prototype);
  }
}

/**
 * Company budget exceeded error.
 */
export class CompanyBudgetExceededError extends ThrottleError {
  /** Company ID */
  readonly companyId: string;
  /** Current company spend */
  readonly companySpend: number;
  /** Company budget limit */
  readonly companyLimit: number;

  constructor(
    companyId: string,
    companySpend: number,
    companyLimit: number,
    options?: {
      vendor?: VendorId;
      agentType?: FailureAgentType;
      node?: FailureNode;
      slotRowId?: string;
    }
  ) {
    super(
      `Company budget exceeded for ${companyId}: $${companySpend.toFixed(2)}/$${companyLimit.toFixed(2)}`,
      {
        code: "COMPANY_BUDGET_EXCEEDED",
        vendor: options?.vendor || "internal",
        reason: "global_budget_exceeded",
        waitMs: 86400000, // Wait until daily reset
        retryable: false,
        failureBay: "agent_failures",
        ...options,
      }
    );

    this.name = "CompanyBudgetExceededError";
    this.companyId = companyId;
    this.companySpend = companySpend;
    this.companyLimit = companyLimit;

    Object.setPrototypeOf(this, CompanyBudgetExceededError.prototype);
  }
}

/**
 * Create appropriate error from throttle check result.
 */
export function createThrottleError(
  vendor: VendorId,
  reason: ThrottleBlockReason,
  waitMs: number,
  options?: {
    usage?: VendorUsage;
    agentType?: FailureAgentType;
    node?: FailureNode;
    slotRowId?: string;
    maxCalls?: number;
    maxCost?: number;
    attemptedCost?: number;
  }
): ThrottleError {
  const usage = options?.usage;

  switch (reason) {
    case "rate_limit_minute":
      return new RateLimitError(
        vendor,
        "minute",
        usage?.calls_this_minute || 0,
        options?.maxCalls || 0,
        waitMs,
        options
      );

    case "rate_limit_hour":
      return new RateLimitError(
        vendor,
        "hour",
        usage?.calls_this_hour || 0,
        options?.maxCalls || 0,
        waitMs,
        options
      );

    case "rate_limit_day":
      return new RateLimitError(
        vendor,
        "day",
        usage?.calls_this_day || 0,
        options?.maxCalls || 0,
        waitMs,
        options
      );

    case "cost_limit_minute":
      return new CostLimitError(
        vendor,
        "minute",
        usage?.cost_this_minute || 0,
        options?.maxCost || 0,
        options?.attemptedCost || 0,
        waitMs,
        options
      );

    case "cost_limit_hour":
      return new CostLimitError(
        vendor,
        "hour",
        usage?.cost_this_hour || 0,
        options?.maxCost || 0,
        options?.attemptedCost || 0,
        waitMs,
        options
      );

    case "cost_limit_day":
      return new CostLimitError(
        vendor,
        "day",
        usage?.cost_this_day || 0,
        options?.maxCost || 0,
        options?.attemptedCost || 0,
        waitMs,
        options
      );

    case "global_budget_exceeded":
      return new BudgetExceededError(
        "Global",
        usage?.total_cost || 0,
        options?.maxCost || 0,
        { vendor, ...options }
      );

    case "circuit_breaker_open":
      return new CircuitBreakerError(
        vendor,
        usage?.consecutive_failures || 0,
        5, // Default threshold
        waitMs,
        options
      );

    case "cooldown_active":
      return new CooldownActiveError(
        vendor,
        usage?.cooldown_until || new Date(Date.now() + waitMs),
        usage?.backoff_multiplier || 1,
        options
      );

    case "vendor_disabled":
      return new VendorDisabledError(vendor, undefined, options);

    default:
      return new ThrottleError(
        `Throttle blocked for ${vendor}: ${reason}`,
        {
          code: "THROTTLE_BLOCKED",
          vendor,
          reason,
          waitMs,
          ...options,
        }
      );
  }
}

/**
 * Check if an error is a throttle error.
 */
export function isThrottleError(error: unknown): error is ThrottleError {
  return error instanceof ThrottleError;
}

/**
 * Check if an error is retryable.
 */
export function isRetryableThrottleError(error: unknown): boolean {
  return isThrottleError(error) && error.retryable;
}

/**
 * Get failure bay for a throttle error.
 */
export function getFailureBayForThrottleError(error: ThrottleError): FailureBay {
  return error.failureBay;
}
