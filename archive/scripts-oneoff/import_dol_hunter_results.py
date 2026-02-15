#!/usr/bin/env python3
"""
Import DOL Hunter.io Results

Imports Hunter enrichment data for DOL filings.
- Stores all Hunter data in enrichment tables (hunter_company, hunter_contact)
- Updates dol.ein_urls with EIN → Domain mapping
- Does NOT modify form_5500, form_5500_sf, schedule_a

Usage:
    doppler run -- python scripts/import_dol_hunter_results.py <csv_file>
"""

import os
import sys
import csv
import re
import logging
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


def clean_value(value):
    if value is None:
        return None
    value = str(value).strip()
    if value == '' or value.lower() == 'null':
        return None
    return value


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


def import_dol_hunter_csv(conn, csv_path: str) -> dict:
    """Import DOL Hunter results - all data preserved."""

    stats = {
        'rows': 0,
        'companies': 0,
        'contacts': 0,
        'ein_urls': 0,
        'errors': 0
    }

    source_file = Path(csv_path).name
    logger.info(f"Importing: {source_file}")

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    stats['rows'] = len(rows)
    logger.info(f"  Found {len(rows):,} rows")

    # Group by domain for companies
    companies = {}
    contacts = []
    ein_domains = {}  # EIN → domain mapping

    for row in rows:
        domain = clean_value(row.get('Domain name'))
        ein = clean_value(row.get('ein'))

        if not domain:
            continue

        # Track EIN → Domain mapping (from DOL data)
        if ein and ein not in ein_domains:
            ein_domains[ein] = {
                'ein': ein,
                'company_name': clean_value(row.get('company_name')),
                'city': clean_value(row.get('city')),
                'state': clean_value(row.get('state')),
                'domain': domain,
                'ack_id': clean_value(row.get('ack_id')),
                'filing_id': clean_value(row.get('filing_id'))
            }

        # Company data (one per domain)
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
                clean_value(row.get('State')),  # Hunter state (company HQ)
                clean_value(row.get('City')),   # Hunter city
                clean_value(row.get('Postal code')),
                clean_value(row.get('Street')),
                clean_value(row.get('Pattern')),
                source_file
            )

        # Contact data
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

    cur = conn.cursor()

    # 1. Insert/Update companies
    logger.info(f"  Upserting {len(companies):,} companies...")
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
        logger.info(f"    Companies done: {stats['companies']:,}")
    except Exception as e:
        logger.error(f"    Company error: {e}")
        conn.rollback()
        stats['errors'] += 1

    # 2. Insert/Update contacts (need unique constraint)
    logger.info(f"  Inserting {len(contacts):,} contacts...")

    # Since we don't have unique constraint, insert with ON CONFLICT DO NOTHING
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
            logger.error(f"    Contact error at {i}: {e}")
            conn.rollback()
            stats['errors'] += 1

    # 3. Update dol.ein_urls with EIN → Domain mapping
    logger.info(f"  Updating {len(ein_domains):,} EIN → Domain mappings...")

    ein_sql = """
        INSERT INTO dol.ein_urls (ein, company_name, city, state, domain, url, discovered_at, discovery_method)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), 'hunter_dol_enrichment')
        ON CONFLICT (ein) DO UPDATE SET
            domain = COALESCE(EXCLUDED.domain, dol.ein_urls.domain),
            url = COALESCE(EXCLUDED.url, dol.ein_urls.url),
            discovery_method = 'hunter_dol_enrichment'
    """

    for ein, data in ein_domains.items():
        try:
            url = f"https://{data['domain']}" if data['domain'] else None
            cur.execute(ein_sql, (
                data['ein'],
                data['company_name'],
                data['city'],
                data['state'],
                data['domain'],
                url
            ))
            stats['ein_urls'] += 1
        except Exception as e:
            logger.debug(f"    EIN {ein} error: {e}")
            stats['errors'] += 1

    conn.commit()
    cur.close()

    logger.info(f"    EIN URLs updated: {stats['ein_urls']:,}")

    return stats


def main():
    if len(sys.argv) < 2:
        print("Usage: python import_dol_hunter_results.py <csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]

    logger.info("=" * 70)
    logger.info("IMPORT DOL HUNTER RESULTS")
    logger.info("=" * 70)
    logger.info(f"File: {csv_file}")
    logger.info("")
    logger.info("Will import to:")
    logger.info("  - enrichment.hunter_company")
    logger.info("  - enrichment.hunter_contact")
    logger.info("  - dol.ein_urls (EIN → Domain mapping)")
    logger.info("")
    logger.info("Will NOT modify:")
    logger.info("  - dol.form_5500")
    logger.info("  - dol.form_5500_sf")
    logger.info("  - dol.schedule_a")
    logger.info("")

    conn = get_db_connection()
    stats = import_dol_hunter_csv(conn, csv_file)
    conn.close()

    logger.info("")
    logger.info("=" * 70)
    logger.info("COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Rows processed:  {stats['rows']:,}")
    logger.info(f"Companies:       {stats['companies']:,}")
    logger.info(f"Contacts:        {stats['contacts']:,}")
    logger.info(f"EIN → Domain:    {stats['ein_urls']:,}")
    logger.info(f"Errors:          {stats['errors']}")

    # Show matching stats
    logger.info("")
    logger.info("Checking outreach matches...")
    conn = get_db_connection()
    cur = conn.cursor()

    # How many of these EINs now match to outreach via domain?
    cur.execute("""
        SELECT COUNT(DISTINCT eu.ein)
        FROM dol.ein_urls eu
        JOIN outreach.outreach o ON LOWER(eu.domain) = LOWER(o.domain)
        WHERE eu.discovery_method = 'hunter_dol_enrichment'
    """)
    matched = cur.fetchone()[0]

    logger.info(f"EINs matched to outreach: {matched:,}")
    conn.close()


if __name__ == '__main__':
    main()
