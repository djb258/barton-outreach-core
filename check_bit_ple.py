#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import psycopg2
from psycopg2.extras import RealDictCursor

database_url = os.getenv('NEON_DATABASE_URL')
conn = psycopg2.connect(database_url)
cur = conn.cursor(cursor_factory=RealDictCursor)

# Check all BIT/PLE related schemas (case variations)
cur.execute("""
    SELECT schemaname, tablename, 
           pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
    FROM pg_tables
    WHERE LOWER(schemaname) IN ('bit', 'ple')
    ORDER BY schemaname, tablename
""")

tables = cur.fetchall()

print("\nBIT/PLE Tables Found:")
print("="*80)
if tables:
    for t in tables:
        cur.execute(f"SELECT COUNT(*) as count FROM {t['schemaname']}.{t['tablename']}")
        count = cur.fetchone()['count']
        print(f"{t['schemaname']}.{t['tablename']}: {count} rows ({t['size']})")
else:
    print("(no tables found)")

# Check views too
cur.execute("""
    SELECT schemaname, viewname
    FROM pg_views
    WHERE LOWER(schemaname) IN ('bit', 'ple')
    ORDER BY schemaname, viewname
""")

views = cur.fetchall()

print("\nBIT/PLE Views Found:")
print("="*80)
if views:
    for v in views:
        print(f"{v['schemaname']}.{v['viewname']}")
else:
    print("(no views found)")

cur.close()
conn.close()

