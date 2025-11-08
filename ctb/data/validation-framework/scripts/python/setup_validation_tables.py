#!/usr/bin/env python3
"""
Setup validation tables in Neon database
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def setup_tables():
    """Create validation tables in Neon"""

    database_url = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')

    if not database_url:
        raise ValueError("DATABASE_URL not set in .env")

    print("Connecting to Neon database...")
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cursor = conn.cursor()

    print("Reading SQL setup script...")
    # Go up to scripts/python, then up to validation-framework, then into sql
    sql_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'sql',
        'neon_wv_validation_setup.sql'
    )

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    print("Executing SQL setup...")
    try:
        cursor.execute(sql)
        print("✓ Validation tables created successfully!")

        # Verify tables exist
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema IN ('shq', 'marketing')
            AND table_name IN ('validation_log', 'company_invalid', 'people_invalid')
            ORDER BY table_name
        """)

        tables = cursor.fetchall()
        print("\n✓ Created tables:")
        for table in tables:
            print(f"  - {table[0]}")

    except Exception as e:
        print(f"✗ Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    setup_tables()
