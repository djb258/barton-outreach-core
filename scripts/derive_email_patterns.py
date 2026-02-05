#!/usr/bin/env python3
"""
Email Pattern Derivation Script
================================

Derives email patterns for companies missing email_method in outreach.company_target
by analyzing Hunter contact emails.

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

def inspect_hunter_contact_table(conn) -> Dict:
    """Inspect the hunter_contact table structure."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Check if enrichment schema and hunter_contact table exist
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'enrichment'
                AND table_name = 'hunter_contact'
            ) as table_exists
        """)
        result = cur.fetchone()

        if not result['table_exists']:
            print("Warning: enrichment.hunter_contact table does not exist")
            # Try to find similar tables
            cur.execute("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_name ILIKE '%hunter%' OR table_name ILIKE '%contact%'
                ORDER BY table_schema, table_name
            """)
            tables = cur.fetchall()
            print(f"\nAvailable tables with 'hunter' or 'contact' in name:")
            for table in tables:
                print(f"  - {table['table_schema']}.{table['table_name']}")
            return {'exists': False, 'columns': [], 'row_count': 0}

        # Get column information
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'enrichment' AND table_name = 'hunter_contact'
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()

        # Get row count
        cur.execute("SELECT COUNT(*) as count FROM enrichment.hunter_contact")
        row_count = cur.fetchone()['count']

        return {
            'exists': True,
            'columns': columns,
            'row_count': row_count
        }

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

    # Try to match patterns
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
        # Join company_target to company_domains to get domain
        # company_target.company_unique_id is TEXT, company_domains.company_unique_id is UUID
        # We need to cast to make the join work
        # Note: We don't filter for first_name/last_name here because we'll check
        # during pattern derivation - many contacts have emails but no names
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
            AND cd.domain IN (
                SELECT DISTINCT domain
                FROM enrichment.hunter_contact
                WHERE email IS NOT NULL
            )
            ORDER BY ct.outreach_id
        """)
        return cur.fetchall()

def get_hunter_contacts_for_domain(conn, domain: str) -> List[Dict]:
    """Get Hunter contacts for a specific domain with verified emails."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # First check what columns are available
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'enrichment' AND table_name = 'hunter_contact'
        """)
        available_columns = [row['column_name'] for row in cur.fetchall()]

        # Build query based on available columns
        select_cols = []
        if 'email' in available_columns:
            select_cols.append('email')
        if 'first_name' in available_columns:
            select_cols.append('first_name')
        if 'last_name' in available_columns:
            select_cols.append('last_name')
        if 'full_name' in available_columns:
            select_cols.append('full_name')
        if 'confidence' in available_columns:
            select_cols.append('confidence')
        if 'verification_status' in available_columns:
            select_cols.append('verification_status')
        if 'domain' in available_columns:
            select_cols.append('domain')

        if not select_cols:
            return []

        query = f"""
            SELECT {', '.join(select_cols)}
            FROM enrichment.hunter_contact
            WHERE domain = %s
        """

        # Add verification filter if column exists
        if 'verification_status' in available_columns:
            query += " AND verification_status = 'valid'"

        query += " LIMIT 100"

        cur.execute(query, (domain,))
        return cur.fetchall()

def analyze_and_derive_patterns(conn, dry_run: bool = True) -> Dict:
    """
    Main function to analyze Hunter contacts and derive email patterns.

    Returns statistics about the derivation process.
    """
    print("=" * 80)
    print("EMAIL PATTERN DERIVATION")
    print("=" * 80)
    print()

    # First inspect hunter_contact table
    print("Step 1: Inspecting enrichment.hunter_contact table...")
    hunter_info = inspect_hunter_contact_table(conn)

    if not hunter_info['exists']:
        print("\nERROR: Cannot proceed without enrichment.hunter_contact table")
        return {
            'companies_missing_patterns': 0,
            'hunter_contacts_available': 0,
            'patterns_derived': 0,
            'pattern_distribution': {},
            'updates_applied': 0
        }

    print(f"  - Table exists: Yes")
    print(f"  - Row count: {hunter_info['row_count']:,}")
    print(f"  - Columns ({len(hunter_info['columns'])}):")
    for col in hunter_info['columns']:
        print(f"    - {col['column_name']} ({col['data_type']})")
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
            'hunter_contacts_available': 0,
            'patterns_derived': 0,
            'pattern_distribution': {},
            'updates_applied': 0
        }

    # Analyze patterns
    print("Step 3: Analyzing Hunter contacts to derive patterns...")
    pattern_counter = Counter()
    derivations = []
    hunter_contact_count = 0

    for i, company in enumerate(companies, 1):
        if i % 100 == 0:
            print(f"  - Processed {i:,} / {len(companies):,} companies...")

        domain = company['domain']
        hunter_contacts = get_hunter_contacts_for_domain(conn, domain)
        hunter_contact_count += len(hunter_contacts)

        # Try to derive pattern from any valid contact
        derived_pattern = None
        for contact in hunter_contacts:
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
                derived_pattern = pattern
                break

        if derived_pattern:
            pattern_counter[derived_pattern] += 1
            derivations.append({
                'outreach_id': company['outreach_id'],
                'domain': domain,
                'pattern': derived_pattern
            })

    print(f"  - Total Hunter contacts analyzed: {hunter_contact_count:,}")
    print(f"  - Patterns successfully derived: {len(derivations):,}")
    print()

    # Show pattern distribution
    print("Step 4: Pattern Distribution")
    print("-" * 80)
    for pattern, count in pattern_counter.most_common():
        percentage = (count / len(derivations) * 100) if derivations else 0
        print(f"  {pattern:20s} : {count:6,} ({percentage:5.1f}%)")
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
                print()
        else:
            print("Step 5: Applying updates to outreach.company_target...")
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
    print(f"Hunter contacts analyzed: {hunter_contact_count:,}")
    print(f"Patterns derived: {len(derivations):,}")
    print(f"Updates applied: {updates_applied:,}")
    print(f"Success rate: {(len(derivations) / len(companies) * 100) if companies else 0:.1f}%")
    print()

    return {
        'companies_missing_patterns': len(companies),
        'hunter_contacts_available': hunter_contact_count,
        'patterns_derived': len(derivations),
        'pattern_distribution': dict(pattern_counter),
        'updates_applied': updates_applied
    }

def main():
    parser = argparse.ArgumentParser(
        description='Derive email patterns from Hunter contacts',
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
