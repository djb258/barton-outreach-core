#!/usr/bin/env python3
"""
WV HR & Benefits Pipeline Intake
================================
Hub-and-Spoke pipeline with slot-based architecture.

Company Hub Source: c:/Users/CUSTOM PC/Desktop/WV Companies Clay - Deduplicated.csv
People Source: c:/Users/CUSTOM PC/Desktop/WV HR and Benefits.csv

Company Hub Stats:
  - Unique Companies: 1,283
  - With Domain: 965
  - Without Domain: 318

Slot Structure (per company):
  - CEO Slot (1)
  - CFO Slot (1)
  - HR Slot (1) - filled from HR people CSV
  - Benefits Slot (1, optional) - filled if dedicated benefits person exists

Pipeline Flow:
  1. Load Company Hub (1,283 companies with 4 slots each)
  2. Load HR/Benefits people (720 people)
  3. Fuzzy match people to companies
  4. Assign best person to each slot (CHRO > VP > Director > Manager)
  5. Output: Companies with filled slots ready for email generation

Created: 2024-12-10
Updated: 2024-12-11 - Added slot-based architecture and fuzzy matching
"""

import csv
import json
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum

# Try to import rapidfuzz for fuzzy matching
try:
    from rapidfuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    print("WARNING: rapidfuzz not installed. Fuzzy matching will use exact match only.")

# Output paths
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "wv_hr_benefits"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Source files
COMPANY_HUB_CSV = Path("c:/Users/CUSTOM PC/Desktop/WV Companies Clay - Deduplicated.csv")
PEOPLE_CSV = Path("c:/Users/CUSTOM PC/Desktop/WV HR and Benefits.csv")

# Fuzzy match thresholds
FUZZY_MATCH_THRESHOLD = 80  # Minimum score to auto-match
FUZZY_REVIEW_THRESHOLD = 70  # Scores between 70-79 go to review queue


class ReviewReason(Enum):
    """Why a person is in the review queue"""
    NO_MATCH = "no_match"                    # No company match found (score < 70)
    LOW_CONFIDENCE = "low_confidence"        # Match found but score 70-79
    LOST_SLOT = "lost_slot"                  # Matched but another person won the slot
    NO_DOMAIN = "no_domain"                  # Company matched but has no domain


class SlotType(Enum):
    CEO = "ceo"
    CFO = "cfo"
    HR = "hr"
    BENEFITS = "benefits"


class TitleSeniority(Enum):
    """HR title seniority for slot assignment priority"""
    CHRO = "chro"           # Priority 1 - Chief HR Officer
    VP = "vp"               # Priority 2 - VP of HR
    DIRECTOR = "director"   # Priority 3 - HR Director
    MANAGER = "manager"     # Priority 4 - HR Manager
    HRBP = "hrbp"           # Priority 5 - HR Business Partner
    GENERALIST = "generalist"
    SPECIALIST = "specialist"
    BENEFITS = "benefits"   # Goes to Benefits slot, not HR
    COORDINATOR = "coordinator"
    INTERN = "intern"
    OTHER = "other"


# Priority order for HR slot assignment (lower = higher priority)
HR_SLOT_PRIORITY = {
    TitleSeniority.CHRO: 1,
    TitleSeniority.VP: 2,
    TitleSeniority.DIRECTOR: 3,
    TitleSeniority.MANAGER: 4,
    TitleSeniority.HRBP: 5,
    TitleSeniority.GENERALIST: 6,
    TitleSeniority.SPECIALIST: 7,
    TitleSeniority.COORDINATOR: 8,
    TitleSeniority.OTHER: 9,
    TitleSeniority.INTERN: 10,
}


@dataclass
class Slot:
    """A slot within a company"""
    slot_type: str
    filled: bool = False
    person_id: Optional[str] = None
    person_name: Optional[str] = None
    person_title: Optional[str] = None
    person_seniority: Optional[str] = None
    person_linkedin: Optional[str] = None


@dataclass
class CompanyRecord:
    """Company Hub record with slots"""
    company_id: str
    company_name: str
    domain: Optional[str]
    industry: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    status: str = "pending"
    email_pattern: Optional[str] = None
    pattern_confidence: float = 0.0

    # Slots
    ceo_slot: Optional[Dict] = None
    cfo_slot: Optional[Dict] = None
    hr_slot: Optional[Dict] = None
    benefits_slot: Optional[Dict] = None

    # Metadata
    source: str = "clay_export"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now

        # Initialize empty slots
        if self.ceo_slot is None:
            self.ceo_slot = asdict(Slot(slot_type="ceo"))
        if self.cfo_slot is None:
            self.cfo_slot = asdict(Slot(slot_type="cfo"))
        if self.hr_slot is None:
            self.hr_slot = asdict(Slot(slot_type="hr"))
        if self.benefits_slot is None:
            self.benefits_slot = asdict(Slot(slot_type="benefits"))


@dataclass
class PersonRecord:
    """People Node record"""
    person_id: str
    company_id: Optional[str]  # Linked after fuzzy match
    company_name_raw: str  # Original company name from CSV
    first_name: str
    last_name: str
    full_name: str
    job_title: str
    title_seniority: str
    location: str
    linkedin_url: Optional[str]
    email: Optional[str] = None
    email_verified: bool = False
    email_confidence: float = 0.0

    # Fuzzy match results
    fuzzy_matched: bool = False
    fuzzy_score: float = 0.0
    fuzzy_matched_company: Optional[str] = None

    # Slot assignment
    slot_assigned: Optional[str] = None  # "hr" or "benefits"

    # Review queue tracking
    in_review_queue: bool = False
    review_reason: Optional[str] = None  # ReviewReason value
    review_notes: Optional[str] = None   # Additional context

    status: str = "pending"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now


@dataclass
class PipelineProgress:
    """Track overall pipeline progress"""
    run_id: str
    source_file: str
    started_at: str

    # Company Hub metrics
    total_companies: int = 0
    companies_with_domain: int = 0
    companies_with_pattern: int = 0

    # People metrics
    total_people: int = 0
    people_fuzzy_matched: int = 0
    people_unmatched: int = 0

    # Slot metrics
    hr_slots_filled: int = 0
    benefits_slots_filled: int = 0
    total_slots_filled: int = 0

    # Status
    current_phase: str = "intake"
    status: str = "running"
    errors: List[str] = field(default_factory=list)


def generate_company_id(company_name: str, domain: Optional[str]) -> str:
    """Generate deterministic company ID"""
    key = f"{company_name.lower().strip()}|{(domain or '').lower().strip()}"
    hash_val = hashlib.md5(key.encode()).hexdigest()[:12]
    return f"CO-WV-{hash_val.upper()}"


def generate_person_id(full_name: str, company_name: str, linkedin_url: Optional[str]) -> str:
    """Generate deterministic person ID"""
    key = f"{full_name.lower().strip()}|{company_name.lower().strip()}|{(linkedin_url or '').lower().strip()}"
    hash_val = hashlib.md5(key.encode()).hexdigest()[:12]
    return f"PE-WV-{hash_val.upper()}"


def classify_title_seniority(job_title: str) -> TitleSeniority:
    """Classify job title into seniority bucket"""
    title_lower = job_title.lower()

    # CHRO level
    if any(x in title_lower for x in ['chro', 'chief human', 'chief people', 'chief hr',
                                       'head of human resources', 'head of hr', 'head of people']):
        return TitleSeniority.CHRO

    # VP level
    elif any(x in title_lower for x in ['vp ', 'vp,', 'vice president', 'v.p.']):
        return TitleSeniority.VP

    # Director level
    elif 'director' in title_lower:
        return TitleSeniority.DIRECTOR

    # Manager level (but not "case manager" etc)
    elif 'manager' in title_lower and 'human' in title_lower or 'hr' in title_lower or 'people' in title_lower:
        return TitleSeniority.MANAGER
    elif 'hr manager' in title_lower or 'human resources manager' in title_lower:
        return TitleSeniority.MANAGER

    # HRBP
    elif 'business partner' in title_lower or 'hrbp' in title_lower:
        return TitleSeniority.HRBP

    # Benefits (separate slot)
    elif 'benefits' in title_lower and 'specialist' not in title_lower:
        return TitleSeniority.BENEFITS

    # Generalist
    elif 'generalist' in title_lower:
        return TitleSeniority.GENERALIST

    # Specialist
    elif 'specialist' in title_lower:
        return TitleSeniority.SPECIALIST

    # Coordinator/Assistant
    elif 'assistant' in title_lower or 'coordinator' in title_lower:
        return TitleSeniority.COORDINATOR

    # Intern
    elif 'intern' in title_lower or 'student' in title_lower:
        return TitleSeniority.INTERN

    # Check for general HR indicators
    elif any(x in title_lower for x in ['human resources', 'hr ', ' hr', 'hr/']):
        # Could be HR role, classify as OTHER for now
        return TitleSeniority.OTHER

    else:
        return TitleSeniority.OTHER


def load_company_hub() -> Dict[str, CompanyRecord]:
    """Load the deduplicated Company Hub (1,283 companies)"""
    print(f"\n📂 Loading Company Hub: {COMPANY_HUB_CSV}")

    companies: Dict[str, CompanyRecord] = {}

    with open(COMPANY_HUB_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            company_name = row.get('Name', '').strip()
            if not company_name:
                continue

            domain = row.get('Domain', '').strip() or None
            company_id = generate_company_id(company_name, domain)

            companies[company_id] = CompanyRecord(
                company_id=company_id,
                company_name=company_name,
                domain=domain,
                industry=row.get('Primary Industry', '').strip() or None,
                size=row.get('Size', '').strip() or None,
                location=row.get('Location', '').strip() or None,
                linkedin_url=row.get('LinkedIn URL', '').strip() or None,
                status="pending"
            )

    with_domain = sum(1 for c in companies.values() if c.domain)

    print(f"   ✅ Loaded {len(companies)} companies")
    print(f"   📊 With domain: {with_domain}")
    print(f"   📊 Without domain: {len(companies) - with_domain}")
    print(f"   📊 Total slots available: {len(companies) * 4}")

    return companies


def load_people() -> List[PersonRecord]:
    """Load HR/Benefits people from CSV"""
    print(f"\n📂 Loading People: {PEOPLE_CSV}")

    people: List[PersonRecord] = []

    with open(PEOPLE_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            company_name = row.get('Company Name', '').strip()
            if not company_name:
                continue

            full_name = row.get('Full Name', '').strip()
            first_name = row.get('First Name', '').strip()
            last_name = row.get('Last Name', '').strip()
            job_title = row.get('Job Title', '').strip()

            person_id = generate_person_id(full_name, company_name, row.get('LinkedIn Profile'))
            seniority = classify_title_seniority(job_title)

            people.append(PersonRecord(
                person_id=person_id,
                company_id=None,  # Will be set after fuzzy match
                company_name_raw=company_name,
                first_name=first_name,
                last_name=last_name,
                full_name=full_name,
                job_title=job_title,
                title_seniority=seniority.value,
                location=row.get('Location', '').strip(),
                linkedin_url=row.get('LinkedIn Profile', '').strip() or None,
                status="pending"
            ))

    # Count seniorities
    seniority_counts = {}
    for p in people:
        s = p.title_seniority
        seniority_counts[s] = seniority_counts.get(s, 0) + 1

    print(f"   ✅ Loaded {len(people)} people")
    print(f"   📊 Seniority breakdown:")
    for s, count in sorted(seniority_counts.items(), key=lambda x: -x[1]):
        print(f"      {s.upper()}: {count}")

    return people


def fuzzy_match_people_to_companies(
    people: List[PersonRecord],
    companies: Dict[str, CompanyRecord]
) -> Tuple[List[PersonRecord], int, int, int, int]:
    """
    Fuzzy match people to companies in the Company Hub.

    Match categories:
    - Exact match (100%) -> auto-match
    - High confidence (80-99%) -> auto-match
    - Low confidence (70-79%) -> match but flag for review
    - No match (<70%) -> review queue

    Returns: (updated_people, exact_count, fuzzy_count, low_conf_count, no_match_count)
    """
    print(f"\n🔍 Fuzzy Matching People to Company Hub")
    print("=" * 55)

    # Build lookup structures
    company_names = {c.company_name: c.company_id for c in companies.values()}
    company_domains = {c.domain.lower(): c.company_id for c in companies.values() if c.domain}
    company_name_list = list(company_names.keys())

    exact_match = 0
    fuzzy_match = 0
    low_confidence = 0
    no_match = 0

    for person in people:
        raw_name = person.company_name_raw

        # Try exact match first
        if raw_name in company_names:
            person.company_id = company_names[raw_name]
            person.fuzzy_matched = True
            person.fuzzy_score = 100.0
            person.fuzzy_matched_company = raw_name
            exact_match += 1
            continue

        # Try fuzzy match if rapidfuzz available
        if FUZZY_AVAILABLE:
            result = process.extractOne(
                raw_name,
                company_name_list,
                scorer=fuzz.token_sort_ratio
            )

            if result:
                matched_name = result[0]
                score = result[1]

                if score >= FUZZY_MATCH_THRESHOLD:
                    # High confidence match (80%+)
                    person.company_id = company_names[matched_name]
                    person.fuzzy_matched = True
                    person.fuzzy_score = score
                    person.fuzzy_matched_company = matched_name
                    fuzzy_match += 1
                    continue

                elif score >= FUZZY_REVIEW_THRESHOLD:
                    # Low confidence match (70-79%) - match but flag for review
                    person.company_id = company_names[matched_name]
                    person.fuzzy_matched = True
                    person.fuzzy_score = score
                    person.fuzzy_matched_company = matched_name
                    person.in_review_queue = True
                    person.review_reason = ReviewReason.LOW_CONFIDENCE.value
                    person.review_notes = f"Best match: {matched_name} ({score:.0f}%)"
                    low_confidence += 1
                    continue

        # No match found (<70%)
        person.fuzzy_matched = False
        person.in_review_queue = True
        person.review_reason = ReviewReason.NO_MATCH.value

        # Store best match attempt for manual review
        if FUZZY_AVAILABLE:
            result = process.extractOne(raw_name, company_name_list, scorer=fuzz.token_sort_ratio)
            if result:
                person.review_notes = f"Best candidate: {result[0]} ({result[1]:.0f}%)"
        no_match += 1

    total_matched = exact_match + fuzzy_match + low_confidence
    print(f"   ✅ Exact Match (100%): {exact_match}")
    print(f"   ✅ Fuzzy Match (80-99%): {fuzzy_match}")
    print(f"   ⚠️  Low Confidence (70-79%): {low_confidence} (matched but flagged)")
    print(f"   ❌ No Match (<70%): {no_match}")
    print(f"   📊 Total Matched: {total_matched} ({total_matched * 100 // len(people)}%)")

    return people, exact_match, fuzzy_match, low_confidence, no_match


def assign_slots(
    people: List[PersonRecord],
    companies: Dict[str, CompanyRecord]
) -> Tuple[Dict[str, CompanyRecord], int, int, int]:
    """
    Assign best person to each company's HR and Benefits slots.

    HR Slot: Best HR person (CHRO > VP > Director > Manager > HRBP > etc)
    Benefits Slot: Best Benefits person

    People who match but don't win a slot go to review queue with LOST_SLOT reason.

    Returns: (updated_companies, hr_slots_filled, benefits_slots_filled, lost_slot_count)
    """
    print(f"\n🎯 Assigning People to Slots")
    print("=" * 55)

    # Group matched people by company
    people_by_company: Dict[str, List[PersonRecord]] = {}
    for person in people:
        if person.company_id and person.fuzzy_matched:
            if person.company_id not in people_by_company:
                people_by_company[person.company_id] = []
            people_by_company[person.company_id].append(person)

    hr_filled = 0
    benefits_filled = 0
    lost_slot = 0

    for company_id, company_people in people_by_company.items():
        if company_id not in companies:
            continue

        company = companies[company_id]

        # Separate HR candidates and Benefits candidates
        hr_candidates = []
        benefits_candidates = []

        for person in company_people:
            seniority = TitleSeniority(person.title_seniority)

            if seniority == TitleSeniority.BENEFITS:
                benefits_candidates.append(person)
            else:
                # All other HR-related titles go to HR slot consideration
                hr_candidates.append(person)

        # Assign HR slot (best candidate by priority)
        if hr_candidates:
            # Sort by priority (lower = better)
            hr_candidates.sort(key=lambda p: HR_SLOT_PRIORITY.get(TitleSeniority(p.title_seniority), 99))
            best_hr = hr_candidates[0]

            company.hr_slot = {
                "slot_type": "hr",
                "filled": True,
                "person_id": best_hr.person_id,
                "person_name": best_hr.full_name,
                "person_title": best_hr.job_title,
                "person_seniority": best_hr.title_seniority,
                "person_linkedin": best_hr.linkedin_url
            }
            best_hr.slot_assigned = "hr"
            hr_filled += 1

            # Mark other HR candidates as lost slot competition
            for loser in hr_candidates[1:]:
                if not loser.in_review_queue:  # Don't override existing review reason
                    loser.in_review_queue = True
                    loser.review_reason = ReviewReason.LOST_SLOT.value
                    loser.review_notes = f"Lost HR slot to {best_hr.full_name} ({best_hr.title_seniority})"
                    lost_slot += 1

        # Assign Benefits slot (best candidate)
        if benefits_candidates:
            best_benefits = benefits_candidates[0]  # Just take first for now

            company.benefits_slot = {
                "slot_type": "benefits",
                "filled": True,
                "person_id": best_benefits.person_id,
                "person_name": best_benefits.full_name,
                "person_title": best_benefits.job_title,
                "person_seniority": best_benefits.title_seniority,
                "person_linkedin": best_benefits.linkedin_url
            }
            best_benefits.slot_assigned = "benefits"
            benefits_filled += 1

            # Mark other Benefits candidates as lost slot competition
            for loser in benefits_candidates[1:]:
                if not loser.in_review_queue:
                    loser.in_review_queue = True
                    loser.review_reason = ReviewReason.LOST_SLOT.value
                    loser.review_notes = f"Lost Benefits slot to {best_benefits.full_name}"
                    lost_slot += 1

    print(f"   ✅ HR Slots Filled: {hr_filled} / {len(companies)}")
    print(f"   ✅ Benefits Slots Filled: {benefits_filled} / {len(companies)}")
    print(f"   📊 Total Slots Filled: {hr_filled + benefits_filled}")
    print(f"   📊 Lost Slot Competition: {lost_slot}")
    print(f"   📊 Empty HR Slots: {len(companies) - hr_filled}")

    return companies, hr_filled, benefits_filled, lost_slot


def save_outputs(
    companies: Dict[str, CompanyRecord],
    people: List[PersonRecord],
    progress: PipelineProgress
):
    """Save all outputs"""
    print(f"\n💾 Saving Outputs")
    print("=" * 55)

    # Convert to dicts for JSON
    companies_dict = {cid: asdict(c) for cid, c in companies.items()}
    people_dict = {p.person_id: asdict(p) for p in people}

    # Save companies.json
    with open(OUTPUT_DIR / "companies.json", 'w') as f:
        json.dump(companies_dict, f, indent=2)
    print(f"   ✅ companies.json: {len(companies_dict)} companies")

    # Save people.json
    with open(OUTPUT_DIR / "people.json", 'w') as f:
        json.dump(people_dict, f, indent=2)
    print(f"   ✅ people.json: {len(people_dict)} people")

    # Save companies.csv
    with open(OUTPUT_DIR / "companies.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'company_id', 'company_name', 'domain', 'industry', 'size', 'location',
            'hr_slot_filled', 'hr_person_name', 'hr_person_title',
            'benefits_slot_filled', 'benefits_person_name', 'benefits_person_title'
        ])
        for c in companies.values():
            hr_slot = c.hr_slot or {}
            ben_slot = c.benefits_slot or {}
            writer.writerow([
                c.company_id, c.company_name, c.domain, c.industry, c.size, c.location,
                hr_slot.get('filled', False), hr_slot.get('person_name'), hr_slot.get('person_title'),
                ben_slot.get('filled', False), ben_slot.get('person_name'), ben_slot.get('person_title')
            ])
    print(f"   ✅ companies.csv")

    # Save people.csv
    with open(OUTPUT_DIR / "people.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'person_id', 'full_name', 'job_title', 'title_seniority',
            'company_id', 'company_name_raw', 'fuzzy_matched', 'fuzzy_score',
            'slot_assigned', 'linkedin_url'
        ])
        for p in people:
            writer.writerow([
                p.person_id, p.full_name, p.job_title, p.title_seniority,
                p.company_id, p.company_name_raw, p.fuzzy_matched, p.fuzzy_score,
                p.slot_assigned, p.linkedin_url
            ])
    print(f"   ✅ people.csv")

    # Save slots_to_fill.csv (people with slot assignments ready for email gen)
    slots_to_fill = [p for p in people if p.slot_assigned]
    with open(OUTPUT_DIR / "slots_to_fill.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'person_id', 'full_name', 'job_title', 'title_seniority',
            'company_id', 'slot_type', 'linkedin_url'
        ])
        for p in slots_to_fill:
            writer.writerow([
                p.person_id, p.full_name, p.job_title, p.title_seniority,
                p.company_id, p.slot_assigned, p.linkedin_url
            ])
    print(f"   ✅ slots_to_fill.csv: {len(slots_to_fill)} slots ready for email generation")

    # Save review_queue.csv (categorized by reason)
    review_queue = [p for p in people if p.in_review_queue]
    with open(OUTPUT_DIR / "review_queue.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'person_id', 'full_name', 'job_title', 'company_name_raw',
            'review_reason', 'review_notes', 'fuzzy_score', 'fuzzy_matched_company',
            'company_id', 'linkedin_url'
        ])
        for p in review_queue:
            writer.writerow([
                p.person_id, p.full_name, p.job_title, p.company_name_raw,
                p.review_reason, p.review_notes, p.fuzzy_score, p.fuzzy_matched_company,
                p.company_id, p.linkedin_url
            ])

    # Count by reason
    reason_counts = {}
    for p in review_queue:
        reason = p.review_reason or 'unknown'
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    print(f"   ✅ review_queue.csv: {len(review_queue)} people")
    for reason, count in sorted(reason_counts.items()):
        print(f"      → {reason}: {count}")

    # Save progress.json
    with open(OUTPUT_DIR / "progress.json", 'w') as f:
        json.dump(asdict(progress), f, indent=2)
    print(f"   ✅ progress.json")


def print_dashboard(
    companies: Dict[str, CompanyRecord],
    people: List[PersonRecord],
    progress: PipelineProgress
):
    """Print monitoring dashboard"""

    # Slot stats
    hr_filled = sum(1 for c in companies.values() if c.hr_slot and c.hr_slot.get('filled'))
    benefits_filled = sum(1 for c in companies.values() if c.benefits_slot and c.benefits_slot.get('filled'))

    # Match stats
    matched = sum(1 for p in people if p.fuzzy_matched)
    unmatched = len(people) - matched

    # Seniority breakdown of filled HR slots
    hr_seniority = {}
    for c in companies.values():
        if c.hr_slot and c.hr_slot.get('filled'):
            sen = c.hr_slot.get('person_seniority', 'unknown')
            hr_seniority[sen] = hr_seniority.get(sen, 0) + 1

    # Review queue breakdown
    review_queue = [p for p in people if p.in_review_queue]
    review_by_reason = {}
    for p in review_queue:
        reason = p.review_reason or 'unknown'
        review_by_reason[reason] = review_by_reason.get(reason, 0) + 1

    print("\n")
    print("+" + "=" * 66 + "+")
    print("|" + " WV HR & BENEFITS - INTAKE COMPLETE (SLOT-BASED) ".center(66) + "|")
    print("+" + "=" * 66 + "+")

    print("|" + " COMPANY HUB ".center(66, "-") + "|")
    print("|" + f"   Total Companies: {len(companies)}".ljust(66) + "|")
    print("|" + f"   With Domain: {sum(1 for c in companies.values() if c.domain)}".ljust(66) + "|")
    print("|" + f"   CEO Slots: {len(companies)} (empty - not in this dataset)".ljust(66) + "|")
    print("|" + f"   CFO Slots: {len(companies)} (empty - not in this dataset)".ljust(66) + "|")
    print("|" + f"   HR Slots: {hr_filled} filled / {len(companies)} total".ljust(66) + "|")
    print("|" + f"   Benefits Slots: {benefits_filled} filled / {len(companies)} total".ljust(66) + "|")

    print("+" + "-" * 66 + "+")
    print("|" + " PEOPLE MATCHING ".center(66, "-") + "|")
    print("|" + f"   Total People: {len(people)}".ljust(66) + "|")
    print("|" + f"   Fuzzy Matched: {matched} ({matched * 100 // len(people)}%)".ljust(66) + "|")
    print("|" + f"   Unmatched: {unmatched}".ljust(66) + "|")

    print("+" + "-" * 66 + "+")
    print("|" + " REVIEW QUEUE ".center(66, "-") + "|")
    print("|" + f"   Total in Review: {len(review_queue)}".ljust(66) + "|")
    for reason, count in sorted(review_by_reason.items()):
        label = reason.upper().replace('_', ' ')
        print("|" + f"   → {label}: {count}".ljust(66) + "|")

    print("+" + "-" * 66 + "+")
    print("|" + " HR SLOT SENIORITY BREAKDOWN ".center(66, "-") + "|")
    for sen, count in sorted(hr_seniority.items(), key=lambda x: -x[1]):
        print("|" + f"   {sen.upper()}: {count}".ljust(66) + "|")

    print("+" + "-" * 66 + "+")
    print("|" + " READY FOR EMAIL GENERATION ".center(66, "-") + "|")
    slots_ready = hr_filled + benefits_filled
    assigned = sum(1 for p in people if p.slot_assigned)
    print("|" + f"   Slots to Fill: {slots_ready}".ljust(66) + "|")
    print("|" + f"   People with Slots: {assigned}".ljust(66) + "|")
    print("|" + f"   API Calls Needed: {assigned} (not {len(people)})".ljust(66) + "|")
    print("|" + f"   API Calls Saved: {len(people) - assigned}".ljust(66) + "|")

    print("+" + "=" * 66 + "+")


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print(" WV HR & BENEFITS PIPELINE INTAKE ".center(70))
    print(" Hub-and-Spoke with Slot-Based Architecture ".center(70))
    print("=" * 70)

    run_id = f"WV-HR-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    progress = PipelineProgress(
        run_id=run_id,
        source_file=str(COMPANY_HUB_CSV),
        started_at=datetime.now(timezone.utc).isoformat()
    )

    # Phase 1: Load Company Hub
    companies = load_company_hub()
    progress.total_companies = len(companies)
    progress.companies_with_domain = sum(1 for c in companies.values() if c.domain)

    # Phase 2: Load People
    people = load_people()
    progress.total_people = len(people)

    # Phase 3: Fuzzy Match (returns 5 values now)
    people, exact_match, fuzzy_match, low_conf, no_match = fuzzy_match_people_to_companies(people, companies)
    progress.people_fuzzy_matched = exact_match + fuzzy_match + low_conf  # All matched (even low conf)
    progress.people_unmatched = no_match

    # Phase 4: Assign Slots (returns 4 values now)
    companies, hr_filled, benefits_filled, lost_slot = assign_slots(people, companies)
    progress.hr_slots_filled = hr_filled
    progress.benefits_slots_filled = benefits_filled
    progress.total_slots_filled = hr_filled + benefits_filled

    # Update progress
    progress.current_phase = "complete"
    progress.status = "ready_for_email_generation"

    # Save outputs
    save_outputs(companies, people, progress)

    # Dashboard
    print_dashboard(companies, people, progress)

    # Summary
    review_count = sum(1 for p in people if p.in_review_queue)
    slots_assigned = sum(1 for p in people if p.slot_assigned)

    print("\n✅ Pipeline intake complete!")
    print(f"   Output directory: {OUTPUT_DIR}")
    print(f"   Slots ready for email generation: {slots_assigned}")
    print(f"   People in review queue: {review_count}")

    return companies, people, progress


if __name__ == "__main__":
    main()
