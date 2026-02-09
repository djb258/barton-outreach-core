#!/usr/bin/env python3
"""
Million Verifier API Connection Test

Tests that the MILLIONVERIFIER_API_KEY is configured and the API responds.
Does NOT verify any real emails - uses a test email only.

Usage:
    doppler run -- python scripts/test_millionverifier_api.py
"""

import os
import sys
import requests

def test_api_connection():
    """Test Million Verifier API connection."""

    # Check for API key
    api_key = os.getenv("MILLIONVERIFIER_API_KEY")

    if not api_key:
        print("ERROR: MILLIONVERIFIER_API_KEY not found in environment")
        print("Make sure Doppler is configured with this secret")
        return False

    print(f"API Key found: {api_key[:8]}...{api_key[-4:]}")

    # Test with a known test email (Million Verifier provides test emails)
    test_email = "test@example.com"

    url = f"https://api.millionverifier.com/api/v3/?api={api_key}&email={test_email}"

    print(f"\nTesting API with: {test_email}")
    print(f"URL: https://api.millionverifier.com/api/v3/?api=***&email={test_email}")

    try:
        response = requests.get(url, timeout=30)

        print(f"\nHTTP Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")

            # Check for error in response (empty string = no error)
            if data.get("error"):
                print(f"\nAPI Error: {data['error']}")
                return False

            # Expected fields
            result = data.get("result", "unknown")
            resultcode = data.get("resultcode", -1)

            print(f"\nResult: {result}")
            print(f"Result Code: {resultcode}")

            # Result code meanings:
            # 1 = ok/valid
            # 2 = catch_all
            # 3 = unknown
            # 4 = error
            # 5 = disposable
            # 6 = invalid

            print("\n" + "="*50)
            print("API CONNECTION TEST: PASSED")
            print("="*50)
            print("\nMillion Verifier API is configured and responding.")
            print("Ready to verify emails.")

            return True
        else:
            print(f"\nHTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("\nERROR: Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\nERROR: Request failed: {e}")
        return False
    except Exception as e:
        print(f"\nERROR: Unexpected error: {e}")
        return False


def check_email_counts():
    """Check how many emails we have to verify."""
    import psycopg2

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("\nWARNING: DATABASE_URL not found - skipping email count")
        return

    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cur = conn.cursor()

        print("\n" + "="*50)
        print("EMAIL VERIFICATION READINESS")
        print("="*50)

        # Count filled slots with emails
        cur.execute("""
            SELECT
                cs.slot_type,
                COUNT(*) as total_slots,
                COUNT(pm.email) as with_email,
                COUNT(CASE WHEN pm.email_verified = TRUE THEN 1 END) as verified,
                COUNT(CASE WHEN pm.email_verified = FALSE OR pm.email_verified IS NULL THEN 1 END) as pending
            FROM people.company_slot cs
            LEFT JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id
            WHERE cs.is_filled = TRUE
            GROUP BY cs.slot_type
            ORDER BY cs.slot_type
        """)

        rows = cur.fetchall()

        print("\nSlot Type    | Filled | With Email | Verified | Pending")
        print("-" * 60)

        total_pending = 0
        for row in rows:
            slot_type, total, with_email, verified, pending = row
            print(f"{slot_type:12} | {total:6} | {with_email:10} | {verified:8} | {pending:7}")
            total_pending += pending or 0

        print("-" * 60)
        print(f"Total emails needing verification: {total_pending:,}")

        # Estimate cost
        cost_per_email = 0.001
        estimated_cost = total_pending * cost_per_email
        print(f"Estimated verification cost: ${estimated_cost:,.2f}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"\nDatabase query error: {e}")


if __name__ == "__main__":
    print("="*50)
    print("MILLION VERIFIER API TEST")
    print("="*50)

    success = test_api_connection()

    if success:
        check_email_counts()

    sys.exit(0 if success else 1)
