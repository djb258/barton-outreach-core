"""
CT Postal Code Repair via DOL Evidence.

Reads repair candidates from outreach.v_ct_zip_repair_candidates (DOL Form 5500
sponsor ZIPs) and updates outreach.company_target.postal_code for companies
missing ZIP data.

Doctrine: CT is the sole ZIP authority. DOL ZIPs are evidence, not authority.
ADR: docs/adr/ADR-CT-ZIP-REPAIR-VIA-DOL-EVIDENCE.md

Usage:
    doppler run -- python scripts/ct_repair_postal_code_from_dol.py
    doppler run -- python scripts/ct_repair_postal_code_from_dol.py --apply
"""

import argparse
import os
import sys
import time

import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def get_connection():
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        dbname=os.environ["NEON_DATABASE"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
    )


def main():
    parser = argparse.ArgumentParser(
        description="CT postal_code repair from DOL Form 5500 evidence"
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Apply repairs (default: dry-run only)"
    )
    parser.add_argument(
        "--min-confidence", type=int, default=0,
        help="Minimum confidence score to apply (default: 0 = all candidates)"
    )
    args = parser.parse_args()

    conn = get_connection()
    cur = conn.cursor()

    # ================================================================
    # Baseline: CT postal_code state BEFORE repair
    # ================================================================
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(CASE WHEN postal_code IS NOT NULL
                        AND TRIM(postal_code) != '' THEN 1 END) AS has_zip,
            COUNT(CASE WHEN postal_code IS NULL
                        OR TRIM(postal_code) = '' THEN 1 END) AS missing
        FROM outreach.company_target
    """)
    total, has_zip, missing = cur.fetchone()

    print(f"{'='*60}")
    print(f"  CT Postal Code Repair — DOL Evidence")
    print(f"{'='*60}")
    print(f"\n  BEFORE:")
    print(f"    CT total:        {total:,}")
    print(f"    With postal_code: {has_zip:,} ({100*has_zip/total:.1f}%)")
    print(f"    Missing:         {missing:,} ({100*missing/total:.1f}%)")

    # ================================================================
    # Load repair candidates
    # ================================================================
    cur.execute("""
        SELECT outreach_id, proposed_postal_code, dol_city, dol_state,
               confidence_score, evidence_summary
        FROM outreach.v_ct_zip_repair_candidates
        WHERE confidence_score >= %s
        ORDER BY confidence_score DESC, outreach_id
    """, (args.min_confidence,))
    candidates = cur.fetchall()

    print(f"\n  Repair candidates: {len(candidates):,}")
    if args.min_confidence > 0:
        print(f"  (min confidence: {args.min_confidence})")

    if not candidates:
        print("\n  No candidates found. CT postal_code is complete for DOL-linked companies.")
        conn.close()
        return

    # ================================================================
    # State breakdown
    # ================================================================
    states = {}
    confidence_tiers = {"high (6+)": 0, "medium (4-5)": 0, "low (1-3)": 0}
    for r in candidates:
        st = r[3] or "UNKNOWN"
        states[st] = states.get(st, 0) + 1
        score = r[4]
        if score >= 6:
            confidence_tiers["high (6+)"] += 1
        elif score >= 4:
            confidence_tiers["medium (4-5)"] += 1
        else:
            confidence_tiers["low (1-3)"] += 1

    print(f"\n  By state:")
    for st, cnt in sorted(states.items(), key=lambda x: -x[1])[:15]:
        print(f"    {st}: {cnt:,}")
    if len(states) > 15:
        print(f"    ... and {len(states) - 15} more states")

    print(f"\n  By confidence:")
    for tier, cnt in confidence_tiers.items():
        print(f"    {tier}: {cnt:,}")

    print(f"\n  Sample candidates:")
    for r in candidates[:10]:
        print(f"    {r[1]} | {r[3] or '??':>2s} | conf={r[4]:>2d} | {r[5]}")

    # ================================================================
    # Dry run vs apply
    # ================================================================
    if not args.apply:
        print(f"\n  [DRY RUN] Would repair {len(candidates):,} companies.")
        print(f"  Post-repair projection: {has_zip + len(candidates):,} / {total:,} "
              f"({100*(has_zip + len(candidates))/total:.1f}%)")
        print(f"\n  To apply: add --apply flag")
        conn.close()
        return

    # ================================================================
    # Apply repairs — single bulk UPDATE via view join
    # ================================================================
    print(f"\n  Applying repairs (bulk UPDATE)...")
    start = time.time()

    cur.execute("""
        UPDATE outreach.company_target ct
        SET postal_code = rc.proposed_postal_code,
            city = COALESCE(NULLIF(TRIM(ct.city), ''), rc.dol_city),
            state = COALESCE(NULLIF(TRIM(ct.state), ''), rc.dol_state),
            postal_code_source = 'DOL_5500',
            postal_code_updated_at = NOW()
        FROM outreach.v_ct_zip_repair_candidates rc
        WHERE rc.outreach_id = ct.outreach_id
          AND rc.confidence_score >= %s
          AND (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
    """, (args.min_confidence,))

    applied = cur.rowcount
    conn.commit()
    elapsed = time.time() - start

    # ================================================================
    # Post-repair verification
    # ================================================================
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(CASE WHEN postal_code IS NOT NULL
                        AND TRIM(postal_code) != '' THEN 1 END) AS has_zip
        FROM outreach.company_target
    """)
    post_total, post_has_zip = cur.fetchone()

    print(f"\n  AFTER:")
    print(f"    Applied:          {applied:,}")
    print(f"    With postal_code: {post_has_zip:,} ({100*post_has_zip/post_total:.1f}%)")
    print(f"    Improvement:      +{post_has_zip - has_zip:,} companies")
    print(f"    Time:             {elapsed:.1f}s")

    # Source breakdown
    cur.execute("""
        SELECT postal_code_source, COUNT(*)
        FROM outreach.company_target
        WHERE postal_code_source IS NOT NULL
        GROUP BY postal_code_source
        ORDER BY COUNT(*) DESC
    """)
    print(f"\n  By source:")
    for r in cur.fetchall():
        print(f"    {r[0]}: {r[1]:,}")

    conn.close()
    print(f"\n{'='*60}")
    print(f"  Done.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
