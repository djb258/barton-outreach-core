#!/usr/bin/env python3
"""Check outreach.blog URL coverage"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Check outreach.blog source_url coverage
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(source_url) as has_url,
        COUNT(CASE WHEN source_url IS NULL OR source_url = '' THEN 1 END) as missing_url
    FROM outreach.blog
""")
r = cur.fetchone()
print(f"outreach.blog total: {r[0]:,}")
print(f"  Has source_url: {r[1]:,}")
print(f"  Missing source_url: {r[2]:,}")

# Sample some
cur.execute("SELECT outreach_id, source_url, source_type FROM outreach.blog LIMIT 5")
print()
print("Sample blog entries:")
for row in cur.fetchall():
    url = row[1][:60] if row[1] else "None"
    print(f"  {row[0]} | {url} | {row[2]}")

# Check how outreach links to company_identity
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN ci.company_domain IS NOT NULL THEN 1 END) as has_domain
    FROM outreach.outreach o
    LEFT JOIN cl.company_identity ci ON o.sovereign_company_id = ci.sovereign_company_id
""")
r = cur.fetchone()
print()
print(f"outreach.outreach joined to CL:")
print(f"  Total: {r[0]:,}")
print(f"  Has company_domain from CL: {r[1]:,}")

cur.close()
conn.close()
