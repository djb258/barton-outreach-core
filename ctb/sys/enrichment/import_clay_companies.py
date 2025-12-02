#!/usr/bin/env python3
"""
Clay.com Company CSV Import Script
===================================
Imports company data from Clay CSV exports into intake.company_raw_from_clay

Usage:
    python import_clay_companies.py <csv_file> [--dry-run]

Example:
    python import_clay_companies.py "C:/Users/CUSTOM PC/Downloads/Find-companies-Table-Default-view-export.csv"
"""

import csv
import os
import sys
import argparse
import uuid
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import execute_values

# Neon connection settings
NEON_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}

# Clay CSV column mapping
CLAY_COLUMN_MAP = {
    'Find companies': 'skip',           # Empty search indicator
    'Name': 'company_name',
    'Description': 'description',
    'Primary Industry': 'industry_enriched',
    'Size': 'employee_size_raw',        # Needs parsing: "51-200 employees"
    'Type': 'company_type',
    'Location': 'location_raw',         # Needs splitting: "City, State"
    'Country': 'country',
    'Domain': 'website_enriched',
    'LinkedIn URL': 'linkedin_company_url'
}

# State abbreviation mapping for normalization
STATE_ABBREV = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
    'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
    'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
    'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
    'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
    'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
    'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
    'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
    'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
    'Wisconsin': 'WI', 'Wyoming': 'WY', 'District of Columbia': 'DC'
}

def parse_employee_count(size_str):
    """
    Parse Clay employee size string to integer midpoint.
    Examples:
        "51-200 employees" -> 125
        "201-500 employees" -> 350
        "1001-5000 employees" -> 3000
        "10001+ employees" -> 15000
    """
    if not size_str:
        return None

    # Remove "employees" and clean up
    size_str = size_str.lower().replace('employees', '').replace(' ', '').strip()

    # Handle 10001+ style
    if '+' in size_str:
        base = size_str.replace('+', '')
        try:
            return int(base) + int(int(base) * 0.5)  # 10001+ -> ~15000
        except:
            return None

    # Handle range like "51-200"
    if '-' in size_str:
        try:
            parts = size_str.split('-')
            low = int(parts[0])
            high = int(parts[1])
            return (low + high) // 2  # Return midpoint
        except:
            return None

    # Handle single number
    try:
        return int(size_str)
    except:
        return None


def parse_location(location_str):
    """
    Parse Clay location string into city and state.
    Examples:
        "Morgantown, West Virginia" -> ("Morgantown", "WV")
        "Charleston, WV" -> ("Charleston", "WV")
        "MARTINSBURG, WV" -> ("Martinsburg", "WV")
    """
    if not location_str:
        return None, None

    parts = [p.strip() for p in location_str.split(',')]

    if len(parts) >= 2:
        city = parts[0].title()  # Normalize to Title Case
        state_raw = parts[-1].strip()

        # Check if it's already abbreviated
        if len(state_raw) == 2:
            state = state_raw.upper()
        else:
            # Look up full state name
            state = STATE_ABBREV.get(state_raw.title(), state_raw.upper()[:2])

        return city, state
    elif len(parts) == 1:
        return parts[0].title(), None

    return None, None


def normalize_company_type(type_str):
    """
    Normalize Clay company type to standard values.
    """
    if not type_str:
        return None

    type_lower = type_str.lower().strip()

    type_map = {
        'privately held': 'private',
        'private': 'private',
        'publicly held': 'public',
        'public': 'public',
        'public company': 'public',
        'non profit': 'nonprofit',
        'nonprofit': 'nonprofit',
        'non-profit': 'nonprofit',
        'government agency': 'government',
        'government': 'government',
        'educational': 'educational',
        'educational institution': 'educational',
        'partnership': 'partnership',
        'sole proprietorship': 'sole_proprietorship',
        'self-employed': 'self_employed'
    }

    return type_map.get(type_lower, type_str.lower().replace(' ', '_'))


def generate_company_id(state):
    """
    Generate a temporary unique ID for the company.
    Format: CLAY-{STATE}-{UUID_SHORT}
    Final Barton ID assigned on promotion to company_master.
    """
    state_code = state if state else 'XX'
    short_uuid = str(uuid.uuid4())[:8].upper()
    return f"CLAY-{state_code}-{short_uuid}"


def read_clay_csv(filepath):
    """
    Read Clay CSV export and parse into normalized records.
    """
    records = []

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Skip empty rows
            if not row.get('Name'):
                continue

            # Parse location
            city, state = parse_location(row.get('Location', ''))

            # Parse employee count
            employee_count = parse_employee_count(row.get('Size', ''))

            # Normalize company type
            company_type = normalize_company_type(row.get('Type', ''))

            # Generate temporary ID
            company_id = generate_company_id(state)

            # Build record
            record = {
                'company_unique_id': company_id,
                'company_name': row.get('Name', '').strip(),
                'website_original': None,  # No original, this is discovery
                'city': city,
                'state': state,
                'website_enriched': row.get('Domain', '').strip() or None,
                'employee_count_enriched': employee_count,
                'industry_enriched': row.get('Primary Industry', '').strip() or None,
                'linkedin_company_url': row.get('LinkedIn URL', '').strip() or None,
                'company_type': company_type,
                'clay_enriched_at': datetime.now(timezone.utc),
                'enrichment_status': 'received'
            }

            records.append(record)

    return records


def insert_to_neon(records, dry_run=False):
    """
    Insert records into intake.company_raw_wv table.
    Table structure:
        company_unique_id, company_name, domain, website, industry,
        employee_count, phone, address, city, state, zip, created_at
    """
    if not records:
        print("No records to insert.")
        return 0

    if dry_run:
        print(f"\n[DRY RUN] Would insert {len(records)} records:")
        for i, r in enumerate(records[:5]):
            print(f"  {i+1}. {r['company_name']} ({r['city']}, {r['state']}) - {r['industry_enriched']}")
        if len(records) > 5:
            print(f"  ... and {len(records) - 5} more")
        return len(records)

    # Connect to Neon
    conn = psycopg2.connect(**NEON_CONFIG)
    cur = conn.cursor()

    # Prepare insert SQL for intake.company_raw_wv
    insert_sql = """
        INSERT INTO intake.company_raw_wv (
            company_unique_id,
            company_name,
            domain,
            website,
            industry,
            employee_count,
            city,
            state,
            created_at
        ) VALUES %s
        ON CONFLICT (company_unique_id) DO UPDATE SET
            company_name = EXCLUDED.company_name,
            domain = EXCLUDED.domain,
            website = EXCLUDED.website,
            industry = EXCLUDED.industry,
            employee_count = EXCLUDED.employee_count,
            city = EXCLUDED.city,
            state = EXCLUDED.state
    """

    # Convert records to tuples matching table structure
    values = [
        (
            r['company_unique_id'],
            r['company_name'],
            r['website_enriched'],           # domain
            r['linkedin_company_url'],       # website (storing LinkedIn URL here)
            r['industry_enriched'],          # industry
            r['employee_count_enriched'],    # employee_count
            r['city'],
            r['state'],
            r['clay_enriched_at']            # created_at
        )
        for r in records
    ]

    try:
        execute_values(cur, insert_sql, values)
        conn.commit()
        inserted = cur.rowcount
        print(f"Successfully inserted/updated {inserted} records in intake.company_raw_wv")
        return inserted
    except Exception as e:
        conn.rollback()
        print(f"Error inserting records: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def print_summary(records):
    """
    Print summary of parsed records.
    """
    if not records:
        print("No records found.")
        return

    # Count by state
    states = {}
    industries = {}

    for r in records:
        state = r['state'] or 'Unknown'
        states[state] = states.get(state, 0) + 1

        industry = r['industry_enriched'] or 'Unknown'
        industries[industry] = industries.get(industry, 0) + 1

    print(f"\n{'='*60}")
    print(f"CLAY IMPORT SUMMARY")
    print(f"{'='*60}")
    print(f"Total companies: {len(records)}")

    print(f"\nBy State:")
    for state, count in sorted(states.items(), key=lambda x: -x[1]):
        print(f"  {state}: {count}")

    print(f"\nTop Industries:")
    for industry, count in sorted(industries.items(), key=lambda x: -x[1])[:10]:
        print(f"  {industry}: {count}")

    print(f"\nSample Records:")
    for i, r in enumerate(records[:3]):
        print(f"  {i+1}. {r['company_name']}")
        print(f"     Location: {r['city']}, {r['state']}")
        print(f"     Industry: {r['industry_enriched']}")
        print(f"     Size: {r['employee_count_enriched']} employees")
        print(f"     Website: {r['website_enriched']}")
        print(f"     LinkedIn: {r['linkedin_company_url']}")
        print()


def main():
    parser = argparse.ArgumentParser(description='Import Clay company CSV to Neon')
    parser.add_argument('csv_file', help='Path to Clay CSV export file')
    parser.add_argument('--dry-run', action='store_true', help='Parse and show summary without inserting')

    args = parser.parse_args()

    # Check file exists
    if not os.path.exists(args.csv_file):
        print(f"Error: File not found: {args.csv_file}")
        sys.exit(1)

    print(f"Reading Clay CSV: {args.csv_file}")

    # Parse CSV
    records = read_clay_csv(args.csv_file)

    # Print summary
    print_summary(records)

    # Insert to database
    if args.dry_run:
        print("\n[DRY RUN MODE - No data inserted]")
        insert_to_neon(records, dry_run=True)
    else:
        print("\nInserting to Neon database...")
        inserted = insert_to_neon(records, dry_run=False)
        print(f"\nDone! {inserted} companies imported to intake.company_raw_from_clay")
        print("Run promotion job to move to marketing.company_master")


if __name__ == '__main__':
    main()
