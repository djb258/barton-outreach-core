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
            c.character_maximum_length,
            d.description
        FROM information_schema.columns c
        LEFT JOIN pg_catalog.pg_description d
            ON d.objoid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
            AND d.objsubid = c.ordinal_position
        WHERE c.table_schema = %s AND c.table_name = %s
        ORDER BY c.ordinal_position
    """, (schema, table))
    rows = cur.fetchall()
    missing = [(r[0], r[1], r[2], r[3], r[4]) for r in rows if not r[5]]
    documented = [(r[0], r[5]) for r in rows if r[5]]

    if missing:
        print(f"\n{'='*80}")
        print(f"  {schema}.{table} - {len(missing)} MISSING descriptions")
        print(f"{'='*80}")
        for col_name, data_type, nullable, default, max_len in missing:
            null_str = 'NULL' if nullable == 'YES' else 'NOT NULL'
            default_str = f" DEFAULT {default}" if default else ""
            len_str = f"({max_len})" if max_len else ""
            print(f"  {col_name:40} {data_type}{len_str:25} {null_str:10}{default_str}")

        if documented:
            print(f"\n  Already documented ({len(documented)}):")
            for col_name, desc in documented:
                print(f"    {col_name:40} -> {desc[:60]}")

# Also get a sample row from key tables to understand actual data
print("\n\n" + "="*80)
print("  SAMPLE DATA (1 row per table)")
print("="*80)

for schema, table in [("outreach", "dol"), ("outreach", "bit_scores"), ("outreach", "blog")]:
    cur.execute(f'SELECT * FROM "{schema}"."{table}" LIMIT 1')
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    if row:
        print(f"\n  {schema}.{table}:")
        for c, v in zip(cols, row):
            print(f"    {c:40} = {repr(v)[:80]}")

cur.close()
conn.close()
