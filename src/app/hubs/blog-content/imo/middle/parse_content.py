"""
Blog Sub-Hub — Content Parsing Layer
═══════════════════════════════════════════════════════════════════════════

Doctrine: /hubs/blog-content/PRD.md
Altitude: 8,000 ft (Content normalization)

EXPLICIT SCOPE:
  ✅ Strip HTML tags
  ✅ Normalize whitespace
  ✅ Extract headline
  ✅ Clean and prepare text for NER

EXPLICIT NON-GOALS (STRICTLY FORBIDDEN):
  ❌ NEVER classify events
  ❌ NEVER match companies
  ❌ NEVER call external APIs

═══════════════════════════════════════════════════════════════════════════
"""

import re
import html
from dataclasses import dataclass
from typing import Optional
import logging

from ..input.ingest_article import ArticlePayload

logger = logging.getLogger(__name__)


@dataclass
class ParsedContent:
    """Parsed and cleaned article content"""
    correlation_id: str
    article_id: str
    
    # Cleaned content
    headline: str
    clean_text: str
    
    # Original payload (immutable reference)
    original_payload: ArticlePayload
    
    # Parsing metadata
    word_count: int
    sentence_count: int
    has_financial_data: bool


@dataclass
class ParseResult:
    """Result of content parsing"""
    success: bool
    parsed: Optional[ParsedContent] = None
    fail_reason: Optional[str] = None
    fail_code: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Text Cleaning Functions
# ─────────────────────────────────────────────────────────────────────────────

def _strip_html(text: str) -> str:
    """Remove HTML tags from text"""
    # Decode HTML entities first
    text = html.unescape(text)
    
    # Remove script and style elements
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    return text


def _normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text"""
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def _extract_headline(title: str, content: str) -> str:
    """
    Extract the best headline from title and content.
    
    Prioritizes title, falls back to first sentence of content.
    """
    if title and len(title.strip()) > 10:
        return title.strip()
    
    # Fall back to first sentence
    sentences = content.split('.')
    if sentences:
        first_sentence = sentences[0].strip()
        if len(first_sentence) > 10:
            return first_sentence
    
    return title.strip() if title else "Untitled"


def _count_sentences(text: str) -> int:
    """Count sentences in text (approximate)"""
    # Split on sentence-ending punctuation
    sentences = re.split(r'[.!?]+', text)
    # Filter out empty strings
    return len([s for s in sentences if s.strip()])


def _detect_financial_data(text: str) -> bool:
    """
    Detect if text contains financial data patterns.
    
    Looks for:
    - Dollar amounts ($X million, $X billion)
    - Percentages
    - Series A/B/C mentions
    - Valuation language
    """
    patterns = [
        r'\$\d+(?:\.\d+)?\s*(?:million|billion|M|B)',  # Dollar amounts
        r'\d+(?:\.\d+)?%',  # Percentages
        r'series\s+[a-z]',  # Funding rounds (case insensitive)
        r'valuation',
        r'raised\s+\$',
        r'funding\s+round',
    ]
    
    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Main Parsing Function
# ─────────────────────────────────────────────────────────────────────────────

def parse_content(payload: ArticlePayload) -> ParseResult:
    """
    Parse and clean article content.
    
    Pipeline Stage 2: Content Parsing
    
    Args:
        payload: Immutable ArticlePayload from ingestion
        
    Returns:
        ParseResult with ParsedContent or failure info
        
    DOCTRINE:
        - No external calls
        - Deterministic transformations only
        - FAIL CLOSED on parsing errors
    """
    logger.info(
        "Content parsing started",
        extra={
            'correlation_id': payload.correlation_id,
            'article_id': payload.article_id
        }
    )
    
    try:
        # ─────────────────────────────────────────────────────────────────────
        # Step 1: Strip HTML
        # ─────────────────────────────────────────────────────────────────────
        clean_content = _strip_html(payload.content)
        clean_title = _strip_html(payload.title)
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 2: Normalize whitespace
        # ─────────────────────────────────────────────────────────────────────
        clean_content = _normalize_whitespace(clean_content)
        clean_title = _normalize_whitespace(clean_title)
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 3: Validate content length
        # ─────────────────────────────────────────────────────────────────────
        if len(clean_content) < 50:
            logger.warning(
                "Content too short after cleaning",
                extra={
                    'correlation_id': payload.correlation_id,
                    'content_length': len(clean_content)
                }
            )
            return ParseResult(
                success=False,
                fail_reason=f"Content too short: {len(clean_content)} chars",
                fail_code="BLOG-001"
            )
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 4: Extract headline
        # ─────────────────────────────────────────────────────────────────────
        headline = _extract_headline(clean_title, clean_content)
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 5: Compute metadata
        # ─────────────────────────────────────────────────────────────────────
        word_count = len(clean_content.split())
        sentence_count = _count_sentences(clean_content)
        has_financial_data = _detect_financial_data(clean_content)
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 6: Build parsed content
        # ─────────────────────────────────────────────────────────────────────
        parsed = ParsedContent(
            correlation_id=payload.correlation_id,
            article_id=payload.article_id,
            headline=headline,
            clean_text=clean_content,
            original_payload=payload,
            word_count=word_count,
            sentence_count=sentence_count,
            has_financial_data=has_financial_data
        )
        
        logger.info(
            "Content parsing successful",
            extra={
                'correlation_id': payload.correlation_id,
                'article_id': payload.article_id,
                'word_count': word_count,
                'has_financial_data': has_financial_data
            }
        )
        
        return ParseResult(success=True, parsed=parsed)
        
    except Exception as e:
        logger.error(
            f"Content parsing failed: {e}",
            extra={
                'correlation_id': payload.correlation_id,
                'article_id': payload.article_id,
                'error': str(e)
            }
        )
        return ParseResult(
            success=False,
            fail_reason=f"Parsing error: {e}",
            fail_code="BLOG-001"
        )
