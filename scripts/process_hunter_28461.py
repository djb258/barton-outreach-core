#!/usr/bin/env python3
"""
Process Hunter enrichment results for 28461/100mi market (SA-003 David Vang).

Pipeline:
  STEP 1: Load contacts into enrichment.hunter_contact
  STEP 2: Mint outreach_ids for NEW companies (outreach.outreach -> CL write-back)
  STEP 3: Create company_target records for NEW companies
  STEP 4: Ensure company_slots exist (CEO/CFO/HR) for all companies
  STEP 5: Fill slots with best Hunter contact per slot type + create people_master
  STEP 6: Update email_method on company_target where missing

Usage:
    doppler run -- python scripts/process_hunter_28461.py [--dry-run]
"""
import os
import sys
import io
import csv
import re
import uuid
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import psycopg2

DRY_RUN = '--dry-run' in sys.argv

CSV_WITH_DOMAINS = r'C:\Users\CUSTOM PC\Desktop\dave-vang-with-domains-2134454.csv'
CSV_NO_DOMAINS = r'C:\Users\CUSTOM PC\Desktop\dave-vang-no-domains-2134453.csv'


def get_conn():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        dbname=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require',
    )


def clean(val):
    """Clean nan/empty strings."""
    if val is None:
        return ''
    s = str(val).strip()
    return '' if s.lower() == 'nan' else s


def get_slot_type(department, job_title):
    """Map Hunter department/title to CEO/CFO/HR slot type."""
    dept = (department or '').lower().strip()
    title = (job_title or '').lower().strip()

    # HR
    if dept == 'hr' or any(kw in title for kw in [
        'human resource', 'chro', 'chief people', 'head of people',
        'vp of people', 'director of people', 'benefits manager',
        'benefits director', 'hr director', 'hr manager',
        'vice president of human', 'director of human',
    ]):
        return 'HR'

    # CFO
    if any(kw in title for kw in [
        'cfo', 'chief financial', 'controller', 'comptroller',
        'finance director', 'vp finance', 'vp of finance',
        'treasurer', 'head of finance', 'director of finance',
        'vice president of finance', 'chief accounting',
    ]):
        return 'CFO'

    # CEO
    if any(kw in title for kw in [
        'ceo', 'chief executive', 'president', 'owner', 'founder',
        'co-founder', 'cofounder', 'managing director', 'managing partner',
        'general manager', 'principal', 'executive director',
        'chairman', 'executive vice president',
    ]):
        return 'CEO'

    # Fallback by department for senior titles
    if dept == 'finance' and any(kw in title for kw in [
        'director', 'vp', 'vice president', 'head', 'chief', 'manager',
    ]):
        return 'CFO'
    if dept in ('executive', 'management') and any(kw in title for kw in [
        'director', 'vp', 'vice president', 'head', 'chief', 'partner',
    ]):
        return 'CEO'

    return None


def parse_headcount(headcount_str):
    """Parse '51-200' -> 51 (lower bound)."""
    if not headcount_str:
        return None
    m = re.match(r'(\d[\d,]*)', str(headcount_str).replace(',', ''))
    return int(m.group(1)) if m else None


def next_barton_seq(cur):
    """Get next Barton ID sequence for people_master (04.04.02.26.NNNNNN.NNN)."""
    cur.execute("""
        SELECT MAX(CAST(SPLIT_PART(unique_id, '.', 5) AS INTEGER))
        FROM people.people_master
        WHERE unique_id LIKE '04.04.02.26.%%'
    """)
    row = cur.fetchone()
    return (row[0] or 0) + 1 if row else 1


def barton_id(seq, sub=1):
    return f"04.04.02.26.{seq:06d}.{sub:03d}"


def main():
    print("=" * 60)
    print("PROCESS HUNTER RESULTS - 28461/100mi (SA-003 David Vang)")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE'}")
    print(f"Started: {datetime.now().isoformat()}")

    # ── Load CSVs ──
    with open(CSV_WITH_DOMAINS, 'r', encoding='utf-8') as f:
        rows_with = list(csv.DictReader(f))
    with open(CSV_NO_DOMAINS, 'r', encoding='utf-8') as f:
        rows_no = list(csv.DictReader(f))

    print(f"\n  With-domains CSV: {len(rows_with):,} rows")
    print(f"  No-domains CSV:  {len(rows_no):,} rows")

    # ── Classify: EXISTING_GAP vs NEW ──
    existing_gap = {}   # outreach_id -> [contacts]
    new_companies = {}  # sovereign_id -> {info + contacts}

    for row in rows_with:
        sid = clean(row.get('sovereign_id'))
        oid = clean(row.get('outreach_id'))
        source = clean(row.get('source'))

        if oid and source == 'EXISTING_GAP':
            existing_gap.setdefault(oid, []).append(row)
        elif sid:
            if sid not in new_companies:
                new_companies[sid] = {
                    'sovereign_id': sid,
                    'domain': clean(row.get('domain')) or clean(row.get('Domain name')),
                    'company_name': clean(row.get('company_name')),
                    'city': clean(row.get('city')),
                    'state': clean(row.get('state')),
                    'zip': clean(row.get('zip')),
                    'ein': clean(row.get('ein')),
                    'contacts': [],
                }
            new_companies[sid]['contacts'].append(row)

    for row in rows_no:
        sid = clean(row.get('sovereign_id'))
        if not sid:
            continue
        domain = clean(row.get('Domain name'))
        if sid not in new_companies:
            new_companies[sid] = {
                'sovereign_id': sid,
                'domain': domain,
                'company_name': clean(row.get('company_name')),
                'city': clean(row.get('city')),
                'state': clean(row.get('state')),
                'zip': clean(row.get('zip')),
                'ein': clean(row.get('ein')),
                'contacts': [],
            }
        elif domain and not new_companies[sid].get('domain'):
            new_companies[sid]['domain'] = domain
        new_companies[sid]['contacts'].append(row)

    total_new_contacts = sum(len(c['contacts']) for c in new_companies.values())
    total_existing_contacts = sum(len(c) for c in existing_gap.values())

    print(f"\n  EXISTING_GAP: {len(existing_gap):,} companies ({total_existing_contacts:,} contacts)")
    print(f"  NEW:          {len(new_companies):,} companies ({total_new_contacts:,} contacts)")

    conn = get_conn()
    cur = conn.cursor()

    # ==============================================================
    # STEP 1: Load contacts into enrichment.hunter_contact
    # ==============================================================
    print(f"\n{'=' * 60}")
    print("STEP 1: Load contacts into enrichment.hunter_contact")
    print(f"{'=' * 60}")

    # Pre-load existing domains in hunter_company (FK target)
    cur.execute("SELECT LOWER(domain) FROM enrichment.hunter_company")
    existing_hc_domains = {r[0] for r in cur.fetchall()}
    print(f"  Existing hunter_company domains: {len(existing_hc_domains):,}")

    cur.execute("SELECT LOWER(email) FROM enrichment.hunter_contact WHERE email IS NOT NULL")
    existing_emails = {r[0] for r in cur.fetchall()}
    print(f"  Existing emails in hunter_contact: {len(existing_emails):,}")

    all_contacts = rows_with + rows_no
    loaded = 0
    skipped = 0
    domains_inserted = 0

    for row in all_contacts:
        email = clean(row.get('Email address')).lower()
        if not email or email in existing_emails:
            skipped += 1
            continue

        domain = clean(row.get('Domain name')).lower()
        first_name = clean(row.get('First name'))
        last_name = clean(row.get('Last name'))
        job_title = clean(row.get('Job title'))
        linkedin = clean(row.get('LinkedIn URL'))
        phone = clean(row.get('Phone number'))
        conf_raw = clean(row.get('Confidence score'))

        try:
            confidence = int(conf_raw) if conf_raw else None
        except ValueError:
            confidence = None

        if not DRY_RUN:
            try:
                # Ensure domain exists in hunter_company (FK requirement)
                if domain and domain not in existing_hc_domains:
                    cur.execute("""
                        INSERT INTO enrichment.hunter_company (domain, created_at)
                        VALUES (%s, NOW())
                        ON CONFLICT DO NOTHING
                    """, (domain,))
                    if cur.rowcount > 0:
                        domains_inserted += 1
                    existing_hc_domains.add(domain)

                cur.execute("""
                    INSERT INTO enrichment.hunter_contact (
                        email, domain, first_name, last_name, job_title,
                        linkedin_url, phone_number, confidence_score,
                        source_file, created_at
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                    ON CONFLICT DO NOTHING
                """, (
                    email, domain or None, first_name or None, last_name or None,
                    job_title or None, linkedin or None, phone or None,
                    confidence, 'hunter-28461-100mi',
                ))
                if cur.rowcount > 0:
                    loaded += 1
                    existing_emails.add(email)
                else:
                    skipped += 1
            except Exception as e:
                print(f"    ERROR loading {email}: {e}")
                conn.rollback()
                skipped += 1
        else:
            loaded += 1
            existing_emails.add(email)

    if not DRY_RUN:
        conn.commit()
    print(f"  Domains added to hunter_company: {domains_inserted:,}")
    print(f"  Contacts loaded: {loaded:,}")
    print(f"  Skipped (existing): {skipped:,}")

    # ==============================================================
    # STEP 2: Mint outreach_ids for NEW companies
    # ==============================================================
    print(f"\n{'=' * 60}")
    print("STEP 2: Mint outreach_ids for NEW companies")
    print(f"{'=' * 60}")

    sids = list(new_companies.keys())
    if sids:
        cur.execute("""
            SELECT company_unique_id::text, outreach_id::text
            FROM cl.company_identity
            WHERE company_unique_id = ANY(%s::uuid[])
        """, (sids,))
        cl_state = {r[0]: r[1] for r in cur.fetchall()}
    else:
        cl_state = {}

    already_have_oid = sum(1 for v in cl_state.values() if v)
    need_mint = [sid for sid in sids if sid in cl_state and not cl_state[sid]]
    not_in_cl = [sid for sid in sids if sid not in cl_state]

    print(f"  CL records found:         {len(cl_state):,}")
    print(f"  Already have outreach_id: {already_have_oid:,}")
    print(f"  Need minting:             {len(need_mint):,}")
    if not_in_cl:
        print(f"  WARNING: {len(not_in_cl):,} sovereign_ids NOT in CL (skipping)")

    minted = 0
    mint_errors = 0
    oid_map = {}  # sovereign_id -> outreach_id

    # Include already-minted ones
    for sid, oid in cl_state.items():
        if oid:
            oid_map[sid] = oid

    for sid in need_mint:
        info = new_companies[sid]
        domain = (info.get('domain') or '').lower().strip() or None
        ein = info.get('ein') or None
        new_oid = str(uuid.uuid4())

        if DRY_RUN:
            oid_map[sid] = new_oid
            minted += 1
            continue

        try:
            # Step A: Insert into outreach.outreach (operational spine)
            cur.execute("""
                INSERT INTO outreach.outreach (outreach_id, sovereign_id, domain, ein)
                VALUES (%s::uuid, %s::uuid, %s, %s)
                ON CONFLICT DO NOTHING
            """, (new_oid, sid, domain, ein))

            if cur.rowcount == 0:
                # Domain might already exist
                if domain:
                    cur.execute("""
                        SELECT outreach_id::text FROM outreach.outreach
                        WHERE LOWER(domain) = %s
                    """, (domain,))
                    existing = cur.fetchone()
                    if existing:
                        new_oid = existing[0]
                    else:
                        mint_errors += 1
                        continue
                else:
                    mint_errors += 1
                    continue

            # Step B: Write outreach_id back to CL (WRITE-ONCE)
            cur.execute("""
                UPDATE cl.company_identity
                SET outreach_id = %s::uuid
                WHERE company_unique_id = %s::uuid AND outreach_id IS NULL
            """, (new_oid, sid))

            if cur.rowcount == 1:
                oid_map[sid] = new_oid
                minted += 1
            else:
                # CL already claimed — fetch what it has
                cur.execute("""
                    SELECT outreach_id::text FROM cl.company_identity
                    WHERE company_unique_id = %s::uuid
                """, (sid,))
                cl_oid = cur.fetchone()
                if cl_oid and cl_oid[0]:
                    oid_map[sid] = cl_oid[0]
                    minted += 1
                else:
                    mint_errors += 1

            if minted % 50 == 0:
                conn.commit()

        except Exception as e:
            print(f"    ERROR minting {sid}: {e}")
            conn.rollback()
            mint_errors += 1

    if not DRY_RUN:
        conn.commit()

    print(f"  Minted: {minted:,}")
    print(f"  Errors: {mint_errors:,}")
    print(f"  Total mapped: {len(oid_map):,}")

    # ==============================================================
    # STEP 3: Create company_target records for NEW companies
    # ==============================================================
    print(f"\n{'=' * 60}")
    print("STEP 3: Create company_target records for NEW companies")
    print(f"{'=' * 60}")

    mapped_oids = list(oid_map.values())
    if mapped_oids:
        cur.execute("""
            SELECT outreach_id::text FROM outreach.company_target
            WHERE outreach_id = ANY(%s::uuid[])
        """, (mapped_oids,))
        existing_ct = {r[0] for r in cur.fetchall()}
    else:
        existing_ct = set()

    ct_created = 0
    ct_skipped = 0
    for sid, oid in oid_map.items():
        if oid in existing_ct:
            ct_skipped += 1
            continue

        info = new_companies.get(sid, {})
        contacts = info.get('contacts', [])

        # Best email pattern from contacts (highest confidence)
        pattern = ''
        best_conf = 0
        for c in contacts:
            try:
                conf = int(clean(c.get('Confidence score')) or 0)
            except ValueError:
                conf = 0
            p = clean(c.get('Pattern'))
            if p and conf > best_conf:
                pattern = p
                best_conf = conf

        # Firmographics from first contact
        industry = clean(contacts[0].get('Industry')) if contacts else ''
        headcount = parse_headcount(clean(contacts[0].get('Headcount'))) if contacts else None

        city = info.get('city', '')
        state = info.get('state', '')
        zip_code = info.get('zip', '')

        if DRY_RUN:
            ct_created += 1
            continue

        try:
            cur.execute("""
                INSERT INTO outreach.company_target (
                    outreach_id, company_unique_id, source,
                    city, state, postal_code,
                    email_method, industry, employees
                ) VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                oid, sid, 'hunter_28461_100mi',
                city or None, state or None, zip_code or None,
                pattern or None, industry or None, headcount,
            ))
            if cur.rowcount > 0:
                ct_created += 1
        except Exception as e:
            print(f"    ERROR creating CT for {sid}: {e}")
            conn.rollback()

    if not DRY_RUN:
        conn.commit()
    print(f"  Created: {ct_created:,}")
    print(f"  Skipped (already exist): {ct_skipped:,}")

    # ==============================================================
    # STEP 4: Ensure company_slots exist (CEO/CFO/HR)
    # ==============================================================
    print(f"\n{'=' * 60}")
    print("STEP 4: Create company_slots (CEO/CFO/HR)")
    print(f"{'=' * 60}")

    # Build full outreach_id -> sovereign_id map
    all_oids = {}
    for sid, oid in oid_map.items():
        all_oids[oid] = sid
    for oid, contacts in existing_gap.items():
        sid = clean(contacts[0].get('sovereign_id'))
        all_oids[oid] = sid

    # Fetch existing slots
    oid_list = list(all_oids.keys())
    existing_slots = {}
    if oid_list:
        cur.execute("""
            SELECT outreach_id::text, slot_type, slot_id::text, is_filled, person_unique_id
            FROM people.company_slot
            WHERE outreach_id = ANY(%s::uuid[])
        """, (oid_list,))
        for r in cur.fetchall():
            existing_slots.setdefault(r[0], {})[r[1]] = {
                'slot_id': r[2], 'is_filled': r[3], 'person_id': r[4],
            }

    slots_created = 0
    for oid, sid in all_oids.items():
        company_slots = existing_slots.get(oid, {})
        for slot_type in ['CEO', 'CFO', 'HR']:
            if slot_type in company_slots:
                continue
            if DRY_RUN:
                slots_created += 1
                new_slot_id = str(uuid.uuid4())
                existing_slots.setdefault(oid, {})[slot_type] = {
                    'slot_id': new_slot_id, 'is_filled': False, 'person_id': None,
                }
                continue
            try:
                new_slot_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO people.company_slot (
                        slot_id, outreach_id, company_unique_id, slot_type
                    ) VALUES (%s::uuid, %s::uuid, %s, %s)
                """, (new_slot_id, oid, sid, slot_type))
                if cur.rowcount > 0:
                    slots_created += 1
                    # Track for slot filling later
                    existing_slots.setdefault(oid, {})[slot_type] = {
                        'slot_id': new_slot_id, 'is_filled': False, 'person_id': None,
                    }
            except Exception as e:
                print(f"    ERROR creating slot {slot_type} for {oid}: {e}")
                conn.rollback()

    if not DRY_RUN:
        conn.commit()
    print(f"  Slots created: {slots_created:,}")

    # ==============================================================
    # STEP 5: Fill slots + create people_master records
    # ==============================================================
    print(f"\n{'=' * 60}")
    print("STEP 5: Fill slots + create people_master records")
    print(f"{'=' * 60}")

    seq = next_barton_seq(cur)
    print(f"  Starting Barton ID sequence: {seq}")

    slots_filled = 0
    people_created = 0
    skipped_no_slot_type = 0
    skipped_already_filled = 0
    skipped_no_slot_record = 0
    pattern_updates = 0

    def process_company(oid, sid, contacts):
        nonlocal seq, slots_filled, people_created
        nonlocal skipped_no_slot_type, skipped_already_filled, skipped_no_slot_record
        nonlocal pattern_updates

        company_slot_data = existing_slots.get(oid, {})

        # Group contacts by slot type, keep best (highest confidence) per slot
        best_per_slot = {}
        for c in contacts:
            dept = clean(c.get('Department'))
            title = clean(c.get('Job title'))
            slot = get_slot_type(dept, title)
            if not slot:
                skipped_no_slot_type += 1
                continue

            try:
                conf = int(clean(c.get('Confidence score')) or 0)
            except ValueError:
                conf = 0

            if slot not in best_per_slot or conf > best_per_slot[slot][1]:
                best_per_slot[slot] = (c, conf)

        for slot_type, (contact, conf) in best_per_slot.items():
            slot_info = company_slot_data.get(slot_type)
            if not slot_info:
                skipped_no_slot_record += 1
                continue
            if slot_info.get('is_filled'):
                skipped_already_filled += 1
                continue

            slot_id = slot_info['slot_id']
            email = clean(contact.get('Email address')).lower()
            first_name = clean(contact.get('First name'))
            last_name = clean(contact.get('Last name'))
            full_name = f"{first_name} {last_name}".strip()
            title = clean(contact.get('Job title'))
            dept = clean(contact.get('Department'))
            linkedin = clean(contact.get('LinkedIn URL'))
            phone = clean(contact.get('Phone number'))

            bid = barton_id(seq)

            if DRY_RUN:
                seq += 1
                slots_filled += 1
                people_created += 1
                continue

            try:
                # Create people_master record (full_name is a generated column)
                cur.execute("""
                    INSERT INTO people.people_master (
                        unique_id, company_unique_id, company_slot_unique_id,
                        first_name, last_name, title, department,
                        email, linkedin_url, source_system
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    bid, sid, slot_id,
                    first_name or 'Unknown', last_name or 'Unknown',
                    title or None, dept or None,
                    email or None, linkedin or None, 'hunter_28461_100mi',
                ))

                if cur.rowcount > 0:
                    people_created += 1

                    # Fill the slot (confidence_score is numeric(3,2), normalize 0-100 to 0.00-1.00)
                    conf_normalized = round(conf / 100.0, 2) if conf else None
                    cur.execute("""
                        UPDATE people.company_slot
                        SET is_filled = TRUE,
                            person_unique_id = %s,
                            filled_at = NOW(),
                            confidence_score = %s,
                            source_system = %s,
                            slot_phone = %s,
                            slot_phone_source = CASE WHEN %s IS NOT NULL THEN 'hunter' ELSE NULL END,
                            slot_phone_updated_at = CASE WHEN %s IS NOT NULL THEN NOW() ELSE NULL END,
                            updated_at = NOW()
                        WHERE slot_id = %s::uuid AND is_filled = FALSE
                    """, (
                        bid, conf_normalized, 'hunter_28461_100mi',
                        phone or None, phone or None, phone or None, slot_id,
                    ))

                    if cur.rowcount > 0:
                        slots_filled += 1

                    seq += 1

            except Exception as e:
                print(f"    ERROR filling {slot_type} for {oid}: {e}")
                conn.rollback()

    # Process NEW companies
    for sid, info in new_companies.items():
        oid = oid_map.get(sid)
        if not oid:
            continue
        process_company(oid, sid, info['contacts'])

    # Process EXISTING_GAP companies
    for oid, contacts in existing_gap.items():
        sid = clean(contacts[0].get('sovereign_id'))
        process_company(oid, sid, contacts)

    if not DRY_RUN:
        conn.commit()

    print(f"  People created:          {people_created:,}")
    print(f"  Slots filled:            {slots_filled:,}")
    print(f"  Skipped (no slot type):  {skipped_no_slot_type:,}")
    print(f"  Skipped (already filled):{skipped_already_filled:,}")
    print(f"  Skipped (no slot record):{skipped_no_slot_record:,}")

    # ==============================================================
    # STEP 6: Update email_method on company_target where missing
    # ==============================================================
    print(f"\n{'=' * 60}")
    print("STEP 6: Update email_method where missing")
    print(f"{'=' * 60}")

    # For EXISTING_GAP companies without email pattern
    pattern_updates = 0
    for oid, contacts in existing_gap.items():
        has_pattern = clean(contacts[0].get('has_email_pattern'))
        if has_pattern == 'YES':
            continue

        # Find best pattern from contacts
        best_p = ''
        best_c = 0
        for c in contacts:
            p = clean(c.get('Pattern'))
            try:
                conf = int(clean(c.get('Confidence score')) or 0)
            except ValueError:
                conf = 0
            if p and conf > best_c:
                best_p = p
                best_c = conf

        if not best_p:
            continue

        if DRY_RUN:
            pattern_updates += 1
            continue

        try:
            cur.execute("""
                UPDATE outreach.company_target
                SET email_method = %s, updated_at = NOW()
                WHERE outreach_id = %s::uuid AND (email_method IS NULL OR email_method = '')
            """, (best_p, oid))
            if cur.rowcount > 0:
                pattern_updates += 1
        except Exception as e:
            print(f"    ERROR updating pattern for {oid}: {e}")
            conn.rollback()

    if not DRY_RUN:
        conn.commit()
    print(f"  Patterns updated: {pattern_updates:,}")

    # ── SUMMARY ──
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Hunter contacts loaded:     {loaded:,}")
    print(f"  Outreach IDs minted:        {minted:,}")
    print(f"  Company targets created:    {ct_created:,}")
    print(f"  Company slots created:      {slots_created:,}")
    print(f"  People records created:     {people_created:,}")
    print(f"  Slots filled:               {slots_filled:,}")
    print(f"  Email patterns updated:     {pattern_updates:,}")
    print(f"{'=' * 60}")
    print(f"Completed: {datetime.now().isoformat()}")

    conn.close()


if __name__ == '__main__':
    main()
