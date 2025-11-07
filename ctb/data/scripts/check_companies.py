"""
Check companies loaded in database
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Find project root by looking for .git directory
project_root = Path(__file__).resolve()
while not (project_root / ".git").exists() and project_root != project_root.parent:
    project_root = project_root.parent
env_path = project_root / "ctb" / "sys" / "security-audit" / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# Count total companies
print("=== COMPANY MASTER TABLE SUMMARY ===\n")
cursor.execute("SELECT COUNT(*) as total FROM marketing.company_master")
total = cursor.fetchone()['total']
print(f"Total companies: {total}")

# Count by state
print("\n=== COMPANIES BY STATE ===")
cursor.execute("""
    SELECT
        COALESCE(state_abbrev, address_state, 'Unknown') as state,
        COUNT(*) as count
    FROM marketing.company_master
    GROUP BY COALESCE(state_abbrev, address_state, 'Unknown')
    ORDER BY count DESC
    LIMIT 20
""")
states = cursor.fetchall()
for row in states:
    print(f"  {row['state']:<15} {row['count']:>5} companies")

# Check enrichment status
print("\n=== ENRICHMENT STATUS ===")
cursor.execute("""
    SELECT
        CASE
            WHEN validated_at IS NOT NULL THEN 'Validated'
            ELSE 'Not Validated'
        END as status,
        COUNT(*) as count
    FROM marketing.company_master
    GROUP BY status
""")
enrichment = cursor.fetchall()
for row in enrichment:
    print(f"  {row['status']:<20} {row['count']:>5} companies")

# Show sample companies (first 10)
print("\n=== SAMPLE COMPANIES (First 10) ===")
cursor.execute("""
    SELECT
        company_unique_id,
        company_name,
        website_url,
        COALESCE(state_abbrev, address_state, 'Unknown') as state,
        validated_at
    FROM marketing.company_master
    ORDER BY created_at DESC
    LIMIT 10
""")
samples = cursor.fetchall()
for i, row in enumerate(samples, 1):
    validated = "✓" if row['validated_at'] else "✗"
    print(f"\n{i}. {row['company_name']}")
    print(f"   ID: {row['company_unique_id']}")
    print(f"   Website: {row['website_url']}")
    print(f"   State: {row['state']}")
    print(f"   Validated: {validated}")

# Check if there are WV companies
print("\n=== WEST VIRGINIA COMPANIES ===")
cursor.execute("""
    SELECT COUNT(*) as count
    FROM marketing.company_master
    WHERE state_abbrev = 'WV' OR address_state = 'WV' OR address_state = 'West Virginia'
""")
wv_count = cursor.fetchone()['count']
print(f"Total WV companies: {wv_count}")

if wv_count > 0:
    cursor.execute("""
        SELECT
            company_unique_id,
            company_name,
            website_url,
            validated_at
        FROM marketing.company_master
        WHERE state_abbrev = 'WV' OR address_state = 'WV' OR address_state = 'West Virginia'
        LIMIT 5
    """)
    wv_samples = cursor.fetchall()
    print("\nSample WV companies:")
    for row in wv_samples:
        print(f"  - {row['company_name']} ({row['website_url']})")

cursor.close()
conn.close()

print("\n" + "="*60)
print("✓ Database check complete!")
