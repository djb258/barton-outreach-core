#!/usr/bin/env python3
"""
CTB Conformance Audit - READ ONLY
Inventories all tables with PKs for CTB mapping.
"""
import psycopg2
import os
import csv

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    # Schemas to audit (exclude system schemas)
    cur.execute("""
    SELECT schema_name
    FROM information_schema.schemata
    WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
      AND schema_name NOT LIKE 'pg_temp%'
      AND schema_name NOT LIKE 'pg_toast_temp%'
    ORDER BY schema_name
    """)
    schemas = [r[0] for r in cur.fetchall()]

    results = []

    for schema in schemas:
        # Get all tables
        cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """, (schema,))
        tables = [r[0] for r in cur.fetchall()]

        for table in tables:
            # Get row count
            try:
                cur.execute(f'SELECT COUNT(*) FROM "{schema}"."{table}"')
                row_count = cur.fetchone()[0]
            except Exception as e:
                row_count = f"ERROR: {e}"

            # Get primary key columns
            cur.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_schema = %s
              AND tc.table_name = %s
            ORDER BY kcu.ordinal_position
            """, (schema, table))
            pk_cols = [r[0] for r in cur.fetchall()]
            pk_str = ", ".join(pk_cols) if pk_cols else "NO PK"

            # Get all columns for analysis
            cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
            """, (schema, table))
            all_cols = [r[0] for r in cur.fetchall()]

            # Check for key columns that indicate CTB position
            has_sovereign = 'sovereign_company_id' in all_cols
            has_outreach = 'outreach_id' in all_cols
            has_company_target = 'company_target_id' in all_cols
            has_dol = 'dol_id' in all_cols
            has_blog = 'blog_id' in all_cols
            has_people = 'people_id' in all_cols or 'people_master_id' in all_cols
            has_ein = 'ein' in all_cols or 'EIN' in all_cols
            has_person = 'person_id' in all_cols
            has_slot = 'slot_type' in all_cols or 'slot_id' in all_cols

            results.append({
                'schema': schema,
                'table': table,
                'row_count': row_count,
                'pk': pk_str,
                'has_sovereign': has_sovereign,
                'has_outreach': has_outreach,
                'has_company_target': has_company_target,
                'has_dol': has_dol,
                'has_blog': has_blog,
                'has_people': has_people,
                'has_ein': has_ein,
                'has_person': has_person,
                'has_slot': has_slot,
                'columns': all_cols
            })

    # Output results
    print("=" * 100)
    print("CTB CONFORMANCE AUDIT - TABLE INVENTORY")
    print("=" * 100)

    print(f"\nTotal tables found: {len(results)}")

    # Print by schema
    current_schema = None
    for r in results:
        if r['schema'] != current_schema:
            current_schema = r['schema']
            print(f"\n[{current_schema}]")

        flags = []
        if r['has_sovereign']: flags.append('SID')
        if r['has_outreach']: flags.append('OID')
        if r['has_company_target']: flags.append('CT')
        if r['has_dol']: flags.append('DOL')
        if r['has_blog']: flags.append('BLOG')
        if r['has_people']: flags.append('PPL')
        if r['has_ein']: flags.append('EIN')
        if r['has_person']: flags.append('PER')
        if r['has_slot']: flags.append('SLOT')

        flag_str = f"[{','.join(flags)}]" if flags else ""
        print(f"  {r['table']}: {r['row_count']:,} rows | PK: {r['pk']} {flag_str}")

    # Write CSV for further analysis
    with open('docs/audit/ctb_inventory.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['schema', 'table', 'row_count', 'pk', 'has_sovereign', 'has_outreach',
                        'has_company_target', 'has_dol', 'has_blog', 'has_people', 'has_ein',
                        'has_person', 'has_slot', 'columns'])
        for r in results:
            writer.writerow([
                r['schema'], r['table'], r['row_count'], r['pk'],
                r['has_sovereign'], r['has_outreach'], r['has_company_target'],
                r['has_dol'], r['has_blog'], r['has_people'], r['has_ein'],
                r['has_person'], r['has_slot'], '|'.join(r['columns'])
            ])

    print(f"\n\nInventory written to docs/audit/ctb_inventory.csv")

    conn.close()

if __name__ == "__main__":
    main()
