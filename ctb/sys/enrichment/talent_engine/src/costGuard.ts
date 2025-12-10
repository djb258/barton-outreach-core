/**
 * Cost Guard
 * ==========
 * Global spend guardrails for the Talent Engine.
 * Tracks daily and monthly spend with configurable limits.
 */

/**
 * Configuration for CostGuard.
 */
export interface CostGuardConfig {
  dailyLimit: number;
  monthlyLimit: number;
}

/**
 * Default cost guard limits.
 */
export const DEFAULT_COST_GUARD_CONFIG: CostGuardConfig = {
  dailyLimit: 50.0,    // $50/day
  monthlyLimit: 500.0, // $500/month
};

/**
 * CostGuard manages global spend limits.
 */
export class CostGuard {
  dailyLimit: number;
  monthlyLimit: number;
  dailySpend: number;
  monthlySpend: number;
  lastDayReset: Date;
  lastMonthReset: Date;

  constructor(config?: Partial<CostGuardConfig>) {
    const now = new Date();
    this.dailyLimit = config?.dailyLimit ?? DEFAULT_COST_GUARD_CONFIG.dailyLimit;
    this.monthlyLimit = config?.monthlyLimit ?? DEFAULT_COST_GUARD_CONFIG.monthlyLimit;
    this.dailySpend = 0;
    this.monthlySpend = 0;
    this.lastDayReset = now;
    this.lastMonthReset = now;
  }

  /**
   * Reset counters if time windows have elapsed.
   */
  private resetIfNeeded(): void {
    const now = new Date();

    // Reset daily counter if a day has passed
    const dayElapsed = now.getTime() - this.lastDayReset.getTime();
    if (dayElapsed >= 86400000) { // 24 hours in ms
      this.dailySpend = 0;
      this.lastDayReset = now;
    }

    // Reset monthly counter if a month has passed (30 days approximation)
    const monthElapsed = now.getTime() - this.lastMonthReset.getTime();
    if (monthElapsed >= 2592000000) { // 30 days in ms
      this.monthlySpend = 0;
      this.lastMonthReset = now;
    }
  }

  /**
   * Check if we can spend a given amount without exceeding limits.
   * @param amount - Amount to spend in USD
   * @returns true if spend is allowed
   */
  canSpend(amount: number): boolean {
    this.resetIfNeeded();
    return (
      this.dailySpend + amount <= this.dailyLimit &&
      this.monthlySpend + amount <= this.monthlyLimit
    );
  }

  /**
   * Record a spend amount.
   * @param amount - Amount spent in USD
   */
  recordSpend(amount: number): void {
    this.resetIfNeeded();
    this.dailySpend += amount;
    this.monthlySpend += amount;
  }

  /**
   * Get remaining daily budget.
   */
  getRemainingDaily(): number {
    this.resetIfNeeded();
    return Math.max(0, this.dailyLimit - this.dailySpend);
  }

  /**
   * Get remaining monthly budget.
   */
  getRemainingMonthly(): number {
    this.resetIfNeeded();
    return Math.max(0, this.monthlyLimit - this.monthlySpend);
  }

  /**
   * Check if daily limit is exceeded.
   */
  isDailyLimitExceeded(): boolean {
    this.resetIfNeeded();
    return this.dailySpend >= this.dailyLimit;
  }

  /**
   * Check if monthly limit is exceeded.
   */
  isMonthlyLimitExceeded(): boolean {
    this.resetIfNeeded();
    return this.monthlySpend >= this.monthlyLimit;
  }

  /**
   * Get current spend status as a string.
   */
  getStatusString(): string {
    this.resetIfNeeded();
    return `Daily: $${this.dailySpend.toFixed(2)}/$${this.dailyLimit.toFixed(2)}, Monthly: $${this.monthlySpend.toFixed(2)}/$${this.monthlyLimit.toFixed(2)}`;
  }

  /**
   * Reset all spend counters (for testing).
   */
  reset(): void {
    const now = new Date();
    this.dailySpend = 0;
    this.monthlySpend = 0;
    this.lastDayReset = now;
    this.lastMonthReset = now;
  }
}

/**
 * Global cost guard instance.
 * Shared across all dispatchers.
 */
export const globalCostGuard = new CostGuard();
