"""Maryland companies and slot breakdown."""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print('=== MARYLAND BREAKDOWN ===')
print()

# Check DOL for Maryland companies
cur.execute("""
    SELECT COUNT(DISTINCT sponsor_dfe_ein) 
    FROM dol.form_5500 
    WHERE spons_dfe_mail_us_state = 'MD'
""")
dol_md = cur.fetchone()[0]
print(f'DOL Form 5500 - Maryland companies (unique EINs): {dol_md:,}')

# Check outreach.dol linked to Maryland
cur.execute("""
    SELECT COUNT(DISTINCT od.ein)
    FROM outreach.dol od
    JOIN dol.form_5500 f ON od.ein = f.sponsor_dfe_ein
    WHERE f.spons_dfe_mail_us_state = 'MD'
""")
outreach_dol_md = cur.fetchone()[0]
print(f'outreach.dol - Maryland EINs: {outreach_dol_md:,}')

# Get slot breakdown for all companies first
cur.execute("""
    SELECT 
        slot_type,
        COUNT(*) as total_slots,
        COUNT(CASE WHEN is_filled = TRUE THEN 1 END) as filled
    FROM people.company_slot
    GROUP BY slot_type
    ORDER BY slot_type
""")
print('\n=== OVERALL SLOT COVERAGE (ALL STATES) ===')
print(f'{"Slot Type":<10} {"Total":>10} {"Filled":>10} {"Fill Rate":>10}')
print('-' * 45)
for row in cur.fetchall():
    slot_type, total, filled = row
    rate = (filled / total * 100) if total > 0 else 0
    print(f'{slot_type:<10} {total:>10,} {filled:>10,} {rate:>9.1f}%')

# Find Maryland companies via EIN linkage
cur.execute("""
    SELECT COUNT(DISTINCT cs.outreach_id)
    FROM people.company_slot cs
    JOIN outreach.dol od ON cs.outreach_id = od.outreach_id
    JOIN dol.form_5500 f ON od.ein = f.sponsor_dfe_ein
    WHERE f.spons_dfe_mail_us_state = 'MD'
""")
md_companies = cur.fetchone()[0]
print(f'\n=== MARYLAND COMPANIES ===')
print(f'Maryland companies in slot system: {md_companies:,}')

# Get Maryland slot breakdown
cur.execute("""
    SELECT 
        cs.slot_type,
        COUNT(*) as total_slots,
        COUNT(CASE WHEN cs.is_filled = TRUE THEN 1 END) as filled
    FROM people.company_slot cs
    JOIN outreach.dol od ON cs.outreach_id = od.outreach_id
    JOIN dol.form_5500 f ON od.ein = f.sponsor_dfe_ein
    WHERE f.spons_dfe_mail_us_state = 'MD'
    GROUP BY cs.slot_type
    ORDER BY cs.slot_type
""")
print(f'\n{"Slot Type":<10} {"Total":>10} {"Filled":>10} {"Fill Rate":>10}')
print('-' * 45)
for row in cur.fetchall():
    slot_type, total, filled = row
    rate = (filled / total * 100) if total > 0 else 0
    print(f'{slot_type:<10} {total:>10,} {filled:>10,} {rate:>9.1f}%')

# Check how many Maryland companies have all 3 slots filled
cur.execute("""
    WITH md_slots AS (
        SELECT 
            cs.outreach_id,
            COUNT(CASE WHEN cs.slot_type = 'ceo' AND cs.is_filled = TRUE THEN 1 END) as has_ceo,
            COUNT(CASE WHEN cs.slot_type = 'cfo' AND cs.is_filled = TRUE THEN 1 END) as has_cfo,
            COUNT(CASE WHEN cs.slot_type = 'hr' AND cs.is_filled = TRUE THEN 1 END) as has_hr
        FROM people.company_slot cs
        JOIN outreach.dol od ON cs.outreach_id = od.outreach_id
        JOIN dol.form_5500 f ON od.ein = f.sponsor_dfe_ein
        WHERE f.spons_dfe_mail_us_state = 'MD'
        GROUP BY cs.outreach_id
    )
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN has_ceo > 0 THEN 1 END) as with_ceo,
        COUNT(CASE WHEN has_cfo > 0 THEN 1 END) as with_cfo,
        COUNT(CASE WHEN has_hr > 0 THEN 1 END) as with_hr,
        COUNT(CASE WHEN has_ceo > 0 AND has_cfo > 0 AND has_hr > 0 THEN 1 END) as all_three
    FROM md_slots
""")
row = cur.fetchone()
print(f'\n=== MARYLAND COMPANY COVERAGE ===')
print(f'Total MD companies with slots: {row[0]:,}')
print(f'  With CEO: {row[1]:,}')
print(f'  With CFO: {row[2]:,}')
print(f'  With HR:  {row[3]:,}')
print(f'  All 3 filled: {row[4]:,}')

conn.close()
