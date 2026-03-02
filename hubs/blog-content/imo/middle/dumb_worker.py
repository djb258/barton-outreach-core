#!/usr/bin/env python3
"""
Blog Dumb Worker — Signal Detection
=====================================
Doctrine: hubs/blog-content/PRD.md
Altitude: Middle (SQL + in-process keyword classification, no HTTP fetching)

PURPOSE:
    Classify pre-extracted text from outreach.blog.context_summary into six
    B-xx signals and write to outreach.signal_output. Runs monthly. Stateless.

    v1 DECISION: Classify context_summary text from outreach.blog directly.
    No HTTP fetching. Covers the full 95K outreach spine. Fast.
    Future: --fetch flag for live scraping via company.company_source_urls (when restored).

SIGNALS:
    B-01  Funding Event       Raised capital, investment round, series funding
    B-02  Hiring Surge        Active recruiting, headcount growth, job openings
    B-03  Acquisition/Merger  Acquired, merger, M&A activity
    B-04  Benefits Language   Open enrollment, health plan, self-funded, benefits
    B-05  Leadership Change   New executive, appointed, departed, promoted
    B-06  Expansion/Growth    New office, new market, expansion, relocation

CLASSIFICATION:
    Keyword matching adapted from classify_event.py patterns.
    Hard rules first (deterministic). Confidence = min(0.90, 0.60 + matches * 0.10).
    Threshold: emit if confidence >= 0.60. No LLM in v1.
    Multiple signals can fire for the same company in the same month.

DATA SOURCE:
    outreach.blog — 42,192 records, 100% outreach spine coverage.
    context_summary: AI-generated text summary of company's web presence.
    source_type: page type (about_page, leadership_page, press_page, etc.)

USAGE:
    doppler run -- python hubs/blog-content/imo/middle/dumb_worker.py
    doppler run -- python hubs/blog-content/imo/middle/dumb_worker.py --dry-run
    doppler run -- python hubs/blog-content/imo/middle/dumb_worker.py --dry-run --limit 50
    doppler run -- python hubs/blog-content/imo/middle/dumb_worker.py --month 2026-02
    doppler run -- python hubs/blog-content/imo/middle/dumb_worker.py --signal B-04
    doppler run -- python hubs/blog-content/imo/middle/dumb_worker.py --batch-size 500

EXIT CODES:
    0 = success (including 0 signals detected)
    1 = error
"""

import os
import sys
import re
import uuid
import argparse
import logging
from datetime import date, datetime, timezone, timedelta
from typing import List, Tuple, Dict, Any, Optional, Set

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
    "B-01": {"name": "Funding Event",       "magnitude": 75, "expiry_days": 60},
    "B-02": {"name": "Hiring Surge",        "magnitude": 55, "expiry_days": 60},
    "B-03": {"name": "Acquisition/Merger",  "magnitude": 70, "expiry_days": 60},
    "B-04": {"name": "Benefits Language",   "magnitude": 50, "expiry_days": 60},
    "B-05": {"name": "Leadership Change",   "magnitude": 60, "expiry_days": 60},
    "B-06": {"name": "Expansion/Growth",    "magnitude": 55, "expiry_days": 60},
}

CONFIDENCE_THRESHOLD = 0.60

# ---------------------------------------------------------------------------
# Keyword patterns per signal
# Adapted from classify_event.py — reuse where overlap, extend for B-02/B-04
# ---------------------------------------------------------------------------

KEYWORD_PATTERNS: Dict[str, List[str]] = {
    "B-01": [
        # From FUNDING_KEYWORDS
        r'\braised\b.*\$',
        r'\bfunding\b',
        r'\bseries\s+[a-z]\b',
        r'\bseed\s+round\b',
        r'\bventure\s+capital\b',
        r'\binvestment\s+round\b',
        r'\bmillion\s+in\s+funding\b',
        r'\bbillion\s+in\s+funding\b',
        r'\bcloses\b.*funding',
        r'\bannounces\s+funding\b',
        r'\bpre-seed\b',
        r'\bgrowth\s+round\b',
        r'\binvestor\b',
        r'\bventure\b',
    ],
    "B-02": [
        # Hiring Surge — new patterns (no overlap in classify_event.py)
        r'\bhiring\b',
        r'\brecruiting\b',
        r'\bjob\s+openings?\b',
        r'\bheadcount\s+(?:growth|increase|expansion)\b',
        r'\bwe.re\s+(?:hiring|growing)\b',
        r'\bjoin\s+our\s+team\b',
        r'\bopen\s+(?:positions?|roles?)\b',
        r'\btalent\s+acquisition\b',
        r'\bworkforce\s+(?:growth|expansion)\b',
        r'\bnew\s+hires?\b',
        r'\bstaff(?:ing)?\s+(?:up|growth|increase)\b',
        r'\bexpanding\s+(?:our\s+)?team\b',
    ],
    "B-03": [
        # From ACQUISITION_KEYWORDS
        r'\bacquired\b',
        r'\bacquisition\b',
        r'\bmerger\b',
        r'\bmerged\s+with\b',
        r'\bbuys\b',
        r'\bpurchased\b',
        r'\bto\s+acquire\b',
        r'\bacquisition\s+of\b',
        r'\bmerger\s+agreement\b',
        r'\bcombined\s+company\b',
        r'\bwill\s+acquire\b',
        r'\btakeover\b',
        r'\bm\s*&\s*a\b',
    ],
    "B-04": [
        # Benefits Language — new patterns (no overlap in classify_event.py)
        r'\bopen\s+enrollment\b',
        r'\bemployee\s+benefits?\b',
        r'\bhealth\s+plan\b',
        r'\bself[- ]funded\b',
        r'\bself[- ]insured\b',
        r'\bbenefits?\s+package\b',
        r'\bbenefits?\s+administration\b',
        r'\bgroup\s+health\b',
        r'\bmedical\s+(?:plan|coverage|benefits?)\b',
        r'\bdental\s+(?:plan|coverage|benefits?)\b',
        r'\bvision\s+(?:plan|coverage|benefits?)\b',
        r'\bhsa\b',
        r'\bfsas?\b',
        r'\bwellness\s+program\b',
        r'\bbenefits?\s+broker\b',
        r'\bstop[- ]loss\b',
        r'\bcaptive\s+insurance\b',
    ],
    "B-05": [
        # From LEADERSHIP_KEYWORDS
        r'\bappointed\b',
        r'\bnamed\b.*(?:CEO|CFO|CTO|COO|President|CHRO|VP)',
        r'\bpromoted\b',
        r'\bjoins\b.*(?:CEO|CFO|CTO|COO|executive)',
        r'\bsteps\s+down\b',
        r'\bdeparts\b',
        r'\bresigned\b',
        r'\bretiring\b',
        r'\bnew\s+(?:CEO|CFO|CTO|COO|CHRO|VP)\b',
        r'\bchief\s+(?:executive|financial|technology|operating|human\s+resources)\b',
        r'\bhires\b.*(?:executive|officer)',
        r'\bnew\s+leadership\b',
        r'\bexecutive\s+(?:hire|appointment|transition)\b',
    ],
    "B-06": [
        # From EXPANSION_KEYWORDS
        r'\bexpansion\b',
        r'\bnew\s+office\b',
        r'\bopening\b.*(?:office|location|facility)',
        r'\bexpanding\s+to\b',
        r'\benters\b.*market',
        r'\blaunch(?:ing|es)?\b.*(?:market|region)',
        r'\bnew\s+headquarters\b',
        r'\brelocation\b',
        r'\bnew\s+market\b',
        r'\bgrowth\b.*(?:market|region|territory)',
        r'\bscaling\b',
        r'\bnational\s+expansion\b',
    ],
}

# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

def classify_text(text: str) -> List[Tuple[str, float, List[str]]]:
    """
    Classify a context_summary text against all B-xx signal patterns.
    Returns list of (signal_code, confidence, matched_keywords) for signals
    that meet the confidence threshold.
    """
    if not text or not text.strip():
        return []

    results = []
    text_lower = text.lower()

    for signal_code, patterns in KEYWORD_PATTERNS.items():
        matches = []
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                matches.append(pattern)

        if not matches:
            continue

        confidence = min(0.90, 0.60 + len(matches) * 0.10)
        if confidence >= CONFIDENCE_THRESHOLD:
            results.append((signal_code, confidence, matches))

    return results


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
# Detection
# ---------------------------------------------------------------------------

def detect_blog_signals(
    cur,
    run_month: date,
    signal_filter: Set[str],
    batch_size: int,
    limit: Optional[int],
) -> Dict[str, List[Tuple]]:
    """
    Read outreach.blog context_summary records, classify each, and return
    detected signals grouped by signal_code.

    Skips companies that already have a signal for this run_month (idempotency
    is also handled by ON CONFLICT, but skipping saves classification work).
    """
    # Get outreach_ids already signaled this month for any B-xx code
    cur.execute("""
        SELECT DISTINCT outreach_id
        FROM   outreach.signal_output
        WHERE  signal_source = 'blog'
          AND  run_month = %(run_month)s
    """, {"run_month": run_month})
    already_done: Set[str] = {str(row["outreach_id"]) for row in cur.fetchall()}
    log.info("  Already signaled this month: %d companies (will skip)", len(already_done))

    # Fetch blog records with context_summary
    limit_clause = f"LIMIT {limit}" if limit else ""
    cur.execute(f"""
        SELECT outreach_id,
               context_summary,
               source_type,
               source_url
        FROM   outreach.blog
        WHERE  context_summary IS NOT NULL
          AND  context_summary <> ''
        ORDER BY outreach_id
        {limit_clause}
    """)

    results: Dict[str, List[Tuple]] = {code: [] for code in SIGNALS}
    processed = 0
    classified = 0
    skipped = 0

    while True:
        rows = cur.fetchmany(batch_size)
        if not rows:
            break

        for row in rows:
            outreach_id = str(row["outreach_id"])
            processed += 1

            if outreach_id in already_done:
                skipped += 1
                continue

            text = row["context_summary"] or ""
            detections = classify_text(text)

            for signal_code, confidence, matched_keywords in detections:
                if signal_code not in signal_filter:
                    continue
                classified += 1
                payload = {
                    "confidence": round(confidence, 3),
                    "matched_keywords": matched_keywords[:5],  # cap for payload size
                    "source_type": row["source_type"],
                    "source_url": row["source_url"],
                    "text_length": len(text),
                    "source_table": "outreach.blog",
                    "detected_by": signal_code,
                }
                results[signal_code].append((
                    row["outreach_id"],
                    SIGNALS[signal_code]["magnitude"],
                    payload,
                ))

        log.info("  Processed: %d | Classified: %d | Skipped (already done): %d",
                 processed, classified, skipped)

    log.info("  Total processed: %d | Total signals: %d | Skipped: %d",
             processed, classified, skipped)
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
                "[DRY-RUN] %s | %s | outreach_id=%s | confidence=%.2f",
                signal_code, signal_name, outreach_id,
                signal_value.get("confidence", 0),
            )
            written += 1
            continue

        cur.execute("""
            INSERT INTO outreach.signal_output
                (outreach_id, signal_code, signal_name, signal_source,
                 signal_value, magnitude, expires_at, correlation_id, run_month)
            VALUES
                (%(outreach_id)s, %(signal_code)s, %(signal_name)s, 'blog',
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
    p = argparse.ArgumentParser(description="Blog Dumb Worker — signal detection")
    p.add_argument("--dry-run", action="store_true",
                   help="Print signals without writing to DB")
    p.add_argument("--month", metavar="YYYY-MM",
                   help="Override run month (default: current month)")
    p.add_argument("--signal", metavar="B-NN",
                   help="Run only a specific signal (e.g. B-04)")
    p.add_argument("--batch-size", type=int, default=500, metavar="N",
                   help="Rows to fetch per batch (default: 500)")
    p.add_argument("--limit", type=int, default=None, metavar="N",
                   help="Cap total records processed (for testing)")
    p.add_argument("--fetch", action="store_true",
                   help="[FUTURE] Live HTTP fetch mode — not implemented in v1")
    return p.parse_args()


def main():
    args = parse_args()

    if args.fetch:
        log.error("--fetch is not implemented in v1. "
                  "v1 classifies outreach.blog.context_summary only.")
        sys.exit(1)

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
    log.info("Blog Dumb Worker starting")
    log.info("  run_month      = %s", run_month)
    log.info("  correlation_id = %s", correlation_id)
    log.info("  dry_run        = %s", args.dry_run)
    log.info("  batch_size     = %d", args.batch_size)
    if args.limit:
        log.info("  limit          = %d", args.limit)
    if args.signal:
        log.info("  signal filter  = %s", args.signal)

    if args.signal and args.signal not in SIGNALS:
        log.error("Unknown signal code: %s. Valid: %s", args.signal, list(SIGNALS.keys()))
        sys.exit(1)

    signal_filter: Set[str] = {args.signal} if args.signal else set(SIGNALS.keys())

    try:
        conn = get_connection()
        conn.autocommit = False
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    except Exception as e:
        log.error("DB connection failed: %s", e)
        sys.exit(1)

    totals: Dict[str, int] = {code: 0 for code in SIGNALS}

    try:
        log.info("Classifying outreach.blog context_summary records...")
        all_detections = detect_blog_signals(
            cur, run_month, signal_filter, args.batch_size, args.limit
        )

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
    print(f"  Blog Dumb Worker — {run_month}{'  [DRY-RUN]' if args.dry_run else ''}")
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
