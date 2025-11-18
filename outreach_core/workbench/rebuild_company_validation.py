"""
Rebuild Company Validation - Fresh Pull from Neon

Purpose: Pull ALL companies from Neon and apply strict validation
Output: Populate companies_bad table in DuckDB with all failures

Validation Rules (Strict):
1. Company name: Not null, not empty, not placeholder
2. Website URL: Valid domain format with TLD
3. LinkedIn URL: Proper linkedin.com format
4. Industry: Not null, not empty
5. Domain must have: protocol, domain name, TLD

Note: apollo_id field does not exist in current schema

Date: 2025-11-18
Purpose: Truth rebuild for Garage 2.0
"""

import os
import sys
import io
import re
import duckdb
import psycopg2
import psycopg2.extras
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

# Configuration
WORKBENCH_ROOT = Path(__file__).parent
DUCKDB_PATH = WORKBENCH_ROOT / "duck" / "outreach_workbench.duckdb"

# Neon PostgreSQL credentials
NEON_HOST = os.getenv('NEON_HOST')
NEON_USER = os.getenv('NEON_USER')
NEON_PASSWORD = os.getenv('NEON_PASSWORD')
NEON_DATABASE = os.getenv('NEON_DATABASE')
NEON_CONNECTION_STRING = f"postgresql://{NEON_USER}:{NEON_PASSWORD}@{NEON_HOST}/{NEON_DATABASE}"

# Snapshot version
SNAPSHOT_VERSION = datetime.utcnow().strftime("%Y%m%d%H%M%S")

# Results tracking
results = {
    'total_companies': 0,
    'companies_good': 0,
    'companies_bad': 0,
    'failure_breakdown': {
        'company_name_missing': 0,
        'company_name_placeholder': 0,
        'website_missing': 0,
        'website_invalid': 0,
        'linkedin_missing': 0,
        'linkedin_invalid': 0,
        'industry_missing': 0,
        'industry_placeholder': 0
    },
    'snapshot_version': SNAPSHOT_VERSION
}

print("=" * 80)
print("REBUILD COMPANY VALIDATION - FRESH PULL FROM NEON")
print("=" * 80)
print()
print(f"Snapshot Version: {SNAPSHOT_VERSION}")
print(f"DuckDB Path: {DUCKDB_PATH}")
print()

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def is_null_or_empty(value):
    """Check if value is null, empty, or whitespace only."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ''
    return False

def is_placeholder(value):
    """Check if value is a placeholder (unknown, n/a, tbd, etc.)."""
    if is_null_or_empty(value):
        return False

    value_lower = str(value).lower().strip()
    placeholders = [
        'unknown', 'n/a', 'na', 'tbd', 'none', 'null',
        'not available', 'not provided', 'blank', 'empty',
        'test', 'placeholder', 'sample', 'example'
    ]
    return value_lower in placeholders

def validate_website_url(url):
    """
    Validate website URL format.

    Must have:
    - Domain name
    - TLD (top-level domain like .com, .org, .net)
    - Optionally: protocol (http/https)

    Returns: (is_valid, reason)
    """
    if is_null_or_empty(url):
        return False, "missing"

    if is_placeholder(url):
        return False, "placeholder"

    url_str = str(url).strip()

    # Check for TLD (must have at least one dot)
    if '.' not in url_str:
        return False, "no_tld"

    # Check if it's just a domain without protocol
    # Valid: "example.com", "https://example.com", "www.example.com"
    # Invalid: "example", "com", "http://", "https://"

    # Remove protocol if present
    url_clean = re.sub(r'^https?://', '', url_str)

    # Check if anything is left after protocol
    if not url_clean or url_clean == '/':
        return False, "empty_after_protocol"

    # Check for valid domain pattern (alphanumeric + dots + hyphens)
    # Must have at least: something.something
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$'

    # Remove trailing slashes and paths
    url_domain = url_clean.split('/')[0]

    if not re.match(domain_pattern, url_domain):
        return False, "invalid_format"

    return True, None

def validate_linkedin_url(url):
    """
    Validate LinkedIn URL format.

    Must:
    - Contain 'linkedin.com'
    - Have proper format: /company/{slug} or /in/{username}

    Returns: (is_valid, reason)
    """
    if is_null_or_empty(url):
        return False, "missing"

    if is_placeholder(url):
        return False, "placeholder"

    url_str = str(url).strip().lower()

    # Must contain linkedin.com
    if 'linkedin.com' not in url_str:
        return False, "not_linkedin"

    # Check for proper format
    # Valid: linkedin.com/company/xyz, linkedin.com/in/xyz
    # Invalid: just "linkedin.com", "linkedin.com/"

    if url_str.endswith('linkedin.com') or url_str.endswith('linkedin.com/'):
        return False, "incomplete"

    # Check for /company/ or /in/ path
    if '/company/' not in url_str and '/in/' not in url_str:
        return False, "no_profile_path"

    return True, None

def validate_company_name(name):
    """
    Validate company name.

    Must:
    - Not be null or empty
    - Not be a placeholder
    - Have at least 2 characters

    Returns: (is_valid, reason)
    """
    if is_null_or_empty(name):
        return False, "missing"

    if is_placeholder(name):
        return False, "placeholder"

    name_str = str(name).strip()

    if len(name_str) < 2:
        return False, "too_short"

    return True, None

def validate_industry(industry):
    """
    Validate industry field.

    Must:
    - Not be null or empty
    - Not be a placeholder

    Returns: (is_valid, reason)
    """
    if is_null_or_empty(industry):
        return False, "missing"

    if is_placeholder(industry):
        return False, "placeholder"

    return True, None

def validate_company_record(company):
    """
    Validate entire company record.

    Returns: (is_valid, validation_errors)
    """
    errors = []

    # Validate company name
    name_valid, name_reason = validate_company_name(company.get('company_name'))
    if not name_valid:
        if name_reason == "missing":
            errors.append('company_name_missing')
            results['failure_breakdown']['company_name_missing'] += 1
        elif name_reason == "placeholder":
            errors.append('company_name_placeholder')
            results['failure_breakdown']['company_name_placeholder'] += 1

    # Validate website URL
    website_valid, website_reason = validate_website_url(company.get('website_url'))
    if not website_valid:
        if website_reason == "missing":
            errors.append('website_missing')
            results['failure_breakdown']['website_missing'] += 1
        else:
            errors.append(f'website_invalid_{website_reason}')
            results['failure_breakdown']['website_invalid'] += 1

    # Validate LinkedIn URL
    linkedin_valid, linkedin_reason = validate_linkedin_url(company.get('linkedin_url'))
    if not linkedin_valid:
        if linkedin_reason == "missing":
            errors.append('linkedin_missing')
            results['failure_breakdown']['linkedin_missing'] += 1
        else:
            errors.append(f'linkedin_invalid_{linkedin_reason}')
            results['failure_breakdown']['linkedin_invalid'] += 1

    # Validate industry
    industry_valid, industry_reason = validate_industry(company.get('industry'))
    if not industry_valid:
        if industry_reason == "missing":
            errors.append('industry_missing')
            results['failure_breakdown']['industry_missing'] += 1
        elif industry_reason == "placeholder":
            errors.append('industry_placeholder')
            results['failure_breakdown']['industry_placeholder'] += 1

    is_valid = len(errors) == 0

    return is_valid, errors

# ============================================================================
# STEP 1: CONNECT TO NEON
# ============================================================================

print("STEP 1: Connecting to Neon PostgreSQL")
print("-" * 80)

try:
    neon_conn = psycopg2.connect(NEON_CONNECTION_STRING)
    neon_cursor = neon_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    print("✅ Connected to Neon PostgreSQL")
except Exception as e:
    print(f"❌ ERROR: Failed to connect to Neon")
    print(f"   {str(e)}")
    sys.exit(1)

print()

# ============================================================================
# STEP 2: PULL ALL COMPANIES FROM NEON
# ============================================================================

print("STEP 2: Pulling ALL Companies from marketing.company_master")
print("-" * 80)

try:
    neon_cursor.execute("""
        SELECT
            company_unique_id,
            company_name,
            website_url,
            linkedin_url,
            industry,
            employee_count,
            address_state,
            address_city,
            company_phone,
            description,
            created_at,
            updated_at
        FROM marketing.company_master
        ORDER BY company_unique_id;
    """)

    companies = neon_cursor.fetchall()
    results['total_companies'] = len(companies)

    print(f"✅ Pulled {results['total_companies']} companies from Neon")
    print()

except Exception as e:
    print(f"❌ ERROR: Failed to pull companies from Neon")
    print(f"   {str(e)}")
    sys.exit(1)

# ============================================================================
# STEP 3: VALIDATE ALL COMPANIES
# ============================================================================

print("STEP 3: Validating All Companies (Strict Rules)")
print("-" * 80)
print()

good_companies = []
bad_companies = []

for idx, company in enumerate(companies, 1):
    if idx % 50 == 0:
        print(f"  Validated {idx}/{results['total_companies']} companies...")

    is_valid, validation_errors = validate_company_record(company)

    if is_valid:
        good_companies.append(dict(company))
        results['companies_good'] += 1
    else:
        # Add validation errors to record
        company_with_errors = dict(company)
        company_with_errors['validation_errors'] = validation_errors
        company_with_errors['validation_timestamp'] = datetime.utcnow().isoformat()
        company_with_errors['snapshot_version'] = SNAPSHOT_VERSION
        bad_companies.append(company_with_errors)
        results['companies_bad'] += 1

print(f"  Validated {results['total_companies']}/{results['total_companies']} companies")
print()
print(f"✅ Validation Complete:")
print(f"   Good: {results['companies_good']}")
print(f"   Bad: {results['companies_bad']}")
print()

# ============================================================================
# STEP 4: CONNECT TO DUCKDB
# ============================================================================

print("STEP 4: Connecting to DuckDB")
print("-" * 80)

try:
    duck_conn = duckdb.connect(str(DUCKDB_PATH))
    print(f"✅ Connected to DuckDB: {DUCKDB_PATH}")
except Exception as e:
    print(f"❌ ERROR: Failed to connect to DuckDB")
    print(f"   {str(e)}")
    sys.exit(1)

print()

# ============================================================================
# STEP 5: CREATE/UPDATE SNAPSHOT TRACKING TABLE
# ============================================================================

print("STEP 5: Creating/Updating Snapshot Tracking")
print("-" * 80)

try:
    # Create snapshots table if not exists
    duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS validation_snapshots (
            snapshot_id INTEGER PRIMARY KEY,
            snapshot_version VARCHAR(20) NOT NULL,
            total_companies INTEGER,
            companies_good INTEGER,
            companies_bad INTEGER,
            validation_timestamp TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # Insert this snapshot
    duck_conn.execute("""
        INSERT INTO validation_snapshots (
            snapshot_id,
            snapshot_version,
            total_companies,
            companies_good,
            companies_bad,
            validation_timestamp,
            created_at
        ) VALUES (
            (SELECT COALESCE(MAX(snapshot_id), 0) + 1 FROM validation_snapshots),
            ?,
            ?,
            ?,
            ?,
            ?,
            NOW()
        );
    """, (
        SNAPSHOT_VERSION,
        results['total_companies'],
        results['companies_good'],
        results['companies_bad'],
        datetime.utcnow().isoformat()
    ))

    print(f"✅ Snapshot tracking updated: {SNAPSHOT_VERSION}")

except Exception as e:
    print(f"❌ ERROR: Failed to create snapshot tracking")
    print(f"   {str(e)}")
    sys.exit(1)

print()

# ============================================================================
# STEP 6: WRITE BAD COMPANIES TO DUCKDB
# ============================================================================

print("STEP 6: Writing Bad Companies to DuckDB")
print("-" * 80)

try:
    # Drop existing companies_bad table
    duck_conn.execute("DROP TABLE IF EXISTS companies_bad;")

    # Create companies_bad table from bad companies list
    if bad_companies:
        # Convert to DataFrame and write to DuckDB
        import pandas as pd

        bad_df = pd.DataFrame(bad_companies)

        duck_conn.execute("CREATE TABLE companies_bad AS SELECT * FROM bad_df;")

        print(f"✅ Wrote {len(bad_companies)} bad companies to companies_bad table")
    else:
        # Create empty table with schema
        duck_conn.execute("""
            CREATE TABLE companies_bad (
                company_unique_id VARCHAR,
                company_name VARCHAR,
                website_url VARCHAR,
                linkedin_url VARCHAR,
                industry VARCHAR,
                employee_count INTEGER,
                address_state VARCHAR,
                address_city VARCHAR,
                company_phone VARCHAR,
                description VARCHAR,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                validation_errors VARCHAR[],
                validation_timestamp VARCHAR,
                snapshot_version VARCHAR
            );
        """)
        print(f"✅ Created empty companies_bad table (no bad companies found)")

except Exception as e:
    print(f"❌ ERROR: Failed to write bad companies to DuckDB")
    print(f"   {str(e)}")
    sys.exit(1)

print()

# ============================================================================
# STEP 7: WRITE GOOD COMPANIES TO DUCKDB (OPTIONAL)
# ============================================================================

print("STEP 7: Writing Good Companies to DuckDB")
print("-" * 80)

try:
    # Drop existing companies_good table
    duck_conn.execute("DROP TABLE IF EXISTS companies_good;")

    # Create companies_good table from good companies list
    if good_companies:
        import pandas as pd

        good_df = pd.DataFrame(good_companies)

        duck_conn.execute("CREATE TABLE companies_good AS SELECT * FROM good_df;")

        print(f"✅ Wrote {len(good_companies)} good companies to companies_good table")
    else:
        # Create empty table with schema
        duck_conn.execute("""
            CREATE TABLE companies_good (
                company_unique_id VARCHAR,
                company_name VARCHAR,
                website_url VARCHAR,
                linkedin_url VARCHAR,
                industry VARCHAR,
                employee_count INTEGER,
                address_state VARCHAR,
                address_city VARCHAR,
                company_phone VARCHAR,
                description VARCHAR,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            );
        """)
        print(f"✅ Created empty companies_good table (no good companies found)")

except Exception as e:
    print(f"❌ ERROR: Failed to write good companies to DuckDB")
    print(f"   {str(e)}")
    sys.exit(1)

print()

# ============================================================================
# STEP 8: VERIFY DUCKDB TABLES
# ============================================================================

print("STEP 8: Verifying DuckDB Tables")
print("-" * 80)

try:
    # Count records in companies_bad
    bad_count = duck_conn.execute("SELECT COUNT(*) FROM companies_bad;").fetchone()[0]
    print(f"✅ companies_bad: {bad_count} records")

    # Count records in companies_good
    good_count = duck_conn.execute("SELECT COUNT(*) FROM companies_good;").fetchone()[0]
    print(f"✅ companies_good: {good_count} records")

    # Count snapshots
    snapshot_count = duck_conn.execute("SELECT COUNT(*) FROM validation_snapshots;").fetchone()[0]
    print(f"✅ validation_snapshots: {snapshot_count} snapshots")

except Exception as e:
    print(f"❌ ERROR: Failed to verify DuckDB tables")
    print(f"   {str(e)}")
    sys.exit(1)

print()

# ============================================================================
# STEP 9: PRINT SUMMARY
# ============================================================================

print("=" * 80)
print("COMPANY VALIDATION SUMMARY")
print("=" * 80)
print()

print(f"Snapshot Version: {SNAPSHOT_VERSION}")
print()

print("VALIDATION RESULTS:")
print(f"  Total Companies Scanned: {results['total_companies']}")
print(f"  Companies GOOD: {results['companies_good']} ({100*results['companies_good']/results['total_companies'] if results['total_companies'] > 0 else 0:.1f}%)")
print(f"  Companies BAD: {results['companies_bad']} ({100*results['companies_bad']/results['total_companies'] if results['total_companies'] > 0 else 0:.1f}%)")
print()

print("FAILURE BREAKDOWN BY FIELD:")
sorted_failures = sorted(results['failure_breakdown'].items(), key=lambda x: x[1], reverse=True)
for field, count in sorted_failures:
    if count > 0:
        percentage = 100 * count / results['total_companies'] if results['total_companies'] > 0 else 0
        print(f"  {field}: {count} ({percentage:.1f}%)")
print()

print("DUCKDB TABLES UPDATED:")
print(f"  companies_bad: {results['companies_bad']} records")
print(f"  companies_good: {results['companies_good']} records")
print(f"  validation_snapshots: New snapshot added")
print()

print("NEXT STEPS:")
print("  1. Review companies_bad in DuckDB:")
print(f"     duckdb {DUCKDB_PATH}")
print("     SELECT * FROM companies_bad LIMIT 10;")
print()
print("  2. Run Garage 2.0 classification:")
print(f"     python enrichment_garage_2_0.py --state [STATE] --snapshot {SNAPSHOT_VERSION}")
print()

print("=" * 80)
print("✅ VALIDATION REBUILD COMPLETE")
print("=" * 80)

# Cleanup
duck_conn.close()
neon_cursor.close()
neon_conn.close()
