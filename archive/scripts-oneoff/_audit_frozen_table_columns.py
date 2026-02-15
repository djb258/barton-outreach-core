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
            d.description
        FROM information_schema.columns c
        LEFT JOIN pg_catalog.pg_description d
            ON d.objoid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
            AND d.objsubid = c.ordinal_position
        WHERE c.table_schema = %s AND c.table_name = %s
        ORDER BY c.ordinal_position
    """, (schema, table))
    rows = cur.fetchall()
    print(f"\n{'='*80}")
    print(f"  {schema}.{table} ({len(rows)} columns)")
    print(f"{'='*80}")
    documented = 0
    for col_name, data_type, nullable, default, desc in rows:
        status = "OK" if desc else "MISSING"
        if desc:
            documented += 1
        print(f"  {status:7}  {col_name:40} {data_type:25} {'NULL' if nullable == 'YES' else 'NOT NULL':10} {(desc or ''):60}")
    print(f"  --- {documented}/{len(rows)} documented ({100*documented/len(rows):.0f}%)")

cur.close()
conn.close()
