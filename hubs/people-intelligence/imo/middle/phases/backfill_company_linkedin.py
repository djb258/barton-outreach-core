#!/usr/bin/env python3
"""
Backfill Company LinkedIn into CL
==================================
Updates cl.company_identity.linkedin_company_url from
intake.company_raw_intake for companies that are missing it.

Match: intake.company_raw_intake.website domain → outreach.outreach.domain
Small dataset (563 records in intake), quick operation.

Usage:
    doppler run -- python backfill_company_linkedin.py [--dry-run]

Created: 2026-02-09
"""

import os
import sys
from datetime import datetime

# Windows encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def get_connection():
    """Get database connection from DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[FAIL] DATABASE_URL not set. Use: doppler run -- python backfill_company_linkedin.py")
        sys.exit(1)

    import psycopg2
    return psycopg2.connect(database_url)


def normalize_domain(url):
    """Extract bare domain from a URL for matching."""
    if not url:
        return None
    url = url.lower().strip()
    url = url.replace('http://', '').replace('https://', '')
    url = url.replace('www.', '')
    url = url.rstrip('/')
    # Take just the domain part (before any path)
    if '/' in url:
        url = url.split('/')[0]
    return url


def find_matches(conn):
    """Find intake companies with LinkedIn URLs that match outreach companies missing LinkedIn.

    Returns list of (company_unique_id, intake_linkedin_url, domain).
    """
    cursor = conn.cursor()

    # Get intake companies with LinkedIn
    cursor.execute("""
        SELECT website, company_linkedin_url
        FROM intake.company_raw_intake
        WHERE company_linkedin_url IS NOT NULL AND company_linkedin_url != ''
          AND website IS NOT NULL AND website != ''
    """)
    intake_rows = cursor.fetchall()
    print(f"  Intake records with LinkedIn: {len(intake_rows)}")

    # Build domain → linkedin map
    domain_linkedin = {}
    for website, linkedin in intake_rows:
        domain = normalize_domain(website)
        if domain and linkedin:
            domain_linkedin[domain] = linkedin

    print(f"  Unique intake domains with LinkedIn: {len(domain_linkedin)}")

    # Get outreach companies missing company LinkedIn
    cursor.execute("""
        SELECT ci.company_unique_id, oo.domain
        FROM cl.company_identity ci
        JOIN outreach.outreach oo ON oo.outreach_id = ci.outreach_id
        WHERE (ci.linkedin_company_url IS NULL OR ci.linkedin_company_url = '')
          AND ci.outreach_id IS NOT NULL
    """)
    missing_rows = cursor.fetchall()
    print(f"  CL companies missing LinkedIn: {len(missing_rows):,}")

    # Match
    matches = []
    for company_unique_id, domain in missing_rows:
        normalized = normalize_domain(domain)
        if normalized and normalized in domain_linkedin:
            matches.append((company_unique_id, domain_linkedin[normalized], domain))

    cursor.close()
    return matches


def run_backfill(conn, dry_run=False):
    """Execute the company LinkedIn backfill."""
    print("\n  Finding matches...")
    matches = find_matches(conn)
    print(f"  Matches found: {len(matches)}")

    if not matches:
        print("  No new matches. Done.")
        return 0

    # Preview
    print(f"\n  Sample matches (first 10):")
    print(f"  {'Company ID':<40} {'Domain':<30} {'LinkedIn URL'}")
    print(f"  {'-'*40} {'-'*30} {'-'*50}")
    for cid, linkedin, domain in matches[:10]:
        print(f"  {str(cid):<40} {domain:<30} {linkedin[:50]}")

    if dry_run:
        print(f"\n[DRY RUN] Would update {len(matches)} cl.company_identity records.")
        return len(matches)

    # Execute updates
    cursor = conn.cursor()
    total_updated = 0

    for company_unique_id, linkedin_url, _ in matches:
        cursor.execute("""
            UPDATE cl.company_identity
            SET linkedin_company_url = %s
            WHERE company_unique_id = %s
              AND (linkedin_company_url IS NULL OR linkedin_company_url = '')
        """, (linkedin_url, company_unique_id))
        total_updated += cursor.rowcount

    conn.commit()
    cursor.close()
    return total_updated


def main():
    dry_run = '--dry-run' in sys.argv

    print("=" * 60)
    print("BACKFILL COMPANY LINKEDIN FROM INTAKE")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Started: {datetime.now().isoformat()}")

    conn = get_connection()
    print("Connected to database.")

    # Current state
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM cl.company_identity
        WHERE linkedin_company_url IS NOT NULL AND linkedin_company_url != ''
          AND outreach_id IS NOT NULL
    """)
    current_filled = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL
    """)
    total_eligible = cursor.fetchone()[0]
    cursor.close()

    print(f"\n  Current CL company LinkedIn: {current_filled:,} / {total_eligible:,} "
          f"({current_filled/total_eligible*100:.1f}%)")

    total_updated = run_backfill(conn, dry_run)

    conn.close()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Company LinkedIn URLs {'would be ' if dry_run else ''}backfilled: {total_updated}")
    print(f"  Source: intake.company_raw_intake")
    print(f"  Target: cl.company_identity.linkedin_company_url")
    if not dry_run and total_updated > 0:
        print(f"  New total: {current_filled + total_updated:,} / {total_eligible:,} "
              f"({(current_filled + total_updated)/total_eligible*100:.1f}%)")
    print(f"Completed: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
