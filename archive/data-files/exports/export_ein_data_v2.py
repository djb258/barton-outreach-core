"""
Export EIN data to CSV files with 24,000 row limit per file.
Handles companies with and without CL company_identity records.
"""
import os
import csv
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

def export_with_ein_and_cl():
    """Export companies WITH EIN and CL company_identity."""
    print("=" * 80)
    print("EXPORTING COMPANIES WITH EIN (CL MATCH)")
    print("=" * 80)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get total count
    cur.execute("""
        SELECT COUNT(*) as count
        FROM outreach.outreach o
        JOIN outreach.dol d ON o.outreach_id = d.outreach_id
        JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
        WHERE d.ein IS NOT NULL
    """)
    total_count = cur.fetchone()['count']
    print(f"\nTotal companies WITH EIN (CL match): {total_count:,}")

    # Calculate number of files needed
    chunk_size = 24000
    num_files = (total_count + chunk_size - 1) // chunk_size
    print(f"Will create {num_files} file(s) with max {chunk_size:,} rows each\n")

    # Export in chunks
    for file_num in range(num_files):
        offset = file_num * chunk_size
        filename = f"companies_with_ein_cl_match_part{file_num + 1}.csv"
        filepath = os.path.join(os.path.dirname(__file__), filename)

        print(f"Exporting {filename} (rows {offset + 1:,} to {min(offset + chunk_size, total_count):,})...")

        cur.execute("""
            SELECT
                o.outreach_id,
                o.domain,
                ci.company_name,
                ci.sovereign_company_id,
                d.ein,
                d.filing_present,
                d.funding_type,
                d.broker_or_advisor,
                d.carrier,
                d.renewal_month,
                d.outreach_start_month
            FROM outreach.outreach o
            JOIN outreach.dol d ON o.outreach_id = d.outreach_id
            JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
            WHERE d.ein IS NOT NULL
            ORDER BY ci.company_name
            LIMIT %s OFFSET %s
        """, (chunk_size, offset))

        rows = cur.fetchall()

        if rows:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            print(f"  SUCCESS: Exported {len(rows):,} rows to {filename}")
        else:
            print(f"  WARNING: No rows found for {filename}")

    cur.close()
    conn.close()
    print()

def export_with_ein_no_cl():
    """Export companies WITH EIN but NO CL company_identity."""
    print("=" * 80)
    print("EXPORTING COMPANIES WITH EIN (NO CL MATCH)")
    print("=" * 80)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get total count
    cur.execute("""
        SELECT COUNT(*) as count
        FROM outreach.outreach o
        JOIN outreach.dol d ON o.outreach_id = d.outreach_id
        LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
        WHERE d.ein IS NOT NULL AND ci.sovereign_company_id IS NULL
    """)
    total_count = cur.fetchone()['count']
    print(f"\nTotal companies WITH EIN (NO CL match): {total_count:,}")

    # Calculate number of files needed
    chunk_size = 24000
    num_files = (total_count + chunk_size - 1) // chunk_size
    print(f"Will create {num_files} file(s) with max {chunk_size:,} rows each\n")

    # Export in chunks
    for file_num in range(num_files):
        offset = file_num * chunk_size
        filename = f"companies_with_ein_no_cl_match_part{file_num + 1}.csv"
        filepath = os.path.join(os.path.dirname(__file__), filename)

        print(f"Exporting {filename} (rows {offset + 1:,} to {min(offset + chunk_size, total_count):,})...")

        cur.execute("""
            SELECT
                o.outreach_id,
                o.domain,
                o.sovereign_id,
                d.ein,
                d.filing_present,
                d.funding_type,
                d.broker_or_advisor,
                d.carrier,
                d.renewal_month,
                d.outreach_start_month,
                ct.email_method,
                ct.execution_status
            FROM outreach.outreach o
            JOIN outreach.dol d ON o.outreach_id = d.outreach_id
            LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
            LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
            WHERE d.ein IS NOT NULL AND ci.sovereign_company_id IS NULL
            ORDER BY o.domain
            LIMIT %s OFFSET %s
        """, (chunk_size, offset))

        rows = cur.fetchall()

        if rows:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            print(f"  SUCCESS: Exported {len(rows):,} rows to {filename}")
        else:
            print(f"  WARNING: No rows found for {filename}")

    cur.close()
    conn.close()
    print()

def export_without_ein():
    """Export companies WITHOUT EIN in chunks of 24,000."""
    print("=" * 80)
    print("EXPORTING COMPANIES WITHOUT EIN")
    print("=" * 80)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get total count
    cur.execute("""
        SELECT COUNT(*) as count
        FROM outreach.outreach o
        LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
        WHERE d.ein IS NULL OR d.outreach_id IS NULL
    """)
    total_count = cur.fetchone()['count']
    print(f"\nTotal companies WITHOUT EIN: {total_count:,}")

    # Calculate number of files needed
    chunk_size = 24000
    num_files = (total_count + chunk_size - 1) // chunk_size
    print(f"Will create {num_files} file(s) with max {chunk_size:,} rows each\n")

    # Export in chunks
    for file_num in range(num_files):
        offset = file_num * chunk_size
        filename = f"companies_without_ein_part{file_num + 1}.csv"
        filepath = os.path.join(os.path.dirname(__file__), filename)

        print(f"Exporting {filename} (rows {offset + 1:,} to {min(offset + chunk_size, total_count):,})...")

        cur.execute("""
            SELECT
                o.outreach_id,
                o.domain,
                o.sovereign_id,
                ci.company_name,
                ci.sovereign_company_id,
                ct.email_method,
                ct.execution_status
            FROM outreach.outreach o
            LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
            LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
            LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
            WHERE d.ein IS NULL OR d.outreach_id IS NULL
            ORDER BY ci.company_name NULLS LAST, o.domain
            LIMIT %s OFFSET %s
        """, (chunk_size, offset))

        rows = cur.fetchall()

        if rows:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            print(f"  SUCCESS: Exported {len(rows):,} rows to {filename}")
        else:
            print(f"  WARNING: No rows found for {filename}")

    cur.close()
    conn.close()
    print()

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("EIN DATA EXPORT UTILITY V2")
    print("=" * 80)
    print("Export directory: C:\\Users\\CUSTOM PC\\Desktop\\Cursor Builds\\barton-outreach-core\\exports")
    print("Row limit per file: 24,000")
    print("=" * 80 + "\n")

    try:
        export_with_ein_and_cl()
        export_with_ein_no_cl()
        export_without_ein()

        print("=" * 80)
        print("EXPORT COMPLETE")
        print("=" * 80)
        print("\nAll files saved to:")
        print("C:\\Users\\CUSTOM PC\\Desktop\\Cursor Builds\\barton-outreach-core\\exports\\")
        print("\nFile Summary:")
        print("- companies_with_ein_cl_match_part*.csv - EIN data with CL company names")
        print("- companies_with_ein_no_cl_match_part*.csv - EIN data without CL match")
        print("- companies_without_ein_part*.csv - No EIN data")
        print()

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
