#!/usr/bin/env python3
"""
Email Pattern Derivation Script v2.0
====================================

Derives email patterns for companies missing email_method in outreach.company_target
by analyzing:
1. Hunter contact emails (enrichment.hunter_contact)
2. Verified people emails (people.people_master where email_verified = true)

This version prioritizes verified people data over Hunter contacts.

Pattern Types:
- {first}.{last} → john.smith@domain.com
- {f}{last} → jsmith@domain.com
- {first} → john@domain.com
- {first}{last} → johnsmith@domain.com
- {first}{l} → johns@domain.com
- {f}.{last} → j.smith@domain.com
- {last} → smith@domain.com
- {last}{f} → smithj@domain.com
- {first}.{l} → john.s@domain.com
- {first}_{last} → john_smith@domain.com
"""

import os
import sys
import re
from typing import Optional, Dict, List, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from collections import Counter
import argparse

def get_db_connection():
    """Get database connection from DATABASE_URL environment variable."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)

def normalize_name(name: str) -> str:
    """Normalize name by removing special characters and converting to lowercase."""
    if not name:
        return ""
    return re.sub(r'[^a-z]', '', name.lower())

def derive_pattern(email: str, first_name: str, last_name: str, domain: str) -> Optional[str]:
    """
    Derive email pattern by comparing email to first_name/last_name.

    Returns pattern string like "{first}.{last}" or None if pattern cannot be determined.
    """
    if not email or not domain or '@' not in email:
        return None

    # Extract local part (before @)
    local_part = email.split('@')[0].lower()
    email_domain = email.split('@')[1].lower()

    # Verify domain matches
    if email_domain != domain.lower():
        return None

    # Normalize names
    first = normalize_name(first_name)
    last = normalize_name(last_name)

    if not first and not last:
        return None

    # Try to match patterns (ordered by likelihood)
    # Pattern: {first}.{last}
    if first and last and local_part == f"{first}.{last}":
        return "{first}.{last}"

    # Pattern: {f}{last}
    if first and last and len(first) > 0 and local_part == f"{first[0]}{last}":
        return "{f}{last}"

    # Pattern: {first}_{last}
    if first and last and local_part == f"{first}_{last}":
        return "{first}_{last}"

    # Pattern: {first}{last}
    if first and last and local_part == f"{first}{last}":
        return "{first}{last}"

    # Pattern: {first}{l}
    if first and last and len(last) > 0 and local_part == f"{first}{last[0]}":
        return "{first}{l}"

    # Pattern: {f}.{last}
    if first and last and len(first) > 0 and local_part == f"{first[0]}.{last}":
        return "{f}.{last}"

    # Pattern: {first}.{l}
    if first and last and len(first) > 0 and len(last) > 0 and local_part == f"{first}.{last[0]}":
        return "{first}.{l}"

    # Pattern: {last}{f}
    if first and last and len(first) > 0 and local_part == f"{last}{first[0]}":
        return "{last}{f}"

    # Pattern: {first}
    if first and local_part == first:
        return "{first}"

    # Pattern: {last}
    if last and local_part == last:
        return "{last}"

    return None

def get_companies_missing_patterns(conn) -> List[Dict]:
    """Get companies from outreach.company_target where email_method IS NULL."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get companies with NULL email_method that have domains
        # We'll check both Hunter and People data sources
        cur.execute("""
            SELECT DISTINCT
                ct.outreach_id,
                ct.company_unique_id,
                ct.email_method,
                cd.domain
            FROM outreach.company_target ct
            INNER JOIN cl.company_domains cd
                ON ct.company_unique_id = cd.company_unique_id::text
            WHERE ct.email_method IS NULL
            AND cd.domain IS NOT NULL
            ORDER BY ct.outreach_id
        """)
        return cur.fetchall()

def get_verified_people_for_domain(conn, domain: str) -> List[Dict]:
    """Get verified people from people.people_master for a specific domain."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                email,
                first_name,
                last_name
            FROM people.people_master
            WHERE email IS NOT NULL
            AND email_verified = true
            AND first_name IS NOT NULL
            AND last_name IS NOT NULL
            AND email LIKE %s
            LIMIT 50
        """, (f'%@{domain}',))
        return cur.fetchall()

def get_hunter_contacts_for_domain(conn, domain: str) -> List[Dict]:
    """Get Hunter contacts for a specific domain."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                email,
                first_name,
                last_name,
                full_name
            FROM enrichment.hunter_contact
            WHERE domain = %s
            AND email IS NOT NULL
            LIMIT 100
        """, (domain,))
        return cur.fetchall()

def derive_pattern_from_contacts(contacts: List[Dict], domain: str) -> Optional[str]:
    """
    Derive pattern from a list of contacts.
    Returns the most common pattern found, or None.
    """
    pattern_votes = Counter()

    for contact in contacts:
        email = contact.get('email')
        first_name = contact.get('first_name', '')
        last_name = contact.get('last_name', '')

        # If no first/last, try to extract from full_name
        if not first_name and not last_name and 'full_name' in contact:
            full_name = contact.get('full_name', '')
            parts = full_name.split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name = parts[-1]
            elif len(parts) == 1:
                first_name = parts[0]

        pattern = derive_pattern(email, first_name, last_name, domain)
        if pattern:
            pattern_votes[pattern] += 1

    if not pattern_votes:
        return None

    # Return the most common pattern
    most_common = pattern_votes.most_common(1)[0]
    return most_common[0]

def analyze_and_derive_patterns(conn, dry_run: bool = True) -> Dict:
    """
    Main function to analyze contacts and derive email patterns.

    Returns statistics about the derivation process.
    """
    print("=" * 80)
    print("EMAIL PATTERN DERIVATION v2.0")
    print("=" * 80)
    print("Data Sources:")
    print("  1. people.people_master (verified emails)")
    print("  2. enrichment.hunter_contact (fallback)")
    print()

    # Get data source stats
    print("Step 1: Checking data source availability...")
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM enrichment.hunter_contact")
        hunter_count = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM people.people_master
            WHERE email_verified = true
            AND email IS NOT NULL
            AND first_name IS NOT NULL
            AND last_name IS NOT NULL
        """)
        people_count = cur.fetchone()[0]

    print(f"  - Hunter contacts: {hunter_count:,}")
    print(f"  - Verified people (usable): {people_count:,}")
    print()

    # Get companies missing patterns
    print("Step 2: Finding companies with NULL email_method...")
    companies = get_companies_missing_patterns(conn)
    print(f"  - Companies missing patterns: {len(companies):,}")
    print()

    if not companies:
        print("No companies need pattern derivation. Exiting.")
        return {
            'companies_missing_patterns': 0,
            'patterns_derived': 0,
            'pattern_distribution': {},
            'updates_applied': 0,
            'source_breakdown': {'people': 0, 'hunter': 0}
        }

    # Analyze patterns
    print("Step 3: Deriving patterns from available data...")
    print(f"  Processing {len(companies):,} companies...")
    pattern_counter = Counter()
    derivations = []
    source_counter = Counter()
    people_contacts_analyzed = 0
    hunter_contacts_analyzed = 0

    for i, company in enumerate(companies, 1):
        if i % 100 == 0:
            print(f"  - Processed {i:,} / {len(companies):,} companies...")

        domain = company['domain']
        derived_pattern = None
        source = None

        # Try verified people first (higher quality)
        people = get_verified_people_for_domain(conn, domain)
        people_contacts_analyzed += len(people)

        if people:
            derived_pattern = derive_pattern_from_contacts(people, domain)
            if derived_pattern:
                source = 'people'

        # Fall back to Hunter if no pattern from people
        if not derived_pattern:
            hunter = get_hunter_contacts_for_domain(conn, domain)
            hunter_contacts_analyzed += len(hunter)

            if hunter:
                derived_pattern = derive_pattern_from_contacts(hunter, domain)
                if derived_pattern:
                    source = 'hunter'

        if derived_pattern:
            pattern_counter[derived_pattern] += 1
            source_counter[source] += 1
            derivations.append({
                'outreach_id': company['outreach_id'],
                'domain': domain,
                'pattern': derived_pattern,
                'source': source
            })

    print(f"  - Verified people contacts analyzed: {people_contacts_analyzed:,}")
    print(f"  - Hunter contacts analyzed: {hunter_contacts_analyzed:,}")
    print(f"  - Patterns successfully derived: {len(derivations):,}")
    print()

    # Show pattern distribution
    if derivations:
        print("Step 4: Pattern Distribution")
        print("-" * 80)
        for pattern, count in pattern_counter.most_common():
            percentage = (count / len(derivations) * 100) if derivations else 0
            print(f"  {pattern:20s} : {count:6,} ({percentage:5.1f}%)")
        print()

        print("Step 5: Source Distribution")
        print("-" * 80)
        for source, count in source_counter.most_common():
            percentage = (count / len(derivations) * 100) if derivations else 0
            print(f"  {source:20s} : {count:6,} ({percentage:5.1f}%)")
        print()

    # Apply updates
    updates_applied = 0
    if derivations:
        if dry_run:
            print("=" * 80)
            print("DRY RUN MODE - No updates will be applied")
            print("=" * 80)
            print(f"\nWould update {len(derivations):,} companies with derived patterns")
            print("\nSample updates (first 10):")
            for deriv in derivations[:10]:
                print(f"  - outreach_id: {deriv['outreach_id']}")
                print(f"    domain: {deriv['domain']}")
                print(f"    pattern: {deriv['pattern']}")
                print(f"    source: {deriv['source']}")
                print()
        else:
            print("Step 6: Applying updates to outreach.company_target...")
            with conn.cursor() as cur:
                for deriv in derivations:
                    cur.execute("""
                        UPDATE outreach.company_target
                        SET email_method = %s,
                            updated_at = NOW()
                        WHERE outreach_id = %s
                        AND email_method IS NULL
                    """, (deriv['pattern'], deriv['outreach_id']))
                    updates_applied += cur.rowcount

                conn.commit()

            print(f"  - Updates applied: {updates_applied:,}")
            print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Companies missing patterns: {len(companies):,}")
    print(f"Verified people contacts analyzed: {people_contacts_analyzed:,}")
    print(f"Hunter contacts analyzed: {hunter_contacts_analyzed:,}")
    print(f"Patterns derived: {len(derivations):,}")
    if derivations:
        print(f"  - From verified people: {source_counter.get('people', 0):,}")
        print(f"  - From Hunter: {source_counter.get('hunter', 0):,}")
    print(f"Updates applied: {updates_applied:,}")
    print(f"Success rate: {(len(derivations) / len(companies) * 100) if companies else 0:.1f}%")
    print()

    return {
        'companies_missing_patterns': len(companies),
        'patterns_derived': len(derivations),
        'pattern_distribution': dict(pattern_counter),
        'updates_applied': updates_applied,
        'source_breakdown': dict(source_counter),
        'contacts_analyzed': {
            'people': people_contacts_analyzed,
            'hunter': hunter_contacts_analyzed
        }
    }

def main():
    parser = argparse.ArgumentParser(
        description='Derive email patterns from verified people and Hunter contacts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--live',
        action='store_true',
        help='Apply updates to database (default is dry run mode)'
    )

    args = parser.parse_args()
    dry_run = not args.live

    if dry_run:
        print("\nRunning in DRY RUN mode (use --live to apply updates)")
        print()
    else:
        print("\nRunning in LIVE mode - updates will be applied to database")
        print()

    try:
        conn = get_db_connection()
        stats = analyze_and_derive_patterns(conn, dry_run=dry_run)
        conn.close()

        return 0
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
