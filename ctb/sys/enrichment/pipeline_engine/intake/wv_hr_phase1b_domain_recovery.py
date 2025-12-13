#!/usr/bin/env python3
"""
WV HR & Benefits - Phase 1.5: Domain Recovery
==============================================
Recovers no-match and low-confidence matches using domain-based matching.

Strategy:
1. For NO_MATCH people: Try to guess company domain from name and match
2. For LOW_CONFIDENCE people: If domains align, auto-promote to high confidence

Domain Guessing Rules:
- "Company Name Inc" → companyname.com
- "The Company" → company.com
- "Company & Associates" → company.com
- Common TLDs: .com, .org, .edu, .net, .gov

Created: 2024-12-11
"""

import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Paths
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "wv_hr_benefits"
COMPANIES_FILE = OUTPUT_DIR / "companies.json"
PEOPLE_FILE = OUTPUT_DIR / "people.json"
REVIEW_QUEUE_FILE = OUTPUT_DIR / "review_queue.csv"


# Common company suffixes to strip
COMPANY_SUFFIXES = [
    r'\s+inc\.?$', r'\s+llc\.?$', r'\s+llp\.?$', r'\s+corp\.?$',
    r'\s+corporation$', r'\s+company$', r'\s+co\.?$', r'\s+ltd\.?$',
    r'\s+limited$', r'\s+pllc\.?$', r'\s+pc\.?$', r'\s+plc\.?$',
    r'\s+associates?$', r'\s+partners?$', r'\s+group$', r'\s+holdings?$',
    r'\s+enterprises?$', r'\s+services?$', r'\s+solutions?$',
    r'\s+international$', r'\s+industries$', r'\s+worldwide$',
    r',?\s*inc\.?$', r',?\s*llc\.?$'
]

# Common prefixes to strip
COMPANY_PREFIXES = [
    r'^the\s+',
]

# Common TLDs to try
TLDS = ['.com', '.org', '.net', '.edu', '.gov', '.us', '.io']

# Known domain mappings for common company name patterns
# These are companies where the domain doesn't match the name directly
# ORDER MATTERS - more specific patterns should come first
KNOWN_DOMAIN_MAPPINGS = [
    # WVU Medicine entities (must come before generic WVU)
    ('wvu medicine', 'wvumedicine.org'),
    ('wvumedicine', 'wvumedicine.org'),

    # Marshall entities
    ('marshall university', 'marshall.edu'),
    ('marshall health', 'marshall.edu'),

    # Generic WVU (catch-all after specific WVU Medicine)
    ('west virginia university', 'wvu.edu'),
    ('wvu ', 'wvu.edu'),  # Note: space to avoid matching wvumedicine

    # Non-profits
    ('goodwill industries', 'goodwill.org'),
    ('goodwill', 'goodwill.org'),
    ('united way', 'unitedway.org'),
    ('american red cross', 'redcross.org'),
    ('red cross', 'redcross.org'),
    ('ymca', 'ymca.org'),
    ('salvation army', 'salvationarmy.org'),
]

# Domain bases to EXCLUDE from matching (too generic, cause false positives)
EXCLUDED_DOMAIN_BASES = {
    'state', 'city', 'health', 'care', 'medical', 'first', 'united',
    'west', 'east', 'north', 'south', 'american', 'national', 'general',
    'community', 'regional', 'valley', 'mountain', 'river', 'service',
    'services', 'group', 'center', 'company', 'systems', 'network'
}


def normalize_company_name(name: str) -> str:
    """Normalize company name for domain guessing"""
    name = name.lower().strip()

    # Remove prefixes
    for prefix in COMPANY_PREFIXES:
        name = re.sub(prefix, '', name, flags=re.IGNORECASE)

    # Remove suffixes
    for suffix in COMPANY_SUFFIXES:
        name = re.sub(suffix, '', name, flags=re.IGNORECASE)

    # Remove special characters, keep alphanumeric
    name = re.sub(r'[^a-z0-9\s]', '', name)

    # Remove extra spaces
    name = re.sub(r'\s+', '', name)

    return name.strip()


def guess_domains(company_name: str) -> List[str]:
    """Generate possible domain guesses for a company name"""
    base = normalize_company_name(company_name)
    if not base:
        return []

    domains = []

    # Try each TLD
    for tld in TLDS:
        domains.append(f"{base}{tld}")

    # Try with hyphens if multi-word
    words = company_name.lower().split()
    if len(words) > 1:
        # First two words hyphenated
        hyphenated = '-'.join(words[:2])
        hyphenated = re.sub(r'[^a-z0-9\-]', '', hyphenated)
        for tld in TLDS[:3]:  # Just .com, .org, .net
            domains.append(f"{hyphenated}{tld}")

    # Try acronym for long names
    if len(words) >= 3:
        acronym = ''.join(w[0] for w in words if w and w[0].isalpha())
        if len(acronym) >= 2:
            for tld in TLDS[:2]:
                domains.append(f"{acronym}{tld}")

    return list(dict.fromkeys(domains))  # Remove duplicates, preserve order


def build_domain_index(companies: Dict) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Build reverse lookups:
    1. domain -> company_id (exact domain match)
    2. domain_base -> company_id (e.g., "wesbanco" -> company_id for fuzzy matching)
    """
    domain_to_company = {}
    domain_base_to_company = {}

    for company_id, company in companies.items():
        domain = company.get('domain')
        if domain:
            # Normalize domain (lowercase, strip www.)
            domain = domain.lower().strip()
            if domain.startswith('www.'):
                domain = domain[4:]
            domain_to_company[domain] = company_id

            # Extract domain base (e.g., "wesbanco" from "wesbanco.com")
            domain_base = domain.split('.')[0]
            if len(domain_base) >= 3:  # Only meaningful bases
                domain_base_to_company[domain_base] = company_id

    return domain_to_company, domain_base_to_company


def extract_domain_from_url(url: str) -> Optional[str]:
    """Extract domain from a URL (like LinkedIn company page)"""
    if not url:
        return None

    # This would require scraping LinkedIn - placeholder for now
    # In production, you'd call an API or scraper here
    return None


def recover_by_domain(
    people: Dict,
    companies: Dict,
    domain_index: Dict[str, str],
    domain_base_index: Dict[str, str]
) -> Tuple[int, int, int]:
    """
    Attempt to recover no-match people using domain guessing.

    Strategies:
    1. Direct domain guess (companyname.com)
    2. Known domain mappings (goodwill -> goodwill.org)
    3. Domain base matching (company name contains domain base like "wesbanco")

    Returns: (recovered_count, promoted_count, still_unmatched_count)
    """
    recovered = 0
    promoted = 0
    still_unmatched = 0

    for person_id, person in people.items():
        review_reason = person.get('review_reason')

        if review_reason == 'no_match':
            company_name_raw = person.get('company_name_raw', '')
            company_name_lower = company_name_raw.lower()
            matched = False

            # Strategy 1: Check known domain mappings first (order matters!)
            for known_name, known_domain in KNOWN_DOMAIN_MAPPINGS:
                if known_name in company_name_lower:
                    if known_domain in domain_index:
                        company_id = domain_index[known_domain]
                        company = companies.get(company_id, {})

                        person['company_id'] = company_id
                        person['fuzzy_matched'] = True
                        person['fuzzy_score'] = 98.0  # Known mapping is very high confidence
                        person['fuzzy_matched_company'] = company.get('company_name')
                        person['in_review_queue'] = False
                        person['review_reason'] = None
                        person['review_notes'] = f"KNOWN_MAPPING: {known_domain}"
                        person['recovery_method'] = 'known_mapping'

                        recovered += 1
                        matched = True
                        break

            if matched:
                continue

            # Strategy 2: Direct domain guess
            guessed_domains = guess_domains(company_name_raw)
            for domain in guessed_domains:
                if domain in domain_index:
                    company_id = domain_index[domain]
                    company = companies.get(company_id, {})

                    person['company_id'] = company_id
                    person['fuzzy_matched'] = True
                    person['fuzzy_score'] = 95.0
                    person['fuzzy_matched_company'] = company.get('company_name')
                    person['in_review_queue'] = False
                    person['review_reason'] = None
                    person['review_notes'] = f"DOMAIN_RECOVERED: {domain}"
                    person['recovery_method'] = 'domain_guess'

                    recovered += 1
                    matched = True
                    break

            if matched:
                continue

            # Strategy 3: Check if company name contains any domain base
            # e.g., "WesBanco Bank" contains "wesbanco" which matches wesbanco.com
            company_name_normalized = normalize_company_name(company_name_raw)
            for domain_base, company_id in domain_base_index.items():
                # Skip generic domain bases that cause false positives
                if domain_base in EXCLUDED_DOMAIN_BASES:
                    continue

                # Check if domain base is contained in company name
                # Require at least 6 chars to avoid false positives
                if len(domain_base) >= 6 and domain_base in company_name_normalized:
                    company = companies.get(company_id, {})

                    person['company_id'] = company_id
                    person['fuzzy_matched'] = True
                    person['fuzzy_score'] = 90.0  # Slightly lower confidence
                    person['fuzzy_matched_company'] = company.get('company_name')
                    person['in_review_queue'] = False
                    person['review_reason'] = None
                    person['review_notes'] = f"DOMAIN_BASE_MATCH: {domain_base}"
                    person['recovery_method'] = 'domain_base_match'

                    recovered += 1
                    matched = True
                    break

            if not matched:
                still_unmatched += 1

        elif review_reason == 'low_confidence':
            # Check if the matched company's domain aligns with guessed domain
            company_id = person.get('company_id')
            if company_id:
                company = companies.get(company_id, {})
                company_domain = (company.get('domain') or '').lower()

                if company_domain:
                    company_name_raw = person.get('company_name_raw', '')
                    guessed_domains = guess_domains(company_name_raw)

                    # Also check domain base match
                    company_domain_base = company_domain.split('.')[0]
                    company_name_normalized = normalize_company_name(company_name_raw)

                    # Check if company domain matches any guessed domain OR domain base matches
                    domain_aligns = (
                        company_domain in guessed_domains or
                        any(company_domain.replace('www.', '') in d for d in guessed_domains) or
                        (len(company_domain_base) >= 5 and company_domain_base in company_name_normalized)
                    )

                    if domain_aligns:
                        person['fuzzy_score'] = 95.0
                        person['in_review_queue'] = False
                        person['review_reason'] = None
                        person['review_notes'] = f"DOMAIN_VERIFIED: {company_domain}"
                        person['recovery_method'] = 'domain_verification'
                        promoted += 1
                    else:
                        person['review_notes'] = (
                            f"{person.get('review_notes', '')} | "
                            f"Domain mismatch: expected {guessed_domains[:3]}, got {company_domain}"
                        )

    return recovered, promoted, still_unmatched


def reassign_slots(people: Dict, companies: Dict) -> Tuple[int, int]:
    """
    Re-run slot assignment for recovered people.

    Returns: (new_hr_slots, new_benefits_slots)
    """
    from wv_hr_benefits_intake import (
        TitleSeniority, HR_SLOT_PRIORITY, ReviewReason
    )

    # Find recovered people who now have company matches
    recovered_people = [
        p for p in people.values()
        if p.get('recovery_method') and p.get('company_id') and not p.get('slot_assigned')
    ]

    new_hr_slots = 0
    new_benefits_slots = 0

    # Group by company
    by_company: Dict[str, List] = {}
    for person in recovered_people:
        company_id = person['company_id']
        if company_id not in by_company:
            by_company[company_id] = []
        by_company[company_id].append(person)

    for company_id, company_people in by_company.items():
        if company_id not in companies:
            continue

        company = companies[company_id]
        hr_slot = company.get('hr_slot', {})
        benefits_slot = company.get('benefits_slot', {})

        # Check if slots are already filled
        hr_filled = hr_slot.get('filled', False)
        benefits_filled = benefits_slot.get('filled', False)

        # Separate HR and Benefits candidates
        hr_candidates = []
        benefits_candidates = []

        for person in company_people:
            seniority_str = person.get('title_seniority', 'other')
            try:
                seniority = TitleSeniority(seniority_str)
            except ValueError:
                seniority = TitleSeniority.OTHER

            if seniority == TitleSeniority.BENEFITS:
                benefits_candidates.append(person)
            else:
                hr_candidates.append(person)

        # Fill HR slot if empty
        if not hr_filled and hr_candidates:
            hr_candidates.sort(
                key=lambda p: HR_SLOT_PRIORITY.get(
                    TitleSeniority(p.get('title_seniority', 'other')), 99
                )
            )
            best_hr = hr_candidates[0]

            company['hr_slot'] = {
                "slot_type": "hr",
                "filled": True,
                "person_id": best_hr.get('person_id'),
                "person_name": best_hr.get('full_name'),
                "person_title": best_hr.get('job_title'),
                "person_seniority": best_hr.get('title_seniority'),
                "person_linkedin": best_hr.get('linkedin_url')
            }
            best_hr['slot_assigned'] = 'hr'
            new_hr_slots += 1

            # Mark others as lost slot
            for loser in hr_candidates[1:]:
                loser['in_review_queue'] = True
                loser['review_reason'] = ReviewReason.LOST_SLOT.value
                loser['review_notes'] = f"Lost HR slot to {best_hr.get('full_name')}"

        # Fill Benefits slot if empty
        if not benefits_filled and benefits_candidates:
            best_benefits = benefits_candidates[0]

            company['benefits_slot'] = {
                "slot_type": "benefits",
                "filled": True,
                "person_id": best_benefits.get('person_id'),
                "person_name": best_benefits.get('full_name'),
                "person_title": best_benefits.get('job_title'),
                "person_seniority": best_benefits.get('title_seniority'),
                "person_linkedin": best_benefits.get('linkedin_url')
            }
            best_benefits['slot_assigned'] = 'benefits'
            new_benefits_slots += 1

    return new_hr_slots, new_benefits_slots


def save_outputs(companies: Dict, people: Dict):
    """Save updated files"""
    print("\n💾 Saving Updated Files")
    print("=" * 55)

    # Save updated JSON files
    with open(COMPANIES_FILE, 'w') as f:
        json.dump(companies, f, indent=2)
    print(f"   ✅ companies.json")

    with open(PEOPLE_FILE, 'w') as f:
        json.dump(people, f, indent=2)
    print(f"   ✅ people.json")

    # Update review queue CSV
    review_people = [p for p in people.values() if p.get('in_review_queue')]
    with open(REVIEW_QUEUE_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'person_id', 'full_name', 'job_title', 'company_name_raw',
            'review_reason', 'review_notes', 'fuzzy_score', 'fuzzy_matched_company',
            'company_id', 'linkedin_url'
        ])
        for p in review_people:
            writer.writerow([
                p.get('person_id'), p.get('full_name'), p.get('job_title'),
                p.get('company_name_raw'), p.get('review_reason'), p.get('review_notes'),
                p.get('fuzzy_score', 0), p.get('fuzzy_matched_company'),
                p.get('company_id'), p.get('linkedin_url')
            ])
    print(f"   ✅ review_queue.csv: {len(review_people)} people")

    # Update slots_to_fill.csv
    slots_to_fill = [p for p in people.values() if p.get('slot_assigned')]
    with open(OUTPUT_DIR / "slots_to_fill.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'person_id', 'full_name', 'job_title', 'title_seniority',
            'company_id', 'slot_type', 'linkedin_url', 'recovery_method'
        ])
        for p in slots_to_fill:
            writer.writerow([
                p.get('person_id'), p.get('full_name'), p.get('job_title'),
                p.get('title_seniority'), p.get('company_id'), p.get('slot_assigned'),
                p.get('linkedin_url'), p.get('recovery_method', 'original')
            ])
    print(f"   ✅ slots_to_fill.csv: {len(slots_to_fill)} slots")

    # Save domain recovery report
    recovered = [p for p in people.values() if p.get('recovery_method')]
    with open(OUTPUT_DIR / "domain_recovery_report.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'person_id', 'full_name', 'company_name_raw', 'recovery_method',
            'matched_company', 'matched_domain', 'slot_assigned'
        ])
        for p in recovered:
            company_id = p.get('company_id')
            writer.writerow([
                p.get('person_id'), p.get('full_name'), p.get('company_name_raw'),
                p.get('recovery_method'), p.get('fuzzy_matched_company'),
                p.get('review_notes', '').replace('DOMAIN_RECOVERED: ', '').replace('DOMAIN_VERIFIED: ', ''),
                p.get('slot_assigned', '')
            ])
    print(f"   ✅ domain_recovery_report.csv: {len(recovered)} recovered")


def print_dashboard(
    companies: Dict,
    people: Dict,
    recovered: int,
    promoted: int,
    still_unmatched: int,
    new_hr_slots: int,
    new_benefits_slots: int
):
    """Print recovery dashboard"""
    # Current stats
    total_people = len(people)
    total_matched = sum(1 for p in people.values() if p.get('fuzzy_matched'))
    total_in_review = sum(1 for p in people.values() if p.get('in_review_queue'))
    total_with_slots = sum(1 for p in people.values() if p.get('slot_assigned'))

    # Review breakdown
    review_by_reason = {}
    for p in people.values():
        if p.get('in_review_queue'):
            reason = p.get('review_reason', 'unknown')
            review_by_reason[reason] = review_by_reason.get(reason, 0) + 1

    print("\n")
    print("+" + "=" * 66 + "+")
    print("|" + " PHASE 1.5: DOMAIN RECOVERY COMPLETE ".center(66) + "|")
    print("+" + "=" * 66 + "+")

    print("|" + " RECOVERY RESULTS ".center(66, "-") + "|")
    print("|" + f"   Recovered (domain guess): {recovered}".ljust(66) + "|")
    print("|" + f"   Promoted (domain verified): {promoted}".ljust(66) + "|")
    print("|" + f"   Still Unmatched: {still_unmatched}".ljust(66) + "|")

    print("+" + "-" * 66 + "+")
    print("|" + " NEW SLOT ASSIGNMENTS ".center(66, "-") + "|")
    print("|" + f"   New HR Slots: {new_hr_slots}".ljust(66) + "|")
    print("|" + f"   New Benefits Slots: {new_benefits_slots}".ljust(66) + "|")

    print("+" + "-" * 66 + "+")
    print("|" + " UPDATED TOTALS ".center(66, "-") + "|")
    print("|" + f"   Total People: {total_people}".ljust(66) + "|")
    print("|" + f"   Total Matched: {total_matched} ({total_matched * 100 // total_people}%)".ljust(66) + "|")
    print("|" + f"   Total With Slots: {total_with_slots}".ljust(66) + "|")
    print("|" + f"   Total In Review: {total_in_review}".ljust(66) + "|")

    print("+" + "-" * 66 + "+")
    print("|" + " REVIEW QUEUE BREAKDOWN ".center(66, "-") + "|")
    for reason, count in sorted(review_by_reason.items()):
        label = reason.upper().replace('_', ' ')
        print("|" + f"   → {label}: {count}".ljust(66) + "|")

    print("+" + "=" * 66 + "+")


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print(" PHASE 1.5: DOMAIN RECOVERY ".center(70))
    print(" Recovering no-match people via domain guessing ".center(70))
    print("=" * 70)

    # Load current data
    print("\n📂 Loading Current Data")
    print("=" * 55)

    with open(COMPANIES_FILE, 'r') as f:
        companies = json.load(f)
    print(f"   Loaded: {len(companies)} companies")

    with open(PEOPLE_FILE, 'r') as f:
        people = json.load(f)
    print(f"   Loaded: {len(people)} people")

    # Pre-recovery stats
    pre_matched = sum(1 for p in people.values() if p.get('fuzzy_matched'))
    pre_review = sum(1 for p in people.values() if p.get('in_review_queue'))
    pre_slots = sum(1 for p in people.values() if p.get('slot_assigned'))

    print(f"\n   Pre-recovery stats:")
    print(f"   - Matched: {pre_matched}")
    print(f"   - In Review: {pre_review}")
    print(f"   - With Slots: {pre_slots}")

    # Build domain index
    print("\n🔍 Building Domain Index")
    print("=" * 55)
    domain_index, domain_base_index = build_domain_index(companies)
    print(f"   Indexed: {len(domain_index)} domains")
    print(f"   Domain bases: {len(domain_base_index)}")

    # Run domain recovery
    print("\n🔧 Running Domain Recovery")
    print("=" * 55)
    recovered, promoted, still_unmatched = recover_by_domain(people, companies, domain_index, domain_base_index)
    print(f"   Recovered via domain guess: {recovered}")
    print(f"   Promoted via domain verification: {promoted}")
    print(f"   Still unmatched: {still_unmatched}")

    # Re-run slot assignment for recovered people
    print("\n🎯 Re-assigning Slots for Recovered People")
    print("=" * 55)
    new_hr_slots, new_benefits_slots = reassign_slots(people, companies)
    print(f"   New HR slots filled: {new_hr_slots}")
    print(f"   New Benefits slots filled: {new_benefits_slots}")

    # Save outputs
    save_outputs(companies, people)

    # Dashboard
    print_dashboard(
        companies, people,
        recovered, promoted, still_unmatched,
        new_hr_slots, new_benefits_slots
    )

    # Summary
    post_slots = sum(1 for p in people.values() if p.get('slot_assigned'))
    print(f"\n✅ Domain Recovery Complete!")
    print(f"   Slots before: {pre_slots}")
    print(f"   Slots after: {post_slots}")
    print(f"   Net gain: +{post_slots - pre_slots}")

    return companies, people


if __name__ == "__main__":
    main()
