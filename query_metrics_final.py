import psycopg2
import os
from datetime import datetime, timezone

conn = psycopg2.connect(
    host=os.getenv('NEON_HOST'),
    database=os.getenv('NEON_DATABASE'),
    user=os.getenv('NEON_USER'),
    password=os.getenv('NEON_PASSWORD'),
    sslmode='require'
)
cur = conn.cursor()

print('=' * 80)
print('NEON DATABASE METRICS SNAPSHOT')
print(f'Timestamp: {datetime.now(timezone.utc).isoformat()}')
print('=' * 80)
print()

print('1. PEOPLE VALIDATION STATUS')
print('-' * 80)
cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE validation_status = 'invalid'), COUNT(*) FILTER (WHERE validation_status = 'valid'), COUNT(*) FILTER (WHERE validation_status IS NULL) FROM people.people_master")
stats = cur.fetchone()
print(f'Total people: {stats[0]:,}')
print(f'Invalid: {stats[1]:,}')
print(f'Valid: {stats[2]:,}')
print(f'NULL: {stats[3]:,}')
print()

print('2. BLOG RECORDS NEEDING URLs')
print('-' * 80)
cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE about_url IS NULL OR about_url = ''), COUNT(*) FILTER (WHERE news_url IS NULL OR news_url = ''), COUNT(*) FILTER (WHERE (about_url IS NULL OR about_url = '') AND (news_url IS NULL OR news_url = '')) FROM outreach.blog")
stats = cur.fetchone()
print(f'Total blog records: {stats[0]:,}')
print(f'Missing about_url: {stats[1]:,}')
print(f'Missing news_url: {stats[2]:,}')
print(f'Missing BOTH: {stats[3]:,}')
print()

print('3. DOL ENRICHMENT STATUS')
print('-' * 80)
cur.execute('SELECT (SELECT COUNT(*) FROM outreach.outreach), COUNT(*), ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM outreach.outreach) * 100, 2) FROM outreach.dol')
stats = cur.fetchone()
print(f'Total companies (spine): {stats[0]:,}')
print(f'With DOL data: {stats[1]:,}')
print(f'Coverage: {stats[2]}%')
print()

print('4. MISSING LINKEDIN URLs')
print('-' * 80)
cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE linkedin_url IS NULL OR linkedin_url = ''), ROUND(COUNT(*) FILTER (WHERE linkedin_url IS NULL OR linkedin_url = '')::numeric / COUNT(*) * 100, 2) FROM people.people_master WHERE validation_status != 'invalid' OR validation_status IS NULL")
stats = cur.fetchone()
print(f'Valid/unknown people: {stats[0]:,}')
print(f'Missing LinkedIn: {stats[1]:,}')
print(f'Percentage: {stats[2]}%')
print()

print('5. COMPANIES NEEDING CONTACTS')
print('-' * 80)
cur.execute('SELECT COUNT(DISTINCT ct.outreach_id), COUNT(DISTINCT ct.outreach_id) FILTER (WHERE NOT EXISTS (SELECT 1 FROM outreach.people p WHERE p.outreach_id = ct.outreach_id)) FROM outreach.company_target ct WHERE ct.email_method IS NOT NULL')
stats = cur.fetchone()
print(f'Companies with email_method: {stats[0]:,}')
print(f'Without people records: {stats[1]:,}')
print()

print('6. HUNTER CONTACT PROMOTION STATUS')
print('-' * 80)
cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE slot_type IS NULL OR slot_type = ''), COUNT(*) FILTER (WHERE slot_type IS NOT NULL AND slot_type != '') FROM outreach.people WHERE source = 'hunter.io'")
stats = cur.fetchone()
print(f'Total Hunter contacts: {stats[0]:,}')
print(f'Pending slot assignment: {stats[1]:,}')
print(f'Assigned to slot: {stats[2]:,}')
print()

print('7. COMPANIES WITH NO HUNTER DATA')
print('-' * 80)
cur.execute("SELECT COUNT(DISTINCT ct.outreach_id), COUNT(DISTINCT ct.outreach_id) FILTER (WHERE NOT EXISTS (SELECT 1 FROM outreach.people p WHERE p.outreach_id = ct.outreach_id AND p.source = 'hunter.io')) FROM outreach.company_target ct WHERE ct.email_method IS NOT NULL")
stats = cur.fetchone()
print(f'Companies with email_method: {stats[0]:,}')
print(f'Without Hunter data: {stats[1]:,}')
print()

print('8. SLOT FILL RATES (CEO, CFO, HR)')
print('-' * 80)
cur.execute("SELECT COUNT(DISTINCT o.outreach_id), COUNT(DISTINCT CASE WHEN cs_ceo.slot_id IS NOT NULL THEN o.outreach_id END), COUNT(DISTINCT CASE WHEN cs_cfo.slot_id IS NOT NULL THEN o.outreach_id END), COUNT(DISTINCT CASE WHEN cs_hr.slot_id IS NOT NULL THEN o.outreach_id END) FROM outreach.outreach o LEFT JOIN people.company_slot cs_ceo ON o.outreach_id = cs_ceo.outreach_id AND cs_ceo.slot_type = 'CEO' LEFT JOIN people.company_slot cs_cfo ON o.outreach_id = cs_cfo.outreach_id AND cs_cfo.slot_type = 'CFO' LEFT JOIN people.company_slot cs_hr ON o.outreach_id = cs_hr.outreach_id AND cs_hr.slot_type = 'HR'")
stats = cur.fetchone()
ceo_pct = (stats[1]/stats[0]*100) if stats[0] > 0 else 0
cfo_pct = (stats[2]/stats[0]*100) if stats[0] > 0 else 0
hr_pct = (stats[3]/stats[0]*100) if stats[0] > 0 else 0
print(f'Total companies: {stats[0]:,}')
print(f'CEO filled: {stats[1]:,} ({ceo_pct:.2f}%)')
print(f'CFO filled: {stats[2]:,} ({cfo_pct:.2f}%)')
print(f'HR filled: {stats[3]:,} ({hr_pct:.2f}%)')
print()

print('9. HUNTER DATA QUALITY BY SLOT')
print('-' * 80)
cur.execute("SELECT COALESCE(slot_type, '(unassigned)'), COUNT(*), COUNT(*) FILTER (WHERE email IS NOT NULL AND email != ''), COUNT(*) FILTER (WHERE linkedin_url IS NOT NULL AND linkedin_url != '') FROM outreach.people WHERE source = 'hunter.io' GROUP BY slot_type ORDER BY CASE slot_type WHEN 'CEO' THEN 1 WHEN 'CFO' THEN 2 WHEN 'HR' THEN 3 WHEN 'CTO' THEN 4 WHEN 'CMO' THEN 5 WHEN 'COO' THEN 6 ELSE 99 END")
rows = cur.fetchall()
if rows:
    for row in rows:
        print(f'{row[0]:15} Total: {row[1]:6,}  |  Email: {row[2]:6,}  |  LinkedIn: {row[3]:6,}')
else:
    print('No Hunter data found in outreach.people')
print()

print('10. OUTREACH.PEOPLE vs COMPANY_SLOT ALIGNMENT')
print('-' * 80)
cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE slot_type IS NOT NULL AND slot_type != ''), COUNT(*) FILTER (WHERE slot_type IS NOT NULL AND slot_type != '' AND NOT EXISTS (SELECT 1 FROM people.company_slot cs WHERE cs.outreach_id = p.outreach_id AND cs.slot_type = p.slot_type AND cs.person_unique_id = p.person_id)) FROM outreach.people p")
stats = cur.fetchone()
print(f'Total outreach.people: {stats[0]:,}')
print(f'With slot_type: {stats[1]:,}')
print(f'NOT in company_slot: {stats[2]:,}')
print()

print('11. ADDITIONAL DIAGNOSTICS')
print('-' * 80)
cur.execute("SELECT COUNT(*) FROM people.company_slot")
slot_count = cur.fetchone()[0]
print(f'Total company_slot records: {slot_count:,}')

cur.execute("SELECT COUNT(DISTINCT outreach_id) FROM people.company_slot")
companies_with_slots = cur.fetchone()[0]
print(f'Companies with at least one slot: {companies_with_slots:,}')

cur.execute("SELECT COUNT(*), source FROM outreach.people GROUP BY source ORDER BY COUNT(*) DESC")
sources = cur.fetchall()
print('People by source:')
for src in sources:
    print(f'  {src[1] if src[1] else "(none)"}: {src[0]:,}')
print()

cur.close()
conn.close()
print('=' * 80)
print('METRICS SNAPSHOT COMPLETE')
print('=' * 80)
