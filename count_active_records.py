#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import psycopg2
from psycopg2.extras import RealDictCursor

database_url = os.getenv('NEON_DATABASE_URL')
conn = psycopg2.connect(database_url)
cur = conn.cursor(cursor_factory=RealDictCursor)

print("\n" + "="*80)
print("ACTIVE RECORDS COUNT")
print("="*80 + "\n")

tables = [
    ('intake', 'company_raw_intake'),
    ('marketing', 'company_master'),
    ('marketing', 'company_slots'),
    ('marketing', 'people_master'),
    ('marketing', 'people_resolution_queue'),
    ('marketing', 'pipeline_events'),
    ('marketing', 'pipeline_errors'),
]

total = 0
for schema, table in tables:
    cur.execute(f"SELECT COUNT(*) as count FROM {schema}.{table}")
    count = cur.fetchone()['count']
    total += count
    print(f"{schema}.{table}: {count:,}")

print("\n" + "-"*80)
print(f"TOTAL ACTIVE RECORDS: {total:,}")
print("-"*80)

print("\nNote: intake.company_raw_intake (453) is source data")
print("      marketing.company_master (453) contains promoted duplicates")
print(f"      Net unique records: {total - 453:,}")
print("="*80 + "\n")

cur.close()
conn.close()

