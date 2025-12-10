/**
 * HashAgent
 * =========
 * Generates movement hash for tracking changes.
 *
 * Services:
 * - Node crypto (no network calls)
 * - Pure local computation - always free
 */

import { AgentTask, AgentResult, SlotRow } from "../SlotRow";
import { createHash } from "crypto";

/**
 * Hash algorithm options.
 */
export type HashAlgorithm = "sha256" | "sha512" | "md5";

/**
 * Agent configuration.
 */
export interface HashAgentConfig {
  algorithm?: HashAlgorithm;
  includeTimestamp?: boolean;
}

/**
 * Default configuration.
 */
const DEFAULT_CONFIG: Required<HashAgentConfig> = {
  algorithm: "sha256",
  includeTimestamp: false,
};

/**
 * HashAgent - Generates movement hash for tracking changes.
 * Uses Node crypto module - no network calls required.
 */
export class HashAgent {
  private algorithm: HashAlgorithm;
  private includeTimestamp: boolean;

  constructor(config?: HashAgentConfig) {
    this.algorithm = config?.algorithm ?? DEFAULT_CONFIG.algorithm;
    this.includeTimestamp = config?.includeTimestamp ?? DEFAULT_CONFIG.includeTimestamp;
  }

  /**
   * Run the agent to generate a movement hash.
   *
   * @param task - The agent task to process
   * @param row - The SlotRow to update (optional)
   * @returns AgentResult with generated hash
   */
  async run(task: AgentTask, row?: SlotRow): Promise<AgentResult> {
    try {
      const {
        slot_row_id,
        company_name,
        slot_type,
        person_name,
        linkedin_url,
        context,
      } = task;

      // Build hash input from relevant fields
      const hashInput = this.buildHashInput({
        slot_row_id,
        company_name,
        slot_type,
        person_name,
        linkedin_url,
        current_title: context?.current_title as string | undefined,
        current_company: context?.current_company as string | undefined,
        email: context?.email as string | undefined,
      });

      // Generate hash
      const movementHash = this.generateHash(hashInput);

      if (row) {
        row.update({ movement_hash: movementHash });
      }

      return this.createResult(task, true, {
        movement_hash: movementHash,
        algorithm: this.algorithm,
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
   * Synchronous run method - HashAgent can run synchronously.
   */
  runSync(task: AgentTask): AgentResult {
    const {
      slot_row_id,
      company_name,
      slot_type,
      person_name,
      linkedin_url,
      context,
    } = task;

    try {
      const hashInput = this.buildHashInput({
        slot_row_id,
        company_name,
        slot_type,
        person_name,
        linkedin_url,
        current_title: context?.current_title as string | undefined,
        current_company: context?.current_company as string | undefined,
        email: context?.email as string | undefined,
      });

      const movementHash = this.generateHash(hashInput);

      return this.createResult(task, true, {
        movement_hash: movementHash,
        algorithm: this.algorithm,
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
   * Generate hash for a SlotRow directly.
   * Utility method for quick hashing without task structure.
   */
  hashRow(row: SlotRow): string {
    const hashInput = this.buildHashInput({
      slot_row_id: row.id,
      company_name: row.company_name,
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
   * Compare two hashes to detect movement.
   */
  detectMovement(oldHash: string | null, newHash: string): boolean {
    if (!oldHash) return false; // No previous hash = no movement
    return oldHash !== newHash;
  }

  /**
   * Build hash input object from fields.
   */
  private buildHashInput(fields: {
    slot_row_id: string;
    company_name: string;
    slot_type: string;
    person_name: string | null;
    linkedin_url: string | null;
    current_title?: string | null;
    current_company?: string | null;
    email?: string | null;
  }): Record<string, string | null> {
    const input: Record<string, string | null> = {
      // Core identity fields (always included)
      slot_row_id: fields.slot_row_id,
      company_name: this.normalize(fields.company_name),
      slot_type: fields.slot_type,
      person_name: this.normalize(fields.person_name),

      // Movement-sensitive fields
      current_title: this.normalize(fields.current_title),
      current_company: this.normalize(fields.current_company),

      // Optional fields
      linkedin_url: fields.linkedin_url,
      email: fields.email ?? null,
    };

    // Optionally add timestamp
    if (this.includeTimestamp) {
      input.timestamp = new Date().toISOString().split("T")[0]; // Date only
    }

    return input;
  }

  /**
   * Generate hash from input object.
   */
  private generateHash(input: Record<string, string | null>): string {
    // Sort keys for deterministic output
    const sortedKeys = Object.keys(input).sort();
    const hashString = sortedKeys
      .map((key) => `${key}:${input[key] ?? ""}`)
      .join("|");

    const hash = createHash(this.algorithm);
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
   * Create a standardized AgentResult.
   */
  private createResult(
    task: AgentTask,
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
}
