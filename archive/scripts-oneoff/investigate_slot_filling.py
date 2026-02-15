"""
Investigate Slot Filling Opportunities
========================================
READ-ONLY analysis of unfilled slots and potential matches in outreach.people.

This script investigates:
1. Count of unfilled slots in people.company_slot by slot_type
2. Sample of unfilled slot structure
3. Count of outreach.people with job_title patterns matching CEO/CFO/HR
4. Linking mechanism between outreach.people and people.company_slot
"""

import os
import sys
from typing import Dict, List, Any
from datetime import datetime

# Direct psycopg2 import for database access
try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


class NeonConfig:
    """Simple Neon database connection configuration."""

    def __init__(self):
        self.host = os.getenv("NEON_HOST", "")
        self.port = int(os.getenv("NEON_PORT", "5432"))
        self.database = os.getenv("NEON_DATABASE", "")
        self.user = os.getenv("NEON_USER", "")
        self.password = os.getenv("NEON_PASSWORD", "")
        self.ssl_mode = os.getenv("NEON_SSL_MODE", "require")

    @property
    def connection_string(self) -> str:
        """Build connection string."""
        db_encoded = self.database.replace(" ", "%20")
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{db_encoded}?sslmode={self.ssl_mode}"
        )

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.host and self.database and self.user and self.password)


class SimpleNeonWriter:
    """Simple database connection wrapper."""

    def __init__(self, config: NeonConfig):
        self.config = config
        self._connection = None

    def _get_connection(self):
        """Get database connection."""
        if self._connection is None or self._connection.closed:
            self._connection = psycopg2.connect(self.config.connection_string)
            self._connection.autocommit = True  # READ-ONLY: autocommit for safety
        return self._connection

    def close(self):
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")


def investigate_unfilled_slots(writer: SimpleNeonWriter):
    """1. Count of unfilled slots by slot_type."""
    print_section("1. UNFILLED SLOTS BY SLOT_TYPE")

    query = """
    SELECT
        slot_type,
        COUNT(*) as unfilled_count
    FROM people.company_slot
    WHERE person_unique_id IS NULL
    GROUP BY slot_type
    ORDER BY unfilled_count DESC;
    """

    try:
        conn = writer._get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()

            print(f"{'Slot Type':<15} {'Unfilled Count':>15}")
            print(f"{'-'*15} {'-'*15}")
            for row in results:
                print(f"{row[0]:<15} {row[1]:>15,}")

            total_unfilled = sum(row[1] for row in results)
            print(f"\n{'TOTAL':<15} {total_unfilled:>15,}")

    except Exception as e:
        print(f"ERROR: {e}")


def investigate_slot_structure(writer: SimpleNeonWriter):
    """2. Sample of unfilled slot structure."""
    print_section("2. SAMPLE UNFILLED SLOT STRUCTURE (5 rows)")

    query = """
    SELECT
        slot_id,
        outreach_id,
        company_unique_id,
        slot_type,
        person_unique_id,
        is_filled,
        source_system,
        created_at,
        updated_at
    FROM people.company_slot
    WHERE person_unique_id IS NULL
    LIMIT 5;
    """

    try:
        conn = writer._get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()

            for row in results:
                print(f"\nSlot ID: {row[0]}")
                print(f"  Outreach ID: {row[1]}")
                print(f"  Company ID: {row[2]}")
                print(f"  Slot Type: {row[3]}")
                print(f"  Person ID: {row[4]}")
                print(f"  Is Filled: {row[5]}")
                print(f"  Source System: {row[6]}")
                print(f"  Created: {row[7]}")
                print(f"  Updated: {row[8]}")

    except Exception as e:
        print(f"ERROR: {e}")


def investigate_people_job_titles(writer: SimpleNeonWriter):
    """3. Count of outreach.people by job title patterns."""
    print_section("3. OUTREACH.PEOPLE BY JOB TITLE PATTERN")

    query = """
    SELECT
        CASE
            WHEN job_title ILIKE '%chief executive%' OR job_title ILIKE '%CEO%' OR job_title = 'CEO' THEN 'CEO'
            WHEN job_title ILIKE '%chief financial%' OR job_title ILIKE '%CFO%' OR job_title = 'CFO' THEN 'CFO'
            WHEN job_title ILIKE '%human resource%' OR job_title ILIKE '%HR%' OR job_title ILIKE '%chief people%' OR job_title ILIKE '%CHRO%' THEN 'HR'
            WHEN job_title ILIKE '%chief technology%' OR job_title ILIKE '%CTO%' OR job_title = 'CTO' THEN 'CTO'
            WHEN job_title ILIKE '%chief marketing%' OR job_title ILIKE '%CMO%' OR job_title = 'CMO' THEN 'CMO'
            WHEN job_title ILIKE '%chief operating%' OR job_title ILIKE '%COO%' OR job_title = 'COO' THEN 'COO'
            ELSE 'OTHER'
        END as matched_slot_type,
        COUNT(*) as count
    FROM outreach.people
    WHERE job_title IS NOT NULL
    GROUP BY matched_slot_type
    ORDER BY count DESC;
    """

    try:
        conn = writer._get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()

            print(f"{'Matched Slot Type':<20} {'Count':>15}")
            print(f"{'-'*20} {'-'*15}")
            for row in results:
                print(f"{row[0]:<20} {row[1]:>15,}")

            total = sum(row[1] for row in results)
            print(f"\n{'TOTAL':<20} {total:>15,}")

    except Exception as e:
        print(f"ERROR: {e}")


def investigate_person_unique_id_usage(writer: SimpleNeonWriter):
    """4. Check person_unique_id usage across tables."""
    print_section("4. PERSON_UNIQUE_ID USAGE ANALYSIS")

    query = """
    SELECT
        'people.company_slot' as source_table,
        COUNT(DISTINCT person_unique_id) as distinct_person_ids,
        COUNT(*) as total_filled_slots
    FROM people.company_slot
    WHERE person_unique_id IS NOT NULL

    UNION ALL

    SELECT
        'outreach.people' as source_table,
        COUNT(DISTINCT person_unique_id) as distinct_person_ids,
        COUNT(*) as total_records
    FROM outreach.people
    WHERE person_unique_id IS NOT NULL;
    """

    try:
        conn = writer._get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()

            print(f"{'Source Table':<25} {'Distinct person_unique_id':>30} {'Total Records':>20}")
            print(f"{'-'*25} {'-'*30} {'-'*20}")
            for row in results:
                print(f"{row[0]:<25} {row[1]:>30,} {row[2]:>20,}")

    except Exception as e:
        print(f"ERROR: {e}")


def investigate_outreach_people_schema(writer: SimpleNeonWriter):
    """Check outreach.people schema for linking columns."""
    print_section("5. OUTREACH.PEOPLE SCHEMA (KEY COLUMNS)")

    query = """
    SELECT
        column_name,
        data_type,
        is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'outreach'
      AND table_name = 'people'
      AND column_name IN ('person_unique_id', 'outreach_id', 'company_unique_id', 'sovereign_company_id', 'job_title', 'email', 'email_status')
    ORDER BY column_name;
    """

    try:
        conn = writer._get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()

            print(f"{'Column Name':<25} {'Data Type':<20} {'Nullable':<10}")
            print(f"{'-'*25} {'-'*20} {'-'*10}")
            for row in results:
                print(f"{row[0]:<25} {row[1]:<20} {row[2]:<10}")

    except Exception as e:
        print(f"ERROR: {e}")


def sample_outreach_people(writer: SimpleNeonWriter):
    """Sample outreach.people records."""
    print_section("6. SAMPLE OUTREACH.PEOPLE RECORDS (5 rows)")

    query = """
    SELECT
        person_unique_id,
        outreach_id,
        company_unique_id,
        first_name,
        last_name,
        job_title,
        email,
        email_status
    FROM outreach.people
    WHERE job_title IS NOT NULL
    LIMIT 5;
    """

    try:
        conn = writer._get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()

            for row in results:
                print(f"\nPerson ID: {row[0]}")
                print(f"  Outreach ID: {row[1]}")
                print(f"  Company ID: {row[2]}")
                print(f"  Name: {row[3]} {row[4]}")
                print(f"  Job Title: {row[5]}")
                print(f"  Email: {row[6]}")
                print(f"  Email Status: {row[7]}")

    except Exception as e:
        print(f"ERROR: {e}")


def investigate_potential_matches(writer: SimpleNeonWriter):
    """Check for potential matches between unfilled slots and outreach.people."""
    print_section("7. POTENTIAL MATCHES ANALYSIS")

    query = """
    SELECT
        cs.slot_type,
        COUNT(DISTINCT p.person_unique_id) as matching_people_count,
        COUNT(DISTINCT cs.slot_id) as unfilled_slots_with_matches
    FROM people.company_slot cs
    LEFT JOIN outreach.people p
        ON cs.company_unique_id = p.company_unique_id
        AND cs.person_unique_id IS NULL
        AND (
            (cs.slot_type = 'CEO' AND (p.job_title ILIKE '%chief executive%' OR p.job_title ILIKE '%CEO%'))
            OR (cs.slot_type = 'CFO' AND (p.job_title ILIKE '%chief financial%' OR p.job_title ILIKE '%CFO%'))
            OR (cs.slot_type = 'HR' AND (p.job_title ILIKE '%human resource%' OR p.job_title ILIKE '%chief people%' OR p.job_title ILIKE '%CHRO%'))
            OR (cs.slot_type = 'CTO' AND (p.job_title ILIKE '%chief technology%' OR p.job_title ILIKE '%CTO%'))
            OR (cs.slot_type = 'CMO' AND (p.job_title ILIKE '%chief marketing%' OR p.job_title ILIKE '%CMO%'))
            OR (cs.slot_type = 'COO' AND (p.job_title ILIKE '%chief operating%' OR p.job_title ILIKE '%COO%'))
        )
    WHERE cs.person_unique_id IS NULL
    GROUP BY cs.slot_type
    ORDER BY matching_people_count DESC;
    """

    try:
        conn = writer._get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()

            print(f"{'Slot Type':<15} {'Matching People':>20} {'Slots w/ Matches':>20}")
            print(f"{'-'*15} {'-'*20} {'-'*20}")
            for row in results:
                print(f"{row[0]:<15} {row[1]:>20,} {row[2]:>20,}")

            total_matches = sum(row[1] for row in results if row[1])
            print(f"\n{'TOTAL MATCHES':<15} {total_matches:>20,}")

    except Exception as e:
        print(f"ERROR: {e}")


def explain_linking_mechanism():
    """Explain how slot filling should work."""
    print_section("8. SLOT FILLING MECHANISM EXPLANATION")

    print("""
LINKING MECHANISM:
==================

1. JOIN PATH:
   people.company_slot.company_unique_id = outreach.people.company_unique_id

   This is the PRIMARY join key for matching companies between the two tables.

2. SLOT ASSIGNMENT:
   When a person in outreach.people matches the criteria for a slot type:

   UPDATE people.company_slot
   SET person_unique_id = outreach.people.person_unique_id,
       is_filled = true,
       filled_at = NOW()
   WHERE company_unique_id = outreach.people.company_unique_id
     AND slot_type = <matched_slot_type>
     AND person_unique_id IS NULL;

3. MATCHING CRITERIA:
   - CEO: job_title ILIKE '%chief executive%' OR '%CEO%'
   - CFO: job_title ILIKE '%chief financial%' OR '%CFO%'
   - HR: job_title ILIKE '%human resource%' OR '%chief people%' OR '%CHRO%'
   - CTO: job_title ILIKE '%chief technology%' OR '%CTO%'
   - CMO: job_title ILIKE '%chief marketing%' OR '%CMO%'
   - COO: job_title ILIKE '%chief operating%' OR '%COO%'

4. CONSTRAINTS:
   - person_unique_id in outreach.people must NOT be NULL
   - Email should be present and verified (email_status = 'valid' or 'verified')
   - Only fill slots where person_unique_id IS NULL (unfilled slots)
   - Respect is_primary flag for slot priority

5. VALIDATION:
   - Check email_status before assignment
   - Verify company_unique_id exists in both tables
   - Ensure no duplicate assignments (one person per slot per company)
""")


def main():
    """Main execution."""
    print(f"\nSlot Filling Investigation - READ ONLY")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    # Initialize Neon writer
    config = NeonConfig()
    if not config.is_valid():
        print("ERROR: Neon configuration is invalid. Check environment variables.")
        return

    writer = SimpleNeonWriter(config)

    try:
        # Run all investigations
        investigate_unfilled_slots(writer)
        investigate_slot_structure(writer)
        investigate_people_job_titles(writer)
        investigate_person_unique_id_usage(writer)
        investigate_outreach_people_schema(writer)
        sample_outreach_people(writer)
        investigate_potential_matches(writer)
        explain_linking_mechanism()

        print(f"\n{'='*80}")
        print(f"Investigation Complete")
        print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")

    finally:
        writer.close()


if __name__ == "__main__":
    main()
