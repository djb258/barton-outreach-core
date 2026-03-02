#!/usr/bin/env python3
"""
DOL Dumb Worker — Signal Detection
====================================
Doctrine: hubs/dol-filings/PRD.md
Altitude: Middle (pure SQL, no external APIs)

PURPOSE:
    Detect seven DOL-derived signals from existing Neon data and write
    to outreach.signal_output. Runs monthly. Stateless — safe to re-run.

SIGNALS:
    D-01  Self-Fund Candidate   outreach.dol.funding_type = 'self_funded'
    D-02  High Cost Growth      YoY participant count increase >20% (same EIN)
    D-03  Broker Change         Different ins_carrier_name across form_years (same EIN)
    D-04  Renewal Proximity     outreach_start_month = current or next month
    D-05  Large Plan            tot_active_partcp_cnt >= 500
    D-06  Cost Increase         YoY total plan assets decrease >10% (benefit drain proxy)
    D-07  Filing Anomaly        EIN has filings in some years but gaps (missing year)

DATA COVERAGE NOTE:
    outreach.dol has ~13,000 rows (~27% of the 95K outreach spine).
    Signals D-01 and D-04 read from outreach.dol — coverage is bounded by
    EIN match rate. D-02, D-03, D-05, D-06, D-07 join through dol.form_5500
    and are similarly bounded. This is expected behavior, not a bug.
    See WO-DOL-001 for EIN enrichment work order.

USAGE:
    doppler run -- python hubs/dol-filings/imo/middle/dumb_worker.py
    doppler run -- python hubs/dol-filings/imo/middle/dumb_worker.py --dry-run
    doppler run -- python hubs/dol-filings/imo/middle/dumb_worker.py --month 2026-02
    doppler run -- python hubs/dol-filings/imo/middle/dumb_worker.py --signal D-03
    doppler run -- python hubs/dol-filings/imo/middle/dumb_worker.py --dry-run --signal D-01

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
    "D-01": {"name": "Self-Fund Candidate",  "magnitude": 60,  "expiry_days": 365},
    "D-02": {"name": "High Cost Growth",     "magnitude": 50,  "expiry_days": 365},
    "D-03": {"name": "Broker Change",        "magnitude": 70,  "expiry_days": 365},
    "D-04": {"name": "Renewal Proximity",    "magnitude": None, "expiry_days": 90},  # dynamic
    "D-05": {"name": "Large Plan",           "magnitude": 55,  "expiry_days": 365},
    "D-06": {"name": "Cost Increase",        "magnitude": 45,  "expiry_days": 365},
    "D-07": {"name": "Filing Anomaly",       "magnitude": 50,  "expiry_days": 365},
}

# ---------------------------------------------------------------------------
# DB connection (identical to run_coverage.py:47-54)
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
# Signal detection functions
# Each returns: List[Tuple[outreach_id, magnitude, signal_value_dict]]
# ---------------------------------------------------------------------------

def detect_d01(cur) -> List[Tuple]:
    """D-01: Self-Fund Candidate — funding_type = 'self_funded' in outreach.dol"""
    cur.execute("""
        SELECT outreach_id,
               ein,
               funding_type
        FROM   outreach.dol
        WHERE  funding_type = 'self_funded'
          AND  outreach_id IS NOT NULL
    """)
    rows = cur.fetchall()
    results = []
    for row in rows:
        results.append((
            row["outreach_id"],
            SIGNALS["D-01"]["magnitude"],
            {"ein": row["ein"], "funding_type": row["funding_type"],
             "source_table": "outreach.dol", "detected_by": "D-01"},
        ))
    return results


def detect_d02(cur) -> List[Tuple]:
    """D-02: High Cost Growth — YoY participant count increase >20% for same EIN"""
    cur.execute("""
        WITH ranked AS (
            SELECT od.outreach_id,
                   f.sponsor_dfe_ein,
                   f.tot_active_partcp_cnt,
                   f.form_year,
                   LAG(f.tot_active_partcp_cnt) OVER (
                       PARTITION BY f.sponsor_dfe_ein
                       ORDER BY f.form_year
                   ) AS prev_cnt
            FROM   dol.form_5500 f
            JOIN   outreach.dol od
                   ON od.ein = regexp_replace(f.sponsor_dfe_ein, '[^0-9]', '', 'g')
            WHERE  f.tot_active_partcp_cnt IS NOT NULL
              AND  f.tot_active_partcp_cnt > 0
        )
        SELECT DISTINCT ON (outreach_id)
               outreach_id,
               sponsor_dfe_ein,
               tot_active_partcp_cnt  AS curr_cnt,
               prev_cnt,
               form_year
        FROM   ranked
        WHERE  prev_cnt IS NOT NULL
          AND  prev_cnt > 0
          AND  (tot_active_partcp_cnt - prev_cnt)::float / prev_cnt > 0.20
        ORDER BY outreach_id, form_year DESC
    """)
    rows = cur.fetchall()
    results = []
    for row in rows:
        pct = round((row["curr_cnt"] - row["prev_cnt"]) / row["prev_cnt"] * 100, 1)
        results.append((
            row["outreach_id"],
            SIGNALS["D-02"]["magnitude"],
            {"ein": row["sponsor_dfe_ein"], "form_year": row["form_year"],
             "curr_participants": row["curr_cnt"], "prev_participants": row["prev_cnt"],
             "growth_pct": pct, "source_table": "dol.form_5500", "detected_by": "D-02"},
        ))
    return results


def detect_d03(cur) -> List[Tuple]:
    """D-03: Broker Change — different ins_carrier_name for same EIN across form_years"""
    cur.execute("""
        WITH carriers AS (
            SELECT od.outreach_id,
                   f.sponsor_dfe_ein,
                   sa.ins_carrier_name,
                   sa.form_year,
                   LAG(sa.ins_carrier_name) OVER (
                       PARTITION BY f.sponsor_dfe_ein
                       ORDER BY sa.form_year
                   ) AS prev_carrier
            FROM   dol.schedule_a sa
            JOIN   dol.form_5500 f  ON f.filing_id = sa.filing_id
            JOIN   outreach.dol od
                   ON od.ein = regexp_replace(f.sponsor_dfe_ein, '[^0-9]', '', 'g')
            WHERE  sa.ins_carrier_name IS NOT NULL
              AND  sa.wlfr_bnft_health_ind = 'X'
        )
        SELECT DISTINCT ON (outreach_id)
               outreach_id,
               sponsor_dfe_ein,
               ins_carrier_name  AS curr_carrier,
               prev_carrier,
               form_year
        FROM   carriers
        WHERE  prev_carrier IS NOT NULL
          AND  ins_carrier_name <> prev_carrier
        ORDER BY outreach_id, form_year DESC
    """)
    rows = cur.fetchall()
    results = []
    for row in rows:
        results.append((
            row["outreach_id"],
            SIGNALS["D-03"]["magnitude"],
            {"ein": row["sponsor_dfe_ein"], "form_year": row["form_year"],
             "curr_carrier": row["curr_carrier"], "prev_carrier": row["prev_carrier"],
             "source_table": "dol.schedule_a", "detected_by": "D-03"},
        ))
    return results


def detect_d04(cur, run_month: date) -> List[Tuple]:
    """D-04: Renewal Proximity — outreach_start_month = current or next month
    Magnitude 80 for current month, 50 for next month."""
    current_month = run_month.month
    next_month = (run_month.month % 12) + 1

    cur.execute("""
        SELECT outreach_id,
               ein,
               renewal_month,
               outreach_start_month
        FROM   outreach.dol
        WHERE  outreach_start_month IN %(months)s
          AND  outreach_id IS NOT NULL
    """, {"months": (current_month, next_month)})
    rows = cur.fetchall()
    results = []
    for row in rows:
        magnitude = 80 if row["outreach_start_month"] == current_month else 50
        results.append((
            row["outreach_id"],
            magnitude,
            {"ein": row["ein"], "renewal_month": row["renewal_month"],
             "outreach_start_month": row["outreach_start_month"],
             "proximity": "current_month" if magnitude == 80 else "next_month",
             "source_table": "outreach.dol", "detected_by": "D-04"},
        ))
    return results


def detect_d05(cur) -> List[Tuple]:
    """D-05: Large Plan — tot_active_partcp_cnt >= 500"""
    cur.execute("""
        SELECT DISTINCT ON (od.outreach_id)
               od.outreach_id,
               f.sponsor_dfe_ein,
               f.tot_active_partcp_cnt,
               f.form_year
        FROM   dol.form_5500 f
        JOIN   outreach.dol od
               ON od.ein = regexp_replace(f.sponsor_dfe_ein, '[^0-9]', '', 'g')
        WHERE  f.tot_active_partcp_cnt >= 500
        ORDER BY od.outreach_id, f.form_year DESC
    """)
    rows = cur.fetchall()
    results = []
    for row in rows:
        results.append((
            row["outreach_id"],
            SIGNALS["D-05"]["magnitude"],
            {"ein": row["sponsor_dfe_ein"], "form_year": row["form_year"],
             "participants": row["tot_active_partcp_cnt"],
             "source_table": "dol.form_5500", "detected_by": "D-05"},
        ))
    return results


def detect_d06(cur) -> List[Tuple]:
    """D-06: Cost Increase — YoY total plan assets decrease >10% (benefit drain proxy).
    Uses tot_active_partcp_cnt as an asset proxy since form_5500 has no direct cost column.
    Detects participant count DECREASE >10% YoY (plan shrinkage / cost pressure signal)."""
    cur.execute("""
        WITH ranked AS (
            SELECT od.outreach_id,
                   f.sponsor_dfe_ein,
                   f.tot_active_partcp_cnt,
                   f.form_year,
                   LAG(f.tot_active_partcp_cnt) OVER (
                       PARTITION BY f.sponsor_dfe_ein
                       ORDER BY f.form_year
                   ) AS prev_cnt
            FROM   dol.form_5500 f
            JOIN   outreach.dol od
                   ON od.ein = regexp_replace(f.sponsor_dfe_ein, '[^0-9]', '', 'g')
            WHERE  f.tot_active_partcp_cnt IS NOT NULL
              AND  f.tot_active_partcp_cnt > 0
        )
        SELECT DISTINCT ON (outreach_id)
               outreach_id,
               sponsor_dfe_ein,
               tot_active_partcp_cnt  AS curr_cnt,
               prev_cnt,
               form_year
        FROM   ranked
        WHERE  prev_cnt IS NOT NULL
          AND  prev_cnt > 0
          AND  (prev_cnt - tot_active_partcp_cnt)::float / prev_cnt > 0.10
        ORDER BY outreach_id, form_year DESC
    """)
    rows = cur.fetchall()
    results = []
    for row in rows:
        pct = round((row["prev_cnt"] - row["curr_cnt"]) / row["prev_cnt"] * 100, 1)
        results.append((
            row["outreach_id"],
            SIGNALS["D-06"]["magnitude"],
            {"ein": row["sponsor_dfe_ein"], "form_year": row["form_year"],
             "curr_participants": row["curr_cnt"], "prev_participants": row["prev_cnt"],
             "decline_pct": pct, "proxy_note": "participant_count_used_as_cost_proxy",
             "source_table": "dol.form_5500", "detected_by": "D-06"},
        ))
    return results


def detect_d07(cur) -> List[Tuple]:
    """D-07: Filing Anomaly — EIN has filings in some years but gaps (missing year).
    Checks for EINs that filed in 2022 and 2024 but not 2023, or similar patterns.
    Gap detection done in Python — simpler than SQL generate_series subqueries."""
    cur.execute("""
        WITH filing_years AS (
            SELECT od.outreach_id,
                   f.sponsor_dfe_ein,
                   array_agg(DISTINCT f.form_year::integer ORDER BY f.form_year::integer) AS years_filed
            FROM   dol.form_5500 f
            JOIN   outreach.dol od
                   ON od.ein = regexp_replace(f.sponsor_dfe_ein, '[^0-9]', '', 'g')
            WHERE  f.form_year ~ '^[0-9]{4}$'
            GROUP BY od.outreach_id, f.sponsor_dfe_ein
            HAVING count(DISTINCT f.form_year) >= 2
        )
        SELECT outreach_id, sponsor_dfe_ein, years_filed
        FROM   filing_years
    """)
    rows = cur.fetchall()
    results = []
    for row in rows:
        years = sorted(row["years_filed"])
        expected = set(range(years[0], years[-1] + 1))
        actual = set(years)
        missing = sorted(expected - actual)
        if missing:
            results.append((
                row["outreach_id"],
                SIGNALS["D-07"]["magnitude"],
                {"ein": row["sponsor_dfe_ein"], "years_filed": years,
                 "missing_years": missing,
                 "source_table": "dol.form_5500", "detected_by": "D-07"},
            ))
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
    """Insert detections into outreach.signal_output. Returns count written."""
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
                (%(outreach_id)s, %(signal_code)s, %(signal_name)s, 'dol',
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
    p = argparse.ArgumentParser(description="DOL Dumb Worker — signal detection")
    p.add_argument("--dry-run", action="store_true",
                   help="Print signals without writing to DB")
    p.add_argument("--month", metavar="YYYY-MM",
                   help="Override run month (default: current month)")
    p.add_argument("--signal", metavar="D-NN",
                   help="Run only a specific signal (e.g. D-03)")
    return p.parse_args()


def main():
    args = parse_args()

    # Resolve run month
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
    log.info("DOL Dumb Worker starting")
    log.info("  run_month      = %s", run_month)
    log.info("  correlation_id = %s", correlation_id)
    log.info("  dry_run        = %s", args.dry_run)
    if args.signal:
        log.info("  signal filter  = %s", args.signal)

    # Validate signal filter
    if args.signal and args.signal not in SIGNALS:
        log.error("Unknown signal code: %s. Valid: %s", args.signal, list(SIGNALS.keys()))
        sys.exit(1)

    signal_filter = [args.signal] if args.signal else list(SIGNALS.keys())

    try:
        conn = get_connection()
        conn.autocommit = False
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    except Exception as e:
        log.error("DB connection failed: %s", e)
        sys.exit(1)

    totals: Dict[str, int] = {}

    try:
        detectors = {
            "D-01": lambda: detect_d01(cur),
            "D-02": lambda: detect_d02(cur),
            "D-03": lambda: detect_d03(cur),
            "D-04": lambda: detect_d04(cur, run_month),
            "D-05": lambda: detect_d05(cur),
            "D-06": lambda: detect_d06(cur),
            "D-07": lambda: detect_d07(cur),
        }

        for code in signal_filter:
            log.info("Running %s (%s)...", code, SIGNALS[code]["name"])
            detections = detectors[code]()
            log.info("  Detected: %d", len(detections))
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
    print(f"  DOL Dumb Worker — {run_month}{'  [DRY-RUN]' if args.dry_run else ''}")
    print("=" * 60)
    print(f"  {'Code':<8} {'Signal':<25} {'Written':>8}")
    print(f"  {'-'*8} {'-'*25} {'-'*8}")
    grand_total = 0
    for code, count in totals.items():
        print(f"  {code:<8} {SIGNALS[code]['name']:<25} {count:>8}")
        grand_total += count
    print(f"  {'-'*8} {'-'*25} {'-'*8}")
    print(f"  {'TOTAL':<34} {grand_total:>8}")
    print("=" * 60)
    print()

    sys.exit(0)


if __name__ == "__main__":
    main()
