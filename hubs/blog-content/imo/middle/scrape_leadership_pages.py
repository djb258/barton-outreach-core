#!/usr/bin/env python3
"""
Leadership/Team Page Scraper — Extract Executive Names for Slot Filling
========================================================================
Scrapes leadership_page and team_page URLs from outreach.source_urls,
extracts executive names, titles, LinkedIn URLs, and emails,
then maps them to CEO/CFO/HR slots.

SNAP_ON_TOOLBOX compliant:
- Tier 0: Free (httpx only, no paid APIs)
- Uses httpx (not requests — requests is BANNED)
- BeautifulSoup for HTML parsing (no LLM)

DOCTRINE compliant:
- Sources URLs from outreach.source_urls (outreach_id FK)
- Scopes by coverage_id or all
- Exports CSV with outreach_id for downstream enrichment
- Can optionally fill slots directly (--fill flag)

Usage:
    # Dry run — scrape 20 pages, preview results
    doppler run -- python hubs/blog-content/imo/middle/scrape_leadership_pages.py \\
        --coverage-id 0456811b-9c77-48c5-9bc3-99f188066272 --dry-run --limit 20

    # Full scrape — export CSV only
    doppler run -- python hubs/blog-content/imo/middle/scrape_leadership_pages.py \\
        --coverage-id 0456811b-9c77-48c5-9bc3-99f188066272

    # Full scrape — export CSV + fill unfilled slots
    doppler run -- python hubs/blog-content/imo/middle/scrape_leadership_pages.py \\
        --coverage-id 0456811b-9c77-48c5-9bc3-99f188066272 --fill
"""

import os
import re
import sys
import io
import csv
import asyncio
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Tuple, Set

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import httpx
import psycopg2
from psycopg2.extras import execute_values
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# TITLE → SLOT TYPE MAPPING
# ═══════════════════════════════════════════════════════════════

CEO_KEYWORDS = [
    'chief executive officer', 'ceo', 'president', 'owner',
    'founder', 'co-founder', 'managing partner', 'principal',
    'managing director', 'general manager', 'managing member',
    'executive director', 'proprietor', 'chairman', 'chairwoman',
    'chief operating officer', 'chief operations officer', 'coo',
    'vice president', 'vp of', 'vp operations', 'vp sales', 'vp global',
    'director of operations', 'operations director',
    'chief strategy officer', 'cso',
    'chief technology officer', 'cto',
    'chief information officer', 'cio',
    'chief marketing officer', 'cmo',
    'chief sales', 'chief banking', 'chief experience',
    'chief investment officer', 'chief risk officer',
    'chief governance', 'chief transformation', 'chief process',
    'chief trade', 'chief engineer',
    'partner', 'evp', 'svp', 'head of',
]

CFO_KEYWORDS = [
    'chief financial officer', 'cfo', 'controller', 'comptroller',
    'vp finance', 'vice president finance', 'vp of finance',
    'director of finance', 'finance director', 'treasurer',
    'finance manager', 'chief accounting officer',
    'senior accountant', 'accounting manager',
    'director of accounting', 'director, accounting',
    'accounting director',
]

HR_KEYWORDS = [
    'human resources', 'hr director', 'hr manager', 'hr ',
    'chief people officer', 'cpo', 'chief human resources',
    'vp hr', 'vp human resources', 'vice president hr',
    'director of people', 'people operations', 'talent director',
    'head of people', 'head of hr', 'benefits manager',
    'benefits director', 'benefits administrator',
    'director of human resources', 'human resource',
    'director of staff', 'recruitment director',
]

# Titles that are NOT executive roles — skip these
# NOTE: These are checked AFTER slot keyword matching, so a
# "Bookkeeper and Finance Manager" will still match CFO.
SKIP_TITLES = [
    'intern', 'assistant', 'receptionist', 'coordinator',
    'specialist', 'technician', 'nurse', 'dental hygienist',
    'hygienist', 'paralegal', 'legal assistant', 'clerk',
    'bookkeeper', 'administrative', 'secretary',
]


def _kw_match(keyword: str, text: str) -> bool:
    """Match keyword in text. Uses word boundaries for short acronyms
    (<=4 chars) to prevent 'cto' matching inside 'director'."""
    kw = keyword.strip()
    if len(kw) <= 4:
        return bool(re.search(r'\b' + re.escape(kw) + r'\b', text))
    return keyword in text


def classify_title(title: str) -> Optional[str]:
    """Map a job title to CEO/CFO/HR slot type, or None."""
    t = title.lower().strip()
    if not t or len(t) < 2:
        return None

    # Check slot keywords FIRST (before skip check)
    # This ensures "Bookkeeper and Finance Manager" matches CFO
    # even though "bookkeeper" is in SKIP_TITLES.
    for kw in CFO_KEYWORDS:
        if _kw_match(kw, t):
            return 'CFO'
    for kw in HR_KEYWORDS:
        if _kw_match(kw, t):
            return 'HR'
    for kw in CEO_KEYWORDS:
        if _kw_match(kw, t):
            return 'CEO'

    # Skip non-executive titles only if no slot matched
    for skip in SKIP_TITLES:
        if skip in t:
            return None

    return None


# ═══════════════════════════════════════════════════════════════
# NAME PARSING
# ═══════════════════════════════════════════════════════════════

def parse_name(full_name: str) -> Tuple[str, str]:
    """Split a full name into first_name, last_name."""
    # Strip trailing pipe/slash and anything after (e.g. "Salta|President" → "Salta")
    cleaned = re.split(r'[|/]', full_name)[0].strip()
    parts = cleaned.split()
    if not parts:
        return '', ''

    # Remove common prefixes/suffixes
    prefixes = {'dr', 'dr.', 'mr', 'mr.', 'mrs', 'mrs.', 'ms', 'ms.', 'rev', 'rev.'}
    suffixes = {
        'jr', 'jr.', 'sr', 'sr.', 'ii', 'iii', 'iv', 'esq', 'esq.',
        'md', 'm.d.', 'dds', 'd.d.s.', 'phd', 'ph.d.', 'cpa', 'c.p.a.',
        'dmd', 'd.m.d.', 'pa', 'p.a.', 'pllc', 'llc', 'inc', 'rn', 'arnp',
    }

    if parts and parts[0].lower().rstrip('.') in {p.rstrip('.') for p in prefixes}:
        parts = parts[1:]
    while parts and parts[-1].lower().rstrip('.,') in {s.rstrip('.') for s in suffixes}:
        parts = parts[:-1]

    if len(parts) == 0:
        return '', ''
    elif len(parts) == 1:
        return parts[0].title(), ''
    else:
        return parts[0].title(), ' '.join(p.title() for p in parts[1:])


def is_plausible_name(text: str) -> bool:
    """Check if text looks like a person's name (not a company or junk)."""
    t = text.strip()
    if not t or len(t) < 3 or len(t) > 50:
        return False
    words = t.split()
    # Must have 2-5 word-parts (real names)
    if len(words) < 2 or len(words) > 5:
        return False
    # No digits
    if any(c.isdigit() for c in t):
        return False
    # Each word should start with uppercase (proper name)
    if not all(w[0].isupper() for w in words if len(w) > 1 and w[0].isalpha()):
        return False

    tl = t.lower()

    # No obvious non-name patterns
    bad_exact = ['@', 'http', 'www.', '.com', '.org', '©', 'copyright',
                 'all rights', 'privacy', 'cookie', 'terms', 'menu',
                 'home', 'contact us', 'learn more', 'read more', 'view all',
                 'click', 'submit', 'search', 'subscribe', 'download',
                 'featured', 'related', 'upcoming', 'previous', 'next']
    if any(b in tl for b in bad_exact):
        return False

    # Block location-like patterns (X Beach, X Office, X County)
    location_words = {
        'office', 'beach', 'county', 'city', 'town', 'village',
        'island', 'river', 'creek', 'mountain', 'valley', 'lake',
        'heights', 'springs', 'falls', 'park', 'plaza', 'center',
        'north', 'south', 'east', 'west', 'avenue', 'street', 'road',
    }
    if words[-1].lower() in location_words:
        return False

    # Block section/category patterns
    section_words = {
        'team', 'staff', 'events', 'services', 'products', 'news',
        'blog', 'resources', 'careers', 'contact', 'about', 'company',
        'corporation', 'development', 'management', 'holdings', 'group',
        'leadership', 'executive', 'department', 'division', 'info',
        'infoorrequest', 'overview', 'request', 'schedule', 'gallery',
    }
    if words[-1].lower() in section_words:
        return False
    if words[0].lower() in {'from', 'the', 'our', 'your', 'all', 'view', 'meet',
                               'get', 'join', 'sign', 'find', 'see', 'read',
                               'call', 'send', 'new', 'more', 'best', 'top'}:
        return False
    # Block common non-name two-word combos
    two_word_block = {
        'social links', 'social media', 'quick links', 'useful links',
        'newsletter sign-up', 'sign up', 'phone number', 'email address',
        'physical therapist', 'physical therapy', 'dental hygienist',
        'account manager', 'project manager', 'office manager',
        'licensed practical', 'registered nurse',
    }
    if tl in two_word_block:
        return False

    # Block first names that are really titles/roles
    title_first_words = {
        'chief', 'director', 'manager', 'officer', 'president',
        'vice', 'executive', 'assistant', 'associate', 'senior',
        'junior', 'head', 'lead', 'service', 'customer', 'company',
        'general', 'regional', 'national', 'corporate', 'titlegeneral',
    }
    if words[0].lower() in title_first_words:
        return False

    # Should have mostly alpha chars
    alpha_ratio = sum(1 for c in t if c.isalpha()) / max(len(t), 1)
    if alpha_ratio < 0.7:
        return False

    # Each name word should be 2-15 chars (not "A" or super long junk)
    for w in words:
        clean = w.rstrip('.,;:')
        if len(clean) < 2 or len(clean) > 15:
            return False

    return True


def name_from_linkedin_slug(url: str) -> Tuple[str, str]:
    """Extract first/last from LinkedIn slug like /in/john-smith-a1b2c3d4/."""
    slug = url.rstrip('/').split('/')[-1]
    parts = slug.split('-')
    # Remove trailing hex hash
    if parts and len(parts[-1]) >= 6 and all(c in '0123456789abcdef' for c in parts[-1]):
        parts = parts[:-1]
    if len(parts) >= 2:
        return parts[0].title(), ' '.join(p.title() for p in parts[1:])
    elif len(parts) == 1:
        return parts[0].title(), ''
    return '', ''


# ═══════════════════════════════════════════════════════════════
# HTML SCRAPING ENGINE
# ═══════════════════════════════════════════════════════════════

def extract_people_from_html(html: str, page_url: str) -> List[Dict]:
    """
    Parse HTML and extract people with name, title, LinkedIn, email.

    Strategy (ordered by reliability):
    1. Find all LinkedIn /in/ links — highest confidence signal
    2. Find structured team member cards (common CSS class patterns)
    3. Find name/title pairs in headings + adjacent text
    4. Extract emails from mailto: links
    """
    soup = BeautifulSoup(html, 'lxml')
    people = []
    seen_names = set()

    # Remove script/style/nav/footer noise
    for tag in soup.find_all(['script', 'style', 'noscript', 'iframe']):
        tag.decompose()

    # ─── PASS 1: LinkedIn URLs ───
    linkedin_urls = {}
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'linkedin.com/in/' in href:
            # Clean the URL
            match = re.search(r'(https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+)', href)
            if match:
                li_url = match.group(1)
                # Try to find name near this link
                # Check the link text itself
                link_text = a.get_text(strip=True)
                # Check parent elements for name
                name_text = ''
                if link_text and is_plausible_name(link_text):
                    name_text = link_text
                else:
                    # Look at siblings and parent for name
                    parent = a.parent
                    for _ in range(3):  # Walk up 3 levels
                        if parent is None:
                            break
                        for child in parent.children:
                            if hasattr(child, 'get_text'):
                                ct = child.get_text(strip=True)
                                if ct and ct != link_text and is_plausible_name(ct):
                                    name_text = ct
                                    break
                        if name_text:
                            break
                        parent = parent.parent

                if not name_text:
                    # Fall back to slug
                    first, last = name_from_linkedin_slug(li_url)
                    name_text = f"{first} {last}".strip()

                linkedin_urls[li_url.lower()] = name_text

    # ─── PASS 2: Structured team member elements ───
    # Common patterns: divs/sections with class containing team/member/person/staff
    member_classes = re.compile(
        r'team[-_]?member|staff[-_]?member|person[-_]?card|'
        r'member[-_]?card|team[-_]?card|people[-_]?card|'
        r'executive|leadership[-_]?card|bio[-_]?card|'
        r'team-block|staff-block|member-block',
        re.I
    )

    member_elements = soup.find_all(
        ['div', 'section', 'article', 'li'],
        class_=member_classes
    )

    for elem in member_elements:
        person = _extract_person_from_element(elem)
        if person and person.get('name'):
            name_key = person['name'].lower()
            if name_key not in seen_names:
                seen_names.add(name_key)
                people.append(person)

    # ─── PASS 3: Heading + subtitle patterns ───
    # Look for h2/h3/h4 followed by a paragraph or span with a title
    for heading_tag in ['h2', 'h3', 'h4']:
        for heading in soup.find_all(heading_tag):
            name_text = heading.get_text(strip=True)
            if not is_plausible_name(name_text):
                continue

            name_key = name_text.lower()
            if name_key in seen_names:
                continue

            # Look for title in next sibling or parent's children
            title_text = ''
            linkedin = ''
            email = ''

            # Check next siblings
            for sib in heading.find_next_siblings():
                if sib.name in ['h1', 'h2', 'h3', 'h4']:
                    break  # Hit next person
                sib_text = sib.get_text(strip=True)
                if sib_text and len(sib_text) < 200:
                    cleaned = _clean_title(sib_text, name_text)
                    if cleaned and not is_plausible_name(cleaned):
                        if classify_title(cleaned) is not None or _looks_like_title(cleaned):
                            title_text = cleaned
                            # Also grab email from this text
                            if not email:
                                email = _extract_email_from_text(sib_text)
                            break

                # Check for LinkedIn link in this sibling
                for a in sib.find_all('a', href=True):
                    if 'linkedin.com/in/' in a['href']:
                        match = re.search(r'(https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+)', a['href'])
                        if match:
                            linkedin = match.group(1)
                    if 'mailto:' in a['href']:
                        email = a['href'].replace('mailto:', '').split('?')[0].strip()

            # Also check the heading's parent container
            if not title_text:
                parent = heading.parent
                if parent:
                    for child in parent.find_all(['p', 'span', 'div', 'small']):
                        ct = child.get_text(strip=True)
                        cleaned = _clean_title(ct, name_text)
                        if cleaned and cleaned != name_text and len(cleaned) < 100:
                            if classify_title(cleaned) is not None or _looks_like_title(cleaned):
                                title_text = cleaned
                                if not email:
                                    email = _extract_email_from_text(ct)
                                break

            # Check for LinkedIn in heading itself or parent
            if not linkedin:
                container = heading.parent or heading
                for a in container.find_all('a', href=True):
                    if 'linkedin.com/in/' in a['href']:
                        match = re.search(r'(https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+)', a['href'])
                        if match:
                            linkedin = match.group(1)
                            break

            if not email:
                container = heading.parent or heading
                for a in container.find_all('a', href=True):
                    if 'mailto:' in a['href']:
                        email = a['href'].replace('mailto:', '').split('?')[0].strip()
                        break

            first, last = parse_name(name_text)
            if first:
                seen_names.add(name_key)
                people.append({
                    'name': name_text,
                    'first_name': first,
                    'last_name': last,
                    'title': title_text,
                    'slot_type': classify_title(title_text) if title_text else None,
                    'linkedin_url': linkedin,
                    'email': email,
                    'source': 'heading_pattern',
                })

    # ─── PASS 4: Merge LinkedIn URLs into found people ───
    for li_url, li_name in linkedin_urls.items():
        # Check if we already have this person
        found = False
        for p in people:
            if p.get('linkedin_url', '').lower() == li_url:
                found = True
                break
            # Name match
            if li_name and p.get('name', '').lower() == li_name.lower():
                p['linkedin_url'] = li_url if li_url.startswith('http') else f"https://{li_url}"
                found = True
                break

        if not found and li_name and is_plausible_name(li_name):
            first, last = parse_name(li_name)
            if first:
                people.append({
                    'name': li_name,
                    'first_name': first,
                    'last_name': last,
                    'title': '',
                    'slot_type': None,
                    'linkedin_url': li_url if li_url.startswith('http') else f"https://{li_url}",
                    'email': '',
                    'source': 'linkedin_link',
                })

    # ─── PASS 5: Extract emails from mailto links ───
    for a in soup.find_all('a', href=True):
        if 'mailto:' in a['href']:
            email = a['href'].replace('mailto:', '').split('?')[0].strip()
            if '@' in email and '.' in email:
                # Try to match to a person we already found
                link_text = a.get_text(strip=True)
                matched = False
                for p in people:
                    if p.get('email'):
                        continue
                    # Name near the email?
                    if link_text and link_text.lower() == p.get('name', '').lower():
                        p['email'] = email
                        matched = True
                        break
                # If not matched, check parent element
                if not matched:
                    parent = a.parent
                    for _ in range(2):
                        if parent is None:
                            break
                        parent_text = parent.get_text(strip=True)
                        for p in people:
                            if p.get('email'):
                                continue
                            if p.get('name', '') and p['name'] in parent_text:
                                p['email'] = email
                                break
                        parent = parent.parent

    return people


def _clean_title(title_text: str, name_text: str) -> str:
    """Strip person's name from the beginning of title text and clean up."""
    t = title_text.strip()
    if not t:
        return ''
    # Strip name prefix (common in concatenated HTML text nodes)
    # e.g., "Austin AvuruEXECUTIVE CHAIRMAN" -> "EXECUTIVE CHAIRMAN"
    if name_text and t.startswith(name_text):
        t = t[len(name_text):].strip()
    # Also try first+last separately
    parts = name_text.split() if name_text else []
    if len(parts) >= 2:
        first_last = parts[0] + ' ' + parts[-1]
        if t.lower().startswith(first_last.lower()):
            t = t[len(first_last):].strip()
    # Strip phone numbers
    t = re.sub(r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', '', t).strip()
    # Strip email addresses
    t = re.sub(r'[\w.+-]+@[\w-]+\.[\w.-]+', '', t).strip()
    # Strip unicode zero-width chars
    t = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', t).strip()
    # Truncate at newline (first line is usually the title)
    if '\n' in t:
        t = t.split('\n')[0].strip()
    return t


def _extract_email_from_text(text: str) -> str:
    """Extract email address from a block of text."""
    match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
    return match.group(0) if match else ''


def _extract_person_from_element(elem) -> Optional[Dict]:
    """Extract person data from a team member card element."""
    name_text = ''
    title_text = ''
    linkedin = ''
    email = ''

    # Name is usually in a heading
    for tag in ['h2', 'h3', 'h4', 'h5', 'strong']:
        el = elem.find(tag)
        if el:
            candidate = el.get_text(strip=True)
            if is_plausible_name(candidate):
                name_text = candidate
                break

    if not name_text:
        # Try class-based name detection
        name_el = elem.find(class_=re.compile(r'name|title-name|member-name|person-name', re.I))
        if name_el:
            candidate = name_el.get_text(strip=True)
            if is_plausible_name(candidate):
                name_text = candidate

    if not name_text:
        return None

    # Title is usually in a p/span/div after the name
    raw_title = ''
    for tag in ['p', 'span', 'div', 'small']:
        for el in elem.find_all(tag):
            ct = el.get_text(strip=True)
            if ct and ct != name_text and len(ct) < 200:
                cleaned = _clean_title(ct, name_text)
                if cleaned and (classify_title(cleaned) is not None or _looks_like_title(cleaned)):
                    raw_title = ct
                    title_text = cleaned
                    break
        if title_text:
            break

    # Also check class-based title
    if not title_text:
        title_el = elem.find(class_=re.compile(r'position|job-title|role|member-title|person-title', re.I))
        if title_el:
            ct = title_el.get_text(strip=True)
            title_text = _clean_title(ct, name_text)

    # LinkedIn
    for a in elem.find_all('a', href=True):
        if 'linkedin.com/in/' in a['href']:
            match = re.search(r'(https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+)', a['href'])
            if match:
                linkedin = match.group(1)
        if 'mailto:' in a['href']:
            email = a['href'].replace('mailto:', '').split('?')[0].strip()

    # Extract email from the full card text if not found via mailto
    if not email:
        full_text = elem.get_text()
        email = _extract_email_from_text(full_text)

    first, last = parse_name(name_text)
    return {
        'name': name_text,
        'first_name': first,
        'last_name': last,
        'title': title_text,
        'slot_type': classify_title(title_text) if title_text else None,
        'linkedin_url': linkedin,
        'email': email,
        'source': 'structured_card',
    }


def _looks_like_title(text: str) -> bool:
    """Heuristic: does this text look like a job title?"""
    t = text.lower().strip()
    if len(t) < 3 or len(t) > 80:
        return False

    title_words = [
        'director', 'manager', 'officer', 'president', 'vice president',
        'vp', 'chief', 'head of', 'partner', 'founder', 'owner',
        'ceo', 'cfo', 'coo', 'cto', 'cmo', 'chro', 'cpo',
        'accountant', 'attorney', 'lawyer', 'counsel',
        'administrator', 'supervisor', 'foreman', 'superintendent',
        'dentist', 'physician', 'surgeon', 'doctor',
        'broker', 'agent', 'advisor', 'consultant',
    ]
    return any(tw in t for tw in title_words)


# ═══════════════════════════════════════════════════════════════
# ASYNC SCRAPER
# ═══════════════════════════════════════════════════════════════

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


async def scrape_one_page(
    client: httpx.AsyncClient,
    outreach_id: str,
    company_name: str,
    domain: str,
    source_type: str,
    url: str,
    semaphore: asyncio.Semaphore,
) -> List[Dict]:
    """Scrape a single leadership/team page and return extracted people."""
    async with semaphore:
        try:
            resp = await client.get(url, follow_redirects=True, timeout=15.0)
            if resp.status_code != 200:
                return []

            content_type = resp.headers.get('content-type', '')
            if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                return []

            html = resp.text
            if len(html) < 200:
                return []

            people = extract_people_from_html(html, url)

            # Attach company context to each person
            for p in people:
                p['outreach_id'] = outreach_id
                p['company_name'] = company_name
                p['domain'] = domain
                p['source_url'] = url
                p['source_type'] = source_type

            return people

        except Exception as e:
            logger.debug(f"Error scraping {url}: {e}")
            return []


# ═══════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════

def get_conn():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        dbname=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require',
    )


def load_urls(conn, coverage_id: str = None, limit: int = None) -> List[Dict]:
    """Load leadership/team URLs from outreach.source_urls."""
    cur = conn.cursor()

    if coverage_id:
        sql = """
            WITH market_zips AS (
                SELECT zip, state_id
                FROM coverage.v_service_agent_coverage_zips
                WHERE coverage_id = %s
            )
            SELECT
                su.outreach_id::text,
                cl.company_name,
                o.domain,
                su.source_type,
                su.source_url
            FROM outreach.source_urls su
            JOIN outreach.outreach o ON o.outreach_id = su.outreach_id
            JOIN cl.company_identity cl ON cl.outreach_id = su.outreach_id
            JOIN outreach.company_target ct ON ct.outreach_id = su.outreach_id
            JOIN (SELECT DISTINCT zip FROM coverage.v_service_agent_coverage_zips WHERE coverage_id = %s) mz
                ON ct.postal_code = mz.zip
            WHERE su.source_type IN ('leadership_page', 'team_page')
            ORDER BY cl.company_name
        """
        params = [coverage_id, coverage_id]
    else:
        sql = """
            SELECT
                su.outreach_id::text,
                cl.company_name,
                o.domain,
                su.source_type,
                su.source_url
            FROM outreach.source_urls su
            JOIN outreach.outreach o ON o.outreach_id = su.outreach_id
            JOIN cl.company_identity cl ON cl.outreach_id = su.outreach_id
            WHERE su.source_type IN ('leadership_page', 'team_page')
            ORDER BY cl.company_name
        """
        params = []

    if limit:
        sql += f" LIMIT {int(limit)}"

    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()

    return [
        {
            'outreach_id': r[0],
            'company_name': r[1],
            'domain': r[2],
            'source_type': r[3],
            'source_url': r[4],
        }
        for r in rows
    ]


def load_filled_slots(conn, outreach_ids: List[str]) -> Set[Tuple[str, str]]:
    """Return set of (outreach_id, slot_type) that are already filled."""
    if not outreach_ids:
        return set()
    cur = conn.cursor()
    filled = set()
    for i in range(0, len(outreach_ids), 5000):
        chunk = outreach_ids[i:i+5000]
        cur.execute("""
            SELECT outreach_id::text, slot_type
            FROM people.company_slot
            WHERE outreach_id = ANY(%s::uuid[])
              AND is_filled = TRUE
        """, (chunk,))
        filled.update((r[0], r[1]) for r in cur.fetchall())
    cur.close()
    return filled


def load_slot_map(conn, outreach_ids: List[str]) -> Dict:
    """Load slot_id + company_unique_id for unfilled slots."""
    if not outreach_ids:
        return {}
    cur = conn.cursor()
    slot_map = {}
    for i in range(0, len(outreach_ids), 5000):
        chunk = outreach_ids[i:i+5000]
        cur.execute("""
            SELECT outreach_id::text, slot_type, slot_id::text, company_unique_id
            FROM people.company_slot
            WHERE outreach_id = ANY(%s::uuid[])
              AND is_filled = FALSE
        """, (chunk,))
        for oid, st, sid, cuid in cur.fetchall():
            slot_map[(oid, st)] = (sid, cuid)
    cur.close()
    return slot_map


def fill_slots(conn, contacts: List[Dict], slot_map: Dict, dry_run: bool = False) -> Dict:
    """Fill people slots with scraped contacts."""
    cur = conn.cursor()

    # Get next Barton ID sequence
    year = datetime.now().year % 100
    BARTON_PREFIX = "04.04.02"
    cur.execute("""
        SELECT MAX(CAST(SPLIT_PART(unique_id, '.', 5) AS INTEGER))
        FROM people.people_master
        WHERE unique_id LIKE %s
    """, (f"{BARTON_PREFIX}.{year:02d}.%",))
    next_seq = (cur.fetchone()[0] or 0) + 1

    stats = {'filled': 0, 'no_slot': 0, 'errors': 0}

    for c in contacts:
        slot_key = (c['outreach_id'], c['slot_type'])
        slot_info = slot_map.get(slot_key)
        if not slot_info:
            stats['no_slot'] += 1
            continue

        slot_id, company_unique_id = slot_info

        if dry_run:
            stats['filled'] += 1
            next_seq += 1
            continue

        try:
            suffix = str(next_seq)[-3:].zfill(3)
            people_uid = f"{BARTON_PREFIX}.{year:02d}.{next_seq}.{suffix}"

            cur.execute("""
                INSERT INTO people.people_master (
                    unique_id, company_unique_id, first_name, last_name,
                    title, linkedin_url, source_system,
                    company_slot_unique_id, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT DO NOTHING
            """, (
                people_uid, company_unique_id, c['first_name'], c['last_name'],
                c['title'] or c['slot_type'],
                c.get('linkedin_url', '') or None,
                'leadership_page_scrape',
                slot_id,
            ))

            if cur.rowcount > 0:
                cur.execute("""
                    UPDATE people.company_slot
                    SET is_filled = TRUE, person_unique_id = %s, updated_at = NOW()
                    WHERE slot_id = %s::uuid AND is_filled = FALSE
                """, (people_uid, slot_id))
                stats['filled'] += 1
                next_seq += 1
                # Remove from slot_map so we don't double-fill
                del slot_map[slot_key]
            else:
                stats['errors'] += 1

            if stats['filled'] % 100 == 0 and stats['filled'] > 0:
                conn.commit()
                print(f"    ... filled {stats['filled']:,}")

        except Exception as e:
            print(f"    ERROR {c['outreach_id']}/{c['slot_type']}: {e}")
            conn.rollback()
            stats['errors'] += 1

    if not dry_run:
        conn.commit()

    cur.close()
    return stats


# ═══════════════════════════════════════════════════════════════
# DEDUP + BEST-PICK
# ═══════════════════════════════════════════════════════════════

def dedup_and_pick_best(all_people: List[Dict], filled_slots: Set) -> List[Dict]:
    """
    Dedup scraped people: one person per (outreach_id, slot_type).
    Prefer: has LinkedIn > has email > has title > structured_card source.
    Skip already-filled slots.
    """
    # Group by (outreach_id, slot_type)
    buckets: Dict[Tuple[str, str], List[Dict]] = {}
    for p in all_people:
        if not p.get('slot_type'):
            continue
        key = (p['outreach_id'], p['slot_type'])
        if key in filled_slots:
            continue
        buckets.setdefault(key, []).append(p)

    result = []
    for key, candidates in buckets.items():
        # Score each candidate
        def score(c):
            s = 0
            if c.get('linkedin_url'):
                s += 10
            if c.get('email'):
                s += 5
            if c.get('title'):
                s += 3
            if c.get('source') == 'structured_card':
                s += 2
            if c.get('source') == 'heading_pattern':
                s += 1
            return s

        best = max(candidates, key=score)
        result.append(best)

    return result


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

async def run_scraper(urls: List[Dict], workers: int) -> List[Dict]:
    """Scrape all URLs concurrently and return extracted people."""
    semaphore = asyncio.Semaphore(workers)
    all_people = []
    chunk_size = 50
    total = len(urls)

    transport = httpx.AsyncHTTPTransport(retries=0)
    async with httpx.AsyncClient(
        headers=HEADERS,
        transport=transport,
        follow_redirects=True,
        timeout=15.0,
    ) as client:
        for i in range(0, total, chunk_size):
            chunk = urls[i:i+chunk_size]
            tasks = [
                scrape_one_page(
                    client, u['outreach_id'], u['company_name'],
                    u['domain'], u['source_type'], u['source_url'],
                    semaphore,
                )
                for u in chunk
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for r in results:
                if isinstance(r, list):
                    all_people.extend(r)

            done = min(i + chunk_size, total)
            people_so_far = len(all_people)
            with_slot = sum(1 for p in all_people if p.get('slot_type'))
            with_li = sum(1 for p in all_people if p.get('linkedin_url'))
            print(f"  [{done}/{total}] People: {people_so_far} | "
                  f"With slot type: {with_slot} | With LinkedIn: {with_li}")

    return all_people


def main():
    parser = argparse.ArgumentParser(description='Scrape leadership/team pages for executives')
    parser.add_argument('--coverage-id', help='Scope to a specific coverage market')
    parser.add_argument('--all', action='store_true', help='Run against all source_urls')
    parser.add_argument('--dry-run', action='store_true', help='Preview without DB writes')
    parser.add_argument('--fill', action='store_true', help='Fill unfilled slots directly')
    parser.add_argument('--limit', type=int, help='Limit number of URLs to scrape')
    parser.add_argument('--workers', type=int, default=15, help='Concurrent workers (default 15)')
    args = parser.parse_args()

    if not args.coverage_id and not args.all:
        parser.error("Must specify --coverage-id or --all")

    print("=" * 70)
    print("Leadership/Team Page Scraper")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Fill slots: {'YES' if args.fill else 'NO (CSV export only)'}")
    print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70)

    conn = get_conn()

    # Load URLs to scrape
    print("\nLoading leadership/team URLs from outreach.source_urls...")
    urls = load_urls(conn, args.coverage_id, args.limit)
    print(f"  URLs to scrape: {len(urls)}")

    if not urls:
        print("  Nothing to scrape.")
        conn.close()
        return

    unique_companies = len(set(u['outreach_id'] for u in urls))
    print(f"  Unique companies: {unique_companies}")
    by_type = {}
    for u in urls:
        by_type[u['source_type']] = by_type.get(u['source_type'], 0) + 1
    for t, c in sorted(by_type.items()):
        print(f"    {t}: {c}")

    # Load filled slots to skip
    oid_list = list(set(u['outreach_id'] for u in urls))
    filled_slots = load_filled_slots(conn, oid_list)
    print(f"  Already-filled slots: {len(filled_slots)}")

    # Scrape
    print(f"\n{'=' * 70}")
    print(f"SCRAPING ({args.workers} workers)")
    print(f"{'=' * 70}")

    all_people = asyncio.run(run_scraper(urls, args.workers))

    print(f"\n{'=' * 70}")
    print("EXTRACTION RESULTS")
    print(f"{'=' * 70}")
    print(f"  Total people extracted: {len(all_people)}")
    print(f"  With slot type (CEO/CFO/HR): {sum(1 for p in all_people if p.get('slot_type'))}")
    print(f"  With LinkedIn URL: {sum(1 for p in all_people if p.get('linkedin_url'))}")
    print(f"  With email: {sum(1 for p in all_people if p.get('email'))}")

    # By source method
    by_source = {}
    for p in all_people:
        s = p.get('source', 'unknown')
        by_source[s] = by_source.get(s, 0) + 1
    print(f"\n  By extraction method:")
    for s, c in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"    {s}: {c}")

    # By slot type
    by_slot = {}
    for p in all_people:
        st = p.get('slot_type', 'no_match')
        by_slot[st] = by_slot.get(st, 0) + 1
    print(f"\n  By slot type:")
    for s, c in sorted(by_slot.items(), key=lambda x: -x[1]):
        print(f"    {s}: {c}")

    # Dedup — one best person per (outreach_id, slot_type)
    best_picks = dedup_and_pick_best(all_people, filled_slots)
    print(f"\n  After dedup (best pick per slot): {len(best_picks)}")
    bp_slot = {}
    for p in best_picks:
        bp_slot[p['slot_type']] = bp_slot.get(p['slot_type'], 0) + 1
    for s, c in sorted(bp_slot.items()):
        print(f"    {s}: {c}")
    bp_li = sum(1 for p in best_picks if p.get('linkedin_url'))
    bp_email = sum(1 for p in best_picks if p.get('email'))
    print(f"    With LinkedIn: {bp_li}")
    print(f"    With email: {bp_email}")

    # Export CSV (always — even in dry run)
    if args.coverage_id:
        # Get zip from coverage
        cur = conn.cursor()
        cur.execute("""
            SELECT anchor_zip FROM coverage.service_agent_coverage
            WHERE coverage_id = %s
        """, (args.coverage_id,))
        row = cur.fetchone()
        zip_code = row[0] if row else 'unknown'
        cur.close()
    else:
        zip_code = 'all'

    export_path = Path(__file__).resolve().parents[4] / 'exports' / f'scraped_executives_{zip_code}.csv'
    export_path.parent.mkdir(parents=True, exist_ok=True)

    with open(export_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'outreach_id', 'company_name', 'domain', 'slot_type',
            'first_name', 'last_name', 'title', 'linkedin_url',
            'email', 'source_url', 'extraction_method',
        ])
        for p in best_picks:
            writer.writerow([
                p.get('outreach_id', ''),
                p.get('company_name', ''),
                p.get('domain', ''),
                p.get('slot_type', ''),
                p.get('first_name', ''),
                p.get('last_name', ''),
                p.get('title', ''),
                p.get('linkedin_url', ''),
                p.get('email', ''),
                p.get('source_url', ''),
                p.get('source', ''),
            ])

    print(f"\n  CSV exported: {export_path}")
    print(f"  CSV rows: {len(best_picks)}")

    # Also export ALL extracted people (not just best picks) for review
    all_export = export_path.with_name(f'scraped_all_people_{zip_code}.csv')
    with open(all_export, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'outreach_id', 'company_name', 'domain', 'slot_type',
            'first_name', 'last_name', 'title', 'linkedin_url',
            'email', 'source_url', 'extraction_method',
        ])
        for p in all_people:
            writer.writerow([
                p.get('outreach_id', ''),
                p.get('company_name', ''),
                p.get('domain', ''),
                p.get('slot_type', ''),
                p.get('first_name', ''),
                p.get('last_name', ''),
                p.get('title', ''),
                p.get('linkedin_url', ''),
                p.get('email', ''),
                p.get('source_url', ''),
                p.get('source', ''),
            ])
    print(f"  All people CSV: {all_export}")
    print(f"  All people rows: {len(all_people)}")

    # Fill slots if requested
    if args.fill and best_picks:
        print(f"\n{'=' * 70}")
        print("FILLING SLOTS")
        print(f"{'=' * 70}")

        slot_map = load_slot_map(conn, oid_list)
        stats = fill_slots(conn, best_picks, slot_map, args.dry_run)

        print(f"\n  Slots filled:  {stats['filled']:,}")
        print(f"  No slot found: {stats['no_slot']:,}")
        print(f"  Errors:        {stats['errors']:,}")

    conn.close()

    print(f"\n{'=' * 70}")
    print("DONE")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
