/**
 * Fail Manager Logic
 * ==================
 * Handles temporary and permanent failures in the pipeline.
 * Implements retry logic with exponential backoff.
 */

import { SlotRow, AgentResult } from "../models/SlotRow";

/**
 * Failure type classification.
 */
export type FailureType =
  | "TEMPORARY"    // Can retry (rate limit, timeout)
  | "PERMANENT"    // Cannot retry (invalid data, not found)
  | "UNKNOWN";     // Needs investigation

/**
 * Failure classification rules.
 */
const PERMANENT_ERROR_PATTERNS = [
  "not found",
  "invalid",
  "does not exist",
  "permanently",
  "no longer available",
  "deleted",
  "blocked",
];

const TEMPORARY_ERROR_PATTERNS = [
  "timeout",
  "rate limit",
  "throttle",
  "temporarily",
  "try again",
  "service unavailable",
  "connection",
  "network",
];

/**
 * Fail manager configuration.
 */
export interface FailManagerConfig {
  /** Maximum retries before permanent failure */
  max_retries: number;
  /** Base delay between retries (ms) */
  base_delay_ms: number;
  /** Maximum delay between retries (ms) */
  max_delay_ms: number;
  /** Multiplier for exponential backoff */
  backoff_multiplier: number;
}

/**
 * Default fail manager configuration.
 */
export const DEFAULT_FAIL_CONFIG: FailManagerConfig = {
  max_retries: 3,
  base_delay_ms: 1000,
  max_delay_ms: 30000,
  backoff_multiplier: 2,
};

/**
 * Failure record for tracking.
 */
export interface FailureRecord {
  row_id: string;
  agent_type: string;
  failure_type: FailureType;
  error_message: string;
  attempt_count: number;
  first_failure_at: Date;
  last_failure_at: Date;
  next_retry_at: Date | null;
  is_permanent: boolean;
}

/**
 * FailManager class for handling pipeline failures.
 */
export class FailManager {
  private config: FailManagerConfig;
  private failures: Map<string, FailureRecord>;

  constructor(config: FailManagerConfig = DEFAULT_FAIL_CONFIG) {
    this.config = config;
    this.failures = new Map();
  }

  /**
   * Classify an error message into failure type.
   */
  classifyError(errorMessage: string): FailureType {
    const lowerError = errorMessage.toLowerCase();

    // Check permanent patterns first
    for (const pattern of PERMANENT_ERROR_PATTERNS) {
      if (lowerError.includes(pattern)) {
        return "PERMANENT";
      }
    }

    // Check temporary patterns
    for (const pattern of TEMPORARY_ERROR_PATTERNS) {
      if (lowerError.includes(pattern)) {
        return "TEMPORARY";
      }
    }

    return "UNKNOWN";
  }

  /**
   * Record a failure from an agent result.
   */
  recordFailure(row: SlotRow, result: AgentResult): FailureRecord {
    const key = `${row.id}:${result.agent_type}`;
    const errorMessage = result.error ?? "Unknown error";
    const failureType = this.classifyError(errorMessage);

    const existing = this.failures.get(key);
    const now = new Date();

    if (existing) {
      // Update existing record
      existing.attempt_count++;
      existing.last_failure_at = now;
      existing.error_message = errorMessage;
      existing.failure_type = failureType;

      // Check if should become permanent
      if (
        failureType === "PERMANENT" ||
        existing.attempt_count >= this.config.max_retries
      ) {
        existing.is_permanent = true;
        existing.next_retry_at = null;
      } else {
        existing.next_retry_at = this.calculateNextRetry(existing.attempt_count);
      }

      // Update row
      row.failure_count = existing.attempt_count;
      row.last_failure_reason = errorMessage;
      row.permanently_failed = existing.is_permanent;

      return existing;
    }

    // Create new record
    const record: FailureRecord = {
      row_id: row.id,
      agent_type: result.agent_type,
      failure_type: failureType,
      error_message: errorMessage,
      attempt_count: 1,
      first_failure_at: now,
      last_failure_at: now,
      next_retry_at:
        failureType === "PERMANENT" ? null : this.calculateNextRetry(1),
      is_permanent: failureType === "PERMANENT",
    };

    this.failures.set(key, record);

    // Update row
    row.failure_count = 1;
    row.last_failure_reason = errorMessage;
    row.permanently_failed = record.is_permanent;

    return record;
  }

  /**
   * Calculate next retry time based on attempt count.
   */
  private calculateNextRetry(attemptCount: number): Date {
    const delay = Math.min(
      this.config.base_delay_ms *
        Math.pow(this.config.backoff_multiplier, attemptCount - 1),
      this.config.max_delay_ms
    );

    return new Date(Date.now() + delay);
  }

  /**
   * Check if a row can be retried.
   */
  canRetry(row: SlotRow, agentType: string): boolean {
    const key = `${row.id}:${agentType}`;
    const record = this.failures.get(key);

    if (!record) return true; // No previous failure

    if (record.is_permanent) return false;

    if (record.next_retry_at && record.next_retry_at > new Date()) {
      return false; // Not yet time to retry
    }

    return true;
  }

  /**
   * Get time until next retry (ms).
   */
  getTimeUntilRetry(row: SlotRow, agentType: string): number | null {
    const key = `${row.id}:${agentType}`;
    const record = this.failures.get(key);

    if (!record || record.is_permanent) return null;

    if (!record.next_retry_at) return 0;

    const remaining = record.next_retry_at.getTime() - Date.now();
    return Math.max(0, remaining);
  }

  /**
   * Clear failure record (for manual reset).
   */
  clearFailure(row: SlotRow, agentType: string): void {
    const key = `${row.id}:${agentType}`;
    this.failures.delete(key);

    // Reset row failure state
    row.failure_count = 0;
    row.last_failure_reason = null;
    row.permanently_failed = false;
    row.last_updated = new Date();
  }

  /**
   * Clear all failures for a row.
   */
  clearAllFailures(row: SlotRow): void {
    const keysToDelete: string[] = [];

    for (const key of this.failures.keys()) {
      if (key.startsWith(`${row.id}:`)) {
        keysToDelete.push(key);
      }
    }

    for (const key of keysToDelete) {
      this.failures.delete(key);
    }

    // Reset row failure state
    row.resetFailure();
  }

  /**
   * Get all permanent failures.
   */
  getPermanentFailures(): FailureRecord[] {
    return Array.from(this.failures.values()).filter((r) => r.is_permanent);
  }

  /**
   * Get all temporary failures.
   */
  getTemporaryFailures(): FailureRecord[] {
    return Array.from(this.failures.values()).filter((r) => !r.is_permanent);
  }

  /**
   * Get failures ready for retry.
   */
  getFailuresReadyForRetry(): FailureRecord[] {
    const now = new Date();
    return Array.from(this.failures.values()).filter(
      (r) => !r.is_permanent && r.next_retry_at && r.next_retry_at <= now
    );
  }

  /**
   * Get failure statistics.
   */
  getStats(): {
    total: number;
    permanent: number;
    temporary: number;
    ready_for_retry: number;
  } {
    const all = Array.from(this.failures.values());
    const now = new Date();

    return {
      total: all.length,
      permanent: all.filter((r) => r.is_permanent).length,
      temporary: all.filter((r) => !r.is_permanent).length,
      ready_for_retry: all.filter(
        (r) => !r.is_permanent && r.next_retry_at && r.next_retry_at <= now
      ).length,
    };
  }

  /**
   * Get status string.
   */
  getStatusString(): string {
    const stats = this.getStats();
    return `Failures: ${stats.total} total (${stats.permanent} permanent, ${stats.temporary} temp, ${stats.ready_for_retry} ready)`;
  }
}

/**
 * Global fail manager instance.
 */
export const globalFailManager = new FailManager();
