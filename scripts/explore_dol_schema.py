#!/usr/bin/env python3
"""Explore full DOL schema - all 1.4M filings."""

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 70)
print("FULL DOL SCHEMA EXPLORATION")
print("=" * 70)

# 1. All tables in dol schema
print("\n1. ALL TABLES IN DOL SCHEMA")
print("-" * 50)

cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'dol'
    ORDER BY table_name
""")
tables = [row['table_name'] for row in cur.fetchall()]
print(f"Found {len(tables)} tables:")
for t in tables:
    print(f"  {t}")

# 2. Row counts for each table
print("\n2. ROW COUNTS PER TABLE")
print("-" * 50)

total_rows = 0
for t in tables:
    try:
        cur.execute(f"SELECT COUNT(*) as cnt FROM dol.{t}")
        cnt = cur.fetchone()['cnt']
        total_rows += cnt
        if cnt > 0:
            print(f"  {t:<40}: {cnt:>10,}")
    except Exception as e:
        print(f"  {t:<40}: ERROR - {e}")

print(f"\n  {'TOTAL':<40}: {total_rows:>10,}")

# 3. Find EIN columns in each table
print("\n3. EIN COLUMNS BY TABLE")
print("-" * 50)

cur.execute("""
    SELECT table_name, column_name
    FROM information_schema.columns
    WHERE table_schema = 'dol'
    AND (column_name LIKE '%ein%' OR column_name LIKE '%EIN%')
    ORDER BY table_name, column_name
""")
ein_cols = cur.fetchall()
print(f"Found {len(ein_cols)} EIN-related columns:")
for row in ein_cols:
    print(f"  {row['table_name']:<30}: {row['column_name']}")

# 4. Unique EINs per table
print("\n4. UNIQUE EINs PER TABLE")
print("-" * 50)

ein_tables = {}
for row in ein_cols:
    t = row['table_name']
    col = row['column_name']
    if t not in ein_tables:
        ein_tables[t] = []
    ein_tables[t].append(col)

total_unique_eins = set()
for t, cols in ein_tables.items():
    for col in cols:
        try:
            cur.execute(f"SELECT COUNT(DISTINCT {col}) as cnt FROM dol.{t} WHERE {col} IS NOT NULL")
            cnt = cur.fetchone()['cnt']
            if cnt > 0:
                print(f"  {t}.{col:<30}: {cnt:>10,}")
                # Get sample of EINs
                cur.execute(f"SELECT DISTINCT {col} FROM dol.{t} WHERE {col} IS NOT NULL LIMIT 10000")
                for r in cur.fetchall():
                    total_unique_eins.add(r[col])
        except Exception as e:
            print(f"  {t}.{col:<30}: ERROR - {e}")

print(f"\n  Unique EINs across all tables (sampled): {len(total_unique_eins):,}+")

# 5. Check for state columns
print("\n5. STATE COLUMNS BY TABLE")
print("-" * 50)

cur.execute("""
    SELECT table_name, column_name
    FROM information_schema.columns
    WHERE table_schema = 'dol'
    AND (column_name LIKE '%state%' OR column_name LIKE '%STATE%')
    ORDER BY table_name, column_name
""")
state_cols = cur.fetchall()
print(f"Found {len(state_cols)} state-related columns:")
for row in state_cols:
    print(f"  {row['table_name']:<30}: {row['column_name']}")

# 6. Let's look at the big tables
print("\n6. MAJOR TABLES STRUCTURE")
print("-" * 50)

major_tables = ['form_5500', 'form_5500_ez', 'schedule_a', 'schedule_h', 'schedule_i']
for t in major_tables:
    if t in tables:
        print(f"\n  {t}:")
        cur.execute(f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'dol' AND table_name = '{t}'
            ORDER BY ordinal_position
            LIMIT 15
        """)
        for col in cur.fetchall():
            print(f"    {col['column_name']}: {col['data_type']}")

conn.close()
