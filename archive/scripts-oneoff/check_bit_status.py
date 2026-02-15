#!/usr/bin/env python3
"""Full BIT status check - understand current state."""

import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host='ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    port=5432,
    database='Marketing DB',
    user='Marketing DB_owner',
    password='npg_OsE4Z2oPCpiT',
    sslmode='require'
)
cur = conn.cursor(cursor_factory=RealDictCursor)

# 1. Check existing bit_signals details
print('=== Current bit_signals ===')
cur.execute("""
    SELECT signal_id, outreach_id, signal_type, signal_impact, source_spoke, decay_period_days, created_at
    FROM outreach.bit_signals
    ORDER BY created_at DESC
    LIMIT 10
""")
for r in cur.fetchall():
    print(f"  {r['signal_type']}: impact={r['signal_impact']}, source={r['source_spoke']}, decay={r['decay_period_days']}d")
    print(f"    outreach_id={r['outreach_id']}")

# 2. Check existing bit_scores details
print('\n=== Current bit_scores ===')
cur.execute("""
    SELECT outreach_id, score, score_tier, signal_count, 
           people_score, dol_score, blog_score, talent_flow_score,
           created_at, updated_at
    FROM outreach.bit_scores
    ORDER BY created_at DESC
    LIMIT 10
""")
for r in cur.fetchall():
    print(f"  score={r['score']}, tier={r['score_tier']}, signals={r['signal_count']}")
    print(f"    people={r['people_score']}, dol={r['dol_score']}, blog={r['blog_score']}, talent_flow={r['talent_flow_score']}")

# 3. Check how many companies have hub statuses (potential signals)
print('\n=== Hub Status Counts ===')
cur.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN hub_company_target = 'PASS' THEN 1 ELSE 0 END) as target_pass,
        SUM(CASE WHEN hub_company_people = 'PASS' THEN 1 ELSE 0 END) as people_pass,
        SUM(CASE WHEN hub_company_dol = 'PASS' THEN 1 ELSE 0 END) as dol_pass,
        SUM(CASE WHEN hub_talent_flow = 'PASS' THEN 1 ELSE 0 END) as talent_pass
    FROM outreach.company_target
    WHERE company_unique_id IS NOT NULL
""")
r = cur.fetchone()
print(f"  Total companies: {r['total']}")
print(f"  company-target PASS: {r['target_pass']}")
print(f"  company-people PASS: {r['people_pass']}")
print(f"  company-dol PASS: {r['dol_pass']}")
print(f"  talent-flow PASS: {r['talent_pass']}")

# 4. Check if there's a slot_fills or similar table
print('\n=== Looking for signal source tables ===')
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'outreach' 
    AND (table_name LIKE '%slot%' 
         OR table_name LIKE '%signal%'
         OR table_name LIKE '%event%'
         OR table_name LIKE '%activity%')
    ORDER BY table_name
""")
for r in cur.fetchall():
    print(f"  {r['table_name']}")

# 5. Check forms table
print('\n=== Checking for form data ===')
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema IN ('outreach', 'public') 
    AND (table_name LIKE '%form%' OR table_name LIKE '%5500%')
    ORDER BY table_name
""")
for r in cur.fetchall():
    print(f"  {r['table_name']}")

# 6. Quick summary of potential signals from hub passes
print('\n=== Potential Signals Summary ===')
print('  Hub passes can generate signals:')
print('    - company-people PASS → people_score contribution')
print('    - company-dol PASS → dol_score contribution')
print('    - talent-flow PASS → talent_flow_score contribution')

# 7. Check if there's a blog hub
print('\n=== Blog Hub Check ===')
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' 
    AND table_name = 'company_target'
    AND column_name LIKE '%blog%'
""")
cols = cur.fetchall()
if cols:
    for c in cols:
        print(f"  Found: {c['column_name']}")
else:
    print('  No blog-related columns in company_target')

cur.close()
conn.close()
