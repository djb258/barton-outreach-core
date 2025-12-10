/**
 * Throttle System
 * ===============
 * Manages rate limiting for the Talent Engine pipeline.
 * Tracks calls per minute and per day.
 */

import { ThrottleState } from "./SlotRow";

/**
 * Default throttle configuration.
 */
export const DEFAULT_THROTTLE_CONFIG = {
  max_calls_per_minute: 60,
  max_calls_per_day: 10000,
};

/**
 * ThrottleManager handles rate limiting for agent calls.
 */
export class ThrottleManager {
  private state: ThrottleState;

  constructor(config?: Partial<ThrottleState>) {
    const now = new Date();
    this.state = {
      max_calls_per_minute: config?.max_calls_per_minute ?? DEFAULT_THROTTLE_CONFIG.max_calls_per_minute,
      max_calls_per_day: config?.max_calls_per_day ?? DEFAULT_THROTTLE_CONFIG.max_calls_per_day,
      calls_this_minute: config?.calls_this_minute ?? 0,
      calls_today: config?.calls_today ?? 0,
      last_reset_minute: config?.last_reset_minute ?? now,
      last_reset_day: config?.last_reset_day ?? now,
    };
  }

  /**
   * Check if throttle limits have been exceeded.
   * @returns true if throttled (cannot make more calls)
   */
  isThrottled(): boolean {
    this.resetIfNeeded();
    return (
      this.state.calls_this_minute >= this.state.max_calls_per_minute ||
      this.state.calls_today >= this.state.max_calls_per_day
    );
  }

  /**
   * Record a call (increment counters).
   * Should be called after successfully routing a task.
   */
  recordCall(): void {
    this.resetIfNeeded();
    this.state.calls_this_minute++;
    this.state.calls_today++;
  }

  /**
   * Reset counters if time windows have elapsed.
   */
  private resetIfNeeded(): void {
    const now = new Date();

    // Reset minute counter if a minute has passed
    const minuteElapsed = now.getTime() - this.state.last_reset_minute.getTime();
    if (minuteElapsed >= 60000) {
      this.state.calls_this_minute = 0;
      this.state.last_reset_minute = now;
    }

    // Reset day counter if a day has passed
    const dayElapsed = now.getTime() - this.state.last_reset_day.getTime();
    if (dayElapsed >= 86400000) {
      this.state.calls_today = 0;
      this.state.last_reset_day = now;
    }
  }

  /**
   * Get current throttle state.
   */
  getState(): ThrottleState {
    this.resetIfNeeded();
    return { ...this.state };
  }

  /**
   * Get remaining calls for the current minute.
   */
  getRemainingMinute(): number {
    this.resetIfNeeded();
    return Math.max(0, this.state.max_calls_per_minute - this.state.calls_this_minute);
  }

  /**
   * Get remaining calls for today.
   */
  getRemainingToday(): number {
    this.resetIfNeeded();
    return Math.max(0, this.state.max_calls_per_day - this.state.calls_today);
  }

  /**
   * Get throttle status as a string.
   */
  getStatusString(): string {
    const state = this.getState();
    return `Minute: ${state.calls_this_minute}/${state.max_calls_per_minute}, Day: ${state.calls_today}/${state.max_calls_per_day}`;
  }
}
