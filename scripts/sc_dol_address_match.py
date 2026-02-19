"""
Match SC HUNTER_DOL companies against DOL filings to get addresses.

Matches company_name against sponsor_dfe_name (form_5500) and
sf_sponsor_name (form_5500_sf), filtered to SC filings.

Usage:
    doppler run -- python scripts/sc_dol_address_match.py
"""
import os, sys, io, csv, re
from collections import defaultdict

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import psycopg2

CSV_IN = r'C:\Users\CUSTOM PC\Desktop\sc_companies_export.csv'
CSV_OUT = r'C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\exports\sc_companies_with_addresses.csv'


def normalize(name):
    """Normalize company name for matching."""
    if not name:
        return ''
    n = name.upper().strip()
    # Remove common suffixes and punctuation
    n = re.sub(r'[,.\'"()]', '', n)
    n = re.sub(r'\s+', ' ', n)
    return n.strip()


def main():
    # Load CSV
    with open(CSV_IN, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    all_companies = {r['company_unique_id'].strip(): r for r in rows}
    hunter_dol = {k: v for k, v in all_companies.items()
                  if v.get('source_system') == 'HUNTER_DOL_SS003'}
    clay = {k: v for k, v in all_companies.items()
            if v.get('source_system') == 'CLAY_SC_SS005'}

    print(f"Total companies: {len(all_companies):,}")
    print(f"  HUNTER_DOL: {len(hunter_dol):,}")
    print(f"  CLAY:       {len(clay):,}")

    conn = psycopg2.connect(
        host=os.environ['NEON_HOST'],
        dbname=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require',
    )
    cur = conn.cursor()

    # ── Pull ALL SC DOL addresses from both filing tables ──
    print("\nLoading DOL SC filings...")

    # form_5500: latest filing per company name (SC only)
    cur.execute("""
        SELECT DISTINCT ON (UPPER(TRIM(sponsor_dfe_name)))
               UPPER(TRIM(sponsor_dfe_name)) as name,
               sponsor_dfe_ein,
               TRIM(spons_dfe_mail_us_city) as city,
               TRIM(spons_dfe_mail_us_state) as state,
               LEFT(TRIM(spons_dfe_mail_us_zip), 5) as zip,
               TRIM(spons_dfe_mail_us_address1) as addr1,
               TRIM(spons_dfe_mail_us_address2) as addr2
        FROM dol.form_5500
        WHERE UPPER(TRIM(spons_dfe_mail_us_state)) = 'SC'
          AND spons_dfe_mail_us_zip IS NOT NULL
          AND spons_dfe_mail_us_zip <> ''
        ORDER BY UPPER(TRIM(sponsor_dfe_name)), ack_id DESC
    """)
    f5500_by_name = {}
    for r in cur.fetchall():
        f5500_by_name[normalize(r[0])] = {
            'ein': r[1], 'city': r[2], 'state': r[3], 'zip': r[4],
            'addr1': r[5], 'addr2': r[6], 'source': 'form_5500',
        }
    print(f"  form_5500 SC companies: {len(f5500_by_name):,}")

    # form_5500_sf: latest filing per company name (SC only)
    cur.execute("""
        SELECT DISTINCT ON (UPPER(TRIM(sf_sponsor_name)))
               UPPER(TRIM(sf_sponsor_name)) as name,
               sf_spons_ein,
               TRIM(sf_spons_us_city) as city,
               TRIM(sf_spons_us_state) as state,
               LEFT(TRIM(sf_spons_us_zip), 5) as zip,
               TRIM(sf_spons_us_address1) as addr1,
               TRIM(sf_spons_us_address2) as addr2
        FROM dol.form_5500_sf
        WHERE UPPER(TRIM(sf_spons_us_state)) = 'SC'
          AND sf_spons_us_zip IS NOT NULL
          AND sf_spons_us_zip <> ''
        ORDER BY UPPER(TRIM(sf_sponsor_name)), ack_id DESC
    """)
    f5500sf_by_name = {}
    for r in cur.fetchall():
        f5500sf_by_name[normalize(r[0])] = {
            'ein': r[1], 'city': r[2], 'state': r[3], 'zip': r[4],
            'addr1': r[5], 'addr2': r[6], 'source': 'form_5500_sf',
        }
    print(f"  form_5500_sf SC companies: {len(f5500sf_by_name):,}")

    # Combine: prefer form_5500 (larger filings) over form_5500_sf
    dol_addresses = {}
    dol_addresses.update(f5500sf_by_name)
    dol_addresses.update(f5500_by_name)  # f5500 overwrites sf
    print(f"  Combined unique SC DOL names: {len(dol_addresses):,}")

    # ── Match HUNTER_DOL companies ──
    print(f"\n{'='*60}")
    print("Matching HUNTER_DOL companies...")
    print(f"{'='*60}")

    matched = {}
    unmatched = []

    for cuid, row in hunter_dol.items():
        name = row.get('company_name', '').strip()
        norm = normalize(name)

        # Try exact normalized match
        if norm in dol_addresses:
            matched[cuid] = dol_addresses[norm]
            continue

        # Try without common suffixes (INC, LLC, CORP, etc.)
        stripped = re.sub(r'\b(INC|LLC|CORP|CORPORATION|CO|COMPANY|LTD|LP|PA|PLLC|PC|DBA)\b', '', norm).strip()
        stripped = re.sub(r'\s+', ' ', stripped).strip()
        for dol_name, addr in dol_addresses.items():
            dol_stripped = re.sub(r'\b(INC|LLC|CORP|CORPORATION|CO|COMPANY|LTD|LP|PA|PLLC|PC|DBA)\b', '', dol_name).strip()
            dol_stripped = re.sub(r'\s+', ' ', dol_stripped).strip()
            if stripped and dol_stripped and stripped == dol_stripped:
                matched[cuid] = addr
                break
        else:
            unmatched.append(row)

    print(f"  Exact/suffix match: {len(matched):,}")
    print(f"  Unmatched:          {len(unmatched):,}")

    # ── Also try matching CLAY companies (bonus) ──
    print(f"\n{'='*60}")
    print("Matching CLAY companies (bonus)...")
    print(f"{'='*60}")

    clay_matched = {}
    for cuid, row in clay.items():
        name = row.get('company_name', '').strip()
        norm = normalize(name)

        if norm in dol_addresses:
            clay_matched[cuid] = dol_addresses[norm]
            continue

        stripped = re.sub(r'\b(INC|LLC|CORP|CORPORATION|CO|COMPANY|LTD|LP|PA|PLLC|PC|DBA)\b', '', norm).strip()
        stripped = re.sub(r'\s+', ' ', stripped).strip()
        for dol_name, addr in dol_addresses.items():
            dol_stripped = re.sub(r'\b(INC|LLC|CORP|CORPORATION|CO|COMPANY|LTD|LP|PA|PLLC|PC|DBA)\b', '', dol_name).strip()
            dol_stripped = re.sub(r'\s+', ' ', dol_stripped).strip()
            if stripped and dol_stripped and stripped == dol_stripped:
                clay_matched[cuid] = addr
                break

    print(f"  Clay matched: {len(clay_matched):,}")

    # ── Combine all matches ──
    all_matched = {}
    all_matched.update(matched)
    all_matched.update(clay_matched)

    # ── Write output CSV ──
    print(f"\n{'='*60}")
    print("Writing output CSV...")
    print(f"{'='*60}")

    os.makedirs('exports', exist_ok=True)
    fieldnames = list(rows[0].keys()) + ['ein', 'address1', 'address2', 'city', 'state', 'zip', 'address_source']

    with open(CSV_OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        addressed = 0
        for row in rows:
            cuid = row['company_unique_id'].strip()
            out = dict(row)
            if cuid in all_matched:
                addr = all_matched[cuid]
                out['ein'] = addr.get('ein', '')
                out['address1'] = addr.get('addr1', '')
                out['address2'] = addr.get('addr2', '')
                out['city'] = addr.get('city', '')
                out['state'] = addr.get('state', '')
                out['zip'] = addr.get('zip', '')
                out['address_source'] = f"DOL_{addr.get('source', '')}"
                addressed += 1
            else:
                out['ein'] = ''
                out['address1'] = ''
                out['address2'] = ''
                out['city'] = ''
                out['state'] = ''
                out['zip'] = ''
                out['address_source'] = ''
            w.writerow(out)

    print(f"  Output: {CSV_OUT}")
    print(f"  Total rows: {len(rows):,}")
    print(f"  With addresses: {addressed:,}")
    print(f"  Without addresses: {len(rows) - addressed:,}")

    # ── Final summary ──
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  HUNTER_DOL matched:  {len(matched):>5,} / {len(hunter_dol):,}")
    print(f"  CLAY matched:        {len(clay_matched):>5,} / {len(clay):,}")
    print(f"  TOTAL addressed:     {addressed:>5,} / {len(rows):,} ({100*addressed/len(rows):.1f}%)")
    print(f"  TOTAL gap:           {len(rows)-addressed:>5,}")

    # Sample matched
    print(f"\nSample matched (first 15):")
    for cuid in list(all_matched.keys())[:15]:
        addr = all_matched[cuid]
        name = all_companies[cuid]['company_name']
        print(f"  {name[:42]:<44s} {addr['city'] or '':<18s} {addr['state'] or '':<4s} {addr['zip'] or ''}")

    # Sample unmatched HUNTER_DOL
    print(f"\nSample unmatched HUNTER_DOL (first 15):")
    for row in unmatched[:15]:
        print(f"  {row['company_name'][:55]}")

    conn.close()


if __name__ == '__main__':
    main()
