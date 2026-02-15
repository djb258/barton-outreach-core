"""
Data State Overview Report
Generated: 2026-02-07
"""
import psycopg2
import os
from psycopg2.extras import RealDictCursor

# Connect to Neon
conn = psycopg2.connect(
    host=os.getenv('NEON_HOST'),
    database=os.getenv('NEON_DATABASE'),
    user=os.getenv('NEON_USER'),
    password=os.getenv('NEON_PASSWORD'),
    sslmode='require'
)

cur = conn.cursor(cursor_factory=RealDictCursor)

print('=' * 80)
print('BARTON OUTREACH CORE - DATA STATE OVERVIEW')
print('Generated: 2026-02-07')
print('=' * 80)

# 1. OUTREACH SPINE
print('\n1. OUTREACH SPINE (outreach.outreach)')
print('-' * 80)
cur.execute('''
    SELECT
        COUNT(*) as total_records,
        COUNT(CASE WHEN domain IS NOT NULL THEN 1 END) as with_domain,
        COUNT(CASE WHEN ein IS NOT NULL THEN 1 END) as with_ein,
        COUNT(CASE WHEN has_appointment = TRUE THEN 1 END) as with_appointment
    FROM outreach.outreach
''')
spine_summary = cur.fetchone()
print(f"Total Records: {spine_summary['total_records']:,}")
print(f"With Domain: {spine_summary['with_domain']:,}")
print(f"With EIN: {spine_summary['with_ein']:,}")
print(f"With Appointment: {spine_summary['with_appointment']:,}")

# 2. COMPANY TARGET
print('\n\n2. COMPANY TARGET (outreach.company_target)')
print('-' * 80)
cur.execute('''
    SELECT
        COUNT(*) as total_records,
        COUNT(CASE WHEN email_method IS NOT NULL THEN 1 END) as with_email_method,
        COUNT(CASE WHEN email_method IS NULL THEN 1 END) as without_email_method,
        ROUND(100.0 * COUNT(CASE WHEN email_method IS NOT NULL THEN 1 END) / NULLIF(COUNT(*), 0), 1) as email_method_pct
    FROM outreach.company_target
''')
ct_summary = cur.fetchone()
print(f"Total Records: {ct_summary['total_records']:,}")
print(f"With email_method: {ct_summary['with_email_method']:,} ({ct_summary['email_method_pct']}%)")
print(f"Without email_method: {ct_summary['without_email_method']:,}")

cur.execute('''
    SELECT execution_status, COUNT(*) as count
    FROM outreach.company_target
    GROUP BY execution_status
    ORDER BY count DESC
''')
exec_status = cur.fetchall()
if exec_status:
    print("\nBy Execution Status:")
    for row in exec_status:
        print(f"  {row['execution_status'] or 'NULL'}: {row['count']:,}")

# 3. DOL
print('\n\n3. DOL FILINGS (outreach.dol)')
print('-' * 80)
cur.execute('''
    SELECT
        COUNT(*) as total_records,
        COUNT(CASE WHEN filing_present = TRUE THEN 1 END) as with_ein,
        COUNT(CASE WHEN filing_present IS NULL OR filing_present = FALSE THEN 1 END) as without_ein,
        ROUND(100.0 * COUNT(CASE WHEN filing_present = TRUE THEN 1 END) / NULLIF(COUNT(*), 0), 1) as ein_match_pct
    FROM outreach.dol
''')
dol_summary = cur.fetchone()
print(f"Total Records: {dol_summary['total_records']:,}")
print(f"With EIN Matched (filing_present = TRUE): {dol_summary['with_ein']:,} ({dol_summary['ein_match_pct']}%)")
print(f"Without EIN: {dol_summary['without_ein']:,}")

# 4. BLOG
print('\n\n4. BLOG CONTENT (outreach.blog)')
print('-' * 80)
cur.execute('''
    SELECT
        COUNT(*) as total_records,
        COUNT(CASE WHEN context_summary IS NOT NULL AND context_summary != '' THEN 1 END) as with_content,
        COUNT(CASE WHEN context_summary IS NULL OR context_summary = '' THEN 1 END) as without_content,
        ROUND(100.0 * COUNT(CASE WHEN context_summary IS NOT NULL AND context_summary != '' THEN 1 END) / NULLIF(COUNT(*), 0), 1) as content_pct
    FROM outreach.blog
''')
blog_summary = cur.fetchone()
print(f"Total Records: {blog_summary['total_records']:,}")
print(f"With context_summary: {blog_summary['with_content']:,} ({blog_summary['content_pct']}%)")
print(f"Without context_summary: {blog_summary['without_content']:,}")

# 5. COMPANY SLOTS
print('\n\n5. PEOPLE SLOTS (people.company_slot)')
print('-' * 80)
cur.execute('''
    SELECT
        COUNT(*) as total_slots,
        COUNT(CASE WHEN is_filled = TRUE THEN 1 END) as filled_slots,
        COUNT(CASE WHEN is_filled = FALSE OR is_filled IS NULL THEN 1 END) as unfilled_slots,
        ROUND(100.0 * COUNT(CASE WHEN is_filled = TRUE THEN 1 END) / NULLIF(COUNT(*), 0), 1) as fill_rate
    FROM people.company_slot
''')
slot_summary = cur.fetchone()
print(f"Total Slots: {slot_summary['total_slots']:,}")
print(f"Filled Slots: {slot_summary['filled_slots']:,} ({slot_summary['fill_rate']}%)")
print(f"Unfilled Slots: {slot_summary['unfilled_slots']:,}")

cur.execute('''
    SELECT
        slot_type,
        COUNT(*) as total,
        COUNT(CASE WHEN is_filled = TRUE THEN 1 END) as filled,
        COUNT(CASE WHEN is_filled = FALSE OR is_filled IS NULL THEN 1 END) as unfilled,
        ROUND(100.0 * COUNT(CASE WHEN is_filled = TRUE THEN 1 END) / NULLIF(COUNT(*), 0), 1) as fill_rate
    FROM people.company_slot
    GROUP BY slot_type
    ORDER BY slot_type
''')
slot_breakdown = cur.fetchall()
if slot_breakdown:
    print("\nBy Slot Type:")
    for row in slot_breakdown:
        print(f"  {row['slot_type']}: {row['filled']:,}/{row['total']:,} filled ({row['fill_rate']}%)")

# Companies with at least 1 filled slot
cur.execute('''
    SELECT COUNT(DISTINCT outreach_id) as campaign_ready
    FROM people.company_slot
    WHERE is_filled = TRUE
''')
campaign_ready = cur.fetchone()
print(f"\nCompanies with >= 1 filled slot (campaign ready): {campaign_ready['campaign_ready']:,}")

# 6. PEOPLE MASTER
print('\n\n6. PEOPLE MASTER (people.people_master)')
print('-' * 80)
cur.execute('''
    SELECT
        COUNT(*) as total_contacts,
        COUNT(CASE WHEN email IS NOT NULL AND email != '' THEN 1 END) as with_email,
        COUNT(CASE WHEN email_verified = TRUE THEN 1 END) as email_verified,
        COUNT(CASE WHEN work_phone_e164 IS NOT NULL AND work_phone_e164 != '' THEN 1 END) as with_work_phone,
        COUNT(CASE WHEN personal_phone_e164 IS NOT NULL AND personal_phone_e164 != '' THEN 1 END) as with_personal_phone,
        ROUND(100.0 * COUNT(CASE WHEN email IS NOT NULL AND email != '' THEN 1 END) / NULLIF(COUNT(*), 0), 1) as email_pct,
        ROUND(100.0 * COUNT(CASE WHEN email_verified = TRUE THEN 1 END) / NULLIF(COUNT(*), 0), 1) as email_verified_pct
    FROM people.people_master
''')
people_summary = cur.fetchone()
print(f"Total Contacts: {people_summary['total_contacts']:,}")
print(f"With Email: {people_summary['with_email']:,} ({people_summary['email_pct']}%)")
print(f"Email Verified: {people_summary['email_verified']:,} ({people_summary['email_verified_pct']}%)")
print(f"With Work Phone: {people_summary['with_work_phone']:,}")
print(f"With Personal Phone: {people_summary['with_personal_phone']:,}")

# 7. BIT SCORES
print('\n\n7. BIT SCORES (outreach.bit_scores)')
print('-' * 80)
cur.execute('''
    SELECT
        COUNT(*) as total_records,
        ROUND(AVG(score), 2) as avg_score,
        MIN(score) as min_score,
        MAX(score) as max_score
    FROM outreach.bit_scores
''')
bit_summary = cur.fetchone()
print(f"Total Records: {bit_summary['total_records']:,}")
if bit_summary['avg_score']:
    print(f"Average Score: {bit_summary['avg_score']}")
    print(f"Min Score: {bit_summary['min_score']}")
    print(f"Max Score: {bit_summary['max_score']}")

# 8. ALIGNMENT CHECK
print('\n\n8. CL-OUTREACH ALIGNMENT')
print('-' * 80)
cur.execute('''
    SELECT COUNT(*) as cl_count
    FROM cl.company_identity
    WHERE outreach_id IS NOT NULL
''')
cl_count = cur.fetchone()

cur.execute('''
    SELECT COUNT(*) as outreach_count
    FROM outreach.outreach
''')
outreach_count = cur.fetchone()

print(f"CL companies with outreach_id: {cl_count['cl_count']:,}")
print(f"Outreach spine records: {outreach_count['outreach_count']:,}")
if cl_count['cl_count'] == outreach_count['outreach_count']:
    print("Status: ALIGNED [OK]")
else:
    print(f"Status: MISALIGNED (Delta {abs(cl_count['cl_count'] - outreach_count['outreach_count']):,})")

print('\n' + '=' * 80)
print('END OF REPORT')
print('=' * 80)

cur.close()
conn.close()
