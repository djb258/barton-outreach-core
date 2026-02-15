"""
EIN Data Status Check
Validates DOL/EIN data and identifies discrepancies
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_neon_connection():
    """Establish Neon database connection"""
    return psycopg2.connect(
        host=os.getenv("NEON_HOST"),
        database=os.getenv("NEON_DATABASE"),
        user=os.getenv("NEON_USER"),
        password=os.getenv("NEON_PASSWORD"),
        sslmode="require"
    )

def run_query(conn, query, description):
    """Execute query and return results"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        result = cur.fetchall()
        print(f"\n{'='*80}")
        print(f"{description}")
        print(f"{'='*80}")
        for row in result:
            for key, value in row.items():
                print(f"{key}: {value:,}" if isinstance(value, int) else f"{key}: {value}")
        return result

def main():
    conn = get_neon_connection()

    try:
        # Query 1: Companies in outreach.dol with EINs
        run_query(
            conn,
            "SELECT COUNT(*) AS companies_with_ein FROM outreach.dol WHERE ein IS NOT NULL;",
            "Query 1: Companies in outreach.dol with EINs"
        )

        # Query 2: EINs in dol.ein_urls from Hunter enrichment
        run_query(
            conn,
            "SELECT COUNT(*) AS hunter_enriched_eins FROM dol.ein_urls WHERE discovery_method = 'hunter_dol_enrichment';",
            "Query 2: EINs in dol.ein_urls (Hunter enriched)"
        )

        # Query 3: Companies with filing_present = TRUE
        run_query(
            conn,
            "SELECT COUNT(*) AS companies_with_filings FROM outreach.dol WHERE filing_present = TRUE;",
            "Query 3: Companies with filing_present = TRUE"
        )

        # Query 4: Total outreach spine count
        run_query(
            conn,
            "SELECT COUNT(*) AS total_outreach_spine FROM outreach.outreach;",
            "Query 4: Total outreach spine records"
        )

        # Query 5: Breakdown of companies with/without EINs
        run_query(
            conn,
            """
            SELECT
                COUNT(*) FILTER (WHERE d.ein IS NOT NULL) AS with_ein,
                COUNT(*) FILTER (WHERE d.ein IS NULL OR d.outreach_id IS NULL) AS without_ein,
                COUNT(*) AS total
            FROM outreach.outreach o
            LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id;
            """,
            "Query 5: Breakdown of outreach companies with/without EINs"
        )

        # Query 6: Companies with EIN but no sovereign_id
        run_query(
            conn,
            """
            SELECT COUNT(*) AS ein_no_sovereign
            FROM outreach.outreach o
            JOIN outreach.dol d ON o.outreach_id = d.outreach_id
            WHERE d.ein IS NOT NULL
              AND o.sovereign_id IS NULL;
            """,
            "Query 6: Companies with EIN but no sovereign_id (orphaned)"
        )

        # Additional Query: Check dol.ein_urls total count
        run_query(
            conn,
            "SELECT COUNT(*) AS total_ein_urls FROM dol.ein_urls;",
            "Additional Query 7: Total records in dol.ein_urls"
        )

        # Additional Query: Discovery method breakdown
        run_query(
            conn,
            """
            SELECT
                discovery_method,
                COUNT(*) AS count
            FROM dol.ein_urls
            GROUP BY discovery_method
            ORDER BY count DESC;
            """,
            "Additional Query 8: Discovery method breakdown in dol.ein_urls"
        )

        # Additional Query: Check if Hunter EINs are linked to outreach.dol
        run_query(
            conn,
            """
            SELECT
                COUNT(DISTINCT e.ein) AS unique_hunter_eins,
                COUNT(DISTINCT d.ein) AS hunter_eins_in_dol,
                COUNT(DISTINCT e.ein) - COUNT(DISTINCT d.ein) AS hunter_eins_not_in_dol
            FROM dol.ein_urls e
            LEFT JOIN outreach.dol d ON e.ein = d.ein
            WHERE e.discovery_method = 'hunter_dol_enrichment';
            """,
            "Additional Query 9: Hunter EINs vs outreach.dol linkage"
        )

        print(f"\n{'='*80}")
        print("EIN STATUS CHECK COMPLETE")
        print(f"{'='*80}\n")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
