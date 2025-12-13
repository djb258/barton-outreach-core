/**
 * RenewalIntentAgent
 * ==================
 * BIT Node: Renewal Window Intent Signal Agent
 *
 * Analyzes renewal timing to generate intent signals.
 * Companies in renewal window = high intent to evaluate options.
 *
 * Hub-and-Spoke Role:
 * - Part of BIT_NODE (spoke)
 * - Receives renewal data from DOL Node (RenewalParserAgent)
 * - Requires company context from Company Hub
 * - Outputs renewal intent signals for BIT scoring
 *
 * Features:
 * - Renewal window proximity scoring
 * - Multi-year renewal pattern analysis
 * - Optimal outreach timing calculation
 * - Renewal urgency classification
 *
 * TODO: Add historical win/loss correlation
 * TODO: Implement optimal outreach timing algorithm
 * TODO: Add carrier-specific renewal patterns
 */

import { AgentResult } from "../../models/SlotRow";
import { RenewalInfo } from "../dol_node/RenewalParserAgent";

/**
 * Renewal intent signal.
 */
export interface RenewalIntentSignal {
  company_id: string;
  intent_score: number;
  urgency: RenewalUrgency;
  days_until_renewal: number;
  in_renewal_window: boolean;
  optimal_outreach_window: {
    start: string;
    end: string;
  };
  outreach_recommendation: string;
  timing_notes: string[];
}

/**
 * Renewal urgency levels.
 */
export type RenewalUrgency = "CRITICAL" | "URGENT" | "APPROACHING" | "DISTANT" | "UNKNOWN";

/**
 * Agent configuration.
 */
export interface RenewalIntentAgentConfig {
  /** Enable verbose logging */
  verbose: boolean;
  /** Days before renewal for CRITICAL urgency */
  critical_days: number;
  /** Days before renewal for URGENT urgency */
  urgent_days: number;
  /** Days before renewal for APPROACHING urgency */
  approaching_days: number;
  /** Optimal outreach start (days before renewal) */
  optimal_outreach_start_days: number;
  /** Optimal outreach end (days before renewal) */
  optimal_outreach_end_days: number;
}

/**
 * Default configuration.
 */
export const DEFAULT_RENEWAL_INTENT_CONFIG: RenewalIntentAgentConfig = {
  verbose: false,
  critical_days: 30,
  urgent_days: 60,
  approaching_days: 120,
  optimal_outreach_start_days: 90,
  optimal_outreach_end_days: 30,
};

/**
 * Task for RenewalIntentAgent.
 */
export interface RenewalIntentTask {
  task_id: string;
  company_id: string;
  company_name: string;
  renewal_info: RenewalInfo | null;
}

/**
 * RenewalIntentAgent - Generates intent signals from renewal timing.
 *
 * Execution Flow:
 * 1. Receive renewal info from DOL Node
 * 2. Calculate days until renewal
 * 3. Determine urgency level
 * 4. Calculate intent score based on timing
 * 5. Determine optimal outreach window
 * 6. Generate outreach recommendations
 */
export class RenewalIntentAgent {
  private config: RenewalIntentAgentConfig;

  constructor(config?: Partial<RenewalIntentAgentConfig>) {
    this.config = {
      ...DEFAULT_RENEWAL_INTENT_CONFIG,
      ...config,
    };
  }

  /**
   * Run the renewal intent agent.
   */
  async run(task: RenewalIntentTask): Promise<AgentResult> {
    try {
      // Validate input
      if (!task.company_id || !task.company_name) {
        return this.createResult(task, false, {}, "company_id and company_name are required");
      }

      if (this.config.verbose) {
        console.log(`[RenewalIntentAgent] Analyzing renewal intent for: ${task.company_name}`);
      }

      // No renewal info = unknown intent
      if (!task.renewal_info) {
        return this.createResult(task, true, {
          company_id: task.company_id,
          intent_score: 0,
          urgency: "UNKNOWN",
          days_until_renewal: -1,
          in_renewal_window: false,
          optimal_outreach_window: { start: "", end: "" },
          outreach_recommendation: "No renewal data available. Needs DOL sync.",
          timing_notes: ["Missing renewal data"],
        } as RenewalIntentSignal);
      }

      // Calculate metrics
      const daysUntil = task.renewal_info.days_until_renewal;
      const urgency = this.determineUrgency(daysUntil);
      const intentScore = this.calculateIntentScore(daysUntil, task.renewal_info.in_renewal_window);
      const optimalWindow = this.calculateOptimalWindow(task.renewal_info.estimated_renewal_date);
      const recommendation = this.generateRecommendation(urgency, daysUntil, optimalWindow);
      const timingNotes = this.generateTimingNotes(daysUntil, urgency, optimalWindow);

      const signal: RenewalIntentSignal = {
        company_id: task.company_id,
        intent_score: intentScore,
        urgency,
        days_until_renewal: daysUntil,
        in_renewal_window: task.renewal_info.in_renewal_window,
        optimal_outreach_window: optimalWindow,
        outreach_recommendation: recommendation,
        timing_notes: timingNotes,
      };

      return this.createResult(task, true, signal);
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
   * Determine urgency level from days until renewal.
   */
  private determineUrgency(daysUntil: number): RenewalUrgency {
    if (daysUntil <= this.config.critical_days) return "CRITICAL";
    if (daysUntil <= this.config.urgent_days) return "URGENT";
    if (daysUntil <= this.config.approaching_days) return "APPROACHING";
    return "DISTANT";
  }

  /**
   * Calculate intent score (0-100).
   * Higher score = higher intent (closer to renewal).
   */
  private calculateIntentScore(daysUntil: number, inWindow: boolean): number {
    // In renewal window = maximum score
    if (inWindow) {
      return 100;
    }

    // Score inversely proportional to days
    if (daysUntil <= 30) return 95;
    if (daysUntil <= 60) return 85;
    if (daysUntil <= 90) return 75;
    if (daysUntil <= 120) return 60;
    if (daysUntil <= 180) return 40;
    if (daysUntil <= 270) return 25;
    if (daysUntil <= 365) return 15;

    return 5; // More than a year out
  }

  /**
   * Calculate optimal outreach window.
   */
  private calculateOptimalWindow(renewalDate: string): { start: string; end: string } {
    const renewal = new Date(renewalDate);

    const start = new Date(renewal);
    start.setDate(start.getDate() - this.config.optimal_outreach_start_days);

    const end = new Date(renewal);
    end.setDate(end.getDate() - this.config.optimal_outreach_end_days);

    return {
      start: start.toISOString().split("T")[0],
      end: end.toISOString().split("T")[0],
    };
  }

  /**
   * Generate outreach recommendation.
   */
  private generateRecommendation(
    urgency: RenewalUrgency,
    daysUntil: number,
    optimalWindow: { start: string; end: string }
  ): string {
    const today = new Date().toISOString().split("T")[0];

    switch (urgency) {
      case "CRITICAL":
        return `IMMEDIATE ACTION: Renewal in ${daysUntil} days. Decision likely imminent.`;

      case "URGENT":
        return `HIGH PRIORITY: Renewal in ${daysUntil} days. Prime engagement window.`;

      case "APPROACHING":
        if (today >= optimalWindow.start && today <= optimalWindow.end) {
          return `OPTIMAL TIMING: Currently in ideal outreach window. Engage now.`;
        }
        if (today < optimalWindow.start) {
          return `COMING UP: Optimal window starts ${optimalWindow.start}. Prepare outreach.`;
        }
        return `Renewal approaching. Good time for initial contact.`;

      case "DISTANT":
        return `Add to nurture sequence. Optimal window: ${optimalWindow.start} to ${optimalWindow.end}`;

      default:
        return "Unable to determine timing. Manual review recommended.";
    }
  }

  /**
   * Generate timing notes.
   */
  private generateTimingNotes(
    daysUntil: number,
    urgency: RenewalUrgency,
    optimalWindow: { start: string; end: string }
  ): string[] {
    const notes: string[] = [];
    const today = new Date();

    notes.push(`${daysUntil} days until estimated renewal`);

    // Check if in optimal window
    const windowStart = new Date(optimalWindow.start);
    const windowEnd = new Date(optimalWindow.end);

    if (today >= windowStart && today <= windowEnd) {
      notes.push("✓ Currently in optimal outreach window");
    } else if (today < windowStart) {
      const daysToWindow = Math.ceil(
        (windowStart.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
      );
      notes.push(`Optimal window starts in ${daysToWindow} days`);
    } else {
      notes.push("⚠ Past optimal outreach window");
    }

    // Urgency-specific notes
    if (urgency === "CRITICAL") {
      notes.push("⚡ Likely in final decision phase");
    }
    if (urgency === "URGENT") {
      notes.push("📋 Probably reviewing options");
    }

    return notes;
  }

  /**
   * Batch analyze multiple companies.
   */
  async analyzeBatch(
    companies: Array<{
      company_id: string;
      company_name: string;
      renewal_info: RenewalInfo | null;
    }>
  ): Promise<RenewalIntentSignal[]> {
    const results: RenewalIntentSignal[] = [];

    for (const company of companies) {
      const task: RenewalIntentTask = {
        task_id: `renewal_intent_${company.company_id}_${Date.now()}`,
        company_id: company.company_id,
        company_name: company.company_name,
        renewal_info: company.renewal_info,
      };

      const result = await this.run(task);
      if (result.success && result.data) {
        results.push(result.data as RenewalIntentSignal);
      }
    }

    return results;
  }

  /**
   * Get companies by urgency.
   */
  filterByUrgency(signals: RenewalIntentSignal[], urgency: RenewalUrgency): RenewalIntentSignal[] {
    return signals.filter((s) => s.urgency === urgency);
  }

  /**
   * Get companies in optimal outreach window.
   */
  filterInOptimalWindow(signals: RenewalIntentSignal[]): RenewalIntentSignal[] {
    const today = new Date().toISOString().split("T")[0];
    return signals.filter(
      (s) => today >= s.optimal_outreach_window.start && today <= s.optimal_outreach_window.end
    );
  }

  /**
   * Sort by days until renewal ascending.
   */
  sortByUrgency(signals: RenewalIntentSignal[]): RenewalIntentSignal[] {
    return [...signals]
      .filter((s) => s.days_until_renewal >= 0)
      .sort((a, b) => a.days_until_renewal - b.days_until_renewal);
  }

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: RenewalIntentTask,
    success: boolean,
    data: Record<string, unknown>,
    error?: string
  ): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "RenewalIntentAgent",
      slot_row_id: task.company_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }

  getConfig(): RenewalIntentAgentConfig {
    return { ...this.config };
  }

  updateConfig(config: Partial<RenewalIntentAgentConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
