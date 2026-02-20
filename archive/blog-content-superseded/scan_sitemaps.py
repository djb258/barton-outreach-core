#!/usr/bin/env python3
"""
Fast Sitemap Scanner — Phase 1
================================
Probes ALL 95K outreach companies with 1-2 requests each to determine
whether the domain has a discoverable sitemap.xml.

SNAP_ON_TOOLBOX compliant:
- Tier 0: Free (httpx only, no paid APIs)
- Uses httpx (not requests — requests is BANNED)

DOCTRINE compliant:
- Sources companies from outreach.outreach (operational spine, outreach_id PK)
- Saves to outreach.sitemap_discovery (FK: outreach_id)
- Credentials via Doppler env vars

Per-company logic (1-2 requests max):
  1. GET {domain}/sitemap.xml — if 200 + looks like XML → save, done
  2. GET {domain}/robots.txt — parse for Sitemap: directive → save, done
  3. Neither → save has_sitemap=FALSE, done

Usage:
    doppler run -- python hubs/blog-content/imo/middle/scan_sitemaps.py
    doppler run -- python hubs/blog-content/imo/middle/scan_sitemaps.py --dry-run --limit 100
    doppler run -- python hubs/blog-content/imo/middle/scan_sitemaps.py --workers 50
"""

import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# HTTP settings
CONNECT_TIMEOUT = 5.0
READ_TIMEOUT = 10.0
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# Batch size for DB writes
SAVE_BATCH_SIZE = 500

# Progress reporting interval
PROGRESS_INTERVAL = 500


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


def get_companies_to_scan(limit: Optional[int] = None) -> List[Dict]:
    """
    Get outreach companies not yet scanned for sitemaps.

    Sources from outreach.outreach (operational spine — all 95,004 companies).
    Resume-safe: excludes companies already in outreach.sitemap_discovery.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    limit_sql = f"LIMIT {int(limit)}" if limit else ""

    cur.execute(f"""
        SELECT
            o.outreach_id,
            o.domain
        FROM outreach.outreach o
        WHERE o.domain IS NOT NULL
          AND o.domain != ''
          AND NOT EXISTS (
            SELECT 1 FROM outreach.sitemap_discovery sd
            WHERE sd.outreach_id = o.outreach_id
          )
        ORDER BY o.domain
        {limit_sql}
    """)

    companies = cur.fetchall()
    cur.close()
    conn.close()
    return companies


def get_scan_progress() -> Dict:
    """Get current scan progress."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            COUNT(*) as total_scanned,
            COUNT(*) FILTER (WHERE has_sitemap = TRUE) as with_sitemap,
            COUNT(*) FILTER (WHERE has_sitemap = FALSE) as without_sitemap
        FROM outreach.sitemap_discovery
    """)
    row = cur.fetchone()

    cur.execute("""
        SELECT COUNT(*) as total_outreach
        FROM outreach.outreach
        WHERE domain IS NOT NULL AND domain != ''
    """)
    total = cur.fetchone()['total_outreach']

    cur.close()
    conn.close()

    return {
        'total_outreach': total,
        'total_scanned': row['total_scanned'],
        'with_sitemap': row['with_sitemap'],
        'without_sitemap': row['without_sitemap'],
    }


def save_batch(results: List[Dict]) -> int:
    """Save scan results to outreach.sitemap_discovery."""
    if not results:
        return 0

    conn = get_connection()
    cur = conn.cursor()

    try:
        execute_values(cur, """
            INSERT INTO outreach.sitemap_discovery
            (outreach_id, domain, sitemap_url, sitemap_source, has_sitemap, discovered_at)
            VALUES %s
            ON CONFLICT (outreach_id) DO NOTHING
        """, [
            (
                r['outreach_id'],
                r['domain'],
                r.get('sitemap_url'),
                r.get('sitemap_source'),
                r['has_sitemap'],
                datetime.now(timezone.utc),
            )
            for r in results
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


# ═══════════════════════════════════════════════════════════════
# SITEMAP PROBING
# ═══════════════════════════════════════════════════════════════

def normalize_domain(domain: str) -> str:
    """Build base URL from domain string."""
    domain = domain.strip()
    if domain.startswith(('http://', 'https://')):
        return domain.rstrip('/')
    return f"https://{domain}"


def looks_like_xml(text: str) -> bool:
    """Quick check if response body looks like XML (sitemap)."""
    # Check first 500 chars for XML indicators
    head = text[:500].strip()
    return (
        head.startswith('<?xml') or
        '<urlset' in head or
        '<sitemapindex' in head
    )


async def probe_company(
    client: httpx.AsyncClient,
    company: Dict,
    semaphore: asyncio.Semaphore,
) -> Dict:
    """
    Probe a single company for sitemap presence.

    Step 1: Try /sitemap.xml directly
    Step 2: If no sitemap, try /robots.txt for Sitemap: directive
    Step 3: If neither, mark has_sitemap=FALSE
    """
    async with semaphore:
        outreach_id = company['outreach_id']
        domain = company['domain']
        base_url = normalize_domain(domain)

        result = {
            'outreach_id': outreach_id,
            'domain': domain,
            'has_sitemap': False,
            'sitemap_url': None,
            'sitemap_source': None,
        }

        # Step 1: Try /sitemap.xml directly
        try:
            resp = await client.get(
                f"{base_url}/sitemap.xml",
                follow_redirects=True,
            )
            if resp.status_code == 200 and looks_like_xml(resp.text):
                result['has_sitemap'] = True
                result['sitemap_url'] = str(resp.url)
                result['sitemap_source'] = 'direct'
                return result
        except Exception:
            pass

        # Step 2: Try robots.txt for Sitemap: directive
        try:
            resp = await client.get(
                f"{base_url}/robots.txt",
                follow_redirects=True,
            )
            if resp.status_code == 200:
                for line in resp.text.splitlines():
                    stripped = line.strip()
                    if stripped.lower().startswith('sitemap:'):
                        # "Sitemap: https://..." — grab everything after "Sitemap:"
                        sitemap_url = stripped[len('Sitemap:'):].strip()
                        if sitemap_url:
                            result['has_sitemap'] = True
                            result['sitemap_url'] = sitemap_url
                            result['sitemap_source'] = 'robots'
                            return result
        except Exception:
            pass

        # Step 3: No sitemap found
        return result


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

async def run_scan(
    limit: Optional[int] = None,
    workers: int = 50,
    dry_run: bool = False,
):
    """Main scan loop."""

    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print('=' * 70)
    print('FAST SITEMAP SCANNER — Phase 1')
    print('=' * 70)
    print(f"Mode:       {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Workers:    {workers}")
    print(f"Limit:      {limit or 'ALL'}")
    print(f"Tier:       0 (FREE — httpx only)")
    print()

    # Current progress
    try:
        progress = get_scan_progress()
        print('CURRENT PROGRESS:')
        print(f"  Total outreach companies: {progress['total_outreach']:,}")
        print(f"  Already scanned:          {progress['total_scanned']:,}")
        print(f"    With sitemap:           {progress['with_sitemap']:,}")
        print(f"    Without sitemap:        {progress['without_sitemap']:,}")
        print()
    except Exception as e:
        print(f"Note: Could not read progress (table may not exist yet): {e}")
        print()

    # Get companies to scan
    companies = get_companies_to_scan(limit)
    total = len(companies)
    print(f"Companies to scan: {total:,}")
    print()

    if total == 0:
        print("All outreach companies already scanned!")
        return

    # Counters
    processed = 0
    with_sitemap = 0
    without_sitemap = 0
    total_saved = 0

    semaphore = asyncio.Semaphore(workers)

    async with httpx.AsyncClient(
        headers=HEADERS,
        follow_redirects=True,
        timeout=httpx.Timeout(
            connect=CONNECT_TIMEOUT,
            read=READ_TIMEOUT,
            write=READ_TIMEOUT,
            pool=READ_TIMEOUT,
        ),
        limits=httpx.Limits(
            max_connections=workers * 2,
            max_keepalive_connections=workers,
        ),
        transport=httpx.AsyncHTTPTransport(retries=0),
    ) as client:

        # Process in chunks for progress reporting and batch saves
        chunk_size = SAVE_BATCH_SIZE
        for chunk_start in range(0, total, chunk_size):
            chunk = companies[chunk_start:chunk_start + chunk_size]

            # Run chunk concurrently
            tasks = [
                probe_company(client, c, semaphore)
                for c in chunk
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect results
            chunk_results = []
            for r in results:
                if isinstance(r, Exception):
                    logger.debug(f"Task exception: {r}")
                    continue
                chunk_results.append(r)
                if r['has_sitemap']:
                    with_sitemap += 1
                else:
                    without_sitemap += 1

            processed += len(chunk)

            # Save batch
            if not dry_run and chunk_results:
                try:
                    saved = save_batch(chunk_results)
                    total_saved += saved
                except Exception as e:
                    logger.error(f"Save error: {e}")
            elif dry_run:
                total_saved += len(chunk_results)

            # Progress line
            pct = 100 * processed / total if total > 0 else 0
            print(
                f"  {processed:,}/{total:,} ({pct:.0f}%) | "
                f"Sitemap: {with_sitemap:,} | "
                f"No sitemap: {without_sitemap:,} | "
                f"Saved: {total_saved:,}",
                flush=True,
            )

    # Final summary
    print()
    print('=' * 70)
    print('RESULTS')
    print('=' * 70)
    print(f"Companies scanned:   {processed:,}")
    print(f"With sitemap:        {with_sitemap:,} ({100 * with_sitemap / max(1, processed):.1f}%)")
    print(f"Without sitemap:     {without_sitemap:,} ({100 * without_sitemap / max(1, processed):.1f}%)")
    print(f"Saved to DB:         {total_saved:,}")
    print()

    if dry_run:
        print("[DRY RUN — No data was saved]")


def main():
    parser = argparse.ArgumentParser(
        description='Fast Sitemap Scanner — Phase 1 (Tier 0 FREE)'
    )
    parser.add_argument('--limit', type=int, help='Max companies to scan')
    parser.add_argument('--workers', type=int, default=50, help='Concurrent workers (default: 50)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    asyncio.run(run_scan(
        limit=args.limit,
        workers=args.workers,
        dry_run=args.dry_run,
    ))


if __name__ == '__main__':
    main()
