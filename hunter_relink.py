#!/usr/bin/env python3
"""
Hunter Data Re-linking Script
Re-links enrichment.hunter_company and enrichment.hunter_contact to operational spine
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def get_neon_connection():
    """Connect to Neon PostgreSQL"""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        port=5432,
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )

def run_query(conn, description, query, fetch=True):
    """Execute a query and return results"""
    print(f"\n{'='*80}")
    print(f"STEP: {description}")
    print(f"{'='*80}")
    print(f"Query: {query[:200]}..." if len(query) > 200 else f"Query: {query}")
    print()

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(query)

    if fetch:
        results = cursor.fetchall()
        for row in results:
            for key, value in row.items():
                print(f"  {key}: {value}")
        return results
    else:
        rowcount = cursor.rowcount
        conn.commit()
        print(f"  Rows affected: {rowcount}")
        return rowcount

def main():
    print(f"\n{'#'*80}")
    print(f"# HUNTER DATA RE-LINKING TO OPERATIONAL SPINE")
    print(f"# Started: {datetime.now().isoformat()}")
    print(f"{'#'*80}")

    conn = get_neon_connection()

    try:
        # BASELINE COUNTS
        print("\n" + "="*80)
        print("BASELINE COUNTS (BEFORE CLEANUP)")
        print("="*80)

        run_query(conn, "hunter_company baseline", """
            SELECT
                COUNT(*) as total_hunter_company,
                COUNT(outreach_id) as with_outreach_id,
                COUNT(*) - COUNT(outreach_id) as null_outreach_id
            FROM enrichment.hunter_company;
        """)

        run_query(conn, "hunter_contact baseline", """
            SELECT
                COUNT(*) as total_hunter_contact,
                COUNT(outreach_id) as with_outreach_id,
                COUNT(*) - COUNT(outreach_id) as null_outreach_id
            FROM enrichment.hunter_contact;
        """)

        # STEP 1: Clear orphaned outreach_ids in hunter_company
        orphaned_company = run_query(conn,
            "1. Clear orphaned outreach_ids in hunter_company",
            """
            UPDATE enrichment.hunter_company
            SET outreach_id = NULL
            WHERE outreach_id IS NOT NULL
            AND outreach_id NOT IN (SELECT outreach_id FROM outreach.outreach);
            """,
            fetch=False
        )

        # STEP 2: Clear orphaned outreach_ids in hunter_contact
        orphaned_contact = run_query(conn,
            "2. Clear orphaned outreach_ids in hunter_contact",
            """
            UPDATE enrichment.hunter_contact
            SET outreach_id = NULL
            WHERE outreach_id IS NOT NULL
            AND outreach_id NOT IN (SELECT outreach_id FROM outreach.outreach);
            """,
            fetch=False
        )

        # STEP 3: Re-link hunter_company to company_target by domain
        relinked_company = run_query(conn,
            "3. Re-link hunter_company to company_target by domain",
            """
            UPDATE enrichment.hunter_company hc
            SET outreach_id = ct.outreach_id
            FROM outreach.company_target ct
            JOIN cl.company_identity ci ON ct.company_unique_id::uuid = ci.company_unique_id
            WHERE LOWER(hc.domain) = LOWER(ci.company_domain)
            AND hc.outreach_id IS NULL
            AND ct.outreach_id IS NOT NULL;
            """,
            fetch=False
        )

        # STEP 4: Re-link hunter_contact based on company linkage
        relinked_contact = run_query(conn,
            "4. Re-link hunter_contact based on company linkage",
            """
            UPDATE enrichment.hunter_contact hcon
            SET outreach_id = hc.outreach_id
            FROM enrichment.hunter_company hc
            WHERE LOWER(hcon.domain) = LOWER(hc.domain)
            AND hc.outreach_id IS NOT NULL
            AND hcon.outreach_id IS NULL;
            """,
            fetch=False
        )

        # STEP 5: Verify the results
        print("\n" + "="*80)
        print("FINAL VERIFICATION")
        print("="*80)

        run_query(conn, "hunter_company final state", """
            SELECT
                COUNT(*) as total_hunter_company,
                COUNT(outreach_id) as with_valid_outreach_id,
                COUNT(*) - COUNT(outreach_id) as still_unlinked,
                ROUND(100.0 * COUNT(outreach_id) / COUNT(*), 2) as linkage_percentage
            FROM enrichment.hunter_company;
        """)

        run_query(conn, "hunter_contact final state", """
            SELECT
                COUNT(*) as total_hunter_contact,
                COUNT(outreach_id) as with_valid_outreach_id,
                COUNT(*) - COUNT(outreach_id) as still_unlinked,
                ROUND(100.0 * COUNT(outreach_id) / COUNT(*), 2) as linkage_percentage
            FROM enrichment.hunter_contact;
        """)

        # SUMMARY
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"  Orphaned hunter_company records cleared: {orphaned_company}")
        print(f"  Orphaned hunter_contact records cleared: {orphaned_contact}")
        print(f"  hunter_company records re-linked: {relinked_company}")
        print(f"  hunter_contact records re-linked: {relinked_contact}")

        print(f"\n{'#'*80}")
        print(f"# HUNTER DATA RE-LINKING COMPLETE")
        print(f"# Completed: {datetime.now().isoformat()}")
        print(f"{'#'*80}\n")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
