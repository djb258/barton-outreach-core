#!/usr/bin/env python3
"""Check signal distribution to understand why all companies are COLD."""

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

# Check blog signal distribution
print('=== Blog signals per company ===')
cur.execute("""
    SELECT 
        COUNT(*) as company_count,
        MIN(blog_count) as min_blogs,
        MAX(blog_count) as max_blogs,
        AVG(blog_count)::numeric(10,2) as avg_blogs
    FROM (
        SELECT ct.outreach_id, COUNT(b.blog_id) as blog_count
        FROM outreach.company_target ct
        LEFT JOIN outreach.blog b ON b.outreach_id = ct.outreach_id
        WHERE ct.company_unique_id IS NOT NULL
        GROUP BY ct.outreach_id
    ) sub
    WHERE blog_count > 0
""")
r = cur.fetchone()
print(f"  Companies with blogs: {r['company_count']}")
print(f"  Min blogs per company: {r['min_blogs']}")
print(f"  Max blogs per company: {r['max_blogs']}")
print(f"  Avg blogs per company: {r['avg_blogs']}")

# Check how many blogs are orphaned
print('\n=== Orphaned blog records ===')
cur.execute("""
    SELECT COUNT(*) as orphan_count
    FROM outreach.blog b
    WHERE NOT EXISTS (
        SELECT 1 FROM outreach.company_target ct WHERE ct.outreach_id = b.outreach_id
    )
""")
print(f"  Blogs with no matching company_target: {cur.fetchone()['orphan_count']}")

# Check DOL distribution
print('\n=== DOL signals per company ===')
cur.execute("""
    SELECT 
        COUNT(*) as company_count,
        MIN(dol_count) as min_dol,
        MAX(dol_count) as max_dol,
        AVG(dol_count)::numeric(10,2) as avg_dol
    FROM (
        SELECT ct.outreach_id, COUNT(d.dol_id) as dol_count
        FROM outreach.company_target ct
        LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
        WHERE ct.company_unique_id IS NOT NULL
        GROUP BY ct.outreach_id
    ) sub
    WHERE dol_count > 0
""")
r = cur.fetchone()
print(f"  Companies with DOL: {r['company_count']}")
print(f"  Min DOL per company: {r['min_dol']}")
print(f"  Max DOL per company: {r['max_dol']}")
print(f"  Avg DOL per company: {r['avg_dol']}")

# Check potential score distribution
print('\n=== Projected Score Distribution ===')
cur.execute("""
    SELECT 
        score_bucket,
        COUNT(*) as company_count
    FROM (
        SELECT 
            CASE 
                WHEN total_score >= 75 THEN 'BURNING (75+)'
                WHEN total_score >= 50 THEN 'HOT (50-74)'
                WHEN total_score >= 25 THEN 'WARM (25-49)'
                WHEN total_score > 0 THEN 'COLD (1-24)'
                ELSE 'NO_SIGNALS (0)'
            END as score_bucket
        FROM (
            SELECT 
                ct.outreach_id,
                COALESCE(blog_sub.blog_score, 0) + COALESCE(dol_sub.dol_score, 0) as total_score
            FROM outreach.company_target ct
            LEFT JOIN (
                SELECT outreach_id, COUNT(*) * 5 as blog_score
                FROM outreach.blog GROUP BY outreach_id
            ) blog_sub ON blog_sub.outreach_id = ct.outreach_id
            LEFT JOIN (
                SELECT outreach_id, COUNT(*) * 5 as dol_score
                FROM outreach.dol WHERE filing_present = true GROUP BY outreach_id
            ) dol_sub ON dol_sub.outreach_id = ct.outreach_id
            WHERE ct.company_unique_id IS NOT NULL
        ) scores
    ) buckets
    GROUP BY score_bucket
    ORDER BY score_bucket
""")
for r in cur.fetchall():
    print(f"  {r['score_bucket']}: {r['company_count']}")

# Check top scoring companies
print('\n=== Top 10 Projected Scores ===')
cur.execute("""
    SELECT 
        ct.outreach_id,
        ct.company_unique_id,
        COALESCE(blog_sub.blog_count, 0) as blog_count,
        COALESCE(blog_sub.blog_score, 0) as blog_score,
        COALESCE(dol_sub.dol_count, 0) as dol_count,
        COALESCE(dol_sub.dol_score, 0) as dol_score,
        COALESCE(blog_sub.blog_score, 0) + COALESCE(dol_sub.dol_score, 0) as total_score
    FROM outreach.company_target ct
    LEFT JOIN (
        SELECT outreach_id, COUNT(*) as blog_count, COUNT(*) * 5 as blog_score
        FROM outreach.blog GROUP BY outreach_id
    ) blog_sub ON blog_sub.outreach_id = ct.outreach_id
    LEFT JOIN (
        SELECT outreach_id, COUNT(*) as dol_count, COUNT(*) * 5 as dol_score
        FROM outreach.dol WHERE filing_present = true GROUP BY outreach_id
    ) dol_sub ON dol_sub.outreach_id = ct.outreach_id
    WHERE ct.company_unique_id IS NOT NULL
    ORDER BY total_score DESC
    LIMIT 10
""")
for r in cur.fetchall():
    print(f"  {r['company_unique_id'][:12]}... blog={r['blog_score']} dol={r['dol_score']} total={r['total_score']}")

cur.close()
conn.close()
