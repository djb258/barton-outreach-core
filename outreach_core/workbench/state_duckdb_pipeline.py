"""
State DuckDB → Parquet → Backblaze B2 Pipeline (Phase 2B)

ENHANCEMENTS:
- Multi-state execution (--state XX)
- Snapshot versioning
- Linked people validation (only for valid companies)
- Kill switches (K1: bad ratio, K2: row delta, K3: ID drift)
- Enhanced audit logging
- B2 metadata tags

Usage:
    python state_duckdb_pipeline.py --state WV
    python state_duckdb_pipeline.py --state PA

Date: 2025-11-18
Status: Production Ready
"""

import os
import sys
import io
import json
import argparse
import duckdb
import psycopg2
import psycopg2.extras
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from b2sdk.v2 import InMemoryAccountInfo, B2Api

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

# ============================================================================
# STEP 1: PARSE STATE ARGUMENT
# ============================================================================

parser = argparse.ArgumentParser(description="State-based validation pipeline")
parser.add_argument("--state", required=True, help="State abbreviation (WV, PA, VA, MD, OH, DE)")
args = parser.parse_args()

STATE = args.state.upper()

# Validate state
VALID_STATES = ['WV', 'PA', 'VA', 'MD', 'OH', 'DE']
if STATE not in VALID_STATES:
    print(f"❌ ERROR: Invalid state '{STATE}'. Must be one of: {', '.join(VALID_STATES)}")
    sys.exit(1)

# ============================================================================
# STEP 2: GENERATE SNAPSHOT VERSION
# ============================================================================

snapshot_version = datetime.utcnow().strftime("%Y%m%d%H%M%S")

# Configuration
WORKBENCH_ROOT = Path(__file__).parent
DUCKDB_PATH = WORKBENCH_ROOT / "duck" / "outreach_workbench.duckdb"
EXPORTS_ROOT = WORKBENCH_ROOT / "exports" / STATE

# Neon PostgreSQL credentials
NEON_HOST = os.getenv('NEON_HOST')
NEON_USER = os.getenv('NEON_USER')
NEON_PASSWORD = os.getenv('NEON_PASSWORD')
NEON_DATABASE = os.getenv('NEON_DATABASE')
NEON_CONNECTION_STRING = f"postgresql://{NEON_USER}:{NEON_PASSWORD}@{NEON_HOST}/{NEON_DATABASE}"

# Backblaze B2 credentials
B2_KEY_ID = os.getenv('B2_KEY_ID')
B2_APP_KEY = os.getenv('B2_APPLICATION_KEY')
B2_BUCKET = os.getenv('B2_BUCKET')

# Kill switch configuration
KILL_SWITCH_BAD_RATIO = 0.15  # 15%
KILL_SWITCH_ROW_DELTA = 0.30  # 30%

# Results tracking
results = {
    'state': STATE,
    'snapshot_version': snapshot_version,
    'companies_good': 0,
    'companies_bad': 0,
    'people_good': 0,
    'people_bad': 0,
    'parquet_files': [],
    'b2_uploads': [],
    'kill_switch_status': 'OK',
    'row_delta': 0.0,
    'snapshot_id': None,
    'start_time': datetime.utcnow().isoformat(),
    'end_time': None
}

print("=" * 80)
print(f"STATE DUCKDB → PARQUET → B2 PIPELINE (PHASE 2B)")
print("=" * 80)
print(f"State: {STATE}")
print(f"Snapshot Version: {snapshot_version}")
print(f"Start Time: {results['start_time']}")
print(f"DuckDB Path: {DUCKDB_PATH}")
print(f"Exports Root: {EXPORTS_ROOT}")
print()

# ============================================================================
# VALIDATE CONFIGURATION
# ============================================================================

print("STEP 1: Validating Configuration")
print("-" * 80)

if not all([NEON_HOST, NEON_USER, NEON_PASSWORD, NEON_DATABASE]):
    print("❌ ERROR: Missing Neon PostgreSQL credentials")
    sys.exit(1)

if not all([B2_KEY_ID, B2_APP_KEY, B2_BUCKET]):
    print("❌ ERROR: Missing Backblaze B2 credentials")
    sys.exit(1)

print(f"✅ State: {STATE}")
print(f"✅ Neon Host: {NEON_HOST}")
print(f"✅ B2 Bucket: {B2_BUCKET}")
print()

# ============================================================================
# CONNECT TO NEON POSTGRESQL
# ============================================================================

print("STEP 2: Connecting to Neon PostgreSQL")
print("-" * 80)

try:
    neon_conn = psycopg2.connect(NEON_CONNECTION_STRING)
    neon_cursor = neon_conn.cursor()
    print("✅ Connected to Neon PostgreSQL")
except Exception as e:
    print(f"❌ ERROR: Failed to connect to Neon PostgreSQL: {str(e)}")
    sys.exit(1)

print()

# ============================================================================
# INITIALIZE DUCKDB
# ============================================================================

print("STEP 3: Initializing DuckDB")
print("-" * 80)

try:
    duck_conn = duckdb.connect(str(DUCKDB_PATH))
    print(f"✅ Initialized DuckDB: {DUCKDB_PATH}")

    # Install PostgreSQL extension
    duck_conn.execute("INSTALL postgres;")
    duck_conn.execute("LOAD postgres;")
    print("✅ Loaded PostgreSQL extension")

    # Create snapshots metadata table
    duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY,
            state VARCHAR,
            snapshot_version VARCHAR,
            companies_good INTEGER,
            companies_bad INTEGER,
            people_good INTEGER,
            people_bad INTEGER,
            created_at TIMESTAMP
        );
    """)
    print("✅ Created/verified snapshots metadata table")

except Exception as e:
    print(f"❌ ERROR: Failed to initialize DuckDB: {str(e)}")
    sys.exit(1)

print()

# ============================================================================
# GET PREVIOUS SNAPSHOT FOR KILL SWITCHES
# ============================================================================

print("STEP 4: Retrieving Previous Snapshot")
print("-" * 80)

try:
    previous_snapshot = duck_conn.execute(f"""
        SELECT
            companies_good + companies_bad + people_good + people_bad as total_rows
        FROM snapshots
        WHERE state = '{STATE}'
        ORDER BY created_at DESC
        LIMIT 1;
    """).fetchone()

    previous_total = previous_snapshot[0] if previous_snapshot else 0
    print(f"✅ Previous snapshot total: {previous_total:,} rows")

except Exception as e:
    print(f"⚠️  No previous snapshot found (first run for {STATE})")
    previous_total = 0

print()

# ============================================================================
# PULL DATA FROM NEON
# ============================================================================

print("STEP 5: Pulling Data from Neon")
print("-" * 80)

# Pull companies
print(f"\nPulling companies for {STATE}...")
try:
    duck_conn.execute(f"""
        CREATE OR REPLACE TABLE companies_raw AS
        SELECT * FROM postgres_scan(
            '{NEON_CONNECTION_STRING}',
            'marketing',
            'company_master'
        ) WHERE address_state = '{STATE}';
    """)

    companies_count = duck_conn.execute("SELECT COUNT(*) FROM companies_raw").fetchone()[0]
    print(f"✅ Loaded {companies_count:,} {STATE} companies")
except Exception as e:
    print(f"❌ ERROR: Failed to pull companies: {str(e)}")
    sys.exit(1)

# Pull people (linked to companies in this state)
print(f"\nPulling people for {STATE}...")
try:
    duck_conn.execute(f"""
        CREATE OR REPLACE TABLE people_raw AS
        SELECT p.* FROM postgres_scan(
            '{NEON_CONNECTION_STRING}',
            'marketing',
            'people_master'
        ) p
        WHERE p.company_unique_id IN (
            SELECT company_unique_id FROM companies_raw
        );
    """)

    people_count = duck_conn.execute("SELECT COUNT(*) FROM people_raw").fetchone()[0]
    print(f"✅ Loaded {people_count:,} {STATE} people")
except Exception as e:
    print(f"❌ ERROR: Failed to pull people: {str(e)}")
    sys.exit(1)

print()

# ============================================================================
# RUN VALIDATION LOGIC
# ============================================================================

print("STEP 6: Running Validation Logic")
print("-" * 80)

# Validate companies
print("\nValidating companies...")
try:
    duck_conn.execute("""
        CREATE OR REPLACE TABLE companies_good AS
        SELECT *
        FROM companies_raw
        WHERE
          company_name IS NOT NULL
          AND website_url IS NOT NULL
          AND website_url LIKE '%.%';
    """)

    results['companies_good'] = duck_conn.execute("SELECT COUNT(*) FROM companies_good").fetchone()[0]
    print(f"✅ companies_good: {results['companies_good']:,} records")

    duck_conn.execute("""
        CREATE OR REPLACE TABLE companies_bad AS
        SELECT *,
          ARRAY_FILTER([
            CASE WHEN company_name IS NULL THEN 'company_name_missing' ELSE NULL END,
            CASE WHEN website_url IS NULL THEN 'website_url_missing' ELSE NULL END,
            CASE WHEN website_url IS NOT NULL AND website_url NOT LIKE '%.%' THEN 'website_url_invalid' ELSE NULL END
          ], x -> x IS NOT NULL) AS validation_errors
        FROM companies_raw
        WHERE NOT (
          company_name IS NOT NULL
          AND website_url IS NOT NULL
          AND website_url LIKE '%.%'
        );
    """)

    results['companies_bad'] = duck_conn.execute("SELECT COUNT(*) FROM companies_bad").fetchone()[0]
    print(f"✅ companies_bad: {results['companies_bad']:,} records")

except Exception as e:
    print(f"❌ ERROR: Failed to validate companies: {str(e)}")
    sys.exit(1)

# Validate people (LINKED TO GOOD COMPANIES ONLY)
print("\nValidating people (linked to good companies)...")
try:
    # People good - only if their company is good
    duck_conn.execute("""
        CREATE OR REPLACE TABLE people_good AS
        SELECT p.*
        FROM people_raw p
        JOIN companies_good cg
            ON p.company_unique_id = cg.company_unique_id
        WHERE
            p.email ~ '^[^@]+@[^@]+\\.[^@]+'
            AND p.title IS NOT NULL;
    """)

    results['people_good'] = duck_conn.execute("SELECT COUNT(*) FROM people_good").fetchone()[0]
    print(f"✅ people_good: {results['people_good']:,} records")

    # People bad - failed validation OR company not good
    duck_conn.execute("""
        CREATE OR REPLACE TABLE people_bad AS
        SELECT p.*,
          ARRAY_FILTER([
            CASE WHEN p.email IS NULL OR p.email !~ '^[^@]+@[^@]+\\.[^@]+' THEN 'email_invalid' ELSE NULL END,
            CASE WHEN p.title IS NULL THEN 'title_missing' ELSE NULL END,
            CASE WHEN cg.company_unique_id IS NULL THEN 'company_not_valid' ELSE NULL END
          ], x -> x IS NOT NULL) AS validation_errors
        FROM people_raw p
        LEFT JOIN companies_good cg
            ON p.company_unique_id = cg.company_unique_id
        WHERE NOT (
            p.email ~ '^[^@]+@[^@]+\\.[^@]+'
            AND p.title IS NOT NULL
            AND cg.company_unique_id IS NOT NULL
        );
    """)

    results['people_bad'] = duck_conn.execute("SELECT COUNT(*) FROM people_bad").fetchone()[0]
    print(f"✅ people_bad: {results['people_bad']:,} records")

except Exception as e:
    print(f"❌ ERROR: Failed to validate people: {str(e)}")
    sys.exit(1)

print()

# ============================================================================
# KILL SWITCHES
# ============================================================================

print("STEP 7: Kill Switch Checks")
print("-" * 80)

total_companies = results['companies_good'] + results['companies_bad']
total_people = results['people_good'] + results['people_bad']
current_total = total_companies + total_people

# K1: Bad Ratio Spike
print("\nK1: Bad Ratio Check...")
if total_companies > 0:
    company_bad_ratio = results['companies_bad'] / total_companies
    if company_bad_ratio > KILL_SWITCH_BAD_RATIO:
        print(f"❌ K1 TRIGGERED: Company bad ratio {company_bad_ratio:.1%} > {KILL_SWITCH_BAD_RATIO:.1%}")
        results['kill_switch_status'] = f"K1_TRIGGERED_COMPANY_{company_bad_ratio:.1%}"
        sys.exit(1)
    print(f"✅ K1 Pass: Company bad ratio {company_bad_ratio:.1%} < {KILL_SWITCH_BAD_RATIO:.1%}")

if total_people > 0:
    people_bad_ratio = results['people_bad'] / total_people
    if people_bad_ratio > KILL_SWITCH_BAD_RATIO:
        print(f"❌ K1 TRIGGERED: People bad ratio {people_bad_ratio:.1%} > {KILL_SWITCH_BAD_RATIO:.1%}")
        results['kill_switch_status'] = f"K1_TRIGGERED_PEOPLE_{people_bad_ratio:.1%}"
        sys.exit(1)
    print(f"✅ K1 Pass: People bad ratio {people_bad_ratio:.1%} < {KILL_SWITCH_BAD_RATIO:.1%}")

# K2: Row Count Delta Drift
print("\nK2: Row Delta Check...")
if previous_total > 0:
    delta = abs(current_total - previous_total) / previous_total
    results['row_delta'] = delta
    if delta > KILL_SWITCH_ROW_DELTA:
        print(f"❌ K2 TRIGGERED: Row delta {delta:.1%} > {KILL_SWITCH_ROW_DELTA:.1%}")
        results['kill_switch_status'] = f"K2_TRIGGERED_{delta:.1%}"
        sys.exit(1)
    print(f"✅ K2 Pass: Row delta {delta:.1%} < {KILL_SWITCH_ROW_DELTA:.1%}")
else:
    print(f"✅ K2 Skip: No previous snapshot (first run)")

# K3: Company ID Drift
print("\nK3: Company ID Integrity Check...")
try:
    # Check for unexpected nulls in company_unique_id
    null_ids = duck_conn.execute("SELECT COUNT(*) FROM companies_raw WHERE company_unique_id IS NULL").fetchone()[0]
    if null_ids > 0:
        print(f"❌ K3 TRIGGERED: {null_ids} null company_unique_id values")
        results['kill_switch_status'] = f"K3_TRIGGERED_NULL_IDS_{null_ids}"
        sys.exit(1)
    print(f"✅ K3 Pass: All company_unique_id values present")
except Exception as e:
    print(f"⚠️  K3 Warning: {str(e)}")

print()

# ============================================================================
# EXPORT TO PARQUET WITH VERSIONING
# ============================================================================

print("STEP 8: Exporting to Parquet (Versioned)")
print("-" * 80)

# Ensure export directories exist
(EXPORTS_ROOT / 'companies' / 'good').mkdir(parents=True, exist_ok=True)
(EXPORTS_ROOT / 'companies' / 'bad').mkdir(parents=True, exist_ok=True)
(EXPORTS_ROOT / 'people' / 'good').mkdir(parents=True, exist_ok=True)
(EXPORTS_ROOT / 'people' / 'bad').mkdir(parents=True, exist_ok=True)

parquet_exports = [
    ('companies_good', EXPORTS_ROOT / 'companies' / 'good' / f'companies_good_{snapshot_version}.parquet'),
    ('companies_bad', EXPORTS_ROOT / 'companies' / 'bad' / f'companies_bad_{snapshot_version}.parquet'),
    ('people_good', EXPORTS_ROOT / 'people' / 'good' / f'people_good_{snapshot_version}.parquet'),
    ('people_bad', EXPORTS_ROOT / 'people' / 'bad' / f'people_bad_{snapshot_version}.parquet'),
]

for table_name, parquet_path in parquet_exports:
    try:
        duck_conn.execute(f"""
            COPY {table_name} TO '{parquet_path}' (FORMAT PARQUET);
        """)

        if not parquet_path.exists():
            raise FileNotFoundError(f"Parquet file not created: {parquet_path}")

        file_size = parquet_path.stat().st_size
        results['parquet_files'].append(str(parquet_path))

        print(f"✅ {table_name}: {parquet_path.name} ({file_size:,} bytes)")

    except Exception as e:
        print(f"❌ ERROR: Failed to export {table_name}: {str(e)}")
        sys.exit(1)

print()

# ============================================================================
# UPLOAD TO BACKBLAZE B2 WITH METADATA
# ============================================================================

print("STEP 9: Uploading to Backblaze B2 (with metadata)")
print("-" * 80)

try:
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", B2_KEY_ID, B2_APP_KEY)
    bucket = b2_api.get_bucket_by_name(B2_BUCKET)
    print(f"✅ Connected to B2 bucket: {B2_BUCKET}")
    print()
except Exception as e:
    print(f"❌ ERROR: Failed to connect to B2: {str(e)}")
    sys.exit(1)

for table_name, local_path in parquet_exports:
    try:
        # Determine B2 path
        if 'companies' in table_name and 'good' in table_name:
            b2_path = f"outreach/{STATE}/companies/good/{local_path.name}"
        elif 'companies' in table_name and 'bad' in table_name:
            b2_path = f"outreach/{STATE}/companies/bad/{local_path.name}"
        elif 'people' in table_name and 'good' in table_name:
            b2_path = f"outreach/{STATE}/people/good/{local_path.name}"
        elif 'people' in table_name and 'bad' in table_name:
            b2_path = f"outreach/{STATE}/people/bad/{local_path.name}"

        # Read file
        with open(local_path, 'rb') as f:
            file_data = f.read()

        # Upload with metadata
        file_info = bucket.upload_bytes(
            data_bytes=file_data,
            file_name=b2_path,
            content_type='application/octet-stream',
            file_infos={
                'snapshot-version': snapshot_version,
                'state': STATE,
                'table_name': table_name,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'pipeline': 'state_duckdb_pipeline'
            }
        )

        b2_url = f"b2://{B2_BUCKET}/{b2_path}"
        results['b2_uploads'].append(b2_url)

        print(f"✅ {table_name}: {b2_url}")

    except Exception as e:
        print(f"❌ ERROR: Failed to upload {table_name}: {str(e)}")
        sys.exit(1)

print()

# ============================================================================
# SAVE SNAPSHOT TO DUCKDB
# ============================================================================

print("STEP 10: Saving Snapshot Metadata")
print("-" * 80)

try:
    # Get next ID
    max_id = duck_conn.execute("SELECT COALESCE(MAX(id), 0) FROM snapshots").fetchone()[0]
    next_id = max_id + 1

    # Insert snapshot
    duck_conn.execute(f"""
        INSERT INTO snapshots VALUES (
            {next_id},
            '{STATE}',
            '{snapshot_version}',
            {results['companies_good']},
            {results['companies_bad']},
            {results['people_good']},
            {results['people_bad']},
            CURRENT_TIMESTAMP
        );
    """)

    results['snapshot_id'] = next_id
    print(f"✅ Snapshot saved (ID: {next_id})")

except Exception as e:
    print(f"❌ ERROR: Failed to save snapshot: {str(e)}")
    sys.exit(1)

print()

# ============================================================================
# WRITE ENHANCED AUDIT LOG
# ============================================================================

print("STEP 11: Writing Enhanced Audit Log")
print("-" * 80)

results['end_time'] = datetime.utcnow().isoformat()

try:
    # Ensure shq schema and table exist
    neon_cursor.execute("CREATE SCHEMA IF NOT EXISTS shq;")
    neon_cursor.execute("""
        CREATE TABLE IF NOT EXISTS shq.audit_log (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(255) NOT NULL,
            event_source VARCHAR(255) NOT NULL,
            details JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # Insert audit log
    details_json = json.dumps({
        'state': results['state'],
        'snapshot_version': results['snapshot_version'],
        'companies_good': results['companies_good'],
        'companies_bad': results['companies_bad'],
        'people_good': results['people_good'],
        'people_bad': results['people_bad'],
        'kill_switch_status': results['kill_switch_status'],
        'row_delta': results['row_delta'],
        'snapshot_id': results['snapshot_id'],
        'parquet_paths': results['parquet_files'],
        'b2_urls': results['b2_uploads'],
        'start_time': results['start_time'],
        'end_time': results['end_time']
    })

    neon_cursor.execute("""
        INSERT INTO shq.audit_log(
            event_type,
            event_source,
            details,
            created_at
        )
        VALUES (
            'outreach_snapshot',
            'state_duckdb_pipeline',
            %s::jsonb,
            NOW()
        )
        RETURNING id;
    """, (details_json,))

    audit_id = neon_cursor.fetchone()[0]
    neon_conn.commit()

    print(f"✅ Audit log written (ID: {audit_id})")

except Exception as e:
    print(f"❌ ERROR: Failed to write audit log: {str(e)}")
    neon_conn.rollback()
    sys.exit(1)

print()

# ============================================================================
# PRINT STRUCTURED SUMMARY
# ============================================================================

print("=" * 80)
print("PIPELINE COMPLETE")
print("=" * 80)
print()

print(f"STATE: {STATE}")
print(f"SNAPSHOT: {snapshot_version}")
print()

print("VALIDATION RESULTS:")
print(f"  Companies: {results['companies_good']:,} good / {results['companies_bad']:,} bad")
print(f"  People: {results['people_good']:,} good / {results['people_bad']:,} bad")
print()

print("ANOMALY CHECKS:")
print(f"  Kill Switch: {results['kill_switch_status']}")
print(f"  Row Delta: {results['row_delta']:.1%}")
print()

print("LOCAL PATHS:")
for path in results['parquet_files']:
    print(f"  {Path(path).name}")
print()

print("B2 URLS:")
for url in results['b2_uploads']:
    print(f"  {url}")
print()

print("AUDIT LOG:")
print(f"  Neon: shq.audit_log (ID: {audit_id})")
print(f"  DuckDB: snapshots (ID: {results['snapshot_id']})")
print()

print("=" * 80)
print("✅ ALL STEPS COMPLETED SUCCESSFULLY")
print("=" * 80)

# Cleanup
duck_conn.close()
neon_cursor.close()
neon_conn.close()
