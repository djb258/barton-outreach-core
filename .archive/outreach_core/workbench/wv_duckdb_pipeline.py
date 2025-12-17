"""
WV DuckDB → Parquet → Backblaze B2 Pipeline

This pipeline:
1. Pulls WV companies + people from Neon PostgreSQL
2. Loads into DuckDB
3. Re-validates using SQL logic
4. Splits into good/bad tables
5. Exports to Parquet with headers
6. Uploads Parquet to Backblaze B2
7. Logs the run in shq.audit_log

Date: 2025-11-18
Status: Production Ready
"""

import os
import sys
import io
import json
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

# Configuration
WORKBENCH_ROOT = Path(__file__).parent
DUCKDB_PATH = WORKBENCH_ROOT / "duck" / "outreach_workbench.duckdb"
EXPORTS_ROOT = WORKBENCH_ROOT / "exports" / "wv"

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

# Validation results
results = {
    'companies_good': 0,
    'companies_bad': 0,
    'people_good': 0,
    'people_bad': 0,
    'parquet_files': [],
    'b2_uploads': [],
    'start_time': datetime.now().isoformat(),
    'end_time': None
}

print("=" * 80)
print("WV DUCKDB → PARQUET → BACKBLAZE B2 PIPELINE")
print("=" * 80)
print()
print(f"Start Time: {results['start_time']}")
print(f"DuckDB Path: {DUCKDB_PATH}")
print(f"Exports Root: {EXPORTS_ROOT}")
print()

# ============================================================================
# STEP 1: VALIDATE CONFIGURATION
# ============================================================================

print("STEP 1: Validating Configuration")
print("-" * 80)

# Validate Neon credentials
if not all([NEON_HOST, NEON_USER, NEON_PASSWORD, NEON_DATABASE]):
    print("❌ ERROR: Missing Neon PostgreSQL credentials")
    print("Required: NEON_HOST, NEON_USER, NEON_PASSWORD, NEON_DATABASE")
    sys.exit(1)

# Validate B2 credentials
if not all([B2_KEY_ID, B2_APP_KEY, B2_BUCKET]):
    print("❌ ERROR: Missing Backblaze B2 credentials")
    print("Required: B2_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET")
    sys.exit(1)

print(f"✅ Neon Host: {NEON_HOST}")
print(f"✅ Neon Database: {NEON_DATABASE}")
print(f"✅ B2 Bucket: {B2_BUCKET}")
print()

# ============================================================================
# STEP 2: CONNECT TO NEON POSTGRESQL
# ============================================================================

print("STEP 2: Connecting to Neon PostgreSQL")
print("-" * 80)

try:
    neon_conn = psycopg2.connect(NEON_CONNECTION_STRING)
    neon_cursor = neon_conn.cursor()
    print("✅ Connected to Neon PostgreSQL")
except Exception as e:
    print(f"❌ ERROR: Failed to connect to Neon PostgreSQL")
    print(f"   {str(e)}")
    sys.exit(1)

print()

# ============================================================================
# STEP 3: PULL WV DATA FROM NEON INTO DUCKDB
# ============================================================================

print("STEP 3: Pulling WV Data from Neon into DuckDB")
print("-" * 80)

# Initialize DuckDB
try:
    duck_conn = duckdb.connect(str(DUCKDB_PATH))
    print(f"✅ Initialized DuckDB: {DUCKDB_PATH}")
except Exception as e:
    print(f"❌ ERROR: Failed to initialize DuckDB")
    print(f"   {str(e)}")
    sys.exit(1)

# Install PostgreSQL extension
try:
    duck_conn.execute("INSTALL postgres;")
    duck_conn.execute("LOAD postgres;")
    print("✅ Loaded PostgreSQL extension")
except Exception as e:
    print(f"❌ ERROR: Failed to load PostgreSQL extension")
    print(f"   {str(e)}")
    sys.exit(1)

# Pull companies from Neon
print("\nPulling companies...")
try:
    duck_conn.execute(f"""
        CREATE OR REPLACE TABLE companies_raw AS
        SELECT * FROM postgres_scan(
            '{NEON_CONNECTION_STRING}',
            'marketing',
            'company_master'
        ) WHERE address_state = 'WV';
    """)

    companies_count = duck_conn.execute("SELECT COUNT(*) FROM companies_raw").fetchone()[0]
    print(f"✅ Loaded {companies_count} WV companies into companies_raw")
except Exception as e:
    print(f"❌ ERROR: Failed to pull companies from Neon")
    print(f"   {str(e)}")
    sys.exit(1)

# Pull people from Neon (linked to WV companies)
print("\nPulling people...")
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
    print(f"✅ Loaded {people_count} WV people into people_raw")
except Exception as e:
    print(f"❌ ERROR: Failed to pull people from Neon")
    print(f"   {str(e)}")
    sys.exit(1)

print()

# ============================================================================
# STEP 4: RE-VALIDATION (SQL LOGIC INSIDE DUCKDB)
# ============================================================================

print("STEP 4: Running Validation Logic in DuckDB")
print("-" * 80)

# Validate companies
print("\nValidating companies...")
try:
    # Create companies_good table
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
    print(f"✅ companies_good: {results['companies_good']} records")

    # Create companies_bad table
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
    print(f"✅ companies_bad: {results['companies_bad']} records")

except Exception as e:
    print(f"❌ ERROR: Failed to validate companies")
    print(f"   {str(e)}")
    sys.exit(1)

# Validate people
print("\nValidating people...")
try:
    # Create people_good table
    duck_conn.execute("""
        CREATE OR REPLACE TABLE people_good AS
        SELECT *
        FROM people_raw
        WHERE
          email ~ '^[^@]+@[^@]+\\.[^@]+'
          AND title IS NOT NULL;
    """)

    results['people_good'] = duck_conn.execute("SELECT COUNT(*) FROM people_good").fetchone()[0]
    print(f"✅ people_good: {results['people_good']} records")

    # Create people_bad table
    duck_conn.execute("""
        CREATE OR REPLACE TABLE people_bad AS
        SELECT *,
          ARRAY_FILTER([
            CASE WHEN email IS NULL OR email !~ '^[^@]+@[^@]+\\.[^@]+' THEN 'email_invalid' ELSE NULL END,
            CASE WHEN title IS NULL THEN 'title_missing' ELSE NULL END
          ], x -> x IS NOT NULL) AS validation_errors
        FROM people_raw
        WHERE NOT (
          email ~ '^[^@]+@[^@]+\\.[^@]+'
          AND title IS NOT NULL
        );
    """)

    results['people_bad'] = duck_conn.execute("SELECT COUNT(*) FROM people_bad").fetchone()[0]
    print(f"✅ people_bad: {results['people_bad']} records")

except Exception as e:
    print(f"❌ ERROR: Failed to validate people")
    print(f"   {str(e)}")
    sys.exit(1)

print()

# ============================================================================
# STEP 5: EXPORT TO PARQUET
# ============================================================================

print("STEP 5: Exporting to Parquet")
print("-" * 80)

parquet_exports = [
    ('companies_good', EXPORTS_ROOT / 'companies' / 'good' / 'companies_good.parquet'),
    ('companies_bad', EXPORTS_ROOT / 'companies' / 'bad' / 'companies_bad.parquet'),
    ('people_good', EXPORTS_ROOT / 'people' / 'good' / 'people_good.parquet'),
    ('people_bad', EXPORTS_ROOT / 'people' / 'bad' / 'people_bad.parquet'),
]

for table_name, parquet_path in parquet_exports:
    try:
        # Ensure parent directory exists
        parquet_path.parent.mkdir(parents=True, exist_ok=True)

        # Export to Parquet
        duck_conn.execute(f"""
            COPY {table_name} TO '{parquet_path}' (FORMAT PARQUET);
        """)

        # Verify file exists
        if not parquet_path.exists():
            raise FileNotFoundError(f"Parquet file not created: {parquet_path}")

        file_size = parquet_path.stat().st_size
        results['parquet_files'].append(str(parquet_path))

        print(f"✅ {table_name}: {parquet_path}")
        print(f"   Size: {file_size:,} bytes")

    except Exception as e:
        print(f"❌ ERROR: Failed to export {table_name} to Parquet")
        print(f"   {str(e)}")
        sys.exit(1)

print()

# ============================================================================
# STEP 6: UPLOAD PARQUET FILES TO BACKBLAZE B2
# ============================================================================

print("STEP 6: Uploading Parquet Files to Backblaze B2")
print("-" * 80)

try:
    # Initialize B2 API
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", B2_KEY_ID, B2_APP_KEY)
    bucket = b2_api.get_bucket_by_name(B2_BUCKET)
    print(f"✅ Connected to B2 bucket: {B2_BUCKET}")
    print()
except Exception as e:
    print(f"❌ ERROR: Failed to connect to Backblaze B2")
    print(f"   {str(e)}")
    sys.exit(1)

# Upload each Parquet file
for table_name, local_path in parquet_exports:
    try:
        # Determine B2 path based on table name
        if 'companies' in table_name and 'good' in table_name:
            b2_path = f"outreach/wv/companies/good/{local_path.name}"
        elif 'companies' in table_name and 'bad' in table_name:
            b2_path = f"outreach/wv/companies/bad/{local_path.name}"
        elif 'people' in table_name and 'good' in table_name:
            b2_path = f"outreach/wv/people/good/{local_path.name}"
        elif 'people' in table_name and 'bad' in table_name:
            b2_path = f"outreach/wv/people/bad/{local_path.name}"

        # Read file
        with open(local_path, 'rb') as f:
            file_data = f.read()

        # Upload to B2
        file_info = bucket.upload_bytes(
            data_bytes=file_data,
            file_name=b2_path,
            content_type='application/octet-stream',
            file_infos={
                'table_name': table_name,
                'upload_timestamp': datetime.now().isoformat(),
                'pipeline': 'wv_duckdb_pipeline'
            }
        )

        b2_url = f"b2://{B2_BUCKET}/{b2_path}"
        results['b2_uploads'].append(b2_url)

        print(f"✅ {table_name}")
        print(f"   Local: {local_path}")
        print(f"   B2: {b2_url}")
        print(f"   File ID: {file_info.id_}")
        print()

    except Exception as e:
        print(f"❌ ERROR: Failed to upload {table_name} to B2")
        print(f"   {str(e)}")
        sys.exit(1)

# ============================================================================
# STEP 7: WRITE AUDIT LOG TO NEON
# ============================================================================

print("STEP 7: Writing Audit Log to Neon")
print("-" * 80)

results['end_time'] = datetime.now().isoformat()

try:
    # Ensure shq schema exists
    neon_cursor.execute("CREATE SCHEMA IF NOT EXISTS shq;")

    # Ensure audit_log table exists
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
        'companies_good': results['companies_good'],
        'companies_bad': results['companies_bad'],
        'people_good': results['people_good'],
        'people_bad': results['people_bad'],
        'parquet_paths': results['parquet_files'],
        'b2_uploads': results['b2_uploads'],
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
            'outreach_validation_run',
            'wv_duckdb_pipeline',
            %s::jsonb,
            NOW()
        )
        RETURNING id;
    """, (details_json,))

    audit_id = neon_cursor.fetchone()[0]
    neon_conn.commit()

    print(f"✅ Audit log written (ID: {audit_id})")

except Exception as e:
    print(f"❌ ERROR: Failed to write audit log")
    print(f"   {str(e)}")
    neon_conn.rollback()
    sys.exit(1)

print()

# ============================================================================
# STEP 8: PRINT FINAL SUMMARY
# ============================================================================

print("=" * 80)
print("PIPELINE COMPLETE")
print("=" * 80)
print()

print("VALIDATION RESULTS:")
print(f"  Companies Good: {results['companies_good']:,}")
print(f"  Companies Bad: {results['companies_bad']:,}")
print(f"  People Good: {results['people_good']:,}")
print(f"  People Bad: {results['people_bad']:,}")
print(f"  Total Processed: {results['companies_good'] + results['companies_bad'] + results['people_good'] + results['people_bad']:,}")
print()

print("PARQUET FILES:")
for path in results['parquet_files']:
    file_size = Path(path).stat().st_size
    print(f"  {path} ({file_size:,} bytes)")
print()

print("BACKBLAZE B2 UPLOADS:")
for url in results['b2_uploads']:
    print(f"  {url}")
print()

print("AUDIT LOG:")
print(f"  ✅ Logged to shq.audit_log (ID: {audit_id})")
print()

print("TIMING:")
print(f"  Start: {results['start_time']}")
print(f"  End: {results['end_time']}")
print()

print("=" * 80)
print("✅ ALL STEPS COMPLETED SUCCESSFULLY")
print("=" * 80)

# Cleanup
duck_conn.close()
neon_cursor.close()
neon_conn.close()
