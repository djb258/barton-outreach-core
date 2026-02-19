#!/usr/bin/env python3
"""
Fill people slots from Clay CSV with Executive Contacts column.

Parses slot_type:linkedin_url from Executive Contacts column,
extracts names from Contacts JSON or LinkedIn slug,
and fills CEO/CFO/HR slots in people.company_slot + people.people_master.

Usage:
    doppler run -- python scripts/fill_slots_from_clay_csv.py <csv_path> --dry-run
    doppler run -- python scripts/fill_slots_from_clay_csv.py <csv_path>
"""
import os
import sys
import io
import csv
import json
import re
import argparse
from datetime import datetime, timezone

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import psycopg2

BAD_DOMAINS = {
    'jnj.com', 'bbb.org', 'judge.com', 'privco.com', 'buzzfile.com',
    'seakexperts.com', 'doitbest.com', 'trinet.com', 'adp.com', 'chubb.com',
    'allstate.com', 'apple.com', 'microsoft.com', 'google.com', 'amazon.com',
    'salesforce.com', 'disney.com', 'king.com', 'acme.com', 'guidestar.org',
    'seamless.ai', 'rocketreach.co', 'marketsizeandtrends.com',
    'nucor.com', 'l3harris.com', 'coca-colacompany.com', 'northropgrumman.com',
    'motorolasolutions.com', 'illumina.com', 'healthgrades.com',
}


def get_conn():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        dbname=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require',
    )


def name_from_slug(linkedin_url):
    """Extract first/last name from LinkedIn slug like /in/john-smith-a1b2c3d4/."""
    slug = linkedin_url.rstrip('/').split('/')[-1]
    parts = slug.split('-')
    # Remove trailing hex hash
    if parts and len(parts[-1]) >= 6 and all(c in '0123456789abcdef' for c in parts[-1]):
        parts = parts[:-1]
    if len(parts) >= 2:
        return parts[0].title(), ' '.join(p.title() for p in parts[1:])
    elif len(parts) == 1:
        return parts[0].title(), ''
    return '', ''


def parse_contacts(rows, spine_map):
    """Parse all contacts from CSV rows, match to outreach_ids."""
    contacts = []

    for r in rows:
        oid = r.get('outreach_id', '').strip()
        company = r.get('company_name', '').strip()
        domain = r.get('Domain', '').strip().lower()
        ec = r.get('Executive Contacts', '').strip()
        cj = r.get('Contacts JSON', '').strip()

        if not ec or 'linkedin.com' not in ec:
            continue
        if domain in BAD_DOMAINS:
            continue

        # Try domain bridge if no outreach_id
        if not oid and domain and domain in spine_map:
            oid = spine_map[domain]
        if not oid:
            continue

        # Parse Contacts JSON for rich person data
        json_people = {}
        if cj:
            try:
                data = json.loads(cj)
                for p in data.get('people', []):
                    url = (p.get('url') or '').strip().rstrip('/')
                    if url:
                        json_people[url.lower()] = {
                            'first_name': p.get('first_name', ''),
                            'last_name': p.get('last_name', ''),
                            'title': p.get('title', ''),
                            'headline': p.get('headline', ''),
                        }
            except Exception:
                pass

        # Parse Executive Contacts: "CEO:https://linkedin.com/in/..., HR:https://..."
        parts = [p.strip() for p in ec.split(', ') if ':https://' in p]
        for p in parts:
            idx = p.index(':https://')
            slot_type = p[:idx].strip().upper()
            linkedin = 'https://' + p[idx + 9:].strip().rstrip('/')

            if slot_type not in ('CEO', 'CFO', 'HR'):
                continue
            if 'linkedin.com/in/' not in linkedin:
                continue

            # Get name from JSON or slug
            person = json_people.get(linkedin.lower(), {})
            first_name = person.get('first_name', '')
            last_name = person.get('last_name', '')
            title = person.get('title', '') or person.get('headline', '')

            if not first_name:
                first_name, last_name = name_from_slug(linkedin)

            if not first_name:
                continue  # Can't fill slot without a name

            contacts.append({
                'outreach_id': oid,
                'company_name': company,
                'domain': domain,
                'slot_type': slot_type,
                'linkedin_url': linkedin,
                'first_name': first_name,
                'last_name': last_name,
                'title': title,
            })

    return contacts


def dedup_contacts(contacts):
    """Keep first contact per (outreach_id, slot_type) — one person per slot."""
    seen = set()
    deduped = []
    for c in contacts:
        key = (c['outreach_id'], c['slot_type'])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(c)
    return deduped


def main():
    parser = argparse.ArgumentParser(description='Fill slots from Clay CSV')
    parser.add_argument('csv_path', help='Path to Clay CSV')
    parser.add_argument('--dry-run', action='store_true', help='Preview without DB writes')
    args = parser.parse_args()

    print("=" * 60)
    print("Fill People Slots from Clay CSV")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)

    # Load CSV
    with open(args.csv_path, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    print(f"  CSV rows: {len(rows):,}")

    conn = get_conn()
    cur = conn.cursor()

    # Build spine domain map
    cur.execute("""
        SELECT LOWER(TRIM(domain)), outreach_id::text
        FROM outreach.outreach
        WHERE domain IS NOT NULL AND LENGTH(TRIM(domain)) > 0
    """)
    spine_map = {d.lower().strip(): oid for d, oid in cur.fetchall()}

    # Parse contacts
    contacts = parse_contacts(rows, spine_map)
    print(f"  Parsed contacts (linkable, named): {len(contacts):,}")

    # Dedup — one person per slot per company
    contacts = dedup_contacts(contacts)
    print(f"  After dedup (1 per slot): {len(contacts):,}")

    ceo = sum(1 for c in contacts if c['slot_type'] == 'CEO')
    cfo = sum(1 for c in contacts if c['slot_type'] == 'CFO')
    hr = sum(1 for c in contacts if c['slot_type'] == 'HR')
    unique_cos = len(set(c['outreach_id'] for c in contacts))
    print(f"  CEO: {ceo}, CFO: {cfo}, HR: {hr}")
    print(f"  Unique companies: {unique_cos}")

    # Load existing slots to check what's already filled
    oid_list = list(set(c['outreach_id'] for c in contacts))
    filled_slots = set()
    for i in range(0, len(oid_list), 5000):
        chunk = oid_list[i:i + 5000]
        cur.execute("""
            SELECT outreach_id::text, slot_type
            FROM people.company_slot
            WHERE outreach_id = ANY(%s::uuid[])
              AND is_filled = TRUE
        """, (chunk,))
        filled_slots.update((r[0], r[1]) for r in cur.fetchall())

    # Filter out already-filled slots
    to_fill = [c for c in contacts if (c['outreach_id'], c['slot_type']) not in filled_slots]
    already = len(contacts) - len(to_fill)
    print(f"\n  Already filled (skip): {already}")
    print(f"  To fill: {len(to_fill)}")

    if not to_fill:
        print("  Nothing to do.")
        conn.close()
        return

    # Load slot IDs + company_unique_id for matching
    slot_map = {}  # (outreach_id, slot_type) -> (slot_id, company_unique_id)
    for i in range(0, len(oid_list), 5000):
        chunk = oid_list[i:i + 5000]
        cur.execute("""
            SELECT outreach_id::text, slot_type, slot_id::text, company_unique_id
            FROM people.company_slot
            WHERE outreach_id = ANY(%s::uuid[])
        """, (chunk,))
        for oid, st, sid, cuid in cur.fetchall():
            slot_map[(oid, st)] = (sid, cuid)

    # Fill slots
    print(f"\n{'=' * 60}")
    print("FILLING SLOTS")
    print(f"{'=' * 60}")

    filled = 0
    no_slot = 0
    errors = 0
    year = datetime.now().year % 100
    BARTON_PREFIX = "04.04.02"

    # Get current max Barton ID sequence for this year
    cur.execute("""
        SELECT MAX(CAST(SPLIT_PART(unique_id, '.', 5) AS INTEGER))
        FROM people.people_master
        WHERE unique_id LIKE %s
    """, (f"{BARTON_PREFIX}.{year:02d}.%",))
    next_seq = (cur.fetchone()[0] or 0) + 1
    print(f"  Barton ID sequence starts at: {BARTON_PREFIX}.{year:02d}.{next_seq}")

    for c in to_fill:
        slot_key = (c['outreach_id'], c['slot_type'])
        slot_info = slot_map.get(slot_key)

        if not slot_info:
            no_slot += 1
            continue

        slot_id, company_unique_id = slot_info

        if args.dry_run:
            filled += 1
            next_seq += 1
            continue

        try:
            # Generate Barton ID: 04.04.02.YY.NNNNNN.NNN
            suffix = str(next_seq)[-3:].zfill(3)
            people_uid = f"{BARTON_PREFIX}.{year:02d}.{next_seq}.{suffix}"

            # Create people_master record
            # NOTE: full_name is a GENERATED column — do not include in INSERT
            cur.execute("""
                INSERT INTO people.people_master (
                    unique_id, company_unique_id, first_name, last_name,
                    title, linkedin_url, source_system,
                    company_slot_unique_id, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT DO NOTHING
            """, (people_uid, company_unique_id, c['first_name'], c['last_name'],
                  c['title'] or c['slot_type'],
                  c['linkedin_url'], 'clay_28461_enrichment', slot_id))

            if cur.rowcount > 0:
                # Mark slot as filled
                cur.execute("""
                    UPDATE people.company_slot
                    SET is_filled = TRUE, person_unique_id = %s,
                        updated_at = NOW()
                    WHERE slot_id = %s::uuid AND is_filled = FALSE
                """, (people_uid, slot_id))

                filled += 1
                next_seq += 1
            else:
                errors += 1

            if filled % 100 == 0 and filled > 0:
                conn.commit()
                print(f"    ... filled {filled:,}")

        except Exception as e:
            print(f"    ERROR {c['outreach_id']}/{c['slot_type']}: {e}")
            conn.rollback()
            errors += 1

    if not args.dry_run:
        conn.commit()

    print(f"\n{'=' * 60}")
    print("RESULTS")
    print(f"{'=' * 60}")
    print(f"  Slots filled:  {filled:,}")
    print(f"  No slot found: {no_slot:,}")
    print(f"  Errors:        {errors:,}")
    print(f"  Already filled: {already:,}")

    if not args.dry_run and filled > 0:
        # Verify
        cur.execute("""
            SELECT slot_type, COUNT(*)
            FROM people.company_slot
            WHERE outreach_id = ANY(%s::uuid[]) AND is_filled = TRUE
            GROUP BY slot_type ORDER BY slot_type
        """, (oid_list,))
        print(f"\n  Verification (filled slots for these companies):")
        for st, cnt in cur.fetchall():
            print(f"    {st}: {cnt:,}")

    conn.close()


if __name__ == '__main__':
    main()
