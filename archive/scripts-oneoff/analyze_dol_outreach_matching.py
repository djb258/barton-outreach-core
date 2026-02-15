"""
DOL Hunter - Outreach Matching Analysis

Analyzes the matching opportunity between DOL Hunter results (dol.ein_urls)
and Outreach database (outreach.outreach + outreach.company_target).

Purpose:
- Understand table schemas
- Identify matching columns
- Quantify matching opportunity
- Provide match statistics

Author: Database Specialist Agent
Date: 2026-02-03
"""

import sys
import os
from pathlib import Path
import psycopg2
import psycopg2.extras
from tabulate import tabulate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get database connection using DATABASE_URL"""
    connection_string = os.getenv("DATABASE_URL")
    if not connection_string:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(connection_string)

def analyze_schema():
    """Query 1-3: Analyze table schemas"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("=" * 80)
    print("SCHEMA ANALYSIS")
    print("=" * 80)

    try:
        # Query 1: dol.ein_urls columns
        print("\n1. Columns in dol.ein_urls:")
        print("-" * 80)
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'dol' AND table_name = 'ein_urls'
            ORDER BY ordinal_position;
        """)
        ein_urls_cols = cursor.fetchall()
        print(tabulate(ein_urls_cols, headers="keys", tablefmt="grid"))

        # Query 2: outreach.outreach columns
        print("\n2. Columns in outreach.outreach:")
        print("-" * 80)
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'outreach' AND table_name = 'outreach'
            ORDER BY ordinal_position;
        """)
        outreach_cols = cursor.fetchall()
        print(tabulate(outreach_cols, headers="keys", tablefmt="grid"))

        # Query 3: outreach.company_target columns
        print("\n3. Columns in outreach.company_target:")
        print("-" * 80)
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'outreach' AND table_name = 'company_target'
            ORDER BY ordinal_position;
        """)
        company_target_cols = cursor.fetchall()
        print(tabulate(company_target_cols, headers="keys", tablefmt="grid"))

    finally:
        cursor.close()
        conn.close()


def analyze_sample_data():
    """Query 4: Show sample data from both datasets"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("\n" + "=" * 80)
    print("SAMPLE DATA ANALYSIS")
    print("=" * 80)

    try:
        # Query 4a: Sample from ein_urls (DOL Hunter results)
        print("\n4a. Sample from dol.ein_urls (DOL Hunter results):")
        print("-" * 80)
        cursor.execute("""
            SELECT ein, company_name, city, state, domain
            FROM dol.ein_urls
            WHERE discovery_method = 'hunter_dol_enrichment'
            LIMIT 5;
        """)
        hunter_sample = cursor.fetchall()
        if hunter_sample:
            print(tabulate(hunter_sample, headers="keys", tablefmt="grid"))
        else:
            print("No Hunter enrichment results found")

        # Query 4b: Sample from outreach with domain
        print("\n4b. Sample from outreach.outreach with domains:")
        print("-" * 80)
        cursor.execute("""
            SELECT o.outreach_id, o.domain
            FROM outreach.outreach o
            WHERE o.domain IS NOT NULL
            LIMIT 5;
        """)
        outreach_sample = cursor.fetchall()
        if outreach_sample:
            print(tabulate(outreach_sample, headers="keys", tablefmt="grid"))
        else:
            print("No outreach records with domains found")

    finally:
        cursor.close()
        conn.close()


def analyze_coverage():
    """Query 5: Analyze domain coverage in outreach"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("\n" + "=" * 80)
    print("OUTREACH DOMAIN COVERAGE")
    print("=" * 80)

    try:
        # Query 5: Count outreach records with domains
        print("\n5. Outreach records with domain data:")
        print("-" * 80)
        cursor.execute("""
            SELECT
                COUNT(*) as total_outreach,
                COUNT(o.domain) as with_domain,
                ROUND(100.0 * COUNT(o.domain) / COUNT(*), 1) as domain_pct
            FROM outreach.outreach o;
        """)
        coverage = cursor.fetchone()
        print(tabulate([coverage], headers="keys", tablefmt="grid"))

    finally:
        cursor.close()
        conn.close()


def analyze_matching_potential():
    """Additional: Analyze potential matches between datasets"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("\n" + "=" * 80)
    print("MATCHING POTENTIAL ANALYSIS")
    print("=" * 80)

    try:
        # Count Hunter results
        print("\n6. DOL Hunter enrichment results count:")
        print("-" * 80)
        cursor.execute("""
            SELECT
                COUNT(*) as total_hunter_results,
                COUNT(DISTINCT domain) as unique_domains,
                COUNT(DISTINCT ein) as unique_eins
            FROM dol.ein_urls
            WHERE discovery_method = 'hunter_dol_enrichment'
              AND domain IS NOT NULL;
        """)
        hunter_stats = cursor.fetchone()
        print(tabulate([hunter_stats], headers="keys", tablefmt="grid"))

        # Check for direct domain matches
        print("\n7. Direct domain matches between Hunter results and Outreach:")
        print("-" * 80)
        cursor.execute("""
            SELECT COUNT(*) as direct_domain_matches
            FROM dol.ein_urls eu
            INNER JOIN outreach.outreach o
                ON LOWER(eu.domain) = LOWER(o.domain)
            WHERE eu.discovery_method = 'hunter_dol_enrichment'
              AND eu.domain IS NOT NULL
              AND o.domain IS NOT NULL;
        """)
        match_stats = cursor.fetchone()
        print(tabulate([match_stats], headers="keys", tablefmt="grid"))

        # Sample matches
        print("\n8. Sample domain matches (first 10):")
        print("-" * 80)
        cursor.execute("""
            SELECT
                eu.ein,
                eu.company_name as hunter_name,
                eu.domain,
                o.outreach_id,
                o.sovereign_id
            FROM dol.ein_urls eu
            INNER JOIN outreach.outreach o
                ON LOWER(eu.domain) = LOWER(o.domain)
            WHERE eu.discovery_method = 'hunter_dol_enrichment'
              AND eu.domain IS NOT NULL
              AND o.domain IS NOT NULL
            LIMIT 10;
        """)
        sample_matches = cursor.fetchall()
        if sample_matches:
            print(tabulate(sample_matches, headers="keys", tablefmt="grid"))
        else:
            print("No direct domain matches found")

    finally:
        cursor.close()
        conn.close()


def main():
    """Run all analysis queries"""
    print("\n")
    print("*" * 80)
    print("DOL HUNTER - OUTREACH MATCHING ANALYSIS")
    print("*" * 80)

    try:
        # Run all analyses
        analyze_schema()
        analyze_sample_data()
        analyze_coverage()
        analyze_matching_potential()

        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        print("\nKey Findings:")
        print("- Schema structures documented")
        print("- Sample data reviewed")
        print("- Domain coverage quantified")
        print("- Matching potential assessed")
        print("\n")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
