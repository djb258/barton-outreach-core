#!/usr/bin/env python3
"""
Clay Company Validation & Promotion Script
===========================================
Validates companies from intake.company_raw_wv and promotes valid records
to company.company_master following the PLE validation pipeline.

Validation Rules (from intake_validator.py):
1. company_name: required, >= 3 chars
2. employee_count: required, >= 50
3. state: must be in target states (PA, VA, MD, OH, WV, KY, DE, OK)
4. domain: recommended (warning if missing) - used as website_url

Usage:
    python validate_clay_companies.py [--dry-run] [--state PA] [--limit 100]

Examples:
    # Dry run - see what would happen
    python validate_clay_companies.py --dry-run

    # Validate and promote PA companies only
    python validate_clay_companies.py --state PA

    # Validate all companies
    python validate_clay_companies.py
"""

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import sys
import argparse
from datetime import datetime, timezone
import uuid
import json

# Neon connection settings
NEON_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}

# Target states for PLE
TARGET_STATES = ['PA', 'VA', 'MD', 'OH', 'WV', 'KY', 'DE', 'OK']

# Minimum employee count
MIN_EMPLOYEE_COUNT = 50

# Barton ID format: 04.04.01.XX.XXXXX.XXX (company)
# Format from existing data: 04.04.01.{2-digit-hash}.{5-digit-seq}.{3-digit-seq}
BARTON_PREFIX = "04.04.01"


def generate_barton_id(sequence_num):
    """Generate Barton Doctrine compliant company ID."""
    # Format: 04.04.01.XX.XXXXX.XXX
    hash_part = (sequence_num % 99) + 1  # 2-digit hash (01-99)
    seq_5 = sequence_num  # 5-digit sequence
    seq_3 = sequence_num % 1000  # 3-digit sequence
    return f"{BARTON_PREFIX}.{hash_part:02d}.{seq_5:05d}.{seq_3:03d}"


def normalize_website_url(domain):
    """Normalize domain to full website URL format."""
    if not domain:
        return None
    domain = str(domain).strip().lower()
    if not domain:
        return None
    # Add http:// prefix if no protocol
    if not domain.startswith('http://') and not domain.startswith('https://'):
        return f"http://{domain}"
    return domain


def validate_company_record(record):
    """
    Validate a single company record from intake.company_raw_wv.

    Returns:
        {
            'valid': bool,
            'errors': List[str],
            'warnings': List[str],
            'record': dict
        }
    """
    errors = []
    warnings = []

    # Rule 1: company_name required, >= 3 chars
    company_name = record.get('company_name', '')
    if not company_name or len(str(company_name).strip()) < 3:
        errors.append(f"company_name: required and must be >= 3 chars (got: '{company_name}')")

    # Rule 2: employee_count >= 50
    employee_count = record.get('employee_count')
    if employee_count is None:
        errors.append("employee_count: required")
    else:
        try:
            emp_int = int(employee_count)
            if emp_int < MIN_EMPLOYEE_COUNT:
                errors.append(f"employee_count: {emp_int} below minimum {MIN_EMPLOYEE_COUNT}")
        except (ValueError, TypeError):
            errors.append(f"employee_count: must be integer, got {type(employee_count).__name__}")

    # Rule 3: state must be in target states
    state = record.get('state', '')
    if not state:
        errors.append("state: required")
    elif state.upper() not in TARGET_STATES:
        errors.append(f"state: '{state}' not in target states {TARGET_STATES}")

    # Rule 4: domain/website_url required (company.company_master requires it)
    domain = record.get('domain', '')
    if not domain or len(str(domain).strip()) == 0:
        errors.append("domain: required for website_url (company.company_master constraint)")

    # Rule 5: company_unique_id required
    company_id = record.get('company_unique_id', '')
    if not company_id:
        errors.append("company_unique_id: required")

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'record': record
    }


def get_next_barton_sequence(cur):
    """Get next available Barton ID sequence number."""
    cur.execute("""
        SELECT company_unique_id
        FROM company.company_master
        WHERE company_unique_id LIKE %s
        ORDER BY company_unique_id DESC
        LIMIT 1
    """, (f"{BARTON_PREFIX}.%",))

    result = cur.fetchone()
    if result:
        # Extract sequence number from last ID - use the 5-digit part (second to last)
        last_id = result['company_unique_id']
        try:
            # ID format: 04.04.01.XX.XXXXX.XXX
            parts = last_id.split('.')
            last_seq = int(parts[4])  # The 5-digit sequence
            return last_seq + 1
        except:
            return 500  # Start after Apollo's ~453 records
    return 500  # Start after Apollo's existing records


def ensure_company_master_exists(cur, conn):
    """Verify company.company_master table exists (should already exist from Apollo import)."""
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'company'
            AND table_name = 'company_master'
        )
    """)
    result = cur.fetchone()
    exists = result['exists'] if isinstance(result, dict) else result[0]

    if not exists:
        raise Exception("company.company_master table does not exist! Run Apollo migration first.")

    # Get current count
    cur.execute("SELECT COUNT(*) as cnt FROM company.company_master")
    result = cur.fetchone()
    count = result['cnt'] if isinstance(result, dict) else result[0]
    print(f"company.company_master exists with {count:,} records")


def ensure_quarantine_exists(cur, conn):
    """Ensure intake.quarantine table exists."""
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'intake'
            AND table_name = 'quarantine'
        )
    """)
    exists = cur.fetchone()[0]

    if not exists:
        print("Creating intake.quarantine table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS intake.quarantine (
                id SERIAL PRIMARY KEY,
                source_table TEXT NOT NULL,
                source_id TEXT NOT NULL,
                record_data JSONB NOT NULL,
                validation_errors JSONB NOT NULL,
                quarantined_at TIMESTAMPTZ DEFAULT NOW(),
                resolved_at TIMESTAMPTZ,
                resolution_action TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_quarantine_source
                ON intake.quarantine(source_table, source_id);
        """)
        conn.commit()
        print("Created intake.quarantine table")


def check_duplicate(cur, company_name, state, table_exists=True):
    """Check if company already exists in company.company_master."""
    if not table_exists:
        return None

    try:
        cur.execute("""
            SELECT company_unique_id, company_name
            FROM company.company_master
            WHERE LOWER(TRIM(company_name)) = LOWER(TRIM(%s))
            AND address_state = %s
            LIMIT 1
        """, (company_name, state))
        return cur.fetchone()
    except:
        return None


def validate_and_promote(dry_run=False, state_filter=None, limit=None):
    """
    Main validation and promotion function.

    Args:
        dry_run: If True, don't make any changes
        state_filter: Optional state to filter by (e.g., 'PA')
        limit: Optional limit on records to process
    """
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    conn = psycopg2.connect(**NEON_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Check if company_master exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'company'
                AND table_name = 'company_master'
            ) as exists
        """)
        company_master_exists = cur.fetchone()['exists']

        # Verify tables exist
        if not dry_run:
            ensure_company_master_exists(cur, conn)
            ensure_quarantine_exists(cur, conn)
            company_master_exists = True

        # Build query
        query = "SELECT * FROM intake.company_raw_wv WHERE 1=1"
        params = []

        if state_filter:
            query += " AND state = %s"
            params.append(state_filter.upper())

        if limit:
            query += f" LIMIT {int(limit)}"

        cur.execute(query, params)
        records = cur.fetchall()

        print("=" * 60)
        print("CLAY COMPANY VALIDATION & PROMOTION")
        print("=" * 60)
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"State filter: {state_filter or 'ALL'}")
        print(f"Records to process: {len(records):,}")
        print()

        # Stats
        stats = {
            'total': len(records),
            'valid': 0,
            'invalid': 0,
            'duplicates': 0,
            'promoted': 0,
            'quarantined': 0,
            'errors_by_type': {}
        }

        # Get next Barton sequence
        next_seq = get_next_barton_sequence(cur) if not dry_run else 1

        # Process each record
        valid_records = []
        invalid_records = []
        duplicate_records = []

        for record in records:
            # Validate
            result = validate_company_record(record)

            if not result['valid']:
                stats['invalid'] += 1
                invalid_records.append({
                    'record': record,
                    'errors': result['errors'],
                    'warnings': result['warnings']
                })

                # Track error types
                for error in result['errors']:
                    field = error.split(':')[0]
                    stats['errors_by_type'][field] = stats['errors_by_type'].get(field, 0) + 1

            else:
                # Check for duplicates
                existing = check_duplicate(cur, record['company_name'], record['state'], company_master_exists)

                if existing:
                    stats['duplicates'] += 1
                    duplicate_records.append({
                        'record': record,
                        'existing_id': existing['company_unique_id'],
                        'existing_name': existing['company_name']
                    })
                else:
                    stats['valid'] += 1
                    valid_records.append(record)

        # Print validation summary
        print("VALIDATION SUMMARY")
        print("-" * 60)
        print(f"Valid: {stats['valid']:,} ({stats['valid']/stats['total']*100:.1f}%)")
        print(f"Invalid: {stats['invalid']:,} ({stats['invalid']/stats['total']*100:.1f}%)")
        print(f"Duplicates: {stats['duplicates']:,} ({stats['duplicates']/stats['total']*100:.1f}%)")
        print()

        if stats['errors_by_type']:
            print("ERRORS BY FIELD")
            print("-" * 60)
            for field, count in sorted(stats['errors_by_type'].items(), key=lambda x: -x[1]):
                print(f"  {field}: {count:,}")
            print()

        # Sample invalid records
        if invalid_records:
            print("SAMPLE INVALID RECORDS (first 5)")
            print("-" * 60)
            for item in invalid_records[:5]:
                r = item['record']
                print(f"  {r.get('company_name', 'N/A')[:40]} ({r.get('state', 'N/A')})")
                for error in item['errors']:
                    print(f"    - {error}")
            if len(invalid_records) > 5:
                print(f"  ... and {len(invalid_records) - 5:,} more")
            print()

        # Promote valid records if not dry run
        if not dry_run and valid_records:
            print("PROMOTING VALID RECORDS")
            print("-" * 60)

            promoted = 0
            batch_id = f"clay_import_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

            for record in valid_records:
                # Generate new Barton ID
                barton_id = generate_barton_id(next_seq)
                next_seq += 1

                # Normalize website URL
                website_url = normalize_website_url(record.get('domain'))

                # Insert into company.company_master (matching existing Apollo schema)
                cur.execute("""
                    INSERT INTO company.company_master (
                        company_unique_id,
                        company_name,
                        website_url,
                        industry,
                        employee_count,
                        address_city,
                        address_state,
                        linkedin_url,
                        source_system,
                        source_record_id,
                        import_batch_id,
                        validated_at,
                        validated_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (company_unique_id) DO NOTHING
                """, (
                    barton_id,
                    record['company_name'],
                    website_url,
                    record.get('industry'),
                    record.get('employee_count'),
                    record.get('city'),
                    record.get('state'),
                    record.get('website'),  # LinkedIn URL stored in 'website' field
                    'clay_import',
                    record.get('company_unique_id'),  # Original Clay ID as source_record_id
                    batch_id,
                    datetime.now(timezone.utc),
                    'validate_clay_companies.py'
                ))
                promoted += 1

                if promoted % 1000 == 0:
                    conn.commit()
                    print(f"  Promoted {promoted:,} records...")

            conn.commit()
            stats['promoted'] = promoted
            print(f"  Total promoted: {promoted:,}")
            print()

        # Quarantine invalid records if not dry run
        if not dry_run and invalid_records:
            print("QUARANTINING INVALID RECORDS")
            print("-" * 60)

            quarantined = 0
            for item in invalid_records:
                record = item['record']
                cur.execute("""
                    INSERT INTO intake.quarantine (
                        source_table,
                        source_id,
                        record_data,
                        validation_errors
                    ) VALUES (%s, %s, %s, %s)
                """, (
                    'intake.company_raw_wv',
                    record.get('company_unique_id', ''),
                    json.dumps({k: str(v) if v else None for k, v in record.items()}),
                    json.dumps(item['errors'])
                ))
                quarantined += 1

                if quarantined % 1000 == 0:
                    conn.commit()
                    print(f"  Quarantined {quarantined:,} records...")

            conn.commit()
            stats['quarantined'] = quarantined
            print(f"  Total quarantined: {quarantined:,}")
            print()

        # Final summary
        print("=" * 60)
        print("FINAL RESULTS")
        print("=" * 60)
        print(f"Total processed: {stats['total']:,}")
        print(f"Valid: {stats['valid']:,}")
        print(f"Invalid: {stats['invalid']:,}")
        print(f"Duplicates skipped: {stats['duplicates']:,}")
        if not dry_run:
            print(f"Promoted to company_master: {stats['promoted']:,}")
            print(f"Quarantined: {stats['quarantined']:,}")

        if dry_run:
            print("\n[DRY RUN - No changes made]")

        return stats

    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Validate and promote Clay companies to company_master')
    parser.add_argument('--dry-run', action='store_true', help='Validate only, do not promote')
    parser.add_argument('--state', type=str, help='Filter by state (e.g., PA, WV)')
    parser.add_argument('--limit', type=int, help='Limit number of records to process')

    args = parser.parse_args()

    validate_and_promote(
        dry_run=args.dry_run,
        state_filter=args.state,
        limit=args.limit
    )


if __name__ == '__main__':
    main()
