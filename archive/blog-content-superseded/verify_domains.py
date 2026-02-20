#!/usr/bin/env python3
"""
Domain Reachability Verifier — Phase 1b
=========================================
Fast follow-up to scan_sitemaps.py. For every company where has_sitemap=FALSE,
sends a single HEAD request to the homepage to determine if the domain is alive.

A domain is "reachable" if the server responds with ANY HTTP status (200, 301,
302, 403, 404, etc.). A domain is "dead" only if the connection fails entirely
(DNS failure, connection refused, timeout with no response).

This separates "alive but no sitemap" from "truly dead domain."

SNAP_ON_TOOLBOX compliant:
- Tier 0: Free (httpx only, no paid APIs)
- Uses httpx (not requests — requests is BANNED)

DOCTRINE compliant:
- Reads/updates outreach.sitemap_discovery (FK: outreach_id)
- Credentials via Doppler env vars

Usage:
    doppler run -- python hubs/blog-content/imo/middle/verify_domains.py
    doppler run -- python hubs/blog-content/imo/middle/verify_domains.py --dry-run --limit 100
    doppler run -- python hubs/blog-content/imo/middle/verify_domains.py --workers 50
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

# HTTP settings
CONNECT_TIMEOUT = 5.0
READ_TIMEOUT = 10.0
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

SAVE_BATCH_SIZE = 500


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


def get_domains_to_verify(limit: Optional[int] = None) -> List[Dict]:
    """Get no-sitemap companies that haven't been reachability-checked yet."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    limit_sql = f"LIMIT {int(limit)}" if limit else ""

    cur.execute(f"""
        SELECT outreach_id, domain
        FROM outreach.sitemap_discovery
        WHERE has_sitemap = FALSE
          AND domain_reachable IS NULL
        ORDER BY domain
        {limit_sql}
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_verify_progress() -> Dict:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            COUNT(*) as total_no_sitemap,
            COUNT(*) FILTER (WHERE domain_reachable IS NOT NULL) as checked,
            COUNT(*) FILTER (WHERE domain_reachable = TRUE) as reachable,
            COUNT(*) FILTER (WHERE domain_reachable = FALSE) as dead,
            COUNT(*) FILTER (WHERE domain_reachable IS NULL) as pending
        FROM outreach.sitemap_discovery
        WHERE has_sitemap = FALSE
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
# DOMAIN VERIFICATION
# ═══════════════════════════════════════════════════════════════

def normalize_domain(domain: str) -> str:
    domain = domain.strip()
    if domain.startswith(('http://', 'https://')):
        return domain.rstrip('/')
    return f"https://{domain}"


async def verify_domain(
    client: httpx.AsyncClient,
    company: Dict,
    semaphore: asyncio.Semaphore,
) -> Dict:
    """
    Single HEAD request to homepage. Any HTTP response = reachable.
    Only connection failures = dead.
    """
    async with semaphore:
        outreach_id = company['outreach_id']
        base_url = normalize_domain(company['domain'])

        result = {
            'outreach_id': outreach_id,
            'domain_reachable': False,
            'http_status': None,
            'checked_at': datetime.now(timezone.utc),
        }

        try:
            resp = await client.head(
                base_url,
                follow_redirects=True,
            )
            # Any HTTP response means the domain is alive
            result['domain_reachable'] = True
            result['http_status'] = resp.status_code
            return result

        except httpx.HTTPStatusError as e:
            # Got an HTTP response but it was an error status — still reachable
            result['domain_reachable'] = True
            result['http_status'] = e.response.status_code
            return result

        except Exception:
            # Connection failed entirely — DNS failure, timeout, refused, etc.
            result['domain_reachable'] = False
            result['http_status'] = None
            return result


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

async def run_verify(
    limit: Optional[int] = None,
    workers: int = 50,
    dry_run: bool = False,
):
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print('=' * 70)
    print('DOMAIN REACHABILITY VERIFIER — Phase 1b')
    print('=' * 70)
    print(f"Mode:       {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Workers:    {workers}")
    print(f"Limit:      {limit or 'ALL'}")
    print(f"Tier:       0 (FREE — httpx only)")
    print()

    # Current progress
    try:
        progress = get_verify_progress()
        print('CURRENT PROGRESS:')
        print(f"  No-sitemap companies:  {progress['total_no_sitemap']:,}")
        print(f"  Already checked:       {progress['checked']:,}")
        print(f"    Reachable:           {progress['reachable']:,}")
        print(f"    Dead:                {progress['dead']:,}")
        print(f"  Pending:               {progress['pending']:,}")
        print()
    except Exception as e:
        print(f"Note: Could not read progress: {e}")
        print()

    # Get domains to verify
    domains = get_domains_to_verify(limit)
    total = len(domains)
    print(f"Domains to verify: {total:,}")
    print()

    if total == 0:
        print("All no-sitemap domains already verified!")
        return

    # Counters
    processed = 0
    reachable = 0
    dead = 0
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

        chunk_size = SAVE_BATCH_SIZE
        for chunk_start in range(0, total, chunk_size):
            chunk = domains[chunk_start:chunk_start + chunk_size]

            tasks = [
                verify_domain(client, d, semaphore)
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
                    reachable += 1
                else:
                    dead += 1

            processed += len(chunk)

            if not dry_run and chunk_results:
                try:
                    saved = save_batch(chunk_results)
                    total_saved += saved
                except Exception as e:
                    logger.error(f"Save error: {e}")
            elif dry_run:
                total_saved += len(chunk_results)

            pct = 100 * processed / total if total > 0 else 0
            print(
                f"  {processed:,}/{total:,} ({pct:.0f}%) | "
                f"Reachable: {reachable:,} | "
                f"Dead: {dead:,} | "
                f"Saved: {total_saved:,}",
                flush=True,
            )

    # Final summary
    print()
    print('=' * 70)
    print('RESULTS')
    print('=' * 70)
    print(f"Domains checked:     {processed:,}")
    print(f"Reachable (alive):   {reachable:,} ({100 * reachable / max(1, processed):.1f}%)")
    print(f"Dead (unreachable):  {dead:,} ({100 * dead / max(1, processed):.1f}%)")
    print(f"Saved to DB:         {total_saved:,}")
    print()

    if dead > 0:
        dead_pct = 100 * dead / max(1, processed)
        print(f"Dead domains are {dead_pct:.1f}% of no-sitemap companies.")
        print(f"Cross-reference with DOL + email verification to confirm exclusion.")

    if dry_run:
        print()
        print("[DRY RUN — No data was saved]")


def main():
    parser = argparse.ArgumentParser(
        description='Domain Reachability Verifier — Phase 1b (Tier 0 FREE)'
    )
    parser.add_argument('--limit', type=int, help='Max domains to verify')
    parser.add_argument('--workers', type=int, default=50, help='Concurrent workers (default: 50)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    asyncio.run(run_verify(
        limit=args.limit,
        workers=args.workers,
        dry_run=args.dry_run,
    ))


if __name__ == '__main__':
    main()
