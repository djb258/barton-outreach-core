#!/usr/bin/env python3
"""
Stage 5 Low Confidence Cleanup Pipeline
========================================
A + C Special Cleanup: Firecrawl Identity Upgrade + Splink ML Matching
"""

import os
import sys
import re
import json
import time
import requests
import pandas as pd
import duckdb
from datetime import datetime
from bs4 import BeautifulSoup
from rapidfuzz.distance import JaroWinkler
from rapidfuzz import fuzz
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import threading

# Load environment variables
load_dotenv()

# Configuration
WORK_DIR = r"C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core"
OUTPUT_DIR = os.path.join(WORK_DIR, "ctb", "sys", "enrichment", "output")
LOGS_DIR = os.path.join(OUTPUT_DIR, "logs")

FIRECRAWL_API_KEY = os.environ.get('FIRECRAWL_API_KEY', '')
FIRECRAWL_URL = 'https://api.firecrawl.dev/v0/scrape'

BATCH_SIZE = 200
BATCH_SLEEP = 1.25
CONCURRENT_WORKERS = 15
REQUEST_TIMEOUT = 20

# Thread-safe logging
log_lock = threading.Lock()

# Ensure directories exist
os.makedirs(LOGS_DIR, exist_ok=True)

# Company name suffixes to remove
COMPANY_SUFFIXES = [
    'llc', 'inc', 'incorporated', 'corp', 'corporation', 'co', 'company',
    'ltd', 'limited', 'lp', 'llp', 'pllc', 'pc', 'pa', 'plc', 'group',
    'holdings', 'enterprises', 'services', 'solutions', 'associates',
    'partners', 'international', 'worldwide', 'global', 'usa', 'us',
    'north america', 'na', 'of america', 'america'
]


def normalize_company_name(name):
    """Normalize company name for comparison."""
    if not name or pd.isna(name):
        return ''

    name = str(name).lower().strip()

    # Remove "the" prefix
    if name.startswith('the '):
        name = name[4:]

    # Remove punctuation
    name = re.sub(r'[^\w\s]', ' ', name)

    # Remove company suffixes
    for suffix in COMPANY_SUFFIXES:
        pattern = r'\b' + suffix + r'\b'
        name = re.sub(pattern, '', name)

    # Normalize whitespace
    name = ' '.join(name.split())

    return name.strip()


def extract_keywords(text):
    """Extract meaningful keywords from text."""
    if not text or pd.isna(text):
        return set()

    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    words = text.split()

    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                  'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'we', 'our',
                  'your', 'home', 'welcome', 'page', 'website', 'site', 'official'}

    keywords = {w for w in words if len(w) > 2 and w not in stop_words}
    return keywords


def compute_token_overlap(text1, text2):
    """Compute token set overlap between two texts."""
    keywords1 = extract_keywords(text1)
    keywords2 = extract_keywords(text2)

    if not keywords1 or not keywords2:
        return 0.0

    intersection = keywords1 & keywords2
    union = keywords1 | keywords2

    if not union:
        return 0.0

    return len(intersection) / len(union)


def scrape_with_firecrawl(url):
    """Scrape URL using Firecrawl API."""
    if not url or pd.isna(url):
        return None

    if not str(url).startswith('http'):
        url = f"https://{url}"

    if not FIRECRAWL_API_KEY:
        return scrape_direct(url)

    headers = {
        'Authorization': f'Bearer {FIRECRAWL_API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'url': url,
        'pageOptions': {
            'onlyMainContent': False,
            'includeHtml': True
        }
    }

    try:
        response = requests.post(FIRECRAWL_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data'):
                return data['data'].get('html', '')
        return scrape_direct(url)
    except Exception:
        return scrape_direct(url)


def scrape_direct(url):
    """Direct scrape fallback."""
    if not url or pd.isna(url):
        return None

    if not str(url).startswith('http'):
        url = f"https://{url}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if response.status_code == 200:
            return response.text
        return None
    except Exception:
        return None


def extract_page_metadata(html):
    """Extract title, h1, og tags, and meta description from HTML."""
    result = {
        'title': None,
        'h1': None,
        'og_site_name': None,
        'og_title': None,
        'meta_description': None
    }

    if not html:
        return result

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            result['title'] = title_tag.get_text(strip=True)

        # Extract h1
        h1_tag = soup.find('h1')
        if h1_tag:
            result['h1'] = h1_tag.get_text(strip=True)

        # Extract og:site_name
        og_site = soup.find('meta', property='og:site_name')
        if og_site:
            result['og_site_name'] = og_site.get('content', '')

        # Extract og:title
        og_title = soup.find('meta', property='og:title')
        if og_title:
            result['og_title'] = og_title.get('content', '')

        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            result['meta_description'] = meta_desc.get('content', '')

    except Exception:
        pass

    return result


def compute_similarity_scores(sponsor_name, metadata):
    """Compute similarity scores between sponsor name and page metadata."""
    normalized_sponsor = normalize_company_name(sponsor_name)

    scores = {
        'title_sim': 0.0,
        'h1_sim': 0.0,
        'og_title_sim': 0.0,
        'token_overlap': 0.0
    }

    if not normalized_sponsor:
        return scores

    # Title similarity
    if metadata.get('title'):
        normalized_title = normalize_company_name(metadata['title'])
        if normalized_title:
            scores['title_sim'] = JaroWinkler.similarity(normalized_sponsor, normalized_title)

    # H1 similarity
    if metadata.get('h1'):
        normalized_h1 = normalize_company_name(metadata['h1'])
        if normalized_h1:
            scores['h1_sim'] = JaroWinkler.similarity(normalized_sponsor, normalized_h1)

    # OG title similarity
    if metadata.get('og_title'):
        normalized_og = normalize_company_name(metadata['og_title'])
        if normalized_og:
            scores['og_title_sim'] = JaroWinkler.similarity(normalized_sponsor, normalized_og)
    elif metadata.get('og_site_name'):
        normalized_og = normalize_company_name(metadata['og_site_name'])
        if normalized_og:
            scores['og_title_sim'] = JaroWinkler.similarity(normalized_sponsor, normalized_og)

    # Token overlap
    combined_text = ' '.join(filter(None, [
        metadata.get('title', ''),
        metadata.get('h1', ''),
        metadata.get('og_title', ''),
        metadata.get('meta_description', '')
    ]))
    scores['token_overlap'] = compute_token_overlap(sponsor_name, combined_text)

    return scores


def compute_enriched_score(scores):
    """Compute combined enriched score."""
    return (
        0.50 * scores['title_sim'] +
        0.25 * scores['h1_sim'] +
        0.15 * scores['og_title_sim'] +
        0.10 * scores['token_overlap']
    )


def process_firecrawl_record(row):
    """Process a single record with Firecrawl."""
    company_id = row.get('company_id', '')
    company_name = row.get('company_name', '')
    url = row.get('url', '')
    sponsor_name = row.get('best_sponsor_name', '') or row.get('canonical_name', '')
    original_score = float(row.get('original_score', 0) or row.get('score', 0) or 0)

    result = {
        'company_id': company_id,
        'company_name': company_name,
        'url': url,
        'sponsor_name': sponsor_name,
        'best_ein_match': row.get('best_ein_match', ''),
        'original_score': original_score,
        'title': None,
        'h1': None,
        'og_title': None,
        'og_site_name': None,
        'meta_description': None,
        'title_sim': 0.0,
        'h1_sim': 0.0,
        'og_title_sim': 0.0,
        'token_overlap': 0.0,
        'enriched_score': 0.0,
        'final_score': original_score,
        'scrape_success': False,
        'upgrade_status': 'UNPROCESSED'
    }

    # Scrape the URL
    html = scrape_with_firecrawl(url)

    if html:
        result['scrape_success'] = True

        # Extract metadata
        metadata = extract_page_metadata(html)
        result.update({
            'title': metadata['title'],
            'h1': metadata['h1'],
            'og_title': metadata['og_title'],
            'og_site_name': metadata['og_site_name'],
            'meta_description': metadata['meta_description']
        })

        # Compute similarity scores
        scores = compute_similarity_scores(sponsor_name, metadata)
        result.update(scores)

        # Compute enriched score
        enriched_score = compute_enriched_score(scores)
        result['enriched_score'] = round(enriched_score, 4)
        result['final_score'] = max(original_score, enriched_score)

        # Determine upgrade status
        if enriched_score >= 0.78:
            result['upgrade_status'] = 'UPGRADED'
        elif enriched_score >= 0.65:
            result['upgrade_status'] = 'CANDIDATE'
        else:
            result['upgrade_status'] = 'FAILURE'
    else:
        result['upgrade_status'] = 'SCRAPE_FAILED'

    return result


def safe_process_firecrawl(row):
    """Wrapper for safe processing."""
    try:
        return {'success': True, 'result': process_firecrawl_record(row)}
    except Exception as e:
        return {
            'success': False,
            'error': str(e)[:100],
            'result': {
                'company_id': row.get('company_id', ''),
                'company_name': row.get('company_name', ''),
                'url': row.get('url', ''),
                'scrape_success': False,
                'upgrade_status': 'ERROR',
                'error': str(e)[:100]
            }
        }


def run_firecrawl_pass(review_df, log):
    """Run Part A: Firecrawl Identity Upgrade."""
    print("\n" + "=" * 70, flush=True)
    print("PART A: FIRECRAWL IDENTITY UPGRADE", flush=True)
    print("=" * 70, flush=True)

    all_results = []
    records = review_df.to_dict('records')
    total_batches = (len(records) + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"\n  Processing {len(records):,} records in batches of {BATCH_SIZE}...", flush=True)

    for batch_num in range(total_batches):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, len(records))
        batch = records[start_idx:end_idx]

        print(f"\n  Batch {batch_num + 1}/{total_batches} ({start_idx+1}-{end_idx})...", flush=True)

        batch_upgraded = 0
        batch_candidates = 0
        batch_failures = 0
        batch_scrape_success = 0

        with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
            futures = {executor.submit(safe_process_firecrawl, row): row for row in batch}

            for future in as_completed(futures):
                result_data = future.result()
                result = result_data['result']
                all_results.append(result)

                if result.get('scrape_success'):
                    batch_scrape_success += 1

                status = result.get('upgrade_status', '')
                if status == 'UPGRADED':
                    batch_upgraded += 1
                elif status == 'CANDIDATE':
                    batch_candidates += 1
                elif status in ['FAILURE', 'SCRAPE_FAILED', 'ERROR']:
                    batch_failures += 1

        print(f"    Scraped: {batch_scrape_success}/{len(batch)}, Upgraded: {batch_upgraded}, Candidates: {batch_candidates}, Failures: {batch_failures}", flush=True)

        # Progress save every 10 batches
        if (batch_num + 1) % 10 == 0:
            progress_df = pd.DataFrame(all_results)
            progress_df.to_csv(os.path.join(OUTPUT_DIR, "firecrawl_progress.csv"), index=False)
            print(f"    [Progress saved: {len(all_results):,} records]", flush=True)

        if batch_num < total_batches - 1:
            time.sleep(BATCH_SLEEP)

    # Split results by status
    results_df = pd.DataFrame(all_results)

    upgraded_df = results_df[results_df['upgrade_status'] == 'UPGRADED']
    candidates_df = results_df[results_df['upgrade_status'] == 'CANDIDATE']
    failures_df = results_df[results_df['upgrade_status'].isin(['FAILURE', 'SCRAPE_FAILED', 'ERROR'])]

    # Save outputs
    print("\n  Saving Firecrawl outputs...", flush=True)

    upgraded_file = os.path.join(OUTPUT_DIR, "firecrawl_upgraded.csv")
    upgraded_df.to_csv(upgraded_file, index=False)
    print(f"    Saved: {upgraded_file} ({len(upgraded_df):,} records)", flush=True)

    candidates_file = os.path.join(OUTPUT_DIR, "firecrawl_candidates.csv")
    candidates_df.to_csv(candidates_file, index=False)
    print(f"    Saved: {candidates_file} ({len(candidates_df):,} records)", flush=True)

    failures_file = os.path.join(OUTPUT_DIR, "firecrawl_failures.csv")
    failures_df.to_csv(failures_file, index=False)
    print(f"    Saved: {failures_file} ({len(failures_df):,} records)", flush=True)

    # Update log
    log['firecrawl_total_processed'] = len(all_results)
    log['firecrawl_upgraded_count'] = len(upgraded_df)
    log['firecrawl_candidates_count'] = len(candidates_df)
    log['firecrawl_failures_count'] = len(failures_df)
    log['firecrawl_scrape_success_count'] = len(results_df[results_df['scrape_success'] == True])

    # Save firecrawl log
    firecrawl_log = {
        'completed_at': datetime.now().isoformat(),
        'total_processed': len(all_results),
        'upgraded': len(upgraded_df),
        'candidates': len(candidates_df),
        'failures': len(failures_df),
        'scrape_success_rate': round(log['firecrawl_scrape_success_count'] / len(all_results) * 100, 2) if all_results else 0
    }

    firecrawl_log_file = os.path.join(LOGS_DIR, "firecrawl_identity_log.json")
    with open(firecrawl_log_file, 'w', encoding='utf-8') as f:
        json.dump(firecrawl_log, f, indent=2)
    print(f"    Saved: {firecrawl_log_file}", flush=True)

    return candidates_df, failures_df


def run_splink_pass(candidates_df, failures_df, log):
    """Run Part C: Splink Advanced Match."""
    print("\n" + "=" * 70, flush=True)
    print("PART C: SPLINK ADVANCED MATCH", flush=True)
    print("=" * 70, flush=True)

    # Combine candidates and failures for Splink
    splink_input_df = pd.concat([candidates_df, failures_df], ignore_index=True)
    print(f"\n  Input records for Splink: {len(splink_input_df):,}", flush=True)

    if len(splink_input_df) == 0:
        print("  No records to process with Splink.", flush=True)
        log['splink_total_processed'] = 0
        log['splink_high_confidence_count'] = 0
        log['splink_medium_confidence_count'] = 0
        log['splink_low_confidence_count'] = 0
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Initialize DuckDB
    print("\n  [1] Initializing DuckDB engine...", flush=True)
    con = duckdb.connect(':memory:')

    # Load DOL datasets
    print("  [2] Loading DOL datasets...", flush=True)

    dol_5500_file = os.path.join(WORK_DIR, "dol_form5500.csv")
    dol_5500sf_file = os.path.join(WORK_DIR, "dol_form5500sf.csv")

    dol_loaded = False
    dol_records = []

    # Try to load DOL files
    for dol_file in [dol_5500_file, dol_5500sf_file]:
        if os.path.exists(dol_file):
            try:
                df = pd.read_csv(dol_file, low_memory=False)
                # Normalize column names
                df.columns = [c.lower().strip() for c in df.columns]

                # Map to standard columns
                col_mapping = {
                    'sponsor_dfe_ein': 'ein',
                    'spons_dfe_ein': 'ein',
                    'ein': 'ein',
                    'sponsor_dfe_name': 'sponsor_name',
                    'spons_dfe_name': 'sponsor_name',
                    'sponsor_name': 'sponsor_name',
                    'spons_dfe_loc_us_address1': 'address',
                    'sponsor_line1_address': 'address',
                    'spons_dfe_loc_us_city': 'city',
                    'spons_dfe_mail_us_city': 'city',
                    'city': 'city',
                    'spons_dfe_loc_us_state': 'state',
                    'spons_dfe_mail_us_state': 'state',
                    'state': 'state',
                    'tot_partcp_boy_cnt': 'participants',
                    'tot_act_partcp_boy_cnt': 'participants',
                    'participants_total': 'participants',
                    'ack_id': 'ack_id'
                }

                standardized = {}
                for old_col, new_col in col_mapping.items():
                    if old_col in df.columns and new_col not in standardized:
                        standardized[new_col] = df[old_col]

                if standardized:
                    std_df = pd.DataFrame(standardized)
                    dol_records.append(std_df)
                    dol_loaded = True
                    print(f"    Loaded: {dol_file} ({len(df):,} records)", flush=True)
            except Exception as e:
                print(f"    Warning: Could not load {dol_file}: {e}", flush=True)

    if not dol_loaded:
        print("  Warning: No DOL files found. Using fallback similarity matching.", flush=True)
        return run_fallback_matching(splink_input_df, log)

    # Combine DOL records
    dol_df = pd.concat(dol_records, ignore_index=True).drop_duplicates()
    print(f"    Combined DOL records: {len(dol_df):,}", flush=True)

    # Try to use Splink, fall back to manual matching if not available
    try:
        from splink import DuckDBAPI, Linker, SettingsCreator, block_on
        import splink.comparison_library as cl

        print("  [3] Configuring Splink...", flush=True)

        # Prepare datasets for Splink
        company_records = splink_input_df[['company_id', 'company_name', 'url', 'best_ein_match']].copy()
        company_records = company_records.rename(columns={
            'company_id': 'unique_id',
            'company_name': 'name',
            'best_ein_match': 'ein'
        })
        company_records['source'] = 'company'
        company_records['state'] = ''
        company_records['city'] = ''

        dol_records_splink = dol_df[['ein', 'sponsor_name', 'state', 'city']].copy()
        dol_records_splink['unique_id'] = dol_records_splink.index.astype(str) + '_dol'
        dol_records_splink = dol_records_splink.rename(columns={'sponsor_name': 'name'})
        dol_records_splink['source'] = 'dol'
        dol_records_splink['url'] = ''

        # Combine for Splink
        combined = pd.concat([company_records, dol_records_splink], ignore_index=True)
        combined['ein'] = combined['ein'].fillna('').astype(str)
        combined['name'] = combined['name'].fillna('')
        combined['state'] = combined['state'].fillna('')
        combined['city'] = combined['city'].fillna('')

        # Register with DuckDB
        con.register('combined_data', combined)

        # Splink settings
        settings = SettingsCreator(
            link_type="link_only",
            comparisons=[
                cl.ExactMatch("ein").configure(term_frequency_adjustments=True),
                cl.JaroWinklerAtThresholds("name", [0.9, 0.8, 0.7]),
                cl.ExactMatch("state"),
                cl.JaroAtThresholds("city", [0.9, 0.8]),
            ],
            blocking_rules_to_generate_predictions=[
                block_on("state"),
                block_on("ein"),
            ],
        )

        db_api = DuckDBAPI(connection=con)
        linker = Linker(combined, settings, db_api=db_api)

        print("  [4] Training Splink model...", flush=True)
        linker.training.estimate_u_using_random_sampling(max_pairs=1e6)
        linker.training.estimate_parameters_using_expectation_maximisation(
            block_on("ein"), estimate_without_term_frequencies=True
        )

        print("  [5] Running predictions...", flush=True)
        predictions = linker.inference.predict(threshold_match_probability=0.5)
        predictions_df = predictions.as_pandas_dataframe()

        print(f"    Generated {len(predictions_df):,} predictions", flush=True)

        # Process predictions
        if len(predictions_df) > 0:
            # Get best match for each company
            company_matches = predictions_df[
                (predictions_df['source_l'] == 'company') | (predictions_df['source_r'] == 'company')
            ].copy()

            company_matches['splink_confidence'] = company_matches['match_probability']

            # Classify by confidence
            high_conf = company_matches[company_matches['splink_confidence'] >= 0.85]
            medium_conf = company_matches[
                (company_matches['splink_confidence'] >= 0.70) &
                (company_matches['splink_confidence'] < 0.85)
            ]
            low_conf = company_matches[company_matches['splink_confidence'] < 0.70]
        else:
            high_conf = pd.DataFrame()
            medium_conf = pd.DataFrame()
            low_conf = splink_input_df.copy()
            low_conf['splink_confidence'] = 0.0

    except ImportError:
        print("  Splink not available. Using fallback matching...", flush=True)
        return run_fallback_matching(splink_input_df, log)
    except Exception as e:
        print(f"  Splink error: {e}. Using fallback matching...", flush=True)
        return run_fallback_matching(splink_input_df, log)

    # Save Splink outputs
    print("\n  [6] Saving Splink outputs...", flush=True)

    high_file = os.path.join(OUTPUT_DIR, "splink_high_confidence.csv")
    high_conf.to_csv(high_file, index=False)
    print(f"    Saved: {high_file} ({len(high_conf):,} records)", flush=True)

    medium_file = os.path.join(OUTPUT_DIR, "splink_medium_confidence.csv")
    medium_conf.to_csv(medium_file, index=False)
    print(f"    Saved: {medium_file} ({len(medium_conf):,} records)", flush=True)

    low_file = os.path.join(OUTPUT_DIR, "splink_low_confidence.csv")
    low_conf.to_csv(low_file, index=False)
    print(f"    Saved: {low_file} ({len(low_conf):,} records)", flush=True)

    # Update log
    log['splink_total_processed'] = len(splink_input_df)
    log['splink_high_confidence_count'] = len(high_conf)
    log['splink_medium_confidence_count'] = len(medium_conf)
    log['splink_low_confidence_count'] = len(low_conf)

    # Save Splink log
    splink_log = {
        'completed_at': datetime.now().isoformat(),
        'total_processed': len(splink_input_df),
        'high_confidence': len(high_conf),
        'medium_confidence': len(medium_conf),
        'low_confidence': len(low_conf)
    }

    splink_log_file = os.path.join(LOGS_DIR, "splink_log.json")
    with open(splink_log_file, 'w', encoding='utf-8') as f:
        json.dump(splink_log, f, indent=2)
    print(f"    Saved: {splink_log_file}", flush=True)

    con.close()

    return high_conf, medium_conf, low_conf


def run_fallback_matching(splink_input_df, log):
    """Fallback matching when Splink is not available."""
    print("\n  Running fallback Jaro-Winkler matching...", flush=True)

    results = []

    for _, row in splink_input_df.iterrows():
        company_name = row.get('company_name', '')
        sponsor_name = row.get('sponsor_name', '') or row.get('best_sponsor_name', '') or row.get('canonical_name', '')
        enriched_score = float(row.get('enriched_score', 0) or 0)

        # Compute additional similarity
        norm_company = normalize_company_name(company_name)
        norm_sponsor = normalize_company_name(sponsor_name)

        if norm_company and norm_sponsor:
            name_sim = JaroWinkler.similarity(norm_company, norm_sponsor)
            token_sim = fuzz.token_set_ratio(norm_company, norm_sponsor) / 100.0
            combined_score = 0.6 * name_sim + 0.4 * token_sim
        else:
            combined_score = enriched_score

        result = row.to_dict()
        result['splink_confidence'] = round(combined_score, 4)
        results.append(result)

    results_df = pd.DataFrame(results)

    # Classify
    high_conf = results_df[results_df['splink_confidence'] >= 0.85]
    medium_conf = results_df[
        (results_df['splink_confidence'] >= 0.70) &
        (results_df['splink_confidence'] < 0.85)
    ]
    low_conf = results_df[results_df['splink_confidence'] < 0.70]

    # Save outputs
    print("\n  Saving fallback matching outputs...", flush=True)

    high_file = os.path.join(OUTPUT_DIR, "splink_high_confidence.csv")
    high_conf.to_csv(high_file, index=False)
    print(f"    Saved: {high_file} ({len(high_conf):,} records)", flush=True)

    medium_file = os.path.join(OUTPUT_DIR, "splink_medium_confidence.csv")
    medium_conf.to_csv(medium_file, index=False)
    print(f"    Saved: {medium_file} ({len(medium_conf):,} records)", flush=True)

    low_file = os.path.join(OUTPUT_DIR, "splink_low_confidence.csv")
    low_conf.to_csv(low_file, index=False)
    print(f"    Saved: {low_file} ({len(low_conf):,} records)", flush=True)

    # Update log
    log['splink_total_processed'] = len(splink_input_df)
    log['splink_high_confidence_count'] = len(high_conf)
    log['splink_medium_confidence_count'] = len(medium_conf)
    log['splink_low_confidence_count'] = len(low_conf)
    log['splink_method'] = 'fallback_jaro_winkler'

    # Save log
    splink_log = {
        'completed_at': datetime.now().isoformat(),
        'method': 'fallback_jaro_winkler',
        'total_processed': len(splink_input_df),
        'high_confidence': len(high_conf),
        'medium_confidence': len(medium_conf),
        'low_confidence': len(low_conf)
    }

    splink_log_file = os.path.join(LOGS_DIR, "splink_log.json")
    with open(splink_log_file, 'w', encoding='utf-8') as f:
        json.dump(splink_log, f, indent=2)
    print(f"    Saved: {splink_log_file}", flush=True)

    return high_conf, medium_conf, low_conf


def run_pipeline():
    """Run the Stage 5 Low Confidence Cleanup pipeline."""
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    start_time = datetime.now()

    print("=" * 70, flush=True)
    print("STAGE 5 LOW CONFIDENCE CLEANUP PIPELINE", flush=True)
    print("=" * 70, flush=True)

    log = {
        'started_at': start_time.isoformat(),
        'total_review_records': 0,
        'firecrawl_upgraded_count': 0,
        'firecrawl_candidates_count': 0,
        'firecrawl_failures_count': 0,
        'splink_high_confidence_count': 0,
        'splink_medium_confidence_count': 0,
        'splink_low_confidence_count': 0,
        'final_unresolved_count': 0,
        'errors': []
    }

    # Load review queue
    print("\n[1] Loading review queue...", flush=True)

    review_queue_file = os.path.join(OUTPUT_DIR, "review_queue.csv")

    if not os.path.exists(review_queue_file):
        print(f"  ERROR: {review_queue_file} not found!", flush=True)
        print("  Please run Stage 2 first.", flush=True)
        return

    review_df = pd.read_csv(review_queue_file)
    log['total_review_records'] = len(review_df)
    print(f"  Loaded: {len(review_df):,} records", flush=True)

    if len(review_df) == 0:
        print("  No records to process.", flush=True)
        return

    # Part A: Firecrawl Identity Upgrade
    candidates_df, failures_df = run_firecrawl_pass(review_df, log)

    # Part C: Splink Advanced Match
    splink_high, splink_medium, splink_low = run_splink_pass(candidates_df, failures_df, log)

    # Final Assembly
    print("\n" + "=" * 70, flush=True)
    print("FINAL OUTPUT ASSEMBLY", flush=True)
    print("=" * 70, flush=True)

    # Load firecrawl upgraded
    upgraded_file = os.path.join(OUTPUT_DIR, "firecrawl_upgraded.csv")
    if os.path.exists(upgraded_file):
        upgraded_df = pd.read_csv(upgraded_file)
        upgraded_df['final_status'] = 'HIGH'
    else:
        upgraded_df = pd.DataFrame()

    # Add final_status to splink results
    if len(splink_high) > 0:
        splink_high = splink_high.copy()
        splink_high['final_status'] = 'HIGH'

    if len(splink_medium) > 0:
        splink_medium = splink_medium.copy()
        splink_medium['final_status'] = 'MEDIUM'

    if len(splink_low) > 0:
        splink_low = splink_low.copy()
        splink_low['final_status'] = 'UNRESOLVED'

    # Create master file
    master_dfs = []
    if len(upgraded_df) > 0:
        master_dfs.append(upgraded_df)
    if len(splink_high) > 0:
        master_dfs.append(splink_high)
    if len(splink_medium) > 0:
        master_dfs.append(splink_medium)
    if len(splink_low) > 0:
        master_dfs.append(splink_low)

    if master_dfs:
        master_df = pd.concat(master_dfs, ignore_index=True)
    else:
        master_df = pd.DataFrame()

    log['final_unresolved_count'] = len(splink_low) if len(splink_low) > 0 else 0

    # Save master file
    master_file = os.path.join(OUTPUT_DIR, "review_cleanup_master.csv")
    master_df.to_csv(master_file, index=False)
    print(f"\n  Saved: {master_file} ({len(master_df):,} records)", flush=True)

    # Calculate run time
    end_time = datetime.now()
    run_time = (end_time - start_time).total_seconds()

    # Save summary
    log['completed_at'] = end_time.isoformat()
    log['run_time_seconds'] = round(run_time, 2)

    summary = {
        'total_review_records': log['total_review_records'],
        'firecrawl_upgraded_count': log['firecrawl_upgraded_count'],
        'splink_high_confidence_count': log['splink_high_confidence_count'],
        'splink_medium_confidence_count': log['splink_medium_confidence_count'],
        'splink_low_confidence_count': log['splink_low_confidence_count'],
        'final_unresolved_count': log['final_unresolved_count'],
        'started_at': log['started_at'],
        'completed_at': log['completed_at'],
        'run_time_seconds': log['run_time_seconds']
    }

    summary_file = os.path.join(OUTPUT_DIR, "low_confidence_cleanup_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    print(f"  Saved: {summary_file}", flush=True)

    # Print summary
    print("\n" + "=" * 70, flush=True)
    print("STAGE 5 COMPLETE", flush=True)
    print("=" * 70, flush=True)
    print(f"Total review records: {log['total_review_records']:,}", flush=True)
    print(f"  Firecrawl upgraded: {log['firecrawl_upgraded_count']:,}", flush=True)
    print(f"  Splink high confidence: {log['splink_high_confidence_count']:,}", flush=True)
    print(f"  Splink medium confidence: {log['splink_medium_confidence_count']:,}", flush=True)
    print(f"  Final unresolved: {log['final_unresolved_count']:,}", flush=True)
    print(f"  Run time: {run_time:.1f} seconds", flush=True)


if __name__ == '__main__':
    run_pipeline()
