#!/usr/bin/env python3
"""
Dead Domain Recovery Scanner — Phase 1c
=========================================
Second-pass scanner for domains marked dead by verify_domains.py (Phase 1b).
Tries alternative connection methods to recover domains that may have been
incorrectly classified as dead.

Recovery strategies (in order):
  1. GET instead of HEAD (some servers reject HEAD)
  2. http:// instead of https:// (SSL issues)
  3. www. prefix (some sites only respond to www.domain.com)
  4. www. + http:// combo

A domain is "recovered" if ANY variant returns an HTTP response.

SNAP_ON_TOOLBOX compliant:
- Tier 0: Free (httpx only, no paid APIs)
- Uses httpx (not requests — requests is BANNED)

DOCTRINE compliant:
- Reads/updates outreach.sitemap_discovery (FK: outreach_id)
- Credentials via Doppler env vars

Usage:
    doppler run -- python hubs/blog-content/imo/middle/recover_dead_domains.py --limit 500
    doppler run -- python hubs/blog-content/imo/middle/recover_dead_domains.py --dry-run --limit 100
    doppler run -- python hubs/blog-content/imo/middle/recover_dead_domains.py --workers 30
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
from psycopg2.extras import RealDictCursor, execute_batch

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# HTTP settings — slightly more generous for recovery
CONNECT_TIMEOUT = 8.0
READ_TIMEOUT = 15.0
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

SAVE_BATCH_SIZE = 250


# ═══════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════

def get_neon_config() -> Dict:
    host = os.environ.get('NEON_HOST')
    password = os.environ.get('NEON_PASSWORD')
    if not host or not password:
        raise EnvironmentError(
            "NEON_HOST and NEON_PASSWORD must be set. "
            "Run with: doppler run -- python ..."
        )
    return {
        'host': host, 'port': 5432,
        'database': os.environ.get('NEON_DATABASE', 'Marketing DB'),
        'user': os.environ.get('NEON_USER', 'Marketing DB_owner'),
        'password': password, 'sslmode': 'require',
    }


def get_connection():
    return psycopg2.connect(**get_neon_config())


def get_dead_domains_with_dol(limit: Optional[int] = None) -> List[Dict]:
    """Get dead domains that have DOL records (recovery candidates)."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    limit_sql = f"LIMIT {int(limit)}" if limit else ""

    cur.execute(f"""
        SELECT sd.outreach_id, sd.domain
        FROM outreach.sitemap_discovery sd
        JOIN outreach.dol d ON d.outreach_id = sd.outreach_id
        WHERE sd.has_sitemap = FALSE
          AND sd.domain_reachable = FALSE
        ORDER BY sd.domain
        {limit_sql}
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_recovery_progress() -> Dict:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            COUNT(*) as total_dead_dol,
            COUNT(*) FILTER (WHERE domain_reachable = TRUE) as recovered,
            COUNT(*) FILTER (WHERE domain_reachable = FALSE) as still_dead
        FROM outreach.sitemap_discovery sd
        JOIN outreach.dol d ON d.outreach_id = sd.outreach_id
        WHERE sd.has_sitemap = FALSE
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def save_batch(results: List[Dict]) -> int:
    if not results:
        return 0

    conn = get_connection()
    cur = conn.cursor()

    try:
        execute_batch(cur, """
            UPDATE outreach.sitemap_discovery
            SET domain_reachable = %(domain_reachable)s,
                http_status = %(http_status)s,
                reachable_checked_at = %(checked_at)s
            WHERE outreach_id = %(outreach_id)s
        """, results)
        conn.commit()
        return len(results)

    except Exception as e:
        logger.error(f"Error saving batch: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


# ═══════════════════════════════════════════════════════════════
# RECOVERY LOGIC
# ═══════════════════════════════════════════════════════════════

def build_variants(domain: str) -> List[str]:
    """
    Build URL variants to try for a dead domain.
    Order: most likely to work first.
    """
    clean = domain.strip().lower()
    # Strip any existing protocol/www
    for prefix in ('https://', 'http://', 'www.'):
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
    clean = clean.rstrip('/')

    has_www = domain.strip().lower().startswith('www.')

    variants = []

    # 1. GET https:// (original was HEAD — try GET)
    variants.append(f"https://{clean}")

    # 2. GET http:// (SSL may be broken)
    variants.append(f"http://{clean}")

    # 3. GET https://www. (some sites only respond to www)
    if not has_www:
        variants.append(f"https://www.{clean}")

    # 4. GET http://www.
    if not has_www:
        variants.append(f"http://www.{clean}")

    return variants


async def try_variant(
    client: httpx.AsyncClient,
    url: str,
) -> Optional[Dict]:
    """Try a single URL variant. Returns status info or None on failure."""
    try:
        resp = await client.get(
            url,
            follow_redirects=True,
        )
        return {
            'reachable': True,
            'status': resp.status_code,
            'url': str(resp.url),
        }
    except httpx.HTTPStatusError as e:
        return {
            'reachable': True,
            'status': e.response.status_code,
            'url': url,
        }
    except Exception:
        return None


async def recover_domain(
    client: httpx.AsyncClient,
    company: Dict,
    semaphore: asyncio.Semaphore,
) -> Dict:
    """
    Try multiple URL variants for a dead domain.
    Returns on first successful contact.
    """
    async with semaphore:
        outreach_id = company['outreach_id']
        domain = company['domain']
        variants = build_variants(domain)

        result = {
            'outreach_id': outreach_id,
            'domain_reachable': False,
            'http_status': None,
            'checked_at': datetime.now(timezone.utc),
            'recovery_method': None,
        }

        for variant_url in variants:
            hit = await try_variant(client, variant_url)
            if hit and hit['reachable']:
                result['domain_reachable'] = True
                result['http_status'] = hit['status']
                result['recovery_method'] = variant_url
                return result

        # All variants failed
        return result


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

async def run_recovery(
    limit: Optional[int] = None,
    workers: int = 30,
    dry_run: bool = False,
):
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print('=' * 70)
    print('DEAD DOMAIN RECOVERY SCANNER - Phase 1c')
    print('=' * 70)
    print(f"Mode:       {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Workers:    {workers}")
    print(f"Limit:      {limit or 'ALL'}")
    print(f"Tier:       0 (FREE - httpx only)")
    print(f"Strategy:   GET + http:// + www. variants")
    print()

    # Get dead domains with DOL
    domains = get_dead_domains_with_dol(limit)
    total = len(domains)
    print(f"Dead+DOL domains to recover: {total:,}")
    print()

    if total == 0:
        print("No dead+DOL domains to recover!")
        return

    # Counters
    processed = 0
    recovered = 0
    still_dead = 0
    total_saved = 0

    # Track recovery methods
    recovery_methods = {}

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

        chunk_size = SAVE_BATCH_SIZE
        for chunk_start in range(0, total, chunk_size):
            chunk = domains[chunk_start:chunk_start + chunk_size]

            tasks = [
                recover_domain(client, d, semaphore)
                for d in chunk
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            chunk_results = []
            for r in results:
                if isinstance(r, Exception):
                    logger.debug(f"Task exception: {r}")
                    continue

                chunk_results.append(r)
                if r['domain_reachable']:
                    recovered += 1
                    method = r.get('recovery_method', 'unknown')
                    # Classify the method
                    if 'http://' in method and 'www.' in method:
                        key = 'http + www'
                    elif 'http://' in method:
                        key = 'http (no SSL)'
                    elif 'www.' in method:
                        key = 'https + www'
                    else:
                        key = 'GET (was HEAD)'
                    recovery_methods[key] = recovery_methods.get(key, 0) + 1
                else:
                    still_dead += 1

            processed += len(chunk)

            # Save only recovered domains (flip reachable to TRUE)
            save_results = [r for r in chunk_results if r['domain_reachable']]

            if not dry_run and save_results:
                try:
                    saved = save_batch(save_results)
                    total_saved += saved
                except Exception as e:
                    logger.error(f"Save error: {e}")
            elif dry_run:
                total_saved += len(save_results)

            pct = 100 * processed / total if total > 0 else 0
            print(
                f"  {processed:,}/{total:,} ({pct:.0f}%) | "
                f"Recovered: {recovered:,} | "
                f"Still dead: {still_dead:,} | "
                f"Saved: {total_saved:,}",
                flush=True,
            )

    # Final summary
    print()
    print('=' * 70)
    print('RESULTS')
    print('=' * 70)
    print(f"Domains checked:     {processed:,}")
    print(f"RECOVERED (alive):   {recovered:,} ({100 * recovered / max(1, processed):.1f}%)")
    print(f"Still dead:          {still_dead:,} ({100 * still_dead / max(1, processed):.1f}%)")
    print(f"Saved to DB:         {total_saved:,}")
    print()

    if recovery_methods:
        print('RECOVERY METHOD BREAKDOWN:')
        for method, count in sorted(recovery_methods.items(), key=lambda x: -x[1]):
            print(f"  {method:20s} {count:,} ({100*count/max(1,recovered):.1f}%)")
        print()

    if dry_run:
        print("[DRY RUN - No data was saved]")


def main():
    parser = argparse.ArgumentParser(
        description='Dead Domain Recovery Scanner - Phase 1c (Tier 0 FREE)'
    )
    parser.add_argument('--limit', type=int, help='Max domains to check')
    parser.add_argument('--workers', type=int, default=30, help='Concurrent workers (default: 30)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    asyncio.run(run_recovery(
        limit=args.limit,
        workers=args.workers,
        dry_run=args.dry_run,
    ))


if __name__ == '__main__':
    main()
