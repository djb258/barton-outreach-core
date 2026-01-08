"""
Blog Sub-Hub — Company Matching Layer
═══════════════════════════════════════════════════════════════════════════

Doctrine: /hubs/blog-content/PRD.md
Altitude: 5,500 ft (Identity resolution)

EXPLICIT SCOPE:
  ✅ Match extracted entities to company_sov_id
  ✅ Use deterministic matching ONLY
  ✅ FAIL CLOSED on ambiguity or no match

EXPLICIT NON-GOALS (STRICTLY FORBIDDEN):
  ❌ NEVER create companies
  ❌ NEVER trigger enrichment
  ❌ NEVER use fuzzy rescue beyond threshold
  ❌ NEVER return multiple matches

MATCHING PRIORITY (Non-Negotiable):
  1. Exact domain match
  2. Exact normalized company name
  3. PostgreSQL FTS match
  4. rapidfuzz (threshold >= 0.90)

═══════════════════════════════════════════════════════════════════════════
"""

import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import logging

from .classify_event import ClassifiedEvent

logger = logging.getLogger(__name__)

# Minimum fuzzy match threshold (locked)
FUZZY_THRESHOLD = 0.90


@dataclass
class CompanyMatch:
    """A matched company record"""
    company_sov_id: str
    company_name: str
    domain: Optional[str]
    match_method: str  # exact_domain, exact_name, fts, fuzzy
    match_confidence: float
    match_source: str  # Which entity triggered the match


@dataclass
class MatchedEvent:
    """Classified event with matched company"""
    correlation_id: str
    article_id: str
    
    # Matched company
    company_sov_id: str
    company_name: str
    company_domain: Optional[str]
    
    # Match metadata
    match_method: str
    match_confidence: float
    match_source: str
    
    # Original classification
    classified_event: ClassifiedEvent


@dataclass
class MatchResult:
    """Result of company matching"""
    success: bool
    matched: Optional[MatchedEvent] = None
    fail_reason: Optional[str] = None
    fail_code: Optional[str] = None
    
    # Queue info for unmatched articles
    queued_for_resolution: bool = False
    queue_payload: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────────────────────────────────────
# Company Name Normalization
# ─────────────────────────────────────────────────────────────────────────────

COMPANY_SUFFIXES = [
    'inc', 'incorporated', 'inc.', 'corp', 'corporation', 'corp.',
    'llc', 'l.l.c.', 'ltd', 'limited', 'ltd.', 'co', 'company', 'co.',
    'group', 'holdings', 'partners', 'ventures', 'technologies',
    'solutions', 'services', 'systems', 'labs', 'studio', 'studios'
]


def _normalize_company_name(name: str) -> str:
    """
    Normalize company name for matching.
    
    - Lowercase
    - Remove legal suffixes
    - Remove punctuation
    - Collapse whitespace
    """
    name = name.lower().strip()
    
    # Remove common suffixes
    for suffix in COMPANY_SUFFIXES:
        pattern = rf'\b{re.escape(suffix)}\b\.?'
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # Remove punctuation except alphanumeric and spaces
    name = re.sub(r'[^\w\s]', '', name)
    
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name


def _normalize_domain(domain: str) -> str:
    """Normalize domain for matching"""
    domain = domain.lower().strip()
    
    # Remove www prefix
    if domain.startswith('www.'):
        domain = domain[4:]
    
    return domain


# ─────────────────────────────────────────────────────────────────────────────
# Database Lookup Functions (Stubs - Require Integration)
# ─────────────────────────────────────────────────────────────────────────────

async def _lookup_by_domain(domain: str) -> Optional[CompanyMatch]:
    """
    Look up company by exact domain match.
    
    PRIORITY 1: Most reliable match method.
    
    In production, this queries:
    SELECT company_sov_id, company_name, domain
    FROM company.company_master
    WHERE LOWER(domain) = LOWER($1)
    LIMIT 1
    """
    # STUB: Replace with actual database query
    logger.debug(f"Domain lookup: {domain}")
    
    # Placeholder for database integration
    # In production, this would use the Company Hub API or direct DB query
    return None


async def _lookup_by_exact_name(normalized_name: str) -> Optional[CompanyMatch]:
    """
    Look up company by exact normalized name.
    
    PRIORITY 2: Reliable after domain.
    
    In production, this queries:
    SELECT company_sov_id, company_name, domain
    FROM company.company_master
    WHERE LOWER(REGEXP_REPLACE(company_name, '(Inc|LLC|Corp|Ltd)\.?', '', 'gi')) = $1
    LIMIT 1
    """
    # STUB: Replace with actual database query
    logger.debug(f"Exact name lookup: {normalized_name}")
    return None


async def _lookup_by_fts(search_text: str) -> List[CompanyMatch]:
    """
    Look up company using PostgreSQL full-text search.
    
    PRIORITY 3: Broader but still deterministic.
    
    In production, this queries:
    SELECT company_sov_id, company_name, domain,
           ts_rank(search_vector, plainto_tsquery($1)) as rank
    FROM company.company_master
    WHERE search_vector @@ plainto_tsquery($1)
    ORDER BY rank DESC
    LIMIT 5
    """
    # STUB: Replace with actual database query
    logger.debug(f"FTS lookup: {search_text}")
    return []


def _fuzzy_match(name: str, candidates: List[Dict[str, str]]) -> Optional[CompanyMatch]:
    """
    Fuzzy match using rapidfuzz.
    
    PRIORITY 4: Last resort, bounded threshold.
    
    Uses token_set_ratio for better handling of word order variations.
    """
    try:
        from rapidfuzz import fuzz
    except ImportError:
        logger.warning("rapidfuzz not available for fuzzy matching")
        return None
    
    best_match = None
    best_score = 0.0
    normalized_name = _normalize_company_name(name)
    
    for candidate in candidates:
        candidate_normalized = _normalize_company_name(candidate['company_name'])
        
        # Use token_set_ratio for better matching
        score = fuzz.token_set_ratio(normalized_name, candidate_normalized) / 100.0
        
        if score >= FUZZY_THRESHOLD and score > best_score:
            best_score = score
            best_match = CompanyMatch(
                company_sov_id=candidate['company_sov_id'],
                company_name=candidate['company_name'],
                domain=candidate.get('domain'),
                match_method='fuzzy',
                match_confidence=score,
                match_source=name
            )
    
    return best_match


# ─────────────────────────────────────────────────────────────────────────────
# Queue for Identity Resolution
# ─────────────────────────────────────────────────────────────────────────────

def _build_resolution_queue_payload(event: ClassifiedEvent) -> Dict[str, Any]:
    """
    Build payload for Identity Resolution Queue.
    
    Unmatched articles are queued for manual review or
    Company Hub identity creation request.
    """
    return {
        'correlation_id': event.correlation_id,
        'article_id': event.article_id,
        'source': 'blog_subhub',
        'extracted_companies': [e.text for e in event.entities.companies],
        'extracted_domains': event.entities.domains,
        'article_url': event.entities.parsed_content.original_payload.source_url,
        'event_type': event.event_type.name_str,
        'confidence': event.confidence,
        'headline': event.entities.parsed_content.headline,
        'queued_at': None,  # Set at queue time
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main Matching Function
# ─────────────────────────────────────────────────────────────────────────────

async def match_company(classified: ClassifiedEvent) -> MatchResult:
    """
    Match classified event to company_sov_id.
    
    Pipeline Stage 5: Company Matching
    
    Args:
        classified: ClassifiedEvent from classification stage
        
    Returns:
        MatchResult with MatchedEvent or failure info
        
    DOCTRINE:
        - FAIL CLOSED on no match
        - FAIL CLOSED on ambiguous match
        - Queue unmatched for Identity Resolution
        - NEVER create companies
    """
    logger.info(
        "Company matching started",
        extra={
            'correlation_id': classified.correlation_id,
            'article_id': classified.article_id,
            'companies_to_match': len(classified.entities.companies),
            'domains_to_match': len(classified.entities.domains)
        }
    )
    
    try:
        matches = []
        
        # ─────────────────────────────────────────────────────────────────────
        # Priority 1: Domain matching (most reliable)
        # ─────────────────────────────────────────────────────────────────────
        for domain in classified.entities.domains:
            normalized_domain = _normalize_domain(domain)
            match = await _lookup_by_domain(normalized_domain)
            if match:
                match.match_source = f"domain:{domain}"
                matches.append(match)
                logger.info(
                    f"Domain match found: {domain} -> {match.company_sov_id}",
                    extra={'correlation_id': classified.correlation_id}
                )
                break  # Take first domain match
        
        # ─────────────────────────────────────────────────────────────────────
        # Priority 2: Exact name matching
        # ─────────────────────────────────────────────────────────────────────
        if not matches:
            for company_entity in classified.entities.companies:
                normalized_name = _normalize_company_name(company_entity.text)
                match = await _lookup_by_exact_name(normalized_name)
                if match:
                    match.match_source = f"name:{company_entity.text}"
                    matches.append(match)
                    logger.info(
                        f"Exact name match found: {company_entity.text} -> {match.company_sov_id}",
                        extra={'correlation_id': classified.correlation_id}
                    )
                    break  # Take first exact match
        
        # ─────────────────────────────────────────────────────────────────────
        # Priority 3: Full-text search
        # ─────────────────────────────────────────────────────────────────────
        if not matches:
            for company_entity in classified.entities.companies:
                fts_matches = await _lookup_by_fts(company_entity.text)
                if len(fts_matches) == 1:
                    # Single unambiguous FTS match
                    match = fts_matches[0]
                    match.match_source = f"fts:{company_entity.text}"
                    matches.append(match)
                    logger.info(
                        f"FTS match found: {company_entity.text} -> {match.company_sov_id}",
                        extra={'correlation_id': classified.correlation_id}
                    )
                    break
                elif len(fts_matches) > 1:
                    # Ambiguous - try fuzzy to disambiguate
                    logger.debug(
                        f"FTS returned {len(fts_matches)} candidates, attempting fuzzy",
                        extra={'correlation_id': classified.correlation_id}
                    )
        
        # ─────────────────────────────────────────────────────────────────────
        # Priority 4: Fuzzy matching (bounded threshold)
        # ─────────────────────────────────────────────────────────────────────
        if not matches:
            # Get candidate pool from FTS
            candidate_pool = []
            for company_entity in classified.entities.companies:
                fts_results = await _lookup_by_fts(company_entity.text)
                for r in fts_results:
                    candidate_pool.append({
                        'company_sov_id': r.company_sov_id,
                        'company_name': r.company_name,
                        'domain': r.domain
                    })
            
            # Fuzzy match against pool
            for company_entity in classified.entities.companies:
                fuzzy_match = _fuzzy_match(company_entity.text, candidate_pool)
                if fuzzy_match:
                    matches.append(fuzzy_match)
                    logger.info(
                        f"Fuzzy match found: {company_entity.text} -> {fuzzy_match.company_sov_id} "
                        f"(confidence: {fuzzy_match.match_confidence:.2f})",
                        extra={'correlation_id': classified.correlation_id}
                    )
                    break
        
        # ─────────────────────────────────────────────────────────────────────
        # Evaluate results
        # ─────────────────────────────────────────────────────────────────────
        if not matches:
            # NO MATCH - Queue for Identity Resolution
            queue_payload = _build_resolution_queue_payload(classified)
            
            logger.warning(
                "No company match found - queuing for identity resolution",
                extra={
                    'correlation_id': classified.correlation_id,
                    'article_id': classified.article_id,
                    'companies_tried': [e.text for e in classified.entities.companies],
                    'domains_tried': classified.entities.domains
                }
            )
            
            return MatchResult(
                success=False,
                fail_reason="No company match found",
                fail_code="BLOG-004",  # Company not matched
                queued_for_resolution=True,
                queue_payload=queue_payload
            )
        
        if len(matches) > 1:
            # AMBIGUOUS - Multiple matches (should not happen with priority chain)
            logger.warning(
                f"Ambiguous match: {len(matches)} companies matched",
                extra={
                    'correlation_id': classified.correlation_id,
                    'matches': [m.company_sov_id for m in matches]
                }
            )
            
            # Take highest confidence
            best = max(matches, key=lambda m: m.match_confidence)
            matches = [best]
        
        # ─────────────────────────────────────────────────────────────────────
        # Build matched event
        # ─────────────────────────────────────────────────────────────────────
        match = matches[0]
        
        matched_event = MatchedEvent(
            correlation_id=classified.correlation_id,
            article_id=classified.article_id,
            company_sov_id=match.company_sov_id,
            company_name=match.company_name,
            company_domain=match.domain,
            match_method=match.match_method,
            match_confidence=match.match_confidence,
            match_source=match.match_source,
            classified_event=classified
        )
        
        logger.info(
            "Company matching successful",
            extra={
                'correlation_id': classified.correlation_id,
                'article_id': classified.article_id,
                'company_sov_id': match.company_sov_id,
                'match_method': match.match_method,
                'match_confidence': match.match_confidence
            }
        )
        
        return MatchResult(success=True, matched=matched_event)
        
    except Exception as e:
        logger.error(
            f"Company matching failed: {e}",
            extra={
                'correlation_id': classified.correlation_id,
                'article_id': classified.article_id,
                'error': str(e)
            }
        )
        return MatchResult(
            success=False,
            fail_reason=f"Matching error: {e}",
            fail_code="BLOG-301"  # Company fuzzy match below threshold
        )
