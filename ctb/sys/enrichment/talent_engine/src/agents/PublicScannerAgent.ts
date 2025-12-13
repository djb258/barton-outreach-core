/**
 * PublicScannerAgent
 * ==================
 * Scans LinkedIn profiles to determine public accessibility.
 *
 * Features:
 * - Check profile public/private status
 * - Validate profile existence
 * - Fallback to private assumption on failure
 */

import { AgentResult, SlotRow } from "../models/SlotRow";
import {
  linkedInAccessibilityAdapter,
  AdapterConfig,
  DEFAULT_ADAPTER_CONFIG,
} from "../adapters";

/**
 * Agent configuration.
 */
export interface PublicScannerConfig extends AdapterConfig {
  /** Default accessibility when check fails */
  default_on_failure: boolean;
  /** Enable verbose logging */
  verbose: boolean;
}

/**
 * Default configuration.
 */
export const DEFAULT_PUBLIC_SCANNER_CONFIG: PublicScannerConfig = {
  ...DEFAULT_ADAPTER_CONFIG,
  default_on_failure: false, // Assume private on failure (conservative)
  verbose: false,
};

/**
 * Task for PublicScannerAgent.
 */
export interface PublicScannerTask {
  task_id: string;
  slot_row_id: string;
  linkedin_url: string;
}

/**
 * PublicScannerAgent - Determines if LinkedIn profiles are publicly accessible.
 *
 * Execution Flow:
 * 1. Validate LinkedIn URL format
 * 2. Call accessibility adapter
 * 3. Return public_accessible status
 * 4. On failure → assume private (conservative)
 */
export class PublicScannerAgent {
  private config: PublicScannerConfig;

  constructor(config?: Partial<PublicScannerConfig>) {
    this.config = {
      ...DEFAULT_PUBLIC_SCANNER_CONFIG,
      ...config,
    };
  }

  /**
   * Run the agent to scan a LinkedIn profile for public accessibility.
   */
  async run(task: PublicScannerTask, row?: SlotRow): Promise<AgentResult> {
    try {
      // Validate input
      if (!task.linkedin_url) {
        return this.createResult(
          task,
          false,
          { public_accessible: false },
          "LinkedIn URL is required for public scan"
        );
      }

      // Validate URL format
      if (!this.isValidLinkedInUrl(task.linkedin_url)) {
        return this.createResult(
          task,
          false,
          { public_accessible: false },
          "Invalid LinkedIn URL format"
        );
      }

      if (this.config.verbose) {
        console.log(`[PublicScannerAgent] Checking: ${task.linkedin_url}`);
      }

      // Try to check accessibility
      const result = await linkedInAccessibilityAdapter(task.linkedin_url, this.config);

      if (result.success && result.data) {
        const isPublic = result.data.public_accessible;

        if (row) {
          row.public_accessible = isPublic;
          row.last_updated = new Date();
        }

        return this.createResult(task, true, {
          public_accessible: isPublic,
          profile_exists: result.data.profile_exists,
          source: result.source || "adapter",
          cost: result.cost || 0,
        });
      }

      // Fallback: Treat failed check as private (conservative)
      if (this.config.verbose) {
        console.log(`[PublicScannerAgent] Check failed, using default: ${this.config.default_on_failure}`);
      }

      if (row) {
        row.public_accessible = this.config.default_on_failure;
        row.last_updated = new Date();
      }

      return this.createResult(task, true, {
        public_accessible: this.config.default_on_failure,
        profile_exists: true, // Assume exists
        source: "fallback",
        warning: "Could not verify accessibility, assuming private",
      });
    } catch (error) {
      // On error, default to private (conservative)
      if (row) {
        row.public_accessible = this.config.default_on_failure;
        row.last_updated = new Date();
      }

      return this.createResult(
        task,
        false,
        { public_accessible: this.config.default_on_failure },
        error instanceof Error ? error.message : "Unknown error occurred"
      );
    }
  }

  /**
   * Run directly on a SlotRow.
   */
  async runOnRow(row: SlotRow): Promise<SlotRow> {
    if (!row.linkedin_url) {
      return row;
    }

    const task: PublicScannerTask = {
      task_id: `public_${row.id}_${Date.now()}`,
      slot_row_id: row.id,
      linkedin_url: row.linkedin_url,
    };

    await this.run(task, row);
    return row;
  }

  /**
   * Validate LinkedIn URL format.
   */
  private isValidLinkedInUrl(url: string): boolean {
    // Support various LinkedIn URL formats
    const linkedInPattern = /^https?:\/\/(www\.)?linkedin\.com\/in\/[a-zA-Z0-9\-_%.]+\/?.*$/i;
    return linkedInPattern.test(url);
  }

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: PublicScannerTask,
    success: boolean,
    data: Record<string, unknown>,
    error?: string
  ): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "PublicScannerAgent",
      slot_row_id: task.slot_row_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }

  /**
   * Get current configuration.
   */
  getConfig(): PublicScannerConfig {
    return { ...this.config };
  }

  /**
   * Update configuration.
   */
  updateConfig(config: Partial<PublicScannerConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
