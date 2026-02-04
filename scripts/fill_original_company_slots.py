#!/usr/bin/env python3
"""
LIVE SLOT FILLING - ORIGINAL COMPANIES ONLY
Fills unfilled slots (CEO, CFO, HR) for non-hunter_dol_intake companies using Hunter contacts.
Follows SLOT_FILLING_GUIDE.md title priority rules.
"""

import psycopg2
import os
from datetime import datetime, timezone
from typing import Dict, List, Tuple

# Title priority rules from SLOT_FILLING_GUIDE.md
TITLE_PRIORITY = {
    'CEO': {
        'departments': ['executive', 'management'],
        'titles': ['ceo', 'chief executive', 'president', 'owner', 'founder'],
        'priority_order': [
            'ceo', 'chief executive officer', 'president', 'founder',
            'owner', 'managing director', 'general manager'
        ]
    },
    'CFO': {
        'departments': ['finance', 'executive', 'management', 'operations'],
        'titles': ['cfo', 'chief financial', 'controller', 'finance director',
                   'vp finance', 'treasurer', 'accounting'],
        'priority_order': [
            'cfo', 'chief financial officer', 'controller', 'finance director',
            'vp finance', 'vice president of finance', 'treasurer',
            'director of accounting', 'accounting manager'
        ]
    },
    'HR': {
        'departments': ['hr', 'human resources', 'executive', 'management', 'operations'],
        'titles': ['human resource', 'hr director', 'hr manager', 'benefit',
                   'payroll', 'chro', 'chief people'],
        'exclude_titles': ['recruit', 'talent acquisition', 'staffing'],
        'priority_order': [
            'chro', 'chief human resources officer', 'chief people officer',
            'hr director', 'director of human resources', 'hr manager',
            'benefits director', 'payroll director', 'people operations'
        ]
    }
}

def connect_db():
    """Connect to Neon database."""
    return psycopg2.connect(
        host=os.getenv('NEON_HOST'),
        database=os.getenv('NEON_DATABASE'),
        user=os.getenv('NEON_USER'),
        password=os.getenv('NEON_PASSWORD'),
        sslmode='require'
    )

def get_next_sequence(cur, batch_size: int = 1) -> List[str]:
    """
    Generate next unique_id sequence for people_master.
    Format: 04.04.02.99.NNNNN.NNN

    Starting new major sequence after 99999.999 exhaustion.
    """
    # Start fresh at 100000.001
    cur.execute("""
        SELECT COALESCE(MAX(unique_id), '04.04.02.99.99999.999')
        FROM people.people_master
        WHERE unique_id LIKE '04.04.02.99.%';
    """)

    max_id = cur.fetchone()[0]
    parts = max_id.split('.')
    major = int(parts[4])
    minor = int(parts[5])

    # If we've exhausted 99999.999, start at 100000.001
    if major == 99999 and minor >= 999:
        major = 100000
        minor = 0

    sequences = []
    for i in range(batch_size):
        minor += 1
        if minor > 999:
            minor = 1
            major += 1
        sequences.append(f'04.04.02.99.{major:05d}.{minor:03d}')

    return sequences

def calculate_title_priority(slot_type: str, job_title: str, department: str) -> int:
    """
    Calculate priority score for a contact based on title and department.
    Lower score = higher priority.
    Returns 999 if title doesn't match slot requirements.
    """
    if not job_title:
        return 999

    job_title_lower = job_title.lower()
    dept_lower = department.lower() if department else ''
    rules = TITLE_PRIORITY[slot_type]

    # HR exclusion rule
    if slot_type == 'HR':
        for exclude in rules.get('exclude_titles', []):
            if exclude in job_title_lower:
                return 999

    # Check priority order
    for idx, priority_title in enumerate(rules['priority_order']):
        if priority_title in job_title_lower:
            return idx

    # Check general title matches
    for idx, title in enumerate(rules['titles']):
        if title in job_title_lower:
            return 100 + idx  # Lower priority than exact matches

    # Check department matches
    for idx, dept in enumerate(rules['departments']):
        if dept in dept_lower:
            return 200 + idx  # Lower priority than title matches

    return 999  # No match

def fill_slots_for_type(cur, slot_type: str) -> Dict:
    """
    Fill unfilled slots for a specific slot type using Hunter contacts.
    Returns stats about fills.
    """
    print(f'\n=== Processing {slot_type} Slots ===\n')

    # Step 1: Find matching candidates with title priority
    print('Finding matching candidates...')

    cur.execute("""
        WITH unfilled_slots AS (
            SELECT
                cs.slot_id,
                cs.company_unique_id,
                cs.slot_type,
                o.domain,
                ci.outreach_id
            FROM people.company_slot cs
            JOIN cl.company_identity ci ON cs.company_unique_id = ci.company_unique_id::text
            JOIN outreach.outreach o ON ci.outreach_id = o.outreach_id
            WHERE cs.is_filled = false
              AND cs.slot_type = %s
              AND (ci.source_system <> 'hunter_dol_intake' OR ci.source_system IS NULL)
        ),
        matching_contacts AS (
            SELECT
                us.slot_id,
                us.company_unique_id,
                us.slot_type,
                us.outreach_id,
                hc.first_name,
                hc.last_name,
                hc.email,
                hc.job_title,
                hc.linkedin_url,
                hc.phone_number,
                hc.department,
                hc.confidence_score,
                hc.domain
            FROM unfilled_slots us
            JOIN enrichment.hunter_contact hc ON LOWER(us.domain) = LOWER(hc.domain)
            WHERE hc.confidence_score > 0
              AND hc.email IS NOT NULL
              AND hc.job_title IS NOT NULL
              AND hc.first_name IS NOT NULL
              AND hc.last_name IS NOT NULL
        )
        SELECT
            slot_id,
            company_unique_id,
            slot_type,
            outreach_id,
            first_name,
            last_name,
            email,
            job_title,
            linkedin_url,
            phone_number,
            department,
            confidence_score,
            domain
        FROM matching_contacts;
    """, (slot_type,))

    candidates = cur.fetchall()
    print(f'Found {len(candidates)} candidate matches')

    if not candidates:
        return {'filled': 0, 'skipped': 0}

    # Step 2: Calculate title priority and rank candidates
    print('Ranking candidates by title priority...')

    ranked_candidates = {}
    for row in candidates:
        slot_id = row[0]
        title_priority = calculate_title_priority(slot_type, row[7], row[10])

        if title_priority == 999:
            continue  # Skip non-matching titles

        if slot_id not in ranked_candidates:
            ranked_candidates[slot_id] = []

        ranked_candidates[slot_id].append({
            'slot_id': row[0],
            'company_unique_id': row[1],
            'slot_type': row[2],
            'outreach_id': row[3],
            'first_name': row[4],
            'last_name': row[5],
            'email': row[6],
            'job_title': row[7],
            'linkedin_url': row[8],
            'phone_number': row[9],
            'department': row[10],
            'confidence_score': row[11],
            'domain': row[12],
            'title_priority': title_priority
        })

    print(f'Ranked candidates for {len(ranked_candidates)} slots')

    # Step 3: Select best candidate per slot
    print('Selecting best candidate per slot...')

    best_candidates = []
    for slot_id, candidates_list in ranked_candidates.items():
        # Sort by title_priority ASC, then confidence_score DESC
        sorted_candidates = sorted(
            candidates_list,
            key=lambda x: (x['title_priority'], -x['confidence_score'])
        )
        best_candidates.append(sorted_candidates[0])

    print(f'Selected {len(best_candidates)} best candidates')

    if not best_candidates:
        return {'filled': 0, 'skipped': 0}

    # Step 4: Get unique_id sequences
    print('Generating unique_id sequences...')
    sequences = get_next_sequence(cur, len(best_candidates))

    # Step 5: Insert into people_master and update company_slot
    print('Inserting people_master records and updating slots...')

    filled_count = 0
    now = datetime.now(timezone.utc)

    for idx, candidate in enumerate(best_candidates):
        unique_id = sequences[idx]

        # Insert into people_master
        cur.execute("""
            INSERT INTO people.people_master (
                unique_id,
                company_unique_id,
                company_slot_unique_id,
                first_name,
                last_name,
                email,
                title,
                linkedin_url,
                work_phone_e164,
                department,
                source_system,
                created_at,
                updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'hunter', %s, %s
            )
            ON CONFLICT (unique_id) DO NOTHING;
        """, (
            unique_id,
            candidate['company_unique_id'],
            str(candidate['slot_id']),
            candidate['first_name'],
            candidate['last_name'],
            candidate['email'],
            candidate['job_title'],
            candidate['linkedin_url'],
            candidate['phone_number'],
            candidate['department'],
            now,
            now
        ))

        # Update company_slot
        cur.execute("""
            UPDATE people.company_slot
            SET
                person_unique_id = %s,
                is_filled = true,
                filled_at = %s,
                confidence_score = %s,
                source_system = 'hunter',
                updated_at = %s
            WHERE slot_id = %s
              AND is_filled = false;
        """, (
            unique_id,
            now,
            candidate['confidence_score'] / 100.0,
            now,
            candidate['slot_id']
        ))

        if cur.rowcount > 0:
            filled_count += 1

    print(f'Successfully filled {filled_count} {slot_type} slots')

    return {
        'filled': filled_count,
        'skipped': len(best_candidates) - filled_count
    }

def main():
    """Main execution function."""
    print('='*80)
    print('LIVE SLOT FILLING - ORIGINAL COMPANIES ONLY')
    print('='*80)
    print(f'Started at: {datetime.now(timezone.utc).isoformat()}Z')
    print()

    conn = connect_db()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # Process each slot type
        results = {}
        for slot_type in ['CEO', 'CFO', 'HR']:
            results[slot_type] = fill_slots_for_type(cur, slot_type)

        # Commit transaction
        print('\n=== Committing Transaction ===\n')
        conn.commit()
        print('Transaction committed successfully!')

        # Print summary
        print('\n' + '='*80)
        print('SLOT FILLING SUMMARY')
        print('='*80)

        total_filled = 0
        for slot_type, stats in results.items():
            print(f'{slot_type:3}: {stats["filled"]:,} filled, {stats["skipped"]:,} skipped')
            total_filled += stats['filled']

        print(f'\nTOTAL FILLED: {total_filled:,}')
        print(f'Completed at: {datetime.now(timezone.utc).isoformat()}Z')

    except Exception as e:
        print(f'\nERROR: {e}')
        print('Rolling back transaction...')
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()
