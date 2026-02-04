#!/usr/bin/env python3
"""
Hunter DOL Slot Filling - LIVE EXECUTION
Fills CEO, CFO, and HR slots for Hunter DOL intake companies
"""

import psycopg2
import os
from datetime import datetime
from psycopg2.extras import execute_values

def get_title_priority_case(slot_type):
    """Generate CASE statement for title priority ranking"""
    if slot_type == 'CEO':
        return """
            CASE
                WHEN hc.job_title ILIKE '%ceo%' OR hc.job_title ILIKE '%chief executive%' THEN 1
                WHEN hc.job_title ILIKE '%president%' OR hc.job_title ILIKE '%owner%' OR hc.job_title ILIKE '%founder%' THEN 2
                WHEN hc.job_title ILIKE '%managing director%' OR hc.job_title ILIKE '%general manager%' THEN 3
                WHEN hc.job_title ILIKE '%coo%' OR hc.job_title ILIKE '%chief operating%' THEN 4
                WHEN hc.job_title ILIKE '%partner%' OR hc.job_title ILIKE '%vice president%' OR hc.job_title ILIKE '%vp %' THEN 5
                WHEN hc.job_title ILIKE '%director%' THEN 6
                WHEN hc.job_title ILIKE '%executive%' THEN 7
                ELSE 999
            END
        """
    elif slot_type == 'CFO':
        return """
            CASE
                WHEN hc.job_title ILIKE '%cfo%' OR hc.job_title ILIKE '%chief financial%' THEN 1
                WHEN hc.job_title ILIKE '%finance director%' OR hc.job_title ILIKE '%vp finance%' THEN 2
                WHEN hc.job_title ILIKE '%controller%' THEN 3
                WHEN hc.job_title ILIKE '%accounting director%' THEN 4
                WHEN hc.job_title ILIKE '%finance manager%' OR hc.job_title ILIKE '%accounting manager%' THEN 5
                WHEN hc.job_title ILIKE '%treasurer%' THEN 6
                WHEN hc.job_title ILIKE '%accountant%' THEN 7
                ELSE 999
            END
        """
    else:  # HR
        return """
            CASE
                WHEN hc.job_title ILIKE '%chro%' OR hc.job_title ILIKE '%chief human%' OR hc.job_title ILIKE '%chief people%' OR hc.job_title ILIKE '%vp human%' OR hc.job_title ILIKE '%head of hr%' THEN 1
                WHEN hc.job_title ILIKE '%hr director%' OR hc.job_title ILIKE '%human resources director%' THEN 2
                WHEN hc.job_title ILIKE '%senior hr%' OR hc.job_title ILIKE '%senior human resource%' THEN 3
                WHEN hc.job_title ILIKE '%hr manager%' OR hc.job_title ILIKE '%human resources manager%' THEN 4
                WHEN hc.job_title ILIKE '%benefit%' OR hc.job_title ILIKE '%payroll%' THEN 5
                WHEN hc.job_title ILIKE '%hr coordinator%' THEN 6
                WHEN hc.job_title ILIKE '%hr generalist%' OR hc.job_title ILIKE '%hr specialist%' THEN 7
                ELSE 999
            END
        """

def get_dept_filter(slot_type):
    """Get department filter for slot type"""
    if slot_type == 'CEO':
        return "hc.department IN ('Executive', 'Management')"
    elif slot_type == 'CFO':
        return "hc.department IN ('Finance', 'Executive', 'Management', 'Operations & logistics')"
    else:  # HR
        return "hc.department IN ('HR', 'Executive', 'Management', 'Operations & logistics')"

def get_title_filter(slot_type):
    """Get title patterns for slot type"""
    if slot_type == 'CEO':
        patterns = [
            "hc.job_title ILIKE '%ceo%' OR hc.job_title ILIKE '%chief executive%'",
            "hc.job_title ILIKE '%president%' OR hc.job_title ILIKE '%owner%' OR hc.job_title ILIKE '%founder%'",
            "hc.job_title ILIKE '%managing director%' OR hc.job_title ILIKE '%general manager%'",
            "hc.job_title ILIKE '%coo%' OR hc.job_title ILIKE '%chief operating%'",
            "hc.job_title ILIKE '%partner%' OR hc.job_title ILIKE '%vice president%' OR hc.job_title ILIKE '%vp %'",
            "hc.job_title ILIKE '%director%'",
            "hc.job_title ILIKE '%executive%'"
        ]
    elif slot_type == 'CFO':
        patterns = [
            "hc.job_title ILIKE '%cfo%' OR hc.job_title ILIKE '%chief financial%'",
            "hc.job_title ILIKE '%finance director%' OR hc.job_title ILIKE '%vp finance%'",
            "hc.job_title ILIKE '%controller%'",
            "hc.job_title ILIKE '%accounting director%'",
            "hc.job_title ILIKE '%finance manager%' OR hc.job_title ILIKE '%accounting manager%'",
            "hc.job_title ILIKE '%treasurer%'",
            "hc.job_title ILIKE '%accountant%'"
        ]
    else:  # HR
        patterns = [
            "hc.job_title ILIKE '%chro%' OR hc.job_title ILIKE '%chief human%' OR hc.job_title ILIKE '%chief people%' OR hc.job_title ILIKE '%vp human%' OR hc.job_title ILIKE '%head of hr%'",
            "hc.job_title ILIKE '%hr director%' OR hc.job_title ILIKE '%human resources director%'",
            "hc.job_title ILIKE '%senior hr%' OR hc.job_title ILIKE '%senior human resource%'",
            "hc.job_title ILIKE '%hr manager%' OR hc.job_title ILIKE '%human resources manager%'",
            "hc.job_title ILIKE '%benefit%' OR hc.job_title ILIKE '%payroll%'",
            "hc.job_title ILIKE '%hr coordinator%'",
            "hc.job_title ILIKE '%hr generalist%' OR hc.job_title ILIKE '%hr specialist%'"
        ]
    return ' OR '.join([f'({p})' for p in patterns])

def get_exclude_filter(slot_type):
    """Get exclude filter for HR"""
    if slot_type == 'HR':
        return "AND hc.job_title NOT ILIKE '%recruit%' AND hc.job_title NOT ILIKE '%talent acquisition%' AND hc.job_title NOT ILIKE '%staffing%'"
    return ''

def fill_slots_for_type(cur, slot_type, max_seq, batch_size=5000):
    """Fill slots for a specific slot type"""
    print(f'\n{"=" * 80}')
    print(f'PROCESSING {slot_type} SLOTS')
    print(f'{"=" * 80}')

    title_priority = get_title_priority_case(slot_type)
    dept_filter = get_dept_filter(slot_type)
    title_filter = get_title_filter(slot_type)
    exclude_filter = get_exclude_filter(slot_type)

    # Get ranked candidates
    print(f'\nStep 1: Ranking candidates for {slot_type} slots...')
    ranked_query = f"""
        WITH ranked_candidates AS (
            SELECT
                cs.slot_id,
                cs.outreach_id,
                o.domain,
                ci.company_unique_id,
                hc.first_name,
                hc.last_name,
                hc.email,
                hc.job_title,
                hc.department,
                hc.linkedin_url,
                hc.phone_number,
                hc.confidence_score,
                {title_priority} as title_priority,
                ROW_NUMBER() OVER (
                    PARTITION BY cs.slot_id
                    ORDER BY {title_priority}, hc.confidence_score DESC
                ) as rn
            FROM people.company_slot cs
            JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
            JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
            JOIN cl.company_identity ci ON o.outreach_id = ci.outreach_id
            JOIN enrichment.hunter_contact hc ON o.domain = hc.domain
            WHERE ct.source = 'hunter_dol_intake'
              AND cs.is_filled = false
              AND cs.slot_type = '{slot_type}'
              AND hc.email IS NOT NULL
              AND hc.email != ''
              AND hc.first_name IS NOT NULL
              AND hc.last_name IS NOT NULL
              AND (({dept_filter}) OR ({title_filter}))
              {exclude_filter}
        )
        SELECT
            slot_id,
            outreach_id,
            domain,
            company_unique_id,
            first_name,
            last_name,
            email,
            job_title,
            department,
            linkedin_url,
            phone_number,
            confidence_score,
            title_priority
        FROM ranked_candidates
        WHERE rn = 1
        ORDER BY slot_id
    """

    cur.execute(ranked_query)
    candidates = cur.fetchall()
    total_candidates = len(candidates)
    print(f'   Found {total_candidates:,} best candidates for {slot_type} slots')

    if total_candidates == 0:
        print(f'   No candidates found for {slot_type}. Skipping.')
        return max_seq

    # Process in batches
    people_created = 0
    slots_filled = 0
    current_seq = max_seq

    for batch_start in range(0, total_candidates, batch_size):
        batch_end = min(batch_start + batch_size, total_candidates)
        batch = candidates[batch_start:batch_end]
        batch_num = (batch_start // batch_size) + 1
        total_batches = (total_candidates + batch_size - 1) // batch_size

        print(f'\nBatch {batch_num}/{total_batches}: Processing records {batch_start+1:,} to {batch_end:,}')

        # Insert people_master records
        people_values = []
        slot_updates = []

        for row in batch:
            current_seq += 1
            person_unique_id = f'04.04.02.99.{current_seq:05d}.001'

            # Use company_unique_id (UUID) from cl.company_identity
            company_unique_id = str(row[3])

            people_values.append((
                person_unique_id,
                company_unique_id,
                str(row[0]),  # slot_id for company_slot_unique_id
                row[4],  # first_name
                row[5],  # last_name
                row[6],  # email
                row[7],  # title
                row[8],  # department
                row[9],  # linkedin_url
                row[10], # phone_number
                'hunter',
                datetime.now(),
                datetime.now()
            ))

            slot_updates.append((
                person_unique_id,
                float(row[11]) / 100.0 if row[11] else 0.0,  # confidence_score normalized
                'hunter',
                datetime.now(),
                str(row[0])  # slot_id
            ))

        # Insert people_master records
        people_insert = """
            INSERT INTO people.people_master (
                unique_id,
                company_unique_id,
                company_slot_unique_id,
                first_name,
                last_name,
                email,
                title,
                department,
                linkedin_url,
                work_phone_e164,
                source_system,
                created_at,
                updated_at
            ) VALUES %s
            ON CONFLICT (unique_id) DO NOTHING
        """

        execute_values(cur, people_insert, people_values)
        people_created += cur.rowcount

        # Update company_slot records
        slot_update = """
            UPDATE people.company_slot
            SET person_unique_id = data.person_unique_id,
                is_filled = true,
                filled_at = data.filled_at,
                confidence_score = data.confidence_score,
                source_system = data.source_system,
                updated_at = NOW()
            FROM (VALUES %s) AS data(person_unique_id, confidence_score, source_system, filled_at, slot_id_text)
            WHERE company_slot.slot_id = data.slot_id_text::uuid
        """

        execute_values(cur, slot_update, slot_updates)
        batch_slots_filled = cur.rowcount
        slots_filled += batch_slots_filled

        print(f'   Created {len(people_values):,} people_master records in this batch')
        print(f'   Updated {batch_slots_filled:,} company_slot records in this batch')

    print(f'\n{slot_type} SUMMARY:')
    print(f'   Total people_master records created: {people_created:,}')
    print(f'   Total company_slot records filled: {slots_filled:,}')

    return current_seq

def main():
    """Main execution"""
    conn = psycopg2.connect(
        host=os.getenv('NEON_HOST'),
        database=os.getenv('NEON_DATABASE'),
        user=os.getenv('NEON_USER'),
        password=os.getenv('NEON_PASSWORD'),
        sslmode='require'
    )
    conn.autocommit = False
    cur = conn.cursor()

    try:
        print('=' * 80)
        print('HUNTER DOL SLOT FILLING - LIVE EXECUTION')
        print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('=' * 80)

        # Get max sequence
        cur.execute("""
            SELECT MAX(
                CAST(SPLIT_PART(SPLIT_PART(unique_id, '.', 5), '.', 1) AS INTEGER)
            ) as max_seq
            FROM people.people_master
            WHERE unique_id LIKE '04.04.02.99.%'
        """)
        result = cur.fetchone()
        max_seq = result[0] if result[0] else 0
        print(f'\nStarting sequence: {max_seq}')

        # Process each slot type
        max_seq = fill_slots_for_type(cur, 'CEO', max_seq)
        max_seq = fill_slots_for_type(cur, 'CFO', max_seq)
        max_seq = fill_slots_for_type(cur, 'HR', max_seq)

        print(f'\n{"=" * 80}')
        print('COMMITTING TRANSACTION...')
        conn.commit()
        print('COMMITTED SUCCESSFULLY')

        # Final verification
        print(f'\n{"=" * 80}')
        print('FINAL VERIFICATION')
        print(f'{"=" * 80}')

        cur.execute("""
            SELECT
                cs.slot_type,
                COUNT(*) as filled_count
            FROM people.company_slot cs
            JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
            JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
            WHERE ct.source = 'hunter_dol_intake'
              AND cs.is_filled = true
              AND cs.slot_type IN ('CEO', 'CFO', 'HR')
              AND cs.source_system = 'hunter'
            GROUP BY cs.slot_type
            ORDER BY cs.slot_type
        """)

        print('\nFilled slots by type (Hunter DOL companies):')
        total_filled = 0
        for row in cur.fetchall():
            print(f'   {row[0]}: {row[1]:,}')
            total_filled += row[1]

        print(f'\nTOTAL SLOTS FILLED: {total_filled:,}')
        print(f'Final sequence: {max_seq}')
        print(f'\nCompleted: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('=' * 80)

    except Exception as e:
        print(f'\n{"!" * 80}')
        print(f'ERROR: {str(e)}')
        print(f'{"!" * 80}')
        conn.rollback()
        print('TRANSACTION ROLLED BACK')
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
