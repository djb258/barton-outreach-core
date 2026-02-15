#!/usr/bin/env python3
"""
Hunter Contact Slot Assignment
Assigns Hunter contacts from outreach.people to unfilled slots in people.company_slot
"""

import os
import psycopg2
from psycopg2.extras import execute_values
import uuid
from datetime import datetime

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')

def get_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL)

def analyze_hunter_contacts(conn):
    """Analyze Hunter contacts by slot type"""
    print("\n" + "="*80)
    print("STEP 1: ANALYZING HUNTER CONTACTS")
    print("="*80)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) as total_hunter_contacts,
                COUNT(CASE WHEN job_title ILIKE ANY(ARRAY['%ceo%', '%chief executive%', '%president%', '%owner%', '%founder%']) THEN 1 END) as potential_ceos,
                COUNT(CASE WHEN job_title ILIKE ANY(ARRAY['%cfo%', '%chief financial%', '%finance director%', '%controller%', '%treasurer%']) THEN 1 END) as potential_cfos,
                COUNT(CASE WHEN job_title ILIKE ANY(ARRAY['%hr %', '%human resource%', '%people %', '%talent%', '%chief people%']) THEN 1 END) as potential_hrs
            FROM enrichment.hunter_contact
            WHERE outreach_id IS NOT NULL;
        """)
        result = cur.fetchone()

        print(f"\nHunter Contacts in enrichment.hunter_contact:")
        print(f"  Total Contacts: {result[0]:,}")
        print(f"  Potential CEOs: {result[1]:,}")
        print(f"  Potential CFOs: {result[2]:,}")
        print(f"  Potential HRs:  {result[3]:,}")

        return result

def analyze_current_slots(conn):
    """Analyze current slot fill status"""
    print("\n" + "="*80)
    print("CURRENT SLOT STATUS")
    print("="*80)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                slot_type,
                COUNT(*) as total_slots,
                COUNT(CASE WHEN is_filled = TRUE THEN 1 END) as filled,
                COUNT(CASE WHEN is_filled = FALSE OR is_filled IS NULL THEN 1 END) as unfilled,
                ROUND(100.0 * COUNT(CASE WHEN is_filled = TRUE THEN 1 END) / COUNT(*), 1) as fill_rate
            FROM people.company_slot
            WHERE slot_type IN ('CEO', 'CFO', 'HR')
            GROUP BY slot_type
            ORDER BY slot_type;
        """)

        print(f"\n{'Slot Type':<12} {'Total':>10} {'Filled':>10} {'Unfilled':>10} {'Fill Rate':>10}")
        print("-" * 60)

        totals = {'total': 0, 'filled': 0, 'unfilled': 0}
        for row in cur.fetchall():
            slot_type, total, filled, unfilled, fill_rate = row
            print(f"{slot_type:<12} {total:>10,} {filled:>10,} {unfilled:>10,} {fill_rate:>9.1f}%")
            totals['total'] += total
            totals['filled'] += filled
            totals['unfilled'] += unfilled

        overall_rate = 100.0 * totals['filled'] / totals['total'] if totals['total'] > 0 else 0
        print("-" * 60)
        print(f"{'TOTAL':<12} {totals['total']:>10,} {totals['filled']:>10,} {totals['unfilled']:>10,} {overall_rate:>9.1f}%")

        return totals

def assign_ceo_slots(conn):
    """Assign CEO slots from Hunter contacts"""
    print("\n" + "="*80)
    print("STEP 2: ASSIGNING CEO SLOTS")
    print("="*80)

    with conn.cursor() as cur:
        # Find Hunter CEOs that can fill unfilled CEO slots
        cur.execute("""
            WITH hunter_ceos AS (
                SELECT
                    hc.id as hunter_id,
                    hc.outreach_id,
                    hc.first_name,
                    hc.last_name,
                    hc.email,
                    hc.linkedin_url,
                    hc.job_title,
                    hc.company_unique_id,
                    o.sovereign_id
                FROM enrichment.hunter_contact hc
                JOIN outreach.outreach o ON hc.outreach_id = o.outreach_id
                WHERE hc.outreach_id IS NOT NULL
                  AND hc.job_title ILIKE ANY(ARRAY['%ceo%', '%chief executive%', '%president%', '%owner%', '%founder%'])
                  AND hc.email IS NOT NULL
            ),
            unfilled_ceo_slots AS (
                SELECT
                    cs.company_slot_id,
                    cs.company_unique_id,
                    cs.sovereign_id
                FROM people.company_slot cs
                WHERE cs.slot_type = 'CEO'
                  AND (cs.is_filled = FALSE OR cs.is_filled IS NULL)
                  AND cs.sovereign_id IS NOT NULL
            ),
            matched AS (
                SELECT
                    hc.hunter_id,
                    hc.outreach_id,
                    hc.first_name,
                    hc.last_name,
                    hc.email,
                    hc.linkedin_url,
                    hc.job_title,
                    hc.company_unique_id as hunter_company_unique_id,
                    hc.sovereign_id,
                    ucs.company_slot_id,
                    ucs.company_unique_id as slot_company_unique_id,
                    ROW_NUMBER() OVER (PARTITION BY ucs.company_slot_id ORDER BY
                        CASE
                            WHEN hc.job_title ILIKE '%ceo%' THEN 1
                            WHEN hc.job_title ILIKE '%chief executive%' THEN 2
                            WHEN hc.job_title ILIKE '%president%' THEN 3
                            WHEN hc.job_title ILIKE '%owner%' THEN 4
                            ELSE 5
                        END,
                        hc.hunter_id
                    ) as rank
                FROM hunter_ceos hc
                JOIN unfilled_ceo_slots ucs ON hc.sovereign_id = ucs.sovereign_id
            )
            SELECT
                hunter_id,
                outreach_id,
                first_name,
                last_name,
                email,
                linkedin_url,
                job_title,
                hunter_company_unique_id,
                sovereign_company_id,
                company_slot_id,
                slot_company_unique_id
            FROM matched
            WHERE rank = 1
            LIMIT 20000;  -- Process in batches
        """)

        matches = cur.fetchall()
        print(f"\nFound {len(matches):,} CEO slot assignments to process")

        if not matches:
            print("No CEO assignments to process")
            return 0

        # Create people_master records
        people_master_inserts = []
        slot_updates = []

        for row in matches:
            hunter_id, outreach_id, first_name, last_name, email, linkedin_url, job_title, hunter_company_unique_id, sovereign_company_id, company_slot_id, slot_company_unique_id = row

            # Generate unique_id for people_master
            unique_id = f"HNT-CEO-{str(uuid.uuid4())[:8].upper()}"

            # Use slot_company_unique_id for people_master (must match company_slot.company_unique_id)
            people_master_inserts.append((
                unique_id,
                slot_company_unique_id,  # Use the company_unique_id from the slot
                sovereign_company_id,
                first_name,
                last_name,
                email,
                linkedin_url,
                job_title,
                'hunter',
                datetime.utcnow(),
                datetime.utcnow()
            ))

            slot_updates.append((
                unique_id,
                company_slot_id
            ))

        # Insert into people_master
        print(f"\nInserting {len(people_master_inserts):,} records into people.people_master...")
        execute_values(cur, """
            INSERT INTO people.people_master (
                unique_id, company_unique_id, sovereign_company_id,
                first_name, last_name, email, linkedin_url, job_title,
                source_system, created_at, updated_at
            ) VALUES %s
            ON CONFLICT (unique_id) DO NOTHING;
        """, people_master_inserts)

        inserted = cur.rowcount
        print(f"  Inserted: {inserted:,} people_master records")

        # Update company_slot
        print(f"\nUpdating {len(slot_updates):,} CEO slots...")
        execute_values(cur, """
            UPDATE people.company_slot AS cs
            SET
                person_unique_id = v.unique_id,
                is_filled = TRUE,
                updated_at = NOW()
            FROM (VALUES %s) AS v(unique_id, company_slot_id)
            WHERE cs.company_slot_id = v.company_slot_id;
        """, slot_updates)

        updated = cur.rowcount
        print(f"  Updated: {updated:,} CEO slots")

        conn.commit()
        return updated

def assign_cfo_slots(conn):
    """Assign CFO slots from Hunter contacts"""
    print("\n" + "="*80)
    print("STEP 3: ASSIGNING CFO SLOTS")
    print("="*80)

    with conn.cursor() as cur:
        cur.execute("""
            WITH hunter_cfos AS (
                SELECT
                    hc.id as hunter_id,
                    hc.outreach_id,
                    hc.first_name,
                    hc.last_name,
                    hc.email,
                    hc.linkedin_url,
                    hc.job_title,
                    hc.company_unique_id,
                    o.sovereign_id
                FROM enrichment.hunter_contact hc
                JOIN outreach.outreach o ON hc.outreach_id = o.outreach_id
                WHERE hc.outreach_id IS NOT NULL
                  AND hc.job_title ILIKE ANY(ARRAY['%cfo%', '%chief financial%', '%finance director%', '%controller%', '%treasurer%'])
                  AND hc.email IS NOT NULL
            ),
            unfilled_cfo_slots AS (
                SELECT
                    cs.company_slot_id,
                    cs.company_unique_id,
                    cs.sovereign_id
                FROM people.company_slot cs
                WHERE cs.slot_type = 'CFO'
                  AND (cs.is_filled = FALSE OR cs.is_filled IS NULL)
                  AND cs.sovereign_id IS NOT NULL
            ),
            matched AS (
                SELECT
                    hc.hunter_id,
                    hc.outreach_id,
                    hc.first_name,
                    hc.last_name,
                    hc.email,
                    hc.linkedin_url,
                    hc.job_title,
                    hc.company_unique_id as hunter_company_unique_id,
                    hc.sovereign_id,
                    ucs.company_slot_id,
                    ucs.company_unique_id as slot_company_unique_id,
                    ROW_NUMBER() OVER (PARTITION BY ucs.company_slot_id ORDER BY
                        CASE
                            WHEN hc.job_title ILIKE '%cfo%' THEN 1
                            WHEN hc.job_title ILIKE '%chief financial%' THEN 2
                            WHEN hc.job_title ILIKE '%finance director%' THEN 3
                            ELSE 4
                        END,
                        hc.hunter_id
                    ) as rank
                FROM hunter_cfos hc
                JOIN unfilled_cfo_slots ucs ON hc.sovereign_id = ucs.sovereign_id
            )
            SELECT
                hunter_id,
                outreach_id,
                first_name,
                last_name,
                email,
                linkedin_url,
                job_title,
                hunter_company_unique_id,
                sovereign_company_id,
                company_slot_id,
                slot_company_unique_id
            FROM matched
            WHERE rank = 1
            LIMIT 20000;
        """)

        matches = cur.fetchall()
        print(f"\nFound {len(matches):,} CFO slot assignments to process")

        if not matches:
            print("No CFO assignments to process")
            return 0

        # Create people_master records
        people_master_inserts = []
        slot_updates = []

        for row in matches:
            hunter_id, outreach_id, first_name, last_name, email, linkedin_url, job_title, hunter_company_unique_id, sovereign_company_id, company_slot_id, slot_company_unique_id = row

            unique_id = f"HNT-CFO-{str(uuid.uuid4())[:8].upper()}"

            people_master_inserts.append((
                unique_id,
                slot_company_unique_id,  # Use the company_unique_id from the slot
                sovereign_company_id,
                first_name,
                last_name,
                email,
                linkedin_url,
                job_title,
                'hunter',
                datetime.utcnow(),
                datetime.utcnow()
            ))

            slot_updates.append((
                unique_id,
                company_slot_id
            ))

        print(f"\nInserting {len(people_master_inserts):,} records into people.people_master...")
        execute_values(cur, """
            INSERT INTO people.people_master (
                unique_id, company_unique_id, sovereign_company_id,
                first_name, last_name, email, linkedin_url, job_title,
                source_system, created_at, updated_at
            ) VALUES %s
            ON CONFLICT (unique_id) DO NOTHING;
        """, people_master_inserts)

        inserted = cur.rowcount
        print(f"  Inserted: {inserted:,} people_master records")

        print(f"\nUpdating {len(slot_updates):,} CFO slots...")
        execute_values(cur, """
            UPDATE people.company_slot AS cs
            SET
                person_unique_id = v.unique_id,
                is_filled = TRUE,
                updated_at = NOW()
            FROM (VALUES %s) AS v(unique_id, company_slot_id)
            WHERE cs.company_slot_id = v.company_slot_id;
        """, slot_updates)

        updated = cur.rowcount
        print(f"  Updated: {updated:,} CFO slots")

        conn.commit()
        return updated

def assign_hr_slots(conn):
    """Assign HR slots from Hunter contacts"""
    print("\n" + "="*80)
    print("STEP 4: ASSIGNING HR SLOTS")
    print("="*80)

    with conn.cursor() as cur:
        cur.execute("""
            WITH hunter_hrs AS (
                SELECT
                    hc.id as hunter_id,
                    hc.outreach_id,
                    hc.first_name,
                    hc.last_name,
                    hc.email,
                    hc.linkedin_url,
                    hc.job_title,
                    hc.company_unique_id,
                    o.sovereign_id
                FROM enrichment.hunter_contact hc
                JOIN outreach.outreach o ON hc.outreach_id = o.outreach_id
                WHERE hc.outreach_id IS NOT NULL
                  AND hc.job_title ILIKE ANY(ARRAY['%hr %', '%human resource%', '%people %', '%talent%', '%chief people%'])
                  AND hc.email IS NOT NULL
            ),
            unfilled_hr_slots AS (
                SELECT
                    cs.company_slot_id,
                    cs.company_unique_id,
                    cs.sovereign_id
                FROM people.company_slot cs
                WHERE cs.slot_type = 'HR'
                  AND (cs.is_filled = FALSE OR cs.is_filled IS NULL)
                  AND cs.sovereign_id IS NOT NULL
            ),
            matched AS (
                SELECT
                    hc.hunter_id,
                    hc.outreach_id,
                    hc.first_name,
                    hc.last_name,
                    hc.email,
                    hc.linkedin_url,
                    hc.job_title,
                    hc.company_unique_id as hunter_company_unique_id,
                    hc.sovereign_id,
                    ucs.company_slot_id,
                    ucs.company_unique_id as slot_company_unique_id,
                    ROW_NUMBER() OVER (PARTITION BY ucs.company_slot_id ORDER BY
                        CASE
                            WHEN hc.job_title ILIKE '%chief people%' THEN 1
                            WHEN hc.job_title ILIKE '%hr %' THEN 2
                            WHEN hc.job_title ILIKE '%human resource%' THEN 3
                            ELSE 4
                        END,
                        hc.hunter_id
                    ) as rank
                FROM hunter_hrs hc
                JOIN unfilled_hr_slots ucs ON hc.sovereign_id = ucs.sovereign_id
            )
            SELECT
                hunter_id,
                outreach_id,
                first_name,
                last_name,
                email,
                linkedin_url,
                job_title,
                hunter_company_unique_id,
                sovereign_company_id,
                company_slot_id,
                slot_company_unique_id
            FROM matched
            WHERE rank = 1
            LIMIT 20000;
        """)

        matches = cur.fetchall()
        print(f"\nFound {len(matches):,} HR slot assignments to process")

        if not matches:
            print("No HR assignments to process")
            return 0

        # Create people_master records
        people_master_inserts = []
        slot_updates = []

        for row in matches:
            hunter_id, outreach_id, first_name, last_name, email, linkedin_url, job_title, hunter_company_unique_id, sovereign_company_id, company_slot_id, slot_company_unique_id = row

            unique_id = f"HNT-HR-{str(uuid.uuid4())[:8].upper()}"

            people_master_inserts.append((
                unique_id,
                slot_company_unique_id,  # Use the company_unique_id from the slot
                sovereign_company_id,
                first_name,
                last_name,
                email,
                linkedin_url,
                job_title,
                'hunter',
                datetime.utcnow(),
                datetime.utcnow()
            ))

            slot_updates.append((
                unique_id,
                company_slot_id
            ))

        print(f"\nInserting {len(people_master_inserts):,} records into people.people_master...")
        execute_values(cur, """
            INSERT INTO people.people_master (
                unique_id, company_unique_id, sovereign_company_id,
                first_name, last_name, email, linkedin_url, job_title,
                source_system, created_at, updated_at
            ) VALUES %s
            ON CONFLICT (unique_id) DO NOTHING;
        """, people_master_inserts)

        inserted = cur.rowcount
        print(f"  Inserted: {inserted:,} people_master records")

        print(f"\nUpdating {len(slot_updates):,} HR slots...")
        execute_values(cur, """
            UPDATE people.company_slot AS cs
            SET
                person_unique_id = v.unique_id,
                is_filled = TRUE,
                updated_at = NOW()
            FROM (VALUES %s) AS v(unique_id, company_slot_id)
            WHERE cs.company_slot_id = v.company_slot_id;
        """, slot_updates)

        updated = cur.rowcount
        print(f"  Updated: {updated:,} HR slots")

        conn.commit()
        return updated

def final_report(conn):
    """Generate final slot fill report"""
    print("\n" + "="*80)
    print("FINAL SLOT FILL REPORT")
    print("="*80)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                slot_type,
                COUNT(*) as total_slots,
                COUNT(CASE WHEN is_filled = TRUE THEN 1 END) as filled,
                COUNT(CASE WHEN is_filled = FALSE OR is_filled IS NULL THEN 1 END) as unfilled,
                ROUND(100.0 * COUNT(CASE WHEN is_filled = TRUE THEN 1 END) / COUNT(*), 1) as fill_rate
            FROM people.company_slot
            WHERE slot_type IN ('CEO', 'CFO', 'HR')
            GROUP BY slot_type
            ORDER BY slot_type;
        """)

        print(f"\n{'Slot Type':<12} {'Total':>10} {'Filled':>10} {'Unfilled':>10} {'Fill Rate':>10}")
        print("-" * 60)

        totals = {'total': 0, 'filled': 0, 'unfilled': 0}
        for row in cur.fetchall():
            slot_type, total, filled, unfilled, fill_rate = row
            print(f"{slot_type:<12} {total:>10,} {filled:>10,} {unfilled:>10,} {fill_rate:>9.1f}%")
            totals['total'] += total
            totals['filled'] += filled
            totals['unfilled'] += unfilled

        overall_rate = 100.0 * totals['filled'] / totals['total'] if totals['total'] > 0 else 0
        print("-" * 60)
        print(f"{'TOTAL':<12} {totals['total']:>10,} {totals['filled']:>10,} {totals['unfilled']:>10,} {overall_rate:>9.1f}%")

        # Check people_master source distribution
        cur.execute("""
            SELECT
                source_system,
                COUNT(*) as count
            FROM people.people_master
            GROUP BY source_system
            ORDER BY count DESC;
        """)

        print("\n\nPeople Master Source Distribution:")
        print("-" * 40)
        for row in cur.fetchall():
            print(f"  {row[0]:<20} {row[1]:>10,}")

def main():
    """Main execution"""
    print("\n" + "="*80)
    print("HUNTER CONTACT SLOT ASSIGNMENT")
    print("="*80)
    print(f"Start Time: {datetime.utcnow().isoformat()}Z")

    conn = get_connection()

    try:
        # Step 1: Analyze
        analyze_hunter_contacts(conn)
        analyze_current_slots(conn)

        # Step 2-4: Assign slots
        ceo_assigned = assign_ceo_slots(conn)
        cfo_assigned = assign_cfo_slots(conn)
        hr_assigned = assign_hr_slots(conn)

        # Step 5: Final report
        final_report(conn)

        print("\n" + "="*80)
        print("ASSIGNMENT SUMMARY")
        print("="*80)
        print(f"  CEO Slots Filled: {ceo_assigned:,}")
        print(f"  CFO Slots Filled: {cfo_assigned:,}")
        print(f"  HR Slots Filled:  {hr_assigned:,}")
        print(f"  TOTAL FILLED:     {ceo_assigned + cfo_assigned + hr_assigned:,}")

        print("\n" + "="*80)
        print("HUNTER SLOT ASSIGNMENT COMPLETE")
        print("="*80)
        print(f"End Time: {datetime.utcnow().isoformat()}Z")

    except Exception as e:
        print(f"\nERROR: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
