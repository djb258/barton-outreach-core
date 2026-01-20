#!/usr/bin/env python3
"""
Company URL Discovery
======================
Discovers and catalogs key pages on company websites.

Finds pages where we can later extract:
- Executive information (leadership, team, about pages)
- Company context (news, press, blog pages)

Usage:
    python discover_company_urls.py [--limit N] [--state XX] [--dry-run]

Examples:
    # Dry run on 10 companies
    python discover_company_urls.py --limit 10 --dry-run

    # Process NC companies
    python discover_company_urls.py --state NC --limit 100

    # Full run
    python discover_company_urls.py
"""

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import requests
from urllib.parse import urljoin, urlparse
import time
import sys
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Neon connection
NEON_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}

# Page paths to probe for each source type
PAGE_PATTERNS = {
    'leadership_page': [
        '/leadership', '/our-leadership', '/executive-team', '/executives',
        '/management', '/management-team', '/our-team', '/team',
        '/about/leadership', '/about/team', '/about/management',
        '/company/leadership', '/company/team',
        '/about-us/leadership', '/about-us/team',
    ],
    'about_page': [
        '/about', '/about-us', '/about-company', '/company',
        '/who-we-are', '/our-story', '/our-company',
        '/about/company', '/about/our-company',
    ],
    'team_page': [
        '/team', '/our-team', '/people', '/our-people', '/staff',
        '/about/people', '/about/team', '/company/people',
    ],
    'press_page': [
        '/press', '/press-room', '/pressroom', '/media', '/media-room',
        '/news', '/newsroom', '/news-room', '/announcements',
        '/press-releases', '/media-center',
        '/about/news', '/about/press', '/company/news',
    ],
    'careers_page': [
        '/careers', '/jobs', '/work-with-us', '/join-us', '/join-our-team',
        '/employment', '/opportunities', '/career-opportunities',
    ],
    'contact_page': [
        '/contact', '/contact-us', '/get-in-touch', '/reach-us',
        '/locations', '/offices', '/find-us',
    ],
}

# Request settings
REQUEST_TIMEOUT = 10
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}


def normalize_url(base_url: str) -> str:
    """Normalize website URL to base form"""
    if not base_url:
        return None

    # Add scheme if missing
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'http://' + base_url

    # Parse and rebuild
    parsed = urlparse(base_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def probe_url(url: str) -> Tuple[bool, int, Optional[str], Optional[str]]:
    """
    Probe a URL to check if it exists.

    Returns: (is_accessible, http_status, final_url, page_title)
    """
    try:
        response = requests.head(
            url,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )

        # If HEAD works, try GET to get title
        if response.status_code == 200:
            try:
                get_response = requests.get(
                    url,
                    headers=REQUEST_HEADERS,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True
                )

                # Extract title
                title = None
                if '<title>' in get_response.text.lower():
                    start = get_response.text.lower().find('<title>') + 7
                    end = get_response.text.lower().find('</title>')
                    if end > start:
                        title = get_response.text[start:end].strip()[:200]

                return True, get_response.status_code, get_response.url, title
            except:
                return True, response.status_code, response.url, None

        # Method not allowed - try GET
        elif response.status_code == 405:
            try:
                get_response = requests.get(
                    url,
                    headers=REQUEST_HEADERS,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True
                )

                title = None
                if get_response.status_code == 200 and '<title>' in get_response.text.lower():
                    start = get_response.text.lower().find('<title>') + 7
                    end = get_response.text.lower().find('</title>')
                    if end > start:
                        title = get_response.text[start:end].strip()[:200]

                return get_response.status_code == 200, get_response.status_code, get_response.url, title
            except:
                return False, 405, url, None

        return False, response.status_code, response.url, None

    except requests.exceptions.Timeout:
        return False, 0, url, None
    except requests.exceptions.ConnectionError:
        return False, 0, url, None
    except Exception as e:
        logger.debug(f"Probe error for {url}: {e}")
        return False, 0, url, None


def normalize_final_url(url: str) -> str:
    """Normalize URL for comparison (remove trailing slash, etc.)"""
    if not url:
        return ''
    parsed = urlparse(url)
    # Reconstruct without trailing slash and lowercase
    path = parsed.path.rstrip('/') or '/'
    return f"{parsed.scheme}://{parsed.netloc}{path}".lower()


def discover_pages(company: Dict, discovered_urls: set) -> List[Dict]:
    """
    Discover key pages for a company.

    Args:
        company: Company dict with website_url, company_unique_id, company_name
        discovered_urls: Set of already discovered URLs (for dedup)

    Returns:
        List of discovered page dicts
    """
    base_url = normalize_url(company['website_url'])
    if not base_url:
        return []

    discovered = []
    company_id = company['company_unique_id']
    found_urls = set()  # Track unique final URLs for this company

    # First, verify base URL is accessible and get canonical homepage
    base_accessible, base_status, homepage_url, _ = probe_url(base_url)
    if not base_accessible:
        logger.debug(f"Base URL not accessible: {base_url} (status: {base_status})")
        return []

    # Normalize homepage for comparison
    homepage_normalized = normalize_final_url(homepage_url or base_url)
    found_urls.add(homepage_normalized)

    # Probe each page type
    for source_type, paths in PAGE_PATTERNS.items():
        found_for_type = False

        for path in paths:
            if found_for_type:
                break  # Only need one URL per type

            full_url = urljoin(base_url, path)

            # Skip if already discovered globally
            if full_url in discovered_urls:
                continue

            is_accessible, status, final_url, title = probe_url(full_url)

            if is_accessible and status == 200:
                # Normalize for comparison
                final_normalized = normalize_final_url(final_url)

                # Skip if this is just the homepage redirect
                if final_normalized == homepage_normalized:
                    continue

                # Skip if we already found this exact URL
                if final_normalized in found_urls:
                    continue

                # Check if redirect stayed on same domain
                final_domain = urlparse(final_url).netloc.lower()
                base_domain = urlparse(base_url).netloc.lower()

                if final_domain == base_domain or final_domain.endswith('.' + base_domain):
                    discovered.append({
                        'company_unique_id': company_id,
                        'source_type': source_type,
                        'source_url': final_url,
                        'page_title': title,
                        'discovered_from': 'crawl',
                        'http_status': status,
                        'is_accessible': True,
                    })
                    discovered_urls.add(full_url)
                    discovered_urls.add(final_url)
                    found_urls.add(final_normalized)
                    found_for_type = True
                    logger.debug(f"Found {source_type}: {final_url}")

            # Small delay between probes
            time.sleep(0.1)

    return discovered


def get_connection():
    """Create a fresh database connection with retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(**NEON_CONFIG)
            conn.autocommit = False
            return conn
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise


def save_discovered_urls(urls_to_save: List[Dict]) -> int:
    """Save discovered URLs with fresh connection (handles SSL drops)."""
    if not urls_to_save:
        return 0

    conn = get_connection()
    cur = conn.cursor()

    try:
        insert_sql = """
            INSERT INTO company.company_source_urls
            (company_unique_id, source_type, source_url, page_title,
             discovered_from, http_status, is_accessible, discovered_at)
            VALUES %s
            ON CONFLICT (company_unique_id, source_url) DO NOTHING
        """

        values = [
            (
                d['company_unique_id'],
                d['source_type'],
                d['source_url'],
                d['page_title'],
                d['discovered_from'],
                d['http_status'],
                d['is_accessible'],
                datetime.now(timezone.utc)
            )
            for d in urls_to_save
        ]

        execute_values(cur, insert_sql, values)
        conn.commit()
        saved_count = len(urls_to_save)
        return saved_count

    except Exception as e:
        logger.error(f"Error saving URLs: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def discover_company_urls(
    limit: Optional[int] = None,
    state: Optional[str] = None,
    dry_run: bool = False,
    batch_size: int = 10  # Smaller batches for better resilience
):
    """
    Main discovery function.

    Args:
        limit: Max companies to process
        state: Filter by state
        dry_run: Preview without saving
        batch_size: Companies per batch (smaller = more resilient)
    """
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print('=' * 70)
    print('COMPANY URL DISCOVERY')
    print('=' * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Limit: {limit or 'None'}")
    print(f"State filter: {state or 'All'}")
    print()

    # Get companies to process (exclude already processed)
    where_clauses = ["cm.website_url IS NOT NULL"]
    params = []

    if state:
        where_clauses.append("cm.address_state = %s")
        params.append(state.upper())

    # Exclude companies we've already processed
    where_clauses.append("""
        NOT EXISTS (
            SELECT 1 FROM company.company_source_urls csu
            WHERE csu.company_unique_id = cm.company_unique_id
        )
    """)

    limit_clause = f"LIMIT {limit}" if limit else ""

    query = f"""
        SELECT
            cm.company_unique_id,
            cm.company_name,
            cm.website_url,
            cm.address_state
        FROM company.company_master cm
        WHERE {' AND '.join(where_clauses)}
        ORDER BY cm.company_name
        {limit_clause}
    """

    cur.execute(query, params)
    companies = cur.fetchall()

    print(f"Companies to process: {len(companies):,}")
    print()

    if len(companies) == 0:
        print("No companies to process.")
        cur.close()
        conn.close()
        return

    # Track stats
    stats = {
        'processed': 0,
        'urls_found': 0,
        'by_type': {},
        'errors': 0,
    }

    # Track all discovered URLs for dedup
    discovered_urls = set()
    all_discovered = []

    # Close initial connection - we'll use fresh connections for saves
    cur.close()
    conn.close()

    # Process in batches
    for i in range(0, len(companies), batch_size):
        batch = companies[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(companies) + batch_size - 1) // batch_size

        print(f"Batch {batch_num}/{total_batches} ({len(batch)} companies)...")

        for company in batch:
            try:
                pages = discover_pages(company, discovered_urls)

                if pages:
                    all_discovered.extend(pages)
                    stats['urls_found'] += len(pages)

                    for page in pages:
                        source_type = page['source_type']
                        stats['by_type'][source_type] = stats['by_type'].get(source_type, 0) + 1

                    logger.info(f"  {company['company_name'][:40]}: {len(pages)} URLs found")

                stats['processed'] += 1

            except Exception as e:
                logger.error(f"Error processing {company['company_name']}: {e}")
                stats['errors'] += 1

        # Save batch if not dry run - uses fresh connection each time
        if not dry_run and all_discovered:
            try:
                saved = save_discovered_urls(all_discovered)
                print(f"  Saved {saved} URLs")
            except Exception as e:
                logger.error(f"Failed to save batch: {e}")
                # Continue processing - URLs will be rediscovered next run
            all_discovered = []

        print(f"  Progress: {stats['processed']}/{len(companies)} ({100*stats['processed']/len(companies):.1f}%)")

    # Final summary
    print()
    print('=' * 70)
    print('RESULTS')
    print('=' * 70)
    print(f"Companies processed: {stats['processed']:,}")
    print(f"URLs discovered: {stats['urls_found']:,}")
    print(f"Errors: {stats['errors']:,}")
    print()
    print("BY TYPE:")
    for source_type, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
        print(f"  {source_type}: {count:,}")

    if dry_run:
        print()
        print("[DRY RUN - No data saved]")

        # Show sample of what would be saved
        if all_discovered:
            print()
            print("SAMPLE DISCOVERIES:")
            for d in all_discovered[:10]:
                print(f"  {d['source_type']}: {d['source_url'][:60]}")


def main():
    parser = argparse.ArgumentParser(description='Discover company URLs for enrichment')
    parser.add_argument('--limit', type=int, help='Limit number of companies')
    parser.add_argument('--state', type=str, help='Filter by state (e.g., NC, PA)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
    parser.add_argument('--batch-size', type=int, default=50, help='Companies per batch')

    args = parser.parse_args()

    discover_company_urls(
        limit=args.limit,
        state=args.state,
        dry_run=args.dry_run,
        batch_size=args.batch_size
    )


if __name__ == '__main__':
    main()
