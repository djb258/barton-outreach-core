"""
Schema Export Script - Barton Outreach Core
Exports table schemas to CSV files for mapping purposes.

Usage:
    doppler run -- python scripts/export_schema_to_csv.py
"""

import os
import csv
import psycopg2
from pathlib import Path

# Table definitions: (schema_name, table_name, output_prefix)
TABLES = [
    ('outreach', 'outreach', '01_outreach_outreach'),
    ('outreach', 'company_target', '02_outreach_company_target'),
    ('outreach', 'dol', '03_outreach_dol'),
    ('outreach', 'blog', '04_outreach_blog'),
    ('outreach', 'people', '05_outreach_people'),
    ('people', 'company_slot', '06_people_company_slot'),
    ('people', 'people_master', '07_people_people_master'),
    ('enrichment', 'hunter_company', '08_enrichment_hunter_company'),
    ('enrichment', 'hunter_contact', '09_enrichment_hunter_contact'),
]

# Output directory
OUTPUT_DIR = Path(r"C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\docs\schema_csv")

# CSV headers
CSV_HEADERS = [
    'schema_name',
    'table_name',
    'column_name',
    'data_type',
    'is_nullable',
    'column_default',
    'description'
]

def get_database_url():
    """Get DATABASE_URL from environment."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set. Use Doppler to run this script.")
    return db_url

def fetch_table_schema(conn, schema_name, table_name):
    """
    Fetch schema information for a specific table.

    Returns:
        List of tuples: (schema_name, table_name, column_name, data_type,
                        is_nullable, column_default, description)
    """
    query = """
    SELECT
        c.table_schema,
        c.table_name,
        c.column_name,
        c.data_type,
        c.is_nullable,
        c.column_default,
        COALESCE(pgd.description, '') as description
    FROM information_schema.columns c
    LEFT JOIN pg_catalog.pg_statio_all_tables st
        ON c.table_schema = st.schemaname AND c.table_name = st.relname
    LEFT JOIN pg_catalog.pg_description pgd
        ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
    WHERE c.table_schema = %s AND c.table_name = %s
    ORDER BY c.ordinal_position;
    """

    with conn.cursor() as cur:
        cur.execute(query, (schema_name, table_name))
        return cur.fetchall()

def write_csv(file_path, rows):
    """Write rows to CSV file."""
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        writer.writerows(rows)
    print(f"[OK] Created: {file_path.name} ({len(rows)} columns)")

def main():
    """Main execution function."""
    print("=" * 80)
    print("SCHEMA EXPORT SCRIPT - Barton Outreach Core")
    print("=" * 80)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {OUTPUT_DIR}")

    # Connect to database
    db_url = get_database_url()
    print("\nConnecting to Neon PostgreSQL...")

    all_rows = []

    try:
        with psycopg2.connect(db_url) as conn:
            print("[OK] Connected successfully\n")

            # Process each table
            for schema_name, table_name, output_prefix in TABLES:
                print(f"Processing {schema_name}.{table_name}...")

                try:
                    # Fetch schema
                    rows = fetch_table_schema(conn, schema_name, table_name)

                    if not rows:
                        print(f"  [WARN] No columns found for {schema_name}.{table_name}")
                        continue

                    # Write individual CSV
                    output_file = OUTPUT_DIR / f"{output_prefix}.csv"
                    write_csv(output_file, rows)

                    # Add to combined list
                    all_rows.extend(rows)

                except Exception as e:
                    print(f"  [ERROR] Error processing {schema_name}.{table_name}: {e}")
                    continue

            # Write combined CSV
            if all_rows:
                print("\nCreating combined schema file...")
                combined_file = OUTPUT_DIR / "all_tables_schema.csv"
                write_csv(combined_file, all_rows)

            print("\n" + "=" * 80)
            print("EXPORT COMPLETE")
            print("=" * 80)
            print(f"\nTotal tables processed: {len(TABLES)}")
            print(f"Total columns exported: {len(all_rows)}")
            print(f"\nFiles saved to: {OUTPUT_DIR}")

    except psycopg2.Error as e:
        print(f"\n[ERROR] Database error: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
