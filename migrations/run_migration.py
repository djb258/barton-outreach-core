#!/usr/bin/env python3
"""Run a SQL migration file against the database, handling $$ dollar-quoting."""
import os
import sys
import re

def split_sql(sql_text):
    """Split SQL into statements, respecting $$ dollar-quoted blocks."""
    # Remove block comments
    sql_text = re.sub(r'/\*.*?\*/', '', sql_text, flags=re.DOTALL)

    statements = []
    current = []
    in_dollar = False
    i = 0

    while i < len(sql_text):
        c = sql_text[i]

        # Check for $$ (dollar-quote delimiter)
        if c == '$' and i + 1 < len(sql_text) and sql_text[i + 1] == '$':
            current.append('$$')
            in_dollar = not in_dollar
            i += 2
            continue

        # Statement terminator (only outside dollar-quoted blocks)
        if c == ';' and not in_dollar:
            current.append(';')
            stmt = ''.join(current).strip()
            # Keep only statements that have actual SQL (not just comments)
            code_lines = [l for l in stmt.split('\n')
                         if l.strip() and not l.strip().startswith('--')]
            if code_lines:
                statements.append(stmt)
            current = []
            i += 1
            continue

        current.append(c)
        i += 1

    return statements


def main():
    if len(sys.argv) < 2:
        print("Usage: doppler run -- python run_migration.py <sql_file>")
        sys.exit(1)

    sql_file = sys.argv[1]
    if not os.path.exists(sql_file):
        print(f"[ERROR] File not found: {sql_file}")
        sys.exit(1)

    import psycopg2
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[FAIL] DATABASE_URL not set")
        sys.exit(1)

    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cursor = conn.cursor()

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    statements = split_sql(sql)
    print(f"Parsed {len(statements)} SQL statements from {sql_file}")

    success = 0
    errors = 0

    for idx, stmt in enumerate(statements):
        try:
            cursor.execute(stmt)
            success += 1
        except Exception as e:
            errors += 1
            err_msg = str(e).strip().split('\n')[0][:150]
            preview = ' '.join(stmt.split())[:100]
            print(f"  [{idx}] ERROR: {err_msg}")
            print(f"       SQL: {preview}")

    print(f"\nResult: {success} success, {errors} errors")

    # Verify new objects
    cursor.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema IN ('sales', 'partners')
          AND table_type = 'BASE TABLE'
        ORDER BY table_schema, table_name
    """)
    rows = cursor.fetchall()
    if rows:
        print("\nNew tables created:")
        for r in rows:
            print(f"  {r[0]}.{r[1]}")

    cursor.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema = 'bit'
          AND table_name IN ('reactivation_intent', 'partner_intent')
        ORDER BY table_name
    """)
    for r in cursor.fetchall():
        print(f"  {r[0]}.{r[1]}")

    cursor.execute("""
        SELECT schemaname, viewname
        FROM pg_views
        WHERE viewname IN ('v_reactivation_ready', 'v_partner_outreach_ready')
    """)
    views = cursor.fetchall()
    if views:
        print("\nViews created:")
        for r in views:
            print(f"  {r[0]}.{r[1]}")

    conn.close()


if __name__ == "__main__":
    main()
