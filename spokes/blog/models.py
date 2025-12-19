"""
Blog Spoke Data Models
======================
Data classes for news articles, events, and signals.

Barton ID Range: 04.04.02.04.4XXXX.###
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class EventType(Enum):
    """Types of business events detected from news"""
    FUNDING_EVENT = "funding_event"
    ACQUISITION = "acquisition"
    LEADERSHIP_CHANGE = "leadership_change"
    EXPANSION = "expansion"
    PRODUCT_LAUNCH = "product_launch"
    PARTNERSHIP = "partnership"
    LAYOFF = "layoff"
    NEGATIVE_NEWS = "negative_news"
    UNKNOWN = "unknown"


class ArticleSource(Enum):
    """Sources of news articles"""
    RSS_FEED = "rss_feed"
    NEWSAPI = "newsapi"
    PR_NEWSWIRE = "pr_newswire"
    GLOBENEWSWIRE = "globenewswire"
    SEC_EDGAR = "sec_edgar"
    COMPANY_BLOG = "company_blog"
    LINKEDIN_NEWS = "linkedin_news"
    BING_NEWS = "bing_news"


class ConfidenceLevel(Enum):
    """Confidence levels for event detection"""
    HIGH = "high"        # >= 0.85
    MEDIUM = "medium"    # >= 0.65
    LOW = "low"          # >= 0.50
    VERY_LOW = "very_low"  # < 0.50


# =============================================================================
# EVENT IMPACT VALUES
# =============================================================================

EVENT_IMPACTS: Dict[EventType, float] = {
    EventType.FUNDING_EVENT: 15.0,
    EventType.ACQUISITION: 12.0,
    EventType.LEADERSHIP_CHANGE: 8.0,
    EventType.EXPANSION: 7.0,
    EventType.PRODUCT_LAUNCH: 5.0,
    EventType.PARTNERSHIP: 5.0,
    EventType.LAYOFF: -3.0,
    EventType.NEGATIVE_NEWS: -5.0,
    EventType.UNKNOWN: 0.0,
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class NewsArticle:
    """
    A news article to be processed.

    Input contract for Blog Spoke processing.
    """
    correlation_id: str  # MANDATORY - UUID v4, propagated through pipeline
    article_id: str
    title: str
    content: str
    source: ArticleSource
    url: str
    published_at: datetime
    ingested_at: datetime = field(default_factory=datetime.utcnow)

    # Extracted entities (populated during processing)
    company_mentions: List[str] = field(default_factory=list)
    domain_mentions: List[str] = field(default_factory=list)
    person_mentions: List[str] = field(default_factory=list)
    amount_mentions: List[str] = field(default_factory=list)

    # Raw metadata from source
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate required fields."""
        if not self.correlation_id:
            raise ValueError("correlation_id is MANDATORY for NewsArticle")
        if not self.article_id:
            raise ValueError("article_id is required")
        if not self.title:
            raise ValueError("title is required")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'correlation_id': self.correlation_id,
            'article_id': self.article_id,
            'title': self.title,
            'content': self.content[:500] + '...' if len(self.content) > 500 else self.content,
            'source': self.source.value,
            'url': self.url,
            'published_at': self.published_at.isoformat(),
            'ingested_at': self.ingested_at.isoformat(),
            'company_mentions': self.company_mentions,
            'domain_mentions': self.domain_mentions,
            'person_mentions': self.person_mentions,
            'amount_mentions': self.amount_mentions,
        }


@dataclass
class FundingDetails:
    """Details of a funding event"""
    amount: Optional[str] = None  # e.g., "$50 million"
    amount_numeric: Optional[float] = None  # e.g., 50000000.0
    round_type: Optional[str] = None  # e.g., "Series B"
    lead_investor: Optional[str] = None
    participating_investors: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class AcquisitionDetails:
    """Details of an acquisition/M&A event"""
    acquisition_type: str = "unknown"  # acquired, acquiring, merger
    target_company: Optional[str] = None
    acquirer_company: Optional[str] = None
    deal_value: Optional[str] = None
    deal_value_numeric: Optional[float] = None
    confidence: float = 0.0


@dataclass
class LeadershipChangeDetails:
    """Details of a leadership change"""
    person_name: Optional[str] = None
    new_title: Optional[str] = None
    previous_title: Optional[str] = None
    previous_company: Optional[str] = None
    change_type: str = "unknown"  # hired, promoted, departed, retired
    confidence: float = 0.0


@dataclass
class LayoffDetails:
    """Details of a layoff event"""
    headcount: Optional[int] = None
    percentage: Optional[float] = None  # Percentage of workforce
    departments: List[str] = field(default_factory=list)
    reason: Optional[str] = None
    confidence: float = 0.0


@dataclass
class ExpansionDetails:
    """Details of an expansion event"""
    expansion_type: str = "unknown"  # office, market, product_line
    location: Optional[str] = None
    market: Optional[str] = None
    headcount_added: Optional[int] = None
    confidence: float = 0.0


@dataclass
class DetectedEvent:
    """
    An event detected from article processing.

    Represents a single detected event from an article,
    with its type, details, and confidence score.
    """
    event_type: EventType
    confidence: float
    keywords_matched: List[str] = field(default_factory=list)
    entities_extracted: Dict[str, Any] = field(default_factory=dict)

    # Type-specific details (one will be populated based on event_type)
    funding_details: Optional[FundingDetails] = None
    acquisition_details: Optional[AcquisitionDetails] = None
    leadership_details: Optional[LeadershipChangeDetails] = None
    layoff_details: Optional[LayoffDetails] = None
    expansion_details: Optional[ExpansionDetails] = None

    @property
    def impact(self) -> float:
        """Get BIT impact for this event type"""
        return EVENT_IMPACTS.get(self.event_type, 0.0)

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Get confidence level category"""
        if self.confidence >= 0.85:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.65:
            return ConfidenceLevel.MEDIUM
        elif self.confidence >= 0.50:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type.value,
            'confidence': self.confidence,
            'confidence_level': self.confidence_level.value,
            'impact': self.impact,
            'keywords_matched': self.keywords_matched,
            'entities_extracted': self.entities_extracted,
        }


@dataclass
class ArticleProcessingResult:
    """
    Result of processing a single article.

    Output contract for Blog Spoke processing.
    """
    correlation_id: str  # Same as input - propagated unchanged
    article_id: str
    success: bool

    # Matching results
    company_id: Optional[str] = None
    company_matched: bool = False
    match_method: Optional[str] = None  # domain, exact_name, fuzzy

    # Detection results
    events_detected: List[DetectedEvent] = field(default_factory=list)
    signals_emitted: int = 0

    # Timing
    processing_time_ms: int = 0

    # Failure info (if any)
    failure_reason: Optional[str] = None
    error_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'correlation_id': self.correlation_id,
            'article_id': self.article_id,
            'success': self.success,
            'company_id': self.company_id,
            'company_matched': self.company_matched,
            'match_method': self.match_method,
            'events_detected': [e.to_dict() for e in self.events_detected],
            'signals_emitted': self.signals_emitted,
            'processing_time_ms': self.processing_time_ms,
            'failure_reason': self.failure_reason,
            'error_code': self.error_code,
        }


# =============================================================================
# RSS FEED MODELS
# =============================================================================

@dataclass
class RSSFeed:
    """An RSS feed to monitor"""
    feed_id: str
    feed_url: str
    company_id: Optional[str] = None  # If known, associated company
    company_domain: Optional[str] = None
    feed_type: str = "company_blog"  # company_blog, news, pr
    poll_frequency_hours: int = 24
    last_polled_at: Optional[datetime] = None
    last_entry_id: Optional[str] = None
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'feed_id': self.feed_id,
            'feed_url': self.feed_url,
            'company_id': self.company_id,
            'company_domain': self.company_domain,
            'feed_type': self.feed_type,
            'poll_frequency_hours': self.poll_frequency_hours,
            'last_polled_at': self.last_polled_at.isoformat() if self.last_polled_at else None,
            'enabled': self.enabled,
        }


@dataclass
class RSSEntry:
    """A single entry from an RSS feed"""
    entry_id: str
    feed_id: str
    title: str
    link: str
    published: Optional[datetime] = None
    updated: Optional[datetime] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_news_article(self, correlation_id: str, source: ArticleSource = ArticleSource.RSS_FEED) -> NewsArticle:
        """Convert RSS entry to NewsArticle for processing"""
        return NewsArticle(
            correlation_id=correlation_id,
            article_id=self.entry_id,
            title=self.title,
            content=self.content or self.summary or "",
            source=source,
            url=self.link,
            published_at=self.published or datetime.utcnow(),
            raw_metadata={
                'feed_id': self.feed_id,
                'author': self.author,
                'tags': self.tags,
            }
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "EventType",
    "ArticleSource",
    "ConfidenceLevel",
    # Constants
    "EVENT_IMPACTS",
    # Data classes
    "NewsArticle",
    "FundingDetails",
    "AcquisitionDetails",
    "LeadershipChangeDetails",
    "LayoffDetails",
    "ExpansionDetails",
    "DetectedEvent",
    "ArticleProcessingResult",
    # RSS models
    "RSSFeed",
    "RSSEntry",
]
