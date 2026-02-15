#!/usr/bin/env python3
"""
Migrate 130 records from outreach.appointments (legacy) to sales.appointments_already_had (new).

Column mapping:
  Legacy                          → New
  ─────────────────────────────────────────────
  appointment_id                  → source_record_id
  outreach_id                     → outreach_id
  (lookup via outreach_id)        → company_id (from cl.company_identity)
  (lookup via contact_email)      → people_id (from people.people_master)
  appt_date (or created_at)       → meeting_date
  'discovery'                     → meeting_type (default)
  'progressed'                    → meeting_outcome (default)
  'manual'                        → source
  contact/company/notes as JSON   → metadata

Usage:
    doppler run -- python scripts/migrate_appointments.py [--dry-run]
"""
import os
import sys
import io
import json
from datetime import date

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import psycopg2
import re

UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)

def is_uuid(val):
    return bool(val and UUID_RE.match(str(val)))

def main():
    dry_run = '--dry-run' in sys.argv

    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    print("=" * 60)
    print("MIGRATE APPOINTMENTS: outreach.appointments → sales.appointments_already_had")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")

    # Check current state
    cur.execute("SELECT COUNT(*) FROM outreach.appointments")
    legacy_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM sales.appointments_already_had")
    new_count = cur.fetchone()[0]
    print(f"\n  Legacy table:  {legacy_count:,} records")
    print(f"  New table:     {new_count:,} records")

    if new_count > 0:
        print("  [WARN] New table already has records. Will skip duplicates via ON CONFLICT.")

    # Fetch all legacy records
    cur.execute("""
        SELECT
            a.appointment_id,
            a.outreach_id,
            a.domain,
            a.appt_date,
            a.contact_first_name,
            a.contact_last_name,
            a.contact_title,
            a.contact_email,
            a.contact_phone,
            a.company_name,
            a.address_1,
            a.city,
            a.state,
            a.zip,
            a.county,
            a.notes,
            a.prospect_keycode_id,
            a.appt_number,
            a.created_at
        FROM outreach.appointments a
        ORDER BY a.appointment_id
    """)
    rows = cur.fetchall()
    print(f"\n  Fetched {len(rows):,} legacy records")

    # Build lookup: outreach_id → company_unique_id (sovereign_id in CL)
    cur.execute("""
        SELECT ci.outreach_id, ci.company_unique_id
        FROM cl.company_identity ci
        WHERE ci.outreach_id IS NOT NULL
    """)
    oid_to_cid = {str(r[0]): r[1] for r in cur.fetchall()}

    # Build lookup: email → people unique_id
    cur.execute("""
        SELECT LOWER(email), unique_id
        FROM people.people_master
        WHERE email IS NOT NULL AND email <> ''
    """)
    email_to_pid = {r[0]: r[1] for r in cur.fetchall()}

    migrated = 0
    skipped = 0
    no_date = 0

    for row in rows:
        (appt_id, outreach_id, domain, appt_date,
         first_name, last_name, title, email, phone,
         company_name, address, city, state, zipcode, county,
         notes, keycode_id, appt_number, created_at) = row

        # meeting_date: use appt_date, fall back to created_at date
        if appt_date:
            meeting_date = appt_date
        elif created_at:
            meeting_date = created_at.date()
            no_date += 1
        else:
            meeting_date = date(2026, 2, 4)  # load date as last resort
            no_date += 1

        # Resolve company_id from outreach_id
        company_id = None
        if outreach_id:
            company_id = oid_to_cid.get(str(outreach_id))

        # Resolve people_id from email (must be UUID for the column type)
        people_id = None
        if email:
            pid_candidate = email_to_pid.get(email.lower().strip())
            if pid_candidate and is_uuid(pid_candidate):
                people_id = pid_candidate

        # Generate deterministic appointment_uid
        cid_str = str(company_id) if company_id else (domain or company_name or 'unknown')
        pid_str = str(people_id) if people_id else (email or f"{first_name}_{last_name}" or 'unknown')
        appointment_uid = f"{cid_str}|{pid_str}|{meeting_date}"

        # Pack legacy data into metadata
        metadata = {}
        if first_name:
            metadata['contact_first_name'] = first_name
        if last_name:
            metadata['contact_last_name'] = last_name
        if title:
            metadata['contact_title'] = title
        if email:
            metadata['contact_email'] = email
        if phone:
            metadata['contact_phone'] = phone
        if company_name:
            metadata['company_name'] = company_name
        if address:
            metadata['address'] = address
        if city:
            metadata['city'] = city
        if state:
            metadata['state'] = state
        if zipcode:
            metadata['zip'] = zipcode
        if county:
            metadata['county'] = county
        if domain:
            metadata['domain'] = domain
        if keycode_id:
            metadata['prospect_keycode_id'] = int(keycode_id)
        if appt_number:
            metadata['appt_number'] = appt_number
        if notes:
            metadata['notes'] = notes[:2000]  # cap notes length in jsonb

        if dry_run:
            migrated += 1
            continue

        try:
            cur.execute("""
                INSERT INTO sales.appointments_already_had (
                    appointment_uid, company_id, people_id, outreach_id,
                    meeting_date, meeting_type, meeting_outcome,
                    source, source_record_id, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (appointment_uid) DO NOTHING
            """, (
                appointment_uid,
                company_id,
                people_id,
                outreach_id,
                meeting_date,
                'discovery',   # default meeting_type
                'progressed',  # default meeting_outcome
                'manual',      # source
                str(appt_id),  # original appointment_id as source_record_id
                json.dumps(metadata)
            ))
            if cur.rowcount > 0:
                migrated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  [ERROR] {appt_id}: {str(e)[:100]}")
            conn.rollback()
            skipped += 1

    if not dry_run:
        conn.commit()

    # Verify
    cur.execute("SELECT COUNT(*) FROM sales.appointments_already_had")
    final_count = cur.fetchone()[0]

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Legacy records:      {len(rows):,}")
    print(f"  Migrated:            {migrated:,}")
    print(f"  Skipped (duplicate): {skipped:,}")
    print(f"  Used fallback date:  {no_date:,}")
    print(f"  Final new table:     {final_count:,}")

    conn.close()


if __name__ == "__main__":
    main()
