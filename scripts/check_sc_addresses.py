"""Check what address data is available for SC companies export."""
import os, sys, io, csv
from collections import Counter

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import psycopg2

with open(r'C:\Users\CUSTOM PC\Desktop\sc_companies_export.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

cuids = [r['company_unique_id'].strip() for r in rows if r.get('company_unique_id','').strip()]
print(f"CSV companies: {len(cuids)}")

sources = Counter(r.get('source_system','') for r in rows)
for s, c in sources.most_common():
    print(f"  {s}: {c}")

conn = psycopg2.connect(
    host=os.environ['NEON_HOST'],
    dbname=os.environ['NEON_DATABASE'],
    user=os.environ['NEON_USER'],
    password=os.environ['NEON_PASSWORD'],
    sslmode='require',
)
cur = conn.cursor()

# Get CL data (domain, state_code)
cur.execute("""
    SELECT company_unique_id::text, company_name, company_domain, state_code
    FROM cl.company_identity
    WHERE company_unique_id = ANY(%s::uuid[])
""", (cuids,))
cl_data = {r[0]: {'name': r[1], 'domain': r[2], 'state': r[3]} for r in cur.fetchall()}
print(f"\nFound in CL: {len(cl_data)}")
has_domain = sum(1 for v in cl_data.values() if v['domain'])
print(f"  With domain: {has_domain}")
print(f"  Without domain: {len(cl_data) - has_domain}")

# Bridge: domain -> EIN via dol.ein_urls
domains = [v['domain'].lower() for v in cl_data.values() if v['domain']]
print(f"\nDomains to look up in dol.ein_urls: {len(domains)}")

if domains:
    cur.execute("""
        SELECT LOWER(domain), ein
        FROM dol.ein_urls
        WHERE LOWER(domain) = ANY(%s)
    """, (domains,))
    domain_ein = {}
    for r in cur.fetchall():
        domain_ein[r[0]] = r[1]
    print(f"  Domains with EIN: {len(domain_ein)}")

    # Get addresses from form_5500
    eins = list(set(domain_ein.values()))
    print(f"  Unique EINs: {len(eins)}")

    cur.execute("""
        SELECT DISTINCT ON (sponsor_dfe_ein)
               sponsor_dfe_ein,
               TRIM(spons_dfe_mail_us_city) as city,
               TRIM(spons_dfe_mail_us_state) as state,
               LEFT(TRIM(spons_dfe_mail_us_zip), 5) as zip
        FROM dol.form_5500
        WHERE sponsor_dfe_ein = ANY(%s)
          AND spons_dfe_mail_us_zip IS NOT NULL AND spons_dfe_mail_us_zip <> ''
        ORDER BY sponsor_dfe_ein, ack_id DESC
    """, (eins,))
    f5500 = {r[0]: {'city': r[1], 'state': r[2], 'zip': r[3]} for r in cur.fetchall()}

    cur.execute("""
        SELECT DISTINCT ON (sf_spons_ein)
               sf_spons_ein,
               TRIM(sf_spons_us_city) as city,
               TRIM(sf_spons_us_state) as state,
               LEFT(TRIM(sf_spons_us_zip), 5) as zip
        FROM dol.form_5500_sf
        WHERE sf_spons_ein = ANY(%s)
          AND sf_spons_us_zip IS NOT NULL AND sf_spons_us_zip <> ''
        ORDER BY sf_spons_ein, ack_id DESC
    """, (eins,))
    f5500sf = {r[0]: {'city': r[1], 'state': r[2], 'zip': r[3]} for r in cur.fetchall()}

    all_dol_addr = {}
    for ein in eins:
        if ein in f5500:
            all_dol_addr[ein] = f5500[ein]
        elif ein in f5500sf:
            all_dol_addr[ein] = f5500sf[ein]

    print(f"\n  form_5500 addresses: {len(f5500)}")
    print(f"  form_5500_sf addresses: {len(f5500sf)}")
    print(f"  Total EINs with addresses: {len(all_dol_addr)}")
else:
    domain_ein = {}
    all_dol_addr = {}

# Also try: companies without domain but name match against DOL
# For HUNTER_DOL_SS003, try name matching
no_domain_hunter = [r for r in rows if r.get('source_system') == 'HUNTER_DOL_SS003'
                    and r['company_unique_id'] in cl_data
                    and not cl_data[r['company_unique_id']].get('domain')]
print(f"\nHUNTER_DOL companies without domain: {len(no_domain_hunter)}")

# Summary: how many can we address?
addressable_via_dol = 0
addressable_companies = {}
for r in rows:
    cuid = r['company_unique_id'].strip()
    if cuid not in cl_data:
        continue
    domain = (cl_data[cuid].get('domain') or '').lower()
    if domain and domain in domain_ein:
        ein = domain_ein[domain]
        if ein in all_dol_addr:
            addr = all_dol_addr[ein]
            addressable_companies[cuid] = addr
            addressable_via_dol += 1

print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
print(f"  Total companies:              {len(cuids):,}")
print(f"  Found in CL:                  {len(cl_data):,}")
print(f"  Have domain in CL:            {has_domain:,}")
print(f"  Domain -> EIN bridge:         {len(domain_ein):,}")
print(f"  EIN -> DOL address:           {len(all_dol_addr):,}")
print(f"  Addressable via DOL:          {addressable_via_dol:,}")
print(f"  NOT addressable (no domain):  {len(cuids) - has_domain:,}")
print(f"  NOT addressable (no EIN):     {has_domain - len(domain_ein):,}")
print(f"  NOT addressable (no addr):    {len(domain_ein) - addressable_via_dol:,}")
print(f"  TOTAL GAP:                    {len(cuids) - addressable_via_dol:,}")

# Sample addresses
print(f"\n{'='*60}")
print("SAMPLE: Companies WITH DOL addresses")
print(f"{'='*60}")
shown = 0
for cuid, addr in list(addressable_companies.items())[:15]:
    name = cl_data[cuid]['name']
    print(f"  {name[:42]:<44s} {addr['city'] or '':<20s} {addr['state'] or '':<4s} {addr['zip'] or ''}")

conn.close()
