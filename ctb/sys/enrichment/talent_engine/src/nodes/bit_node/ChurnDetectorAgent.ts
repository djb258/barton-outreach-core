/**
 * ChurnDetectorAgent
 * ==================
 * BIT Node: Executive Churn Detection Agent
 *
 * Detects patterns of executive turnover that signal buying opportunities.
 * Key signal: New HR/Benefits executive = potential broker change.
 *
 * Hub-and-Spoke Role:
 * - Part of BIT_NODE (spoke)
 * - Receives movement signals from People Node
 * - Requires company context from Company Hub
 * - Outputs churn signals for BIT scoring
 *
 * Features:
 * - Executive turnover pattern detection
 * - Churn velocity calculation
 * - Role-specific churn analysis
 * - Churn risk scoring
 *
 * TODO: Implement historical churn tracking
 * TODO: Add industry benchmarking
 * TODO: Integrate with movement_detected signals
 */

import { AgentResult, SlotType, ALL_SLOT_TYPES } from "../../models/SlotRow";

/**
 * Movement event for churn analysis.
 */
export interface MovementEvent {
  slot_type: SlotType;
  person_name: string;
  previous_company: string | null;
  current_company: string | null;
  previous_title: string | null;
  current_title: string | null;
  detected_at: Date;
  movement_type: "company_change" | "title_change" | "new_hire" | "departure";
}

/**
 * Churn analysis result.
 */
export interface ChurnAnalysis {
  company_id: string;
  churn_detected: boolean;
  churn_score: number;
  churn_velocity: number;
  events_analyzed: number;
  critical_churn: boolean;
  recent_events: MovementEvent[];
  risk_level: ChurnRiskLevel;
  recommendation: string;
}

/**
 * Churn risk levels.
 */
export type ChurnRiskLevel = "HIGH" | "MEDIUM" | "LOW" | "NONE";

/**
 * Agent configuration.
 */
export interface ChurnDetectorAgentConfig {
  /** Enable verbose logging */
  verbose: boolean;
  /** Days to look back for events */
  lookback_days: number;
  /** Minimum events to calculate velocity */
  min_events_for_velocity: number;
  /** Critical slot types (churn here = high priority) */
  critical_slots: SlotType[];
  /** Churn score thresholds */
  risk_thresholds: {
    high: number;
    medium: number;
    low: number;
  };
}

/**
 * Default configuration.
 */
export const DEFAULT_CHURN_DETECTOR_CONFIG: ChurnDetectorAgentConfig = {
  verbose: false,
  lookback_days: 180,
  min_events_for_velocity: 2,
  critical_slots: ["HR", "BENEFITS"],
  risk_thresholds: {
    high: 70,
    medium: 40,
    low: 20,
  },
};

/**
 * Task for ChurnDetectorAgent.
 */
export interface ChurnDetectorTask {
  task_id: string;
  company_id: string;
  company_name: string;
  movement_events: MovementEvent[];
}

/**
 * ChurnDetectorAgent - Detects executive turnover patterns.
 *
 * Execution Flow:
 * 1. Receive movement events from People Node
 * 2. Filter events within lookback period
 * 3. Analyze turnover patterns by slot type
 * 4. Calculate churn velocity
 * 5. Determine risk level
 * 6. Return analysis for BIT scoring
 */
export class ChurnDetectorAgent {
  private config: ChurnDetectorAgentConfig;

  constructor(config?: Partial<ChurnDetectorAgentConfig>) {
    this.config = {
      ...DEFAULT_CHURN_DETECTOR_CONFIG,
      ...config,
    };
  }

  /**
   * Run the churn detector agent.
   */
  async run(task: ChurnDetectorTask): Promise<AgentResult> {
    try {
      // Validate input
      if (!task.company_id || !task.company_name) {
        return this.createResult(task, false, {}, "company_id and company_name are required");
      }

      if (this.config.verbose) {
        console.log(`[ChurnDetectorAgent] Analyzing churn for: ${task.company_name}`);
      }

      // Filter events within lookback period
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - this.config.lookback_days);

      const recentEvents = task.movement_events.filter(
        (e) => new Date(e.detected_at) >= cutoffDate
      );

      // No events = no churn
      if (recentEvents.length === 0) {
        return this.createResult(task, true, {
          company_id: task.company_id,
          churn_detected: false,
          churn_score: 0,
          churn_velocity: 0,
          events_analyzed: 0,
          critical_churn: false,
          recent_events: [],
          risk_level: "NONE",
          recommendation: "No recent executive changes detected",
        } as ChurnAnalysis);
      }

      // Calculate churn metrics
      const churnScore = this.calculateChurnScore(recentEvents);
      const churnVelocity = this.calculateChurnVelocity(recentEvents);
      const criticalChurn = this.hasCriticalChurn(recentEvents);
      const riskLevel = this.determineRiskLevel(churnScore, criticalChurn);
      const recommendation = this.generateRecommendation(riskLevel, criticalChurn, recentEvents);

      const analysis: ChurnAnalysis = {
        company_id: task.company_id,
        churn_detected: recentEvents.length > 0,
        churn_score: churnScore,
        churn_velocity: churnVelocity,
        events_analyzed: recentEvents.length,
        critical_churn: criticalChurn,
        recent_events: recentEvents.slice(0, 5), // Top 5 most recent
        risk_level: riskLevel,
        recommendation,
      };

      return this.createResult(task, true, analysis);
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
   * Calculate churn score (0-100).
   */
  private calculateChurnScore(events: MovementEvent[]): number {
    let score = 0;

    for (const event of events) {
      // Base score per event
      let eventScore = 20;

      // Critical slot bonus
      if (this.config.critical_slots.includes(event.slot_type)) {
        eventScore += 30;
      }

      // Company change is more significant than title change
      if (event.movement_type === "company_change" || event.movement_type === "departure") {
        eventScore += 20;
      }

      // Recency bonus (more recent = higher score)
      const daysAgo = Math.floor(
        (Date.now() - new Date(event.detected_at).getTime()) / (1000 * 60 * 60 * 24)
      );
      if (daysAgo <= 30) {
        eventScore += 15;
      } else if (daysAgo <= 60) {
        eventScore += 10;
      } else if (daysAgo <= 90) {
        eventScore += 5;
      }

      score += eventScore;
    }

    return Math.min(score, 100);
  }

  /**
   * Calculate churn velocity (events per month).
   */
  private calculateChurnVelocity(events: MovementEvent[]): number {
    if (events.length < this.config.min_events_for_velocity) {
      return 0;
    }

    // Calculate time span
    const dates = events.map((e) => new Date(e.detected_at).getTime());
    const earliest = Math.min(...dates);
    const latest = Math.max(...dates);
    const monthsSpan = (latest - earliest) / (1000 * 60 * 60 * 24 * 30) || 1;

    return Math.round((events.length / monthsSpan) * 10) / 10;
  }

  /**
   * Check if any critical slot has churned.
   */
  private hasCriticalChurn(events: MovementEvent[]): boolean {
    return events.some((e) => this.config.critical_slots.includes(e.slot_type));
  }

  /**
   * Determine risk level from score and critical flag.
   */
  private determineRiskLevel(score: number, criticalChurn: boolean): ChurnRiskLevel {
    // Critical churn automatically elevates to at least MEDIUM
    if (criticalChurn && score < this.config.risk_thresholds.medium) {
      return "MEDIUM";
    }

    if (score >= this.config.risk_thresholds.high) return "HIGH";
    if (score >= this.config.risk_thresholds.medium) return "MEDIUM";
    if (score >= this.config.risk_thresholds.low) return "LOW";
    return "NONE";
  }

  /**
   * Generate recommendation based on analysis.
   */
  private generateRecommendation(
    riskLevel: ChurnRiskLevel,
    criticalChurn: boolean,
    events: MovementEvent[]
  ): string {
    if (riskLevel === "HIGH") {
      if (criticalChurn) {
        const criticalSlots = events
          .filter((e) => this.config.critical_slots.includes(e.slot_type))
          .map((e) => e.slot_type);
        return `HIGH PRIORITY: New ${criticalSlots.join("/")} executive detected. Immediate outreach recommended.`;
      }
      return "High executive turnover detected. Consider proactive outreach.";
    }

    if (riskLevel === "MEDIUM") {
      if (criticalChurn) {
        return "Recent change in HR/Benefits leadership. Good timing for introduction.";
      }
      return "Moderate executive changes. Monitor for additional signals.";
    }

    if (riskLevel === "LOW") {
      return "Minor executive changes. Add to nurture sequence.";
    }

    return "Stable executive team. No immediate action needed.";
  }

  /**
   * Batch analyze multiple companies.
   */
  async analyzeBatch(
    companies: Array<{
      company_id: string;
      company_name: string;
      movement_events: MovementEvent[];
    }>
  ): Promise<ChurnAnalysis[]> {
    const results: ChurnAnalysis[] = [];

    for (const company of companies) {
      const task: ChurnDetectorTask = {
        task_id: `churn_${company.company_id}_${Date.now()}`,
        company_id: company.company_id,
        company_name: company.company_name,
        movement_events: company.movement_events,
      };

      const result = await this.run(task);
      if (result.success && result.data) {
        results.push(result.data as ChurnAnalysis);
      }
    }

    return results;
  }

  /**
   * Get high-risk companies.
   */
  filterHighRisk(analyses: ChurnAnalysis[]): ChurnAnalysis[] {
    return analyses.filter((a) => a.risk_level === "HIGH" || a.critical_churn);
  }

  /**
   * Create a standardized AgentResult.
   */
  private createResult(
    task: ChurnDetectorTask,
    success: boolean,
    data: Record<string, unknown>,
    error?: string
  ): AgentResult {
    return {
      task_id: task.task_id,
      agent_type: "ChurnDetectorAgent",
      slot_row_id: task.company_id,
      success,
      data,
      error: error ?? null,
      completed_at: new Date(),
    };
  }

  getConfig(): ChurnDetectorAgentConfig {
    return { ...this.config };
  }

  updateConfig(config: Partial<ChurnDetectorAgentConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
