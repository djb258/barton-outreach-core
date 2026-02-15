#!/usr/bin/env python3
"""
Sub-Hub Coverage Audit
Comprehensive gap analysis across Outreach spine and all sub-hubs
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

def execute_query(conn, query, description):
    """Execute query and return results"""
    print(f"[QUERY] {description}")
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        results = cur.fetchall()
        return results

def main():
    print(f"\n{'='*80}")
    print(f"  SUB-HUB COVERAGE AUDIT")
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print(f"{'='*80}\n")

    conn = get_neon_connection()

    try:
        # 1. OUTREACH SPINE BASELINE
        print_section("1. OUTREACH SPINE BASELINE")
        results = execute_query(conn,
            "SELECT COUNT(*) as total_outreach FROM outreach.outreach;",
            "Total companies in Outreach spine")
        print(f"Total Outreach records: {results[0]['total_outreach']:,}")
        baseline = results[0]['total_outreach']

        # 2. COMPANY TARGET COVERAGE
        print_section("2. COMPANY TARGET COVERAGE")
        results = execute_query(conn, """
            SELECT
                (SELECT COUNT(*) FROM outreach.outreach) as spine_count,
                (SELECT COUNT(*) FROM outreach.company_target) as ct_count,
                (SELECT COUNT(*) FROM outreach.outreach o
                 LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
                 WHERE ct.outreach_id IS NULL) as missing_from_ct
        """, "Company Target coverage analysis")

        r = results[0]
        print(f"Spine Count:            {r['spine_count']:,}")
        print(f"Company Target Count:   {r['ct_count']:,}")
        print(f"Missing from CT:        {r['missing_from_ct']:,}")
        print(f"Coverage Rate:          {(r['ct_count']/r['spine_count']*100):.2f}%")

        if r['missing_from_ct'] > 0:
            print(f"\n[ALERT] {r['missing_from_ct']:,} companies missing Company Target records!")

        # 3. DOL COVERAGE
        print_section("3. DOL FILINGS COVERAGE")
        results = execute_query(conn, """
            SELECT
                (SELECT COUNT(*) FROM outreach.outreach) as spine_count,
                (SELECT COUNT(DISTINCT outreach_id) FROM outreach.dol) as dol_unique_companies,
                (SELECT COUNT(*) FROM outreach.outreach o
                 LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
                 WHERE d.outreach_id IS NULL) as missing_from_dol
        """, "DOL coverage analysis")

        r = results[0]
        print(f"Spine Count:            {r['spine_count']:,}")
        print(f"DOL Unique Companies:   {r['dol_unique_companies']:,}")
        print(f"Missing from DOL:       {r['missing_from_dol']:,}")
        print(f"Coverage Rate:          {(r['dol_unique_companies']/r['spine_count']*100):.2f}%")

        if r['missing_from_dol'] > 0:
            print(f"\n[NOTE] {r['missing_from_dol']:,} companies missing DOL records (expected - not all companies have filings)")

        # 4. PEOPLE SLOTS COVERAGE
        print_section("4. PEOPLE SLOTS COVERAGE")
        results = execute_query(conn, """
            SELECT
                (SELECT COUNT(*) FROM outreach.outreach) as spine_count,
                (SELECT COUNT(DISTINCT outreach_id) FROM people.company_slot) as slot_unique_companies,
                (SELECT COUNT(*) FROM outreach.outreach o
                 LEFT JOIN people.company_slot cs ON o.outreach_id = cs.outreach_id
                 WHERE cs.outreach_id IS NULL) as missing_from_slots
        """, "People Slots coverage analysis")

        r = results[0]
        print(f"Spine Count:              {r['spine_count']:,}")
        print(f"Slot Unique Companies:    {r['slot_unique_companies']:,}")
        print(f"Missing from Slots:       {r['missing_from_slots']:,}")
        print(f"Coverage Rate:            {(r['slot_unique_companies']/r['spine_count']*100):.2f}%")

        if r['missing_from_slots'] > 0:
            print(f"\n[ALERT] {r['missing_from_slots']:,} companies missing ALL slot records!")

        # 5. BLOG COVERAGE
        print_section("5. BLOG CONTENT COVERAGE")
        results = execute_query(conn, """
            SELECT
                (SELECT COUNT(*) FROM outreach.outreach) as spine_count,
                (SELECT COUNT(DISTINCT outreach_id) FROM outreach.blog) as blog_unique_companies,
                (SELECT COUNT(*) FROM outreach.outreach o
                 LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
                 WHERE b.outreach_id IS NULL) as missing_from_blog
        """, "Blog coverage analysis")

        r = results[0]
        print(f"Spine Count:              {r['spine_count']:,}")
        print(f"Blog Unique Companies:    {r['blog_unique_companies']:,}")
        print(f"Missing from Blog:        {r['missing_from_blog']:,}")
        print(f"Coverage Rate:            {(r['blog_unique_companies']/r['spine_count']*100):.2f}%")

        if r['missing_from_blog'] > 0:
            print(f"\n[ALERT] {r['missing_from_blog']:,} companies missing Blog records!")

        # 6. SLOT COUNT DISTRIBUTION
        print_section("6. SLOT COUNT DISTRIBUTION PER COMPANY")
        results = execute_query(conn, """
            SELECT
                slots_per_company,
                COUNT(*) as companies
            FROM (
                SELECT outreach_id, COUNT(*) as slots_per_company
                FROM people.company_slot
                GROUP BY outreach_id
            ) sub
            GROUP BY slots_per_company
            ORDER BY slots_per_company
        """, "Slot count distribution")

        print(f"{'Slots Per Company':<20} {'# Companies':>15}")
        print("-" * 35)
        for row in results:
            print(f"{row['slots_per_company']:<20} {row['companies']:>15,}")

        # Expected: 3 slots per company (CEO, CFO, HR)
        correct_count = sum(r['companies'] for r in results if r['slots_per_company'] == 3)
        total_with_slots = sum(r['companies'] for r in results)
        print(f"\nCompanies with exactly 3 slots: {correct_count:,} / {total_with_slots:,} ({(correct_count/total_with_slots*100):.2f}%)")

        # 7. MISSING SLOT TYPES
        print_section("7. COMPANIES MISSING SPECIFIC SLOT TYPES")
        results = execute_query(conn, """
            WITH companies AS (
                SELECT DISTINCT outreach_id FROM outreach.outreach
            ),
            slot_coverage AS (
                SELECT
                    c.outreach_id,
                    MAX(CASE WHEN cs.slot_type = 'CEO' THEN 1 ELSE 0 END) as has_ceo,
                    MAX(CASE WHEN cs.slot_type = 'CFO' THEN 1 ELSE 0 END) as has_cfo,
                    MAX(CASE WHEN cs.slot_type = 'HR' THEN 1 ELSE 0 END) as has_hr
                FROM companies c
                LEFT JOIN people.company_slot cs ON c.outreach_id = cs.outreach_id
                GROUP BY c.outreach_id
            )
            SELECT
                SUM(CASE WHEN has_ceo = 0 THEN 1 ELSE 0 END) as missing_ceo_slot,
                SUM(CASE WHEN has_cfo = 0 THEN 1 ELSE 0 END) as missing_cfo_slot,
                SUM(CASE WHEN has_hr = 0 THEN 1 ELSE 0 END) as missing_hr_slot,
                SUM(CASE WHEN has_ceo = 0 AND has_cfo = 0 AND has_hr = 0 THEN 1 ELSE 0 END) as missing_all_slots
            FROM slot_coverage
        """, "Missing slot types by company")

        r = results[0]
        print(f"Companies missing CEO slot:  {r['missing_ceo_slot']:,}")
        print(f"Companies missing CFO slot:  {r['missing_cfo_slot']:,}")
        print(f"Companies missing HR slot:   {r['missing_hr_slot']:,}")
        print(f"Companies missing ALL slots: {r['missing_all_slots']:,}")

        # 8. GAP SUMMARY SAMPLE
        print_section("8. GAP SUMMARY - SAMPLE OF 100 COMPANIES WITH GAPS")
        results = execute_query(conn, """
            SELECT
                o.outreach_id,
                CASE WHEN ct.outreach_id IS NULL THEN 'MISSING' ELSE 'OK' END as company_target,
                CASE WHEN d.outreach_id IS NULL THEN 'MISSING' ELSE 'OK' END as dol,
                CASE WHEN cs.outreach_id IS NULL THEN 'MISSING' ELSE 'OK' END as slots,
                CASE WHEN b.outreach_id IS NULL THEN 'MISSING' ELSE 'OK' END as blog
            FROM outreach.outreach o
            LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
            LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
            LEFT JOIN (SELECT DISTINCT outreach_id FROM people.company_slot) cs ON o.outreach_id = cs.outreach_id
            LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
            WHERE ct.outreach_id IS NULL
               OR d.outreach_id IS NULL
               OR cs.outreach_id IS NULL
               OR b.outreach_id IS NULL
            LIMIT 100
        """, "Sample companies with gaps")

        if results:
            print(f"{'Outreach ID':<40} {'CT':<10} {'DOL':<10} {'Slots':<10} {'Blog':<10}")
            print("-" * 80)
            for row in results[:20]:  # Show first 20
                print(f"{row['outreach_id']:<40} {row['company_target']:<10} {row['dol']:<10} {row['slots']:<10} {row['blog']:<10}")

            if len(results) > 20:
                print(f"\n... and {len(results) - 20} more companies with gaps")
        else:
            print("[SUCCESS] No companies found with gaps!")

        # 9. OVERALL SUMMARY
        print_section("9. OVERALL COVERAGE SUMMARY")

        # Get all metrics
        ct_query = execute_query(conn, "SELECT COUNT(*) as ct FROM outreach.company_target", "CT count")
        dol_query = execute_query(conn, "SELECT COUNT(DISTINCT outreach_id) as dol FROM outreach.dol", "DOL count")
        slots_query = execute_query(conn, "SELECT COUNT(DISTINCT outreach_id) as slots FROM people.company_slot", "Slots count")
        blog_query = execute_query(conn, "SELECT COUNT(DISTINCT outreach_id) as blog FROM outreach.blog", "Blog count")

        ct_count = ct_query[0]['ct']
        dol_count = dol_query[0]['dol']
        slots_count = slots_query[0]['slots']
        blog_count = blog_query[0]['blog']

        print(f"{'Sub-Hub':<30} {'Coverage':<15} {'Gap':<15} {'Coverage %':<15}")
        print("-" * 75)
        print(f"{'Company Target':<30} {ct_count:>14,} {baseline - ct_count:>14,} {(ct_count/baseline*100):>14.2f}%")
        print(f"{'DOL Filings':<30} {dol_count:>14,} {baseline - dol_count:>14,} {(dol_count/baseline*100):>14.2f}%")
        print(f"{'People Slots':<30} {slots_count:>14,} {baseline - slots_count:>14,} {(slots_count/baseline*100):>14.2f}%")
        print(f"{'Blog Content':<30} {blog_count:>14,} {baseline - blog_count:>14,} {(blog_count/baseline*100):>14.2f}%")

        # CRITICAL GAPS (must be 100%)
        critical_gaps = []
        if ct_count < baseline:
            critical_gaps.append(f"Company Target: {baseline - ct_count:,} missing")
        if blog_count < baseline:
            critical_gaps.append(f"Blog: {baseline - blog_count:,} missing")

        if critical_gaps:
            print("\n[CRITICAL] The following sub-hubs must have 100% coverage:")
            for gap in critical_gaps:
                print(f"  - {gap}")

        # ACCEPTABLE GAPS
        print("\n[NOTE] DOL Filings gap is expected (not all companies have filings)")

        # PEOPLE SLOTS ALERT
        if slots_count < baseline:
            print(f"[ALERT] People Slots gap: {baseline - slots_count:,} companies without slots")

    finally:
        conn.close()

    print(f"\n{'='*80}")
    print("  AUDIT COMPLETE")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
