"""
Stage 6A: Google Places Enrichment
==================================
Enriches unresolved low-confidence companies using Google Places API.

Input: splink_low_confidence.csv (≈ 6,386 unresolved companies)
Output:
  - google_places_high_confidence.csv (jw >= 0.88)
  - google_places_medium_confidence.csv (0.72 <= jw < 0.88)
  - google_places_low_confidence.csv (jw < 0.72, for Clay pass)
  - google_places_full_dump.jsonl
  - logs/google_places_enrichment_log.json
"""

import os
import json
import time
import requests
import pandas as pd
from datetime import datetime
from rapidfuzz.distance import JaroWinkler
from dotenv import load_dotenv
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment
load_dotenv()

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
LOG_DIR = os.path.join(OUTPUT_DIR, 'logs')

INPUT_FILE = os.path.join(OUTPUT_DIR, 'splink_low_confidence.csv')
HIGH_CONF_OUTPUT = os.path.join(OUTPUT_DIR, 'google_places_high_confidence.csv')
MEDIUM_CONF_OUTPUT = os.path.join(OUTPUT_DIR, 'google_places_medium_confidence.csv')
LOW_CONF_OUTPUT = os.path.join(OUTPUT_DIR, 'google_places_low_confidence.csv')
FULL_DUMP_OUTPUT = os.path.join(OUTPUT_DIR, 'google_places_full_dump.jsonl')
LOG_FILE = os.path.join(LOG_DIR, 'google_places_enrichment_log.json')

# API Configuration
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
TEXT_SEARCH_URL = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
DETAILS_URL = 'https://maps.googleapis.com/maps/api/place/details/json'

# Batch settings
BATCH_SIZE = 150
SLEEP_BETWEEN_BATCHES = 1.2
MAX_RETRIES = 3
RETRY_DELAY = 2.0

# Confidence thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.88
MEDIUM_CONFIDENCE_THRESHOLD = 0.72


def compute_jaro_winkler(s1, s2):
    """Compute Jaro-Winkler similarity between two strings."""
    if not s1 or not s2:
        return 0.0
    return JaroWinkler.normalized_similarity(s1.lower().strip(), s2.lower().strip())


def compute_token_overlap(s1, s2):
    """Compute token overlap ratio between two strings."""
    if not s1 or not s2:
        return 0.0
    tokens1 = set(s1.lower().split())
    tokens2 = set(s2.lower().split())
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    return len(intersection) / len(union) if union else 0.0


def check_city_state_match(google_address, city, state):
    """Check if city and state appear in the Google address."""
    if not google_address:
        return False, False
    addr_lower = google_address.lower()
    city_match = city.lower().strip() in addr_lower if city else False
    state_match = state.lower().strip() in addr_lower if state else False
    return city_match, state_match


def text_search_place(company_name, city, state, retries=MAX_RETRIES):
    """Search for a place using Google Places Text Search API."""
    query = f'"{company_name}" {city} {state} company website'

    for attempt in range(retries):
        try:
            params = {
                'query': query,
                'key': GOOGLE_PLACES_API_KEY
            }
            response = requests.get(TEXT_SEARCH_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'OK' and data.get('results'):
                return data['results'][0].get('place_id')
            elif data.get('status') == 'ZERO_RESULTS':
                return None
            elif data.get('status') in ['OVER_QUERY_LIMIT', 'REQUEST_DENIED']:
                raise Exception(f"API Error: {data.get('status')} - {data.get('error_message', '')}")

            return None

        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise e

    return None


def get_place_details(place_id, retries=MAX_RETRIES):
    """Get detailed information for a place using Google Places Details API."""
    fields = [
        'name',
        'website',
        'formatted_address',
        'formatted_phone_number',
        'international_phone_number',
        'business_status',
        'types',
        'rating',
        'user_ratings_total'
    ]

    for attempt in range(retries):
        try:
            params = {
                'place_id': place_id,
                'fields': ','.join(fields),
                'key': GOOGLE_PLACES_API_KEY
            }
            response = requests.get(DETAILS_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'OK':
                return data.get('result', {})
            elif data.get('status') in ['OVER_QUERY_LIMIT', 'REQUEST_DENIED']:
                raise Exception(f"API Error: {data.get('status')} - {data.get('error_message', '')}")

            return None

        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise e

    return None


def classify_confidence(jw_score):
    """Classify confidence level based on Jaro-Winkler score."""
    if jw_score >= HIGH_CONFIDENCE_THRESHOLD:
        return 'HIGH_CONFIDENCE'
    elif jw_score >= MEDIUM_CONFIDENCE_THRESHOLD:
        return 'MEDIUM_CONFIDENCE'
    else:
        return 'LOW_CONFIDENCE'


def process_company(row):
    """Process a single company through Google Places API."""
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
        'google_canonical_name': None,
        'google_website': None,
        'google_phone': None,
        'google_international_phone': None,
        'google_address': None,
        'google_business_status': None,
        'google_types': None,
        'google_rating': None,
        'google_ratings_total': None,
        'place_id': None,
        'jw_score': 0.0,
        'token_overlap': 0.0,
        'city_match': False,
        'state_match': False,
        'confidence_class': 'LOW_CONFIDENCE',
        'api_success': False,
        'error_message': None,
        'timestamp': datetime.now().isoformat()
    }

    try:
        # Step 1: Text Search to get place_id
        place_id = text_search_place(company_name, city, state)

        if not place_id:
            result['error_message'] = 'No place found in text search'
            return result

        result['place_id'] = place_id

        # Step 2: Get Place Details
        details = get_place_details(place_id)

        if not details:
            result['error_message'] = 'Failed to get place details'
            return result

        # Extract details
        canonical_name = details.get('name', '')
        result['google_canonical_name'] = canonical_name
        result['google_website'] = details.get('website')
        result['google_phone'] = details.get('formatted_phone_number')
        result['google_international_phone'] = details.get('international_phone_number')
        result['google_address'] = details.get('formatted_address')
        result['google_business_status'] = details.get('business_status')
        result['google_types'] = ','.join(details.get('types', []))
        result['google_rating'] = details.get('rating')
        result['google_ratings_total'] = details.get('user_ratings_total')

        # Compute similarity scores
        result['jw_score'] = compute_jaro_winkler(company_name, canonical_name)
        result['token_overlap'] = compute_token_overlap(company_name, canonical_name)

        # Check city/state match
        city_match, state_match = check_city_state_match(
            result['google_address'], city, state
        )
        result['city_match'] = city_match
        result['state_match'] = state_match

        # Classify confidence
        result['confidence_class'] = classify_confidence(result['jw_score'])
        result['api_success'] = True

    except Exception as e:
        result['error_message'] = str(e)

    return result


def process_batch(batch_df, batch_num, total_batches):
    """Process a batch of companies."""
    results = []
    batch_start = (batch_num - 1) * BATCH_SIZE + 1
    batch_end = batch_start + len(batch_df) - 1

    print(f"  Batch {batch_num}/{total_batches} ({batch_start}-{batch_end})...")

    api_success = 0
    high_conf = 0
    medium_conf = 0
    low_conf = 0

    for idx, row in batch_df.iterrows():
        result = process_company(row)
        results.append(result)

        if result['api_success']:
            api_success += 1
            if result['confidence_class'] == 'HIGH_CONFIDENCE':
                high_conf += 1
            elif result['confidence_class'] == 'MEDIUM_CONFIDENCE':
                medium_conf += 1
            else:
                low_conf += 1

        # Small delay between API calls to avoid rate limiting
        time.sleep(0.1)

    print(f"    API Success: {api_success}/{len(batch_df)}, "
          f"High: {high_conf}, Medium: {medium_conf}, Low: {low_conf}")

    return results


def main():
    print("=" * 70)
    print("STAGE 6A: GOOGLE PLACES ENRICHMENT")
    print("=" * 70)
    print()

    start_time = datetime.now()

    # Validate API key
    if not GOOGLE_PLACES_API_KEY:
        print("ERROR: GOOGLE_PLACES_API_KEY not found in environment variables")
        print("Please add GOOGLE_PLACES_API_KEY to your .env file")
        return

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
    print("GOOGLE PLACES API ENRICHMENT")
    print("=" * 70)
    print()

    # Calculate batches
    total_batches = (total_records + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"  Processing {total_records:,} records in {total_batches} batches of {BATCH_SIZE}...")
    print()

    all_results = []
    stats = {
        'total_processed': 0,
        'api_success': 0,
        'api_failed': 0,
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
                if r['api_success']:
                    stats['api_success'] += 1
                    if r['confidence_class'] == 'HIGH_CONFIDENCE':
                        stats['high_confidence'] += 1
                    elif r['confidence_class'] == 'MEDIUM_CONFIDENCE':
                        stats['medium_confidence'] += 1
                    else:
                        stats['low_confidence'] += 1
                else:
                    stats['api_failed'] += 1

            # Save progress every 10 batches
            if batch_num % 10 == 0:
                print(f"    [Progress saved: {stats['total_processed']:,} records]")

        except Exception as e:
            error_msg = f"Batch {batch_num} failed: {str(e)}"
            print(f"    ERROR: {error_msg}")
            stats['errors'].append(error_msg)

        # Sleep between batches
        if batch_num < total_batches:
            time.sleep(SLEEP_BETWEEN_BATCHES)

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
        'api_success': stats['api_success'],
        'api_failed': stats['api_failed'],
        'high_confidence': stats['high_confidence'],
        'medium_confidence': stats['medium_confidence'],
        'low_confidence': stats['low_confidence'],
        'success_rate': round(100 * stats['api_success'] / stats['total_processed'], 2) if stats['total_processed'] > 0 else 0,
        'errors': stats['errors'][:20]
    }

    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2)
    print(f"  Saved: {LOG_FILE}")

    print()
    print("=" * 70)
    print("STAGE 6A COMPLETE")
    print("=" * 70)
    print(f"  Total processed: {stats['total_processed']:,}")
    print(f"  API success: {stats['api_success']:,} ({log['success_rate']}%)")
    print(f"  High confidence (>={HIGH_CONFIDENCE_THRESHOLD}): {stats['high_confidence']:,}")
    print(f"  Medium confidence ({MEDIUM_CONFIDENCE_THRESHOLD}-{HIGH_CONFIDENCE_THRESHOLD}): {stats['medium_confidence']:,}")
    print(f"  Low confidence (<{MEDIUM_CONFIDENCE_THRESHOLD}): {stats['low_confidence']:,}")
    print(f"  Run time: {log['run_time_seconds']:.1f} seconds")


if __name__ == '__main__':
    main()
