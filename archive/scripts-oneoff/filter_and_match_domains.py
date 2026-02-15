#!/usr/bin/env python3
"""
Filter garbage domains and match to outreach records
"""
import csv
import psycopg2
import os
import re

# Known garbage/parked domain patterns
GARBAGE_DOMAINS = [
    'yahoo.com', 'mapquest.com', 'sunbiz.org', 'eindata.com', 'b2bhint.com',
    'bloomberg.com', 'linkedin.com', 'facebook.com', 'google.com', 'yelp.com',
    'dnb.com', 'zoominfo.com', 'bizapedia.com', 'opencorporates.com', 'privco.com',
    'propublica.org', 'dandb.com', 'meetbeagle.com', 'nycompanyregistry.com',
    'domainmarket.com', 'hugedomains.com', 'sedo.com', 'godaddy.com', 'afternic.com',
    'dan.com', 'parked.com', 'parkingcrew.com', 'bodis.com', 'undeveloped.com',
    'wikipedia.org', 'irs.gov', 'sec.gov', 'bbb.org', 'yellowpages.com',
    'whitepages.com', 'manta.com', 'buzzfile.com', 'chamberofcommerce.com',
    'indeed.com', 'glassdoor.com', 'crunchbase.com', 'pitchbook.com',
    'archive.org', 'wayback', 'webcache', 'cached'
]

# Patterns that indicate parked/for-sale domains
PARKED_PATTERNS = [
    r'\.xyz$', r'\.info$', r'\.biz$',  # Suspicious TLDs for businesses
    r'domainmarket', r'hugedomains', r'forsale', r'parked',
    r'buy.*domain', r'domain.*sale'
]

def is_garbage_domain(domain: str) -> tuple:
    """Check if domain is garbage, return (is_garbage, reason)"""
    if not domain:
        return True, "empty"
    
    domain_lower = domain.lower().replace('www.', '')
    
    # Check against known garbage
    for garbage in GARBAGE_DOMAINS:
        if garbage in domain_lower:
            return True, f"known_garbage:{garbage}"
    
    # Check patterns
    for pattern in PARKED_PATTERNS:
        if re.search(pattern, domain_lower):
            return True, f"pattern:{pattern}"
    
    return False, "ok"

def main():
    print("Domain Filtering and Outreach Matching")
    print("=" * 70)
    
    # Load domain results
    with open('scripts/domain_results_ALL.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_results = list(reader)
    
    print(f"Loaded {len(all_results):,} domain results")
    
    # Filter
    valid = []
    garbage = []
    not_found = []
    
    for r in all_results:
        if r.get('found') != 'True':
            not_found.append(r)
            continue
        
        domain = r.get('domain', '')
        is_bad, reason = is_garbage_domain(domain)
        
        if is_bad:
            r['filter_reason'] = reason
            garbage.append(r)
        else:
            valid.append(r)
    
    print(f"  Valid domains: {len(valid):,}")
    print(f"  Garbage filtered: {len(garbage):,}")
    print(f"  Not found: {len(not_found):,}")
    print()
    
    # Show garbage breakdown
    garbage_reasons = {}
    for r in garbage:
        reason = r.get('filter_reason', 'unknown')
        garbage_reasons[reason] = garbage_reasons.get(reason, 0) + 1
    
    print("Garbage breakdown:")
    for reason, count in sorted(garbage_reasons.items(), key=lambda x: -x[1])[:15]:
        print(f"  {reason}: {count}")
    print()
    
    # Connect to database and match to outreach
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Check outreach.blog structure
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'outreach' AND table_name = 'blog'
        ORDER BY ordinal_position
    """)
    blog_cols = [r[0] for r in cur.fetchall()]
    print(f"outreach.blog columns: {blog_cols}")
    print()
    
    # Get EINs from valid results
    valid_eins = {r['ein'] for r in valid if r.get('ein')}
    print(f"Valid EINs to match: {len(valid_eins):,}")
    
    # Check how many EINs exist in company_master
    cur.execute("""
        SELECT ein, company_unique_id 
        FROM company.company_master 
        WHERE ein = ANY(%s)
    """, (list(valid_eins),))
    ein_to_company = {r[0]: r[1] for r in cur.fetchall()}
    print(f"EINs found in company_master: {len(ein_to_company):,}")
    
    # Check how many have outreach_id via cl.company_identity
    if ein_to_company:
        company_ids = list(ein_to_company.values())
        cur.execute("""
            SELECT company_unique_id, outreach_id, sovereign_company_id
            FROM cl.company_identity
            WHERE company_unique_id = ANY(%s)
            AND outreach_id IS NOT NULL
        """, (company_ids,))
        company_to_outreach = {str(r[0]): {'outreach_id': r[1], 'sid': r[2]} for r in cur.fetchall()}
        print(f"Companies with outreach_id: {len(company_to_outreach):,}")
    else:
        company_to_outreach = {}
    
    # Build update mapping: EIN → domain → outreach_id
    updates = []
    for r in valid:
        ein = r.get('ein')
        if ein not in ein_to_company:
            continue
        
        company_id = str(ein_to_company[ein])
        if company_id not in company_to_outreach:
            continue
        
        outreach_info = company_to_outreach[company_id]
        updates.append({
            'ein': ein,
            'company_name': r['company_name'],
            'domain': r['domain'],
            'url': r.get('url', ''),
            'outreach_id': outreach_info['outreach_id'],
            'sovereign_company_id': outreach_info['sid']
        })
    
    print(f"Updates to apply (EIN → outreach): {len(updates):,}")
    print()
    
    # Save filtered results
    with open('scripts/domain_results_VALID.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ein', 'company_name', 'city', 'state', 'domain', 'url'])
        for r in valid:
            writer.writerow([r['ein'], r['company_name'], r['city'], r['state'], r['domain'], r.get('url', '')])
    print(f"Saved {len(valid):,} valid domains to scripts/domain_results_VALID.csv")
    
    # Save updates for outreach
    with open('scripts/outreach_url_updates.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ein', 'company_name', 'domain', 'url', 'outreach_id', 'sovereign_company_id'])
        for u in updates:
            writer.writerow([u['ein'], u['company_name'], u['domain'], u['url'], u['outreach_id'], u['sovereign_company_id']])
    print(f"Saved {len(updates):,} outreach updates to scripts/outreach_url_updates.csv")
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total DOL records:      {len(all_results):,}")
    print(f"Domains found:          {len(valid) + len(garbage):,}")
    print(f"  - Valid after filter: {len(valid):,}")
    print(f"  - Garbage filtered:   {len(garbage):,}")
    print(f"Not found:              {len(not_found):,}")
    print()
    print(f"Matchable to outreach:  {len(updates):,}")
    print(f"New companies (no EIN): {len(valid) - len(updates):,}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
