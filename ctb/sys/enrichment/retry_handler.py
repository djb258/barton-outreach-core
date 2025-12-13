"""
Retry Handler - Barton Outreach Core
Exponential backoff retry logic for API calls.

Prevents:
- Transient failures from killing enrichment
- Hammering APIs during outages
- Losing data due to temporary network issues

Usage:
    from retry_handler import retry_with_backoff

    def call_api():
        return requests.get("https://api.example.com/data")

    result = retry_with_backoff(
        func=call_api,
        provider="example",
        max_retries=3,
        base_delay=2.0
    )

Barton Doctrine ID: 04.04.02.04.enrichment.retry_handler
"""

import time
import random
from typing import Callable, Optional, Any, TypeVar, List
from functools import wraps

T = TypeVar('T')


class RetryExhausted(Exception):
    """Raised when all retry attempts have been exhausted"""

    def __init__(self, provider: str, attempts: int, errors: List[str]):
        self.provider = provider
        self.attempts = attempts
        self.errors = errors
        super().__init__(f"{provider}: Failed after {attempts} attempts. Errors: {errors}")


def retry_with_backoff(
    func: Callable[[], T],
    provider: str,
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[int, Exception, float], None]] = None
) -> Optional[T]:
    """
    Execute function with exponential backoff on failures.

    Args:
        func: Function to execute (should take no arguments)
        provider: Provider name for logging
        max_retries: Maximum retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 2.0)
        max_delay: Maximum delay between retries (default: 30.0)
        jitter: Add randomness to delay to prevent thundering herd (default: True)
        retryable_exceptions: Tuple of exceptions that trigger retry
        on_retry: Optional callback(attempt, exception, delay) called before each retry

    Returns:
        Function result or None if all retries failed

    Delay Formula:
        delay = min(base_delay * (2 ** attempt), max_delay)
        if jitter: delay *= random.uniform(0.5, 1.5)

    Example delays with base_delay=2.0:
        Attempt 1 fail: wait ~2s
        Attempt 2 fail: wait ~4s
        Attempt 3 fail: wait ~8s (then give up)
    """
    errors = []

    for attempt in range(max_retries):
        try:
            result = func()
            return result

        except retryable_exceptions as e:
            error_msg = str(e)
            errors.append(f"Attempt {attempt + 1}: {error_msg}")

            if attempt < max_retries - 1:
                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** attempt), max_delay)

                # Add jitter to prevent thundering herd
                if jitter:
                    delay *= random.uniform(0.5, 1.5)

                # Log retry
                print(f"  [RETRY] {provider} attempt {attempt + 1}/{max_retries} failed: {error_msg[:100]}")
                print(f"          Retrying in {delay:.1f}s...")

                # Call retry callback if provided
                if on_retry:
                    on_retry(attempt, e, delay)

                time.sleep(delay)
            else:
                # Final attempt failed
                print(f"  [FAILED] {provider} exhausted {max_retries} attempts")
                for i, err in enumerate(errors):
                    print(f"           {err[:80]}")

    return None


def retry_with_backoff_raise(
    func: Callable[[], T],
    provider: str,
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,)
) -> T:
    """
    Same as retry_with_backoff but raises RetryExhausted instead of returning None.

    Use this when you need to distinguish between "returned None" and "all retries failed".
    """
    errors = []

    for attempt in range(max_retries):
        try:
            result = func()
            return result

        except retryable_exceptions as e:
            error_msg = str(e)
            errors.append(f"Attempt {attempt + 1}: {error_msg}")

            if attempt < max_retries - 1:
                delay = min(base_delay * (2 ** attempt), max_delay)
                if jitter:
                    delay *= random.uniform(0.5, 1.5)

                print(f"  [RETRY] {provider} attempt {attempt + 1}/{max_retries} failed")
                print(f"          Retrying in {delay:.1f}s...")

                time.sleep(delay)
            else:
                raise RetryExhausted(provider, max_retries, errors)

    raise RetryExhausted(provider, max_retries, errors)


def retryable(
    max_retries: int = 3,
    base_delay: float = 2.0,
    provider: Optional[str] = None
):
    """
    Decorator version of retry_with_backoff.

    Usage:
        @retryable(max_retries=3, base_delay=2.0, provider="serpapi")
        def call_serpapi(query):
            return requests.get(f"https://serpapi.com/search?q={query}")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            provider_name = provider or func.__name__

            def call():
                return func(*args, **kwargs)

            return retry_with_backoff(
                func=call,
                provider=provider_name,
                max_retries=max_retries,
                base_delay=base_delay
            )

        return wrapper
    return decorator


# ============================================================================
# Specific Exception Categories
# ============================================================================

# Exceptions that should trigger a retry
RETRYABLE_ERRORS = (
    ConnectionError,
    TimeoutError,
    # Add requests exceptions if available
)

try:
    import requests
    RETRYABLE_ERRORS = RETRYABLE_ERRORS + (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
    )
except ImportError:
    pass


# Exceptions that should NOT trigger a retry (immediate failure)
NON_RETRYABLE_ERRORS = (
    ValueError,
    TypeError,
    KeyError,
    # Authentication errors should not retry
)


def is_retryable_http_status(status_code: int) -> bool:
    """
    Check if an HTTP status code should trigger a retry.

    Retryable:
        429 - Too Many Requests (rate limited)
        500 - Internal Server Error
        502 - Bad Gateway
        503 - Service Unavailable
        504 - Gateway Timeout

    Not Retryable:
        400 - Bad Request (our fault)
        401 - Unauthorized (auth issue)
        403 - Forbidden (permission issue)
        404 - Not Found (won't change)
    """
    return status_code in (429, 500, 502, 503, 504)


# ============================================================================
# CLI Testing
# ============================================================================

if __name__ == "__main__":
    print("Testing retry handler...")
    print()

    # Test 1: Successful call (no retries needed)
    print("Test 1: Successful call")
    print("-" * 40)

    call_count = 0

    def success_func():
        global call_count
        call_count += 1
        return f"Success on call {call_count}"

    result = retry_with_backoff(success_func, "test", max_retries=3)
    print(f"Result: {result}")
    print()

    # Test 2: Failing call (retries then succeeds)
    print("Test 2: Fail twice, succeed on third")
    print("-" * 40)

    call_count = 0

    def flaky_func():
        global call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError(f"Simulated failure {call_count}")
        return f"Success on call {call_count}"

    result = retry_with_backoff(flaky_func, "flaky_api", max_retries=3, base_delay=0.5)
    print(f"Result: {result}")
    print()

    # Test 3: All retries exhausted
    print("Test 3: All retries exhausted")
    print("-" * 40)

    def always_fail():
        raise TimeoutError("Always fails")

    result = retry_with_backoff(always_fail, "bad_api", max_retries=3, base_delay=0.5)
    print(f"Result: {result}")
    print()

    # Test 4: Decorator usage
    print("Test 4: Decorator usage")
    print("-" * 40)

    @retryable(max_retries=2, base_delay=0.5, provider="decorated_api")
    def decorated_func(x):
        if x < 2:
            raise ValueError(f"x={x} is too small")
        return x * 2

    result = decorated_func(5)
    print(f"Result: {result}")
