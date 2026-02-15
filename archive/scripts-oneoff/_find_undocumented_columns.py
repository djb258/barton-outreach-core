import os, psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

for leaf_type in ['CANONICAL', 'SUPPORTING', 'ERROR']:
    cur.execute("""
        SELECT table_schema, table_name
        FROM ctb.table_registry
        WHERE leaf_type = %s
        ORDER BY table_schema, table_name
    """, (leaf_type,))
    tables = cur.fetchall()

    for schema, table in tables:
        cur.execute("""
            SELECT
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default
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
            print(f"\n{schema}.{table} ({len(rows)} gaps):")
            for col_name, data_type, nullable, default in rows:
                null_str = 'NOT NULL' if nullable == 'NO' else 'NULL'
                print(f"  ('{schema}', '{table}', '{col_name}',")
                print(f"   ''),  # {data_type} {null_str}")

            # Sample data
            try:
                cur.execute(f'SELECT * FROM "{schema}"."{table}" LIMIT 1')
                cols_desc = cur.description
                row = cur.fetchone()
                if row:
                    missing_names = set(r[0] for r in rows)
                    for i, d in enumerate(cols_desc):
                        if d.name in missing_names and row[i] is not None:
                            print(f"  # SAMPLE {d.name} = {repr(row[i])[:100]}")
            except:
                pass

cur.close()
conn.close()
