/**
 * BITScoreAgent
 * =============
 * BIT Node: Buyer Intent Tool Score Calculator
 *
 * Calculates composite buyer intent scores from multiple signals.
 * Central scoring engine for outreach prioritization.
 *
 * Hub-and-Spoke Role:
 * - Part of BIT_NODE (spoke)
 * - Receives signals from People Node (movement) and DOL Node (renewal)
 * - Requires company anchor from Company Hub
 * - Outputs scores for outreach prioritization
 *
 * Features:
 * - Composite score calculation
 * - Signal weighting and normalization
 * - Score decay over time
 * - Threshold-based tier assignment
 *
 * TODO: Implement full scoring algorithm
 * TODO: Add configurable signal weights
 * TODO: Integrate with Neon database for persistence
 */

import { AgentResult } from "../../models/SlotRow";

/**
 * Intent signals for scoring.
 */
export interface IntentSignals {
  /** Movement detected in people node */
  movement_detected: boolean;
  /** Days until renewal (from DOL node) */
  days_until_renewal: number | null;
  /** Currently in renewal window */
  in_renewal_window: boolean;
  /** Job postings detected */
  job_postings_count: number;
  /** Recent news/press mentions */
  news_mentions_count: number;
  /** Website activity signals */
  website_activity_score: number;
  /** Competitor carrier detected */
  competitor_carrier: boolean;
  /** Company size (employees) */
  employee_count: number;
}

/**
 * BIT score tiers.
 */
export type BITScoreTier = "HOT" | "WARM" | "COOL" | "COLD" | "EXCLUDED";

/**
 * BIT score result.
 */
export interface BITScoreResult {
  company_id: string;
  composite_score: number;
  tier: BITScoreTier;
  component_scores: {
    movement_score: number;
    renewal_score: number;
    activity_score: number;
    size_score: number;
  };
  signals_used: string[];
  score_breakdown: string;
  calculated_at: Date;
}

/**
 * Agent configuration.
 */
export interface BITScoreAgentConfig {
  /** Enable verbose logging */
  verbose: boolean;
  /** Signal weights */
  weights: {
    movement: number;
    renewal: number;
    activity: number;
    size: number;
  };
  /** Tier thresholds */
  tier_thresholds: {
    hot: number;
    warm: number;
    cool: number;
    cold: number;
  };
  /** Minimum score to include */
  min_score: number;
}

/**
 * Default configuration.
 */
export const DEFAULT_BIT_SCORE_CONFIG: BITScoreAgentConfig = {
  verbose: false,
  weights: {
    movement: 0.35,
    renewal: 0.30,
    activity: 0.20,
    size: 0.15,
  },
  tier_thresholds: {
    hot: 80,
    warm: 60,
    cool: 40,
    cold: 20,
  },
  min_score: 0,
};

/**
 * Task for BITScoreAgent.
 */
export interface BITScoreTask {
  task_id: string;
  company_id: string;
  company_name: string;
  signals: IntentSignals;
}

/**
 * BITScoreAgent - Calculates composite buyer intent scores.
 *
 * Execution Flow:
 * 1. Receive intent signals from upstream nodes
 * 2. Normalize each signal to 0-100 scale
 * 3. Apply weights to each signal category
 * 4. Calculate composite score
 * 5. Assign tier based on thresholds
 * 6. Return score result for prioritization
 */
export class BITScoreAgent {
  private config: BITScoreAgentConfig;

  constructor(config?: Partial<BITScoreAgentConfig>) {
    this.config = {
      ...DEFAULT_BIT_SCORE_CONFIG,
      ...config,
    };
  }

  /**
   * Run the BIT score agent.
   */
  async run(task: BITScoreTask): Promise<AgentResult> {
    try {
      // Validate input
      if (!task.company_id || !task.company_name) {
        return this.createResult(task, false, {}, "company_id and company_name are required");
      }

      if (this.config.verbose) {
        console.log(`[BITScoreAgent] Calculating score for: ${task.company_name}`);
      }

      // Calculate component scores
      const movementScore = this.calculateMovementScore(task.signals);
      const renewalScore = this.calculateRenewalScore(task.signals);
      const activityScore = this.calculateActivityScore(task.signals);
      const sizeScore = this.calculateSizeScore(task.signals);

      // Calculate weighted composite
      const compositeScore = Math.round(
        movementScore * this.config.weights.movement +
        renewalScore * this.config.weights.renewal +
        activityScore * this.config.weights.activity +
        sizeScore * this.config.weights.size
      );

      // Determine tier
      const tier = this.determineTier(compositeScore);

      // Build signals used list
      const signalsUsed = this.getSignalsUsed(task.signals);

      // Build score breakdown
      const breakdown = this.buildBreakdown(
        movementScore,
        renewalScore,
        activityScore,
        sizeScore
      );

      const result: BITScoreResult = {
        company_id: task.company_id,
        composite_score: compositeScore,
        tier,
        component_scores: {
          movement_score: movementScore,
          renewal_score: renewalScore,
          activity_score: activityScore,
          size_score: sizeScore,
        },
        signals_used: signalsUsed,
        score_breakdown: breakdown,
        calculated_at: new Date(),
      };

      return this.createResult(task, true, result);
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
   * Calculate movement score (0-100).
   */
  private calculateMovementScore(signals: IntentSignals): number {
    if (signals.movement_detected) {
      return 100; // Maximum score for detected movement
    }
    return 0;
  }

  /**
   * Calculate renewal score (0-100).
   */
  private calculateRenewalScore(signals: IntentSignals): number {
    if (signals.in_renewal_window) {
      return 100; // Maximum for active renewal window
    }

    if (signals.days_until_renewal === null) {
      return 0; // No renewal data
    }

    // Score based on days until renewal
    // Closer to renewal = higher score
    if (signals.days_until_renewal <= 30) return 90;
    if (signals.days_until_renewal <= 60) return 75;
    if (signals.days_until_renewal <= 90) return 60;
    if (signals.days_until_renewal <= 120) return 45;
    if (signals.days_until_renewal <= 180) return 30;
    if (signals.days_until_renewal <= 270) return 15;

    return 5; // More than 9 months out
  }

  /**
   * Calculate activity score (0-100).
   */
  private calculateActivityScore(signals: IntentSignals): number {
    let score = 0;

    // Job postings (up to 40 points)
    score += Math.min(signals.job_postings_count * 10, 40);

    // News mentions (up to 30 points)
    score += Math.min(signals.news_mentions_count * 10, 30);

    // Website activity (already 0-100, scale to 20 points)
    score += (signals.website_activity_score / 100) * 20;

    // Competitor carrier bonus (10 points)
    if (signals.competitor_carrier) {
      score += 10;
    }

    return Math.min(score, 100);
  }

  /**
   * Calculate size score (0-100).
   * Targets mid-market companies (100-5000 employees).
   */
  private calculateSizeScore(signals: IntentSignals): number {
    const employees = signals.employee_count;

    // Too small (< 50) or too large (> 10000) = lower score
    if (employees < 50) return 20;
    if (employees < 100) return 40;
    if (employees < 500) return 80;
    if (employees < 1000) return 100; // Sweet spot
    if (employees < 2500) return 90;
    if (employees < 5000) return 70;
    if (employees < 10000) return 50;

    return 30; // Very large enterprise
  }

  /**
   * Determine tier from composite score.
   */
  private determineTier(score: number): BITScoreTier {
    if (score >= this.config.tier_thresholds.hot) return "HOT";
    if (score >= this.config.tier_thresholds.warm) return "WARM";
    if (score >= this.config.tier_thresholds.cool) return "COOL";
    if (score >= this.config.tier_thresholds.cold) return "COLD";
    return "EXCLUDED";
  }

  /**
   * Get list of signals that contributed to score.
   */
  private getSignalsUsed(signals: IntentSignals): string[] {
    const used: string[] = [];

    if (signals.movement_detected) used.push("movement");
    if (signals.days_until_renewal !== null) used.push("renewal");
    if (signals.job_postings_count > 0) used.push("job_postings");
    if (signals.news_mentions_count > 0) used.push("news");
    if (signals.website_activity_score > 0) used.push("website_activity");
    if (signals.competitor_carrier) used.push("competitor");
    if (signals.employee_count > 0) used.push("company_size");

    return used;
  }

  /**
   * Build human-readable score breakdown.
   */
  private buildBreakdown(
    movement: number,
    renewal: number,
    activity: number,
    size: number
  ): string {
    const parts: string[] = [];

    parts.push(`Movement: ${movement} × ${this.config.weights.movement} = ${Math.round(movement * this.config.weights.movement)}`);
    parts.push(`Renewal: ${renewal} × ${this.config.weights.renewal} = ${Math.round(renewal * this.config.weights.renewal)}`);
    parts.push(`Activity: ${activity} × ${this.config.weights.activity} = ${Math.round(activity * this.config.weights.activity)}`);
    parts.push(`Size: ${size} × ${this.config.weights.size} = ${Math.round(size * this.config.weights.size)}`);

    return parts.join(" | ");
  }

  /**
   * Batch calculate scores for multiple companies.
   */
  async scoreBatch(
    companies: Array<{
      company_id: string;
      company_name: string;
      signals: IntentSignals;
    }>
  ): Promise<BITScoreResult[]> {
    const results: BITScoreResult[] = [];

    for (const company of companies) {
      const task: BITScoreTask = {
        task_id: `bit_${company.company_id}_${Date.now()}`,
        company_id: company.company_id,
        company_name: company.company_name,
        signals: company.signals,
      };

      const result = await this.run(task);
      if (result.success && result.data) {
        results.push(result.data as BITScoreResult);
      }
    }

    return results;
  }

  /**
   * Get companies by tier.
   */
  filterByTier(results: BITScoreResult[], tier: BITScoreTier): BITScoreResult[] {
    return results.filter((r) => r.tier === tier);
  }

  /**
   * Sort by composite score descending.
   */
  sortByScore(results: BITScoreResult[]): BITScoreResult[] {
    return [...results].sort((a, b) => b.composite_score - a.composite_score);
  }

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: BITScoreTask,
    success: boolean,
    data: Record<string, unknown>,
    error?: string
  ): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "BITScoreAgent",
      slot_row_id: task.company_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }

  getConfig(): BITScoreAgentConfig {
    return { ...this.config };
  }

  updateConfig(config: Partial<BITScoreAgentConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
