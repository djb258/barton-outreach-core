#!/usr/bin/env python3
"""
Hunter Contact Slot Assignment v3
Fills unfilled slots with Hunter contacts from the same outreach_id
Uses title matching to prefer appropriate contacts, but fills with any contact if needed
"""

import os
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone
import random

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')

# Barton ID counter
_id_counter = random.randint(100000, 999999)

def get_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL)

def generate_barton_id():
    """Generate Barton doctrine-compliant ID"""
    global _id_counter
    _id_counter += 1
    return f"04.04.02.99.{_id_counter:06d}.{random.randint(100, 999):03d}"

def analyze_potential(conn):
    """Analyze matching potential"""
    print("\n" + "="*80)
    print("ANALYZING MATCH POTENTIAL")
    print("="*80)

    with conn.cursor() as cur:
        # Check current slot status
        cur.execute("""
            SELECT
                slot_type,
                COUNT(*) as total,
                COUNT(CASE WHEN is_filled = TRUE THEN 1 END) as filled,
                COUNT(CASE WHEN is_filled = FALSE OR is_filled IS NULL THEN 1 END) as unfilled
            FROM people.company_slot
            WHERE slot_type IN ('CEO', 'CFO', 'HR')
            GROUP BY slot_type;
        """)

        print("\nCurrent slot status:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]:,} total, {row[2]:,} filled, {row[3]:,} unfilled")

        # Check Hunter contact availability for unfilled slots
        cur.execute("""
            SELECT
                cs.slot_type,
                COUNT(DISTINCT hc.id) as available_contacts
            FROM people.company_slot cs
            JOIN enrichment.hunter_contact hc ON cs.outreach_id = hc.outreach_id
            WHERE (cs.is_filled = FALSE OR cs.is_filled IS NULL)
              AND hc.first_name IS NOT NULL
              AND hc.last_name IS NOT NULL
              AND hc.email IS NOT NULL
            GROUP BY cs.slot_type
            ORDER BY cs.slot_type;
        """)

        print("\nHunter contacts available for unfilled slots:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]:,} contacts available")

def fill_slots_by_type(conn, slot_type, title_patterns):
    """Fill unfilled slots of a specific type with Hunter contacts"""
    print(f"\n" + "="*80)
    print(f"FILLING {slot_type} SLOTS")
    print("="*80)

    with conn.cursor() as cur:
        # Build title match CASE expression
        title_case_parts = []
        for i, pattern in enumerate(title_patterns, 1):
            title_case_parts.append(f"WHEN hc.job_title ILIKE '{pattern}' THEN {i}")
        title_case = f"CASE {' '.join(title_case_parts)} ELSE 99 END"

        query = f"""
            WITH unfilled_slots AS (
                SELECT
                    cs.slot_id,
                    cs.outreach_id,
                    cs.company_unique_id
                FROM people.company_slot cs
                WHERE cs.slot_type = '{slot_type}'
                  AND (cs.is_filled = FALSE OR cs.is_filled IS NULL)
                  AND cs.outreach_id IS NOT NULL
            ),
            available_contacts AS (
                SELECT
                    hc.id as hunter_id,
                    hc.outreach_id,
                    hc.first_name,
                    hc.last_name,
                    hc.email,
                    hc.linkedin_url,
                    hc.job_title,
                    {title_case} as title_match_score
                FROM enrichment.hunter_contact hc
                WHERE hc.outreach_id IS NOT NULL
                  AND hc.first_name IS NOT NULL
                  AND hc.last_name IS NOT NULL
                  AND hc.email IS NOT NULL
            ),
            matched AS (
                SELECT
                    ac.hunter_id,
                    ac.outreach_id,
                    ac.first_name,
                    ac.last_name,
                    ac.email,
                    ac.linkedin_url,
                    ac.job_title,
                    us.slot_id,
                    us.company_unique_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY us.slot_id
                        ORDER BY ac.title_match_score, ac.hunter_id
                    ) as rank
                FROM available_contacts ac
                JOIN unfilled_slots us ON ac.outreach_id = us.outreach_id
            )
            SELECT
                hunter_id,
                outreach_id,
                first_name,
                last_name,
                email,
                linkedin_url,
                job_title,
                slot_id,
                company_unique_id
            FROM matched
            WHERE rank = 1;
        """

        cur.execute(query)
        matches = cur.fetchall()

        print(f"\nFound {len(matches):,} {slot_type} slot assignments")

        if not matches:
            return 0

        # Create people_master records and slot updates
        people_master_inserts = []
        slot_updates = []

        for row in matches:
            hunter_id, outreach_id, first_name, last_name, email, linkedin_url, job_title, slot_id, company_unique_id = row

            unique_id = generate_barton_id()

            people_master_inserts.append((
                unique_id,
                company_unique_id,
                slot_id,  # company_slot_unique_id
                first_name,
                last_name,
                email,
                linkedin_url,
                job_title,
                'hunter',
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            ))

            slot_updates.append((unique_id, slot_id))

        # Insert people_master records
        print(f"Inserting {len(people_master_inserts):,} people_master records...")
        execute_values(cur, """
            INSERT INTO people.people_master (
                unique_id, company_unique_id, company_slot_unique_id,
                first_name, last_name, email, linkedin_url, title,
                source_system, created_at, updated_at
            ) VALUES %s
            ON CONFLICT (unique_id) DO NOTHING;
        """, people_master_inserts)

        inserted = cur.rowcount
        print(f"  Inserted: {inserted:,} records")

        # Update slots
        print(f"Updating {len(slot_updates):,} slots...")
        execute_values(cur, """
            UPDATE people.company_slot AS cs
            SET
                person_unique_id = v.unique_id,
                is_filled = TRUE,
                filled_at = NOW(),
                source_system = 'hunter',
                updated_at = NOW()
            FROM (VALUES %s) AS v(unique_id, slot_id)
            WHERE cs.slot_id = v.slot_id::uuid;
        """, slot_updates)

        updated = cur.rowcount
        print(f"  Updated: {updated:,} slots")

        conn.commit()
        return updated

def final_report(conn):
    """Generate final report"""
    print("\n" + "="*80)
    print("FINAL SLOT FILL REPORT")
    print("="*80)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                slot_type,
                COUNT(*) as total,
                COUNT(CASE WHEN is_filled = TRUE THEN 1 END) as filled,
                ROUND(100.0 * COUNT(CASE WHEN is_filled = TRUE THEN 1 END) / COUNT(*), 1) as fill_rate
            FROM people.company_slot
            WHERE slot_type IN ('CEO', 'CFO', 'HR')
            GROUP BY slot_type
            ORDER BY slot_type;
        """)

        print(f"\n{'Slot Type':<12} {'Total':>10} {'Filled':>10} {'Fill Rate':>10}")
        print("-" * 50)

        totals = {'total': 0, 'filled': 0}
        for row in cur.fetchall():
            slot_type, total, filled, fill_rate = row
            print(f"{slot_type:<12} {total:>10,} {filled:>10,} {fill_rate:>9.1f}%")
            totals['total'] += total
            totals['filled'] += filled

        overall_rate = 100.0 * totals['filled'] / totals['total'] if totals['total'] > 0 else 0
        print("-" * 50)
        print(f"{'TOTAL':<12} {totals['total']:>10,} {totals['filled']:>10,} {overall_rate:>9.1f}%")

def main():
    """Main execution"""
    print("\n" + "="*80)
    print("HUNTER CONTACT SLOT ASSIGNMENT V3")
    print("="*80)
    print(f"Start Time: {datetime.now(timezone.utc).isoformat()}")

    conn = get_connection()

    try:
        # Analyze potential
        analyze_potential(conn)

        # Fill slots by type with title preferences
        ceo_filled = fill_slots_by_type(conn, 'CEO', [
            '%ceo%', '%chief executive%', '%president%', '%owner%', '%founder%'
        ])

        cfo_filled = fill_slots_by_type(conn, 'CFO', [
            '%cfo%', '%chief financial%', '%finance director%', '%controller%', '%treasurer%'
        ])

        hr_filled = fill_slots_by_type(conn, 'HR', [
            '%chief people%', '%hr %', '%human resource%', '%people %', '%talent%'
        ])

        # Final report
        final_report(conn)

        print("\n" + "="*80)
        print("ASSIGNMENT SUMMARY")
        print("="*80)
        print(f"  CEO Slots Filled: {ceo_filled:,}")
        print(f"  CFO Slots Filled: {cfo_filled:,}")
        print(f"  HR Slots Filled:  {hr_filled:,}")
        print(f"  TOTAL FILLED:     {ceo_filled + cfo_filled + hr_filled:,}")

        print("\n" + "="*80)
        print("HUNTER SLOT ASSIGNMENT COMPLETE")
        print("="*80)
        print(f"End Time: {datetime.now(timezone.utc).isoformat()}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
