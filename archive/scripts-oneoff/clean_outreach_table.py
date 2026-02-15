"""
Clean duplicates from outreach.outreach table
Then analyze how many would be filtered as non-commercial
"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print('='*60)
print('CLEANING DUPLICATES FROM outreach.outreach')
print('='*60)

# Get before counts
cur.execute('SELECT COUNT(*) FROM outreach.outreach')
before_outreach = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM outreach.dol')
before_dol = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM outreach.company_target')
before_ct = cur.fetchone()[0]

print(f'\nBEFORE:')
print(f'  outreach.outreach: {before_outreach:,}')
print(f'  outreach.dol: {before_dol:,}')
print(f'  outreach.company_target: {before_ct:,}')

# Delete duplicates - keep oldest per normalized domain
print('\nDeleting duplicate domains (keeping oldest per domain)...')

# Do everything in one transaction - delete from ref tables and main table
# FK dependencies from pg_constraint:
# - outreach: company_target, people, engagement_events, dol, blog,
#             company_target_errors, dol_errors, people_errors, blog_errors,
#             bit_signals, bit_scores, bit_errors, blog_source_history, bit_input_history
# - people: people_resolution_history, company_slot
# - talent_flow: movement_history
cur.execute(r'''
WITH dups AS (
    SELECT outreach_id FROM (
        SELECT outreach_id,
            ROW_NUMBER() OVER (
                PARTITION BY LOWER(REGEXP_REPLACE(domain, '^www\.', ''))
                ORDER BY created_at ASC, outreach_id ASC
            ) as rn
        FROM outreach.outreach
        WHERE domain IS NOT NULL
    ) ranked
    WHERE rn > 1
),
-- Error tables
del_dol_errors AS (
    DELETE FROM outreach.dol_errors WHERE outreach_id IN (SELECT outreach_id FROM dups)
),
del_ct_errors AS (
    DELETE FROM outreach.company_target_errors WHERE outreach_id IN (SELECT outreach_id FROM dups)
),
del_people_errors AS (
    DELETE FROM outreach.people_errors WHERE outreach_id IN (SELECT outreach_id FROM dups)
),
del_blog_errors AS (
    DELETE FROM outreach.blog_errors WHERE outreach_id IN (SELECT outreach_id FROM dups)
),
del_bit_errors AS (
    DELETE FROM outreach.bit_errors WHERE outreach_id IN (SELECT outreach_id FROM dups)
),
-- History/tracking tables
del_engagement AS (
    DELETE FROM outreach.engagement_events WHERE outreach_id IN (SELECT outreach_id FROM dups)
),
del_bit_signals AS (
    DELETE FROM outreach.bit_signals WHERE outreach_id IN (SELECT outreach_id FROM dups)
),
del_blog_history AS (
    DELETE FROM outreach.blog_source_history WHERE outreach_id IN (SELECT outreach_id FROM dups)
),
del_bit_input AS (
    DELETE FROM outreach.bit_input_history WHERE outreach_id IN (SELECT outreach_id FROM dups)
),
del_bit_scores AS (
    DELETE FROM outreach.bit_scores WHERE outreach_id IN (SELECT outreach_id FROM dups)
),
-- Cross-schema FK tables
del_people_res_history AS (
    DELETE FROM people.people_resolution_history WHERE outreach_id IN (SELECT outreach_id FROM dups)
),
del_company_slot AS (
    DELETE FROM people.company_slot WHERE outreach_id IN (SELECT outreach_id FROM dups)
),
del_movement_from AS (
    DELETE FROM talent_flow.movement_history WHERE from_outreach_id IN (SELECT outreach_id FROM dups) OR to_outreach_id IN (SELECT outreach_id FROM dups)
),
-- Sub-hub tables (must delete before main)
del_dol AS (
    DELETE FROM outreach.dol WHERE outreach_id IN (SELECT outreach_id FROM dups)
),
del_blog AS (
    DELETE FROM outreach.blog WHERE outreach_id IN (SELECT outreach_id FROM dups)
),
del_people AS (
    DELETE FROM outreach.people WHERE outreach_id IN (SELECT outreach_id FROM dups)
),
del_company_target AS (
    DELETE FROM outreach.company_target WHERE outreach_id IN (SELECT outreach_id FROM dups)
)
DELETE FROM outreach.outreach WHERE outreach_id IN (SELECT outreach_id FROM dups)
''')
deleted = cur.rowcount
conn.commit()
print(f'Deleted: {deleted:,} duplicate records from outreach.outreach')

# Get after counts
cur.execute('SELECT COUNT(*) FROM outreach.outreach')
after_outreach = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM outreach.dol')
after_dol = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM outreach.company_target')
after_ct = cur.fetchone()[0]

print(f'\nAFTER:')
print(f'  outreach.outreach: {after_outreach:,} (removed {before_outreach - after_outreach:,})')
print(f'  outreach.dol: {after_dol:,} (removed {before_dol - after_dol:,})')
print(f'  outreach.company_target: {after_ct:,} (removed {before_ct - after_ct:,})')

# Verify no more duplicate domains
cur.execute(r'''
    SELECT COUNT(*) FROM (
        SELECT LOWER(REGEXP_REPLACE(domain, '^www\.', '')) as norm_domain
        FROM outreach.outreach WHERE domain IS NOT NULL
        GROUP BY LOWER(REGEXP_REPLACE(domain, '^www\.', ''))
        HAVING COUNT(*) > 1
    ) dupes
''')
remaining_dupes = cur.fetchone()[0]
print(f'\nRemaining duplicate domains: {remaining_dupes}')

# Now move non-commercial to exclusion table
print('\n' + '='*60)
print('MOVING NON-COMMERCIAL RECORDS TO EXCLUSION TABLE')
print('='*60)

# Create exclusion table if not exists
cur.execute('''
    CREATE TABLE IF NOT EXISTS outreach.outreach_excluded (
        outreach_id UUID PRIMARY KEY,
        company_name TEXT,
        domain TEXT,
        exclusion_reason TEXT,
        excluded_at TIMESTAMPTZ DEFAULT NOW(),
        created_at TIMESTAMPTZ,
        updated_at TIMESTAMPTZ
    )
''')
conn.commit()

# Exclusion TLDs
excluded_tlds = ('.gov', '.edu', '.org', '.church', '.coop')
tld_pattern = r'\.(gov|edu|org|church|coop)$'

# Exclusion keywords
excluded_keywords = [
    'county', 'city of', 'state of', 'township', 'municipality', 'borough',
    'government', 'federal', 'dept of', 'department of', 'public works',
    'water authority', 'sewer', 'port authority', 'transit authority',
    'school district', 'public school', 'high school', 'middle school',
    'elementary school', 'university', 'college', 'academy', ' isd',
    'insurance company', 'mutual insurance', 'indemnity',
    'foundation', 'charitable', 'ministry', 'ministries', 'church',
    'temple', 'synagogue', 'mosque', 'baptist', 'methodist', 'lutheran',
    'presbyterian', 'catholic', 'diocese', 'archdiocese',
    'credit union', 'veterans', 'va hospital'
]
keyword_pattern = '|'.join(excluded_keywords)

# Move TLD exclusions - join with company_target -> company_master to get company_name
cur.execute(r'''
    INSERT INTO outreach.outreach_excluded (outreach_id, company_name, domain, exclusion_reason, created_at, updated_at)
    SELECT o.outreach_id, cm.company_name, o.domain, 'TLD: ' || SUBSTRING(o.domain FROM '(\.[^.]+)$'), o.created_at, o.updated_at
    FROM outreach.outreach o
    LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
    LEFT JOIN company.company_master cm ON ct.company_unique_id = cm.company_unique_id
    WHERE o.domain ~* %s
    ON CONFLICT (outreach_id) DO NOTHING
''', (tld_pattern,))
tld_moved = cur.rowcount
print(f'Moved {tld_moved:,} records (excluded TLDs)')

# Move keyword exclusions - check company_name OR domain for keywords
cur.execute(r'''
    INSERT INTO outreach.outreach_excluded (outreach_id, company_name, domain, exclusion_reason, created_at, updated_at)
    SELECT o.outreach_id, cm.company_name, o.domain, 'Keyword match', o.created_at, o.updated_at
    FROM outreach.outreach o
    LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
    LEFT JOIN company.company_master cm ON ct.company_unique_id = cm.company_unique_id
    WHERE (LOWER(cm.company_name) ~* %s OR LOWER(o.domain) ~* %s)
    AND o.outreach_id NOT IN (SELECT outreach_id FROM outreach.outreach_excluded)
    ON CONFLICT (outreach_id) DO NOTHING
''', (keyword_pattern, keyword_pattern))
keyword_moved = cur.rowcount
print(f'Moved {keyword_moved:,} records (keyword matches)')

conn.commit()

# Now delete from all FK tables and main table for excluded IDs
print('\nDeleting excluded records from main tables...')
cur.execute(r'''
WITH excluded_ids AS (
    SELECT outreach_id FROM outreach.outreach_excluded
),
-- Error tables
del_dol_errors AS (
    DELETE FROM outreach.dol_errors WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
),
del_ct_errors AS (
    DELETE FROM outreach.company_target_errors WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
),
del_people_errors AS (
    DELETE FROM outreach.people_errors WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
),
del_blog_errors AS (
    DELETE FROM outreach.blog_errors WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
),
del_bit_errors AS (
    DELETE FROM outreach.bit_errors WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
),
-- History/tracking tables
del_engagement AS (
    DELETE FROM outreach.engagement_events WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
),
del_bit_signals AS (
    DELETE FROM outreach.bit_signals WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
),
del_blog_history AS (
    DELETE FROM outreach.blog_source_history WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
),
del_bit_input AS (
    DELETE FROM outreach.bit_input_history WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
),
del_bit_scores AS (
    DELETE FROM outreach.bit_scores WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
),
-- Cross-schema FK tables
del_people_res_history AS (
    DELETE FROM people.people_resolution_history WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
),
del_company_slot AS (
    DELETE FROM people.company_slot WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
),
del_movement AS (
    DELETE FROM talent_flow.movement_history WHERE from_outreach_id IN (SELECT outreach_id FROM excluded_ids) OR to_outreach_id IN (SELECT outreach_id FROM excluded_ids)
),
-- Sub-hub tables
del_dol AS (
    DELETE FROM outreach.dol WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
),
del_blog AS (
    DELETE FROM outreach.blog WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
),
del_people AS (
    DELETE FROM outreach.people WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
),
del_company_target AS (
    DELETE FROM outreach.company_target WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
)
DELETE FROM outreach.outreach WHERE outreach_id IN (SELECT outreach_id FROM excluded_ids)
''')
deleted_main = cur.rowcount
conn.commit()
print(f'Deleted {deleted_main:,} non-commercial records from outreach.outreach')

# Final counts
cur.execute('SELECT COUNT(*) FROM outreach.outreach')
final_outreach = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM outreach.outreach_excluded')
final_excluded = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM outreach.dol')
final_dol = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM outreach.company_target')
final_ct = cur.fetchone()[0]

print('\n' + '='*60)
print('FINAL RESULTS')
print('='*60)
print(f'outreach.outreach (commercial): {final_outreach:,}')
print(f'outreach.outreach_excluded:     {final_excluded:,}')
print(f'outreach.dol:                   {final_dol:,}')
print(f'outreach.company_target:        {final_ct:,}')

# Show exclusion breakdown
cur.execute('''
    SELECT exclusion_reason, COUNT(*) 
    FROM outreach.outreach_excluded 
    GROUP BY exclusion_reason 
    ORDER BY COUNT(*) DESC
    LIMIT 15
''')
print('\nExclusion breakdown:')
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]:,}')

conn.close()
print('\nDone!')
