/**
 * CarrierNormalizerAgent
 * ======================
 * DOL Node: Insurance Carrier Name Normalizer
 *
 * Normalizes carrier names from Schedule A filings for consistent tracking.
 * Enables carrier-based intelligence and competitive analysis.
 *
 * Hub-and-Spoke Role:
 * - Part of DOL_NODE (spoke)
 * - Receives Schedule A data from DOLSyncAgent
 * - Normalizes carrier names for deduplication
 * - Feeds carrier intelligence to BIT Node
 *
 * Features:
 * - Carrier name normalization
 * - Subsidiary → parent mapping
 * - Carrier type classification
 * - Coverage type extraction
 *
 * TODO: Build comprehensive carrier name mapping
 * TODO: Add carrier merger/acquisition tracking
 * TODO: Integrate with carrier master database
 */

import { AgentResult } from "../../models/SlotRow";

/**
 * Schedule A carrier record.
 */
export interface ScheduleACarrier {
  carrier_name: string;
  policy_number?: string;
  premium_amount?: number;
  coverage_type?: string;
  contract_type?: string;
}

/**
 * Normalized carrier information.
 */
export interface NormalizedCarrier {
  original_name: string;
  normalized_name: string;
  parent_company: string;
  carrier_type: CarrierType;
  confidence: number;
}

/**
 * Carrier types.
 */
export type CarrierType =
  | "HEALTH"
  | "DENTAL"
  | "VISION"
  | "LIFE"
  | "DISABILITY"
  | "STOP_LOSS"
  | "PBM"
  | "TPA"
  | "UNKNOWN";

/**
 * Agent configuration.
 */
export interface CarrierNormalizerAgentConfig {
  /** Enable verbose logging */
  verbose: boolean;
  /** Minimum confidence to auto-accept normalization */
  auto_accept_threshold: number;
  /** Use fuzzy matching for unknown carriers */
  use_fuzzy_matching: boolean;
}

/**
 * Default configuration.
 */
export const DEFAULT_CARRIER_NORMALIZER_CONFIG: CarrierNormalizerAgentConfig = {
  verbose: false,
  auto_accept_threshold: 0.9,
  use_fuzzy_matching: true,
};

/**
 * Task for CarrierNormalizerAgent.
 */
export interface CarrierNormalizerTask {
  task_id: string;
  company_id: string;
  carriers: ScheduleACarrier[];
}

/**
 * Known carrier mappings (name → parent company).
 */
const CARRIER_MAPPINGS: Record<string, { parent: string; type: CarrierType }> = {
  // UnitedHealth Group
  "united healthcare": { parent: "UnitedHealth Group", type: "HEALTH" },
  "unitedhealthcare": { parent: "UnitedHealth Group", type: "HEALTH" },
  "uhc": { parent: "UnitedHealth Group", type: "HEALTH" },
  "optum": { parent: "UnitedHealth Group", type: "PBM" },
  "optumrx": { parent: "UnitedHealth Group", type: "PBM" },

  // Anthem / Elevance
  "anthem": { parent: "Elevance Health", type: "HEALTH" },
  "anthem blue cross": { parent: "Elevance Health", type: "HEALTH" },
  "blue cross blue shield": { parent: "BCBSA", type: "HEALTH" },
  "bcbs": { parent: "BCBSA", type: "HEALTH" },
  "elevance": { parent: "Elevance Health", type: "HEALTH" },

  // Cigna
  "cigna": { parent: "The Cigna Group", type: "HEALTH" },
  "cigna healthcare": { parent: "The Cigna Group", type: "HEALTH" },
  "express scripts": { parent: "The Cigna Group", type: "PBM" },
  "evernorth": { parent: "The Cigna Group", type: "PBM" },

  // Aetna / CVS
  "aetna": { parent: "CVS Health", type: "HEALTH" },
  "cvs caremark": { parent: "CVS Health", type: "PBM" },
  "caremark": { parent: "CVS Health", type: "PBM" },

  // Humana
  "humana": { parent: "Humana Inc", type: "HEALTH" },

  // Kaiser
  "kaiser": { parent: "Kaiser Permanente", type: "HEALTH" },
  "kaiser permanente": { parent: "Kaiser Permanente", type: "HEALTH" },

  // Dental carriers
  "delta dental": { parent: "Delta Dental", type: "DENTAL" },
  "metlife dental": { parent: "MetLife", type: "DENTAL" },
  "guardian dental": { parent: "Guardian Life", type: "DENTAL" },

  // Vision carriers
  "vsp": { parent: "VSP Global", type: "VISION" },
  "eyemed": { parent: "EyeMed", type: "VISION" },

  // Life/Disability
  "metlife": { parent: "MetLife", type: "LIFE" },
  "prudential": { parent: "Prudential Financial", type: "LIFE" },
  "lincoln financial": { parent: "Lincoln Financial", type: "DISABILITY" },
  "unum": { parent: "Unum Group", type: "DISABILITY" },
  "standard insurance": { parent: "The Standard", type: "DISABILITY" },
  "the standard": { parent: "The Standard", type: "DISABILITY" },
  "hartford": { parent: "The Hartford", type: "DISABILITY" },

  // Stop-loss
  "sun life": { parent: "Sun Life Financial", type: "STOP_LOSS" },
  "voya": { parent: "Voya Financial", type: "STOP_LOSS" },

  // TPAs
  "usi": { parent: "USI Insurance Services", type: "TPA" },
  "gallagher": { parent: "Arthur J. Gallagher", type: "TPA" },
  "marsh": { parent: "Marsh McLennan", type: "TPA" },
  "aon": { parent: "Aon plc", type: "TPA" },
};

/**
 * CarrierNormalizerAgent - Normalizes carrier names from Schedule A.
 *
 * Execution Flow:
 * 1. Receive carrier list from Schedule A
 * 2. Normalize each carrier name
 * 3. Match to known carrier database
 * 4. Classify carrier type
 * 5. Return normalized carrier list
 */
export class CarrierNormalizerAgent {
  private config: CarrierNormalizerAgentConfig;

  constructor(config?: Partial<CarrierNormalizerAgentConfig>) {
    this.config = {
      ...DEFAULT_CARRIER_NORMALIZER_CONFIG,
      ...config,
    };
  }

  /**
   * Run the carrier normalizer agent.
   */
  async run(task: CarrierNormalizerTask): Promise<AgentResult> {
    try {
      // Validate input
      if (!task.company_id) {
        return this.createResult(task, false, {}, "company_id is required");
      }

      if (!task.carriers || task.carriers.length === 0) {
        return this.createResult(task, true, {
          normalized_carriers: [],
          carriers_count: 0,
        });
      }

      if (this.config.verbose) {
        console.log(`[CarrierNormalizerAgent] Normalizing ${task.carriers.length} carriers`);
      }

      // Normalize each carrier
      const normalizedCarriers: NormalizedCarrier[] = [];

      for (const carrier of task.carriers) {
        const normalized = this.normalizeCarrier(carrier);
        normalizedCarriers.push(normalized);
      }

      // Deduplicate by parent company
      const uniqueParents = new Map<string, NormalizedCarrier>();
      for (const carrier of normalizedCarriers) {
        const existing = uniqueParents.get(carrier.parent_company);
        if (!existing || carrier.confidence > existing.confidence) {
          uniqueParents.set(carrier.parent_company, carrier);
        }
      }

      return this.createResult(task, true, {
        normalized_carriers: normalizedCarriers,
        unique_parents: Array.from(uniqueParents.values()),
        carriers_count: task.carriers.length,
        unique_parent_count: uniqueParents.size,
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
   * Normalize a single carrier.
   */
  private normalizeCarrier(carrier: ScheduleACarrier): NormalizedCarrier {
    const cleanName = this.cleanCarrierName(carrier.carrier_name);

    // Look up in known mappings
    const mapping = CARRIER_MAPPINGS[cleanName];

    if (mapping) {
      return {
        original_name: carrier.carrier_name,
        normalized_name: cleanName,
        parent_company: mapping.parent,
        carrier_type: carrier.coverage_type
          ? this.inferCarrierType(carrier.coverage_type)
          : mapping.type,
        confidence: 1.0,
      };
    }

    // Try fuzzy matching
    if (this.config.use_fuzzy_matching) {
      const fuzzyMatch = this.fuzzyMatchCarrier(cleanName);
      if (fuzzyMatch) {
        return {
          original_name: carrier.carrier_name,
          normalized_name: cleanName,
          parent_company: fuzzyMatch.parent,
          carrier_type: carrier.coverage_type
            ? this.inferCarrierType(carrier.coverage_type)
            : fuzzyMatch.type,
          confidence: 0.7,
        };
      }
    }

    // Unknown carrier
    return {
      original_name: carrier.carrier_name,
      normalized_name: cleanName,
      parent_company: carrier.carrier_name, // Use original as parent
      carrier_type: carrier.coverage_type
        ? this.inferCarrierType(carrier.coverage_type)
        : "UNKNOWN",
      confidence: 0.3,
    };
  }

  /**
   * Clean carrier name for matching.
   */
  private cleanCarrierName(name: string): string {
    return name
      .toLowerCase()
      .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()'"]/g, " ")
      .replace(/\s+(inc|llc|ltd|corp|co|company|corporation|group|insurance)\.?/gi, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  /**
   * Fuzzy match against known carriers.
   */
  private fuzzyMatchCarrier(
    name: string
  ): { parent: string; type: CarrierType } | null {
    for (const [key, mapping] of Object.entries(CARRIER_MAPPINGS)) {
      if (name.includes(key) || key.includes(name)) {
        return mapping;
      }
    }
    return null;
  }

  /**
   * Infer carrier type from coverage type string.
   */
  private inferCarrierType(coverageType: string): CarrierType {
    const lower = coverageType.toLowerCase();

    if (lower.includes("health") || lower.includes("medical")) return "HEALTH";
    if (lower.includes("dental")) return "DENTAL";
    if (lower.includes("vision") || lower.includes("eye")) return "VISION";
    if (lower.includes("life")) return "LIFE";
    if (lower.includes("disab") || lower.includes("std") || lower.includes("ltd")) return "DISABILITY";
    if (lower.includes("stop") || lower.includes("excess")) return "STOP_LOSS";
    if (lower.includes("pbm") || lower.includes("pharmacy") || lower.includes("rx")) return "PBM";

    return "UNKNOWN";
  }

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: CarrierNormalizerTask,
    success: boolean,
    data: Record<string, unknown>,
    error?: string
  ): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "CarrierNormalizerAgent",
      slot_row_id: task.company_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }

  getConfig(): CarrierNormalizerAgentConfig {
    return { ...this.config };
  }

  updateConfig(config: Partial<CarrierNormalizerAgentConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
