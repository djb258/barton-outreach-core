#!/usr/bin/env python3
"""Verify BIT scores were populated."""

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

# 1. Check bit_scores table
print('=== bit_scores Summary ===')
cur.execute("""
    SELECT 
        COUNT(*) as total,
        MIN(score) as min_score,
        MAX(score) as max_score,
        AVG(score)::numeric(10,2) as avg_score
    FROM outreach.bit_scores
""")
r = cur.fetchone()
print(f"  Total records: {r['total']}")
print(f"  Min score: {r['min_score']}")
print(f"  Max score: {r['max_score']}")
print(f"  Avg score: {r['avg_score']}")

# 2. Tier distribution
print('\n=== Tier Distribution ===')
cur.execute("""
    SELECT score_tier, COUNT(*) as cnt
    FROM outreach.bit_scores
    GROUP BY score_tier
    ORDER BY score_tier
""")
for r in cur.fetchall():
    print(f"  {r['score_tier']}: {r['cnt']}")

# 3. Check bit_score_snapshot in company_target
print('\n=== bit_score_snapshot in company_target ===')
cur.execute("""
    SELECT 
        COUNT(*) as with_snapshot,
        MIN(bit_score_snapshot) as min_snap,
        MAX(bit_score_snapshot) as max_snap
    FROM outreach.company_target
    WHERE bit_score_snapshot IS NOT NULL
""")
r = cur.fetchone()
print(f"  Companies with snapshot: {r['with_snapshot']}")
print(f"  Min snapshot: {r['min_snap']}")
print(f"  Max snapshot: {r['max_snap']}")

# 4. Check marketing eligibility view now shows BIT scores
print('\n=== Marketing Eligibility (sample) ===')
cur.execute("""
    SELECT company_unique_id, overall_status, bit_gate_status, bit_score, computed_tier
    FROM outreach.vw_marketing_eligibility_with_overrides
    LIMIT 5
""")
for r in cur.fetchall():
    print(f"  {r['company_unique_id'][:12]}... status={r['overall_status']}, bit_gate={r['bit_gate_status']}, bit={r['bit_score']}, tier={r['computed_tier']}")

# 5. Check sovereign completion view
print('\n=== Sovereign Completion (sample) ===')
cur.execute("""
    SELECT company_unique_id, company_target_status, bit_gate_status, bit_score, overall_status
    FROM outreach.vw_sovereign_completion
    WHERE bit_score > 0
    LIMIT 5
""")
for r in cur.fetchall():
    print(f"  {r['company_unique_id'][:12]}... target={r['company_target_status']}, bit_gate={r['bit_gate_status']}, bit={r['bit_score']}, overall={r['overall_status']}")

cur.close()
conn.close()
