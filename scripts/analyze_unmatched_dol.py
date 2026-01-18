#!/usr/bin/env python3
"""
Analyze Unmatched DOL Filings
==============================
Analyzes DOL Form 5500 filings that haven't been matched to company_master.
Identifies match opportunities and provides insights for improving EIN matching.

Usage:
    python scripts/analyze_unmatched_dol.py [--export] [--top N]

Options:
    --export    Export unmatched filings to CSV for review
    --top N     Show top N near-matches (default: 20)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import argparse
import csv
from datetime import datetime
from pathlib import Path

# Neon connection settings
NEON_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}


def print_section(title):
    """Print a formatted section header."""
    print()
    print('=' * 70)
    print(title)
    print('=' * 70)


def print_subsection(title):
    """Print a formatted subsection header."""
    print()
    print(f"--- {title} ---")


def analyze_unmatched_dol(export=False, top_n=20):
    """
    Analyze unmatched DOL filings and identify match opportunities.
    """
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    conn = psycopg2.connect(**NEON_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print_section("DOL FILING MATCH ANALYSIS")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # =========================================================================
    # SECTION 0: Get Target States (from company_master)
    # =========================================================================
    cur.execute('''
        SELECT DISTINCT address_state
        FROM company.company_master
        WHERE address_state IS NOT NULL
    ''')
    target_states = [r['address_state'] for r in cur.fetchall()]

    print(f"\nTarget States (from company_master): {', '.join(sorted(target_states))}")
    print(f"Only analyzing DOL filings in these {len(target_states)} states.\n")

    # =========================================================================
    # SECTION 1: Overall Statistics
    # =========================================================================
    print_section("1. OVERALL STATISTICS")

    # Total DOL filings (in target states only)
    cur.execute("""
        SELECT COUNT(*) as total FROM dol.form_5500
        WHERE spons_dfe_mail_us_state = ANY(%s)
    """, (target_states,))
    total_dol = cur.fetchone()['total']

    # Matched filings (have company_unique_id)
    cur.execute("""
        SELECT COUNT(*) as matched FROM dol.form_5500
        WHERE company_unique_id IS NOT NULL
          AND spons_dfe_mail_us_state = ANY(%s)
    """, (target_states,))
    matched_dol = cur.fetchone()['matched']

    # Unmatched filings
    unmatched_dol = total_dol - matched_dol

    # Company master stats
    cur.execute("SELECT COUNT(*) as total FROM company.company_master")
    total_companies = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) as with_ein FROM company.company_master WHERE ein IS NOT NULL")
    companies_with_ein = cur.fetchone()['with_ein']

    print(f"DOL Form 5500 Filings (in target states):")
    print(f"  Total:     {total_dol:,}")
    print(f"  Matched:   {matched_dol:,} ({100*matched_dol/total_dol:.1f}%)" if total_dol > 0 else "  Matched:   0")
    print(f"  Unmatched: {unmatched_dol:,} ({100*unmatched_dol/total_dol:.1f}%)" if total_dol > 0 else "  Unmatched: 0")
    print()
    print(f"Company Master:")
    print(f"  Total:    {total_companies:,}")
    print(f"  With EIN: {companies_with_ein:,} ({100*companies_with_ein/total_companies:.1f}%)" if total_companies > 0 else "  With EIN: 0")

    if total_dol == 0:
        print("\nNo DOL filings found in target states. Check data.")
        cur.close()
        conn.close()
        return

    # =========================================================================
    # SECTION 2: Unmatched by State (target states only)
    # =========================================================================
    print_section("2. UNMATCHED FILINGS BY STATE")

    cur.execute('''
        SELECT
            COALESCE(spons_dfe_mail_us_state, 'UNKNOWN') as state,
            COUNT(*) as unmatched_count,
            SUM(COALESCE(tot_active_partcp_cnt, 0)) as total_participants
        FROM dol.form_5500
        WHERE company_unique_id IS NULL
          AND spons_dfe_mail_us_state = ANY(%s)
        GROUP BY COALESCE(spons_dfe_mail_us_state, 'UNKNOWN')
        ORDER BY unmatched_count DESC
    ''', (target_states,))

    print(f"{'State':<10} {'Unmatched':>12} {'Participants':>15}")
    print("-" * 40)
    for row in cur.fetchall():
        print(f"{row['state']:<10} {row['unmatched_count']:>12,} {row['total_participants']:>15,}")

    # =========================================================================
    # SECTION 3: Unmatched by Participant Size
    # =========================================================================
    print_section("3. UNMATCHED BY PARTICIPANT SIZE")

    cur.execute('''
        SELECT
            CASE
                WHEN tot_active_partcp_cnt IS NULL THEN 'Unknown'
                WHEN tot_active_partcp_cnt < 100 THEN 'Small (<100)'
                WHEN tot_active_partcp_cnt < 500 THEN 'Medium (100-499)'
                WHEN tot_active_partcp_cnt < 1000 THEN 'Large (500-999)'
                WHEN tot_active_partcp_cnt < 5000 THEN 'Very Large (1K-5K)'
                ELSE 'Enterprise (5K+)'
            END as size_bucket,
            COUNT(*) as count,
            ROUND(AVG(tot_active_partcp_cnt)) as avg_participants,
            CASE
                WHEN MIN(tot_active_partcp_cnt) IS NULL THEN 6
                WHEN MAX(tot_active_partcp_cnt) < 100 THEN 1
                WHEN MAX(tot_active_partcp_cnt) < 500 THEN 2
                WHEN MAX(tot_active_partcp_cnt) < 1000 THEN 3
                WHEN MAX(tot_active_partcp_cnt) < 5000 THEN 4
                ELSE 5
            END as sort_order
        FROM dol.form_5500
        WHERE company_unique_id IS NULL
          AND spons_dfe_mail_us_state = ANY(%s)
        GROUP BY 1
        ORDER BY sort_order
    ''', (target_states,))

    print(f"{'Size Bucket':<22} {'Count':>10} {'Avg Participants':>18}")
    print("-" * 55)
    for row in cur.fetchall():
        avg = int(row['avg_participants']) if row['avg_participants'] else 0
        print(f"{row['size_bucket']:<22} {row['count']:>10,} {avg:>18,}")

    # =========================================================================
    # SECTION 4: High-Value Unmatched (Large Employers)
    # =========================================================================
    print_section("4. HIGH-VALUE UNMATCHED (500+ PARTICIPANTS)")

    cur.execute('''
        SELECT
            sponsor_dfe_name,
            sponsor_dfe_ein,
            spons_dfe_mail_us_city,
            spons_dfe_mail_us_state,
            tot_active_partcp_cnt
        FROM dol.form_5500
        WHERE company_unique_id IS NULL
          AND tot_active_partcp_cnt >= 500
          AND spons_dfe_mail_us_state = ANY(%s)
        ORDER BY tot_active_partcp_cnt DESC
        LIMIT 15
    ''', (target_states,))

    results = cur.fetchall()
    if results:
        print(f"{'Company Name':<40} {'EIN':<12} {'City/State':<20} {'Participants':>12}")
        print("-" * 90)
        for row in results:
            name = (row['sponsor_dfe_name'] or '')[:38]
            location = f"{(row['spons_dfe_mail_us_city'] or '')[:12]}, {row['spons_dfe_mail_us_state'] or ''}"
            print(f"{name:<40} {row['sponsor_dfe_ein']:<12} {location:<20} {row['tot_active_partcp_cnt'] or 0:>12,}")
    else:
        print("No large unmatched employers found.")

    # =========================================================================
    # SECTION 5: Near-Matches (Similarity 0.6-0.8)
    # =========================================================================
    print_section("5. NEAR-MATCHES (Similarity 0.6-0.8)")

    cur.execute('''
        WITH near_matches AS (
            SELECT
                d.sponsor_dfe_name as dol_name,
                d.sponsor_dfe_ein as dol_ein,
                d.spons_dfe_mail_us_state as dol_state,
                d.tot_active_partcp_cnt as participants,
                cm.company_name,
                cm.address_state,
                SIMILARITY(LOWER(d.sponsor_dfe_name), LOWER(cm.company_name)) as similarity,
                ROW_NUMBER() OVER (
                    PARTITION BY d.ack_id
                    ORDER BY SIMILARITY(LOWER(d.sponsor_dfe_name), LOWER(cm.company_name)) DESC
                ) as rn
            FROM dol.form_5500 d
            JOIN company.company_master cm
                ON d.spons_dfe_mail_us_state = cm.address_state
            WHERE d.company_unique_id IS NULL
              AND cm.ein IS NULL
              AND d.spons_dfe_mail_us_state = ANY(%s)
              AND SIMILARITY(LOWER(d.sponsor_dfe_name), LOWER(cm.company_name)) BETWEEN 0.6 AND 0.8
        )
        SELECT * FROM near_matches
        WHERE rn = 1
        ORDER BY participants DESC NULLS LAST, similarity DESC
        LIMIT %s
    ''', (target_states, top_n))

    results = cur.fetchall()
    if results:
        print(f"Potential matches with 60-80%% name similarity:")
        print()
        print(f"{'Similarity':>10} {'DOL Name':<35} {'Company Name':<35}")
        print("-" * 85)
        for row in results:
            dol_name = (row['dol_name'] or '')[:33]
            company_name = (row['company_name'] or '')[:33]
            print(f"{row['similarity']:>10.2f} {dol_name:<35} {company_name:<35}")
        print()
        print(f"Consider lowering similarity threshold from 0.8 to 0.7 to capture these.")
    else:
        print("No near-matches found in the 0.6-0.8 similarity range.")

    # =========================================================================
    # SECTION 6: Company Master by State
    # =========================================================================
    print_section("6. COMPANY MASTER COVERAGE")

    cur.execute('''
        SELECT
            address_state,
            COUNT(*) as companies,
            COUNT(ein) as with_ein
        FROM company.company_master
        WHERE address_state IS NOT NULL
        GROUP BY address_state
        ORDER BY companies DESC
    ''')

    print(f"{'State':<8} {'Companies':>12} {'With EIN':>12} {'EIN %':>10}")
    print("-" * 45)
    for row in cur.fetchall():
        pct = 100 * row['with_ein'] / row['companies'] if row['companies'] > 0 else 0
        print(f"{row['address_state']:<8} {row['companies']:>12,} {row['with_ein']:>12,} {pct:>9.1f}%")

    # =========================================================================
    # SECTION 7: Filing Year Distribution
    # =========================================================================
    print_section("7. UNMATCHED BY FILING YEAR")

    cur.execute('''
        SELECT
            COALESCE(form_year, 'Unknown') as year,
            COUNT(*) as unmatched
        FROM dol.form_5500
        WHERE company_unique_id IS NULL
          AND spons_dfe_mail_us_state = ANY(%s)
        GROUP BY COALESCE(form_year, 'Unknown')
        ORDER BY year DESC
    ''', (target_states,))

    print(f"{'Year':<12} {'Unmatched':>12}")
    print("-" * 28)
    for row in cur.fetchall():
        print(f"{row['year']:<12} {row['unmatched']:>12,}")

    # =========================================================================
    # SECTION 8: EIN Overlap Analysis (TARGET STATES ONLY)
    # =========================================================================
    print_section("8. EIN OVERLAP ANALYSIS")

    # Check for EINs in both DOL (target states) and company_master
    cur.execute('''
        SELECT COUNT(DISTINCT d.sponsor_dfe_ein) as dol_eins
        FROM dol.form_5500 d
        WHERE d.sponsor_dfe_ein IS NOT NULL
          AND d.spons_dfe_mail_us_state = ANY(%s)
    ''', (target_states,))
    total_dol_eins = cur.fetchone()['dol_eins']

    cur.execute('''
        SELECT COUNT(DISTINCT cm.ein) as company_eins
        FROM company.company_master cm
        WHERE cm.ein IS NOT NULL
    ''')
    total_company_eins = cur.fetchone()['company_eins']

    # EINs that match directly (ready to link!)
    cur.execute('''
        SELECT COUNT(DISTINCT d.sponsor_dfe_ein) as matching_eins
        FROM dol.form_5500 d
        JOIN company.company_master cm ON d.sponsor_dfe_ein = cm.ein
        WHERE d.sponsor_dfe_ein IS NOT NULL
          AND d.spons_dfe_mail_us_state = ANY(%s)
    ''', (target_states,))
    matching_eins = cur.fetchone()['matching_eins']

    # DOL filings that can be linked right now via EIN
    cur.execute('''
        SELECT COUNT(*) as linkable_filings
        FROM dol.form_5500 d
        JOIN company.company_master cm ON d.sponsor_dfe_ein = cm.ein
        WHERE d.company_unique_id IS NULL
          AND d.spons_dfe_mail_us_state = ANY(%s)
    ''', (target_states,))
    linkable_filings = cur.fetchone()['linkable_filings']

    print(f"Unique EINs in DOL (target states): {total_dol_eins:,}")
    print(f"Unique EINs in Company Master:      {total_company_eins:,}")
    print(f"Overlapping EINs:                   {matching_eins:,}")
    print()
    print(f"*** DOL filings ready to link via EIN: {linkable_filings:,} ***")

    if total_dol_eins > 0:
        overlap_pct = 100 * matching_eins / total_dol_eins
        print(f"\nEIN Match Rate: {overlap_pct:.1f}% of DOL EINs in target states")

    # =========================================================================
    # SECTION 9: Recommendations
    # =========================================================================
    print_section("9. RECOMMENDATIONS")

    recommendations = []

    if linkable_filings > 0:
        recommendations.append(f"IMMEDIATE: Link {linkable_filings:,} DOL filings via existing EIN matches")

    if unmatched_dol > 0 and total_companies > 0:
        if companies_with_ein < total_companies * 0.2:
            recommendations.append("Backfill EINs on company_master using ein_matcher.py")

    if unmatched_dol > 1000:
        recommendations.append("Run similarity matching to find name-based matches")

    if not recommendations:
        recommendations.append("Match rate looks healthy. Continue monitoring.")

    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")

    # =========================================================================
    # EXPORT (Optional)
    # =========================================================================
    if export:
        print_section("10. EXPORTING UNMATCHED FILINGS")

        cur.execute('''
            SELECT
                sponsor_dfe_ein,
                sponsor_dfe_name,
                spons_dfe_dba_name,
                spons_dfe_mail_us_city,
                spons_dfe_mail_us_state,
                spons_dfe_mail_us_zip,
                tot_active_partcp_cnt,
                form_year,
                ack_id
            FROM dol.form_5500
            WHERE company_unique_id IS NULL
              AND spons_dfe_mail_us_state = ANY(%s)
            ORDER BY tot_active_partcp_cnt DESC NULLS LAST
        ''', (target_states,))

        rows = cur.fetchall()
        if rows:
            output_dir = Path("pipeline_output")
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / f"unmatched_dol_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            print(f"Exported {len(rows):,} unmatched filings to: {output_file}")
        else:
            print("No unmatched filings to export.")

    # Cleanup
    cur.close()
    conn.close()

    print()
    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

    return {
        'total_dol': total_dol,
        'matched': matched_dol,
        'unmatched': unmatched_dol,
        'match_rate': 100 * matched_dol / total_dol if total_dol > 0 else 0
    }


def main():
    parser = argparse.ArgumentParser(description='Analyze unmatched DOL filings')
    parser.add_argument('--export', action='store_true', help='Export unmatched filings to CSV')
    parser.add_argument('--top', type=int, default=20, help='Number of near-matches to show (default: 20)')

    args = parser.parse_args()

    analyze_unmatched_dol(export=args.export, top_n=args.top)


if __name__ == '__main__':
    main()
