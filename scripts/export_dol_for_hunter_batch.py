#!/usr/bin/env python3
"""
DOL Export for Hunter.io - Batch CSV Generator

Exports Form 5500 and 5500-SF filings from 8 target states for Hunter.io domain enrichment.
Excludes EINs already matched (in dol.ein_urls or outreach.dol).

Output: Multiple CSV files with max 24,000 rows each (Hunter.io limit is 25,000)

Target States: WV, VA, MD, OH, PA, KY, NC, DC
"""

import os
import sys
import csv
import math
import logging
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Target states for DOL enrichment
TARGET_STATES = ['WV', 'VA', 'MD', 'OH', 'PA', 'KY', 'NC', 'DC']

# Hunter.io limit is 25,000 - using 24,000 for safety
ROWS_PER_FILE = 24000

# Output directory
OUTPUT_DIR = Path(r"C:\Users\CUSTOM PC\Desktop\dol-hunter-exports")


def get_db_connection():
    """Get Neon database connection."""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )


def get_unmatched_dol_records(conn) -> list:
    """
    Get DOL filings that need Hunter.io enrichment.

    Excludes:
    - EINs already in dol.ein_urls (already have URLs)
    - EINs already linked in outreach.dol (already matched to outreach)

    Returns combined records from both Form 5500 and 5500-SF.
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Query Form 5500 (full form) - larger plans
        logger.info("Querying Form 5500 records...")
        cur.execute("""
            SELECT DISTINCT ON (f.sponsor_dfe_ein)
                f.ack_id,
                f.filing_id,
                f.sponsor_dfe_ein as ein,
                f.sponsor_dfe_name as company_name,
                f.spons_dfe_mail_us_address1 as address,
                f.spons_dfe_mail_us_city as city,
                f.spons_dfe_mail_us_state as state,
                f.spons_dfe_mail_us_zip as zip,
                f.spons_dfe_phone_num as phone,
                '5500' as form_type,
                f.tot_active_partcp_cnt as participant_count
            FROM dol.form_5500 f
            LEFT JOIN outreach.dol od ON f.sponsor_dfe_ein = od.ein
            WHERE f.spons_dfe_mail_us_state IN %s
              AND od.ein IS NULL
              AND f.sponsor_dfe_ein IS NOT NULL
              AND f.sponsor_dfe_ein != ''
              AND f.sponsor_dfe_name IS NOT NULL
            ORDER BY f.sponsor_dfe_ein, f.form_year DESC
        """, (tuple(TARGET_STATES),))
        form_5500_records = cur.fetchall()
        logger.info(f"  Found {len(form_5500_records):,} unmatched Form 5500 records")

        # Query Form 5500-SF (short form) - smaller plans
        logger.info("Querying Form 5500-SF records...")
        cur.execute("""
            SELECT DISTINCT ON (sf.sf_spons_ein)
                sf.ack_id,
                sf.filing_id,
                sf.sf_spons_ein as ein,
                sf.sf_sponsor_name as company_name,
                sf.sf_spons_us_address1 as address,
                sf.sf_spons_us_city as city,
                sf.sf_spons_us_state as state,
                sf.sf_spons_us_zip as zip,
                sf.sf_spons_phone_num as phone,
                '5500-SF' as form_type,
                sf.sf_tot_partcp_boy_cnt as participant_count
            FROM dol.form_5500_sf sf
            LEFT JOIN outreach.dol od ON sf.sf_spons_ein = od.ein
            WHERE sf.sf_spons_us_state IN %s
              AND od.ein IS NULL
              AND sf.sf_spons_ein IS NOT NULL
              AND sf.sf_spons_ein != ''
              AND sf.sf_sponsor_name IS NOT NULL
            ORDER BY sf.sf_spons_ein, sf.form_year DESC
        """, (tuple(TARGET_STATES),))
        form_5500_sf_records = cur.fetchall()
        logger.info(f"  Found {len(form_5500_sf_records):,} unmatched Form 5500-SF records")

        # Combine and deduplicate by EIN (prefer 5500 over 5500-SF)
        logger.info("Deduplicating by EIN...")
        seen_eins = set()
        combined = []

        # Add 5500 first (larger plans, higher priority)
        for record in form_5500_records:
            ein = record['ein']
            if ein not in seen_eins:
                seen_eins.add(ein)
                combined.append(dict(record))

        # Add 5500-SF that weren't in 5500
        for record in form_5500_sf_records:
            ein = record['ein']
            if ein not in seen_eins:
                seen_eins.add(ein)
                combined.append(dict(record))

        logger.info(f"  Total unique EINs: {len(combined):,}")

        return combined


def export_to_csv_batches(records: list, output_dir: Path) -> list:
    """
    Export records to multiple CSV files (24,000 rows each).

    Returns list of created file paths.
    """

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    total_records = len(records)
    num_files = math.ceil(total_records / ROWS_PER_FILE)

    logger.info(f"Exporting {total_records:,} records to {num_files} CSV files...")

    # CSV columns - ack_id and filing_id for matching, rest for Hunter.io
    fieldnames = ['ack_id', 'filing_id', 'ein', 'company_name', 'address', 'city', 'state', 'zip', 'phone']

    created_files = []
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    for batch_num in range(num_files):
        start_idx = batch_num * ROWS_PER_FILE
        end_idx = min(start_idx + ROWS_PER_FILE, total_records)
        batch_records = records[start_idx:end_idx]

        filename = f"dol_hunter_batch_{batch_num + 1:02d}_{timestamp}.csv"
        filepath = output_dir / filename

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(batch_records)

        created_files.append(filepath)
        logger.info(f"  Created {filename} ({len(batch_records):,} records)")

    return created_files


def print_state_breakdown(records: list):
    """Print breakdown by state."""

    state_counts = {}
    for record in records:
        state = record.get('state', 'UNKNOWN')
        state_counts[state] = state_counts.get(state, 0) + 1

    logger.info("")
    logger.info("Records by State:")
    logger.info("-" * 30)
    for state in sorted(state_counts.keys()):
        count = state_counts[state]
        logger.info(f"  {state}: {count:,}")
    logger.info("-" * 30)
    logger.info(f"  TOTAL: {len(records):,}")


def main():
    """Main execution."""

    logger.info("=" * 70)
    logger.info("DOL EXPORT FOR HUNTER.IO - BATCH CSV GENERATOR")
    logger.info("=" * 70)
    logger.info(f"Target States: {', '.join(TARGET_STATES)}")
    logger.info(f"Max rows per file: {ROWS_PER_FILE:,}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info("")

    try:
        # Connect to database
        logger.info("Connecting to Neon database...")
        conn = get_db_connection()
        logger.info("Connected")
        logger.info("")

        # Get unmatched records
        logger.info("Finding unmatched DOL filings...")
        records = get_unmatched_dol_records(conn)
        conn.close()

        if not records:
            logger.info("No unmatched records found!")
            return

        # Print state breakdown
        print_state_breakdown(records)
        logger.info("")

        # Export to CSV files
        created_files = export_to_csv_batches(records, OUTPUT_DIR)

        logger.info("")
        logger.info("=" * 70)
        logger.info("EXPORT COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total records exported: {len(records):,}")
        logger.info(f"Files created: {len(created_files)}")
        for filepath in created_files:
            logger.info(f"  - {filepath}")
        logger.info("")
        logger.info("Upload these files to Hunter.io for domain enrichment.")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
