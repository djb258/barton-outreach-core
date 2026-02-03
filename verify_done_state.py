#!/usr/bin/env python3
"""
ERD-Based DONE Verification from Neon PostgreSQL
Executes read-only queries to determine completion criteria for each Outreach sub-hub.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_neon_connection():
    """Establish connection to Neon PostgreSQL."""
    return psycopg2.connect(
        host=os.getenv('NEON_HOST'),
        database=os.getenv('NEON_DATABASE'),
        user=os.getenv('NEON_USER'),
        password=os.getenv('NEON_PASSWORD'),
        sslmode='require'
    )

def execute_query(cursor, query, description):
    """Execute query and print results."""
    print(f"\n{'='*80}")
    print(f"QUERY: {description}")
    print(f"{'='*80}")
    print(f"SQL: {query.strip()}\n")

    cursor.execute(query)
    results = cursor.fetchall()

    if not results:
        print("No results returned.")
        return

    # Print column headers
    if results:
        headers = results[0].keys()
        header_line = " | ".join(str(h) for h in headers)
        print(header_line)
        print("-" * len(header_line))

        # Print rows
        for row in results:
            row_line = " | ".join(str(v) for v in row.values())
            print(row_line)

    print(f"\nTotal rows returned: {len(results)}")

def main():
    """Execute all verification queries."""

    print("\n" + "="*80)
    print("ERD-BASED DONE VERIFICATION - NEON POSTGRESQL")
    print("="*80)

    conn = get_neon_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # ========================================================================
        # 1. COMPANY TARGET (outreach.company_target)
        # ========================================================================
        print("\n" + "#"*80)
        print("# 1. COMPANY TARGET (outreach.company_target)")
        print("#"*80)

        execute_query(
            cursor,
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'outreach' AND table_name = 'company_target'
            ORDER BY ordinal_position;
            """,
            "Company Target Schema"
        )

        execute_query(
            cursor,
            """
            SELECT execution_status, COUNT(*)
            FROM outreach.company_target
            GROUP BY execution_status;
            """,
            "Execution Status Distribution"
        )

        execute_query(
            cursor,
            """
            SELECT
              COUNT(*) as total,
              COUNT(email_method) as has_email_method,
              COUNT(confidence_score) as has_confidence,
              COUNT(imo_completed_at) as has_imo_completed
            FROM outreach.company_target;
            """,
            "Field Coverage for DONE Records"
        )

        execute_query(
            cursor,
            """
            SELECT COUNT(*) as error_count FROM outreach.company_target_errors;
            """,
            "Error Table Count"
        )

        # ========================================================================
        # 2. PEOPLE INTELLIGENCE
        # ========================================================================
        print("\n" + "#"*80)
        print("# 2. PEOPLE INTELLIGENCE (people.company_slot, outreach.people)")
        print("#"*80)

        execute_query(
            cursor,
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'people' AND table_name = 'company_slot'
            ORDER BY ordinal_position;
            """,
            "people.company_slot Schema"
        )

        execute_query(
            cursor,
            """
            SELECT is_filled, COUNT(*)
            FROM people.company_slot
            GROUP BY is_filled;
            """,
            "Slot Fill Status Distribution"
        )

        execute_query(
            cursor,
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'outreach' AND table_name = 'people'
            ORDER BY ordinal_position;
            """,
            "outreach.people Schema"
        )

        execute_query(
            cursor,
            """
            SELECT COUNT(*) as total_people FROM outreach.people;
            """,
            "outreach.people Record Count"
        )

        # ========================================================================
        # 3. DOL FILINGS
        # ========================================================================
        print("\n" + "#"*80)
        print("# 3. DOL FILINGS (outreach.dol, dol.form_5500)")
        print("#"*80)

        execute_query(
            cursor,
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'outreach' AND table_name = 'dol'
            ORDER BY ordinal_position;
            """,
            "outreach.dol Schema"
        )

        execute_query(
            cursor,
            """
            SELECT
              COUNT(*) as total,
              COUNT(ein) as has_ein,
              COUNT(CASE WHEN filing_present THEN 1 END) as has_filing
            FROM outreach.dol;
            """,
            "DOL Coverage Analysis"
        )

        execute_query(
            cursor,
            """
            SELECT COUNT(*) as total_filings FROM dol.form_5500;
            """,
            "dol.form_5500 Record Count"
        )

        # ========================================================================
        # 4. BLOG CONTENT
        # ========================================================================
        print("\n" + "#"*80)
        print("# 4. BLOG CONTENT (outreach.blog)")
        print("#"*80)

        execute_query(
            cursor,
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'outreach' AND table_name = 'blog'
            ORDER BY ordinal_position;
            """,
            "outreach.blog Schema"
        )

        execute_query(
            cursor,
            """
            SELECT COUNT(*) as total_blog_records FROM outreach.blog;
            """,
            "Blog Record Count"
        )

        # ========================================================================
        # 5. BIT SCORES
        # ========================================================================
        print("\n" + "#"*80)
        print("# 5. BIT SCORES (outreach.bit_scores)")
        print("#"*80)

        execute_query(
            cursor,
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'outreach' AND table_name = 'bit_scores'
            ORDER BY ordinal_position;
            """,
            "outreach.bit_scores Schema"
        )

        execute_query(
            cursor,
            """
            SELECT COUNT(*) as total_bit_scores FROM outreach.bit_scores;
            """,
            "BIT Score Record Count"
        )

        # ========================================================================
        # 6. OUTREACH SPINE
        # ========================================================================
        print("\n" + "#"*80)
        print("# 6. OUTREACH SPINE (outreach.outreach)")
        print("#"*80)

        execute_query(
            cursor,
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'outreach' AND table_name = 'outreach'
            ORDER BY ordinal_position;
            """,
            "outreach.outreach Schema"
        )

        execute_query(
            cursor,
            """
            SELECT COUNT(*) as total_outreach_records FROM outreach.outreach;
            """,
            "Outreach Spine Record Count"
        )

        # ========================================================================
        # 7. CL ALIGNMENT CHECK
        # ========================================================================
        print("\n" + "#"*80)
        print("# 7. CL ALIGNMENT CHECK")
        print("#"*80)

        execute_query(
            cursor,
            """
            SELECT
              (SELECT COUNT(*) FROM outreach.outreach) as outreach_spine,
              (SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL) as cl_with_outreach_id;
            """,
            "CL-Outreach Alignment Verification"
        )

        print("\n" + "="*80)
        print("VERIFICATION COMPLETE")
        print("="*80)

    except Exception as e:
        print(f"\nERROR: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
