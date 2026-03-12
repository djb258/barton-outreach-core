# TODO: BAR-114 — migrate 408-line dumb worker from psycopg2/Neon to CF Worker/D1
#!/usr/bin/env python3
"""
People Dumb Worker — Signal Detection
=======================================
Doctrine: hubs/people-intelligence/PRD.md
Altitude: Middle (SQL against existing Neon data, no external APIs)

PURPOSE:
    Detect five people-movement signals from people.slot_assignment_history
    and write to outreach.signal_output. Runs monthly. Stateless — safe to re-run.

    No snapshot table needed. slot_assignment_history is populated automatically
    via trigger on people.company_slot. It has 1,370 rows and is live.

SIGNALS:
    P-01  Slot Filled      ASSIGN event in run_month — slot was empty, now filled
    P-02  Promotion        ASSIGN event — same person, seniority upgraded
    P-03  Departure        VACATE event in run_month — slot was filled, now empty
    P-04  New Executive    DISPLACE event — different person took the slot
    P-05  Title Change     ASSIGN event — same person, different title, same seniority

SIGNAL PRIORITY (when multiple apply to same slot event):
    P-04 > P-02 > P-01/P-03 > P-05
    P-03 and P-01 are mutually exclusive (VACATE vs ASSIGN)

DATA JOIN:
    slot_assignment_history.company_unique_id → people.company_slot.company_unique_id
    → people.company_slot.outreach_id (direct FK to outreach.outreach)

USAGE:
    doppler run -- python hubs/people-intelligence/imo/middle/dumb_worker.py
    doppler run -- python hubs/people-intelligence/imo/middle/dumb_worker.py --dry-run
    doppler run -- python hubs/people-intelligence/imo/middle/dumb_worker.py --month 2026-02
    doppler run -- python hubs/people-intelligence/imo/middle/dumb_worker.py --signal P-03

EXIT CODES:
    0 = success (including 0 signals detected)
    1 = error
"""

import os
import sys
import uuid
import argparse
import logging
from datetime import date, datetime, timezone, timedelta
from typing import List, Tuple, Dict, Any, Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Signal metadata
# ---------------------------------------------------------------------------
SIGNALS: Dict[str, Dict[str, Any]] = {
    "P-01": {"name": "Slot Filled",     "magnitude": 60, "expiry_days": 90},
    "P-02": {"name": "Promotion",       "magnitude": 50, "expiry_days": 90},
    "P-03": {"name": "Departure",       "magnitude": 65, "expiry_days": 90},
    "P-04": {"name": "New Executive",   "magnitude": 70, "expiry_days": 90},
    "P-05": {"name": "Title Change",    "magnitude": 40, "expiry_days": 90},
}

# Seniority rank for promotion detection (higher = more senior)
SENIORITY_RANK: Dict[str, int] = {
    "CHRO": 100,
    "HR_MANAGER": 80,
    "BENEFITS_LEAD": 60,
    "PAYROLL_ADMIN": 50,
    "HR_SUPPORT": 30,
    "UNSLOTTED": 0,
}

# ---------------------------------------------------------------------------
# DB connection
# ---------------------------------------------------------------------------
def get_connection():
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        dbname=os.environ["NEON_DATABASE"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
    )


# ---------------------------------------------------------------------------
# Signal detection
# ---------------------------------------------------------------------------

def detect_people_signals(cur, run_month: date) -> Dict[str, List[Tuple]]:
    """
    Query slot_assignment_history for events in run_month and classify into
    P-01 through P-05 signals.

    Returns dict: signal_code -> List[(outreach_id, magnitude, signal_value)]
    """
    month_start = run_month
    month_end = date(
        run_month.year + (run_month.month // 12),
        (run_month.month % 12) + 1,
        1,
    )

    # Pull all events in the run month with the outreach_id join.
    # Join path: slot_assignment_history.company_slot_unique_id
    #            → people.company_slot.slot_id (UUID PK)
    #            → people.company_slot.outreach_id
    # NOTE: Legacy history rows (pre-2026-02) use Barton IDs in
    # company_slot_unique_id/company_unique_id which cannot join to the
    # current UUID-based company_slot. The trigger emits UUID-compatible
    # rows going forward; legacy rows are effectively orphaned.
    cur.execute("""
        SELECT
            h.history_id,
            h.event_type,
            h.company_unique_id,
            h.slot_type,
            h.person_unique_id,
            h.displaced_by_person_id,
            h.displacement_reason,
            h.tenure_days,
            h.event_ts,
            h.event_metadata,
            cs.outreach_id,
            pm_curr.title        AS curr_title,
            pm_curr.seniority    AS curr_seniority,
            pm_prev.title        AS prev_title,
            pm_prev.seniority    AS prev_seniority
        FROM   people.slot_assignment_history h
        -- Join via slot_id (UUID) — only works for post-migration rows
        JOIN   people.company_slot cs
               ON cs.slot_id = h.company_slot_unique_id::uuid
        -- Current person details
        LEFT JOIN people.people_master pm_curr
               ON pm_curr.unique_id = h.person_unique_id
        -- Previous person details (for displacement comparison)
        LEFT JOIN people.people_master pm_prev
               ON pm_prev.unique_id = h.displaced_by_person_id
        WHERE  h.event_ts >= %(month_start)s
          AND  h.event_ts <  %(month_end)s
          AND  h.company_slot_unique_id ~ '^[0-9a-f]{8}-'
        ORDER BY h.event_ts
    """, {"month_start": month_start, "month_end": month_end})

    rows = cur.fetchall()
    log.info("  Joinable events in run month: %d", len(rows))
    if len(rows) == 0:
        # Check if there are unjoinable legacy rows (Barton ID format)
        cur.execute("""
            SELECT count(*) FROM people.slot_assignment_history
            WHERE event_ts >= %(month_start)s AND event_ts < %(month_end)s
        """, {"month_start": month_start, "month_end": month_end})
        total_raw = cur.fetchone()["count"]
        if total_raw > 0:
            log.warning(
                "  %d raw events exist but 0 are joinable. "
                "Legacy rows use Barton IDs (04.04.xx) which don't match "
                "current UUID-based company_slot. New trigger events will join.",
                total_raw,
            )

    results: Dict[str, List[Tuple]] = {code: [] for code in SIGNALS}

    for row in rows:
        outreach_id = row["outreach_id"]
        if not outreach_id:
            continue

        event_type = row["event_type"]
        slot_type = row["slot_type"]
        person_id = row["person_unique_id"]
        displaced_by = row["displaced_by_person_id"]
        curr_seniority = row["curr_seniority"] or ""
        prev_seniority = row["prev_seniority"] or ""
        curr_title = row["curr_title"] or ""
        prev_title = row["prev_title"] or ""

        base_payload = {
            "event_type": event_type,
            "slot_type": slot_type,
            "person_unique_id": person_id,
            "event_ts": row["event_ts"].isoformat() if row["event_ts"] else None,
            "tenure_days": row["tenure_days"],
            "source_table": "people.slot_assignment_history",
        }

        if event_type == "VACATE":
            # P-03: Departure
            payload = {**base_payload, "detected_by": "P-03"}
            results["P-03"].append((outreach_id, SIGNALS["P-03"]["magnitude"], payload))

        elif event_type == "DISPLACE":
            # P-04: New Executive (someone replaced someone else)
            payload = {
                **base_payload,
                "displaced_by_person_id": displaced_by,
                "displacement_reason": row["displacement_reason"],
                "detected_by": "P-04",
            }
            results["P-04"].append((outreach_id, SIGNALS["P-04"]["magnitude"], payload))

        elif event_type == "ASSIGN":
            # Determine which P signal applies — priority: P-02 > P-01 > P-05
            curr_rank = SENIORITY_RANK.get(curr_seniority.upper(), 0)
            prev_rank = SENIORITY_RANK.get(prev_seniority.upper(), 0)

            if prev_seniority and curr_rank > prev_rank:
                # P-02: Promotion — same person, seniority upgraded
                payload = {
                    **base_payload,
                    "prev_seniority": prev_seniority,
                    "curr_seniority": curr_seniority,
                    "seniority_rank_delta": curr_rank - prev_rank,
                    "detected_by": "P-02",
                }
                results["P-02"].append((outreach_id, SIGNALS["P-02"]["magnitude"], payload))

            elif prev_title and curr_title and curr_title != prev_title and curr_rank == prev_rank:
                # P-05: Title Change — same seniority, different title (lateral)
                payload = {
                    **base_payload,
                    "prev_title": prev_title,
                    "curr_title": curr_title,
                    "detected_by": "P-05",
                }
                results["P-05"].append((outreach_id, SIGNALS["P-05"]["magnitude"], payload))

            else:
                # P-01: Slot Filled — new assignment with no prior context
                payload = {
                    **base_payload,
                    "curr_title": curr_title,
                    "curr_seniority": curr_seniority,
                    "detected_by": "P-01",
                }
                results["P-01"].append((outreach_id, SIGNALS["P-01"]["magnitude"], payload))

    return results


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

def write_signals(
    cur,
    signal_code: str,
    detections: List[Tuple],
    run_month: date,
    correlation_id: str,
    dry_run: bool,
) -> int:
    meta = SIGNALS[signal_code]
    expiry_days = meta["expiry_days"]
    signal_name = meta["name"]
    written = 0

    for outreach_id, magnitude, signal_value in detections:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expiry_days)
        if dry_run:
            log.info(
                "[DRY-RUN] %s | %s | outreach_id=%s | magnitude=%d | value=%s",
                signal_code, signal_name, outreach_id, magnitude, signal_value,
            )
            written += 1
            continue

        cur.execute("""
            INSERT INTO outreach.signal_output
                (outreach_id, signal_code, signal_name, signal_source,
                 signal_value, magnitude, expires_at, correlation_id, run_month)
            VALUES
                (%(outreach_id)s, %(signal_code)s, %(signal_name)s, 'people',
                 %(signal_value)s, %(magnitude)s, %(expires_at)s,
                 %(correlation_id)s, %(run_month)s)
            ON CONFLICT (outreach_id, signal_code, run_month) DO NOTHING
        """, {
            "outreach_id": outreach_id,
            "signal_code": signal_code,
            "signal_name": signal_name,
            "signal_value": psycopg2.extras.Json(signal_value),
            "magnitude": magnitude,
            "expires_at": expires_at,
            "correlation_id": correlation_id,
            "run_month": run_month,
        })
        if cur.rowcount > 0:
            written += 1

    return written


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="People Dumb Worker — signal detection")
    p.add_argument("--dry-run", action="store_true",
                   help="Print signals without writing to DB")
    p.add_argument("--month", metavar="YYYY-MM",
                   help="Override run month (default: current month)")
    p.add_argument("--signal", metavar="P-NN",
                   help="Run only a specific signal (e.g. P-03)")
    return p.parse_args()


def main():
    args = parse_args()

    if args.month:
        try:
            run_month = date.fromisoformat(args.month + "-01")
        except ValueError:
            log.error("Invalid --month format. Use YYYY-MM (e.g. 2026-03)")
            sys.exit(1)
    else:
        today = date.today()
        run_month = date(today.year, today.month, 1)

    correlation_id = str(uuid.uuid4())
    log.info("People Dumb Worker starting")
    log.info("  run_month      = %s", run_month)
    log.info("  correlation_id = %s", correlation_id)
    log.info("  dry_run        = %s", args.dry_run)
    if args.signal:
        log.info("  signal filter  = %s", args.signal)

    if args.signal and args.signal not in SIGNALS:
        log.error("Unknown signal code: %s. Valid: %s", args.signal, list(SIGNALS.keys()))
        sys.exit(1)

    signal_filter = {args.signal} if args.signal else set(SIGNALS.keys())

    try:
        conn = get_connection()
        conn.autocommit = False
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    except Exception as e:
        log.error("DB connection failed: %s", e)
        sys.exit(1)

    totals: Dict[str, int] = {code: 0 for code in SIGNALS}

    try:
        log.info("Detecting signals from slot_assignment_history...")
        all_detections = detect_people_signals(cur, run_month)

        for code in SIGNALS:
            if code not in signal_filter:
                continue
            detections = all_detections[code]
            log.info("  %s (%s): %d detected", code, SIGNALS[code]["name"], len(detections))
            written = write_signals(cur, code, detections, run_month,
                                    correlation_id, args.dry_run)
            totals[code] = written

        if not args.dry_run:
            conn.commit()
            log.info("Committed.")

    except Exception as e:
        conn.rollback()
        log.error("Worker failed: %s", e)
        cur.close()
        conn.close()
        sys.exit(1)

    cur.close()
    conn.close()

    # Summary
    print()
    print("=" * 60)
    print(f"  People Dumb Worker — {run_month}{'  [DRY-RUN]' if args.dry_run else ''}")
    print("=" * 60)
    print(f"  {'Code':<8} {'Signal':<25} {'Written':>8}")
    print(f"  {'-'*8} {'-'*25} {'-'*8}")
    grand_total = 0
    for code in SIGNALS:
        if code in signal_filter:
            count = totals[code]
            print(f"  {code:<8} {SIGNALS[code]['name']:<25} {count:>8}")
            grand_total += count
    print(f"  {'-'*8} {'-'*25} {'-'*8}")
    print(f"  {'TOTAL':<34} {grand_total:>8}")
    print("=" * 60)
    print()

    sys.exit(0)


if __name__ == "__main__":
    main()
