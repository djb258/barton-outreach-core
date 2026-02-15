"""
Final column documentation audit report.
Verifies 100% coverage and generates summary.
"""
import os
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]


def run():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("=" * 80)
    print("  COLUMN DOCUMENTATION AUDIT REPORT")
    print("  Date: 2026-02-13")
    print("=" * 80)

    # 1. Grand totals by leaf type
    cur.execute("""
        SELECT r.leaf_type,
               COUNT(DISTINCT r.table_schema || '.' || r.table_name) as table_count,
               COUNT(c.column_name) as total_cols,
               COUNT(d.description) as documented_cols
        FROM ctb.table_registry r
        JOIN information_schema.columns c
            ON c.table_schema = r.table_schema
            AND c.table_name = r.table_name
        LEFT JOIN pg_catalog.pg_description d
            ON d.objoid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
            AND d.objsubid = c.ordinal_position
        GROUP BY r.leaf_type
        ORDER BY total_cols DESC
    """)
    results = cur.fetchall()

    print(f"\n  BY LEAF TYPE:")
    print(f"  {'Leaf Type':15} {'Tables':>7} {'Columns':>8} {'Documented':>11} {'%':>6}")
    print(f"  {'-'*15} {'-'*7} {'-'*8} {'-'*11} {'-'*6}")

    grand_tables = 0
    grand_total = 0
    grand_documented = 0

    for leaf_type, tables, total, documented in results:
        pct = 100 * documented / total if total > 0 else 0
        print(f"  {leaf_type:15} {tables:>7} {total:>8} {documented:>11} {pct:>5.1f}%")
        grand_tables += tables
        grand_total += total
        grand_documented += documented

    pct = 100 * grand_documented / grand_total if grand_total > 0 else 0
    print(f"  {'-'*15} {'-'*7} {'-'*8} {'-'*11} {'-'*6}")
    print(f"  {'TOTAL':15} {grand_tables:>7} {grand_total:>8} {grand_documented:>11} {pct:>5.1f}%")

    # 2. By schema
    cur.execute("""
        SELECT r.table_schema,
               COUNT(DISTINCT r.table_schema || '.' || r.table_name) as table_count,
               COUNT(c.column_name) as total_cols,
               COUNT(d.description) as documented_cols
        FROM ctb.table_registry r
        JOIN information_schema.columns c
            ON c.table_schema = r.table_schema
            AND c.table_name = r.table_name
        LEFT JOIN pg_catalog.pg_description d
            ON d.objoid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
            AND d.objsubid = c.ordinal_position
        GROUP BY r.table_schema
        ORDER BY total_cols DESC
    """)
    results = cur.fetchall()

    print(f"\n  BY SCHEMA:")
    print(f"  {'Schema':20} {'Tables':>7} {'Columns':>8} {'Documented':>11} {'%':>6}")
    print(f"  {'-'*20} {'-'*7} {'-'*8} {'-'*11} {'-'*6}")
    for schema, tables, total, documented in results:
        pct = 100 * documented / total if total > 0 else 0
        print(f"  {schema:20} {tables:>7} {total:>8} {documented:>11} {pct:>5.1f}%")

    # 3. CTB_CONTRACT comments
    cur.execute("""
        SELECT COUNT(*)
        FROM pg_catalog.pg_description d
        WHERE d.description LIKE '%CTB_CONTRACT%'
    """)
    ctb_count = cur.fetchone()[0]
    print(f"\n  CTB_CONTRACT comments: {ctb_count}")

    # 4. Frozen core table detail
    print(f"\n  FROZEN CORE TABLES (9):")
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
            SELECT COUNT(*), COUNT(d.description)
            FROM information_schema.columns c
            LEFT JOIN pg_catalog.pg_description d
                ON d.objoid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
                AND d.objsubid = c.ordinal_position
            WHERE c.table_schema = %s AND c.table_name = %s
        """, (schema, table))
        total, documented = cur.fetchone()
        pct = 100 * documented / total
        print(f"    {schema}.{table:30} {documented}/{total} ({pct:.0f}%)")

    # 5. Tables with any gaps
    cur.execute("""
        SELECT r.table_schema, r.table_name, r.leaf_type,
               COUNT(c.column_name) as total,
               COUNT(d.description) as documented
        FROM ctb.table_registry r
        JOIN information_schema.columns c
            ON c.table_schema = r.table_schema
            AND c.table_name = r.table_name
        LEFT JOIN pg_catalog.pg_description d
            ON d.objoid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
            AND d.objsubid = c.ordinal_position
        GROUP BY r.table_schema, r.table_name, r.leaf_type
        HAVING COUNT(c.column_name) > COUNT(d.description)
        ORDER BY r.leaf_type, r.table_schema, r.table_name
    """)
    gaps = cur.fetchall()

    print(f"\n  TABLES WITH DOCUMENTATION GAPS: {len(gaps)}")
    if gaps:
        for schema, table, leaf_type, total, documented in gaps:
            print(f"    {schema}.{table:40} {leaf_type:15} {documented}/{total}")
    else:
        print("    NONE - All tables at 100%")

    # Summary
    print(f"\n{'='*80}")
    print(f"  RESULT: {'COMPLETE' if grand_total == grand_documented else 'INCOMPLETE'}")
    print(f"  Tables:  {grand_tables}")
    print(f"  Columns: {grand_total}")
    print(f"  Documented: {grand_documented} ({100*grand_documented/grand_total:.1f}%)")
    print(f"  CTB_CONTRACT: {ctb_count}")
    print(f"  Gaps: {len(gaps)} tables")
    print(f"{'='*80}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    run()
