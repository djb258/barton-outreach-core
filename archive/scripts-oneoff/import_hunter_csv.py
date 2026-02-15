#!/usr/bin/env python3
"""
Hunter.io CSV Import Script

Imports Hunter.io enrichment CSV files into the v2 tables:
- enrichment.hunter_company_v2
- enrichment.hunter_contact_v2

Captures ALL data including all 30 source URLs.

Usage:
    doppler run -- python scripts/import_hunter_csv.py <csv_file_or_directory>
    doppler run -- python scripts/import_hunter_csv.py "path/to/hunter/*.csv"
"""

import os
import sys
import csv
import glob
import logging
import re
from pathlib import Path
from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import execute_values

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get Neon database connection."""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )


def parse_headcount(headcount_str: str) -> tuple:
    """Parse headcount string like '51-200' into (min, max)."""
    if not headcount_str:
        return None, None

    # Handle ranges like "51-200", "1001-5000"
    match = re.match(r'(\d+)-(\d+)', headcount_str)
    if match:
        return int(match.group(1)), int(match.group(2))

    # Handle single numbers
    match = re.match(r'(\d+)\+?', headcount_str)
    if match:
        num = int(match.group(1))
        return num, num

    return None, None


def clean_value(value: str) -> str:
    """Clean a CSV value."""
    if value is None:
        return None
    value = value.strip()
    if value == '' or value.lower() == 'null':
        return None
    return value


def import_csv_file(conn, csv_path: str) -> dict:
    """
    Import a single Hunter CSV file.

    Returns stats dict with counts.
    """
    stats = {
        'companies_inserted': 0,
        'companies_updated': 0,
        'contacts_inserted': 0,
        'contacts_updated': 0,
        'rows_processed': 0,
        'errors': 0
    }

    source_file = Path(csv_path).name
    logger.info(f"Importing: {source_file}")

    # Read CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    logger.info(f"  Found {len(rows):,} rows")

    # Group by domain for company-level dedup
    companies = {}
    contacts = []

    for row in rows:
        domain = clean_value(row.get('domain'))
        if not domain:
            continue

        stats['rows_processed'] += 1

        # Extract company data (first occurrence wins)
        if domain not in companies:
            headcount = clean_value(row.get('Headcount'))
            headcount_min, headcount_max = parse_headcount(headcount)

            companies[domain] = {
                'domain': domain,
                'domain_name': clean_value(row.get('Domain name')),
                'organization': clean_value(row.get('Organization')),
                'company_type': clean_value(row.get('Company type')),
                'industry': clean_value(row.get('Industry')),
                'headcount': headcount,
                'headcount_min': headcount_min,
                'headcount_max': headcount_max,
                'country': clean_value(row.get('Country')),
                'state': clean_value(row.get('State')),
                'city': clean_value(row.get('City')),
                'postal_code': clean_value(row.get('Postal code')),
                'street': clean_value(row.get('Street')),
                'email_pattern': clean_value(row.get('Pattern')),
                'source_file': source_file,
            }

        # Extract contact data
        email = clean_value(row.get('Email address'))
        if email:
            contact = {
                'domain': domain,
                'email': email,
                'email_type': clean_value(row.get('Type')),
                'confidence_score': int(row.get('Confidence score', 0) or 0),
                'num_sources': int(row.get('Number of sources', 0) or 0),
                'first_name': clean_value(row.get('First name')),
                'last_name': clean_value(row.get('Last name')),
                'department': clean_value(row.get('Department')),
                'job_title': clean_value(row.get('Job title')),
                'position_raw': clean_value(row.get('Position raw')),
                'twitter_handle': clean_value(row.get('Twitter handle')),
                'linkedin_url': clean_value(row.get('LinkedIn URL')),
                'phone_number': clean_value(row.get('Phone number')),
                'source_file': source_file,
            }

            # Add all 30 source columns
            for i in range(1, 31):
                source_key = f'Source {i}'
                contact[f'source_{i}'] = clean_value(row.get(source_key))

            contacts.append(contact)

    # Insert companies (use autocommit for resilience)
    logger.info(f"  Upserting {len(companies):,} companies...")
    conn.autocommit = True
    with conn.cursor() as cur:
        for company in companies.values():
            try:
                cur.execute("""
                    INSERT INTO enrichment.hunter_company (
                        domain, organization, company_type, industry,
                        headcount, headcount_min, headcount_max,
                        country, state, city, postal_code, street,
                        email_pattern, source_file, enriched_at
                    ) VALUES (
                        %(domain)s, %(organization)s, %(company_type)s, %(industry)s,
                        %(headcount)s, %(headcount_min)s, %(headcount_max)s,
                        %(country)s, %(state)s, %(city)s, %(postal_code)s, %(street)s,
                        %(email_pattern)s, %(source_file)s, NOW()
                    )
                    ON CONFLICT (domain) DO UPDATE SET
                        organization = COALESCE(EXCLUDED.organization, enrichment.hunter_company.organization),
                        company_type = COALESCE(EXCLUDED.company_type, enrichment.hunter_company.company_type),
                        industry = COALESCE(EXCLUDED.industry, enrichment.hunter_company.industry),
                        headcount = COALESCE(EXCLUDED.headcount, enrichment.hunter_company.headcount),
                        headcount_min = COALESCE(EXCLUDED.headcount_min, enrichment.hunter_company.headcount_min),
                        headcount_max = COALESCE(EXCLUDED.headcount_max, enrichment.hunter_company.headcount_max),
                        country = COALESCE(EXCLUDED.country, enrichment.hunter_company.country),
                        state = COALESCE(EXCLUDED.state, enrichment.hunter_company.state),
                        city = COALESCE(EXCLUDED.city, enrichment.hunter_company.city),
                        postal_code = COALESCE(EXCLUDED.postal_code, enrichment.hunter_company.postal_code),
                        street = COALESCE(EXCLUDED.street, enrichment.hunter_company.street),
                        email_pattern = COALESCE(EXCLUDED.email_pattern, enrichment.hunter_company.email_pattern),
                        updated_at = NOW()
                """, company)

                if cur.rowcount > 0:
                    stats['companies_inserted'] += 1
            except Exception as e:
                logger.error(f"  Error inserting company {company['domain']}: {e}")
                stats['errors'] += 1

    # Insert contacts
    logger.info(f"  Upserting {len(contacts):,} contacts...")
    with conn.cursor() as cur:
        for contact in contacts:
            try:
                cur.execute("""
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
                    ) VALUES (
                        %(domain)s, %(email)s, %(email_type)s, %(confidence_score)s, %(num_sources)s,
                        %(first_name)s, %(last_name)s, %(department)s, %(job_title)s, %(position_raw)s,
                        %(twitter_handle)s, %(linkedin_url)s, %(phone_number)s, %(source_file)s,
                        %(source_1)s, %(source_2)s, %(source_3)s, %(source_4)s, %(source_5)s,
                        %(source_6)s, %(source_7)s, %(source_8)s, %(source_9)s, %(source_10)s,
                        %(source_11)s, %(source_12)s, %(source_13)s, %(source_14)s, %(source_15)s,
                        %(source_16)s, %(source_17)s, %(source_18)s, %(source_19)s, %(source_20)s,
                        %(source_21)s, %(source_22)s, %(source_23)s, %(source_24)s, %(source_25)s,
                        %(source_26)s, %(source_27)s, %(source_28)s, %(source_29)s, %(source_30)s
                    )
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
                        source_30 = COALESCE(EXCLUDED.source_30, enrichment.hunter_contact.source_30)
                """, contact)

                if cur.rowcount > 0:
                    stats['contacts_inserted'] += 1
            except Exception as e:
                logger.error(f"  Error inserting contact {contact['email']}: {e}")
                stats['errors'] += 1

    return stats


def main():
    """Main execution."""
    if len(sys.argv) < 2:
        print("Usage: python import_hunter_csv.py <csv_file_or_pattern>")
        print("Examples:")
        print('  python import_hunter_csv.py "path/to/hunter/*.csv"')
        print('  python import_hunter_csv.py file1.csv file2.csv file3.csv')
        sys.exit(1)

    # Collect all CSV files
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
    logger.info("HUNTER.IO CSV IMPORT")
    logger.info("=" * 70)
    logger.info(f"Files to import: {len(csv_files)}")
    for f in csv_files:
        logger.info(f"  - {Path(f).name}")
    logger.info("")

    # Connect to database
    logger.info("Connecting to Neon database...")
    conn = get_db_connection()
    logger.info("Connected")
    logger.info("")

    # Process each file
    total_stats = {
        'companies_inserted': 0,
        'contacts_inserted': 0,
        'rows_processed': 0,
        'errors': 0,
        'files_processed': 0
    }

    for csv_file in csv_files:
        try:
            stats = import_csv_file(conn, csv_file)
            total_stats['companies_inserted'] += stats['companies_inserted']
            total_stats['contacts_inserted'] += stats['contacts_inserted']
            total_stats['rows_processed'] += stats['rows_processed']
            total_stats['errors'] += stats['errors']
            total_stats['files_processed'] += 1
            logger.info(f"  Done: {stats['companies_inserted']} companies, {stats['contacts_inserted']} contacts")
            logger.info("")
        except Exception as e:
            logger.error(f"Error processing {csv_file}: {e}")
            total_stats['errors'] += 1

    conn.close()

    # Summary
    logger.info("=" * 70)
    logger.info("IMPORT COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Files processed:    {total_stats['files_processed']}")
    logger.info(f"Rows processed:     {total_stats['rows_processed']:,}")
    logger.info(f"Companies upserted: {total_stats['companies_inserted']:,}")
    logger.info(f"Contacts upserted:  {total_stats['contacts_inserted']:,}")
    logger.info(f"Errors:             {total_stats['errors']}")

    # Verify counts
    logger.info("")
    logger.info("Verifying table counts...")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_company")
    company_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_contact")
    contact_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM enrichment.v_hunter_contact_sources")
    source_count = cur.fetchone()[0]
    conn.close()

    logger.info(f"  hunter_company:           {company_count:,} records")
    logger.info(f"  hunter_contact:           {contact_count:,} records")
    logger.info(f"  v_hunter_contact_sources: {source_count:,} source URLs")


if __name__ == '__main__':
    main()
