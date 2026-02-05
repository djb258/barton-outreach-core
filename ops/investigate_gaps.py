#!/usr/bin/env python3
"""
Gap Investigation
Detailed analysis of companies missing sub-hub records
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def get_neon_connection():
    """Get Neon PostgreSQL connection"""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )

def print_section(title):
    """Print section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def main():
    print(f"\n{'='*80}")
    print(f"  GAP INVESTIGATION")
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print(f"{'='*80}\n")

    conn = get_neon_connection()

    try:
        # 1. COMPANIES MISSING COMPANY TARGET & BLOG
        print_section("1. COMPANIES MISSING BOTH COMPANY TARGET & BLOG (Critical)")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    o.outreach_id,
                    o.sovereign_id,
                    o.domain,
                    o.has_appointment,
                    o.created_at,
                    o.updated_at
                FROM outreach.outreach o
                LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
                LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
                WHERE ct.outreach_id IS NULL
                  AND b.outreach_id IS NULL
                ORDER BY o.created_at DESC
                LIMIT 20
            """)
            results = cur.fetchall()

            if results:
                print(f"Found {len(results)} companies (showing first 20):\n")
                print(f"{'Outreach ID':<38} {'Domain':<30} {'Created At':<20}")
                print("-" * 88)
                for row in results:
                    domain = row['domain'] if row['domain'] else 'NULL'
                    print(f"{row['outreach_id']:<38} {domain:<30} {str(row['created_at'])[:19]:<20}")

                # Get domain status breakdown
                cur.execute("""
                    SELECT
                        CASE WHEN o.domain IS NOT NULL THEN 'HAS_DOMAIN' ELSE 'NO_DOMAIN' END as domain_status,
                        COUNT(*) as count
                    FROM outreach.outreach o
                    LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
                    LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
                    WHERE ct.outreach_id IS NULL
                      AND b.outreach_id IS NULL
                    GROUP BY domain_status
                    ORDER BY count DESC
                """)
                status_results = cur.fetchall()

                print(f"\nDomain status breakdown:")
                for row in status_results:
                    print(f"  {row['domain_status']}: {row['count']:,}")
            else:
                print("No companies found missing both CT and Blog")

        # 2. COMPANIES MISSING ONLY COMPANY TARGET
        print_section("2. COMPANIES MISSING ONLY COMPANY TARGET (Has Blog)")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    o.outreach_id,
                    o.domain,
                    o.created_at
                FROM outreach.outreach o
                LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
                INNER JOIN outreach.blog b ON o.outreach_id = b.outreach_id
                WHERE ct.outreach_id IS NULL
                ORDER BY o.created_at DESC
                LIMIT 20
            """)
            results = cur.fetchall()

            if results:
                print(f"Found {len(results)} companies (showing first 20)")
            else:
                print("No companies found missing only CT (all missing CT also missing Blog)")

        # 3. COMPANIES MISSING ONLY BLOG
        print_section("3. COMPANIES MISSING ONLY BLOG (Has Company Target)")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    o.outreach_id,
                    o.domain,
                    o.created_at
                FROM outreach.outreach o
                INNER JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
                LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
                WHERE b.outreach_id IS NULL
                ORDER BY o.created_at DESC
                LIMIT 20
            """)
            results = cur.fetchall()

            if results:
                print(f"Found {len(results)} companies (showing first 20)")
            else:
                print("No companies found missing only Blog (all missing Blog also missing CT)")

        # 4. COMPANIES MISSING SLOTS
        print_section("4. COMPANIES MISSING ALL SLOTS (Critical)")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    o.outreach_id,
                    o.domain,
                    o.created_at,
                    CASE WHEN ct.outreach_id IS NOT NULL THEN 'YES' ELSE 'NO' END as has_ct,
                    CASE WHEN b.outreach_id IS NOT NULL THEN 'YES' ELSE 'NO' END as has_blog
                FROM outreach.outreach o
                LEFT JOIN people.company_slot cs ON o.outreach_id = cs.outreach_id
                LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
                LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
                WHERE cs.outreach_id IS NULL
                ORDER BY o.created_at DESC
                LIMIT 20
            """)
            results = cur.fetchall()

            if results:
                print(f"Found {len(results)} companies missing slots (showing first 20):\n")
                print(f"{'Outreach ID':<38} {'Domain':<25} {'Has CT':<8} {'Has Blog':<10}")
                print("-" * 81)
                for row in results:
                    domain = (row['domain'] if row['domain'] else 'NULL')[:24]
                    print(f"{row['outreach_id']:<38} {domain:<25} {row['has_ct']:<8} {row['has_blog']:<10}")

                # Overlap analysis
                cur.execute("""
                    SELECT
                        CASE WHEN ct.outreach_id IS NOT NULL THEN 'YES' ELSE 'NO' END as has_ct,
                        CASE WHEN b.outreach_id IS NOT NULL THEN 'YES' ELSE 'NO' END as has_blog,
                        COUNT(*) as count
                    FROM outreach.outreach o
                    LEFT JOIN people.company_slot cs ON o.outreach_id = cs.outreach_id
                    LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
                    LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
                    WHERE cs.outreach_id IS NULL
                    GROUP BY has_ct, has_blog
                    ORDER BY count DESC
                """)
                overlap = cur.fetchall()

                print(f"\nOverlap analysis (companies missing slots):")
                for row in overlap:
                    print(f"  Has CT: {row['has_ct']}, Has Blog: {row['has_blog']} -> {row['count']:,} companies")

        # 5. TEMPORAL PATTERN ANALYSIS
        print_section("5. TEMPORAL PATTERN - When Were Gap Companies Created?")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    DATE(o.created_at) as creation_date,
                    COUNT(*) as total_created,
                    COUNT(ct.outreach_id) as with_ct,
                    COUNT(cs.outreach_id) as with_slots,
                    COUNT(b.outreach_id) as with_blog
                FROM outreach.outreach o
                LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
                LEFT JOIN (SELECT DISTINCT outreach_id FROM people.company_slot) cs ON o.outreach_id = cs.outreach_id
                LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
                WHERE o.created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE(o.created_at)
                ORDER BY creation_date DESC
                LIMIT 30
            """)
            results = cur.fetchall()

            if results:
                print(f"{'Date':<12} {'Created':<10} {'With CT':<10} {'With Slots':<12} {'With Blog':<10}")
                print("-" * 54)
                for row in results:
                    print(f"{str(row['creation_date']):<12} {row['total_created']:>9} {row['with_ct']:>9} {row['with_slots']:>11} {row['with_blog']:>9}")

        # 6. GAP PATTERN SUMMARY
        print_section("6. GAP PATTERN SUMMARY")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Pattern 1: CT and Blog gaps are identical
            cur.execute("""
                SELECT COUNT(*) as count
                FROM outreach.outreach o
                LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
                LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
                WHERE ct.outreach_id IS NULL AND b.outreach_id IS NULL
            """)
            both_missing = cur.fetchone()['count']

            cur.execute("""
                SELECT COUNT(*) as count
                FROM outreach.outreach o
                LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
                WHERE ct.outreach_id IS NULL
            """)
            ct_missing = cur.fetchone()['count']

            cur.execute("""
                SELECT COUNT(*) as count
                FROM outreach.outreach o
                LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
                WHERE b.outreach_id IS NULL
            """)
            blog_missing = cur.fetchone()['count']

            print(f"Companies missing CT:         {ct_missing:,}")
            print(f"Companies missing Blog:       {blog_missing:,}")
            print(f"Companies missing BOTH:       {both_missing:,}")

            if ct_missing == blog_missing == both_missing:
                print("\n[FINDING] CT and Blog gaps are IDENTICAL - same 767 companies missing both")
                print("[HYPOTHESIS] Company Target hub may not have initialized for these companies")

            # Pattern 2: Slot gaps
            cur.execute("""
                SELECT COUNT(*) as count
                FROM outreach.outreach o
                LEFT JOIN people.company_slot cs ON o.outreach_id = cs.outreach_id
                WHERE cs.outreach_id IS NULL
            """)
            slots_missing = cur.fetchone()['count']

            print(f"\nCompanies missing Slots:      {slots_missing:,}")

            # Pattern 3: Overlap between CT/Blog gaps and Slot gaps
            cur.execute("""
                SELECT COUNT(*) as count
                FROM outreach.outreach o
                LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
                LEFT JOIN people.company_slot cs ON o.outreach_id = cs.outreach_id
                WHERE ct.outreach_id IS NULL AND cs.outreach_id IS NULL
            """)
            both_ct_and_slots = cur.fetchone()['count']

            print(f"Companies missing CT & Slots: {both_ct_and_slots:,}")

            if both_ct_and_slots > 0:
                overlap_pct = (both_ct_and_slots / min(ct_missing, slots_missing)) * 100
                print(f"Overlap percentage:           {overlap_pct:.1f}%")

                if overlap_pct > 90:
                    print("\n[FINDING] Most companies missing CT also missing Slots")
                    print("[HYPOTHESIS] These companies never went through Company Target pipeline")

    finally:
        conn.close()

    print(f"\n{'='*80}")
    print("  INVESTIGATION COMPLETE")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
