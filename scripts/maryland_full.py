"""Full Maryland breakdown using all data sources."""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print('=== FULL MARYLAND BREAKDOWN ===')
print()

# 1. DOL sources
cur.execute("SELECT COUNT(DISTINCT sponsor_dfe_ein) FROM dol.form_5500 WHERE spons_dfe_mail_us_state = 'MD'")
print(f'DOL form_5500 Maryland EINs: {cur.fetchone()[0]:,}')

cur.execute("SELECT COUNT(*) FROM dol.form_5500_sf WHERE sf_spons_us_state = 'MD'")
print(f'DOL form_5500_sf Maryland filings: {cur.fetchone()[0]:,}')

# 2. Hunter company with state = MD
cur.execute("SELECT COUNT(*) FROM enrichment.hunter_company WHERE state = 'MD'")
hunter_co_md = cur.fetchone()[0]
print(f'\nHunter companies in MD: {hunter_co_md:,}')

# 3. Hunter contacts for MD companies
cur.execute("""
    SELECT COUNT(*) 
    FROM enrichment.hunter_contact hc
    JOIN enrichment.hunter_company hco ON hc.domain = hco.domain
    WHERE hco.state = 'MD'
""")
hunter_contacts_md = cur.fetchone()[0]
print(f'Hunter contacts for MD companies: {hunter_contacts_md:,}')

# 4. Outreach companies in MD (via hunter_company)
cur.execute("""
    SELECT COUNT(DISTINCT o.outreach_id)
    FROM outreach.outreach o
    JOIN enrichment.hunter_company hc ON o.domain = hc.domain
    WHERE hc.state = 'MD'
""")
outreach_md = cur.fetchone()[0]
print(f'\nOutreach companies in MD (via Hunter): {outreach_md:,}')

# 5. Slots for MD companies
cur.execute("""
    SELECT 
        cs.slot_type,
        COUNT(*) as total,
        COUNT(CASE WHEN cs.is_filled = TRUE THEN 1 END) as filled
    FROM people.company_slot cs
    JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
    JOIN enrichment.hunter_company hc ON o.domain = hc.domain
    WHERE hc.state = 'MD'
    GROUP BY cs.slot_type
    ORDER BY cs.slot_type
""")
print('\n=== MARYLAND SLOT COVERAGE (via Hunter state) ===')
print(f'{"Slot":<6} {"Total":>8} {"Filled":>8} {"Rate":>8}')
print('-' * 35)
total_slots = 0
total_filled = 0
for row in cur.fetchall():
    slot, tot, filled = row
    rate = filled/tot*100 if tot else 0
    print(f'{slot:<6} {tot:>8,} {filled:>8,} {rate:>7.1f}%')
    total_slots += tot
    total_filled += filled

print(f'\nTotal MD slots: {total_slots:,}')
print(f'Total filled: {total_filled:,}')

# 6. Unique MD companies with slots
cur.execute("""
    SELECT COUNT(DISTINCT cs.outreach_id)
    FROM people.company_slot cs
    JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
    JOIN enrichment.hunter_company hc ON o.domain = hc.domain
    WHERE hc.state = 'MD'
""")
print(f'\nUnique MD companies with slots: {cur.fetchone()[0]:,}')

# 7. Check what states have the most data
print('\n=== TOP STATES IN HUNTER_COMPANY ===')
cur.execute("""
    SELECT state, COUNT(*) as cnt
    FROM enrichment.hunter_company
    WHERE state IS NOT NULL AND state != ''
    GROUP BY state
    ORDER BY cnt DESC
    LIMIT 20
""")
print(f'{"State":<6} {"Count":>10}')
print('-' * 20)
for row in cur.fetchall():
    print(f'{row[0]:<6} {row[1]:>10,}')

conn.close()
