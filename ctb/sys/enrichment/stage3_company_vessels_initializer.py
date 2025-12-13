#!/usr/bin/env python3
"""
Stage 3 Company Vessels Initializer
====================================
Finalizes the Company Hub by installing all internal vessels
before People Hub is introduced.
"""

import os
import sys
import re
import json
import time
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
WORK_DIR = r"C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core"
OUTPUT_DIR = os.path.join(WORK_DIR, "ctb", "sys", "enrichment", "output")
LOGS_DIR = os.path.join(OUTPUT_DIR, "logs")

SCRAPERAPI_KEY = os.environ.get('SCRAPERAPI_KEY', '')
SCRAPERAPI_URL = 'http://api.scraperapi.com'

BATCH_SIZE = 200
BATCH_SLEEP = 1.25

# Regex patterns
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")

# Email pattern inference
EMAIL_PATTERNS = [
    'first.last',
    'flast',
    'firstlast',
    'f.last',
    'last.first',
    'lastf',
    'first',
    'last',
    'unknown'
]

# Phone categorization keywords
PHONE_CATEGORIES = {
    'hr': ['hr', 'human resources', 'benefits', 'employee'],
    'benefits': ['benefit', 'erisa', '401k', 'retirement', 'insurance'],
    'sales': ['sales', 'contact sales', 'buy', 'pricing'],
    'support': ['support', 'help', 'customer service', 'assistance'],
    'main': ['main', 'general', 'office', 'headquarters', 'contact us']
}

# Slot vessels to initialize
SLOT_VESSELS = [
    'slot_ceo',
    'slot_cfo',
    'slot_chro',
    'slot_hr_manager',
    'slot_benefits_lead',
    'slot_payroll_admin',
    'slot_controller',
    'slot_operations_head',
    'slot_it_admin',
    'slot_office_manager',
    'slot_founder'
]

# BIT engine vessels
BIT_VESSELS = [
    'bit_renewal_signal',
    'bit_talentflow_signal',
    'bit_advisor_signal',
    'bit_carrier_signal',
    'bit_compliance_signal',
    'bit_growth_signal',
    'bit_risk_signal'
]

# Ensure directories exist
os.makedirs(LOGS_DIR, exist_ok=True)


def scrape_url(url):
    """Scrape URL using ScraperAPI."""
    if not url or pd.isna(url):
        return None

    if not str(url).startswith('http'):
        url = f"https://{url}"

    params = {
        'api_key': SCRAPERAPI_KEY,
        'url': url,
        'render': 'false'
    }

    try:
        response = requests.get(SCRAPERAPI_URL, params=params, timeout=30)
        if response.status_code == 200:
            return response.text
        return None
    except Exception:
        return None


def scrape_direct(url):
    """Direct scrape fallback."""
    if not url or pd.isna(url):
        return None

    if not str(url).startswith('http'):
        url = f"https://{url}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if response.status_code == 200:
            return response.text
        return None
    except Exception:
        return None


def get_page_content(url):
    """Get page content with ScraperAPI fallback to direct."""
    if SCRAPERAPI_KEY:
        content = scrape_url(url)
        if content:
            return content
    return scrape_direct(url)


def extract_emails(html):
    """Extract all email addresses from HTML."""
    if not html:
        return []
    emails = EMAIL_PATTERN.findall(html)
    # Filter out common false positives
    filtered = []
    for email in emails:
        email_lower = email.lower()
        if not any(x in email_lower for x in ['example.com', 'domain.com', 'email.com', 'test.com', 'sample.com', '.png', '.jpg', '.gif']):
            filtered.append(email.lower())
    return list(set(filtered))


def infer_email_pattern(emails, domain):
    """Infer email pattern from collected emails."""
    if not emails or not domain:
        return 'unknown', 0.0

    domain_emails = [e for e in emails if domain.lower() in e.lower()]
    if not domain_emails:
        return 'unknown', 0.0

    patterns_found = {}

    for email in domain_emails:
        local_part = email.split('@')[0].lower()

        if '.' in local_part:
            parts = local_part.split('.')
            if len(parts) == 2:
                if len(parts[0]) == 1:
                    patterns_found['f.last'] = patterns_found.get('f.last', 0) + 1
                elif len(parts[1]) == 1:
                    patterns_found['first.l'] = patterns_found.get('first.l', 0) + 1
                else:
                    if len(parts[0]) > 2 and len(parts[1]) > 2:
                        patterns_found['first.last'] = patterns_found.get('first.last', 0) + 1
                    else:
                        patterns_found['last.first'] = patterns_found.get('last.first', 0) + 1
        elif len(local_part) <= 3:
            patterns_found['unknown'] = patterns_found.get('unknown', 0) + 1
        elif local_part[1:].isalpha() and len(local_part) > 4:
            if local_part[0].isalpha():
                patterns_found['flast'] = patterns_found.get('flast', 0) + 1
        elif local_part[:-1].isalpha() and len(local_part) > 4:
            patterns_found['lastf'] = patterns_found.get('lastf', 0) + 1
        else:
            patterns_found['firstlast'] = patterns_found.get('firstlast', 0) + 1

    if not patterns_found:
        return 'unknown', 0.0

    best_pattern = max(patterns_found, key=patterns_found.get)
    total = sum(patterns_found.values())
    confidence = patterns_found[best_pattern] / total if total > 0 else 0.0

    return best_pattern, round(confidence, 2)


def extract_phones(html):
    """Extract all phone numbers from HTML."""
    if not html:
        return []
    phones = PHONE_PATTERN.findall(html)
    # Normalize phone numbers
    normalized = []
    for phone in phones:
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            formatted = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            normalized.append(formatted)
    return list(set(normalized))


def categorize_phone(phone, context_html):
    """Categorize phone number based on surrounding context."""
    if not context_html:
        return 'main'

    context_lower = context_html.lower()
    phone_idx = context_lower.find(re.sub(r'\D', '', phone)[:6])

    if phone_idx == -1:
        return 'main'

    # Get surrounding text (200 chars before and after)
    start = max(0, phone_idx - 200)
    end = min(len(context_lower), phone_idx + 200)
    surrounding = context_lower[start:end]

    for category, keywords in PHONE_CATEGORIES.items():
        if category == 'main':
            continue
        for keyword in keywords:
            if keyword in surrounding:
                return category

    return 'main'


def scrape_company_pages(base_url):
    """Scrape multiple pages for a company."""
    if not base_url or pd.isna(base_url):
        return {}

    if not str(base_url).startswith('http'):
        base_url = f"https://{base_url}"

    base_url = base_url.rstrip('/')

    pages = {
        'homepage': base_url,
        'contact': f"{base_url}/contact",
        'about': f"{base_url}/about",
        'privacy': f"{base_url}/privacy",
        'team': f"{base_url}/team"
    }

    results = {}
    for page_type, url in pages.items():
        content = get_page_content(url)
        if content:
            results[page_type] = content

    return results


def process_company(row):
    """Process a single company and initialize all vessels."""
    company_id = row.get('company_id', '')
    company_name = row.get('company_name', '')
    domain = row.get('domain', '') or row.get('url', '')
    url = row.get('url', '') or row.get('domain', '')
    ein_cluster = row.get('ein_cluster', '')
    ack_id = row.get('ack_id', '')
    final_score = float(row.get('final_score', 0))
    confidence = row.get('confidence', '') or row.get('confidence_label', '')

    # Initialize result
    result = {
        'company_id': company_id,
        'company_name': company_name,
        'domain': domain,
        'url': url,
        'final_score': final_score,
        'confidence': confidence,

        # Email vessels
        'company_email_pattern': 'unknown',
        'company_email_samples': [],
        'pattern_confidence': 0.0,
        'pattern_last_verified_at': None,

        # Phone vessels
        'company_phone_main': None,
        'company_phone_hr': None,
        'company_phone_benefits': None,
        'company_phone_sales': None,
        'company_phone_support': None,
        'company_phone_other': [],
        'phones_last_verified_at': None,

        # DOL linkage
        'ein_cluster': ein_cluster,
        'ack_id': ack_id,
        'dol_plan_ids': [ack_id] if ack_id and not pd.isna(ack_id) else [],
        'dol_last_verified_at': None,

        # BIT engine vessels
        'bit_score': 0.0,
        'bit_last_updated_at': None,
        'bit_signal_log': [],
        'bit_renewal_signal': None,
        'bit_talentflow_signal': None,
        'bit_advisor_signal': None,
        'bit_carrier_signal': None,
        'bit_compliance_signal': None,
        'bit_growth_signal': None,
        'bit_risk_signal': None,

        # Slot vessels
        'slot_ceo': None,
        'slot_cfo': None,
        'slot_chro': None,
        'slot_hr_manager': None,
        'slot_benefits_lead': None,
        'slot_payroll_admin': None,
        'slot_controller': None,
        'slot_operations_head': None,
        'slot_it_admin': None,
        'slot_office_manager': None,
        'slot_founder': None,
        'slot_board_members': [],
        'slot_last_filled_at': None,
        'slot_last_changed_at': None
    }

    # Scrape company pages
    pages = scrape_company_pages(url)

    if pages:
        now = datetime.now().isoformat()

        # Combine all HTML content
        all_html = '\n'.join(pages.values())

        # Extract emails
        all_emails = extract_emails(all_html)
        if all_emails:
            # Get domain from URL for pattern inference
            url_domain = domain or url
            if url_domain:
                url_domain = url_domain.replace('http://', '').replace('https://', '').split('/')[0]

            pattern, confidence_score = infer_email_pattern(all_emails, url_domain)
            result['company_email_pattern'] = pattern
            result['company_email_samples'] = all_emails[:3]
            result['pattern_confidence'] = confidence_score
            result['pattern_last_verified_at'] = now

        # Extract and categorize phones
        all_phones = extract_phones(all_html)
        if all_phones:
            result['phones_last_verified_at'] = now

            categorized = {
                'main': None,
                'hr': None,
                'benefits': None,
                'sales': None,
                'support': None,
                'other': []
            }

            for phone in all_phones:
                category = categorize_phone(phone, all_html)
                if category in ['main', 'hr', 'benefits', 'sales', 'support']:
                    if categorized[category] is None:
                        categorized[category] = phone
                    else:
                        categorized['other'].append(phone)
                else:
                    categorized['other'].append(phone)

            result['company_phone_main'] = categorized['main']
            result['company_phone_hr'] = categorized['hr']
            result['company_phone_benefits'] = categorized['benefits']
            result['company_phone_sales'] = categorized['sales']
            result['company_phone_support'] = categorized['support']
            result['company_phone_other'] = categorized['other']

    return result


def initialize_vessel_structure(row):
    """Initialize all vessel fields for a company without scraping."""
    company_id = row.get('company_id', '')
    company_name = row.get('company_name', '')
    domain = row.get('domain', '') or row.get('url', '')
    url = row.get('url', '') or row.get('domain', '')
    ein = row.get('best_ein_match', '') or row.get('ein_cluster', '')
    canonical_name = row.get('canonical_name', '') or row.get('best_sponsor_name', '')
    final_score = float(row.get('final_score', 0))
    confidence = row.get('confidence', '') or row.get('confidence_label', '')
    scrape_success = row.get('scrape_success', False)

    # Data from Stage 2 enrichment
    scraped_title = row.get('scraped_title', '') or row.get('title', '')
    scraped_h1 = row.get('scraped_h1', '') or row.get('h1', '')
    title_sim = float(row.get('title_sim', 0) or 0)
    h1_sim = float(row.get('h1_sim', 0) or 0)

    now = datetime.now().isoformat()

    return {
        'company_id': company_id,
        'company_name': company_name,
        'domain': domain,
        'url': url,
        'final_score': final_score,
        'confidence': confidence,

        # DOL linkage vessels
        'dol_ein': ein,
        'dol_sponsor_name': canonical_name,
        'dol_match_score': final_score,
        'dol_plan_ids': [],
        'dol_last_verified_at': now if ein else None,

        # Scraped data from Stage 2
        'scraped_title': scraped_title,
        'scraped_h1': scraped_h1,
        'title_similarity': title_sim,
        'h1_similarity': h1_sim,
        'scrape_success': scrape_success,

        # Email vessels (to be filled by future enrichment)
        'company_email_pattern': 'unknown',
        'company_email_samples': [],
        'pattern_confidence': 0.0,
        'pattern_last_verified_at': None,

        # Phone vessels (to be filled by future enrichment)
        'company_phone_main': None,
        'company_phone_hr': None,
        'company_phone_benefits': None,
        'company_phone_sales': None,
        'company_phone_support': None,
        'company_phone_other': [],
        'phones_last_verified_at': None,

        # BIT engine vessels (initialized empty)
        'bit_score': 0.0,
        'bit_last_updated_at': None,
        'bit_signal_log': [],
        'bit_renewal_signal': None,
        'bit_talentflow_signal': None,
        'bit_advisor_signal': None,
        'bit_carrier_signal': None,
        'bit_compliance_signal': None,
        'bit_growth_signal': None,
        'bit_risk_signal': None,

        # Slot vessels (to be filled by Stage 4 People Hub)
        'slot_ceo': None,
        'slot_cfo': None,
        'slot_chro': None,
        'slot_hr_manager': None,
        'slot_benefits_lead': None,
        'slot_payroll_admin': None,
        'slot_controller': None,
        'slot_operations_head': None,
        'slot_it_admin': None,
        'slot_office_manager': None,
        'slot_founder': None,
        'slot_board_members': [],
        'slot_last_filled_at': None,
        'slot_last_changed_at': None,

        # Metadata
        'initialized_at': now,
        'last_updated_at': now
    }


def run_pipeline():
    """Run the Stage 3 Company Vessels Initializer pipeline."""
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 70, flush=True)
    print("STAGE 3 COMPANY VESSELS INITIALIZER", flush=True)
    print("=" * 70, flush=True)

    log = {
        'started_at': datetime.now().isoformat(),
        'total_companies_processed': 0,
        'number_high_confidence': 0,
        'number_medium_confidence': 0,
        'number_low_confidence_skipped': 0,
        'number_with_dol_match': 0,
        'number_with_scrape': 0,
        'errors': []
    }

    # Load data
    print("\n[1] Loading enriched matches from Stage 2...", flush=True)

    enriched_file = os.path.join(OUTPUT_DIR, "enriched_matches.csv")

    if not os.path.exists(enriched_file):
        print(f"  ERROR: {enriched_file} not found!")
        print("  Please run Stage 2 first.")
        return

    enriched_df = pd.read_csv(enriched_file)
    print(f"  Loaded: {len(enriched_df):,} records", flush=True)

    # Extract domain from URL
    def get_domain(url):
        if pd.isna(url) or not url:
            return None
        url = str(url).replace('http://', '').replace('https://', '')
        return url.split('/')[0]

    enriched_df['domain'] = enriched_df['url'].apply(get_domain)

    # Filter by confidence
    print("\n[2] Analyzing confidence distribution...", flush=True)

    # Handle different column names for confidence
    conf_col = 'confidence' if 'confidence' in enriched_df.columns else 'confidence_label'
    if conf_col not in enriched_df.columns:
        enriched_df['confidence'] = enriched_df['final_score'].apply(
            lambda x: 'HIGH_CONFIDENCE' if x >= 0.75 else ('MEDIUM_CONFIDENCE' if x >= 0.60 else 'LOW_CONFIDENCE')
        )
        conf_col = 'confidence'

    high_df = enriched_df[enriched_df[conf_col] == 'HIGH_CONFIDENCE']
    medium_df = enriched_df[enriched_df[conf_col] == 'MEDIUM_CONFIDENCE']
    low_df = enriched_df[enriched_df[conf_col] == 'LOW_CONFIDENCE']

    log['number_high_confidence'] = len(high_df)
    log['number_medium_confidence'] = len(medium_df)
    log['number_low_confidence_skipped'] = len(low_df)

    print(f"  HIGH_CONFIDENCE: {len(high_df):,}", flush=True)
    print(f"  MEDIUM_CONFIDENCE: {len(medium_df):,}", flush=True)
    print(f"  LOW_CONFIDENCE (skipped): {len(low_df):,}", flush=True)

    # Process HIGH + MEDIUM only
    process_df = pd.concat([high_df, medium_df], ignore_index=True)
    print(f"\n  Total to process: {len(process_df):,} companies", flush=True)

    # Initialize vessels for each company
    print(f"\n[3] Initializing vessel structures...", flush=True)

    all_results = []
    records = process_df.to_dict('records')

    for i, row in enumerate(records):
        try:
            result = initialize_vessel_structure(row)
            all_results.append(result)

            if result.get('dol_ein'):
                log['number_with_dol_match'] += 1
            if result.get('scrape_success'):
                log['number_with_scrape'] += 1

        except Exception as e:
            log['errors'].append({
                'company_id': row.get('company_id', ''),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

        # Progress update every 5000 records
        if (i + 1) % 5000 == 0:
            print(f"    Processed: {i+1:,} / {len(records):,}", flush=True)

    log['total_companies_processed'] = len(all_results)
    print(f"    Completed: {len(all_results):,} companies initialized", flush=True)

    # Save outputs
    print("\n[4] Saving output files...", flush=True)

    # A. company_hub_initialized.csv
    results_df = pd.DataFrame(all_results)

    # Convert list columns to JSON strings for CSV
    list_columns = ['company_email_samples', 'company_phone_other', 'dol_plan_ids',
                    'bit_signal_log', 'slot_board_members']
    for col in list_columns:
        if col in results_df.columns:
            results_df[col] = results_df[col].apply(lambda x: json.dumps(x) if isinstance(x, list) else x)

    csv_file = os.path.join(OUTPUT_DIR, "company_hub_initialized.csv")
    results_df.to_csv(csv_file, index=False)
    print(f"  Saved: {csv_file} ({len(results_df):,} records)", flush=True)

    # B. company_hub_vessels.jsonl
    jsonl_file = os.path.join(OUTPUT_DIR, "company_hub_vessels.jsonl")
    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for result in all_results:
            f.write(json.dumps(result, default=str) + '\n')
    print(f"  Saved: {jsonl_file} ({len(all_results):,} records)", flush=True)

    # C. logs/company_initializer_log.json
    log['completed_at'] = datetime.now().isoformat()
    log_file = os.path.join(LOGS_DIR, "company_initializer_log.json")
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, default=str)
    print(f"  Saved: {log_file}", flush=True)

    # Summary
    print("\n" + "=" * 70, flush=True)
    print("STAGE 3 COMPLETE", flush=True)
    print("=" * 70, flush=True)
    print(f"Total companies initialized: {log['total_companies_processed']:,}", flush=True)
    print(f"  HIGH_CONFIDENCE: {log['number_high_confidence']:,}", flush=True)
    print(f"  MEDIUM_CONFIDENCE: {log['number_medium_confidence']:,}", flush=True)
    print(f"  LOW_CONFIDENCE skipped: {log['number_low_confidence_skipped']:,}", flush=True)
    print(f"  With DOL match: {log['number_with_dol_match']:,}", flush=True)
    print(f"  With scrape data: {log['number_with_scrape']:,}", flush=True)
    print(f"  Errors: {len(log['errors'])}", flush=True)


if __name__ == '__main__':
    run_pipeline()
