"""
DOL Reverse Derivation Pressure Test

Tests the hypothesis: If DOL is complete (EIN matched + filing_present),
can we DERIVE Company Target and Blog completion?

This is a READ-ONLY analysis to validate data relationships.

Queries:
1. DOL-complete records with EINs that have domains in ein_urls
2. DOL-complete companies MISSING Company Target completion
3. DOL-complete but CT-incomplete where EIN provides domain
4. DOL-complete records that can derive Blog URLs via domain

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


def run_pressure_test():
    """Execute all four pressure test queries"""

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

    results: Dict[str, int] = {}

    try:
        print("=" * 80)
        print("DOL REVERSE DERIVATION PRESSURE TEST")
        print("=" * 80)
        print()

        # Query 1: DOL-complete with domains
        print("[Query 1] DOL-complete records with EINs that have domains in ein_urls")
        print("-" * 80)
        query1 = """
        SELECT COUNT(*)
        FROM outreach.dol d
        JOIN dol.ein_urls eu ON d.ein = eu.ein
        WHERE d.filing_present = TRUE
          AND eu.domain IS NOT NULL;
        """
        cursor.execute(query1)
        results['dol_complete_with_domain'] = cursor.fetchone()[0]
        print(f"Result: {results['dol_complete_with_domain']:,} records")
        print()

        # Query 2: DOL-complete missing CT completion
        print("[Query 2] DOL-complete companies MISSING Company Target completion")
        print("-" * 80)
        query2 = """
        SELECT COUNT(*)
        FROM outreach.dol d
        JOIN outreach.company_target ct ON d.outreach_id = ct.outreach_id
        WHERE d.filing_present = TRUE
          AND d.ein IS NOT NULL
          AND (ct.email_method IS NULL OR ct.execution_status != 'ready');
        """
        cursor.execute(query2)
        results['dol_complete_ct_incomplete'] = cursor.fetchone()[0]
        print(f"Result: {results['dol_complete_ct_incomplete']:,} records")
        print()

        # Query 3: EIN-derived domain rescue potential
        print("[Query 3] DOL-complete but CT-incomplete where EIN provides domain")
        print("-" * 80)
        query3 = """
        SELECT COUNT(*)
        FROM outreach.dol d
        JOIN outreach.company_target ct ON d.outreach_id = ct.outreach_id
        JOIN dol.ein_urls eu ON d.ein = eu.ein
        WHERE d.filing_present = TRUE
          AND (ct.email_method IS NULL OR ct.execution_status != 'ready')
          AND eu.domain IS NOT NULL;
        """
        cursor.execute(query3)
        results['ein_domain_rescue_potential'] = cursor.fetchone()[0]
        print(f"Result: {results['ein_domain_rescue_potential']:,} records")
        print()

        # Query 4: Blog URL derivation potential
        print("[Query 4] DOL-complete records that can derive Blog URLs via domain")
        print("-" * 80)
        query4 = """
        SELECT COUNT(DISTINCT d.outreach_id)
        FROM outreach.dol d
        JOIN outreach.outreach o ON d.outreach_id = o.outreach_id
        JOIN company.company_master cm ON LOWER(o.domain) = LOWER(
            REPLACE(REPLACE(REPLACE(cm.website_url, 'http://', ''), 'https://', ''), 'www.', '')
        )
        JOIN company.company_source_urls csu ON cm.company_unique_id = csu.company_unique_id
        WHERE d.filing_present = TRUE
          AND csu.source_type IN ('about_page', 'press_page');
        """
        cursor.execute(query4)
        results['blog_url_derivation_potential'] = cursor.fetchone()[0]
        print(f"Result: {results['blog_url_derivation_potential']:,} records")
        print()

        # Summary Analysis
        print("=" * 80)
        print("ANALYSIS SUMMARY")
        print("=" * 80)
        print()

        total_dol_complete = results['dol_complete_with_domain']
        ct_incomplete = results['dol_complete_ct_incomplete']
        ein_rescue = results['ein_domain_rescue_potential']
        blog_derivation = results['blog_url_derivation_potential']

        print(f"Total DOL-complete with domains:     {total_dol_complete:>10,}")
        print(f"Missing Company Target completion:   {ct_incomplete:>10,}")
        print()

        if ct_incomplete > 0:
            rescue_pct = (ein_rescue / ct_incomplete) * 100
            print(f"Can rescue via EIN -> domain:        {ein_rescue:>10,} ({rescue_pct:.1f}%)")
        else:
            print(f"Can rescue via EIN -> domain:        {ein_rescue:>10,} (N/A)")

        print()
        print(f"Can derive Blog URLs via domain:     {blog_derivation:>10,}")
        print()

        # Verdict
        print("=" * 80)
        print("VERDICT")
        print("=" * 80)
        print()

        if ein_rescue > 0:
            print("HYPOTHESIS CONFIRMED: DOL completion CAN enable reverse derivation")
            print(f"   - {ein_rescue:,} companies have DOL-provided domains that could rescue CT")
            print(f"   - {blog_derivation:,} companies could derive Blog URLs from domain")
            print()
            print("IMPLICATIONS:")
            print("  1. DOL Hub could publish domain to Company Target via spoke")
            print("  2. Company Target could accept domain updates from DOL")
            print("  3. Blog could subscribe to domain from either CT or DOL")
            print()
            print("ARCHITECTURE QUESTION:")
            print("  Should DOL -> CT domain flow be BIDIRECTIONAL spoke or waterfall override?")
        else:
            print("HYPOTHESIS REJECTED: No rescue potential found")
            print("   - DOL-complete companies without CT are missing domains in ein_urls")

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
    run_pressure_test()
