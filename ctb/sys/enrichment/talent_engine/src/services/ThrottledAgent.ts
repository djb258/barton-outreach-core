/**
 * ThrottledAgent
 * ==============
 * Base class and decorators for throttle-aware agents.
 *
 * Provides:
 * - Automatic throttle checking before API calls
 * - Cost tracking and reporting
 * - Automatic retry with backoff
 * - Integration with failure routing
 * - Cooldown management
 *
 * Usage:
 * ```typescript
 * // Method 1: Extend ThrottledAgentBase
 * class MyAgent extends ThrottledAgentBase {
 *   protected vendor: VendorId = "proxycurl";
 *   protected baseCost: number = 0.01;
 *
 *   async executeThrottled(task: MyTask): Promise<MyResult> {
 *     // Your API call here
 *   }
 * }
 *
 * // Method 2: Use decorator
 * class MyAgent {
 *   @throttled("hunter", 0.005)
 *   async lookupEmail(domain: string): Promise<string> {
 *     // Your API call here
 *   }
 * }
 *
 * // Method 3: Use wrapper function
 * const result = await withThrottle("proxycurl", 0.01, async () => {
 *   return await proxycurlService.getProfile(url);
 * });
 * ```
 */

import {
  ThrottleManagerV2,
  VendorId,
  ThrottleCheckResult,
  globalThrottleManager,
} from "./ThrottleManagerV2";
import { CostGovernor, globalCostGovernor } from "./CostGovernor";
import {
  ThrottleError,
  createThrottleError,
  isThrottleError,
} from "./ThrottleError";
import { FailureRouter, globalFailureRouter } from "./FailureRouter";
import { FailureNode, FailureAgentType } from "../models/FailureRecord";
import { SlotRow } from "../models/SlotRow";

/**
 * Throttled execution options.
 */
export interface ThrottledExecutionOptions {
  /** Vendor to throttle against */
  vendor: VendorId;
  /** Cost of the operation ($) */
  cost: number;
  /** Company ID for budget tracking */
  companyId?: string;
  /** Operation name for tracking */
  operation?: string;
  /** Maximum retries */
  maxRetries?: number;
  /** Retry delay base (ms) */
  retryDelayMs?: number;
  /** Whether to auto-retry on throttle */
  autoRetry?: boolean;
  /** Maximum wait time for clearance (ms) */
  maxWaitMs?: number;
  /** Agent type for failure routing */
  agentType?: FailureAgentType;
  /** Node for failure routing */
  node?: FailureNode;
  /** Slot row being processed */
  slotRow?: SlotRow;
  /** Custom throttle manager */
  throttleManager?: ThrottleManagerV2;
  /** Custom cost governor */
  costGovernor?: CostGovernor;
  /** Custom failure router */
  failureRouter?: FailureRouter;
}

/**
 * Throttled execution result.
 */
export interface ThrottledExecutionResult<T> {
  success: boolean;
  result?: T;
  error?: Error | ThrottleError;
  throttled: boolean;
  retries: number;
  cost: number;
  waitedMs: number;
}

/**
 * Execute a function with throttling.
 */
export async function withThrottle<T>(
  vendor: VendorId,
  cost: number,
  fn: () => Promise<T>,
  options?: Partial<ThrottledExecutionOptions>
): Promise<ThrottledExecutionResult<T>> {
  const throttleManager = options?.throttleManager || globalThrottleManager;
  const costGovernor = options?.costGovernor || globalCostGovernor;
  const failureRouter = options?.failureRouter || globalFailureRouter;

  const maxRetries = options?.maxRetries ?? 3;
  const autoRetry = options?.autoRetry ?? true;
  const maxWaitMs = options?.maxWaitMs ?? 60000;

  let retries = 0;
  let totalWaitedMs = 0;
  const startTime = Date.now();

  while (retries <= maxRetries) {
    // Check throttle
    const checkResult = await throttleManager.checkAndConsume(vendor, cost);

    if (!checkResult.permitted) {
      // Create throttle error
      const throttleError = createThrottleError(
        vendor,
        checkResult.reason!,
        checkResult.wait_ms || 1000,
        {
          usage: checkResult.usage,
          agentType: options?.agentType,
          node: options?.node,
          slotRowId: options?.slotRow?.id,
        }
      );

      // Check if we should auto-retry
      if (autoRetry && throttleError.retryable && checkResult.wait_ms) {
        const waitTime = Math.min(checkResult.wait_ms, maxWaitMs - totalWaitedMs);

        if (waitTime > 0 && totalWaitedMs + waitTime <= maxWaitMs) {
          await new Promise((resolve) => setTimeout(resolve, waitTime));
          totalWaitedMs += waitTime;
          retries++;
          continue;
        }
      }

      // Route to failure bay if we can't retry
      if (options?.slotRow && options?.agentType) {
        await failureRouter.autoRoute(options.agentType, {
          reason: throttleError.message,
          slot_row_id: options.slotRow.id,
          slot_row: options.slotRow,
          ...throttleError.toFailureData(),
        } as any);
      }

      return {
        success: false,
        error: throttleError,
        throttled: true,
        retries,
        cost: 0,
        waitedMs: totalWaitedMs,
      };
    }

    // Check company budget if provided
    if (options?.companyId) {
      const budgetCheck = costGovernor.canSpend(
        options.companyId,
        vendor,
        cost,
        options.operation
      );

      if (!budgetCheck.allowed) {
        throttleManager.reportFailure(vendor); // Don't actually count the call

        return {
          success: false,
          error: new Error(`Budget check failed: ${budgetCheck.reason}`),
          throttled: true,
          retries,
          cost: 0,
          waitedMs: totalWaitedMs,
        };
      }
    }

    // Execute the function
    try {
      const result = await fn();

      // Record success
      throttleManager.reportSuccess(vendor);

      // Record spend
      if (options?.companyId) {
        costGovernor.recordSpend(
          options.companyId,
          vendor,
          cost,
          options.operation || "unknown",
          {
            slot_type: options.slotRow?.slot_type,
            person_name: options.slotRow?.person_name || undefined,
            success: true,
          }
        );
      }

      return {
        success: true,
        result,
        throttled: false,
        retries,
        cost,
        waitedMs: totalWaitedMs,
      };
    } catch (error) {
      // Report failure for backoff
      throttleManager.reportFailure(vendor);

      // Record failed spend
      if (options?.companyId) {
        costGovernor.recordSpend(
          options.companyId,
          vendor,
          cost,
          options.operation || "unknown",
          {
            slot_type: options.slotRow?.slot_type,
            person_name: options.slotRow?.person_name || undefined,
            success: false,
          }
        );
      }

      // Route to failure bay
      if (options?.slotRow && options?.agentType) {
        await failureRouter.autoRoute(options.agentType, {
          reason: error instanceof Error ? error.message : "Unknown error",
          slot_row_id: options.slotRow.id,
          slot_row: options.slotRow,
        } as any);
      }

      return {
        success: false,
        error: error instanceof Error ? error : new Error(String(error)),
        throttled: false,
        retries,
        cost, // Cost was consumed
        waitedMs: totalWaitedMs,
      };
    }
  }

  // Should not reach here, but handle gracefully
  return {
    success: false,
    error: new Error("Max retries exceeded"),
    throttled: true,
    retries,
    cost: 0,
    waitedMs: totalWaitedMs,
  };
}

/**
 * Decorator for throttled methods.
 */
export function throttled(
  vendor: VendorId,
  cost: number,
  options?: Partial<ThrottledExecutionOptions>
) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const result = await withThrottle(
        vendor,
        cost,
        () => originalMethod.apply(this, args),
        {
          ...options,
          operation: options?.operation || `${target.constructor.name}.${propertyKey}`,
        }
      );

      if (!result.success) {
        throw result.error;
      }

      return result.result;
    };

    return descriptor;
  };
}

/**
 * Base configuration for throttled agents.
 */
export interface ThrottledAgentConfig {
  /** Vendor for this agent */
  vendor: VendorId;
  /** Base cost per operation */
  baseCost: number;
  /** Agent type for failure routing */
  agentType: FailureAgentType;
  /** Node for failure routing */
  node: FailureNode;
  /** Enable verbose logging */
  verbose?: boolean;
  /** Custom throttle manager */
  throttleManager?: ThrottleManagerV2;
  /** Custom cost governor */
  costGovernor?: CostGovernor;
  /** Custom failure router */
  failureRouter?: FailureRouter;
  /** Auto-retry on throttle */
  autoRetry?: boolean;
  /** Max retries */
  maxRetries?: number;
}

/**
 * Base class for throttled agents.
 */
export abstract class ThrottledAgentBase {
  protected vendor: VendorId;
  protected baseCost: number;
  protected agentType: FailureAgentType;
  protected node: FailureNode;
  protected verbose: boolean;
  protected throttleManager: ThrottleManagerV2;
  protected costGovernor: CostGovernor;
  protected failureRouter: FailureRouter;
  protected autoRetry: boolean;
  protected maxRetries: number;

  // Metrics
  protected callCount: number = 0;
  protected successCount: number = 0;
  protected failureCount: number = 0;
  protected throttleCount: number = 0;
  protected totalCost: number = 0;
  protected totalWaitTime: number = 0;

  constructor(config: ThrottledAgentConfig) {
    this.vendor = config.vendor;
    this.baseCost = config.baseCost;
    this.agentType = config.agentType;
    this.node = config.node;
    this.verbose = config.verbose ?? false;
    this.throttleManager = config.throttleManager || globalThrottleManager;
    this.costGovernor = config.costGovernor || globalCostGovernor;
    this.failureRouter = config.failureRouter || globalFailureRouter;
    this.autoRetry = config.autoRetry ?? true;
    this.maxRetries = config.maxRetries ?? 3;
  }

  /**
   * Execute a throttled operation.
   */
  protected async executeWithThrottle<T>(
    operation: string,
    cost: number,
    fn: () => Promise<T>,
    options?: {
      companyId?: string;
      slotRow?: SlotRow;
    }
  ): Promise<ThrottledExecutionResult<T>> {
    this.callCount++;

    const result = await withThrottle(this.vendor, cost, fn, {
      companyId: options?.companyId,
      operation,
      agentType: this.agentType,
      node: this.node,
      slotRow: options?.slotRow,
      throttleManager: this.throttleManager,
      costGovernor: this.costGovernor,
      failureRouter: this.failureRouter,
      autoRetry: this.autoRetry,
      maxRetries: this.maxRetries,
    });

    // Update metrics
    if (result.success) {
      this.successCount++;
    } else if (result.throttled) {
      this.throttleCount++;
    } else {
      this.failureCount++;
    }

    this.totalCost += result.cost;
    this.totalWaitTime += result.waitedMs;

    if (this.verbose) {
      console.log(
        `[${this.constructor.name}] ${operation}: ${result.success ? "SUCCESS" : "FAILED"} ` +
          `(throttled: ${result.throttled}, cost: $${result.cost.toFixed(4)}, waited: ${result.waitedMs}ms)`
      );
    }

    return result;
  }

  /**
   * Check if we can make a call.
   */
  protected async canMakeCall(cost: number = this.baseCost): Promise<ThrottleCheckResult> {
    return this.throttleManager.check(this.vendor, cost);
  }

  /**
   * Wait for throttle clearance.
   */
  protected async waitForClearance(
    cost: number = this.baseCost,
    maxWaitMs: number = 60000
  ): Promise<ThrottleCheckResult> {
    return this.throttleManager.waitForClearance(this.vendor, cost, maxWaitMs);
  }

  /**
   * Get agent metrics.
   */
  getMetrics(): {
    vendor: VendorId;
    call_count: number;
    success_count: number;
    failure_count: number;
    throttle_count: number;
    success_rate: number;
    throttle_rate: number;
    total_cost: number;
    total_wait_time_ms: number;
    avg_cost: number;
  } {
    const successRate = this.callCount > 0 ? (this.successCount / this.callCount) * 100 : 0;
    const throttleRate = this.callCount > 0 ? (this.throttleCount / this.callCount) * 100 : 0;

    return {
      vendor: this.vendor,
      call_count: this.callCount,
      success_count: this.successCount,
      failure_count: this.failureCount,
      throttle_count: this.throttleCount,
      success_rate: successRate,
      throttle_rate: throttleRate,
      total_cost: this.totalCost,
      total_wait_time_ms: this.totalWaitTime,
      avg_cost: this.callCount > 0 ? this.totalCost / this.callCount : 0,
    };
  }

  /**
   * Reset metrics.
   */
  resetMetrics(): void {
    this.callCount = 0;
    this.successCount = 0;
    this.failureCount = 0;
    this.throttleCount = 0;
    this.totalCost = 0;
    this.totalWaitTime = 0;
  }

  /**
   * Get vendor usage.
   */
  getVendorUsage() {
    return this.throttleManager.getVendorUsage(this.vendor);
  }
}

/**
 * Create a throttled wrapper for any async function.
 */
export function createThrottledFunction<TArgs extends any[], TResult>(
  vendor: VendorId,
  cost: number,
  fn: (...args: TArgs) => Promise<TResult>,
  options?: Partial<ThrottledExecutionOptions>
): (...args: TArgs) => Promise<ThrottledExecutionResult<TResult>> {
  return async (...args: TArgs) => {
    return withThrottle(vendor, cost, () => fn(...args), options);
  };
}

/**
 * Batch execute with throttling (respects rate limits).
 */
export async function batchWithThrottle<T, R>(
  vendor: VendorId,
  items: T[],
  cost: number,
  fn: (item: T) => Promise<R>,
  options?: Partial<ThrottledExecutionOptions> & {
    concurrency?: number;
    onProgress?: (completed: number, total: number) => void;
  }
): Promise<ThrottledExecutionResult<R>[]> {
  const results: ThrottledExecutionResult<R>[] = [];
  const concurrency = options?.concurrency ?? 1;

  // Process in batches respecting concurrency
  for (let i = 0; i < items.length; i += concurrency) {
    const batch = items.slice(i, i + concurrency);

    const batchResults = await Promise.all(
      batch.map((item) =>
        withThrottle(vendor, cost, () => fn(item), options)
      )
    );

    results.push(...batchResults);

    if (options?.onProgress) {
      options.onProgress(results.length, items.length);
    }

    // If any were throttled, add a small delay before next batch
    if (batchResults.some((r) => r.throttled)) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  }

  return results;
}
