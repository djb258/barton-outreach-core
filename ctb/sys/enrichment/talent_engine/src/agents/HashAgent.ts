/**
 * HashAgent
 * =========
 * Generates movement hash for tracking changes.
 *
 * Features:
 * - SHA-256 hashing of slot data
 * - Movement detection via hash comparison
 * - Deterministic output (sorted keys)
 * - Pure local computation (no network calls)
 * - Always free - no vendor costs
 */

import { AgentResult, SlotRow } from "../models/SlotRow";
import { createHash } from "crypto";

/**
 * Hash algorithm options.
 */
export type HashAlgorithm = "sha256" | "sha512" | "md5";

/**
 * Agent configuration.
 */
export interface HashAgentConfig {
  /** Hash algorithm to use */
  algorithm: HashAlgorithm;
  /** Include timestamp in hash (for daily snapshots) */
  include_timestamp: boolean;
  /** Include email in hash */
  include_email: boolean;
  /** Include LinkedIn URL in hash */
  include_linkedin: boolean;
  /** Enable verbose logging */
  verbose: boolean;
}

/**
 * Default configuration.
 */
export const DEFAULT_HASH_AGENT_CONFIG: HashAgentConfig = {
  algorithm: "sha256",
  include_timestamp: false,
  include_email: true,
  include_linkedin: true,
  verbose: false,
};

/**
 * Task for HashAgent.
 */
export interface HashTask {
  task_id: string;
  slot_row_id: string;
  company_name: string;
  slot_type: string;
  person_name: string | null;
  linkedin_url?: string | null;
  current_title?: string | null;
  current_company?: string | null;
  email?: string | null;
  previous_hash?: string | null;
}

/**
 * Hash input fields.
 */
interface HashInputFields {
  slot_row_id: string;
  company_name: string;
  slot_type: string;
  person_name: string | null;
  linkedin_url?: string | null;
  current_title?: string | null;
  current_company?: string | null;
  email?: string | null;
}

/**
 * HashAgent - Generates movement hash for tracking changes.
 *
 * Execution Flow:
 * 1. Collect all relevant fields from task
 * 2. Normalize strings (lowercase, trim)
 * 3. Build deterministic hash input
 * 4. Generate hash using configured algorithm
 * 5. Compare with previous hash to detect movement
 */
export class HashAgent {
  private config: HashAgentConfig;

  constructor(config?: Partial<HashAgentConfig>) {
    this.config = {
      ...DEFAULT_HASH_AGENT_CONFIG,
      ...config,
    };
  }

  /**
   * Run the agent to generate a movement hash.
   */
  async run(task: HashTask, row?: SlotRow): Promise<AgentResult> {
    try {
      // Validate input
      if (!task.slot_row_id || !task.company_name || !task.slot_type) {
        return this.createResult(
          task,
          false,
          {},
          "slot_row_id, company_name, and slot_type are required"
        );
      }

      if (this.config.verbose) {
        console.log(`[HashAgent] Generating hash for slot: ${task.slot_row_id}`);
      }

      // Build hash input
      const hashInput = this.buildHashInput({
        slot_row_id: task.slot_row_id,
        company_name: task.company_name,
        slot_type: task.slot_type,
        person_name: task.person_name,
        linkedin_url: task.linkedin_url,
        current_title: task.current_title,
        current_company: task.current_company,
        email: task.email,
      });

      // Generate hash
      const movementHash = this.generateHash(hashInput);

      // Detect movement
      const movementDetected = this.detectMovement(task.previous_hash ?? null, movementHash);

      if (row) {
        row.movement_hash = movementHash;
        row.movement_detected = movementDetected;
        row.last_updated = new Date();
      }

      return this.createResult(task, true, {
        movement_hash: movementHash,
        algorithm: this.config.algorithm,
        movement_detected: movementDetected,
        previous_hash: task.previous_hash ?? null,
        input_fields: Object.keys(hashInput).filter(
          (k) => hashInput[k as keyof typeof hashInput] != null
        ),
      });
    } catch (error) {
      return this.createResult(
        task,
        false,
        {},
        error instanceof Error ? error.message : "Unknown error occurred"
      );
    }
  }

  /**
   * Run directly on a SlotRow.
   */
  async runOnRow(row: SlotRow): Promise<SlotRow> {
    const previousHash = row.movement_hash;

    const task: HashTask = {
      task_id: `hash_${row.id}_${Date.now()}`,
      slot_row_id: row.id,
      company_name: row.company_name || "",
      slot_type: row.slot_type,
      person_name: row.person_name,
      linkedin_url: row.linkedin_url,
      current_title: row.current_title,
      current_company: row.current_company,
      email: row.email,
      previous_hash: previousHash,
    };

    await this.run(task, row);
    return row;
  }

  /**
   * Synchronous hash generation for a SlotRow.
   * Utility method for quick hashing without full task structure.
   */
  hashRow(row: SlotRow): string {
    const hashInput = this.buildHashInput({
      slot_row_id: row.id,
      company_name: row.company_name || "",
      slot_type: row.slot_type,
      person_name: row.person_name,
      linkedin_url: row.linkedin_url,
      current_title: row.current_title,
      current_company: row.current_company,
      email: row.email,
    });

    return this.generateHash(hashInput);
  }

  /**
   * Synchronous hash comparison.
   * Returns true if movement detected (hashes differ).
   */
  detectMovement(oldHash: string | null, newHash: string): boolean {
    if (!oldHash) return false; // No previous hash = no movement
    return oldHash !== newHash;
  }

  /**
   * Build hash input object from fields.
   * Normalizes all strings and filters based on config.
   */
  private buildHashInput(fields: HashInputFields): Record<string, string | null> {
    const input: Record<string, string | null> = {
      // Core identity fields (always included)
      slot_row_id: fields.slot_row_id,
      company_name: this.normalize(fields.company_name),
      slot_type: fields.slot_type.toUpperCase(),
      person_name: this.normalize(fields.person_name),

      // Movement-sensitive fields
      current_title: this.normalize(fields.current_title),
      current_company: this.normalize(fields.current_company),
    };

    // Optional fields based on config
    if (this.config.include_linkedin) {
      input.linkedin_url = fields.linkedin_url ?? null;
    }

    if (this.config.include_email) {
      input.email = fields.email ? fields.email.toLowerCase().trim() : null;
    }

    // Optionally add timestamp (for daily snapshots)
    if (this.config.include_timestamp) {
      input.timestamp = new Date().toISOString().split("T")[0]; // Date only (YYYY-MM-DD)
    }

    return input;
  }

  /**
   * Generate hash from input object.
   * Keys are sorted for deterministic output.
   */
  private generateHash(input: Record<string, string | null>): string {
    // Sort keys for deterministic output
    const sortedKeys = Object.keys(input).sort();

    // Build hash string
    const hashString = sortedKeys
      .map((key) => `${key}:${input[key] ?? ""}`)
      .join("|");

    // Generate hash
    const hash = createHash(this.config.algorithm);
    hash.update(hashString);

    return hash.digest("hex");
  }

  /**
   * Normalize string for consistent hashing.
   */
  private normalize(value: string | null | undefined): string | null {
    if (!value) return null;
    return value.toLowerCase().trim().replace(/\s+/g, " ");
  }

  /**
   * Batch hash multiple rows.
   */
  async hashBatch(rows: SlotRow[]): Promise<Map<string, string>> {
    const results = new Map<string, string>();

    for (const row of rows) {
      const hash = this.hashRow(row);
      results.set(row.id, hash);
    }

    return results;
  }

  /**
   * Compare two snapshots and return changed row IDs.
   */
  findChangedRows(
    previousHashes: Map<string, string>,
    currentHashes: Map<string, string>
  ): string[] {
    const changedRowIds: string[] = [];

    for (const [rowId, currentHash] of currentHashes) {
      const previousHash = previousHashes.get(rowId);

      if (!previousHash) {
        // New row
        changedRowIds.push(rowId);
      } else if (this.detectMovement(previousHash, currentHash)) {
        // Hash changed
        changedRowIds.push(rowId);
      }
    }

    return changedRowIds;
  }

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: HashTask,
    success: boolean,
    data: Record<string, unknown>,
    error?: string
  ): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "HashAgent",
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
  getConfig(): HashAgentConfig {
    return { ...this.config };
  }

  /**
   * Update configuration.
   */
  updateConfig(config: Partial<HashAgentConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
