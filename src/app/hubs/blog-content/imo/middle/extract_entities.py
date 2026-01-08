"""
Blog Sub-Hub — Entity Extraction Layer
═══════════════════════════════════════════════════════════════════════════

Doctrine: /hubs/blog-content/PRD.md
Altitude: 7,000 ft (NER extraction)

EXPLICIT SCOPE:
  ✅ Extract company names (ORG entities)
  ✅ Extract person names (PERSON entities)
  ✅ Extract domains from URLs
  ✅ Extract monetary values (MONEY entities)
  ✅ Extract locations (GPE, LOC entities)

EXPLICIT NON-GOALS (STRICTLY FORBIDDEN):
  ❌ NEVER classify events
  ❌ NEVER match to company_sov_id
  ❌ NEVER make decisions

TOOLS:
  - spaCy (en_core_web_lg) - PRIMARY
  - Regex patterns - FALLBACK

═══════════════════════════════════════════════════════════════════════════
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import logging

from .parse_content import ParsedContent

logger = logging.getLogger(__name__)

# Lazy load spaCy to avoid import errors if not installed
_nlp = None


def _get_nlp():
    """Lazy load spaCy model"""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_lg")
            logger.info("spaCy model loaded: en_core_web_lg")
        except Exception as e:
            logger.warning(f"spaCy model not available: {e}. Using regex fallback.")
            _nlp = "FALLBACK"
    return _nlp


@dataclass
class ExtractedEntity:
    """A single extracted entity"""
    text: str
    entity_type: str  # ORG, PERSON, MONEY, GPE, DATE, etc.
    start_char: int
    end_char: int
    confidence: float  # 0.0 - 1.0


@dataclass
class MonetaryValue:
    """Extracted monetary value with normalization"""
    raw_text: str
    amount: float
    currency: str  # USD, EUR, etc.
    magnitude: str  # million, billion, etc.


@dataclass
class ExtractedEntities:
    """All extracted entities from an article"""
    correlation_id: str
    article_id: str
    
    # Entity lists
    companies: List[ExtractedEntity] = field(default_factory=list)
    persons: List[ExtractedEntity] = field(default_factory=list)
    locations: List[ExtractedEntity] = field(default_factory=list)
    monetary_values: List[MonetaryValue] = field(default_factory=list)
    
    # Extracted domains (from URLs in content)
    domains: List[str] = field(default_factory=list)
    
    # Original parsed content
    parsed_content: ParsedContent = None
    
    # Extraction metadata
    extraction_method: str = "spacy"  # spacy, regex, hybrid
    total_entities: int = 0


@dataclass
class ExtractionResult:
    """Result of entity extraction"""
    success: bool
    entities: Optional[ExtractedEntities] = None
    fail_reason: Optional[str] = None
    fail_code: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Regex Patterns (Fallback + Enhancement)
# ─────────────────────────────────────────────────────────────────────────────

# Company name patterns (Inc., LLC, Corp., etc.)
COMPANY_SUFFIX_PATTERN = re.compile(
    r'\b([A-Z][A-Za-z0-9\s&]+(?:Inc\.?|LLC|Corp\.?|Corporation|Ltd\.?|Limited|Co\.?|Company|Group|Holdings|Partners|Ventures))\b',
    re.IGNORECASE
)

# Domain extraction pattern
DOMAIN_PATTERN = re.compile(
    r'(?:https?://)?(?:www\.)?([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+)',
    re.IGNORECASE
)

# Monetary value patterns
MONEY_PATTERN = re.compile(
    r'\$\s*(\d+(?:\.\d+)?)\s*(million|billion|M|B|K|thousand)?',
    re.IGNORECASE
)

# Executive title patterns (for person validation)
EXECUTIVE_TITLES = [
    'CEO', 'CFO', 'CTO', 'COO', 'CMO', 'CIO', 'CISO', 'CPO',
    'Chief Executive', 'Chief Financial', 'Chief Technology', 'Chief Operating',
    'President', 'Vice President', 'VP', 'SVP', 'EVP',
    'Director', 'Managing Director', 'Partner', 'Founder', 'Co-Founder'
]


# ─────────────────────────────────────────────────────────────────────────────
# Extraction Functions
# ─────────────────────────────────────────────────────────────────────────────

def _extract_with_spacy(text: str) -> Tuple[List[ExtractedEntity], List[ExtractedEntity], List[ExtractedEntity]]:
    """
    Extract entities using spaCy NER.
    
    Returns: (companies, persons, locations)
    """
    nlp = _get_nlp()
    
    if nlp == "FALLBACK":
        return [], [], []
    
    doc = nlp(text[:100000])  # Limit text length for performance
    
    companies = []
    persons = []
    locations = []
    
    for ent in doc.ents:
        entity = ExtractedEntity(
            text=ent.text,
            entity_type=ent.label_,
            start_char=ent.start_char,
            end_char=ent.end_char,
            confidence=0.85  # spaCy doesn't provide confidence, use default
        )
        
        if ent.label_ == "ORG":
            companies.append(entity)
        elif ent.label_ == "PERSON":
            persons.append(entity)
        elif ent.label_ in ("GPE", "LOC"):
            locations.append(entity)
    
    return companies, persons, locations


def _extract_companies_regex(text: str) -> List[ExtractedEntity]:
    """Extract company names using regex patterns"""
    companies = []
    
    for match in COMPANY_SUFFIX_PATTERN.finditer(text):
        companies.append(ExtractedEntity(
            text=match.group(1).strip(),
            entity_type="ORG",
            start_char=match.start(),
            end_char=match.end(),
            confidence=0.70  # Lower confidence for regex
        ))
    
    return companies


def _extract_domains(text: str) -> List[str]:
    """Extract unique domains from text"""
    matches = DOMAIN_PATTERN.findall(text)
    
    # Deduplicate and filter out common non-company domains
    excluded_domains = {
        'twitter.com', 'facebook.com', 'linkedin.com', 'youtube.com',
        'instagram.com', 'github.com', 'google.com', 'apple.com',
        'example.com', 'test.com', 'localhost'
    }
    
    domains = []
    seen = set()
    
    for domain in matches:
        domain_lower = domain.lower()
        if domain_lower not in seen and domain_lower not in excluded_domains:
            seen.add(domain_lower)
            domains.append(domain_lower)
    
    return domains


def _extract_monetary_values(text: str) -> List[MonetaryValue]:
    """Extract and normalize monetary values"""
    values = []
    
    for match in MONEY_PATTERN.finditer(text):
        raw_amount = float(match.group(1))
        magnitude = (match.group(2) or '').lower()
        
        # Normalize to actual number
        multiplier = 1
        if magnitude in ('million', 'm'):
            multiplier = 1_000_000
        elif magnitude in ('billion', 'b'):
            multiplier = 1_000_000_000
        elif magnitude in ('thousand', 'k'):
            multiplier = 1_000
        
        values.append(MonetaryValue(
            raw_text=match.group(0),
            amount=raw_amount * multiplier,
            currency="USD",  # Assume USD for $ symbol
            magnitude=magnitude or "units"
        ))
    
    return values


def _deduplicate_entities(entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
    """Remove duplicate entities, keeping highest confidence"""
    seen = {}  # text_lower -> entity
    
    for entity in entities:
        key = entity.text.lower().strip()
        if key not in seen or entity.confidence > seen[key].confidence:
            seen[key] = entity
    
    return list(seen.values())


# ─────────────────────────────────────────────────────────────────────────────
# Main Extraction Function
# ─────────────────────────────────────────────────────────────────────────────

def extract_entities(parsed: ParsedContent) -> ExtractionResult:
    """
    Extract named entities from parsed content.
    
    Pipeline Stage 3: Entity Extraction
    
    Args:
        parsed: ParsedContent from parsing stage
        
    Returns:
        ExtractionResult with ExtractedEntities or failure info
        
    DOCTRINE:
        - Local-first (spaCy)
        - Regex fallback/enhancement
        - FAIL CLOSED on extraction errors
    """
    logger.info(
        "Entity extraction started",
        extra={
            'correlation_id': parsed.correlation_id,
            'article_id': parsed.article_id
        }
    )
    
    try:
        text = parsed.clean_text
        extraction_method = "hybrid"
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 1: Extract with spaCy (if available)
        # ─────────────────────────────────────────────────────────────────────
        spacy_companies, spacy_persons, spacy_locations = _extract_with_spacy(text)
        
        if not spacy_companies and not spacy_persons:
            extraction_method = "regex"
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 2: Enhance companies with regex
        # ─────────────────────────────────────────────────────────────────────
        regex_companies = _extract_companies_regex(text)
        
        # Merge and deduplicate
        all_companies = _deduplicate_entities(spacy_companies + regex_companies)
        all_persons = _deduplicate_entities(spacy_persons)
        all_locations = _deduplicate_entities(spacy_locations)
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 3: Extract domains
        # ─────────────────────────────────────────────────────────────────────
        domains = _extract_domains(text)
        
        # Also extract from source URL
        source_domain = _extract_domains(parsed.original_payload.source_url)
        domains.extend(source_domain)
        domains = list(set(domains))  # Deduplicate
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 4: Extract monetary values
        # ─────────────────────────────────────────────────────────────────────
        monetary_values = _extract_monetary_values(text)
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 5: Build result
        # ─────────────────────────────────────────────────────────────────────
        total_entities = len(all_companies) + len(all_persons) + len(all_locations) + len(monetary_values)
        
        entities = ExtractedEntities(
            correlation_id=parsed.correlation_id,
            article_id=parsed.article_id,
            companies=all_companies,
            persons=all_persons,
            locations=all_locations,
            monetary_values=monetary_values,
            domains=domains,
            parsed_content=parsed,
            extraction_method=extraction_method,
            total_entities=total_entities
        )
        
        logger.info(
            "Entity extraction successful",
            extra={
                'correlation_id': parsed.correlation_id,
                'article_id': parsed.article_id,
                'companies_found': len(all_companies),
                'persons_found': len(all_persons),
                'domains_found': len(domains),
                'monetary_values_found': len(monetary_values),
                'extraction_method': extraction_method
            }
        )
        
        return ExtractionResult(success=True, entities=entities)
        
    except Exception as e:
        logger.error(
            f"Entity extraction failed: {e}",
            extra={
                'correlation_id': parsed.correlation_id,
                'article_id': parsed.article_id,
                'error': str(e)
            }
        )
        return ExtractionResult(
            success=False,
            fail_reason=f"NER extraction error: {e}",
            fail_code="BLOG-002"  # NER extraction failed
        )
