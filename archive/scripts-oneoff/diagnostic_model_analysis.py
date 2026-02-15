#!/usr/bin/env python3
"""
OUTREACH ID DIAGNOSTIC MODEL ANALYSIS
=====================================
Pressure-test current checkbox model and design diagnostic alternative.
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

print("=" * 70)
print("OUTREACH ID DIAGNOSTIC MODEL ANALYSIS")
print("=" * 70)

# 1. Total outreach_ids
print("\n=== CURRENT STATE: outreach_id distribution ===")
cur.execute("SELECT COUNT(*) as cnt FROM outreach.outreach")
total = cur.fetchone()['cnt']
print(f"Total outreach_ids: {total}")

# 2. company_target status distribution
print("\n=== company_target status distribution ===")
cur.execute("""
    SELECT outreach_status, execution_status, COUNT(*) as cnt
    FROM outreach.company_target
    GROUP BY outreach_status, execution_status
    ORDER BY cnt DESC
""")
for r in cur.fetchall():
    print(f"  {r['outreach_status']} / {r['execution_status']}: {r['cnt']}")

# 3. Sub-hub coverage
print("\n=== SUB-HUB COVERAGE ===")

cur.execute("""
    SELECT 
        COUNT(DISTINCT o.outreach_id) as total,
        COUNT(DISTINCT ct.outreach_id) as has_ct,
        COUNT(DISTINCT d.outreach_id) as has_dol,
        COUNT(DISTINCT p.outreach_id) as has_people,
        COUNT(DISTINCT b.outreach_id) as has_blog
    FROM outreach.outreach o
    LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
    LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
    LEFT JOIN outreach.people p ON o.outreach_id = p.outreach_id
    LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
""")
r = cur.fetchone()
print(f"  Company Target: {r['has_ct']} / {r['total']} ({100*r['has_ct']/r['total']:.1f}%)")
print(f"  DOL:            {r['has_dol']} / {r['total']} ({100*r['has_dol']/r['total']:.1f}%)")
print(f"  People:         {r['has_people']} / {r['total']} ({100*r['has_people']/r['total']:.1f}%)")
print(f"  Blog:           {r['has_blog']} / {r['total']} ({100*r['has_blog']/r['total']:.1f}%)")

# 4. Error distribution
print("\n=== UNRESOLVED ERRORS BY SUB-HUB ===")
cur.execute("""
    SELECT 'company_target_errors' as tbl, COUNT(*) as cnt FROM outreach.company_target_errors WHERE resolved_at IS NULL
    UNION ALL SELECT 'dol_errors', COUNT(*) FROM outreach.dol_errors WHERE resolved_at IS NULL
    UNION ALL SELECT 'people_errors', COUNT(*) FROM outreach.people_errors WHERE resolved_at IS NULL
    UNION ALL SELECT 'blog_errors', COUNT(*) FROM outreach.blog_errors WHERE resolved_at IS NULL
    UNION ALL SELECT 'outreach_errors', COUNT(*) FROM outreach.outreach_errors
""")
for r in cur.fetchall():
    print(f"  {r['tbl']}: {r['cnt']}")

# 5. What does "complete" actually mean today?
print("\n=== CHECKBOX MODEL CRITIQUE ===")
print("""
PROBLEM: Binary complete/incomplete is too coarse.

Current v_context_current uses:
  - ct_completed_at IS NOT NULL → Company Target "done"
  - dol_ein IS NOT NULL → DOL "done"  
  - people_count > 0 → People "done"
  - blog_signal_count > 0 → Blog "done"

ISSUES:
  1. NO EXPLANATION: "incomplete" tells you nothing about WHY
  2. CONFLATES STATES: "not started" vs "failed" vs "waiting" all = incomplete
  3. BLOCKS VALID OUTREACH: Missing blog shouldn't block if we have email+DOL
  4. ERROR ORPHANS: 75k+ errors sit in tables with no visibility in main view
""")

# 6. How many outreach_ids are actually outreach-ready?
print("\n=== OUTREACH READINESS (CURRENT LOGIC) ===")
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE ct_completed_at IS NOT NULL) as has_ct,
        COUNT(*) FILTER (WHERE dol_ein IS NOT NULL) as has_dol,
        COUNT(*) FILTER (WHERE people_count > 0) as has_people,
        COUNT(*) FILTER (WHERE ct_completed_at IS NOT NULL AND people_count > 0) as ready_minimal,
        COUNT(*) FILTER (WHERE ct_completed_at IS NOT NULL AND dol_ein IS NOT NULL AND people_count > 0) as ready_full
    FROM outreach.v_context_current
""")
r = cur.fetchone()
print(f"  Total in view: {r['total']}")
print(f"  Has Company Target: {r['has_ct']}")
print(f"  Has DOL: {r['has_dol']}")
print(f"  Has People: {r['has_people']}")
print(f"  Ready (CT + People): {r['ready_minimal']}")
print(f"  Ready (CT + DOL + People): {r['ready_full']}")

# 7. Error breakdown by failure code
print("\n=== TOP ERROR CODES (unresolved) ===")
cur.execute("""
    SELECT 'CT' as hub, failure_code, COUNT(*) as cnt 
    FROM outreach.company_target_errors WHERE resolved_at IS NULL
    GROUP BY failure_code
    UNION ALL
    SELECT 'DOL', failure_code, COUNT(*) 
    FROM outreach.dol_errors WHERE resolved_at IS NULL
    GROUP BY failure_code
    ORDER BY cnt DESC
    LIMIT 10
""")
for r in cur.fetchall():
    print(f"  [{r['hub']}] {r['failure_code']}: {r['cnt']}")

conn.close()

print("\n" + "=" * 70)
print("PROPOSED DIAGNOSTIC MODEL")
print("=" * 70)
print("""
STATUS ENUM per sub-hub (not boolean):

  PASS          - Data present, valid, ready for use
  NOT_REQUIRED  - This sub-hub not needed for this outreach_id
  WAITING       - Queued, processing, or awaiting upstream
  BLOCKED       - Failed with known error code (diagnosable)
  MISSING       - No data and no error (needs investigation)

OUTREACH ELIGIBILITY RULES:

  HARD REQUIREMENTS (must be PASS to send email):
    - Company Target: PASS (need email method)
    - People: PASS (need at least 1 verified contact)
  
  SOFT REQUIREMENTS (enhance but don't block):
    - DOL: PASS or NOT_REQUIRED (retirement plan data)
    - Blog: PASS or NOT_REQUIRED (signal enrichment)

DIAGNOSTIC VIEW: v_outreach_diagnostic

  outreach_id         UUID
  domain              TEXT
  
  -- Sub-hub statuses (ENUM)
  ct_status           PASS|WAITING|BLOCKED|MISSING
  dol_status          PASS|NOT_REQUIRED|BLOCKED|MISSING  
  people_status       PASS|WAITING|BLOCKED|MISSING
  blog_status         PASS|NOT_REQUIRED|BLOCKED|MISSING
  
  -- Computed
  outreach_ready      BOOLEAN (ct=PASS AND people=PASS)
  bottleneck_hub      TEXT (first non-PASS hard requirement)
  bottleneck_code     TEXT (failure_code if BLOCKED)
  
  -- Timestamps
  created_at          TIMESTAMP
  last_activity_at    TIMESTAMP

KEY INSIGHT:
  Every outreach_id is visible. 
  No hidden failures.
  One row = one diagnosis.
""")
