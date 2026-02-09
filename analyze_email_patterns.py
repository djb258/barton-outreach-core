#!/usr/bin/env python3
"""
Email Pattern Source Analysis
Identifies Hunter.io sourced vs guessed email patterns
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Neon connection
conn = psycopg2.connect(
    host=os.getenv('NEON_HOST'),
    database=os.getenv('NEON_DATABASE'),
    user=os.getenv('NEON_USER'),
    password=os.getenv('NEON_PASSWORD'),
    sslmode='require'
)

def run_query(query, description):
    print(f"\n{'='*80}")
    print(f"QUERY: {description}")
    print(f"{'='*80}\n")

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        results = cur.fetchall()

        if not results:
            print("No results found.")
            return

        # Print header
        if results:
            headers = list(results[0].keys())
            print(" | ".join(f"{h:20}" for h in headers))
            print("-" * (len(headers) * 23))

            # Print rows
            for row in results:
                print(" | ".join(f"{str(row[h]):20}" for h in headers))

    print(f"\nTotal rows: {len(results)}")

# Query 1: Email method distribution
query1 = """
SELECT email_method, COUNT(*) as count
FROM outreach.company_target
WHERE email_method IS NOT NULL
GROUP BY email_method
ORDER BY COUNT(*) DESC
LIMIT 30;
"""

# Query 2: Schema inspection
query2 = """
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'outreach'
  AND table_name = 'company_target'
ORDER BY ordinal_position;
"""

# Query 3: Hunter email patterns
query3 = """
SELECT email_pattern, COUNT(*) as count
FROM enrichment.hunter_company
WHERE email_pattern IS NOT NULL
GROUP BY email_pattern
ORDER BY COUNT(*) DESC
LIMIT 20;
"""

# Query 4: Hunter match rate
query4 = """
SELECT
    COUNT(*) AS total_with_pattern,
    COUNT(*) FILTER (WHERE hc.email_pattern IS NOT NULL) AS matched_to_hunter,
    COUNT(*) FILTER (WHERE hc.email_pattern IS NULL) AS likely_guessed
FROM outreach.company_target ct
JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE ct.email_method IS NOT NULL;
"""

# Query 5: Guessed pattern breakdown
query5 = """
SELECT ct.email_method, COUNT(*) as count
FROM outreach.company_target ct
JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE ct.email_method IS NOT NULL
  AND hc.email_pattern IS NULL
GROUP BY ct.email_method
ORDER BY COUNT(*) DESC
LIMIT 20;
"""

# Query 6: Confidence score distribution
query6 = """
SELECT
    CASE WHEN hc.domain IS NOT NULL THEN 'Hunter' ELSE 'Guessed' END AS source,
    COUNT(*) AS count,
    ROUND(AVG(ct.confidence_score)::numeric, 2) AS avg_confidence,
    MIN(ct.confidence_score) AS min_confidence,
    MAX(ct.confidence_score) AS max_confidence
FROM outreach.company_target ct
JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE ct.email_method IS NOT NULL
GROUP BY CASE WHEN hc.domain IS NOT NULL THEN 'Hunter' ELSE 'Guessed' END;
"""

# Query 7: Check for domain presence in Hunter
query7 = """
SELECT
    COUNT(DISTINCT o.domain) as total_domains,
    COUNT(DISTINCT hc.domain) as hunter_domains,
    COUNT(DISTINCT o.domain) - COUNT(DISTINCT hc.domain) as missing_from_hunter
FROM outreach.outreach o
LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE o.domain IS NOT NULL;
"""

# Query 8: Sample of guessed vs Hunter patterns
query8 = """
SELECT
    CASE WHEN hc.domain IS NOT NULL THEN 'Hunter' ELSE 'Guessed' END AS source,
    ct.email_method,
    hc.email_pattern as hunter_pattern,
    COUNT(*) as count
FROM outreach.company_target ct
JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE ct.email_method IS NOT NULL
GROUP BY
    CASE WHEN hc.domain IS NOT NULL THEN 'Hunter' ELSE 'Guessed' END,
    ct.email_method,
    hc.email_pattern
ORDER BY count DESC
LIMIT 30;
"""

try:
    run_query(query1, "1. Email Method Distribution")
    run_query(query2, "2. Company Target Schema")
    run_query(query3, "3. Hunter Email Patterns")
    run_query(query4, "4. Hunter Match Rate")
    run_query(query5, "5. Guessed Pattern Breakdown")
    run_query(query6, "6. Confidence Score Distribution (Hunter vs Guessed)")
    run_query(query7, "7. Domain Coverage in Hunter")
    run_query(query8, "8. Pattern Comparison (Hunter vs Guessed)")

    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}\n")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    conn.close()
