#!/usr/bin/env python3
"""
Generate EIN Status CSV Exports
Split companies by EIN status and chunk large files
"""

import os
import psycopg2
import csv
from typing import List, Tuple

# Neon connection details
NEON_CONFIG = {
    'host': os.getenv('NEON_HOST', 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech'),
    'database': os.getenv('NEON_DATABASE', 'Marketing DB'),
    'user': os.getenv('NEON_USER', 'Marketing DB_owner'),
    'password': os.getenv('NEON_PASSWORD'),
    'port': 5432,
    'sslmode': 'require'
}

EXPORT_DIR = r'C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\exports\ein_status'
CHUNK_SIZE = 24000


def get_connection():
    """Create Neon database connection."""
    return psycopg2.connect(**NEON_CONFIG)


def export_with_ein():
    """Export companies WITH EIN (split into 24K chunks)."""
    print("\n=== EXPORTING COMPANIES WITH EIN ===")

    query = """
    SELECT DISTINCT ON (o.outreach_id)
        o.outreach_id,
        o.domain,
        d.ein,
        d.filing_present,
        d.funding_type,
        d.broker_or_advisor,
        d.carrier
    FROM outreach.outreach o
    JOIN outreach.dol d ON o.outreach_id = d.outreach_id
    WHERE d.ein IS NOT NULL
    ORDER BY o.outreach_id, d.created_at DESC;
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        total_rows = len(rows)

        print(f"Total companies WITH EIN: {total_rows:,}")

        # Get column names
        columns = [desc[0] for desc in cursor.description]

        # Split into chunks
        chunk_num = 1
        start_idx = 0

        while start_idx < total_rows:
            end_idx = min(start_idx + CHUNK_SIZE, total_rows)
            chunk_rows = rows[start_idx:end_idx]

            filename = f"companies_with_ein_part{chunk_num}.csv"
            filepath = os.path.join(EXPORT_DIR, filename)

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(chunk_rows)

            print(f"  [OK] {filename}: {len(chunk_rows):,} rows (rows {start_idx + 1}-{end_idx})")

            chunk_num += 1
            start_idx = end_idx

        return total_rows

    finally:
        cursor.close()
        conn.close()


def export_without_ein():
    """Export companies WITHOUT EIN (enrichment queue)."""
    print("\n=== EXPORTING COMPANIES WITHOUT EIN (Enrichment Queue) ===")

    query = """
    SELECT
        o.outreach_id,
        o.domain,
        ci.company_name,
        ct.email_method
    FROM outreach.outreach o
    LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
    LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
    LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
    WHERE d.ein IS NULL OR d.outreach_id IS NULL
    ORDER BY o.domain;
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        total_rows = len(rows)

        print(f"Total companies WITHOUT EIN: {total_rows:,}")

        # Get column names
        columns = [desc[0] for desc in cursor.description]

        # Split into chunks if needed
        chunk_num = 1
        start_idx = 0

        while start_idx < total_rows:
            end_idx = min(start_idx + CHUNK_SIZE, total_rows)
            chunk_rows = rows[start_idx:end_idx]

            filename = f"companies_without_ein_part{chunk_num}.csv"
            filepath = os.path.join(EXPORT_DIR, filename)

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(chunk_rows)

            print(f"  [OK] {filename}: {len(chunk_rows):,} rows (rows {start_idx + 1}-{end_idx})")

            chunk_num += 1
            start_idx = end_idx

        return total_rows

    finally:
        cursor.close()
        conn.close()


def verify_totals(with_ein_count: int, without_ein_count: int):
    """Verify total against outreach spine."""
    print("\n=== VERIFICATION ===")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get total outreach records
        cursor.execute("SELECT COUNT(*) FROM outreach.outreach;")
        total_outreach = cursor.fetchone()[0]

        exported_total = with_ein_count + without_ein_count

        print(f"Total in outreach.outreach: {total_outreach:,}")
        print(f"Total exported (WITH + WITHOUT EIN): {exported_total:,}")
        print(f"  - WITH EIN: {with_ein_count:,}")
        print(f"  - WITHOUT EIN: {without_ein_count:,}")

        if exported_total == total_outreach:
            print("[OK] VERIFICATION PASSED: All records accounted for")
        else:
            diff = total_outreach - exported_total
            print(f"[WARNING] VERIFICATION WARNING: {diff:,} records difference")

    finally:
        cursor.close()
        conn.close()


def main():
    """Main execution."""
    print("=" * 80)
    print("EIN STATUS CSV EXPORT GENERATOR")
    print("=" * 80)

    # Clean directory first
    print(f"\nExport directory: {EXPORT_DIR}")
    if os.path.exists(EXPORT_DIR):
        existing_files = [f for f in os.listdir(EXPORT_DIR) if f.endswith('.csv')]
        if existing_files:
            print(f"Removing {len(existing_files)} old CSV files...")
            for f in existing_files:
                os.remove(os.path.join(EXPORT_DIR, f))

    # Export companies WITH EIN
    with_ein_count = export_with_ein()

    # Export companies WITHOUT EIN
    without_ein_count = export_without_ein()

    # Verify totals
    verify_totals(with_ein_count, without_ein_count)

    print("\n" + "=" * 80)
    print("EXPORT COMPLETE")
    print("=" * 80)
    print(f"Files saved to: {EXPORT_DIR}")


if __name__ == '__main__':
    main()
