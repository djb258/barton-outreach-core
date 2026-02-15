"""
Fill Missing LinkedIn URLs and Emails from Hunter Contact Data

This script enriches people_master records with data from enrichment.hunter_contact
by matching on domain + first name + last name.

Task 1: Fill missing LinkedIn URLs
Task 2: Fill missing emails
Task 3: Report coverage statistics

Status: Production Ready
Date: 2026-02-05
"""

import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_db_connection():
    """Get PostgreSQL database connection to Neon"""
    connection_string = os.getenv("DATABASE_URL") or os.getenv("NEON_CONNECTION_STRING")

    if not connection_string:
        raise ValueError("DATABASE_URL or NEON_CONNECTION_STRING environment variable not set")

    return psycopg2.connect(connection_string)


def fill_linkedin_urls():
    """Fill missing LinkedIn URLs from Hunter contact data"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("\n[TASK 1] Filling missing LinkedIn URLs from Hunter contact data...")

        query = """
        WITH people_needing_linkedin AS (
            SELECT
                pm.unique_id,
                pm.first_name,
                pm.last_name,
                o.domain
            FROM people.people_master pm
            JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id
            JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
            WHERE cs.is_filled = true
            AND (pm.linkedin_url IS NULL OR pm.linkedin_url = '')
            AND pm.first_name IS NOT NULL
            AND pm.last_name IS NOT NULL
        ),
        hunter_matches AS (
            SELECT DISTINCT ON (pnl.unique_id)
                pnl.unique_id,
                hc.linkedin_url
            FROM people_needing_linkedin pnl
            JOIN enrichment.hunter_contact hc ON LOWER(pnl.domain) = LOWER(hc.domain)
                AND LOWER(pnl.first_name) = LOWER(hc.first_name)
                AND LOWER(pnl.last_name) = LOWER(hc.last_name)
            WHERE hc.linkedin_url IS NOT NULL AND hc.linkedin_url != ''
            ORDER BY pnl.unique_id, hc.confidence_score DESC NULLS LAST
        )
        UPDATE people.people_master pm
        SET linkedin_url = hm.linkedin_url,
            updated_at = NOW()
        FROM hunter_matches hm
        WHERE pm.unique_id = hm.unique_id;
        """

        cursor.execute(query)
        rows_updated = cursor.rowcount
        conn.commit()

        print(f"[OK] Filled {rows_updated} LinkedIn URLs from Hunter contact data")
        return rows_updated

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to fill LinkedIn URLs: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


def fill_emails():
    """Fill missing emails from Hunter contact data"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("\n[TASK 2] Filling missing emails from Hunter contact data...")

        query = """
        WITH people_needing_email AS (
            SELECT
                pm.unique_id,
                pm.first_name,
                pm.last_name,
                o.domain
            FROM people.people_master pm
            JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id
            JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
            WHERE cs.is_filled = true
            AND (pm.email IS NULL OR pm.email = '')
            AND pm.first_name IS NOT NULL
            AND pm.last_name IS NOT NULL
        ),
        hunter_matches AS (
            SELECT DISTINCT ON (pne.unique_id)
                pne.unique_id,
                hc.email
            FROM people_needing_email pne
            JOIN enrichment.hunter_contact hc ON LOWER(pne.domain) = LOWER(hc.domain)
                AND LOWER(pne.first_name) = LOWER(hc.first_name)
                AND LOWER(pne.last_name) = LOWER(hc.last_name)
            WHERE hc.email IS NOT NULL AND hc.email != ''
            ORDER BY pne.unique_id, hc.confidence_score DESC NULLS LAST
        )
        UPDATE people.people_master pm
        SET email = hm.email,
            updated_at = NOW()
        FROM hunter_matches hm
        WHERE pm.unique_id = hm.unique_id;
        """

        cursor.execute(query)
        rows_updated = cursor.rowcount
        conn.commit()

        print(f"[OK] Filled {rows_updated} emails from Hunter contact data")
        return rows_updated

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to fill emails: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


def check_coverage():
    """Check final coverage statistics for filled slots"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        print("\n[TASK 3] Checking final coverage for filled slots...")

        query = """
        SELECT
            COUNT(*) as total_people,
            COUNT(linkedin_url) FILTER (WHERE linkedin_url IS NOT NULL AND linkedin_url != '') as has_linkedin,
            COUNT(email) FILTER (WHERE email IS NOT NULL AND email != '') as has_email,
            COUNT(title) FILTER (WHERE title IS NOT NULL AND title != '') as has_title,
            ROUND(100.0 * COUNT(linkedin_url) FILTER (WHERE linkedin_url IS NOT NULL AND linkedin_url != '') / COUNT(*), 2) as linkedin_pct,
            ROUND(100.0 * COUNT(email) FILTER (WHERE email IS NOT NULL AND email != '') / COUNT(*), 2) as email_pct,
            ROUND(100.0 * COUNT(title) FILTER (WHERE title IS NOT NULL AND title != '') / COUNT(*), 2) as title_pct
        FROM people.people_master pm
        WHERE EXISTS (
            SELECT 1 FROM people.company_slot cs
            WHERE cs.person_unique_id = pm.unique_id
            AND cs.is_filled = true
        );
        """

        cursor.execute(query)
        result = cursor.fetchone()

        print("\n" + "=" * 70)
        print("COVERAGE REPORT - PEOPLE IN FILLED SLOTS")
        print("=" * 70)
        print(f"Total People:        {result['total_people']:,}")
        print(f"Has LinkedIn URL:    {result['has_linkedin']:,} ({result['linkedin_pct']}%)")
        print(f"Has Email:           {result['has_email']:,} ({result['email_pct']}%)")
        print(f"Has Title:           {result['has_title']:,} ({result['title_pct']}%)")
        print("=" * 70)

        return dict(result)

    except Exception as e:
        print(f"[ERROR] Failed to check coverage: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


def main():
    """Main execution"""
    print("=" * 70)
    print("FILL MISSING DATA FROM HUNTER CONTACT")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Task 1: Fill LinkedIn URLs
        linkedin_filled = fill_linkedin_urls()

        # Task 2: Fill emails
        emails_filled = fill_emails()

        # Task 3: Check coverage
        coverage = check_coverage()

        # Summary
        print("\n" + "=" * 70)
        print("EXECUTION SUMMARY")
        print("=" * 70)
        print(f"LinkedIn URLs filled: {linkedin_filled:,}")
        print(f"Emails filled:        {emails_filled:,}")
        print(f"Total enrichments:    {linkedin_filled + emails_filled:,}")
        print("=" * 70)
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
