#!/usr/bin/env python3
"""Check validation status of intake records"""

import os, psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

print("Intake Validation Status Breakdown:")
print("=" * 60)

# Total count
cursor.execute("SELECT COUNT(*) FROM intake.company_raw_intake")
total = cursor.fetchone()[0]
print(f"Total records in intake: {total}\n")

# By validation status
cursor.execute("""
    SELECT
        validated,
        COUNT(*) as count
    FROM intake.company_raw_intake
    GROUP BY validated
    ORDER BY validated NULLS FIRST
""")

print("Validation Status:")
print("-" * 60)
for validated, count in cursor.fetchall():
    status = "Already Validated" if validated else "Not Yet Validated"
    print(f"  {status}: {count} records")

# Check who validated
cursor.execute("""
    SELECT
        validated_by,
        COUNT(*) as count
    FROM intake.company_raw_intake
    WHERE validated = TRUE
    GROUP BY validated_by
    ORDER BY count DESC
""")

print("\nAlready Validated By:")
print("-" * 60)
already_validated = cursor.fetchall()
if already_validated:
    for validator, count in already_validated:
        print(f"  {validator}: {count} records")
else:
    print("  (none)")

print("\n" + "=" * 60)
print(f"Summary:")
print(f"  Total: {total}")

cursor.execute("SELECT COUNT(*) FROM intake.company_raw_intake WHERE validated = TRUE")
validated_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM intake.company_raw_intake WHERE validated IS NULL OR validated = FALSE")
unvalidated_count = cursor.fetchone()[0]

print(f"  Already validated: {validated_count}")
print(f"  Need validation: {unvalidated_count}")

cursor.close()
conn.close()
