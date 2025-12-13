#!/usr/bin/env python3
"""
Bulk Company Validation & Promotion Runner
Executes the bulk SQL validation against Neon PostgreSQL.
Processes 62,792+ records in ~10-20 seconds (vs 40+ minutes row-by-row)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys

# Neon connection settings
NEON_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}

def run_bulk_validation():
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    conn = psycopg2.connect(**NEON_CONFIG)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print('=' * 60)
    print('BULK COMPANY VALIDATION & PROMOTION')
    print('=' * 60)

    # Step 0: Get current count
    cur.execute('SELECT COUNT(*) as cnt FROM company.company_master')
    before_count = cur.fetchone()['cnt']
    print(f'BEFORE: {before_count:,} records in company.company_master')
    print()

    # Step 1: Get next Barton ID sequence
    cur.execute('''
        SELECT COALESCE(MAX(CAST(SPLIT_PART(company_unique_id, '.', 5) AS INTEGER)), 499) as max_seq
        FROM company.company_master
        WHERE company_unique_id LIKE '04.04.01.%%'
    ''')
    max_seq = cur.fetchone()['max_seq']
    next_seq = max_seq + 1
    print(f'Next Barton sequence starting at: {next_seq}')
    print()

    # Step 2: Create validation results with new Barton IDs
    print('Creating validation results...')
    cur.execute('DROP TABLE IF EXISTS _validation_results')

    cur.execute('''
        CREATE TEMP TABLE _validation_results AS
        WITH numbered_records AS (
            SELECT
                *,
                ROW_NUMBER() OVER (ORDER BY company_unique_id) AS row_seq
            FROM intake.company_raw_wv
        ),
        validation AS (
            SELECT
                r.company_unique_id AS intake_id,
                r.company_name,
                r.domain,
                r.website AS linkedin_url,
                r.industry,
                r.employee_count,
                r.city,
                r.state,
                r.row_seq,

                -- Generate new Barton ID: 04.04.01.XX.XXXXX.XXX
                '04.04.01.' ||
                LPAD(((%s + r.row_seq - 1) %% 99 + 1)::TEXT, 2, '0') || '.' ||
                LPAD((%s + r.row_seq - 1)::TEXT, 5, '0') || '.' ||
                LPAD(((%s + r.row_seq - 1) %% 1000)::TEXT, 3, '0')
                AS new_barton_id,

                -- Validation checks
                (r.company_name IS NOT NULL AND LENGTH(TRIM(r.company_name)) >= 3) AS name_valid,
                (r.employee_count IS NOT NULL AND r.employee_count >= 50) AS employee_valid,
                (r.state IS NOT NULL AND r.state IN ('PA', 'VA', 'MD', 'OH', 'WV', 'KY', 'DE', 'OK')) AS state_valid,
                (r.domain IS NOT NULL AND LENGTH(TRIM(r.domain)) > 0) AS domain_valid,

                -- Overall validation
                (
                    r.company_name IS NOT NULL AND LENGTH(TRIM(r.company_name)) >= 3 AND
                    r.employee_count IS NOT NULL AND r.employee_count >= 50 AND
                    r.state IS NOT NULL AND r.state IN ('PA', 'VA', 'MD', 'OH', 'WV', 'KY', 'DE', 'OK') AND
                    r.domain IS NOT NULL AND LENGTH(TRIM(r.domain)) > 0
                ) AS is_valid,

                -- Error messages array
                ARRAY_REMOVE(ARRAY[
                    CASE WHEN r.company_name IS NULL OR LENGTH(TRIM(r.company_name)) < 3
                         THEN 'company_name: required and must be >= 3 chars' END,
                    CASE WHEN r.employee_count IS NULL
                         THEN 'employee_count: required'
                         WHEN r.employee_count < 50
                         THEN 'employee_count: ' || r.employee_count || ' below minimum 50' END,
                    CASE WHEN r.state IS NULL
                         THEN 'state: required'
                         WHEN r.state NOT IN ('PA', 'VA', 'MD', 'OH', 'WV', 'KY', 'DE', 'OK')
                         THEN 'state: ' || r.state || ' not in target states' END,
                    CASE WHEN r.domain IS NULL OR LENGTH(TRIM(r.domain)) = 0
                         THEN 'domain: required for website_url' END
                ], NULL) AS validation_errors

            FROM numbered_records r
        )
        SELECT * FROM validation
    ''', (next_seq, next_seq, next_seq))

    print('Validation results created.')
    print()

    # Step 3: Show validation summary
    print('=' * 60)
    print('VALIDATION SUMMARY')
    print('=' * 60)
    cur.execute('''
        SELECT
            COUNT(*) AS total_records,
            SUM(CASE WHEN is_valid THEN 1 ELSE 0 END) AS valid_count,
            SUM(CASE WHEN NOT is_valid THEN 1 ELSE 0 END) AS invalid_count,
            ROUND(100.0 * SUM(CASE WHEN is_valid THEN 1 ELSE 0 END) / COUNT(*), 2) AS pass_rate_pct
        FROM _validation_results
    ''')
    summary = cur.fetchone()
    print(f"Total records: {summary['total_records']:,}")
    print(f"Valid: {summary['valid_count']:,} ({summary['pass_rate_pct']}%)")
    print(f"Invalid: {summary['invalid_count']:,}")
    print()

    # Step 4: Error breakdown
    print('ERROR BREAKDOWN')
    print('-' * 60)
    cur.execute('''
        SELECT
            error_type,
            COUNT(*) AS failure_count
        FROM (
            SELECT UNNEST(validation_errors) AS error_type
            FROM _validation_results
            WHERE NOT is_valid
        ) errors
        GROUP BY error_type
        ORDER BY failure_count DESC
    ''')
    for row in cur.fetchall():
        print(f"  {row['error_type'][:50]}: {row['failure_count']:,}")
    print()

    # Step 5: Check for duplicates
    cur.execute('''
        SELECT COUNT(*) AS duplicate_count
        FROM _validation_results v
        JOIN company.company_master cm
            ON LOWER(TRIM(v.company_name)) = LOWER(TRIM(cm.company_name))
            AND v.state = cm.address_state
        WHERE v.is_valid
    ''')
    dupe_count = cur.fetchone()['duplicate_count']
    print(f'Duplicates against existing Apollo data: {dupe_count:,}')
    print()

    # Step 6: Insert valid records
    print('=' * 60)
    print('PROMOTING VALID RECORDS...')
    print('=' * 60)
    cur.execute('''
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
            validated_by,
            promoted_from_intake_at
        )
        SELECT
            v.new_barton_id,
            v.company_name,
            CASE
                WHEN v.domain LIKE 'http%%' THEN v.domain
                ELSE 'http://' || v.domain
            END AS website_url,
            v.industry,
            v.employee_count,
            v.city,
            v.state,
            v.linkedin_url,
            'clay_import',
            v.intake_id,
            'clay_bulk_' || TO_CHAR(NOW(), 'YYYYMMDD_HH24MISS'),
            NOW(),
            'bulk_validate_companies.sql',
            NOW()
        FROM _validation_results v
        WHERE v.is_valid = TRUE
          AND NOT EXISTS (
              SELECT 1 FROM company.company_master cm
              WHERE LOWER(TRIM(cm.company_name)) = LOWER(TRIM(v.company_name))
                AND cm.address_state = v.state
          )
        ON CONFLICT (company_unique_id) DO NOTHING
    ''')
    inserted = cur.rowcount
    print(f'Promoted: {inserted:,} records')

    # Commit
    conn.commit()
    print('Transaction committed.')
    print()

    # Step 7: Final count
    cur.execute('SELECT COUNT(*) as cnt FROM company.company_master')
    after_count = cur.fetchone()['cnt']
    print('=' * 60)
    print('FINAL RESULTS')
    print('=' * 60)
    print(f'BEFORE: {before_count:,} records')
    print(f'AFTER: {after_count:,} records')
    print(f'NEW: {after_count - before_count:,} records added')
    print()

    # Sample promoted records
    print('SAMPLE PROMOTED RECORDS:')
    cur.execute('''
        SELECT company_unique_id, company_name, address_state, employee_count
        FROM company.company_master
        WHERE source_system = 'clay_import'
        ORDER BY promoted_from_intake_at DESC
        LIMIT 5
    ''')
    for row in cur.fetchall():
        name = row['company_name'][:40] if row['company_name'] else 'N/A'
        print(f"  {row['company_unique_id']} | {name} | {row['address_state']} | {row['employee_count']} emp")

    # By state breakdown
    print()
    print('BY STATE:')
    cur.execute('''
        SELECT address_state, COUNT(*) as cnt
        FROM company.company_master
        WHERE source_system = 'clay_import'
        GROUP BY address_state
        ORDER BY cnt DESC
    ''')
    for row in cur.fetchall():
        print(f"  {row['address_state']}: {row['cnt']:,}")

    # Cleanup
    cur.execute('DROP TABLE IF EXISTS _validation_results')
    cur.close()
    conn.close()

    print()
    print('Done!')

if __name__ == '__main__':
    run_bulk_validation()
