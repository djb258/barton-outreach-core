"""Maryland slots based on DOL EINs."""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print('=== MARYLAND SLOTS - BASED ON DOL EINs ===')
print()

# Total Maryland EINs from DOL
cur.execute("""
    SELECT COUNT(DISTINCT ein) FROM (
        SELECT sponsor_dfe_ein as ein FROM dol.form_5500 WHERE spons_dfe_mail_us_state = 'MD'
        UNION
        SELECT sf_spons_ein as ein FROM dol.form_5500_sf WHERE sf_spons_us_state = 'MD'
    ) combined
    WHERE ein IS NOT NULL
""")
total_md_eins = cur.fetchone()[0]
print(f'Total Maryland EINs from DOL: {total_md_eins:,}')

# How many of these have entries in outreach.dol
cur.execute("""
    WITH md_eins AS (
        SELECT sponsor_dfe_ein as ein FROM dol.form_5500 WHERE spons_dfe_mail_us_state = 'MD'
        UNION
        SELECT sf_spons_ein as ein FROM dol.form_5500_sf WHERE sf_spons_us_state = 'MD'
    )
    SELECT COUNT(DISTINCT od.ein)
    FROM outreach.dol od
    WHERE od.ein IN (SELECT ein FROM md_eins WHERE ein IS NOT NULL)
""")
md_in_outreach_dol = cur.fetchone()[0]
print(f'Maryland EINs in outreach.dol: {md_in_outreach_dol:,}')

# Get Maryland slots via outreach.dol
cur.execute("""
    WITH md_eins AS (
        SELECT sponsor_dfe_ein as ein FROM dol.form_5500 WHERE spons_dfe_mail_us_state = 'MD'
        UNION
        SELECT sf_spons_ein as ein FROM dol.form_5500_sf WHERE sf_spons_us_state = 'MD'
    )
    SELECT 
        cs.slot_type,
        COUNT(*) as total,
        COUNT(CASE WHEN cs.is_filled = TRUE THEN 1 END) as filled
    FROM people.company_slot cs
    JOIN outreach.dol od ON cs.outreach_id = od.outreach_id
    WHERE od.ein IN (SELECT ein FROM md_eins WHERE ein IS NOT NULL)
    GROUP BY cs.slot_type
    ORDER BY cs.slot_type
""")
print('\n=== MARYLAND SLOTS (via outreach.dol EIN) ===')
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

# How many unique MD companies have slots
cur.execute("""
    WITH md_eins AS (
        SELECT sponsor_dfe_ein as ein FROM dol.form_5500 WHERE spons_dfe_mail_us_state = 'MD'
        UNION
        SELECT sf_spons_ein as ein FROM dol.form_5500_sf WHERE sf_spons_us_state = 'MD'
    )
    SELECT COUNT(DISTINCT cs.outreach_id)
    FROM people.company_slot cs
    JOIN outreach.dol od ON cs.outreach_id = od.outreach_id
    WHERE od.ein IN (SELECT ein FROM md_eins WHERE ein IS NOT NULL)
""")
md_companies_with_slots = cur.fetchone()[0]
print(f'\nMD companies with slots: {md_companies_with_slots:,}')
print(f'MD companies in DOL (total): {total_md_eins:,}')
if total_md_eins > 0:
    print(f'Coverage: {md_companies_with_slots/total_md_eins*100:.1f}%')

conn.close()
