#!/usr/bin/env python3
"""
Bridge SC companies to DOL filings → create outreach.dol records.

Match strategies (in priority order):
  1. Domain bridge via dol.ein_urls (domain → EIN)
  2. Exact normalized name match against form_5500 / form_5500_sf
  3. Suffix-stripped name match (remove INC, LLC, CORP, etc.)

For each match, derives:
  - ein, filing_present, funding_type
  - renewal_month, outreach_start_month
  - carrier (from schedule_a), broker_or_advisor (from schedule_c)

Usage:
    doppler run -- python scripts/sc_dol_bridge.py --dry-run
    doppler run -- python scripts/sc_dol_bridge.py
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


SUFFIX_PATTERN = re.compile(
    r'\b(INC|LLC|CORP|CORPORATION|CO|COMPANY|COMPANIES|LTD|LP|LLP|PA|PLLC|PC|'
    r'DBA|GROUP|ASSOCIATES|INTERNATIONAL|SERVICES|SERVICE|SOLUTIONS|ENTERPRISES|'
    r'HOLDINGS|CONSULTING|MANAGEMENT|TECHNOLOGIES|TECHNOLOGY|SYSTEMS|INDUSTRIES)\b'
)


def get_conn():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        dbname=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require',
    )


def normalize(name):
    """Normalize company name for matching."""
    if not name:
        return ''
    n = name.upper().strip()
    n = re.sub(r'[,.\'"()&]', ' ', n)
    n = re.sub(r'\s+', ' ', n)
    return n.strip()


def strip_suffixes(name):
    """Remove common corporate suffixes."""
    stripped = SUFFIX_PATTERN.sub('', name).strip()
    stripped = re.sub(r'\s+', ' ', stripped).strip()
    return stripped


def derive_funding_type(row):
    """Derive funding_type from form_5500 fields."""
    pension = row.get('type_pension_bnft_code')
    welfare = row.get('type_welfare_bnft_code')
    fund_ins = row.get('funding_insurance_ind')
    fund_trust = row.get('funding_trust_ind')

    if pension and not welfare:
        return 'pension_only'
    if fund_trust == '1':
        return 'self_funded'
    if fund_ins == '1' and (not fund_trust or fund_trust == '0'):
        return 'fully_insured'
    return 'unknown'


def main():
    parser = argparse.ArgumentParser(description='Bridge SC companies to DOL filings')
    parser.add_argument('--dry-run', action='store_true', help='Preview without DB writes')
    args = parser.parse_args()

    print("=" * 60)
    print("SC DOL BRIDGE — Link Companies to DOL Filings")
    print("=" * 60)
    print(f"Mode:    {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Started: {datetime.now().isoformat()}")

    conn = get_conn()
    cur = conn.cursor()

    # ── Load SC companies without DOL records ──
    cur.execute("""
        SELECT ci.company_unique_id::text,
               ci.company_name,
               ci.company_domain,
               ci.source_system,
               o.outreach_id::text
        FROM cl.company_identity ci
        JOIN outreach.outreach o ON o.sovereign_id = ci.company_unique_id
        WHERE ci.state_code = 'SC'
          AND NOT EXISTS (
              SELECT 1 FROM outreach.dol d WHERE d.outreach_id = o.outreach_id
          )
        ORDER BY ci.company_name
    """)
    companies = cur.fetchall()
    total = len(companies)
    print(f"\nSC companies without DOL: {total:,}")

    if total == 0:
        print("All SC companies already have DOL records!")
        conn.close()
        return

    # Build lookup maps
    oid_by_cuid = {}
    name_by_cuid = {}
    domain_by_cuid = {}
    for cuid, name, domain, src, oid in companies:
        oid_by_cuid[cuid] = oid
        name_by_cuid[cuid] = name
        domain_by_cuid[cuid] = domain

    # ── STRATEGY 1: Domain bridge via dol.ein_urls ──
    print(f"\n{'=' * 60}")
    print("STRATEGY 1: Domain bridge (dol.ein_urls)")
    print(f"{'=' * 60}")

    cur.execute("""
        SELECT ci.company_unique_id::text, eu.ein
        FROM cl.company_identity ci
        JOIN dol.ein_urls eu ON LOWER(ci.company_domain) = LOWER(eu.domain)
        JOIN outreach.outreach o ON o.sovereign_id = ci.company_unique_id
        WHERE ci.state_code = 'SC'
          AND NOT EXISTS (
              SELECT 1 FROM outreach.dol d WHERE d.outreach_id = o.outreach_id
          )
    """)
    domain_matches = {}
    for cuid, ein in cur.fetchall():
        domain_matches[cuid] = ein
    print(f"  Domain bridge matches: {len(domain_matches):,}")

    # ── Load DOL SC filings ──
    print(f"\n{'=' * 60}")
    print("Loading DOL SC filings...")
    print(f"{'=' * 60}")

    # form_5500: latest filing per EIN (SC)
    cur.execute("""
        SELECT DISTINCT ON (sponsor_dfe_ein)
               UPPER(TRIM(sponsor_dfe_name)) as name,
               sponsor_dfe_ein as ein,
               form_plan_year_begin_date,
               type_pension_bnft_code,
               type_welfare_bnft_code,
               funding_insurance_ind,
               funding_trust_ind
        FROM dol.form_5500
        WHERE UPPER(TRIM(spons_dfe_mail_us_state)) = 'SC'
          AND sponsor_dfe_ein IS NOT NULL
          AND sponsor_dfe_ein <> ''
        ORDER BY sponsor_dfe_ein, ack_id DESC
    """)
    f5500_by_name = {}
    f5500_by_ein = {}
    for row in cur.fetchall():
        name, ein, plan_begin, pension, welfare, fund_ins, fund_trust = row
        entry = {
            'ein': ein,
            'plan_begin': plan_begin,
            'type_pension_bnft_code': pension,
            'type_welfare_bnft_code': welfare,
            'funding_insurance_ind': fund_ins,
            'funding_trust_ind': fund_trust,
            'source': 'form_5500',
        }
        norm = normalize(name)
        if norm:
            f5500_by_name[norm] = entry
        if ein:
            f5500_by_ein[ein] = entry
    print(f"  form_5500 SC filings (by EIN): {len(f5500_by_ein):,}")
    print(f"  form_5500 SC filings (by name): {len(f5500_by_name):,}")

    # form_5500_sf: latest filing per EIN (SC)
    cur.execute("""
        SELECT DISTINCT ON (sf_spons_ein)
               UPPER(TRIM(sf_sponsor_name)) as name,
               sf_spons_ein as ein,
               sf_plan_year_begin_date,
               sf_type_pension_bnft_code,
               sf_type_welfare_bnft_code
        FROM dol.form_5500_sf
        WHERE UPPER(TRIM(sf_spons_us_state)) = 'SC'
          AND sf_spons_ein IS NOT NULL
          AND sf_spons_ein <> ''
        ORDER BY sf_spons_ein, ack_id DESC
    """)
    f5500sf_by_name = {}
    f5500sf_by_ein = {}
    for row in cur.fetchall():
        name, ein, plan_begin, pension, welfare = row
        entry = {
            'ein': ein,
            'plan_begin': plan_begin,
            'type_pension_bnft_code': pension,
            'type_welfare_bnft_code': welfare,
            'funding_insurance_ind': None,
            'funding_trust_ind': None,
            'source': 'form_5500_sf',
        }
        norm = normalize(name)
        if norm:
            f5500sf_by_name[norm] = entry
        if ein:
            f5500sf_by_ein[ein] = entry
    print(f"  form_5500_sf SC filings (by EIN): {len(f5500sf_by_ein):,}")
    print(f"  form_5500_sf SC filings (by name): {len(f5500sf_by_name):,}")

    # Combined name lookup: form_5500 takes priority
    dol_by_name = {}
    dol_by_name.update(f5500sf_by_name)
    dol_by_name.update(f5500_by_name)
    print(f"  Combined unique names: {len(dol_by_name):,}")

    # Pre-compute stripped versions of DOL names
    dol_stripped = {}
    for dol_name, entry in dol_by_name.items():
        stripped = strip_suffixes(dol_name)
        if stripped and len(stripped) >= 3:
            dol_stripped[stripped] = entry

    # ── Load carrier and broker data by EIN ──
    print(f"\nLoading carrier/broker data...")
    cur.execute("""
        SELECT DISTINCT ON (sch_a_ein)
               sch_a_ein, ins_carrier_name
        FROM dol.schedule_a
        WHERE sponsor_state = 'SC'
          AND ins_carrier_name IS NOT NULL
          AND ins_carrier_name <> ''
        ORDER BY sch_a_ein, ack_id DESC
    """)
    carriers_by_ein = {}
    for ein, carrier in cur.fetchall():
        carriers_by_ein[ein] = carrier
    print(f"  SC carriers (by EIN): {len(carriers_by_ein):,}")

    # Schedule C for brokers — check column names
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'dol' AND table_name = 'schedule_c'
        ORDER BY ordinal_position
    """)
    sched_c_cols = [c[0] for c in cur.fetchall()]

    brokers_by_ein = {}
    if 'provider_name' in sched_c_cols:
        cur.execute("""
            SELECT DISTINCT ON (ein)
                   ein, provider_name
            FROM dol.schedule_c
            WHERE provider_name IS NOT NULL AND provider_name <> ''
            ORDER BY ein, ack_id DESC
        """)
        for ein, broker in cur.fetchall():
            brokers_by_ein[ein] = broker
    print(f"  SC brokers (by EIN): {len(brokers_by_ein):,}")

    # ══════════════════════════════════════════════════════════════
    # MATCHING
    # ══════════════════════════════════════════════════════════════
    print(f"\n{'=' * 60}")
    print("MATCHING")
    print(f"{'=' * 60}")

    matches = {}  # cuid -> {ein, filing, ...}
    match_method = defaultdict(int)

    for cuid, name, domain, src, oid in companies:
        # Strategy 1: Domain bridge
        if cuid in domain_matches:
            ein = domain_matches[cuid]
            # Look up filing details by EIN
            filing = f5500_by_ein.get(ein) or f5500sf_by_ein.get(ein)
            if filing:
                matches[cuid] = filing
                match_method['domain_bridge'] += 1
                continue
            else:
                # Have EIN but no SC filing details — still record EIN
                matches[cuid] = {
                    'ein': ein,
                    'plan_begin': None,
                    'type_pension_bnft_code': None,
                    'type_welfare_bnft_code': None,
                    'funding_insurance_ind': None,
                    'funding_trust_ind': None,
                    'source': 'domain_bridge',
                }
                match_method['domain_bridge_ein_only'] += 1
                continue

        # Strategy 2: Exact normalized name match
        norm = normalize(name)
        if norm in dol_by_name:
            matches[cuid] = dol_by_name[norm]
            match_method['exact_name'] += 1
            continue

        # Strategy 3: Suffix-stripped name match
        stripped = strip_suffixes(norm)
        if stripped and len(stripped) >= 3 and stripped in dol_stripped:
            matches[cuid] = dol_stripped[stripped]
            match_method['suffix_stripped'] += 1
            continue

    print(f"\n  Match results:")
    for method, cnt in sorted(match_method.items(), key=lambda x: -x[1]):
        print(f"    {method:<25s} {cnt:,}")
    print(f"    {'─' * 40}")
    print(f"    Total matched:            {len(matches):,}")
    print(f"    Unmatched:                {total - len(matches):,}")

    # ══════════════════════════════════════════════════════════════
    # INSERT INTO outreach.dol
    # ══════════════════════════════════════════════════════════════
    print(f"\n{'=' * 60}")
    print(f"{'INSERTING' if not args.dry_run else 'WOULD INSERT'} DOL RECORDS")
    print(f"{'=' * 60}")

    inserted = 0
    errors = 0

    for cuid, filing in matches.items():
        oid = oid_by_cuid[cuid]
        ein = filing['ein']

        # Derive funding_type
        funding_type = derive_funding_type(filing)

        # Derive renewal_month from plan_year_begin_date
        plan_begin = filing.get('plan_begin')
        renewal_month = None
        outreach_start_month = None
        if plan_begin:
            try:
                renewal_month = plan_begin.month
                outreach_start_month = ((renewal_month - 5 - 1) % 12) + 1
            except Exception:
                pass

        # Carrier and broker
        carrier = carriers_by_ein.get(ein)
        broker = brokers_by_ein.get(ein)

        # Filing present?
        filing_present = ein in f5500_by_ein or ein in f5500sf_by_ein

        if not args.dry_run:
            try:
                dol_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO outreach.dol
                        (dol_id, outreach_id, ein, filing_present, funding_type,
                         carrier, broker_or_advisor, renewal_month, outreach_start_month,
                         created_at, updated_at)
                    SELECT %s, %s::uuid, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    WHERE NOT EXISTS (
                        SELECT 1 FROM outreach.dol WHERE outreach_id = %s::uuid
                    )
                """, (
                    dol_id, oid, ein, filing_present, funding_type,
                    carrier, broker, renewal_month, outreach_start_month,
                    oid,
                ))
                if cur.rowcount > 0:
                    inserted += 1
            except Exception as e:
                print(f"    ERROR for {oid}: {e}")
                conn.rollback()
                errors += 1
        else:
            inserted += 1

        # Commit every 500
        if not args.dry_run and inserted % 500 == 0 and inserted > 0:
            conn.commit()

    if not args.dry_run:
        conn.commit()

    # ══════════════════════════════════════════════════════════════
    # RESULTS
    # ══════════════════════════════════════════════════════════════
    print(f"\n{'=' * 60}")
    print("RESULTS")
    print(f"{'=' * 60}")
    print(f"  DOL records created: {inserted:,}")
    print(f"  Errors:              {errors:,}")

    # Enrichment breakdown
    funding_counts = defaultdict(int)
    has_renewal = 0
    has_carrier = 0
    has_broker = 0
    for cuid, filing in matches.items():
        ft = derive_funding_type(filing)
        funding_counts[ft] += 1
        if filing.get('plan_begin'):
            has_renewal += 1
        if carriers_by_ein.get(filing['ein']):
            has_carrier += 1
        if brokers_by_ein.get(filing['ein']):
            has_broker += 1

    print(f"\n  Enrichment levels ({inserted:,} records):")
    print(f"    Funding type breakdown:")
    for ft, cnt in sorted(funding_counts.items(), key=lambda x: -x[1]):
        print(f"      {ft:<20s} {cnt:,}")
    print(f"    With renewal_month:   {has_renewal:,}")
    print(f"    With carrier:         {has_carrier:,}")
    print(f"    With broker:          {has_broker:,}")

    # Final SC DOL status
    try:
        conn.close()
    except Exception:
        pass
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*),
               COUNT(CASE WHEN EXISTS (
                   SELECT 1 FROM outreach.dol d
                   WHERE d.outreach_id = o.outreach_id
               ) THEN 1 END)
        FROM outreach.outreach o
        JOIN cl.company_identity ci ON ci.company_unique_id = o.sovereign_id
        WHERE ci.state_code = 'SC'
    """)
    total_sc, with_dol = cur.fetchone()

    print(f"\nFINAL SC DOL STATUS:")
    print(f"  Total SC in outreach: {total_sc:,}")
    print(f"  With DOL record:      {with_dol:,} ({100*with_dol/max(1,total_sc):.1f}%)")
    print(f"  Without DOL record:   {total_sc - with_dol:,}")
    print(f"{'=' * 60}")
    print(f"Completed: {datetime.now().isoformat()}")

    if args.dry_run:
        print("\n[DRY RUN — No data was written]")

    conn.close()


if __name__ == '__main__':
    main()
