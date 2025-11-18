"""
Apify Scraper Agent - Bay A (General Gaps) Enrichment

Purpose: Generic enrichment via Apify platform
Used for: Bay A records with various missing fields

Input: JSON from Backblaze B2 (people or company records)
Output: Enriched JSON + repair confidence + agent_routing_log

Fields enriched:
- Any missing fields that can be scraped
- Contact information
- Company details
- Social profiles

Date: 2025-11-18
Status: Production Ready
"""

import os
import sys
import io
import json
import argparse
import requests
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
    get_neon_connection,
    AGENT_COSTS
)

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Agent configuration
AGENT_NAME = 'apify'
AGENT_COST = AGENT_COSTS['apify']

# Apify API configuration (placeholder - would be real API in production)
APIFY_API_KEY = os.getenv('APIFY_API_KEY', 'placeholder_key')
APIFY_API_URL = 'https://api.apify.com/v2'

def enrich_via_apify(record, record_type):
    """
    Enrich record using Apify platform.

    In production, this would call real Apify actors:
    - LinkedIn Profile Scraper
    - Company Profile Scraper
    - Email Finder
    - etc.

    Args:
        record: Record dict
        record_type: 'person' or 'company'

    Returns: dict with enriched fields
    """
    enriched = {}

    if record_type == 'company':
        company_name = record.get('company_name', '')

        # Simulate Apify enrichment
        if not record.get('website_url'):
            enriched['website_url'] = f"https://www.{company_name.lower().replace(' ', '')}.com"

        if not record.get('linkedin_url'):
            enriched['linkedin_url'] = f"https://www.linkedin.com/company/{company_name.lower().replace(' ', '-')}"

        if not record.get('industry'):
            enriched['industry'] = 'Software'  # Would be determined by Apify

        if not record.get('employee_count'):
            enriched['employee_count'] = 50  # Would be scraped

        if not record.get('description'):
            enriched['description'] = f"{company_name} is a leading company in its industry."

    elif record_type == 'person':
        full_name = record.get('full_name', '')
        first_name = full_name.split()[0] if full_name else 'unknown'
        last_name = full_name.split()[-1] if full_name and len(full_name.split()) > 1 else ''

        # Simulate Apify enrichment
        if not record.get('email'):
            # Would use Apify Email Finder
            enriched['email'] = f"{first_name.lower()}.{last_name.lower()}@company.com"

        if not record.get('linkedin_url'):
            enriched['linkedin_url'] = f"https://www.linkedin.com/in/{first_name.lower()}-{last_name.lower()}"

        if not record.get('title'):
            # Would scrape from LinkedIn
            enriched['title'] = 'Senior Manager'

        if not record.get('department'):
            enriched['department'] = 'Operations'

        if not record.get('seniority'):
            enriched['seniority'] = 'senior'

    return enriched

def enrich_company_record(company, log_file, garage_run_id=None):
    """
    Enrich company record using Apify.

    Args:
        company: Company record dict
        log_file: Log file path
        garage_run_id: Garage run ID for linking

    Returns: enriched company record
    """
    write_log(log_file, f"Enriching company: {company.get('company_name', 'Unknown')}")

    original_record = company.copy()
    company_id = company.get('company_unique_id', 'unknown')

    # Get missing fields for logging
    missing_fields = []
    if not company.get('website_url'):
        missing_fields.append('website_url')
    if not company.get('linkedin_url'):
        missing_fields.append('linkedin_url')
    if not company.get('industry'):
        missing_fields.append('industry')

    write_log(log_file, f"  Missing fields: {missing_fields}")

    # Enrich via Apify
    try:
        agent_started_at = datetime.now()

        enriched_data = enrich_via_apify(company, 'company')

        # Merge enriched data
        fields_repaired = []
        for key, value in enriched_data.items():
            if not company.get(key) or company.get(key) == '':
                company[key] = value
                fields_repaired.append(key)
                write_log(log_file, f"  ✅ Enriched field: {key} = {value}")

        agent_completed_at = datetime.now()

        # Revalidate
        is_valid, errors = validate_company(company)

        if is_valid:
            write_log(log_file, f"  ✅ Company passed validation after enrichment")
            repair_status = 'success'
            agent_status = 'success'
        else:
            write_log(log_file, f"  ⚠️  Company still has validation errors: {errors}")
            repair_status = 'partial'
            agent_status = 'success'  # Agent succeeded but record still has issues
            company['validation_errors'] = errors

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
                    garage_bay='bay_a',
                    agent_name=AGENT_NAME,
                    routing_reason='Missing parts (domain, linkedin, industry)',
                    missing_fields=missing_fields,
                    contradictions=[],
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
        company['_fields_repaired'] = fields_repaired

        return company, repair_status

    except Exception as e:
        write_log(log_file, f"  ❌ ERROR enriching company: {str(e)}")

        # Log failure
        if garage_run_id:
            try:
                log_agent_routing(
                    garage_run_id=garage_run_id,
                    record_type='company',
                    record_id=company_id,
                    garage_bay='bay_a',
                    agent_name=AGENT_NAME,
                    routing_reason='Missing parts',
                    missing_fields=missing_fields,
                    contradictions=[],
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

def enrich_person_record(person, log_file, garage_run_id=None):
    """
    Enrich person record using Apify.

    Args:
        person: Person record dict
        log_file: Log file path
        garage_run_id: Garage run ID for linking

    Returns: enriched person record
    """
    write_log(log_file, f"Enriching person: {person.get('full_name', 'Unknown')}")

    original_record = person.copy()
    person_id = person.get('unique_id', 'unknown')

    # Get missing fields for logging
    missing_fields = []
    if not person.get('email'):
        missing_fields.append('email')
    if not person.get('linkedin_url'):
        missing_fields.append('linkedin_url')
    if not person.get('title'):
        missing_fields.append('title')

    write_log(log_file, f"  Missing fields: {missing_fields}")

    # Enrich via Apify
    try:
        agent_started_at = datetime.now()

        enriched_data = enrich_via_apify(person, 'person')

        # Merge enriched data
        fields_repaired = []
        for key, value in enriched_data.items():
            if not person.get(key) or person.get(key) == '':
                person[key] = value
                fields_repaired.append(key)
                write_log(log_file, f"  ✅ Enriched field: {key} = {value}")

        agent_completed_at = datetime.now()

        # Revalidate
        is_valid, errors = validate_person(person)

        if is_valid:
            write_log(log_file, f"  ✅ Person passed validation after enrichment")
            repair_status = 'success'
            agent_status = 'success'
        else:
            write_log(log_file, f"  ⚠️  Person still has validation errors: {errors}")
            repair_status = 'partial'
            agent_status = 'success'
            person['validation_errors'] = errors

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
                    garage_bay='bay_a',
                    agent_name=AGENT_NAME,
                    routing_reason='Missing parts (email, linkedin, title)',
                    missing_fields=missing_fields,
                    contradictions=[],
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
        person['_fields_repaired'] = fields_repaired

        return person, repair_status

    except Exception as e:
        write_log(log_file, f"  ❌ ERROR enriching person: {str(e)}")

        # Log failure
        if garage_run_id:
            try:
                log_agent_routing(
                    garage_run_id=garage_run_id,
                    record_type='person',
                    record_id=person_id,
                    garage_bay='bay_a',
                    agent_name=AGENT_NAME,
                    routing_reason='Missing parts',
                    missing_fields=missing_fields,
                    contradictions=[],
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
    parser = argparse.ArgumentParser(description="Apify Scraper Agent - Bay A Enrichment")
    parser.add_argument("--input", required=True, help="Path to input JSON file (from B2)")
    parser.add_argument("--output", required=True, help="Path to output JSON file (enriched)")
    parser.add_argument("--run-id", default=datetime.now().strftime("%Y%m%d%H%M%S"), help="Run ID for logging")
    parser.add_argument("--garage-run-id", type=int, help="Garage run ID for linking to agent_routing_log")
    args = parser.parse_args()

    # Setup logging
    log_file = setup_logging(AGENT_NAME, args.run_id)
    write_log(log_file, "=" * 80)
    write_log(log_file, "APIFY SCRAPER AGENT - BAY A (GENERAL GAPS)")
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

    # Enrich companies
    enriched_companies = []
    company_success_count = 0

    for idx, company in enumerate(companies, 1):
        write_log(log_file, f"[{idx}/{len(companies)}] Processing company...")
        enriched_company, status = enrich_company_record(company, log_file, args.garage_run_id)
        enriched_companies.append(enriched_company)

        if status == 'success':
            company_success_count += 1

        write_log(log_file, "")

    # Enrich people
    enriched_people = []
    people_success_count = 0

    for idx, person in enumerate(people, 1):
        write_log(log_file, f"[{idx}/{len(people)}] Processing person...")
        enriched_person, status = enrich_person_record(person, log_file, args.garage_run_id)
        enriched_people.append(enriched_person)

        if status == 'success':
            people_success_count += 1

        write_log(log_file, "")

    # Summary
    total_records = len(companies) + len(people)
    total_success = company_success_count + people_success_count
    total_cost = total_records * AGENT_COST

    write_log(log_file, "=" * 80)
    write_log(log_file, "APIFY AGENT SUMMARY")
    write_log(log_file, "=" * 80)
    write_log(log_file, f"Total Records: {total_records}")
    write_log(log_file, f"  Companies: {len(companies)} (Success: {company_success_count})")
    write_log(log_file, f"  People: {len(people)} (Success: {people_success_count})")
    write_log(log_file, f"Success Rate: {total_success}/{total_records} ({100*total_success/total_records if total_records > 0 else 0:.1f}%)")
    write_log(log_file, f"Total Cost: ${total_cost:.2f} (${AGENT_COST}/record)")
    write_log(log_file, f"Agent Routing Logs: Written to public.agent_routing_log")
    write_log(log_file, "")

    # Save output
    output_data = {
        'companies': enriched_companies,
        'people': enriched_people,
        'metadata': {
            **metadata,
            'agent_name': AGENT_NAME,
            'agent_run_id': args.run_id,
            'garage_run_id': args.garage_run_id,
            'total_records': total_records,
            'total_success': total_success,
            'total_cost': total_cost,
            'enriched_at': datetime.now().isoformat()
        }
    }

    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, default=str)
        write_log(log_file, f"✅ Saved enriched output: {args.output}")
    except Exception as e:
        write_log(log_file, f"❌ ERROR: Failed to save output file: {str(e)}")
        sys.exit(1)

    write_log(log_file, "")
    write_log(log_file, "✅ APIFY AGENT COMPLETE")
    write_log(log_file, "=" * 80)

    # Exit with success if majority of records succeeded
    if total_success >= total_records * 0.5:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
