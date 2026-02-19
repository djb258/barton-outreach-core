#!/usr/bin/env python3
"""
Onboard the remaining 7,129 CL companies without outreach_ids.

Handles:
  - Junk domain filtering (72 domains appearing 5+ times = Clay noise)
  - Spine overlap linking (298 domains already in outreach.outreach)
  - Dedup (keep 1 per domain for 2-4 copy duplicates)
  - Clean onboarding for 5,586 unique companies

Pipeline per company:
  1. Mint outreach_id -> outreach.outreach
  2. Write outreach_id -> cl.company_identity (WRITE-ONCE)
  3. Create outreach.company_target record
  4. Create CEO/CFO/HR slots in people.company_slot
  5. DOL bridge by name match where possible

Usage:
    doppler run -- python scripts/onboard_remaining_7129.py --dry-run
    doppler run -- python scripts/onboard_remaining_7129.py
"""
import os
import sys
import io
import re
import uuid
import argparse
from datetime import datetime, timezone
from collections import Counter, defaultdict

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import psycopg2

JUNK_THRESHOLD = 5  # domains appearing this many times = junk


def get_conn():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        dbname=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require',
    )


def norm_name(name):
    """Normalize company name for DOL matching."""
    n = (name or '').upper().strip()
    n = re.sub(
        r'\s*,?\s*(LLC|INC|INCORPORATED|CORP|CORPORATION|COMPANY|CO|LTD|LIMITED|'
        r'LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|'
        r'INTERNATIONAL|\.)+\s*$', '', n, flags=re.IGNORECASE
    )
    n = re.sub(r'[^A-Z0-9 ]', '', n)
    return n.strip()


def main():
    parser = argparse.ArgumentParser(description='Onboard remaining 7,129 CL companies')
    parser.add_argument('--dry-run', action='store_true', help='Preview without DB writes')
    args = parser.parse_args()

    print("=" * 60)
    print("Onboard Remaining CL Companies (dedup-safe)")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)

    conn = get_conn()
    cur = conn.cursor()

    # ── STEP 1: Load all 7,129 ──────────────────────────────
    print(f"\n{'=' * 60}")
    print("STEP 1: Load + classify")
    print(f"{'=' * 60}")

    cur.execute("""
        SELECT company_unique_id::text, company_name, company_domain,
               source_system, state_code
        FROM cl.company_identity
        WHERE outreach_id IS NULL
        ORDER BY company_name
    """)
    all_rows = cur.fetchall()
    print(f"  Total without outreach_id: {len(all_rows):,}")

    # Count domains
    domain_counts = Counter()
    for _, _, dom, _, _ in all_rows:
        d = (dom or '').lower().strip()
        if d:
            domain_counts[d] += 1

    # Identify junk domains (5+ copies)
    junk_domains = {d for d, c in domain_counts.items() if c >= JUNK_THRESHOLD}
    print(f"  Junk domains (>={JUNK_THRESHOLD} copies): {len(junk_domains)} -> {sum(domain_counts[d] for d in junk_domains):,} rows")

    # Load spine domain map for overlap detection
    cur.execute("""
        SELECT LOWER(domain), outreach_id::text
        FROM outreach.outreach
        WHERE domain IS NOT NULL AND domain != ''
    """)
    spine_domain_map = {}
    for d, oid in cur.fetchall():
        spine_domain_map[d.lower().strip()] = oid

    # Classify each row
    to_skip_junk = []
    to_link = []       # (cuid, name, domain, existing_outreach_id)
    to_onboard = []    # (cuid, name, domain, source, state)
    seen_domains = set()
    to_skip_dup = []

    for cuid, name, dom, source, state in all_rows:
        d = (dom or '').lower().strip()

        # Junk domain?
        if d and d in junk_domains:
            to_skip_junk.append((cuid, name, d))
            continue

        # Already in spine?
        if d and d in spine_domain_map:
            to_link.append((cuid, name, d, spine_domain_map[d]))
            continue

        # Dedup within this batch
        if d and d in seen_domains:
            to_skip_dup.append((cuid, name, d))
            continue

        if d:
            seen_domains.add(d)

        to_onboard.append({
            'cuid': cuid, 'name': name, 'domain': d or None,
            'source': source, 'state': state,
        })

    print(f"  Junk skip:     {len(to_skip_junk):,}")
    print(f"  Spine link:    {len(to_link):,}")
    print(f"  Dedup skip:    {len(to_skip_dup):,}")
    print(f"  To onboard:    {len(to_onboard):,}")

    # ── STEP 2: Link spine overlaps ─────────────────────────
    print(f"\n{'=' * 60}")
    print("STEP 2: Link spine overlaps to existing outreach_ids")
    print(f"{'=' * 60}")

    linked = 0
    for cuid, name, dom, existing_oid in to_link:
        if args.dry_run:
            linked += 1
            continue
        try:
            cur.execute("""
                UPDATE cl.company_identity
                SET outreach_id = %s::uuid
                WHERE company_unique_id = %s::uuid AND outreach_id IS NULL
            """, (existing_oid, cuid))
            if cur.rowcount == 1:
                linked += 1
            if linked % 100 == 0:
                conn.commit()
        except Exception as e:
            print(f"    ERROR linking {cuid}: {e}")
            conn.rollback()

    if not args.dry_run:
        conn.commit()
    print(f"  Linked: {linked:,}")

    # ── STEP 3: Mint outreach_ids ───────────────────────────
    print(f"\n{'=' * 60}")
    print("STEP 3: Mint outreach_ids")
    print(f"{'=' * 60}")

    minted = 0
    errors = 0

    for co in to_onboard:
        domain_clean = co['domain']
        new_oid = str(uuid.uuid4())

        if args.dry_run:
            co['outreach_id'] = new_oid
            minted += 1
            continue

        try:
            cur.execute("""
                INSERT INTO outreach.outreach (outreach_id, sovereign_id, domain)
                VALUES (%s::uuid, %s::uuid, %s)
                ON CONFLICT DO NOTHING
            """, (new_oid, co['cuid'], domain_clean))

            if cur.rowcount == 0:
                if domain_clean:
                    cur.execute("""
                        SELECT outreach_id::text FROM outreach.outreach
                        WHERE LOWER(domain) = %s
                    """, (domain_clean,))
                    existing = cur.fetchone()
                    if existing:
                        new_oid = existing[0]
                    else:
                        errors += 1
                        co['outreach_id'] = None
                        continue
                else:
                    errors += 1
                    co['outreach_id'] = None
                    continue

            cur.execute("""
                UPDATE cl.company_identity
                SET outreach_id = %s::uuid
                WHERE company_unique_id = %s::uuid AND outreach_id IS NULL
            """, (new_oid, co['cuid']))

            if cur.rowcount == 1:
                co['outreach_id'] = new_oid
                minted += 1
            else:
                cur.execute("""
                    SELECT outreach_id::text FROM cl.company_identity
                    WHERE company_unique_id = %s::uuid
                """, (co['cuid'],))
                cl_oid = cur.fetchone()
                if cl_oid and cl_oid[0]:
                    co['outreach_id'] = cl_oid[0]
                    minted += 1
                else:
                    errors += 1
                    co['outreach_id'] = None

            if minted % 500 == 0:
                conn.commit()
                print(f"    ... minted {minted:,}")

        except Exception as e:
            print(f"    ERROR minting {co['cuid']}: {e}")
            conn.rollback()
            errors += 1
            co['outreach_id'] = None

    if not args.dry_run:
        conn.commit()

    print(f"  Minted: {minted:,}")
    print(f"  Errors: {errors:,}")

    # ── STEP 4: Create company_target records ───────────────
    print(f"\n{'=' * 60}")
    print("STEP 4: Create company_target records")
    print(f"{'=' * 60}")

    cur_check = conn.cursor()
    oid_list = [co['outreach_id'] for co in to_onboard if co.get('outreach_id')]
    existing_ct = set()
    if oid_list:
        for i in range(0, len(oid_list), 5000):
            chunk = oid_list[i:i+5000]
            cur_check.execute("""
                SELECT outreach_id::text FROM outreach.company_target
                WHERE outreach_id = ANY(%s::uuid[])
            """, (chunk,))
            existing_ct.update(r[0] for r in cur_check.fetchall())

    print(f"  Already in CT: {len(existing_ct):,}")

    created_ct = 0
    for co in to_onboard:
        oid = co.get('outreach_id')
        if not oid or oid in existing_ct:
            continue

        state = co.get('state') or None
        # Validate state is 2-letter code
        if state and (len(state.strip()) != 2 or not state.strip().isalpha()):
            state = None

        if args.dry_run:
            created_ct += 1
            continue

        try:
            cur.execute("""
                INSERT INTO outreach.company_target (
                    outreach_id, company_unique_id, source, state
                ) VALUES (%s::uuid, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (oid, co['cuid'], 'cl_backfill_2026', state))
            if cur.rowcount > 0:
                created_ct += 1
        except Exception as e:
            print(f"    ERROR CT for {co['cuid']}: {e}")
            conn.rollback()

        if created_ct % 500 == 0 and created_ct > 0:
            conn.commit()
            print(f"    ... created {created_ct:,}")

    if not args.dry_run:
        conn.commit()
    print(f"  CT created: {created_ct:,}")

    # ── STEP 5: Create slots ────────────────────────────────
    print(f"\n{'=' * 60}")
    print("STEP 5: Create company_slots (CEO/CFO/HR)")
    print(f"{'=' * 60}")

    oid_list2 = [co['outreach_id'] for co in to_onboard if co.get('outreach_id')]
    existing_slots = set()
    if oid_list2:
        for i in range(0, len(oid_list2), 5000):
            chunk = oid_list2[i:i+5000]
            cur_check.execute("""
                SELECT outreach_id::text, slot_type
                FROM people.company_slot
                WHERE outreach_id = ANY(%s::uuid[])
            """, (chunk,))
            existing_slots.update((r[0], r[1]) for r in cur_check.fetchall())

    created_slots = 0
    for co in to_onboard:
        oid = co.get('outreach_id')
        if not oid:
            continue
        for slot_type in ['CEO', 'CFO', 'HR']:
            if (oid, slot_type) in existing_slots:
                continue
            if args.dry_run:
                created_slots += 1
                continue
            try:
                new_slot_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO people.company_slot (
                        slot_id, outreach_id, company_unique_id, slot_type
                    ) VALUES (%s::uuid, %s::uuid, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (new_slot_id, oid, co['cuid'], slot_type))
                if cur.rowcount > 0:
                    created_slots += 1
            except Exception as e:
                print(f"    ERROR slot {slot_type} for {oid}: {e}")
                conn.rollback()

        if created_slots % 600 == 0 and created_slots > 0 and not args.dry_run:
            conn.commit()
            print(f"    ... created {created_slots:,}")

    if not args.dry_run:
        conn.commit()
    print(f"  Slots created: {created_slots:,}")

    # ── STEP 6: DOL bridge by name match ────────────────────
    print(f"\n{'=' * 60}")
    print("STEP 6: DOL bridge by name match")
    print(f"{'=' * 60}")

    # Build DOL lookup from all filings
    cur.execute("""
        WITH filings AS (
            SELECT UPPER(TRIM(sponsor_dfe_name)) AS name_upper,
                   sponsor_dfe_ein AS ein,
                   spons_dfe_mail_us_city AS city,
                   spons_dfe_mail_us_state AS state,
                   LEFT(TRIM(spons_dfe_mail_us_zip), 5) AS zip,
                   form_plan_year_begin_date::date AS plan_begin,
                   type_pension_bnft_code, type_welfare_bnft_code,
                   funding_insurance_ind, funding_trust_ind
            FROM dol.form_5500
            WHERE sponsor_dfe_name IS NOT NULL

            UNION ALL

            SELECT UPPER(TRIM(sf_sponsor_name)),
                   sf_spons_ein,
                   sf_spons_us_city, sf_spons_us_state,
                   LEFT(TRIM(sf_spons_us_zip), 5),
                   sf_plan_year_begin_date::date,
                   sf_type_pension_bnft_code, sf_type_welfare_bnft_code,
                   NULL, NULL
            FROM dol.form_5500_sf
            WHERE sf_sponsor_name IS NOT NULL
        )
        SELECT DISTINCT ON (name_upper)
            name_upper, ein, city, state, zip, plan_begin,
            type_pension_bnft_code, type_welfare_bnft_code,
            funding_insurance_ind, funding_trust_ind
        FROM filings
        ORDER BY name_upper, plan_begin DESC NULLS LAST
    """)
    dol_lookup = {}
    dol_norm_lookup = {}
    for row in cur.fetchall():
        (name_upper, ein, city, state, zip_code, plan_begin,
         pension, welfare, ins_ind, trust_ind) = row
        if not name_upper:
            continue

        has_pension = bool(pension and pension.strip())
        has_welfare = bool(welfare and welfare.strip())
        if has_pension and not has_welfare:
            funding = 'pension_only'
        elif trust_ind and trust_ind.strip() == '1':
            funding = 'self_funded'
        elif ins_ind and ins_ind.strip() == '1':
            funding = 'fully_insured'
        else:
            funding = 'unknown'

        renewal_month = plan_begin.month if plan_begin else None
        outreach_start = ((renewal_month - 6) % 12) + 1 if renewal_month else None

        data = {
            'ein': (ein or '').replace('-', '').strip(),
            'city': (city or '').strip(),
            'state': (state or '').strip(),
            'zip': (zip_code or '').strip(),
            'filing_present': True,
            'funding_type': funding,
            'renewal_month': renewal_month,
            'outreach_start_month': outreach_start,
        }
        dol_lookup[name_upper] = data
        nn = norm_name(name_upper)
        if nn and nn not in dol_norm_lookup:
            dol_norm_lookup[nn] = data

    print(f"  DOL lookup: {len(dol_lookup):,} exact, {len(dol_norm_lookup):,} normalized")

    # Check existing DOL records
    existing_dol = set()
    if oid_list2:
        for i in range(0, len(oid_list2), 5000):
            chunk = oid_list2[i:i+5000]
            cur_check.execute("""
                SELECT outreach_id::text FROM outreach.dol
                WHERE outreach_id = ANY(%s::uuid[])
            """, (chunk,))
            existing_dol.update(r[0] for r in cur_check.fetchall())

    created_dol = 0
    dol_with_zip = 0

    for co in to_onboard:
        oid = co.get('outreach_id')
        if not oid or oid in existing_dol:
            continue

        name_upper = (co['name'] or '').upper().strip()
        dol = dol_lookup.get(name_upper) or dol_norm_lookup.get(norm_name(co['name']))
        if not dol:
            continue

        # Also backfill CT postal_code if we got one from DOL
        if dol['zip'] and len(dol['zip']) == 5:
            dol_with_zip += 1
            if not args.dry_run:
                try:
                    cur.execute("""
                        UPDATE outreach.company_target
                        SET postal_code = %s, city = COALESCE(city, %s),
                            state = COALESCE(state, %s),
                            postal_code_source = 'dol_filing',
                            postal_code_updated_at = NOW()
                        WHERE outreach_id = %s::uuid
                          AND (postal_code IS NULL OR postal_code = '')
                    """, (dol['zip'], dol['city'], dol['state'], oid))
                except Exception:
                    conn.rollback()

        dol_id = str(uuid.uuid4())
        if args.dry_run:
            created_dol += 1
            continue

        try:
            cur.execute("""
                INSERT INTO outreach.dol
                    (dol_id, outreach_id, ein, filing_present, funding_type,
                     renewal_month, outreach_start_month, created_at, updated_at)
                SELECT %s::uuid, %s::uuid, %s, %s, %s, %s, %s, NOW(), NOW()
                WHERE NOT EXISTS (
                    SELECT 1 FROM outreach.dol WHERE outreach_id = %s::uuid
                )
            """, (dol_id, oid, dol['ein'], dol['filing_present'], dol['funding_type'],
                  dol['renewal_month'], dol['outreach_start_month'], oid))
            if cur.rowcount > 0:
                created_dol += 1
        except Exception as e:
            print(f"    ERROR DOL for {oid}: {e}")
            conn.rollback()

        if created_dol % 500 == 0 and created_dol > 0:
            conn.commit()
            print(f"    ... created {created_dol:,}")

    if not args.dry_run:
        conn.commit()

    print(f"  DOL records created: {created_dol:,}")
    print(f"  CT postal_codes backfilled: {dol_with_zip:,}")

    # ── SUMMARY ─────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Junk skipped:          {len(to_skip_junk):,}")
    print(f"  Dedup skipped:         {len(to_skip_dup):,}")
    print(f"  Linked to existing:    {linked:,}")
    print(f"  Outreach IDs minted:   {minted:,}")
    print(f"  CT records created:    {created_ct:,}")
    print(f"  Slots created:         {created_slots:,}")
    print(f"  DOL records created:   {created_dol:,}")
    print(f"  DOL ZIPs backfilled:   {dol_with_zip:,}")

    if not args.dry_run:
        # Verify
        cur.execute('SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NULL')
        remaining = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM outreach.outreach')
        spine = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM outreach.company_target')
        ct = cur.fetchone()[0]
        print(f"\n  DB verification:")
        print(f"    CL still no outreach_id: {remaining:,}")
        print(f"    Spine total:             {spine:,}")
        print(f"    CT total:                {ct:,}")

    conn.close()


if __name__ == '__main__':
    main()
