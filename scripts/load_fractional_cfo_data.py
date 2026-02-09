#!/usr/bin/env python3
"""
Load fractional CFO data from CSV files into production tables.

Steps:
  1. Load Hunter-enriched contacts into enrichment.hunter_contact
  2. Mint outreach_ids for fractional CFO companies (CL → outreach.outreach)
  3. Write outreach_ids back to CL
  4. Create company_target records
  5. Populate partners.fractional_cfo_master with best contact per firm

Usage:
    doppler run -- python scripts/load_fractional_cfo_data.py [--dry-run]
"""
import os
import sys
import io
import uuid
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import psycopg2

DRY_RUN = '--dry-run' in sys.argv

CSV_FILES = [
    r'C:\Users\CUSTOM PC\Desktop\fractioanl-cfo-2-2131130.csv',
    r'C:\Users\CUSTOM PC\Desktop\clay-fractional-cfo-2131129.csv',
]

# Priority for selecting "best" contact per company for partners table
TITLE_PRIORITY = [
    'founder', 'co-founder', 'cofounder', 'ceo', 'chief executive',
    'president', 'owner', 'managing partner', 'managing director',
    'partner', 'principal', 'cfo', 'chief financial', 'director'
]


def title_score(title):
    """Higher score = better primary contact."""
    if not title:
        return 0
    t = title.lower()
    for i, kw in enumerate(TITLE_PRIORITY):
        if kw in t:
            return len(TITLE_PRIORITY) - i
    return 0


def main():
    print("=" * 60)
    print("LOAD FRACTIONAL CFO DATA")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE'}")
    print(f"Started: {datetime.now().isoformat()}")

    # ── Load CSVs ──
    dfs = [pd.read_csv(f, low_memory=False) for f in CSV_FILES]
    combined = pd.concat(dfs, ignore_index=True)
    print(f"\n  CSV rows loaded: {len(combined):,}")

    # Dedup by email
    combined = combined.drop_duplicates(subset=['Email address'])
    print(f"  After email dedup: {len(combined):,}")

    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    # ── Get existing CL fractional CFO records ──
    cur.execute("""
        SELECT company_unique_id, LOWER(company_domain), company_name, outreach_id
        FROM cl.company_identity
        WHERE source_system = 'fractional_cfo_outreach'
    """)
    cl_records = {r[1]: {'cid': r[0], 'name': r[2], 'oid': r[3]} for r in cur.fetchall() if r[1]}
    print(f"  CL fractional_cfo_outreach: {len(cl_records):,}")

    # ══════════════════════════════════════════════════════════════
    # STEP 1: Load contacts into enrichment.hunter_contact
    # ══════════════════════════════════════════════════════════════
    print(f"\n{'─' * 60}")
    print("STEP 1: Load contacts into enrichment.hunter_contact")
    print(f"{'─' * 60}")

    # Check what's already in hunter_contact
    cur.execute("SELECT LOWER(email) FROM enrichment.hunter_contact WHERE email IS NOT NULL")
    existing_emails = {r[0] for r in cur.fetchall()}
    print(f"  Existing hunter_contact emails: {len(existing_emails):,}")

    loaded = 0
    skipped_existing = 0
    for _, row in combined.iterrows():
        email = str(row.get('Email address', '')).strip()
        if not email or email.lower() in existing_emails:
            skipped_existing += 1
            continue

        domain = str(row.get('Domain (2)', '') or row.get('Domain', '') or '').lower().strip()
        first_name = str(row.get('First name', '') or '').strip()
        last_name = str(row.get('Last name', '') or '').strip()
        job_title = str(row.get('Job title', '') or '').strip()
        linkedin = str(row.get('LinkedIn URL', '') or '').strip()
        phone = str(row.get('Phone number', '') or '').strip()
        confidence = row.get('Confidence score')
        org = str(row.get('Organization', '') or '').strip()

        # Clean up 'nan' strings
        for var_name in ['domain', 'first_name', 'last_name', 'job_title', 'linkedin', 'phone', 'org']:
            val = locals()[var_name]
            if val == 'nan':
                locals()[var_name] = ''

        if not DRY_RUN:
            try:
                cur.execute("""
                    INSERT INTO enrichment.hunter_contact (
                        email, domain, first_name, last_name, job_title,
                        linkedin_url, phone_number, confidence_score, organization,
                        source_file, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT DO NOTHING
                """, (
                    email.lower(), domain or None, first_name or None, last_name or None,
                    job_title or None, linkedin or None, phone or None,
                    int(confidence) if pd.notna(confidence) else None,
                    org or None, 'fractional-cfo-csv'
                ))
                if cur.rowcount > 0:
                    loaded += 1
                    existing_emails.add(email.lower())
                else:
                    skipped_existing += 1
            except Exception as e:
                conn.rollback()
                skipped_existing += 1
        else:
            loaded += 1
            existing_emails.add(email.lower())

    if not DRY_RUN:
        conn.commit()
    print(f"  Loaded: {loaded:,}")
    print(f"  Skipped (already existed): {skipped_existing:,}")

    # ══════════════════════════════════════════════════════════════
    # STEP 2: Mint outreach_ids for fractional CFO companies
    # ══════════════════════════════════════════════════════════════
    print(f"\n{'─' * 60}")
    print("STEP 2: Mint outreach_ids for fractional CFO companies")
    print(f"{'─' * 60}")

    # Refresh CL records
    cur.execute("""
        SELECT company_unique_id, LOWER(company_domain), company_name, outreach_id
        FROM cl.company_identity
        WHERE source_system = 'fractional_cfo_outreach'
          AND outreach_id IS NULL
          AND company_domain IS NOT NULL AND company_domain <> ''
    """)
    need_oid = cur.fetchall()
    print(f"  Companies needing outreach_id: {len(need_oid):,}")

    minted = 0
    mint_errors = 0
    for cid, domain, name, _ in need_oid:
        new_oid = str(uuid.uuid4())

        if DRY_RUN:
            minted += 1
            continue

        try:
            # Step 1: Insert into outreach.outreach (operational spine)
            cur.execute("""
                INSERT INTO outreach.outreach (outreach_id, sovereign_id, domain)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (new_oid, cid, domain))

            if cur.rowcount == 0:
                # Domain might already be in outreach - check
                cur.execute("SELECT outreach_id FROM outreach.outreach WHERE LOWER(domain) = %s", (domain,))
                existing = cur.fetchone()
                if existing:
                    new_oid = str(existing[0])
                else:
                    mint_errors += 1
                    continue

            # Step 2: Write outreach_id back to CL (WRITE-ONCE)
            cur.execute("""
                UPDATE cl.company_identity
                SET outreach_id = %s
                WHERE company_unique_id = %s AND outreach_id IS NULL
            """, (new_oid, cid))

            if cur.rowcount == 1:
                minted += 1
            else:
                mint_errors += 1

            if minted % 100 == 0:
                conn.commit()

        except Exception as e:
            conn.rollback()
            mint_errors += 1

    if not DRY_RUN:
        conn.commit()
    print(f"  Minted: {minted:,}")
    print(f"  Errors: {mint_errors:,}")

    # ══════════════════════════════════════════════════════════════
    # STEP 3: Create company_target records
    # ══════════════════════════════════════════════════════════════
    print(f"\n{'─' * 60}")
    print("STEP 3: Create company_target records")
    print(f"{'─' * 60}")

    cur.execute("""
        SELECT ci.outreach_id, ci.company_domain
        FROM cl.company_identity ci
        WHERE ci.source_system = 'fractional_cfo_outreach'
          AND ci.outreach_id IS NOT NULL
          AND ci.outreach_id NOT IN (SELECT outreach_id FROM outreach.company_target)
    """)
    need_ct = cur.fetchall()
    print(f"  Companies needing company_target: {len(need_ct):,}")

    ct_created = 0
    for oid, domain in need_ct:
        if DRY_RUN:
            ct_created += 1
            continue
        try:
            cur.execute("""
                INSERT INTO outreach.company_target (outreach_id, domain)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (oid, domain))
            if cur.rowcount > 0:
                ct_created += 1
        except Exception as e:
            conn.rollback()

    if not DRY_RUN:
        conn.commit()
    print(f"  Created: {ct_created:,}")

    # ══════════════════════════════════════════════════════════════
    # STEP 4: Populate partners.fractional_cfo_master
    # ══════════════════════════════════════════════════════════════
    print(f"\n{'─' * 60}")
    print("STEP 4: Populate partners.fractional_cfo_master")
    print(f"{'─' * 60}")

    # For each company, pick the best contact by title priority
    # Group CSV data by domain
    company_contacts = {}
    for _, row in combined.iterrows():
        domain = str(row.get('Domain (2)', '') or row.get('Domain', '') or '').lower().strip()
        if not domain or domain == 'nan':
            continue
        if domain not in company_contacts:
            company_contacts[domain] = []
        company_contacts[domain].append(row)

    # Refresh CL with outreach_ids
    cur.execute("""
        SELECT company_unique_id, LOWER(company_domain), company_name,
               linkedin_company_url, employee_count_band
        FROM cl.company_identity
        WHERE source_system = 'fractional_cfo_outreach'
          AND company_domain IS NOT NULL AND company_domain <> ''
    """)
    cl_all = {r[1]: {'cid': r[0], 'name': r[2], 'li': r[3], 'size': r[4]} for r in cur.fetchall()}

    # Check existing
    cur.execute("SELECT firm_name FROM partners.fractional_cfo_master")
    existing_firms = {r[0] for r in cur.fetchall()}
    print(f"  Existing partners: {len(existing_firms):,}")

    partner_created = 0
    for domain, cl_info in cl_all.items():
        firm_name = cl_info['name']
        if firm_name in existing_firms:
            continue

        # Find best contact from CSV
        contacts = company_contacts.get(domain, [])
        if contacts:
            # Sort by title priority
            best = max(contacts, key=lambda r: title_score(str(r.get('Job title', ''))))
            primary_name = f"{str(best.get('First name', '')).strip()} {str(best.get('Last name', '')).strip()}".strip()
            primary_email = str(best.get('Email address', '')).strip().lower()
            primary_linkedin = str(best.get('LinkedIn URL', '')).strip()
            primary_title = str(best.get('Job title', '')).strip()
        else:
            primary_name = ''
            primary_email = None
            primary_linkedin = None
            primary_title = None

        # Clean nan
        if primary_name == 'nan nan' or primary_name == 'nan':
            primary_name = ''
        if primary_email == 'nan':
            primary_email = None
        if primary_linkedin == 'nan':
            primary_linkedin = None

        if not primary_name:
            primary_name = firm_name  # fallback

        if DRY_RUN:
            partner_created += 1
            continue

        try:
            cur.execute("""
                INSERT INTO partners.fractional_cfo_master (
                    fractional_cfo_id, firm_name, primary_contact_name,
                    linkedin_url, email, geography, niche_focus,
                    source, source_detail, status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, 'prospect'
                )
                ON CONFLICT DO NOTHING
            """, (
                cl_info['cid'],  # Use sovereign ID as fractional_cfo_id
                firm_name,
                primary_name,
                primary_linkedin,
                primary_email,
                cl_info.get('size', ''),  # geography approximation from size
                'fractional_cfo',
                'clay_hunter_enrichment',
                f"CSV: {', '.join(os.path.basename(f) for f in CSV_FILES)}"
            ))
            if cur.rowcount > 0:
                partner_created += 1
        except Exception as e:
            conn.rollback()

    if not DRY_RUN:
        conn.commit()
    print(f"  Partners created: {partner_created:,}")

    # ── Summary ──
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Hunter contacts loaded:     {loaded:,}")
    print(f"  Outreach IDs minted:        {minted:,}")
    print(f"  Company targets created:    {ct_created:,}")
    print(f"  Partners created:           {partner_created:,}")
    print(f"\nCompleted: {datetime.now().isoformat()}")

    conn.close()


if __name__ == "__main__":
    main()
