#!/usr/bin/env python3
"""
Onboard ALL South Carolina companies to the outreach spine + scrape ZIPs.

Pipeline:
  STEP 1: Mint outreach_ids (outreach.outreach -> CL write-back)
  STEP 2: Create company_target records (with DOL address where available)
  STEP 3: Create company_slots (CEO/CFO/HR)
  STEP 4: Scrape CLAY domains for About Us / Contact page -> extract ZIP
  STEP 5: Update company_target.postal_code from scraped addresses

Sources:
  - HUNTER_DOL_SS003: 762 need onboarding (already have DOL addresses)
  - CLAY_SC_SS005:   2,878 need onboarding (need domain scraping for ZIPs)

Usage:
    doppler run -- python scripts/onboard_sc_companies.py [--dry-run]
    doppler run -- python scripts/onboard_sc_companies.py --step 1   # Onboard only
    doppler run -- python scripts/onboard_sc_companies.py --step 4   # Scrape only
    doppler run -- python scripts/onboard_sc_companies.py --workers 30
"""
import os
import sys
import io
import re
import csv
import uuid
import json
import asyncio
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from collections import defaultdict

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import httpx
import psycopg2

# DOL address file from sc_dol_address_match.py
DOL_ADDR_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'exports', 'sc_companies_with_addresses.csv',
)


def get_conn():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        dbname=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require',
    )


# ══════════════════════════════════════════════════════════════
# STEP 1: Mint outreach_ids
# ══════════════════════════════════════════════════════════════

def step1_mint_outreach_ids(conn, dry_run=False):
    """Mint outreach_ids for all SC companies without one."""
    print(f"\n{'=' * 60}")
    print("STEP 1: Mint outreach_ids for SC companies")
    print(f"{'=' * 60}")

    cur = conn.cursor()

    # Get all SC companies without outreach_id
    cur.execute("""
        SELECT company_unique_id::text, company_name, company_domain,
               source_system
        FROM cl.company_identity
        WHERE state_code = 'SC'
          AND outreach_id IS NULL
        ORDER BY source_system, company_name
    """)
    companies = cur.fetchall()
    print(f"  SC companies needing outreach_id: {len(companies):,}")

    by_source = defaultdict(int)
    for _, _, _, ss in companies:
        by_source[ss] += 1
    for ss, cnt in sorted(by_source.items()):
        print(f"    {ss}: {cnt:,}")

    minted = 0
    errors = 0
    oid_map = {}  # sovereign_id -> outreach_id

    for sid, name, domain, source_sys in companies:
        domain_clean = (domain or '').lower().strip() or None
        new_oid = str(uuid.uuid4())

        if dry_run:
            oid_map[sid] = new_oid
            minted += 1
            continue

        try:
            # Insert into outreach.outreach (operational spine)
            cur.execute("""
                INSERT INTO outreach.outreach (outreach_id, sovereign_id, domain)
                VALUES (%s::uuid, %s::uuid, %s)
                ON CONFLICT DO NOTHING
            """, (new_oid, sid, domain_clean))

            if cur.rowcount == 0:
                # Might already exist by domain
                if domain_clean:
                    cur.execute("""
                        SELECT outreach_id::text FROM outreach.outreach
                        WHERE LOWER(domain) = %s
                    """, (domain_clean,))
                    existing = cur.fetchone()
                    if existing:
                        new_oid = existing[0]
                    else:
                        errors += 1
                        continue
                else:
                    errors += 1
                    continue

            # Write outreach_id back to CL (WRITE-ONCE)
            cur.execute("""
                UPDATE cl.company_identity
                SET outreach_id = %s::uuid
                WHERE company_unique_id = %s::uuid AND outreach_id IS NULL
            """, (new_oid, sid))

            if cur.rowcount == 1:
                oid_map[sid] = new_oid
                minted += 1
            else:
                # Already claimed — fetch
                cur.execute("""
                    SELECT outreach_id::text FROM cl.company_identity
                    WHERE company_unique_id = %s::uuid
                """, (sid,))
                cl_oid = cur.fetchone()
                if cl_oid and cl_oid[0]:
                    oid_map[sid] = cl_oid[0]
                    minted += 1
                else:
                    errors += 1

            if minted % 200 == 0:
                conn.commit()

        except Exception as e:
            print(f"    ERROR minting {sid}: {e}")
            conn.rollback()
            errors += 1

    if not dry_run:
        conn.commit()

    print(f"  Minted: {minted:,}")
    print(f"  Errors: {errors:,}")
    return oid_map


# ══════════════════════════════════════════════════════════════
# STEP 2: Create company_target records
# ══════════════════════════════════════════════════════════════

def load_dol_addresses():
    """Load DOL-matched addresses from the export CSV."""
    if not os.path.exists(DOL_ADDR_CSV):
        print(f"  WARNING: DOL address CSV not found: {DOL_ADDR_CSV}")
        return {}

    addr_map = {}  # company_unique_id -> {city, state, zip, ein, addr1, addr2}
    with open(DOL_ADDR_CSV, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            cuid = (row.get('company_unique_id') or '').strip()
            zip_code = (row.get('zip') or '').strip()
            if cuid and zip_code:
                addr_map[cuid] = {
                    'city': (row.get('city') or '').strip(),
                    'state': (row.get('state') or '').strip(),
                    'zip': zip_code,
                    'ein': (row.get('ein') or '').strip(),
                    'addr1': (row.get('address1') or '').strip(),
                    'addr2': (row.get('address2') or '').strip(),
                }
    return addr_map


def step2_create_company_targets(conn, oid_map, dry_run=False):
    """Create company_target records. Use DOL addresses where available."""
    print(f"\n{'=' * 60}")
    print("STEP 2: Create company_target records")
    print(f"{'=' * 60}")

    cur = conn.cursor()

    # Load DOL addresses from the earlier match
    dol_addr = load_dol_addresses()
    print(f"  DOL addresses loaded: {len(dol_addr):,}")

    # Check which already exist in CT
    oid_list = list(oid_map.values())
    existing_ct = set()
    if oid_list:
        # Batch check in chunks of 5000
        for i in range(0, len(oid_list), 5000):
            chunk = oid_list[i:i+5000]
            cur.execute("""
                SELECT outreach_id::text FROM outreach.company_target
                WHERE outreach_id = ANY(%s::uuid[])
            """, (chunk,))
            existing_ct.update(r[0] for r in cur.fetchall())

    print(f"  Already in CT: {len(existing_ct):,}")

    created = 0
    skipped = 0
    with_zip = 0

    for sid, oid in oid_map.items():
        if oid in existing_ct:
            skipped += 1
            continue

        # Check DOL address
        addr = dol_addr.get(sid, {})
        city = addr.get('city') or None
        state = addr.get('state') or None
        zip_code = addr.get('zip') or None
        ein = addr.get('ein') or None

        if zip_code:
            with_zip += 1

        if dry_run:
            created += 1
            continue

        try:
            cur.execute("""
                INSERT INTO outreach.company_target (
                    outreach_id, company_unique_id, source,
                    city, state, postal_code,
                    postal_code_source, postal_code_updated_at
                ) VALUES (
                    %s::uuid, %s, %s,
                    %s, %s, %s,
                    %s, %s
                )
                ON CONFLICT DO NOTHING
            """, (
                oid, sid, 'sc_onboard_2026',
                city, state, zip_code,
                'dol_name_match' if zip_code else None,
                datetime.now(timezone.utc) if zip_code else None,
            ))
            if cur.rowcount > 0:
                created += 1
        except Exception as e:
            print(f"    ERROR creating CT for {sid}: {e}")
            conn.rollback()

        if created % 200 == 0 and created > 0:
            conn.commit()

    # Also write EIN to outreach.outreach where available
    ein_updates = 0
    for sid, oid in oid_map.items():
        addr = dol_addr.get(sid, {})
        ein = addr.get('ein')
        if not ein:
            continue
        if dry_run:
            ein_updates += 1
            continue
        try:
            cur.execute("""
                UPDATE outreach.outreach
                SET ein = %s
                WHERE outreach_id = %s::uuid AND (ein IS NULL OR ein = '')
            """, (ein, oid))
            if cur.rowcount > 0:
                ein_updates += 1
        except Exception as e:
            conn.rollback()

    if not dry_run:
        conn.commit()

    print(f"  Created: {created:,}")
    print(f"  With DOL ZIP: {with_zip:,}")
    print(f"  Skipped (already exist): {skipped:,}")
    print(f"  EINs written to spine: {ein_updates:,}")
    return created


# ══════════════════════════════════════════════════════════════
# STEP 3: Create company_slots (CEO/CFO/HR)
# ══════════════════════════════════════════════════════════════

def step3_create_slots(conn, oid_map, dry_run=False):
    """Create CEO/CFO/HR slots for all onboarded companies."""
    print(f"\n{'=' * 60}")
    print("STEP 3: Create company_slots (CEO/CFO/HR)")
    print(f"{'=' * 60}")

    cur = conn.cursor()

    # Fetch existing slots
    oid_list = list(oid_map.values())
    existing_slots = set()  # (outreach_id, slot_type)
    if oid_list:
        for i in range(0, len(oid_list), 5000):
            chunk = oid_list[i:i+5000]
            cur.execute("""
                SELECT outreach_id::text, slot_type
                FROM people.company_slot
                WHERE outreach_id = ANY(%s::uuid[])
            """, (chunk,))
            existing_slots.update((r[0], r[1]) for r in cur.fetchall())

    print(f"  Existing slots: {len(existing_slots):,}")

    created = 0
    for sid, oid in oid_map.items():
        for slot_type in ['CEO', 'CFO', 'HR']:
            if (oid, slot_type) in existing_slots:
                continue

            if dry_run:
                created += 1
                continue

            try:
                new_slot_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO people.company_slot (
                        slot_id, outreach_id, company_unique_id, slot_type
                    ) VALUES (%s::uuid, %s::uuid, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (new_slot_id, oid, sid, slot_type))
                if cur.rowcount > 0:
                    created += 1
            except Exception as e:
                print(f"    ERROR slot {slot_type} for {oid}: {e}")
                conn.rollback()

        if created % 300 == 0 and created > 0 and not dry_run:
            conn.commit()

    if not dry_run:
        conn.commit()

    print(f"  Slots created: {created:,}")
    return created


# ══════════════════════════════════════════════════════════════
# STEP 4: Scrape CLAY domains for addresses
# ══════════════════════════════════════════════════════════════

# HTTP settings
REQUEST_TIMEOUT = 10.0
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}
SITEMAP_NS = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

# About Us / Contact page patterns
ABOUT_CONTACT_PATTERNS = [
    '/about', '/about-us', '/about-company', '/our-story',
    '/who-we-are', '/our-company', '/company/about',
    '/contact', '/contact-us', '/get-in-touch', '/locations',
]

# US state abbreviations + full names
STATE_ABBREVS = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
    'DC',
}


def strip_html(html):
    """Strip HTML tags, decode entities, normalize whitespace."""
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode common entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"')
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text


def extract_address_from_html(html):
    """
    Extract US address (city, state, ZIP) from HTML content.

    Returns dict with {city, state, zip, address1} or None.
    """
    if not html:
        return None

    # 1. Try JSON-LD (schema.org PostalAddress)
    result = _extract_jsonld_address(html)
    if result:
        return result

    # 2. Try regex on plain text
    text = strip_html(html)
    return _extract_regex_address(text)


def _extract_jsonld_address(html):
    """Extract address from schema.org JSON-LD."""
    try:
        for match in re.finditer(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html, re.DOTALL | re.IGNORECASE,
        ):
            try:
                data = json.loads(match.group(1))
            except (json.JSONDecodeError, ValueError):
                continue

            # Handle @graph array
            items = [data]
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict) and '@graph' in data:
                items = data['@graph']

            for item in items:
                if not isinstance(item, dict):
                    continue
                addr = item.get('address')
                if isinstance(addr, dict):
                    zip_code = str(addr.get('postalCode', '')).strip()[:5]
                    state = str(addr.get('addressRegion', '')).strip()
                    city = str(addr.get('addressLocality', '')).strip()
                    street = str(addr.get('streetAddress', '')).strip()
                    if zip_code and len(zip_code) == 5 and zip_code.isdigit() and state in STATE_ABBREVS:
                        return {
                            'address1': street,
                            'city': city,
                            'state': state,
                            'zip': zip_code,
                            'method': 'jsonld',
                        }
    except Exception:
        pass
    return None


def _extract_regex_address(text):
    """
    Extract US address from plain text using regex.
    Looks for patterns like: "123 Main St, City, SC 29XXX"
    """
    # Pattern: City, STATE ZIP (captures city, state abbrev, 5-digit zip)
    # Allow for multi-word city names
    pattern = r'([A-Z][a-zA-Z\s\.]{1,30}?)\s*,\s*([A-Z]{2})\s+(\d{5})(?:\s*[-–]\s*\d{4})?'
    matches = re.findall(pattern, text)

    for city, state, zip_code in matches:
        state = state.upper()
        if state not in STATE_ABBREVS:
            continue
        city = city.strip().rstrip(',').strip()
        # Skip garbage (too short, all caps noise, common false positives)
        if len(city) < 2 or city.upper() in ('PO BOX', 'P O BOX', 'BOX'):
            continue
        # Prefer SC addresses for SC companies, but accept any US address
        return {
            'address1': '',
            'city': city,
            'state': state,
            'zip': zip_code,
            'method': 'regex',
        }

    # Fallback: look for "Street Address\nCity, ST ZIP" multi-line pattern
    ml_pattern = r'(\d+\s+[A-Za-z\s\.]+(?:St|Street|Ave|Avenue|Blvd|Boulevard|Dr|Drive|Rd|Road|Way|Ln|Lane|Ct|Court|Pl|Place|Pkwy|Hwy|Suite|Ste|Cir)[.\s,]*)\s*([A-Z][a-zA-Z\s\.]{1,30}?)\s*,\s*([A-Z]{2})\s+(\d{5})'
    ml_matches = re.findall(ml_pattern, text)
    for street, city, state, zip_code in ml_matches:
        state = state.upper()
        if state not in STATE_ABBREVS:
            continue
        city = city.strip().rstrip(',').strip()
        if len(city) < 2:
            continue
        return {
            'address1': street.strip().rstrip(',').strip(),
            'city': city,
            'state': state,
            'zip': zip_code,
            'method': 'regex_street',
        }

    return None


def classify_url_about_contact(url):
    """Check if URL is an about or contact page."""
    try:
        path = urlparse(url).path.lower().rstrip('/')
    except Exception:
        return False
    if not path or path == '/':
        return False
    for pattern in ABOUT_CONTACT_PATTERNS:
        if path == pattern or path.startswith(pattern + '/'):
            return True
    return False


def is_same_domain(url, base_domain):
    try:
        url_domain = urlparse(url).netloc.lower().replace('www.', '')
        base_clean = base_domain.lower().replace('www.', '')
        return url_domain == base_clean or url_domain.endswith('.' + base_clean)
    except Exception:
        return False


async def _parse_sitemap_urls(client, sitemap_url, domain, depth=0):
    """Parse sitemap.xml, return list of page URLs."""
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
            sub_urls = []
            for el in root.findall('.//sm:sitemap/sm:loc', SITEMAP_NS):
                if el.text:
                    sub_urls.append(el.text.strip())
            for el in root.findall('.//sitemap/loc'):
                if el.text and el.text.strip() not in sub_urls:
                    sub_urls.append(el.text.strip())
            # Only fetch sitemaps likely to have pages (not products/posts)
            page_kw = ['page', 'main', 'site', 'about', 'contact', 'company', 'misc']
            filtered = [u for u in sub_urls
                        if any(k in u.lower().rsplit('/', 1)[-1] for k in page_kw)]
            if not filtered:
                filtered = sub_urls[:5]  # fallback: first 5
            for sub in filtered[:10]:
                child = await _parse_sitemap_urls(client, sub, domain, depth + 1)
                urls.extend(child)
        elif 'urlset' in tag:
            for el in root.findall('.//sm:url/sm:loc', SITEMAP_NS):
                if el.text and is_same_domain(el.text.strip(), domain):
                    urls.append(el.text.strip())
            for el in root.findall('.//url/loc'):
                if el.text and is_same_domain(el.text.strip(), domain):
                    urls.append(el.text.strip())
        return urls
    except Exception:
        return []


async def scrape_domain_for_address(client, domain, semaphore):
    """
    Hit a domain, find About Us / Contact page, extract address.
    Returns {city, state, zip, address1, source_url, method} or None.
    """
    async with semaphore:
        base_url = f"https://{domain}"

        # Step 1: Try sitemap for about/contact URLs
        about_urls = []
        try:
            sitemap_urls = await _parse_sitemap_urls(
                client, f"{base_url}/sitemap.xml", domain
            )
            for url in sitemap_urls:
                if classify_url_about_contact(url):
                    about_urls.append(url)
        except Exception:
            pass

        # Step 2: Try homepage links
        if not about_urls:
            try:
                resp = await client.get(base_url, timeout=REQUEST_TIMEOUT, follow_redirects=True)
                if resp.status_code == 200:
                    hrefs = re.findall(r'href=["\']([^"\']+)["\']', resp.text, re.IGNORECASE)
                    for href in hrefs:
                        if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                            continue
                        full_url = urljoin(base_url, href)
                        if is_same_domain(full_url, domain) and classify_url_about_contact(full_url):
                            parsed = urlparse(full_url)
                            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                            about_urls.append(clean_url)

                    # Also try extracting address from homepage itself (footer)
                    result = extract_address_from_html(resp.text)
                    if result:
                        result['source_url'] = str(resp.url)
                        result['method'] = 'homepage_' + result.get('method', 'regex')
                        return result
            except Exception:
                pass

        # Step 3: Probe common paths
        if not about_urls:
            for path in ['/about', '/about-us', '/contact', '/contact-us', '/locations']:
                try:
                    resp = await client.get(
                        f"{base_url}{path}", timeout=REQUEST_TIMEOUT, follow_redirects=True
                    )
                    if resp.status_code == 200:
                        final_path = urlparse(str(resp.url)).path.rstrip('/') or '/'
                        if final_path != '/':  # Not redirected to homepage
                            about_urls.append(str(resp.url))
                            break
                except Exception:
                    continue

        # Deduplicate
        seen = set()
        unique_urls = []
        for u in about_urls:
            normalized = urlparse(u).path.lower().rstrip('/')
            if normalized not in seen:
                seen.add(normalized)
                unique_urls.append(u)

        # Fetch each about/contact page and try to extract address
        for url in unique_urls[:4]:  # max 4 pages
            try:
                resp = await client.get(url, timeout=REQUEST_TIMEOUT, follow_redirects=True)
                if resp.status_code != 200:
                    continue
                result = extract_address_from_html(resp.text)
                if result:
                    result['source_url'] = url
                    return result
            except Exception:
                continue

        return None


async def step4_scrape_clay_addresses(conn, oid_map, workers=20, dry_run=False):
    """Scrape Clay SC domains for addresses."""
    print(f"\n{'=' * 60}")
    print("STEP 4: Scrape CLAY domains for addresses")
    print(f"{'=' * 60}")

    cur = conn.cursor()

    # Get Clay SC companies with domains that are in oid_map (just onboarded)
    # AND don't already have postal_code in CT
    cur.execute("""
        SELECT ci.company_unique_id::text, ci.company_name, ci.company_domain
        FROM cl.company_identity ci
        JOIN outreach.company_target ct
          ON ct.outreach_id = (
              SELECT o.outreach_id FROM outreach.outreach o
              WHERE o.sovereign_id = ci.company_unique_id
              LIMIT 1
          )
        WHERE ci.source_system = 'CLAY_SC_SS005'
          AND ci.company_domain IS NOT NULL
          AND ci.company_domain <> ''
          AND (ct.postal_code IS NULL OR ct.postal_code = '')
    """)
    companies = cur.fetchall()
    print(f"  Clay companies needing ZIP scrape: {len(companies):,}")

    if not companies:
        print("  Nothing to scrape.")
        return {}

    if dry_run:
        print("  [DRY RUN — skipping scraping]")
        return {}

    # Scrape
    semaphore = asyncio.Semaphore(workers)
    results = {}  # company_unique_id -> address dict
    processed = 0
    found = 0
    errors = 0

    async with httpx.AsyncClient(
        headers=HEADERS,
        follow_redirects=True,
        timeout=httpx.Timeout(connect=5.0, read=REQUEST_TIMEOUT,
                              write=REQUEST_TIMEOUT, pool=REQUEST_TIMEOUT),
        limits=httpx.Limits(max_connections=workers * 2,
                            max_keepalive_connections=workers),
        transport=httpx.AsyncHTTPTransport(retries=0),
    ) as client:

        chunk_size = 100
        total = len(companies)
        for chunk_start in range(0, total, chunk_size):
            chunk = companies[chunk_start:chunk_start + chunk_size]

            tasks = []
            for sid, name, domain in chunk:
                tasks.append(scrape_domain_for_address(client, domain, semaphore))

            task_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(task_results):
                sid = chunk[i][0]
                processed += 1
                if isinstance(result, Exception):
                    errors += 1
                elif result:
                    results[sid] = result
                    found += 1

            pct = 100 * processed / total
            print(
                f"  [{processed:,}/{total:,}] ({pct:.0f}%) "
                f"Found: {found:,} | Errors: {errors:,}",
                flush=True,
            )

    # Breakdown by method
    by_method = defaultdict(int)
    for addr in results.values():
        by_method[addr.get('method', 'unknown')] += 1
    print(f"\n  Total addresses found: {found:,}")
    for method, cnt in sorted(by_method.items(), key=lambda x: -x[1]):
        print(f"    {method}: {cnt:,}")

    # Breakdown by state
    by_state = defaultdict(int)
    for addr in results.values():
        by_state[addr.get('state', '?')] += 1
    print(f"\n  By state (top 10):")
    for st, cnt in sorted(by_state.items(), key=lambda x: -x[1])[:10]:
        print(f"    {st}: {cnt:,}")

    return results


# ══════════════════════════════════════════════════════════════
# STEP 5: Write scraped ZIPs to company_target
# ══════════════════════════════════════════════════════════════

def step5_write_zips(conn, oid_map, scraped_addresses, dry_run=False):
    """Write scraped addresses to company_target.postal_code."""
    print(f"\n{'=' * 60}")
    print("STEP 5: Write scraped ZIPs to company_target")
    print(f"{'=' * 60}")

    if not scraped_addresses:
        print("  No addresses to write.")
        return

    cur = conn.cursor()
    updated = 0
    errors = 0

    for sid, addr in scraped_addresses.items():
        oid = oid_map.get(sid)
        if not oid:
            continue

        zip_code = addr.get('zip', '')
        city = addr.get('city', '')
        state = addr.get('state', '')
        method = addr.get('method', 'scrape')

        if not zip_code:
            continue

        if dry_run:
            updated += 1
            continue

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
                f"web_scrape_{method}",
                datetime.now(timezone.utc),
                oid,
            ))
            if cur.rowcount > 0:
                updated += 1
        except Exception as e:
            print(f"    ERROR updating {oid}: {e}")
            conn.rollback()
            errors += 1

        if updated % 200 == 0 and updated > 0 and not dry_run:
            conn.commit()

    if not dry_run:
        conn.commit()

    print(f"  ZIPs written: {updated:,}")
    print(f"  Errors: {errors:,}")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Onboard SC companies + scrape ZIPs')
    parser.add_argument('--dry-run', action='store_true', help='Preview without DB writes')
    parser.add_argument('--step', type=int, help='Run only this step (1-5)')
    parser.add_argument('--workers', type=int, default=20, help='Scraping concurrency (default: 20)')
    args = parser.parse_args()

    dry_run = args.dry_run

    print("=" * 60)
    print("ONBOARD SC COMPANIES + SCRAPE ZIPS")
    print("=" * 60)
    print(f"Mode:    {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Workers: {args.workers}")
    print(f"Step:    {args.step or 'ALL'}")
    print(f"Started: {datetime.now().isoformat()}")

    conn = get_conn()

    # If running a specific step, we still need oid_map
    oid_map = {}

    if args.step is None or args.step == 1:
        oid_map = step1_mint_outreach_ids(conn, dry_run)
    else:
        # Load existing oid_map from DB
        cur = conn.cursor()
        cur.execute("""
            SELECT company_unique_id::text, outreach_id::text
            FROM cl.company_identity
            WHERE state_code = 'SC' AND outreach_id IS NOT NULL
        """)
        oid_map = {r[0]: r[1] for r in cur.fetchall()}
        print(f"\n  Loaded {len(oid_map):,} existing SC outreach_ids")

    if args.step is None or args.step == 2:
        step2_create_company_targets(conn, oid_map, dry_run)

    if args.step is None or args.step == 3:
        step3_create_slots(conn, oid_map, dry_run)

    scraped = {}
    if args.step is None or args.step == 4 or args.step == 45:
        scraped = asyncio.run(
            step4_scrape_clay_addresses(conn, oid_map, args.workers, dry_run)
        )

    if args.step is None or args.step == 5 or args.step == 45:
        if not scraped and args.step == 5:
            print("\n  Step 5 requires step 4 results. Run --step 45 for scrape+write.")
        else:
            # Reconnect — long scraping session kills the DB connection
            try:
                conn.close()
            except Exception:
                pass
            conn = get_conn()
            step5_write_zips(conn, oid_map, scraped, dry_run)

    # ── FINAL SUMMARY ──
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

    print(f"\n{'=' * 60}")
    print("FINAL STATUS: SC Companies")
    print(f"{'=' * 60}")
    print(f"  Total SC in CT:     {total_sc:,}")
    print(f"  With ZIP:           {with_zip:,}")
    print(f"  Without ZIP:        {total_sc - with_zip:,}")
    print(f"  ZIP coverage:       {100*with_zip/max(1,total_sc):.1f}%")
    print(f"{'=' * 60}")
    print(f"Completed: {datetime.now().isoformat()}")

    conn.close()


if __name__ == '__main__':
    main()
