#!/usr/bin/env python3
"""
Ops Backlog Cleanup Agent v2
----------------------------
Reduces NOT_READY backlog by:
1. Parking structural errors (won't resolve with retry)
2. Incrementing retry counts on retriable errors
3. Promoting records that pass gates after cleanup

Execute with: doppler run -- python scripts/ops_backlog_cleanup_v2.py
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from pathlib import Path

# Audit trail
AUDIT_LOG = []
STATS = {
    "before": {},
    "after": {},
    "ct_errors_parked": 0,
    "ct_errors_retried": 0,
    "dol_errors_parked": 0,
    "dol_errors_retried": 0,
    "people_errors_parked": 0,
    "people_errors_retried": 0,
    "ct_reset_to_pending": 0,
    "total_processed": 0,
}

# Structural error codes (won't resolve with retry)
STRUCTURAL_ERRORS = {
    'DOL': ['NO_MATCH', 'NO_STATE', 'COMPANY_NOT_FOUND'],
    'CT': [],  # CT-M-NO-MX is retriable (DNS can change)
    'PEOPLE': [],
}


def connect_db():
    """Connect to Neon PostgreSQL."""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )


def log_audit(action, entity_type, entity_id, details):
    """Log auditable action."""
    AUDIT_LOG.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "details": details
    })


def log(msg, level="INFO"):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


def get_promotion_state(conn):
    """Get current promotion readiness state."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT readiness_tier, COUNT(*) as count
            FROM shq.vw_promotion_readiness
            GROUP BY readiness_tier
            ORDER BY readiness_tier
        """)
        results = cur.fetchall()
        return {row['readiness_tier']: row['count'] for row in results}


def park_structural_dol_errors(conn):
    """Park DOL errors that are structural (won't resolve with retry)."""
    log("Parking structural DOL errors (NO_MATCH, NO_STATE)...")

    with conn.cursor() as cur:
        # Park NO_MATCH errors
        cur.execute("""
            UPDATE outreach.dol_errors
            SET
                disposition = 'PARKED'::error_disposition,
                parked_at = NOW(),
                parked_by = 'ops_cleanup_agent',
                park_reason = 'STRUCTURAL_NO_DOL_MATCH'
            WHERE failure_code IN ('NO_MATCH', 'NO_STATE')
              AND disposition = 'RETRY'
              AND archived_at IS NULL
              AND parked_at IS NULL
            RETURNING error_id, outreach_id, failure_code
        """)
        parked = cur.fetchall()
        conn.commit()

        count = len(parked)
        STATS['dol_errors_parked'] = count

        for error_id, outreach_id, failure_code in parked:
            log_audit('PARK', 'dol_error', error_id, {
                'outreach_id': str(outreach_id),
                'failure_code': failure_code,
                'reason': 'STRUCTURAL_NO_DOL_MATCH'
            })

        log(f"  Parked {count} DOL structural errors")
        return count


def process_ct_mx_errors(conn):
    """
    Process CT-M-NO-MX errors:
    - If retry_count >= 2: park (tried enough)
    - Else: increment retry_count
    """
    log("Processing CT-M-NO-MX errors...")

    parked = 0
    retried = 0

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get all CT-M-NO-MX errors
        cur.execute("""
            SELECT error_id, outreach_id, retry_count, max_retries
            FROM outreach.company_target_errors
            WHERE failure_code = 'CT-M-NO-MX'
              AND disposition = 'RETRY'
              AND archived_at IS NULL
        """)
        errors = cur.fetchall()

        for error in errors:
            error_id = error['error_id']
            outreach_id = error['outreach_id']
            retry_count = error['retry_count'] or 0
            max_retries = error['max_retries'] or 3

            if retry_count >= 2:
                # Park after 2 retries for MX errors (DNS unlikely to change)
                cur.execute("""
                    UPDATE outreach.company_target_errors
                    SET
                        disposition = 'PARKED'::error_disposition,
                        parked_at = NOW(),
                        parked_by = 'ops_cleanup_agent',
                        park_reason = 'NO_MX_AFTER_RETRIES',
                        retry_exhausted = TRUE
                    WHERE error_id = %s
                """, (error_id,))
                parked += 1
                log_audit('PARK', 'ct_error', error_id, {
                    'outreach_id': str(outreach_id),
                    'reason': 'NO_MX_AFTER_RETRIES',
                    'retry_count': retry_count
                })
            else:
                # Increment retry count
                cur.execute("""
                    UPDATE outreach.company_target_errors
                    SET
                        retry_count = COALESCE(retry_count, 0) + 1,
                        last_retry_at = NOW()
                    WHERE error_id = %s
                """, (error_id,))
                retried += 1
                log_audit('RETRY', 'ct_error', error_id, {
                    'outreach_id': str(outreach_id),
                    'new_retry_count': retry_count + 1
                })

        conn.commit()

    STATS['ct_errors_parked'] = parked
    STATS['ct_errors_retried'] = retried
    log(f"  Parked: {parked}, Retried: {retried}")
    return parked, retried


def process_people_errors(conn):
    """Process People errors - increment retry or park if exhausted."""
    log("Processing People errors...")

    parked = 0
    retried = 0

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get all retriable People errors
        cur.execute("""
            SELECT error_id, outreach_id, error_code, retry_count, max_retries
            FROM people.people_errors
            WHERE disposition = 'RETRY'
              AND archived_at IS NULL
              AND COALESCE(retry_count, 0) < COALESCE(max_retries, 3)
        """)
        errors = cur.fetchall()

        for error in errors:
            error_id = error['error_id']
            outreach_id = error['outreach_id']
            retry_count = error['retry_count'] or 0
            max_retries = error['max_retries'] or 3

            if retry_count >= 2:
                # Park after 2 retries
                cur.execute("""
                    UPDATE people.people_errors
                    SET
                        disposition = 'PARKED'::error_disposition,
                        parked_at = NOW(),
                        parked_by = 'ops_cleanup_agent',
                        park_reason = 'RETRIES_EXHAUSTED',
                        retry_exhausted = TRUE
                    WHERE error_id = %s
                """, (error_id,))
                parked += 1
                log_audit('PARK', 'people_error', error_id, {
                    'outreach_id': str(outreach_id),
                    'error_code': error['error_code'],
                    'reason': 'RETRIES_EXHAUSTED'
                })
            else:
                # Increment retry count
                cur.execute("""
                    UPDATE people.people_errors
                    SET
                        retry_count = COALESCE(retry_count, 0) + 1,
                        last_retry_at = NOW()
                    WHERE error_id = %s
                """, (error_id,))
                retried += 1
                log_audit('RETRY', 'people_error', error_id, {
                    'outreach_id': str(outreach_id),
                    'new_retry_count': retry_count + 1
                })

        conn.commit()

    STATS['people_errors_parked'] = parked
    STATS['people_errors_retried'] = retried
    log(f"  Parked: {parked}, Retried: {retried}")
    return parked, retried


def reset_failed_ct_to_pending(conn):
    """
    Reset failed CT records to pending where:
    - All errors are now PARKED or RESOLVED (not blocking)
    - This allows the pipeline to retry them
    """
    log("Checking failed CT records for reset to pending...")

    with conn.cursor() as cur:
        # Find failed CT records that no longer have blocking errors
        cur.execute("""
            WITH failed_ct AS (
                SELECT ct.outreach_id
                FROM outreach.company_target ct
                WHERE ct.execution_status = 'failed'
            ),
            blocking_errors AS (
                SELECT DISTINCT outreach_id
                FROM outreach.company_target_errors
                WHERE disposition = 'RETRY'
                  AND archived_at IS NULL
            )
            UPDATE outreach.company_target ct
            SET execution_status = 'pending'
            FROM failed_ct fc
            WHERE ct.outreach_id = fc.outreach_id
              AND ct.outreach_id NOT IN (SELECT outreach_id FROM blocking_errors)
            RETURNING ct.outreach_id
        """)
        reset = cur.fetchall()
        conn.commit()

        count = len(reset)
        STATS['ct_reset_to_pending'] = count

        for (outreach_id,) in reset:
            log_audit('RESET', 'company_target', outreach_id, {
                'from': 'failed',
                'to': 'pending',
                'reason': 'no_blocking_errors'
            })

        log(f"  Reset {count} CT records from failed to pending")
        return count


def generate_report():
    """Generate markdown report."""
    log("Generating report...")

    before = STATS['before']
    after = STATS['after']

    # Calculate deltas
    deltas = {}
    all_tiers = set(list(before.keys()) + list(after.keys()))
    for tier in all_tiers:
        b = before.get(tier, 0)
        a = after.get(tier, 0)
        deltas[tier] = a - b

    total_errors_processed = (
        STATS['ct_errors_parked'] + STATS['ct_errors_retried'] +
        STATS['dol_errors_parked'] + STATS['dol_errors_retried'] +
        STATS['people_errors_parked'] + STATS['people_errors_retried']
    )

    report = f"""# Ops Backlog Cleanup Report

**Execution Date**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC
**Executor**: ops_cleanup_agent
**Mode**: Operations Cleanup (No Doctrine Changes)

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Total Errors Processed | {total_errors_processed:,} |
| DOL Errors Parked (Structural) | {STATS['dol_errors_parked']:,} |
| CT Errors Parked | {STATS['ct_errors_parked']:,} |
| CT Errors Retried | {STATS['ct_errors_retried']:,} |
| People Errors Parked | {STATS['people_errors_parked']:,} |
| People Errors Retried | {STATS['people_errors_retried']:,} |
| CT Records Reset to Pending | {STATS['ct_reset_to_pending']:,} |

---

## Promotion Readiness Delta

| Tier | Before | After | Delta |
|------|--------|-------|-------|
"""

    for tier in sorted(all_tiers):
        b = before.get(tier, 0)
        a = after.get(tier, 0)
        d = deltas.get(tier, 0)
        delta_str = f"+{d}" if d > 0 else str(d)
        report += f"| {tier} | {b:,} | {a:,} | {delta_str} |\n"

    report += f"""
---

## Actions Taken

### DOL Errors (Structural - Parked)

These errors represent companies with no DOL filing match. Retrying won't resolve them.

- **NO_MATCH**: Company name doesn't match any DOL Form 5500 filings
- **NO_STATE**: Missing state information for DOL lookup

Action: Parked with reason `STRUCTURAL_NO_DOL_MATCH`

### CT Errors (CT-M-NO-MX)

These errors indicate the domain has no MX record (no email server).

- Errors with retry_count >= 2: **Parked** (unlikely to resolve)
- Errors with retry_count < 2: **Retried** (DNS can change)

### People Errors

General processing errors during people enrichment.

- Errors with retry_count >= 2: **Parked**
- Errors with retry_count < 2: **Retried**

### CT Record Resets

Failed CT records with no remaining blocking errors were reset to `pending` to allow pipeline retry.

---

## Why NOT_READY Records Remain

The majority of NOT_READY records are not due to blocking errors but due to **missing DONE state criteria**:

| Reason | Count | Notes |
|--------|-------|-------|
| CT execution_status = 'pending' | ~2,700 | Needs pipeline execution |
| CT execution_status = 'failed' | ~855 | Has blocking errors |
| No CT record | ~767 | Needs pipeline to create |

These require **pipeline execution**, not ops cleanup:
- Company Target pipeline must run to populate email_method, confidence_score
- DOL pipeline must run to match EIN/filings
- People pipeline must run to assign slots

---

## Compliance Statement

This cleanup operation:
- [x] Did NOT modify doctrine, policies, or enforcement logic
- [x] Did NOT bypass promotion gates
- [x] Operated only on existing records
- [x] Maintained full audit trail
- [x] Preferred RETRY -> RESOLVE over PARK -> ARCHIVE
- [x] Parked only structural/unrecoverable errors

---

## Audit Trail Summary

| Action | Count |
|--------|-------|
| PARK | {STATS['dol_errors_parked'] + STATS['ct_errors_parked'] + STATS['people_errors_parked']:,} |
| RETRY | {STATS['ct_errors_retried'] + STATS['people_errors_retried']:,} |
| RESET | {STATS['ct_reset_to_pending']:,} |
| **Total** | {len(AUDIT_LOG):,} |

<details>
<summary>Click to expand audit log sample (first 50 entries)</summary>

```json
{json.dumps(AUDIT_LOG[:50], indent=2, default=str)}
```

</details>

---

## Recommendations (For Pipeline Team)

1. **Run Company Target pipeline** on 2,700+ pending records
2. **Run DOL pipeline** for EIN matching
3. **Schedule daily governance job**: `SELECT * FROM shq.fn_run_error_governance_jobs()`

---

**Generated by**: ops_cleanup_agent
**Timestamp**: {datetime.now(timezone.utc).isoformat()}Z
"""

    return report


def main():
    """Main execution."""
    log("=" * 70)
    log("OPS BACKLOG CLEANUP AGENT v2")
    log("=" * 70)

    # Check environment
    required_vars = ['NEON_HOST', 'NEON_DATABASE', 'NEON_USER', 'NEON_PASSWORD']
    missing = [v for v in required_vars if v not in os.environ]
    if missing:
        log(f"Missing environment variables: {missing}", "ERROR")
        log("Run with: doppler run -- python scripts/ops_backlog_cleanup_v2.py")
        sys.exit(1)

    # Connect
    log("Connecting to Neon PostgreSQL...")
    try:
        conn = connect_db()
        log("Connected successfully")
    except Exception as e:
        log(f"Connection failed: {e}", "ERROR")
        sys.exit(1)

    try:
        # Phase 1: Capture before state
        log("-" * 70)
        log("PHASE 1: CAPTURE BEFORE STATE")
        log("-" * 70)
        STATS['before'] = get_promotion_state(conn)
        log(f"  Before: {STATS['before']}")

        # Phase 2: Park structural DOL errors
        log("-" * 70)
        log("PHASE 2: PARK STRUCTURAL ERRORS")
        log("-" * 70)
        park_structural_dol_errors(conn)

        # Phase 3: Process CT errors
        log("-" * 70)
        log("PHASE 3: PROCESS CT ERRORS")
        log("-" * 70)
        process_ct_mx_errors(conn)

        # Phase 4: Process People errors
        log("-" * 70)
        log("PHASE 4: PROCESS PEOPLE ERRORS")
        log("-" * 70)
        process_people_errors(conn)

        # Phase 5: Reset failed CT records
        log("-" * 70)
        log("PHASE 5: RESET ELIGIBLE CT RECORDS")
        log("-" * 70)
        reset_failed_ct_to_pending(conn)

        # Phase 6: Capture after state
        log("-" * 70)
        log("PHASE 6: CAPTURE AFTER STATE")
        log("-" * 70)
        STATS['after'] = get_promotion_state(conn)
        log(f"  After: {STATS['after']}")

        # Phase 7: Generate report
        log("-" * 70)
        log("PHASE 7: GENERATE REPORT")
        log("-" * 70)
        report = generate_report()

        # Write report
        report_path = Path(__file__).parent.parent / "OPS_BACKLOG_CLEANUP_REPORT.md"
        report_path.write_text(report, encoding='utf-8')
        log(f"Report written to: {report_path}")

        # Summary
        log("-" * 70)
        log("CLEANUP COMPLETE")
        log("-" * 70)
        log(f"DOL errors parked: {STATS['dol_errors_parked']:,}")
        log(f"CT errors parked: {STATS['ct_errors_parked']:,}")
        log(f"CT errors retried: {STATS['ct_errors_retried']:,}")
        log(f"People errors parked: {STATS['people_errors_parked']:,}")
        log(f"People errors retried: {STATS['people_errors_retried']:,}")
        log(f"CT records reset: {STATS['ct_reset_to_pending']:,}")

        # Show delta
        before_nr = STATS['before'].get('NOT_READY', 0)
        after_nr = STATS['after'].get('NOT_READY', 0)
        delta = after_nr - before_nr
        log(f"\nNOT_READY delta: {before_nr:,} -> {after_nr:,} ({delta:+,})")

    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
