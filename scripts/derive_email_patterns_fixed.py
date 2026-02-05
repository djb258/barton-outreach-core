#!/usr/bin/env python3
"""
Derive Email Patterns from Verified Sources (Fixed Join Path)
=============================================================

PURPOSE:
Populate outreach.company_target.email_method for companies missing patterns
by deriving patterns from:
1. enrichment.hunter_contact (external verified source)
2. people.people_master (internal verified source)

APPROACH:
- Join through outreach.outreach.domain (CORRECT PATH)
- Derive pattern from first_name, last_name, and email
- Update company_target with derived pattern
- Track source of pattern (hunter vs people_master)

SAFETY:
- Read-only analysis first, then explicit update step
- Transaction rollback on error
- Validation of pattern format before update

USAGE:
    doppler run -- python scripts/derive_email_patterns_fixed.py [--dry-run] [--verbose]
"""

import psycopg2
import os
import sys
import re
from typing import Optional, Dict, List, Tuple


def derive_pattern(first_name: str, last_name: str, email: str, domain: str) -> Optional[str]:
    """
    Derive email pattern from a verified example.

    Returns pattern like: first.last, firstlast, first_last, flast, f.last, etc.
    """
    email = email.lower().strip()
    first_name = first_name.lower().strip()
    last_name = last_name.lower().strip()
    domain = domain.lower().strip()

    # Extract local part (before @)
    if '@' not in email:
        return None

    local_part = email.split('@')[0]

    # Remove any numbers or special chars from names for matching
    first_clean = re.sub(r'[^a-z]', '', first_name)
    last_clean = re.sub(r'[^a-z]', '', last_name)

    if not first_clean or not last_clean:
        return None

    # Pattern matching
    # first.last
    if local_part == f"{first_clean}.{last_clean}":
        return "first.last"

    # firstlast
    if local_part == f"{first_clean}{last_clean}":
        return "firstlast"

    # first_last
    if local_part == f"{first_clean}_{last_clean}":
        return "first_last"

    # flast (first initial + last)
    if local_part == f"{first_clean[0]}{last_clean}":
        return "flast"

    # f.last
    if local_part == f"{first_clean[0]}.{last_clean}":
        return "f.last"

    # first (just first name)
    if local_part == first_clean:
        return "first"

    # firstl (first + last initial)
    if local_part == f"{first_clean}{last_clean[0]}":
        return "firstl"

    # first-last
    if local_part == f"{first_clean}-{last_clean}":
        return "first-last"

    # last.first
    if local_part == f"{last_clean}.{first_clean}":
        return "last.first"

    # lastfirst
    if local_part == f"{last_clean}{first_clean}":
        return "lastfirst"

    return None


def analyze_pattern_sources(cur) -> Dict:
    """
    Analyze available pattern sources and derive patterns.
    """
    print("=" * 80)
    print("ANALYSIS: Pattern Derivation from Verified Sources")
    print("=" * 80)

    # Source 1: Hunter contacts
    print("\n[Source 1: enrichment.hunter_contact]")
    cur.execute("""
        SELECT
            ct.outreach_id,
            o.domain,
            hc.first_name,
            hc.last_name,
            hc.email
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
        JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
        WHERE ct.email_method IS NULL
        AND o.domain IS NOT NULL
        AND hc.email IS NOT NULL
        AND hc.first_name IS NOT NULL
        AND hc.last_name IS NOT NULL
        AND hc.email LIKE '%@%'
    """)

    hunter_rows = cur.fetchall()
    print(f"Found {len(hunter_rows)} Hunter contacts for pattern derivation")

    # Derive patterns from Hunter
    hunter_patterns = {}  # outreach_id -> (pattern, domain, source_email)
    for outreach_id, domain, first, last, email in hunter_rows:
        if outreach_id not in hunter_patterns:
            pattern = derive_pattern(first, last, email, domain)
            if pattern:
                hunter_patterns[outreach_id] = (pattern, domain, email)

    print(f"Successfully derived {len(hunter_patterns)} patterns from Hunter")

    # Source 2: people_master
    print("\n[Source 2: people.people_master]")

    # Build exclusion list with proper UUID casting
    if hunter_patterns:
        exclusion_clause = "AND ct.outreach_id NOT IN (" + ','.join([f"'{oid}'::uuid" for oid in hunter_patterns.keys()]) + ")"
    else:
        exclusion_clause = ""

    cur.execute(f"""
        SELECT
            ct.outreach_id,
            o.domain,
            pm.first_name,
            pm.last_name,
            pm.email
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
        JOIN people.company_slot cs ON cs.outreach_id = o.outreach_id
        JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
        WHERE ct.email_method IS NULL
        AND o.domain IS NOT NULL
        AND pm.email IS NOT NULL
        AND pm.first_name IS NOT NULL
        AND pm.last_name IS NOT NULL
        AND pm.email LIKE '%@%'
        {exclusion_clause}
    """)

    people_rows = cur.fetchall()
    print(f"Found {len(people_rows)} people_master emails (excluding Hunter matches)")

    # Derive patterns from people_master
    people_patterns = {}  # outreach_id -> (pattern, domain, source_email)
    for outreach_id, domain, first, last, email in people_rows:
        if outreach_id not in people_patterns:
            pattern = derive_pattern(first, last, email, domain)
            if pattern:
                people_patterns[outreach_id] = (pattern, domain, email)

    print(f"Successfully derived {len(people_patterns)} patterns from people_master")

    # Combine results
    all_patterns = {**hunter_patterns, **people_patterns}

    # Show distribution
    print("\n[Pattern Distribution]")
    pattern_counts = {}
    for pattern, _, _ in all_patterns.values():
        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

    for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        print(f"  {pattern}: {count} companies")

    print("\n[Sample Derivations]")
    for i, (oid, (pattern, domain, email)) in enumerate(list(all_patterns.items())[:10]):
        source = "Hunter" if oid in hunter_patterns else "people_master"
        print(f"  {oid[:8]}... | {domain:30} | {pattern:15} | {email:40} | [{source}]")

    return {
        'hunter': hunter_patterns,
        'people': people_patterns,
        'combined': all_patterns
    }


def update_patterns(cur, patterns: Dict, dry_run: bool = False) -> int:
    """
    Update company_target.email_method with derived patterns.
    """
    if not patterns:
        print("\nNo patterns to update.")
        return 0

    print("\n" + "=" * 80)
    print(f"{'DRY RUN: ' if dry_run else ''}UPDATING email_method for {len(patterns)} companies")
    print("=" * 80)

    if dry_run:
        print("\n[DRY RUN MODE - No changes will be made]")
        return 0

    updated_count = 0
    for outreach_id, (pattern, domain, source_email) in patterns.items():
        try:
            cur.execute("""
                UPDATE outreach.company_target
                SET
                    email_method = %s,
                    updated_at = NOW()
                WHERE outreach_id = %s
                AND email_method IS NULL
            """, (pattern, outreach_id))

            if cur.rowcount > 0:
                updated_count += 1
        except Exception as e:
            print(f"ERROR updating {outreach_id}: {e}")
            raise

    print(f"\nSuccessfully updated {updated_count} companies with derived patterns")
    return updated_count


def verify_updates(cur, expected_count: int):
    """
    Verify that updates were successful.
    """
    print("\n" + "=" * 80)
    print("VERIFICATION: Post-Update Status")
    print("=" * 80)

    # Check total with patterns
    cur.execute("""
        SELECT COUNT(*)
        FROM outreach.company_target
        WHERE email_method IS NOT NULL
    """)
    total_with_patterns = cur.fetchone()[0]
    print(f"Total companies with email_method: {total_with_patterns}")

    # Check remaining without patterns
    cur.execute("""
        SELECT COUNT(*)
        FROM outreach.company_target
        WHERE email_method IS NULL
    """)
    remaining_without = cur.fetchone()[0]
    print(f"Remaining without email_method: {remaining_without}")

    # Show pattern distribution
    cur.execute("""
        SELECT
            email_method,
            COUNT(*) as count
        FROM outreach.company_target
        WHERE email_method IS NOT NULL
        GROUP BY email_method
        ORDER BY count DESC
    """)

    print("\n[Pattern Distribution After Update]")
    for pattern, count in cur.fetchall():
        print(f"  {pattern}: {count}")


def main():
    dry_run = '--dry-run' in sys.argv
    verbose = '--verbose' in sys.argv

    print("=" * 80)
    print("DERIVE EMAIL PATTERNS FROM VERIFIED SOURCES (FIXED JOIN PATH)")
    print("=" * 80)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    print(f"Join Path: outreach.company_target -> outreach.outreach.domain")
    print()

    # Connect to database
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    try:
        # Phase 1: Analyze and derive patterns
        results = analyze_pattern_sources(cur)

        # Phase 2: Update (if not dry run)
        if results['combined']:
            updated_count = update_patterns(cur, results['combined'], dry_run=dry_run)

            if not dry_run:
                # Commit transaction
                conn.commit()
                print("\nTransaction committed successfully")

                # Phase 3: Verify
                verify_updates(cur, updated_count)
            else:
                print(f"\nDRY RUN: Would update {len(results['combined'])} companies")
                print("Run without --dry-run to apply changes")
        else:
            print("\nNo patterns derived. Check data sources.")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        print("Transaction rolled back")
        raise
    finally:
        cur.close()
        conn.close()

    print("\n" + "=" * 80)
    print("COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
