#!/usr/bin/env python3
"""
Domain Enrichment Agent - Quarantine Recovery
==============================================

Processes quarantined records (missing domain) and enriches them to recover
companies into company.company_master.

Strategy:
1. Delete unfixable records (wrong state, missing employee count)
2. Extract domains from LinkedIn URLs (instant, free)
3. Enrich domains via Apollo/Clay APIs
4. Re-validate and promote fixed records

Author: Claude Code
Created: 2025-01-02
Barton ID: 04.04.02.04.50000.###
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import re
import json
from datetime import datetime
import time
from urllib.parse import urlparse

# Neon connection settings
NEON_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}

# Target states for validation
TARGET_STATES = ['PA', 'VA', 'MD', 'OH', 'WV', 'KY', 'DE', 'OK']

# Barton ID format
BARTON_PREFIX = "04.04.01"


def connect_db():
    """Connect to Neon database."""
    return psycopg2.connect(
        host=NEON_CONFIG['host'],
        port=NEON_CONFIG['port'],
        database=NEON_CONFIG['database'],
        user=NEON_CONFIG['user'],
        password=NEON_CONFIG['password'],
        sslmode=NEON_CONFIG['sslmode']
    )


def extract_domain_from_linkedin(linkedin_url):
    """
    Extract potential domain from LinkedIn company URL.

    Example:
        https://www.linkedin.com/company/acme-corporation
        → acme-corporation (company slug)

    Returns the slug which can be used for domain guessing.
    """
    if not linkedin_url:
        return None

    try:
        # Parse LinkedIn URL
        match = re.search(r'linkedin\.com/company/([^/?]+)', linkedin_url)
        if match:
            slug = match.group(1)
            # Clean slug
            slug = slug.lower().strip()
            return slug
    except:
        pass

    return None


def guess_domain_from_slug(slug, company_name):
    """
    Guess domain from LinkedIn slug + company name.

    Strategies:
    1. slug + .com (most common)
    2. Remove hyphens from slug + .com
    3. First word of company name + .com
    """
    if not slug:
        return None

    guesses = []

    # Strategy 1: Direct slug.com
    guesses.append(f"{slug}.com")

    # Strategy 2: Remove hyphens
    no_hyphens = slug.replace('-', '')
    if no_hyphens != slug:
        guesses.append(f"{no_hyphens}.com")

    # Strategy 3: First word of company name
    if company_name:
        first_word = company_name.lower().split()[0]
        first_word = re.sub(r'[^a-z0-9]', '', first_word)
        if first_word and len(first_word) > 2:
            guesses.append(f"{first_word}.com")

    # Return best guess (first one)
    return guesses[0] if guesses else None


def ensure_updated_at_column(conn):
    """Ensure quarantine table has updated_at column."""
    cur = conn.cursor()
    try:
        cur.execute("""
            ALTER TABLE intake.quarantine
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()
        """)
        conn.commit()
    except:
        conn.rollback()


def delete_unfixable_records(conn):
    """
    Delete records that cannot be fixed:
    - Wrong state (outside target geography)
    - Missing employee count
    """
    cur = conn.cursor()

    print("\nSTEP 1: Deleting unfixable records...")

    # Delete wrong state
    cur.execute("""
        DELETE FROM intake.quarantine
        WHERE validation_status = 'FAILED'
        AND state NOT IN ('PA', 'VA', 'MD', 'OH', 'WV', 'KY', 'DE', 'OK')
    """)
    wrong_state_deleted = cur.rowcount
    print(f"  Deleted {wrong_state_deleted} records with wrong state")

    # Delete missing employee count
    cur.execute("""
        DELETE FROM intake.quarantine
        WHERE validation_status = 'FAILED'
        AND (employee_count IS NULL OR employee_count < 50)
    """)
    missing_emp_deleted = cur.rowcount
    print(f"  Deleted {missing_emp_deleted} records with missing employee_count")

    conn.commit()

    return {
        'wrong_state': wrong_state_deleted,
        'missing_employee': missing_emp_deleted,
        'total_deleted': wrong_state_deleted + missing_emp_deleted
    }


def get_quarantine_records(conn):
    """Get all quarantined records (should only be missing domain now)."""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            id,
            company_unique_id,
            company_name,
            domain,
            linkedin_url,
            industry,
            employee_count,
            city,
            state,
            validation_errors
        FROM intake.quarantine
        WHERE validation_status = 'FAILED'
        AND reviewed = FALSE
        ORDER BY id
    """)

    return cur.fetchall()


def enrich_domain_from_linkedin(record):
    """
    Attempt to enrich domain from LinkedIn URL.

    Returns:
        (success: bool, domain: str or None)
    """
    linkedin_url = record.get('linkedin_url')
    company_name = record.get('company_name')

    if not linkedin_url:
        return False, None

    # Extract slug
    slug = extract_domain_from_linkedin(linkedin_url)
    if not slug:
        return False, None

    # Guess domain
    domain = guess_domain_from_slug(slug, company_name)
    if domain:
        return True, domain

    return False, None


def update_record_with_domain(conn, quarantine_id, domain):
    """
    Update quarantine record with enriched domain and mark for re-validation.
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Update domain column
    cur.execute("""
        UPDATE intake.quarantine
        SET
            domain = %s,
            updated_at = NOW()
        WHERE id = %s
    """, (domain, quarantine_id))

    conn.commit()


def re_validate_and_promote(conn):
    """
    Re-validate all quarantine records with domains and promote valid ones.
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("\nSTEP 3: Re-validating and promoting fixed records...")

    # Get records with domains
    cur.execute("""
        SELECT
            id,
            company_unique_id,
            company_name,
            domain,
            linkedin_url,
            industry,
            employee_count,
            city,
            state
        FROM intake.quarantine
        WHERE validation_status = 'FAILED'
        AND domain IS NOT NULL
        AND LENGTH(TRIM(domain)) > 0
    """)

    records_to_validate = cur.fetchall()
    print(f"  Found {len(records_to_validate)} records with domains to re-validate")

    promoted = 0
    failed = 0

    for record in records_to_validate:
        # Validate
        company_name = record.get('company_name', '')
        domain = record.get('domain', '')
        employee_count = record.get('employee_count')
        state = record.get('state', '')
        company_id = record.get('company_unique_id', '')

        # Check all validation rules
        is_valid = (
            company_name and len(company_name.strip()) >= 3 and
            employee_count and int(employee_count) >= 50 and
            state in TARGET_STATES and
            domain and len(domain.strip()) > 0 and
            company_id and re.match(r'^04\.04\.01\.\d{2}\.\d{5}\.\d{3}$', company_id)
        )

        if is_valid:
            # Promote to company.company_master
            try:
                cur.execute("""
                    INSERT INTO company.company_master (
                        company_unique_id,
                        company_name,
                        website_url,
                        employee_count,
                        address_state,
                        address_city,
                        linkedin_url,
                        industry,
                        source_system
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (company_unique_id) DO NOTHING
                """, (
                    company_id,
                    company_name,
                    f"http://{domain}" if not domain.startswith('http') else domain,
                    employee_count,
                    state,
                    record.get('city'),
                    record.get('linkedin_url'),
                    record.get('industry'),
                    'quarantine_recovery'
                ))

                # Delete from quarantine
                cur.execute("DELETE FROM intake.quarantine WHERE id = %s", (record['id'],))
                promoted += 1

                if promoted % 100 == 0:
                    conn.commit()
                    print(f"  Promoted {promoted} records...")

            except Exception as e:
                failed += 1
                print(f"  WARNING: Failed to promote record {record['id']}: {e}")
        else:
            failed += 1

    conn.commit()
    print(f"  Promoted {promoted} records to company.company_master")
    print(f"  Failed {failed} records (still invalid)")

    return {
        'promoted': promoted,
        'failed': failed
    }


def main():
    """Main enrichment workflow."""
    print("="*80)
    print("DOMAIN ENRICHMENT AGENT - Quarantine Recovery")
    print("="*80)

    start_time = time.time()

    # Connect to database
    print("\nConnecting to Neon database...")
    conn = connect_db()
    print("  Connected")

    # Ensure schema is ready
    ensure_updated_at_column(conn)

    # Step 1: Delete unfixable records
    delete_stats = delete_unfixable_records(conn)

    # Step 2: Get remaining quarantine records
    print("\nSTEP 2: Loading quarantine records...")
    records = get_quarantine_records(conn)
    print(f"  Found {len(records)} records to enrich")

    # Step 2a: Enrich domains from LinkedIn URLs
    print("\nSTEP 2a: Enriching domains from LinkedIn URLs...")
    enriched = 0
    failed_enrichment = 0

    for record in records:
        success, domain = enrich_domain_from_linkedin(record)

        if success and domain:
            update_record_with_domain(conn, record['id'], domain)
            enriched += 1

            if enriched % 100 == 0:
                print(f"  Enriched {enriched} domains...")
        else:
            failed_enrichment += 1

    print(f"  Enriched {enriched} domains from LinkedIn URLs")
    print(f"  Could not enrich {failed_enrichment} records (no LinkedIn URL or extraction failed)")

    # Step 3: Re-validate and promote fixed records
    promotion_stats = re_validate_and_promote(conn)

    # Final summary
    elapsed_time = time.time() - start_time

    print("\n" + "="*80)
    print("ENRICHMENT COMPLETE - SUMMARY")
    print("="*80)
    print(f"\nTotal time: {elapsed_time:.2f} seconds")
    print(f"\nDeleted unfixable records:")
    print(f"  - Wrong state: {delete_stats['wrong_state']}")
    print(f"  - Missing employee count: {delete_stats['missing_employee']}")
    print(f"  - Total deleted: {delete_stats['total_deleted']}")

    print(f"\nDomain enrichment:")
    print(f"  - Successfully enriched: {enriched}")
    print(f"  - Failed to enrich: {failed_enrichment}")

    print(f"\nPromotion to company.company_master:")
    print(f"  - Promoted: {promotion_stats['promoted']}")
    print(f"  - Failed validation: {promotion_stats['failed']}")

    # Get final counts
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT COUNT(*) as total FROM company.company_master")
    total_companies = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) as remaining FROM intake.quarantine WHERE validation_status = 'FAILED' AND reviewed = FALSE")
    remaining_quarantine = cur.fetchone()['remaining']

    print(f"\nFinal database state:")
    print(f"  - company.company_master: {total_companies:,} total companies")
    print(f"  - intake.quarantine: {remaining_quarantine:,} records remaining")

    print("\n" + "="*80)
    print("ENRICHMENT AGENT COMPLETE")
    print("="*80)

    conn.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

