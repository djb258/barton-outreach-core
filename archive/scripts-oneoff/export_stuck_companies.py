#!/usr/bin/env python3
"""
Export stuck companies (no email_method AND no Hunter contacts) to CSV.
Execution Date: 2026-02-07
"""

import os
import csv
import psycopg2
from psycopg2.extras import RealDictCursor

def export_stuck_companies():
    """Export stuck companies to CSV."""

    # Neon connection string
    conn_string = (
        f"postgresql://{os.getenv('NEON_USER')}:{os.getenv('NEON_PASSWORD')}"
        f"@{os.getenv('NEON_HOST')}/{os.getenv('NEON_DATABASE')}?sslmode=require"
    )

    query = """
    SELECT
        o.outreach_id,
        o.domain,
        ci.company_name,
        ct.execution_status,
        'NO_EMAIL_PATTERN_NO_HUNTER' AS stuck_reason
    FROM outreach.outreach o
    LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
    LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
    LEFT JOIN (SELECT DISTINCT domain FROM enrichment.hunter_contact) hc
        ON LOWER(o.domain) = LOWER(hc.domain)
    WHERE (ct.email_method IS NULL)
      AND hc.domain IS NULL
    ORDER BY o.domain;
    """

    output_path = r"C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\exports\stuck_companies.csv"

    try:
        # Connect to Neon
        print("Connecting to Neon PostgreSQL...")
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Execute query
        print("Executing query...")
        cursor.execute(query)

        # Fetch all results
        results = cursor.fetchall()
        count = len(results)

        print(f"Retrieved {count:,} stuck companies")

        # Write to CSV
        if results:
            print(f"Writing to {output_path}...")
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['outreach_id', 'domain', 'company_name', 'execution_status', 'stuck_reason']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for row in results:
                    writer.writerow(row)

            print(f"[OK] Export complete: {count:,} records written to stuck_companies.csv")
        else:
            print("No stuck companies found")

        # Close connection
        cursor.close()
        conn.close()

        return count

    except Exception as e:
        print(f"ERROR: {e}")
        raise

if __name__ == "__main__":
    count = export_stuck_companies()
    print(f"\n{'='*60}")
    print(f"FINAL COUNT: {count:,} stuck companies")
    print(f"{'='*60}")
