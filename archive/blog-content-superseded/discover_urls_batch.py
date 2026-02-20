#!/usr/bin/env python3
"""
Batch URL Discovery (Parallelized)
===================================
High-speed company URL discovery using concurrent requests.

Usage:
    doppler run -- python discover_urls_batch.py --state NC --workers 20
    doppler run -- python discover_urls_batch.py --all-states --workers 30

Examples:
    # Process NC with 20 parallel workers
    doppler run -- python discover_urls_batch.py --state NC --workers 20

    # Process all states
    doppler run -- python discover_urls_batch.py --all-states --workers 30
"""

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import requests
from urllib.parse import urljoin, urlparse
import sys
import argparse
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Thread-safe counter
class Counter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self, n=1):
        with self.lock:
            self.value += n
            return self.value

NEON_CONFIG = {
    'host': os.environ.get('NEON_HOST', 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech'),
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': os.environ.get('NEON_PASSWORD', 'npg_OsE4Z2oPCpiT'),
    'sslmode': 'require'
}

PAGE_PATTERNS = {
    'leadership_page': ['/leadership', '/our-leadership', '/executive-team', '/executives', '/management', '/about/leadership', '/about/team'],
    'about_page': ['/about', '/about-us', '/company', '/who-we-are', '/our-story'],
    'team_page': ['/team', '/our-team', '/people', '/staff'],
    'press_page': ['/press', '/news', '/newsroom', '/media', '/announcements'],
    'careers_page': ['/careers', '/jobs', '/work-with-us', '/join-us'],
    'contact_page': ['/contact', '/contact-us', '/locations'],
}

REQUEST_TIMEOUT = 5  # Faster timeout
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
}


def normalize_url(base_url: str) -> str:
    if not base_url:
        return None
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url
    parsed = urlparse(base_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def probe_url(url: str) -> Tuple[bool, int, Optional[str], Optional[str]]:
    """Quick probe - just HEAD request, no title extraction for speed."""
    try:
        response = requests.head(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if response.status_code == 200:
            return True, 200, response.url, None
        elif response.status_code == 405:
            # Try GET
            response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            return response.status_code == 200, response.status_code, response.url, None
        return False, response.status_code, response.url, None
    except:
        return False, 0, url, None


def discover_company(company: Dict) -> List[Dict]:
    """Discover URLs for a single company."""
    base_url = normalize_url(company['website_url'])
    if not base_url:
        return []

    discovered = []
    company_id = company['company_unique_id']
    found_urls = set()

    # Check base URL
    base_ok, _, homepage_url, _ = probe_url(base_url)
    if not base_ok:
        return []

    homepage_norm = urlparse(homepage_url or base_url).path.rstrip('/') or '/'
    found_urls.add(homepage_norm.lower())

    for source_type, paths in PAGE_PATTERNS.items():
        for path in paths:
            full_url = urljoin(base_url, path)
            is_ok, status, final_url, title = probe_url(full_url)

            if is_ok and status == 200:
                final_path = urlparse(final_url).path.rstrip('/') or '/'
                if final_path.lower() in found_urls:
                    continue

                # Check same domain
                final_domain = urlparse(final_url).netloc.lower()
                base_domain = urlparse(base_url).netloc.lower()
                if final_domain != base_domain and not final_domain.endswith('.' + base_domain):
                    continue

                discovered.append({
                    'company_unique_id': company_id,
                    'source_type': source_type,
                    'source_url': final_url,
                    'page_title': title,
                    'discovered_from': 'crawl',
                    'http_status': status,
                    'is_accessible': True,
                })
                found_urls.add(final_path.lower())
                break  # One URL per type

    return discovered


def save_batch(urls: List[Dict]) -> int:
    if not urls:
        return 0

    conn = psycopg2.connect(**NEON_CONFIG)
    cur = conn.cursor()

    try:
        execute_values(cur, """
            INSERT INTO company.company_source_urls
            (company_unique_id, source_type, source_url, page_title, discovered_from, http_status, is_accessible, discovered_at)
            VALUES %s
            ON CONFLICT (company_unique_id, source_url) DO NOTHING
        """, [(d['company_unique_id'], d['source_type'], d['source_url'], d['page_title'],
               d['discovered_from'], d['http_status'], d['is_accessible'], datetime.now(timezone.utc)) for d in urls])
        conn.commit()
        return len(urls)
    finally:
        cur.close()
        conn.close()


def run_batch(state: Optional[str] = None, workers: int = 20, limit: Optional[int] = None):
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    conn = psycopg2.connect(**NEON_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print('=' * 60)
    print('BATCH URL DISCOVERY')
    print('=' * 60)
    print(f"State: {state or 'ALL'}")
    print(f"Workers: {workers}")
    print()

    # Get companies
    where = ["cm.website_url IS NOT NULL",
             "NOT EXISTS (SELECT 1 FROM company.company_source_urls csu WHERE csu.company_unique_id = cm.company_unique_id)"]
    params = []

    if state:
        where.append("cm.address_state = %s")
        params.append(state.upper())

    limit_sql = f"LIMIT {limit}" if limit else ""

    cur.execute(f"""
        SELECT company_unique_id, company_name, website_url, address_state
        FROM company.company_master cm
        WHERE {' AND '.join(where)}
        ORDER BY company_name
        {limit_sql}
    """, params)

    companies = cur.fetchall()
    cur.close()
    conn.close()

    total = len(companies)
    print(f"Companies to process: {total:,}")
    print()

    if total == 0:
        print("Nothing to process!")
        return

    # Process in chunks - more reliable than trying to save during parallel execution
    chunk_size = 200
    total_urls = 0
    total_processed = 0

    print(f"Processing {total:,} companies in chunks of {chunk_size} with {workers} workers...", flush=True)

    for chunk_start in range(0, total, chunk_size):
        chunk = companies[chunk_start:chunk_start + chunk_size]
        chunk_num = chunk_start // chunk_size + 1
        total_chunks = (total + chunk_size - 1) // chunk_size

        chunk_urls = []

        # Process chunk in parallel
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(discover_company, c) for c in chunk]
            for future in as_completed(futures):
                try:
                    urls = future.result()
                    if urls:
                        chunk_urls.extend(urls)
                except Exception as e:
                    pass  # Skip failed companies

        total_processed += len(chunk)

        # Save chunk
        if chunk_urls:
            saved = save_batch(chunk_urls)
            total_urls += saved
            print(f"  [{chunk_num}/{total_chunks}] {total_processed:,}/{total:,} companies ({100*total_processed/total:.0f}%) | +{saved} URLs | Total: {total_urls:,}", flush=True)
        else:
            print(f"  [{chunk_num}/{total_chunks}] {total_processed:,}/{total:,} companies ({100*total_processed/total:.0f}%) | 0 URLs", flush=True)

    print()
    print('=' * 60)
    print('RESULTS')
    print('=' * 60)
    print(f"Companies processed: {total_processed:,}")
    print(f"URLs discovered: {total_urls:,}")
    print(f"Avg per company: {total_urls/total_processed:.1f}" if total_processed else "")


def main():
    parser = argparse.ArgumentParser(description='Batch URL discovery')
    parser.add_argument('--state', type=str, help='State to process (e.g., NC)')
    parser.add_argument('--all-states', action='store_true', help='Process all states')
    parser.add_argument('--workers', type=int, default=20, help='Parallel workers (default: 20)')
    parser.add_argument('--limit', type=int, help='Limit companies')

    args = parser.parse_args()

    if args.all_states:
        for state in ['NC', 'PA', 'OH', 'VA', 'MD', 'KY', 'OK', 'DE', 'WV']:
            print(f"\n{'#' * 60}")
            print(f"# PROCESSING: {state}")
            print(f"{'#' * 60}\n")
            run_batch(state=state, workers=args.workers, limit=args.limit)
    else:
        run_batch(state=args.state, workers=args.workers, limit=args.limit)


if __name__ == '__main__':
    main()
