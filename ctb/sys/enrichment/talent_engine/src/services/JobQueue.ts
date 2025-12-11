/**
 * JobQueue
 * ========
 * Persistent job queue for resume_enrichment jobs.
 *
 * Provides durable job storage and processing:
 * - In-memory queue with optional Neon persistence
 * - FIFO processing with priority support
 * - Automatic retry with exponential backoff
 * - Dead letter queue for failed jobs
 * - Job status tracking and reporting
 *
 * Job Types:
 * - resume_enrichment: Resume processing from failure point
 * - bulk_requeue: Batch requeue operation
 * - manual_repair: Manual fix submitted via UI/CLI
 *
 * Usage:
 * ```typescript
 * const queue = new JobQueue({ verbose: true });
 *
 * // Add a job
 * const jobId = queue.enqueue({
 *   type: "resume_enrichment",
 *   failureId: "fail_123",
 *   bay: "email_pattern_failures",
 *   resumeNode: "COMPANY_HUB",
 *   resumeAgent: "PatternAgent",
 *   slotRow: { ... },
 * });
 *
 * // Process jobs
 * await queue.processAll(async (job) => {
 *   // Process the job
 *   return { success: true };
 * });
 * ```
 */

import { FailureBay } from "../models/FailureRecord";
import { FailureNode, FailureAgentType } from "../models/FailureRecord";
import { SlotRow } from "../models/SlotRow";

/**
 * Job types supported by the queue.
 */
export type JobType = "resume_enrichment" | "bulk_requeue" | "manual_repair";

/**
 * Job status.
 */
export type JobStatus = "pending" | "processing" | "completed" | "failed" | "dead";

/**
 * Job priority levels.
 */
export type JobPriority = "low" | "normal" | "high" | "urgent";

/**
 * Base job interface.
 */
export interface BaseJob {
  id: string;
  type: JobType;
  status: JobStatus;
  priority: JobPriority;
  createdAt: Date;
  updatedAt: Date;
  attempts: number;
  maxAttempts: number;
  lastError?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Resume enrichment job.
 */
export interface ResumeEnrichmentJob extends BaseJob {
  type: "resume_enrichment";
  failureId: string;
  bay: FailureBay;
  resumeNode: FailureNode;
  resumeAgent: FailureAgentType;
  slotRow: SlotRow | Record<string, unknown>;
}

/**
 * Bulk requeue job.
 */
export interface BulkRequeueJob extends BaseJob {
  type: "bulk_requeue";
  bay: FailureBay;
  failureIds: string[];
}

/**
 * Manual repair job.
 */
export interface ManualRepairJob extends BaseJob {
  type: "manual_repair";
  failureId: string;
  bay: FailureBay;
  fixedData: Record<string, unknown>;
  submittedBy?: string;
}

/**
 * Union type of all jobs.
 */
export type Job = ResumeEnrichmentJob | BulkRequeueJob | ManualRepairJob;

/**
 * Job result interface.
 */
export interface JobResult {
  success: boolean;
  error?: string;
  data?: Record<string, unknown>;
}

/**
 * Job processor function type.
 */
export type JobProcessor = (job: Job) => Promise<JobResult>;

/**
 * JobQueue configuration.
 */
export interface JobQueueConfig {
  /** Enable verbose logging */
  verbose: boolean;
  /** Maximum queue size */
  maxQueueSize: number;
  /** Default max attempts for jobs */
  defaultMaxAttempts: number;
  /** Base delay for retry (ms) */
  retryBaseDelay: number;
  /** Maximum retry delay (ms) */
  maxRetryDelay: number;
  /** Enable Neon persistence */
  enablePersistence: boolean;
  /** Neon connection string */
  neonConnectionString?: string;
  /** Process timeout (ms) */
  processTimeout: number;
}

/**
 * Default configuration.
 */
export const DEFAULT_JOB_QUEUE_CONFIG: JobQueueConfig = {
  verbose: false,
  maxQueueSize: 10000,
  defaultMaxAttempts: 3,
  retryBaseDelay: 1000,
  maxRetryDelay: 60000,
  enablePersistence: false,
  processTimeout: 300000, // 5 minutes
};

/**
 * Queue statistics.
 */
export interface QueueStats {
  total: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  dead: number;
  byType: Record<JobType, number>;
  byPriority: Record<JobPriority, number>;
}

/**
 * JobQueue - Persistent job queue for enrichment operations.
 */
export class JobQueue {
  private config: JobQueueConfig;
  private jobs: Map<string, Job> = new Map();
  private deadLetterQueue: Job[] = [];
  private isProcessing: boolean = false;

  constructor(config?: Partial<JobQueueConfig>) {
    this.config = {
      ...DEFAULT_JOB_QUEUE_CONFIG,
      ...config,
    };
  }

  /**
   * Enqueue a resume enrichment job.
   */
  enqueueResumeEnrichment(
    failureId: string,
    bay: FailureBay,
    resumeNode: FailureNode,
    resumeAgent: FailureAgentType,
    slotRow: SlotRow | Record<string, unknown>,
    priority: JobPriority = "normal"
  ): string {
    const job: ResumeEnrichmentJob = {
      id: this.generateId(),
      type: "resume_enrichment",
      status: "pending",
      priority,
      createdAt: new Date(),
      updatedAt: new Date(),
      attempts: 0,
      maxAttempts: this.config.defaultMaxAttempts,
      failureId,
      bay,
      resumeNode,
      resumeAgent,
      slotRow,
    };

    return this.addJob(job);
  }

  /**
   * Enqueue a bulk requeue job.
   */
  enqueueBulkRequeue(
    bay: FailureBay,
    failureIds: string[],
    priority: JobPriority = "normal"
  ): string {
    const job: BulkRequeueJob = {
      id: this.generateId(),
      type: "bulk_requeue",
      status: "pending",
      priority,
      createdAt: new Date(),
      updatedAt: new Date(),
      attempts: 0,
      maxAttempts: this.config.defaultMaxAttempts,
      bay,
      failureIds,
    };

    return this.addJob(job);
  }

  /**
   * Enqueue a manual repair job.
   */
  enqueueManualRepair(
    failureId: string,
    bay: FailureBay,
    fixedData: Record<string, unknown>,
    submittedBy?: string,
    priority: JobPriority = "high"
  ): string {
    const job: ManualRepairJob = {
      id: this.generateId(),
      type: "manual_repair",
      status: "pending",
      priority,
      createdAt: new Date(),
      updatedAt: new Date(),
      attempts: 0,
      maxAttempts: this.config.defaultMaxAttempts,
      failureId,
      bay,
      fixedData,
      submittedBy,
    };

    return this.addJob(job);
  }

  /**
   * Add a job to the queue.
   */
  private addJob(job: Job): string {
    if (this.jobs.size >= this.config.maxQueueSize) {
      throw new Error(`Queue full (max: ${this.config.maxQueueSize})`);
    }

    this.jobs.set(job.id, job);

    if (this.config.verbose) {
      console.log(`[JobQueue] Added job: ${job.id} (${job.type})`);
    }

    return job.id;
  }

  /**
   * Get next job to process (respects priority).
   */
  getNextJob(): Job | null {
    const priorityOrder: JobPriority[] = ["urgent", "high", "normal", "low"];

    for (const priority of priorityOrder) {
      for (const job of this.jobs.values()) {
        if (job.status === "pending" && job.priority === priority) {
          return job;
        }
      }
    }

    return null;
  }

  /**
   * Get all pending jobs.
   */
  getPendingJobs(): Job[] {
    return Array.from(this.jobs.values()).filter((j) => j.status === "pending");
  }

  /**
   * Get a job by ID.
   */
  getJob(jobId: string): Job | undefined {
    return this.jobs.get(jobId);
  }

  /**
   * Update job status.
   */
  updateJobStatus(jobId: string, status: JobStatus, error?: string): boolean {
    const job = this.jobs.get(jobId);
    if (!job) return false;

    job.status = status;
    job.updatedAt = new Date();
    if (error) job.lastError = error;

    if (this.config.verbose) {
      console.log(`[JobQueue] Job ${jobId} status: ${status}`);
    }

    return true;
  }

  /**
   * Process a single job.
   */
  async processJob(job: Job, processor: JobProcessor): Promise<JobResult> {
    // Update status
    job.status = "processing";
    job.attempts++;
    job.updatedAt = new Date();

    if (this.config.verbose) {
      console.log(`[JobQueue] Processing job: ${job.id} (attempt ${job.attempts})`);
    }

    try {
      // Run with timeout
      const result = await this.withTimeout(
        processor(job),
        this.config.processTimeout
      );

      if (result.success) {
        job.status = "completed";
        if (this.config.verbose) {
          console.log(`[JobQueue] Job ${job.id} completed`);
        }
      } else {
        this.handleJobFailure(job, result.error || "Unknown error");
      }

      job.updatedAt = new Date();
      return result;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "Unknown error";
      this.handleJobFailure(job, errorMsg);
      return { success: false, error: errorMsg };
    }
  }

  /**
   * Handle job failure (retry or dead letter).
   */
  private handleJobFailure(job: Job, error: string): void {
    job.lastError = error;
    job.updatedAt = new Date();

    if (job.attempts >= job.maxAttempts) {
      // Move to dead letter queue
      job.status = "dead";
      this.deadLetterQueue.push(job);
      this.jobs.delete(job.id);

      if (this.config.verbose) {
        console.log(`[JobQueue] Job ${job.id} moved to dead letter queue`);
      }
    } else {
      // Mark as pending for retry
      job.status = "pending";

      if (this.config.verbose) {
        console.log(`[JobQueue] Job ${job.id} will retry (${job.attempts}/${job.maxAttempts})`);
      }
    }
  }

  /**
   * Process all pending jobs.
   */
  async processAll(processor: JobProcessor): Promise<JobResult[]> {
    if (this.isProcessing) {
      throw new Error("Queue is already being processed");
    }

    this.isProcessing = true;
    const results: JobResult[] = [];

    try {
      let job = this.getNextJob();

      while (job) {
        // Calculate retry delay if needed
        if (job.attempts > 0) {
          const delay = this.calculateRetryDelay(job.attempts);
          await this.sleep(delay);
        }

        const result = await this.processJob(job, processor);
        results.push(result);

        job = this.getNextJob();
      }
    } finally {
      this.isProcessing = false;
    }

    return results;
  }

  /**
   * Calculate exponential backoff delay.
   */
  private calculateRetryDelay(attempt: number): number {
    const delay = this.config.retryBaseDelay * Math.pow(2, attempt - 1);
    return Math.min(delay, this.config.maxRetryDelay);
  }

  /**
   * Sleep helper.
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Run with timeout.
   */
  private async withTimeout<T>(promise: Promise<T>, timeout: number): Promise<T> {
    return Promise.race([
      promise,
      new Promise<T>((_, reject) =>
        setTimeout(() => reject(new Error("Job timeout")), timeout)
      ),
    ]);
  }

  /**
   * Generate unique ID.
   */
  private generateId(): string {
    return `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get queue statistics.
   */
  getStats(): QueueStats {
    const jobs = Array.from(this.jobs.values());

    const byType: Record<JobType, number> = {
      resume_enrichment: 0,
      bulk_requeue: 0,
      manual_repair: 0,
    };

    const byPriority: Record<JobPriority, number> = {
      low: 0,
      normal: 0,
      high: 0,
      urgent: 0,
    };

    let pending = 0;
    let processing = 0;
    let completed = 0;
    let failed = 0;

    for (const job of jobs) {
      byType[job.type]++;
      byPriority[job.priority]++;

      switch (job.status) {
        case "pending":
          pending++;
          break;
        case "processing":
          processing++;
          break;
        case "completed":
          completed++;
          break;
        case "failed":
          failed++;
          break;
      }
    }

    return {
      total: jobs.length,
      pending,
      processing,
      completed,
      failed,
      dead: this.deadLetterQueue.length,
      byType,
      byPriority,
    };
  }

  /**
   * Get dead letter queue.
   */
  getDeadLetterQueue(): Job[] {
    return [...this.deadLetterQueue];
  }

  /**
   * Retry a dead letter job.
   */
  retryDeadLetter(jobId: string): boolean {
    const index = this.deadLetterQueue.findIndex((j) => j.id === jobId);
    if (index === -1) return false;

    const job = this.deadLetterQueue[index];
    job.status = "pending";
    job.attempts = 0;
    job.updatedAt = new Date();

    this.jobs.set(job.id, job);
    this.deadLetterQueue.splice(index, 1);

    if (this.config.verbose) {
      console.log(`[JobQueue] Dead letter job ${jobId} retried`);
    }

    return true;
  }

  /**
   * Clear completed jobs.
   */
  clearCompleted(): number {
    let count = 0;
    for (const [id, job] of this.jobs) {
      if (job.status === "completed") {
        this.jobs.delete(id);
        count++;
      }
    }
    return count;
  }

  /**
   * Clear all jobs.
   */
  clear(): void {
    this.jobs.clear();
    this.deadLetterQueue = [];
  }

  /**
   * Get configuration.
   */
  getConfig(): JobQueueConfig {
    return { ...this.config };
  }

  /**
   * Update configuration.
   */
  updateConfig(config: Partial<JobQueueConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Generate queue report.
   */
  generateReport(): string {
    const stats = this.getStats();
    const lines: string[] = [];

    lines.push("=".repeat(60));
    lines.push("JOB QUEUE REPORT");
    lines.push("=".repeat(60));
    lines.push("");

    lines.push("QUEUE STATUS");
    lines.push("-".repeat(40));
    lines.push(`  Total:       ${stats.total}`);
    lines.push(`  Pending:     ${stats.pending}`);
    lines.push(`  Processing:  ${stats.processing}`);
    lines.push(`  Completed:   ${stats.completed}`);
    lines.push(`  Failed:      ${stats.failed}`);
    lines.push(`  Dead Letter: ${stats.dead}`);
    lines.push("");

    lines.push("BY TYPE");
    lines.push("-".repeat(40));
    for (const [type, count] of Object.entries(stats.byType)) {
      if (count > 0) {
        lines.push(`  ${type}: ${count}`);
      }
    }
    lines.push("");

    lines.push("BY PRIORITY");
    lines.push("-".repeat(40));
    for (const [priority, count] of Object.entries(stats.byPriority)) {
      if (count > 0) {
        lines.push(`  ${priority}: ${count}`);
      }
    }
    lines.push("");

    if (this.deadLetterQueue.length > 0) {
      lines.push("DEAD LETTER QUEUE");
      lines.push("-".repeat(40));
      for (const job of this.deadLetterQueue.slice(0, 10)) {
        lines.push(`  ${job.id}: ${job.type} - ${job.lastError}`);
      }
      if (this.deadLetterQueue.length > 10) {
        lines.push(`  ... and ${this.deadLetterQueue.length - 10} more`);
      }
      lines.push("");
    }

    lines.push("=".repeat(60));

    return lines.join("\n");
  }
}

/**
 * Create a JobQueue with default configuration.
 */
export function createJobQueue(config?: Partial<JobQueueConfig>): JobQueue {
  return new JobQueue(config);
}
