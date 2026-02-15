import os, psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

for leaf_type in ['SYSTEM', 'STAGING', 'REGISTRY', 'MV']:
    cur.execute("""
        SELECT table_schema, table_name
        FROM ctb.table_registry
        WHERE leaf_type = %s
        ORDER BY table_schema, table_name
    """, (leaf_type,))
    tables = cur.fetchall()

    print(f"\n{'#'*80}")
    print(f"  {leaf_type} ({len(tables)} tables)")
    print(f"{'#'*80}")

    for schema, table in tables:
        cur.execute("""
            SELECT
                c.column_name,
                c.data_type,
                c.is_nullable
            FROM information_schema.columns c
            LEFT JOIN pg_catalog.pg_description d
                ON d.objoid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
                AND d.objsubid = c.ordinal_position
            WHERE c.table_schema = %s AND c.table_name = %s
              AND d.description IS NULL
            ORDER BY c.ordinal_position
        """, (schema, table))
        rows = cur.fetchall()
        if rows:
            print(f"\n  {schema}.{table} ({len(rows)} gaps):")
            for col_name, data_type, nullable in rows:
                null_str = 'NOT NULL' if nullable == 'NO' else 'NULL'
                print(f"    ('{schema}', '{table}', '{col_name}', ''),  # {data_type} {null_str}")

            try:
                cur.execute(f'SELECT * FROM "{schema}"."{table}" LIMIT 1')
                cols_desc = cur.description
                row = cur.fetchone()
                if row:
                    missing_names = set(r[0] for r in rows)
                    for i, d in enumerate(cols_desc):
                        if d.name in missing_names and row[i] is not None:
                            print(f"    # SAMPLE {d.name} = {repr(row[i])[:100]}")
            except:
                pass
        else:
            print(f"\n  {schema}.{table}: FULLY DOCUMENTED")

# Get totals
print(f"\n{'#'*80}")
print("  SUMMARY")
print(f"{'#'*80}")
for leaf_type in ['SYSTEM', 'STAGING', 'REGISTRY', 'MV']:
    cur.execute("""
        SELECT table_schema, table_name
        FROM ctb.table_registry
        WHERE leaf_type = %s
    """, (leaf_type,))
    tables = cur.fetchall()
    total_cols = 0
    total_doc = 0
    for schema, table in tables:
        cur.execute("""
            SELECT COUNT(*), COUNT(d.description)
            FROM information_schema.columns c
            LEFT JOIN pg_catalog.pg_description d
                ON d.objoid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
                AND d.objsubid = c.ordinal_position
            WHERE c.table_schema = %s AND c.table_name = %s
        """, (schema, table))
        t, d = cur.fetchone()
        total_cols += t
        total_doc += d
    pct = 100*total_doc/total_cols if total_cols > 0 else 0
    print(f"  {leaf_type:10}: {total_doc}/{total_cols} ({pct:.0f}%)")

cur.close()
conn.close()
