#!/usr/bin/env python3
"""
Blog Executive Scraper v2
=========================
Uses EXISTING URLs from company.company_source_urls to extract executive names.
Feeds discovered names into People pipeline to fill empty slots.

Data Source: company.company_source_urls (97,124 URLs already discovered)
- leadership_page: 9,214 URLs (best for executives)
- team_page: 7,959 URLs
- about_page: 24,099 URLs

Execute with: doppler run -- python scripts/blog_executive_scraper.py

FREE tool - no API costs.
"""

import os
import re
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

# Barton ID sequence counters (will be initialized from DB)
NEXT_PERSON_SEQ = 120000  # For unique_id: 04.04.02.XX.XXXXX.XXX
NEXT_SLOT_SEQ = 120000    # For company_slot_unique_id: 04.04.05.XX.XXXXX.XXX

# Stats
STATS = {
    "companies_processed": 0,
    "urls_available": 0,
    "pages_scraped": 0,
    "pages_failed": 0,
    "executives_found": 0,
    "ceo_found": 0,
    "cfo_found": 0,
    "hr_found": 0,
    "slots_filled": 0,
    "blog_updated": 0,
}


def get_next_person_barton_id() -> str:
    """
    Generate a Barton ID in doctrine format for People Intelligence hub (people).
    Format: 04.04.02.99.{seq}.{last3}
    """
    global NEXT_PERSON_SEQ
    seq = NEXT_PERSON_SEQ
    NEXT_PERSON_SEQ += 1
    last3 = str(seq)[-3:].zfill(3)
    return f"04.04.02.99.{seq}.{last3}"


def get_next_slot_barton_id() -> str:
    """
    Generate a Barton ID in doctrine format for company_slot_unique_id.
    Format: 04.04.05.99.{seq}.{last3}
    """
    global NEXT_SLOT_SEQ
    seq = NEXT_SLOT_SEQ
    NEXT_SLOT_SEQ += 1
    last3 = str(seq)[-3:].zfill(3)
    return f"04.04.05.99.{seq}.{last3}"


def init_sequence_from_db(conn):
    """Initialize sequence counters from existing max in DB."""
    global NEXT_PERSON_SEQ, NEXT_SLOT_SEQ

    with conn.cursor() as cur:
        # Person sequence
        cur.execute("""
            SELECT COALESCE(MAX(CAST(SPLIT_PART(unique_id, '.', 5) AS INTEGER)), 0) + 1 as next_seq
            FROM people.people_master
            WHERE unique_id ~ '^04\\.04\\.02\\.[0-9]{2}\\.[0-9]{1,6}\\.[0-9]{3}$'
        """)
        result = cur.fetchone()
        if result and result[0]:
            NEXT_PERSON_SEQ = max(NEXT_PERSON_SEQ, result[0])

        # Slot sequence
        cur.execute("""
            SELECT COALESCE(MAX(CAST(SPLIT_PART(company_slot_unique_id, '.', 5) AS INTEGER)), 0) + 1 as next_seq
            FROM people.people_master
            WHERE company_slot_unique_id ~ '^04\\.04\\.05\\.[0-9]{2}\\.[0-9]{1,6}\\.[0-9]{3}$'
        """)
        result = cur.fetchone()
        if result and result[0]:
            NEXT_SLOT_SEQ = max(NEXT_SLOT_SEQ, result[0])

    log(f"Initialized person sequence at {NEXT_PERSON_SEQ}, slot sequence at {NEXT_SLOT_SEQ}")


@dataclass
class Executive:
    """Extracted executive info."""
    first_name: str
    last_name: str
    full_name: str
    title: str
    slot_type: str  # CEO, CFO, HR
    confidence: float
    source_url: str


def log(msg, level="INFO"):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


def connect_db():
    """Connect to Neon PostgreSQL."""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )


# =============================================================================
# Title Classification
# =============================================================================

CEO_TITLES = [
    r'\bCEO\b', r'\bChief Executive Officer\b', r'\bPresident\b',
    r'\bFounder\b', r'\bCo-Founder\b', r'\bOwner\b', r'\bPrincipal\b',
    r'\bManaging Director\b', r'\bGeneral Manager\b', r'\bChairman\b',
    r'\bExecutive Director\b'
]

CFO_TITLES = [
    r'\bCFO\b', r'\bChief Financial Officer\b', r'\bFinance Director\b',
    r'\bVP Finance\b', r'\bVice President.*Finance\b', r'\bController\b',
    r'\bTreasurer\b', r'\bFinancial Controller\b'
]

HR_TITLES = [
    r'\bCHRO\b', r'\bChief Human Resources\b', r'\bChief People Officer\b',
    r'\bHR Director\b', r'\bHuman Resources Director\b', r'\bVP HR\b',
    r'\bVice President.*Human Resources\b', r'\bHead of HR\b',
    r'\bHead of People\b', r'\bBenefits Director\b', r'\bBenefits Manager\b',
    r'\bHR Manager\b', r'\bPeople Operations\b'
]


def classify_title(title: str) -> Optional[str]:
    """Classify a title into CEO, CFO, or HR."""
    title_upper = title.upper()

    for pattern in CEO_TITLES:
        if re.search(pattern, title, re.IGNORECASE):
            return 'CEO'

    for pattern in CFO_TITLES:
        if re.search(pattern, title, re.IGNORECASE):
            return 'CFO'

    for pattern in HR_TITLES:
        if re.search(pattern, title, re.IGNORECASE):
            return 'HR'

    return None


# =============================================================================
# Name Extraction
# =============================================================================

def is_valid_name(name: str) -> bool:
    """Check if a string looks like a valid person name."""
    parts = name.split()
    if len(parts) < 2 or len(parts) > 4:
        return False

    # Each part should be a proper name (starts with capital, mostly letters)
    for part in parts:
        if len(part) < 2 or len(part) > 20:
            return False
        if not part[0].isupper():
            return False
        # Allow apostrophes (O'Brien) and hyphens (Smith-Jones)
        cleaned = part.replace("'", "").replace("-", "")
        if not cleaned.isalpha():
            return False

    # Reject common false positives
    lower_name = name.lower()
    false_positives = [
        'of the', 'at the', 'for the', 'and the', 'in the',
        'of pennsylvania', 'of advertising', 'of sales',
        'general counsel', 'board of', 'corporate controller',
        'director of', 'vp of', 'overseeing the', 'almost',
        'menu blog', 'digital specs'
    ]
    for fp in false_positives:
        if fp in lower_name:
            return False

    return True


def extract_executives_from_html(html: str, url: str) -> List[Executive]:
    """
    Extract executive names and titles from HTML content.

    Looks for patterns like:
    - "John Smith, CEO"
    - "John Smith - Chief Executive Officer"
    - "CEO: John Smith"
    """
    executives = []

    # Clean HTML - remove scripts, styles
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<[^>]+>', ' ', html)  # Remove tags
    html = re.sub(r'\s+', ' ', html)  # Normalize whitespace

    # Title patterns for all three slot types
    # CEO: CEO, President, Founder, Owner, Managing Director
    # CFO: CFO, Finance Director, VP Finance, Controller, Treasurer
    # HR: CHRO, HR Director, VP HR, Head of HR, Benefits Director

    title_pattern = (
        r'CEO|CFO|CHRO|'
        r'Chief\s+Executive\s+Officer|Chief\s+Financial\s+Officer|Chief\s+Human\s+Resources\s+Officer|'
        r'Chief\s+People\s+Officer|'
        r'President|Founder|Co-Founder|Owner|Managing\s+Director|'
        r'Finance\s+Director|VP\s+Finance|Vice\s+President\s+of\s+Finance|Controller|Treasurer|'
        r'HR\s+Director|Human\s+Resources\s+Director|VP\s+HR|Vice\s+President\s+of\s+HR|'
        r'Head\s+of\s+HR|Head\s+of\s+People|Benefits\s+Director|People\s+Operations\s+Director'
    )

    # Pattern 1: "Name, Title" or "Name - Title"
    pattern1 = rf'\b([A-Z][a-z]{{1,15}}(?:\s+[A-Z][a-z]{{1,15}}){{1,3}})\s*[,\-–—]\s*({title_pattern})\b'

    for match in re.finditer(pattern1, html, re.IGNORECASE):
        full_name = match.group(1).strip()
        title = match.group(2).strip()
        slot_type = classify_title(title)

        if slot_type and is_valid_name(full_name):
            parts = full_name.split()
            executives.append(Executive(
                first_name=parts[0],
                last_name=' '.join(parts[1:]),
                full_name=full_name,
                title=title,
                slot_type=slot_type,
                confidence=0.8,
                source_url=url
            ))

    # Pattern 2: "Title: Name" or "Title - Name"
    pattern2 = rf'\b({title_pattern})\s*[:–—-]\s*([A-Z][a-z]{{1,15}}(?:\s+[A-Z][a-z]{{1,15}}){{1,3}})\b'

    for match in re.finditer(pattern2, html, re.IGNORECASE):
        title = match.group(1).strip()
        full_name = match.group(2).strip()
        slot_type = classify_title(title)

        if slot_type and is_valid_name(full_name):
            parts = full_name.split()
            # Avoid duplicates
            if not any(e.full_name == full_name for e in executives):
                executives.append(Executive(
                    first_name=parts[0],
                    last_name=' '.join(parts[1:]),
                    full_name=full_name,
                    title=title,
                    slot_type=slot_type,
                    confidence=0.7,
                    source_url=url
                ))

    return executives


def scrape_known_urls(urls: List[str]) -> Tuple[List[Executive], str, str]:
    """
    Scrape KNOWN URLs from company_source_urls table.

    Returns: (executives_found, page_content, best_source_url)
    """
    if not urls:
        return ([], '', '')

    all_executives = []
    all_content = []
    best_url = urls[0] if urls else ''

    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        for url in urls[:5]:  # Limit to 5 URLs per company
            try:
                response = client.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })

                if response.status_code == 200:
                    html = response.text
                    executives = extract_executives_from_html(html, url)

                    if executives:
                        all_executives.extend(executives)
                        best_url = url  # Remember which URL found executives

                    # Store content summary (first 2000 chars of cleaned text)
                    clean_text = re.sub(r'<[^>]+>', ' ', html)
                    clean_text = re.sub(r'\s+', ' ', clean_text)[:2000]
                    all_content.append(clean_text)

            except Exception:
                continue

    # Deduplicate executives by name
    seen = set()
    unique_executives = []
    for exec in all_executives:
        if exec.full_name not in seen:
            seen.add(exec.full_name)
            unique_executives.append(exec)

    content_summary = ' | '.join(all_content)[:4000] if all_content else ''

    return (unique_executives, content_summary, best_url)


# =============================================================================
# Database Operations
# =============================================================================

def get_companies_with_empty_slots_and_urls(conn, limit: int = 1000) -> List[dict]:
    """
    Get companies that have ANY empty slots (CEO, CFO, HR) AND have discovered URLs.

    Join chain:
    - people.company_slot (UUID) → cl.company_identity (UUID)
    - cl.company_identity → company.company_master (via domain)
    - company.company_master → company.company_source_urls (doctrine ID)

    Returns doctrine_company_id for people_master (which requires Barton format)
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get companies with ANY empty slots (CEO, CFO, HR) that have discoverable URLs
        cur.execute("""
            WITH empty_slot_companies AS (
                -- Target companies with any empty CEO/CFO/HR slots
                SELECT DISTINCT
                    cs.outreach_id,
                    cs.company_unique_id as slot_company_id,
                    ci.normalized_domain as domain,
                    ci.company_name,
                    array_agg(DISTINCT cs.slot_type) FILTER (WHERE cs.is_filled = false) as empty_slots
                FROM people.company_slot cs
                JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
                JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
                WHERE cs.is_filled = false
                  AND cs.slot_type IN ('CEO', 'CFO', 'HR')
                  AND ci.normalized_domain IS NOT NULL
                  AND ci.normalized_domain <> ''
                GROUP BY cs.outreach_id, cs.company_unique_id, ci.normalized_domain, ci.company_name
                HAVING COUNT(*) FILTER (WHERE cs.is_filled = false) > 0
            ),
            domain_to_doctrine AS (
                -- Bridge cl.company_identity UUID to company.company_master doctrine ID via domain
                SELECT DISTINCT
                    esc.outreach_id,
                    esc.slot_company_id,
                    esc.domain,
                    esc.company_name,
                    esc.empty_slots,
                    cm.company_unique_id as doctrine_company_id
                FROM empty_slot_companies esc
                JOIN company.company_master cm
                    ON LOWER(esc.domain) = LOWER(
                        REPLACE(REPLACE(REPLACE(cm.website_url, 'https://', ''), 'http://', ''), 'www.', '')
                    )
            ),
            company_urls AS (
                SELECT
                    company_unique_id as doctrine_id,
                    array_agg(DISTINCT source_url) FILTER (WHERE source_type = 'leadership_page') as leadership_urls,
                    array_agg(DISTINCT source_url) FILTER (WHERE source_type = 'team_page') as team_urls,
                    array_agg(DISTINCT source_url) FILTER (WHERE source_type = 'about_page') as about_urls
                FROM company.company_source_urls
                WHERE source_type IN ('leadership_page', 'team_page', 'about_page')
                GROUP BY company_unique_id
            )
            SELECT
                dtd.outreach_id,
                dtd.slot_company_id,
                dtd.doctrine_company_id,
                dtd.domain,
                dtd.company_name,
                dtd.empty_slots,
                cu.leadership_urls,
                cu.team_urls,
                cu.about_urls
            FROM domain_to_doctrine dtd
            JOIN company_urls cu ON dtd.doctrine_company_id = cu.doctrine_id
            -- Skip companies already processed (have blog content)
            LEFT JOIN outreach.blog b ON dtd.outreach_id = b.outreach_id
            WHERE (cu.leadership_urls IS NOT NULL OR cu.team_urls IS NOT NULL OR cu.about_urls IS NOT NULL)
              AND (b.context_summary IS NULL OR b.context_summary = '')
            LIMIT %s
        """, (limit,))

        return cur.fetchall()


def update_blog_content(conn, outreach_id: str, content: str, source_url: str):
    """Update blog record with scraped content."""

    # Sanitize content - remove NUL characters
    clean_content = content.replace('\x00', '') if content else ''

    with conn.cursor() as cur:
        cur.execute("""
            UPDATE outreach.blog
            SET
                context_summary = %s,
                source_url = %s,
                context_timestamp = NOW()
            WHERE outreach_id = %s
        """, (clean_content[:4000], source_url, outreach_id))

        return cur.rowcount


def get_empty_slot(conn, outreach_id: str, slot_type: str) -> Optional[dict]:
    """Get the empty slot for a company and slot type."""

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT slot_id, company_unique_id
            FROM people.company_slot
            WHERE outreach_id = %s
              AND slot_type = %s
              AND is_filled = false
            LIMIT 1
        """, (outreach_id, slot_type))

        return cur.fetchone()


def create_people_and_fill_slot(conn, slot: dict, doctrine_company_id: str, exec: Executive) -> bool:
    """
    Create a people_master record and fill the slot in one transaction.

    Note: people_master uses Barton IDs for all ID fields, but company_slot uses UUIDs.
    We generate Barton IDs for people_master and link via person_unique_id in company_slot.

    Args:
        slot: The slot record with slot_id (UUID)
        doctrine_company_id: Barton format company ID for people_master
        exec: The executive to create
    """

    person_unique_id = get_next_person_barton_id()  # 04.04.02.XX format
    slot_barton_id = get_next_slot_barton_id()      # 04.04.05.XX format

    with conn.cursor() as cur:
        # Step 1: Create people_master record
        # All ID fields require Barton format
        cur.execute("""
            INSERT INTO people.people_master (
                unique_id, company_unique_id, company_slot_unique_id,
                first_name, last_name, title, source_system
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING unique_id
        """, (
            person_unique_id,       # 04.04.02.XX format
            doctrine_company_id,    # 04.04.01.XX format
            slot_barton_id,         # 04.04.05.XX format (not UUID slot_id!)
            exec.first_name,
            exec.last_name,
            exec.title,
            'blog_scrape'
        ))

        result = cur.fetchone()
        if not result:
            return False

        # Step 2: Fill the slot (company_slot uses UUID slot_id)
        cur.execute("""
            UPDATE people.company_slot
            SET
                person_unique_id = %s,
                is_filled = true,
                filled_at = NOW(),
                confidence_score = 0.7,
                source_system = 'blog_scrape'
            WHERE slot_id = %s
              AND is_filled = false
        """, (person_unique_id, slot['slot_id']))  # Link via person_unique_id

        return cur.rowcount > 0


# =============================================================================
# Main Processing
# =============================================================================

def process_company(conn, company: dict) -> dict:
    """Process a single company - scrape known URLs and fill slots."""

    domain = company['domain'] or 'unknown'
    outreach_id = company['outreach_id']
    slot_company_id = company['slot_company_id']  # UUID for slot lookup
    doctrine_company_id = company['doctrine_company_id']  # Barton format for people_master
    empty_slots = company['empty_slots'] or []

    # Prioritize: leadership > team > about (most likely to have executive names)
    leadership_urls = company.get('leadership_urls') or []
    team_urls = company.get('team_urls') or []
    about_urls = company.get('about_urls') or []

    # Combine URLs in priority order
    all_urls = leadership_urls + team_urls + about_urls
    STATS['urls_available'] += len(all_urls)

    result = {
        'domain': domain,
        'scraped': False,
        'executives_found': 0,
        'slots_filled': 0,
        'urls_tried': len(all_urls)
    }

    if not all_urls:
        return result

    # Scrape the known URLs
    try:
        executives, content, source_url = scrape_known_urls(all_urls)
        result['scraped'] = True
        STATS['pages_scraped'] += 1
    except Exception as e:
        STATS['pages_failed'] += 1
        return result

    # Update blog with content
    if content and source_url:
        updated = update_blog_content(conn, outreach_id, content, source_url)
        if updated:
            STATS['blog_updated'] += 1

    # Process found executives
    for exec in executives:
        STATS['executives_found'] += 1

        if exec.slot_type == 'CEO':
            STATS['ceo_found'] += 1
        elif exec.slot_type == 'CFO':
            STATS['cfo_found'] += 1
        elif exec.slot_type == 'HR':
            STATS['hr_found'] += 1

        # Only fill if slot is empty
        if exec.slot_type not in (empty_slots or []):
            continue

        # Get the empty slot first (need slot_id for people_master)
        slot = get_empty_slot(conn, outreach_id, exec.slot_type)

        if not slot:
            continue

        # Create people_master and fill slot
        try:
            filled = create_people_and_fill_slot(conn, slot, doctrine_company_id, exec)
            if filled:
                STATS['slots_filled'] += 1
                result['slots_filled'] += 1
        except Exception as e:
            log(f"Error filling slot: {e}", "ERROR")

    result['executives_found'] = len(executives)
    return result


def main():
    """Run the blog executive scraper using discovered URLs."""

    log("=" * 70)
    log("BLOG EXECUTIVE SCRAPER v2")
    log("=" * 70)
    log("Using EXISTING URLs from company.company_source_urls")
    log("Source: leadership_page, team_page, about_page URLs")
    log("Cost: $0.00 (FREE)")
    log("")

    # Connect
    log("Connecting to database...")
    try:
        conn = connect_db()
        conn.autocommit = False
        log("Connected")
    except Exception as e:
        log(f"Connection failed: {e}", "ERROR")
        sys.exit(1)

    try:
        # Initialize sequence counter
        init_sequence_from_db(conn)

        # Get companies with empty slots AND discovered URLs
        log("-" * 70)
        log("Finding companies with empty slots AND discovered URLs...")
        companies = get_companies_with_empty_slots_and_urls(conn, limit=20000)
        log(f"Found {len(companies):,} companies with URLs to process")

        if not companies:
            log("No companies with empty slots and discovered URLs found")
            return 0

        # Process companies in parallel batches
        log("-" * 70)
        log("Scraping known URLs (parallel batches)...")

        batch_size = 10  # Process 10 at a time
        for batch_start in range(0, len(companies), batch_size):
            batch = companies[batch_start:batch_start + batch_size]

            # Process batch in parallel
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(process_company, conn, c): c for c in batch}
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        STATS['companies_processed'] += 1
                    except Exception as e:
                        log(f"Error processing company: {e}", "ERROR")

            # Commit after each batch
            conn.commit()

            processed = min(batch_start + batch_size, len(companies))
            if processed % 50 == 0 or processed == len(companies):
                log(f"  Processed {processed}/{len(companies)} - Found {STATS['executives_found']} executives, filled {STATS['slots_filled']} slots")

        # Generate report
        log("-" * 70)
        log("RESULTS")
        log("-" * 70)
        log(f"Companies processed: {STATS['companies_processed']:,}")
        log(f"URLs available: {STATS['urls_available']:,}")
        log(f"Pages scraped: {STATS['pages_scraped']:,}")
        log(f"Pages failed: {STATS['pages_failed']:,}")
        log(f"Blog records updated: {STATS['blog_updated']:,}")
        log(f"Executives found: {STATS['executives_found']:,}")
        log(f"  - CEO: {STATS['ceo_found']:,}")
        log(f"  - CFO: {STATS['cfo_found']:,}")
        log(f"  - HR: {STATS['hr_found']:,}")
        log(f"Slots filled: {STATS['slots_filled']:,}")
        log(f"Cost: $0.00")

        # Write report
        report = f"""# Blog Executive Scraper v2 Report

**Execution Date**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC
**Cost**: $0.00 (FREE)
**Data Source**: company.company_source_urls (97,124 URLs)

## Results

| Metric | Count |
|--------|------:|
| Companies processed | {STATS['companies_processed']:,} |
| URLs available | {STATS['urls_available']:,} |
| Pages scraped | {STATS['pages_scraped']:,} |
| Blog records updated | {STATS['blog_updated']:,} |
| Executives found | {STATS['executives_found']:,} |
| - CEO | {STATS['ceo_found']:,} |
| - CFO | {STATS['cfo_found']:,} |
| - HR | {STATS['hr_found']:,} |
| **Slots filled** | **{STATS['slots_filled']:,}** |

## Method

1. Queried company.company_source_urls for discovered leadership/team/about URLs
2. Joined with companies having empty slots in people.company_slot
3. Scraped known URLs (not guessing paths)
4. Extracted "Name, Title" patterns from HTML
5. Classified titles into CEO/CFO/HR
6. Created people_master records
7. Filled empty company_slot records

## URL Priority

1. leadership_page (9,214 available) - Most likely to have executive bios
2. team_page (7,959 available) - Staff listings with titles
3. about_page (24,099 available) - Company overview, sometimes leadership

**Generated**: {datetime.now(timezone.utc).isoformat()}Z
"""

        report_path = Path(__file__).parent.parent / "BLOG_SCRAPER_REPORT.md"
        report_path.write_text(report, encoding='utf-8')
        log(f"Report written to: {report_path}")

    except Exception as e:
        conn.rollback()
        log(f"Error: {e}", "ERROR")
        raise
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
