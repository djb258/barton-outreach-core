import psycopg2
import os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print('=== Understanding the join paths ===')

# The proper path is:
# hunter_contact.domain -> outreach.outreach.domain -> company_slot.outreach_id = outreach.sovereign_id

print('\n=== Path: Hunter -> domain -> outreach.outreach -> slot ===')
cur.execute("""
SELECT COUNT(DISTINCT cs.slot_id)
FROM people.company_slot cs
JOIN outreach.outreach o ON o.sovereign_id = cs.outreach_id
JOIN enrichment.hunter_contact hc ON LOWER(hc.domain) = LOWER(o.domain)
WHERE cs.is_filled = FALSE
AND hc.email IS NOT NULL
""")
print(f'Empty slots joinable to Hunter via domain: {cur.fetchone()[0]:,}')

# Check with slot types
for slot_type in ['CEO', 'CFO', 'HR']:
    cur.execute("""
        SELECT COUNT(DISTINCT cs.slot_id)
        FROM people.company_slot cs
        JOIN outreach.outreach o ON o.sovereign_id = cs.outreach_id
        JOIN enrichment.hunter_contact hc ON LOWER(hc.domain) = LOWER(o.domain)
        WHERE cs.is_filled = FALSE
        AND cs.slot_type = %s
        AND hc.email IS NOT NULL
        AND hc.confidence_score >= 80
    """, (slot_type,))
    print(f'  {slot_type}: {cur.fetchone()[0]:,}')

# Now check the full path to Barton ID
print('\n=== Full path with Barton ===')
cur.execute("""
SELECT COUNT(DISTINCT cs.slot_id)
FROM people.company_slot cs
JOIN outreach.outreach o ON o.sovereign_id = cs.outreach_id
JOIN company.company_master cm ON LOWER(REPLACE(REPLACE(REPLACE(cm.website_url, 'https://', ''), 'http://', ''), 'www.', '')) LIKE LOWER(o.domain) || '%'
JOIN enrichment.hunter_contact hc ON LOWER(hc.domain) = LOWER(o.domain)
WHERE cs.is_filled = FALSE
AND hc.email IS NOT NULL
AND cm.company_unique_id LIKE '04.04.01%'
""")
print(f'Empty slots with full Barton path: {cur.fetchone()[0]:,}')