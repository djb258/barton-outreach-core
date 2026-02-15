#!/usr/bin/env python3
"""
CREATE DIAGNOSTIC VIEW: v_outreach_diagnostic
==============================================
Every outreach_id explains itself in one row.

No new tables. No external tools. Just a view.
"""

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

VIEW_SQL = """
CREATE OR REPLACE VIEW outreach.v_outreach_diagnostic AS
WITH 
-- Company Target status
ct_status AS (
    SELECT 
        ct.outreach_id,
        CASE 
            WHEN ct.imo_completed_at IS NOT NULL THEN 'PASS'
            WHEN ct.execution_status = 'failed' THEN 'BLOCKED'
            WHEN ct.execution_status = 'pending' THEN 'WAITING'
            WHEN ct.execution_status = 'ready' THEN 'WAITING'
            ELSE 'MISSING'
        END as status,
        cte.failure_code as error_code
    FROM outreach.company_target ct
    LEFT JOIN LATERAL (
        SELECT failure_code 
        FROM outreach.company_target_errors 
        WHERE outreach_id = ct.outreach_id AND resolved_at IS NULL
        ORDER BY created_at DESC LIMIT 1
    ) cte ON true
),

-- DOL status  
dol_status AS (
    SELECT 
        o.outreach_id,
        CASE 
            WHEN d.dol_id IS NOT NULL AND d.ein IS NOT NULL THEN 'PASS'
            WHEN de.failure_code = 'NO_MATCH' THEN 'NOT_REQUIRED'  -- No 5500 filing = not a plan sponsor
            WHEN de.failure_code IS NOT NULL THEN 'BLOCKED'
            WHEN d.dol_id IS NOT NULL THEN 'WAITING'  -- Has record but no EIN yet
            ELSE 'WAITING'  -- Not yet processed
        END as status,
        de.failure_code as error_code
    FROM outreach.outreach o
    LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
    LEFT JOIN LATERAL (
        SELECT failure_code 
        FROM outreach.dol_errors 
        WHERE outreach_id = o.outreach_id AND resolved_at IS NULL
        ORDER BY created_at DESC LIMIT 1
    ) de ON true
),

-- People status
people_status AS (
    SELECT 
        o.outreach_id,
        CASE 
            WHEN COUNT(p.person_id) FILTER (WHERE p.email_verified = true) > 0 THEN 'PASS'
            WHEN COUNT(p.person_id) > 0 THEN 'WAITING'  -- Has people but not verified
            WHEN pe.failure_code IS NOT NULL THEN 'BLOCKED'
            ELSE 'WAITING'  -- Not yet processed
        END as status,
        pe.failure_code as error_code,
        COUNT(p.person_id) as people_count,
        COUNT(p.person_id) FILTER (WHERE p.email_verified = true) as verified_count
    FROM outreach.outreach o
    LEFT JOIN outreach.people p ON o.outreach_id = p.outreach_id
    LEFT JOIN LATERAL (
        SELECT failure_code 
        FROM outreach.people_errors 
        WHERE outreach_id = o.outreach_id AND resolved_at IS NULL
        ORDER BY created_at DESC LIMIT 1
    ) pe ON true
    GROUP BY o.outreach_id, pe.failure_code
),

-- Blog status
blog_status AS (
    SELECT 
        o.outreach_id,
        CASE 
            WHEN COUNT(b.blog_id) > 0 THEN 'PASS'
            WHEN be.failure_code IS NOT NULL THEN 'BLOCKED'
            ELSE 'NOT_REQUIRED'  -- Blog is enrichment, not required
        END as status,
        be.failure_code as error_code,
        COUNT(b.blog_id) as signal_count
    FROM outreach.outreach o
    LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
    LEFT JOIN LATERAL (
        SELECT failure_code 
        FROM outreach.blog_errors 
        WHERE outreach_id = o.outreach_id AND resolved_at IS NULL
        ORDER BY created_at DESC LIMIT 1
    ) be ON true
    GROUP BY o.outreach_id, be.failure_code
)

SELECT 
    o.outreach_id,
    o.domain,
    o.sovereign_id,
    
    -- Sub-hub statuses
    COALESCE(ct.status, 'MISSING') as ct_status,
    COALESCE(dol.status, 'WAITING') as dol_status,
    COALESCE(ppl.status, 'WAITING') as people_status,
    COALESCE(blg.status, 'NOT_REQUIRED') as blog_status,
    
    -- Error codes (for BLOCKED status)
    ct.error_code as ct_error,
    dol.error_code as dol_error,
    ppl.error_code as people_error,
    blg.error_code as blog_error,
    
    -- Counts
    COALESCE(ppl.people_count, 0) as people_count,
    COALESCE(ppl.verified_count, 0) as people_verified,
    COALESCE(blg.signal_count, 0) as blog_signals,
    
    -- OUTREACH READY: CT must be PASS, People must be PASS
    (COALESCE(ct.status, 'MISSING') = 'PASS' 
     AND COALESCE(ppl.status, 'WAITING') = 'PASS') as outreach_ready,
    
    -- Bottleneck identification (first blocking hard requirement)
    CASE 
        WHEN COALESCE(ct.status, 'MISSING') NOT IN ('PASS') THEN 'COMPANY_TARGET'
        WHEN COALESCE(ppl.status, 'WAITING') NOT IN ('PASS') THEN 'PEOPLE'
        ELSE NULL
    END as bottleneck_hub,
    
    CASE 
        WHEN COALESCE(ct.status, 'MISSING') = 'BLOCKED' THEN ct.error_code
        WHEN COALESCE(ct.status, 'MISSING') = 'WAITING' THEN 'PROCESSING'
        WHEN COALESCE(ct.status, 'MISSING') = 'MISSING' THEN 'NO_DATA'
        WHEN COALESCE(ppl.status, 'WAITING') = 'BLOCKED' THEN ppl.error_code
        WHEN COALESCE(ppl.status, 'WAITING') = 'WAITING' THEN 'PROCESSING'
        ELSE NULL
    END as bottleneck_reason,
    
    -- Timestamps
    o.created_at,
    o.updated_at as last_activity_at

FROM outreach.outreach o
LEFT JOIN ct_status ct ON o.outreach_id = ct.outreach_id
LEFT JOIN dol_status dol ON o.outreach_id = dol.outreach_id
LEFT JOIN people_status ppl ON o.outreach_id = ppl.outreach_id
LEFT JOIN blog_status blg ON o.outreach_id = blg.outreach_id
"""

print("Creating v_outreach_diagnostic view...")
cur.execute(VIEW_SQL)
conn.commit()
print("✅ View created!")

# Test it
print("\n=== DIAGNOSTIC VIEW SAMPLE ===")
cur.execute("""
    SELECT * FROM outreach.v_outreach_diagnostic
    LIMIT 5
""")
for r in cur.fetchall():
    print(f"\n  outreach_id: {r['outreach_id']}")
    print(f"    domain: {r['domain']}")
    print(f"    CT: {r['ct_status']} | DOL: {r['dol_status']} | People: {r['people_status']} | Blog: {r['blog_status']}")
    print(f"    outreach_ready: {r['outreach_ready']}")
    print(f"    bottleneck: {r['bottleneck_hub']} → {r['bottleneck_reason']}")

# Summary stats
print("\n=== DIAGNOSTIC SUMMARY ===")
cur.execute("""
    SELECT 
        ct_status, 
        COUNT(*) as cnt,
        COUNT(*) FILTER (WHERE outreach_ready) as ready
    FROM outreach.v_outreach_diagnostic
    GROUP BY ct_status
    ORDER BY cnt DESC
""")
print("\nBy CT Status:")
for r in cur.fetchall():
    print(f"  {r['ct_status']}: {r['cnt']} (ready: {r['ready']})")

cur.execute("""
    SELECT 
        people_status, 
        COUNT(*) as cnt
    FROM outreach.v_outreach_diagnostic
    GROUP BY people_status
    ORDER BY cnt DESC
""")
print("\nBy People Status:")
for r in cur.fetchall():
    print(f"  {r['people_status']}: {r['cnt']}")

cur.execute("""
    SELECT 
        bottleneck_hub,
        bottleneck_reason,
        COUNT(*) as cnt
    FROM outreach.v_outreach_diagnostic
    WHERE bottleneck_hub IS NOT NULL
    GROUP BY bottleneck_hub, bottleneck_reason
    ORDER BY cnt DESC
    LIMIT 10
""")
print("\nTop Bottlenecks:")
for r in cur.fetchall():
    print(f"  [{r['bottleneck_hub']}] {r['bottleneck_reason']}: {r['cnt']}")

cur.execute("""
    SELECT COUNT(*) as ready FROM outreach.v_outreach_diagnostic WHERE outreach_ready = true
""")
print(f"\nTotal Outreach Ready: {cur.fetchone()['ready']}")

conn.close()
