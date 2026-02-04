#!/usr/bin/env python3
"""
Check for city/state data in related tables.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def check_location_data():
    """Query for city/state columns in related schemas."""

    # Build connection string from environment
    conn_str = f"postgresql://{os.getenv('NEON_USER')}:{os.getenv('NEON_PASSWORD')}@{os.getenv('NEON_HOST')}/{os.getenv('NEON_DATABASE')}?sslmode=require"

    try:
        conn = psycopg2.connect(conn_str)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check for tables with location data
        query = """
            SELECT
                table_schema,
                table_name,
                string_agg(column_name, ', ' ORDER BY ordinal_position) as columns
            FROM information_schema.columns
            WHERE
                table_schema IN ('cl', 'outreach', 'intake', 'marketing')
                AND (
                    column_name ILIKE '%city%'
                    OR column_name ILIKE '%state%'
                    OR column_name ILIKE '%location%'
                    OR column_name ILIKE '%address%'
                    OR column_name ILIKE '%country%'
                    OR column_name ILIKE '%zip%'
                    OR column_name ILIKE '%postal%'
                )
            GROUP BY table_schema, table_name
            ORDER BY table_schema, table_name;
        """

        cursor.execute(query)
        results = cursor.fetchall()

        print(f"\n{'='*100}")
        print("TABLES WITH LOCATION COLUMNS (city, state, address, etc.)")
        print(f"{'='*100}\n")

        if results:
            for row in results:
                print(f"Schema: {row['table_schema']}")
                print(f"Table:  {row['table_name']}")
                print(f"Columns: {row['columns']}")
                print(f"{'-'*100}\n")
        else:
            print("No location columns found in cl, outreach, intake, or marketing schemas.")

        # Sample cl.company_identity to see actual data
        print(f"\n{'='*100}")
        print("SAMPLE DATA FROM cl.company_identity (first 3 records)")
        print(f"{'='*100}\n")

        sample_query = """
            SELECT
                company_name,
                company_domain,
                state_verified,
                state_match_result,
                canonical_name
            FROM cl.company_identity
            LIMIT 3;
        """

        cursor.execute(sample_query)
        samples = cursor.fetchall()

        for sample in samples:
            print(f"Company Name: {sample['company_name']}")
            print(f"Domain: {sample['company_domain']}")
            print(f"State Verified: {sample['state_verified']}")
            print(f"State Match Result: {sample['state_match_result']}")
            print(f"Canonical Name: {sample['canonical_name']}")
            print(f"{'-'*100}\n")

        cursor.close()
        conn.close()

        print("\nRECOMMENDATION:")
        print("- Company names are in: cl.company_identity.company_name (or canonical_name)")
        print("- State data is in: cl.company_identity.state_verified")
        print("- City data: Check intake or marketing schemas if available")
        print("- Domain: cl.company_identity.company_domain (for matching)")

    except Exception as e:
        print(f"Error querying database: {e}")
        raise

if __name__ == "__main__":
    check_location_data()
