#!/usr/bin/env python3
"""
Talent Flow Dumb Worker — Signal Detection
=============================================
Doctrine: hubs/talent-flow/PRD.md
Altitude: Middle (SQL against existing Neon data, no external APIs)

PURPOSE:
    Detect four talent-flow signals from people.slot_assignment_history,
    trace person movements across companies, validate ICP for discovered
    companies, and write to outreach.signal_output. Runs monthly.
    Stateless — safe to re-run.

    Reads slot_assignment_history events in run_month, traces where
    people went (via people_master LinkedIn/email changes), discovers
    new companies via cascade, and validates ICP (50-2000 employees,
    PA/VA/MD/OH/WV/KY).

SIGNALS:
    TF-01  Departure         Person left a tracked slot (VACATE event)
    TF-02  Arrival           Person filled a tracked slot (ASSIGN event, came from another company)
    TF-03  Replacement       Person displaced another in a tracked slot (DISPLACE event)
    TF-04  Company Discovered  Cascade traced a person to a company NOT in outreach — ICP validated

DATA JOIN:
    slot_assignment_history.company_slot_unique_id → people.company_slot.slot_id
    → people.company_slot.outreach_id (FK to outreach.outreach)

    For cascade: people_master.unique_id → LinkedIn/company changes
    ICP: outreach.outreach for employee_count + state validation

USAGE:
    doppler run -- python hubs/talent-flow/imo/middle/dumb_worker.py
    doppler run -- python hubs/talent-flow/imo/middle/dumb_worker.py --dry-run
    doppler run -- python hubs/talent-flow/imo/middle/dumb_worker.py --month 2026-02
    doppler run -- python hubs/talent-flow/imo/middle/dumb_worker.py --signal TF-01

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
from typing import List, Tuple, Dict, Any

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
    "TF-01": {"name": "Departure",          "magnitude": 55, "expiry_days": 90},
    "TF-02": {"name": "Arrival",            "magnitude": 60, "expiry_days": 90},
    "TF-03": {"name": "Replacement",        "magnitude": 65, "expiry_days": 90},
    "TF-04": {"name": "Company Discovered", "magnitude": 70, "expiry_days": 180},
}

# ICP filter constants
ICP_MIN_EMPLOYEES = 50
ICP_MAX_EMPLOYEES = 2000
ICP_STATES = {"PA", "VA", "MD", "OH", "WV", "KY"}

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

def detect_talent_flow_signals(cur, run_month: date) -> Dict[str, List[Tuple]]:
    """
    Query slot_assignment_history for events in run_month and classify into
    TF-01 through TF-03 signals. Also traces person movements for TF-04.

    Returns dict: signal_code -> List[(outreach_id, magnitude, signal_value)]
    """
    month_start = run_month
    month_end = date(
        run_month.year + (run_month.month // 12),
        (run_month.month % 12) + 1,
        1,
    )

    # Pull all events in the run month with the outreach_id join.
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
            pm_curr.first_name   AS person_first_name,
            pm_curr.last_name    AS person_last_name,
            pm_curr.title        AS person_title,
            pm_curr.linkedin_url AS person_linkedin
        FROM   people.slot_assignment_history h
        JOIN   people.company_slot cs
               ON cs.slot_id = h.company_slot_unique_id::uuid
        LEFT JOIN people.people_master pm_curr
               ON pm_curr.unique_id = h.person_unique_id
        WHERE  h.event_ts >= %(month_start)s
          AND  h.event_ts <  %(month_end)s
          AND  h.company_slot_unique_id ~ '^[0-9a-f]{8}-'
        ORDER BY h.event_ts
    """, {"month_start": month_start, "month_end": month_end})

    rows = cur.fetchall()
    log.info("  Joinable events in run month: %d", len(rows))

    if len(rows) == 0:
        cur.execute("""
            SELECT count(*) FROM people.slot_assignment_history
            WHERE event_ts >= %(month_start)s AND event_ts < %(month_end)s
        """, {"month_start": month_start, "month_end": month_end})
        total_raw = cur.fetchone()["count"]
        if total_raw > 0:
            log.warning(
                "  %d raw events exist but 0 are joinable. "
                "Legacy rows use Barton IDs which don't match UUID-based company_slot.",
                total_raw,
            )

    results: Dict[str, List[Tuple]] = {code: [] for code in SIGNALS}
    persons_who_left: List[Dict[str, Any]] = []

    for row in rows:
        outreach_id = row["outreach_id"]
        if not outreach_id:
            continue

        event_type = row["event_type"]
        slot_type = row["slot_type"]
        person_id = row["person_unique_id"]

        base_payload = {
            "event_type": event_type,
            "slot_type": slot_type,
            "person_unique_id": person_id,
            "person_name": f"{row['person_first_name'] or ''} {row['person_last_name'] or ''}".strip(),
            "person_title": row["person_title"],
            "event_ts": row["event_ts"].isoformat() if row["event_ts"] else None,
            "tenure_days": row["tenure_days"],
            "source_table": "people.slot_assignment_history",
        }

        if event_type == "VACATE":
            # TF-01: Departure — person left a tracked slot
            payload = {**base_payload, "detected_by": "TF-01"}
            results["TF-01"].append((outreach_id, SIGNALS["TF-01"]["magnitude"], payload))
            # Track this person for cascade tracing
            persons_who_left.append({
                "person_unique_id": person_id,
                "from_outreach_id": outreach_id,
                "from_company_id": row["company_unique_id"],
                "person_linkedin": row["person_linkedin"],
            })

        elif event_type == "DISPLACE":
            # TF-03: Replacement — someone replaced someone else
            payload = {
                **base_payload,
                "displaced_by_person_id": row["displaced_by_person_id"],
                "displacement_reason": row["displacement_reason"],
                "detected_by": "TF-03",
            }
            results["TF-03"].append((outreach_id, SIGNALS["TF-03"]["magnitude"], payload))

        elif event_type == "ASSIGN":
            # TF-02: Arrival — person filled a slot (check if they came from elsewhere)
            payload = {**base_payload, "detected_by": "TF-02"}
            results["TF-02"].append((outreach_id, SIGNALS["TF-02"]["magnitude"], payload))

    # --- Cascade tracing for TF-04 ---
    # For each person who left, check if they appear in a different company's slot
    # that is NOT currently in the outreach spine (new company discovery)
    if persons_who_left:
        log.info("  Tracing %d departures for cascade discovery...", len(persons_who_left))
        discovered = _cascade_trace(cur, persons_who_left, month_start, month_end)
        results["TF-04"].extend(discovered)

    return results


def _cascade_trace(
    cur,
    persons_who_left: List[Dict[str, Any]],
    month_start: date,
    month_end: date,
) -> List[Tuple]:
    """
    For each person who left, check if they were assigned to a DIFFERENT company
    in the same time window (cross-company movement). If the new company passes
    ICP, emit TF-04.

    Returns: List[(outreach_id_of_source_company, magnitude, signal_value)]
    """
    results = []
    person_ids = [p["person_unique_id"] for p in persons_who_left if p["person_unique_id"]]
    if not person_ids:
        return results

    # Find any ASSIGN events for these persons at a different company in the same window
    cur.execute("""
        SELECT
            h.person_unique_id,
            h.company_unique_id AS new_company_id,
            cs.outreach_id AS new_outreach_id,
            h.event_ts,
            h.slot_type,
            o.domain AS new_company_domain,
            o.company_name AS new_company_name
        FROM   people.slot_assignment_history h
        JOIN   people.company_slot cs
               ON cs.slot_id = h.company_slot_unique_id::uuid
        LEFT JOIN outreach.outreach o
               ON o.outreach_id = cs.outreach_id
        WHERE  h.event_type = 'ASSIGN'
          AND  h.event_ts >= %(month_start)s
          AND  h.event_ts <  %(month_end)s
          AND  h.person_unique_id = ANY(%(person_ids)s)
          AND  h.company_slot_unique_id ~ '^[0-9a-f]{8}-'
    """, {
        "month_start": month_start,
        "month_end": month_end,
        "person_ids": person_ids,
    })

    arrivals = cur.fetchall()
    log.info("  Cascade found %d arrival events for departed persons", len(arrivals))

    # Build lookup for persons who left
    left_lookup = {}
    for p in persons_who_left:
        pid = p["person_unique_id"]
        if pid:
            left_lookup[pid] = p

    for arr in arrivals:
        pid = arr["person_unique_id"]
        if pid not in left_lookup:
            continue

        departure = left_lookup[pid]
        # Only emit if the person moved to a DIFFERENT company
        if arr["new_company_id"] == departure["from_company_id"]:
            continue

        # If destination company already has an outreach_id, this is a known company
        # — not a TF-04 discovery (though the movement itself is tracked via TF-01/TF-02)
        if arr["new_outreach_id"]:
            log.info(
                "  Person %s moved to known company (outreach_id=%s) — not TF-04",
                pid, arr["new_outreach_id"],
            )
            continue

        # New company discovered — validate ICP
        icp_result = _validate_icp(cur, arr["new_company_id"])
        if not icp_result["passed"]:
            log.info(
                "  Discovered company %s failed ICP: %s",
                arr["new_company_id"], icp_result["reason"],
            )
            continue

        # TF-04: Company Discovered via cascade
        payload = {
            "detected_by": "TF-04",
            "person_unique_id": pid,
            "from_outreach_id": str(departure["from_outreach_id"]),
            "new_company_id": arr["new_company_id"],
            "new_company_name": arr["new_company_name"],
            "new_company_domain": arr["new_company_domain"],
            "movement_type": "departure_to_new_company",
            "event_ts": arr["event_ts"].isoformat() if arr["event_ts"] else None,
            "icp_result": icp_result,
            "source_table": "people.slot_assignment_history",
        }
        # Emit against the SOURCE company's outreach_id (the company that lost the person)
        results.append((
            departure["from_outreach_id"],
            SIGNALS["TF-04"]["magnitude"],
            payload,
        ))

    return results


def _validate_icp(cur, company_unique_id: str) -> Dict[str, Any]:
    """
    ICP validation gate for discovered companies.
    Criteria: 50-2000 employees, PA/VA/MD/OH/WV/KY.
    """
    cur.execute("""
        SELECT
            o.outreach_id,
            o.employee_count,
            o.state
        FROM outreach.outreach o
        WHERE o.company_unique_id = %(company_id)s
        LIMIT 1
    """, {"company_id": company_unique_id})

    row = cur.fetchone()
    if not row:
        # Company not in outreach at all — could be truly new
        return {"passed": False, "reason": "NOT_IN_OUTREACH_SPINE"}

    emp_count = row.get("employee_count")
    state = row.get("state", "")

    if emp_count is None:
        return {"passed": False, "reason": "NO_EMPLOYEE_COUNT"}

    if emp_count < ICP_MIN_EMPLOYEES or emp_count > ICP_MAX_EMPLOYEES:
        return {
            "passed": False,
            "reason": f"EMPLOYEE_COUNT_OUT_OF_RANGE: {emp_count}",
            "employee_count": emp_count,
        }

    if state and state.upper() not in ICP_STATES:
        return {
            "passed": False,
            "reason": f"STATE_NOT_IN_ICP: {state}",
            "state": state,
        }

    return {
        "passed": True,
        "employee_count": emp_count,
        "state": state,
    }


# ---------------------------------------------------------------------------
# Error logging
# ---------------------------------------------------------------------------

def log_error(cur, source_spoke: str, error_type: str, raw_payload: dict) -> None:
    """Write to talent_flow error table."""
    cur.execute("""
        INSERT INTO outreach.talent_flow_errors
            (error_id, source_spoke, error_type, raw_payload)
        VALUES
            (%(error_id)s, %(source_spoke)s, %(error_type)s, %(raw_payload)s)
    """, {
        "error_id": str(uuid.uuid4()),
        "source_spoke": source_spoke,
        "error_type": error_type,
        "raw_payload": psycopg2.extras.Json(raw_payload),
    })


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

        try:
            cur.execute("""
                INSERT INTO outreach.signal_output
                    (outreach_id, signal_code, signal_name, signal_source,
                     signal_value, magnitude, expires_at, correlation_id, run_month)
                VALUES
                    (%(outreach_id)s, %(signal_code)s, %(signal_name)s, 'talent_flow',
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
        except Exception as e:
            log.warning("Failed to write %s for outreach_id=%s: %s", signal_code, outreach_id, e)
            try:
                log_error(cur, "talent_flow", "SIGNAL_WRITE_FAILED", {
                    "signal_code": signal_code,
                    "outreach_id": str(outreach_id),
                    "error": str(e),
                })
            except Exception:
                pass

    return written


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="Talent Flow Dumb Worker — signal detection")
    p.add_argument("--dry-run", action="store_true",
                   help="Print signals without writing to DB")
    p.add_argument("--month", metavar="YYYY-MM",
                   help="Override run month (default: current month)")
    p.add_argument("--signal", metavar="TF-NN",
                   help="Run only a specific signal (e.g. TF-01)")
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
    log.info("Talent Flow Dumb Worker starting")
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
        all_detections = detect_talent_flow_signals(cur, run_month)

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
    print(f"  Talent Flow Dumb Worker — {run_month}{'  [DRY-RUN]' if args.dry_run else ''}")
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
