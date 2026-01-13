#!/usr/bin/env python3
"""
People Intelligence Pipeline - Full Execution (Phases 5-8)
==========================================================
Processes CEO CSV through the complete People Intelligence pipeline.

Usage:
    doppler run -- python infra/scripts/run_people_pipeline.py <csv_path> <slot_type>

Example:
    doppler run -- python infra/scripts/run_people_pipeline.py "path/to/ceo.csv" CEO
"""

import os
import sys
import csv
import uuid
import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

# Windows encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PersonRecord:
    """Person record from CSV."""
    row_id: int
    company_name: str
    first_name: str
    last_name: str
    full_name: str
    job_title: str
    location: str
    company_domain: str
    linkedin_url: str

    # Enriched fields
    company_unique_id: Optional[str] = None
    company_slot_unique_id: Optional[str] = None
    person_unique_id: Optional[str] = None
    generated_email: Optional[str] = None
    email_confidence: Optional[str] = None
    email_pattern: Optional[str] = None
    slot_type: Optional[str] = None
    seniority_score: float = 9.99  # CEO = 9.99 (max for numeric(3,2))
    data_source: str = "clay"

    # Processing state
    company_matched: bool = False
    email_generated: bool = False
    slot_assigned: bool = False
    needs_enrichment: bool = False
    enrichment_reason: Optional[str] = None


@dataclass
class PipelineStats:
    """Pipeline execution statistics."""
    total_records: int = 0
    companies_matched: int = 0
    companies_created: int = 0
    emails_generated: int = 0
    emails_verified: int = 0
    emails_derived: int = 0
    slots_assigned: int = 0
    slots_displaced: int = 0
    enrichment_queued: int = 0
    errors: List[str] = field(default_factory=list)


# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_connection():
    """Get database connection."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    import psycopg2
    return psycopg2.connect(database_url)


# =============================================================================
# PHASE 5: EMAIL GENERATION
# =============================================================================

# Common email patterns
EMAIL_PATTERNS = [
    ("{first}.{last}", "{first}.{last}@{domain}"),
    ("{first}{last}", "{first}{last}@{domain}"),
    ("{f}{last}", "{f}{last}@{domain}"),
    ("{first}_{last}", "{first}_{last}@{domain}"),
    ("{first}", "{first}@{domain}"),
    ("{last}", "{last}@{domain}"),
    ("{f}.{last}", "{f}.{last}@{domain}"),
]


def generate_email(person: PersonRecord, pattern: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Generate email for a person.

    Returns: (email, confidence, pattern_used)
    """
    if not person.company_domain:
        return ("", "NO_DOMAIN", "")

    first = person.first_name.lower().strip() if person.first_name else ""
    last = person.last_name.lower().strip() if person.last_name else ""
    domain = person.company_domain.lower().strip()

    # Remove special characters
    first = ''.join(c for c in first if c.isalnum())
    last = ''.join(c for c in last if c.isalnum())

    if not first or not last:
        return ("", "MISSING_NAME", "")

    f = first[0] if first else ""

    # If pattern provided, use it
    if pattern:
        try:
            email = pattern.format(first=first, last=last, f=f, domain=domain)
            return (email, "VERIFIED", pattern)
        except:
            pass

    # Default to first.last pattern (most common)
    default_pattern = "{first}.{last}@{domain}"
    email = f"{first}.{last}@{domain}"

    return (email, "DERIVED", default_pattern)


def run_phase5(records: List[PersonRecord], conn, stats: PipelineStats) -> List[PersonRecord]:
    """
    Phase 5: Email Generation

    - Look up verified patterns from company_target
    - Generate emails for each person
    - Track confidence levels
    """
    print("\n" + "="*60)
    print("PHASE 5: EMAIL GENERATION")
    print("="*60)

    cursor = conn.cursor()

    # Build domain -> pattern lookup from company.company_master via cl.company_domains
    print("Loading verified patterns from company.company_master...")
    cursor.execute("""
        SELECT cd.domain, cm.email_pattern
        FROM cl.company_domains cd
        JOIN company.company_master cm ON cd.company_unique_id::text = cm.company_unique_id::text
        WHERE cm.email_pattern IS NOT NULL AND cm.email_pattern != ''
    """)
    domain_patterns = {row[0].lower(): row[1] for row in cursor.fetchall()}
    print(f"  Loaded {len(domain_patterns)} verified patterns")

    for person in records:
        if not person.company_domain:
            person.enrichment_reason = "missing_domain"
            person.needs_enrichment = True
            continue

        domain = person.company_domain.lower()
        pattern = domain_patterns.get(domain)

        email, confidence, pattern_used = generate_email(person, pattern)

        person.generated_email = email
        person.email_confidence = confidence
        person.email_pattern = pattern_used

        if email:
            person.email_generated = True
            stats.emails_generated += 1

            if confidence == "VERIFIED":
                stats.emails_verified += 1
            elif confidence == "DERIVED":
                stats.emails_derived += 1
        else:
            person.needs_enrichment = True
            person.enrichment_reason = confidence

    cursor.close()

    print(f"  Emails generated: {stats.emails_generated}")
    print(f"    - Verified: {stats.emails_verified}")
    print(f"    - Derived: {stats.emails_derived}")

    return records


# =============================================================================
# PHASE 6: SLOT ASSIGNMENT
# =============================================================================

def run_phase6(records: List[PersonRecord], conn, stats: PipelineStats, slot_type: str) -> List[PersonRecord]:
    """
    Phase 6: Slot Assignment

    - Assign persons to slots based on seniority
    - Handle conflicts (higher seniority wins)
    - Track displacements
    """
    print("\n" + "="*60)
    print("PHASE 6: SLOT ASSIGNMENT")
    print("="*60)

    cursor = conn.cursor()

    for person in records:
        if not person.company_unique_id:
            continue

        person.slot_type = slot_type

        # Check if slot exists for this company
        cursor.execute("""
            SELECT company_slot_unique_id, person_unique_id, confidence_score, is_filled
            FROM people.company_slot
            WHERE company_unique_id = %s AND slot_type = %s
        """, (person.company_unique_id, slot_type))

        existing_slot = cursor.fetchone()

        if existing_slot:
            slot_id, current_person, current_score, is_filled = existing_slot
            current_score = current_score or 0

            # Seniority competition - higher score wins
            if person.seniority_score > current_score or not is_filled:
                # Update slot - this will trigger history via trg_slot_assignment_history
                cursor.execute("""
                    UPDATE people.company_slot
                    SET person_unique_id = %s,
                        confidence_score = %s,
                        is_filled = TRUE,
                        filled_at = NOW(),
                        source_system = %s,
                        slot_status = 'filled'
                    WHERE company_slot_unique_id = %s
                """, (person.person_unique_id, person.seniority_score,
                      person.data_source, slot_id))

                person.slot_assigned = True
                stats.slots_assigned += 1

                if current_person and is_filled:
                    stats.slots_displaced += 1
            else:
                # Lost competition
                person.slot_assigned = False
        else:
            # Create new slot - use the pre-generated company_slot_unique_id
            cursor.execute("""
                INSERT INTO people.company_slot (
                    company_slot_unique_id, company_unique_id, person_unique_id,
                    slot_type, confidence_score, is_filled, filled_at,
                    source_system, slot_status, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, TRUE, NOW(), %s, 'filled', NOW()
                )
            """, (person.company_slot_unique_id, person.company_unique_id, person.person_unique_id,
                  slot_type, person.seniority_score, person.data_source))

            person.slot_assigned = True
            stats.slots_assigned += 1

    conn.commit()
    cursor.close()

    print(f"  Slots assigned: {stats.slots_assigned}")
    print(f"  Displacements: {stats.slots_displaced}")

    return records


# =============================================================================
# PHASE 7: ENRICHMENT QUEUE
# =============================================================================

def run_phase7(records: List[PersonRecord], stats: PipelineStats) -> List[PersonRecord]:
    """
    Phase 7: Enrichment Queue

    - Identify records needing additional enrichment
    - Prioritize by slot importance and data gaps
    """
    print("\n" + "="*60)
    print("PHASE 7: ENRICHMENT QUEUE")
    print("="*60)

    for person in records:
        if person.needs_enrichment:
            stats.enrichment_queued += 1
        elif not person.company_matched:
            person.needs_enrichment = True
            person.enrichment_reason = "company_not_matched"
            stats.enrichment_queued += 1
        elif not person.linkedin_url:
            person.needs_enrichment = True
            person.enrichment_reason = "missing_linkedin"
            stats.enrichment_queued += 1

    print(f"  Queued for enrichment: {stats.enrichment_queued}")

    # Group by reason
    reasons = {}
    for p in records:
        if p.needs_enrichment and p.enrichment_reason:
            reasons[p.enrichment_reason] = reasons.get(p.enrichment_reason, 0) + 1

    for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"    - {reason}: {count}")

    return records


# =============================================================================
# PHASE 8: OUTPUT WRITER
# =============================================================================

def run_phase8(records: List[PersonRecord], stats: PipelineStats, output_dir: str) -> Dict[str, str]:
    """
    Phase 8: Output Writer

    - Write results to CSV files
    - Generate summary report
    """
    print("\n" + "="*60)
    print("PHASE 8: OUTPUT WRITER")
    print("="*60)

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_files = {}

    # 1. Write people_final.csv
    people_file = os.path.join(output_dir, f"people_final_{timestamp}.csv")
    with open(people_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'person_unique_id', 'company_unique_id', 'first_name', 'last_name',
            'full_name', 'job_title', 'generated_email', 'email_confidence',
            'slot_type', 'seniority_score', 'linkedin_url', 'company_domain',
            'company_name', 'data_source'
        ])
        for p in records:
            writer.writerow([
                p.person_unique_id, p.company_unique_id, p.first_name, p.last_name,
                p.full_name, p.job_title, p.generated_email, p.email_confidence,
                p.slot_type, p.seniority_score, p.linkedin_url, p.company_domain,
                p.company_name, p.data_source
            ])
    output_files['people_final'] = people_file
    print(f"  Written: {people_file} ({len(records)} records)")

    # 2. Write slot_assignments.csv
    slots_file = os.path.join(output_dir, f"slot_assignments_{timestamp}.csv")
    assigned = [p for p in records if p.slot_assigned]
    with open(slots_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'company_unique_id', 'company_name', 'slot_type', 'person_unique_id',
            'full_name', 'seniority_score', 'generated_email'
        ])
        for p in assigned:
            writer.writerow([
                p.company_unique_id, p.company_name, p.slot_type, p.person_unique_id,
                p.full_name, p.seniority_score, p.generated_email
            ])
    output_files['slot_assignments'] = slots_file
    print(f"  Written: {slots_file} ({len(assigned)} records)")

    # 3. Write enrichment_queue.csv
    queue_file = os.path.join(output_dir, f"enrichment_queue_{timestamp}.csv")
    queued = [p for p in records if p.needs_enrichment]
    with open(queue_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'person_unique_id', 'company_name', 'company_domain', 'full_name',
            'enrichment_reason', 'linkedin_url'
        ])
        for p in queued:
            writer.writerow([
                p.person_unique_id, p.company_name, p.company_domain, p.full_name,
                p.enrichment_reason, p.linkedin_url
            ])
    output_files['enrichment_queue'] = queue_file
    print(f"  Written: {queue_file} ({len(queued)} records)")

    # 4. Write summary
    summary_file = os.path.join(output_dir, f"pipeline_summary_{timestamp}.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("PEOPLE PIPELINE SUMMARY\n")
        f.write("="*60 + "\n\n")
        f.write(f"Run Time: {datetime.now().isoformat()}\n")
        f.write(f"Total Records: {stats.total_records}\n\n")
        f.write("-"*60 + "\n")
        f.write("COMPANY MATCHING\n")
        f.write("-"*60 + "\n")
        f.write(f"  Matched: {stats.companies_matched}\n")
        f.write(f"  Created: {stats.companies_created}\n\n")
        f.write("-"*60 + "\n")
        f.write("EMAIL GENERATION (Phase 5)\n")
        f.write("-"*60 + "\n")
        f.write(f"  Generated: {stats.emails_generated}\n")
        f.write(f"    - Verified: {stats.emails_verified}\n")
        f.write(f"    - Derived: {stats.emails_derived}\n\n")
        f.write("-"*60 + "\n")
        f.write("SLOT ASSIGNMENT (Phase 6)\n")
        f.write("-"*60 + "\n")
        f.write(f"  Assigned: {stats.slots_assigned}\n")
        f.write(f"  Displaced: {stats.slots_displaced}\n\n")
        f.write("-"*60 + "\n")
        f.write("ENRICHMENT QUEUE (Phase 7)\n")
        f.write("-"*60 + "\n")
        f.write(f"  Queued: {stats.enrichment_queued}\n\n")
        f.write("="*60 + "\n")
    output_files['summary'] = summary_file
    print(f"  Written: {summary_file}")

    return output_files


# =============================================================================
# COMPANY MATCHING
# =============================================================================

def match_or_create_companies(records: List[PersonRecord], conn, stats: PipelineStats) -> List[PersonRecord]:
    """
    Match companies by domain or create new ones in company.company_master.

    The FK constraint on people.company_slot requires companies to exist in
    company.company_master (with Barton format IDs), not cl.company_domains (UUIDs).
    """
    print("\n" + "="*60)
    print("COMPANY MATCHING")
    print("="*60)

    cursor = conn.cursor()

    # Get unique domains from records
    domains = set(p.company_domain.lower() for p in records if p.company_domain)
    print(f"  Unique domains in CSV: {len(domains)}")

    # Build domain -> company mapping from company.company_master via website_url
    # Extract domain from website_url (e.g., 'https://example.com' -> 'example.com')
    print("  Loading existing companies from company.company_master...")
    cursor.execute("""
        SELECT company_unique_id, company_name, website_url
        FROM company.company_master
        WHERE website_url IS NOT NULL AND website_url != ''
    """)

    domain_to_company = {}
    for row in cursor.fetchall():
        company_id, company_name, website_url = row
        # Extract domain from website_url
        url = website_url.lower().strip()
        url = url.replace('https://', '').replace('http://', '').replace('www.', '')
        url = url.split('/')[0]  # Remove path
        if url:
            domain_to_company[url] = company_id
    print(f"  Existing companies with website_url: {len(domain_to_company)}")

    # Also check the company_name to domain mapping via keyword matching
    domain_to_name = {p.company_domain.lower(): p.company_name for p in records if p.company_domain}

    # Track companies to create
    companies_to_create = {}  # domain -> PersonRecord (for company details)

    # First pass: identify which companies exist and which need creation
    matched_domains = set()
    for person in records:
        if not person.company_domain:
            continue

        domain = person.company_domain.lower()

        if domain in domain_to_company:
            person.company_unique_id = domain_to_company[domain]
            person.company_matched = True
            matched_domains.add(domain)
        elif domain not in companies_to_create:
            # Need to create this company
            companies_to_create[domain] = person

    stats.companies_matched = len(matched_domains)
    print(f"  Domains matched to existing companies: {stats.companies_matched}")
    print(f"  Domains needing new company creation: {len(companies_to_create)}")

    # Create new companies in company.company_master
    if companies_to_create:
        print("  Creating new companies in company.company_master...")
        # Get next sequence number
        cursor.execute("""
            SELECT COUNT(*) FROM company.company_master
            WHERE company_unique_id LIKE '04.04.01.99.%'
        """)
        seq_start = cursor.fetchone()[0] + 1

        for i, (domain, person) in enumerate(companies_to_create.items()):
            seq = seq_start + i
            new_id = f"04.04.01.99.{seq:05d}.{seq % 1000:03d}"

            try:
                cursor.execute("""
                    INSERT INTO company.company_master (
                        company_unique_id, company_name, website_url,
                        employee_count, address_state, source_system,
                        promoted_from_intake_at, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    )
                    ON CONFLICT (company_unique_id) DO NOTHING
                """, (
                    new_id,
                    person.company_name or f"Company ({domain})",
                    f"https://{domain}",
                    50,  # employee_count - constraint requires >= 50
                    'DE',  # address_state - required, using DE for Delaware
                    'clay_pipeline'
                ))
                domain_to_company[domain] = new_id
                stats.companies_created += 1
            except Exception as e:
                print(f"    Error creating company for {domain}: {e}")
                conn.rollback()

        conn.commit()
        print(f"    Created: {stats.companies_created} companies")

    # Second pass: assign company IDs to all records
    for person in records:
        if not person.company_domain:
            continue

        domain = person.company_domain.lower()
        if domain in domain_to_company:
            person.company_unique_id = domain_to_company[domain]
            person.company_matched = True

    cursor.close()

    print(f"  Total companies matched: {stats.companies_matched}")
    print(f"  Total companies created: {stats.companies_created}")

    return records


# =============================================================================
# PERSON ID GENERATION
# =============================================================================

def generate_person_ids(records: List[PersonRecord], conn, stats: PipelineStats) -> List[PersonRecord]:
    """
    Generate or look up person unique IDs.
    """
    print("\n" + "="*60)
    print("PERSON ID GENERATION")
    print("="*60)

    cursor = conn.cursor()

    # Check for existing people by LinkedIn URL
    linkedin_urls = [p.linkedin_url for p in records if p.linkedin_url]

    if linkedin_urls:
        cursor.execute("""
            SELECT linkedin_url, unique_id
            FROM people.people_master
            WHERE linkedin_url = ANY(%s)
        """, (linkedin_urls,))
        linkedin_to_id = {row[0]: row[1] for row in cursor.fetchall()}
        print(f"  Found existing by LinkedIn: {len(linkedin_to_id)}")
    else:
        linkedin_to_id = {}

    new_count = 0
    existing_count = 0

    for i, person in enumerate(records):
        if person.linkedin_url and person.linkedin_url in linkedin_to_id:
            person.person_unique_id = linkedin_to_id[person.linkedin_url]
            existing_count += 1
        else:
            # Generate new ID matching Barton format: 04.04.02.XX.XXXXX.XXX
            seq = i + 1
            person.person_unique_id = f"04.04.02.99.{seq:05d}.{seq:03d}"
            new_count += 1

        # Also generate slot ID: 04.04.05.XX.XXXXX.XXX
        person.company_slot_unique_id = f"04.04.05.99.{i+1:05d}.{i+1:03d}"

    cursor.close()

    print(f"  Existing people matched: {existing_count}")
    print(f"  New person IDs generated: {new_count}")

    return records


# =============================================================================
# WRITE TO NEON
# =============================================================================

def write_people_to_neon(records: List[PersonRecord], conn, stats: PipelineStats):
    """
    Write person records to people.people_master.
    Note: full_name is a GENERATED column, don't insert into it.
    Required columns: unique_id, company_unique_id, company_slot_unique_id,
                     first_name, last_name, source_system, promoted_from_intake_at, last_verified_at
    """
    print("\n" + "="*60)
    print("WRITING TO NEON: people.people_master")
    print("="*60)

    cursor = conn.cursor()
    written = 0
    errors = 0
    skipped = 0

    for person in records:
        # Skip if missing required fields
        if not person.company_unique_id or not person.first_name or not person.last_name:
            skipped += 1
            continue

        try:
            cursor.execute("""
                INSERT INTO people.people_master (
                    unique_id, company_unique_id, company_slot_unique_id,
                    first_name, last_name, title, linkedin_url, email,
                    source_system, promoted_from_intake_at, last_verified_at, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, NOW(), NOW(), NOW()
                )
                ON CONFLICT (unique_id) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    title = EXCLUDED.title,
                    linkedin_url = COALESCE(EXCLUDED.linkedin_url, people.people_master.linkedin_url),
                    email = COALESCE(EXCLUDED.email, people.people_master.email),
                    updated_at = NOW()
            """, (
                person.person_unique_id,
                person.company_unique_id,
                person.company_slot_unique_id,
                person.first_name,
                person.last_name,
                person.job_title,
                person.linkedin_url,
                person.generated_email,
                person.data_source
            ))
            written += 1
        except Exception as e:
            conn.rollback()
            errors += 1
            if errors <= 5:
                print(f"  Error: {e}")

    conn.commit()
    cursor.close()

    print(f"  Written: {written}")
    print(f"  Skipped (missing required): {skipped}")
    print(f"  Errors: {errors}")


# =============================================================================
# MAIN
# =============================================================================

def load_csv(csv_path: str) -> List[PersonRecord]:
    """Load records from CSV."""
    records = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            record = PersonRecord(
                row_id=i + 1,
                company_name=row.get('Company Name', '').strip(),
                first_name=row.get('First Name', '').strip(),
                last_name=row.get('Last Name', '').strip(),
                full_name=row.get('Full Name', '').strip(),
                job_title=row.get('Job Title', '').strip(),
                location=row.get('Location', '').strip(),
                company_domain=row.get('Company Domain', '').strip(),
                linkedin_url=row.get('LinkedIn Profile', '').strip(),
            )
            records.append(record)

    return records


def main():
    if len(sys.argv) < 3:
        print("Usage: python run_people_pipeline.py <csv_path> <slot_type>")
        print("Example: python run_people_pipeline.py ceo.csv CEO")
        sys.exit(1)

    csv_path = sys.argv[1]
    slot_type = sys.argv[2].upper()

    print("="*60)
    print("PEOPLE INTELLIGENCE PIPELINE")
    print("="*60)
    print(f"CSV: {csv_path}")
    print(f"Slot Type: {slot_type}")
    print(f"Started: {datetime.now().isoformat()}")

    # Initialize
    stats = PipelineStats()
    conn = get_connection()

    # Load CSV
    print("\n" + "="*60)
    print("LOADING CSV")
    print("="*60)
    records = load_csv(csv_path)
    stats.total_records = len(records)
    print(f"  Loaded: {stats.total_records} records")

    # Pre-processing: Match companies and generate person IDs
    records = match_or_create_companies(records, conn, stats)
    records = generate_person_ids(records, conn, stats)

    # Write people to Neon first (required for FK constraints)
    write_people_to_neon(records, conn, stats)

    # Phase 5: Email Generation
    records = run_phase5(records, conn, stats)

    # Phase 6: Slot Assignment
    records = run_phase6(records, conn, stats, slot_type)

    # Phase 7: Enrichment Queue
    records = run_phase7(records, stats)

    # Phase 8: Output Writer
    output_dir = os.path.join(os.path.dirname(csv_path), "pipeline_output")
    output_files = run_phase8(records, stats, output_dir)

    # Final Summary
    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(f"  Total records: {stats.total_records}")
    print(f"  Companies matched/created: {stats.companies_matched}/{stats.companies_created}")
    print(f"  Emails generated: {stats.emails_generated}")
    print(f"  Slots assigned: {stats.slots_assigned}")
    print(f"  Enrichment queued: {stats.enrichment_queued}")
    print(f"\nOutput directory: {output_dir}")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
