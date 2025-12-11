/**
 * CostGovernor
 * ============
 * Budget tracking and cost governance for the Talent Engine.
 *
 * Provides:
 * - Per-company budget tracking
 * - Per-slot-type budget allocation
 * - Daily/weekly/monthly budget caps
 * - Cost forecasting
 * - Budget alerts and warnings
 * - ROI tracking
 *
 * Usage:
 * ```typescript
 * const governor = new CostGovernor({
 *   daily_budget: 100.0,
 *   per_company_limit: 5.0,
 * });
 *
 * // Check if spend is allowed
 * const allowed = governor.canSpend("company_123", "proxycurl", 0.10);
 *
 * // Record spend
 * governor.recordSpend("company_123", "proxycurl", 0.10, "linkedin_lookup");
 *
 * // Get budget status
 * const status = governor.getBudgetStatus();
 * ```
 */

import { VendorId } from "./ThrottleManagerV2";

/**
 * Spend record for audit trail.
 */
export interface SpendRecord {
  id: string;
  timestamp: Date;
  company_id: string;
  vendor: VendorId;
  amount: number;
  operation: string;
  slot_type?: string;
  person_name?: string;
  success: boolean;
  metadata?: Record<string, unknown>;
}

/**
 * Budget period type.
 */
export type BudgetPeriod = "minute" | "hour" | "day" | "week" | "month";

/**
 * Budget allocation by category.
 */
export interface BudgetAllocation {
  linkedin_enrichment: number;
  email_discovery: number;
  email_verification: number;
  company_enrichment: number;
  llm_processing: number;
  other: number;
}

/**
 * Company budget state.
 */
export interface CompanyBudget {
  company_id: string;
  total_spent: number;
  limit: number;
  spend_by_vendor: Partial<Record<VendorId, number>>;
  spend_by_operation: Record<string, number>;
  last_spend_at: Date | null;
  blocked: boolean;
  block_reason?: string;
}

/**
 * Budget alert.
 */
export interface BudgetAlert {
  id: string;
  type: "warning" | "critical" | "exceeded";
  message: string;
  threshold_percent: number;
  current_percent: number;
  timestamp: Date;
  acknowledged: boolean;
}

/**
 * CostGovernor configuration.
 */
export interface CostGovernorConfig {
  /** Daily budget cap ($) */
  daily_budget: number;
  /** Weekly budget cap ($) */
  weekly_budget?: number;
  /** Monthly budget cap ($) */
  monthly_budget?: number;
  /** Per-company spend limit ($) */
  per_company_limit: number;
  /** Per-slot enrichment limit ($) */
  per_slot_limit?: number;
  /** Budget allocation by category */
  allocation?: Partial<BudgetAllocation>;
  /** Warning threshold (percent of budget) */
  warning_threshold?: number;
  /** Critical threshold (percent of budget) */
  critical_threshold?: number;
  /** Enable verbose logging */
  verbose?: boolean;
  /** Maximum spend records to keep */
  max_spend_records?: number;
}

/**
 * Default configuration.
 */
export const DEFAULT_COST_GOVERNOR_CONFIG: CostGovernorConfig = {
  daily_budget: 100.0,
  weekly_budget: 500.0,
  monthly_budget: 2000.0,
  per_company_limit: 5.0,
  per_slot_limit: 1.0,
  allocation: {
    linkedin_enrichment: 0.40, // 40% of budget
    email_discovery: 0.25,
    email_verification: 0.15,
    company_enrichment: 0.10,
    llm_processing: 0.05,
    other: 0.05,
  },
  warning_threshold: 75,
  critical_threshold: 90,
  verbose: false,
  max_spend_records: 10000,
};

/**
 * Budget status response.
 */
export interface BudgetStatus {
  daily: {
    spent: number;
    budget: number;
    remaining: number;
    percent_used: number;
  };
  weekly: {
    spent: number;
    budget: number;
    remaining: number;
    percent_used: number;
  };
  monthly: {
    spent: number;
    budget: number;
    remaining: number;
    percent_used: number;
  };
  by_vendor: Partial<Record<VendorId, number>>;
  by_operation: Record<string, number>;
  total_companies: number;
  blocked_companies: number;
  active_alerts: BudgetAlert[];
}

/**
 * Spend check result.
 */
export interface SpendCheckResult {
  allowed: boolean;
  reason?: string;
  remaining_budget?: number;
  company_remaining?: number;
}

/**
 * CostGovernor - Budget tracking and governance.
 */
export class CostGovernor {
  private config: CostGovernorConfig;
  private spendRecords: SpendRecord[] = [];
  private companyBudgets: Map<string, CompanyBudget> = new Map();
  private alerts: BudgetAlert[] = [];

  // Time window tracking
  private dayStart: Date;
  private weekStart: Date;
  private monthStart: Date;

  // Aggregated spend
  private dailySpend: number = 0;
  private weeklySpend: number = 0;
  private monthlySpend: number = 0;
  private spendByVendor: Partial<Record<VendorId, number>> = {};
  private spendByOperation: Record<string, number> = {};

  constructor(config?: Partial<CostGovernorConfig>) {
    this.config = {
      ...DEFAULT_COST_GOVERNOR_CONFIG,
      ...config,
    };

    // Initialize time windows
    const now = new Date();
    this.dayStart = this.getStartOfDay(now);
    this.weekStart = this.getStartOfWeek(now);
    this.monthStart = this.getStartOfMonth(now);

    if (this.config.verbose) {
      console.log("[CostGovernor] Initialized with config:", {
        daily_budget: this.config.daily_budget,
        per_company_limit: this.config.per_company_limit,
      });
    }
  }

  /**
   * Check if a spend is allowed.
   */
  canSpend(
    companyId: string,
    vendor: VendorId,
    amount: number,
    operation?: string
  ): SpendCheckResult {
    // Refresh time windows
    this.refreshTimeWindows();

    // Check daily budget
    if (this.dailySpend + amount > this.config.daily_budget) {
      return {
        allowed: false,
        reason: "daily_budget_exceeded",
        remaining_budget: this.config.daily_budget - this.dailySpend,
      };
    }

    // Check weekly budget
    if (this.config.weekly_budget && this.weeklySpend + amount > this.config.weekly_budget) {
      return {
        allowed: false,
        reason: "weekly_budget_exceeded",
        remaining_budget: this.config.weekly_budget - this.weeklySpend,
      };
    }

    // Check monthly budget
    if (this.config.monthly_budget && this.monthlySpend + amount > this.config.monthly_budget) {
      return {
        allowed: false,
        reason: "monthly_budget_exceeded",
        remaining_budget: this.config.monthly_budget - this.monthlySpend,
      };
    }

    // Check company budget
    const companyBudget = this.getOrCreateCompanyBudget(companyId);
    if (companyBudget.blocked) {
      return {
        allowed: false,
        reason: companyBudget.block_reason || "company_blocked",
        company_remaining: 0,
      };
    }

    if (companyBudget.total_spent + amount > companyBudget.limit) {
      return {
        allowed: false,
        reason: "company_budget_exceeded",
        company_remaining: companyBudget.limit - companyBudget.total_spent,
      };
    }

    return {
      allowed: true,
      remaining_budget: this.config.daily_budget - this.dailySpend - amount,
      company_remaining: companyBudget.limit - companyBudget.total_spent - amount,
    };
  }

  /**
   * Record a spend.
   */
  recordSpend(
    companyId: string,
    vendor: VendorId,
    amount: number,
    operation: string,
    options?: {
      slot_type?: string;
      person_name?: string;
      success?: boolean;
      metadata?: Record<string, unknown>;
    }
  ): SpendRecord {
    // Refresh time windows
    this.refreshTimeWindows();

    // Create record
    const record: SpendRecord = {
      id: `spend_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      company_id: companyId,
      vendor,
      amount,
      operation,
      slot_type: options?.slot_type,
      person_name: options?.person_name,
      success: options?.success ?? true,
      metadata: options?.metadata,
    };

    // Add to records
    this.spendRecords.push(record);

    // Trim if needed
    if (this.spendRecords.length > (this.config.max_spend_records || 10000)) {
      this.spendRecords = this.spendRecords.slice(-5000);
    }

    // Update aggregates
    this.dailySpend += amount;
    this.weeklySpend += amount;
    this.monthlySpend += amount;

    this.spendByVendor[vendor] = (this.spendByVendor[vendor] || 0) + amount;
    this.spendByOperation[operation] = (this.spendByOperation[operation] || 0) + amount;

    // Update company budget
    const companyBudget = this.getOrCreateCompanyBudget(companyId);
    companyBudget.total_spent += amount;
    companyBudget.spend_by_vendor[vendor] = (companyBudget.spend_by_vendor[vendor] || 0) + amount;
    companyBudget.spend_by_operation[operation] = (companyBudget.spend_by_operation[operation] || 0) + amount;
    companyBudget.last_spend_at = new Date();

    // Check for budget alerts
    this.checkBudgetAlerts();

    if (this.config.verbose) {
      console.log(`[CostGovernor] Recorded: ${companyId} / ${vendor} / $${amount.toFixed(4)} / ${operation}`);
    }

    return record;
  }

  /**
   * Get or create company budget.
   */
  private getOrCreateCompanyBudget(companyId: string): CompanyBudget {
    let budget = this.companyBudgets.get(companyId);

    if (!budget) {
      budget = {
        company_id: companyId,
        total_spent: 0,
        limit: this.config.per_company_limit,
        spend_by_vendor: {},
        spend_by_operation: {},
        last_spend_at: null,
        blocked: false,
      };
      this.companyBudgets.set(companyId, budget);
    }

    return budget;
  }

  /**
   * Refresh time windows.
   */
  private refreshTimeWindows(): void {
    const now = new Date();

    // Check day rollover
    const currentDayStart = this.getStartOfDay(now);
    if (currentDayStart.getTime() !== this.dayStart.getTime()) {
      this.dayStart = currentDayStart;
      this.dailySpend = 0;

      // Reset company budgets for new day
      for (const budget of this.companyBudgets.values()) {
        budget.total_spent = 0;
        budget.blocked = false;
        budget.block_reason = undefined;
      }

      if (this.config.verbose) {
        console.log("[CostGovernor] Day rollover - daily spend reset");
      }
    }

    // Check week rollover
    const currentWeekStart = this.getStartOfWeek(now);
    if (currentWeekStart.getTime() !== this.weekStart.getTime()) {
      this.weekStart = currentWeekStart;
      this.weeklySpend = 0;

      if (this.config.verbose) {
        console.log("[CostGovernor] Week rollover - weekly spend reset");
      }
    }

    // Check month rollover
    const currentMonthStart = this.getStartOfMonth(now);
    if (currentMonthStart.getTime() !== this.monthStart.getTime()) {
      this.monthStart = currentMonthStart;
      this.monthlySpend = 0;

      if (this.config.verbose) {
        console.log("[CostGovernor] Month rollover - monthly spend reset");
      }
    }
  }

  /**
   * Check for budget alerts.
   */
  private checkBudgetAlerts(): void {
    const dailyPercent = (this.dailySpend / this.config.daily_budget) * 100;

    // Warning alert
    if (
      dailyPercent >= (this.config.warning_threshold || 75) &&
      dailyPercent < (this.config.critical_threshold || 90)
    ) {
      this.createAlert("warning", `Daily budget at ${dailyPercent.toFixed(1)}%`, dailyPercent);
    }

    // Critical alert
    if (
      dailyPercent >= (this.config.critical_threshold || 90) &&
      dailyPercent < 100
    ) {
      this.createAlert("critical", `Daily budget at ${dailyPercent.toFixed(1)}% - approaching limit`, dailyPercent);
    }

    // Exceeded alert
    if (dailyPercent >= 100) {
      this.createAlert("exceeded", `Daily budget EXCEEDED at ${dailyPercent.toFixed(1)}%`, dailyPercent);
    }
  }

  /**
   * Create a budget alert.
   */
  private createAlert(
    type: BudgetAlert["type"],
    message: string,
    currentPercent: number
  ): void {
    // Don't create duplicate alerts
    const existing = this.alerts.find(
      (a) => a.type === type && !a.acknowledged && Date.now() - a.timestamp.getTime() < 3600000
    );
    if (existing) return;

    const thresholdPercent =
      type === "warning"
        ? this.config.warning_threshold || 75
        : type === "critical"
        ? this.config.critical_threshold || 90
        : 100;

    const alert: BudgetAlert = {
      id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      message,
      threshold_percent: thresholdPercent,
      current_percent: currentPercent,
      timestamp: new Date(),
      acknowledged: false,
    };

    this.alerts.push(alert);

    if (this.config.verbose) {
      console.log(`[CostGovernor] ALERT (${type}): ${message}`);
    }
  }

  /**
   * Acknowledge an alert.
   */
  acknowledgeAlert(alertId: string): boolean {
    const alert = this.alerts.find((a) => a.id === alertId);
    if (alert) {
      alert.acknowledged = true;
      return true;
    }
    return false;
  }

  /**
   * Get budget status.
   */
  getBudgetStatus(): BudgetStatus {
    this.refreshTimeWindows();

    return {
      daily: {
        spent: this.dailySpend,
        budget: this.config.daily_budget,
        remaining: this.config.daily_budget - this.dailySpend,
        percent_used: (this.dailySpend / this.config.daily_budget) * 100,
      },
      weekly: {
        spent: this.weeklySpend,
        budget: this.config.weekly_budget || 0,
        remaining: (this.config.weekly_budget || 0) - this.weeklySpend,
        percent_used: this.config.weekly_budget
          ? (this.weeklySpend / this.config.weekly_budget) * 100
          : 0,
      },
      monthly: {
        spent: this.monthlySpend,
        budget: this.config.monthly_budget || 0,
        remaining: (this.config.monthly_budget || 0) - this.monthlySpend,
        percent_used: this.config.monthly_budget
          ? (this.monthlySpend / this.config.monthly_budget) * 100
          : 0,
      },
      by_vendor: { ...this.spendByVendor },
      by_operation: { ...this.spendByOperation },
      total_companies: this.companyBudgets.size,
      blocked_companies: Array.from(this.companyBudgets.values()).filter((b) => b.blocked).length,
      active_alerts: this.alerts.filter((a) => !a.acknowledged),
    };
  }

  /**
   * Get company budget.
   */
  getCompanyBudget(companyId: string): CompanyBudget | null {
    return this.companyBudgets.get(companyId) || null;
  }

  /**
   * Block a company.
   */
  blockCompany(companyId: string, reason: string): void {
    const budget = this.getOrCreateCompanyBudget(companyId);
    budget.blocked = true;
    budget.block_reason = reason;

    if (this.config.verbose) {
      console.log(`[CostGovernor] Company blocked: ${companyId} - ${reason}`);
    }
  }

  /**
   * Unblock a company.
   */
  unblockCompany(companyId: string): void {
    const budget = this.companyBudgets.get(companyId);
    if (budget) {
      budget.blocked = false;
      budget.block_reason = undefined;

      if (this.config.verbose) {
        console.log(`[CostGovernor] Company unblocked: ${companyId}`);
      }
    }
  }

  /**
   * Set company budget limit.
   */
  setCompanyLimit(companyId: string, limit: number): void {
    const budget = this.getOrCreateCompanyBudget(companyId);
    budget.limit = limit;

    if (this.config.verbose) {
      console.log(`[CostGovernor] Company limit set: ${companyId} = $${limit}`);
    }
  }

  /**
   * Get spend records for a company.
   */
  getCompanySpendRecords(companyId: string, limit: number = 100): SpendRecord[] {
    return this.spendRecords
      .filter((r) => r.company_id === companyId)
      .slice(-limit);
  }

  /**
   * Get spend records by vendor.
   */
  getVendorSpendRecords(vendor: VendorId, limit: number = 100): SpendRecord[] {
    return this.spendRecords
      .filter((r) => r.vendor === vendor)
      .slice(-limit);
  }

  /**
   * Get recent spend records.
   */
  getRecentRecords(limit: number = 100): SpendRecord[] {
    return this.spendRecords.slice(-limit);
  }

  /**
   * Forecast spend to end of day.
   */
  forecastDailySpend(): {
    current: number;
    projected: number;
    projected_percent: number;
    will_exceed: boolean;
  } {
    const now = new Date();
    const hoursElapsed = (now.getTime() - this.dayStart.getTime()) / 3600000;
    const hoursRemaining = 24 - hoursElapsed;

    if (hoursElapsed < 0.5) {
      // Not enough data
      return {
        current: this.dailySpend,
        projected: this.dailySpend,
        projected_percent: (this.dailySpend / this.config.daily_budget) * 100,
        will_exceed: false,
      };
    }

    const hourlyRate = this.dailySpend / hoursElapsed;
    const projected = this.dailySpend + hourlyRate * hoursRemaining;

    return {
      current: this.dailySpend,
      projected,
      projected_percent: (projected / this.config.daily_budget) * 100,
      will_exceed: projected > this.config.daily_budget,
    };
  }

  /**
   * Get ROI metrics.
   */
  getROIMetrics(): {
    total_spend: number;
    successful_operations: number;
    failed_operations: number;
    success_rate: number;
    cost_per_success: number;
    spend_by_category: Record<string, { spend: number; count: number; avg: number }>;
  } {
    const successful = this.spendRecords.filter((r) => r.success);
    const failed = this.spendRecords.filter((r) => !r.success);
    const totalSpend = this.spendRecords.reduce((sum, r) => sum + r.amount, 0);

    const byCategory: Record<string, { spend: number; count: number }> = {};
    for (const record of this.spendRecords) {
      if (!byCategory[record.operation]) {
        byCategory[record.operation] = { spend: 0, count: 0 };
      }
      byCategory[record.operation].spend += record.amount;
      byCategory[record.operation].count++;
    }

    const spendByCategory: Record<string, { spend: number; count: number; avg: number }> = {};
    for (const [op, data] of Object.entries(byCategory)) {
      spendByCategory[op] = {
        ...data,
        avg: data.count > 0 ? data.spend / data.count : 0,
      };
    }

    return {
      total_spend: totalSpend,
      successful_operations: successful.length,
      failed_operations: failed.length,
      success_rate: this.spendRecords.length > 0
        ? (successful.length / this.spendRecords.length) * 100
        : 0,
      cost_per_success: successful.length > 0
        ? totalSpend / successful.length
        : 0,
      spend_by_category: spendByCategory,
    };
  }

  /**
   * Generate cost report.
   */
  generateReport(): string {
    const status = this.getBudgetStatus();
    const forecast = this.forecastDailySpend();
    const roi = this.getROIMetrics();
    const lines: string[] = [];

    lines.push("=".repeat(70));
    lines.push("COST GOVERNOR - BUDGET REPORT");
    lines.push("=".repeat(70));
    lines.push("");

    lines.push("BUDGET STATUS");
    lines.push("-".repeat(50));
    lines.push(`  Daily:   $${status.daily.spent.toFixed(2)} / $${status.daily.budget.toFixed(2)} (${status.daily.percent_used.toFixed(1)}%)`);
    lines.push(`  Weekly:  $${status.weekly.spent.toFixed(2)} / $${status.weekly.budget.toFixed(2)} (${status.weekly.percent_used.toFixed(1)}%)`);
    lines.push(`  Monthly: $${status.monthly.spent.toFixed(2)} / $${status.monthly.budget.toFixed(2)} (${status.monthly.percent_used.toFixed(1)}%)`);
    lines.push("");

    lines.push("FORECAST");
    lines.push("-".repeat(50));
    lines.push(`  Current:   $${forecast.current.toFixed(2)}`);
    lines.push(`  Projected: $${forecast.projected.toFixed(2)} (${forecast.projected_percent.toFixed(1)}%)`);
    lines.push(`  Status:    ${forecast.will_exceed ? "WILL EXCEED BUDGET" : "Within budget"}`);
    lines.push("");

    lines.push("SPEND BY VENDOR");
    lines.push("-".repeat(50));
    for (const [vendor, amount] of Object.entries(status.by_vendor)) {
      if (amount && amount > 0) {
        lines.push(`  ${vendor}: $${amount.toFixed(4)}`);
      }
    }
    lines.push("");

    lines.push("ROI METRICS");
    lines.push("-".repeat(50));
    lines.push(`  Total Spend:      $${roi.total_spend.toFixed(4)}`);
    lines.push(`  Successful Ops:   ${roi.successful_operations}`);
    lines.push(`  Failed Ops:       ${roi.failed_operations}`);
    lines.push(`  Success Rate:     ${roi.success_rate.toFixed(1)}%`);
    lines.push(`  Cost per Success: $${roi.cost_per_success.toFixed(4)}`);
    lines.push("");

    if (status.active_alerts.length > 0) {
      lines.push("ACTIVE ALERTS");
      lines.push("-".repeat(50));
      for (const alert of status.active_alerts) {
        lines.push(`  [${alert.type.toUpperCase()}] ${alert.message}`);
      }
      lines.push("");
    }

    lines.push(`Companies: ${status.total_companies} total, ${status.blocked_companies} blocked`);
    lines.push("");
    lines.push("=".repeat(70));

    return lines.join("\n");
  }

  /**
   * Reset daily counters (for testing).
   */
  resetDaily(): void {
    this.dailySpend = 0;
    this.dayStart = this.getStartOfDay(new Date());

    for (const budget of this.companyBudgets.values()) {
      budget.total_spent = 0;
      budget.blocked = false;
      budget.block_reason = undefined;
    }

    if (this.config.verbose) {
      console.log("[CostGovernor] Daily reset complete");
    }
  }

  /**
   * Full reset (for testing).
   */
  reset(): void {
    this.dailySpend = 0;
    this.weeklySpend = 0;
    this.monthlySpend = 0;
    this.spendRecords = [];
    this.companyBudgets.clear();
    this.alerts = [];
    this.spendByVendor = {};
    this.spendByOperation = {};

    const now = new Date();
    this.dayStart = this.getStartOfDay(now);
    this.weekStart = this.getStartOfWeek(now);
    this.monthStart = this.getStartOfMonth(now);

    if (this.config.verbose) {
      console.log("[CostGovernor] Full reset complete");
    }
  }

  // Helper methods for date calculations
  private getStartOfDay(date: Date): Date {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    return d;
  }

  private getStartOfWeek(date: Date): Date {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    d.setDate(diff);
    d.setHours(0, 0, 0, 0);
    return d;
  }

  private getStartOfMonth(date: Date): Date {
    const d = new Date(date);
    d.setDate(1);
    d.setHours(0, 0, 0, 0);
    return d;
  }

  /**
   * Get configuration.
   */
  getConfig(): CostGovernorConfig {
    return { ...this.config };
  }

  /**
   * Update configuration.
   */
  updateConfig(config: Partial<CostGovernorConfig>): void {
    this.config = { ...this.config, ...config };
  }
}

/**
 * Global cost governor instance.
 */
export const globalCostGovernor = new CostGovernor();

/**
 * Create a cost governor with custom config.
 */
export function createCostGovernor(config?: Partial<CostGovernorConfig>): CostGovernor {
  return new CostGovernor(config);
}
