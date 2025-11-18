#!/usr/bin/env python3
"""
Import Apollo Companies from CSV to intake.company_raw_intake

Imports WV companies with Apollo IDs from CSV export.

Author: Claude Code
Created: 2025-11-18
Barton ID: 04.04.02.04.50000.###
"""

import os
import csv
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv('../../.env')

# CSV file path
CSV_FILE = "c:/Users/CUSTOM PC/Desktop/WV Companies.csv"

# Import batch ID for tracking
IMPORT_BATCH_ID = f"apollo_wv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def import_companies():
    """Import companies from CSV to intake table"""

    print("=" * 80)
    print("APOLLO COMPANIES IMPORT TO INTAKE")
    print("=" * 80)
    print()
    print(f"CSV File: {CSV_FILE}")
    print(f"Import Batch ID: {IMPORT_BATCH_ID}")
    print()

    # Connect to database
    try:
        conn = psycopg2.connect(
            host=os.getenv('NEON_HOST'),
            database=os.getenv('NEON_DATABASE'),
            user=os.getenv('NEON_USER'),
            password=os.getenv('NEON_PASSWORD'),
            sslmode='require'
        )
        cursor = conn.cursor()
        print("[OK] Connected to Neon PostgreSQL")
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return

    # Read CSV file
    companies = []
    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append(row)

    print(f"[OK] Read {len(companies)} companies from CSV")
    print()

    # Import companies
    print("Importing Companies to intake.company_raw_intake")
    print("-" * 80)

    imported = 0
    skipped = 0
    errors = 0

    for idx, company in enumerate(companies, 1):
        company_name = company.get('Company Name', '').strip()
        apollo_id = company.get('Apollo Account Id', '').strip()

        if not company_name:
            print(f"  [{idx}/{len(companies)}] SKIPPED: No company name")
            skipped += 1
            continue

        try:
            # Check if company already exists (by company name and website)
            cursor.execute("""
                SELECT id FROM intake.company_raw_intake
                WHERE company = %s OR website = %s
                LIMIT 1;
            """, (
                company.get('Company Name', '').strip(),
                company.get('Website', '').strip()
            ))

            existing = cursor.fetchone()

            if existing:
                # Update existing record with Apollo ID and latest data
                cursor.execute("""
                    UPDATE intake.company_raw_intake
                    SET
                        apollo_id = %s,
                        num_employees = %s,
                        industry = %s,
                        company_linkedin_url = %s,
                        facebook_url = %s,
                        twitter_url = %s,
                        company_street = %s,
                        company_city = %s,
                        company_state = %s,
                        company_postal_code = %s,
                        company_address = %s,
                        company_phone = %s,
                        sic_codes = %s,
                        import_batch_id = %s,
                        validated = FALSE,
                        enrichment_attempt = 0,
                        chronic_bad = FALSE
                    WHERE id = %s;
                """, (
                    apollo_id if apollo_id else None,
                    int(company.get('# Employees', 0)) if company.get('# Employees', '').strip() else None,
                    company.get('Industry', '').strip().lower(),
                    company.get('Company Linkedin Url', '').strip(),
                    company.get('Facebook Url', '').strip(),
                    company.get('Twitter Url', '').strip(),
                    company.get('Company Street', '').strip(),
                    company.get('Company City', '').strip(),
                    company.get('Company State', '').strip(),
                    company.get('Company Postal Code', '').strip(),
                    company.get('Company Address', '').strip(),
                    company.get('Company Phone', '').strip(),
                    company.get('SIC Codes', '').strip(),
                    IMPORT_BATCH_ID,
                    existing[0]
                ))
                action = "UPDATED"
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO intake.company_raw_intake (
                        company,
                        company_name_for_emails,
                        num_employees,
                        industry,
                        website,
                        company_linkedin_url,
                        facebook_url,
                        twitter_url,
                        company_street,
                        company_city,
                        company_state,
                        company_postal_code,
                        company_address,
                        company_phone,
                        apollo_id,
                        sic_codes,
                        state_abbrev,
                        import_batch_id,
                        validated,
                        enrichment_attempt,
                        chronic_bad,
                        created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, NOW()
                    );
                """, (
                    company.get('Company Name', '').strip(),
                    company.get('Company Name for Emails', '').strip(),
                    int(company.get('# Employees', 0)) if company.get('# Employees', '').strip() else None,
                    company.get('Industry', '').strip().lower(),
                    company.get('Website', '').strip(),
                    company.get('Company Linkedin Url', '').strip(),
                    company.get('Facebook Url', '').strip(),
                    company.get('Twitter Url', '').strip(),
                    company.get('Company Street', '').strip(),
                    company.get('Company City', '').strip(),
                    company.get('Company State', '').strip(),
                    company.get('Company Postal Code', '').strip(),
                    company.get('Company Address', '').strip(),
                    company.get('Company Phone', '').strip(),
                    apollo_id if apollo_id else None,
                    company.get('SIC Codes', '').strip(),
                    'WV',  # State abbreviation
                    IMPORT_BATCH_ID,
                    False,  # Not validated yet
                    0,  # Initial enrichment attempt
                    False  # Not chronic bad
                ))
                action = "INSERTED"

            # Print progress (ASCII-safe)
            company_name_safe = company_name.encode('ascii', 'ignore').decode('ascii')
            status = "+" if apollo_id else "-"
            apollo_status = f"Apollo ID: {apollo_id[:12]}..." if apollo_id else "No Apollo ID"
            print(f"  [{idx}/{len(companies)}] {action} {status} {company_name_safe} ({apollo_status})")

            imported += 1

        except Exception as e:
            # ASCII-safe error messages
            company_name_safe = company_name.encode('ascii', 'ignore').decode('ascii')
            error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
            print(f"  [{idx}/{len(companies)}] ERROR: {company_name_safe} - {error_msg}")
            errors += 1
            conn.rollback()  # Rollback failed transaction

    # Commit transaction
    conn.commit()
    print()
    print("[OK] Import complete")
    print()

    # Summary
    print("=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)
    print(f"Total Companies in CSV: {len(companies)}")
    print(f"Imported: {imported}")
    print(f"Skipped: {skipped}")
    print(f"Errors: {errors}")
    print()

    # Check Apollo ID coverage
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE apollo_id IS NOT NULL AND apollo_id != '') as with_apollo_id,
            COUNT(*) FILTER (WHERE apollo_id IS NULL OR apollo_id = '') as without_apollo_id
        FROM intake.company_raw_intake
        WHERE import_batch_id = %s;
    """, (IMPORT_BATCH_ID,))

    total, with_apollo, without_apollo = cursor.fetchone()

    print("Apollo ID Coverage:")
    print(f"  With Apollo ID: {with_apollo} ({100 * with_apollo / total if total > 0 else 0:.1f}%)")
    print(f"  Without Apollo ID: {without_apollo} ({100 * without_apollo / total if total > 0 else 0:.1f}%)")
    print()

    print(f"Import Batch ID: {IMPORT_BATCH_ID}")
    print()
    print("Next Steps:")
    print("  1. Run validation: python validate_and_promote_companies.py")
    print("  2. Check promoted companies in marketing.company_master")
    print("  3. Review failed validations in intake.company_raw_intake")
    print()

    cursor.close()
    conn.close()

if __name__ == '__main__':
    import_companies()
