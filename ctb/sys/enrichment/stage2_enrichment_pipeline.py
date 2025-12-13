#!/usr/bin/env python3
"""
Stage 2 Enrichment Pipeline
============================
Improves match accuracy for ambiguous matches (score 0.50-0.70) using
Firecrawl web scraping and multi-signal similarity scoring.

Inputs:
    - duckdb_matches.csv (from Stage 1)
    - companies.csv (company master with website_url)
    - schedule_a.csv (insurance data for enrichment)

Outputs:
    - enriched_matches.csv (all matches with updated scores)
    - review_queue.csv (LOW_CONFIDENCE matches for manual review)

Usage:
    python stage2_enrichment_pipeline.py [--batch N] [--skip N]

    --batch N   Process only first N ambiguous matches (default: all)
    --skip N    Skip first N ambiguous matches (default: 0)
"""

import csv
import re
import sys
import os
import time
import argparse
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

# Firecrawl API configuration
FIRECRAWL_API_KEY = os.environ.get('FIRECRAWL_API_KEY', 'fc-b936adee5dff4980b7a1e03f0c57562c')
FIRECRAWL_BASE_URL = 'https://api.firecrawl.dev/v1'

# Working directory
WORK_DIR = r"C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core"
OUTPUT_DIR = os.path.join(WORK_DIR, "ctb", "sys", "enrichment", "output")

# Confidence thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.75
MEDIUM_CONFIDENCE_THRESHOLD = 0.60


def normalize_name(name: str) -> str:
    """Normalize company name for comparison."""
    if not name:
        return ""
    name = str(name).upper()
    # Remove common suffixes
    suffixes = [
        r'\bLLC\b', r'\bL\.L\.C\.\b', r'\bINC\b', r'\bINC\.\b',
        r'\bINCORPORATED\b', r'\bCORP\b', r'\bCORP\.\b', r'\bCORPORATION\b',
        r'\bLTD\b', r'\bLTD\.\b', r'\bLIMITED\b', r'\bCO\b', r'\bCO\.\b',
        r'\bCOMPANY\b', r'\bLP\b', r'\bL\.P\.\b', r'\bLLP\b', r'\bL\.L\.P\.\b',
        r'\bPC\b', r'\bP\.C\.\b', r'\bPLLC\b', r'\bP\.L\.L\.C\.\b',
        r'\bNA\b', r'\bN\.A\.\b', r'\bDBA\b', r'\bD/B/A\b', r'\bTHE\b'
    ]
    for suffix in suffixes:
        name = re.sub(suffix, '', name)
    # Remove punctuation and extra whitespace
    name = re.sub(r'[^A-Z0-9\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def jaro_winkler(s1: str, s2: str) -> float:
    """Calculate Jaro-Winkler similarity."""
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    len1, len2 = len(s1), len(s2)
    match_distance = max(len1, len2) // 2 - 1
    if match_distance < 0:
        match_distance = 0

    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0
    transpositions = 0

    for i in range(len1):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len2)
        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    jaro = (matches / len1 + matches / len2 + (matches - transpositions / 2) / matches) / 3

    # Winkler modification
    prefix = 0
    for i in range(min(4, len1, len2)):
        if s1[i] == s2[i]:
            prefix += 1
        else:
            break

    return jaro + prefix * 0.1 * (1 - jaro)


def trigram_similarity(s1: str, s2: str) -> float:
    """Calculate trigram (3-gram) Jaccard similarity."""
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    if len(s1) < 3 or len(s2) < 3:
        return 1.0 if s1 == s2 else 0.0

    def get_trigrams(s):
        s = f"  {s} "  # Pad for edge trigrams
        return set(s[i:i+3] for i in range(len(s) - 2))

    t1 = get_trigrams(s1)
    t2 = get_trigrams(s2)

    intersection = len(t1 & t2)
    union = len(t1 | t2)

    return intersection / union if union > 0 else 0.0


def token_set_overlap(s1: str, s2: str) -> float:
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


def combined_similarity(text: str, canonical: str) -> float:
    """Calculate combined similarity score."""
    text_norm = normalize_name(text)
    canonical_norm = normalize_name(canonical)

    if not text_norm or not canonical_norm:
        return 0.0

    jw = jaro_winkler(text_norm, canonical_norm)
    tg = trigram_similarity(text_norm, canonical_norm)
    ts = token_set_overlap(text_norm, canonical_norm)

    # Weighted average
    return 0.50 * jw + 0.35 * tg + 0.15 * ts


def scrape_direct(url: str) -> Optional[Dict]:
    """
    Scrape a URL directly using requests + BeautifulSoup.
    Fallback when Firecrawl is unavailable.
    """
    if not url:
        return None

    # Ensure URL has protocol
    if not url.startswith('http'):
        url = f"https://{url}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        result = {
            'title': '',
            'h1': '',
            'og_title': '',
            'og_site_name': '',
            'description': ''
        }

        # Get title
        title_tag = soup.find('title')
        if title_tag:
            result['title'] = title_tag.get_text(strip=True)

        # Get first H1
        h1_tag = soup.find('h1')
        if h1_tag:
            result['h1'] = h1_tag.get_text(strip=True)

        # Get og:title
        og_title = soup.find('meta', property='og:title')
        if og_title:
            result['og_title'] = og_title.get('content', '')

        # Get og:site_name
        og_site = soup.find('meta', property='og:site_name')
        if og_site:
            result['og_site_name'] = og_site.get('content', '')

        # Get description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            result['description'] = meta_desc.get('content', '')

        return result

    except Exception as e:
        # Silently fail
        return None


def scrape_with_firecrawl(url: str) -> Optional[Dict]:
    """
    Scrape a URL using Firecrawl API with fallback to direct scraping.
    Returns extracted metadata or None on failure.
    """
    if not url:
        return None

    # Ensure URL has protocol
    if not url.startswith('http'):
        url = f"https://{url}"

    # Try direct scraping first (faster, no API needed)
    result = scrape_direct(url)
    if result and (result.get('title') or result.get('h1')):
        return result

    # Fallback to Firecrawl if direct fails
    headers = {
        'Authorization': f'Bearer {FIRECRAWL_API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'url': url,
        'formats': ['html'],
        'onlyMainContent': False,
        'timeout': 30000
    }

    try:
        response = requests.post(
            f"{FIRECRAWL_BASE_URL}/scrape",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return extract_metadata(data.get('data', {}))
            return None
        elif response.status_code == 429:
            # Rate limited - wait and retry once
            time.sleep(2)
            response = requests.post(
                f"{FIRECRAWL_BASE_URL}/scrape",
                headers=headers,
                json=payload,
                timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return extract_metadata(data.get('data', {}))
        return None

    except Exception:
        return None


def extract_metadata(data: Dict) -> Dict:
    """Extract relevant metadata from Firecrawl response."""
    metadata = data.get('metadata', {})
    html = data.get('html', '')

    result = {
        'title': '',
        'h1': '',
        'og_title': '',
        'og_site_name': '',
        'description': ''
    }

    # Get title from metadata
    result['title'] = metadata.get('title', '')

    # Get og tags
    result['og_title'] = metadata.get('ogTitle', '')
    result['og_site_name'] = metadata.get('ogSiteName', '')
    result['description'] = metadata.get('description', '')

    # Extract first H1 from HTML
    if html:
        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html, re.IGNORECASE)
        if h1_match:
            result['h1'] = h1_match.group(1).strip()

    return result


def calculate_enriched_score(metadata: Dict, canonical_name: str) -> Tuple[float, Dict]:
    """
    Calculate enriched score from scraped metadata.
    Returns (score, detail_dict)
    """
    scores = {
        'title_sim': 0.0,
        'h1_sim': 0.0,
        'og_title_sim': 0.0,
        'og_site_name_sim': 0.0,
        'token_overlap': 0.0
    }

    if not metadata or not canonical_name:
        return 0.0, scores

    # Calculate individual similarities
    if metadata.get('title'):
        scores['title_sim'] = combined_similarity(metadata['title'], canonical_name)

    if metadata.get('h1'):
        scores['h1_sim'] = combined_similarity(metadata['h1'], canonical_name)

    if metadata.get('og_title'):
        scores['og_title_sim'] = combined_similarity(metadata['og_title'], canonical_name)

    if metadata.get('og_site_name'):
        scores['og_site_name_sim'] = combined_similarity(metadata['og_site_name'], canonical_name)

    # Token overlap on best available text
    best_text = metadata.get('title') or metadata.get('h1') or metadata.get('og_title') or ''
    scores['token_overlap'] = token_set_overlap(
        normalize_name(best_text),
        normalize_name(canonical_name)
    )

    # Combined enriched score
    enriched_score = (
        0.50 * scores['title_sim'] +
        0.30 * scores['h1_sim'] +
        0.10 * scores['og_title_sim'] +
        0.10 * scores['token_overlap']
    )

    return enriched_score, scores


def classify_confidence(score: float) -> str:
    """Classify match confidence based on score."""
    if score >= HIGH_CONFIDENCE_THRESHOLD:
        return "HIGH_CONFIDENCE"
    elif score >= MEDIUM_CONFIDENCE_THRESHOLD:
        return "MEDIUM_CONFIDENCE"
    else:
        return "LOW_CONFIDENCE"


def load_csv(filepath: str) -> List[Dict]:
    """Load CSV file into list of dicts."""
    rows = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def get_company_url(company_id: str, companies: List[Dict]) -> Optional[str]:
    """Get website URL for a company from companies.csv."""
    for company in companies:
        if company.get('company_unique_id') == company_id:
            return company.get('website_url') or company.get('domain') or None
    return None


def run_pipeline(batch_limit: int = None, skip: int = 0):
    """Run the Stage 2 enrichment pipeline.

    Args:
        batch_limit: Process only first N ambiguous matches (None = all)
        skip: Skip first N ambiguous matches
    """
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 70)
    print("STAGE 2 ENRICHMENT PIPELINE")
    print("=" * 70)
    if batch_limit:
        print(f"  BATCH MODE: Processing {batch_limit} records (skip={skip})")

    # =========================================================================
    # STEP 1: Load input files
    # =========================================================================
    print("\n[1] Loading input files...")

    matches_file = os.path.join(OUTPUT_DIR, "duckdb_matches.csv")
    companies_file = os.path.join(WORK_DIR, "companies_with_urls.csv")
    schedule_a_file = os.path.join(WORK_DIR, "schedule_a.csv")

    matches = load_csv(matches_file)
    companies = load_csv(companies_file)
    schedule_a = load_csv(schedule_a_file)

    print(f"  Loaded matches: {len(matches):,}")
    print(f"  Loaded companies: {len(companies):,}")
    print(f"  Loaded schedule_a: {len(schedule_a):,}")

    # Build company lookup
    company_lookup = {c.get('company_unique_id'): c for c in companies}

    # =========================================================================
    # STEP 2: Filter ambiguous matches (0.50 <= score < 0.70)
    # =========================================================================
    print("\n[2] Filtering ambiguous matches (0.50 <= score < 0.70)...")

    ambiguous_matches = []
    high_confidence = []
    other_matches = []

    for match in matches:
        score = float(match.get('score', 0))
        if 0.50 <= score < 0.70:
            ambiguous_matches.append(match)
        elif score >= 0.70:
            high_confidence.append(match)
        else:
            other_matches.append(match)

    print(f"  Ambiguous (0.50-0.70): {len(ambiguous_matches):,}")
    print(f"  High confidence (>=0.70): {len(high_confidence):,}")
    print(f"  Below threshold (<0.50): {len(other_matches):,}")

    # Apply batch limits
    if skip > 0:
        ambiguous_matches = ambiguous_matches[skip:]
        print(f"  After skip({skip}): {len(ambiguous_matches):,}")
    if batch_limit:
        ambiguous_matches = ambiguous_matches[:batch_limit]
        print(f"  After batch limit({batch_limit}): {len(ambiguous_matches):,}")

    # =========================================================================
    # STEP 3: Enrich ambiguous matches with Firecrawl
    # =========================================================================
    print("\n[3] Enriching ambiguous matches with Firecrawl...")
    print(f"  Processing {len(ambiguous_matches):,} records...")

    enriched_results = []
    processed = 0
    enriched_count = 0
    failed_count = 0

    for match in ambiguous_matches:
        company_id = match.get('company_id')
        company_name = match.get('company_name', '')
        original_score = float(match.get('score', 0))
        canonical_name = match.get('canonical_name', match.get('best_sponsor_name', ''))
        ein = match.get('best_ein_match', '')

        # Get company URL
        company = company_lookup.get(company_id, {})
        url = company.get('website_url') or company.get('domain')

        result = {
            'company_id': company_id,
            'company_name': company_name,
            'best_ein_match': ein,
            'best_sponsor_name': match.get('best_sponsor_name', ''),
            'canonical_name': canonical_name,
            'original_score': original_score,
            'enriched_score': 0.0,
            'final_score': original_score,
            'title_sim': 0.0,
            'h1_sim': 0.0,
            'og_title_sim': 0.0,
            'token_overlap': 0.0,
            'scraped_title': '',
            'scraped_h1': '',
            'url': url or '',
            'scrape_success': False,
            'confidence': classify_confidence(original_score)
        }

        if url:
            metadata = scrape_with_firecrawl(url)
            if metadata:
                enriched_score, scores = calculate_enriched_score(metadata, canonical_name)
                result['enriched_score'] = round(enriched_score, 4)
                result['final_score'] = round(max(original_score, enriched_score), 4)
                result['title_sim'] = round(scores['title_sim'], 4)
                result['h1_sim'] = round(scores['h1_sim'], 4)
                result['og_title_sim'] = round(scores['og_title_sim'], 4)
                result['token_overlap'] = round(scores['token_overlap'], 4)
                result['scraped_title'] = metadata.get('title', '')[:100]
                result['scraped_h1'] = metadata.get('h1', '')[:100]
                result['scrape_success'] = True
                result['confidence'] = classify_confidence(result['final_score'])
                enriched_count += 1
            else:
                failed_count += 1
        else:
            failed_count += 1

        enriched_results.append(result)
        processed += 1

        if processed % 50 == 0:
            print(f"  Processed {processed:,}/{len(ambiguous_matches):,} "
                  f"(enriched: {enriched_count:,}, failed: {failed_count:,})")

        # Rate limiting - Firecrawl has limits
        time.sleep(0.5)

    print(f"\n  Enrichment complete:")
    print(f"    Successfully enriched: {enriched_count:,}")
    print(f"    Failed/no URL: {failed_count:,}")

    # =========================================================================
    # STEP 4: Combine all results
    # =========================================================================
    print("\n[4] Combining results...")

    all_results = []

    # Add high confidence matches (no enrichment needed)
    for match in high_confidence:
        score = float(match.get('score', 0))
        all_results.append({
            'company_id': match.get('company_id'),
            'company_name': match.get('company_name', ''),
            'best_ein_match': match.get('best_ein_match', ''),
            'best_sponsor_name': match.get('best_sponsor_name', ''),
            'canonical_name': match.get('canonical_name', ''),
            'original_score': score,
            'enriched_score': 0.0,
            'final_score': score,
            'confidence': classify_confidence(score),
            'scrape_success': False,
            'url': ''
        })

    # Add enriched results
    all_results.extend(enriched_results)

    # Add below-threshold matches
    for match in other_matches:
        score = float(match.get('score', 0))
        all_results.append({
            'company_id': match.get('company_id'),
            'company_name': match.get('company_name', ''),
            'best_ein_match': match.get('best_ein_match', ''),
            'best_sponsor_name': match.get('best_sponsor_name', ''),
            'canonical_name': match.get('canonical_name', ''),
            'original_score': score,
            'enriched_score': 0.0,
            'final_score': score,
            'confidence': classify_confidence(score),
            'scrape_success': False,
            'url': ''
        })

    # =========================================================================
    # STEP 5: Analyze results
    # =========================================================================
    print("\n[5] Analyzing results...")

    # Count confidence levels
    confidence_counts = {'HIGH_CONFIDENCE': 0, 'MEDIUM_CONFIDENCE': 0, 'LOW_CONFIDENCE': 0}
    upgraded_count = 0

    for result in all_results:
        confidence_counts[result['confidence']] += 1
        if result.get('enriched_score', 0) > result.get('original_score', 0):
            upgraded_count += 1

    print(f"\n  CONFIDENCE DISTRIBUTION:")
    print(f"    HIGH_CONFIDENCE:   {confidence_counts['HIGH_CONFIDENCE']:,}")
    print(f"    MEDIUM_CONFIDENCE: {confidence_counts['MEDIUM_CONFIDENCE']:,}")
    print(f"    LOW_CONFIDENCE:    {confidence_counts['LOW_CONFIDENCE']:,}")
    print(f"\n  Upgraded by enrichment: {upgraded_count:,}")

    # =========================================================================
    # STEP 6: Save output files
    # =========================================================================
    print("\n[6] Saving output files...")

    # Save enriched_matches.csv (all results)
    enriched_file = os.path.join(OUTPUT_DIR, "enriched_matches.csv")
    fieldnames = [
        'company_id', 'company_name', 'best_ein_match', 'best_sponsor_name',
        'canonical_name', 'original_score', 'enriched_score', 'final_score',
        'confidence', 'scrape_success', 'url'
    ]

    with open(enriched_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for result in sorted(all_results, key=lambda x: x['final_score'], reverse=True):
            writer.writerow(result)

    print(f"  Saved: {enriched_file}")
    print(f"         ({len(all_results):,} records)")

    # Save review_queue.csv (LOW_CONFIDENCE only)
    review_file = os.path.join(OUTPUT_DIR, "review_queue.csv")
    review_queue = [r for r in all_results if r['confidence'] == 'LOW_CONFIDENCE']

    with open(review_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for result in sorted(review_queue, key=lambda x: x['final_score'], reverse=True):
            writer.writerow(result)

    print(f"  Saved: {review_file}")
    print(f"         ({len(review_queue):,} records)")

    # Save detailed enrichment results (for debugging)
    detailed_file = os.path.join(OUTPUT_DIR, "enrichment_details.csv")
    detail_fields = [
        'company_id', 'company_name', 'best_ein_match', 'canonical_name',
        'original_score', 'enriched_score', 'final_score', 'confidence',
        'title_sim', 'h1_sim', 'og_title_sim', 'token_overlap',
        'scraped_title', 'scraped_h1', 'url', 'scrape_success'
    ]

    with open(detailed_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=detail_fields, extrasaction='ignore')
        writer.writeheader()
        for result in enriched_results:
            writer.writerow(result)

    print(f"  Saved: {detailed_file}")
    print(f"         ({len(enriched_results):,} records)")

    # =========================================================================
    # STEP 7: Summary
    # =========================================================================
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"Total records processed: {len(all_results):,}")
    print(f"Ambiguous matches enriched: {len(ambiguous_matches):,}")
    print(f"Successfully scraped: {enriched_count:,}")
    print(f"Upgraded by enrichment: {upgraded_count:,}")
    print(f"\nFinal distribution:")
    print(f"  HIGH_CONFIDENCE:   {confidence_counts['HIGH_CONFIDENCE']:,}")
    print(f"  MEDIUM_CONFIDENCE: {confidence_counts['MEDIUM_CONFIDENCE']:,}")
    print(f"  LOW_CONFIDENCE:    {confidence_counts['LOW_CONFIDENCE']:,}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Stage 2 Enrichment Pipeline')
    parser.add_argument('--batch', type=int, default=None,
                        help='Process only first N ambiguous matches')
    parser.add_argument('--skip', type=int, default=0,
                        help='Skip first N ambiguous matches')
    args = parser.parse_args()

    run_pipeline(batch_limit=args.batch, skip=args.skip)
