#!/usr/bin/env python3
"""
WV Executive Import Script

Imports executive data from Clay CSV files directly into slots.

Join Chain:
    CSV Company Domain → marketing.company_master.domain → company_unique_id
    → people.company_slot (where slot_type matches) → update person_unique_id
    → Insert into people.people_master

Usage:
    doppler run -- python scripts/import_wv_executives.py <csv_path> --slot-type CEO
"""

import os
import sys
import csv
import uuid
import psycopg2
from datetime import datetime

# Windows encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def get_connection():
    """Get database connection."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[FAIL] DATABASE_URL not set")
        sys.exit(1)
    return psycopg2.connect(database_url)


def normalize_domain(domain: str) -> str:
    """Normalize domain for matching."""
    if not domain:
        return ""
    domain = domain.lower().strip()
    domain = domain.replace('https://', '').replace('http://', '').replace('www.', '')
    domain = domain.split('/')[0]
    return domain


def generate_person_id(row_num: int) -> str:
    """Generate Barton-format person ID: 04.04.02.XX.XXXXX.XXX"""
    return f"04.04.02.99.{row_num:05d}.{row_num % 1000:03d}"


def generate_slot_barton_id(row_num: int) -> str:
    """Generate Barton-format slot ID: 04.04.05.XX.XXXXX.XXX"""
    return f"04.04.05.99.{row_num:05d}.{row_num % 1000:03d}"


def import_executives(csv_path: str, slot_type: str = "CEO") -> dict:
    """
    Import executives from CSV into slots.

    Join Chain:
        CSV Company Domain -> outreach.outreach.domain -> sovereign_id (UUID)
        sovereign_id = people.company_slot.company_unique_id

    Returns: Statistics dict
    """
    print(f"\n{'='*60}")
    print(f"WV EXECUTIVE IMPORT - {slot_type}")
    print(f"{'='*60}")
    print(f"CSV: {csv_path}")
    print(f"Slot Type: {slot_type}")

    conn = get_connection()
    cur = conn.cursor()

    stats = {
        'total_records': 0,
        'domains_matched': 0,
        'slots_found': 0,
        'slots_filled': 0,
        'slots_already_filled': 0,
        'people_created': 0,
        'errors': []
    }

    # Step 1a: Build domain → sovereign_id (UUID) from outreach.outreach (for slot lookup)
    print("\nLoading company domain lookup from outreach.outreach...")
    cur.execute("""
        SELECT LOWER(domain) as domain, sovereign_id
        FROM outreach.outreach
        WHERE domain IS NOT NULL AND domain != ''
    """)
    domain_to_uuid = {}
    for row in cur.fetchall():
        domain_to_uuid[row[0]] = row[1]
    print(f"  Loaded {len(domain_to_uuid)} domains with sovereign_ids (UUID)")

    # Step 1b: Build domain → Barton company_unique_id from company.company_master
    print("Loading Barton company IDs from company.company_master...")
    cur.execute("""
        SELECT LOWER(REPLACE(REPLACE(REPLACE(website_url, 'https://', ''), 'http://', ''), 'www.', '')) as domain,
               company_unique_id
        FROM company.company_master
        WHERE website_url IS NOT NULL AND company_unique_id LIKE '04.04.01%'
    """)
    domain_to_barton = {}
    for row in cur.fetchall():
        domain = row[0].split('/')[0]
        domain_to_barton[domain] = row[1]
    print(f"  Loaded {len(domain_to_barton)} domains with Barton IDs")

    # Step 1c: Load email patterns from marketing.company_master (by domain)
    cur.execute("""
        SELECT LOWER(domain) as domain, email_pattern
        FROM marketing.company_master
        WHERE domain IS NOT NULL AND email_pattern IS NOT NULL
    """)
    pattern_lookup = {}
    for row in cur.fetchall():
        pattern_lookup[row[0]] = row[1]
    print(f"  Loaded {len(pattern_lookup)} email patterns")

    # Step 2: Load CSV records
    print(f"\nLoading CSV records...")
    records = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    stats['total_records'] = len(records)
    print(f"  Loaded {len(records)} records")

    # Step 3: Match domains - need BOTH UUID (for slot) AND Barton ID (for people_master)
    print("\nMatching domains to companies...")
    matched_records = []
    for i, row in enumerate(records):
        domain = normalize_domain(row.get('Company Domain', ''))

        # Need both UUID and Barton ID
        uuid_company_id = domain_to_uuid.get(domain)
        barton_company_id = domain_to_barton.get(domain)

        if uuid_company_id and barton_company_id:
            matched_records.append({
                'row': row,
                'domain': domain,
                'company_uuid': uuid_company_id,      # For slot lookup
                'company_barton': barton_company_id,  # For people_master
                'email_pattern': pattern_lookup.get(domain),
                'row_num': i + 1
            })
    stats['domains_matched'] = len(matched_records)
    print(f"  Matched {len(matched_records)} of {len(records)} domains (with both UUID and Barton ID)")

    # Step 4: Find slots and insert people
    print(f"\nProcessing {slot_type} slots...")

    for record in matched_records:
        row = record['row']
        company_uuid = record['company_uuid']      # UUID for slot lookup
        company_barton = record['company_barton']  # Barton ID for people_master
        domain = record['domain']
        row_num = record['row_num']

        # Find the slot for this company + slot_type (using UUID)
        cur.execute("""
            SELECT slot_id, person_unique_id, is_filled
            FROM people.company_slot
            WHERE company_unique_id = %s AND slot_type = %s
            LIMIT 1
        """, (company_uuid, slot_type))

        slot = cur.fetchone()
        if not slot:
            stats['errors'].append(f"No slot found for {company_uuid[:8]}... / {slot_type}")
            continue

        stats['slots_found'] += 1
        slot_id, existing_person, is_filled = slot

        # Skip if already filled with someone
        if is_filled and existing_person:
            stats['slots_already_filled'] += 1
            continue

        # Generate person ID and slot Barton ID (offset to avoid conflicts with existing data)
        # Max existing IDs are around 1200, so start at 10000 for safety
        offset = 10000
        person_id = generate_person_id(row_num + offset)
        slot_barton_id = generate_slot_barton_id(row_num + offset)

        # Extract person data from CSV
        first_name = row.get('First Name', '').strip()
        last_name = row.get('Last Name', '').strip()
        full_name = row.get('Full Name', '').strip() or f"{first_name} {last_name}".strip()
        job_title = row.get('Job Title', '').strip()
        linkedin_url = row.get('LinkedIn Profile', '').strip()
        company_name = row.get('Company Name', '').strip()
        location = row.get('Location', '').strip()

        # Generate email if pattern exists
        email = None
        if record['email_pattern'] and first_name and last_name:
            try:
                import re
                # Clean name components - ASCII alphanumeric only
                first_clean = re.sub(r'[^a-z]', '', first_name.lower())
                last_clean = re.sub(r'[^a-z]', '', last_name.lower())

                if first_clean and last_clean:
                    email = record['email_pattern'].format(
                        first=first_clean,
                        last=last_clean,
                        f=first_clean[0] if first_clean else '',
                        l=last_clean[0] if last_clean else '',
                        domain=domain
                    )
                    # Validate email format before using
                    if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
                        email = None
            except (KeyError, IndexError):
                # Pattern doesn't match expected format
                if first_clean and last_clean:
                    email = f"{first_clean}.{last_clean}@{domain}"

        try:
            # Insert into people.people_master (full_name is generated, don't insert)
            # slot_id is used as company_slot_unique_id
            cur.execute("""
                INSERT INTO people.people_master (
                    unique_id, company_unique_id, company_slot_unique_id, first_name, last_name,
                    title, linkedin_url, email, source_system, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, 'wv_executive_import', NOW()
                )
                ON CONFLICT (unique_id) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    title = EXCLUDED.title,
                    linkedin_url = EXCLUDED.linkedin_url,
                    email = EXCLUDED.email,
                    company_slot_unique_id = EXCLUDED.company_slot_unique_id,
                    updated_at = NOW()
            """, (
                person_id, company_barton, slot_barton_id, first_name, last_name,
                job_title, linkedin_url, email
            ))
            stats['people_created'] += 1

            # Update slot with person
            cur.execute("""
                UPDATE people.company_slot
                SET person_unique_id = %s,
                    is_filled = TRUE,
                    filled_at = NOW(),
                    source_system = 'wv_executive_import',
                    updated_at = NOW()
                WHERE slot_id = %s
            """, (person_id, slot_id))
            stats['slots_filled'] += 1

            # Commit after each successful insert to preserve progress
            conn.commit()

        except Exception as e:
            conn.rollback()
            stats['errors'].append(f"Error inserting {full_name}: {str(e)[:100]}")
            continue
    cur.close()
    conn.close()

    # Summary
    print(f"\n{'='*60}")
    print("IMPORT SUMMARY")
    print(f"{'='*60}")
    print(f"  Total records: {stats['total_records']}")
    print(f"  Domains matched: {stats['domains_matched']}")
    print(f"  Slots found: {stats['slots_found']}")
    print(f"  Slots already filled: {stats['slots_already_filled']}")
    print(f"  New slots filled: {stats['slots_filled']}")
    print(f"  People created: {stats['people_created']}")

    if stats['errors']:
        print(f"\n  Errors ({len(stats['errors'])}):")
        for err in stats['errors'][:5]:
            print(f"    - {err}")

    return stats


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_wv_executives.py <csv_path> [--slot-type TYPE]")
        print("")
        print("Options:")
        print("  --slot-type TYPE   Slot type: CEO, CFO, HR (default: CEO)")
        sys.exit(1)

    csv_path = sys.argv[1]

    # Parse slot-type
    slot_type = "CEO"
    if '--slot-type' in sys.argv:
        idx = sys.argv.index('--slot-type')
        if idx + 1 < len(sys.argv):
            slot_type = sys.argv[idx + 1].upper()

    if not os.path.exists(csv_path):
        print(f"[FAIL] CSV not found: {csv_path}")
        sys.exit(1)

    stats = import_executives(csv_path, slot_type)

    print(f"\nDone. Filled {stats['slots_filled']} {slot_type} slots.")
