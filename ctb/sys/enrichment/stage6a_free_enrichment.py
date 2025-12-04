"""
Stage 6A: Free Multi-Source Enrichment Pipeline
================================================
Enriches unresolved low-confidence companies using FREE APIs:

1. DuckDuckGo Instant Answers (free, no key)
2. OpenStreetMap Nominatim (free, 1 req/sec)
3. WHOIS domain lookup (free)
4. Re-analyze existing Firecrawl data with looser thresholds

Input: splink_low_confidence.csv (≈ 6,386 unresolved companies)
Output:
  - free_enrichment_high_confidence.csv (combined score >= 0.85)
  - free_enrichment_medium_confidence.csv (0.70 <= score < 0.85)
  - free_enrichment_low_confidence.csv (score < 0.70, for Clay)
  - free_enrichment_full_dump.jsonl
  - logs/free_enrichment_log.json

Cost: $0
"""

import os
import json
import time
import re
import requests
from urllib.parse import urlparse, quote_plus
import pandas as pd
from datetime import datetime
from rapidfuzz.distance import JaroWinkler
from concurrent.futures import ThreadPoolExecutor, as_completed
import socket
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Force unbuffered output
import functools
print = functools.partial(print, flush=True)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
LOG_DIR = os.path.join(OUTPUT_DIR, 'logs')

INPUT_FILE = os.path.join(OUTPUT_DIR, 'splink_low_confidence.csv')
FIRECRAWL_FAILURES = os.path.join(OUTPUT_DIR, 'firecrawl_failures.csv')

HIGH_CONF_OUTPUT = os.path.join(OUTPUT_DIR, 'free_enrichment_high_confidence.csv')
MEDIUM_CONF_OUTPUT = os.path.join(OUTPUT_DIR, 'free_enrichment_medium_confidence.csv')
LOW_CONF_OUTPUT = os.path.join(OUTPUT_DIR, 'free_enrichment_low_confidence.csv')
FULL_DUMP_OUTPUT = os.path.join(OUTPUT_DIR, 'free_enrichment_full_dump.jsonl')
LOG_FILE = os.path.join(LOG_DIR, 'free_enrichment_log.json')

# Batch settings
BATCH_SIZE = 100
NOMINATIM_DELAY = 1.1  # OSM requires 1 request per second
DDG_DELAY = 0.5
WHOIS_DELAY = 0.3

# Confidence thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.85
MEDIUM_CONFIDENCE_THRESHOLD = 0.70

# User agent for APIs
USER_AGENT = 'BartonOutreachEnrichment/1.0 (contact@svg.agency)'

# Request session with retry
session = requests.Session()
session.headers.update({'User-Agent': USER_AGENT})


def compute_jaro_winkler(s1, s2):
    """Compute Jaro-Winkler similarity between two strings."""
    if not s1 or not s2:
        return 0.0
    return JaroWinkler.normalized_similarity(s1.lower().strip(), s2.lower().strip())


def compute_token_overlap(s1, s2):
    """Compute token overlap ratio between two strings."""
    if not s1 or not s2:
        return 0.0
    # Remove common business suffixes for better matching
    suffixes = ['inc', 'llc', 'corp', 'corporation', 'company', 'co', 'ltd', 'limited', 'llp', 'lp', 'pllc']
    tokens1 = set(w for w in s1.lower().split() if w not in suffixes)
    tokens2 = set(w for w in s2.lower().split() if w not in suffixes)
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    return len(intersection) / len(union) if union else 0.0


def normalize_company_name(name):
    """Normalize company name for matching."""
    if not name:
        return ''
    # Remove common suffixes and punctuation
    name = name.lower()
    suffixes = [', inc.', ', inc', ' inc.', ' inc', ', llc', ' llc', ', corp.', ', corp',
                ' corp.', ' corp', ' corporation', ', ltd.', ', ltd', ' ltd.', ' ltd',
                ' company', ' co.', ' co', ', lp', ' lp', ', llp', ' llp', ' pllc']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    # Remove punctuation
    name = re.sub(r'[^\w\s]', '', name)
    return name.strip()


def extract_domain(url):
    """Extract domain from URL."""
    if not url:
        return None
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        domain = domain.lower().replace('www.', '')
        return domain
    except:
        return None


def verify_domain_exists(domain):
    """Check if domain resolves (DNS lookup)."""
    if not domain:
        return False
    try:
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        return False


def duckduckgo_search(company_name, city, state):
    """Search DuckDuckGo Instant Answers API."""
    try:
        query = f'{company_name} {city} {state}'
        url = f'https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1'

        response = session.get(url, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()

        result = {
            'abstract': data.get('Abstract', ''),
            'abstract_source': data.get('AbstractSource', ''),
            'abstract_url': data.get('AbstractURL', ''),
            'heading': data.get('Heading', ''),
            'image': data.get('Image', ''),
            'infobox': data.get('Infobox', {}),
            'related_topics': [],
            'website': None
        }

        # Extract website from infobox if available
        if result['infobox'] and isinstance(result['infobox'], dict):
            content = result['infobox'].get('content', [])
            for item in content:
                if isinstance(item, dict):
                    label = item.get('label', '').lower()
                    if 'website' in label or 'url' in label:
                        result['website'] = item.get('value')
                        break

        # Get related topics for additional context
        for topic in data.get('RelatedTopics', [])[:5]:
            if isinstance(topic, dict) and topic.get('Text'):
                result['related_topics'].append(topic.get('Text', '')[:200])

        return result

    except Exception as e:
        return {'error': str(e)}


def nominatim_search(company_name, city, state):
    """Search OpenStreetMap Nominatim for business location."""
    try:
        # Try specific business search first
        query = f'{company_name}, {city}, {state}, USA'
        url = f'https://nominatim.openstreetmap.org/search?q={quote_plus(query)}&format=json&addressdetails=1&limit=3'

        response = session.get(url, timeout=10)
        if response.status_code != 200:
            return None

        results = response.json()

        if not results:
            # Fallback to just city/state
            query = f'{city}, {state}, USA'
            url = f'https://nominatim.openstreetmap.org/search?q={quote_plus(query)}&format=json&addressdetails=1&limit=1'
            response = session.get(url, timeout=10)
            results = response.json() if response.status_code == 200 else []

        if results:
            best = results[0]
            address = best.get('address', {})
            return {
                'display_name': best.get('display_name', ''),
                'lat': best.get('lat'),
                'lon': best.get('lon'),
                'type': best.get('type', ''),
                'class': best.get('class', ''),
                'city': address.get('city') or address.get('town') or address.get('village', ''),
                'state': address.get('state', ''),
                'postcode': address.get('postcode', ''),
                'country': address.get('country', ''),
                'importance': best.get('importance', 0)
            }

        return None

    except Exception as e:
        return {'error': str(e)}


def whois_lookup(domain):
    """Basic WHOIS lookup using web service."""
    if not domain:
        return None
    try:
        # Use a free WHOIS API
        url = f'https://www.whoisxmlapi.com/whoisserver/WhoisService?domainName={domain}&outputFormat=JSON&apiKey=at_demo'

        response = session.get(url, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()
        whois_record = data.get('WhoisRecord', {})

        return {
            'domain_name': whois_record.get('domainName'),
            'registrar': whois_record.get('registrarName'),
            'created_date': whois_record.get('createdDate'),
            'updated_date': whois_record.get('updatedDate'),
            'expires_date': whois_record.get('expiresDate'),
            'status': whois_record.get('status'),
            'registrant_org': whois_record.get('registrant', {}).get('organization'),
            'registrant_country': whois_record.get('registrant', {}).get('country')
        }

    except Exception as e:
        return {'error': str(e)}


def check_website_title(url):
    """Quick check of website title tag."""
    if not url:
        return None
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        response = session.get(url, timeout=8, allow_redirects=True)
        if response.status_code != 200:
            return None

        # Extract title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', response.text, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else ''

        # Extract meta description
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
                               response.text, re.IGNORECASE)
        if not desc_match:
            desc_match = re.search(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']description["\']',
                                   response.text, re.IGNORECASE)
        description = desc_match.group(1).strip() if desc_match else ''

        return {
            'title': title[:500],
            'description': description[:500],
            'final_url': response.url
        }

    except Exception as e:
        return {'error': str(e)}


def compute_enrichment_score(company_name, city, state, url, ddg_result, osm_result, whois_result, website_result):
    """Compute combined enrichment confidence score."""
    scores = []
    evidence = []

    normalized_name = normalize_company_name(company_name)

    # DuckDuckGo heading match
    if ddg_result and ddg_result.get('heading'):
        jw = compute_jaro_winkler(normalized_name, normalize_company_name(ddg_result['heading']))
        if jw > 0.5:
            scores.append(jw * 0.25)
            evidence.append(f"DDG heading match: {jw:.2f}")

    # DuckDuckGo abstract contains company name
    if ddg_result and ddg_result.get('abstract'):
        if normalized_name in ddg_result['abstract'].lower():
            scores.append(0.15)
            evidence.append("DDG abstract contains name")

    # OSM location match
    if osm_result and not osm_result.get('error'):
        osm_city = osm_result.get('city', '').lower()
        osm_state = osm_result.get('state', '').lower()
        if city and city.lower() in osm_city:
            scores.append(0.10)
            evidence.append("OSM city match")
        if state and state.lower() in osm_state:
            scores.append(0.10)
            evidence.append("OSM state match")

    # Domain verification
    domain = extract_domain(url)
    if domain and verify_domain_exists(domain):
        scores.append(0.15)
        evidence.append("Domain resolves")

        # WHOIS registrant match
        if whois_result and whois_result.get('registrant_org'):
            jw = compute_jaro_winkler(normalized_name, normalize_company_name(whois_result['registrant_org']))
            if jw > 0.6:
                scores.append(jw * 0.15)
                evidence.append(f"WHOIS org match: {jw:.2f}")

    # Website title match
    if website_result and website_result.get('title'):
        jw = compute_jaro_winkler(normalized_name, normalize_company_name(website_result['title']))
        if jw > 0.5:
            scores.append(jw * 0.20)
            evidence.append(f"Website title match: {jw:.2f}")

        # Check if company name appears in title
        if normalized_name in website_result['title'].lower():
            scores.append(0.10)
            evidence.append("Name in website title")

    # Token overlap bonus
    if website_result and website_result.get('title'):
        overlap = compute_token_overlap(company_name, website_result['title'])
        if overlap > 0.3:
            scores.append(overlap * 0.10)
            evidence.append(f"Token overlap: {overlap:.2f}")

    total_score = min(sum(scores), 1.0)  # Cap at 1.0

    return total_score, evidence


def classify_confidence(score):
    """Classify confidence level based on enrichment score."""
    if score >= HIGH_CONFIDENCE_THRESHOLD:
        return 'HIGH_CONFIDENCE'
    elif score >= MEDIUM_CONFIDENCE_THRESHOLD:
        return 'MEDIUM_CONFIDENCE'
    else:
        return 'LOW_CONFIDENCE'


def process_company(row):
    """Process a single company through all free enrichment sources."""
    company_id = row.get('company_id') or row.get('company_unique_id')
    company_name = row.get('company_name', '')
    city = row.get('address_city', '') or row.get('city', '')
    state = row.get('address_state', '') or row.get('state', '')
    url = row.get('url', '') or row.get('website_url', '')

    result = {
        'original_company_id': company_id,
        'original_company_name': company_name,
        'original_city': city,
        'original_state': state,
        'original_url': url,
        'ddg_heading': None,
        'ddg_abstract': None,
        'ddg_website': None,
        'osm_display_name': None,
        'osm_city': None,
        'osm_state': None,
        'osm_type': None,
        'whois_registrant': None,
        'whois_created': None,
        'website_title': None,
        'website_description': None,
        'domain_valid': False,
        'enrichment_score': 0.0,
        'evidence': [],
        'confidence_class': 'LOW_CONFIDENCE',
        'sources_checked': [],
        'timestamp': datetime.now().isoformat()
    }

    try:
        # Source 1: DuckDuckGo
        ddg = duckduckgo_search(company_name, city, state)
        if ddg and not ddg.get('error'):
            result['ddg_heading'] = ddg.get('heading')
            result['ddg_abstract'] = ddg.get('abstract', '')[:500]
            result['ddg_website'] = ddg.get('website')
            result['sources_checked'].append('duckduckgo')
        time.sleep(DDG_DELAY)

        # Source 2: OpenStreetMap Nominatim
        osm = nominatim_search(company_name, city, state)
        if osm and not osm.get('error'):
            result['osm_display_name'] = osm.get('display_name', '')[:300]
            result['osm_city'] = osm.get('city')
            result['osm_state'] = osm.get('state')
            result['osm_type'] = osm.get('type')
            result['sources_checked'].append('openstreetmap')
        time.sleep(NOMINATIM_DELAY)

        # Source 3: Domain verification + WHOIS
        domain = extract_domain(url)
        if domain:
            result['domain_valid'] = verify_domain_exists(domain)
            if result['domain_valid']:
                whois = whois_lookup(domain)
                if whois and not whois.get('error'):
                    result['whois_registrant'] = whois.get('registrant_org')
                    result['whois_created'] = whois.get('created_date')
                    result['sources_checked'].append('whois')
                time.sleep(WHOIS_DELAY)

        # Source 4: Direct website title check
        if url:
            website = check_website_title(url)
            if website and not website.get('error'):
                result['website_title'] = website.get('title')
                result['website_description'] = website.get('description')
                result['sources_checked'].append('website_direct')

        # Compute combined score
        score, evidence = compute_enrichment_score(
            company_name, city, state, url,
            ddg, osm,
            {'registrant_org': result['whois_registrant']} if result['whois_registrant'] else None,
            {'title': result['website_title']} if result['website_title'] else None
        )

        result['enrichment_score'] = round(score, 4)
        result['evidence'] = evidence
        result['confidence_class'] = classify_confidence(score)

    except Exception as e:
        result['error'] = str(e)

    # Convert lists to strings for CSV
    result['evidence'] = '|'.join(result['evidence'])
    result['sources_checked'] = ','.join(result['sources_checked'])

    return result


def process_batch(batch_df, batch_num, total_batches):
    """Process a batch of companies."""
    results = []
    batch_start = (batch_num - 1) * BATCH_SIZE + 1
    batch_end = batch_start + len(batch_df) - 1

    print(f"  Batch {batch_num}/{total_batches} ({batch_start}-{batch_end})...")

    high_conf = 0
    medium_conf = 0
    low_conf = 0

    for idx, row in batch_df.iterrows():
        result = process_company(row)
        results.append(result)

        if result['confidence_class'] == 'HIGH_CONFIDENCE':
            high_conf += 1
        elif result['confidence_class'] == 'MEDIUM_CONFIDENCE':
            medium_conf += 1
        else:
            low_conf += 1

    print(f"    High: {high_conf}, Medium: {medium_conf}, Low: {low_conf}")

    return results


def main():
    print("=" * 70)
    print("STAGE 6A: FREE MULTI-SOURCE ENRICHMENT")
    print("=" * 70)
    print()
    print("Sources: DuckDuckGo, OpenStreetMap, WHOIS, Direct Website")
    print("Cost: $0")
    print()

    start_time = datetime.now()

    print(f"[1] Loading input file...")
    if not os.path.exists(INPUT_FILE):
        print(f"  ERROR: Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    total_records = len(df)
    print(f"  Loaded: {total_records:,} records")
    print()

    # Create output directories
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    print("=" * 70)
    print("FREE ENRICHMENT PIPELINE")
    print("=" * 70)
    print()

    # Calculate batches
    total_batches = (total_records + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"  Processing {total_records:,} records in {total_batches} batches of {BATCH_SIZE}...")
    print(f"  Estimated time: {total_records * 3 / 60:.0f} minutes (rate-limited APIs)")
    print()

    all_results = []
    stats = {
        'total_processed': 0,
        'high_confidence': 0,
        'medium_confidence': 0,
        'low_confidence': 0,
        'errors': []
    }

    # Process in batches
    for batch_num in range(1, total_batches + 1):
        batch_start_idx = (batch_num - 1) * BATCH_SIZE
        batch_end_idx = min(batch_start_idx + BATCH_SIZE, total_records)
        batch_df = df.iloc[batch_start_idx:batch_end_idx]

        try:
            batch_results = process_batch(batch_df, batch_num, total_batches)
            all_results.extend(batch_results)

            # Update stats
            for r in batch_results:
                stats['total_processed'] += 1
                if r['confidence_class'] == 'HIGH_CONFIDENCE':
                    stats['high_confidence'] += 1
                elif r['confidence_class'] == 'MEDIUM_CONFIDENCE':
                    stats['medium_confidence'] += 1
                else:
                    stats['low_confidence'] += 1

            # Save progress every 10 batches
            if batch_num % 10 == 0:
                print(f"    [Progress saved: {stats['total_processed']:,} records]")
                # Save intermediate results
                pd.DataFrame(all_results).to_csv(
                    os.path.join(OUTPUT_DIR, 'free_enrichment_progress.csv'),
                    index=False
                )

        except Exception as e:
            error_msg = f"Batch {batch_num} failed: {str(e)}"
            print(f"    ERROR: {error_msg}")
            stats['errors'].append(error_msg)

    print()
    print("=" * 70)
    print("SAVING OUTPUTS")
    print("=" * 70)
    print()

    # Convert results to DataFrame
    results_df = pd.DataFrame(all_results)

    # Split by confidence class
    high_conf_df = results_df[results_df['confidence_class'] == 'HIGH_CONFIDENCE']
    medium_conf_df = results_df[results_df['confidence_class'] == 'MEDIUM_CONFIDENCE']
    low_conf_df = results_df[results_df['confidence_class'] == 'LOW_CONFIDENCE']

    # Save CSV outputs
    high_conf_df.to_csv(HIGH_CONF_OUTPUT, index=False)
    print(f"  Saved: {HIGH_CONF_OUTPUT} ({len(high_conf_df):,} records)")

    medium_conf_df.to_csv(MEDIUM_CONF_OUTPUT, index=False)
    print(f"  Saved: {MEDIUM_CONF_OUTPUT} ({len(medium_conf_df):,} records)")

    low_conf_df.to_csv(LOW_CONF_OUTPUT, index=False)
    print(f"  Saved: {LOW_CONF_OUTPUT} ({len(low_conf_df):,} records)")

    # Save full JSONL dump
    with open(FULL_DUMP_OUTPUT, 'w', encoding='utf-8') as f:
        for result in all_results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    print(f"  Saved: {FULL_DUMP_OUTPUT} ({len(all_results):,} records)")

    # Save log
    end_time = datetime.now()
    log = {
        'started_at': start_time.isoformat(),
        'completed_at': end_time.isoformat(),
        'run_time_seconds': (end_time - start_time).total_seconds(),
        'input_file': INPUT_FILE,
        'total_input_records': total_records,
        'total_processed': stats['total_processed'],
        'high_confidence': stats['high_confidence'],
        'medium_confidence': stats['medium_confidence'],
        'low_confidence': stats['low_confidence'],
        'high_confidence_pct': round(100 * stats['high_confidence'] / stats['total_processed'], 2) if stats['total_processed'] > 0 else 0,
        'medium_confidence_pct': round(100 * stats['medium_confidence'] / stats['total_processed'], 2) if stats['total_processed'] > 0 else 0,
        'cost': '$0.00',
        'errors': stats['errors'][:20]
    }

    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2)
    print(f"  Saved: {LOG_FILE}")

    # Cleanup progress file
    progress_file = os.path.join(OUTPUT_DIR, 'free_enrichment_progress.csv')
    if os.path.exists(progress_file):
        os.remove(progress_file)

    print()
    print("=" * 70)
    print("STAGE 6A COMPLETE")
    print("=" * 70)
    print(f"  Total processed: {stats['total_processed']:,}")
    print(f"  High confidence (>={HIGH_CONFIDENCE_THRESHOLD}): {stats['high_confidence']:,} ({log['high_confidence_pct']}%)")
    print(f"  Medium confidence ({MEDIUM_CONFIDENCE_THRESHOLD}-{HIGH_CONFIDENCE_THRESHOLD}): {stats['medium_confidence']:,} ({log['medium_confidence_pct']}%)")
    print(f"  Low confidence (<{MEDIUM_CONFIDENCE_THRESHOLD}): {stats['low_confidence']:,}")
    print(f"  Run time: {log['run_time_seconds']/60:.1f} minutes")
    print(f"  Total cost: {log['cost']}")


if __name__ == '__main__':
    main()
