"""
Direct Database Validation Script

Directly queries Neon database and runs validation on companies and people.
Bypasses the phase executor to avoid schema dependencies.

Usage:
    python backend/run_direct_validation.py
"""

import os
import sys
import io
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from datetime import datetime
import json

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

# Database connection
NEON_CONNECTION_STRING = os.getenv("NEON_CONNECTION_STRING")

if not NEON_CONNECTION_STRING:
    print("❌ NEON_CONNECTION_STRING not set in .env")
    sys.exit(1)

print("=" * 70)
print("DIRECT DATABASE VALIDATION")
print("=" * 70)
print(f"Timestamp: {datetime.now().isoformat()}")
print(f"Database: Neon PostgreSQL (Marketing DB)")
print("=" * 70)
print()

# Connect to database
try:
    conn = psycopg2.connect(NEON_CONNECTION_STRING)
    print("✅ Database connection established")
    print()
except Exception as e:
    print(f"❌ Database connection failed: {str(e)}")
    sys.exit(1)

cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Initialize variables
total_companies = 0
total_people = 0

# ============================================================================
# QUERY COMPANIES
# ============================================================================

print("COMPANY VALIDATION")
print("-" * 70)

try:
    # Get total companies
    cursor.execute("SELECT COUNT(*) as total FROM marketing.company_master;")
    total_companies = cursor.fetchone()['total']
    print(f"Total companies in database: {total_companies}")

    # Get companies with state = WV (if state column exists)
    try:
        cursor.execute("SELECT COUNT(*) as total FROM marketing.company_master WHERE state = 'WV';")
        wv_companies = cursor.fetchone()['total']
        print(f"West Virginia companies: {wv_companies}")
    except Exception as e:
        # Rollback transaction to recover from error
        conn.rollback()
        print(f"Note: State filter not available (column may not exist)")
        wv_companies = 0

    # Get sample companies
    cursor.execute("""
        SELECT
            company_unique_id,
            company_name,
            industry,
            employee_count,
            linkedin_url,
            created_at
        FROM marketing.company_master
        LIMIT 10;
    """)
    companies = cursor.fetchall()

    print(f"\nSample companies (first 10):")
    print()

    company_failures = []

    for i, company in enumerate(companies, 1):
        print(f"{i}. {company['company_name']} (ID: {company['company_unique_id']})")

        # Basic validation
        failures = []
        if not company.get('industry'):
            failures.append("Missing industry")
        if not company.get('employee_count') or company['employee_count'] <= 0:
            failures.append("Invalid employee_count")
        if not company.get('linkedin_url'):
            failures.append("Missing LinkedIn URL")

        if failures:
            print(f"   ❌ INVALID: {', '.join(failures)}")
            company_failures.append({
                "company_id": company['company_unique_id'],
                "company_name": company['company_name'],
                "fail_reason": '; '.join(failures),
                "validation_timestamp": datetime.now().isoformat(),
                "state": "N/A"
            })
        else:
            print(f"   ✅ VALID")

    print()
    print(f"Company Validation Summary:")
    print(f"  Sample Size: {len(companies)}")
    print(f"  Valid: {len(companies) - len(company_failures)}")
    print(f"  Invalid: {len(company_failures)}")
    print()

except Exception as e:
    print(f"❌ Company query failed: {str(e)}")
    company_failures = []

# ============================================================================
# QUERY PEOPLE
# ============================================================================

print("PEOPLE VALIDATION")
print("-" * 70)

try:
    # Get total people
    cursor.execute("SELECT COUNT(*) as total FROM marketing.people_master;")
    total_people = cursor.fetchone()['total']
    print(f"Total people in database: {total_people}")

    # Get sample people
    cursor.execute("""
        SELECT
            unique_id,
            full_name,
            email,
            title,
            linkedin_url,
            company_unique_id,
            created_at
        FROM marketing.people_master
        LIMIT 20;
    """)
    people = cursor.fetchall()

    print(f"\nSample people (first 20):")
    print()

    person_failures = []

    for i, person in enumerate(people, 1):
        print(f"{i}. {person['full_name']} - {person.get('title', 'No title')} (ID: {person['unique_id']})")

        # Basic validation
        failures = []
        if not person.get('full_name') or len(person['full_name'].strip()) == 0:
            failures.append("Missing full_name")
        if not person.get('email') or len(person.get('email', '').strip()) == 0:
            failures.append("Missing email")
        if not person.get('title') or len(person.get('title', '').strip()) == 0:
            failures.append("Missing title")
        if not person.get('linkedin_url'):
            failures.append("Missing LinkedIn URL")
        if not person.get('company_unique_id'):
            failures.append("Not linked to company")

        if failures:
            print(f"   ❌ INVALID: {', '.join(failures)}")
            person_failures.append({
                "person_id": person['unique_id'],
                "full_name": person['full_name'],
                "email": person.get('email', ''),
                "company_id": person.get('company_unique_id', ''),
                "company_name": "N/A",
                "fail_reason": '; '.join(failures),
                "validation_timestamp": datetime.now().isoformat(),
                "state": "N/A"
            })
        else:
            print(f"   ✅ VALID")

    print()
    print(f"People Validation Summary:")
    print(f"  Sample Size: {len(people)}")
    print(f"  Valid: {len(people) - len(person_failures)}")
    print(f"  Invalid: {len(person_failures)}")
    print()

except Exception as e:
    print(f"❌ People query failed: {str(e)}")
    person_failures = []

# ============================================================================
# SAVE RESULTS
# ============================================================================

print("=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
print(f"Total Companies in DB: {total_companies}")
print(f"Total People in DB: {total_people}")
print()
print(f"Sample Validation Results:")
print(f"  Companies Validated: {len(companies) if 'companies' in locals() else 0}")
print(f"  Companies Invalid: {len(company_failures)}")
print(f"  People Validated: {len(people) if 'people' in locals() else 0}")
print(f"  People Invalid: {len(person_failures)}")
print("=" * 70)
print()

# Save failures to JSON
if company_failures or person_failures:
    output_file = "validation_failures.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "company_failures": company_failures,
            "person_failures": person_failures
        }, f, indent=2)

    print(f"✅ Validation failures saved to: {output_file}")
    print()

    # Print sample failures
    if company_failures:
        print("Sample Company Failures:")
        for failure in company_failures[:3]:
            print(f"  - {failure['company_name']}: {failure['fail_reason']}")
        print()

    if person_failures:
        print("Sample Person Failures:")
        for failure in person_failures[:3]:
            print(f"  - {failure['full_name']}: {failure['fail_reason']}")
        print()

# Close connection
cursor.close()
conn.close()

print("✅ Validation complete!")
