#!/usr/bin/env python3
"""
URL Pattern Discovery Script v4 - Optimized Threading

Discovers leadership/team/about URLs for companies that don't have them.
Uses optimized threading for speed with reliability.

Cost: FREE ($0.00)
"""

import os
import sys
import logging
import threading
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict

import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging with immediate flush
import sys
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

# Disable noisy logging
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)

# Suppress SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Thread-safe stats
STATS_LOCK = threading.Lock()
STATS = {
    'companies_processed': 0,
    'urls_found': 0,
    'urls_saved': 0,
}

def increment_stat(key: str, value: int = 1):
    with STATS_LOCK:
        STATS[key] += value

# Minimal URL patterns for speed (only 1-2 per type)
URL_PATTERNS = {
    'leadership_page': ['/about-us'],
    'team_page': ['/team'],
    'about_page': ['/about'],
}

# Speed optimized settings
REQUEST_TIMEOUT = 3
MAX_WORKERS = 50
BATCH_SIZE = 100
MAX_COMPANIES = 50000

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'


def get_db_connection():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )


def get_session():
    """Get a requests session with retry logic."""
    session = requests.Session()
    retry = Retry(total=1, backoff_factor=0.1)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session

def check_url(url: str) -> tuple:
    """Check if URL exists. Returns (success, final_url, status)."""
    try:
        session = get_session()
        response = session.get(
            url,
            headers={'User-Agent': USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
            verify=False  # Disable SSL verification for sites with cert issues
        )
        session.close()

        if response.status_code == 200 and len(response.text) > 500:
            lower_text = response.text.lower()[:2000]
            # Skip 404 pages, suspended pages, parked domains
            if any(x in lower_text for x in ['404', 'not found', 'suspended', 'parked', 'cgi-sys', 'this domain']):
                return False, None, 404
            # Skip if redirected to a different domain (likely parked/suspended)
            final_url = str(response.url)
            if 'suspendedpage' in final_url or 'cgi-sys' in final_url:
                return False, None, 404
            return True, final_url, 200
        return False, None, response.status_code
    except:
        return False, None, None


def discover_company_urls(company: dict) -> dict:
    """Discover URLs for a company using sync HTTP."""

    result = {
        'doctrine_company_id': company['doctrine_company_id'],
        'domain': company['domain'],
        'urls': []
    }

    domain = company['domain']

    for source_type, patterns in URL_PATTERNS.items():
        found = False

        for pattern in patterns:
            if found:
                break

            # Try domain first, then www
            for base in [f'https://{domain}', f'https://www.{domain}']:
                url = f'{base}{pattern}'
                success, final_url, status = check_url(url)

                if success:
                    result['urls'].append({
                        'source_type': source_type,
                        'source_url': final_url or url,
                        'http_status': status
                    })
                    increment_stat('urls_found')
                    found = True
                    break

    increment_stat('companies_processed')
    return result


def save_batch_urls(results: List[dict]) -> int:
    """Save URLs to database using batch insert."""

    now = datetime.now(timezone.utc)
    records = []

    for result in results:
        for url_info in result.get('urls', []):
            records.append((
                result['doctrine_company_id'],
                url_info['source_type'],
                url_info['source_url'],
                now,
                'url_pattern_discovery',
                now,
                url_info['http_status'],
                True,
                'pending',
                now,
            ))

    if not records:
        return 0

    saved = 0
    conn = get_db_connection()
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            company_ids = list(set(r[0] for r in records))
            # Check for existing source_urls (unique constraint)
            cur.execute("""
                SELECT company_unique_id, source_url
                FROM company.company_source_urls
                WHERE company_unique_id = ANY(%s)
            """, (company_ids,))
            existing_urls = set((row[0], row[1]) for row in cur.fetchall())

            # Filter out duplicates and track URLs we're inserting
            new_records = []
            inserting_urls = set()
            for r in records:
                key = (r[0], r[2])  # company_id, source_url
                if key not in existing_urls and key not in inserting_urls:
                    new_records.append(r)
                    inserting_urls.add(key)

            if new_records:
                # Use ON CONFLICT DO NOTHING to handle any remaining edge cases
                for record in new_records:
                    try:
                        cur.execute("""
                            INSERT INTO company.company_source_urls (
                                company_unique_id, source_type, source_url,
                                discovered_at, discovered_from, last_checked_at,
                                http_status, is_accessible, extraction_status, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (company_unique_id, source_url) DO NOTHING
                        """, record)
                        saved += 1
                    except Exception:
                        pass  # Skip any remaining duplicates
    except Exception as e:
        logger.error(f"DB error: {e}")
    finally:
        conn.close()

    return saved


def get_companies_without_urls(conn, limit: int) -> List[dict]:
    """Get Hunter companies needing URL discovery - verified domains."""

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Use hunter_company as source - these are verified domains
        cur.execute("""
            WITH has_urls AS (
                SELECT DISTINCT hc.domain
                FROM enrichment.hunter_company hc
                JOIN company.company_master cm
                    ON LOWER(hc.domain) = LOWER(REGEXP_REPLACE(REGEXP_REPLACE(cm.website_url, '^https?://', ''), '/.*$', ''))
                JOIN company.company_source_urls cu ON cm.company_unique_id = cu.company_unique_id
                WHERE cu.source_type IN ('leadership_page', 'team_page', 'about_page')
            )
            SELECT DISTINCT
                hc.domain,
                hc.company_unique_id as doctrine_company_id
            FROM enrichment.hunter_company hc
            WHERE hc.domain IS NOT NULL
              AND hc.domain <> ''
              AND hc.domain NOT IN (SELECT domain FROM has_urls)
            ORDER BY hc.domain
            LIMIT %s
        """, (limit,))
        return cur.fetchall()


def main():
    """Main execution."""

    logger.info("=" * 70)
    logger.info("URL PATTERN DISCOVERY v4 - Optimized Threading")
    logger.info("=" * 70)
    logger.info(f"Workers: {MAX_WORKERS}, Timeout: {REQUEST_TIMEOUT}s, Batch: {BATCH_SIZE}")
    logger.info("Cost: $0.00 (FREE)")
    logger.info("")

    try:
        logger.info("Connecting to database...")
        conn = get_db_connection()
        logger.info("Connected")

        logger.info("Finding companies without URLs...")
        companies = get_companies_without_urls(conn, MAX_COMPANIES)
        conn.close()

        total = len(companies)
        logger.info(f"Found {total:,} companies to process")

        if not companies:
            return

        logger.info("-" * 70)
        logger.info(f"Processing with {MAX_WORKERS} workers...")

        for batch_start in range(0, total, BATCH_SIZE):
            batch = companies[batch_start:batch_start + BATCH_SIZE]
            batch_results = []

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {executor.submit(discover_company_urls, c): c for c in batch}
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        batch_results.append(result)
                    except Exception as e:
                        logger.debug(f"Error: {e}")

            saved = save_batch_urls(batch_results)
            increment_stat('urls_saved', saved)

            processed = min(batch_start + BATCH_SIZE, total)
            logger.info(
                f"  Processed {processed:,}/{total:,} - "
                f"Found {STATS['urls_found']:,} URLs, Saved {STATS['urls_saved']:,}"
            )

        logger.info("-" * 70)
        logger.info("RESULTS")
        logger.info("-" * 70)
        logger.info(f"Companies processed: {STATS['companies_processed']:,}")
        logger.info(f"URLs found: {STATS['urls_found']:,}")
        logger.info(f"URLs saved: {STATS['urls_saved']:,}")
        logger.info("Cost: $0.00")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
