#!/usr/bin/env python3
"""Check remaining unverified emails by source."""

import psycopg2
import os

conn = psycopg2.connect(
    host=os.environ['NEON_HOST'],
    database=os.environ['NEON_DATABASE'],
    user=os.environ['NEON_USER'],
    password=os.environ['NEON_PASSWORD'],
    sslmode='require'
)
cur = conn.cursor()

print('CLAY SOURCE EMAILS (unverified):')
cur.execute("""
SELECT pm.email, pm.full_name
FROM people.people_master pm
WHERE pm.source_system = 'clay'
  AND pm.email IS NOT NULL
  AND pm.email_verified_at IS NULL
LIMIT 10
""")
for row in cur.fetchall():
    email = row[0][:45] if row[0] else 'N/A'
    name = row[1][:25] if row[1] else 'N/A'
    print(f'  {email:45} | {name}')

print()
print('APOLLO_IMPORT SOURCE EMAILS (unverified):')
cur.execute("""
SELECT pm.email, pm.full_name
FROM people.people_master pm
WHERE pm.source_system = 'apollo_import'
  AND pm.email IS NOT NULL
  AND pm.email_verified_at IS NULL
LIMIT 10
""")
for row in cur.fetchall():
    email = row[0][:45] if row[0] else 'N/A'
    name = row[1][:25] if row[1] else 'N/A'
    print(f'  {email:45} | {name}')

conn.close()
