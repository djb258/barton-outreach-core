#!/usr/bin/env python3
"""
Complete WV Validation Setup and Execution

This script:
1. Creates validation infrastructure tables
2. Creates sample WV data
3. Runs validation
4. Generates summary report
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def run_sql_file(cursor, filename, description):
    """Run a SQL file"""
    print(f"\n{description}...")

    sql_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'sql'
    )
    sql_file = os.path.join(sql_dir, filename)

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    try:
        # Execute entire SQL file (handles DO blocks and complex statements)
        cursor.execute(sql)
        print(f"  Done {description}")
        return True
    except psycopg2.errors.DuplicateColumn as e:
        print(f"  (Warning: Column already exists - continuing)")
        return True
    except psycopg2.errors.DuplicateTable as e:
        print(f"  (Warning: Table already exists - continuing)")
        return True
    except psycopg2.errors.DuplicateObject as e:
        print(f"  (Warning: Object already exists - continuing)")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        # Continue anyway - tables might already exist
        return True

def main():
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("ERROR: DATABASE_URL not set in .env")
        sys.exit(1)

    print("=" * 70)
    print("Enricha-Vision WV Validation - Complete Setup and Execution")
    print("=" * 70)

    # Connect to Neon
    print("\nConnecting to Neon database...")
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cursor = conn.cursor()
    print("  Connected")

    # Step 1: Create validation infrastructure
    print("\n" + "=" * 70)
    print("STEP 1: Create Validation Infrastructure")
    print("=" * 70)
    run_sql_file(cursor, 'neon_wv_validation_setup.sql', 'Creating validation tables')

    # Step 2: Create sample WV data
    print("\n" + "=" * 70)
    print("STEP 2: Create Sample WV Data")
    print("=" * 70)
    run_sql_file(cursor, 'create_wv_sample_data.sql', 'Creating sample WV data')

    # Step 3: Verify setup
    print("\n" + "=" * 70)
    print("STEP 3: Verify Setup")
    print("=" * 70)

    cursor.execute("SELECT COUNT(*) FROM marketing.company_raw_wv WHERE state='WV'")
    company_count = cursor.fetchone()[0]
    print(f"  Company records (WV): {company_count}")

    cursor.execute("SELECT COUNT(*) FROM marketing.people_raw_wv WHERE state='WV'")
    people_count = cursor.fetchone()[0]
    print(f"  People records (WV): {people_count}")

    if company_count == 0 and people_count == 0:
        print("\n  WARNING: No WV data found. Please check data creation.")
        cursor.close()
        conn.close()
        sys.exit(1)

    cursor.close()
    conn.close()

    # Step 4: Run validation
    print("\n" + "=" * 70)
    print("STEP 4: Run Validation")
    print("=" * 70)

    print("\nExecuting validation script...")
    print("(This will validate all WV companies and people)\n")

    # Import and run the validator
    sys.path.insert(0, os.path.dirname(__file__))
    from validate_wv_neon import NeonWVValidator

    validator = NeonWVValidator(dry_run=False)

    try:
        validator.connect()
        validator.process_company_batch()
        validator.process_people_batch()

        # Generate and print summary
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        print(validator.generate_summary())
        print("=" * 70)

    except Exception as e:
        print(f"\nValidation failed: {e}")
        sys.exit(1)
    finally:
        validator.close()

    print("\n" + "=" * 70)
    print("Setup and validation complete!")
    print("=" * 70)

if __name__ == '__main__':
    main()
