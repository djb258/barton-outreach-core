#!/usr/bin/env python3
"""
DOL Full Data Import Script

Imports ALL columns from Form 5500, Form 5500-SF, and Schedule A datasets
into the Neon PostgreSQL dol schema.

This script dynamically reads all columns from the CSV files and creates
corresponding database columns.
"""

import pandas as pd
import psycopg2
from psycopg2 import sql
import os
import sys
import argparse
from pathlib import Path
import logging
from datetime import datetime
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_connection():
    """Get database connection from environment variables."""
    conn_string = os.getenv('DATABASE_URL') or os.getenv('NEON_CONNECTION_STRING')
    if not conn_string:
        host = os.getenv('NEON_HOST')
        database = os.getenv('NEON_DATABASE')
        user = os.getenv('NEON_USER')
        password = os.getenv('NEON_PASSWORD')
        if not all([host, database, user, password]):
            raise ValueError("Database connection not configured")
        conn_string = f"postgresql://{user}:{password}@{host}:5432/{database}?sslmode=require"
    return psycopg2.connect(conn_string)


def normalize_column_name(col: str) -> str:
    """Convert DOL column name to PostgreSQL-friendly name."""
    # Lowercase and replace spaces/special chars with underscore
    col = col.lower().strip()
    col = re.sub(r'[^a-z0-9_]', '_', col)
    col = re.sub(r'_+', '_', col)  # Remove duplicate underscores
    col = col.strip('_')
    # Ensure doesn't start with number
    if col[0].isdigit():
        col = 'col_' + col
    return col


def infer_pg_type(series: pd.Series, col_name: str) -> str:
    """Infer PostgreSQL type from pandas series."""
    # Check for common patterns in column names
    col_lower = col_name.lower()

    if '_amt' in col_lower or '_cnt' in col_lower:
        return 'NUMERIC'
    if '_ind' in col_lower:
        return 'VARCHAR(5)'
    if '_date' in col_lower:
        return 'VARCHAR(30)'
    if '_ein' in col_lower:
        return 'VARCHAR(20)'
    if '_zip' in col_lower:
        return 'VARCHAR(20)'
    if '_phone' in col_lower:
        return 'VARCHAR(30)'
    if '_code' in col_lower:
        return 'VARCHAR(50)'
    if '_text' in col_lower:
        return 'TEXT'
    if '_name' in col_lower:
        return 'VARCHAR(255)'
    if '_address' in col_lower:
        return 'VARCHAR(255)'
    if '_city' in col_lower:
        return 'VARCHAR(100)'
    if '_state' in col_lower:
        return 'VARCHAR(10)'

    # Default to VARCHAR(255) for most text
    return 'VARCHAR(255)'


def ensure_columns_exist(cur, conn, table_name: str, df: pd.DataFrame, schema: str = 'dol'):
    """Ensure all DataFrame columns exist in the database table."""
    # Get existing columns
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
    """, (schema, table_name))
    existing_cols = {row[0] for row in cur.fetchall()}

    # Add missing columns
    for col in df.columns:
        pg_col = normalize_column_name(col)
        if pg_col not in existing_cols:
            pg_type = infer_pg_type(df[col], col)
            try:
                cur.execute(f'ALTER TABLE {schema}.{table_name} ADD COLUMN IF NOT EXISTS {pg_col} {pg_type}')
                logger.debug(f'Added column {pg_col} ({pg_type})')
            except Exception as e:
                logger.warning(f'Could not add column {pg_col}: {e}')
                conn.rollback()

    conn.commit()


def import_full_table(csv_path: Path, table_name: str, year: str = "2023",
                      batch_size: int = 1000, schema: str = 'dol') -> dict:
    """
    Import ALL columns from CSV into database table.

    Args:
        csv_path: Path to CSV file
        table_name: Target table name
        year: Form year
        batch_size: Rows per batch
        schema: Database schema

    Returns:
        Dict with import statistics
    """
    logger.info(f"Loading {csv_path.name}...")

    # Read CSV with all columns as strings initially
    df = pd.read_csv(csv_path, dtype=str, low_memory=False)
    logger.info(f"Loaded {len(df):,} rows, {len(df.columns)} columns")

    # Strip whitespace from all string columns
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()

    # Add form_year column
    df['FORM_YEAR'] = year

    # Normalize column names
    df.columns = [normalize_column_name(c) for c in df.columns]

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Enable DOL import mode to bypass read-only triggers
        logger.info("Enabling DOL import mode (bypassing read-only lock)...")
        cur.execute("SET session dol.import_mode = 'active'")
        conn.commit()

        # Ensure all columns exist in database
        logger.info(f"Ensuring columns exist in {schema}.{table_name}...")
        ensure_columns_exist(cur, conn, table_name, df, schema)

        # Clear existing data for this year
        logger.info(f"Clearing existing {year} data...")
        cur.execute(f"DELETE FROM {schema}.{table_name} WHERE form_year = %s", (year,))
        conn.commit()

        # Get list of columns to insert (only those that exist in table)
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
        """, (schema, table_name))
        db_cols = {row[0] for row in cur.fetchall()}

        # Filter to columns that exist in both DataFrame and database
        insert_cols = [c for c in df.columns if c in db_cols]
        logger.info(f"Inserting {len(insert_cols)} columns")

        # Batch insert
        total_inserted = 0
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size][insert_cols]

            if len(batch) == 0:
                continue

            # Build INSERT statement
            cols_str = ', '.join(insert_cols)
            placeholders = ', '.join(['%s'] * len(insert_cols))

            # Prepare values
            values_list = []
            for _, row in batch.iterrows():
                values = []
                for c in insert_cols:
                    val = row[c]
                    if pd.isna(val) or val == '':
                        values.append(None)
                    else:
                        values.append(val)
                values_list.append(values)

            # Execute batch insert
            args_str = ','.join(
                cur.mogrify(f"({placeholders})", tuple(v)).decode('utf-8')
                for v in values_list
            )

            cur.execute(f"INSERT INTO {schema}.{table_name} ({cols_str}) VALUES {args_str}")
            total_inserted += len(batch)

            conn.commit()

            if total_inserted % 25000 == 0:
                logger.info(f"Progress: {total_inserted:,} rows")

        logger.info(f"Completed: {total_inserted:,} rows inserted")

        # Verify
        cur.execute(f"SELECT COUNT(*) FROM {schema}.{table_name} WHERE form_year = %s", (year,))
        final_count = cur.fetchone()[0]

        return {
            'table': f'{schema}.{table_name}',
            'rows_loaded': total_inserted,
            'rows_in_table': final_count,
            'columns': len(insert_cols),
            'year': year
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"Error: {e}")
        raise
    finally:
        # Always reset import mode to restore read-only lock
        try:
            cur.execute("RESET dol.import_mode")
            conn.commit()
            logger.info("DOL import mode disabled (read-only lock restored)")
        except Exception:
            pass  # Connection may already be closed
        cur.close()
        conn.close()


def link_schedule_a_to_forms(year: str = "2023"):
    """Link Schedule A to Form 5500 via ACK_ID and populate sponsor info."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Enable DOL import mode to bypass read-only triggers
        cur.execute("SET session dol.import_mode = 'active'")
        conn.commit()

        logger.info("Linking Schedule A to Form 5500...")

        # Ensure linking columns exist
        cur.execute("ALTER TABLE dol.schedule_a ADD COLUMN IF NOT EXISTS filing_id UUID")
        cur.execute("ALTER TABLE dol.schedule_a ADD COLUMN IF NOT EXISTS sponsor_state VARCHAR(10)")
        cur.execute("ALTER TABLE dol.schedule_a ADD COLUMN IF NOT EXISTS sponsor_name VARCHAR(255)")
        conn.commit()

        # Update filing_id from form_5500
        cur.execute("""
            UPDATE dol.schedule_a sa
            SET filing_id = f5.filing_id,
                sponsor_state = f5.spons_dfe_mail_us_state,
                sponsor_name = f5.sponsor_dfe_name
            FROM dol.form_5500 f5
            WHERE sa.ack_id = f5.ack_id
              AND sa.form_year = %s
        """, (year,))
        updated = cur.rowcount
        conn.commit()

        logger.info(f"Linked {updated:,} Schedule A records to Form 5500")

        return updated

    finally:
        # Restore read-only lock
        try:
            cur.execute("RESET dol.import_mode")
            conn.commit()
        except Exception:
            pass
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Import FULL DOL data")
    parser.add_argument('--data-dir', type=str, required=True,
                       help='Directory containing DOL CSV files')
    parser.add_argument('--year', type=str, default='2023',
                       help='Form year')
    parser.add_argument('--table', type=str,
                       choices=['form_5500', 'form_5500_sf', 'schedule_a', 'all'],
                       default='all', help='Which table(s) to import')
    parser.add_argument('--batch-size', type=int, default=1000,
                       help='Batch size for inserts')

    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        sys.exit(1)

    results = []

    # Import Form 5500
    if args.table in ['form_5500', 'all']:
        csv_path = data_dir / 'f_5500_2023_latest.csv'
        if csv_path.exists():
            result = import_full_table(csv_path, 'form_5500', args.year, args.batch_size)
            results.append(result)

    # Import Form 5500-SF
    if args.table in ['form_5500_sf', 'all']:
        csv_path = data_dir / 'f_5500_sf_2023_latest.csv'
        if csv_path.exists():
            result = import_full_table(csv_path, 'form_5500_sf', args.year, args.batch_size)
            results.append(result)

    # Import Schedule A
    if args.table in ['schedule_a', 'all']:
        csv_path = data_dir / 'F_SCH_A_2023_latest.csv'
        if csv_path.exists():
            result = import_full_table(csv_path, 'schedule_a', args.year, args.batch_size)
            results.append(result)

            # Link to Form 5500
            link_schedule_a_to_forms(args.year)

    # Summary
    print("\n" + "=" * 70)
    print("FULL IMPORT SUMMARY")
    print("=" * 70)
    for r in results:
        print(f"\n{r['table']}:")
        print(f"  Year: {r['year']}")
        print(f"  Columns: {r['columns']}")
        print(f"  Rows loaded: {r['rows_loaded']:,}")
        print(f"  Rows in table: {r['rows_in_table']:,}")
    print("=" * 70)


if __name__ == "__main__":
    main()
