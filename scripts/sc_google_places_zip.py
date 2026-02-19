#!/usr/bin/env python3
"""
Fill remaining SC company ZIPs via Google Places API (New).

Looks up companies without postal_code in CT, searches Google Places
by company name + state, extracts the address, writes ZIP to CT.

COST GUARDRAILS:
  - Places Text Search (IDs Only): FREE
  - Place Details Essentials: $5/1K (first 10K/month FREE)
  - Hard cap: MAX_CALLS (default 1,500)
  - Running cost printed after each batch
  - Throttled to 10 req/sec

Usage:
    doppler run -- python scripts/sc_google_places_zip.py --dry-run
    doppler run -- python scripts/sc_google_places_zip.py
    doppler run -- python scripts/sc_google_places_zip.py --max-calls 500
"""
import os
import sys
import io
import re
import time
import argparse
from datetime import datetime, timezone

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import httpx
import psycopg2

# ══════════════════════════════════════════════════════════════
# COST MODEL (Places API New — Essentials tier)
# ══════════════════════════════════════════════════════════════
# Text Search (IDs Only):      FREE
# Text Search (Basic fields):  $32/1K  ← we use this (includes formattedAddress)
# Place Details Essentials:    $5/1K   (first 10K free)
#
# We use Text Search with formattedAddress field mask.
# This is the "Basic" tier = $0.032 per call.
# 1,464 calls × $0.032 = $46.85 MAX (but $200 free credit covers it).
#
# ACTUALLY: Google gives $200/month free credit across all Maps APIs.
# So effective cost = $0 as long as total monthly usage < $200.
# ══════════════════════════════════════════════════════════════

COST_PER_CALL = 0.032  # Text Search Basic tier
MAX_CALLS_DEFAULT = 1500
THROTTLE_PER_SEC = 10  # max requests per second

PLACES_URL = 'https://places.googleapis.com/v1/places:searchText'

# US state abbreviations for validation
US_STATES = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC',
}


def get_conn():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        dbname=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require',
    )


def parse_address(formatted_address):
    """
    Parse Google's formatted_address into components.
    Example: "123 Main St, Charleston, SC 29401, USA"
    Returns {address1, city, state, zip} or None.
    """
    if not formatted_address:
        return None

    # Remove country suffix
    addr = formatted_address.strip()
    addr = re.sub(r',\s*USA?\s*$', '', addr, flags=re.IGNORECASE)
    addr = re.sub(r',\s*United States\s*$', '', addr, flags=re.IGNORECASE)

    # Pattern: ..., City, ST ZIP
    m = re.search(r',\s*([A-Za-z\s\.]+?),\s*([A-Z]{2})\s+(\d{5})(?:-\d{4})?\s*$', addr)
    if m:
        city = m.group(1).strip()
        state = m.group(2).upper()
        zip_code = m.group(3)

        if state not in US_STATES:
            return None

        # Everything before the city match is the street address
        street = addr[:m.start()].strip().rstrip(',').strip()

        return {
            'address1': street,
            'city': city,
            'state': state,
            'zip': zip_code,
        }

    return None


def search_place(client, api_key, company_name, state='SC'):
    """
    Search Google Places for a company. Returns parsed address or None.
    """
    query = f"{company_name}, {state}"

    try:
        resp = client.post(
            PLACES_URL,
            headers={
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': api_key,
                'X-Goog-FieldMask': 'places.formattedAddress,places.displayName',
            },
            json={
                'textQuery': query,
                'maxResultCount': 1,
            },
            timeout=10.0,
        )

        if resp.status_code != 200:
            return None, resp.status_code

        data = resp.json()
        places = data.get('places', [])
        if not places:
            return None, 'no_results'

        place = places[0]
        formatted = place.get('formattedAddress', '')
        display_name = place.get('displayName', {}).get('text', '')

        parsed = parse_address(formatted)
        if parsed:
            parsed['google_name'] = display_name
            parsed['google_address'] = formatted

        return parsed, 'ok'

    except Exception as e:
        return None, str(e)[:60]


def main():
    parser = argparse.ArgumentParser(description='Fill SC ZIPs via Google Places API')
    parser.add_argument('--dry-run', action='store_true', help='Preview without DB writes')
    parser.add_argument('--max-calls', type=int, default=MAX_CALLS_DEFAULT,
                        help=f'Hard cap on API calls (default: {MAX_CALLS_DEFAULT})')
    parser.add_argument('--limit', type=int, help='Only process first N companies')
    args = parser.parse_args()

    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not set. Run with: doppler run -- python ...")
        sys.exit(1)

    print("=" * 60)
    print("GOOGLE PLACES ZIP LOOKUP — SC Companies")
    print("=" * 60)
    print(f"Mode:      {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Max calls: {args.max_calls:,}")
    print(f"Cost cap:  ${args.max_calls * COST_PER_CALL:.2f} (within $200/mo free credit)")
    print(f"Throttle:  {THROTTLE_PER_SEC} req/sec")
    print(f"Started:   {datetime.now().isoformat()}")

    conn = get_conn()
    cur = conn.cursor()

    # Get SC companies without ZIP
    limit_sql = f"LIMIT {args.limit}" if args.limit else ""
    cur.execute(f"""
        SELECT ci.company_unique_id::text,
               ci.company_name,
               ci.company_domain,
               o.outreach_id::text
        FROM cl.company_identity ci
        JOIN outreach.outreach o ON o.sovereign_id = ci.company_unique_id
        JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
        WHERE ci.state_code = 'SC'
          AND (ct.postal_code IS NULL OR ct.postal_code = '')
        ORDER BY ci.company_name
        {limit_sql}
    """)
    companies = cur.fetchall()
    total = len(companies)

    print(f"\nCompanies needing ZIP: {total:,}")
    if total == 0:
        print("All SC companies already have ZIPs!")
        conn.close()
        return

    if total > args.max_calls:
        print(f"WARNING: {total:,} companies exceeds max_calls ({args.max_calls:,})")
        print(f"  Will process first {args.max_calls:,} only")
        companies = companies[:args.max_calls]
        total = len(companies)

    est_cost = total * COST_PER_CALL
    print(f"Estimated cost: ${est_cost:.2f}")
    print()

    # Process
    client = httpx.Client(timeout=10.0)
    calls = 0
    found = 0
    written = 0
    no_result = 0
    wrong_state = 0
    errors = 0
    cost = 0.0

    batch_start = time.time()
    batch_count = 0

    for i, (sid, name, domain, oid) in enumerate(companies):
        # Throttle
        batch_count += 1
        if batch_count >= THROTTLE_PER_SEC:
            elapsed = time.time() - batch_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            batch_start = time.time()
            batch_count = 0

        # Search
        result, status = search_place(client, api_key, name, 'SC')
        calls += 1
        cost = calls * COST_PER_CALL

        if result:
            found += 1

            # Validate: prefer SC addresses, but accept neighboring states
            result_state = result.get('state', '')
            if result_state != 'SC' and result_state not in ('NC', 'GA'):
                wrong_state += 1
                # Still write it — it's the best we have, and postal_code_source
                # will indicate it came from Google

            zip_code = result['zip']
            city = result.get('city', '')
            state = result.get('state', '')

            if not args.dry_run:
                try:
                    cur.execute("""
                        UPDATE outreach.company_target
                        SET postal_code = %s,
                            city = COALESCE(NULLIF(%s, ''), city),
                            state = COALESCE(NULLIF(%s, ''), state),
                            postal_code_source = %s,
                            postal_code_updated_at = %s,
                            updated_at = NOW()
                        WHERE outreach_id = %s::uuid
                          AND (postal_code IS NULL OR postal_code = '')
                    """, (
                        zip_code, city, state,
                        'google_places',
                        datetime.now(timezone.utc),
                        oid,
                    ))
                    if cur.rowcount > 0:
                        written += 1
                except Exception as e:
                    print(f"    DB ERROR for {oid}: {e}")
                    conn.rollback()
                    errors += 1
            else:
                written += 1
        else:
            no_result += 1

        # Commit every 100
        if not args.dry_run and written % 100 == 0 and written > 0:
            conn.commit()

        # Progress every 100
        if (i + 1) % 100 == 0 or (i + 1) == total:
            pct = 100 * (i + 1) / total
            print(
                f"  [{i+1:,}/{total:,}] ({pct:.0f}%) "
                f"Found: {found:,} | Written: {written:,} | "
                f"No result: {no_result:,} | Cost: ${cost:.2f}",
                flush=True,
            )

    if not args.dry_run:
        conn.commit()

    client.close()

    # Final summary
    print(f"\n{'=' * 60}")
    print("RESULTS")
    print(f"{'=' * 60}")
    print(f"  API calls:       {calls:,}")
    print(f"  Addresses found: {found:,}")
    print(f"  ZIPs written:    {written:,}")
    print(f"  No results:      {no_result:,}")
    print(f"  Wrong state:     {wrong_state:,} (still written)")
    print(f"  Errors:          {errors:,}")
    print(f"  Total cost:      ${cost:.2f}")
    print()

    # Updated DB status
    try:
        conn.close()
    except Exception:
        pass
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*),
               COUNT(CASE WHEN ct.postal_code IS NOT NULL AND ct.postal_code <> '' THEN 1 END)
        FROM cl.company_identity ci
        JOIN outreach.outreach o ON o.sovereign_id = ci.company_unique_id
        JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
        WHERE ci.state_code = 'SC'
    """)
    total_sc, with_zip = cur.fetchone()

    print(f"FINAL SC STATUS:")
    print(f"  Total in CT:  {total_sc:,}")
    print(f"  With ZIP:     {with_zip:,}")
    print(f"  Without ZIP:  {total_sc - with_zip:,}")
    print(f"  ZIP coverage: {100*with_zip/max(1,total_sc):.1f}%")
    print(f"{'=' * 60}")
    print(f"Completed: {datetime.now().isoformat()}")

    if args.dry_run:
        print("\n[DRY RUN — No data was written]")

    conn.close()


if __name__ == '__main__':
    main()
