import os, csv, psycopg2
from collections import Counter

# Load CSV company_unique_ids
with open(r'C:\Users\CUSTOM PC\Desktop\sc_companies_export.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

cuids = [r['company_unique_id'].strip() for r in rows if r.get('company_unique_id','').strip()]
print(f"CSV companies: {len(cuids)}")

# Count by source
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

# Check how many exist in CL
cur.execute("""
    SELECT company_unique_id::text, company_name, company_domain, ein
    FROM cl.company_identity
    WHERE company_unique_id = ANY(%s::uuid[])
""", (cuids,))
cl_data = {r[0]: {'name': r[1], 'domain': r[2], 'ein': r[3]} for r in cur.fetchall()}
print(f"\nFound in CL: {len(cl_data)}")
has_ein = sum(1 for v in cl_data.values() if v['ein'])
print(f"  With EIN: {has_ein}")

# For those with EINs, check DOL addresses
eins = [v['ein'] for v in cl_data.values() if v['ein']]
if eins:
    # form_5500
    cur.execute("""
        SELECT DISTINCT sponsor_dfe_ein, 
               spons_dfe_mail_us_city, spons_dfe_mail_us_state, 
               LEFT(spons_dfe_mail_us_zip, 5) as zip
        FROM dol.form_5500
        WHERE sponsor_dfe_ein = ANY(%s)
          AND spons_dfe_mail_us_zip IS NOT NULL
          AND spons_dfe_mail_us_zip <> ''
    """, (eins,))
    f5500_addr = {}
    for r in cur.fetchall():
        f5500_addr[r[0]] = {'city': r[1], 'state': r[2], 'zip': r[3]}
    
    # form_5500_sf
    cur.execute("""
        SELECT DISTINCT sf_spons_ein, 
               sf_spons_us_city, sf_spons_us_state,
               LEFT(sf_spons_us_zip, 5) as zip
        FROM dol.form_5500_sf
        WHERE sf_spons_ein = ANY(%s)
          AND sf_spons_us_zip IS NOT NULL
          AND sf_spons_us_zip <> ''
    """, (eins,))
    f5500sf_addr = {}
    for r in cur.fetchall():
        f5500sf_addr[r[0]] = {'city': r[1], 'state': r[2], 'zip': r[3]}
    
    print(f"\nDOL form_5500 addresses found: {len(f5500_addr)}")
    print(f"DOL form_5500_sf addresses found: {len(f5500sf_addr)}")
    
    # Combine - how many total EINs have addresses from either source?
    all_dol_eins = set(f5500_addr.keys()) | set(f5500sf_addr.keys())
    print(f"Total EINs with DOL addresses: {len(all_dol_eins)}")
    
    # How many of our companies can get addresses?
    addressable = 0
    for cuid in cuids:
        if cuid in cl_data and cl_data[cuid]['ein']:
            ein = cl_data[cuid]['ein']
            if ein in all_dol_eins:
                addressable += 1
    print(f"\nCompanies addressable via DOL: {addressable} of {len(cuids)}")
else:
    print("No EINs found")

# Also check: do any of these have outreach_ids already?
cur.execute("""
    SELECT COUNT(*) FROM cl.company_identity
    WHERE company_unique_id = ANY(%s::uuid[]) AND outreach_id IS NOT NULL
""", (cuids,))
print(f"\nAlready have outreach_id: {cur.fetchone()[0]}")

# Check dol.ein_urls for additional domain->address mapping
if eins:
    cur.execute("""
        SELECT COUNT(DISTINCT ein) FROM dol.ein_urls
        WHERE ein = ANY(%s)
    """, (eins[:5000],))
    print(f"EINs in dol.ein_urls: {cur.fetchone()[0]}")

conn.close()
