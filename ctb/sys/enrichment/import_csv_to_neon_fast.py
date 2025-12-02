#!/usr/bin/env python3
"""
DOL Form 5500 Fast CSV Import to Neon PostgreSQL

Uses psycopg2 copy_expert for high-speed bulk loading.
Handles large files (230K, 759K, 336K records) efficiently.
"""

import os
import sys
from pathlib import Path
from io import StringIO
import pandas as pd
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

# Database connection
conn_string = os.getenv('DATABASE_URL') or os.getenv('NEON_CONNECTION_STRING')

# CSV file paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
CSV_FILES = {
    'form_5500': BASE_DIR / 'ctb' / 'sys' / 'enrichment' / 'output' / 'form_5500_2023_staging.csv',
    'form_5500_sf': BASE_DIR / 'output' / 'form_5500_sf_2023_staging.csv',
    'schedule_a': BASE_DIR / 'output' / 'schedule_a_2023_staging.csv'
}

STAGING_TABLES = {
    'form_5500': 'marketing.form_5500_staging',
    'form_5500_sf': 'marketing.form_5500_sf_staging',
    'schedule_a': 'marketing.schedule_a_staging'
}


def get_table_columns(cursor, table_name):
    """Get column names from staging table"""
    schema, table = table_name.split('.')
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """, (schema, table))
    return [row[0] for row in cursor.fetchall()]


def import_csv_fast(conn, csv_path, staging_table, table_key):
    """Import CSV using COPY command for maximum speed"""
    print(f"\nImporting {table_key}...")
    print(f"  File: {csv_path}")

    if not csv_path.exists():
        print(f"  ERROR: File not found!")
        return 0

    cursor = conn.cursor()

    # Get table columns
    table_cols = get_table_columns(cursor, staging_table)
    print(f"  Table columns: {len(table_cols)}")

    # Read CSV header to match columns
    df = pd.read_csv(csv_path, nrows=0)
    csv_cols = list(df.columns)
    print(f"  CSV columns: {len(csv_cols)}")

    # Find matching columns (case-insensitive)
    matching_cols = []
    for csv_col in csv_cols:
        for table_col in table_cols:
            if csv_col.lower() == table_col.lower():
                matching_cols.append((csv_col, table_col))
                break

    print(f"  Matching columns: {len(matching_cols)}")

    if len(matching_cols) == 0:
        print("  ERROR: No matching columns found!")
        return 0

    # Read full CSV with only matching columns
    csv_col_names = [m[0] for m in matching_cols]
    table_col_names = [m[1] for m in matching_cols]

    print(f"  Loading CSV into memory...")
    df = pd.read_csv(csv_path, usecols=csv_col_names, dtype=str, low_memory=False)

    # Rename to table column names
    rename_map = {m[0]: m[1] for m in matching_cols}
    df = df.rename(columns=rename_map)

    # Fill NaN with empty strings
    df = df.fillna('')

    print(f"  Rows to import: {len(df):,}")

    # Use StringIO buffer for COPY
    buffer = StringIO()
    df.to_csv(buffer, index=False, header=False)
    buffer.seek(0)

    # Build COPY command
    schema, table = staging_table.split('.')
    columns_sql = ', '.join([f'"{col}"' for col in table_col_names])
    copy_sql = f'COPY {staging_table} ({columns_sql}) FROM STDIN WITH CSV'

    print(f"  Executing COPY command...")
    try:
        cursor.copy_expert(copy_sql, buffer)
        conn.commit()
        print(f"  SUCCESS: {len(df):,} rows imported")
        return len(df)
    except Exception as e:
        conn.rollback()
        print(f"  ERROR: {e}")
        return 0


def main():
    print("=" * 80)
    print("DOL FORM 5500 FAST CSV IMPORT TO NEON POSTGRESQL")
    print("=" * 80)

    # Connect
    print("\nConnecting to Neon PostgreSQL...")
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    print("Connected!")

    # Clear staging tables
    print("\nClearing staging tables...")
    cursor.execute('TRUNCATE marketing.form_5500_staging')
    cursor.execute('TRUNCATE marketing.form_5500_sf_staging')
    cursor.execute('TRUNCATE marketing.schedule_a_staging')
    conn.commit()
    print("Staging tables cleared")

    # Import each CSV
    results = {}

    for key in ['form_5500', 'form_5500_sf', 'schedule_a']:
        results[key] = import_csv_fast(
            conn,
            CSV_FILES[key],
            STAGING_TABLES[key],
            key
        )

    # Summary
    print("\n" + "=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)
    print(f"Form 5500 (Large Plans):    {results['form_5500']:,} records")
    print(f"Form 5500-SF (Small Plans): {results['form_5500_sf']:,} records")
    print(f"Schedule A (Insurance):     {results['schedule_a']:,} records")
    total = sum(results.values())
    print(f"TOTAL:                      {total:,} records")

    # Verify counts
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    cursor.execute('SELECT COUNT(*) FROM marketing.form_5500_staging')
    print(f"form_5500_staging:    {cursor.fetchone()[0]:,} rows")

    cursor.execute('SELECT COUNT(*) FROM marketing.form_5500_sf_staging')
    print(f"form_5500_sf_staging: {cursor.fetchone()[0]:,} rows")

    cursor.execute('SELECT COUNT(*) FROM marketing.schedule_a_staging')
    print(f"schedule_a_staging:   {cursor.fetchone()[0]:,} rows")

    # Close
    cursor.close()
    conn.close()

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("""
1. Process staging tables (creates company matches, populates main tables):
   CALL marketing.process_5500_staging();
   CALL marketing.process_5500_sf_staging();
   CALL marketing.process_schedule_a_staging();

2. Verify main tables:
   SELECT COUNT(*) FROM marketing.form_5500;
   SELECT COUNT(*) FROM marketing.form_5500_sf;
   SELECT COUNT(*) FROM marketing.schedule_a;

3. Check hub-and-spoke joins:
   SELECT f.sponsor_dfe_name, COUNT(a.ack_id) as insurance_contracts
   FROM marketing.form_5500 f
   JOIN marketing.schedule_a a ON f.ack_id = a.ack_id
   GROUP BY f.sponsor_dfe_name
   ORDER BY insurance_contracts DESC
   LIMIT 10;
""")

    print("=" * 80)
    print("IMPORT COMPLETE!")
    print("=" * 80)


if __name__ == '__main__':
    main()
