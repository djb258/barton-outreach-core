"""Find all FK references to outreach.outreach."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")
conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()
cur.execute("""
    SELECT
        tc.table_schema || '.' || tc.table_name AS referencing_table,
        kcu.column_name,
        ccu.table_schema || '.' || ccu.table_name AS referenced_table,
        tc.constraint_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage ccu
        ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND ccu.table_schema = 'outreach' AND ccu.table_name = 'outreach'
    ORDER BY referencing_table
""")
for r in cur.fetchall():
    print(f"  {r[0]:45s} {r[1]:20s} -> {r[2]:25s} ({r[3]})")
conn.close()
