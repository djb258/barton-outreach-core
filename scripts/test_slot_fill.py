"""
Test script for slot filling functionality.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection configuration
DB_CONFIG = {
    'host': os.getenv('NEON_HOST'),
    'database': os.getenv('NEON_DATABASE'),
    'user': os.getenv('NEON_USER'),
    'password': os.getenv('NEON_PASSWORD'),
    'port': 5432,
    'sslmode': 'require'
}

def test_id_generation():
    """Test Barton ID generation."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Get next ID
    cursor.execute("""
        SELECT MAX(
            CAST(
                SPLIT_PART(unique_id, '.', 5) AS INTEGER
            )
        ) as max_seq
        FROM people.people_master
        WHERE unique_id LIKE '04.04.02.99.%'
    """)

    result = cursor.fetchone()
    max_seq = result['max_seq'] if result and result['max_seq'] else 0
    next_seq = max_seq + 1

    print(f"Current max sequential: {max_seq}")
    print(f"Next sequential: {next_seq}")

    # Generate IDs
    person_id = f"04.04.02.99.{next_seq:06d}.{(next_seq % 1000):03d}"
    slot_uid = f"04.04.05.99.{next_seq:06d}.{(next_seq % 1000):03d}"

    print(f"Next person_id: {person_id}")
    print(f"Next slot_uid: {slot_uid}")

    # Find a test outreach_id with an unfilled CEO slot
    cursor.execute("""
        SELECT
            cs.outreach_id,
            o.sovereign_id,
            ci.company_unique_id,
            cs.slot_type
        FROM people.company_slot cs
        JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
        JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
        WHERE cs.slot_type = 'CEO'
          AND (cs.is_filled = FALSE OR cs.is_filled IS NULL)
        LIMIT 1
    """)

    slot = cursor.fetchone()
    if slot:
        print(f"\nFound unfilled CEO slot:")
        print(f"  outreach_id: {slot['outreach_id']}")
        print(f"  company_unique_id: {slot['company_unique_id']}")
    else:
        print("\nNo unfilled CEO slots found")

    conn.close()

if __name__ == '__main__':
    test_id_generation()
