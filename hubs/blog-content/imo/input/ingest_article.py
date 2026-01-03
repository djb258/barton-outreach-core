"""
Blog Sub-Hub — Article Ingestion Layer
═══════════════════════════════════════════════════════════════════════════

Doctrine: /hubs/blog-content/PRD.md
Altitude: 10,000 ft (Input normalization only)

EXPLICIT SCOPE:
  ✅ Normalize raw article content from various sources
  ✅ Generate correlation_id for pipeline tracing
  ✅ Validate minimum required fields
  ✅ Return immutable ArticlePayload

EXPLICIT NON-GOALS (STRICTLY FORBIDDEN):
  ❌ NEVER parse or classify content
  ❌ NEVER match companies
  ❌ NEVER make decisions
  ❌ NEVER call external APIs beyond fetch

═══════════════════════════════════════════════════════════════════════════
"""

import uuid
import hashlib
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ArticleSource(Enum):
    """Declared article sources (must match PRD)"""
    NEWSAPI = "newsapi"
    RSS = "rss"
    PR_NEWSWIRE = "pr_newswire"
    GLOBENEWSWIRE = "globenewswire"
    SEC_EDGAR = "sec_edgar"
    COMPANY_BLOG = "company_blog"
    MANUAL = "manual"


@dataclass(frozen=True)
class ArticlePayload:
    """
    Immutable article payload for pipeline processing.
    
    Once created, this payload cannot be modified.
    Each stage receives this and returns either:
    - The same payload (pass-through)
    - A new enriched payload (with additional fields)
    - A FailureResult
    """
    # Required fields
    correlation_id: str
    article_id: str
    title: str
    content: str
    source: ArticleSource
    source_url: str
    published_at: datetime
    ingested_at: datetime
    
    # Hash for deduplication
    content_hash: str
    
    # Optional fields (extracted later)
    company_mentions: List[str] = field(default_factory=list)
    domain_mentions: List[str] = field(default_factory=list)
    
    # Metadata
    raw_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestionResult:
    """Result of article ingestion"""
    success: bool
    payload: Optional[ArticlePayload] = None
    fail_reason: Optional[str] = None
    fail_code: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Validation Functions
# ─────────────────────────────────────────────────────────────────────────────

def _validate_required_fields(raw: Dict[str, Any]) -> Optional[str]:
    """
    Validate all required fields are present.
    
    Returns error message if validation fails, None if OK.
    """
    required = ['title', 'content', 'source', 'source_url', 'published_at']
    
    for field in required:
        if field not in raw or raw[field] is None:
            return f"Missing required field: {field}"
        if isinstance(raw[field], str) and not raw[field].strip():
            return f"Empty required field: {field}"
    
    return None


def _validate_source(source: str) -> Optional[ArticleSource]:
    """
    Validate and convert source string to enum.
    
    Returns None if source is not declared in PRD.
    """
    try:
        return ArticleSource(source.lower())
    except ValueError:
        return None


def _generate_content_hash(title: str, content: str, source_url: str) -> str:
    """
    Generate SHA-256 hash for deduplication.
    
    Hash is based on immutable content identifiers.
    """
    unique_string = f"{title}|{content[:500]}|{source_url}"
    return hashlib.sha256(unique_string.encode()).hexdigest()


def _generate_article_id(source: ArticleSource, source_url: str, content_hash: str) -> str:
    """
    Generate unique article ID.
    
    Format: {source}_{hash_prefix}_{timestamp}
    """
    hash_prefix = content_hash[:12]
    timestamp = int(datetime.utcnow().timestamp())
    return f"{source.value}_{hash_prefix}_{timestamp}"


# ─────────────────────────────────────────────────────────────────────────────
# Main Ingestion Function
# ─────────────────────────────────────────────────────────────────────────────

def ingest_article(raw_input: Dict[str, Any]) -> IngestionResult:
    """
    Ingest and normalize raw article input.
    
    This is the ENTRY POINT for the Blog Sub-Hub pipeline.
    
    Args:
        raw_input: Raw article data from any source
        
    Returns:
        IngestionResult with either payload or failure info
        
    DOCTRINE:
        - No business logic
        - No external calls
        - Validation and normalization only
        - FAIL CLOSED on any validation error
    """
    # Generate correlation_id for tracing
    correlation_id = raw_input.get('correlation_id') or str(uuid.uuid4())
    
    logger.info(
        "Article ingestion started",
        extra={
            'correlation_id': correlation_id,
            'source': raw_input.get('source', 'unknown')
        }
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 1: Validate required fields
    # ─────────────────────────────────────────────────────────────────────────
    validation_error = _validate_required_fields(raw_input)
    if validation_error:
        logger.warning(
            f"Ingestion validation failed: {validation_error}",
            extra={'correlation_id': correlation_id}
        )
        return IngestionResult(
            success=False,
            fail_reason=validation_error,
            fail_code="BLOG-001"  # Article parsing failed
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 2: Validate source
    # ─────────────────────────────────────────────────────────────────────────
    source = _validate_source(raw_input['source'])
    if source is None:
        logger.warning(
            f"Unknown source: {raw_input['source']}",
            extra={'correlation_id': correlation_id}
        )
        return IngestionResult(
            success=False,
            fail_reason=f"Undeclared source: {raw_input['source']}",
            fail_code="BLOG-001"
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 3: Parse dates
    # ─────────────────────────────────────────────────────────────────────────
    try:
        published_at = raw_input['published_at']
        if isinstance(published_at, str):
            # Try ISO format first
            published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        elif not isinstance(published_at, datetime):
            raise ValueError("Invalid published_at format")
    except Exception as e:
        logger.warning(
            f"Date parsing failed: {e}",
            extra={'correlation_id': correlation_id}
        )
        return IngestionResult(
            success=False,
            fail_reason=f"Invalid published_at: {e}",
            fail_code="BLOG-001"
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 4: Generate hashes and IDs
    # ─────────────────────────────────────────────────────────────────────────
    content_hash = _generate_content_hash(
        raw_input['title'],
        raw_input['content'],
        raw_input['source_url']
    )
    
    article_id = raw_input.get('article_id') or _generate_article_id(
        source,
        raw_input['source_url'],
        content_hash
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 5: Build immutable payload
    # ─────────────────────────────────────────────────────────────────────────
    try:
        payload = ArticlePayload(
            correlation_id=correlation_id,
            article_id=article_id,
            title=raw_input['title'].strip(),
            content=raw_input['content'].strip(),
            source=source,
            source_url=raw_input['source_url'].strip(),
            published_at=published_at,
            ingested_at=datetime.utcnow(),
            content_hash=content_hash,
            company_mentions=raw_input.get('company_mentions', []),
            domain_mentions=raw_input.get('domain_mentions', []),
            raw_metadata=raw_input.get('metadata', {})
        )
    except Exception as e:
        logger.error(
            f"Payload construction failed: {e}",
            extra={'correlation_id': correlation_id}
        )
        return IngestionResult(
            success=False,
            fail_reason=f"Payload construction error: {e}",
            fail_code="BLOG-001"
        )
    
    logger.info(
        "Article ingestion successful",
        extra={
            'correlation_id': correlation_id,
            'article_id': article_id,
            'source': source.value,
            'content_hash': content_hash[:16]
        }
    )
    
    return IngestionResult(success=True, payload=payload)


# ─────────────────────────────────────────────────────────────────────────────
# Source-Specific Normalizers (Pluggable)
# ─────────────────────────────────────────────────────────────────────────────

def normalize_newsapi_article(newsapi_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize NewsAPI response to standard format.
    
    NewsAPI Format:
    {
        "title": "...",
        "description": "...",
        "content": "...",
        "url": "...",
        "publishedAt": "2024-01-15T10:30:00Z",
        "source": {"id": "...", "name": "..."}
    }
    """
    return {
        'title': newsapi_response.get('title', ''),
        'content': newsapi_response.get('content') or newsapi_response.get('description', ''),
        'source': ArticleSource.NEWSAPI.value,
        'source_url': newsapi_response.get('url', ''),
        'published_at': newsapi_response.get('publishedAt', ''),
        'metadata': {
            'source_name': newsapi_response.get('source', {}).get('name'),
            'author': newsapi_response.get('author')
        }
    }


def normalize_rss_entry(rss_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize RSS feed entry to standard format.
    
    RSS Entry Format (feedparser):
    {
        "title": "...",
        "summary": "...",
        "link": "...",
        "published_parsed": time.struct_time
    }
    """
    import time
    
    published_at = None
    if 'published_parsed' in rss_entry and rss_entry['published_parsed']:
        published_at = datetime(*rss_entry['published_parsed'][:6]).isoformat()
    elif 'published' in rss_entry:
        published_at = rss_entry['published']
    
    return {
        'title': rss_entry.get('title', ''),
        'content': rss_entry.get('summary') or rss_entry.get('description', ''),
        'source': ArticleSource.RSS.value,
        'source_url': rss_entry.get('link', ''),
        'published_at': published_at or datetime.utcnow().isoformat(),
        'metadata': {
            'feed_title': rss_entry.get('feed', {}).get('title'),
            'tags': [tag.get('term') for tag in rss_entry.get('tags', [])]
        }
    }


def normalize_sec_8k(filing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize SEC EDGAR 8-K filing to standard format.
    
    8-K filings contain item codes that map directly to event types:
    - Item 1.01: Entry into Material Agreement
    - Item 2.01: Completion of Acquisition
    - Item 5.02: Departure/Appointment of Officers
    - Item 8.01: Other Events (often funding announcements)
    """
    return {
        'title': filing.get('title', ''),
        'content': filing.get('content', ''),
        'source': ArticleSource.SEC_EDGAR.value,
        'source_url': filing.get('url', ''),
        'published_at': filing.get('filed_at', ''),
        'metadata': {
            'cik': filing.get('cik'),
            'ticker': filing.get('ticker'),
            'item_codes': filing.get('item_codes', []),
            'form_type': '8-K'
        }
    }
