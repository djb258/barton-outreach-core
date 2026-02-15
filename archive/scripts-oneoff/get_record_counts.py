#!/usr/bin/env python3
"""
Record Count Report - Barton Outreach Core
Queries all major tables for current counts
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sys


def get_connection():
    """Establish connection to Neon PostgreSQL using environment variables"""
    try:
        conn = psycopg2.connect(
            host=os.environ['NEON_HOST'],
            database=os.environ['NEON_DATABASE'],
            user=os.environ['NEON_USER'],
            password=os.environ['NEON_PASSWORD'],
            sslmode='require'
        )
        conn.set_session(autocommit=True)  # Prevent transaction rollback cascade
        return conn
    except KeyError as e:
        print(f"ERROR: Missing environment variable: {e}")
        print("Ensure you're running with: doppler run -- python get_record_counts.py")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        sys.exit(1)


def execute_query(cursor, query, label):
    """Execute a query and return results with error handling"""
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        print(f"  [ERROR: {label}] {e}")
        return None


def main():
    print("=" * 80)
    print("BARTON OUTREACH CORE - RECORD COUNT REPORT")
    print("=" * 80)
    print()

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # CL Authority Registry
    print("=" * 80)
    print("CL AUTHORITY REGISTRY")
    print("=" * 80)

    result = execute_query(cursor, "SELECT COUNT(*) as total FROM cl.company_identity", "CL total")
    if result:
        print(f"Total companies: {result[0]['total']:,}")

    result = execute_query(cursor, "SELECT COUNT(*) as eligible FROM cl.company_identity WHERE eligibility_status = 'ELIGIBLE'", "CL eligible")
    if result:
        print(f"Eligibility status = ELIGIBLE: {result[0]['eligible']:,}")

    result = execute_query(cursor, "SELECT COUNT(*) as with_outreach FROM cl.company_identity WHERE outreach_id IS NOT NULL", "CL with outreach_id")
    if result:
        print(f"With outreach_id: {result[0]['with_outreach']:,}")

    result = execute_query(cursor, "SELECT COUNT(*) as excluded FROM cl.company_identity_excluded", "CL excluded")
    if result:
        print(f"Excluded companies: {result[0]['excluded']:,}")

    result = execute_query(cursor, "SELECT eligibility_status, COUNT(*) as cnt FROM cl.company_identity GROUP BY eligibility_status ORDER BY cnt DESC", "CL status breakdown")
    if result:
        print(f"\nEligibility status breakdown:")
        for row in result:
            status = row['eligibility_status'] or 'NULL'
            print(f"  {status}: {row['cnt']:,}")
    print()

    # Outreach Spine
    print("=" * 80)
    print("OUTREACH OPERATIONAL SPINE")
    print("=" * 80)

    result = execute_query(cursor, "SELECT COUNT(*) as spine FROM outreach.outreach", "Outreach spine")
    if result:
        print(f"Outreach spine records: {result[0]['spine']:,}")
    print()

    # Company Target
    print("=" * 80)
    print("COMPANY TARGET SUB-HUB (04.04.01)")
    print("=" * 80)

    result = execute_query(cursor, "SELECT COUNT(*) as ct_total FROM outreach.company_target", "CT total")
    if result:
        ct_total = result[0]['ct_total']
        print(f"Total records: {ct_total:,}")

    result = execute_query(cursor, "SELECT COUNT(*) as ct_with_email_method FROM outreach.company_target WHERE email_method IS NOT NULL AND email_method != ''", "CT with email_method")
    if result:
        count = result[0]['ct_with_email_method']
        pct = (count / ct_total * 100) if ct_total > 0 else 0
        print(f"With email_method: {count:,} ({pct:.1f}%)")

    result = execute_query(cursor, "SELECT COUNT(*) as ct_with_domain FROM outreach.company_target WHERE company_unique_id IS NOT NULL", "CT with company_unique_id")
    if result:
        print(f"With company_unique_id: {result[0]['ct_with_domain']:,}")
    print()

    # DOL Sub-Hub
    print("=" * 80)
    print("DOL FILINGS SUB-HUB (04.04.03)")
    print("=" * 80)

    result = execute_query(cursor, "SELECT COUNT(*) as dol_total FROM outreach.dol", "DOL total")
    if result:
        dol_total = result[0]['dol_total']
        print(f"Total records: {dol_total:,}")

        result = execute_query(cursor, "SELECT COUNT(*) as dol_with_ein FROM outreach.dol WHERE ein IS NOT NULL", "DOL with EIN")
        if result:
            count = result[0]['dol_with_ein']
            pct = (count / dol_total * 100) if dol_total > 0 else 0
            print(f"With EIN: {count:,} ({pct:.1f}%)")

        result = execute_query(cursor, "SELECT COUNT(*) as dol_with_filing FROM outreach.dol WHERE filing_present = TRUE", "DOL with filing")
        if result:
            count = result[0]['dol_with_filing']
            pct = (count / dol_total * 100) if dol_total > 0 else 0
            print(f"With filing_present: {count:,} ({pct:.1f}%)")

        result = execute_query(cursor, "SELECT COUNT(*) as dol_with_carrier FROM outreach.dol WHERE carrier IS NOT NULL AND carrier != ''", "DOL with carrier")
        if result:
            count = result[0]['dol_with_carrier']
            pct = (count / dol_total * 100) if dol_total > 0 else 0
            print(f"With carrier: {count:,} ({pct:.1f}%)")

        result = execute_query(cursor, "SELECT COUNT(*) as dol_with_broker FROM outreach.dol WHERE broker_or_advisor IS NOT NULL AND broker_or_advisor != ''", "DOL with broker")
        if result:
            count = result[0]['dol_with_broker']
            pct = (count / dol_total * 100) if dol_total > 0 else 0
            print(f"With broker/advisor: {count:,} ({pct:.1f}%)")

        result = execute_query(cursor, "SELECT COUNT(*) as dol_with_renewal FROM outreach.dol WHERE renewal_month IS NOT NULL", "DOL with renewal")
        if result:
            count = result[0]['dol_with_renewal']
            pct = (count / dol_total * 100) if dol_total > 0 else 0
            print(f"With renewal_month: {count:,} ({pct:.1f}%)")
    print()

    # People Sub-Hub
    print("=" * 80)
    print("PEOPLE INTELLIGENCE SUB-HUB (04.04.02)")
    print("=" * 80)

    result = execute_query(cursor, "SELECT COUNT(*) as people_total FROM people.people_master", "People total")
    if result:
        print(f"People master records: {result[0]['people_total']:,}")

    result = execute_query(cursor, "SELECT COUNT(*) as slots_total FROM people.company_slot", "Slots total")
    if result:
        slots_total = result[0]['slots_total']
        print(f"Total company slots: {slots_total:,}")

        result = execute_query(cursor, "SELECT COUNT(*) as slots_filled FROM people.company_slot WHERE is_filled = TRUE", "Slots filled")
        if result:
            slots_filled = result[0]['slots_filled']
            pct = (slots_filled / slots_total * 100) if slots_total > 0 else 0
            print(f"Filled slots: {slots_filled:,} ({pct:.1f}%)")

            print("\nSlot fill by type:")
            result = execute_query(cursor, "SELECT slot_type, COUNT(*) as filled FROM people.company_slot WHERE is_filled = TRUE GROUP BY slot_type ORDER BY slot_type", "Slot fill by type")
            if result:
                for row in result:
                    print(f"  {row['slot_type']}: {row['filled']:,}")

            result = execute_query(cursor,
                "SELECT COUNT(*) as slots_with_email FROM people.company_slot cs "
                "JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id "
                "WHERE cs.is_filled = TRUE AND pm.email IS NOT NULL AND pm.email != ''",
                "Slots with email")
            if result:
                count = result[0]['slots_with_email']
                pct = (count / slots_filled * 100) if slots_filled > 0 else 0
                print(f"\nFilled slots with email: {count:,} ({pct:.1f}%)")

            result = execute_query(cursor,
                "SELECT COUNT(*) as slots_with_linkedin FROM people.company_slot cs "
                "JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id "
                "WHERE cs.is_filled = TRUE AND pm.linkedin_url IS NOT NULL AND pm.linkedin_url != ''",
                "Slots with LinkedIn")
            if result:
                count = result[0]['slots_with_linkedin']
                pct = (count / slots_filled * 100) if slots_filled > 0 else 0
                print(f"Filled slots with LinkedIn: {count:,} ({pct:.1f}%)")

            result = execute_query(cursor,
                "SELECT COUNT(*) as slots_with_phone FROM people.company_slot "
                "WHERE is_filled = TRUE AND slot_phone IS NOT NULL AND slot_phone != ''",
                "Slots with phone")
            if result:
                count = result[0]['slots_with_phone']
                pct = (count / slots_filled * 100) if slots_filled > 0 else 0
                print(f"Filled slots with phone: {count:,} ({pct:.1f}%)")
    print()

    # Blog Sub-Hub
    print("=" * 80)
    print("BLOG CONTENT SUB-HUB (04.04.05)")
    print("=" * 80)

    result = execute_query(cursor, "SELECT COUNT(*) as blog_total FROM outreach.blog", "Blog total")
    if result:
        blog_total = result[0]['blog_total']
        print(f"Total records: {blog_total:,}")

        result = execute_query(cursor, "SELECT COUNT(*) as with_about FROM outreach.blog WHERE about_url IS NOT NULL AND about_url != ''", "Blog with about URL")
        if result:
            count = result[0]['with_about']
            pct = (count / blog_total * 100) if blog_total > 0 else 0
            print(f"With about URL: {count:,} ({pct:.1f}%)")

        result = execute_query(cursor, "SELECT COUNT(*) as with_news FROM outreach.blog WHERE news_url IS NOT NULL AND news_url != ''", "Blog with news URL")
        if result:
            count = result[0]['with_news']
            pct = (count / blog_total * 100) if blog_total > 0 else 0
            print(f"With news URL: {count:,} ({pct:.1f}%)")
    print()

    # Blog URLs
    print("=" * 80)
    print("BLOG URL STORAGE (company.company_source_urls)")
    print("=" * 80)

    result = execute_query(cursor, "SELECT source_type, COUNT(*) as cnt FROM company.company_source_urls GROUP BY source_type ORDER BY cnt DESC", "URLs by type")
    if result:
        total_urls = sum(row['cnt'] for row in result)
        print(f"Total URLs: {total_urls:,}\n")
        for row in result:
            print(f"  {row['source_type']}: {row['cnt']:,}")

        result = execute_query(cursor, "SELECT COUNT(DISTINCT company_unique_id) as companies_with_urls FROM company.company_source_urls", "Companies with URLs")
        if result:
            print(f"\nCompanies with URLs: {result[0]['companies_with_urls']:,}")
    print()

    # BIT Scores
    print("=" * 80)
    print("BIT/CLS AUTHORIZATION SYSTEM")
    print("=" * 80)

    result = execute_query(cursor, "SELECT COUNT(*) as bit_total FROM outreach.bit_scores", "BIT scores")
    if result:
        bit_total = result[0]['bit_total']
        print(f"BIT score records: {bit_total:,}")

        result = execute_query(cursor, "SELECT COUNT(*) as with_outreach FROM outreach.bit_scores WHERE outreach_id IS NOT NULL", "BIT with outreach_id")
        if result:
            print(f"With outreach_id: {result[0]['with_outreach']:,}")
    print()

    # Domain Health (from CL)
    print("=" * 80)
    print("DOMAIN HEALTH STATUS (from CL)")
    print("=" * 80)

    result = execute_query(cursor, "SELECT domain_status_code, COUNT(*) as cnt FROM cl.company_identity WHERE outreach_id IS NOT NULL GROUP BY domain_status_code ORDER BY cnt DESC", "Domain status breakdown")
    if result:
        print("Domain status breakdown (CL companies with outreach_id):")
        total = sum(row['cnt'] for row in result)
        for row in result:
            status = row['domain_status_code'] or 'NULL'
            pct = (row['cnt'] / total * 100) if total > 0 else 0
            print(f"  {status}: {row['cnt']:,} ({pct:.1f}%)")
    print()

    # Three Messaging Lanes
    print("=" * 80)
    print("THREE MESSAGING LANES")
    print("=" * 80)

    result = execute_query(cursor, "SELECT COUNT(*) as appointments FROM sales.appointments_already_had", "Appointments already had")
    if result:
        print(f"Appointments already had: {result[0]['appointments']:,}")

    result = execute_query(cursor, "SELECT COUNT(*) as partners FROM partners.fractional_cfo_master", "Fractional CFO partners")
    if result:
        print(f"Fractional CFO partners: {result[0]['partners']:,}")

    result = execute_query(cursor, "SELECT COUNT(*) as appt_tracking FROM outreach.appointments", "Appointment tracking")
    if result:
        print(f"Appointment tracking records: {result[0]['appt_tracking']:,}")
    print()

    # DOL Filing Tables
    print("=" * 80)
    print("DOL FILING SOURCE TABLES (dol.* schema)")
    print("=" * 80)

    result = execute_query(cursor, "SELECT COUNT(*) as form_5500 FROM dol.form_5500", "Form 5500")
    if result:
        print(f"Form 5500 records: {result[0]['form_5500']:,}")

    result = execute_query(cursor, "SELECT COUNT(*) as schedule_a FROM dol.schedule_a", "Schedule A")
    if result:
        print(f"Schedule A records: {result[0]['schedule_a']:,}")
    print()

    # Summary alignment check
    print("=" * 80)
    print("ALIGNMENT CHECK")
    print("=" * 80)

    result_cl = execute_query(cursor, "SELECT COUNT(*) as with_outreach FROM cl.company_identity WHERE outreach_id IS NOT NULL", "CL with outreach_id")
    result_spine = execute_query(cursor, "SELECT COUNT(*) as spine FROM outreach.outreach", "Outreach spine")
    result_ct = execute_query(cursor, "SELECT COUNT(*) as ct_total FROM outreach.company_target", "CT total")

    if result_cl and result_spine and result_ct:
        cl_with_outreach = result_cl[0]['with_outreach']
        outreach_spine = result_spine[0]['spine']
        ct_total = result_ct[0]['ct_total']

        print(f"CL with outreach_id: {cl_with_outreach:,}")
        print(f"Outreach Spine: {outreach_spine:,}")
        print(f"Company Target: {ct_total:,}")

        if cl_with_outreach == outreach_spine == ct_total:
            print("\n[OK] ALIGNED - All counts match")
        else:
            print(f"\n[!] MISALIGNMENT DETECTED")
            if cl_with_outreach != outreach_spine:
                print(f"  CL vs Spine diff: {cl_with_outreach - outreach_spine:+,}")
            if outreach_spine != ct_total:
                print(f"  Spine vs CT diff: {outreach_spine - ct_total:+,}")

    print()
    print("=" * 80)
    print("REPORT COMPLETE")
    print("=" * 80)

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
