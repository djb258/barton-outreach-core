#!/usr/bin/env python3
"""
Sitemap Cross-Reference Analysis
==================================
Run AFTER scan_sitemaps.py completes to classify the no-sitemap companies
by cross-referencing with DOL filings, slot fills, and email methods.

Buckets:
  A. No sitemap + No DOL + No slots filled  → likely dead/phantom → exclusion candidate
  B. No sitemap + No DOL + Has slots         → real but minimal data
  C. No sitemap + Has DOL + No slots         → real company, needs people enrichment
  D. No sitemap + Has DOL + Has slots        → real company, just no sitemap (homepage/probe)
  E. Not yet scanned                         → scan still running

Also exports bucket A (exclusion candidates) to CSV for review.

Usage:
    doppler run -- python scripts/sitemap_crossref_analysis.py
    doppler run -- python scripts/sitemap_crossref_analysis.py --export
"""

import os
import sys
import csv
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    host = os.environ.get('NEON_HOST')
    password = os.environ.get('NEON_PASSWORD')
    if not host or not password:
        raise EnvironmentError("NEON_HOST and NEON_PASSWORD must be set. Run with: doppler run -- python ...")
    return psycopg2.connect(
        host=host, port=5432,
        database=os.environ.get('NEON_DATABASE', 'Marketing DB'),
        user=os.environ.get('NEON_USER', 'Marketing DB_owner'),
        password=password, sslmode='require',
    )


def run_analysis(export: bool = False):
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print('=' * 70)
    print('SITEMAP CROSS-REFERENCE ANALYSIS')
    print('=' * 70)
    print()

    # ── 1. Scan completion status ──
    cur.execute("""
        SELECT
            (SELECT COUNT(*) FROM outreach.outreach WHERE domain IS NOT NULL AND domain != '') as total_outreach,
            (SELECT COUNT(*) FROM outreach.sitemap_discovery) as total_scanned,
            (SELECT COUNT(*) FROM outreach.sitemap_discovery WHERE has_sitemap = TRUE) as with_sitemap,
            (SELECT COUNT(*) FROM outreach.sitemap_discovery WHERE has_sitemap = FALSE) as without_sitemap
    """)
    scan = cur.fetchone()

    remaining = scan['total_outreach'] - scan['total_scanned']
    pct_scanned = 100 * scan['total_scanned'] / max(1, scan['total_outreach'])

    print(f"SCAN STATUS: {scan['total_scanned']:,} / {scan['total_outreach']:,} ({pct_scanned:.0f}%)")
    print(f"  With sitemap:    {scan['with_sitemap']:,}")
    print(f"  Without sitemap: {scan['without_sitemap']:,}")
    if remaining > 0:
        print(f"  Not yet scanned: {remaining:,}")
    print()

    # ── 2. Four-bucket breakdown for no-sitemap companies ──
    cur.execute("""
        WITH no_sitemap AS (
            SELECT sd.outreach_id, sd.domain
            FROM outreach.sitemap_discovery sd
            WHERE sd.has_sitemap = FALSE
        ),
        enrichment AS (
            SELECT
                ns.outreach_id,
                ns.domain,
                (d.outreach_id IS NOT NULL)                    as has_dol,
                d.filing_present,
                d.funding_type,
                d.renewal_month,
                ct.email_method,
                ct.industry,
                ct.state,
                ct.employees,
                COALESCE(slot_counts.filled_slots, 0)          as filled_slots,
                COALESCE(slot_counts.total_slots, 0)           as total_slots
            FROM no_sitemap ns
            LEFT JOIN outreach.dol d ON d.outreach_id = ns.outreach_id
            LEFT JOIN outreach.company_target ct ON ct.outreach_id = ns.outreach_id
            LEFT JOIN (
                SELECT outreach_id,
                       COUNT(*) FILTER (WHERE is_filled = TRUE) as filled_slots,
                       COUNT(*) as total_slots
                FROM people.company_slot
                GROUP BY outreach_id
            ) slot_counts ON slot_counts.outreach_id = ns.outreach_id
        )
        SELECT
            COUNT(*) as total_no_sitemap,
            COUNT(*) FILTER (WHERE NOT has_dol AND filled_slots = 0 AND email_method IS NULL)
                as bucket_a_dead,
            COUNT(*) FILTER (WHERE NOT has_dol AND filled_slots = 0 AND email_method IS NOT NULL)
                as bucket_a2_email_only,
            COUNT(*) FILTER (WHERE NOT has_dol AND filled_slots > 0)
                as bucket_b_no_dol_has_slots,
            COUNT(*) FILTER (WHERE has_dol AND filled_slots = 0)
                as bucket_c_has_dol_no_slots,
            COUNT(*) FILTER (WHERE has_dol AND filled_slots > 0)
                as bucket_d_has_dol_has_slots,
            COUNT(*) FILTER (WHERE has_dol)
                as total_with_dol,
            COUNT(*) FILTER (WHERE email_method IS NOT NULL)
                as total_with_email_method,
            COUNT(*) FILTER (WHERE filled_slots > 0)
                as total_with_slots
        FROM enrichment
    """)
    b = cur.fetchone()

    print('NO-SITEMAP COMPANY BREAKDOWN:')
    print(f"  Total without sitemap: {b['total_no_sitemap']:,}")
    print()
    print(f"  Bucket A  - No DOL, No slots, No email method (DEAD?):  {b['bucket_a_dead']:,}")
    print(f"  Bucket A2 - No DOL, No slots, HAS email method:         {b['bucket_a2_email_only']:,}")
    print(f"  Bucket B  - No DOL, HAS filled slots:                   {b['bucket_b_no_dol_has_slots']:,}")
    print(f"  Bucket C  - HAS DOL, No filled slots:                   {b['bucket_c_has_dol_no_slots']:,}")
    print(f"  Bucket D  - HAS DOL, HAS filled slots:                  {b['bucket_d_has_dol_has_slots']:,}")
    print()
    print(f"  Cross-enrichment signals present:")
    print(f"    With DOL filing:   {b['total_with_dol']:,}")
    print(f"    With email method: {b['total_with_email_method']:,}")
    print(f"    With filled slots: {b['total_with_slots']:,}")
    print()

    # ── 3. Same breakdown for WITH-sitemap (for comparison) ──
    cur.execute("""
        WITH has_sitemap AS (
            SELECT sd.outreach_id
            FROM outreach.sitemap_discovery sd
            WHERE sd.has_sitemap = TRUE
        )
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE d.outreach_id IS NOT NULL) as with_dol,
            COUNT(*) FILTER (WHERE ct.email_method IS NOT NULL) as with_email,
            COUNT(*) FILTER (WHERE slot_counts.filled_slots > 0) as with_slots
        FROM has_sitemap hs
        LEFT JOIN outreach.dol d ON d.outreach_id = hs.outreach_id
        LEFT JOIN outreach.company_target ct ON ct.outreach_id = hs.outreach_id
        LEFT JOIN (
            SELECT outreach_id,
                   COUNT(*) FILTER (WHERE is_filled = TRUE) as filled_slots
            FROM people.company_slot
            GROUP BY outreach_id
        ) slot_counts ON slot_counts.outreach_id = hs.outreach_id
    """)
    s = cur.fetchone()

    print('WITH-SITEMAP COMPARISON (baseline):')
    print(f"  Total with sitemap:  {s['total']:,}")
    print(f"    With DOL filing:   {s['with_dol']:,} ({100*s['with_dol']/max(1,s['total']):.0f}%)")
    print(f"    With email method: {s['with_email']:,} ({100*s['with_email']/max(1,s['total']):.0f}%)")
    print(f"    With filled slots: {s['with_slots']:,} ({100*s['with_slots']/max(1,s['total']):.0f}%)")
    print()

    # ── 4. Sitemap source breakdown (direct vs robots) ──
    cur.execute("""
        SELECT sitemap_source, COUNT(*) as cnt
        FROM outreach.sitemap_discovery
        WHERE has_sitemap = TRUE
        GROUP BY sitemap_source
        ORDER BY cnt DESC
    """)
    print('SITEMAP SOURCE:')
    for row in cur.fetchall():
        print(f"  {row['sitemap_source'] or 'unknown':10s} {row['cnt']:,}")
    print()

    # ── 5. Export bucket A (exclusion candidates) ──
    if export:
        cur.execute("""
            SELECT
                ns.outreach_id::text,
                ns.domain,
                ct.industry,
                ct.state,
                ct.employees,
                ct.email_method
            FROM outreach.sitemap_discovery ns
            LEFT JOIN outreach.company_target ct ON ct.outreach_id = ns.outreach_id
            LEFT JOIN outreach.dol d ON d.outreach_id = ns.outreach_id
            LEFT JOIN (
                SELECT outreach_id, COUNT(*) FILTER (WHERE is_filled = TRUE) as filled
                FROM people.company_slot GROUP BY outreach_id
            ) slots ON slots.outreach_id = ns.outreach_id
            WHERE ns.has_sitemap = FALSE
              AND d.outreach_id IS NULL
              AND COALESCE(slots.filled, 0) = 0
              AND ct.email_method IS NULL
            ORDER BY ns.domain
        """)
        rows = cur.fetchall()

        export_path = 'exports/no_sitemap_no_dol_no_slots_exclusion_candidates.csv'
        with open(export_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['outreach_id', 'domain', 'industry', 'state', 'employees', 'email_method'])
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

        print(f"EXPORTED: {len(rows):,} exclusion candidates → {export_path}")
        print()

    # ── 6. Summary recommendation ──
    print('=' * 70)
    print('RECOMMENDED ACTIONS')
    print('=' * 70)
    print(f"  1. Bucket A ({b['bucket_a_dead']:,}) — No sitemap, no DOL, no slots, no email.")
    print(f"     → Review for exclusion. Cross-check with company_source_urls before removing.")
    print()
    print(f"  2. Bucket A2 ({b['bucket_a2_email_only']:,}) — No sitemap, no DOL, but has email method.")
    print(f"     → Keep. Email method means CT enrichment succeeded. Use homepage/probe for URLs.")
    print()
    print(f"  3. Bucket B ({b['bucket_b_no_dol_has_slots']:,}) — No sitemap, no DOL, but has slots.")
    print(f"     → Keep. People are assigned. Use homepage/probe for URLs.")
    print()
    print(f"  4. Bucket C ({b['bucket_c_has_dol_no_slots']:,}) — Has DOL but no slots yet.")
    print(f"     → Priority for people enrichment pipeline. DOL confirms real company.")
    print()
    print(f"  5. Bucket D ({b['bucket_d_has_dol_has_slots']:,}) — Has DOL + slots, just no sitemap.")
    print(f"     → Fully enriched. Use discover_blog_urls.py (homepage + probe) for URLs.")

    cur.close()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description='Sitemap cross-reference analysis')
    parser.add_argument('--export', action='store_true', help='Export Bucket A exclusion candidates to CSV')
    args = parser.parse_args()
    run_analysis(export=args.export)


if __name__ == '__main__':
    main()
