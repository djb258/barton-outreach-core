#!/usr/bin/env python3
"""
Stage 4 People Hub Initializer
==============================
Builds the People Hub and attaches people to the Company Hub.
"""

import os
import sys
import re
import json
import time
import hashlib
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import unicodedata

# Configuration
WORK_DIR = r"C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core"
OUTPUT_DIR = os.path.join(WORK_DIR, "ctb", "sys", "enrichment", "output")
LOGS_DIR = os.path.join(OUTPUT_DIR, "logs")

BATCH_SIZE = 150
BATCH_SLEEP = 1.0
MAX_RETRIES = 3
CONCURRENT_WORKERS = 10
REQUEST_TIMEOUT = 15

# Ensure directories exist
os.makedirs(LOGS_DIR, exist_ok=True)

# Role function keywords
ROLE_FUNCTION_KEYWORDS = {
    'HR': ['hr', 'human resources', 'people', 'talent', 'recruiting', 'recruitment', 'workforce', 'employee relations', 'hrbp', 'people ops', 'people operations', 'talent acquisition'],
    'Finance': ['finance', 'financial', 'accounting', 'accountant', 'cfo', 'controller', 'treasury', 'fp&a', 'accounts payable', 'accounts receivable', 'bookkeeper', 'audit'],
    'Benefits': ['benefits', 'compensation', 'comp & ben', 'total rewards', 'erisa', '401k', 'retirement', 'pension', 'health benefits', 'employee benefits'],
    'Payroll': ['payroll', 'payroll manager', 'payroll admin', 'payroll specialist'],
    'Executive': ['ceo', 'chief executive', 'president', 'founder', 'co-founder', 'owner', 'principal', 'managing partner', 'managing director', 'general manager'],
    'Operations': ['operations', 'ops', 'coo', 'chief operating', 'supply chain', 'logistics', 'facilities', 'procurement'],
    'IT': ['it', 'information technology', 'technology', 'cto', 'cio', 'systems', 'network', 'infrastructure', 'devops', 'sysadmin', 'system admin', 'helpdesk'],
    'Admin': ['admin', 'administrative', 'office manager', 'executive assistant', 'office admin', 'receptionist', 'front desk'],
    'Sales': ['sales', 'business development', 'account executive', 'account manager', 'revenue', 'commercial'],
    'Legal': ['legal', 'counsel', 'attorney', 'lawyer', 'compliance', 'regulatory', 'general counsel', 'paralegal'],
    'Marketing': ['marketing', 'brand', 'communications', 'pr', 'public relations', 'content', 'digital marketing', 'cmo']
}

# Seniority keywords
SENIORITY_KEYWORDS = {
    'C-Level': ['chief', 'ceo', 'cfo', 'coo', 'cto', 'cio', 'cmo', 'cpo', 'chro', 'cro', 'cco', 'president', 'founder', 'co-founder', 'owner', 'principal'],
    'VP': ['vp', 'vice president', 'svp', 'senior vice president', 'evp', 'executive vice president', 'avp'],
    'Director': ['director', 'head of', 'head,'],
    'Manager': ['manager', 'mgr', 'lead', 'supervisor', 'team lead', 'group lead'],
    'Specialist': ['specialist', 'analyst', 'consultant', 'advisor', 'associate', 'senior'],
    'Coordinator': ['coordinator', 'administrator', 'admin', 'assistant', 'support'],
    'Staff': ['staff', 'junior', 'entry', 'intern', 'trainee', 'representative', 'rep']
}

# Slot mapping rules
SLOT_MAPPING = {
    'slot_ceo': [('Executive', 'C-Level'), ('Executive', 'VP')],
    'slot_cfo': [('Finance', 'C-Level')],
    'slot_chro': [('HR', 'C-Level')],
    'slot_hr_manager': [('HR', 'VP'), ('HR', 'Director'), ('HR', 'Manager')],
    'slot_benefits_lead': [('Benefits', 'C-Level'), ('Benefits', 'VP'), ('Benefits', 'Director'), ('Benefits', 'Manager'), ('Benefits', 'Specialist')],
    'slot_payroll_admin': [('Payroll', 'C-Level'), ('Payroll', 'VP'), ('Payroll', 'Director'), ('Payroll', 'Manager'), ('Payroll', 'Specialist'), ('Payroll', 'Coordinator')],
    'slot_controller': [('Finance', 'VP'), ('Finance', 'Director')],
    'slot_operations_head': [('Operations', 'C-Level'), ('Operations', 'VP'), ('Operations', 'Director')],
    'slot_it_admin': [('IT', 'C-Level'), ('IT', 'VP'), ('IT', 'Director'), ('IT', 'Manager')],
    'slot_office_manager': [('Admin', 'Manager'), ('Admin', 'Coordinator'), ('Admin', 'Specialist')]
}

# Email patterns
EMAIL_PATTERNS = {
    'first.last': lambda f, l, d: f"{f}.{l}@{d}",
    'flast': lambda f, l, d: f"{f[0]}{l}@{d}" if f else f"{l}@{d}",
    'firstlast': lambda f, l, d: f"{f}{l}@{d}",
    'f.last': lambda f, l, d: f"{f[0]}.{l}@{d}" if f else f"{l}@{d}",
    'last.first': lambda f, l, d: f"{l}.{f}@{d}",
    'lastf': lambda f, l, d: f"{l}{f[0]}@{d}" if f else f"{l}@{d}",
    'first': lambda f, l, d: f"{f}@{d}",
    'last': lambda f, l, d: f"{l}@{d}",
}


def generate_person_id(linkedin_url):
    """Generate SHA256 hash of LinkedIn URL as person_id."""
    if not linkedin_url:
        return hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:16]
    return hashlib.sha256(linkedin_url.encode()).hexdigest()[:16]


def generate_company_hash(company_id):
    """Generate SHA256 hash for talentflow tracking."""
    if not company_id:
        return None
    return hashlib.sha256(str(company_id).encode()).hexdigest()[:16]


def normalize_name(name):
    """Normalize name to ASCII lowercase for email generation."""
    if not name or pd.isna(name):
        return '', ''

    # Remove accents and special characters
    name = unicodedata.normalize('NFKD', str(name))
    name = name.encode('ASCII', 'ignore').decode('ASCII')
    name = re.sub(r'[^a-zA-Z\s]', '', name).strip().lower()

    parts = name.split()
    if len(parts) >= 2:
        return parts[0], parts[-1]
    elif len(parts) == 1:
        return parts[0], ''
    return '', ''


def generate_work_email(person_name, pattern, domain):
    """Generate work email based on company email pattern."""
    if not pattern or pattern == 'unknown' or not domain:
        return None

    first, last = normalize_name(person_name)
    if not first and not last:
        return None

    pattern_func = EMAIL_PATTERNS.get(pattern)
    if not pattern_func:
        return None

    try:
        return pattern_func(first, last, domain)
    except Exception:
        return None


def parse_role_function(title):
    """Parse title to determine role function."""
    if not title or pd.isna(title):
        return 'Unknown'

    title_lower = str(title).lower()

    # Check each function's keywords
    for function, keywords in ROLE_FUNCTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in title_lower:
                return function

    return 'Unknown'


def parse_role_seniority(title):
    """Parse title to determine seniority level."""
    if not title or pd.isna(title):
        return 'Staff'

    title_lower = str(title).lower()

    # Check seniority in order of precedence
    for seniority, keywords in SENIORITY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in title_lower:
                return seniority

    return 'Staff'


def extract_keywords(text):
    """Extract keywords from text for search/matching."""
    if not text or pd.isna(text):
        return []

    # Tokenize and clean
    text = str(text).lower()
    text = re.sub(r'[^a-z\s]', ' ', text)
    words = text.split()

    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours'}

    keywords = [w for w in words if len(w) > 2 and w not in stop_words]
    return list(set(keywords))[:20]


def scrape_linkedin_profile(linkedin_url, retry_count=0):
    """Scrape public LinkedIn profile without login."""
    result = {
        'linkedin_name': None,
        'linkedin_title': None,
        'linkedin_location': None,
        'linkedin_about': None,
        'linkedin_keywords': [],
        'scrape_success': False
    }

    if not linkedin_url or pd.isna(linkedin_url):
        return result

    # Ensure URL is properly formatted
    if not str(linkedin_url).startswith('http'):
        linkedin_url = f"https://{linkedin_url}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        response = requests.get(linkedin_url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Try to extract name
            name_elem = soup.find('h1', class_=re.compile('top-card-layout__title|text-heading-xlarge'))
            if name_elem:
                result['linkedin_name'] = name_elem.get_text(strip=True)

            # Try to extract title/headline
            title_elem = soup.find('div', class_=re.compile('top-card-layout__headline|text-body-medium'))
            if title_elem:
                result['linkedin_title'] = title_elem.get_text(strip=True)

            # Try to extract location
            location_elem = soup.find('div', class_=re.compile('top-card-layout__first-subline|top-card__subline-item'))
            if location_elem:
                result['linkedin_location'] = location_elem.get_text(strip=True)

            # Try to extract about section
            about_elem = soup.find('section', class_=re.compile('summary|about'))
            if about_elem:
                about_text = about_elem.find('p') or about_elem.find('div', class_=re.compile('inline-show-more'))
                if about_text:
                    result['linkedin_about'] = about_text.get_text(strip=True)[:500]

            # Generate keywords from available text
            combined_text = ' '.join(filter(None, [
                result['linkedin_title'],
                result['linkedin_about']
            ]))
            result['linkedin_keywords'] = extract_keywords(combined_text)

            result['scrape_success'] = True

        elif response.status_code == 429 and retry_count < MAX_RETRIES:
            time.sleep(2 ** retry_count)
            return scrape_linkedin_profile(linkedin_url, retry_count + 1)

    except requests.exceptions.Timeout:
        if retry_count < MAX_RETRIES:
            time.sleep(1)
            return scrape_linkedin_profile(linkedin_url, retry_count + 1)
    except Exception:
        pass

    return result


def determine_slot_assignment(role_function, role_seniority):
    """Determine which slot a person should fill based on role."""
    for slot, mappings in SLOT_MAPPING.items():
        for func, sen in mappings:
            if role_function == func and role_seniority == sen:
                return slot
    return None


def process_person(row, company_lookup, company_slots):
    """Process a single person and create People Hub record."""
    linkedin_url = row.get('linkedin_url', '')
    person_name = row.get('person_name', '') or row.get('name', '')
    company_id = row.get('company_id', '')
    title_from_source = row.get('title_from_source', '') or row.get('title', '')

    now = datetime.now().isoformat()
    person_id = generate_person_id(linkedin_url)

    # Get company info
    company_info = company_lookup.get(company_id, {})
    domain = company_info.get('domain', '')
    email_pattern = company_info.get('company_email_pattern', 'unknown')

    # Initialize result
    result = {
        'person_id': person_id,
        'linkedin_url': linkedin_url,
        'linkedin_name': None,
        'person_name_source': person_name,
        'title_raw': title_from_source,
        'linkedin_title': None,
        'linkedin_location': None,
        'linkedin_about': None,
        'linkedin_keywords': [],
        'role_function': 'Unknown',
        'role_seniority': 'Staff',
        'work_email': None,
        'work_phone': None,
        'company_id': company_id,
        'company_name': company_info.get('company_name', ''),
        'domain': domain,
        'slot_assignment': None,
        'slot_collision': False,
        'first_seen_at': now,
        'last_updated_at': now,
        'talentflow_company_hash': generate_company_hash(company_id),
        'talentflow_baseline_title': None,
        'talentflow_baseline_company': company_id,
        'scrape_success': False
    }

    # Scrape LinkedIn profile
    linkedin_data = scrape_linkedin_profile(linkedin_url)
    result.update({
        'linkedin_name': linkedin_data['linkedin_name'],
        'linkedin_title': linkedin_data['linkedin_title'],
        'linkedin_location': linkedin_data['linkedin_location'],
        'linkedin_about': linkedin_data['linkedin_about'],
        'linkedin_keywords': linkedin_data['linkedin_keywords'],
        'scrape_success': linkedin_data['scrape_success']
    })

    # Use scraped title or fall back to source title
    effective_title = linkedin_data['linkedin_title'] or title_from_source
    result['talentflow_baseline_title'] = effective_title

    # Parse role function and seniority
    result['role_function'] = parse_role_function(effective_title)
    result['role_seniority'] = parse_role_seniority(effective_title)

    # Generate work email
    effective_name = linkedin_data['linkedin_name'] or person_name
    result['work_email'] = generate_work_email(effective_name, email_pattern, domain)

    # Determine slot assignment
    slot = determine_slot_assignment(result['role_function'], result['role_seniority'])

    if slot and company_id:
        # Check if slot is already filled
        if company_id not in company_slots:
            company_slots[company_id] = {}

        if slot not in company_slots[company_id] or not company_slots[company_id][slot]:
            company_slots[company_id][slot] = person_id
            result['slot_assignment'] = slot
        else:
            result['slot_collision'] = True

    return result


def safe_process_person(row, company_lookup, company_slots):
    """Wrapper to safely process a person."""
    try:
        return {'success': True, 'result': process_person(row, company_lookup, company_slots)}
    except Exception as e:
        return {
            'success': False,
            'error': str(e)[:100],
            'result': {
                'person_id': generate_person_id(row.get('linkedin_url', '')),
                'linkedin_url': row.get('linkedin_url', ''),
                'person_name_source': row.get('person_name', ''),
                'company_id': row.get('company_id', ''),
                'scrape_success': False,
                'error': str(e)[:100]
            }
        }


def run_pipeline():
    """Run the Stage 4 People Hub Initializer pipeline."""
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 70, flush=True)
    print("STAGE 4 PEOPLE HUB INITIALIZER", flush=True)
    print("=" * 70, flush=True)

    log = {
        'started_at': datetime.now().isoformat(),
        'total_people_processed': 0,
        'successful_scrapes': 0,
        'failed_scrapes': 0,
        'slot_assignments': 0,
        'collisions_detected': 0,
        'emails_generated': 0,
        'pattern_failures': 0,
        'errors': []
    }

    # Load Company Hub
    print("\n[1] Loading Company Hub...", flush=True)

    company_hub_file = os.path.join(OUTPUT_DIR, "company_hub_initialized.csv")

    if not os.path.exists(company_hub_file):
        print(f"  ERROR: {company_hub_file} not found!", flush=True)
        print("  Please run Stage 3 first.", flush=True)
        return

    company_df = pd.read_csv(company_hub_file)
    print(f"  Loaded: {len(company_df):,} companies", flush=True)

    # Create company lookup dictionary
    company_lookup = {}
    for _, row in company_df.iterrows():
        cid = row.get('company_id', '')
        if cid:
            company_lookup[cid] = {
                'company_name': row.get('company_name', ''),
                'domain': row.get('domain', ''),
                'company_email_pattern': row.get('company_email_pattern', 'unknown'),
                'company_email_samples': row.get('company_email_samples', [])
            }

    # Load People Seed
    print("\n[2] Loading People Seed...", flush=True)

    people_seed_file = os.path.join(WORK_DIR, "people_seed.csv")

    if not os.path.exists(people_seed_file):
        # Try alternative locations
        alt_locations = [
            os.path.join(OUTPUT_DIR, "people_seed.csv"),
            os.path.join(WORK_DIR, "data", "people_seed.csv"),
        ]
        for alt in alt_locations:
            if os.path.exists(alt):
                people_seed_file = alt
                break
        else:
            print(f"  ERROR: people_seed.csv not found!", flush=True)
            print(f"  Checked: {people_seed_file}", flush=True)
            print("  Creating empty People Hub structure...", flush=True)

            # Create empty output files
            empty_log = log.copy()
            empty_log['completed_at'] = datetime.now().isoformat()
            empty_log['note'] = 'No people_seed.csv found'

            log_file = os.path.join(LOGS_DIR, "people_initializer_log.json")
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(empty_log, f, indent=2, default=str)
            print(f"  Saved: {log_file}", flush=True)
            return

    people_df = pd.read_csv(people_seed_file)
    print(f"  Loaded: {len(people_df):,} people", flush=True)

    # Normalize column names
    column_mapping = {
        'name': 'person_name',
        'full_name': 'person_name',
        'title': 'title_from_source',
        'job_title': 'title_from_source',
        'linkedin': 'linkedin_url',
        'linkedin_profile': 'linkedin_url',
        'company_unique_id': 'company_id'
    }

    for old_col, new_col in column_mapping.items():
        if old_col in people_df.columns and new_col not in people_df.columns:
            people_df[new_col] = people_df[old_col]

    # Track company slots
    company_slots = {}

    # Process in batches
    print(f"\n[3] Processing {len(people_df):,} people in batches of {BATCH_SIZE}...", flush=True)

    all_results = []
    all_baselines = []
    records = people_df.to_dict('records')
    total_batches = (len(records) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_num in range(total_batches):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, len(records))
        batch = records[start_idx:end_idx]

        print(f"\n  Batch {batch_num + 1}/{total_batches} ({start_idx+1}-{end_idx})...", flush=True)

        batch_success = 0
        batch_slots = 0
        batch_collisions = 0
        batch_emails = 0
        batch_errors = 0

        # Process batch with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
            futures = {
                executor.submit(safe_process_person, row, company_lookup, company_slots): row
                for row in batch
            }

            for future in as_completed(futures):
                result_data = future.result()
                result = result_data['result']
                all_results.append(result)

                if result_data['success']:
                    if result.get('scrape_success'):
                        batch_success += 1
                        log['successful_scrapes'] += 1
                    else:
                        log['failed_scrapes'] += 1

                    if result.get('slot_assignment'):
                        batch_slots += 1
                        log['slot_assignments'] += 1

                    if result.get('slot_collision'):
                        batch_collisions += 1
                        log['collisions_detected'] += 1

                    if result.get('work_email'):
                        batch_emails += 1
                        log['emails_generated'] += 1
                    elif result.get('domain') and not result.get('work_email'):
                        log['pattern_failures'] += 1

                    # Create baseline entry
                    baseline = {
                        'linkedin_url': result.get('linkedin_url'),
                        'person_id': result.get('person_id'),
                        'company_id': result.get('company_id'),
                        'title_initial': result.get('linkedin_title') or result.get('title_raw'),
                        'title_normalized': f"{result.get('role_function', 'Unknown')} / {result.get('role_seniority', 'Staff')}",
                        'baseline_timestamp': result.get('first_seen_at')
                    }
                    all_baselines.append(baseline)
                else:
                    batch_errors += 1
                    log['errors'].append({
                        'linkedin_url': result.get('linkedin_url', ''),
                        'error': result_data.get('error', 'Unknown error'),
                        'timestamp': datetime.now().isoformat()
                    })

        print(f"    Scraped: {batch_success}/{len(batch)}, Slots: {batch_slots}, Collisions: {batch_collisions}, Emails: {batch_emails}", flush=True)

        # Save progress every 10 batches
        if (batch_num + 1) % 10 == 0:
            progress_file = os.path.join(OUTPUT_DIR, "stage4_progress.csv")
            pd.DataFrame(all_results).to_csv(progress_file, index=False)
            print(f"    [Progress saved: {len(all_results):,} records]", flush=True)

        if batch_num < total_batches - 1:
            time.sleep(BATCH_SLEEP)

    log['total_people_processed'] = len(all_results)
    print(f"\n    Completed: {len(all_results):,} people processed", flush=True)

    # Save outputs
    print("\n[4] Saving output files...", flush=True)

    # A. people_hub_initialized.csv
    results_df = pd.DataFrame(all_results)

    # Convert list columns to JSON strings
    list_columns = ['linkedin_keywords']
    for col in list_columns:
        if col in results_df.columns:
            results_df[col] = results_df[col].apply(lambda x: json.dumps(x) if isinstance(x, list) else x)

    csv_file = os.path.join(OUTPUT_DIR, "people_hub_initialized.csv")
    results_df.to_csv(csv_file, index=False)
    print(f"  Saved: {csv_file} ({len(results_df):,} records)", flush=True)

    # B. people_hub.jsonl
    jsonl_file = os.path.join(OUTPUT_DIR, "people_hub.jsonl")
    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for result in all_results:
            f.write(json.dumps(result, default=str) + '\n')
    print(f"  Saved: {jsonl_file} ({len(all_results):,} records)", flush=True)

    # C. people_talentflow_baseline.jsonl
    baseline_file = os.path.join(OUTPUT_DIR, "people_talentflow_baseline.jsonl")
    with open(baseline_file, 'w', encoding='utf-8') as f:
        for baseline in all_baselines:
            f.write(json.dumps(baseline, default=str) + '\n')
    print(f"  Saved: {baseline_file} ({len(all_baselines):,} records)", flush=True)

    # D. logs/people_initializer_log.json
    log['completed_at'] = datetime.now().isoformat()
    log_file = os.path.join(LOGS_DIR, "people_initializer_log.json")
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, default=str)
    print(f"  Saved: {log_file}", flush=True)

    # Summary
    print("\n" + "=" * 70, flush=True)
    print("STAGE 4 COMPLETE", flush=True)
    print("=" * 70, flush=True)
    print(f"Total people processed: {log['total_people_processed']:,}", flush=True)
    print(f"  Successful scrapes: {log['successful_scrapes']:,}", flush=True)
    print(f"  Failed scrapes: {log['failed_scrapes']:,}", flush=True)
    print(f"  Slot assignments: {log['slot_assignments']:,}", flush=True)
    print(f"  Collisions detected: {log['collisions_detected']:,}", flush=True)
    print(f"  Emails generated: {log['emails_generated']:,}", flush=True)
    print(f"  Pattern failures: {log['pattern_failures']:,}", flush=True)
    print(f"  Errors: {len(log['errors'])}", flush=True)


if __name__ == '__main__':
    run_pipeline()
