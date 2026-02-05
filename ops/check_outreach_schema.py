#!/usr/bin/env python3
"""Check outreach.outreach table schema"""

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
              AND table_name = 'outreach'
            ORDER BY ordinal_position
        """)
        results = cur.fetchall()

        print("\noutreach.outreach columns:")
        print("-" * 60)
        for row in results:
            print(f"{row['column_name']:<30} {row['data_type']:<20} {row['is_nullable']}")

        # Get sample row
        cur.execute("SELECT * FROM outreach.outreach LIMIT 1")
        sample = cur.fetchone()

        print("\nSample row keys:")
        if sample:
            for key in sample.keys():
                print(f"  - {key}")

finally:
    conn.close()
