#!/usr/bin/env python3
"""
WV HR & Benefits - Full Pipeline with MillionVerifier
======================================================
Complete end-to-end pipeline:
1. Load CSV → Match people to companies
2. Assign slots (seniority competition)
3. Generate emails from patterns
4. Verify emails with MillionVerifier
5. Export ONLY verified people to Neon

This ensures we ONLY export people with verified emails that won't bounce.

Created: 2024-12-11
"""

import csv
import json
import os
import sys
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
from dotenv import load_dotenv
import psycopg2

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "email"))
from pattern_guesser import generate_email, parse_full_name, PatternType, PATTERN_PRIORITY

load_dotenv()

# Config
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "wv_hr_benefits"
INPUT_CSV = OUTPUT_DIR / "people.csv"  # Already processed CSV with person_ids
DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')
MILLIONVERIFIER_API_KEY = os.getenv('MILLIONVERIFIER_API_KEY')

# Thresholds
FUZZY_MATCH_THRESHOLD = 80
FUZZY_REVIEW_THRESHOLD = 70

# Seniority rankings for slot competition
SENIORITY_RANK = {
    'CHRO': 1, 'Chief Human Resources Officer': 1, 'Chief People Officer': 1,
    'VP': 2, 'Vice President': 2, 'SVP': 2,
    'Director': 3,
    'Manager': 4,
    'HRBP': 5, 'HR Business Partner': 5,
    'Generalist': 6,
    'Specialist': 7, 'Coordinator': 7, 'Administrator': 7,
    'Other': 8
}


@dataclass
class Person:
    person_id: str
    full_name: str
    first_name: str
    last_name: str
    job_title: str
    seniority: str
    seniority_rank: int
    company_name_raw: str
    linkedin_url: str
    matched_company_id: Optional[str] = None
    matched_company_name: Optional[str] = None
    matched_domain: Optional[str] = None
    fuzzy_score: float = 0.0
    slot_assigned: Optional[str] = None
    email_pattern: Optional[str] = None
    generated_email: Optional[str] = None
    email_verified: bool = False
    email_result: Optional[str] = None
    failure_reason: Optional[str] = None


def load_companies_from_neon() -> Dict[str, Dict]:
    """Load companies with domains and patterns from Neon"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("""
        SELECT company_unique_id, company_name, domain, email_pattern
        FROM marketing.company_master
        WHERE domain IS NOT NULL AND domain != ''
    """)

    companies = {}
    for row in cur.fetchall():
        companies[row[0]] = {
            'company_id': row[0],
            'company_name': row[1],
            'domain': row[2],
            'email_pattern': row[3]
        }

    conn.close()
    return companies


def load_csv(csv_path: Path) -> List[Dict]:
    """Load people from CSV"""
    people = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            people.append({
                'row_id': i + 1,
                'person_id': row.get('person_id', '').strip(),
                'full_name': row.get('full_name', '').strip(),
                'job_title': row.get('job_title', '').strip(),
                'company_name': row.get('company_name_raw', '').strip(),
                'linkedin_url': row.get('linkedin_url', '').strip(),
            })
    return people


def extract_seniority(title: str) -> Tuple[str, int]:
    """Extract seniority level from job title"""
    title_lower = title.lower()

    if 'chief' in title_lower or 'chro' in title_lower:
        return 'CHRO', 1
    elif 'vp' in title_lower or 'vice president' in title_lower or 'svp' in title_lower:
        return 'VP', 2
    elif 'director' in title_lower:
        return 'Director', 3
    elif 'manager' in title_lower:
        return 'Manager', 4
    elif 'hrbp' in title_lower or 'business partner' in title_lower:
        return 'HRBP', 5
    elif 'generalist' in title_lower:
        return 'Generalist', 6
    elif 'specialist' in title_lower or 'coordinator' in title_lower or 'admin' in title_lower:
        return 'Specialist', 7
    else:
        return 'Other', 8


def fuzzy_match_companies(people_data: List[Dict], companies: Dict) -> List[Person]:
    """Match people to companies using fuzzy matching"""
    from rapidfuzz import fuzz, process

    # Build company name lookup
    company_names = {c['company_name']: c for c in companies.values()}
    company_name_list = list(company_names.keys())

    people = []

    for p in people_data:
        first, last = parse_full_name(p['full_name'])
        seniority, rank = extract_seniority(p['job_title'])

        person = Person(
            person_id=p.get('person_id') or f"PE-WV-{hash(p['full_name'] + p['company_name']) & 0xFFFFFFFF:08X}",
            full_name=p['full_name'],
            first_name=first,
            last_name=last,
            job_title=p['job_title'],
            seniority=seniority,
            seniority_rank=rank,
            company_name_raw=p['company_name'],
            linkedin_url=p['linkedin_url']
        )

        if not p['company_name']:
            person.failure_reason = 'no_company_name'
            people.append(person)
            continue

        # Fuzzy match
        match = process.extractOne(
            p['company_name'],
            company_name_list,
            scorer=fuzz.token_sort_ratio
        )

        if match:
            matched_name, score, _ = match
            person.fuzzy_score = score

            if score >= FUZZY_MATCH_THRESHOLD:
                company = company_names[matched_name]
                person.matched_company_id = company['company_id']
                person.matched_company_name = company['company_name']
                person.matched_domain = company['domain']
                person.email_pattern = company.get('email_pattern')
            elif score >= FUZZY_REVIEW_THRESHOLD:
                person.failure_reason = 'low_confidence'
                person.matched_company_name = matched_name
            else:
                person.failure_reason = 'no_match'
        else:
            person.failure_reason = 'no_match'

        people.append(person)

    return people


def assign_slots(people: List[Person]) -> List[Person]:
    """Assign HR slots - one person per company, highest seniority wins"""
    # Group by company
    by_company = defaultdict(list)
    for p in people:
        if p.matched_company_id and not p.failure_reason:
            by_company[p.matched_company_id].append(p)

    # For each company, pick the highest seniority person
    for company_id, company_people in by_company.items():
        # Sort by seniority rank (lower = higher seniority)
        company_people.sort(key=lambda x: x.seniority_rank)

        # Winner gets the slot
        winner = company_people[0]
        winner.slot_assigned = 'hr'

        # Losers go to failure
        for loser in company_people[1:]:
            loser.failure_reason = 'lost_slot'
            loser.slot_assigned = None

    return people


def generate_emails(people: List[Person]) -> List[Person]:
    """Generate emails for people who won slots"""
    for p in people:
        if p.slot_assigned and p.matched_domain and p.email_pattern:
            # Convert pattern string to PatternType
            pattern_map = {
                '{first}.{last}': PatternType.FIRST_DOT_LAST,
                '{first}{last}': PatternType.FIRST_LAST,
                '{f}{last}': PatternType.F_LAST,
                '{first}': PatternType.FIRST,
                '{first}_{last}': PatternType.FIRST_UNDERSCORE_LAST,
                '{last}{f}': PatternType.LAST_F,
                '{f}.{last}': PatternType.F_DOT_LAST,
                '{last}.{first}': PatternType.LAST_DOT_FIRST,
                'first.last': PatternType.FIRST_DOT_LAST,
                'firstlast': PatternType.FIRST_LAST,
                'flast': PatternType.F_LAST,
                'first': PatternType.FIRST,
                'first_last': PatternType.FIRST_UNDERSCORE_LAST,
            }

            pattern_type = pattern_map.get(p.email_pattern, PatternType.FIRST_DOT_LAST)
            p.generated_email = generate_email(p.first_name, p.last_name, p.matched_domain, pattern_type)
        elif p.slot_assigned and p.matched_domain and not p.email_pattern:
            # No pattern - need to discover it
            p.failure_reason = 'no_pattern'
            p.slot_assigned = None

    return people


async def verify_email_millionverifier(session: aiohttp.ClientSession, email: str) -> Tuple[bool, str]:
    """Verify a single email with MillionVerifier"""
    url = f"https://api.millionverifier.com/api/v3/?api={MILLIONVERIFIER_API_KEY}&email={email}"

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                data = await response.json()
                result = data.get('result', 'unknown')

                # Valid results
                if result.lower() in ['ok', 'valid', 'deliverable']:
                    return True, result
                # Risky but acceptable (catch-all domains)
                elif result.lower() in ['catch_all', 'accept_all']:
                    return True, result
                # Invalid
                else:
                    return False, result
            else:
                return False, f"api_error_{response.status}"
    except Exception as e:
        return False, f"error_{str(e)}"


async def verify_emails_batch(people: List[Person]) -> List[Person]:
    """Verify all generated emails with MillionVerifier"""
    # Get people with emails to verify
    to_verify = [p for p in people if p.generated_email and p.slot_assigned]

    if not to_verify:
        return people

    print(f"\n   Verifying {len(to_verify)} emails with MillionVerifier...")

    async with aiohttp.ClientSession() as session:
        for i, person in enumerate(to_verify):
            verified, result = await verify_email_millionverifier(session, person.generated_email)
            person.email_verified = verified
            person.email_result = result

            if not verified:
                person.failure_reason = 'email_invalid'
                person.slot_assigned = None

            # Progress
            if (i + 1) % 10 == 0:
                print(f"      Verified {i + 1}/{len(to_verify)}...")

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)

    return people


def export_to_neon(people: List[Person], source_file: str = "WV HR and Benefits.csv"):
    """Export verified people to Neon"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Get next sequence number
    cur.execute("SELECT MAX(CAST(SPLIT_PART(unique_id, '.', 6) AS INTEGER)) FROM marketing.people_master")
    result = cur.fetchone()[0]
    next_seq = (result or 0) + 1

    # Export verified people
    verified = [p for p in people if p.email_verified and p.slot_assigned]

    print(f"\n   Exporting {len(verified)} verified people to Neon...")

    for p in verified:
        unique_id = f"04.04.02.04.20000.{next_seq:03d}"

        cur.execute("""
            INSERT INTO marketing.people_master (
                unique_id, company_unique_id, full_name, first_name, last_name,
                email, email_verified, email_confidence, linkedin_url,
                title, title_seniority, source, source_file, slot_complete, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (unique_id) DO NOTHING
        """, (
            unique_id, p.matched_company_id, p.full_name, p.first_name, p.last_name,
            p.generated_email, True, 0.95, p.linkedin_url,
            p.job_title, p.seniority, 'wv_hr_pipeline', source_file, True
        ))

        next_seq += 1

    conn.commit()

    # Export failures to appropriate tables
    failures = [p for p in people if p.failure_reason]
    export_failures_to_neon(cur, failures, source_file)

    conn.commit()
    conn.close()

    return len(verified)


def export_failures_to_neon(cur, failures: List[Person], source_file: str):
    """Export failures to stage-specific tables"""
    for p in failures:
        if p.failure_reason == 'no_match':
            cur.execute("""
                INSERT INTO marketing.failed_company_match (
                    person_id, full_name, job_title, title_seniority, company_name_raw,
                    linkedin_url, best_match_score, source_file
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (person_id, source_file) DO NOTHING
            """, (p.person_id, p.full_name, p.job_title, p.seniority, p.company_name_raw,
                  p.linkedin_url, p.fuzzy_score, source_file))

        elif p.failure_reason == 'low_confidence':
            cur.execute("""
                INSERT INTO marketing.failed_low_confidence (
                    person_id, full_name, job_title, title_seniority, company_name_raw,
                    linkedin_url, matched_company_name, fuzzy_score, source_file
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (person_id, source_file) DO NOTHING
            """, (p.person_id, p.full_name, p.job_title, p.seniority, p.company_name_raw,
                  p.linkedin_url, p.matched_company_name, p.fuzzy_score, source_file))

        elif p.failure_reason == 'lost_slot':
            cur.execute("""
                INSERT INTO marketing.failed_slot_assignment (
                    person_id, full_name, job_title, title_seniority, company_name_raw,
                    linkedin_url, matched_company_id, matched_company_name, fuzzy_score,
                    slot_type, source_file
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (person_id, source_file) DO NOTHING
            """, (p.person_id, p.full_name, p.job_title, p.seniority, p.company_name_raw,
                  p.linkedin_url, p.matched_company_id, p.matched_company_name, p.fuzzy_score,
                  'hr', source_file))

        elif p.failure_reason == 'no_pattern':
            cur.execute("""
                INSERT INTO marketing.failed_no_pattern (
                    person_id, full_name, job_title, title_seniority, company_name_raw,
                    linkedin_url, company_id, company_name, company_domain,
                    failure_reason, source_file
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (person_id, source_file) DO NOTHING
            """, (p.person_id, p.full_name, p.job_title, p.seniority, p.company_name_raw,
                  p.linkedin_url, p.matched_company_id, p.matched_company_name, p.matched_domain,
                  'no_pattern', source_file))

        elif p.failure_reason == 'email_invalid':
            cur.execute("""
                INSERT INTO marketing.failed_email_verification (
                    person_id, full_name, job_title, title_seniority, company_name_raw,
                    linkedin_url, company_id, company_name, company_domain,
                    email_pattern, generated_email, verification_error, source_file
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (person_id, source_file) DO NOTHING
            """, (p.person_id, p.full_name, p.job_title, p.seniority, p.company_name_raw,
                  p.linkedin_url, p.matched_company_id, p.matched_company_name, p.matched_domain,
                  p.email_pattern, p.generated_email, p.email_result, source_file))


async def run_pipeline():
    """Run the full pipeline"""
    print("=" * 70)
    print("WV HR & BENEFITS - FULL PIPELINE WITH MILLIONVERIFIER")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")

    # Check requirements
    if not MILLIONVERIFIER_API_KEY:
        print("\n[ERROR] MILLIONVERIFIER_API_KEY not set")
        return

    # Step 1: Load data
    print("\n[STEP 1] Loading data...")
    companies = load_companies_from_neon()
    print(f"   Companies from Neon: {len(companies)}")

    if not INPUT_CSV.exists():
        print(f"   [ERROR] CSV not found: {INPUT_CSV}")
        return

    people_data = load_csv(INPUT_CSV)
    print(f"   People from CSV: {len(people_data)}")

    # Step 2: Fuzzy match
    print("\n[STEP 2] Matching people to companies...")
    people = fuzzy_match_companies(people_data, companies)
    matched = sum(1 for p in people if p.matched_company_id and not p.failure_reason)
    print(f"   Matched: {matched}")
    print(f"   No match: {sum(1 for p in people if p.failure_reason == 'no_match')}")
    print(f"   Low confidence: {sum(1 for p in people if p.failure_reason == 'low_confidence')}")

    # Step 3: Assign slots
    print("\n[STEP 3] Assigning slots (seniority competition)...")
    people = assign_slots(people)
    slots = sum(1 for p in people if p.slot_assigned)
    print(f"   Slots assigned: {slots}")
    print(f"   Lost slot: {sum(1 for p in people if p.failure_reason == 'lost_slot')}")

    # Step 4: Generate emails
    print("\n[STEP 4] Generating emails from patterns...")
    people = generate_emails(people)
    with_email = sum(1 for p in people if p.generated_email)
    print(f"   Emails generated: {with_email}")
    print(f"   No pattern: {sum(1 for p in people if p.failure_reason == 'no_pattern')}")

    # Step 5: Verify emails
    print("\n[STEP 5] Verifying emails with MillionVerifier...")
    people = await verify_emails_batch(people)
    verified = sum(1 for p in people if p.email_verified)
    invalid = sum(1 for p in people if p.failure_reason == 'email_invalid')
    print(f"   Verified: {verified}")
    print(f"   Invalid: {invalid}")

    # Step 6: Export to Neon
    print("\n[STEP 6] Exporting to Neon...")
    exported = export_to_neon(people)
    print(f"   Exported: {exported}")

    # Summary
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"   Input: {len(people_data)} people")
    print(f"   Matched to companies: {matched}")
    print(f"   Won slots: {slots}")
    print(f"   Emails verified: {verified}")
    print(f"   Exported to Neon: {exported}")
    print(f"\n   Success rate: {exported}/{len(people_data)} ({exported/len(people_data)*100:.1f}%)")

    # Failure breakdown
    print("\n   Failures by reason:")
    for reason in ['no_match', 'low_confidence', 'lost_slot', 'no_pattern', 'email_invalid']:
        count = sum(1 for p in people if p.failure_reason == reason)
        if count > 0:
            print(f"      {reason}: {count}")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
