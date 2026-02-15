import os, psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

for leaf_type in ['SUPPORTING', 'ERROR']:
    cur.execute("""
        SELECT table_schema, table_name
        FROM ctb.table_registry
        WHERE leaf_type = %s
        ORDER BY table_schema, table_name
    """, (leaf_type,))
    tables = cur.fetchall()
    print(f"\n{'#'*80}")
    print(f"  {leaf_type} TABLES ({len(tables)} total)")
    print(f"{'#'*80}")

    for schema, table in tables:
        cur.execute("""
            SELECT
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                d.description
            FROM information_schema.columns c
            LEFT JOIN pg_catalog.pg_description d
                ON d.objoid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
                AND d.objsubid = c.ordinal_position
            WHERE c.table_schema = %s AND c.table_name = %s
            ORDER BY c.ordinal_position
        """, (schema, table))
        rows = cur.fetchall()
        missing = [(r[0], r[1], r[2], r[3]) for r in rows if not r[4]]
        documented = sum(1 for r in rows if r[4])

        print(f"\n  {schema}.{table} ({len(rows)} cols, {documented} documented, {len(missing)} missing)")

        if missing:
            for col_name, data_type, nullable, default in missing:
                null_str = 'NULL' if nullable == 'YES' else 'NOT NULL'
                default_str = f" DEFAULT {default}" if default else ""
                print(f"    MISSING  '{col_name}' {data_type} {null_str}{default_str}")

            # Sample data
            try:
                cur.execute(f'SELECT * FROM "{schema}"."{table}" LIMIT 1')
                cols = [d[0] for d in cur.description]
                row = cur.fetchone()
                if row:
                    print(f"    Sample:")
                    for c, v in zip(cols, row):
                        if c in [m[0] for m in missing]:
                            val = repr(v)[:80] if v is not None else 'NULL'
                            print(f"      {c:35} = {val}")
            except Exception as e:
                print(f"    (Sample error: {e})")
        else:
            print(f"    FULLY DOCUMENTED")

cur.close()
conn.close()
