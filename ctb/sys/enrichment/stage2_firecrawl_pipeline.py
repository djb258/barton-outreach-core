#!/usr/bin/env python3
"""
Stage 2 Firecrawl Enrichment Pipeline
======================================
Batch processing with Firecrawl API for ambiguous matches (0.50-0.75).
"""

import os
import sys
import re
import json
import time
import requests
import pandas as pd
from datetime import datetime
from rapidfuzz import fuzz
from bs4 import BeautifulSoup

# Configuration
WORK_DIR = r"C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core"
OUTPUT_DIR = os.path.join(WORK_DIR, "ctb", "sys", "enrichment", "output")
LOGS_DIR = os.path.join(OUTPUT_DIR, "logs")

FIRECRAWL_API_KEY = os.environ.get('FIRECRAWL_API_KEY', 'fc-b936adee5dff4980b7a1e03f0c57562c')
FIRECRAWL_URL = 'https://api.firecrawl.dev/v1/scrape'

BATCH_SIZE = 250
BATCH_SLEEP = 1.5

# Ensure directories exist
os.makedirs(LOGS_DIR, exist_ok=True)


def normalize_name(text):
    """Normalize company name for comparison."""
    if not text or pd.isna(text):
        return ""
    text = str(text).upper()
    suffixes = [
        r'\bLLC\b', r'\bL\.L\.C\.\b', r'\bINC\b', r'\bINC\.\b',
        r'\bINCORPORATED\b', r'\bCORP\b', r'\bCORP\.\b', r'\bCORPORATION\b',
        r'\bLTD\b', r'\bLTD\.\b', r'\bLIMITED\b', r'\bCO\b', r'\bCO\.\b',
        r'\bCOMPANY\b', r'\bLP\b', r'\bL\.P\.\b', r'\bLLP\b', r'\bL\.L\.P\.\b',
        r'\bPC\b', r'\bP\.C\.\b', r'\bPLLC\b', r'\bP\.L\.L\.C\.\b',
        r'\bNA\b', r'\bN\.A\.\b', r'\bDBA\b', r'\bD/B/A\b', r'\bTHE\b'
    ]
    for suffix in suffixes:
        text = re.sub(suffix, '', text)
    text = re.sub(r'[^A-Z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def jaro_winkler_sim(s1, s2):
    """Calculate Jaro-Winkler similarity using rapidfuzz."""
    if not s1 or not s2:
        return 0.0
    return fuzz.jaro_winkler_similarity(s1, s2) / 100.0


def trigram_sim(s1, s2):
    """Calculate trigram similarity."""
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0
    if len(s1) < 3 or len(s2) < 3:
        return 1.0 if s1 == s2 else 0.0

    def get_trigrams(s):
        s = f"  {s} "
        return set(s[i:i+3] for i in range(len(s) - 2))

    t1, t2 = get_trigrams(s1), get_trigrams(s2)
    intersection = len(t1 & t2)
    union = len(t1 | t2)
    return intersection / union if union > 0 else 0.0


def token_set_overlap(s1, s2):
    """Calculate token set overlap ratio."""
    if not s1 or not s2:
        return 0.0
    tokens1 = set(s1.split())
    tokens2 = set(s2.split())
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1 & tokens2)
    min_size = min(len(tokens1), len(tokens2))
    return intersection / min_size if min_size > 0 else 0.0


def max_similarity(text, canonical):
    """Calculate max similarity across all methods."""
    text_norm = normalize_name(text)
    canonical_norm = normalize_name(canonical)
    if not text_norm or not canonical_norm:
        return 0.0
    jw = jaro_winkler_sim(text_norm, canonical_norm)
    tg = trigram_sim(text_norm, canonical_norm)
    ts = token_set_overlap(text_norm, canonical_norm)
    return max(jw, tg, ts)


def scrape_with_firecrawl(url):
    """Scrape URL using Firecrawl API."""
    if not url or pd.isna(url):
        return None

    if not str(url).startswith('http'):
        url = f"https://{url}"

    headers = {
        'Authorization': f'Bearer {FIRECRAWL_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'url': url,
        'formats': ['html']
    }

    try:
        response = requests.post(FIRECRAWL_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('data', {})
        return None
    except Exception:
        return None


def scrape_direct(url):
    """Direct scrape fallback using requests + BeautifulSoup."""
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
        if response.status_code != 200:
            return None
        return {'html': response.text}
    except Exception:
        return None


def parse_html_fields(data):
    """Parse homepage fields from scraped data."""
    result = {
        'title': None,
        'h1': None,
        'og_title': None,
        'og_site_name': None
    }

    if not data:
        return result

    html = data.get('html', '')
    if not html:
        return result

    try:
        soup = BeautifulSoup(html, 'html.parser')

        title_tag = soup.find('title')
        if title_tag:
            result['title'] = title_tag.get_text(strip=True)

        h1_tag = soup.find('h1')
        if h1_tag:
            result['h1'] = h1_tag.get_text(strip=True)

        og_title = soup.find('meta', property='og:title')
        if og_title:
            result['og_title'] = og_title.get('content', '')

        og_site = soup.find('meta', property='og:site_name')
        if og_site:
            result['og_site_name'] = og_site.get('content', '')
    except Exception:
        pass

    return result


def process_record(row):
    """Process a single record: scrape + score."""
    company_id = row.get('company_id', '')
    canonical = row.get('canonical_name', '') or row.get('best_sponsor_name', '')
    original_score = float(row.get('score', 0))
    url = row.get('url', '') or row.get('website_url', '')

    log_entry = {
        'company_id': company_id,
        'url': url,
        'timestamp': datetime.now().isoformat(),
        'scrape_success': False,
        'scrape_method': None,
        'fields': {},
        'scores': {},
        'original_score': original_score,
        'enriched_score': 0.0,
        'final_score': original_score,
        'confidence': 'LOW_CONFIDENCE'
    }

    result = {
        'company_id': company_id,
        'company_name': row.get('company_name', ''),
        'best_ein_match': row.get('best_ein_match', ''),
        'best_sponsor_name': row.get('best_sponsor_name', ''),
        'canonical_name': canonical,
        'url': url,
        'original_score': original_score,
        'title': None,
        'h1': None,
        'og_title': None,
        'og_site_name': None,
        'title_sim': 0.0,
        'h1_sim': 0.0,
        'og_title_sim': 0.0,
        'token_overlap': 0.0,
        'enriched_score': 0.0,
        'final_score': original_score,
        'confidence': 'LOW_CONFIDENCE',
        'scrape_success': False
    }

    if not url:
        return result, log_entry

    # Try Firecrawl first, then direct scrape
    data = scrape_with_firecrawl(url)
    if data:
        log_entry['scrape_method'] = 'firecrawl'
    else:
        data = scrape_direct(url)
        if data:
            log_entry['scrape_method'] = 'direct'

    if not data:
        return result, log_entry

    # Parse HTML fields
    fields = parse_html_fields(data)
    log_entry['fields'] = fields
    log_entry['scrape_success'] = True
    result['scrape_success'] = True

    result['title'] = fields['title']
    result['h1'] = fields['h1']
    result['og_title'] = fields['og_title']
    result['og_site_name'] = fields['og_site_name']

    # Calculate similarities
    title_sim = max_similarity(fields['title'], canonical) if fields['title'] else 0.0
    h1_sim = max_similarity(fields['h1'], canonical) if fields['h1'] else 0.0
    og_title_sim = max_similarity(fields['og_title'], canonical) if fields['og_title'] else 0.0
    og_site_sim = max_similarity(fields['og_site_name'], canonical) if fields['og_site_name'] else 0.0

    # Token overlap on best text
    best_text = fields['title'] or fields['h1'] or fields['og_title'] or ''
    token_overlap = token_set_overlap(normalize_name(best_text), normalize_name(canonical))

    result['title_sim'] = round(title_sim, 4)
    result['h1_sim'] = round(h1_sim, 4)
    result['og_title_sim'] = round(og_title_sim, 4)
    result['token_overlap'] = round(token_overlap, 4)

    log_entry['scores'] = {
        'title_sim': title_sim,
        'h1_sim': h1_sim,
        'og_title_sim': og_title_sim,
        'og_site_sim': og_site_sim,
        'token_overlap': token_overlap
    }

    # Calculate enriched score
    enriched_score = (
        0.50 * title_sim +
        0.30 * h1_sim +
        0.10 * og_title_sim +
        0.10 * token_overlap
    )

    result['enriched_score'] = round(enriched_score, 4)
    log_entry['enriched_score'] = enriched_score

    # Final score = max(original, enriched)
    final_score = max(original_score, enriched_score)
    result['final_score'] = round(final_score, 4)
    log_entry['final_score'] = final_score

    # Classify confidence
    if final_score >= 0.75:
        confidence = 'HIGH_CONFIDENCE'
    elif final_score >= 0.60:
        confidence = 'MEDIUM_CONFIDENCE'
    else:
        confidence = 'LOW_CONFIDENCE'

    result['confidence'] = confidence
    log_entry['confidence'] = confidence

    return result, log_entry


def run_pipeline():
    """Run the full enrichment pipeline."""
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 70)
    print("STAGE 2 FIRECRAWL ENRICHMENT PIPELINE")
    print("=" * 70)

    # Load data
    print("\n[1] Loading data...")

    matches_file = os.path.join(OUTPUT_DIR, "duckdb_matches.csv")
    companies_file = os.path.join(WORK_DIR, "companies_with_urls.csv")

    matches_df = pd.read_csv(matches_file)
    companies_df = pd.read_csv(companies_file)

    print(f"  Loaded matches: {len(matches_df):,}")
    print(f"  Loaded companies: {len(companies_df):,}")

    # Merge to get URLs
    companies_df = companies_df.rename(columns={'company_unique_id': 'company_id'})
    merged_df = matches_df.merge(
        companies_df[['company_id', 'website_url']],
        on='company_id',
        how='left'
    )
    merged_df['url'] = merged_df['website_url']

    # Filter ambiguous matches (0.50 <= score < 0.75)
    print("\n[2] Filtering ambiguous matches (0.50 <= score < 0.75)...")

    merged_df['score'] = merged_df['score'].astype(float)
    ambiguous_df = merged_df[(merged_df['score'] >= 0.50) & (merged_df['score'] < 0.75)].copy()
    high_conf_df = merged_df[merged_df['score'] >= 0.75].copy()

    print(f"  Ambiguous (0.50-0.75): {len(ambiguous_df):,}")
    print(f"  High confidence (>=0.75): {len(high_conf_df):,}")

    # Process in batches
    print(f"\n[3] Processing {len(ambiguous_df):,} records in batches of {BATCH_SIZE}...")

    all_results = []
    all_logs = []

    records = ambiguous_df.to_dict('records')
    total_batches = (len(records) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_num in range(total_batches):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, len(records))
        batch = records[start_idx:end_idx]

        print(f"\n  Batch {batch_num + 1}/{total_batches} ({start_idx+1}-{end_idx})...")

        batch_success = 0
        for row in batch:
            result, log_entry = process_record(row)
            all_results.append(result)
            all_logs.append(log_entry)
            if result['scrape_success']:
                batch_success += 1

        print(f"    Scraped: {batch_success}/{len(batch)}")

        if batch_num < total_batches - 1:
            time.sleep(BATCH_SLEEP)

    # Add high confidence records (no enrichment needed)
    print("\n[4] Adding high confidence records...")

    for _, row in high_conf_df.iterrows():
        score = float(row['score'])
        all_results.append({
            'company_id': row['company_id'],
            'company_name': row.get('company_name', ''),
            'best_ein_match': row.get('best_ein_match', ''),
            'best_sponsor_name': row.get('best_sponsor_name', ''),
            'canonical_name': row.get('canonical_name', ''),
            'url': row.get('url', ''),
            'original_score': score,
            'title': None,
            'h1': None,
            'og_title': None,
            'og_site_name': None,
            'title_sim': 0.0,
            'h1_sim': 0.0,
            'og_title_sim': 0.0,
            'token_overlap': 0.0,
            'enriched_score': 0.0,
            'final_score': score,
            'confidence': 'HIGH_CONFIDENCE' if score >= 0.75 else 'MEDIUM_CONFIDENCE',
            'scrape_success': False
        })

    # Analyze results
    print("\n[5] Analyzing results...")

    results_df = pd.DataFrame(all_results)

    confidence_counts = results_df['confidence'].value_counts()
    scrape_success = results_df['scrape_success'].sum()
    upgraded = (results_df['enriched_score'] > results_df['original_score']).sum()

    print(f"\n  CONFIDENCE DISTRIBUTION:")
    for conf in ['HIGH_CONFIDENCE', 'MEDIUM_CONFIDENCE', 'LOW_CONFIDENCE']:
        count = confidence_counts.get(conf, 0)
        print(f"    {conf}: {count:,}")

    print(f"\n  Scrape success: {scrape_success:,}")
    print(f"  Upgraded by enrichment: {upgraded:,}")

    # Save outputs
    print("\n[6] Saving output files...")

    # enriched_matches.csv
    enriched_file = os.path.join(OUTPUT_DIR, "enriched_matches.csv")
    results_df.to_csv(enriched_file, index=False)
    print(f"  Saved: {enriched_file} ({len(results_df):,} records)")

    # review_queue.csv
    review_df = results_df[results_df['confidence'] == 'LOW_CONFIDENCE']
    review_file = os.path.join(OUTPUT_DIR, "review_queue.csv")
    review_df.to_csv(review_file, index=False)
    print(f"  Saved: {review_file} ({len(review_df):,} records)")

    # enrichment_log.json
    log_file = os.path.join(LOGS_DIR, "enrichment_log.json")
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(all_logs, f, indent=2, default=str)
    print(f"  Saved: {log_file} ({len(all_logs):,} entries)")

    # Summary
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"Total records: {len(results_df):,}")
    print(f"Ambiguous processed: {len(ambiguous_df):,}")
    print(f"Scrape success: {scrape_success:,}")
    print(f"Upgraded: {upgraded:,}")
    print(f"\nFinal distribution:")
    for conf in ['HIGH_CONFIDENCE', 'MEDIUM_CONFIDENCE', 'LOW_CONFIDENCE']:
        count = confidence_counts.get(conf, 0)
        print(f"  {conf}: {count:,}")


if __name__ == '__main__':
    run_pipeline()
