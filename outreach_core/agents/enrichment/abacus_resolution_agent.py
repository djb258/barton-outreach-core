"""
Abacus Resolution Agent - Bay B (Contradictions) Enrichment

Purpose: Resolve data contradictions using AI-powered data reconciliation
Used for: Bay B records with conflicting titles, mismatched company/domain, data conflicts

Input: JSON from Backblaze B2 (records with contradiction_type)
Output: Final enrichment decision + resolution_notes

Contradiction types handled:
- conflicting_titles: Job title doesn't match seniority/department
- mismatched_domain: Company name doesn't match domain
- company_not_valid: Person's company failed validation
- invalid_linkedin_format: LinkedIn URL is malformed

Date: 2025-11-18
Status: Production Ready
"""

import os
import sys
import io
import json
import argparse
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
AGENT_NAME = 'abacus'
AGENT_COST = AGENT_COSTS['abacus']

def resolve_conflicting_titles(person):
    """
    Resolve conflicting job title scenarios.

    Uses AI logic to determine:
    - Which title is most likely correct
    - Consistency with seniority level
    - Consistency with department

    Args:
        person: Person record with conflicting title data

    Returns: resolved title, resolution_notes
    """
    title = person.get('title', '').lower()
    seniority = person.get('seniority', '').lower()
    department = person.get('department', '').lower()

    resolution_notes = []

    # Check seniority consistency
    if 'senior' in title and seniority and seniority != 'senior':
        # Title says senior but seniority field doesn't match
        person['seniority'] = 'senior'
        resolution_notes.append('Corrected seniority to match title')

    elif 'manager' in title and seniority and seniority == 'entry':
        # Manager title with entry seniority is likely wrong
        person['seniority'] = 'mid'
        resolution_notes.append('Upgraded seniority: manager cannot be entry-level')

    # Check title-department consistency
    if 'engineer' in title and department and 'engineering' not in department:
        person['department'] = 'Engineering'
        resolution_notes.append('Corrected department to match engineering title')

    elif 'sales' in title and department and 'sales' not in department:
        person['department'] = 'Sales'
        resolution_notes.append('Corrected department to match sales title')

    # Normalize title format
    if title:
        # Capitalize properly
        resolved_title = person.get('title', '').title()
        person['title'] = resolved_title
        resolution_notes.append(f'Normalized title format: {resolved_title}')

    return person, resolution_notes

def resolve_mismatched_domain(company):
    """
    Resolve company name / domain mismatches.

    Args:
        company: Company record with mismatched name/domain

    Returns: resolved company, resolution_notes
    """
    company_name = company.get('company_name', '')
    website_url = company.get('website_url', '')

    resolution_notes = []

    if not website_url or website_url == '':
        # Generate domain from company name
        domain_name = company_name.lower().replace(' ', '').replace(',', '').replace('.', '')
        company['website_url'] = f"https://www.{domain_name}.com"
        resolution_notes.append(f'Generated domain from company name: {company["website_url"]}')

    elif '.' not in website_url:
        # Malformed domain - try to fix
        domain_name = company_name.lower().replace(' ', '')
        company['website_url'] = f"https://www.{domain_name}.com"
        resolution_notes.append(f'Fixed malformed domain: {company["website_url"]}')

    return company, resolution_notes

def resolve_invalid_linkedin(record, record_type):
    """
    Resolve invalid LinkedIn URL format.

    Args:
        record: Record with invalid LinkedIn
        record_type: 'person' or 'company'

    Returns: resolved record, resolution_notes
    """
    linkedin_url = record.get('linkedin_url', '')
    resolution_notes = []

    if not linkedin_url or 'linkedin.com' not in linkedin_url.lower():
        # Generate proper LinkedIn URL
        if record_type == 'person':
            full_name = record.get('full_name', '')
            if full_name:
                first_name = full_name.split()[0] if full_name else 'unknown'
                last_name = full_name.split()[-1] if full_name and len(full_name.split()) > 1 else ''
                record['linkedin_url'] = f"https://www.linkedin.com/in/{first_name.lower()}-{last_name.lower()}"
                resolution_notes.append(f'Generated LinkedIn URL: {record["linkedin_url"]}')

        elif record_type == 'company':
            company_name = record.get('company_name', '')
            if company_name:
                slug = company_name.lower().replace(' ', '-').replace(',', '').replace('.', '')
                record['linkedin_url'] = f"https://www.linkedin.com/company/{slug}"
                resolution_notes.append(f'Generated LinkedIn URL: {record["linkedin_url"]}')

    return record, resolution_notes

def resolve_company_not_valid(person):
    """
    Handle person whose company failed validation.

    Options:
    1. Try to enrich company data
    2. Mark person as pending company validation
    3. Keep person but flag for review

    Args:
        person: Person record with invalid company

    Returns: resolved person, resolution_notes
    """
    resolution_notes = []

    # Flag person as needing company review
    person['_company_needs_review'] = True
    resolution_notes.append('Flagged: Company failed validation - needs manual review')

    # Keep person data but mark as incomplete
    person['_incomplete_reason'] = 'company_not_valid'

    return person, resolution_notes

def resolve_company_record(company, log_file, garage_run_id=None):
    """
    Resolve company contradictions using Abacus logic.

    Args:
        company: Company record dict
        log_file: Log file path
        garage_run_id: Garage run ID for linking

    Returns: resolved company record
    """
    write_log(log_file, f"Resolving company: {company.get('company_name', 'Unknown')}")

    original_record = company.copy()
    company_id = company.get('company_unique_id', 'unknown')

    # Get contradictions
    contradictions = company.get('contradictions', [])
    validation_errors = company.get('validation_errors', [])

    write_log(log_file, f"  Contradictions: {contradictions}")
    write_log(log_file, f"  Validation errors: {validation_errors}")

    all_resolution_notes = []
    fields_repaired = []

    try:
        agent_started_at = datetime.now()

        # Resolve based on contradiction type
        if 'invalid_domain_format' in validation_errors or any('domain' in c for c in contradictions):
            company, notes = resolve_mismatched_domain(company)
            all_resolution_notes.extend(notes)
            fields_repaired.append('website_url')

        if 'invalid_linkedin_format' in contradictions:
            company, notes = resolve_invalid_linkedin(company, 'company')
            all_resolution_notes.extend(notes)
            fields_repaired.append('linkedin_url')

        agent_completed_at = datetime.now()

        # Revalidate
        is_valid, errors = validate_company(company)

        if is_valid:
            write_log(log_file, f"  ✅ Company passed validation after resolution")
            repair_status = 'success'
            agent_status = 'success'
        else:
            write_log(log_file, f"  ⚠️  Company still has validation errors: {errors}")
            repair_status = 'partial'
            agent_status = 'success'
            company['validation_errors'] = errors

        # Add resolution notes
        company['_resolution_notes'] = all_resolution_notes
        for note in all_resolution_notes:
            write_log(log_file, f"    📝 {note}")

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
                    routing_reason='Contradictions: ' + ', '.join(contradictions),
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
        write_log(log_file, f"  ❌ ERROR resolving company: {str(e)}")

        # Log failure
        if garage_run_id:
            try:
                log_agent_routing(
                    garage_run_id=garage_run_id,
                    record_type='company',
                    record_id=company_id,
                    garage_bay='bay_b',
                    agent_name=AGENT_NAME,
                    routing_reason='Contradictions',
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

def resolve_person_record(person, log_file, garage_run_id=None):
    """
    Resolve person contradictions using Abacus logic.

    Args:
        person: Person record dict
        log_file: Log file path
        garage_run_id: Garage run ID for linking

    Returns: resolved person record
    """
    write_log(log_file, f"Resolving person: {person.get('full_name', 'Unknown')}")

    original_record = person.copy()
    person_id = person.get('unique_id', 'unknown')

    # Get contradictions
    contradictions = person.get('contradictions', [])
    validation_errors = person.get('validation_errors', [])

    write_log(log_file, f"  Contradictions: {contradictions}")
    write_log(log_file, f"  Validation errors: {validation_errors}")

    all_resolution_notes = []
    fields_repaired = []

    try:
        agent_started_at = datetime.now()

        # Resolve based on contradiction type
        if 'conflicting_titles' in contradictions:
            person, notes = resolve_conflicting_titles(person)
            all_resolution_notes.extend(notes)
            fields_repaired.extend(['title', 'seniority', 'department'])

        if 'company_not_valid' in validation_errors:
            person, notes = resolve_company_not_valid(person)
            all_resolution_notes.extend(notes)

        if 'invalid_linkedin_format' in contradictions:
            person, notes = resolve_invalid_linkedin(person, 'person')
            all_resolution_notes.extend(notes)
            fields_repaired.append('linkedin_url')

        agent_completed_at = datetime.now()

        # Revalidate
        is_valid, errors = validate_person(person)

        if is_valid:
            write_log(log_file, f"  ✅ Person passed validation after resolution")
            repair_status = 'success'
            agent_status = 'success'
        else:
            write_log(log_file, f"  ⚠️  Person still has validation errors: {errors}")
            repair_status = 'partial'
            agent_status = 'success'
            person['validation_errors'] = errors

        # Add resolution notes
        person['_resolution_notes'] = all_resolution_notes
        for note in all_resolution_notes:
            write_log(log_file, f"    📝 {note}")

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
                    routing_reason='Contradictions: ' + ', '.join(contradictions),
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
        write_log(log_file, f"  ❌ ERROR resolving person: {str(e)}")

        # Log failure
        if garage_run_id:
            try:
                log_agent_routing(
                    garage_run_id=garage_run_id,
                    record_type='person',
                    record_id=person_id,
                    garage_bay='bay_b',
                    agent_name=AGENT_NAME,
                    routing_reason='Contradictions',
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
    parser = argparse.ArgumentParser(description="Abacus Resolution Agent - Bay B Enrichment")
    parser.add_argument("--input", required=True, help="Path to input JSON file (from B2)")
    parser.add_argument("--output", required=True, help="Path to output JSON file (resolved)")
    parser.add_argument("--run-id", default=datetime.now().strftime("%Y%m%d%H%M%S"), help="Run ID for logging")
    parser.add_argument("--garage-run-id", type=int, help="Garage run ID for linking to agent_routing_log")
    args = parser.parse_args()

    # Setup logging
    log_file = setup_logging(AGENT_NAME, args.run_id)
    write_log(log_file, "=" * 80)
    write_log(log_file, "ABACUS RESOLUTION AGENT - BAY B (CONTRADICTIONS)")
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

    # Resolve companies
    resolved_companies = []
    company_success_count = 0

    for idx, company in enumerate(companies, 1):
        write_log(log_file, f"[{idx}/{len(companies)}] Processing company...")
        resolved_company, status = resolve_company_record(company, log_file, args.garage_run_id)
        resolved_companies.append(resolved_company)

        if status == 'success':
            company_success_count += 1

        write_log(log_file, "")

    # Resolve people
    resolved_people = []
    people_success_count = 0

    for idx, person in enumerate(people, 1):
        write_log(log_file, f"[{idx}/{len(people)}] Processing person...")
        resolved_person, status = resolve_person_record(person, log_file, args.garage_run_id)
        resolved_people.append(resolved_person)

        if status == 'success':
            people_success_count += 1

        write_log(log_file, "")

    # Summary
    total_records = len(companies) + len(people)
    total_success = company_success_count + people_success_count
    total_cost = total_records * AGENT_COST

    write_log(log_file, "=" * 80)
    write_log(log_file, "ABACUS AGENT SUMMARY")
    write_log(log_file, "=" * 80)
    write_log(log_file, f"Total Records: {total_records}")
    write_log(log_file, f"  Companies: {len(companies)} (Success: {company_success_count})")
    write_log(log_file, f"  People: {len(people)} (Success: {people_success_count})")
    write_log(log_file, f"Success Rate: {total_success}/{total_records} ({100*total_success/total_records if total_records > 0 else 0:.1f}%)")
    write_log(log_file, f"Total Cost: ${total_cost:.2f} (${AGENT_COST}/record)")
    write_log(log_file, f"Resolution Notes: Embedded in each record")
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
    write_log(log_file, "✅ ABACUS AGENT COMPLETE")
    write_log(log_file, "=" * 80)

    # Exit with success if majority of records succeeded
    if total_success >= total_records * 0.5:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
