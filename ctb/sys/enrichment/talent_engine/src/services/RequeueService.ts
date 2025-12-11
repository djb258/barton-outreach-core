/**
 * RequeueService
 * ==============
 * Service for requeuing and fixing failed records.
 *
 * Provides the "Fix & Re-Run" functionality:
 * 1. requeue(bay, failureId) - Creates a resume job from an existing failure
 * 2. fixAndRerun(bay, failureId, fixedData) - Updates the slot row and requeues
 * 3. requeueAll(bay) - Requeue all unresolved failures in a bay
 * 4. fixAndRerunBatch(repairs) - Process multiple repairs at once
 *
 * Usage:
 * ```typescript
 * const requeueService = new RequeueService(failureRouter, dispatcher);
 *
 * // Simple requeue (retry with same data)
 * await requeueService.requeue("email_pattern_failures", "fail_123");
 *
 * // Fix and requeue (update data first)
 * await requeueService.fixAndRerun("email_pattern_failures", "fail_123", {
 *   company_domain: "corrected-domain.com",
 *   email_pattern: "{first}.{last}@corrected-domain.com"
 * });
 *
 * // Process all pending
 * await requeueService.processQueue(companyMaster);
 * ```
 */

import {
  FailureRouter,
  ResumeJob,
  RepairRequest,
} from "./FailureRouter";
import { NodeDispatcher, ResumeExecutionResult } from "../dispatcher/NodeDispatcher";
import {
  FailureBay,
  FailureRecord,
  getResumePointForBay,
} from "../models/FailureRecord";
import { SlotRow } from "../models/SlotRow";

/**
 * Repair result interface.
 */
export interface RepairResult {
  success: boolean;
  failureId: string;
  bay: FailureBay;
  jobId?: string;
  error?: string;
}

/**
 * Batch repair result.
 */
export interface BatchRepairResult {
  total: number;
  successful: number;
  failed: number;
  results: RepairResult[];
}

/**
 * Process queue result.
 */
export interface ProcessQueueResult {
  total: number;
  completed: number;
  failed: number;
  results: ResumeExecutionResult[];
}

/**
 * RequeueService configuration.
 */
export interface RequeueServiceConfig {
  /** Enable verbose logging */
  verbose: boolean;
  /** Maximum retries per failure */
  maxRetries: number;
  /** Auto-process queue after requeue */
  autoProcess: boolean;
}

/**
 * Default configuration.
 */
export const DEFAULT_REQUEUE_CONFIG: RequeueServiceConfig = {
  verbose: false,
  maxRetries: 3,
  autoProcess: false,
};

/**
 * RequeueService - Manages failure requeuing and repair workflow.
 */
export class RequeueService {
  private failureRouter: FailureRouter;
  private dispatcher: NodeDispatcher | null;
  private config: RequeueServiceConfig;

  constructor(
    failureRouter: FailureRouter,
    dispatcher?: NodeDispatcher,
    config?: Partial<RequeueServiceConfig>
  ) {
    this.failureRouter = failureRouter;
    this.dispatcher = dispatcher || null;
    this.config = {
      ...DEFAULT_REQUEUE_CONFIG,
      ...config,
    };
  }

  /**
   * Requeue a failure for retry (same data).
   *
   * Creates a resume job from an existing failure record.
   * The job will be processed when processQueue() is called.
   */
  requeue(bay: FailureBay, failureId: string): RepairResult {
    if (this.config.verbose) {
      console.log(`[RequeueService] Requeuing failure: ${failureId} from ${bay}`);
    }

    // Check retry count
    const failure = this.getFailure(bay, failureId);
    if (!failure) {
      return {
        success: false,
        failureId,
        bay,
        error: `Failure not found: ${failureId}`,
      };
    }

    if ((failure as any).attempts >= this.config.maxRetries) {
      return {
        success: false,
        failureId,
        bay,
        error: `Max retries (${this.config.maxRetries}) exceeded`,
      };
    }

    // Create resume job
    const job = this.failureRouter.createResumeJob(bay, failureId);
    if (!job) {
      return {
        success: false,
        failureId,
        bay,
        error: "Failed to create resume job (missing slot_row data?)",
      };
    }

    if (this.config.verbose) {
      console.log(`[RequeueService] Created resume job: ${job.id}`);
    }

    return {
      success: true,
      failureId,
      bay,
      jobId: job.id,
    };
  }

  /**
   * Fix a failure and requeue it.
   *
   * Updates the fixed_slot_row data and creates a resume job.
   */
  fixAndRerun(
    bay: FailureBay,
    failureId: string,
    fixedData: Partial<SlotRow> | Record<string, unknown>
  ): RepairResult {
    if (this.config.verbose) {
      console.log(`[RequeueService] Fix and rerun: ${failureId}`);
      console.log(`[RequeueService] Fixed data:`, fixedData);
    }

    // Get existing failure
    const failure = this.getFailure(bay, failureId);
    if (!failure) {
      return {
        success: false,
        failureId,
        bay,
        error: `Failure not found: ${failureId}`,
      };
    }

    // Merge fixed data with existing slot_row
    const existingSlotRow = (failure as any).slot_row || {};
    const mergedSlotRow = {
      ...existingSlotRow,
      ...fixedData,
    };

    // Update fixed_slot_row
    const updated = this.failureRouter.updateFixedSlotRow(bay, failureId, mergedSlotRow);
    if (!updated) {
      return {
        success: false,
        failureId,
        bay,
        error: "Failed to update fixed_slot_row",
      };
    }

    // Create resume job with fixed data
    const job = this.failureRouter.createResumeJob(bay, failureId, mergedSlotRow);
    if (!job) {
      return {
        success: false,
        failureId,
        bay,
        error: "Failed to create resume job",
      };
    }

    if (this.config.verbose) {
      console.log(`[RequeueService] Created resume job: ${job.id}`);
    }

    return {
      success: true,
      failureId,
      bay,
      jobId: job.id,
    };
  }

  /**
   * Requeue all unresolved failures in a bay.
   */
  requeueAll(bay: FailureBay): BatchRepairResult {
    const failures = this.failureRouter.getUnresolvedFailures(bay);
    const results: RepairResult[] = [];

    if (this.config.verbose) {
      console.log(`[RequeueService] Requeuing ${failures.length} failures from ${bay}`);
    }

    for (const failure of failures) {
      const failureId = (failure as any).id;
      const result = this.requeue(bay, failureId);
      results.push(result);
    }

    return {
      total: results.length,
      successful: results.filter((r) => r.success).length,
      failed: results.filter((r) => !r.success).length,
      results,
    };
  }

  /**
   * Process multiple repairs at once.
   */
  fixAndRerunBatch(
    repairs: Array<{
      bay: FailureBay;
      failureId: string;
      fixedData?: Record<string, unknown>;
    }>
  ): BatchRepairResult {
    const results: RepairResult[] = [];

    if (this.config.verbose) {
      console.log(`[RequeueService] Processing batch of ${repairs.length} repairs`);
    }

    for (const repair of repairs) {
      let result: RepairResult;

      if (repair.fixedData) {
        result = this.fixAndRerun(repair.bay, repair.failureId, repair.fixedData);
      } else {
        result = this.requeue(repair.bay, repair.failureId);
      }

      results.push(result);
    }

    return {
      total: results.length,
      successful: results.filter((r) => r.success).length,
      failed: results.filter((r) => !r.success).length,
      results,
    };
  }

  /**
   * Process all pending resume jobs.
   *
   * Requires a NodeDispatcher to be set.
   */
  async processQueue(companyMaster: string[] = []): Promise<ProcessQueueResult> {
    if (!this.dispatcher) {
      throw new Error("No NodeDispatcher configured. Cannot process queue.");
    }

    const results = await this.dispatcher.processAllResumeJobs(companyMaster);

    return {
      total: results.length,
      completed: results.filter((r) => r.success).length,
      failed: results.filter((r) => !r.success).length,
      results,
    };
  }

  /**
   * Process a single resume job.
   */
  async processJob(
    jobId: string,
    companyMaster: string[] = []
  ): Promise<ResumeExecutionResult | null> {
    if (!this.dispatcher) {
      throw new Error("No NodeDispatcher configured. Cannot process job.");
    }

    const job = this.failureRouter.getPendingResumeJobs().find((j) => j.id === jobId);
    if (!job) {
      return null;
    }

    return this.dispatcher.processResumeJob(job, companyMaster);
  }

  /**
   * Get a failure record.
   */
  private getFailure(bay: FailureBay, failureId: string): FailureRecord | null {
    const failures = this.failureRouter.getFailures(bay);
    return failures.find((f) => (f as any).id === failureId) || null;
  }

  /**
   * Get pending job count.
   */
  getPendingJobCount(): number {
    return this.failureRouter.getPendingResumeJobs().length;
  }

  /**
   * Get queue statistics.
   */
  getQueueStats(): {
    total: number;
    pending: number;
    in_progress: number;
    completed: number;
    failed: number;
  } {
    return this.failureRouter.getResumeQueueStats();
  }

  /**
   * Get resumable failures (failures that can be requeued).
   */
  getResumableFailures(bay: FailureBay): FailureRecord[] {
    return this.failureRouter.getResumableFailures(bay);
  }

  /**
   * Get all unresolved failures across all bays.
   */
  getAllUnresolved(): Map<FailureBay, FailureRecord[]> {
    return this.failureRouter.getAllUnresolvedFailures();
  }

  /**
   * Mark a failure as manually resolved (no reprocessing needed).
   */
  markManuallyResolved(bay: FailureBay, failureId: string, notes?: string): boolean {
    return this.failureRouter.markResolved(bay, failureId, notes || "Manually resolved");
  }

  /**
   * Set the NodeDispatcher (for deferred initialization).
   */
  setDispatcher(dispatcher: NodeDispatcher): void {
    this.dispatcher = dispatcher;
  }

  /**
   * Get configuration.
   */
  getConfig(): RequeueServiceConfig {
    return { ...this.config };
  }

  /**
   * Update configuration.
   */
  updateConfig(config: Partial<RequeueServiceConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Generate repair report.
   */
  generateRepairReport(): string {
    const lines: string[] = [];
    const stats = this.getQueueStats();
    const unresolvedByBay = this.getAllUnresolved();

    lines.push("=".repeat(60));
    lines.push("REPAIR QUEUE REPORT");
    lines.push("=".repeat(60));
    lines.push("");

    lines.push("QUEUE STATUS");
    lines.push("-".repeat(40));
    lines.push(`  Total Jobs:     ${stats.total}`);
    lines.push(`  Pending:        ${stats.pending}`);
    lines.push(`  In Progress:    ${stats.in_progress}`);
    lines.push(`  Completed:      ${stats.completed}`);
    lines.push(`  Failed:         ${stats.failed}`);
    lines.push("");

    lines.push("UNRESOLVED FAILURES BY BAY");
    lines.push("-".repeat(40));
    for (const [bay, failures] of unresolvedByBay) {
      const resumable = failures.filter(
        (f) => (f as any).slot_row || (f as any).fixed_slot_row
      ).length;
      lines.push(`  ${bay}:`);
      lines.push(`    Total: ${failures.length}`);
      lines.push(`    Resumable: ${resumable}`);
    }
    lines.push("");

    lines.push("=".repeat(60));

    return lines.join("\n");
  }
}

/**
 * Create a RequeueService with default configuration.
 */
export function createRequeueService(
  failureRouter: FailureRouter,
  dispatcher?: NodeDispatcher,
  config?: Partial<RequeueServiceConfig>
): RequeueService {
  return new RequeueService(failureRouter, dispatcher, config);
}
