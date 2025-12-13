/**
 * MetricsGenerator
 * ================
 * Metrics tracking and reporting for the Talent Engine.
 *
 * Features:
 * - Validation metrics (company/person)
 * - Email generation metrics with skip tracking
 * - Skip reason breakdown
 * - Agent performance metrics
 * - Cost tracking
 *
 * Integrates with AgentEventLog for detailed event-based metrics.
 */

import {
  SlotRow,
  AgentEventLog,
  globalEventLog,
  EmailSkipReason,
} from "../models";
import { NodeExecutionResult, ValidationSummary } from "../dispatcher/NodeDispatcher";

/**
 * Validation metrics.
 */
export interface ValidationMetrics {
  /** Company validation */
  companies_processed: number;
  companies_valid: number;
  companies_invalid: number;
  companies_manual_review: number;
  company_validation_rate: number;

  /** Person-company validation */
  people_processed: number;
  people_valid: number;
  people_invalid: number;
  person_validation_rate: number;
}

/**
 * Email generation metrics.
 */
export interface EmailMetrics {
  /** Total people eligible for email */
  total_eligible: number;
  /** Emails successfully generated */
  emails_generated: number;
  /** Emails verified */
  emails_verified: number;
  /** Emails skipped due to validation */
  emails_skipped: number;
  /** Generation rate (generated / eligible) */
  generation_rate: number;
  /** Skip rate (skipped / eligible) */
  skip_rate: number;
}

/**
 * Skip reason metrics.
 */
export interface SkipMetrics {
  total_skipped: number;
  by_reason: Record<EmailSkipReason, number>;
  top_reasons: Array<{ reason: string; count: number; percentage: number }>;
}

/**
 * Agent performance metrics.
 */
export interface AgentMetrics {
  agent_name: string;
  executions: number;
  successes: number;
  failures: number;
  success_rate: number;
  total_cost: number;
  avg_cost_per_execution: number;
}

/**
 * Full metrics report.
 */
export interface MetricsReport {
  timestamp: Date;
  period_start?: Date;
  period_end?: Date;
  validation: ValidationMetrics;
  email: EmailMetrics;
  skips: SkipMetrics;
  agents: AgentMetrics[];
  total_cost: number;
}

/**
 * MetricsGenerator - Tracks and reports pipeline metrics.
 */
export class MetricsGenerator {
  private eventLog: AgentEventLog;

  constructor(eventLog?: AgentEventLog) {
    this.eventLog = eventLog || globalEventLog;
  }

  /**
   * Generate metrics from processed SlotRows.
   */
  generateFromSlotRows(rows: SlotRow[]): MetricsReport {
    const validation = this.calculateValidationMetrics(rows);
    const email = this.calculateEmailMetrics(rows);
    const skips = this.calculateSkipMetrics(rows);

    return {
      timestamp: new Date(),
      validation,
      email,
      skips,
      agents: [],
      total_cost: 0,
    };
  }

  /**
   * Generate metrics from node execution results.
   */
  generateFromNodeResults(results: {
    company_hub: NodeExecutionResult;
    people_node: NodeExecutionResult;
    dol_node: NodeExecutionResult;
    bit_node: NodeExecutionResult;
  }): MetricsReport {
    const companyHubSummary = results.company_hub.validation_summary;
    const peopleNodeSummary = results.people_node.validation_summary;

    const validation: ValidationMetrics = {
      companies_processed: 1, // Single company per execution
      companies_valid: companyHubSummary?.company_valid ? 1 : 0,
      companies_invalid: companyHubSummary?.company_valid ? 0 : 1,
      companies_manual_review: 0,
      company_validation_rate: companyHubSummary?.company_valid ? 100 : 0,

      people_processed: peopleNodeSummary?.people_validated || 0,
      people_valid: peopleNodeSummary?.people_valid || 0,
      people_invalid: peopleNodeSummary?.people_invalid || 0,
      person_validation_rate: peopleNodeSummary?.people_validated
        ? ((peopleNodeSummary.people_valid || 0) / peopleNodeSummary.people_validated) * 100
        : 0,
    };

    const totalEligible = peopleNodeSummary?.people_validated || 0;
    const generated = peopleNodeSummary?.emails_generated || 0;
    const skipped = peopleNodeSummary?.emails_skipped || 0;

    const email: EmailMetrics = {
      total_eligible: totalEligible,
      emails_generated: generated,
      emails_verified: 0, // Would need additional tracking
      emails_skipped: skipped,
      generation_rate: totalEligible ? (generated / totalEligible) * 100 : 0,
      skip_rate: totalEligible ? (skipped / totalEligible) * 100 : 0,
    };

    const skipReasons = peopleNodeSummary?.skip_reasons || {};
    const skips = this.buildSkipMetrics(skipReasons);

    // Calculate total cost
    const totalCost =
      results.company_hub.cost_incurred +
      results.people_node.cost_incurred +
      results.dol_node.cost_incurred +
      results.bit_node.cost_incurred;

    return {
      timestamp: new Date(),
      validation,
      email,
      skips,
      agents: [],
      total_cost: totalCost,
    };
  }

  /**
   * Calculate validation metrics from SlotRows.
   */
  private calculateValidationMetrics(rows: SlotRow[]): ValidationMetrics {
    const companiesValid = rows.filter((r) => r.company_valid === true).length;
    const companiesInvalid = rows.filter((r) => r.company_valid === false).length;
    const totalCompanies = companiesValid + companiesInvalid;

    const peopleValid = rows.filter((r) => r.person_company_valid === true).length;
    const peopleInvalid = rows.filter((r) => r.person_company_valid === false).length;
    const totalPeople = rows.filter((r) => r.person_name).length;

    return {
      companies_processed: totalCompanies,
      companies_valid: companiesValid,
      companies_invalid: companiesInvalid,
      companies_manual_review: rows.filter(
        (r) => r.fuzzy_match_status === "MANUAL_REVIEW"
      ).length,
      company_validation_rate: totalCompanies
        ? (companiesValid / totalCompanies) * 100
        : 0,

      people_processed: totalPeople,
      people_valid: peopleValid,
      people_invalid: peopleInvalid,
      person_validation_rate: totalPeople
        ? (peopleValid / totalPeople) * 100
        : 0,
    };
  }

  /**
   * Calculate email metrics from SlotRows.
   */
  private calculateEmailMetrics(rows: SlotRow[]): EmailMetrics {
    const eligible = rows.filter((r) => r.person_name);
    const generated = rows.filter((r) => r.email);
    const verified = rows.filter((r) => r.email_verified);
    const skipped = rows.filter((r) => r.skip_email);

    return {
      total_eligible: eligible.length,
      emails_generated: generated.length,
      emails_verified: verified.length,
      emails_skipped: skipped.length,
      generation_rate: eligible.length
        ? (generated.length / eligible.length) * 100
        : 0,
      skip_rate: eligible.length
        ? (skipped.length / eligible.length) * 100
        : 0,
    };
  }

  /**
   * Calculate skip metrics from SlotRows.
   */
  private calculateSkipMetrics(rows: SlotRow[]): SkipMetrics {
    const skippedRows = rows.filter((r) => r.skip_email);
    const reasonCounts: Record<string, number> = {};

    for (const row of skippedRows) {
      const reason = this.categorizeSkipReason(row.skip_reason);
      reasonCounts[reason] = (reasonCounts[reason] || 0) + 1;
    }

    return this.buildSkipMetrics(reasonCounts);
  }

  /**
   * Build skip metrics from reason counts.
   */
  private buildSkipMetrics(reasonCounts: Record<string, number>): SkipMetrics {
    const total = Object.values(reasonCounts).reduce((sum, c) => sum + c, 0);

    const topReasons = Object.entries(reasonCounts)
      .map(([reason, count]) => ({
        reason,
        count,
        percentage: total ? (count / total) * 100 : 0,
      }))
      .sort((a, b) => b.count - a.count);

    return {
      total_skipped: total,
      by_reason: reasonCounts as Record<EmailSkipReason, number>,
      top_reasons: topReasons,
    };
  }

  /**
   * Categorize skip reason into standard categories.
   */
  private categorizeSkipReason(reason: string | null): EmailSkipReason {
    if (!reason) return "OTHER";

    const lowerReason = reason.toLowerCase();

    if (lowerReason.includes("company") && lowerReason.includes("invalid")) {
      return "COMPANY_INVALID";
    }
    if (lowerReason.includes("manual review")) {
      return "COMPANY_MANUAL_REVIEW";
    }
    if (lowerReason.includes("person") && lowerReason.includes("match")) {
      return "PERSON_COMPANY_MISMATCH";
    }
    if (lowerReason.includes("pattern")) {
      return "NO_EMAIL_PATTERN";
    }
    if (lowerReason.includes("person_name")) {
      return "NO_PERSON_NAME";
    }
    if (lowerReason.includes("company_name")) {
      return "NO_COMPANY_NAME";
    }
    if (lowerReason.includes("linkedin")) {
      return "NO_LINKEDIN_URL";
    }

    return "OTHER";
  }

  /**
   * Generate text report.
   */
  generateTextReport(metrics: MetricsReport): string {
    const lines: string[] = [];

    lines.push("=".repeat(60));
    lines.push("TALENT ENGINE METRICS REPORT");
    lines.push(`Generated: ${metrics.timestamp.toISOString()}`);
    lines.push("=".repeat(60));
    lines.push("");

    // Validation Section
    lines.push("VALIDATION METRICS");
    lines.push("-".repeat(40));
    lines.push(`  Companies Processed:    ${metrics.validation.companies_processed}`);
    lines.push(`  Companies Valid:        ${metrics.validation.companies_valid}`);
    lines.push(`  Companies Invalid:      ${metrics.validation.companies_invalid}`);
    lines.push(`  Company Validation Rate: ${metrics.validation.company_validation_rate.toFixed(1)}%`);
    lines.push("");
    lines.push(`  People Processed:       ${metrics.validation.people_processed}`);
    lines.push(`  People Valid:           ${metrics.validation.people_valid}`);
    lines.push(`  People Invalid:         ${metrics.validation.people_invalid}`);
    lines.push(`  Person Validation Rate: ${metrics.validation.person_validation_rate.toFixed(1)}%`);
    lines.push("");

    // Email Section
    lines.push("EMAIL GENERATION METRICS");
    lines.push("-".repeat(40));
    lines.push(`  Total Eligible:         ${metrics.email.total_eligible}`);
    lines.push(`  Emails Generated:       ${metrics.email.emails_generated}`);
    lines.push(`  Emails Verified:        ${metrics.email.emails_verified}`);
    lines.push(`  Emails Skipped:         ${metrics.email.emails_skipped}`);
    lines.push(`  Generation Rate:        ${metrics.email.generation_rate.toFixed(1)}%`);
    lines.push(`  Skip Rate:              ${metrics.email.skip_rate.toFixed(1)}%`);
    lines.push("");

    // Skip Reasons Section
    lines.push("SKIP REASONS BREAKDOWN");
    lines.push("-".repeat(40));
    if (metrics.skips.top_reasons.length === 0) {
      lines.push("  No emails skipped");
    } else {
      for (const { reason, count, percentage } of metrics.skips.top_reasons) {
        lines.push(`  ${reason}: ${count} (${percentage.toFixed(1)}%)`);
      }
    }
    lines.push("");

    // Cost Section
    lines.push("COST SUMMARY");
    lines.push("-".repeat(40));
    lines.push(`  Total Cost: $${metrics.total_cost.toFixed(4)}`);
    lines.push("");

    lines.push("=".repeat(60));

    return lines.join("\n");
  }

  /**
   * Export metrics to JSON.
   */
  exportToJSON(metrics: MetricsReport): string {
    return JSON.stringify(metrics, null, 2);
  }

  /**
   * Get metrics from event log.
   */
  getEventLogMetrics(): MetricsReport {
    const summary = this.eventLog.getValidationSummary();
    const skipStats = this.eventLog.getSkipStatistics();

    const validation: ValidationMetrics = {
      companies_processed: summary.companies_validated,
      companies_valid: summary.companies_valid,
      companies_invalid: summary.companies_invalid,
      companies_manual_review: 0,
      company_validation_rate: summary.companies_validated
        ? (summary.companies_valid / summary.companies_validated) * 100
        : 0,

      people_processed: summary.people_validated,
      people_valid: summary.people_valid,
      people_invalid: summary.people_invalid,
      person_validation_rate: summary.people_validated
        ? (summary.people_valid / summary.people_validated) * 100
        : 0,
    };

    const totalEligible = summary.people_validated;
    const email: EmailMetrics = {
      total_eligible: totalEligible,
      emails_generated: summary.emails_generated,
      emails_verified: 0,
      emails_skipped: summary.emails_skipped,
      generation_rate: totalEligible
        ? (summary.emails_generated / totalEligible) * 100
        : 0,
      skip_rate: totalEligible
        ? (summary.emails_skipped / totalEligible) * 100
        : 0,
    };

    return {
      timestamp: new Date(),
      validation,
      email,
      skips: this.buildSkipMetrics(skipStats.by_reason),
      agents: [],
      total_cost: 0,
    };
  }
}

/**
 * Global metrics generator instance.
 */
export const globalMetricsGenerator = new MetricsGenerator();
