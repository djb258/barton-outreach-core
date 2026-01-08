# Blog Worker Contract (READ-ONLY SPECIFICATION)

**Version:** 1.1.0 (Canary-Aware)
**Status:** LOCKED
**Date:** 2026-01-08
**Author:** Claude Code (IMO-Creator)

---

## Purpose

This document defines the contract for the Blog Worker. It is **READ-ONLY** — the worker must implement these guards exactly as specified.

---

## Canary Rollout Strategy

```
PHASE 1: Global enabled = FALSE, Canary enabled = TRUE
         → Only process outreach_ids in blog_canary_allowlist
         → Run twice back-to-back, verify second run = 0 fetches

PHASE 2: Monitor 24 hours
         → Watch: blog_source_history growth
         → Watch: blog_errors rate
         → Watch: duplicate rows (must be 0)

PHASE 3: If clean, promote to global
         → SELECT outreach.promote_canary_to_global('operator_name');
```

---

## Worker Guard Pseudocode

```python
"""
Blog Worker — Production Guard Contract

This is the REQUIRED guard logic for the blog worker.
Implementing code MUST follow this pattern exactly.
"""

import hashlib
from datetime import datetime
from typing import Optional, Tuple
from dataclasses import dataclass

@dataclass
class BlogIngressConfig:
    enabled: bool
    max_urls_per_hour: int
    max_urls_per_company: int
    url_ttl_days: int
    content_ttl_days: int


class BlogWorker:
    """
    Blog Worker with Production Guards.

    DOCTRINE:
    - No people data
    - No scoring
    - No execution
    - No retries without history check
    - Company-level ONLY
    """

    def __init__(self, db_connection):
        self.db = db_connection
        self.urls_fetched_this_hour = 0
        self.company_url_counts = {}

    # =========================================================================
    # GUARD 1: Check Ingress Control (CANARY-AWARE)
    # =========================================================================

    def check_should_process(self, outreach_id: str) -> Tuple[bool, str, str]:
        """
        GUARD 1: Canary-aware ingress check.

        MUST be called for EACH outreach_id before processing.
        Returns (should_process, mode, reason).

        Modes:
        - GLOBAL: Global ingress enabled, process all
        - CANARY: Canary mode, only allowlist processed
        - DISABLED: Nothing enabled, halt
        """
        result = self.db.execute("""
            SELECT * FROM outreach.blog_should_process(%s)
        """, (outreach_id,)).fetchone()

        return result.should_process, result.mode, result.reason

    def get_ingress_config(self) -> Optional[BlogIngressConfig]:
        """
        Get ingress configuration (rate limits, TTLs).
        """
        result = self.db.execute("""
            SELECT * FROM outreach.get_blog_ingress_config()
        """).fetchone()

        if not result:
            return None

        return BlogIngressConfig(
            enabled=result.enabled,
            max_urls_per_hour=result.max_urls_per_hour,
            max_urls_per_company=result.max_urls_per_company,
            url_ttl_days=result.url_ttl_days,
            content_ttl_days=result.content_ttl_days
        )

    # =========================================================================
    # GUARD 2: Check History Before Fetch
    # =========================================================================

    def should_fetch_url(self, outreach_id: str, source_url: str) -> Tuple[bool, str]:
        """
        GUARD 2: Check history before making any HTTP request.

        MUST be called BEFORE fetching any URL.
        Prevents duplicate work and cost.
        """
        result = self.db.execute("""
            SELECT * FROM outreach.should_fetch_blog_url(%s, %s)
        """, (outreach_id, source_url)).fetchone()

        return result.should_fetch, result.reason

    # =========================================================================
    # GUARD 3: Rate Limiting
    # =========================================================================

    def check_rate_limits(self, outreach_id: str, config: BlogIngressConfig) -> bool:
        """
        GUARD 3: Check rate limits before fetch.

        Prevents runaway costs and API abuse.
        """
        # Global rate limit
        if self.urls_fetched_this_hour >= config.max_urls_per_hour:
            return False

        # Per-company rate limit
        company_count = self.company_url_counts.get(outreach_id, 0)
        if company_count >= config.max_urls_per_company:
            return False

        return True

    # =========================================================================
    # GUARD 4: Source Type Validation (No Social)
    # =========================================================================

    def validate_source_type(self, source_type: str) -> bool:
        """
        GUARD 4: Validate source type against doctrine.

        DISALLOW_SOCIAL_METRICS = TRUE
        """
        FORBIDDEN_TYPES = {'social'}
        ALLOWED_TYPES = {'website', 'blog', 'press', 'news', 'filing', 'careers'}

        if source_type in FORBIDDEN_TYPES:
            raise ValueError(f"DOCTRINE VIOLATION: source_type '{source_type}' is forbidden")

        if source_type not in ALLOWED_TYPES:
            raise ValueError(f"Invalid source_type: {source_type}")

        return True

    # =========================================================================
    # MAIN WORKER LOOP (Canary-Aware)
    # =========================================================================

    def run(self):
        """
        Main worker loop with canary-aware production guards.
        """
        # Get config (for rate limits)
        config = self.get_ingress_config()
        if not config:
            print("HALT: No ingress config found")
            return

        # Track fetches for this run (for idempotency check)
        fetches_this_run = 0

        # Get work queue (canary-aware view)
        queue = self.db.execute("""
            SELECT * FROM outreach.v_blog_ingestion_queue
        """).fetchall()

        if not queue:
            print("QUEUE_EMPTY: No work to do (check canary_enabled or global enabled)")
            return

        for item in queue:
            outreach_id = item.outreach_id
            domain = item.domain

            # GUARD 1: Canary-aware check (per outreach_id)
            should_process, mode, reason = self.check_should_process(outreach_id)
            if not should_process:
                print(f"SKIP: {outreach_id} ({mode}: {reason})")
                continue

            print(f"PROCESSING: {outreach_id} (mode={mode})")

            # Construct blog URL (example)
            source_url = f"https://{domain}/blog"

            # GUARD 2: Check history
            should_fetch, reason = self.should_fetch_url(outreach_id, source_url)
            if not should_fetch:
                print(f"  HISTORY_HIT: {source_url} ({reason})")
                continue  # This is expected on second run!

            # GUARD 3: Check rate limits
            if not self.check_rate_limits(outreach_id, config):
                print(f"RATE_LIMIT: Stopping worker")
                break

            # GUARD 4: Validate source type
            source_type = 'blog'
            self.validate_source_type(source_type)

            try:
                # FETCH URL (actual HTTP call)
                content, http_status = self.fetch_url(source_url)

                # SUCCESS: Write to blog + history
                self.write_blog_record(outreach_id, source_type, source_url, content)
                self.write_history_record(outreach_id, source_type, source_url, 'active', http_status, content)

                # Update counters
                self.urls_fetched_this_hour += 1
                self.company_url_counts[outreach_id] = self.company_url_counts.get(outreach_id, 0) + 1
                fetches_this_run += 1

                # Record canary run (for idempotency tracking)
                if mode == 'CANARY':
                    self.db.execute("""
                        SELECT outreach.record_canary_run(%s, %s)
                    """, (outreach_id, 1))

            except Exception as e:
                # FAILURE: Write to blog_errors + history
                self.write_error_record(outreach_id, source_url, str(e))
                self.write_history_record(outreach_id, source_type, source_url, 'dead', None, None)

        # End of run summary
        print(f"RUN_COMPLETE: {fetches_this_run} fetches this run")
        if fetches_this_run == 0:
            print("IDEMPOTENT: Second run produced zero fetches (expected)")
        else:
            print(f"NEW_FETCHES: {fetches_this_run} new URLs fetched")

    # =========================================================================
    # WRITE FUNCTIONS (Blog or Errors ONLY)
    # =========================================================================

    def write_blog_record(self, outreach_id: str, source_type: str, source_url: str, content: str):
        """
        Write to outreach.blog table.

        ONLY writes to blog table. No other tables.
        """
        checksum = hashlib.sha256(content.encode()).hexdigest() if content else None

        self.db.execute("""
            INSERT INTO outreach.blog (outreach_id, source_type_enum, source_url, context_summary, context_timestamp)
            VALUES (%s, %s::outreach.blog_source_type, %s, %s, NOW())
            ON CONFLICT (outreach_id, source_url) DO UPDATE SET
                context_summary = EXCLUDED.context_summary,
                context_timestamp = NOW()
        """, (outreach_id, source_type, source_url, content[:1000] if content else None))

    def write_history_record(self, outreach_id: str, source_type: str, source_url: str,
                             status: str, http_status: Optional[int], content: Optional[str]):
        """
        Write to outreach.blog_source_history table.

        APPEND-ONLY pattern: Only update last_checked_at, status, http_status, checksum.
        """
        checksum = hashlib.sha256(content.encode()).hexdigest() if content else None

        self.db.execute("""
            INSERT INTO outreach.blog_source_history
                (outreach_id, source_type, source_url, status, http_status, checksum, last_checked_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (outreach_id, source_url) DO UPDATE SET
                last_checked_at = NOW(),
                status = EXCLUDED.status,
                http_status = EXCLUDED.http_status,
                checksum = EXCLUDED.checksum
        """, (outreach_id, source_type, source_url, status, http_status, checksum))

    def write_error_record(self, outreach_id: str, source_url: str, error_message: str):
        """
        Write to outreach.blog_errors table.

        Per Error Persistence Doctrine: failures are work items.
        """
        self.db.execute("""
            INSERT INTO outreach.blog_errors
                (outreach_id, pipeline_stage, failure_code, blocking_reason, raw_input)
            VALUES (%s, 'FETCH', 'BLOG_FETCH_ERROR', %s, %s)
        """, (outreach_id, error_message, {'source_url': source_url}))

    def fetch_url(self, url: str) -> Tuple[str, int]:
        """
        Placeholder for actual HTTP fetch.
        Implement with appropriate timeout, retries, user-agent.
        """
        # Implementation here
        pass
```

---

## Guard Summary

| Guard | Check | Action on Fail |
|-------|-------|----------------|
| **GUARD 1** | `blog_ingress_enabled()` | HALT worker immediately |
| **GUARD 2** | `should_fetch_blog_url()` | SKIP this URL |
| **GUARD 3** | Rate limits | STOP worker or SKIP company |
| **GUARD 4** | Source type validation | RAISE exception |

---

## Write Targets (ONLY These)

| Target | When |
|--------|------|
| `outreach.blog` | Successful fetch |
| `outreach.blog_source_history` | Every fetch (success or fail) |
| `outreach.blog_errors` | Failed fetch |

---

## Forbidden Operations

| Operation | Reason |
|-----------|--------|
| Write to people tables | Blog is company-level only |
| Write to BIT/scoring | Blog does not score |
| Write to execution tables | Blog does not execute |
| Fetch without history check | Causes duplicate work/cost |
| Fetch with social source_type | Doctrine violation |

---

## Canary Rollout Commands

### Step 1: Enable Canary Mode

```sql
-- Enable canary mode (global stays OFF)
UPDATE outreach.blog_ingress_control
SET canary_enabled = TRUE,
    canary_started_at = NOW(),
    canary_notes = 'Starting canary with 25 outreach_ids';
```

### Step 2: Run Worker Twice

```bash
# First run - should fetch URLs
python blog_worker.py

# Second run - should have 0 fetches (history hits only)
python blog_worker.py
```

### Step 3: Check Idempotency

```sql
-- All second_run_fetches should be 0
SELECT * FROM outreach.check_canary_idempotency();
```

### Step 4: Monitor for 24 Hours

```sql
-- Check health metrics
SELECT * FROM outreach.get_canary_health();

-- Expected:
-- duplicate_urls = 0 (CRITICAL)
-- errors_24h = low/reasonable
-- history_records_24h = growing
```

### Step 5: Promote to Global (If Clean)

```sql
-- ONE COMMAND to promote canary to global
SELECT outreach.promote_canary_to_global('your_operator_name');

-- This will:
-- 1. Check for failures (blocks if any)
-- 2. Check idempotency (blocks if second_run > 0)
-- 3. Check duplicates (blocks if any)
-- 4. If all pass: flip enabled=TRUE, mark canary as promoted
```

---

## Emergency Stop

```sql
-- Disable everything immediately
UPDATE outreach.blog_ingress_control
SET enabled = FALSE,
    canary_enabled = FALSE,
    disabled_at = NOW(),
    disabled_by = 'operator',
    notes = 'Emergency stop';
```

---

**Document Status:** LOCKED
**Last Updated:** 2026-01-08
**Version:** 1.1.0 (Canary-Aware)
**Owner:** Blog Content Sub-Hub
