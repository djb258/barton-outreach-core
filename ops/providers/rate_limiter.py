"""
Rate Limiter - Barton Outreach Core
Global rate limiter with per-provider limits and circuit breaker.

Prevents:
- API rate limit violations
- Cost explosions from runaway loops
- Getting blocked by providers
- Race conditions with expensive Tier 3 calls

Usage:
    from rate_limiter import rate_limiter, get_rate_limiter_status

    # Before any API call
    rate_limiter.wait_if_needed("firecrawl")

    # After failure
    rate_limiter.record_failure("firecrawl")

    # After success
    rate_limiter.record_success("firecrawl")

    # Check status
    print(get_rate_limiter_status())

Barton Doctrine ID: 04.04.02.04.enrichment.rate_limiter
"""

import time
from collections import defaultdict, deque
from typing import Dict, Optional
import threading


class RateLimiter:
    """
    Global rate limiter with per-provider limits and circuit breaker.

    Features:
    - Global rate limit (max calls/second across all providers)
    - Per-provider rate limits (respects each API's limits)
    - Circuit breaker (stops calling failing providers)
    - Thread-safe (can be used in async contexts)
    """

    def __init__(self):
        self.global_limit = 5  # Max 5 calls/second globally
        self.global_calls = deque()

        # Per-provider limits (calls per second)
        # These are CONSERVATIVE estimates - actual limits may be higher
        self.provider_limits = {
            # ═══════════════════════════════════════════════════════════
            # TIER 0: FREE/NEAR-FREE (generous limits - these are cheap!)
            # ═══════════════════════════════════════════════════════════
            "google_cse": 10.0,     # 10 calls/second (within daily quota)
            "direct_scrape": 5.0,   # 5 calls/second (be nice to servers)

            # ═══════════════════════════════════════════════════════════
            # TIER 1: PAID ($0.20 per call)
            # ═══════════════════════════════════════════════════════════
            "serpapi": 1.0,         # 1 call/second (strict)
            "firecrawl": 0.083,     # 5 calls/minute = 0.083/second (their limit)
            "scraperapi": 2.0,      # 2 calls/second
            "zenrows": 2.0,         # 2 calls/second
            "scrapingbee": 2.0,     # 2 calls/second

            # ═══════════════════════════════════════════════════════════
            # TIER 2: MID-COST ($1.50 per call)
            # ═══════════════════════════════════════════════════════════
            "clearbit": 5.0,        # 5 calls/second (generous)
            "abacus": 2.0,          # 2 calls/second
            "clay": 1.0,            # 1 call/second (unknown, be safe)

            # ═══════════════════════════════════════════════════════════
            # TIER 3: EXPENSIVE ($3.00 per call)
            # ═══════════════════════════════════════════════════════════
            "peopledatalabs": 0.5,  # 1 call/2 seconds (strict)
            "pdl": 0.5,             # Alias for peopledatalabs
            "rocketreach": 0.5,     # 1 call/2 seconds (very strict)
            "apify": 0.5            # 1 call/2 seconds (actor startup time)
        }

        # Track calls per provider
        self.provider_calls: Dict[str, deque] = defaultdict(deque)

        # Track consecutive failures per provider
        self.provider_failures: Dict[str, int] = defaultdict(int)

        # Circuit breakers: provider -> timestamp when circuit can close
        self.circuit_breakers: Dict[str, float] = {}

        # Circuit breaker settings
        self.circuit_breaker_threshold = 5  # 5 consecutive failures opens circuit
        self.circuit_breaker_cooldown = 60.0  # 60 seconds cooldown

        # Thread safety
        self.lock = threading.Lock()

        # Stats
        self.total_calls = 0
        self.total_waits = 0
        self.total_wait_time = 0.0

    def wait_if_needed(self, provider: str) -> float:
        """
        Block until it's safe to make a call to this provider.
        Enforces both global and per-provider rate limits.

        Args:
            provider: Name of the API provider (lowercase)

        Returns:
            float: Time spent waiting (seconds)
        """
        provider = provider.lower()
        wait_start = time.time()
        total_waited = 0.0

        with self.lock:
            # Check circuit breaker first
            if provider in self.circuit_breakers:
                cooldown_until = self.circuit_breakers[provider]
                if time.time() < cooldown_until:
                    wait_time = cooldown_until - time.time()
                    print(f"  [CIRCUIT BREAKER] {provider} cooling down, waiting {wait_time:.1f}s")
                    # Release lock while waiting
                    self.lock.release()
                    time.sleep(wait_time)
                    self.lock.acquire()
                    total_waited += wait_time

                # Circuit breaker expired, reset
                if provider in self.circuit_breakers:
                    del self.circuit_breakers[provider]
                self.provider_failures[provider] = 0

            # Enforce global rate limit
            now = time.time()
            self._cleanup_old_calls(self.global_calls, now, 1.0)

            while len(self.global_calls) >= self.global_limit:
                self.lock.release()
                time.sleep(0.2)
                self.lock.acquire()
                now = time.time()
                self._cleanup_old_calls(self.global_calls, now, 1.0)
                total_waited += 0.2

            # Enforce per-provider rate limit
            provider_limit = self.provider_limits.get(provider, 1.0)
            min_interval = 1.0 / provider_limit  # Seconds between calls

            provider_queue = self.provider_calls[provider]
            self._cleanup_old_calls(provider_queue, now, 1.0)

            if provider_queue:
                time_since_last = now - provider_queue[-1]
                if time_since_last < min_interval:
                    wait_time = min_interval - time_since_last
                    self.lock.release()
                    time.sleep(wait_time)
                    self.lock.acquire()
                    now = time.time()
                    total_waited += wait_time

            # Record this call
            self.global_calls.append(now)
            self.provider_calls[provider].append(now)
            self.total_calls += 1

            if total_waited > 0:
                self.total_waits += 1
                self.total_wait_time += total_waited

        return total_waited

    def _cleanup_old_calls(self, queue: deque, now: float, window: float):
        """Remove calls older than window seconds"""
        while queue and (now - queue[0]) > window:
            queue.popleft()

    def record_failure(self, provider: str):
        """
        Record a failure. If threshold consecutive failures, open circuit breaker.

        Args:
            provider: Name of the provider that failed
        """
        provider = provider.lower()

        with self.lock:
            self.provider_failures[provider] += 1

            if self.provider_failures[provider] >= self.circuit_breaker_threshold:
                # Open circuit breaker
                cooldown_until = time.time() + self.circuit_breaker_cooldown
                self.circuit_breakers[provider] = cooldown_until
                print(f"  [CIRCUIT BREAKER OPEN] {provider} - {self.circuit_breaker_threshold} consecutive failures")
                print(f"     Will retry after {self.circuit_breaker_cooldown}s cooldown")

    def record_success(self, provider: str):
        """
        Record a success. Resets failure counter for provider.

        Args:
            provider: Name of the provider that succeeded
        """
        provider = provider.lower()

        with self.lock:
            self.provider_failures[provider] = 0
            # Close circuit breaker if open
            if provider in self.circuit_breakers:
                del self.circuit_breakers[provider]

    def is_circuit_open(self, provider: str) -> bool:
        """Check if circuit breaker is open for a provider"""
        provider = provider.lower()
        with self.lock:
            if provider in self.circuit_breakers:
                return time.time() < self.circuit_breakers[provider]
            return False

    def get_status(self) -> str:
        """Get human-readable status of rate limiter"""
        with self.lock:
            lines = []

            # Header
            lines.append("=" * 50)
            lines.append("RATE LIMITER STATUS")
            lines.append("=" * 50)

            # Stats
            lines.append(f"Total API calls: {self.total_calls}")
            lines.append(f"Times throttled: {self.total_waits}")
            if self.total_waits > 0:
                lines.append(f"Total wait time: {self.total_wait_time:.1f}s")

            # Circuit breakers
            if self.circuit_breakers:
                lines.append("")
                lines.append("CIRCUIT BREAKERS OPEN:")
                for provider, until in self.circuit_breakers.items():
                    remaining = until - time.time()
                    if remaining > 0:
                        lines.append(f"  {provider}: {remaining:.1f}s remaining")
                    else:
                        lines.append(f"  {provider}: ready to retry")

            # Failure counts
            failing = {p: c for p, c in self.provider_failures.items() if c > 0}
            if failing:
                lines.append("")
                lines.append("FAILURE COUNTS:")
                for provider, count in failing.items():
                    lines.append(f"  {provider}: {count}/{self.circuit_breaker_threshold}")

            # All clear
            if not self.circuit_breakers and not failing:
                lines.append("")
                lines.append("All systems nominal")

            lines.append("=" * 50)

            return "\n".join(lines)

    def reset(self):
        """Reset all state (for testing)"""
        with self.lock:
            self.global_calls.clear()
            self.provider_calls.clear()
            self.provider_failures.clear()
            self.circuit_breakers.clear()
            self.total_calls = 0
            self.total_waits = 0
            self.total_wait_time = 0.0


# Singleton instance
rate_limiter = RateLimiter()


def get_rate_limiter_status() -> str:
    """Get human-readable status of the global rate limiter"""
    return rate_limiter.get_status()


# ============================================================================
# CLI Testing
# ============================================================================

if __name__ == "__main__":
    print("Testing rate limiter...")
    print()

    # Test 1: Global rate limiting
    print("Test 1: Global rate limiting (5 calls/sec)")
    print("-" * 40)
    start = time.time()
    for i in range(10):
        waited = rate_limiter.wait_if_needed("test_provider")
        elapsed = time.time() - start
        print(f"  Call {i+1}: elapsed={elapsed:.2f}s, waited={waited:.2f}s")

    print()

    # Test 2: Per-provider rate limiting
    print("Test 2: Per-provider rate limiting (serpapi: 1 call/sec)")
    print("-" * 40)
    rate_limiter.reset()
    start = time.time()
    for i in range(5):
        waited = rate_limiter.wait_if_needed("serpapi")
        elapsed = time.time() - start
        print(f"  Call {i+1}: elapsed={elapsed:.2f}s, waited={waited:.2f}s")

    print()

    # Test 3: Circuit breaker
    print("Test 3: Circuit breaker (5 failures)")
    print("-" * 40)
    rate_limiter.reset()
    for i in range(6):
        rate_limiter.record_failure("bad_provider")
        print(f"  Failure {i+1}: circuit_open={rate_limiter.is_circuit_open('bad_provider')}")

    print()

    # Test 4: Status display
    print("Test 4: Status display")
    print("-" * 40)
    print(rate_limiter.get_status())
