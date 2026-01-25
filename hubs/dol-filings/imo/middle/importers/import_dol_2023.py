#!/usr/bin/env python3
"""
DOL 2023 Data Import Script

Imports Form 5500, Form 5500-SF, and Schedule A data from DOL EFAST2 datasets
into the Neon PostgreSQL dol schema.

Data Source: https://www.dol.gov/agencies/ebsa/about-ebsa/our-activities/public-disclosure/foia/form-5500-datasets
"""

import pandas as pd
import psycopg2
from psycopg2 import sql
import os
import sys
import argparse
from pathlib import Path
from io import StringIO
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_connection():
    """Get database connection from environment variables."""
    conn_string = os.getenv('DATABASE_URL') or os.getenv('NEON_CONNECTION_STRING')

    if not conn_string:
        host = os.getenv('NEON_HOST')
        database = os.getenv('NEON_DATABASE')
        user = os.getenv('NEON_USER')
        password = os.getenv('NEON_PASSWORD')

        if not all([host, database, user, password]):
            raise ValueError("Database connection not configured. Set DATABASE_URL or NEON_* env vars")

        conn_string = f"postgresql://{user}:{password}@{host}:5432/{database}?sslmode=require"

    return psycopg2.connect(conn_string)

# =============================================================================
# FORM 5500 IMPORT (Large Plans)
# =============================================================================

def import_form_5500(csv_path: Path, year: str = "2023", batch_size: int = 5000) -> dict:
    """
    Import Form 5500 data into dol.form_5500 table.

    Args:
        csv_path: Path to the CSV file
        year: Form year
        batch_size: Number of rows per batch insert

    Returns:
        Dict with import statistics
    """
    logger.info(f"Loading Form 5500 from {csv_path}...")

    # Column mapping: DOL CSV -> Neon schema
    column_mapping = {
        'ACK_ID': 'ack_id',
        'SPONS_DFE_EIN': 'sponsor_dfe_ein',
        'SPONSOR_DFE_NAME': 'sponsor_dfe_name',
        'SPONS_DFE_DBA_NAME': 'spons_dfe_dba_name',
        'PLAN_NAME': 'plan_name',
        'SPONS_DFE_PN': 'plan_number',
        'PLAN_EFF_DATE': 'plan_eff_date',
        'SPONS_DFE_MAIL_US_CITY': 'spons_dfe_mail_us_city',
        'SPONS_DFE_MAIL_US_STATE': 'spons_dfe_mail_us_state',
        'SPONS_DFE_MAIL_US_ZIP': 'spons_dfe_mail_us_zip',
        'TOT_ACTIVE_PARTCP_CNT': 'tot_active_partcp_cnt',
        'TOT_PARTCP_BOY_CNT': 'tot_partcp_boy_cnt',
        'SCH_A_ATTACHED_IND': 'sch_a_attached_ind',
        'NUM_SCH_A_ATTACHED_CNT': 'num_sch_a_attached_cnt',
        'ADMIN_NAME': 'admin_name',
        'ADMIN_EIN': 'admin_ein',
        'FORM_PLAN_YEAR_BEGIN_DATE': 'form_plan_year_begin_date',
        'FILING_STATUS': 'filing_status',
        'DATE_RECEIVED': 'date_received',
    }

    # Read CSV
    df = pd.read_csv(csv_path, dtype=str, low_memory=False)
    logger.info(f"Loaded {len(df):,} rows from CSV")

    # Strip whitespace
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Select and rename columns
    available_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
    df_import = df[list(available_cols.keys())].rename(columns=available_cols)

    # Add form_year
    df_import['form_year'] = year

    # Convert numeric columns
    numeric_cols = ['tot_active_partcp_cnt', 'tot_partcp_boy_cnt', 'num_sch_a_attached_cnt']
    for col in numeric_cols:
        if col in df_import.columns:
            df_import[col] = pd.to_numeric(df_import[col], errors='coerce')

    # Filter out rows without EIN
    df_import = df_import[df_import['sponsor_dfe_ein'].notna() & (df_import['sponsor_dfe_ein'] != '')]
    logger.info(f"After filtering: {len(df_import):,} rows with valid EIN")

    # Connect and import
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Clear existing data for this year
        logger.info(f"Clearing existing {year} data from dol.form_5500...")
        cur.execute("DELETE FROM dol.form_5500 WHERE form_year = %s", (year,))
        conn.commit()

        # Insert columns
        insert_cols = ['ack_id', 'sponsor_dfe_ein', 'sponsor_dfe_name', 'spons_dfe_dba_name',
                      'plan_name', 'plan_number', 'plan_eff_date', 'spons_dfe_mail_us_city',
                      'spons_dfe_mail_us_state', 'spons_dfe_mail_us_zip', 'tot_active_partcp_cnt',
                      'tot_partcp_boy_cnt', 'sch_a_attached_ind', 'num_sch_a_attached_cnt',
                      'admin_name', 'admin_ein', 'form_plan_year_begin_date', 'form_year',
                      'filing_status', 'date_received']

        # Filter to available columns
        insert_cols = [c for c in insert_cols if c in df_import.columns]

        # Batch insert
        total_inserted = 0
        for i in range(0, len(df_import), batch_size):
            batch = df_import.iloc[i:i+batch_size][insert_cols]

            # Create VALUES placeholders
            values_list = []
            params = []
            for _, row in batch.iterrows():
                placeholders = ', '.join(['%s'] * len(insert_cols))
                values_list.append(f"({placeholders})")
                params.extend([row[c] if pd.notna(row[c]) else None for c in insert_cols])

            if values_list:
                insert_sql = f"""
                    INSERT INTO dol.form_5500 ({', '.join(insert_cols)})
                    VALUES {', '.join(values_list)}
                    ON CONFLICT (ack_id) DO UPDATE SET
                        sponsor_dfe_ein = EXCLUDED.sponsor_dfe_ein,
                        sponsor_dfe_name = EXCLUDED.sponsor_dfe_name,
                        updated_at = NOW()
                """
                cur.execute(insert_sql, params)
                total_inserted += len(batch)

            if (i + batch_size) % 50000 == 0:
                conn.commit()
                logger.info(f"Progress: {total_inserted:,} rows inserted")

        conn.commit()
        logger.info(f"Completed: {total_inserted:,} rows inserted into dol.form_5500")

        # Verify
        cur.execute("SELECT COUNT(*) FROM dol.form_5500 WHERE form_year = %s", (year,))
        final_count = cur.fetchone()[0]

        return {
            'table': 'dol.form_5500',
            'rows_loaded': total_inserted,
            'rows_in_table': final_count,
            'year': year
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"Error importing Form 5500: {e}")
        raise
    finally:
        cur.close()
        conn.close()

# =============================================================================
# FORM 5500-SF IMPORT (Small Plans)
# =============================================================================

def import_form_5500_sf(csv_path: Path, year: str = "2023", batch_size: int = 5000) -> dict:
    """
    Import Form 5500-SF data into dol.form_5500_sf table.

    Args:
        csv_path: Path to the CSV file
        year: Form year
        batch_size: Number of rows per batch insert

    Returns:
        Dict with import statistics
    """
    logger.info(f"Loading Form 5500-SF from {csv_path}...")

    # Column mapping: DOL CSV -> Neon schema
    column_mapping = {
        'ACK_ID': 'ack_id',
        'SF_SPONS_EIN': 'sponsor_dfe_ein',
        'SF_SPONSOR_NAME': 'sponsor_dfe_name',
        'SF_SPONSOR_DFE_DBA_NAME': 'spons_dfe_dba_name',
        'SF_PLAN_NAME': 'plan_name',
        'SF_PLAN_NUM': 'plan_number',
        'SF_PLAN_EFF_DATE': 'plan_eff_date',
        'SF_SPONS_US_CITY': 'spons_dfe_mail_us_city',
        'SF_SPONS_US_STATE': 'spons_dfe_mail_us_state',
        'SF_SPONS_US_ZIP': 'spons_dfe_mail_us_zip',
        'SF_TOT_PARTCP_BOY_CNT': 'tot_partcp_boy_cnt',
        'SF_PLAN_YEAR_BEGIN_DATE': 'form_plan_year_begin_date',
        'FILING_STATUS': 'filing_status',
    }

    # Read CSV
    df = pd.read_csv(csv_path, dtype=str, low_memory=False)
    logger.info(f"Loaded {len(df):,} rows from CSV")

    # Strip whitespace
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Select and rename columns
    available_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
    df_import = df[list(available_cols.keys())].rename(columns=available_cols)

    # Add form_year
    df_import['form_year'] = year

    # Convert numeric columns
    if 'tot_partcp_boy_cnt' in df_import.columns:
        df_import['tot_partcp_boy_cnt'] = pd.to_numeric(df_import['tot_partcp_boy_cnt'], errors='coerce')

    # Filter out rows without EIN
    df_import = df_import[df_import['sponsor_dfe_ein'].notna() & (df_import['sponsor_dfe_ein'] != '')]
    logger.info(f"After filtering: {len(df_import):,} rows with valid EIN")

    # Connect and import
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Clear existing data for this year
        logger.info(f"Clearing existing {year} data from dol.form_5500_sf...")
        cur.execute("DELETE FROM dol.form_5500_sf WHERE form_year = %s", (year,))
        conn.commit()

        # Insert columns
        insert_cols = ['ack_id', 'sponsor_dfe_ein', 'sponsor_dfe_name', 'spons_dfe_dba_name',
                      'plan_name', 'plan_number', 'plan_eff_date', 'spons_dfe_mail_us_city',
                      'spons_dfe_mail_us_state', 'spons_dfe_mail_us_zip', 'tot_partcp_boy_cnt',
                      'form_plan_year_begin_date', 'form_year', 'filing_status']

        # Filter to available columns
        insert_cols = [c for c in insert_cols if c in df_import.columns]

        # Batch insert
        total_inserted = 0
        for i in range(0, len(df_import), batch_size):
            batch = df_import.iloc[i:i+batch_size][insert_cols]

            # Create VALUES placeholders
            values_list = []
            params = []
            for _, row in batch.iterrows():
                placeholders = ', '.join(['%s'] * len(insert_cols))
                values_list.append(f"({placeholders})")
                params.extend([row[c] if pd.notna(row[c]) else None for c in insert_cols])

            if values_list:
                insert_sql = f"""
                    INSERT INTO dol.form_5500_sf ({', '.join(insert_cols)})
                    VALUES {', '.join(values_list)}
                    ON CONFLICT (ack_id) DO UPDATE SET
                        sponsor_dfe_ein = EXCLUDED.sponsor_dfe_ein,
                        sponsor_dfe_name = EXCLUDED.sponsor_dfe_name,
                        updated_at = NOW()
                """
                cur.execute(insert_sql, params)
                total_inserted += len(batch)

            # Commit more frequently to avoid timeouts
            conn.commit()
            if total_inserted % 25000 == 0:
                logger.info(f"Progress: {total_inserted:,} rows inserted")

        logger.info(f"Completed: {total_inserted:,} rows inserted into dol.form_5500_sf")

        # Verify
        cur.execute("SELECT COUNT(*) FROM dol.form_5500_sf WHERE form_year = %s", (year,))
        final_count = cur.fetchone()[0]

        return {
            'table': 'dol.form_5500_sf',
            'rows_loaded': total_inserted,
            'rows_in_table': final_count,
            'year': year
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"Error importing Form 5500-SF: {e}")
        raise
    finally:
        cur.close()
        conn.close()

# =============================================================================
# SCHEDULE A IMPORT
# =============================================================================

def import_schedule_a(csv_path: Path, year: str = "2023", batch_size: int = 5000) -> dict:
    """
    Import Schedule A data into dol.schedule_a table.

    Args:
        csv_path: Path to the CSV file
        year: Form year
        batch_size: Number of rows per batch insert

    Returns:
        Dict with import statistics
    """
    logger.info(f"Loading Schedule A from {csv_path}...")

    # Column mapping: DOL CSV -> Neon schema
    column_mapping = {
        'ACK_ID': 'ack_id',
        'SCH_A_EIN': 'sponsor_ein',  # Plan sponsor EIN - links to Form 5500
        'INS_CARRIER_NAME': 'insurance_company_name',
        'INS_CARRIER_EIN': 'insurance_company_ein',
        'INS_CONTRACT_NUM': 'contract_number',
        'INS_PRSN_COVERED_EOY_CNT': 'covered_lives',
        'INS_POLICY_FROM_DATE': 'policy_year_begin_date',
        'INS_POLICY_TO_DATE': 'policy_year_end_date',
        'SCH_A_PLAN_YEAR_BEGIN_DATE': 'sch_a_plan_year_begin_date',
        'SCH_A_PLAN_YEAR_END_DATE': 'sch_a_plan_year_end_date',
    }

    # Read CSV
    df = pd.read_csv(csv_path, dtype=str, low_memory=False)
    logger.info(f"Loaded {len(df):,} rows from CSV")

    # Strip whitespace
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Select and rename columns
    available_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
    df_import = df[list(available_cols.keys())].rename(columns=available_cols)

    # Add form_year
    df_import['form_year'] = year

    # Convert numeric columns
    if 'covered_lives' in df_import.columns:
        df_import['covered_lives'] = pd.to_numeric(df_import['covered_lives'], errors='coerce')

    # Filter out rows without ACK_ID
    df_import = df_import[df_import['ack_id'].notna() & (df_import['ack_id'] != '')]
    logger.info(f"After filtering: {len(df_import):,} rows with valid ACK_ID")

    # Connect and import
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Clear existing data for this year
        logger.info(f"Clearing existing {year} data from dol.schedule_a...")
        cur.execute("DELETE FROM dol.schedule_a WHERE form_year = %s", (year,))
        conn.commit()

        # Insert columns
        insert_cols = ['ack_id', 'sponsor_ein', 'insurance_company_name', 'insurance_company_ein',
                      'contract_number', 'covered_lives', 'policy_year_begin_date',
                      'policy_year_end_date', 'sch_a_plan_year_begin_date',
                      'sch_a_plan_year_end_date', 'form_year']

        # Filter to available columns
        insert_cols = [c for c in insert_cols if c in df_import.columns]

        # Batch insert
        total_inserted = 0
        for i in range(0, len(df_import), batch_size):
            batch = df_import.iloc[i:i+batch_size][insert_cols]

            # Create VALUES placeholders
            values_list = []
            params = []
            for _, row in batch.iterrows():
                placeholders = ', '.join(['%s'] * len(insert_cols))
                values_list.append(f"({placeholders})")
                params.extend([row[c] if pd.notna(row[c]) else None for c in insert_cols])

            if values_list:
                # Schedule A can have multiple entries per ACK_ID, so no ON CONFLICT
                insert_sql = f"""
                    INSERT INTO dol.schedule_a ({', '.join(insert_cols)})
                    VALUES {', '.join(values_list)}
                """
                cur.execute(insert_sql, params)
                total_inserted += len(batch)

            # Commit more frequently to avoid timeouts
            conn.commit()
            if total_inserted % 25000 == 0:
                logger.info(f"Progress: {total_inserted:,} rows inserted")

        logger.info(f"Completed: {total_inserted:,} rows inserted into dol.schedule_a")

        # Verify
        cur.execute("SELECT COUNT(*) FROM dol.schedule_a WHERE form_year = %s", (year,))
        final_count = cur.fetchone()[0]

        return {
            'table': 'dol.schedule_a',
            'rows_loaded': total_inserted,
            'rows_in_table': final_count,
            'year': year
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"Error importing Schedule A: {e}")
        raise
    finally:
        cur.close()
        conn.close()

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Import DOL 2023 data into Neon")
    parser.add_argument('--data-dir', type=str,
                       default='data/dol_2023',
                       help='Directory containing DOL CSV files')
    parser.add_argument('--year', type=str, default='2023',
                       help='Form year')
    parser.add_argument('--table', type=str, choices=['form_5500', 'form_5500_sf', 'schedule_a', 'all'],
                       default='all', help='Which table(s) to import')
    parser.add_argument('--batch-size', type=int, default=5000,
                       help='Batch size for inserts')

    args = parser.parse_args()

    # Find data directory
    script_dir = Path(__file__).parent.parent.parent.parent.parent
    data_dir = script_dir / args.data_dir

    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        sys.exit(1)

    results = []

    # Import Form 5500
    if args.table in ['form_5500', 'all']:
        csv_path = data_dir / 'f_5500_2023_latest.csv'
        if csv_path.exists():
            result = import_form_5500(csv_path, args.year, args.batch_size)
            results.append(result)
        else:
            logger.warning(f"Form 5500 CSV not found: {csv_path}")

    # Import Form 5500-SF
    if args.table in ['form_5500_sf', 'all']:
        csv_path = data_dir / 'f_5500_sf_2023_latest.csv'
        if csv_path.exists():
            result = import_form_5500_sf(csv_path, args.year, args.batch_size)
            results.append(result)
        else:
            logger.warning(f"Form 5500-SF CSV not found: {csv_path}")

    # Import Schedule A
    if args.table in ['schedule_a', 'all']:
        csv_path = data_dir / 'F_SCH_A_2023_latest.csv'
        if csv_path.exists():
            result = import_schedule_a(csv_path, args.year, args.batch_size)
            results.append(result)
        else:
            logger.warning(f"Schedule A CSV not found: {csv_path}")

    # Summary
    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    for r in results:
        print(f"\n{r['table']}:")
        print(f"  Year: {r['year']}")
        print(f"  Rows loaded: {r['rows_loaded']:,}")
        print(f"  Rows in table: {r['rows_in_table']:,}")
    print("=" * 60)

if __name__ == "__main__":
    main()
