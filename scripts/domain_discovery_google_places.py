#!/usr/bin/env python3
"""
Discover domains for companies with no domain using Google Places API.

Searches by company_name + city + state, extracts websiteUri.
Updates outreach.outreach.domain for matches.

Cost: $0.032/call (Basic SKU), covered by $200/mo free credit.

Usage:
    doppler run -- python scripts/domain_discovery_google_places.py --dry-run
    doppler run -- python scripts/domain_discovery_google_places.py
    doppler run -- python scripts/domain_discovery_google_places.py --coverage-id <id>
"""
import os
import sys
import io
import re
import time
import argparse
from datetime import datetime, timezone
from urllib.parse import urlparse

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import httpx
import psycopg2

PLACES_URL = 'https://places.googleapis.com/v1/places:searchText'
FIELD_MASK = 'places.displayName,places.websiteUri,places.formattedAddress'
THROTTLE_PER_SEC = 10
MAX_CALLS = 500  # safety cap
COST_PER_CALL = 0.032


def get_conn():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        dbname=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require',
    )


def extract_domain(url):
    """Extract clean domain from URL."""
    if not url:
        return None
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ''
        # Strip www.
        if host.startswith('www.'):
            host = host[4:]
        return host.lower() if host else None
    except Exception:
        return None


def search_place(client, api_key, company_name, city, state):
    """Search Google Places for a company, return (domain, website_url, display_name)."""
    query = f"{company_name} {city} {state}" if city else f"{company_name} {state}"

    try:
        resp = client.post(
            PLACES_URL,
            json={'textQuery': query},
            headers={
                'X-Goog-Api-Key': api_key,
                'X-Goog-FieldMask': FIELD_MASK,
                'Content-Type': 'application/json',
            },
            timeout=10.0,
        )

        if resp.status_code != 200:
            return None, None, None, f"HTTP {resp.status_code}"

        data = resp.json()
        places = data.get('places', [])
        if not places:
            return None, None, None, "no results"

        place = places[0]
        website = place.get('websiteUri')
        display = place.get('displayName', {}).get('text', '')
        address = place.get('formattedAddress', '')
        domain = extract_domain(website)

        return domain, website, display, None

    except Exception as e:
        return None, None, None, str(e)


def main():
    parser = argparse.ArgumentParser(description='Domain discovery via Google Places API')
    parser.add_argument('--dry-run', action='store_true', help='Preview without DB writes')
    parser.add_argument('--coverage-id', default='0456811b-9c77-48c5-9bc3-99f188066272',
                        help='Coverage ID to scope companies')
    parser.add_argument('--limit', type=int, default=0, help='Limit number of API calls')
    args = parser.parse_args()

    api_key = os.environ.get('GOOGLE_PLACES_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("ERROR: Set GOOGLE_PLACES_API_KEY or GOOGLE_API_KEY env var")
        sys.exit(1)

    print("=" * 60)
    print("Domain Discovery via Google Places API")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Coverage: {args.coverage_id}")
    print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)

    conn = get_conn()
    cur = conn.cursor()

    # Get radius ZIPs
    cur.execute('SELECT zip FROM coverage.v_service_agent_coverage_zips WHERE coverage_id = %s',
                (args.coverage_id,))
    zips = [r[0] for r in cur.fetchall()]
    if not zips:
        print("ERROR: No ZIPs found for coverage_id")
        sys.exit(1)

    cur.execute('''
        SELECT anchor_zip, radius_miles FROM coverage.service_agent_coverage
        WHERE coverage_id = %s
    ''', (args.coverage_id,))
    azip, radius = cur.fetchone()

    # Get allowed states from the ZIPs
    cur.execute('''
        SELECT DISTINCT UPPER(TRIM(ct.state))
        FROM outreach.company_target ct
        WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
          AND ct.state IS NOT NULL
    ''', (zips,))
    allowed_states = [r[0] for r in cur.fetchall() if r[0] and len(r[0]) == 2]

    print(f"  Anchor: {azip} / {radius}mi")
    print(f"  ZIPs: {len(zips)}, States: {', '.join(sorted(allowed_states))}")

    # Find no-domain companies in this market
    cur.execute('''
        WITH market AS (
            SELECT ct.outreach_id, ct.company_unique_id, ct.city, ct.state, ct.postal_code
            FROM outreach.company_target ct
            WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
              AND UPPER(TRIM(ct.state)) = ANY(%s)
        )
        SELECT
            m.outreach_id::text,
            ci.company_name,
            m.city,
            m.state,
            m.postal_code,
            ci.source_system
        FROM market m
        JOIN outreach.outreach o ON m.outreach_id = o.outreach_id
        JOIN cl.company_identity ci ON m.company_unique_id = ci.company_unique_id::text
        WHERE (o.domain IS NULL OR o.domain = '')
        ORDER BY ci.company_name
    ''', (zips, allowed_states))

    companies = cur.fetchall()
    print(f"  No-domain companies: {len(companies)}")

    if not companies:
        print("  Nothing to do.")
        return

    limit = args.limit if args.limit > 0 else min(len(companies), MAX_CALLS)
    companies = companies[:limit]
    print(f"  Will process: {len(companies)} (est. cost: ${len(companies) * COST_PER_CALL:.2f})")

    # Run API calls
    found = 0
    not_found = 0
    errors = 0
    total_cost = 0.0

    client = httpx.Client(transport=httpx.HTTPTransport(retries=0))

    for i, (oid, name, city, state, zip_code, source) in enumerate(companies):
        domain, website, display, error = search_place(client, api_key, name, city, state)
        total_cost += COST_PER_CALL

        if error:
            not_found += 1
            if i < 5 or 'HTTP' in str(error):
                print(f"    [{i+1}] {name} -> {error}")
        elif domain:
            found += 1
            if i < 20 or found <= 10:
                print(f"    [{i+1}] {name} -> {domain}")

            if not args.dry_run:
                try:
                    cur.execute("""
                        UPDATE outreach.outreach
                        SET domain = %s
                        WHERE outreach_id = %s::uuid
                          AND (domain IS NULL OR domain = '')
                    """, (domain, oid))
                    conn.commit()
                except Exception as e:
                    print(f"    DB ERROR for {oid}: {e}")
                    conn.rollback()
                    errors += 1
        else:
            not_found += 1

        # Throttle
        if (i + 1) % THROTTLE_PER_SEC == 0:
            time.sleep(1.0)

        # Progress
        if (i + 1) % 50 == 0:
            print(f"  ... {i+1}/{len(companies)} | found={found} | cost=${total_cost:.2f}")

    client.close()

    print(f"\n{'=' * 60}")
    print("RESULTS")
    print(f"{'=' * 60}")
    print(f"  API calls:     {len(companies)}")
    print(f"  Domains found: {found} ({100*found/max(len(companies),1):.1f}%)")
    print(f"  Not found:     {not_found}")
    print(f"  DB errors:     {errors}")
    print(f"  Total cost:    ${total_cost:.2f}")

    if not args.dry_run and found > 0:
        # Verify
        cur.execute('''
            WITH market AS (
                SELECT ct.outreach_id
                FROM outreach.company_target ct
                WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
                  AND UPPER(TRIM(ct.state)) = ANY(%s)
            )
            SELECT COUNT(*) FROM market m
            JOIN outreach.outreach o ON m.outreach_id = o.outreach_id
            WHERE (o.domain IS NULL OR o.domain = '')
        ''', (zips, allowed_states))
        remaining = cur.fetchone()[0]
        print(f"  Remaining no-domain: {remaining}")

    conn.close()


if __name__ == '__main__':
    main()
