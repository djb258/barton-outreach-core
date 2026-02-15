import os, psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

# Get all CANONICAL tables that are NOT frozen
cur.execute("""
    SELECT table_schema, table_name, is_frozen
    FROM ctb.table_registry
    WHERE leaf_type = 'CANONICAL'
    ORDER BY table_schema, table_name
""")
canonical_tables = cur.fetchall()
print(f"Total CANONICAL tables: {len(canonical_tables)}")

frozen_core = {
    ("cl", "company_identity"),
    ("outreach", "outreach"),
    ("outreach", "company_target"),
    ("outreach", "dol"),
    ("outreach", "blog"),
    ("outreach", "people"),
    ("outreach", "bit_scores"),
    ("people", "people_master"),
    ("people", "company_slot"),
}

for schema, table, is_frozen in canonical_tables:
    if (schema, table) in frozen_core:
        continue  # Already done

    cur.execute("""
        SELECT
            c.column_name,
            c.data_type,
            c.is_nullable,
            d.description
        FROM information_schema.columns c
        LEFT JOIN pg_catalog.pg_description d
            ON d.objoid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
            AND d.objsubid = c.ordinal_position
        WHERE c.table_schema = %s AND c.table_name = %s
        ORDER BY c.ordinal_position
    """, (schema, table))
    rows = cur.fetchall()
    missing = [(r[0], r[1], r[2]) for r in rows if not r[3]]
    documented = sum(1 for r in rows if r[3])

    frozen_str = " [FROZEN]" if is_frozen else ""
    print(f"\n{'='*80}")
    print(f"  {schema}.{table}{frozen_str} ({len(rows)} cols, {documented} documented, {len(missing)} missing)")
    print(f"{'='*80}")

    if missing:
        for col_name, data_type, nullable in missing:
            null_str = 'NULL' if nullable == 'YES' else 'NOT NULL'
            print(f"  MISSING  '{col_name}' {data_type} {null_str}")
    else:
        print(f"  FULLY DOCUMENTED")

    # Get sample row if there are missing columns
    if missing:
        try:
            cur.execute(f'SELECT * FROM "{schema}"."{table}" LIMIT 1')
            cols = [d[0] for d in cur.description]
            row = cur.fetchone()
            if row:
                print(f"\n  Sample data:")
                for c, v in zip(cols, row):
                    if c in [m[0] for m in missing]:
                        val = repr(v)[:80] if v is not None else 'NULL'
                        print(f"    {c:40} = {val}")
        except Exception as e:
            print(f"  (Could not fetch sample: {e})")

cur.close()
conn.close()
