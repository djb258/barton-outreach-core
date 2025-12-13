/**
 * Retry Utility
 * =============
 * Generic retry wrapper for service calls with exponential backoff.
 */

import { ServiceResponse } from "../services/types";

/**
 * Retry configuration options.
 */
export interface RetryConfig {
  /** Maximum number of retry attempts (default: 2) */
  retries?: number;
  /** Base delay in milliseconds between retries (default: 200) */
  delay?: number;
  /** Whether to use exponential backoff (default: true) */
  exponentialBackoff?: boolean;
  /** Maximum delay in milliseconds (default: 5000) */
  maxDelay?: number;
  /** Only retry if the response indicates retryable (default: true) */
  respectRetryable?: boolean;
}

/**
 * Default retry configuration.
 */
export const DEFAULT_RETRY_CONFIG: Required<RetryConfig> = {
  retries: 2,
  delay: 200,
  exponentialBackoff: true,
  maxDelay: 5000,
  respectRetryable: true,
};

/**
 * Sleep for a specified duration.
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Calculate delay for current attempt with exponential backoff.
 */
function calculateDelay(
  attempt: number,
  baseDelay: number,
  exponential: boolean,
  maxDelay: number
): number {
  if (!exponential) {
    return baseDelay;
  }
  // Exponential backoff: delay * 2^attempt with jitter
  const expDelay = baseDelay * Math.pow(2, attempt);
  const jitter = Math.random() * 0.1 * expDelay; // 10% jitter
  return Math.min(expDelay + jitter, maxDelay);
}

/**
 * Execute a function with retry logic.
 * Returns ServiceResponse format - never throws.
 *
 * @param fn - Async function that returns ServiceResponse
 * @param config - Retry configuration
 * @returns ServiceResponse with result or error
 *
 * @example
 * ```typescript
 * const result = await withRetry(
 *   () => proxycurlService.getLinkedInProfile(url),
 *   { retries: 3, delay: 500 }
 * );
 * ```
 */
export async function withRetry<T>(
  fn: () => Promise<ServiceResponse<T>>,
  config?: RetryConfig
): Promise<ServiceResponse<T>> {
  const {
    retries,
    delay,
    exponentialBackoff,
    maxDelay,
    respectRetryable,
  } = { ...DEFAULT_RETRY_CONFIG, ...config };

  let attempt = 0;
  let lastError: string = "Unknown error";
  let lastResponse: ServiceResponse<T> | null = null;

  while (attempt <= retries) {
    try {
      const result = await fn();

      // If successful, return immediately
      if (result.success) {
        return result;
      }

      // Store last response for error reporting
      lastResponse = result;
      lastError = result.error ?? "Unknown error";

      // Check if we should retry based on response
      if (respectRetryable && result.retryable === false) {
        // Not retryable - return immediately
        return result;
      }

      // If we've exhausted retries, return last response
      if (attempt >= retries) {
        return {
          ...result,
          error: `${lastError} (after ${attempt + 1} attempts)`,
        };
      }

      // Calculate delay and wait before retry
      const waitTime = calculateDelay(attempt, delay, exponentialBackoff, maxDelay);
      await sleep(waitTime);

      attempt++;
    } catch (error) {
      // Unexpected error during execution
      lastError = error instanceof Error ? error.message : "Unknown error occurred";

      if (attempt >= retries) {
        return {
          success: false,
          error: `${lastError} (after ${attempt + 1} attempts)`,
          retryable: false,
        };
      }

      const waitTime = calculateDelay(attempt, delay, exponentialBackoff, maxDelay);
      await sleep(waitTime);

      attempt++;
    }
  }

  // Fallback - should not reach here normally
  return {
    success: false,
    error: `All ${retries + 1} retries failed: ${lastError}`,
    retryable: false,
  };
}

/**
 * Execute multiple functions with retry, returning first success.
 * Useful for fallback chains (e.g., Proxycurl -> Apollo).
 *
 * @param fns - Array of async functions to try in order
 * @param config - Retry configuration for each function
 * @returns ServiceResponse from first successful call or last failure
 *
 * @example
 * ```typescript
 * const result = await withFallback([
 *   () => proxycurlService.getLinkedInProfile(url),
 *   () => apolloService.enrichPerson(company, slot, name),
 * ]);
 * ```
 */
export async function withFallback<T>(
  fns: Array<() => Promise<ServiceResponse<T>>>,
  config?: RetryConfig
): Promise<ServiceResponse<T>> {
  if (fns.length === 0) {
    return {
      success: false,
      error: "No functions provided for fallback",
      retryable: false,
    };
  }

  let lastResponse: ServiceResponse<T> | null = null;

  for (let i = 0; i < fns.length; i++) {
    const result = await withRetry(fns[i], config);

    if (result.success) {
      return result;
    }

    lastResponse = result;
  }

  // All fallbacks failed
  return {
    success: false,
    error: `All ${fns.length} fallback attempts failed: ${lastResponse?.error ?? "Unknown error"}`,
    retryable: false,
  };
}

/**
 * Create a retryable version of a service method.
 * Useful for wrapping service methods with default retry behavior.
 *
 * @param fn - Original async function
 * @param config - Default retry configuration
 * @returns Wrapped function with retry logic
 *
 * @example
 * ```typescript
 * const retryableGetProfile = makeRetryable(
 *   (url) => proxycurlService.getLinkedInProfile(url),
 *   { retries: 3 }
 * );
 *
 * const result = await retryableGetProfile(linkedinUrl);
 * ```
 */
export function makeRetryable<TArgs extends unknown[], TResult>(
  fn: (...args: TArgs) => Promise<ServiceResponse<TResult>>,
  config?: RetryConfig
): (...args: TArgs) => Promise<ServiceResponse<TResult>> {
  return (...args: TArgs) => withRetry(() => fn(...args), config);
}
