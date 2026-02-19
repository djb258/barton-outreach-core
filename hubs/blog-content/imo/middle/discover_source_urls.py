#!/usr/bin/env python3
"""
Source URL Discovery — Spine-Sourced, Sitemap-First
====================================================
Discovers company web pages (about, leadership, team, press, blog, etc.)
sourced directly from the outreach spine (outreach.outreach.domain).

THIS IS THE CANONICAL BLOG DISCOVERY TOOL.
The spine owns the domain. CT is the authoritative company list.
We do NOT route through company.company_master.

SNAP_ON_TOOLBOX compliant:
- Tier 0: Free (httpx only, no paid APIs)
- Uses httpx (not requests — requests is BANNED)
- Deterministic URL classification (no LLM)

DOCTRINE compliant:
- Sources domains from outreach.outreach (operational spine)
- Scopes by coverage_id or runs against full CT
- Saves to outreach.source_urls (outreach_id FK)
- Also exports CSV with outreach_id for downstream enrichment
- Credentials via Doppler env vars

3-Step Waterfall:
  1. Sitemap: Fetch sitemap.xml → parse all URLs → classify page types
  2. Homepage: Fetch homepage → extract nav/footer links → classify
  3. Probe: Brute-force path probing (last resort only)

Usage:
    # Scope to a specific market (coverage_id)
    doppler run -- python hubs/blog-content/imo/middle/discover_source_urls.py \\
        --coverage-id 0456811b-9c77-48c5-9bc3-99f188066272

    # Dry run (no DB writes, no CSV)
    doppler run -- python hubs/blog-content/imo/middle/discover_source_urls.py \\
        --coverage-id 0456811b-9c77-48c5-9bc3-99f188066272 --dry-run --limit 20

    # Full spine (all CT companies, no coverage filter)
    doppler run -- python hubs/blog-content/imo/middle/discover_source_urls.py --all

    # Control concurrency
    doppler run -- python hubs/blog-content/imo/middle/discover_source_urls.py \\
        --coverage-id <uuid> --workers 30
"""

import os
import re
import sys
import csv
import asyncio
import argparse
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional

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

# Paths to probe in Step 3 (brute-force fallback)
PROBE_PATHS = {
    'about_page': ['/about', '/about-us', '/company', '/who-we-are', '/our-story'],
    'press_page': ['/press', '/news', '/newsroom', '/media', '/announcements', '/blog'],
    'leadership_page': ['/leadership', '/our-leadership', '/executive-team', '/team',
                        '/about/leadership', '/about/team', '/our-team'],
    'team_page': ['/team', '/our-team', '/people', '/staff', '/our-people'],
}

# HTTP settings
REQUEST_TIMEOUT = 10.0
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

SITEMAP_NS = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

SUB_SITEMAP_PRIORITY_KEYWORDS = [
    'page', 'pages', 'main', 'site', 'misc',
    'team', 'staff', 'people', 'leadership',
    'about', 'company', 'corporate',
    'news', 'press', 'media',
    'career', 'job', 'contact',
    'blog', 'post', 'article', 'insight',
    'investor',
]
SUB_SITEMAP_SKIP_KEYWORDS = [
    '-es-', '-fr-', '-de-', '-ja-', '-zh-', '-ko-', '-pt-', '-it-',
    '-ru-', '-ar-', '-nl-', '-sv-', '-da-', '-fi-', '-no-', '-pl-',
    '-bg-', '-cd-', '-ke-', '-mk-', '-mu-', '-rw-', '-ug-', '-tz-',
    '-zm-', '-mz-', '-et-', '-al-', '-rs-',
    'travelers-cheque', 'upgrade-sitemap', 'w8registration',
]
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
    """Fetch and parse sitemap.xml. Returns classified URLs."""
    discovered = []
    sitemap_url = f"{base_url}/sitemap.xml"

    urls = await _parse_sitemap_url(client, sitemap_url, domain)

    if not urls:
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

    seen_types: Dict[str, str] = {}
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
    """Pick sub-sitemaps likely to contain navigational pages."""
    if len(sub_urls) <= 5:
        return sub_urls

    priority = []
    generic = []

    for url in sub_urls:
        url_lower = url.lower()
        filename = url_lower.rsplit('/', 1)[-1] if '/' in url_lower else url_lower

        if any(kw in url_lower for kw in SUB_SITEMAP_SKIP_KEYWORDS):
            continue
        if re.search(r'sitemap\d{2,}\.xml', filename):
            continue

        if any(kw in filename for kw in SUB_SITEMAP_PRIORITY_KEYWORDS):
            priority.append(url)
        else:
            generic.append(url)

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
    if depth > 2:
        return []

    try:
        resp = await client.get(sitemap_url, timeout=REQUEST_TIMEOUT, follow_redirects=True)
        if resp.status_code != 200:
            return []

        text = resp.text
        if '<' not in text[:500]:
            return []

        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            return []

        urls = []
        tag = root.tag.lower()

        if 'sitemapindex' in tag:
            all_sub_urls = []
            for sitemap_el in root.findall('.//sm:sitemap/sm:loc', SITEMAP_NS):
                if sitemap_el.text:
                    all_sub_urls.append(sitemap_el.text.strip())
            for sitemap_el in root.findall('.//sitemap/loc'):
                if sitemap_el.text:
                    sub_url = sitemap_el.text.strip()
                    if sub_url not in all_sub_urls:
                        all_sub_urls.append(sub_url)

            to_fetch = _select_sub_sitemaps(all_sub_urls)
            for sub_url in to_fetch:
                child_urls = await _parse_sitemap_url(client, sub_url, domain, depth + 1)
                urls.extend(child_urls)

        elif 'urlset' in tag:
            for url_el in root.findall('.//sm:url/sm:loc', SITEMAP_NS):
                if url_el.text and is_same_domain(url_el.text.strip(), domain):
                    urls.append(url_el.text.strip())
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
    """Fetch homepage and extract navigation/footer links."""
    try:
        resp = await client.get(base_url, timeout=REQUEST_TIMEOUT, follow_redirects=True)
        if resp.status_code != 200:
            return []

        html = resp.text
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE)

        resolved_urls = set()
        for href in hrefs:
            if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                continue
            try:
                full_url = urljoin(base_url, href)
                if is_same_domain(full_url, domain):
                    parsed = urlparse(full_url)
                    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    resolved_urls.add(clean_url)
            except Exception:
                continue

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
# STEP 3: BRUTE-FORCE PATH PROBING
# ═══════════════════════════════════════════════════════════════

async def probe_paths(
    client: httpx.AsyncClient,
    base_url: str,
    domain: str,
    needed_types: List[str],
) -> List[Dict]:
    """Probe hardcoded paths for page types we still haven't found."""
    discovered = []
    homepage_path = '/'

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

                    if final_path == homepage_path:
                        continue
                    if not is_same_domain(final_url, domain):
                        continue

                    discovered.append({
                        'source_type': source_type,
                        'source_url': final_url,
                        'discovered_from': 'probe',
                    })
                    break

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
    Returns list of discovered URL dicts keyed by outreach_id.
    """
    async with semaphore:
        domain = company.get('domain', '').strip()
        if not domain:
            stats.no_website += 1
            stats.processed += 1
            return []

        base_url = normalize_base_url(domain)
        clean_domain = get_domain(base_url)
        if not clean_domain:
            stats.no_website += 1
            stats.processed += 1
            return []

        outreach_id = company['outreach_id']
        all_discovered = []

        try:
            # Step 1: Sitemap
            sitemap_results = await fetch_sitemap(client, base_url, clean_domain)
            if sitemap_results:
                stats.sitemap_hits += 1
                all_discovered.extend(sitemap_results)

            # Step 2: Homepage (if sitemap found nothing)
            if not all_discovered:
                homepage_results = await extract_homepage_links(client, base_url, clean_domain)
                if homepage_results:
                    stats.homepage_hits += 1
                    found_types = {d['source_type'] for d in all_discovered}
                    for result in homepage_results:
                        if result['source_type'] not in found_types:
                            all_discovered.append(result)
                            found_types.add(result['source_type'])

            # Step 3: Probe (for about, press, leadership, team if still missing)
            found_types = {d['source_type'] for d in all_discovered}
            needed = [t for t in PROBE_PATHS.keys() if t not in found_types]
            if needed:
                probe_results = await probe_paths(client, base_url, clean_domain, needed)
                if probe_results:
                    stats.probe_hits += 1
                    all_discovered.extend(probe_results)

            # Attach outreach_id to all results
            for d in all_discovered:
                d['outreach_id'] = outreach_id
                d['domain'] = domain
                d['company_name'] = company.get('company_name', '')
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

def get_connection():
    """Create fresh database connection."""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        dbname=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require',
    )


def ensure_source_urls_table(conn):
    """Create outreach.source_urls if it doesn't exist."""
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS outreach.source_urls (
            id              BIGSERIAL PRIMARY KEY,
            outreach_id     UUID NOT NULL REFERENCES outreach.outreach(outreach_id),
            source_type     TEXT NOT NULL,
            source_url      TEXT NOT NULL,
            discovered_from TEXT,
            discovered_at   TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(outreach_id, source_url)
        )
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_source_urls_outreach_id
        ON outreach.source_urls(outreach_id)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_source_urls_source_type
        ON outreach.source_urls(source_type)
    """)
    conn.commit()
    cur.close()


def get_companies_for_market(coverage_id: str, limit: Optional[int] = None) -> List[Dict]:
    """Get companies from spine scoped to a coverage market."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    limit_sql = f"LIMIT {int(limit)}" if limit else ""

    cur.execute(f"""
        WITH market_zips AS (
            SELECT zip, state_id
            FROM coverage.v_service_agent_coverage_zips
            WHERE coverage_id = %s
        )
        SELECT
            o.outreach_id::text AS outreach_id,
            o.domain,
            cl.company_name
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
        JOIN cl.company_identity cl ON cl.outreach_id = o.outreach_id
        WHERE ct.postal_code IN (SELECT zip FROM market_zips)
          AND ct.state IN (SELECT state_id FROM market_zips)
          AND o.domain IS NOT NULL
          AND LENGTH(TRIM(o.domain)) > 0
          AND NOT EXISTS (
              SELECT 1 FROM outreach.source_urls su
              WHERE su.outreach_id = o.outreach_id
          )
        ORDER BY cl.company_name
        {limit_sql}
    """, (coverage_id,))

    companies = cur.fetchall()
    cur.close()
    conn.close()
    return companies


def get_companies_all(limit: Optional[int] = None) -> List[Dict]:
    """Get all CT companies from spine that need URL discovery."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    limit_sql = f"LIMIT {int(limit)}" if limit else ""

    cur.execute(f"""
        SELECT
            o.outreach_id::text AS outreach_id,
            o.domain,
            cl.company_name
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
        JOIN cl.company_identity cl ON cl.outreach_id = o.outreach_id
        WHERE o.domain IS NOT NULL
          AND LENGTH(TRIM(o.domain)) > 0
          AND NOT EXISTS (
              SELECT 1 FROM outreach.source_urls su
              WHERE su.outreach_id = o.outreach_id
          )
        ORDER BY cl.company_name
        {limit_sql}
    """)

    companies = cur.fetchall()
    cur.close()
    conn.close()
    return companies


def get_market_info(coverage_id: str) -> Dict:
    """Get market metadata for display."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT sac.coverage_id, sac.anchor_zip, sac.radius_miles, sac.status,
               sa.agent_name, sa.service_agent_id
        FROM coverage.service_agent_coverage sac
        JOIN coverage.service_agent sa ON sac.service_agent_id = sa.service_agent_id
        WHERE sac.coverage_id = %s
    """, (coverage_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row or {}


def save_batch(urls: List[Dict]) -> int:
    """Save discovered URLs to outreach.source_urls."""
    if not urls:
        return 0

    conn = get_connection()
    cur = conn.cursor()

    try:
        execute_values(cur, """
            INSERT INTO outreach.source_urls
            (outreach_id, source_type, source_url, discovered_from, discovered_at)
            VALUES %s
            ON CONFLICT (outreach_id, source_url) DO NOTHING
        """, [
            (
                d['outreach_id'],
                d['source_type'],
                d['source_url'],
                d['discovered_from'],
                datetime.now(timezone.utc),
            )
            for d in urls
        ])
        conn.commit()
        saved = cur.rowcount
        return saved

    except Exception as e:
        logger.error(f"Error saving batch: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def get_current_coverage() -> Dict:
    """Get current source URL coverage stats."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("""
            SELECT source_type, COUNT(*) as cnt
            FROM outreach.source_urls
            GROUP BY source_type
            ORDER BY cnt DESC
        """)
        by_type = {row['source_type']: row['cnt'] for row in cur.fetchall()}

        cur.execute("SELECT COUNT(DISTINCT outreach_id) as total FROM outreach.source_urls")
        total_companies = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) as total FROM outreach.source_urls")
        total_urls = cur.fetchone()['total']

    except psycopg2.errors.UndefinedTable:
        # Table doesn't exist yet
        by_type = {}
        total_companies = 0
        total_urls = 0
        conn.rollback()

    cur.close()
    conn.close()

    return {
        'total_companies': total_companies,
        'total_urls': total_urls,
        'by_type': by_type,
    }


# ═══════════════════════════════════════════════════════════════
# CSV EXPORT
# ═══════════════════════════════════════════════════════════════

def export_csv(all_urls: List[Dict], coverage_id: Optional[str], anchor_zip: str = '') -> str:
    """Export discovered URLs to CSV with outreach_id."""
    exports_dir = Path(__file__).resolve().parents[4] / 'exports'
    exports_dir.mkdir(exist_ok=True)

    if anchor_zip:
        filename = f"source_urls_{anchor_zip}.csv"
    elif coverage_id:
        filename = f"source_urls_{coverage_id[:8]}.csv"
    else:
        filename = "source_urls_all.csv"

    filepath = exports_dir / filename

    fieldnames = ['outreach_id', 'company_name', 'domain', 'source_type', 'source_url', 'discovered_from']

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_urls)

    return str(filepath)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

async def run_discovery(
    coverage_id: Optional[str] = None,
    run_all: bool = False,
    limit: Optional[int] = None,
    workers: int = 20,
    dry_run: bool = False,
    chunk_size: int = 100,
):
    """Main discovery loop."""

    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print('=' * 70)
    print('SOURCE URL DISCOVERY — Spine-Sourced, Sitemap-First')
    print('=' * 70)
    print(f"Mode:       {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Workers:    {workers}")
    print(f"Limit:      {limit or 'ALL'}")
    print(f"Tier:       0 (FREE — httpx only)")

    # Market info
    anchor_zip = ''
    if coverage_id:
        market = get_market_info(coverage_id)
        if market:
            anchor_zip = market.get('anchor_zip', '')
            print(f"Market:     {anchor_zip} / {market.get('radius_miles')}mi")
            print(f"Agent:      {market.get('agent_name', 'unknown')}")
        else:
            print(f"Coverage:   {coverage_id}")
    else:
        print(f"Scope:      ALL CT companies")
    print()

    # Ensure table exists (always, so queries work)
    conn = get_connection()
    ensure_source_urls_table(conn)
    conn.close()

    # Current coverage
    coverage = get_current_coverage()
    if coverage['total_urls'] > 0:
        print('EXISTING COVERAGE:')
        print(f"  Companies with URLs: {coverage['total_companies']:,}")
        print(f"  Total URLs:          {coverage['total_urls']:,}")
        for stype, cnt in sorted(coverage['by_type'].items(), key=lambda x: -x[1]):
            print(f"    {stype}: {cnt:,}")
        print()

    # Get companies needing discovery
    if coverage_id:
        companies = get_companies_for_market(coverage_id, limit)
    else:
        companies = get_companies_all(limit)

    total = len(companies)
    print(f"Companies to discover: {total:,}")
    print()

    if total == 0:
        print("All companies already have discovered URLs!")
        return

    # Process
    stats = Stats()
    semaphore = asyncio.Semaphore(workers)
    total_saved = 0
    all_urls = []

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

            tasks = [
                discover_company(client, c, stats, semaphore)
                for c in chunk
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            chunk_urls = []
            for result in results:
                if isinstance(result, Exception):
                    logger.debug(f"Task exception: {result}")
                    continue
                if result:
                    chunk_urls.extend(result)

            all_urls.extend(chunk_urls)

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

    # Export CSV
    csv_path = ''
    if all_urls and not dry_run:
        csv_path = export_csv(all_urls, coverage_id, anchor_zip)

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
    print(f"No domain:             {stats.no_website:,}")
    print(f"Total URLs found:      {stats.urls_found:,}")
    print(f"Saved to DB:           {total_saved:,}")
    if csv_path:
        print(f"CSV export:            {csv_path}")
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
        description='Source URL Discovery — Spine-sourced, sitemap-first (Tier 0 FREE)'
    )
    parser.add_argument('--coverage-id', help='Coverage ID to scope to a market')
    parser.add_argument('--all', action='store_true', help='Run against all CT companies')
    parser.add_argument('--limit', type=int, help='Max companies to process')
    parser.add_argument('--workers', type=int, default=20, help='Concurrent workers (default: 20)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
    parser.add_argument('--chunk-size', type=int, default=100, help='Companies per batch (default: 100)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    if not args.coverage_id and not args.all:
        parser.error('Must specify --coverage-id or --all')

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    asyncio.run(run_discovery(
        coverage_id=args.coverage_id,
        run_all=args.all,
        limit=args.limit,
        workers=args.workers,
        dry_run=args.dry_run,
        chunk_size=args.chunk_size,
    ))


if __name__ == '__main__':
    main()
