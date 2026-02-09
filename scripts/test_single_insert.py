"""
Test inserting a single person record.
"""

import os
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

def test_insert():
    """Test inserting one person."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
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

        person_id = f"04.04.02.99.{next_seq:06d}.{(next_seq % 1000):03d}"
        slot_uid = f"04.04.05.99.{next_seq:06d}.{(next_seq % 1000):03d}"

        print(f"Attempting to insert person with ID: {person_id}")

        # Test data
        test_email = f"test_{next_seq}@example.com"
        company_uid = "074481e5-21fe-4d79-a44b-c57845e6ed7d"  # From previous test

        cursor.execute("""
            INSERT INTO people.people_master (
                unique_id,
                company_unique_id,
                company_slot_unique_id,
                first_name,
                last_name,
                title,
                email,
                work_phone_e164,
                linkedin_url,
                source_system,
                promoted_from_intake_at,
                created_at,
                updated_at,
                last_verified_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW(), NOW())
            RETURNING unique_id
        """, (
            person_id,
            company_uid,
            slot_uid,
            'Test',
            'Person',
            'Test Title',
            test_email,
            '+1 555 555 5555',
            'https://linkedin.com/in/test',
            'test'
        ))

        result = cursor.fetchone()
        print(f"Successfully inserted person: {result['unique_id']}")

        conn.commit()

        # Now delete the test record
        cursor.execute("DELETE FROM people.people_master WHERE unique_id = %s", (person_id,))
        conn.commit()
        print(f"Cleaned up test record")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == '__main__':
    test_insert()
