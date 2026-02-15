import os, psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

frozen_tables = [
    ("cl", "company_identity"),
    ("outreach", "outreach"),
    ("outreach", "company_target"),
    ("outreach", "dol"),
    ("outreach", "blog"),
    ("outreach", "people"),
    ("outreach", "bit_scores"),
    ("people", "people_master"),
    ("people", "company_slot"),
]

for schema, table in frozen_tables:
    cur.execute("""
        SELECT
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.column_default,
            c.character_maximum_length
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
        print(f"\n{schema}.{table} ({len(rows)} undocumented):")
        for col_name, data_type, nullable, default, max_len in rows:
            null_str = 'NULL' if nullable == 'YES' else 'NOT NULL'
            default_str = f" DEFAULT {default}" if default else ""
            len_str = f"({max_len})" if max_len else ""
            print(f"  '{col_name}' {data_type}{len_str} {null_str}{default_str}")

# Also get 1 sample row from tables with most gaps
print("\n\nSample data for gap tables:")
for schema, table in [("cl", "company_identity"), ("people", "people_master"), ("people", "company_slot"), ("outreach", "blog"), ("outreach", "bit_scores"), ("outreach", "company_target")]:
    # Check if table has outreach_id column
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s AND column_name = 'outreach_id'
    """, (schema, table))
    has_outreach_id = cur.fetchone() is not None

    if has_outreach_id:
        cur.execute(f'SELECT * FROM "{schema}"."{table}" WHERE outreach_id IS NOT NULL LIMIT 1')
    else:
        cur.execute(f'SELECT * FROM "{schema}"."{table}" LIMIT 1')

    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    if row:
        print(f"\n  {schema}.{table} columns: {cols}")
        for c, v in zip(cols, row):
            val = repr(v)[:80] if v is not None else 'NULL'
            print(f"    {c:40} = {val}")

cur.close()
conn.close()
