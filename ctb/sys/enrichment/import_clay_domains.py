#!/usr/bin/env python3
"""
Import Clay Enriched Domains & Promote to company_master
=========================================================
1. Updates intake.company_raw_wv with enriched domains from Clay CSV
2. Promotes newly-valid records to company.company_master

Usage:
    python import_clay_domains.py <csv_file> [--dry-run]
"""

import csv
import os
import sys
import argparse
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import RealDictCursor

NEON_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}

# Known bad/generic domains to filter out
BAD_DOMAINS = {
    'reddit.com', 'bbb.org', 'wikipedia.org', 'linkedin.com', 'facebook.com',
    'twitter.com', 'youtube.com', 'google.com', 'yelp.com', 'glassdoor.com',
    'indeed.com', 'craigslist.org', 'amazon.com', 'ihs.gov', 'nlrb.gov',
    'sc.gov', 'army.mil', 'responsiblebusiness.org', 'dowjones.com',
    'forrester.com', 'henkel.com', 'datacore.com', 'kpmguscareers.com',
    'safety-kleen.com', 'allentownsd.org', 'huntingtondf.com', 'ahima.org',
    'uoflhealth.org', 'alphaomega.com', 'visionmonday.com', 'kisacoresearch.com',
    'alliedbuildings.com', '53.com', '4thecreatives.com'
}


def normalize_domain(domain):
    if not domain:
        return None
    domain = str(domain).strip().lower()
    if domain.startswith('http://'):
        domain = domain[7:]
    if domain.startswith('https://'):
        domain = domain[8:]
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain.rstrip('/') or None


def import_and_promote(csv_file, dry_run=False):
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))

    print('=' * 70)
    print('CLAY DOMAIN IMPORT & PROMOTION')
    print('=' * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Records in CSV: {len(rows):,}")
    print()

    conn = psycopg2.connect(**NEON_CONFIG)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Step 1: Update intake with enriched domains
    print("STEP 1: Updating intake.company_raw_wv with enriched domains...")
    updated_intake = 0

    for row in rows:
        company_id = row.get('company_unique_id', '').strip()
        domain = normalize_domain(row.get('Domain', ''))

        if not domain or domain in BAD_DOMAINS:
            continue

        if not dry_run:
            cur.execute('''
                UPDATE intake.company_raw_wv
                SET domain = %s
                WHERE company_unique_id = %s AND (domain IS NULL OR domain = '')
            ''', (domain, company_id))
            if cur.rowcount > 0:
                updated_intake += 1
        else:
            updated_intake += 1

    if not dry_run:
        conn.commit()
    print(f"  Updated {updated_intake:,} intake records with domains")
    print()

    # Step 2: Get next Barton ID sequence
    cur.execute('''
        SELECT COALESCE(MAX(CAST(SPLIT_PART(company_unique_id, '.', 5) AS INTEGER)), 499) as max_seq
        FROM company.company_master
        WHERE company_unique_id LIKE '04.04.01.%'
    ''')
    next_seq = cur.fetchone()['max_seq'] + 1
    print(f"Next Barton sequence: {next_seq}")

    # Step 3: Promote newly-valid records
    print()
    print("STEP 2: Promoting newly-valid records to company.company_master...")

    if not dry_run:
        cur.execute('''
            INSERT INTO company.company_master (
                company_unique_id, company_name, website_url, industry,
                employee_count, address_city, address_state, linkedin_url,
                source_system, source_record_id, import_batch_id,
                validated_at, validated_by, promoted_from_intake_at
            )
            SELECT
                '04.04.01.' ||
                LPAD(((%s + ROW_NUMBER() OVER (ORDER BY r.company_unique_id) - 1) %% 99 + 1)::TEXT, 2, '0') || '.' ||
                LPAD((%s + ROW_NUMBER() OVER (ORDER BY r.company_unique_id) - 1)::TEXT, 5, '0') || '.' ||
                LPAD(((%s + ROW_NUMBER() OVER (ORDER BY r.company_unique_id) - 1) %% 1000)::TEXT, 3, '0'),
                r.company_name,
                CASE WHEN r.domain LIKE 'http%%' THEN r.domain ELSE 'http://' || r.domain END,
                r.industry,
                r.employee_count,
                r.city,
                r.state,
                r.website,
                'clay_import',
                r.company_unique_id,
                'clay_domain_enrichment_' || TO_CHAR(NOW(), 'YYYYMMDD'),
                NOW(),
                'import_clay_domains.py',
                NOW()
            FROM intake.company_raw_wv r
            WHERE r.domain IS NOT NULL AND LENGTH(TRIM(r.domain)) > 0
              AND r.company_name IS NOT NULL AND LENGTH(TRIM(r.company_name)) >= 3
              AND r.employee_count >= 50
              AND r.state IN ('PA', 'VA', 'MD', 'OH', 'WV', 'KY', 'DE', 'OK')
              AND NOT EXISTS (
                  SELECT 1 FROM company.company_master cm
                  WHERE LOWER(TRIM(cm.company_name)) = LOWER(TRIM(r.company_name))
                    AND cm.address_state = r.state
              )
            ON CONFLICT (company_unique_id) DO NOTHING
        ''', (next_seq, next_seq, next_seq))
        promoted = cur.rowcount
        conn.commit()
    else:
        cur.execute('''
            SELECT COUNT(*) as cnt
            FROM intake.company_raw_wv r
            WHERE r.domain IS NOT NULL AND LENGTH(TRIM(r.domain)) > 0
              AND r.company_name IS NOT NULL AND LENGTH(TRIM(r.company_name)) >= 3
              AND r.employee_count >= 50
              AND r.state IN ('PA', 'VA', 'MD', 'OH', 'WV', 'KY', 'DE', 'OK')
              AND NOT EXISTS (
                  SELECT 1 FROM company.company_master cm
                  WHERE LOWER(TRIM(cm.company_name)) = LOWER(TRIM(r.company_name))
                    AND cm.address_state = r.state
              )
        ''')
        promoted = cur.fetchone()['cnt']

    print(f"  {'Would promote' if dry_run else 'Promoted'}: {promoted:,} records")
    print()

    # Final count
    cur.execute('SELECT COUNT(*) as cnt FROM company.company_master')
    total = cur.fetchone()['cnt']

    print('=' * 70)
    print('FINAL RESULTS')
    print('=' * 70)
    print(f"Intake records updated: {updated_intake:,}")
    print(f"Records promoted: {promoted:,}")
    print(f"Total in company_master: {total:,}")

    if dry_run:
        print("\n[DRY RUN - No changes made]")

    cur.close()
    conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('csv_file', help='Clay CSV with enriched domains')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    if not os.path.exists(args.csv_file):
        print(f"Error: File not found: {args.csv_file}")
        sys.exit(1)

    import_and_promote(args.csv_file, args.dry_run)


if __name__ == '__main__':
    main()
