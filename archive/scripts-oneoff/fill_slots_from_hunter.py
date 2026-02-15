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

# DEPARTMENT-FIRST slot filling strategy
# Step 1: Filter by Department (column Q in Hunter CSV)
# Step 2: Then filter by Job Title (column R) and Position Raw (column S)
#
# This is more accurate than title-only matching because Hunter's
# Department field is already normalized.

SLOT_DEPARTMENT_MAP = {
    'CEO': ['Executive', 'Management'],  # Both departments have CEO-type contacts
    'CFO': ['Finance', 'Executive', 'Management', 'Operations & logistics'],  # CFO titles spread across depts
    'HR': ['HR', 'Executive', 'Management', 'Operations & logistics'],         # HR titles spread across depts
}

# For CFO/HR, we also do TITLE-BASED matching (ignores department)
# This catches CFO/HR people who are tagged as Executive, Management, or NULL department
# NOTE: HR excludes recruiters, talent acquisition, staffing
TITLE_BASED_PATTERNS = {
    'CFO': [
        '%cfo%', '%chief financial%', '%controller%', '%finance director%',
        '%vp finance%', '%vp of finance%', '%treasurer%', '%accounting director%',
        '%finance manager%', '%accounting manager%', '%comptroller%'
    ],
    'HR': [
        # HR Directors and Managers
        '%human resource% director%', '%hr director%', '%director of human%', '%director of hr%',
        '%human resource% manager%', '%hr manager%',
        # Head of HR
        '%head of human%', '%head of hr%',
        # VP and C-level HR
        '%vp%human resource%', '%vice president%human resource%', 
        '%chro%', '%chief human resource%', '%chief people%',
        # Senior HR
        '%senior%human resource%', '%senior hr%',
        '%senior human resource% manager%', '%senior hr manager%',
        # HR Coordinators
        '%human resource% coordinator%', '%hr coordinator%',
        # Benefits and Payroll (often handles benefits)
        '%benefit% manager%', '%benefit% director%', '%benefit% coordinator%',
        '%benefit% administrator%', '%benefit% specialist%',
        '%payroll manager%', '%payroll director%', '%payroll coordinator%',
        '%payroll administrator%', '%payroll specialist%',
    ],
}

# Within each department, prioritize by job title
# Higher priority = filled first (lower number = higher priority)
TITLE_PRIORITY = {
    'CEO': [
        # Priority 1: C-level executives
        ('%ceo%', 1), ('%chief executive%', 1), ('ceo', 1),
        # Priority 2: Presidents and owners
        ('%president%', 2), ('owner', 2), ('founder', 2),
        # Priority 3: Managing/General managers
        ('%managing director%', 3), ('%general manager%', 3),
        # Priority 4: COO (often acts as CEO)
        ('%coo%', 4), ('%chief operating%', 4),
        # Priority 5: Partners and VPs
        ('partner', 5), ('%vice president%', 5), ('%vp %', 5),
        # Priority 6: Directors
        ('%director%', 6),
        # Priority 7: Any executive title
        ('%executive%', 7),
    ],
    'CFO': [
        # Priority 1: CFO titles
        ('%cfo%', 1), ('%chief financial%', 1),
        # Priority 2: Finance directors/VPs
        ('%finance director%', 2), ('%vp finance%', 2), ('%vp of finance%', 2),
        # Priority 3: Controllers
        ('%controller%', 3), ('%financial controller%', 3),
        # Priority 4: Accounting directors
        ('%director of accounting%', 4), ('%accounting director%', 4),
        # Priority 5: Finance/Accounting managers
        ('%finance manager%', 5), ('%accounting manager%', 5),
        # Priority 6: Treasurers and analysts
        ('%treasurer%', 6), ('%financial analyst%', 6),
        # Priority 7: Accountants
        ('%accountant%', 7),
    ],
    'HR': [
        # Priority 1: CHRO / VP HR / Head of HR
        ('%chro%', 1), ('%chief human%', 1), ('%chief people%', 1),
        ('%vp human%', 1), ('%vp of human%', 1), ('%vice president of human%', 1),
        ('%head of human%', 1), ('%head of hr%', 1),
        # Priority 2: HR Directors
        ('%hr director%', 2), ('%human resources director%', 2), 
        ('%director of human%', 2), ('%director of hr%', 2),
        # Priority 3: Senior HR (including Senior HR Manager)
        ('%senior%human resource%', 3), ('%senior hr%', 3), ('%senior director%human%', 3),
        ('%senior human resources manager%', 3), ('%senior hr manager%', 3),
        # Priority 4: HR Managers
        ('%hr manager%', 4), ('%human resources manager%', 4),
        # Priority 5: Benefits and Payroll
        ('%benefit%', 5), ('%payroll%', 5),
        # Priority 6: HR Coordinators
        ('%hr coordinator%', 6), ('%human resources coordinator%', 6),
        # Priority 7: HR generalists and specialists (no recruiters)
        ('%hr generalist%', 7), ('%hr specialist%', 7), 
        ('%human resources generalist%', 7), ('%human resources specialist%', 7),
    ],
}

def build_department_filter(slot_type):
    """Build SQL WHERE clause filtering by DEPARTMENT or TITLE."""
    departments = SLOT_DEPARTMENT_MAP[slot_type]
    
    # For CFO and HR, use TITLE-based matching (more inclusive)
    if slot_type in TITLE_BASED_PATTERNS:
        title_patterns = TITLE_BASED_PATTERNS[slot_type]
        title_conditions = [f"LOWER(hc.job_title) LIKE '{p}'" for p in title_patterns]
        # Also include department match
        dept_list = ", ".join(f"'{d}'" for d in departments)
        return f"(hc.department IN ({dept_list}) OR ({' OR '.join(title_conditions)}))"
    
    # For CEO, use department-based matching
    if len(departments) == 1:
        return f"hc.department = '{departments[0]}'"
    else:
        dept_list = ", ".join(f"'{d}'" for d in departments)
        return f"hc.department IN ({dept_list})"


def build_title_priority_case(slot_type):
    """Build SQL CASE statement to rank contacts by job title priority."""
    priorities = TITLE_PRIORITY[slot_type]
    
    # Build CASE statement for ranking
    cases = []
    for pattern, priority in priorities:
        if '%' in pattern:
            cases.append(f"WHEN LOWER(COALESCE(hc.job_title, '') || ' ' || COALESCE(hc.position_raw, '')) LIKE '{pattern}' THEN {priority}")
        else:
            cases.append(f"WHEN LOWER(COALESCE(hc.job_title, '') || ' ' || COALESCE(hc.position_raw, '')) = '{pattern}' THEN {priority}")
    
    # Default priority (lowest) for contacts that don't match any pattern
    return "CASE " + " ".join(cases) + " ELSE 99 END"


def get_fillable_slots(cur, slot_type, limit=None):
    """
    Get empty slots with matching Hunter contacts using DEPARTMENT-FIRST logic.
    
    Strategy:
      1. Filter by Hunter department (Executive→CEO, Finance→CFO, HR→HR)
      2. Rank contacts within department by job title priority
      3. Pick best contact per slot (highest priority, then highest confidence)
    
    Join path:
      company_slot → company_target → outreach.outreach (domain) 
      → company.company_master (Barton ID via website_url) → hunter_contact
    """
    dept_filter = build_department_filter(slot_type)
    title_priority = build_title_priority_case(slot_type)
    
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
                hc.position_raw,
                hc.department,
                hc.linkedin_url,
                hc.phone_number,
                hc.confidence_score,
                {title_priority} as title_priority,
                ROW_NUMBER() OVER (
                    PARTITION BY cs.slot_id 
                    ORDER BY 
                        {title_priority} ASC,  -- Lower priority number = better match
                        hc.confidence_score DESC NULLS LAST, 
                        hc.id
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
            AND {dept_filter}
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
            confidence_score,
            title_priority
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
             department, linkedin_url, phone_number, confidence_score, title_priority) = slot
            
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
    print("HUNTER -> SLOT FILLER")
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
