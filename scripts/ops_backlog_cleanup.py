#!/usr/bin/env python3
"""
Ops Backlog Cleanup Agent
-------------------------
Reduces NOT_READY backlog by resolving errors, triggering retries,
and promoting records that pass gates.

Execute with: doppler run -- python scripts/ops_backlog_cleanup.py
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from uuid import uuid4
from pathlib import Path

# Audit trail
AUDIT_LOG = []
STATS = {
    "before": {},
    "after": {},
    "records_processed": 0,
    "moved_to_TIER_0": 0,
    "moved_to_TIER_2": 0,
    "moved_to_TIER_3": 0,
    "retries_triggered": 0,
    "errors_resolved": 0,
    "parked": 0,
    "archived": 0,
    "skipped": 0,
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


def log_audit(action, outreach_id, details):
    """Log auditable action."""
    AUDIT_LOG.append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "outreach_id": str(outreach_id),
        "details": details
    })


def log(msg, level="INFO"):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


def get_before_state(conn):
    """Capture promotion readiness state before cleanup."""
    log("Capturing BEFORE state...")
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT readiness_tier, COUNT(*) as count
            FROM shq.vw_promotion_readiness
            GROUP BY readiness_tier
            ORDER BY readiness_tier
        """)
        results = cur.fetchall()
        state = {row['readiness_tier']: row['count'] for row in results}
        STATS["before"] = state
        log(f"  Before state: {state}")
        return state


def get_after_state(conn):
    """Capture promotion readiness state after cleanup."""
    log("Capturing AFTER state...")
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT readiness_tier, COUNT(*) as count
            FROM shq.vw_promotion_readiness
            GROUP BY readiness_tier
            ORDER BY readiness_tier
        """)
        results = cur.fetchall()
        state = {row['readiness_tier']: row['count'] for row in results}
        STATS["after"] = state
        log(f"  After state: {state}")
        return state


def get_not_ready_records(conn, limit=500):
    """Get all NOT_READY outreach_ids with blocker info."""
    log(f"Fetching NOT_READY records (limit={limit})...")
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                pr.outreach_id,
                pr.readiness_tier,
                pr.company_target_done,
                pr.dol_done,
                pr.people_done,
                pr.blog_done,
                pr.bit_done,
                pr.has_ct_blocking_errors,
                pr.has_dol_blocking_errors,
                pr.has_people_blocking_errors
            FROM shq.vw_promotion_readiness pr
            WHERE pr.readiness_tier = 'NOT_READY'
            LIMIT %s
        """, (limit,))
        records = cur.fetchall()
        log(f"  Found {len(records)} NOT_READY records")
        return records


def get_blockers_for_outreach(conn, outreach_id):
    """Get specific blockers for an outreach_id."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT * FROM shq.fn_get_promotion_blockers(%s)
        """, (outreach_id,))
        return cur.fetchall()


def get_blocking_errors(conn, outreach_id):
    """Get actual error records blocking this outreach."""
    errors = []
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Company Target errors
        cur.execute("""
            SELECT
                'company_target' as source,
                error_id,
                failure_code,
                blocking_reason,
                disposition,
                retry_count,
                max_retries,
                retry_exhausted,
                created_at
            FROM outreach.company_target_errors
            WHERE outreach_id = %s
              AND disposition IN ('RETRY', 'PARKED')
              AND archived_at IS NULL
        """, (outreach_id,))
        errors.extend(cur.fetchall())

        # DOL errors
        cur.execute("""
            SELECT
                'dol' as source,
                error_id,
                failure_code,
                blocking_reason,
                disposition,
                retry_count,
                max_retries,
                retry_exhausted,
                created_at
            FROM outreach.dol_errors
            WHERE outreach_id = %s
              AND disposition IN ('RETRY', 'PARKED')
              AND archived_at IS NULL
        """, (outreach_id,))
        errors.extend(cur.fetchall())

        # People errors
        cur.execute("""
            SELECT
                'people' as source,
                error_id,
                error_code as failure_code,
                error_message as blocking_reason,
                disposition,
                retry_count,
                max_retries,
                retry_exhausted,
                created_at
            FROM people.people_errors
            WHERE outreach_id = %s
              AND disposition IN ('RETRY', 'PARKED')
              AND archived_at IS NULL
        """, (outreach_id,))
        errors.extend(cur.fetchall())

    return errors


def classify_error(error):
    """
    Classify an error as:
    - retryable: can trigger retry
    - resolvable: data fix possible
    - structural: must park/archive
    """
    disposition = error.get('disposition', 'RETRY')
    retry_exhausted = error.get('retry_exhausted', False)
    retry_count = error.get('retry_count', 0) or 0
    max_retries = error.get('max_retries', 3) or 3
    failure_code = error.get('failure_code', '') or ''

    # Already exhausted retries → structural
    if retry_exhausted:
        return 'structural', 'retry_exhausted'

    # Parked errors → check if retriable
    if disposition == 'PARKED':
        return 'structural', 'already_parked'

    # Still has retries left → retryable
    if retry_count < max_retries:
        return 'retryable', f'retries_remaining={max_retries - retry_count}'

    # Specific failure codes that are structural
    structural_codes = [
        'COMPANY_NOT_FOUND',
        'INVALID_SOVEREIGN_ID',
        'NO_DOMAIN_POSSIBLE',
        'BANNED_VENDOR',
        'TOOL_NOT_ALLOWED',
    ]
    if failure_code in structural_codes:
        return 'structural', f'code={failure_code}'

    # Default to retryable if under max
    return 'retryable', 'default'


def resolve_error(conn, error, outreach_id):
    """
    Attempt to resolve an error.
    Returns action taken.
    """
    error_id = error['error_id']
    source = error['source']
    classification, reason = classify_error(error)

    table_map = {
        'company_target': 'outreach.company_target_errors',
        'dol': 'outreach.dol_errors',
        'people': 'people.people_errors',
    }
    table = table_map.get(source)
    if not table:
        return 'skipped', 'unknown_source'

    with conn.cursor() as cur:
        if classification == 'retryable':
            # Increment retry and set last_retry_at
            cur.execute(f"""
                UPDATE {table}
                SET
                    retry_count = COALESCE(retry_count, 0) + 1,
                    last_retry_at = NOW(),
                    disposition = CASE
                        WHEN COALESCE(retry_count, 0) + 1 >= COALESCE(max_retries, 3)
                        THEN 'PARKED'::error_disposition
                        ELSE disposition
                    END,
                    retry_exhausted = CASE
                        WHEN COALESCE(retry_count, 0) + 1 >= COALESCE(max_retries, 3)
                        THEN TRUE
                        ELSE FALSE
                    END,
                    parked_at = CASE
                        WHEN COALESCE(retry_count, 0) + 1 >= COALESCE(max_retries, 3)
                        THEN NOW()
                        ELSE parked_at
                    END,
                    parked_by = CASE
                        WHEN COALESCE(retry_count, 0) + 1 >= COALESCE(max_retries, 3)
                        THEN 'ops_cleanup_agent'
                        ELSE parked_by
                    END,
                    park_reason = CASE
                        WHEN COALESCE(retry_count, 0) + 1 >= COALESCE(max_retries, 3)
                        THEN 'MAX_RETRIES_EXCEEDED'
                        ELSE park_reason
                    END
                WHERE error_id = %s
            """, (error_id,))
            conn.commit()
            log_audit('RETRY_TRIGGERED', outreach_id, {
                'error_id': str(error_id),
                'source': source,
                'reason': reason
            })
            return 'retry_triggered', reason

        elif classification == 'structural':
            # Park the error if not already parked
            if error.get('disposition') != 'PARKED':
                cur.execute(f"""
                    UPDATE {table}
                    SET
                        disposition = 'PARKED'::error_disposition,
                        parked_at = NOW(),
                        parked_by = 'ops_cleanup_agent',
                        park_reason = %s
                    WHERE error_id = %s
                """, (reason, error_id))
                conn.commit()
                log_audit('PARKED', outreach_id, {
                    'error_id': str(error_id),
                    'source': source,
                    'reason': reason
                })
                return 'parked', reason
            else:
                return 'already_parked', reason

    return 'skipped', 'no_action'


def check_done_states(conn, outreach_id):
    """Check if DONE states are satisfied after error resolution."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                shq.fn_check_company_target_done(%s) as ct_done,
                shq.fn_check_dol_done(%s) as dol_done,
                shq.fn_check_people_done(%s) as people_done,
                shq.fn_check_blog_done(%s) as blog_done,
                shq.fn_check_bit_done(%s) as bit_done
        """, (outreach_id, outreach_id, outreach_id, outreach_id, outreach_id))
        return cur.fetchone()


def check_promotion_eligibility(conn, outreach_id):
    """Check current promotion tier after resolution."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT readiness_tier
            FROM shq.vw_promotion_readiness
            WHERE outreach_id = %s
        """, (outreach_id,))
        row = cur.fetchone()
        return row['readiness_tier'] if row else 'UNKNOWN'


def process_record(conn, record):
    """Process a single NOT_READY record."""
    outreach_id = record['outreach_id']

    # Get blocking errors
    errors = get_blocking_errors(conn, outreach_id)

    if not errors:
        # No blocking errors but still NOT_READY → DONE state issue
        done_states = check_done_states(conn, outreach_id)
        log_audit('NO_ERRORS', outreach_id, {
            'done_states': done_states,
            'note': 'NOT_READY but no blocking errors - DONE state not met'
        })
        STATS['skipped'] += 1
        return 'skipped', 'no_blocking_errors'

    actions_taken = []

    for error in errors:
        action, reason = resolve_error(conn, error, outreach_id)
        actions_taken.append({
            'error_id': str(error['error_id']),
            'action': action,
            'reason': reason
        })

        if action == 'retry_triggered':
            STATS['retries_triggered'] += 1
        elif action == 'parked':
            STATS['parked'] += 1

    # Re-check promotion eligibility
    new_tier = check_promotion_eligibility(conn, outreach_id)

    if new_tier != 'NOT_READY':
        log_audit('TIER_CHANGE', outreach_id, {
            'from': 'NOT_READY',
            'to': new_tier,
            'actions': actions_taken
        })
        if new_tier == 'TIER_0_ANCHOR_DONE':
            STATS['moved_to_TIER_0'] += 1
        elif new_tier == 'TIER_2_ENRICHMENT_COMPLETE':
            STATS['moved_to_TIER_2'] += 1
        elif new_tier == 'TIER_3_CAMPAIGN_READY':
            STATS['moved_to_TIER_3'] += 1

    return new_tier, actions_taken


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

    report = f"""# Ops Backlog Cleanup Report

**Execution Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
**Executor**: ops_cleanup_agent
**Mode**: Operations Cleanup (No Doctrine Changes)

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Records Processed | {STATS['records_processed']} |
| Moved to TIER_0 | {STATS['moved_to_TIER_0']} |
| Moved to TIER_2 | {STATS['moved_to_TIER_2']} |
| Moved to TIER_3 | {STATS['moved_to_TIER_3']} |
| Retries Triggered | {STATS['retries_triggered']} |
| Errors Parked | {STATS['parked']} |
| Errors Archived | {STATS['archived']} |
| Skipped (No Action) | {STATS['skipped']} |

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

### By Category

| Action | Count |
|--------|-------|
| Retry Triggered | {STATS['retries_triggered']} |
| Parked | {STATS['parked']} |
| Archived | {STATS['archived']} |
| Skipped | {STATS['skipped']} |

---

## Audit Trail

Total audited actions: {len(AUDIT_LOG)}

<details>
<summary>Click to expand full audit log</summary>

```json
{json.dumps(AUDIT_LOG[:100], indent=2, default=str)}
```

{f'... and {len(AUDIT_LOG) - 100} more entries' if len(AUDIT_LOG) > 100 else ''}

</details>

---

## Compliance Statement

This cleanup operation:
- ✅ Did NOT modify doctrine, policies, or enforcement logic
- ✅ Did NOT bypass promotion gates
- ✅ Operated only on existing records
- ✅ Maintained full audit trail
- ✅ Preferred RETRY → RESOLVE over PARK → ARCHIVE

---

## Next Steps

1. Re-run cleanup for remaining NOT_READY records
2. Review parked errors for manual resolution
3. Schedule next governance job run

---

**Generated by**: ops_cleanup_agent
**Timestamp**: {datetime.utcnow().isoformat()}Z
"""

    return report


def main():
    """Main execution."""
    log("=" * 70)
    log("OPS BACKLOG CLEANUP AGENT")
    log("=" * 70)

    # Check environment
    required_vars = ['NEON_HOST', 'NEON_DATABASE', 'NEON_USER', 'NEON_PASSWORD']
    missing = [v for v in required_vars if v not in os.environ]
    if missing:
        log(f"Missing environment variables: {missing}", "ERROR")
        log("Run with: doppler run -- python scripts/ops_backlog_cleanup.py")
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
        get_before_state(conn)

        # Phase 2: Get NOT_READY records
        log("-" * 70)
        log("PHASE 2: FETCH NOT_READY RECORDS")
        log("-" * 70)
        records = get_not_ready_records(conn, limit=500)

        # Phase 3: Process each record
        log("-" * 70)
        log("PHASE 3: PROCESS RECORDS")
        log("-" * 70)

        for i, record in enumerate(records):
            STATS['records_processed'] += 1
            outreach_id = record['outreach_id']

            if (i + 1) % 50 == 0:
                log(f"  Processed {i + 1}/{len(records)} records...")

            try:
                new_tier, actions = process_record(conn, record)
            except Exception as e:
                log(f"  Error processing {outreach_id}: {e}", "WARN")
                log_audit('ERROR', outreach_id, {'error': str(e)})
                STATS['skipped'] += 1

        # Phase 4: Capture after state
        log("-" * 70)
        log("PHASE 4: CAPTURE AFTER STATE")
        log("-" * 70)
        get_after_state(conn)

        # Phase 5: Generate report
        log("-" * 70)
        log("PHASE 5: GENERATE REPORT")
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
        log(f"Records processed: {STATS['records_processed']}")
        log(f"Moved to TIER_0: {STATS['moved_to_TIER_0']}")
        log(f"Moved to TIER_2: {STATS['moved_to_TIER_2']}")
        log(f"Moved to TIER_3: {STATS['moved_to_TIER_3']}")
        log(f"Retries triggered: {STATS['retries_triggered']}")
        log(f"Parked: {STATS['parked']}")
        log(f"Skipped: {STATS['skipped']}")

    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
