#!/usr/bin/env python3
"""
Fill empty company slots from Hunter enrichment data.

Join path:
  people.company_slot.outreach_id 
  → outreach.company_target.outreach_id 
  → outreach.outreach.outreach_id
  → outreach.outreach.domain 
  → enrichment.hunter_contact.domain

Only fills slots where we have a matching person TYPE:
- CEO slots: CEO, Chief Executive, President, Owner, Founder
- CFO slots: CFO, Chief Financial, Finance department
- HR slots: HR titles, Human Resources, HR department
"""
import psycopg2
from psycopg2.extras import execute_values
import os
from datetime import datetime

# Title matching patterns for each slot type
SLOT_PATTERNS = {
    'CEO': {
        'title_patterns': ['%ceo%', '%chief executive%', '%president%'],
        'exact_titles': ['owner', 'founder'],
        'departments': []
    },
    'CFO': {
        'title_patterns': ['%cfo%', '%chief financial%', '%controller%', '%treasurer%'],
        'exact_titles': [],
        'departments': ['Finance']
    },
    'HR': {
        'title_patterns': ['%hr %', '%human resource%', '%talent%', '%recruiting%', '%people operations%'],
        'exact_titles': [],
        'departments': ['HR']
    }
}

def build_title_filter(slot_type):
    """Build SQL WHERE clause for title matching."""
    patterns = SLOT_PATTERNS[slot_type]
    conditions = []
    
    for p in patterns['title_patterns']:
        conditions.append(f"LOWER(hc.job_title) LIKE '{p}'")
    
    for t in patterns['exact_titles']:
        conditions.append(f"LOWER(hc.job_title) = '{t}'")
    
    for d in patterns['departments']:
        conditions.append(f"hc.department = '{d}'")
    
    return '(' + ' OR '.join(conditions) + ')'


def get_fillable_slots(cur, slot_type, limit=None):
    """
    Get empty slots with matching Hunter contacts.
    Returns one best contact per slot (highest confidence).
    
    Join path:
      company_slot → company_target → outreach.outreach (domain) 
      → company.company_master (Barton ID via website_url) → hunter_contact
    """
    title_filter = build_title_filter(slot_type)
    
    limit_clause = f"LIMIT {limit}" if limit else ""
    
    # Using string formatting since we control the slot_type values
    query = f"""
        WITH cm_domains AS (
            SELECT 
                company_unique_id,
                LOWER(REGEXP_REPLACE(
                    REGEXP_REPLACE(website_url, '^https?://(www\\.)?', ''),
                    '/.*$', ''
                )) as domain
            FROM company.company_master
            WHERE website_url IS NOT NULL
        ),
        ranked_contacts AS (
            SELECT 
                cs.slot_id,
                cs.outreach_id,
                cmd.company_unique_id as barton_company_id,
                o.domain,
                hc.first_name,
                hc.last_name,
                hc.email,
                hc.job_title,
                hc.department,
                hc.linkedin_url,
                hc.phone_number,
                hc.confidence_score,
                ROW_NUMBER() OVER (
                    PARTITION BY cs.slot_id 
                    ORDER BY hc.confidence_score DESC NULLS LAST, hc.id
                ) as rn
            FROM people.company_slot cs
            JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
            JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
            JOIN cm_domains cmd ON cmd.domain = LOWER(o.domain)
            JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
            WHERE cs.is_filled = false
            AND cs.slot_type = '{slot_type}'
            AND hc.email IS NOT NULL
            AND hc.first_name IS NOT NULL
            AND hc.last_name IS NOT NULL
            AND cmd.company_unique_id IS NOT NULL
            AND {title_filter}
        )
        SELECT 
            slot_id,
            outreach_id,
            barton_company_id,
            domain,
            first_name,
            last_name,
            email,
            job_title,
            department,
            linkedin_url,
            phone_number,
            confidence_score
        FROM ranked_contacts
        WHERE rn = 1
        {limit_clause}
    """
    
    cur.execute(query)
    return cur.fetchall()


# Global counter for ID generation
_person_seq_counter = None

def get_next_person_seq(cur):
    """Get next person sequence number, using in-memory counter."""
    global _person_seq_counter
    
    if _person_seq_counter is None:
        # Initialize from database
        cur.execute("""
            SELECT COALESCE(
                MAX(CAST(SPLIT_PART(unique_id, '.', 5) AS INTEGER)),
                0
            )
            FROM people.people_master
            WHERE unique_id LIKE '04.04.02.%'
        """)
        _person_seq_counter = cur.fetchone()[0]
    
    _person_seq_counter += 1
    return _person_seq_counter


def generate_person_id(cur):
    """Generate a new Barton doctrine person ID."""
    # Format: 04.04.02.XX.NNNNN.NNN (people spoke)
    next_seq = get_next_person_seq(cur)
    
    # Simple checksum (last 3 digits)
    checksum = next_seq % 1000
    
    # Use 99 as the type code for Hunter-sourced records
    return f"04.04.02.99.{next_seq:05d}.{checksum:03d}"


def generate_slot_unique_id(person_seq):
    """Generate slot unique ID matching person sequence."""
    # Format: 04.04.05.XX.NNNNN.NNN (slot spoke)
    checksum = person_seq % 1000
    return f"04.04.05.99.{person_seq:05d}.{checksum:03d}"


def fill_slots(conn, slot_type, batch_size=100, dry_run=True):
    """Fill slots of given type from Hunter data."""
    cur = conn.cursor()
    
    # Get fillable slots
    slots = get_fillable_slots(cur, slot_type)
    print(f"\n{slot_type} slots to fill: {len(slots):,}")
    
    if not slots:
        return 0
    
    filled_count = 0
    
    for i in range(0, len(slots), batch_size):
        batch = slots[i:i+batch_size]
        
        people_values = []
        slot_updates = []
        
        for slot in batch:
            (slot_id, outreach_id, barton_company_id,
             domain, first_name, last_name, email, job_title, 
             department, linkedin_url, phone_number, confidence_score) = slot
            
            # Generate person ID
            person_id = generate_person_id(cur)
            # Extract sequence from person_id for slot_unique_id
            person_seq = int(person_id.split('.')[4])
            slot_unique_id = generate_slot_unique_id(person_seq)
            
            # Prepare people_master record
            # Note: full_name is a generated column, don't insert it
            people_values.append((
                person_id,           # unique_id
                barton_company_id,   # company_unique_id (Barton format)
                slot_unique_id,      # company_slot_unique_id
                first_name,          # first_name
                last_name,           # last_name
                job_title,           # title
                department,          # seniority (using department as proxy)
                department,          # department
                email,               # email
                phone_number,        # work_phone_e164
                linkedin_url,        # linkedin_url
                'hunter',            # source_system
            ))
            
            slot_updates.append((person_id, (confidence_score or 50) / 100.0, slot_id))
        
        if dry_run:
            print(f"  [DRY RUN] Would insert {len(people_values)} people and update {len(slot_updates)} slots")
            for p in people_values[:3]:
                print(f"    - {p[3]} {p[4]} <{p[8]}> @ company {p[1]}")
            if len(people_values) > 3:
                print(f"    ... and {len(people_values) - 3} more")
        else:
            # Insert people
            execute_values(cur, """
                INSERT INTO people.people_master 
                (unique_id, company_unique_id, company_slot_unique_id, 
                 first_name, last_name, title, seniority, department,
                 email, work_phone_e164, linkedin_url, source_system)
                VALUES %s
                ON CONFLICT (unique_id) DO NOTHING
            """, people_values)
            
            # Update slots
            execute_values(cur, """
                UPDATE people.company_slot 
                SET is_filled = true,
                    person_unique_id = data.person_id,
                    confidence_score = data.confidence,
                    filled_at = NOW(),
                    source_system = 'hunter'
                FROM (VALUES %s) AS data(person_id, confidence, slot_id)
                WHERE company_slot.slot_id = data.slot_id::uuid
            """, slot_updates)
            
            conn.commit()
            print(f"  Filled batch {i//batch_size + 1}: {len(slot_updates)} slots")
        
        filled_count += len(slot_updates)
    
    return filled_count


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fill slots from Hunter data')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Preview without making changes (default)')
    parser.add_argument('--execute', action='store_true',
                        help='Actually execute the changes')
    parser.add_argument('--slot-type', choices=['CEO', 'CFO', 'HR', 'ALL'],
                        default='ALL', help='Which slot type to fill')
    parser.add_argument('--batch-size', type=int, default=100,
                        help='Batch size for inserts')
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    
    print("=" * 60)
    print("HUNTER → SLOT FILLER")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    print(f"Slot type: {args.slot_type}")
    print(f"Batch size: {args.batch_size}")
    
    slot_types = ['CEO', 'CFO', 'HR'] if args.slot_type == 'ALL' else [args.slot_type]
    
    total_filled = 0
    for slot_type in slot_types:
        filled = fill_slots(conn, slot_type, args.batch_size, dry_run)
        total_filled += filled
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {total_filled:,} slots {'would be' if dry_run else ''} filled")
    print("=" * 60)
    
    if dry_run:
        print("\nTo execute, run with --execute flag")
    
    conn.close()


if __name__ == '__main__':
    main()
