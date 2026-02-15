#!/usr/bin/env python3
"""
Full Numbers Audit Script
========================
Queries the database to get verified counts for documentation updates.
Run with: doppler run -- python scripts/full_numbers_audit.py
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    """Get database connection from environment variables."""
    return psycopg2.connect(
        host=os.environ.get('NEON_HOST'),
        database=os.environ.get('NEON_DATABASE'),
        user=os.environ.get('NEON_USER'),
        password=os.environ.get('NEON_PASSWORD'),
        sslmode='require'
    )

def run_audit():
    """Run full audit and print results."""
    conn = get_connection()
    conn.autocommit = True  # Prevent transaction issues
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 80)
    print("FULL NUMBERS AUDIT - BARTON OUTREACH CORE")
    print("=" * 80)
    print()

    # =========================================================================
    # SECTION 1: CORE SPINE COUNTS
    # =========================================================================
    print("SECTION 1: CORE SPINE COUNTS")
    print("-" * 40)

    # CL company_identity counts
    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN outreach_id IS NOT NULL THEN 1 END) as with_outreach_id
        FROM cl.company_identity
    """)
    cl_counts = cur.fetchone()
    print(f"cl.company_identity total: {cl_counts['total']:,}")
    print(f"cl.company_identity with outreach_id: {cl_counts['with_outreach_id']:,}")

    # Check for excluded table
    cur.execute("""
        SELECT COUNT(*) as count FROM cl.company_identity_excluded
    """)
    cl_excluded = cur.fetchone()['count']
    print(f"cl.company_identity_excluded: {cl_excluded:,}")

    # Outreach spine count
    cur.execute("SELECT COUNT(*) as count FROM outreach.outreach")
    spine_count = cur.fetchone()['count']
    print(f"outreach.outreach (spine): {spine_count:,}")

    # Sovereign eligible calculation
    sovereign_eligible = cl_counts['with_outreach_id']
    print(f"\nSOVEREIGN ELIGIBLE: {sovereign_eligible:,}")
    print(f"ALIGNMENT CHECK: CL claimed ({cl_counts['with_outreach_id']:,}) vs Spine ({spine_count:,})")
    if cl_counts['with_outreach_id'] == spine_count:
        print("  STATUS: ALIGNED")
    else:
        print(f"  STATUS: MISALIGNED (delta: {abs(cl_counts['with_outreach_id'] - spine_count):,})")

    print()

    # =========================================================================
    # SECTION 2: SUB-HUB COUNTS
    # =========================================================================
    print("SECTION 2: SUB-HUB COUNTS")
    print("-" * 40)

    subhub_tables = [
        ('outreach.company_target', 'Company Target'),
        ('outreach.dol', 'DOL'),
        ('outreach.blog', 'Blog'),
        ('outreach.bit_scores', 'BIT Scores'),
    ]

    for table, name in subhub_tables:
        try:
            cur.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cur.fetchone()['count']
            pct = (count / spine_count * 100) if spine_count > 0 else 0
            print(f"{name} ({table}): {count:,} ({pct:.1f}%)")
        except Exception as e:
            print(f"{name} ({table}): ERROR - {e}")

    print()

    # =========================================================================
    # SECTION 3: PEOPLE SUB-HUB
    # =========================================================================
    print("SECTION 3: PEOPLE SUB-HUB")
    print("-" * 40)

    # People master count
    cur.execute("SELECT COUNT(*) as count FROM people.people_master")
    people_count = cur.fetchone()['count']
    print(f"people.people_master: {people_count:,}")

    # Company slot total
    cur.execute("SELECT COUNT(*) as count FROM people.company_slot")
    total_slots = cur.fetchone()['count']
    print(f"people.company_slot (total): {total_slots:,}")

    # Slots by type
    cur.execute("""
        SELECT
            slot_type,
            COUNT(*) as total,
            COUNT(CASE WHEN is_filled = TRUE THEN 1 END) as filled
        FROM people.company_slot
        GROUP BY slot_type
        ORDER BY slot_type
    """)
    slots_by_type = cur.fetchall()

    print("\nSlots by type:")
    total_filled = 0
    for row in slots_by_type:
        slot_type = row['slot_type']
        total = row['total']
        filled = row['filled']
        total_filled += filled
        fill_rate = (filled / total * 100) if total > 0 else 0
        print(f"  {slot_type}: {filled:,} / {total:,} filled ({fill_rate:.1f}%)")

    overall_fill_rate = (total_filled / total_slots * 100) if total_slots > 0 else 0
    print(f"\nOVERALL SLOT FILL: {total_filled:,} / {total_slots:,} ({overall_fill_rate:.1f}%)")

    # Companies with at least one slot
    cur.execute("""
        SELECT COUNT(DISTINCT outreach_id) as count
        FROM people.company_slot
    """)
    companies_with_slots = cur.fetchone()['count']
    print(f"Companies with slots: {companies_with_slots:,}")

    print()

    # =========================================================================
    # SECTION 4: DATA QUALITY ISSUES
    # =========================================================================
    print("SECTION 4: DATA QUALITY ISSUES")
    print("-" * 40)

    # NULL domains on spine
    cur.execute("""
        SELECT COUNT(*) as count
        FROM outreach.outreach
        WHERE domain IS NULL OR domain = ''
    """)
    null_domains = cur.fetchone()['count']
    print(f"NULL domains on spine: {null_domains:,}")

    # Duplicate domains on spine
    cur.execute("""
        SELECT COUNT(*) as count FROM (
            SELECT domain
            FROM outreach.outreach
            WHERE domain IS NOT NULL AND domain != ''
            GROUP BY domain
            HAVING COUNT(*) > 1
        ) dupes
    """)
    dupe_domains = cur.fetchone()['count']
    print(f"Duplicate domains on spine: {dupe_domains:,}")

    # Check if appointments table exists and has issues
    try:
        cur.execute("""
            SELECT COUNT(*) as count
            FROM execution.appointments
            WHERE outreach_id IS NULL
        """)
        null_oid_appointments = cur.fetchone()['count']
        print(f"NULL outreach_id in appointments: {null_oid_appointments:,}")

        cur.execute("""
            SELECT COUNT(*) as count FROM (
                SELECT email
                FROM execution.appointments
                WHERE email IS NOT NULL
                GROUP BY email
                HAVING COUNT(*) > 1
            ) dupes
        """)
        dupe_appt_emails = cur.fetchone()['count']
        print(f"Duplicate emails in appointments: {dupe_appt_emails:,}")
    except Exception as e:
        print(f"Appointments table: N/A or error - {e}")

    # Orphan people (no matching slot)
    try:
        cur.execute("""
            SELECT COUNT(*) as count
            FROM people.people_master pm
            WHERE NOT EXISTS (
                SELECT 1 FROM people.company_slot cs
                WHERE cs.person_id = pm.person_id
            )
        """)
        orphan_people = cur.fetchone()['count']
        print(f"Orphan people (no slot): {orphan_people:,}")
    except Exception as e:
        print(f"Orphan people check: ERROR - {e}")

    # Duplicate emails in people_master
    cur.execute("""
        SELECT COUNT(*) as count FROM (
            SELECT email
            FROM people.people_master
            WHERE email IS NOT NULL AND email != ''
            GROUP BY email
            HAVING COUNT(*) > 1
        ) dupes
    """)
    dupe_people_emails = cur.fetchone()['count']
    print(f"Duplicate emails in people_master: {dupe_people_emails:,}")

    # Orphan slots (no matching outreach_id)
    cur.execute("""
        SELECT COUNT(*) as count
        FROM people.company_slot cs
        WHERE NOT EXISTS (
            SELECT 1 FROM outreach.outreach o
            WHERE o.outreach_id = cs.outreach_id
        )
    """)
    orphan_slots = cur.fetchone()['count']
    print(f"Orphan slots (no spine match): {orphan_slots:,}")

    # Missing sovereign IDs on spine
    cur.execute("""
        SELECT COUNT(*) as count
        FROM outreach.outreach
        WHERE sovereign_company_id IS NULL
    """)
    missing_sovereign = cur.fetchone()['count']
    print(f"Missing sovereign_company_id on spine: {missing_sovereign:,}")

    print()

    # =========================================================================
    # SECTION 5: DOL ENRICHMENT STATUS
    # =========================================================================
    print("SECTION 5: DOL ENRICHMENT STATUS")
    print("-" * 40)

    try:
        cur.execute("SELECT COUNT(*) as count FROM outreach.dol")
        dol_count = cur.fetchone()['count']
        print(f"outreach.dol records: {dol_count:,}")

        # DOL column fill rates
        dol_columns = ['ein', 'filing_present', 'funding_type', 'carrier', 'broker_or_advisor', 'renewal_month', 'outreach_start_month']
        for col in dol_columns:
            try:
                cur.execute(f"""
                    SELECT COUNT(*) as count
                    FROM outreach.dol
                    WHERE {col} IS NOT NULL
                """)
                filled = cur.fetchone()['count']
                pct = (filled / dol_count * 100) if dol_count > 0 else 0
                print(f"  {col}: {filled:,} ({pct:.1f}%)")
            except Exception as e:
                print(f"  {col}: ERROR - {e}")
    except Exception as e:
        print(f"DOL table: ERROR - {e}")

    print()

    # =========================================================================
    # SECTION 6: COMPANY TARGET ENRICHMENT
    # =========================================================================
    print("SECTION 6: COMPANY TARGET ENRICHMENT")
    print("-" * 40)

    try:
        cur.execute("SELECT COUNT(*) as count FROM outreach.company_target")
        ct_count = cur.fetchone()['count']

        cur.execute("""
            SELECT COUNT(*) as count
            FROM outreach.company_target
            WHERE email_method IS NOT NULL AND email_method != ''
        """)
        with_email_method = cur.fetchone()['count']
        pct = (with_email_method / ct_count * 100) if ct_count > 0 else 0
        print(f"With email_method: {with_email_method:,} / {ct_count:,} ({pct:.1f}%)")
    except Exception as e:
        print(f"Company target enrichment: ERROR - {e}")

    print()

    # =========================================================================
    # SECTION 7: SUMMARY FOR DOCS
    # =========================================================================
    print("=" * 80)
    print("SUMMARY FOR DOCUMENTATION UPDATES")
    print("=" * 80)
    print()
    print("Copy these values into docs:")
    print()
    print(f"SOVEREIGN_ELIGIBLE = {sovereign_eligible:,}")
    print(f"SPINE_COUNT = {spine_count:,}")
    print(f"TOTAL_SLOTS = {total_slots:,}")
    print(f"TOTAL_FILLED = {total_filled:,}")
    print(f"FILL_RATE = {overall_fill_rate:.1f}%")
    print(f"PEOPLE_COUNT = {people_count:,}")
    print(f"COMPANIES_WITH_SLOTS = {companies_with_slots:,}")
    print()
    print("Slots per type (for denominators):")
    for row in slots_by_type:
        print(f"  {row['slot_type']}_TOTAL = {row['total']:,}")
        print(f"  {row['slot_type']}_FILLED = {row['filled']:,}")

    print()
    print("=" * 80)

    cur.close()
    conn.close()

if __name__ == "__main__":
    run_audit()
