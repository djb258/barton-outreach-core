#!/usr/bin/env python3
"""
Intake Company Validation Pipeline
====================================

Purpose:
--------
Validates ALL companies in intake.company_raw_intake table using strict validation rules.
Updates validation flags (validated, validation_notes, validated_at, validated_by) in the database.
Outputs results to DuckDB for Garage 2.0 enrichment pipeline.

Author: Claude Code
Created: 2025-11-18
Barton ID: 04.04.02.04.50000.###
"""

import os
import sys
import re
from datetime import datetime
import psycopg2
from dotenv import load_dotenv
import duckdb

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

SNAPSHOT_VERSION = datetime.now().isoformat(timespec='seconds').replace(':', '').replace('-', '').replace('T', '')
DUCKDB_PATH = os.path.join(os.path.dirname(__file__), 'duck', 'outreach_workbench.duckdb')

# Validation configuration
VALIDATED_BY = "validate_intake_companies.py"
PLACEHOLDER_PATTERNS = [
    r'^\s*$',           # Empty or whitespace only
    r'^n/?a$',          # n/a or N/A
    r'^none$',          # none
    r'^null$',          # null
    r'^unknown$',       # unknown
    r'^tbd$',           # tbd
    r'^test',           # test*
    r'^example',        # example*
    r'^placeholder',    # placeholder*
]

# Statistics tracking
validation_stats = {
    'total_scanned': 0,
    'total_valid': 0,
    'total_invalid': 0,
    'failure_breakdown': {
        'company_name_missing': 0,
        'company_name_placeholder': 0,
        'website_missing': 0,
        'website_invalid': 0,
        'linkedin_missing': 0,
        'linkedin_invalid': 0,
        'industry_missing': 0,
        'industry_placeholder': 0,
    }
}

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def is_null_or_empty(value):
    """Check if value is None, empty string, or whitespace only."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == '':
        return True
    return False

def is_placeholder(value):
    """Check if value matches common placeholder patterns."""
    if is_null_or_empty(value):
        return True

    value_str = str(value).lower().strip()
    for pattern in PLACEHOLDER_PATTERNS:
        if re.match(pattern, value_str, re.IGNORECASE):
            return True
    return False

def validate_company_name(name):
    """
    Validate company name.

    Rules:
    - Must not be null/empty
    - Must not be a placeholder
    - Must be at least 2 characters

    Returns: (is_valid: bool, error_type: str or None)
    """
    if is_null_or_empty(name):
        return False, "missing"

    if is_placeholder(name):
        return False, "placeholder"

    name_str = str(name).strip()
    if len(name_str) < 2:
        return False, "too_short"

    return True, None

def validate_website_url(url):
    """
    Validate website URL.

    Rules:
    - Must not be null/empty
    - Must not be a placeholder
    - Must contain at least one dot (for TLD)
    - Must match basic domain pattern

    Returns: (is_valid: bool, error_type: str or None)
    """
    if is_null_or_empty(url):
        return False, "missing"

    if is_placeholder(url):
        return False, "placeholder"

    url_str = str(url).strip().lower()

    # Remove protocol if present
    url_str = re.sub(r'^https?://', '', url_str)
    url_str = re.sub(r'^www\.', '', url_str)

    # Must have a TLD
    if '.' not in url_str:
        return False, "no_tld"

    # Extract domain part (before first slash)
    url_domain = url_str.split('/')[0]

    # Basic domain validation (alphanumeric, dots, hyphens)
    # Must end with valid TLD pattern
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$'
    if not re.match(domain_pattern, url_domain):
        return False, "invalid_format"

    return True, None

def validate_linkedin_url(url):
    """
    Validate LinkedIn URL.

    Rules:
    - Must not be null/empty
    - Must not be a placeholder
    - Must contain 'linkedin.com'
    - Must contain /company/ or /in/ path

    Returns: (is_valid: bool, error_type: str or None)
    """
    if is_null_or_empty(url):
        return False, "missing"

    if is_placeholder(url):
        return False, "placeholder"

    url_str = str(url).strip().lower()

    # Must be a linkedin.com URL
    if 'linkedin.com' not in url_str:
        return False, "not_linkedin"

    # Must have company or person profile path
    if '/company/' not in url_str and '/in/' not in url_str:
        return False, "no_profile_path"

    return True, None

def validate_industry(industry):
    """
    Validate industry field.

    Rules:
    - Must not be null/empty
    - Must not be a placeholder

    Returns: (is_valid: bool, error_type: str or None)
    """
    if is_null_or_empty(industry):
        return False, "missing"

    if is_placeholder(industry):
        return False, "placeholder"

    return True, None

def validate_company_record(company):
    """
    Validate a complete company record from intake.company_raw_intake.

    Args:
        company: dict with keys matching intake.company_raw_intake columns

    Returns:
        (is_valid: bool, errors: list of str, validation_notes: str)
    """
    errors = []
    field_errors = []

    # Validate company name (column: 'company')
    is_valid, error_type = validate_company_name(company.get('company'))
    if not is_valid:
        field_name = f'company_name_{error_type}'
        errors.append(field_name)
        field_errors.append(f"company: {error_type}")
        validation_stats['failure_breakdown'][field_name] = validation_stats['failure_breakdown'].get(field_name, 0) + 1

    # Validate website (column: 'website')
    is_valid, error_type = validate_website_url(company.get('website'))
    if not is_valid:
        field_name = f'website_{error_type}'
        errors.append(field_name)
        field_errors.append(f"website: {error_type}")
        validation_stats['failure_breakdown'][field_name] = validation_stats['failure_breakdown'].get(field_name, 0) + 1

    # Validate LinkedIn (column: 'company_linkedin_url')
    is_valid, error_type = validate_linkedin_url(company.get('company_linkedin_url'))
    if not is_valid:
        field_name = f'linkedin_{error_type}'
        errors.append(field_name)
        field_errors.append(f"linkedin: {error_type}")
        validation_stats['failure_breakdown'][field_name] = validation_stats['failure_breakdown'].get(field_name, 0) + 1

    # Validate industry (column: 'industry')
    is_valid, error_type = validate_industry(company.get('industry'))
    if not is_valid:
        field_name = f'industry_{error_type}'
        errors.append(field_name)
        field_errors.append(f"industry: {error_type}")
        validation_stats['failure_breakdown'][field_name] = validation_stats['failure_breakdown'].get(field_name, 0) + 1

    is_valid = len(errors) == 0
    validation_notes = '; '.join(field_errors) if field_errors else 'All validations passed'

    return is_valid, errors, validation_notes

# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    print("=" * 80)
    print("INTAKE COMPANY VALIDATION PIPELINE")
    print("=" * 80)
    print()
    print(f"Snapshot Version: {SNAPSHOT_VERSION}")
    print(f"DuckDB Path: {DUCKDB_PATH}")
    print(f"Validated By: {VALIDATED_BY}")
    print()

    # ========================================================================
    # STEP 1: Connect to Neon PostgreSQL
    # ========================================================================
    print("STEP 1: Connecting to Neon PostgreSQL")
    print("-" * 80)

    try:
        neon_conn = psycopg2.connect(
            host=os.getenv('NEON_HOST'),
            database=os.getenv('NEON_DATABASE'),
            user=os.getenv('NEON_USER'),
            password=os.getenv('NEON_PASSWORD'),
            sslmode='require'
        )
        neon_cursor = neon_conn.cursor()
        print("[OK] Connected to Neon PostgreSQL")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to connect to Neon PostgreSQL")
        print(f"   {e}")
        sys.exit(1)

    # ========================================================================
    # STEP 2: Pull ALL companies from intake.company_raw_intake
    # ========================================================================
    print("STEP 2: Pulling ALL Companies from intake.company_raw_intake")
    print("-" * 80)

    try:
        neon_cursor.execute("""
            SELECT
                id,
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
                company_country,
                company_postal_code,
                company_address,
                company_phone,
                sic_codes,
                founded_year,
                created_at,
                state_abbrev,
                import_batch_id,
                validated,
                validation_notes,
                validated_at,
                validated_by
            FROM intake.company_raw_intake
            ORDER BY id;
        """)

        column_names = [desc[0] for desc in neon_cursor.description]
        companies = []
        for row in neon_cursor.fetchall():
            company = dict(zip(column_names, row))
            companies.append(company)

        print(f"[OK] Pulled {len(companies)} companies from intake.company_raw_intake")
        print()
    except Exception as e:
        print(f"[ERROR] ERROR: Failed to pull companies from Neon")
        print(f"   {e}")
        neon_cursor.close()
        neon_conn.close()
        sys.exit(1)

    # ========================================================================
    # STEP 3: Validate all companies with strict rules
    # ========================================================================
    print("STEP 3: Validating All Companies (Strict Rules)")
    print("-" * 80)
    print()

    valid_companies = []
    invalid_companies = []
    update_queries = []

    for idx, company in enumerate(companies, start=1):
        validation_stats['total_scanned'] += 1

        # Validate the company record
        is_valid, errors, validation_notes = validate_company_record(company)

        if is_valid:
            validation_stats['total_valid'] += 1
            valid_companies.append(company)

            # Prepare UPDATE query to mark as validated=TRUE
            update_queries.append({
                'id': company['id'],
                'validated': True,
                'validation_notes': validation_notes,
                'validated_at': datetime.now(),
                'validated_by': VALIDATED_BY
            })
        else:
            validation_stats['total_invalid'] += 1
            invalid_companies.append({
                **company,
                'validation_errors': errors,
                'validation_notes_new': validation_notes,
                'validation_timestamp': datetime.now().isoformat()
            })

            # Prepare UPDATE query to mark as validated=FALSE
            update_queries.append({
                'id': company['id'],
                'validated': False,
                'validation_notes': validation_notes,
                'validated_at': datetime.now(),
                'validated_by': VALIDATED_BY
            })

        # Progress indicator
        if idx % 50 == 0 or idx == len(companies):
            print(f"  Validated {idx}/{len(companies)} companies...")

    print()
    print(f"[OK] Validation Complete:")
    print(f"   Valid: {validation_stats['total_valid']}")
    print(f"   Invalid: {validation_stats['total_invalid']}")
    print()

    # ========================================================================
    # STEP 4: Update validation flags in Neon
    # ========================================================================
    print("STEP 4: Updating Validation Flags in Neon")
    print("-" * 80)

    try:
        for update in update_queries:
            neon_cursor.execute("""
                UPDATE intake.company_raw_intake
                SET validated = %s,
                    validation_notes = %s,
                    validated_at = %s,
                    validated_by = %s
                WHERE id = %s;
            """, (
                update['validated'],
                update['validation_notes'],
                update['validated_at'],
                update['validated_by'],
                update['id']
            ))

        neon_conn.commit()
        print(f"[OK] Updated {len(update_queries)} records in intake.company_raw_intake")
        print()
    except Exception as e:
        print(f"[ERROR] ERROR: Failed to update validation flags in Neon")
        print(f"   {e}")
        neon_conn.rollback()
        neon_cursor.close()
        neon_conn.close()
        sys.exit(1)

    # Close Neon connection
    neon_cursor.close()
    neon_conn.close()

    # ========================================================================
    # STEP 5: Connect to DuckDB
    # ========================================================================
    print("STEP 5: Connecting to DuckDB")
    print("-" * 80)

    try:
        os.makedirs(os.path.dirname(DUCKDB_PATH), exist_ok=True)
        duck_conn = duckdb.connect(DUCKDB_PATH)
        print(f"[OK] Connected to DuckDB: {DUCKDB_PATH}")
        print()
    except Exception as e:
        print(f"[ERROR] ERROR: Failed to connect to DuckDB")
        print(f"   {e}")
        sys.exit(1)

    # ========================================================================
    # STEP 6: Create/update snapshot tracking table
    # ========================================================================
    print("STEP 6: Creating/Updating Snapshot Tracking")
    print("-" * 80)

    try:
        # Create validation_snapshots table if not exists
        duck_conn.execute("""
            CREATE TABLE IF NOT EXISTS validation_snapshots (
                snapshot_id INTEGER PRIMARY KEY,
                snapshot_version VARCHAR(50) NOT NULL,
                total_companies INTEGER,
                companies_good INTEGER,
                companies_bad INTEGER,
                validation_timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # Add source_table column if it doesn't exist
        try:
            duck_conn.execute("""
                ALTER TABLE validation_snapshots ADD COLUMN source_table VARCHAR(100);
            """)
        except Exception:
            pass  # Column already exists

        # Get next snapshot_id
        result = duck_conn.execute("SELECT COALESCE(MAX(snapshot_id), 0) + 1 FROM validation_snapshots;").fetchone()
        snapshot_id = result[0]

        # Insert new snapshot
        duck_conn.execute("""
            INSERT INTO validation_snapshots (
                snapshot_id,
                snapshot_version,
                source_table,
                total_companies,
                companies_good,
                companies_bad,
                validation_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            snapshot_id,
            SNAPSHOT_VERSION,
            'intake.company_raw_intake',
            validation_stats['total_scanned'],
            validation_stats['total_valid'],
            validation_stats['total_invalid'],
            datetime.now()
        ))

        print(f"[OK] Snapshot tracking updated: {SNAPSHOT_VERSION}")
        print()
    except Exception as e:
        print(f"[ERROR] ERROR: Failed to update snapshot tracking")
        print(f"   {e}")
        duck_conn.close()
        sys.exit(1)

    # ========================================================================
    # STEP 7: Write invalid companies to DuckDB (companies_bad)
    # ========================================================================
    print("STEP 7: Writing Invalid Companies to DuckDB")
    print("-" * 80)

    try:
        import pandas as pd

        if invalid_companies:
            # Convert to DataFrame
            invalid_df = pd.DataFrame(invalid_companies)

            # Drop existing table and create new one
            duck_conn.execute("DROP TABLE IF EXISTS companies_bad;")
            duck_conn.execute("""
                CREATE TABLE companies_bad AS
                SELECT * FROM invalid_df;
            """)

            print(f"[OK] Wrote {len(invalid_companies)} invalid companies to companies_bad table")
        else:
            print("[OK] No invalid companies found (all records passed validation)")
        print()
    except Exception as e:
        print(f"[ERROR] ERROR: Failed to write invalid companies to DuckDB")
        print(f"   {e}")
        duck_conn.close()
        sys.exit(1)

    # ========================================================================
    # STEP 8: Write valid companies to DuckDB (companies_good)
    # ========================================================================
    print("STEP 8: Writing Valid Companies to DuckDB")
    print("-" * 80)

    try:
        if valid_companies:
            # Convert to DataFrame
            valid_df = pd.DataFrame(valid_companies)

            # Drop existing table and create new one
            duck_conn.execute("DROP TABLE IF EXISTS companies_good;")
            duck_conn.execute("""
                CREATE TABLE companies_good AS
                SELECT * FROM valid_df;
            """)

            print(f"[OK] Wrote {len(valid_companies)} valid companies to companies_good table")
        else:
            print("[OK] No valid companies found (all records failed validation)")
        print()
    except Exception as e:
        print(f"[ERROR] ERROR: Failed to write valid companies to DuckDB")
        print(f"   {e}")
        duck_conn.close()
        sys.exit(1)

    # ========================================================================
    # STEP 9: Verify DuckDB tables
    # ========================================================================
    print("STEP 9: Verifying DuckDB Tables")
    print("-" * 80)

    try:
        # Check companies_bad
        result = duck_conn.execute("SELECT COUNT(*) FROM companies_bad;").fetchone()
        bad_count = result[0]
        print(f"[OK] companies_bad: {bad_count} records")

        # Check companies_good
        result = duck_conn.execute("SELECT COUNT(*) FROM companies_good;").fetchone()
        good_count = result[0]
        print(f"[OK] companies_good: {good_count} records")

        # Check validation_snapshots
        result = duck_conn.execute("SELECT COUNT(*) FROM validation_snapshots;").fetchone()
        snapshot_count = result[0]
        print(f"[OK] validation_snapshots: {snapshot_count} snapshots")
        print()
    except Exception as e:
        print(f"[ERROR] ERROR: Failed to verify DuckDB tables")
        print(f"   {e}")

    duck_conn.close()

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("=" * 80)
    print("INTAKE COMPANY VALIDATION SUMMARY")
    print("=" * 80)
    print()
    print(f"Snapshot Version: {SNAPSHOT_VERSION}")
    print(f"Source Table: intake.company_raw_intake")
    print()
    print("VALIDATION RESULTS:")
    print(f"  Total Companies Scanned: {validation_stats['total_scanned']}")
    print(f"  Companies VALID: {validation_stats['total_valid']} ({validation_stats['total_valid']/validation_stats['total_scanned']*100:.1f}%)")
    print(f"  Companies INVALID: {validation_stats['total_invalid']} ({validation_stats['total_invalid']/validation_stats['total_scanned']*100:.1f}%)")
    print()
    print("FAILURE BREAKDOWN BY FIELD:")

    # Sort failure breakdown by count
    sorted_failures = sorted(
        validation_stats['failure_breakdown'].items(),
        key=lambda x: x[1],
        reverse=True
    )

    for field, count in sorted_failures:
        if count > 0:
            percentage = (count / validation_stats['total_scanned']) * 100
            print(f"  {field}: {count} ({percentage:.1f}%)")

    print()
    print("DATABASE UPDATES:")
    print(f"  intake.company_raw_intake: Updated validation flags for all {validation_stats['total_scanned']} records")
    print(f"    - validated=TRUE: {validation_stats['total_valid']} records")
    print(f"    - validated=FALSE: {validation_stats['total_invalid']} records")
    print()
    print("DUCKDB TABLES UPDATED:")
    print(f"  companies_bad: {validation_stats['total_invalid']} records (ready for Garage 2.0)")
    print(f"  companies_good: {validation_stats['total_valid']} records")
    print(f"  validation_snapshots: New snapshot added")
    print()
    print("NEXT STEPS:")
    print("  1. Review invalid companies in DuckDB:")
    print(f"     duckdb {DUCKDB_PATH}")
    print("     SELECT * FROM companies_bad LIMIT 10;")
    print()
    print("  2. Verify validation flags in Neon:")
    print("     SELECT validated, COUNT(*) FROM intake.company_raw_intake GROUP BY validated;")
    print()
    print("  3. Run Garage 2.0 enrichment on invalid companies:")
    print("     python enrichment_garage_2_0.py --snapshot " + SNAPSHOT_VERSION)
    print()
    print("=" * 80)
    print("[OK] INTAKE VALIDATION COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
