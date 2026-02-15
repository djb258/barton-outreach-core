#!/usr/bin/env python3
"""
Check DOL/EIN coverage for guessed email pattern companies.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_neon_connection():
    """Establish connection to Neon PostgreSQL."""
    return psycopg2.connect(
        host=os.getenv("NEON_HOST"),
        database=os.getenv("NEON_DATABASE"),
        user=os.getenv("NEON_USER"),
        password=os.getenv("NEON_PASSWORD"),
        sslmode="require"
    )

def main():
    """Check DOL coverage for guessed companies."""

    conn = get_neon_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("\n" + "="*80)
    print("DOL/EIN COVERAGE FOR GUESSED EMAIL PATTERN COMPANIES")
    print("="*80)

    # Overall statistics
    query1 = """
    WITH guessed_companies AS (
        SELECT o.outreach_id, o.domain
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
        LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
        WHERE ct.email_method IS NOT NULL
          AND hc.domain IS NULL
    )
    SELECT
        COUNT(*) AS total_guessed,
        COUNT(d.ein) AS has_ein,
        COUNT(*) FILTER (WHERE d.filing_present = TRUE) AS has_dol_filing,
        COUNT(*) - COUNT(d.ein) AS no_ein
    FROM guessed_companies gc
    LEFT JOIN outreach.dol d ON gc.outreach_id = d.outreach_id;
    """

    cur.execute(query1)
    result = cur.fetchone()

    print("\nOVERALL STATISTICS:")
    print("-" * 80)
    print(f"Total Guessed Companies:        {result['total_guessed']:,}")
    print(f"Has EIN:                        {result['has_ein']:,} ({result['has_ein']/result['total_guessed']*100:.1f}%)")
    print(f"Has DOL Filing:                 {result['has_dol_filing']:,} ({result['has_dol_filing']/result['total_guessed']*100:.1f}%)")
    print(f"No EIN:                         {result['no_ein']:,} ({result['no_ein']/result['total_guessed']*100:.1f}%)")

    # Breakdown by DOL status
    query2 = """
    WITH guessed_companies AS (
        SELECT o.outreach_id, o.domain
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
        LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
        WHERE ct.email_method IS NOT NULL
          AND hc.domain IS NULL
    )
    SELECT
        CASE
            WHEN d.ein IS NOT NULL AND d.filing_present = TRUE THEN 'Has EIN + DOL Filing'
            WHEN d.ein IS NOT NULL THEN 'Has EIN only'
            ELSE 'No DOL data'
        END AS dol_status,
        COUNT(*) AS count
    FROM guessed_companies gc
    LEFT JOIN outreach.dol d ON gc.outreach_id = d.outreach_id
    GROUP BY 1
    ORDER BY 2 DESC;
    """

    cur.execute(query2)
    breakdown = cur.fetchall()

    print("\nDOL DATA BREAKDOWN:")
    print("-" * 80)
    print(f"{'Status':<30} {'Count':>10} {'Percentage':>12}")
    print("-" * 80)

    total = sum(row['count'] for row in breakdown)
    for row in breakdown:
        pct = (row['count'] / total * 100) if total > 0 else 0
        print(f"{row['dol_status']:<30} {row['count']:>10,} {pct:>11.1f}%")

    print("="*80)
    print(f"\nKEY INSIGHT: {result['has_ein']:,} of {result['total_guessed']:,} guessed companies have DOL/EIN data available")
    print(f"This represents a {result['has_ein']/result['total_guessed']*100:.1f}% fallback enrichment opportunity!")
    print("="*80 + "\n")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
