#!/usr/bin/env python3
"""
Onboard 1,076 NC HUNTER_DOL_SS003 companies to the outreach spine.

These companies came FROM DOL enrichment — they should match DOL filings
by name and already have EINs. Address data comes from DOL filings.

Pipeline:
  STEP 1: Query CL, filter non-commercial, match DOL filings for addresses
  STEP 2: Mint outreach_ids (outreach.outreach -> CL write-back)
  STEP 3: Create company_target records (with DOL address)
  STEP 4: Create company_slots (CEO/CFO/HR)
  STEP 5: Create outreach.dol records (EIN, funding, renewal, carrier)

Usage:
    doppler run -- python scripts/onboard_nc_hunter_dol.py --dry-run
    doppler run -- python scripts/onboard_nc_hunter_dol.py
    doppler run -- python scripts/onboard_nc_hunter_dol.py --step 2  # individual step
"""
import os
import sys
import io
import re
import uuid
import argparse
from datetime import datetime, timezone
from collections import defaultdict

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import psycopg2

# ── Commercial eligibility filter ────────────────────────────
# These keywords in company_name indicate non-commercial entities
# that were excluded in the Jan 2026 commercial eligibility cleanup.
EXCLUDE_KEYWORDS = [
    'HOSPITAL', 'MEDICAL CENTER', 'HEALTH SYSTEM', 'HEALTH CARE',
    'HEALTHCARE', 'CLINIC', 'NURSING', 'REHABILITATION',
    'CHURCH', 'MINISTRY', 'MINISTRIES', 'BAPTIST', 'METHODIST',
    'PRESBYTERIAN', 'LUTHERAN', 'EPISCOPAL', 'CATHOLIC',
    'SYNAGOGUE', 'MOSQUE', 'TEMPLE', 'CONGREGATION',
    'SCHOOL DISTRICT', 'BOARD OF EDUCATION', 'UNIVERSITY',
    'COLLEGE', 'ACADEMY',
    'COUNTY OF', 'CITY OF', 'TOWN OF', 'VILLAGE OF',
    'STATE OF', 'DEPARTMENT OF', 'MUNICIPALITY',
    'FIRE DEPARTMENT', 'POLICE DEPARTMENT', 'SHERIFF',
    'HOUSING AUTHORITY', 'WATER AUTHORITY', 'TRANSIT AUTHORITY',
]


def get_conn():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        dbname=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require',
    )


def is_non_commercial(name):
    """Check if company name matches non-commercial keywords."""
    upper = (name or '').upper()
    return any(kw in upper for kw in EXCLUDE_KEYWORDS)


def norm_name(name):
    """Normalize company name for matching: strip suffixes, uppercase, alphanum only."""
    n = (name or '').upper().strip()
    # Strip common suffixes
    n = re.sub(
        r'\s*,?\s*(LLC|INC|INCORPORATED|CORP|CORPORATION|COMPANY|CO|LTD|LIMITED|'
        r'LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|'
        r'INTERNATIONAL|\.)+\s*$', '', n, flags=re.IGNORECASE
    )
    # Keep only alphanumeric + spaces
    n = re.sub(r'[^A-Z0-9 ]', '', n)
    return n.strip()


# ══════════════════════════════════════════════════════════════
# STEP 1: Load CL companies + match DOL filings
# ══════════════════════════════════════════════════════════════

def step1_load_and_match(conn, dry_run=False):
    """
    Load NC HUNTER_DOL_SS003 companies from CL, filter non-commercial,
    match to DOL filings for address/EIN data.
    """
    print(f"\n{'=' * 60}")
    print("STEP 1: Load CL companies + match DOL filings")
    print(f"{'=' * 60}")

    cur = conn.cursor()

    # Get all NC HUNTER_DOL_SS003 companies without outreach_id
    cur.execute("""
        SELECT company_unique_id::text, company_name, company_domain
        FROM cl.company_identity
        WHERE source_system = 'HUNTER_DOL_SS003'
          AND state_code = 'NC'
          AND outreach_id IS NULL
        ORDER BY company_name
    """)
    all_companies = cur.fetchall()
    print(f"  Total NC HUNTER_DOL_SS003 without outreach_id: {len(all_companies):,}")

    # Filter non-commercial
    excluded = []
    eligible = []
    for cuid, name, domain in all_companies:
        if is_non_commercial(name):
            excluded.append((cuid, name, domain))
        else:
            eligible.append((cuid, name, domain))

    print(f"  Non-commercial filtered out: {len(excluded):,}")
    if excluded:
        by_keyword = defaultdict(list)
        for _, name, _ in excluded:
            upper = (name or '').upper()
            for kw in EXCLUDE_KEYWORDS:
                if kw in upper:
                    by_keyword[kw].append(name)
                    break
        for kw in sorted(by_keyword, key=lambda k: -len(by_keyword[k])):
            print(f"    {kw}: {len(by_keyword[kw])}")

    print(f"  Eligible for onboarding: {len(eligible):,}")

    # Build DOL filing lookup: normalized_name -> best filing data
    # Use form_5500 + form_5500_sf for NC filings
    print(f"\n  Loading NC DOL filings for address matching...")
    cur.execute("""
        WITH filings AS (
            SELECT
                sponsor_dfe_name AS sponsor_name,
                sponsor_dfe_ein AS ein,
                spons_dfe_mail_us_city AS city,
                spons_dfe_mail_us_state AS state,
                LEFT(TRIM(spons_dfe_mail_us_zip), 5) AS zip,
                form_plan_year_begin_date::date AS plan_begin,
                'form_5500' AS filing_source,
                type_pension_bnft_code,
                type_welfare_bnft_code,
                funding_insurance_ind,
                funding_trust_ind
            FROM dol.form_5500
            WHERE UPPER(TRIM(spons_dfe_mail_us_state)) = 'NC'

            UNION ALL

            SELECT
                sf_sponsor_name AS sponsor_name,
                sf_spons_ein AS ein,
                sf_spons_us_city AS city,
                sf_spons_us_state AS state,
                LEFT(TRIM(sf_spons_us_zip), 5) AS zip,
                sf_plan_year_begin_date::date AS plan_begin,
                'form_5500_sf' AS filing_source,
                sf_type_pension_bnft_code,
                sf_type_welfare_bnft_code,
                NULL AS funding_insurance_ind,
                NULL AS funding_trust_ind
            FROM dol.form_5500_sf
            WHERE UPPER(TRIM(sf_spons_us_state)) = 'NC'
        )
        SELECT sponsor_name, ein, city, state, zip, plan_begin,
               filing_source, type_pension_bnft_code, type_welfare_bnft_code,
               funding_insurance_ind, funding_trust_ind
        FROM filings
        WHERE sponsor_name IS NOT NULL
        ORDER BY plan_begin DESC NULLS LAST
    """)
    filings = cur.fetchall()
    print(f"  NC DOL filings loaded: {len(filings):,}")

    # Build lookup: norm_name -> best filing (most recent plan_begin)
    dol_lookup = {}  # norm_name -> filing dict
    for row in filings:
        (sname, ein, city, state, zip_code, plan_begin,
         fsource, pension_code, welfare_code, ins_ind, trust_ind) = row
        nname = norm_name(sname)
        if not nname:
            continue
        if nname not in dol_lookup:  # first = most recent (ORDER BY DESC)
            # Derive funding type
            has_pension = bool(pension_code and pension_code.strip())
            has_welfare = bool(welfare_code and welfare_code.strip())
            if has_pension and not has_welfare:
                funding_type = 'pension_only'
            elif trust_ind and trust_ind.strip() == '1':
                funding_type = 'self_funded'
            elif ins_ind and ins_ind.strip() == '1':
                funding_type = 'fully_insured'
            else:
                funding_type = 'unknown'

            # Derive renewal month
            renewal_month = None
            outreach_start_month = None
            if plan_begin:
                renewal_month = plan_begin.month
                outreach_start_month = ((renewal_month - 6) % 12) + 1  # 5 months before

            dol_lookup[nname] = {
                'sponsor_name': sname,
                'ein': (ein or '').replace('-', '').strip(),
                'city': (city or '').strip(),
                'state': (state or '').strip(),
                'zip': (zip_code or '').strip(),
                'filing_present': True,
                'funding_type': funding_type,
                'renewal_month': renewal_month,
                'outreach_start_month': outreach_start_month,
            }

    print(f"  Unique DOL names (normalized): {len(dol_lookup):,}")

    # Load carrier data from schedule_a (by EIN)
    # Get all EINs from matches first
    ein_set = set()
    for data in dol_lookup.values():
        if data['ein']:
            ein_set.add(data['ein'])

    carrier_map = {}  # ein -> carrier name
    if ein_set:
        ein_list = list(ein_set)
        for i in range(0, len(ein_list), 5000):
            chunk = ein_list[i:i+5000]
            # Carrier from schedule_a (by sponsor EIN -> ins_carrier_name)
            cur.execute("""
                SELECT DISTINCT ON (sch_a_ein)
                    sch_a_ein, ins_carrier_name
                FROM dol.schedule_a
                WHERE sch_a_ein = ANY(%s)
                  AND ins_carrier_name IS NOT NULL
                  AND UPPER(ins_carrier_name) NOT LIKE '%%TRUST%%'
                ORDER BY sch_a_ein, ack_id DESC
            """, (chunk,))
            for sein, cname in cur.fetchall():
                carrier_map[sein] = cname

    print(f"  Carriers found: {len(carrier_map):,}")

    # Match eligible companies to DOL filings
    matched = []    # (cuid, name, domain, dol_data)
    unmatched = []  # (cuid, name, domain)

    for cuid, name, domain in eligible:
        nname = norm_name(name)
        dol_data = dol_lookup.get(nname)
        if dol_data:
            # Add carrier from schedule_a
            ein = dol_data['ein']
            dol_data = dict(dol_data)  # copy
            dol_data['carrier'] = carrier_map.get(ein)
            dol_data['broker'] = None
            matched.append((cuid, name, domain, dol_data))
        else:
            unmatched.append((cuid, name, domain))

    print(f"\n  DOL name match: {len(matched):,} ({100*len(matched)/max(len(eligible),1):.1f}%)")
    print(f"  No DOL match: {len(unmatched):,}")

    # Count address fill
    with_zip = sum(1 for _, _, _, d in matched if d.get('zip'))
    with_ein = sum(1 for _, _, _, d in matched if d.get('ein'))
    print(f"  With ZIP from DOL: {with_zip:,}")
    print(f"  With EIN from DOL: {with_ein:,}")

    # Return all eligible companies (matched + unmatched)
    # Unmatched get empty DOL data but still get onboarded
    companies = []
    for cuid, name, domain, dol_data in matched:
        companies.append({
            'cuid': cuid, 'name': name, 'domain': domain,
            'dol': dol_data,
        })
    for cuid, name, domain in unmatched:
        companies.append({
            'cuid': cuid, 'name': name, 'domain': domain,
            'dol': None,
        })

    return companies, excluded


# ══════════════════════════════════════════════════════════════
# STEP 2: Mint outreach_ids
# ══════════════════════════════════════════════════════════════

def step2_mint_outreach_ids(conn, companies, dry_run=False):
    """Mint outreach_ids for all eligible companies."""
    print(f"\n{'=' * 60}")
    print("STEP 2: Mint outreach_ids")
    print(f"{'=' * 60}")

    cur = conn.cursor()
    minted = 0
    errors = 0

    for co in companies:
        domain_clean = (co['domain'] or '').lower().strip() or None
        new_oid = str(uuid.uuid4())

        if dry_run:
            co['outreach_id'] = new_oid
            minted += 1
            continue

        try:
            # Insert into outreach.outreach (operational spine)
            cur.execute("""
                INSERT INTO outreach.outreach (outreach_id, sovereign_id, domain)
                VALUES (%s::uuid, %s::uuid, %s)
                ON CONFLICT DO NOTHING
            """, (new_oid, co['cuid'], domain_clean))

            if cur.rowcount == 0:
                # Might already exist by domain
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

            # Write outreach_id back to CL (WRITE-ONCE)
            cur.execute("""
                UPDATE cl.company_identity
                SET outreach_id = %s::uuid
                WHERE company_unique_id = %s::uuid AND outreach_id IS NULL
            """, (new_oid, co['cuid']))

            if cur.rowcount == 1:
                co['outreach_id'] = new_oid
                minted += 1
            else:
                # Already claimed — fetch existing
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

            if minted % 200 == 0:
                conn.commit()

        except Exception as e:
            print(f"    ERROR minting {co['cuid']}: {e}")
            conn.rollback()
            errors += 1
            co['outreach_id'] = None

    if not dry_run:
        conn.commit()

    print(f"  Minted: {minted:,}")
    print(f"  Errors: {errors:,}")
    return minted


# ══════════════════════════════════════════════════════════════
# STEP 3: Create company_target records
# ══════════════════════════════════════════════════════════════

def step3_create_company_targets(conn, companies, dry_run=False):
    """Create company_target records with DOL-derived addresses."""
    print(f"\n{'=' * 60}")
    print("STEP 3: Create company_target records")
    print(f"{'=' * 60}")

    cur = conn.cursor()

    # Check which already exist
    oid_list = [co['outreach_id'] for co in companies if co.get('outreach_id')]
    existing_ct = set()
    if oid_list:
        for i in range(0, len(oid_list), 5000):
            chunk = oid_list[i:i+5000]
            cur.execute("""
                SELECT outreach_id::text FROM outreach.company_target
                WHERE outreach_id = ANY(%s::uuid[])
            """, (chunk,))
            existing_ct.update(r[0] for r in cur.fetchall())

    print(f"  Already in CT: {len(existing_ct):,}")

    created = 0
    skipped = 0
    with_zip = 0
    ein_updates = 0

    for co in companies:
        oid = co.get('outreach_id')
        if not oid:
            continue
        if oid in existing_ct:
            skipped += 1
            continue

        dol = co.get('dol') or {}
        city = dol.get('city') or None
        state = dol.get('state') or 'NC'
        zip_code = dol.get('zip') or None
        ein = dol.get('ein') or None

        if zip_code:
            with_zip += 1

        if dry_run:
            created += 1
            continue

        try:
            cur.execute("""
                INSERT INTO outreach.company_target (
                    outreach_id, company_unique_id, source,
                    city, state, postal_code,
                    postal_code_source, postal_code_updated_at
                ) VALUES (
                    %s::uuid, %s, %s,
                    %s, %s, %s,
                    %s, %s
                )
                ON CONFLICT DO NOTHING
            """, (
                oid, co['cuid'], 'nc_hunter_dol_onboard_2026',
                city, state, zip_code,
                'dol_filing' if zip_code else None,
                datetime.now(timezone.utc) if zip_code else None,
            ))
            if cur.rowcount > 0:
                created += 1
        except Exception as e:
            print(f"    ERROR creating CT for {co['cuid']}: {e}")
            conn.rollback()

        if created % 200 == 0 and created > 0:
            conn.commit()

    # Write EIN to outreach.outreach where available
    for co in companies:
        oid = co.get('outreach_id')
        dol = co.get('dol') or {}
        ein = dol.get('ein')
        if not oid or not ein:
            continue
        if dry_run:
            ein_updates += 1
            continue
        try:
            cur.execute("""
                UPDATE outreach.outreach
                SET ein = %s
                WHERE outreach_id = %s::uuid AND (ein IS NULL OR ein = '')
            """, (ein, oid))
            if cur.rowcount > 0:
                ein_updates += 1
        except Exception as e:
            conn.rollback()

    if not dry_run:
        conn.commit()

    print(f"  Created: {created:,}")
    print(f"  With DOL ZIP: {with_zip:,}")
    print(f"  Skipped (already exist): {skipped:,}")
    print(f"  EINs written to spine: {ein_updates:,}")
    return created


# ══════════════════════════════════════════════════════════════
# STEP 4: Create company_slots (CEO/CFO/HR)
# ══════════════════════════════════════════════════════════════

def step4_create_slots(conn, companies, dry_run=False):
    """Create CEO/CFO/HR slots for all onboarded companies."""
    print(f"\n{'=' * 60}")
    print("STEP 4: Create company_slots (CEO/CFO/HR)")
    print(f"{'=' * 60}")

    cur = conn.cursor()

    # Check existing slots
    oid_list = [co['outreach_id'] for co in companies if co.get('outreach_id')]
    existing_slots = set()
    if oid_list:
        for i in range(0, len(oid_list), 5000):
            chunk = oid_list[i:i+5000]
            cur.execute("""
                SELECT outreach_id::text, slot_type
                FROM people.company_slot
                WHERE outreach_id = ANY(%s::uuid[])
            """, (chunk,))
            existing_slots.update((r[0], r[1]) for r in cur.fetchall())

    print(f"  Existing slots: {len(existing_slots):,}")

    created = 0
    for co in companies:
        oid = co.get('outreach_id')
        if not oid:
            continue

        for slot_type in ['CEO', 'CFO', 'HR']:
            if (oid, slot_type) in existing_slots:
                continue

            if dry_run:
                created += 1
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
                    created += 1
            except Exception as e:
                print(f"    ERROR slot {slot_type} for {oid}: {e}")
                conn.rollback()

        if created % 300 == 0 and created > 0 and not dry_run:
            conn.commit()

    if not dry_run:
        conn.commit()

    print(f"  Slots created: {created:,}")
    return created


# ══════════════════════════════════════════════════════════════
# STEP 5: Create outreach.dol records
# ══════════════════════════════════════════════════════════════

def step5_create_dol_records(conn, companies, dry_run=False):
    """Create outreach.dol records for companies with DOL matches."""
    print(f"\n{'=' * 60}")
    print("STEP 5: Create outreach.dol records")
    print(f"{'=' * 60}")

    cur = conn.cursor()

    # Check existing DOL records
    oid_list = [co['outreach_id'] for co in companies if co.get('outreach_id')]
    existing_dol = set()
    if oid_list:
        for i in range(0, len(oid_list), 5000):
            chunk = oid_list[i:i+5000]
            cur.execute("""
                SELECT outreach_id::text FROM outreach.dol
                WHERE outreach_id = ANY(%s::uuid[])
            """, (chunk,))
            existing_dol.update(r[0] for r in cur.fetchall())

    print(f"  Existing DOL records: {len(existing_dol):,}")

    created = 0
    skipped_no_dol = 0

    for co in companies:
        oid = co.get('outreach_id')
        dol = co.get('dol')
        if not oid:
            continue
        if not dol:
            skipped_no_dol += 1
            continue
        if oid in existing_dol:
            continue

        dol_id = str(uuid.uuid4())
        ein = dol.get('ein') or None
        filing_present = dol.get('filing_present', False)
        funding_type = dol.get('funding_type') or 'unknown'
        carrier = dol.get('carrier') or None
        broker = dol.get('broker') or None
        renewal_month = dol.get('renewal_month')
        outreach_start_month = dol.get('outreach_start_month')

        if dry_run:
            created += 1
            continue

        try:
            cur.execute("""
                INSERT INTO outreach.dol
                    (dol_id, outreach_id, ein, filing_present, funding_type,
                     carrier, broker_or_advisor, renewal_month, outreach_start_month,
                     created_at, updated_at)
                SELECT %s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                WHERE NOT EXISTS (
                    SELECT 1 FROM outreach.dol WHERE outreach_id = %s::uuid
                )
            """, (dol_id, oid, ein, filing_present, funding_type,
                  carrier, broker, renewal_month, outreach_start_month, oid))
            if cur.rowcount > 0:
                created += 1
        except Exception as e:
            print(f"    ERROR DOL for {oid}: {e}")
            conn.rollback()

        if created % 200 == 0 and created > 0:
            conn.commit()

    if not dry_run:
        conn.commit()

    print(f"  DOL records created: {created:,}")
    print(f"  No DOL match (skipped): {skipped_no_dol:,}")
    return created


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Onboard NC HUNTER_DOL_SS003 companies')
    parser.add_argument('--dry-run', action='store_true', help='Preview without DB writes')
    parser.add_argument('--step', type=int, help='Run a single step (1-5)')
    args = parser.parse_args()

    print("=" * 60)
    print("NC HUNTER_DOL_SS003 Onboarding Pipeline")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)

    conn = get_conn()

    try:
        # Step 1 always runs (loads data for other steps)
        companies, excluded = step1_load_and_match(conn, dry_run=args.dry_run)

        if not companies:
            print("\nNo eligible companies found. Nothing to do.")
            return

        if args.step and args.step != 1:
            # Load existing outreach_ids for companies if skipping step 2
            cur = conn.cursor()
            for co in companies:
                cur.execute("""
                    SELECT outreach_id::text FROM cl.company_identity
                    WHERE company_unique_id = %s::uuid
                """, (co['cuid'],))
                row = cur.fetchone()
                co['outreach_id'] = row[0] if row and row[0] else None

        if not args.step or args.step == 2:
            step2_mint_outreach_ids(conn, companies, dry_run=args.dry_run)

        if not args.step or args.step == 3:
            step3_create_company_targets(conn, companies, dry_run=args.dry_run)

        if not args.step or args.step == 4:
            step4_create_slots(conn, companies, dry_run=args.dry_run)

        if not args.step or args.step == 5:
            step5_create_dol_records(conn, companies, dry_run=args.dry_run)

        # Final summary
        print(f"\n{'=' * 60}")
        print("SUMMARY")
        print(f"{'=' * 60}")
        with_oid = sum(1 for co in companies if co.get('outreach_id'))
        with_dol = sum(1 for co in companies if co.get('dol'))
        with_zip = sum(1 for co in companies if co.get('dol') and co['dol'].get('zip'))
        print(f"  Total eligible:     {len(companies):,}")
        print(f"  Non-commercial out: {len(excluded):,}")
        print(f"  With outreach_id:   {with_oid:,}")
        print(f"  With DOL match:     {with_dol:,}")
        print(f"  With DOL ZIP:       {with_zip:,}")

        if not args.dry_run:
            # Verify counts in DB
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM outreach.company_target ct
                JOIN cl.company_identity ci ON ct.outreach_id = ci.outreach_id
                WHERE ci.source_system = 'HUNTER_DOL_SS003' AND ci.state_code = 'NC'
            """)
            ct_count = cur.fetchone()[0]
            cur.execute("""
                SELECT COUNT(*) FROM outreach.dol d
                JOIN cl.company_identity ci ON d.outreach_id = ci.outreach_id
                WHERE ci.source_system = 'HUNTER_DOL_SS003' AND ci.state_code = 'NC'
            """)
            dol_count = cur.fetchone()[0]
            cur.execute("""
                SELECT COUNT(*) FROM people.company_slot cs
                JOIN cl.company_identity ci ON cs.outreach_id = ci.outreach_id
                WHERE ci.source_system = 'HUNTER_DOL_SS003' AND ci.state_code = 'NC'
            """)
            slot_count = cur.fetchone()[0]

            print(f"\n  DB verification:")
            print(f"    CT records:   {ct_count:,}")
            print(f"    DOL records:  {dol_count:,}")
            print(f"    Slots:        {slot_count:,}")

    finally:
        conn.close()


if __name__ == '__main__':
    main()
