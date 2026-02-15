#!/usr/bin/env python3
"""
Hunter.io CSV Import Script - FAST BATCH VERSION

Imports Hunter.io enrichment CSV files into existing tables using batch operations.
Much faster than individual inserts.

Usage:
    doppler run -- python scripts/import_hunter_csv_fast.py <csv_files>
"""

import os
import sys
import csv
import glob
import logging
import re
from pathlib import Path
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_values

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


def parse_headcount(headcount_str: str) -> tuple:
    if not headcount_str:
        return None, None
    match = re.match(r'(\d+)-(\d+)', headcount_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    match = re.match(r'(\d+)\+?', headcount_str)
    if match:
        num = int(match.group(1))
        return num, num
    return None, None


def clean_value(value):
    if value is None:
        return None
    value = str(value).strip()
    if value == '' or value.lower() == 'null':
        return None
    return value


def import_csv_file(conn, csv_path: str) -> dict:
    stats = {'companies': 0, 'contacts': 0, 'errors': 0}
    source_file = Path(csv_path).name
    logger.info(f"Importing: {source_file}")

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    logger.info(f"  Found {len(rows):,} rows")

    # Group by domain for companies
    companies = {}
    contacts = []

    for row in rows:
        domain = clean_value(row.get('domain'))
        if not domain:
            continue

        if domain not in companies:
            headcount = clean_value(row.get('Headcount'))
            hmin, hmax = parse_headcount(headcount)
            companies[domain] = (
                domain,
                clean_value(row.get('Organization')),
                clean_value(row.get('Company type')),
                clean_value(row.get('Industry')),
                headcount, hmin, hmax,
                clean_value(row.get('Country')),
                clean_value(row.get('State')),
                clean_value(row.get('City')),
                clean_value(row.get('Postal code')),
                clean_value(row.get('Street')),
                clean_value(row.get('Pattern')),
                source_file
            )

        email = clean_value(row.get('Email address'))
        if email:
            contact = [
                domain, email,
                clean_value(row.get('Type')),
                int(row.get('Confidence score', 0) or 0),
                int(row.get('Number of sources', 0) or 0),
                clean_value(row.get('First name')),
                clean_value(row.get('Last name')),
                clean_value(row.get('Department')),
                clean_value(row.get('Job title')),
                clean_value(row.get('Position raw')),
                clean_value(row.get('Twitter handle')),
                clean_value(row.get('LinkedIn URL')),
                clean_value(row.get('Phone number')),
                source_file
            ]
            # Add 30 source columns
            for i in range(1, 31):
                contact.append(clean_value(row.get(f'Source {i}')))
            contacts.append(tuple(contact))

    # Batch insert companies
    logger.info(f"  Upserting {len(companies):,} companies (batch)...")
    cur = conn.cursor()

    company_sql = """
        INSERT INTO enrichment.hunter_company (
            domain, organization, company_type, industry,
            headcount, headcount_min, headcount_max,
            country, state, city, postal_code, street,
            email_pattern, source_file
        ) VALUES %s
        ON CONFLICT (domain) DO UPDATE SET
            organization = COALESCE(EXCLUDED.organization, enrichment.hunter_company.organization),
            company_type = COALESCE(EXCLUDED.company_type, enrichment.hunter_company.company_type),
            industry = COALESCE(EXCLUDED.industry, enrichment.hunter_company.industry),
            headcount = COALESCE(EXCLUDED.headcount, enrichment.hunter_company.headcount),
            headcount_min = COALESCE(EXCLUDED.headcount_min, enrichment.hunter_company.headcount_min),
            headcount_max = COALESCE(EXCLUDED.headcount_max, enrichment.hunter_company.headcount_max),
            email_pattern = COALESCE(EXCLUDED.email_pattern, enrichment.hunter_company.email_pattern),
            updated_at = NOW()
    """

    try:
        execute_values(cur, company_sql, list(companies.values()), page_size=1000)
        conn.commit()
        stats['companies'] = len(companies)
        logger.info(f"  Companies done: {stats['companies']:,}")
    except Exception as e:
        logger.error(f"  Company batch error: {e}")
        conn.rollback()
        stats['errors'] += 1

    # Batch insert contacts (in chunks to avoid memory issues)
    logger.info(f"  Upserting {len(contacts):,} contacts (batch)...")

    contact_sql = """
        INSERT INTO enrichment.hunter_contact (
            domain, email, email_type, confidence_score, num_sources,
            first_name, last_name, department, job_title, position_raw,
            twitter_handle, linkedin_url, phone_number, source_file,
            source_1, source_2, source_3, source_4, source_5,
            source_6, source_7, source_8, source_9, source_10,
            source_11, source_12, source_13, source_14, source_15,
            source_16, source_17, source_18, source_19, source_20,
            source_21, source_22, source_23, source_24, source_25,
            source_26, source_27, source_28, source_29, source_30
        ) VALUES %s
        ON CONFLICT (domain, email) DO UPDATE SET
            email_type = COALESCE(EXCLUDED.email_type, enrichment.hunter_contact.email_type),
            confidence_score = GREATEST(EXCLUDED.confidence_score, enrichment.hunter_contact.confidence_score),
            num_sources = GREATEST(EXCLUDED.num_sources, enrichment.hunter_contact.num_sources),
            first_name = COALESCE(EXCLUDED.first_name, enrichment.hunter_contact.first_name),
            last_name = COALESCE(EXCLUDED.last_name, enrichment.hunter_contact.last_name),
            department = COALESCE(EXCLUDED.department, enrichment.hunter_contact.department),
            job_title = COALESCE(EXCLUDED.job_title, enrichment.hunter_contact.job_title),
            position_raw = COALESCE(EXCLUDED.position_raw, enrichment.hunter_contact.position_raw),
            twitter_handle = COALESCE(EXCLUDED.twitter_handle, enrichment.hunter_contact.twitter_handle),
            linkedin_url = COALESCE(EXCLUDED.linkedin_url, enrichment.hunter_contact.linkedin_url),
            phone_number = COALESCE(EXCLUDED.phone_number, enrichment.hunter_contact.phone_number),
            source_1 = COALESCE(EXCLUDED.source_1, enrichment.hunter_contact.source_1),
            source_2 = COALESCE(EXCLUDED.source_2, enrichment.hunter_contact.source_2),
            source_3 = COALESCE(EXCLUDED.source_3, enrichment.hunter_contact.source_3),
            source_4 = COALESCE(EXCLUDED.source_4, enrichment.hunter_contact.source_4),
            source_5 = COALESCE(EXCLUDED.source_5, enrichment.hunter_contact.source_5),
            source_6 = COALESCE(EXCLUDED.source_6, enrichment.hunter_contact.source_6),
            source_7 = COALESCE(EXCLUDED.source_7, enrichment.hunter_contact.source_7),
            source_8 = COALESCE(EXCLUDED.source_8, enrichment.hunter_contact.source_8),
            source_9 = COALESCE(EXCLUDED.source_9, enrichment.hunter_contact.source_9),
            source_10 = COALESCE(EXCLUDED.source_10, enrichment.hunter_contact.source_10),
            source_11 = COALESCE(EXCLUDED.source_11, enrichment.hunter_contact.source_11),
            source_12 = COALESCE(EXCLUDED.source_12, enrichment.hunter_contact.source_12),
            source_13 = COALESCE(EXCLUDED.source_13, enrichment.hunter_contact.source_13),
            source_14 = COALESCE(EXCLUDED.source_14, enrichment.hunter_contact.source_14),
            source_15 = COALESCE(EXCLUDED.source_15, enrichment.hunter_contact.source_15),
            source_16 = COALESCE(EXCLUDED.source_16, enrichment.hunter_contact.source_16),
            source_17 = COALESCE(EXCLUDED.source_17, enrichment.hunter_contact.source_17),
            source_18 = COALESCE(EXCLUDED.source_18, enrichment.hunter_contact.source_18),
            source_19 = COALESCE(EXCLUDED.source_19, enrichment.hunter_contact.source_19),
            source_20 = COALESCE(EXCLUDED.source_20, enrichment.hunter_contact.source_20),
            source_21 = COALESCE(EXCLUDED.source_21, enrichment.hunter_contact.source_21),
            source_22 = COALESCE(EXCLUDED.source_22, enrichment.hunter_contact.source_22),
            source_23 = COALESCE(EXCLUDED.source_23, enrichment.hunter_contact.source_23),
            source_24 = COALESCE(EXCLUDED.source_24, enrichment.hunter_contact.source_24),
            source_25 = COALESCE(EXCLUDED.source_25, enrichment.hunter_contact.source_25),
            source_26 = COALESCE(EXCLUDED.source_26, enrichment.hunter_contact.source_26),
            source_27 = COALESCE(EXCLUDED.source_27, enrichment.hunter_contact.source_27),
            source_28 = COALESCE(EXCLUDED.source_28, enrichment.hunter_contact.source_28),
            source_29 = COALESCE(EXCLUDED.source_29, enrichment.hunter_contact.source_29),
            source_30 = COALESCE(EXCLUDED.source_30, enrichment.hunter_contact.source_30),
            source_file = EXCLUDED.source_file
    """

    CHUNK_SIZE = 5000
    for i in range(0, len(contacts), CHUNK_SIZE):
        chunk = contacts[i:i+CHUNK_SIZE]
        try:
            execute_values(cur, contact_sql, chunk, page_size=500)
            conn.commit()
            stats['contacts'] += len(chunk)
            logger.info(f"    Contacts: {stats['contacts']:,}/{len(contacts):,}")
        except Exception as e:
            logger.error(f"  Contact batch error at {i}: {e}")
            conn.rollback()
            stats['errors'] += 1

    cur.close()
    return stats


def main():
    if len(sys.argv) < 2:
        print("Usage: python import_hunter_csv_fast.py <csv_files>")
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
    logger.info("HUNTER.IO CSV IMPORT - FAST BATCH")
    logger.info("=" * 70)
    logger.info(f"Files: {len(csv_files)}")

    conn = get_db_connection()

    total = {'companies': 0, 'contacts': 0, 'errors': 0}
    for csv_file in csv_files:
        stats = import_csv_file(conn, csv_file)
        total['companies'] += stats['companies']
        total['contacts'] += stats['contacts']
        total['errors'] += stats['errors']

    conn.close()

    logger.info("=" * 70)
    logger.info("COMPLETE")
    logger.info(f"Companies: {total['companies']:,}")
    logger.info(f"Contacts:  {total['contacts']:,}")
    logger.info(f"Errors:    {total['errors']}")

    # Verify
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_contact WHERE source_1 IS NOT NULL")
    with_sources = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM enrichment.v_hunter_contact_sources")
    source_urls = cur.fetchone()[0]
    conn.close()

    logger.info(f"Contacts with sources: {with_sources:,}")
    logger.info(f"Total source URLs:     {source_urls:,}")


if __name__ == '__main__':
    main()
