#!/usr/bin/env python3
"""Check the double filter issue on slot filling."""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("="*70)
print("DOUBLE FILTER ANALYSIS")
print("="*70)

# Current empty slots
cur.execute("""
SELECT slot_type, COUNT(*) as empty_slots
FROM people.company_slot
WHERE is_filled = false
GROUP BY slot_type
ORDER BY slot_type
""")
print("\n=== EMPTY SLOTS ===")
empty = {r[0]: r[1] for r in cur.fetchall()}
for slot, cnt in empty.items():
    print(f"  {slot}: {cnt:,}")

# Hunter contacts available by domain (no title filter)
print("\n=== SLOTS WITH ANY HUNTER CONTACT (no title filter) ===")
cur.execute("""
    WITH cm_domains AS (
        SELECT 
            company_unique_id,
            LOWER(REGEXP_REPLACE(
                REGEXP_REPLACE(website_url, '^https?://(www\.)?', ''),
                '/.*$', ''
            )) as domain
        FROM company.company_master
        WHERE website_url IS NOT NULL
    )
    SELECT 
        cs.slot_type,
        COUNT(DISTINCT cs.slot_id) as slots_with_any_contact
    FROM people.company_slot cs
    JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
    JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
    JOIN cm_domains cmd ON cmd.domain = LOWER(o.domain)
    JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
    WHERE cs.is_filled = false
    AND hc.email IS NOT NULL
    AND hc.first_name IS NOT NULL
    AND hc.last_name IS NOT NULL
    AND cmd.company_unique_id IS NOT NULL
    GROUP BY cs.slot_type
    ORDER BY cs.slot_type
""")
no_filter = {r[0]: r[1] for r in cur.fetchall()}
for slot, cnt in no_filter.items():
    print(f"  {slot}: {cnt:,} slots have ANY Hunter contact")

# With title filter (current behavior)
print("\n=== SLOTS WITH TITLE FILTER (current behavior) ===")

title_filters = {
    'CEO': """(
        LOWER(hc.job_title) LIKE '%ceo%' 
        OR LOWER(hc.job_title) LIKE '%chief executive%' 
        OR LOWER(hc.job_title) LIKE '%president%'
        OR LOWER(hc.job_title) = 'owner'
        OR LOWER(hc.job_title) = 'founder'
    )""",
    'CFO': """(
        LOWER(hc.job_title) LIKE '%cfo%'
        OR LOWER(hc.job_title) LIKE '%chief financial%'
        OR LOWER(hc.job_title) LIKE '%controller%'
        OR LOWER(hc.job_title) LIKE '%treasurer%'
        OR hc.department = 'Finance'
    )""",
    'HR': """(
        LOWER(hc.job_title) LIKE '%hr %'
        OR LOWER(hc.job_title) LIKE '%human resource%'
        OR LOWER(hc.job_title) LIKE '%talent%'
        OR LOWER(hc.job_title) LIKE '%recruiting%'
        OR LOWER(hc.job_title) LIKE '%people operations%'
        OR hc.department = 'HR'
    )"""
}

with_filter = {}
for slot_type, title_filter in title_filters.items():
    cur.execute(f"""
        WITH cm_domains AS (
            SELECT 
                company_unique_id,
                LOWER(REGEXP_REPLACE(
                    REGEXP_REPLACE(website_url, '^https?://(www\.)?', ''),
                    '/.*$', ''
                )) as domain
            FROM company.company_master
            WHERE website_url IS NOT NULL
        )
        SELECT COUNT(DISTINCT cs.slot_id) 
        FROM people.company_slot cs
        JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
        JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
        JOIN cm_domains cmd ON cmd.domain = LOWER(o.domain)
        JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
        WHERE cs.is_filled = false
        AND cs.slot_type = '{slot_type}'
        AND hc.email IS NOT NULL
        AND hc.first_name IS NOT NULL
        AND hc.last_name IS NOT NULL
        AND cmd.company_unique_id IS NOT NULL
        AND {title_filter}
    """)
    with_filter[slot_type] = cur.fetchone()[0]
    print(f"  {slot_type}: {with_filter[slot_type]:,} slots")

print("\n=== GAP ANALYSIS (potential additional fills) ===")
for slot_type in ['CEO', 'CFO', 'HR']:
    gap = no_filter.get(slot_type, 0) - with_filter.get(slot_type, 0)
    print(f"  {slot_type}: {gap:,} additional slots could be filled if we relaxed title filter")

# Check what titles we're missing
print("\n=== TOP MISSING TITLES BY SLOT TYPE ===")
for slot_type in ['CEO', 'CFO', 'HR']:
    print(f"\n{slot_type} - Top titles NOT matching current filter:")
    cur.execute(f"""
        WITH cm_domains AS (
            SELECT 
                company_unique_id,
                LOWER(REGEXP_REPLACE(
                    REGEXP_REPLACE(website_url, '^https?://(www\.)?', ''),
                    '/.*$', ''
                )) as domain
            FROM company.company_master
            WHERE website_url IS NOT NULL
        )
        SELECT hc.job_title, hc.department, COUNT(*) as cnt
        FROM people.company_slot cs
        JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
        JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
        JOIN cm_domains cmd ON cmd.domain = LOWER(o.domain)
        JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
        WHERE cs.is_filled = false
        AND cs.slot_type = '{slot_type}'
        AND hc.email IS NOT NULL
        AND hc.first_name IS NOT NULL
        AND hc.last_name IS NOT NULL
        AND cmd.company_unique_id IS NOT NULL
        AND NOT {title_filters[slot_type]}
        GROUP BY hc.job_title, hc.department
        ORDER BY COUNT(*) DESC
        LIMIT 20
    """)
    for r in cur.fetchall():
        print(f"  {r[0]:50} | dept={r[1]:20} | {r[2]:,}")

conn.close()
