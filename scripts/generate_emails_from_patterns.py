#!/usr/bin/env python3
"""
Generate Emails from Company Patterns
=====================================
Uses email patterns discovered in company_target to generate emails
for people in people_master who don't have email addresses.

Path: people_master -> company_slot -> company_target (pattern) + outreach (domain)

Usage:
    doppler run -- python scripts/generate_emails_from_patterns.py [--dry-run]
"""

import os
import sys
import re
import psycopg2
from datetime import datetime, timezone

DRY_RUN = "--dry-run" in sys.argv


def connect_db():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )


def clean_name(name: str) -> str:
    """Clean name for email generation - remove special chars, lowercase."""
    if not name:
        return ""
    # Remove common suffixes and special characters
    cleaned = name.lower()
    cleaned = re.sub(r'\s+(jr\.?|sr\.?|iii?|iv|phd|md|cpa|esq)\.?$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'[^a-z]', '', cleaned)  # Keep only letters
    return cleaned


def generate_email(first_name: str, last_name: str, domain: str, method_type: str) -> str:
    """Generate email based on pattern type."""
    first = clean_name(first_name)
    last = clean_name(last_name)

    if not first or not last or not domain:
        return None

    # Handle different pattern types
    if method_type == 'first.last':
        return f"{first}.{last}@{domain}"
    elif method_type == 'flast':
        return f"{first[0]}{last}@{domain}"
    elif method_type == 'firstl':
        return f"{first}{last[0]}@{domain}"
    elif method_type == 'first_last':
        return f"{first}_{last}@{domain}"
    elif method_type == 'first':
        return f"{first}@{domain}"
    elif method_type == 'last':
        return f"{last}@{domain}"
    else:
        # Default to first.last
        return f"{first}.{last}@{domain}"


def run_email_generation():
    conn = connect_db()
    cur = conn.cursor()

    print("=" * 80)
    print("GENERATE EMAILS FROM COMPANY PATTERNS")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE EXECUTION'}")
    print("=" * 80)

    # Pre-stats
    print("\n[1] PRE-GENERATION STATUS")
    print("-" * 50)
    cur.execute("SELECT COUNT(*) FROM people.people_master WHERE email IS NULL")
    no_email = cur.fetchone()[0]
    print(f"  People without email: {no_email:,}")

    cur.execute("SELECT COUNT(*) FROM people.people_master WHERE email IS NOT NULL")
    has_email = cur.fetchone()[0]
    print(f"  People with email: {has_email:,}")

    # Find candidates
    print("\n[2] FINDING CANDIDATES")
    print("-" * 50)

    cur.execute("""
        SELECT
            pm.unique_id,
            pm.first_name,
            pm.last_name,
            o.domain,
            ct.method_type
        FROM people.people_master pm
        JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id
        JOIN outreach.company_target ct ON ct.outreach_id = cs.outreach_id
        JOIN outreach.outreach o ON o.outreach_id = cs.outreach_id
        WHERE pm.email IS NULL
        AND ct.method_type IS NOT NULL
        AND o.domain IS NOT NULL
        AND pm.first_name IS NOT NULL
        AND pm.last_name IS NOT NULL
    """)
    candidates = cur.fetchall()
    print(f"  Candidates found: {len(candidates):,}")

    # Generate emails
    print("\n[3] GENERATING EMAILS")
    print("-" * 50)

    generated = []
    skipped = 0

    for row in candidates:
        unique_id, first_name, last_name, domain, method_type = row
        email = generate_email(first_name, last_name, domain, method_type)

        if email:
            generated.append((email, unique_id))
        else:
            skipped += 1

    print(f"  Emails generated: {len(generated):,}")
    print(f"  Skipped (invalid data): {skipped:,}")

    # Show samples
    print("\n  Sample generated emails:")
    for email, uid in generated[:10]:
        print(f"    {email}")

    if DRY_RUN:
        print(f"\n  [DRY RUN] Would update {len(generated):,} records")
    else:
        # Update in batches with commit after each batch
        print("\n[4] UPDATING DATABASE")
        print("-" * 50)

        batch_size = 500
        updated = 0

        for i in range(0, len(generated), batch_size):
            batch = generated[i:i + batch_size]
            for email, unique_id in batch:
                cur.execute("""
                    UPDATE people.people_master
                    SET email = %s,
                        email_verification_source = 'pattern_generated',
                        updated_at = NOW()
                    WHERE unique_id = %s
                    AND email IS NULL
                """, (email, unique_id))
                updated += cur.rowcount

            # Commit after each batch to avoid connection timeout
            conn.commit()

            if (i + batch_size) % 2500 == 0 or i + batch_size >= len(generated):
                print(f"    Progress: {min(i + batch_size, len(generated)):,} / {len(generated):,} (committed)")

        print(f"\n  Updated: {updated:,} records")

        # Post-stats
        print("\n[5] POST-GENERATION STATUS")
        print("-" * 50)
        cur.execute("SELECT COUNT(*) FROM people.people_master WHERE email IS NULL")
        new_no_email = cur.fetchone()[0]
        print(f"  People without email: {new_no_email:,}")

        cur.execute("SELECT COUNT(*) FROM people.people_master WHERE email IS NOT NULL")
        new_has_email = cur.fetchone()[0]
        print(f"  People with email: {new_has_email:,}")

        cur.execute("""
            SELECT COUNT(*) FROM people.people_master
            WHERE email_verification_source = 'pattern_generated'
        """)
        pattern_gen = cur.fetchone()[0]
        print(f"  Pattern-generated emails: {pattern_gen:,}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Emails generated: {len(generated):,}")

    if DRY_RUN:
        print("\n  [DRY RUN] No changes made.")
    else:
        print("\n  Changes committed!")

    conn.close()


if __name__ == "__main__":
    run_email_generation()
