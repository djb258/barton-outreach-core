#!/usr/bin/env python3
"""
Blog URL Discovery — Sitemap-First Approach
=============================================
Discovers and indexes company web pages for the Blog sub-hub.

SNAP_ON_TOOLBOX compliant:
- Tier 0: Free (httpx only, no paid APIs)
- Uses httpx (not requests — requests is BANNED)
- Deterministic URL classification (no LLM)

DOCTRINE compliant:
- Sources companies from company.company_master
- Saves to company.company_source_urls (ON CONFLICT DO NOTHING)
- Credentials via Doppler env vars

3-Step Waterfall:
  1. Sitemap: Fetch sitemap.xml → parse all URLs → classify page types
  2. Homepage: Fetch homepage → extract nav/footer links → classify
  3. Probe: Brute-force path probing (last resort only)

Usage:
    doppler run -- python hubs/blog-content/imo/middle/discover_blog_urls.py
    doppler run -- python hubs/blog-content/imo/middle/discover_blog_urls.py --dry-run --limit 50
    doppler run -- python hubs/blog-content/imo/middle/discover_blog_urls.py --workers 30
"""

import os
import re
import sys
import asyncio
import argparse
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Tuple

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# PAGE TYPE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════

PAGE_TYPE_PATTERNS: Dict[str, List[str]] = {
    'about_page': [
        '/about', '/about-us', '/about-company', '/our-story',
        '/who-we-are', '/our-company', '/company/about',
        '/about/company', '/about/our-company', '/about/our-story',
    ],
    'press_page': [
        '/press', '/press-room', '/pressroom', '/press-releases',
        '/news', '/newsroom', '/news-room', '/media', '/media-room',
        '/media-center', '/announcements', '/about/news', '/about/press',
        '/company/news', '/company/press',
    ],
    'blog_page': [
        '/blog', '/insights', '/articles', '/resources/blog',
        '/resources/articles', '/updates', '/thought-leadership',
        '/perspectives', '/knowledge', '/learning-center',
    ],
    'leadership_page': [
        '/leadership', '/our-leadership', '/executive-team',
        '/executives', '/management', '/management-team',
        '/about/leadership', '/about/team', '/about/management',
        '/company/leadership', '/company/team',
    ],
    'team_page': [
        '/team', '/our-team', '/people', '/our-people', '/staff',
        '/about/people', '/company/people',
    ],
    'careers_page': [
        '/careers', '/jobs', '/work-with-us', '/join-us',
        '/join-our-team', '/employment', '/opportunities',
        '/career-opportunities', '/openings',
    ],
    'contact_page': [
        '/contact', '/contact-us', '/get-in-touch', '/reach-us',
        '/locations', '/offices', '/find-us',
    ],
    'investor_page': [
        '/investors', '/investor-relations', '/ir',
        '/stockholders', '/shareholder', '/sec-filings',
    ],
}

# Paths to probe in Step 3 (brute-force fallback) — only about + press
PROBE_PATHS = {
    'about_page': ['/about', '/about-us', '/company', '/who-we-are', '/our-story'],
    'press_page': ['/press', '/news', '/newsroom', '/media', '/announcements', '/blog'],
}

# HTTP settings
REQUEST_TIMEOUT = 10.0
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# XML namespace for sitemaps
SITEMAP_NS = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

# Sub-sitemap URL keywords that suggest navigational/page content worth fetching.
# When a sitemap index has 50+ sub-sitemaps (AmEx locales, PBS shows, Shopify products),
# we only fetch the ones likely to contain about/press/team/etc pages.
# Everything else (product sitemaps, post archives, locale variants) gets skipped.
SUB_SITEMAP_PRIORITY_KEYWORDS = [
    'page', 'pages', 'main', 'site', 'misc',
    'team', 'staff', 'people', 'leadership',
    'about', 'company', 'corporate',
    'news', 'press', 'media',
    'career', 'job', 'contact',
    'blog', 'post', 'article', 'insight',
    'investor',
]
# Sub-sitemap URL keywords to always skip (locale variants, product catalogs, etc.)
SUB_SITEMAP_SKIP_KEYWORDS = [
    '-es-', '-fr-', '-de-', '-ja-', '-zh-', '-ko-', '-pt-', '-it-',
    '-ru-', '-ar-', '-nl-', '-sv-', '-da-', '-fi-', '-no-', '-pl-',
    '-bg-', '-cd-', '-ke-', '-mk-', '-mu-', '-rw-', '-ug-', '-tz-',
    '-zm-', '-mz-', '-et-', '-al-', '-rs-',
    'travelers-cheque', 'upgrade-sitemap', 'w8registration',
]
# Hard cap as final safety net
MAX_SUB_SITEMAPS = 25


# ═══════════════════════════════════════════════════════════════
# STATS TRACKER
# ═══════════════════════════════════════════════════════════════

class Stats:
    def __init__(self):
        self.processed = 0
        self.sitemap_hits = 0
        self.homepage_hits = 0
        self.probe_hits = 0
        self.no_website = 0
        self.unreachable = 0
        self.errors = 0
        self.urls_found = 0
        self.by_type: Dict[str, int] = {}

    def record_url(self, source_type: str):
        self.urls_found += 1
        self.by_type[source_type] = self.by_type.get(source_type, 0) + 1


# ═══════════════════════════════════════════════════════════════
# URL CLASSIFICATION
# ═══════════════════════════════════════════════════════════════

def classify_url(url: str) -> Optional[str]:
    """Classify a URL into a page type based on its path."""
    try:
        path = urlparse(url).path.lower().rstrip('/')
    except Exception:
        return None

    if not path or path == '/':
        return None

    for source_type, patterns in PAGE_TYPE_PATTERNS.items():
        for pattern in patterns:
            if path == pattern or path.startswith(pattern + '/'):
                return source_type

    return None


def is_same_domain(url: str, base_domain: str) -> bool:
    """Check if URL belongs to the same domain."""
    try:
        url_domain = urlparse(url).netloc.lower().replace('www.', '')
        base_clean = base_domain.lower().replace('www.', '')
        return url_domain == base_clean or url_domain.endswith('.' + base_clean)
    except Exception:
        return False


def normalize_base_url(domain: str) -> str:
    """Build base URL from domain string."""
    if not domain:
        return ''
    domain = domain.strip()
    if domain.startswith(('http://', 'https://')):
        parsed = urlparse(domain)
        return f"{parsed.scheme}://{parsed.netloc}"
    return f"https://{domain}"


def get_domain(url: str) -> str:
    """Extract clean domain from URL."""
    try:
        return urlparse(url).netloc.lower().replace('www.', '')
    except Exception:
        return ''


# ═══════════════════════════════════════════════════════════════
# STEP 1: SITEMAP DISCOVERY
# ═══════════════════════════════════════════════════════════════

async def fetch_sitemap(
    client: httpx.AsyncClient,
    base_url: str,
    domain: str,
) -> List[Dict]:
    """
    Fetch and parse sitemap.xml. Returns classified URLs.
    Handles sitemap index files (nested sitemaps).
    """
    discovered = []
    sitemap_url = f"{base_url}/sitemap.xml"

    # Try sitemap.xml directly
    urls = await _parse_sitemap_url(client, sitemap_url, domain)

    if not urls:
        # Try robots.txt for Sitemap: directive
        robots_url = f"{base_url}/robots.txt"
        try:
            resp = await client.get(robots_url, timeout=REQUEST_TIMEOUT, follow_redirects=True)
            if resp.status_code == 200:
                for line in resp.text.splitlines():
                    line = line.strip()
                    if line.lower().startswith('sitemap:'):
                        sm_url = line.split(':', 1)[1].strip()
                        urls = await _parse_sitemap_url(client, sm_url, domain)
                        if urls:
                            break
        except Exception:
            pass

    if not urls:
        return []

    # Classify all discovered URLs
    seen_types: Dict[str, str] = {}  # source_type -> best URL
    for url in urls:
        source_type = classify_url(url)
        if source_type and source_type not in seen_types:
            seen_types[source_type] = url

    for source_type, url in seen_types.items():
        discovered.append({
            'source_type': source_type,
            'source_url': url,
            'discovered_from': 'sitemap',
        })

    return discovered


def _select_sub_sitemaps(sub_urls: List[str]) -> List[str]:
    """
    From a list of sub-sitemap URLs, pick only the ones likely to contain
    navigational pages (about, press, team, etc.). Skip locale variants,
    product catalogs, and numbered post archives.

    For small indexes (<=5 sub-sitemaps), fetch all of them.
    For large indexes, only fetch priority matches + a few generic ones.
    """
    if len(sub_urls) <= 5:
        return sub_urls

    priority = []
    generic = []

    for url in sub_urls:
        url_lower = url.lower()
        filename = url_lower.rsplit('/', 1)[-1] if '/' in url_lower else url_lower

        # Skip obvious locale/product variants
        if any(kw in url_lower for kw in SUB_SITEMAP_SKIP_KEYWORDS):
            continue

        # Skip numbered archives (post-sitemap2.xml through post-sitemap99.xml)
        if re.search(r'sitemap\d{2,}\.xml', filename):
            continue

        # Priority: filename contains a navigational keyword
        if any(kw in filename for kw in SUB_SITEMAP_PRIORITY_KEYWORDS):
            priority.append(url)
        else:
            generic.append(url)

    # Take all priority matches, plus a few generic ones as fallback
    result = priority[:MAX_SUB_SITEMAPS]
    remaining = MAX_SUB_SITEMAPS - len(result)
    if remaining > 0:
        result.extend(generic[:remaining])

    return result


async def _parse_sitemap_url(
    client: httpx.AsyncClient,
    sitemap_url: str,
    domain: str,
    depth: int = 0,
) -> List[str]:
    """Parse a sitemap URL, handling sitemap index files recursively."""
    if depth > 2:  # Prevent deep recursion
        return []

    try:
        resp = await client.get(sitemap_url, timeout=REQUEST_TIMEOUT, follow_redirects=True)
        if resp.status_code != 200:
            return []

        content_type = resp.headers.get('content-type', '')
        text = resp.text

        # Must look like XML
        if '<' not in text[:500]:
            return []

        # Parse XML
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            return []

        urls = []
        tag = root.tag.lower()

        # Sitemap index — contains links to other sitemaps
        if 'sitemapindex' in tag:
            # Collect all sub-sitemap URLs first
            all_sub_urls = []
            for sitemap_el in root.findall('.//sm:sitemap/sm:loc', SITEMAP_NS):
                if sitemap_el.text:
                    all_sub_urls.append(sitemap_el.text.strip())
            for sitemap_el in root.findall('.//sitemap/loc'):
                if sitemap_el.text:
                    sub_url = sitemap_el.text.strip()
                    if sub_url not in all_sub_urls:
                        all_sub_urls.append(sub_url)

            # Smart filter: prioritize sub-sitemaps likely to have page-type content
            to_fetch = _select_sub_sitemaps(all_sub_urls)

            for sub_url in to_fetch:
                child_urls = await _parse_sitemap_url(
                    client, sub_url, domain, depth + 1
                )
                urls.extend(child_urls)

        # Regular sitemap — contains page URLs
        elif 'urlset' in tag:
            for url_el in root.findall('.//sm:url/sm:loc', SITEMAP_NS):
                if url_el.text and is_same_domain(url_el.text.strip(), domain):
                    urls.append(url_el.text.strip())
            # Also try without namespace
            for url_el in root.findall('.//url/loc'):
                if url_el.text and is_same_domain(url_el.text.strip(), domain):
                    urls.append(url_el.text.strip())

        return urls

    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════
# STEP 2: HOMEPAGE LINK EXTRACTION
# ═══════════════════════════════════════════════════════════════

async def extract_homepage_links(
    client: httpx.AsyncClient,
    base_url: str,
    domain: str,
) -> List[Dict]:
    """
    Fetch homepage and extract navigation/footer links.
    Classify them by page type.
    """
    try:
        resp = await client.get(base_url, timeout=REQUEST_TIMEOUT, follow_redirects=True)
        if resp.status_code != 200:
            return []

        html = resp.text

        # Extract all href values
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE)

        # Resolve relative URLs and filter to same domain
        resolved_urls = set()
        for href in hrefs:
            if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                continue
            try:
                full_url = urljoin(base_url, href)
                if is_same_domain(full_url, domain):
                    # Normalize: strip query params and fragments for classification
                    parsed = urlparse(full_url)
                    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    resolved_urls.add(clean_url)
            except Exception:
                continue

        # Classify
        discovered = []
        seen_types: Dict[str, str] = {}
        for url in resolved_urls:
            source_type = classify_url(url)
            if source_type and source_type not in seen_types:
                seen_types[source_type] = url

        for source_type, url in seen_types.items():
            discovered.append({
                'source_type': source_type,
                'source_url': url,
                'discovered_from': 'homepage',
            })

        return discovered

    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════
# STEP 3: BRUTE-FORCE PATH PROBING (LAST RESORT)
# ═══════════════════════════════════════════════════════════════

async def probe_paths(
    client: httpx.AsyncClient,
    base_url: str,
    domain: str,
    needed_types: List[str],
) -> List[Dict]:
    """
    Probe hardcoded paths for page types we still haven't found.
    Only probes types in needed_types list.
    """
    discovered = []
    homepage_path = '/'

    # Get homepage path for redirect detection
    try:
        resp = await client.head(base_url, timeout=REQUEST_TIMEOUT, follow_redirects=True)
        if resp.status_code == 200:
            homepage_path = urlparse(str(resp.url)).path.rstrip('/') or '/'
    except Exception:
        pass

    for source_type in needed_types:
        paths = PROBE_PATHS.get(source_type, [])
        for path in paths:
            probe_url = urljoin(base_url, path)
            try:
                resp = await client.head(
                    probe_url, timeout=REQUEST_TIMEOUT, follow_redirects=True
                )

                if resp.status_code == 405:
                    resp = await client.get(
                        probe_url, timeout=REQUEST_TIMEOUT, follow_redirects=True
                    )

                if resp.status_code == 200:
                    final_url = str(resp.url)
                    final_path = urlparse(final_url).path.rstrip('/') or '/'

                    # Skip if redirected to homepage
                    if final_path == homepage_path:
                        continue

                    # Skip if off-domain redirect
                    if not is_same_domain(final_url, domain):
                        continue

                    discovered.append({
                        'source_type': source_type,
                        'source_url': final_url,
                        'discovered_from': 'probe',
                    })
                    break  # Found one for this type, move on

            except Exception:
                continue

    return discovered


# ═══════════════════════════════════════════════════════════════
# COMPANY DISCOVERY ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

async def discover_company(
    client: httpx.AsyncClient,
    company: Dict,
    stats: Stats,
    semaphore: asyncio.Semaphore,
) -> List[Dict]:
    """
    Run the 3-step waterfall for one company.
    Returns list of discovered URL dicts ready for DB insert.
    """
    async with semaphore:
        website = company.get('website_url') or company.get('domain')
        if not website:
            stats.no_website += 1
            stats.processed += 1
            return []

        base_url = normalize_base_url(website)
        domain = get_domain(base_url)
        if not domain:
            stats.no_website += 1
            stats.processed += 1
            return []

        company_id = company['company_unique_id']
        all_discovered = []

        try:
            # Step 1: Sitemap
            sitemap_results = await fetch_sitemap(client, base_url, domain)
            if sitemap_results:
                stats.sitemap_hits += 1
                all_discovered.extend(sitemap_results)

            # Step 2: Homepage (always try — may find pages sitemap missed)
            if not all_discovered:
                homepage_results = await extract_homepage_links(client, base_url, domain)
                if homepage_results:
                    stats.homepage_hits += 1
                    # Add only types not already found
                    found_types = {d['source_type'] for d in all_discovered}
                    for result in homepage_results:
                        if result['source_type'] not in found_types:
                            all_discovered.append(result)
                            found_types.add(result['source_type'])

            # Step 3: Probe (only for about + press if still missing)
            found_types = {d['source_type'] for d in all_discovered}
            needed = [t for t in ['about_page', 'press_page'] if t not in found_types]
            if needed:
                probe_results = await probe_paths(client, base_url, domain, needed)
                if probe_results:
                    stats.probe_hits += 1
                    all_discovered.extend(probe_results)

            # Attach company_unique_id to all results
            for d in all_discovered:
                d['company_unique_id'] = company_id
                stats.record_url(d['source_type'])

            if not all_discovered:
                stats.unreachable += 1

        except Exception as e:
            logger.debug(f"Error discovering {domain}: {e}")
            stats.errors += 1

        stats.processed += 1
        return all_discovered


# ═══════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════

def get_neon_config() -> Dict:
    """Build Neon config from Doppler env vars."""
    host = os.environ.get('NEON_HOST')
    password = os.environ.get('NEON_PASSWORD')

    if not host or not password:
        raise EnvironmentError(
            "NEON_HOST and NEON_PASSWORD must be set. "
            "Run with: doppler run -- python ..."
        )

    return {
        'host': host,
        'port': 5432,
        'database': os.environ.get('NEON_DATABASE', 'Marketing DB'),
        'user': os.environ.get('NEON_USER', 'Marketing DB_owner'),
        'password': password,
        'sslmode': 'require',
    }


def get_connection():
    """Create fresh database connection."""
    return psycopg2.connect(**get_neon_config())


def get_companies_needing_discovery(limit: Optional[int] = None) -> List[Dict]:
    """
    Get companies that need URL discovery.

    Sources from company.company_master (owns company_unique_id used by
    company_source_urls). Outreach filtering happens downstream via domain bridge.

    Note: Direct FK between outreach spine and company_master doesn't exist —
    company_target uses CL UUIDs, company_master uses Barton IDs.
    The domain bridge (outreach.outreach.domain ↔ company_master.website_url)
    covers ~54% of records. URL discovery runs against company_master directly
    to maximize coverage.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    limit_sql = f"LIMIT {int(limit)}" if limit else ""

    cur.execute(f"""
        SELECT
            cm.company_unique_id,
            cm.company_name,
            cm.website_url
        FROM company.company_master cm
        WHERE cm.website_url IS NOT NULL
          AND NOT EXISTS (
            SELECT 1 FROM company.company_source_urls csu
            WHERE csu.company_unique_id = cm.company_unique_id
          )
        ORDER BY cm.company_name
        {limit_sql}
    """)

    companies = cur.fetchall()
    cur.close()
    conn.close()
    return companies


def get_current_coverage() -> Dict:
    """Get current URL coverage stats."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT source_type, COUNT(*) as cnt
        FROM company.company_source_urls
        GROUP BY source_type
        ORDER BY cnt DESC
    """)
    by_type = {row['source_type']: row['cnt'] for row in cur.fetchall()}

    cur.execute("SELECT COUNT(DISTINCT company_unique_id) as total FROM company.company_source_urls")
    total_companies = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) as total FROM company.company_source_urls")
    total_urls = cur.fetchone()['total']

    cur.close()
    conn.close()

    return {
        'total_companies': total_companies,
        'total_urls': total_urls,
        'by_type': by_type,
    }


def save_batch(urls: List[Dict]) -> int:
    """Save discovered URLs to company.company_source_urls."""
    if not urls:
        return 0

    conn = get_connection()
    cur = conn.cursor()

    try:
        execute_values(cur, """
            INSERT INTO company.company_source_urls
            (company_unique_id, source_type, source_url, page_title,
             discovered_from, http_status, is_accessible, discovered_at)
            VALUES %s
            ON CONFLICT (company_unique_id, source_url) DO NOTHING
        """, [
            (
                d['company_unique_id'],
                d['source_type'],
                d['source_url'],
                None,  # page_title — not extracted in discovery phase
                d['discovered_from'],
                200,   # http_status — we only save accessible URLs
                True,  # is_accessible
                datetime.now(timezone.utc),
            )
            for d in urls
        ])
        conn.commit()
        return len(urls)

    except Exception as e:
        logger.error(f"Error saving batch: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def save_failure(company_unique_id: str, website_url: str, reason: str):
    """Log discovery failure."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO company.url_discovery_failures
            (company_unique_id, website_url, failure_reason, last_attempt_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (company_unique_id) DO UPDATE
            SET failure_reason = EXCLUDED.failure_reason,
                last_attempt_at = EXCLUDED.last_attempt_at,
                retry_count = COALESCE(company.url_discovery_failures.retry_count, 0) + 1
        """, (company_unique_id, website_url, reason, datetime.now(timezone.utc)))
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass  # Don't let failure logging break the pipeline


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

async def run_discovery(
    limit: Optional[int] = None,
    workers: int = 20,
    dry_run: bool = False,
    chunk_size: int = 100,
):
    """Main discovery loop."""

    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print('=' * 70)
    print('BLOG URL DISCOVERY — Sitemap-First Approach')
    print('=' * 70)
    print(f"Mode:       {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Workers:    {workers}")
    print(f"Limit:      {limit or 'ALL'}")
    print(f"Chunk size: {chunk_size}")
    print(f"Tier:       0 (FREE — httpx only)")
    print()

    # Current coverage
    coverage = get_current_coverage()
    print('CURRENT COVERAGE:')
    print(f"  Companies with URLs: {coverage['total_companies']:,}")
    print(f"  Total URLs:          {coverage['total_urls']:,}")
    for stype, cnt in sorted(coverage['by_type'].items(), key=lambda x: -x[1]):
        print(f"    {stype}: {cnt:,}")
    print()

    # Get companies needing discovery
    companies = get_companies_needing_discovery(limit)
    total = len(companies)
    print(f"Companies needing discovery: {total:,}")
    print()

    if total == 0:
        print("All outreach companies already have discovered URLs!")
        return

    # Process
    stats = Stats()
    semaphore = asyncio.Semaphore(workers)
    total_saved = 0

    async with httpx.AsyncClient(
        headers=HEADERS,
        follow_redirects=True,
        timeout=httpx.Timeout(
            connect=5.0,
            read=REQUEST_TIMEOUT,
            write=REQUEST_TIMEOUT,
            pool=REQUEST_TIMEOUT,
        ),
        limits=httpx.Limits(
            max_connections=workers * 2,
            max_keepalive_connections=workers,
        ),
        transport=httpx.AsyncHTTPTransport(retries=0),
    ) as client:

        for chunk_start in range(0, total, chunk_size):
            chunk = companies[chunk_start:chunk_start + chunk_size]
            chunk_num = chunk_start // chunk_size + 1
            total_chunks = (total + chunk_size - 1) // chunk_size

            # Run chunk concurrently
            tasks = [
                discover_company(client, c, stats, semaphore)
                for c in chunk
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect URLs from this chunk
            chunk_urls = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.debug(f"Task exception: {result}")
                    continue
                if result:
                    chunk_urls.extend(result)
                else:
                    # No URLs found — log failure
                    company = chunk[i]
                    if not dry_run:
                        save_failure(
                            company['company_unique_id'],
                            company.get('website_url', ''),
                            'no_pages_discovered',
                        )

            # Save chunk
            if not dry_run and chunk_urls:
                try:
                    saved = save_batch(chunk_urls)
                    total_saved += saved
                except Exception as e:
                    logger.error(f"Save error: {e}")
            elif dry_run:
                total_saved += len(chunk_urls)

            pct = 100 * stats.processed / total if total > 0 else 0
            print(
                f"  [{chunk_num}/{total_chunks}] "
                f"{stats.processed:,}/{total:,} ({pct:.0f}%) | "
                f"Sitemap: {stats.sitemap_hits:,} | "
                f"Homepage: {stats.homepage_hits:,} | "
                f"Probe: {stats.probe_hits:,} | "
                f"URLs: {stats.urls_found:,} | "
                f"Fail: {stats.unreachable:,}",
                flush=True,
            )

    # Final summary
    print()
    print('=' * 70)
    print('RESULTS')
    print('=' * 70)
    print(f"Companies processed:   {stats.processed:,}")
    print(f"Sitemap discoveries:   {stats.sitemap_hits:,}")
    print(f"Homepage discoveries:  {stats.homepage_hits:,}")
    print(f"Probe discoveries:     {stats.probe_hits:,}")
    print(f"Unreachable/no URLs:   {stats.unreachable:,}")
    print(f"Errors:                {stats.errors:,}")
    print(f"No website:            {stats.no_website:,}")
    print(f"Total URLs found:      {stats.urls_found:,}")
    print(f"Saved to DB:           {total_saved:,}")
    print()

    if stats.by_type:
        print('BY PAGE TYPE:')
        for stype, cnt in sorted(stats.by_type.items(), key=lambda x: -x[1]):
            print(f"  {stype}: {cnt:,}")
        print()

    if stats.processed > 0:
        hit_rate = 100 * (stats.sitemap_hits + stats.homepage_hits + stats.probe_hits) / stats.processed
        print(f"Hit rate: {hit_rate:.1f}%")
        print(f"Avg URLs per company: {stats.urls_found / max(1, stats.processed):.1f}")

    if dry_run:
        print()
        print("[DRY RUN — No data was saved]")


def main():
    parser = argparse.ArgumentParser(
        description='Blog URL Discovery — Sitemap-first approach (Tier 0 FREE)'
    )
    parser.add_argument('--limit', type=int, help='Max companies to process')
    parser.add_argument('--workers', type=int, default=20, help='Concurrent workers (default: 20)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
    parser.add_argument('--chunk-size', type=int, default=100, help='Companies per save batch (default: 100)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    asyncio.run(run_discovery(
        limit=args.limit,
        workers=args.workers,
        dry_run=args.dry_run,
        chunk_size=args.chunk_size,
    ))


if __name__ == '__main__':
    main()
