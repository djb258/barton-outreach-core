#!/usr/bin/env python3
"""
WV HR & Benefits - Phase 2: Email Pattern Discovery (Talent Engine)
====================================================================
Delegates email pattern discovery to the TypeScript Talent Engine.

This phase NO LONGER contains pattern detection logic. All enrichment
is handled by the Talent Engine's PatternAgent.

Input: output/wv_hr_benefits/companies.json, people.json
Output: Updated companies with patterns, people with emails (via Talent Engine)

Created: 2024-12-10
Updated: 2024-12-11 - Migrated to Talent Engine
"""

import json
import csv
import subprocess
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Paths
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "wv_hr_benefits"
COMPANIES_FILE = OUTPUT_DIR / "companies.json"
PEOPLE_FILE = OUTPUT_DIR / "people.json"
TALENT_ENGINE_DIR = Path(__file__).parent.parent.parent / "talent_engine"
SCRIPTS_DIR = TALENT_ENGINE_DIR / "dist" / "scripts"  # Compiled TypeScript output

# Batch size for Talent Engine calls
BATCH_SIZE = 50


def call_talent_engine(mode: str, input_data: List[Dict]) -> Dict:
    """
    Call the TypeScript Talent Engine via Node.js subprocess.

    Args:
        mode: The engine mode ('pattern', 'verify', 'enrich')
        input_data: List of records to process

    Returns:
        Dict with 'success', 'results', and optional 'errors'
    """
    script_path = SCRIPTS_DIR / "run_talent_engine.js"  # Compiled from .ts

    if not script_path.exists():
        print(f"   [ERROR] Talent Engine script not found: {script_path}")
        return {"success": False, "results": [], "errors": ["Script not found"]}

    try:
        # Call Node.js script with JSON input
        result = subprocess.run(
            ["node", str(script_path), "--mode", mode, "--input", json.dumps(input_data)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=str(TALENT_ENGINE_DIR)
        )

        if result.returncode != 0:
            print(f"   [ERROR] Talent Engine failed: {result.stderr}")
            return {"success": False, "results": [], "errors": [result.stderr]}

        # Parse JSON output
        try:
            output = json.loads(result.stdout)
            return output
        except json.JSONDecodeError:
            # If not JSON, return raw output
            return {"success": True, "results": [], "raw_output": result.stdout}

    except subprocess.TimeoutExpired:
        print(f"   [ERROR] Talent Engine timeout after 300s")
        return {"success": False, "results": [], "errors": ["Timeout"]}
    except Exception as e:
        print(f"   [ERROR] Talent Engine call failed: {e}")
        return {"success": False, "results": [], "errors": [str(e)]}


def process_companies_via_talent_engine(companies: Dict) -> Dict:
    """
    Process companies through Talent Engine's PatternAgent.

    The Talent Engine handles:
    - Domain validation
    - Email pattern discovery (Hunter.io, etc.)
    - Pattern confidence scoring
    - Vendor throttling and cost management
    """
    print("\n[PHASE 2A] Email Pattern Discovery via Talent Engine")
    print("=" * 55)

    # Filter companies with domains
    companies_with_domain = [
        {
            "company_id": cid,
            "company_name": c.get("company_name"),
            "domain": c.get("domain")
        }
        for cid, c in companies.items()
        if c.get("domain")
    ]

    print(f"   Companies to process: {len(companies_with_domain)}")
    print(f"   Companies without domain (skipped): {len(companies) - len(companies_with_domain)}")

    # Process in batches
    processed = 0
    patterns_found = 0

    for i in range(0, len(companies_with_domain), BATCH_SIZE):
        batch = companies_with_domain[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(companies_with_domain) + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} companies)...")

        result = call_talent_engine("pattern", batch)

        if result.get("success"):
            for item in result.get("results", []):
                company_id = item.get("company_id")
                if company_id and company_id in companies:
                    companies[company_id]["email_pattern"] = item.get("email_pattern")
                    companies[company_id]["pattern_confidence"] = item.get("pattern_confidence", 0)
                    companies[company_id]["pattern_source"] = item.get("source", "talent_engine")
                    companies[company_id]["status"] = "pattern_detected"
                    companies[company_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

                    if item.get("email_pattern"):
                        patterns_found += 1

                processed += len(batch)
        else:
            print(f"   [WARN] Batch {batch_num} failed: {result.get('errors', ['Unknown error'])}")
            # Mark as failed but continue
            for item in batch:
                company_id = item.get("company_id")
                if company_id and company_id in companies:
                    companies[company_id]["status"] = "pattern_failed"
                    companies[company_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            processed += len(batch)

    print(f"\n   Processed: {processed} companies")
    print(f"   Patterns Found: {patterns_found}")

    return companies


def process_people_via_talent_engine(people: Dict, companies: Dict) -> Dict:
    """
    Process people through Talent Engine's EmailGeneratorAgent.

    SLOT-BASED PROCESSING (Golden Rule):
    Only generate emails for people who have a slot_assigned.
    This uses the slot assignment from Phase 1 (wv_hr_benefits_intake.py).

    The Talent Engine handles:
    - Email generation based on company pattern
    - Name normalization
    - Variant generation
    - Vendor throttling
    """
    print("\n[PHASE 2B] Email Generation via Talent Engine")
    print("=" * 55)

    # Prepare people data - ONLY process people with slot_assigned
    people_to_process = []
    skipped_no_pattern = 0
    skipped_no_slot = 0

    for pid, person in people.items():
        company_id = person.get("company_id")
        company = companies.get(company_id, {})
        slot_assigned = person.get("slot_assigned")

        # Check 1: Person must have a slot assignment (from Phase 1)
        # This is the Golden Rule - no email generation without a slot
        if not slot_assigned:
            skipped_no_slot += 1
            continue

        # Check 2: Company must have pattern AND domain
        if not (company.get("email_pattern") and company.get("domain")):
            skipped_no_pattern += 1
            continue

        people_to_process.append({
            "person_id": pid,
            "first_name": person.get("first_name"),
            "last_name": person.get("last_name"),
            "full_name": person.get("full_name"),
            "company_id": company_id,
            "domain": company.get("domain"),
            "email_pattern": company.get("email_pattern"),
            "slot_type": slot_assigned
        })

    print(f"   People with slots to process: {len(people_to_process)}")
    print(f"   Skipped (no slot assigned): {skipped_no_slot}")
    print(f"   Skipped (no company pattern): {skipped_no_pattern}")
    print(f"   Total skipped: {skipped_no_pattern + skipped_no_slot}")

    # Process in batches
    processed = 0
    emails_generated = 0

    for i in range(0, len(people_to_process), BATCH_SIZE):
        batch = people_to_process[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(people_to_process) + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} people)...")

        result = call_talent_engine("generate_email", batch)

        if result.get("success"):
            for item in result.get("results", []):
                person_id = item.get("person_id")
                if person_id and person_id in people:
                    people[person_id]["email"] = item.get("email")
                    people[person_id]["email_pattern_used"] = item.get("pattern_used")
                    people[person_id]["email_confidence"] = item.get("confidence", 0)
                    people[person_id]["email_variants"] = item.get("variants", [])
                    people[person_id]["email_verified"] = False
                    people[person_id]["status"] = "email_generated"
                    people[person_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

                    if item.get("email"):
                        emails_generated += 1

                processed += len(batch)
        else:
            print(f"   [WARN] Batch {batch_num} failed: {result.get('errors', ['Unknown error'])}")
            for item in batch:
                person_id = item.get("person_id")
                if person_id and person_id in people:
                    people[person_id]["status"] = "email_generation_failed"
                    people[person_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            processed += len(batch)

    print(f"\n   Processed: {processed} people")
    print(f"   Emails Generated: {emails_generated}")

    return people


def save_outputs(companies: Dict, people: Dict):
    """Save updated data"""
    print("\n[SAVING] Updated Files")
    print("=" * 55)

    # Update JSON files
    with open(COMPANIES_FILE, 'w') as f:
        json.dump(companies, f, indent=2)
    print(f"   Updated: companies.json")

    with open(PEOPLE_FILE, 'w') as f:
        json.dump(people, f, indent=2)
    print(f"   Updated: people.json")

    # Create enriched people CSV with emails
    enriched_csv = OUTPUT_DIR / "people_with_emails.csv"
    with open(enriched_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'person_id', 'full_name', 'job_title', 'title_seniority',
            'company_id', 'email', 'email_confidence', 'linkedin_url', 'location'
        ])

        for person in sorted(people.values(), key=lambda x: (
            0 if x.get('title_seniority') == 'chro' else
            1 if x.get('title_seniority') == 'vp' else
            2 if x.get('title_seniority') == 'director' else 3,
            -(x.get('email_confidence') or 0)
        )):
            writer.writerow([
                person.get('person_id'),
                person.get('full_name'),
                person.get('job_title'),
                person.get('title_seniority'),
                person.get('company_id'),
                person.get('email'),
                person.get('email_confidence'),
                person.get('linkedin_url'),
                person.get('location')
            ])
    print(f"   Created: people_with_emails.csv")

    # Create high-value targets with emails
    high_value_csv = OUTPUT_DIR / "high_value_with_emails.csv"
    high_value = [p for p in people.values()
                  if p.get('title_seniority') in ['chro', 'vp', 'director'] and p.get('email')]

    with open(high_value_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'full_name', 'job_title', 'title_seniority', 'email',
            'email_confidence', 'linkedin_url', 'location', 'company_id'
        ])

        for person in sorted(high_value, key=lambda x: (
            0 if x.get('title_seniority') == 'chro' else
            1 if x.get('title_seniority') == 'vp' else 2
        )):
            writer.writerow([
                person.get('full_name'),
                person.get('job_title'),
                person.get('title_seniority'),
                person.get('email'),
                person.get('email_confidence'),
                person.get('linkedin_url'),
                person.get('location'),
                person.get('company_id')
            ])
    print(f"   Created: high_value_with_emails.csv ({len(high_value)} records)")

    # Update progress.json
    progress_file = OUTPUT_DIR / "progress.json"
    with open(progress_file, 'r') as f:
        progress = json.load(f)

    progress['companies_with_pattern'] = sum(1 for c in companies.values() if c.get('email_pattern'))
    progress['people_with_email'] = sum(1 for p in people.values() if p.get('email'))
    progress['current_phase'] = 'pattern_complete'
    progress['status'] = 'emails_generated'
    progress['phase2_completed_at'] = datetime.now(timezone.utc).isoformat()
    progress['enrichment_engine'] = 'talent_engine'

    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)
    print(f"   Updated: progress.json")


def export_no_pattern_failures(people: Dict, companies: Dict, source_file: str = "WV HR and Benefits.csv") -> int:
    """
    Export people who have slots but whose companies have no email pattern.
    These go to marketing.failed_no_pattern table.

    Returns: count of failures exported
    """
    DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')
    if not DATABASE_URL:
        print("   [WARN] No DATABASE_URL - skipping failure export")
        return 0

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    exported = 0

    for pid, person in people.items():
        slot_assigned = person.get('slot_assigned')
        if not slot_assigned:
            continue  # Only process people with slots

        company_id = person.get('company_id')
        company = companies.get(company_id, {})

        # Check if company has pattern and domain
        has_pattern = bool(company.get('email_pattern'))
        has_domain = bool(company.get('domain'))

        if has_pattern and has_domain:
            continue  # This person can get an email, no failure

        # Determine failure reason
        if not has_domain:
            failure_reason = 'no_domain'
            failure_notes = 'Company has no domain - cannot generate email'
        else:
            failure_reason = 'no_pattern'
            failure_notes = f"Company has domain ({company.get('domain')}) but no email pattern discovered"

        # Check if already exists
        cur.execute("""
            SELECT id FROM marketing.failed_no_pattern
            WHERE person_id = %s AND source_file = %s
        """, (pid, source_file))

        if cur.fetchone():
            # Update existing
            cur.execute("""
                UPDATE marketing.failed_no_pattern SET
                    full_name = %s,
                    job_title = %s,
                    title_seniority = %s,
                    company_name_raw = %s,
                    linkedin_url = %s,
                    company_id = %s,
                    company_name = %s,
                    company_domain = %s,
                    slot_type = %s,
                    failure_reason = %s,
                    failure_notes = %s,
                    updated_at = NOW()
                WHERE person_id = %s AND source_file = %s
            """, (
                person.get('full_name'),
                person.get('job_title'),
                person.get('title_seniority'),
                person.get('company_name_raw'),
                person.get('linkedin_url'),
                company_id,
                company.get('company_name'),
                company.get('domain'),
                slot_assigned,
                failure_reason,
                failure_notes,
                pid,
                source_file
            ))
        else:
            # Insert new
            cur.execute("""
                INSERT INTO marketing.failed_no_pattern (
                    person_id, full_name, job_title, title_seniority,
                    company_name_raw, linkedin_url, company_id, company_name,
                    company_domain, slot_type, failure_reason, failure_notes,
                    resolution_status, source, source_file, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s, NOW(), NOW())
            """, (
                pid,
                person.get('full_name'),
                person.get('job_title'),
                person.get('title_seniority'),
                person.get('company_name_raw'),
                person.get('linkedin_url'),
                company_id,
                company.get('company_name'),
                company.get('domain'),
                slot_assigned,
                failure_reason,
                failure_notes,
                'WV_HR_Pipeline',
                source_file
            ))

        exported += 1

    conn.commit()
    conn.close()

    return exported


def print_dashboard(companies: Dict, people: Dict):
    """Print monitoring dashboard"""
    with_pattern = sum(1 for c in companies.values() if c.get('email_pattern'))
    with_email = sum(1 for p in people.values() if p.get('email'))

    # Slot analysis - use actual slot_assigned field
    total_people = len(people)
    with_slot = sum(1 for p in people.values() if p.get('slot_assigned'))
    without_slot = total_people - with_slot

    # Pattern distribution
    patterns = {}
    for c in companies.values():
        pattern = c.get('email_pattern')
        if pattern:
            patterns[pattern] = patterns.get(pattern, 0) + 1

    # Slot type breakdown with emails
    slot_emails = {'hr': 0, 'benefits': 0}
    for p in people.values():
        slot = p.get('slot_assigned')
        if slot and p.get('email'):
            slot_emails[slot] = slot_emails.get(slot, 0) + 1

    # Seniority breakdown of people with emails
    seniority_emails = {}
    for p in people.values():
        if p.get('email') and p.get('slot_assigned'):
            seniority = p.get('title_seniority')
            seniority_emails[seniority] = seniority_emails.get(seniority, 0) + 1

    print("\n")
    print("+" + "=" * 62 + "+")
    print("|" + " WV HR & BENEFITS - PHASE 2 COMPLETE (TALENT ENGINE) ".center(62) + "|")
    print("+" + "=" * 62 + "+")

    print("|" + " COMPANY PATTERNS ".center(62, "-") + "|")
    print("|" + f"   Companies with Pattern: {with_pattern}/{len(companies)}".ljust(62) + "|")
    print("|" + "   Pattern Distribution:".ljust(62) + "|")
    for pattern, count in sorted(patterns.items(), key=lambda x: -x[1]):
        print("|" + f"     - {pattern}: {count}".ljust(62) + "|")

    print("+" + "-" * 62 + "+")
    print("|" + " SLOT-BASED EMAIL GENERATION ".center(62, "-") + "|")
    print("|" + f"   Total People: {total_people}".ljust(62) + "|")
    print("|" + f"   With Slot Assigned: {with_slot}".ljust(62) + "|")
    print("|" + f"   Without Slot (skipped): {without_slot}".ljust(62) + "|")
    print("|" + f"   Emails Generated: {with_email}".ljust(62) + "|")
    if with_slot > 0:
        efficiency = with_email * 100 // with_slot
        print("|" + f"   Generation Efficiency: {efficiency}%".ljust(62) + "|")
    print("|" + f"   API Calls Saved: {without_slot}".ljust(62) + "|")

    print("+" + "-" * 62 + "+")
    print("|" + " SLOT BREAKDOWN WITH EMAIL ".center(62, "-") + "|")
    print("|" + f"   HR Slots: {slot_emails.get('hr', 0)}".ljust(62) + "|")
    print("|" + f"   Benefits Slots: {slot_emails.get('benefits', 0)}".ljust(62) + "|")
    print("|" + f"   TOTAL: {slot_emails.get('hr', 0) + slot_emails.get('benefits', 0)}".ljust(62) + "|")

    print("+" + "-" * 62 + "+")
    print("|" + " SENIORITY OF PEOPLE WITH EMAILS ".center(62, "-") + "|")
    for sen, count in sorted(seniority_emails.items(), key=lambda x: -x[1]):
        print("|" + f"   {sen.upper()}: {count}".ljust(62) + "|")

    print("+" + "=" * 62 + "+")


def main():
    """Main execution"""
    print("\n" + "=" * 60)
    print(" WV HR & BENEFITS - PHASE 2: EMAIL PATTERNS ".center(60))
    print(" (via Talent Engine) ".center(60))
    print("=" * 60)

    # Load data
    print("\n[LOADING] Input Files")
    print("=" * 55)

    with open(COMPANIES_FILE, 'r') as f:
        companies = json.load(f)
    print(f"   Loaded: {len(companies)} companies")

    with open(PEOPLE_FILE, 'r') as f:
        people = json.load(f)
    print(f"   Loaded: {len(people)} people")

    # Process via Talent Engine
    companies = process_companies_via_talent_engine(companies)
    people = process_people_via_talent_engine(people, companies)

    # Save
    save_outputs(companies, people)

    # Export failures to Neon
    print("\n[EXPORTING] No-Pattern Failures to Neon")
    print("=" * 55)
    no_pattern_count = export_no_pattern_failures(people, companies)
    print(f"   Exported: {no_pattern_count} people to failed_no_pattern table")

    # Dashboard
    print_dashboard(companies, people)

    print("\n[COMPLETE] Phase 2 finished successfully!")
    print(f"   Output: {OUTPUT_DIR}")
    print("   Enrichment Engine: TypeScript Talent Engine")

    return companies, people


if __name__ == "__main__":
    main()
