#!/usr/bin/env python3
"""Check company_target schema"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_neon_connection():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )

conn = get_neon_connection()

try:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get table schema
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'outreach'
              AND table_name = 'company_target'
            ORDER BY ordinal_position
        """)
        results = cur.fetchall()

        print("\noutreach.company_target columns:")
        print("-" * 60)
        for row in results:
            print(f"{row['column_name']:<30} {row['data_type']:<20} {row['is_nullable']}")

finally:
    conn.close()
