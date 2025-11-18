#!/usr/bin/env python3
"""
People Validation Pipeline
===========================

Purpose:
--------
Validates ALL people in marketing.people_master table using strict validation rules.
Writes failures to marketing.people_invalid and outputs to DuckDB for Garage 2.0.

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
VALIDATED_BY = "validate_people.py"
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
        'full_name_missing': 0,
        'full_name_placeholder': 0,
        'email_missing': 0,
        'email_invalid': 0,
        'linkedin_missing': 0,
        'linkedin_invalid': 0,
        'title_missing': 0,
        'title_placeholder': 0,
        'company_unique_id_missing': 0,
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

def validate_full_name(name):
    """
    Validate person's full name.

    Rules:
    - Must not be null/empty
    - Must not be a placeholder
    - Must be at least 2 characters
    - Should contain at least first and last name (space separated)

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

def validate_email(email):
    """
    Validate email address.

    Rules:
    - Must not be null/empty
    - Must not be a placeholder
    - Must contain @ symbol
    - Must have domain part with TLD

    Returns: (is_valid: bool, error_type: str or None)
    """
    if is_null_or_empty(email):
        return False, "missing"

    if is_placeholder(email):
        return False, "placeholder"

    email_str = str(email).strip().lower()

    # Must have @ symbol
    if '@' not in email_str:
        return False, "no_at_symbol"

    # Basic email pattern validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email_str):
        return False, "invalid_format"

    return True, None

def validate_linkedin_url(url):
    """
    Validate LinkedIn URL.

    Rules:
    - Must not be null/empty
    - Must not be a placeholder
    - Must contain 'linkedin.com'
    - Must contain /in/ path (person profile)

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

    # Must have person profile path
    if '/in/' not in url_str:
        return False, "no_profile_path"

    return True, None

def validate_title(title):
    """
    Validate job title.

    Rules:
    - Must not be null/empty
    - Must not be a placeholder

    Returns: (is_valid: bool, error_type: str or None)
    """
    if is_null_or_empty(title):
        return False, "missing"

    if is_placeholder(title):
        return False, "placeholder"

    return True, None

def validate_company_unique_id(company_id):
    """
    Validate company foreign key.

    Rules:
    - Must not be null/empty

    Returns: (is_valid: bool, error_type: str or None)
    """
    if is_null_or_empty(company_id):
        return False, "missing"

    return True, None

def validate_person_record(person):
    """
    Validate a complete person record from marketing.people_master.

    Args:
        person: dict with keys matching people_master columns

    Returns:
        (is_valid: bool, errors: list of str, validation_notes: str)
    """
    errors = []
    field_errors = []

    # Validate full name
    is_valid, error_type = validate_full_name(person.get('full_name'))
    if not is_valid:
        field_name = f'full_name_{error_type}'
        errors.append(field_name)
        field_errors.append(f"full_name: {error_type}")
        validation_stats['failure_breakdown'][field_name] = validation_stats['failure_breakdown'].get(field_name, 0) + 1

    # Validate email
    is_valid, error_type = validate_email(person.get('email'))
    if not is_valid:
        field_name = f'email_{error_type}'
        errors.append(field_name)
        field_errors.append(f"email: {error_type}")
        validation_stats['failure_breakdown'][field_name] = validation_stats['failure_breakdown'].get(field_name, 0) + 1

    # Validate LinkedIn
    is_valid, error_type = validate_linkedin_url(person.get('linkedin_url'))
    if not is_valid:
        field_name = f'linkedin_{error_type}'
        errors.append(field_name)
        field_errors.append(f"linkedin: {error_type}")
        validation_stats['failure_breakdown'][field_name] = validation_stats['failure_breakdown'].get(field_name, 0) + 1

    # Validate title
    is_valid, error_type = validate_title(person.get('title'))
    if not is_valid:
        field_name = f'title_{error_type}'
        errors.append(field_name)
        field_errors.append(f"title: {error_type}")
        validation_stats['failure_breakdown'][field_name] = validation_stats['failure_breakdown'].get(field_name, 0) + 1

    # Validate company_unique_id
    is_valid, error_type = validate_company_unique_id(person.get('company_unique_id'))
    if not is_valid:
        field_name = f'company_unique_id_{error_type}'
        errors.append(field_name)
        field_errors.append(f"company_unique_id: {error_type}")
        validation_stats['failure_breakdown'][field_name] = validation_stats['failure_breakdown'].get(field_name, 0) + 1

    is_valid = len(errors) == 0
    validation_notes = '; '.join(field_errors) if field_errors else 'All validations passed'

    return is_valid, errors, validation_notes

# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    print("=" * 80)
    print("PEOPLE VALIDATION PIPELINE")
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
    # STEP 2: Pull ALL people from marketing.people_master
    # ========================================================================
    print("STEP 2: Pulling ALL People from marketing.people_master")
    print("-" * 80)

    try:
        neon_cursor.execute("""
            SELECT
                unique_id,
                company_unique_id,
                company_slot_unique_id,
                first_name,
                last_name,
                full_name,
                title,
                seniority,
                department,
                email,
                work_phone_e164,
                personal_phone_e164,
                linkedin_url,
                twitter_url,
                facebook_url,
                bio,
                skills,
                education,
                certifications,
                source_system,
                source_record_id,
                promoted_from_intake_at,
                promotion_audit_log_id,
                created_at,
                updated_at,
                email_verified,
                message_key_scheduled,
                email_verification_source,
                email_verified_at
            FROM marketing.people_master
            ORDER BY unique_id;
        """)

        column_names = [desc[0] for desc in neon_cursor.description]
        people = []
        for row in neon_cursor.fetchall():
            person = dict(zip(column_names, row))
            people.append(person)

        print(f"[OK] Pulled {len(people)} people from marketing.people_master")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to pull people from Neon")
        print(f"   {e}")
        neon_cursor.close()
        neon_conn.close()
        sys.exit(1)

    # ========================================================================
    # STEP 3: Validate all people with strict rules
    # ========================================================================
    print("STEP 3: Validating All People (Strict Rules)")
    print("-" * 80)
    print()

    valid_people = []
    invalid_people = []

    for idx, person in enumerate(people, start=1):
        validation_stats['total_scanned'] += 1

        # Validate the person record
        is_valid, errors, validation_notes = validate_person_record(person)

        if is_valid:
            validation_stats['total_valid'] += 1
            valid_people.append(person)
        else:
            validation_stats['total_invalid'] += 1
            invalid_people.append({
                **person,
                'validation_errors': errors,
                'validation_notes': validation_notes,
                'validation_timestamp': datetime.now().isoformat()
            })

        # Progress indicator
        if idx % 50 == 0 or idx == len(people):
            print(f"  Validated {idx}/{len(people)} people...")

    print()
    print(f"[OK] Validation Complete:")
    print(f"   Valid: {validation_stats['total_valid']}")
    print(f"   Invalid: {validation_stats['total_invalid']}")
    print()

    # ========================================================================
    # STEP 4: Write invalid people to marketing.people_invalid
    # ========================================================================
    print("STEP 4: Writing Invalid People to marketing.people_invalid")
    print("-" * 80)

    try:
        inserted_count = 0
        for person in invalid_people:
            # Check if already in people_invalid
            neon_cursor.execute("""
                SELECT COUNT(*) FROM marketing.people_invalid
                WHERE unique_id = %s;
            """, (person['unique_id'],))

            exists = neon_cursor.fetchone()[0] > 0

            if not exists:
                # Insert into people_invalid
                neon_cursor.execute("""
                    INSERT INTO marketing.people_invalid (
                        unique_id,
                        full_name,
                        first_name,
                        last_name,
                        email,
                        title,
                        company_unique_id,
                        linkedin_url,
                        validation_status,
                        reason_code,
                        validation_errors,
                        failed_at,
                        source_table,
                        batch_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    person['unique_id'],
                    person.get('full_name'),
                    person.get('first_name'),
                    person.get('last_name'),
                    person.get('email'),
                    person.get('title'),
                    person.get('company_unique_id'),
                    person.get('linkedin_url'),
                    'failed',
                    'validation_failed',
                    ', '.join(person['validation_errors']),
                    datetime.now(),
                    'marketing.people_master',
                    SNAPSHOT_VERSION
                ))
                inserted_count += 1

        neon_conn.commit()
        print(f"[OK] Inserted {inserted_count} new invalid people records")
        print(f"    ({len(invalid_people) - inserted_count} already existed)")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to write to people_invalid")
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
        print(f"[ERROR] Failed to connect to DuckDB")
        print(f"   {e}")
        sys.exit(1)

    # ========================================================================
    # STEP 6: Create/update snapshot tracking table
    # ========================================================================
    print("STEP 6: Creating/Updating Snapshot Tracking")
    print("-" * 80)

    try:
        # Create people_validation_snapshots table if not exists
        duck_conn.execute("""
            CREATE TABLE IF NOT EXISTS people_validation_snapshots (
                snapshot_id INTEGER PRIMARY KEY,
                snapshot_version VARCHAR(50) NOT NULL,
                source_table VARCHAR(100) NOT NULL,
                total_people INTEGER,
                people_good INTEGER,
                people_bad INTEGER,
                validation_timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # Get next snapshot_id
        result = duck_conn.execute("SELECT COALESCE(MAX(snapshot_id), 0) + 1 FROM people_validation_snapshots;").fetchone()
        snapshot_id = result[0]

        # Insert new snapshot
        duck_conn.execute("""
            INSERT INTO people_validation_snapshots (
                snapshot_id,
                snapshot_version,
                source_table,
                total_people,
                people_good,
                people_bad,
                validation_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            snapshot_id,
            SNAPSHOT_VERSION,
            'marketing.people_master',
            validation_stats['total_scanned'],
            validation_stats['total_valid'],
            validation_stats['total_invalid'],
            datetime.now()
        ))

        print(f"[OK] Snapshot tracking updated: {SNAPSHOT_VERSION}")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to update snapshot tracking")
        print(f"   {e}")
        duck_conn.close()
        sys.exit(1)

    # ========================================================================
    # STEP 7: Write invalid people to DuckDB (people_bad)
    # ========================================================================
    print("STEP 7: Writing Invalid People to DuckDB")
    print("-" * 80)

    try:
        import pandas as pd

        if invalid_people:
            # Convert to DataFrame
            invalid_df = pd.DataFrame(invalid_people)

            # Drop existing table and create new one
            duck_conn.execute("DROP TABLE IF EXISTS people_bad;")
            duck_conn.execute("""
                CREATE TABLE people_bad AS
                SELECT * FROM invalid_df;
            """)

            print(f"[OK] Wrote {len(invalid_people)} invalid people to people_bad table")
        else:
            print("[OK] No invalid people found (all records passed validation)")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to write invalid people to DuckDB")
        print(f"   {e}")
        duck_conn.close()
        sys.exit(1)

    # ========================================================================
    # STEP 8: Write valid people to DuckDB (people_good)
    # ========================================================================
    print("STEP 8: Writing Valid People to DuckDB")
    print("-" * 80)

    try:
        if valid_people:
            # Convert to DataFrame
            valid_df = pd.DataFrame(valid_people)

            # Drop existing table and create new one
            duck_conn.execute("DROP TABLE IF EXISTS people_good;")
            duck_conn.execute("""
                CREATE TABLE people_good AS
                SELECT * FROM valid_df;
            """)

            print(f"[OK] Wrote {len(valid_people)} valid people to people_good table")
        else:
            print("[OK] No valid people found (all records failed validation)")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to write valid people to DuckDB")
        print(f"   {e}")
        duck_conn.close()
        sys.exit(1)

    # ========================================================================
    # STEP 9: Verify DuckDB tables
    # ========================================================================
    print("STEP 9: Verifying DuckDB Tables")
    print("-" * 80)

    try:
        # Check people_bad
        result = duck_conn.execute("SELECT COUNT(*) FROM people_bad;").fetchone()
        bad_count = result[0] if result else 0
        print(f"[OK] people_bad: {bad_count} records")

        # Check people_good
        result = duck_conn.execute("SELECT COUNT(*) FROM people_good;").fetchone()
        good_count = result[0] if result else 0
        print(f"[OK] people_good: {good_count} records")

        # Check people_validation_snapshots
        result = duck_conn.execute("SELECT COUNT(*) FROM people_validation_snapshots;").fetchone()
        snapshot_count = result[0]
        print(f"[OK] people_validation_snapshots: {snapshot_count} snapshots")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to verify DuckDB tables")
        print(f"   {e}")

    duck_conn.close()

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("=" * 80)
    print("PEOPLE VALIDATION SUMMARY")
    print("=" * 80)
    print()
    print(f"Snapshot Version: {SNAPSHOT_VERSION}")
    print(f"Source Table: marketing.people_master")
    print()
    print("VALIDATION RESULTS:")
    print(f"  Total People Scanned: {validation_stats['total_scanned']}")
    print(f"  People VALID: {validation_stats['total_valid']} ({validation_stats['total_valid']/validation_stats['total_scanned']*100:.1f}%)")
    print(f"  People INVALID: {validation_stats['total_invalid']} ({validation_stats['total_invalid']/validation_stats['total_scanned']*100:.1f}%)")
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
    print(f"  marketing.people_invalid: {inserted_count} new records added")
    print()
    print("DUCKDB TABLES UPDATED:")
    print(f"  people_bad: {validation_stats['total_invalid']} records (ready for Garage 2.0)")
    print(f"  people_good: {validation_stats['total_valid']} records")
    print(f"  people_validation_snapshots: New snapshot added")
    print()
    print("NEXT STEPS:")
    print("  1. Review invalid people in DuckDB:")
    print(f"     duckdb {DUCKDB_PATH}")
    print("     SELECT * FROM people_bad LIMIT 10;")
    print()
    print("  2. Verify invalid people in Neon:")
    print("     SELECT COUNT(*) FROM marketing.people_invalid WHERE batch_id = '" + SNAPSHOT_VERSION + "';")
    print()
    print("  3. Run Garage 2.0 enrichment on invalid people:")
    print("     python enrichment_garage_2_0.py --record-type person --snapshot " + SNAPSHOT_VERSION)
    print()
    print("=" * 80)
    print("[OK] PEOPLE VALIDATION COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
