#!/usr/bin/env python3
"""
Check column structure for company name, city, state matching.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def check_columns():
    """Query schema columns from Neon database."""

    # Build connection string from environment
    conn_str = f"postgresql://{os.getenv('NEON_USER')}:{os.getenv('NEON_PASSWORD')}@{os.getenv('NEON_HOST')}/{os.getenv('NEON_DATABASE')}?sslmode=require"

    queries = [
        ("outreach.company_target", """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'outreach' AND table_name = 'company_target'
            ORDER BY ordinal_position;
        """),
        ("outreach.outreach", """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'outreach' AND table_name = 'outreach'
            ORDER BY ordinal_position;
        """),
        ("cl.company_identity", """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'cl' AND table_name = 'company_identity'
            ORDER BY ordinal_position;
        """)
    ]

    try:
        conn = psycopg2.connect(conn_str)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        for table_name, query in queries:
            print(f"\n{'='*80}")
            print(f"TABLE: {table_name}")
            print(f"{'='*80}")

            cursor.execute(query)
            columns = cursor.fetchall()

            if columns:
                print(f"\n{'Column Name':<40} {'Data Type':<30}")
                print(f"{'-'*40} {'-'*30}")
                for col in columns:
                    print(f"{col['column_name']:<40} {col['data_type']:<30}")
            else:
                print("No columns found or table does not exist.")

            # Highlight matching-relevant columns
            name_cols = [c['column_name'] for c in columns if any(x in c['column_name'].lower() for x in ['name', 'company'])]
            location_cols = [c['column_name'] for c in columns if any(x in c['column_name'].lower() for x in ['city', 'state', 'location', 'address'])]

            if name_cols:
                print(f"\n[NAME COLUMNS]: {', '.join(name_cols)}")
            if location_cols:
                print(f"[LOCATION COLUMNS]: {', '.join(location_cols)}")

        cursor.close()
        conn.close()

        print(f"\n{'='*80}")
        print("RECOMMENDATION:")
        print("='*80")
        print("For company name/city/state matching, check the highlighted columns above.")
        print("Company name is likely stored in cl.company_identity or outreach.company_target.")

    except Exception as e:
        print(f"Error querying database: {e}")
        raise

if __name__ == "__main__":
    check_columns()
