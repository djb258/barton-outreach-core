#!/usr/bin/env python3
"""Debug: Check what domains are being processed."""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host=os.environ['NEON_HOST'],
    database=os.environ['NEON_DATABASE'],
    user=os.environ['NEON_USER'],
    password=os.environ['NEON_PASSWORD'],
    sslmode='require'
)

with conn.cursor(cursor_factory=RealDictCursor) as cur:
    cur.execute("""
        WITH has_urls AS (
            SELECT DISTINCT cs.outreach_id
            FROM people.company_slot cs
            JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
            JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
            JOIN company.company_master cm ON ci.normalized_domain = LOWER(REGEXP_REPLACE(REGEXP_REPLACE(cm.website_url, '^https?://', ''), '/.*$', ''))
            JOIN company.company_source_urls cu ON cm.company_unique_id = cu.company_unique_id
            WHERE cs.is_filled = false
              AND cs.slot_type IN ('CEO', 'CFO', 'HR')
              AND cu.source_type IN ('leadership_page', 'team_page', 'about_page')
        ),
        no_urls AS (
            SELECT DISTINCT cs.outreach_id
            FROM people.company_slot cs
            WHERE cs.is_filled = false
              AND cs.slot_type IN ('CEO', 'CFO', 'HR')
              AND cs.outreach_id NOT IN (SELECT outreach_id FROM has_urls)
        )
        SELECT
            ci.normalized_domain as domain,
            COUNT(*) as cnt
        FROM no_urls nu
        JOIN outreach.outreach o ON nu.outreach_id = o.outreach_id
        JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
        JOIN company.company_master cm ON ci.normalized_domain = LOWER(REGEXP_REPLACE(REGEXP_REPLACE(cm.website_url, '^https?://', ''), '/.*$', ''))
        WHERE ci.normalized_domain IS NOT NULL
          AND ci.normalized_domain <> ''
        GROUP BY ci.normalized_domain
        ORDER BY ci.normalized_domain
        LIMIT 100
    """)
    rows = cur.fetchall()
    print(f"Sample of {len(rows)} domains being processed:")
    for row in rows:
        print(f"  {row['domain']}")

conn.close()
