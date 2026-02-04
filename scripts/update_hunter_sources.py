#!/usr/bin/env python3
"""
Update Hunter Source Columns

Updates existing hunter_contact records with source URLs from CSV files.
Uses UPDATE instead of INSERT to avoid unique constraint issues.
"""

import os
import sys
import csv
import glob
import logging
from pathlib import Path

import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


def get_db_connection():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )


def clean_value(value):
    if value is None:
        return None
    value = str(value).strip()
    if value == '' or value.lower() == 'null':
        return None
    return value


def update_sources_from_csv(conn, csv_path: str) -> dict:
    stats = {'updated': 0, 'not_found': 0, 'total': 0}
    source_file = Path(csv_path).name
    logger.info(f"Processing: {source_file}")

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    logger.info(f"  Found {len(rows):,} rows")

    cur = conn.cursor()
    conn.autocommit = True

    for i, row in enumerate(rows):
        domain = clean_value(row.get('domain'))
        email = clean_value(row.get('Email address'))

        if not domain or not email:
            continue

        stats['total'] += 1

        # Collect source values
        sources = {}
        for j in range(1, 31):
            val = clean_value(row.get(f'Source {j}'))
            if val:
                sources[f'source_{j}'] = val

        if not sources:
            continue

        # Build UPDATE query
        set_clause = ', '.join([f"{k} = %s" for k in sources.keys()])
        set_clause += ", source_file = %s"
        values = list(sources.values()) + [source_file, domain, email]

        try:
            cur.execute(f"""
                UPDATE enrichment.hunter_contact
                SET {set_clause}
                WHERE domain = %s AND email = %s
            """, values)

            if cur.rowcount > 0:
                stats['updated'] += 1
            else:
                stats['not_found'] += 1
        except Exception as e:
            logger.error(f"Error updating {email}: {e}")

        if (i + 1) % 10000 == 0:
            logger.info(f"  Progress: {i+1:,}/{len(rows):,} - Updated: {stats['updated']:,}")

    cur.close()
    return stats


def main():
    if len(sys.argv) < 2:
        print("Usage: python update_hunter_sources.py <csv_files>")
        sys.exit(1)

    csv_files = []
    for arg in sys.argv[1:]:
        if '*' in arg:
            csv_files.extend(glob.glob(arg))
        else:
            csv_files.append(arg)

    if not csv_files:
        logger.error("No CSV files found!")
        sys.exit(1)

    logger.info("=" * 70)
    logger.info("UPDATE HUNTER SOURCE COLUMNS")
    logger.info("=" * 70)
    logger.info(f"Files: {len(csv_files)}")

    conn = get_db_connection()

    total = {'updated': 0, 'not_found': 0, 'total': 0}
    for csv_file in csv_files:
        stats = update_sources_from_csv(conn, csv_file)
        total['updated'] += stats['updated']
        total['not_found'] += stats['not_found']
        total['total'] += stats['total']
        logger.info(f"  Done: Updated {stats['updated']:,}, Not found {stats['not_found']:,}")

    conn.close()

    logger.info("=" * 70)
    logger.info("COMPLETE")
    logger.info(f"Total rows:    {total['total']:,}")
    logger.info(f"Updated:       {total['updated']:,}")
    logger.info(f"Not found:     {total['not_found']:,}")

    # Verify
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_contact WHERE source_1 IS NOT NULL")
    with_sources = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM enrichment.v_hunter_contact_sources")
    source_urls = cur.fetchone()[0]
    conn.close()

    logger.info("")
    logger.info(f"Contacts with sources: {with_sources:,}")
    logger.info(f"Total source URLs:     {source_urls:,}")


if __name__ == '__main__':
    main()
