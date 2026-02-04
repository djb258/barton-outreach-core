"""
Create CEO, CFO, HR slots for Hunter DOL intake companies (commercially eligible only).

This script:
1. Identifies companies from the Hunter DOL intake (source_system='hunter_dol_intake')
2. Filters out non-commercial entities (GOV, EDU, HCF, REL, INS)
3. Creates 3 slots (CEO, CFO, HR) per eligible company
4. Uses bulk insert with execute_values for performance

Execution:
    doppler run -- python scripts/create_hunter_dol_slots.py
"""

import os
import sys
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
import uuid

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_neon_connection():
    """Establish connection to Neon PostgreSQL."""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )

def count_eligible_companies(conn):
    """
    Count commercially eligible companies from Hunter DOL intake.

    Exclusion patterns:
    - GOV: .gov domains or government entity names
    - EDU: .edu domains or educational institution names
    - HCF: healthcare facility names
    - REL: religious organization names
    - INS: insurance company names
    """
    query = """
    WITH hunter_companies AS (
        SELECT DISTINCT
            ci.outreach_id,
            ci.sovereign_company_id,
            ci.company_domain AS domain,
            ci.company_name
        FROM cl.company_identity ci
        WHERE ci.outreach_attached_at >= '2026-02-04'
          AND ci.outreach_id IS NOT NULL
    ),
    filtered_companies AS (
        SELECT
            outreach_id,
            sovereign_company_id,
            domain,
            company_name,
            CASE
                -- GOV filter
                WHEN domain LIKE '%.gov'
                    OR LOWER(company_name) ~ '\\m(city of|county of|state of|township|municipality|borough|village of)\\M'
                    THEN 'GOV'
                -- EDU filter
                WHEN domain LIKE '%.edu'
                    OR LOWER(company_name) ~ '\\m(school district|university|college|academy|school system)\\M'
                    THEN 'EDU'
                -- HCF filter
                WHEN LOWER(company_name) ~ '\\m(hospital|medical center|health system|healthcare|clinic|nursing home)\\M'
                    THEN 'HCF'
                -- REL filter
                WHEN LOWER(company_name) ~ '\\m(church|diocese|parish|ministries|synagogue|mosque|temple)\\M'
                    THEN 'REL'
                -- INS filter
                WHEN LOWER(company_name) ~ '\\m(insurance company|insurance co|mutual insurance|life insurance|insurance agency)\\M'
                    THEN 'INS'
                ELSE 'ELIGIBLE'
            END AS eligibility_status
        FROM hunter_companies
    )
    SELECT
        COUNT(*) FILTER (WHERE eligibility_status = 'ELIGIBLE') AS eligible_count,
        COUNT(*) FILTER (WHERE eligibility_status = 'GOV') AS gov_count,
        COUNT(*) FILTER (WHERE eligibility_status = 'EDU') AS edu_count,
        COUNT(*) FILTER (WHERE eligibility_status = 'HCF') AS hcf_count,
        COUNT(*) FILTER (WHERE eligibility_status = 'REL') AS rel_count,
        COUNT(*) FILTER (WHERE eligibility_status = 'INS') AS ins_count,
        COUNT(*) AS total_count
    FROM filtered_companies;
    """

    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchone()
        return {
            'eligible': result[0],
            'gov': result[1],
            'edu': result[2],
            'hcf': result[3],
            'rel': result[4],
            'ins': result[5],
            'total': result[6]
        }

def get_eligible_companies(conn):
    """Fetch eligible companies for slot creation."""
    query = """
    WITH hunter_companies AS (
        SELECT DISTINCT
            ci.outreach_id,
            ci.sovereign_company_id,
            ci.company_domain AS domain,
            ci.company_name
        FROM cl.company_identity ci
        WHERE ci.outreach_attached_at >= '2026-02-04'
          AND ci.outreach_id IS NOT NULL
    ),
    filtered_companies AS (
        SELECT
            outreach_id,
            sovereign_company_id,
            domain,
            company_name,
            CASE
                -- GOV filter
                WHEN domain LIKE '%.gov'
                    OR LOWER(company_name) ~ '\\m(city of|county of|state of|township|municipality|borough|village of)\\M'
                    THEN 'GOV'
                -- EDU filter
                WHEN domain LIKE '%.edu'
                    OR LOWER(company_name) ~ '\\m(school district|university|college|academy|school system)\\M'
                    THEN 'EDU'
                -- HCF filter
                WHEN LOWER(company_name) ~ '\\m(hospital|medical center|health system|healthcare|clinic|nursing home)\\M'
                    THEN 'HCF'
                -- REL filter
                WHEN LOWER(company_name) ~ '\\m(church|diocese|parish|ministries|synagogue|mosque|temple)\\M'
                    THEN 'REL'
                -- INS filter
                WHEN LOWER(company_name) ~ '\\m(insurance company|insurance co|mutual insurance|life insurance|insurance agency)\\M'
                    THEN 'INS'
                ELSE 'ELIGIBLE'
            END AS eligibility_status
        FROM hunter_companies
    )
    SELECT
        outreach_id,
        sovereign_company_id
    FROM filtered_companies
    WHERE eligibility_status = 'ELIGIBLE'
    ORDER BY outreach_id;
    """

    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

def check_existing_slots(conn, outreach_ids):
    """Check which companies already have slots."""
    # Convert list to tuple for IN clause
    query = """
    SELECT DISTINCT outreach_id
    FROM people.company_slot
    WHERE outreach_id IN %s;
    """

    with conn.cursor() as cur:
        cur.execute(query, (tuple(outreach_ids),))
        return set(row[0] for row in cur.fetchall())

def create_slots_bulk(conn, companies):
    """Create CEO, CFO, HR slots for companies using bulk insert."""
    slot_types = ['CEO', 'CFO', 'HR']
    now = datetime.utcnow()

    # Prepare values: (slot_id, outreach_id, company_unique_id, slot_type, is_filled, created_at, updated_at)
    values = []
    for outreach_id, sovereign_company_id in companies:
        company_unique_id = str(sovereign_company_id)
        for slot_type in slot_types:
            values.append((
                str(uuid.uuid4()),
                outreach_id,
                company_unique_id,
                slot_type,
                False,
                now,
                now
            ))

    insert_query = """
    INSERT INTO people.company_slot (
        slot_id, outreach_id, company_unique_id, slot_type,
        is_filled, created_at, updated_at
    )
    VALUES %s
    ON CONFLICT (outreach_id, slot_type) DO NOTHING;
    """

    with conn.cursor() as cur:
        execute_values(cur, insert_query, values, page_size=1000)
        inserted_count = cur.rowcount

    return inserted_count

def main():
    print("=" * 80)
    print("HUNTER DOL SLOT CREATION")
    print("=" * 80)
    print()

    conn = None
    try:
        # Connect to Neon
        print("Connecting to Neon PostgreSQL...")
        conn = get_neon_connection()
        print("[OK] Connected")
        print()

        # Step 1: Count eligible companies
        print("Step 1: Counting eligible companies...")
        counts = count_eligible_companies(conn)

        print(f"\nHunter DOL Intake Analysis:")
        print(f"  Total companies:        {counts['total']:,}")
        print(f"  -------------------------------------")
        print(f"  ELIGIBLE (commercial):  {counts['eligible']:,}")
        print(f"  -------------------------------------")
        print(f"  Excluded:")
        print(f"    GOV (government):     {counts['gov']:,}")
        print(f"    EDU (education):      {counts['edu']:,}")
        print(f"    HCF (healthcare):     {counts['hcf']:,}")
        print(f"    REL (religious):      {counts['rel']:,}")
        print(f"    INS (insurance):      {counts['ins']:,}")
        print(f"  -------------------------------------")
        print(f"  Total excluded:         {counts['gov'] + counts['edu'] + counts['hcf'] + counts['rel'] + counts['ins']:,}")
        print()

        if counts['eligible'] == 0:
            print("[WARN] No eligible companies found. Exiting.")
            return

        # Confirmation
        expected_slots = counts['eligible'] * 3
        print(f"This will create {expected_slots:,} slots (CEO, CFO, HR for {counts['eligible']:,} companies)")
        print("\nProceeding with slot creation...")
        print()

        # Step 2: Fetch eligible companies
        print("Step 2: Fetching eligible companies...")
        companies = get_eligible_companies(conn)
        print(f"[OK] Fetched {len(companies):,} companies")
        print()

        # Step 3: Check for existing slots
        print("Step 3: Checking for existing slots...")
        outreach_ids = [company[0] for company in companies]
        existing_slots = check_existing_slots(conn, outreach_ids)

        if existing_slots:
            print(f"[WARN] Found {len(existing_slots):,} companies with existing slots")
            companies_to_process = [
                (oid, sid) for oid, sid in companies if oid not in existing_slots
            ]
            print(f"  Will create slots for {len(companies_to_process):,} companies (no existing slots)")
        else:
            companies_to_process = companies
            print(f"[OK] No existing slots found")

        print()

        if not companies_to_process:
            print("[WARN] All companies already have slots. Nothing to do.")
            return

        # Step 4: Create slots
        print(f"Step 4: Creating slots for {len(companies_to_process):,} companies...")
        inserted_count = create_slots_bulk(conn, companies_to_process)
        conn.commit()

        print(f"[OK] Created {inserted_count:,} slots")
        print()

        # Summary
        print("=" * 80)
        print("SLOT CREATION COMPLETE")
        print("=" * 80)
        print(f"  Companies processed:    {len(companies_to_process):,}")
        print(f"  Slots created:          {inserted_count:,}")
        print(f"  Slots per company:      {inserted_count / len(companies_to_process):.1f}")
        print()

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
            print("[OK] Connection closed")

if __name__ == "__main__":
    main()
