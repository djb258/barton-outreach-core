#!/usr/bin/env python3
"""
WV HR & Benefits - Phase 3: Email Verification (Talent Engine)
===============================================================
Delegates email verification to the TypeScript Talent Engine.

This phase NO LONGER contains DNS/MX verification logic. All verification
is handled by the Talent Engine's EmailVerificationAgent.

Input: output/wv_hr_benefits/people.json
Output: Updated people with verification status (via Talent Engine)

Created: 2024-12-10
Updated: 2024-12-11 - Migrated to Talent Engine
"""

import json
import csv
import subprocess
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Paths
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "wv_hr_benefits"
PEOPLE_FILE = OUTPUT_DIR / "people.json"
COMPANIES_FILE = OUTPUT_DIR / "companies.json"
TALENT_ENGINE_DIR = Path(__file__).parent.parent.parent / "talent_engine"
SCRIPTS_DIR = TALENT_ENGINE_DIR / "dist" / "scripts"  # Compiled TypeScript output

# Batch size for Talent Engine calls
BATCH_SIZE = 100  # Verification can handle larger batches


def call_talent_engine(mode: str, input_data: List[Dict]) -> Dict:
    """
    Call the TypeScript Talent Engine via Node.js subprocess.

    Args:
        mode: The engine mode ('verify', 'pattern', etc.)
        input_data: List of records to process

    Returns:
        Dict with 'success', 'results', and optional 'errors'
    """
    script_path = SCRIPTS_DIR / "run_talent_engine.js"  # Compiled from .ts

    if not script_path.exists():
        print(f"   [ERROR] Talent Engine script not found: {script_path}")
        return {"success": False, "results": [], "errors": ["Script not found"]}

    try:
        result = subprocess.run(
            ["node", str(script_path), "--mode", mode, "--input", json.dumps(input_data)],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(TALENT_ENGINE_DIR)
        )

        if result.returncode != 0:
            print(f"   [ERROR] Talent Engine failed: {result.stderr}")
            return {"success": False, "results": [], "errors": [result.stderr]}

        try:
            output = json.loads(result.stdout)
            return output
        except json.JSONDecodeError:
            return {"success": True, "results": [], "raw_output": result.stdout}

    except subprocess.TimeoutExpired:
        print(f"   [ERROR] Talent Engine timeout after 300s")
        return {"success": False, "results": [], "errors": ["Timeout"]}
    except Exception as e:
        print(f"   [ERROR] Talent Engine call failed: {e}")
        return {"success": False, "results": [], "errors": [str(e)]}


def verify_emails_via_talent_engine(people: Dict) -> Dict:
    """
    Verify emails through Talent Engine's EmailVerificationAgent.

    The Talent Engine handles:
    - Syntax validation
    - MX record checks
    - SMTP verification (optional, rate-limited)
    - Vendor throttling (VitaMail, etc.)
    - Cost tracking
    """
    print("\n[PHASE 3] Email Verification via Talent Engine")
    print("=" * 55)

    # Filter people with emails to verify
    emails_to_verify = [
        {
            "person_id": pid,
            "email": person.get("email"),
            "company_id": person.get("company_id")
        }
        for pid, person in people.items()
        if person.get("email") and not person.get("email_verified")
    ]

    print(f"   Emails to verify: {len(emails_to_verify)}")
    print(f"   Already verified (skipped): {len(people) - len(emails_to_verify)}")

    # Process in batches
    processed = 0
    verified_count = 0
    failed_count = 0

    for i in range(0, len(emails_to_verify), BATCH_SIZE):
        batch = emails_to_verify[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(emails_to_verify) + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} emails)...")

        result = call_talent_engine("verify", batch)

        if result.get("success"):
            for item in result.get("results", []):
                person_id = item.get("person_id")
                if person_id and person_id in people:
                    is_valid = item.get("is_valid", False)

                    people[person_id]["email_verified"] = is_valid
                    people[person_id]["email_verification_status"] = item.get("status", "unknown")
                    people[person_id]["email_mx_records"] = item.get("mx_records", [])
                    people[person_id]["verification_source"] = "talent_engine"

                    # Adjust confidence based on verification
                    old_confidence = people[person_id].get("email_confidence", 0.7)
                    if is_valid:
                        new_confidence = min(1.0, old_confidence + 0.1)
                        verified_count += 1
                    else:
                        new_confidence = max(0.1, old_confidence - 0.2)
                        failed_count += 1

                    people[person_id]["email_confidence"] = round(new_confidence, 2)
                    people[person_id]["status"] = "verified" if is_valid else "verification_failed"
                    people[person_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

            processed += len(batch)
        else:
            print(f"   [WARN] Batch {batch_num} failed: {result.get('errors', ['Unknown error'])}")
            for item in batch:
                person_id = item.get("person_id")
                if person_id and person_id in people:
                    people[person_id]["email_verification_status"] = "error"
                    people[person_id]["status"] = "verification_error"
                    people[person_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            processed += len(batch)

    print(f"\n   Processed: {processed} emails")
    print(f"   Verified (valid): {verified_count}")
    print(f"   Failed verification: {failed_count}")

    return people


def save_outputs(people: Dict):
    """Save updated data"""
    print("\n[SAVING] Updated Files")
    print("=" * 55)

    # Update people JSON
    with open(PEOPLE_FILE, 'w') as f:
        json.dump(people, f, indent=2)
    print(f"   Updated: people.json")

    # Create verified emails CSV
    verified_csv = OUTPUT_DIR / "verified_emails.csv"
    verified_people = [p for p in people.values() if p.get('email_verified')]

    with open(verified_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'full_name', 'job_title', 'title_seniority', 'email',
            'email_confidence', 'linkedin_url', 'location', 'company_id'
        ])

        for person in sorted(verified_people, key=lambda x: (
            0 if x.get('title_seniority') == 'chro' else
            1 if x.get('title_seniority') == 'vp' else
            2 if x.get('title_seniority') == 'director' else 3,
            -(x.get('email_confidence') or 0)
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

    print(f"   Created: verified_emails.csv ({len(verified_people)} records)")

    # Create failed verification CSV for review
    failed_csv = OUTPUT_DIR / "failed_verification.csv"
    failed_people = [p for p in people.values()
                     if p.get('email') and not p.get('email_verified')]

    with open(failed_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'full_name', 'job_title', 'email', 'verification_status',
            'company_id', 'linkedin_url'
        ])

        for person in failed_people:
            writer.writerow([
                person.get('full_name'),
                person.get('job_title'),
                person.get('email'),
                person.get('email_verification_status'),
                person.get('company_id'),
                person.get('linkedin_url')
            ])

    print(f"   Created: failed_verification.csv ({len(failed_people)} records)")

    # Create no email generated CSV
    no_email_csv = OUTPUT_DIR / "no_email_generated.csv"
    no_email_people = [p for p in people.values() if not p.get('email')]

    with open(no_email_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'full_name', 'job_title', 'title_seniority', 'company_id',
            'linkedin_url', 'status'
        ])

        for person in no_email_people:
            writer.writerow([
                person.get('full_name'),
                person.get('job_title'),
                person.get('title_seniority'),
                person.get('company_id'),
                person.get('linkedin_url'),
                person.get('status')
            ])

    print(f"   Created: no_email_generated.csv ({len(no_email_people)} records)")

    # Create high-value verified CSV
    high_value_verified = [
        p for p in people.values()
        if p.get('email_verified') and p.get('title_seniority') in ['chro', 'vp', 'director']
    ]

    high_value_csv = OUTPUT_DIR / "high_value_verified.csv"
    with open(high_value_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'full_name', 'job_title', 'title_seniority', 'email',
            'email_confidence', 'linkedin_url', 'location', 'company_id'
        ])

        for person in sorted(high_value_verified, key=lambda x: (
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

    print(f"   Created: high_value_verified.csv ({len(high_value_verified)} records)")

    # Update progress.json
    progress_file = OUTPUT_DIR / "progress.json"
    with open(progress_file, 'r') as f:
        progress = json.load(f)

    verified_count = sum(1 for p in people.values() if p.get('email_verified'))
    failed_count = sum(1 for p in people.values()
                       if p.get('email') and not p.get('email_verified'))

    progress['emails_verified'] = verified_count
    progress['emails_failed_verification'] = failed_count
    progress['current_phase'] = 'verification_complete'
    progress['status'] = 'ready_for_export'
    progress['phase3_completed_at'] = datetime.now(timezone.utc).isoformat()
    progress['verification_engine'] = 'talent_engine'

    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)
    print(f"   Updated: progress.json")


def export_verification_failures(people: Dict, companies: Dict, source_file: str = "WV HR and Benefits.csv") -> int:
    """
    Export people whose emails failed verification.
    These go to marketing.failed_email_verification table.

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
        # Only export people who had email but failed verification
        email = person.get('email')
        if not email:
            continue

        if person.get('email_verified'):
            continue  # Successfully verified, not a failure

        company_id = person.get('company_id')
        company = companies.get(company_id, {}) if companies else {}

        verification_status = person.get('email_verification_status', 'unknown')
        verification_error = verification_status if verification_status != 'valid' else None

        # Check if already exists
        cur.execute("""
            SELECT id FROM marketing.failed_email_verification
            WHERE person_id = %s AND source_file = %s
        """, (pid, source_file))

        if cur.fetchone():
            # Update existing
            cur.execute("""
                UPDATE marketing.failed_email_verification SET
                    full_name = %s,
                    job_title = %s,
                    title_seniority = %s,
                    company_name_raw = %s,
                    linkedin_url = %s,
                    company_id = %s,
                    company_name = %s,
                    company_domain = %s,
                    email_pattern = %s,
                    slot_type = %s,
                    generated_email = %s,
                    verification_error = %s,
                    verification_notes = %s,
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
                company.get('email_pattern'),
                person.get('slot_assigned'),
                email,
                verification_error,
                f"Status: {verification_status}",
                pid,
                source_file
            ))
        else:
            # Insert new
            cur.execute("""
                INSERT INTO marketing.failed_email_verification (
                    person_id, full_name, job_title, title_seniority,
                    company_name_raw, linkedin_url, company_id, company_name,
                    company_domain, email_pattern, slot_type, generated_email,
                    verification_error, verification_notes,
                    resolution_status, source, source_file, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s, NOW(), NOW())
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
                company.get('email_pattern'),
                person.get('slot_assigned'),
                email,
                verification_error,
                f"Status: {verification_status}",
                'WV_HR_Pipeline',
                source_file
            ))

        exported += 1

    conn.commit()
    conn.close()

    return exported


def print_dashboard(people: Dict):
    """Print monitoring dashboard"""
    total = len(people)
    with_email = sum(1 for p in people.values() if p.get('email'))
    verified = sum(1 for p in people.values() if p.get('email_verified'))
    failed = sum(1 for p in people.values()
                 if p.get('email') and not p.get('email_verified'))

    # High-value breakdown
    high_value_verified = [
        p for p in people.values()
        if p.get('email_verified') and p.get('title_seniority') in ['chro', 'vp', 'director']
    ]

    chro_verified = sum(1 for p in high_value_verified if p.get('title_seniority') == 'chro')
    vp_verified = sum(1 for p in high_value_verified if p.get('title_seniority') == 'vp')
    dir_verified = sum(1 for p in high_value_verified if p.get('title_seniority') == 'director')

    print("\n")
    print("+" + "=" * 62 + "+")
    print("|" + " WV HR & BENEFITS - PHASE 3 COMPLETE (TALENT ENGINE) ".center(62) + "|")
    print("+" + "=" * 62 + "+")

    print("|" + " VERIFICATION RESULTS ".center(62, "-") + "|")
    print("|" + f"   Total People: {total}".ljust(62) + "|")
    print("|" + f"   With Email: {with_email}".ljust(62) + "|")
    if with_email > 0:
        pct = verified * 100 // with_email
        print("|" + f"   Verified (MX valid): {verified} ({pct}%)".ljust(62) + "|")
    print("|" + f"   Failed Verification: {failed}".ljust(62) + "|")

    print("+" + "-" * 62 + "+")
    print("|" + " HIGH-VALUE VERIFIED ".center(62, "-") + "|")
    print("|" + f"   CHRO: {chro_verified}".ljust(62) + "|")
    print("|" + f"   VP: {vp_verified}".ljust(62) + "|")
    print("|" + f"   Director: {dir_verified}".ljust(62) + "|")
    print("|" + f"   TOTAL: {len(high_value_verified)}".ljust(62) + "|")

    print("+" + "=" * 62 + "+")


def main():
    """Main execution"""
    print("\n" + "=" * 60)
    print(" WV HR & BENEFITS - PHASE 3: EMAIL VERIFICATION ".center(60))
    print(" (via Talent Engine) ".center(60))
    print("=" * 60)

    # Load data
    print("\n[LOADING] Input Files")
    print("=" * 55)

    with open(PEOPLE_FILE, 'r') as f:
        people = json.load(f)
    print(f"   Loaded: {len(people)} people")

    with open(COMPANIES_FILE, 'r') as f:
        companies = json.load(f)
    print(f"   Loaded: {len(companies)} companies")

    # Verify via Talent Engine
    people = verify_emails_via_talent_engine(people)

    # Save
    save_outputs(people)

    # Export verification failures to Neon
    print("\n[EXPORTING] Verification Failures to Neon")
    print("=" * 55)
    failed_count = export_verification_failures(people, companies)
    print(f"   Exported: {failed_count} people to failed_email_verification table")

    # Dashboard
    print_dashboard(people)

    verified_count = sum(1 for p in people.values() if p.get('email_verified'))
    print("\n[COMPLETE] Phase 3 finished successfully!")
    print(f"   Ready for Neon export: {verified_count} verified emails")
    print("   Verification Engine: TypeScript Talent Engine")

    return people


if __name__ == "__main__":
    main()
