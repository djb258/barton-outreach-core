#!/usr/bin/env python3
"""
Promote Intake to Slots

Moves people from intake.people_raw_intake to people.people_master and fills slots.

Flow:
    1. Read unprocessed records from intake (validated = FALSE)
    2. Match domain to company (outreach + company_master)
    3. Find slot by company_uuid + slot_type
    4. Insert into people_master, update slot
    5. Mark intake as validated = TRUE

Usage:
    doppler run -- python scripts/promote_intake_to_slots.py [--state XX] [--slot-type CEO]
"""

import os
import sys
import re
import psycopg2
from datetime import datetime

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[FAIL] DATABASE_URL not set")
        sys.exit(1)
    return psycopg2.connect(database_url)


def generate_person_id(row_num: int) -> str:
    """Generate Barton-format person ID: 04.04.02.XX.XXXXX.XXX"""
    return f"04.04.02.99.{row_num:05d}.{row_num % 1000:03d}"


def generate_slot_barton_id(row_num: int) -> str:
    """Generate Barton-format slot ID: 04.04.05.XX.XXXXX.XXX"""
    return f"04.04.05.99.{row_num:05d}.{row_num % 1000:03d}"


def promote_intake(state_filter=None, slot_filter=None, limit=None):
    """Promote intake records to people_master and fill slots."""

    print("=" * 70)
    print("PROMOTE INTAKE TO SLOTS")
    print("=" * 70)

    conn = get_connection()
    cur = conn.cursor()

    # Build domain lookups
    print("\nBuilding domain lookups...")

    # UUID lookup: domain -> sovereign_id (for slot lookup)
    cur.execute("""
        SELECT LOWER(domain), sovereign_id
        FROM outreach.outreach
        WHERE domain IS NOT NULL
    """)
    domain_to_uuid = {r[0]: r[1] for r in cur.fetchall()}
    print(f"  outreach domains: {len(domain_to_uuid):,}")

    # Barton lookup: domain -> company_unique_id (for people_master)
    cur.execute("""
        SELECT LOWER(REPLACE(REPLACE(REPLACE(website_url, 'https://', ''), 'http://', ''), 'www.', '')),
               company_unique_id
        FROM company.company_master
        WHERE website_url IS NOT NULL AND company_unique_id LIKE '04.04.01%'
    """)
    domain_to_barton = {}
    for r in cur.fetchall():
        domain = r[0].split('/')[0]
        domain_to_barton[domain] = r[1]
    print(f"  company Barton IDs: {len(domain_to_barton):,}")

    # Get max existing person ID to set offset
    cur.execute("SELECT MAX(unique_id) FROM people.people_master WHERE unique_id LIKE '04.04.02%'")
    max_id = cur.fetchone()[0]
    if max_id:
        # Extract the 5-digit number
        parts = max_id.split('.')
        offset = int(parts[4]) + 1000
    else:
        offset = 20000
    print(f"  ID offset: {offset}")

    # Build query for intake records
    query = """
        SELECT id, first_name, last_name, full_name, title,
               company_name, linkedin_url, source_record_id,
               state_abbrev, slot_type
        FROM intake.people_raw_intake
        WHERE validated = FALSE
    """
    params = []

    if state_filter:
        query += " AND state_abbrev = %s"
        params.append(state_filter)

    if slot_filter:
        query += " AND slot_type = %s"
        params.append(slot_filter)

    if limit:
        query += f" LIMIT {limit}"

    cur.execute(query, params)
    records = cur.fetchall()
    print(f"\nProcessing {len(records):,} intake records...")

    stats = {
        'total': len(records),
        'matched': 0,
        'slots_found': 0,
        'slots_filled': 0,
        'already_filled': 0,
        'people_created': 0,
        'errors': 0
    }

    row_num = offset

    for record in records:
        intake_id, first_name, last_name, full_name, title, company_name, linkedin_url, domain, state, slot_type = record

        if not domain:
            stats['errors'] += 1
            continue

        domain = domain.lower().strip()

        # Need both UUID and Barton ID
        company_uuid = domain_to_uuid.get(domain)
        company_barton = domain_to_barton.get(domain)

        if not company_uuid or not company_barton:
            continue

        stats['matched'] += 1

        # Find slot
        cur.execute("""
            SELECT slot_id, person_unique_id, is_filled
            FROM people.company_slot
            WHERE company_unique_id = %s AND slot_type = %s
            LIMIT 1
        """, (company_uuid, slot_type))

        slot = cur.fetchone()
        if not slot:
            continue

        stats['slots_found'] += 1
        slot_id, existing_person, is_filled = slot

        if is_filled and existing_person:
            stats['already_filled'] += 1
            # Mark as validated even if slot was filled
            cur.execute("UPDATE intake.people_raw_intake SET validated = TRUE, validated_at = NOW() WHERE id = %s", (intake_id,))
            conn.commit()
            continue

        row_num += 1
        person_id = generate_person_id(row_num)
        slot_barton_id = generate_slot_barton_id(row_num)

        # Clean name for email
        first_clean = re.sub(r'[^a-z]', '', (first_name or '').lower())
        last_clean = re.sub(r'[^a-z]', '', (last_name or '').lower())

        try:
            # Insert into people_master
            cur.execute("""
                INSERT INTO people.people_master (
                    unique_id, company_unique_id, company_slot_unique_id,
                    first_name, last_name, title, linkedin_url,
                    source_system, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'intake_promotion', NOW())
                ON CONFLICT (unique_id) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    title = EXCLUDED.title,
                    linkedin_url = EXCLUDED.linkedin_url,
                    updated_at = NOW()
            """, (person_id, company_barton, slot_barton_id, first_name, last_name, title, linkedin_url))
            stats['people_created'] += 1

            # Update slot
            cur.execute("""
                UPDATE people.company_slot
                SET person_unique_id = %s,
                    is_filled = TRUE,
                    filled_at = NOW(),
                    source_system = 'intake_promotion',
                    updated_at = NOW()
                WHERE slot_id = %s
            """, (person_id, slot_id))
            stats['slots_filled'] += 1

            # Mark intake as validated
            cur.execute("""
                UPDATE intake.people_raw_intake
                SET validated = TRUE, validated_at = NOW()
                WHERE id = %s
            """, (intake_id,))

            conn.commit()

        except Exception as e:
            conn.rollback()
            stats['errors'] += 1
            if stats['errors'] <= 5:
                print(f"  Error: {str(e)[:80]}")

    cur.close()
    conn.close()

    # Summary
    print("\n" + "=" * 70)
    print("PROMOTION SUMMARY")
    print("=" * 70)
    print(f"  Total intake records: {stats['total']:,}")
    print(f"  Domains matched: {stats['matched']:,}")
    print(f"  Slots found: {stats['slots_found']:,}")
    print(f"  Already filled: {stats['already_filled']:,}")
    print(f"  New slots filled: {stats['slots_filled']:,}")
    print(f"  People created: {stats['people_created']:,}")
    print(f"  Errors: {stats['errors']:,}")

    return stats


if __name__ == "__main__":
    state = None
    slot = None
    limit = None

    # Parse args
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--state' and i + 1 < len(args):
            state = args[i + 1].upper()
            i += 2
        elif args[i] == '--slot-type' and i + 1 < len(args):
            slot = args[i + 1].upper()
            i += 2
        elif args[i] == '--limit' and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        else:
            i += 1

    if state:
        print(f"Filter: state={state}")
    if slot:
        print(f"Filter: slot_type={slot}")
    if limit:
        print(f"Limit: {limit}")

    promote_intake(state, slot, limit)
