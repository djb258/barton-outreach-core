"""
Export companies with email pattern issues to CSV files.

Two issue types:
1. GUESSED patterns (no Hunter data) - ~8,535 companies
2. INVALID patterns (hardcoded domain or malformed) - ~38,233 companies
"""

import os
import psycopg2
import csv
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
conn_params = {
    'host': os.getenv('NEON_HOST'),
    'database': os.getenv('NEON_DATABASE'),
    'user': os.getenv('NEON_USER'),
    'password': os.getenv('NEON_PASSWORD'),
    'sslmode': 'require',
    'port': 5432
}

# Output directory
output_dir = r"C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\exports\pattern_issues"
os.makedirs(output_dir, exist_ok=True)

# Query 1: GUESSED patterns (no Hunter data)
guessed_query = """
SELECT
    o.outreach_id,
    o.domain,
    ci.company_name,
    ct.email_method,
    ct.confidence_score,
    'GUESSED_NO_HUNTER' AS issue_type
FROM outreach.company_target ct
JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE ct.email_method IS NOT NULL
  AND hc.domain IS NULL
ORDER BY o.domain;
"""

# Query 2: INVALID patterns (hardcoded domain or malformed)
invalid_query = """
SELECT
    o.outreach_id,
    o.domain,
    ci.company_name,
    ct.email_method,
    ct.confidence_score,
    'INVALID_HARDCODED_DOMAIN' AS issue_type
FROM outreach.company_target ct
JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
WHERE ct.email_method IS NOT NULL
  AND ct.email_method LIKE '%@%'
ORDER BY o.domain;
"""

def export_to_csv(query, output_path, chunk_size=None):
    """Execute query and export results to CSV, optionally in chunks."""
    print(f"\nExecuting query for: {os.path.basename(output_path)}")

    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()

    try:
        cursor.execute(query)

        # Get column names
        columns = [desc[0] for desc in cursor.description]

        if chunk_size is None:
            # Single file export
            rows = cursor.fetchall()
            print(f"  Found {len(rows):,} records")

            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(rows)

            print(f"  [OK] Exported to: {output_path}")
            return len(rows)
        else:
            # Chunked export
            total_rows = 0
            chunk_num = 1

            while True:
                rows = cursor.fetchmany(chunk_size)
                if not rows:
                    break

                # Generate chunk filename
                base, ext = os.path.splitext(output_path)
                chunk_path = f"{base}_part{chunk_num}{ext}"

                with open(chunk_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                    writer.writerows(rows)

                total_rows += len(rows)
                print(f"  [OK] Chunk {chunk_num}: {len(rows):,} records -> {os.path.basename(chunk_path)}")
                chunk_num += 1

            print(f"  Total: {total_rows:,} records in {chunk_num - 1} chunk(s)")
            return total_rows

    finally:
        cursor.close()
        conn.close()

# Export 1: Guessed patterns (single file)
print("=" * 80)
print("EXPORT 1: GUESSED PATTERNS (NO HUNTER DATA)")
print("=" * 80)
guessed_count = export_to_csv(
    guessed_query,
    os.path.join(output_dir, "guessed_patterns.csv")
)

# Export 2: Invalid patterns (chunked at 24,000)
print("\n" + "=" * 80)
print("EXPORT 2: INVALID PATTERNS (HARDCODED DOMAIN)")
print("=" * 80)
invalid_count = export_to_csv(
    invalid_query,
    os.path.join(output_dir, "invalid_patterns.csv"),
    chunk_size=24000
)

# Summary
print("\n" + "=" * 80)
print("EXPORT SUMMARY")
print("=" * 80)
print(f"Guessed patterns (no Hunter data): {guessed_count:,} companies")
print(f"Invalid patterns (hardcoded domain): {invalid_count:,} companies")
print(f"Total companies with pattern issues: {guessed_count + invalid_count:,}")
print(f"\nAll exports saved to:")
print(f"  {output_dir}")
print("=" * 80)
