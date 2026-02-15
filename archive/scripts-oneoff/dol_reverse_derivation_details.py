"""
DOL Reverse Derivation - Deep Dive Analysis

Follow-up queries to understand:
- Quality of DOL-derived domains
- Overlap between CT and DOL domain sources
- Blog URL derivation potential breakdown
- Waterfall execution status implications

Author: Claude Code
Date: 2026-02-06
Status: Read-Only Analysis
"""

import sys
import os
import io
from typing import Dict

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2


def run_deep_dive():
    """Execute deep dive analysis queries"""

    # Build connection string from environment
    host = os.getenv('NEON_HOST')
    database = os.getenv('NEON_DATABASE')
    user = os.getenv('NEON_USER')
    password = os.getenv('NEON_PASSWORD')

    if not all([host, database, user, password]):
        raise ValueError("Missing required Neon connection environment variables")

    conn_string = f"postgresql://{user}:{password}@{host}/{database}?sslmode=require"
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()

    try:
        print("=" * 80)
        print("DOL REVERSE DERIVATION - DEEP DIVE ANALYSIS")
        print("=" * 80)
        print()

        # Query 1: Domain source comparison
        print("[Query 1] Domain source comparison - Outreach.domain vs DOL EIN domain")
        print("-" * 80)
        query1 = """
        SELECT
            COUNT(*) FILTER (WHERE o.domain IS NOT NULL) as outreach_has_domain,
            COUNT(*) FILTER (WHERE eu.domain IS NOT NULL) as dol_has_domain,
            COUNT(*) FILTER (WHERE o.domain IS NOT NULL AND eu.domain IS NOT NULL) as both_have_domain,
            COUNT(*) FILTER (WHERE o.domain IS NULL AND eu.domain IS NOT NULL) as only_dol_has_domain,
            COUNT(*) FILTER (WHERE o.domain IS NOT NULL AND eu.domain IS NULL) as only_outreach_has_domain,
            COUNT(*) FILTER (WHERE
                o.domain IS NOT NULL
                AND eu.domain IS NOT NULL
                AND LOWER(o.domain) = LOWER(eu.domain)
            ) as domains_match,
            COUNT(*) FILTER (WHERE
                o.domain IS NOT NULL
                AND eu.domain IS NOT NULL
                AND LOWER(o.domain) != LOWER(eu.domain)
            ) as domains_differ
        FROM outreach.dol d
        JOIN outreach.outreach o ON d.outreach_id = o.outreach_id
        LEFT JOIN dol.ein_urls eu ON d.ein = eu.ein
        WHERE d.filing_present = TRUE;
        """
        cursor.execute(query1)
        row = cursor.fetchone()
        print(f"  Outreach has domain:     {row[0]:>10,}")
        print(f"  DOL has domain:          {row[1]:>10,}")
        print(f"  Both have domain:        {row[2]:>10,}")
        print(f"  Only DOL has domain:     {row[3]:>10,}  <- RESCUE POTENTIAL")
        print(f"  Only Outreach has domain:{row[4]:>10,}")
        print(f"  Domains match:           {row[5]:>10,}")
        print(f"  Domains differ:          {row[6]:>10,}  <- CONFLICT!")
        print()

        # Query 2: CT execution status breakdown
        print("[Query 2] CT execution status for DOL-complete records")
        print("-" * 80)
        query2 = """
        SELECT
            ct.execution_status,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
        FROM outreach.dol d
        JOIN outreach.company_target ct ON d.outreach_id = ct.outreach_id
        WHERE d.filing_present = TRUE
        GROUP BY ct.execution_status
        ORDER BY count DESC;
        """
        cursor.execute(query2)
        rows = cursor.fetchall()
        for status, count, pct in rows:
            status_str = status if status else "(NULL)"
            print(f"  {status_str:20} {count:>10,}  ({pct:>5.1f}%)")
        print()

        # Query 3: Email method breakdown
        print("[Query 3] Email method for DOL-complete records")
        print("-" * 80)
        query3 = """
        SELECT
            ct.email_method,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
        FROM outreach.dol d
        JOIN outreach.company_target ct ON d.outreach_id = ct.outreach_id
        WHERE d.filing_present = TRUE
        GROUP BY ct.email_method
        ORDER BY count DESC;
        """
        cursor.execute(query3)
        rows = cursor.fetchall()
        for method, count, pct in rows:
            method_str = method if method else "(NULL)"
            print(f"  {method_str:20} {count:>10,}  ({pct:>5.1f}%)")
        print()

        # Query 4: Blog coverage for DOL+CT complete
        print("[Query 4] Blog coverage when both DOL and CT are complete")
        print("-" * 80)
        query4 = """
        SELECT
            COUNT(DISTINCT d.outreach_id) as total_dol_ct_complete,
            COUNT(DISTINCT b.outreach_id) as has_blog_record,
            COUNT(DISTINCT CASE WHEN b.has_about_page THEN b.outreach_id END) as has_about_page,
            COUNT(DISTINCT CASE WHEN b.has_press_page THEN b.outreach_id END) as has_press_page,
            COUNT(DISTINCT CASE WHEN b.has_about_page OR b.has_press_page THEN b.outreach_id END) as has_any_page
        FROM outreach.dol d
        JOIN outreach.company_target ct ON d.outreach_id = ct.outreach_id
        LEFT JOIN outreach.blog b ON d.outreach_id = b.outreach_id
        WHERE d.filing_present = TRUE
          AND ct.email_method IS NOT NULL
          AND ct.execution_status = 'ready';
        """
        cursor.execute(query4)
        row = cursor.fetchone()
        total = row[0]
        has_blog = row[1]
        has_about = row[2]
        has_press = row[3]
        has_any = row[4]

        print(f"  Total DOL+CT complete:      {total:>10,}")
        print(f"  Has blog record:            {has_blog:>10,}  ({100.0 * has_blog / total if total > 0 else 0:.1f}%)")
        print(f"  Has about page:             {has_about:>10,}  ({100.0 * has_about / total if total > 0 else 0:.1f}%)")
        print(f"  Has press page:             {has_press:>10,}  ({100.0 * has_press / total if total > 0 else 0:.1f}%)")
        print(f"  Has any page:               {has_any:>10,}  ({100.0 * has_any / total if total > 0 else 0:.1f}%)")
        print()

        # Query 5: Sample conflicts (domains differ)
        print("[Query 5] Sample records where Outreach and DOL domains differ")
        print("-" * 80)
        query5 = """
        SELECT
            d.outreach_id,
            o.domain as outreach_domain,
            eu.domain as dol_domain,
            d.ein
        FROM outreach.dol d
        JOIN outreach.outreach o ON d.outreach_id = o.outreach_id
        JOIN dol.ein_urls eu ON d.ein = eu.ein
        WHERE d.filing_present = TRUE
          AND o.domain IS NOT NULL
          AND eu.domain IS NOT NULL
          AND LOWER(o.domain) != LOWER(eu.domain)
        LIMIT 10;
        """
        cursor.execute(query5)
        rows = cursor.fetchall()
        if rows:
            print("  Sample conflicts (showing first 10):")
            for oid, outreach_domain, dol_domain, ein in rows:
                oid_str = str(oid)
                print(f"    {oid_str[:30]:30} | Outreach: {outreach_domain:25} | DOL: {dol_domain:25} | EIN: {ein}")
        else:
            print("  No conflicts found")
        print()

        # Summary
        print("=" * 80)
        print("KEY FINDINGS")
        print("=" * 80)
        print()
        print("1. DOMAIN SOURCE CONFLICT:")
        print("   - If domains differ between Outreach and DOL, which is authoritative?")
        print("   - Propose: EIN-derived domain (DOL) should be GROUND TRUTH")
        print()
        print("2. CT INCOMPLETE RESCUE:")
        print("   - 53,530 companies have DOL domains but incomplete CT")
        print("   - DOL could rescue CT via bidirectional spoke")
        print()
        print("3. BLOG DERIVATION:")
        print("   - Blog URLs can be constructed from domain via company_source_urls")
        print("   - Both CT and DOL can provide domain to Blog")
        print()
        print("4. WATERFALL IMPLICATION:")
        print("   - Current: CT -> DOL -> People -> Blog")
        print("   - Proposed: Allow DOL -> CT reverse flow for domain rescue")
        print("   - Mechanism: Bidirectional spoke (dol-target)")
        print()
        print("=" * 80)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    run_deep_dive()
