"""
Verify the exact count of 12,136 companies and understand the data.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from tabulate import tabulate

def main():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment")

    conn = psycopg2.connect(database_url)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Verify the exact count
    query1 = """
    SELECT COUNT(DISTINCT o.outreach_id) as total_pattern_less_companies
    FROM outreach.outreach o
    JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
    WHERE ct.email_method IS NULL
    AND NOT EXISTS (
        SELECT 1 FROM people.company_slot cs
        WHERE cs.outreach_id = o.outreach_id AND cs.is_filled = true
    );
    """
    cursor.execute(query1)
    result1 = cursor.fetchone()
    print(f"\n{'='*80}")
    print("VERIFICATION: Total Pattern-less Companies")
    print('='*80)
    print(f"Total companies with NO email_method and NO filled slots: {result1['total_pattern_less_companies']:,}")

    # Now break down by Hunter data availability
    query2 = """
    WITH pattern_less AS (
        SELECT DISTINCT o.outreach_id, o.domain
        FROM outreach.outreach o
        JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
        WHERE ct.email_method IS NULL
        AND NOT EXISTS (
            SELECT 1 FROM people.company_slot cs
            WHERE cs.outreach_id = o.outreach_id AND cs.is_filled = true
        )
    )
    SELECT
        COUNT(DISTINCT pl.outreach_id) FILTER (WHERE hc.domain IS NOT NULL) as has_hunter_company,
        COUNT(DISTINCT pl.outreach_id) FILTER (WHERE hc.domain IS NULL) as no_hunter_company
    FROM pattern_less pl
    LEFT JOIN enrichment.hunter_company hc ON LOWER(pl.domain) = LOWER(hc.domain);
    """
    cursor.execute(query2)
    result2 = cursor.fetchone()
    print(f"\n{'='*80}")
    print("Hunter Data Breakdown")
    print('='*80)
    print(f"Companies WITH hunter_company match: {result2['has_hunter_company']:,}")
    print(f"Companies WITHOUT hunter_company match: {result2['no_hunter_company']:,}")
    print(f"Total: {result2['has_hunter_company'] + result2['no_hunter_company']:,}")

    # Check if Hunter has patterns for these companies
    query3 = """
    WITH pattern_less AS (
        SELECT DISTINCT o.outreach_id, o.domain
        FROM outreach.outreach o
        JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
        WHERE ct.email_method IS NULL
        AND NOT EXISTS (
            SELECT 1 FROM people.company_slot cs
            WHERE cs.outreach_id = o.outreach_id AND cs.is_filled = true
        )
    )
    SELECT
        COUNT(DISTINCT pl.outreach_id) FILTER (WHERE hc.email_pattern IS NOT NULL AND hc.email_pattern != '') as has_pattern_in_hunter,
        COUNT(DISTINCT pl.outreach_id) FILTER (WHERE hc.email_pattern IS NULL OR hc.email_pattern = '') as no_pattern_in_hunter,
        COUNT(DISTINCT pl.outreach_id) FILTER (WHERE hc.domain IS NULL) as no_hunter_record
    FROM pattern_less pl
    LEFT JOIN enrichment.hunter_company hc ON LOWER(pl.domain) = LOWER(hc.domain);
    """
    cursor.execute(query3)
    result3 = cursor.fetchone()
    print(f"\n{'='*80}")
    print("Pattern Availability in hunter_company")
    print('='*80)
    print(f"Companies where hunter_company HAS email_pattern: {result3['has_pattern_in_hunter']:,}")
    print(f"Companies where hunter_company has NO email_pattern: {result3['no_pattern_in_hunter']:,}")
    print(f"Companies with NO hunter_company record: {result3['no_hunter_record']:,}")
    print(f"Total: {result3['has_pattern_in_hunter'] + result3['no_pattern_in_hunter'] + result3['no_hunter_record']:,}")

    # Sample of companies where Hunter HAS patterns but company_target doesn't
    query4 = """
    WITH pattern_less AS (
        SELECT DISTINCT o.outreach_id, o.domain
        FROM outreach.outreach o
        JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
        WHERE ct.email_method IS NULL
        AND NOT EXISTS (
            SELECT 1 FROM people.company_slot cs
            WHERE cs.outreach_id = o.outreach_id AND cs.is_filled = true
        )
    )
    SELECT
        pl.outreach_id,
        pl.domain,
        hc.email_pattern,
        hc.organization,
        hc.enriched_at
    FROM pattern_less pl
    JOIN enrichment.hunter_company hc ON LOWER(pl.domain) = LOWER(hc.domain)
    WHERE hc.email_pattern IS NOT NULL AND hc.email_pattern != ''
    LIMIT 20;
    """
    cursor.execute(query4)
    results4 = cursor.fetchall()
    print(f"\n{'='*80}")
    print("Sample: Companies Where Hunter HAS Patterns (but company_target doesn't)")
    print('='*80)
    if results4:
        headers = results4[0].keys()
        rows = [list(row.values()) for row in results4]
        print(tabulate(rows, headers=headers, tablefmt='grid'))
    else:
        print("No results found.")

    # Check hunter_contact for patterns
    query5 = """
    WITH pattern_less AS (
        SELECT DISTINCT o.outreach_id, o.domain
        FROM outreach.outreach o
        JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
        WHERE ct.email_method IS NULL
        AND NOT EXISTS (
            SELECT 1 FROM people.company_slot cs
            WHERE cs.outreach_id = o.outreach_id AND cs.is_filled = true
        )
    )
    SELECT COUNT(DISTINCT pl.outreach_id) as has_hunter_contacts
    FROM pattern_less pl
    WHERE EXISTS (
        SELECT 1 FROM enrichment.hunter_contact hcont
        WHERE LOWER(pl.domain) = LOWER(hcont.domain)
        AND hcont.email IS NOT NULL AND hcont.email != ''
    );
    """
    cursor.execute(query5)
    result5 = cursor.fetchone()
    print(f"\n{'='*80}")
    print("Hunter Contact Analysis")
    print('='*80)
    print(f"Companies with actual hunter_contact emails: {result5['has_hunter_contacts']:,}")

    cursor.close()
    conn.close()

    # Final summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print('='*80)
    print(f"\nTotal companies with NO email_method and NO filled slots: {result1['total_pattern_less_companies']:,}")
    print(f"\nBreakdown:")
    print(f"  1. Companies with hunter_company record: {result2['has_hunter_company']:,}")
    print(f"     - With email_pattern in hunter_company: {result3['has_pattern_in_hunter']:,}")
    print(f"     - Without email_pattern in hunter_company: {result3['no_pattern_in_hunter']:,}")
    print(f"  2. Companies WITHOUT hunter_company record: {result2['no_hunter_company']:,}")
    print(f"\nConclusion:")
    if result3['has_pattern_in_hunter'] > 0:
        print(f"  - {result3['has_pattern_in_hunter']:,} companies CAN be backfilled from hunter_company.email_pattern")
        print(f"  - This represents {(result3['has_pattern_in_hunter'] / result1['total_pattern_less_companies'] * 100):.1f}% recovery potential")
    else:
        print(f"  - Hunter has records but NO email_pattern for these {result2['has_hunter_company']:,} companies")
        print(f"  - These are likely small businesses or domains Hunter couldn't crack")
        print(f"  - The {result2['no_hunter_company']:,} companies without Hunter records need alternative enrichment")

if __name__ == "__main__":
    main()
