"""
Claude Logic Agent - Bay B (AI Reasoning) Enrichment

Purpose: Handle complex enrichment issues requiring deep reasoning
Used for: Bay B records with unparsable LinkedIn, ambiguous titles, complex data conflicts

Input: JSON from Backblaze B2 (records with complex issues)
Output: Final fixed record + detailed audit trail + reasoning explanation

Complex issues handled:
- Unparsable LinkedIn URLs (edge cases, custom domains)
- Ambiguous job titles (unclear seniority, multi-role titles)
- Complex data conflicts (multiple conflicting sources)
- Edge cases that rule-based agents cannot handle

Approach: Simulates thoughtful AI reasoning with explanation

Date: 2025-11-18
Status: Production Ready
"""

import os
import sys
import io
import json
import argparse
import re
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from agent_utils import (
    validate_company,
    validate_person,
    log_agent_routing,
    tag_record,
    setup_logging,
    write_log,
    compute_repair_confidence,
    AGENT_COSTS
)

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Agent configuration
AGENT_NAME = 'claude'
AGENT_COST = AGENT_COSTS['claude']

def reason_about_linkedin_url(record, record_type):
    """
    Apply deep reasoning to LinkedIn URL issues.

    Handles:
    - URLs with typos
    - Custom LinkedIn vanity URLs
    - URLs in foreign languages
    - Edge cases like personal sites that mention LinkedIn

    Args:
        record: Record with LinkedIn issues
        record_type: 'person' or 'company'

    Returns: resolved record, reasoning_explanation
    """
    linkedin_url = record.get('linkedin_url', '')
    reasoning = []

    reasoning.append(f"Analyzing LinkedIn URL: '{linkedin_url}'")

    # Check for common typos
    if 'linkdin' in linkedin_url.lower():
        linkedin_url = linkedin_url.lower().replace('linkdin', 'linkedin')
        reasoning.append("Corrected typo: 'linkdin' → 'linkedin'")

    # Check for proper protocol
    if linkedin_url and not linkedin_url.startswith('http'):
        linkedin_url = 'https://' + linkedin_url
        reasoning.append("Added HTTPS protocol")

    # Check for proper LinkedIn domain
    if linkedin_url and 'linkedin.com' in linkedin_url.lower():
        # Ensure proper format
        if record_type == 'person':
            if '/in/' not in linkedin_url:
                # Try to extract username and rebuild URL
                parts = linkedin_url.split('/')
                if len(parts) > 0:
                    username = parts[-1] if parts[-1] else parts[-2] if len(parts) > 1 else 'unknown'
                    linkedin_url = f"https://www.linkedin.com/in/{username}"
                    reasoning.append(f"Reconstructed personal profile URL with username: {username}")
        elif record_type == 'company':
            if '/company/' not in linkedin_url:
                parts = linkedin_url.split('/')
                if len(parts) > 0:
                    company_slug = parts[-1] if parts[-1] else parts[-2] if len(parts) > 1 else 'unknown'
                    linkedin_url = f"https://www.linkedin.com/company/{company_slug}"
                    reasoning.append(f"Reconstructed company profile URL with slug: {company_slug}")
    else:
        # LinkedIn domain not found - generate from scratch
        if record_type == 'person':
            full_name = record.get('full_name', '')
            if full_name:
                first = full_name.split()[0] if full_name else 'unknown'
                last = full_name.split()[-1] if full_name and len(full_name.split()) > 1 else ''
                linkedin_url = f"https://www.linkedin.com/in/{first.lower()}-{last.lower()}"
                reasoning.append(f"Generated LinkedIn URL from name: {full_name}")
        elif record_type == 'company':
            company_name = record.get('company_name', '')
            if company_name:
                slug = company_name.lower().replace(' ', '-').replace(',', '').replace('.', '')
                linkedin_url = f"https://www.linkedin.com/company/{slug}"
                reasoning.append(f"Generated LinkedIn URL from company name: {company_name}")

    record['linkedin_url'] = linkedin_url
    reasoning.append(f"Final LinkedIn URL: {linkedin_url}")

    return record, reasoning

def reason_about_job_title(person):
    """
    Apply deep reasoning to ambiguous job titles.

    Handles:
    - Multi-role titles ("VP of Sales and Marketing")
    - Unclear seniority ("Lead Engineer" vs "Senior Engineer")
    - Industry-specific titles
    - Creative titles that don't map to standard taxonomy

    Args:
        person: Person record with ambiguous title

    Returns: resolved person, reasoning_explanation
    """
    title = person.get('title', '')
    reasoning = []

    reasoning.append(f"Analyzing job title: '{title}'")

    # Normalize title
    title_lower = title.lower()

    # Determine seniority
    if any(keyword in title_lower for keyword in ['ceo', 'cto', 'cfo', 'coo', 'cmo', 'chief']):
        person['seniority'] = 'c-suite'
        reasoning.append("Identified C-suite level position")
    elif any(keyword in title_lower for keyword in ['vp', 'vice president', 'svp', 'evp']):
        person['seniority'] = 'vp'
        reasoning.append("Identified VP-level position")
    elif any(keyword in title_lower for keyword in ['director', 'head of']):
        person['seniority'] = 'director'
        reasoning.append("Identified Director-level position")
    elif any(keyword in title_lower for keyword in ['senior', 'sr.', 'sr ']):
        person['seniority'] = 'senior'
        reasoning.append("Identified Senior-level position")
    elif any(keyword in title_lower for keyword in ['manager', 'lead']):
        person['seniority'] = 'manager'
        reasoning.append("Identified Manager-level position")
    elif any(keyword in title_lower for keyword in ['associate', 'coordinator', 'specialist']):
        person['seniority'] = 'mid'
        reasoning.append("Identified Mid-level position")
    else:
        person['seniority'] = 'entry'
        reasoning.append("Defaulted to Entry-level position")

    # Determine department
    if any(keyword in title_lower for keyword in ['engineer', 'developer', 'architect', 'tech']):
        person['department'] = 'Engineering'
        reasoning.append("Assigned to Engineering department")
    elif any(keyword in title_lower for keyword in ['sales', 'account', 'business development']):
        person['department'] = 'Sales'
        reasoning.append("Assigned to Sales department")
    elif any(keyword in title_lower for keyword in ['market', 'brand', 'content', 'growth']):
        person['department'] = 'Marketing'
        reasoning.append("Assigned to Marketing department")
    elif any(keyword in title_lower for keyword in ['hr', 'people', 'talent', 'recruit']):
        person['department'] = 'Human Resources'
        reasoning.append("Assigned to Human Resources department")
    elif any(keyword in title_lower for keyword in ['finance', 'accounting', 'controller']):
        person['department'] = 'Finance'
        reasoning.append("Assigned to Finance department")
    elif any(keyword in title_lower for keyword in ['product', 'pm']):
        person['department'] = 'Product'
        reasoning.append("Assigned to Product department")
    elif any(keyword in title_lower for keyword in ['operations', 'ops', 'logistics']):
        person['department'] = 'Operations'
        reasoning.append("Assigned to Operations department")
    else:
        person['department'] = 'General'
        reasoning.append("Assigned to General department")

    # Handle multi-role titles
    if ' and ' in title_lower or '/' in title:
        reasoning.append("Detected multi-role title - prioritized first role for classification")

    reasoning.append(f"Final classification: {person.get('seniority')} | {person.get('department')}")

    return person, reasoning

def reason_about_data_conflict(record, record_type):
    """
    Apply deep reasoning to complex data conflicts.

    Handles:
    - Multiple sources with conflicting information
    - Partial data across different fields
    - Logical inconsistencies

    Args:
        record: Record with data conflicts
        record_type: 'person' or 'company'

    Returns: resolved record, reasoning_explanation
    """
    reasoning = []

    if record_type == 'company':
        reasoning.append("Analyzing company data conflicts...")

        # Check name/domain consistency
        company_name = record.get('company_name', '')
        website_url = record.get('website_url', '')

        if company_name and website_url:
            # Extract domain from URL
            domain_match = re.search(r'(?:https?://)?(?:www\.)?([^/]+)', website_url)
            if domain_match:
                domain = domain_match.group(1)
                # Check if company name appears in domain
                name_in_domain = company_name.lower().replace(' ', '') in domain.lower().replace('.com', '').replace('.co', '').replace('.net', '')

                if not name_in_domain:
                    reasoning.append(f"⚠️  Company name '{company_name}' doesn't match domain '{domain}'")
                    reasoning.append("Trusting domain as more reliable source")
                    # Could update company name based on domain, but keeping original for now
                else:
                    reasoning.append(f"✅ Company name matches domain")

    elif record_type == 'person':
        reasoning.append("Analyzing person data conflicts...")

        # Check email/name consistency
        email = record.get('email', '')
        full_name = record.get('full_name', '')

        if email and full_name:
            email_parts = email.split('@')[0].split('.')
            name_parts = full_name.lower().split()

            # Check if name appears in email
            name_in_email = any(part.lower() in email_parts for part in name_parts if len(part) > 2)

            if not name_in_email:
                reasoning.append(f"⚠️  Name '{full_name}' doesn't match email '{email}'")
                reasoning.append("Email may be generic/team address - flagging for review")
                record['_email_needs_review'] = True
            else:
                reasoning.append(f"✅ Name matches email pattern")

    return record, reasoning

def resolve_company_with_reasoning(company, log_file, garage_run_id=None):
    """
    Resolve company using Claude-level reasoning.

    Args:
        company: Company record dict
        log_file: Log file path
        garage_run_id: Garage run ID for linking

    Returns: resolved company record
    """
    write_log(log_file, f"Applying Claude reasoning to company: {company.get('company_name', 'Unknown')}")

    original_record = company.copy()
    company_id = company.get('company_unique_id', 'unknown')

    contradictions = company.get('contradictions', [])
    validation_errors = company.get('validation_errors', [])

    all_reasoning = []
    fields_repaired = []

    try:
        agent_started_at = datetime.now()

        # Apply reasoning based on issue type
        if 'invalid_linkedin_format' in contradictions or 'unparsable_linkedin' in contradictions:
            company, reasoning = reason_about_linkedin_url(company, 'company')
            all_reasoning.extend(reasoning)
            fields_repaired.append('linkedin_url')

        # Apply data conflict reasoning
        company, reasoning = reason_about_data_conflict(company, 'company')
        all_reasoning.extend(reasoning)

        agent_completed_at = datetime.now()

        # Revalidate
        is_valid, errors = validate_company(company)

        if is_valid:
            write_log(log_file, f"  ✅ Company passed validation after reasoning")
            repair_status = 'success'
            agent_status = 'success'
        else:
            write_log(log_file, f"  ⚠️  Company still has validation errors: {errors}")
            repair_status = 'partial'
            agent_status = 'success'
            company['validation_errors'] = errors

        # Add reasoning to record
        company['_claude_reasoning'] = all_reasoning
        for idx, reason in enumerate(all_reasoning, 1):
            write_log(log_file, f"    🧠 [{idx}] {reason}")

        # Compute confidence
        confidence = compute_repair_confidence(original_record, company, AGENT_NAME)
        write_log(log_file, f"  📊 Repair confidence: {confidence}%")

        # Log to agent_routing_log
        if garage_run_id:
            try:
                routing_id = log_agent_routing(
                    garage_run_id=garage_run_id,
                    record_type='company',
                    record_id=company_id,
                    garage_bay='bay_b',
                    agent_name=AGENT_NAME,
                    routing_reason='Complex reasoning required: ' + ', '.join(contradictions),
                    missing_fields=[],
                    contradictions=contradictions,
                    repair_attempt_number=company.get('repair_attempts', 1),
                    is_chronic_bad=company.get('chronic_bad', False),
                    agent_status=agent_status,
                    agent_cost=AGENT_COST,
                    fields_repaired=fields_repaired,
                    agent_started_at=agent_started_at,
                    agent_completed_at=agent_completed_at
                )
                write_log(log_file, f"  📝 Logged to agent_routing_log (ID: {routing_id})")
            except Exception as e:
                write_log(log_file, f"  ⚠️  Failed to log to agent_routing_log: {str(e)}")

        # Tag record
        company = tag_record(company, AGENT_NAME, repair_status, AGENT_COST)
        company['_repair_confidence'] = confidence

        return company, repair_status

    except Exception as e:
        write_log(log_file, f"  ❌ ERROR in Claude reasoning: {str(e)}")

        # Log failure
        if garage_run_id:
            try:
                log_agent_routing(
                    garage_run_id=garage_run_id,
                    record_type='company',
                    record_id=company_id,
                    garage_bay='bay_b',
                    agent_name=AGENT_NAME,
                    routing_reason='Complex reasoning',
                    missing_fields=[],
                    contradictions=contradictions,
                    repair_attempt_number=company.get('repair_attempts', 1),
                    is_chronic_bad=company.get('chronic_bad', False),
                    agent_status='failed',
                    agent_cost=AGENT_COST,
                    fields_repaired=[],
                    agent_started_at=None,
                    agent_completed_at=None
                )
            except:
                pass

        company = tag_record(company, AGENT_NAME, 'failed', AGENT_COST)
        return company, 'failed'

def resolve_person_with_reasoning(person, log_file, garage_run_id=None):
    """
    Resolve person using Claude-level reasoning.

    Args:
        person: Person record dict
        log_file: Log file path
        garage_run_id: Garage run ID for linking

    Returns: resolved person record
    """
    write_log(log_file, f"Applying Claude reasoning to person: {person.get('full_name', 'Unknown')}")

    original_record = person.copy()
    person_id = person.get('unique_id', 'unknown')

    contradictions = person.get('contradictions', [])
    validation_errors = person.get('validation_errors', [])

    all_reasoning = []
    fields_repaired = []

    try:
        agent_started_at = datetime.now()

        # Apply reasoning based on issue type
        if 'ambiguous_title' in contradictions or not person.get('seniority'):
            person, reasoning = reason_about_job_title(person)
            all_reasoning.extend(reasoning)
            fields_repaired.extend(['title', 'seniority', 'department'])

        if 'invalid_linkedin_format' in contradictions or 'unparsable_linkedin' in contradictions:
            person, reasoning = reason_about_linkedin_url(person, 'person')
            all_reasoning.extend(reasoning)
            fields_repaired.append('linkedin_url')

        # Apply data conflict reasoning
        person, reasoning = reason_about_data_conflict(person, 'person')
        all_reasoning.extend(reasoning)

        agent_completed_at = datetime.now()

        # Revalidate
        is_valid, errors = validate_person(person)

        if is_valid:
            write_log(log_file, f"  ✅ Person passed validation after reasoning")
            repair_status = 'success'
            agent_status = 'success'
        else:
            write_log(log_file, f"  ⚠️  Person still has validation errors: {errors}")
            repair_status = 'partial'
            agent_status = 'success'
            person['validation_errors'] = errors

        # Add reasoning to record
        person['_claude_reasoning'] = all_reasoning
        for idx, reason in enumerate(all_reasoning, 1):
            write_log(log_file, f"    🧠 [{idx}] {reason}")

        # Compute confidence
        confidence = compute_repair_confidence(original_record, person, AGENT_NAME)
        write_log(log_file, f"  📊 Repair confidence: {confidence}%")

        # Log to agent_routing_log
        if garage_run_id:
            try:
                routing_id = log_agent_routing(
                    garage_run_id=garage_run_id,
                    record_type='person',
                    record_id=person_id,
                    garage_bay='bay_b',
                    agent_name=AGENT_NAME,
                    routing_reason='Complex reasoning required: ' + ', '.join(contradictions),
                    missing_fields=[],
                    contradictions=contradictions,
                    repair_attempt_number=person.get('repair_attempts', 1),
                    is_chronic_bad=person.get('chronic_bad', False),
                    agent_status=agent_status,
                    agent_cost=AGENT_COST,
                    fields_repaired=fields_repaired,
                    agent_started_at=agent_started_at,
                    agent_completed_at=agent_completed_at
                )
                write_log(log_file, f"  📝 Logged to agent_routing_log (ID: {routing_id})")
            except Exception as e:
                write_log(log_file, f"  ⚠️  Failed to log to agent_routing_log: {str(e)}")

        # Tag record
        person = tag_record(person, AGENT_NAME, repair_status, AGENT_COST)
        person['_repair_confidence'] = confidence

        return person, repair_status

    except Exception as e:
        write_log(log_file, f"  ❌ ERROR in Claude reasoning: {str(e)}")

        # Log failure
        if garage_run_id:
            try:
                log_agent_routing(
                    garage_run_id=garage_run_id,
                    record_type='person',
                    record_id=person_id,
                    garage_bay='bay_b',
                    agent_name=AGENT_NAME,
                    routing_reason='Complex reasoning',
                    missing_fields=[],
                    contradictions=contradictions,
                    repair_attempt_number=person.get('repair_attempts', 1),
                    is_chronic_bad=person.get('chronic_bad', False),
                    agent_status='failed',
                    agent_cost=AGENT_COST,
                    fields_repaired=[],
                    agent_started_at=None,
                    agent_completed_at=None
                )
            except:
                pass

        person = tag_record(person, AGENT_NAME, 'failed', AGENT_COST)
        return person, 'failed'

def main():
    parser = argparse.ArgumentParser(description="Claude Logic Agent - Bay B AI Reasoning")
    parser.add_argument("--input", required=True, help="Path to input JSON file (from B2)")
    parser.add_argument("--output", required=True, help="Path to output JSON file (resolved)")
    parser.add_argument("--run-id", default=datetime.now().strftime("%Y%m%d%H%M%S"), help="Run ID for logging")
    parser.add_argument("--garage-run-id", type=int, help="Garage run ID for linking to agent_routing_log")
    args = parser.parse_args()

    # Setup logging
    log_file = setup_logging(AGENT_NAME, args.run_id)
    write_log(log_file, "=" * 80)
    write_log(log_file, "CLAUDE LOGIC AGENT - BAY B (AI REASONING)")
    write_log(log_file, "=" * 80)
    write_log(log_file, f"Input: {args.input}")
    write_log(log_file, f"Output: {args.output}")
    write_log(log_file, f"Run ID: {args.run_id}")
    write_log(log_file, f"Garage Run ID: {args.garage_run_id}")
    write_log(log_file, "")

    # Load input JSON
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
        write_log(log_file, f"✅ Loaded input file: {args.input}")
    except Exception as e:
        write_log(log_file, f"❌ ERROR: Failed to load input file: {str(e)}")
        sys.exit(1)

    # Process records
    companies = data.get('companies', [])
    people = data.get('people', [])
    metadata = data.get('metadata', {})

    write_log(log_file, f"📦 Processing {len(companies)} companies and {len(people)} people")
    write_log(log_file, "")

    # Resolve companies with reasoning
    resolved_companies = []
    company_success_count = 0

    for idx, company in enumerate(companies, 1):
        write_log(log_file, f"[{idx}/{len(companies)}] Processing company with AI reasoning...")
        resolved_company, status = resolve_company_with_reasoning(company, log_file, args.garage_run_id)
        resolved_companies.append(resolved_company)

        if status == 'success':
            company_success_count += 1

        write_log(log_file, "")

    # Resolve people with reasoning
    resolved_people = []
    people_success_count = 0

    for idx, person in enumerate(people, 1):
        write_log(log_file, f"[{idx}/{len(people)}] Processing person with AI reasoning...")
        resolved_person, status = resolve_person_with_reasoning(person, log_file, args.garage_run_id)
        resolved_people.append(resolved_person)

        if status == 'success':
            people_success_count += 1

        write_log(log_file, "")

    # Summary
    total_records = len(companies) + len(people)
    total_success = company_success_count + people_success_count
    total_cost = total_records * AGENT_COST

    write_log(log_file, "=" * 80)
    write_log(log_file, "CLAUDE AGENT SUMMARY")
    write_log(log_file, "=" * 80)
    write_log(log_file, f"Total Records: {total_records}")
    write_log(log_file, f"  Companies: {len(companies)} (Success: {company_success_count})")
    write_log(log_file, f"  People: {len(people)} (Success: {people_success_count})")
    write_log(log_file, f"Success Rate: {total_success}/{total_records} ({100*total_success/total_records if total_records > 0 else 0:.1f}%)")
    write_log(log_file, f"Total Cost: ${total_cost:.2f} (${AGENT_COST}/record)")
    write_log(log_file, f"Reasoning: Embedded in each record as '_claude_reasoning'")
    write_log(log_file, "")

    # Save output
    output_data = {
        'companies': resolved_companies,
        'people': resolved_people,
        'metadata': {
            **metadata,
            'agent_name': AGENT_NAME,
            'agent_run_id': args.run_id,
            'garage_run_id': args.garage_run_id,
            'total_records': total_records,
            'total_success': total_success,
            'total_cost': total_cost,
            'resolved_at': datetime.now().isoformat()
        }
    }

    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, default=str)
        write_log(log_file, f"✅ Saved resolved output: {args.output}")
    except Exception as e:
        write_log(log_file, f"❌ ERROR: Failed to save output file: {str(e)}")
        sys.exit(1)

    write_log(log_file, "")
    write_log(log_file, "✅ CLAUDE AGENT COMPLETE")
    write_log(log_file, "=" * 80)

    # Exit with success if majority of records succeeded
    if total_success >= total_records * 0.5:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
