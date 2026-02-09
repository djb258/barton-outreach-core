"""
Add phone columns to people.company_slot and populate with Hunter data.

This script:
1. Adds slot_phone, slot_phone_source, slot_phone_updated_at columns
2. Reads CEO, CFO, HR CSV exports from Hunter
3. Updates slots with phone numbers where available
"""

import os
import sys
import csv
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_batch
import logging

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_neon_connection():
    """Get Neon PostgreSQL connection."""
    return psycopg2.connect(
        host=os.getenv('NEON_HOST'),
        database=os.getenv('NEON_DATABASE'),
        user=os.getenv('NEON_USER'),
        password=os.getenv('NEON_PASSWORD'),
        sslmode='require'
    )

def add_phone_columns(conn):
    """Add phone columns to people.company_slot if they don't exist."""
    logger.info("Adding phone columns to people.company_slot...")

    with conn.cursor() as cur:
        # Check if columns already exist
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'people'
              AND table_name = 'company_slot'
              AND column_name IN ('slot_phone', 'slot_phone_source', 'slot_phone_updated_at')
            ORDER BY column_name;
        """)
        existing_columns = [row[0] for row in cur.fetchall()]

        if len(existing_columns) == 3:
            logger.info("Phone columns already exist: %s", existing_columns)
            return

        # Add columns
        cur.execute("""
            ALTER TABLE people.company_slot
            ADD COLUMN IF NOT EXISTS slot_phone TEXT,
            ADD COLUMN IF NOT EXISTS slot_phone_source TEXT,
            ADD COLUMN IF NOT EXISTS slot_phone_updated_at TIMESTAMPTZ;

            COMMENT ON COLUMN people.company_slot.slot_phone IS 'Office/desk phone for this position - tied to slot, not person';
            COMMENT ON COLUMN people.company_slot.slot_phone_source IS 'Source of phone number (hunter, manual, etc)';
            COMMENT ON COLUMN people.company_slot.slot_phone_updated_at IS 'Timestamp when phone was last updated';
        """)
        conn.commit()
        logger.info("Successfully added phone columns to people.company_slot")

def read_csv_with_phones(csv_path):
    """Read CSV and extract records with phone numbers."""
    records_with_phones = []
    total_records = 0

    logger.info("Reading CSV: %s", csv_path)

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_records += 1
            if row.get('phone') and row['phone'].strip():
                records_with_phones.append({
                    'outreach_id': row['outreach_id'],
                    'slot_type': row['slot_type'],
                    'phone': row['phone'].strip()
                })

    logger.info("Found %d records with phones out of %d total records",
                len(records_with_phones), total_records)
    return records_with_phones

def update_phone_numbers(conn, phone_records):
    """Update people.company_slot with phone numbers."""
    logger.info("Updating phone numbers for %d records...", len(phone_records))

    if not phone_records:
        logger.warning("No phone records to update")
        return 0

    update_query = """
        UPDATE people.company_slot
        SET slot_phone = %s,
            slot_phone_source = 'hunter',
            slot_phone_updated_at = NOW()
        WHERE outreach_id = %s
          AND slot_type = %s
          AND (slot_phone IS NULL OR slot_phone = '');
    """

    batch_data = [
        (record['phone'], record['outreach_id'], record['slot_type'])
        for record in phone_records
    ]

    with conn.cursor() as cur:
        execute_batch(cur, update_query, batch_data, page_size=100)
        updated_count = cur.rowcount
        conn.commit()

    logger.info("Updated %d slots with phone numbers", updated_count)
    return updated_count

def main():
    """Main execution."""
    logger.info("=" * 80)
    logger.info("ADD PHONE TO COMPANY_SLOT - HUNTER DATA IMPORT")
    logger.info("=" * 80)

    # Verify environment
    required_env = ['NEON_HOST', 'NEON_DATABASE', 'NEON_USER', 'NEON_PASSWORD']
    missing_env = [env for env in required_env if not os.getenv(env)]
    if missing_env:
        logger.error("Missing environment variables: %s", missing_env)
        sys.exit(1)

    # CSV file paths
    base_path = r"C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\exports\slot_contacts"
    csv_files = [
        ('CEO', os.path.join(base_path, 'ceo_slot_contacts.csv')),
        ('CFO', os.path.join(base_path, 'cfo_slot_contacts.csv')),
        ('HR', os.path.join(base_path, 'hr_slot_contacts.csv'))
    ]

    # Verify files exist
    for slot_type, csv_path in csv_files:
        if not os.path.exists(csv_path):
            logger.error("CSV file not found: %s", csv_path)
            sys.exit(1)

    try:
        # Connect to Neon
        conn = get_neon_connection()
        logger.info("Connected to Neon PostgreSQL")

        # Step 1: Add phone columns
        add_phone_columns(conn)

        # Step 2: Process each CSV file
        total_phone_records = []
        for slot_type, csv_path in csv_files:
            logger.info("\n" + "-" * 80)
            logger.info("Processing %s slots from: %s", slot_type, csv_path)
            logger.info("-" * 80)
            phone_records = read_csv_with_phones(csv_path)
            total_phone_records.extend(phone_records)

        logger.info("\n" + "=" * 80)
        logger.info("TOTAL PHONE RECORDS ACROSS ALL SLOTS: %d", len(total_phone_records))
        logger.info("=" * 80)

        # Step 3: Update database
        updated_count = update_phone_numbers(conn, total_phone_records)

        # Step 4: Verify updates
        with conn.cursor() as cur:
            cur.execute("""
                SELECT slot_type, COUNT(*) as count
                FROM people.company_slot
                WHERE slot_phone IS NOT NULL AND slot_phone != ''
                GROUP BY slot_type
                ORDER BY slot_type;
            """)
            results = cur.fetchall()

            logger.info("\n" + "=" * 80)
            logger.info("PHONE NUMBER POPULATION BY SLOT TYPE")
            logger.info("=" * 80)
            for slot_type, count in results:
                logger.info("%s: %d slots with phone numbers", slot_type, count)

            # Total check
            cur.execute("""
                SELECT COUNT(*)
                FROM people.company_slot
                WHERE slot_phone IS NOT NULL AND slot_phone != '';
            """)
            total_with_phones = cur.fetchone()[0]
            logger.info("-" * 80)
            logger.info("TOTAL: %d slots with phone numbers", total_with_phones)

        conn.close()
        logger.info("\n" + "=" * 80)
        logger.info("PHONE DATA IMPORT COMPLETE")
        logger.info("Updated: %d slots", updated_count)
        logger.info("=" * 80)

    except Exception as e:
        logger.error("Error during phone import: %s", str(e), exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
