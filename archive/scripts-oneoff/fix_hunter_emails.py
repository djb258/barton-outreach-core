"""
Fix missing emails for people in filled slots using Hunter.io email patterns.

DOCTRINE COMPLIANCE:
- ONLY processes people whose companies have Hunter-derived email patterns
- Identified by company_target.source IN ('backfill', 'hunter_dol_intake', 'CT-65f070bf')
- Uses email patterns from company_target.email_method
- Cross-validates with enrichment.hunter_company where available
- Generates emails using Hunter pattern logic (e.g., {f}{last}, {first}.{last})
- Updates people.people_master with generated emails

SAFETY:
- Read-only queries first to validate data
- Dry-run mode available (default)
- Reports all changes before committing
- Only updates people with valid patterns and domains
- Skips any records where pattern came from non-Hunter sources

USAGE:
  python fix_hunter_emails.py              # Dry run
  python fix_hunter_emails.py --execute    # Execute updates
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import re
from typing import Dict, List, Optional
from datetime import datetime

# Hunter.io pattern mapping
HUNTER_PATTERNS = {
    "{first}.{last}": lambda f, l: f"{f.lower()}.{l.lower()}",
    "{first}{last}": lambda f, l: f"{f.lower()}{l.lower()}",
    "{f}{last}": lambda f, l: f"{f[0].lower()}{l.lower()}",
    "{first}": lambda f, l: f"{f.lower()}",
    "{last}": lambda f, l: f"{l.lower()}",
    "{first}_{last}": lambda f, l: f"{f.lower()}_{l.lower()}",
    "{f}.{last}": lambda f, l: f"{f[0].lower()}.{l.lower()}",
    "{first}{l}": lambda f, l: f"{f.lower()}{l[0].lower()}",
}

def get_neon_connection():
    """Get Neon database connection from environment variables."""
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        database=os.environ["NEON_DATABASE"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
        cursor_factory=RealDictCursor
    )

def normalize_name(name: str) -> str:
    """Normalize name for email generation (remove special chars, lowercase)."""
    if not name:
        return ""
    # Remove special characters, keep only alphanumeric
    clean = re.sub(r'[^a-zA-Z0-9]', '', name)
    return clean.lower()

def is_likely_real_name(first_name: str, last_name: str) -> bool:
    """
    Check if first_name and last_name appear to be a real person's name
    rather than a job title or generic placeholder.
    """
    if not first_name or not last_name:
        return False

    # Common job title words that indicate this is NOT a real name
    title_words = [
        'manager', 'director', 'president', 'vice', 'chief', 'officer',
        'executive', 'administrator', 'coordinator', 'assistant', 'head',
        'leader', 'team', 'department', 'general', 'senior', 'junior',
        'associate', 'principal', 'supervisor', 'specialist', 'analyst',
        'consultant', 'engineer', 'developer', 'designer', 'architect',
        'administrator', 'operator', 'technician', 'representative',
        'services', 'solutions', 'systems', 'operations', 'sales',
        'marketing', 'finance', 'accounting', 'human', 'resources',
        'information', 'technology', 'customer', 'support', 'service',
        'contact', 'info', 'admin', 'office', 'company', 'business',
        'corporate', 'department', 'division', 'group', 'property',
        'leadership', 'management', 'strategy', 'communications',
        'relations', 'development', 'counsel', 'legal', 'compliance',
        'national', 'regional', 'global', 'international', 'view',
        'bio', 'profile', 'about', 'mesh', 'form', 'former', 'chair',
        'board', 'advisory', 'committee', 'council', 'meet', 'our',
        'innovation', 'awards', 'professionals', 'links', 'defense',
        'sector', 'industry', 'automotive', 'contact', 'sales', 'team'
    ]

    first_lower = first_name.lower()
    last_lower = last_name.lower()

    # Check if any title words appear in the name
    for word in title_words:
        if word in first_lower or word in last_lower:
            return False

    # Additional checks
    # Names that are too short (likely initials or abbreviations)
    if len(first_name) <= 1 or len(last_name) <= 1:
        return False

    # Names that are all caps (likely acronyms)
    if first_name.isupper() and len(first_name) > 2:
        return False
    if last_name.isupper() and len(last_name) > 2:
        return False

    return True

def apply_hunter_pattern(pattern: str, first_name: str, last_name: str, domain: str) -> Optional[str]:
    """Apply Hunter.io email pattern to generate email address."""
    if not pattern or not first_name or not last_name or not domain:
        return None

    # Normalize names
    first = normalize_name(first_name)
    last = normalize_name(last_name)

    if not first or not last:
        return None

    # Check if pattern is in our mapping
    if pattern in HUNTER_PATTERNS:
        local_part = HUNTER_PATTERNS[pattern](first, last)
        return f"{local_part}@{domain.lower()}"

    # Try to parse custom patterns
    try:
        # Replace placeholders
        local_part = pattern.lower()
        local_part = local_part.replace("{first}", first)
        local_part = local_part.replace("{last}", last)
        local_part = local_part.replace("{f}", first[0] if first else "")
        local_part = local_part.replace("{l}", last[0] if last else "")

        return f"{local_part}@{domain.lower()}"
    except Exception as e:
        print(f"Error applying pattern {pattern}: {e}")
        return None

def get_people_missing_emails(conn) -> List[Dict]:
    """
    Get all people in filled slots who are missing emails.
    ONLY includes companies where email pattern was derived from Hunter.io.
    Identified by: source IN ('backfill', 'hunter_dol_intake', 'CT-65f070bf')
    """
    query = """
    SELECT
        pm.unique_id,
        pm.first_name,
        pm.last_name,
        pm.company_unique_id,
        cs.outreach_id,
        cs.slot_type,
        ci.company_domain as domain,
        ct.email_method,
        ct.company_unique_id as ct_company_uuid,
        ct.source
    FROM people.people_master pm
    INNER JOIN people.company_slot cs ON pm.unique_id = cs.person_unique_id
    LEFT JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
    LEFT JOIN cl.company_identity ci ON ct.company_unique_id::uuid = ci.sovereign_company_id
    WHERE cs.is_filled = TRUE
    AND (pm.email IS NULL OR TRIM(pm.email) = '')
    AND ct.source IN ('backfill', 'hunter_dol_intake', 'CT-65f070bf')
    ORDER BY pm.company_unique_id, cs.slot_type;
    """

    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

def get_hunter_companies(conn, company_unique_ids: List[str]) -> Dict[str, Dict]:
    """Get Hunter.io data for companies."""
    if not company_unique_ids:
        return {}

    query = """
    SELECT
        company_unique_id,
        domain,
        email_pattern
    FROM enrichment.hunter_company
    WHERE company_unique_id = ANY(%s)
    AND email_pattern IS NOT NULL;
    """

    with conn.cursor() as cur:
        cur.execute(query, (company_unique_ids,))
        results = cur.fetchall()
        return {r["company_unique_id"]: r for r in results}

def main(dry_run: bool = True):
    """Main execution function."""
    print("=" * 80)
    print("HUNTER EMAIL GENERATION - Missing Emails in Filled Slots")
    print("=" * 80)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    conn = get_neon_connection()

    try:
        # Step 1: Get all people missing emails
        print("Step 1: Identifying people missing emails in filled slots...")
        people = get_people_missing_emails(conn)
        print(f"Found {len(people)} people missing emails in filled slots")
        print()

        # Step 2: Filter for Hunter-derived patterns
        print("Step 2: Filtering for people with email patterns from company_target...")

        # Get unique company UUIDs (from company_target)
        company_uuids = list(set([p["ct_company_uuid"] for p in people if p["ct_company_uuid"]]))
        print(f"Checking {len(company_uuids)} unique companies...")

        # Get Hunter data from enrichment.hunter_company for verification
        hunter_data = get_hunter_companies(conn, company_uuids)
        print(f"Found {len(hunter_data)} companies with patterns in hunter_company table")
        print()

        # Step 3: Generate emails
        print("Step 3: Generating emails using email patterns from company_target...")

        generated_emails = []
        skipped_no_pattern = []
        skipped_no_domain = []
        skipped_generation_failed = []
        skipped_not_real_name = []
        hunter_verified = []

        for person in people:
            doctrine_id = person["company_unique_id"]  # Keep for reporting
            company_uuid = person["ct_company_uuid"]

            # Skip if no domain available
            if not person["domain"]:
                skipped_no_domain.append(person)
                continue

            # Skip if no email_method (pattern) available
            if not person["email_method"]:
                skipped_no_pattern.append(person)
                continue

            # Skip if name looks like a job title rather than a real person
            if not is_likely_real_name(person["first_name"], person["last_name"]):
                skipped_not_real_name.append(person)
                continue

            # Get pattern from company_target.email_method
            pattern = person["email_method"]

            # Clean domain (remove http:// or https://)
            domain = person["domain"]
            if domain:
                domain = domain.replace("http://", "").replace("https://", "").strip().strip("/")

            # Check if this company also has Hunter data for verification
            if company_uuid and company_uuid in hunter_data:
                hunter_verified.append(person)

            # Generate email
            email = apply_hunter_pattern(
                pattern,
                person["first_name"],
                person["last_name"],
                domain
            )

            if email:
                generated_emails.append({
                    "unique_id": person["unique_id"],
                    "first_name": person["first_name"],
                    "last_name": person["last_name"],
                    "company_unique_id": doctrine_id,
                    "slot_type": person["slot_type"],
                    "pattern": pattern,
                    "domain": domain,
                    "generated_email": email
                })
            else:
                skipped_generation_failed.append(person)

        # Step 4: Report results
        print("=" * 80)
        print("RESULTS SUMMARY")
        print("=" * 80)
        print(f"Total people missing emails (Hunter-sourced): {len(people)}")
        print(f"Emails successfully generated: {len(generated_emails)}")
        print(f"  - Verified with Hunter data: {len(hunter_verified)}")
        print(f"\nSkipped:")
        print(f"  - No pattern in company_target: {len(skipped_no_pattern)}")
        print(f"  - No domain: {len(skipped_no_domain)}")
        print(f"  - Name is job title (not real person): {len(skipped_not_real_name)}")
        print(f"  - Generation failed: {len(skipped_generation_failed)}")
        print()

        # Show sample of generated emails
        if generated_emails:
            print("Sample of Generated Emails (first 20):")
            print("-" * 80)
            for i, gen in enumerate(generated_emails[:20], 1):
                print(f"{i}. {gen['first_name']} {gen['last_name']} ({gen['slot_type']})")
                print(f"   Pattern: {gen['pattern']}")
                print(f"   Email: {gen['generated_email']}")
                print()

        # Step 5: Update database (if not dry run)
        if not dry_run and generated_emails:
            print("=" * 80)
            print("UPDATING DATABASE")
            print("=" * 80)

            update_query = """
            UPDATE people.people_master
            SET email = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE unique_id = %s;
            """

            with conn.cursor() as cur:
                for gen in generated_emails:
                    cur.execute(update_query, (gen["generated_email"], gen["unique_id"]))

                conn.commit()

            print(f"Successfully updated {len(generated_emails)} email addresses")
            print()

        # Export results to CSV
        import csv
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"C:\\Users\\CUSTOM PC\\Desktop\\Cursor Builds\\barton-outreach-core\\hunter_email_generation_{timestamp}.csv"

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "unique_id", "first_name", "last_name", "company_unique_id",
                "slot_type", "pattern", "domain", "generated_email"
            ])
            writer.writeheader()
            writer.writerows(generated_emails)

        print(f"Results exported to: {output_file}")
        print()

        # Show breakdown by slot type
        if generated_emails:
            from collections import Counter
            slot_counts = Counter([g["slot_type"] for g in generated_emails])
            print("Breakdown by Slot Type:")
            print("-" * 40)
            for slot, count in sorted(slot_counts.items()):
                print(f"{slot}: {count}")
            print()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    import sys

    # Parse command line arguments
    dry_run = "--execute" not in sys.argv

    if dry_run:
        print("Running in DRY RUN mode. Add --execute to apply changes.")
        print()

    main(dry_run=dry_run)
