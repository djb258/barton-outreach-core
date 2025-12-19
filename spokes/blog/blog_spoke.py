"""
Blog Node Spoke - Spoke #3
==========================
Processes news articles and emits signals to BIT Engine.

Per PRD v2.1: Blog/News Sub-Hub
- Owns: News article ingestion, event detection, signal emission
- Does NOT own: Company identity, email patterns, outreach decisions

Signals emitted:
- FUNDING_EVENT: +15.0
- ACQUISITION: +12.0
- LEADERSHIP_CHANGE: +8.0
- EXPANSION: +7.0
- PRODUCT_LAUNCH: +5.0
- PARTNERSHIP: +5.0
- LAYOFF: -3.0
- NEGATIVE_NEWS: -5.0

Barton ID Range: 04.04.02.04.4XXXX.###
"""

import os
import time
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

# Wheel imports
from ctb.sys.enrichment.pipeline_engine.wheel.bicycle_wheel import Spoke, Hub
from ctb.sys.enrichment.pipeline_engine.wheel.wheel_result import SpokeResult, ResultStatus, FailureType

# BIT Engine
from hub.company.bit_engine import BITEngine, SignalType

# Doctrine enforcement
from ops.enforcement.correlation_id import validate_correlation_id, CorrelationIDError
from ops.enforcement.hub_gate import validate_company_anchor, HubGateError, GateLevel
from ops.enforcement.signal_dedup import should_emit_signal, get_deduplicator

# Local imports
from .models import (
    NewsArticle,
    ArticleProcessingResult,
    DetectedEvent,
    EventType,
    EVENT_IMPACTS,
)
from .event_detector import EventDetector
from .rss_ingestor import RSSIngestor, RSSFeed


logger = logging.getLogger(__name__)


# =============================================================================
# SIGNAL TYPE MAPPING (Complete per PRD v2.1)
# =============================================================================

EVENT_TO_SIGNAL: Dict[EventType, SignalType] = {
    EventType.FUNDING_EVENT: SignalType.FUNDING_EVENT,
    EventType.ACQUISITION: SignalType.ACQUISITION,
    EventType.LEADERSHIP_CHANGE: SignalType.LEADERSHIP_CHANGE,
    EventType.EXPANSION: SignalType.EXPANSION,
    EventType.PRODUCT_LAUNCH: SignalType.PRODUCT_LAUNCH,
    EventType.PARTNERSHIP: SignalType.PARTNERSHIP,
    EventType.LAYOFF: SignalType.LAYOFF,
    EventType.NEGATIVE_NEWS: SignalType.NEGATIVE_NEWS,
}


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class BlogSpokeConfig:
    """Configuration for Blog Spoke."""
    enabled: bool = True
    min_confidence: float = 0.50  # Minimum to emit signal
    review_threshold: float = 0.75  # Queue for review if below
    burn_in_mode: bool = True  # Higher thresholds during burn-in
    burn_in_min_confidence: float = 0.85
    dedup_window_days: int = 30  # News signal dedup window
    max_signals_per_article: int = 3


def load_blog_config() -> BlogSpokeConfig:
    """Load Blog Spoke configuration from environment."""
    return BlogSpokeConfig(
        enabled=os.getenv("BLOG_SPOKE_ENABLED", "true").lower() == "true",
        min_confidence=float(os.getenv("BLOG_MIN_CONFIDENCE", "0.50")),
        review_threshold=float(os.getenv("BLOG_REVIEW_THRESHOLD", "0.75")),
        burn_in_mode=os.getenv("BLOG_BURN_IN_MODE", "true").lower() == "true",
        burn_in_min_confidence=float(os.getenv("BLOG_BURN_IN_CONFIDENCE", "0.85")),
        dedup_window_days=int(os.getenv("BLOG_DEDUP_WINDOW_DAYS", "30")),
        max_signals_per_article=int(os.getenv("BLOG_MAX_SIGNALS_PER_ARTICLE", "3")),
    )


# =============================================================================
# SIGNAL CACHE FOR DEDUPLICATION
# =============================================================================

class SignalCache:
    """
    Signal deduplication cache.

    Per PRD v2.1:
    - Key: (company_id, signal_type, article_id)
    - Window: 30 days
    - Hash: SHA-256 for fast lookup
    """

    def __init__(self, window_days: int = 30):
        self.window_days = window_days
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _generate_key(self, company_id: str, signal_type: str, article_id: str) -> str:
        """Generate dedup key hash."""
        combined = f"{company_id}:{signal_type}:{article_id}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def get(self, dedup_key: str, window_days: int = None) -> Optional[Dict[str, Any]]:
        """Get cached signal if within window."""
        if dedup_key not in self._cache:
            return None

        entry = self._cache[dedup_key]
        cached_at = datetime.fromisoformat(entry['cached_at'])
        window = window_days or self.window_days
        age = (datetime.utcnow() - cached_at).days

        if age <= window:
            return entry
        return None

    def set(self, dedup_key: str, data: Dict[str, Any], ttl_days: int = None):
        """Cache signal data."""
        self._cache[dedup_key] = {
            **data,
            'cached_at': datetime.utcnow().isoformat(),
        }

    def exists(
        self,
        company_id: str,
        signal_type: str,
        article_id: str
    ) -> bool:
        """Check if signal already emitted."""
        key = self._generate_key(company_id, signal_type, article_id)
        return self.get(key) is not None

    def record(
        self,
        company_id: str,
        signal_type: str,
        article_id: str,
        correlation_id: str,
        confidence: float
    ):
        """Record emitted signal for deduplication."""
        key = self._generate_key(company_id, signal_type, article_id)
        self.set(key, {
            'correlation_id': correlation_id,
            'source': 'blog_node',
            'confidence': confidence,
        })


# =============================================================================
# BLOG NODE SPOKE
# =============================================================================

class BlogNodeSpoke(Spoke):
    """
    Blog/News Node - Spoke #3 of the Company Hub.

    Processes news articles to:
    1. Detect business events (funding, M&A, leadership changes)
    2. Match articles to companies
    3. Emit signals to BIT Engine

    DOCTRINE:
    - ONLY emits signals. NEVER makes outreach decisions.
    - Requires company_id anchor before signal emission.
    - Uses 30-day deduplication window for news events.

    Company Hub Integration:
    - Uses CompanyPipeline for domain/name lookups
    - Signals persisted to Neon via BIT Engine
    """

    def __init__(
        self,
        hub: Hub,
        bit_engine: Optional[BITEngine] = None,
        config: BlogSpokeConfig = None,
        company_pipeline=None
    ):
        """
        Initialize Blog Node Spoke.

        Args:
            hub: Parent hub instance
            bit_engine: BIT Engine for signals
            config: Blog Spoke configuration
            company_pipeline: CompanyPipeline for company lookups
        """
        super().__init__(name="blog_node", hub=hub)
        self.bit_engine = bit_engine or BITEngine()
        self.config = config or load_blog_config()
        self._company_pipeline = company_pipeline

        # Sub-components
        self.event_detector = EventDetector(
            min_confidence=self._get_min_confidence()
        )
        self.rss_ingestor = RSSIngestor()
        self.signal_cache = SignalCache(window_days=self.config.dedup_window_days)

        # Stats
        self.stats = {
            'total_processed': 0,
            'articles_matched': 0,
            'articles_unmatched': 0,
            'events_detected': 0,
            'signals_emitted': 0,
            'signals_deduped': 0,
            'signals_below_threshold': 0,
            'errors': 0,
        }

    def set_company_pipeline(self, pipeline) -> None:
        """Set company pipeline for company lookups."""
        self._company_pipeline = pipeline

    def _get_min_confidence(self) -> float:
        """Get minimum confidence based on mode."""
        if self.config.burn_in_mode:
            return self.config.burn_in_min_confidence
        return self.config.min_confidence

    def process(self, data: Any, correlation_id: str = None) -> SpokeResult:
        """
        Process a news article or RSS feed.

        DOCTRINE: correlation_id is MANDATORY. FAIL HARD if missing.

        Args:
            data: NewsArticle, RSSFeed, or list of NewsArticle
            correlation_id: MANDATORY - End-to-end trace ID (UUID v4)

        Returns:
            SpokeResult with processing outcome

        Raises:
            CorrelationIDError: If correlation_id is missing or invalid
        """
        # Kill switch
        if not self.config.enabled or os.getenv('KILL_BLOG_SUBHUB', '').lower() == 'true':
            return SpokeResult(
                status=ResultStatus.SKIPPED,
                failure_reason='killed_by_config'
            )

        # Handle different input types
        if isinstance(data, NewsArticle):
            # Use article's correlation_id or provided one
            cid = data.correlation_id or correlation_id
            return self._process_article(data, cid)
        elif isinstance(data, RSSFeed):
            return self._process_feed(data, correlation_id)
        elif isinstance(data, list):
            return self._process_batch(data, correlation_id)
        else:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason=f"Unknown data type: {type(data).__name__}"
            )

    def _process_article(
        self,
        article: NewsArticle,
        correlation_id: str
    ) -> SpokeResult:
        """Process a single news article."""
        # DOCTRINE: Validate correlation_id
        process_id = "blog.spoke.process_article"
        try:
            correlation_id = validate_correlation_id(correlation_id, process_id, "Blog Spoke")
        except CorrelationIDError as e:
            self.stats['errors'] += 1
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason=str(e)
            )

        start_time = time.time()
        self.stats['total_processed'] += 1

        result = ArticleProcessingResult(
            correlation_id=correlation_id,
            article_id=article.article_id,
            success=False
        )

        try:
            # Step 1: Match to company
            company_id = self._match_company(article)

            if not company_id:
                # Queue for identity resolution
                self._queue_for_identity(article, correlation_id)
                self.stats['articles_unmatched'] += 1

                result.success = True  # Processing succeeded, just no company match
                result.failure_reason = "company_not_matched"

                return SpokeResult(
                    status=ResultStatus.SUCCESS,
                    data=result,
                    metrics={'matched': False}
                )

            result.company_id = company_id
            result.company_matched = True
            self.stats['articles_matched'] += 1

            # Step 2: Detect events
            events = self.event_detector.detect_events(article)
            result.events_detected = events
            self.stats['events_detected'] += len(events)

            if not events:
                result.success = True
                result.processing_time_ms = int((time.time() - start_time) * 1000)

                return SpokeResult(
                    status=ResultStatus.SUCCESS,
                    data=result,
                    metrics={'events_detected': 0}
                )

            # Step 3: Emit signals for detected events
            signals_emitted = 0
            for event in events[:self.config.max_signals_per_article]:
                emitted = self._emit_signal(
                    correlation_id=correlation_id,
                    company_id=company_id,
                    article=article,
                    event=event
                )
                if emitted:
                    signals_emitted += 1

            result.signals_emitted = signals_emitted
            result.success = True
            result.processing_time_ms = int((time.time() - start_time) * 1000)

            return SpokeResult(
                status=ResultStatus.SUCCESS,
                data=result,
                hub_signal={
                    'signal_type': 'article_processed',
                    'impact': sum(e.impact for e in events if e.confidence >= self._get_min_confidence()),
                    'source': self.name,
                    'company_id': company_id
                } if signals_emitted > 0 else None,
                metrics={
                    'events_detected': len(events),
                    'signals_emitted': signals_emitted,
                    'processing_time_ms': result.processing_time_ms
                }
            )

        except Exception as e:
            logger.error(f"Error processing article {article.article_id}: {e}")
            self.stats['errors'] += 1
            result.failure_reason = str(e)
            result.error_code = "BLOG-001"

            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason=str(e)
            )

    def _process_feed(
        self,
        feed: RSSFeed,
        correlation_id: str
    ) -> SpokeResult:
        """Process an RSS feed."""
        articles = self.rss_ingestor.ingest_feed(feed)

        results = []
        for article in articles:
            result = self._process_article(article, article.correlation_id)
            results.append(result)

        return SpokeResult(
            status=ResultStatus.SUCCESS,
            data=results,
            metrics={
                'articles_ingested': len(articles),
                'articles_processed': len(results)
            }
        )

    def _process_batch(
        self,
        articles: List[NewsArticle],
        correlation_id: str
    ) -> SpokeResult:
        """Process a batch of articles."""
        results = []
        for article in articles:
            cid = article.correlation_id or correlation_id
            result = self._process_article(article, cid)
            results.append(result)

        successful = sum(1 for r in results if r.success)

        return SpokeResult(
            status=ResultStatus.SUCCESS,
            data=results,
            metrics={
                'total': len(articles),
                'successful': successful,
                'failed': len(articles) - successful
            }
        )

    def _match_company(self, article: NewsArticle) -> Optional[str]:
        """
        Match article to Company Hub record.

        Matching priority:
        1. Known company_id in metadata (from RSS feed)
        2. Domain match
        3. Exact name match
        4. Fuzzy match (threshold 0.90)

        Returns company_id if found, None otherwise.
        """
        # Check for known company from metadata
        known_id = article.raw_metadata.get('known_company_id')
        if known_id:
            return known_id

        # Try domain match
        for domain in article.domain_mentions:
            company_id = self._lookup_by_domain(domain)
            if company_id:
                return company_id

        # Try company name match
        for company_name in article.company_mentions:
            company_id = self._lookup_by_name(company_name)
            if company_id:
                return company_id

        return None

    def _lookup_by_domain(self, domain: str) -> Optional[str]:
        """
        Look up company by domain (GOLD match).

        Priority:
        1. Company Pipeline (production Neon lookup)
        2. Company Hub direct lookup
        3. Legacy hub.db (fallback)
        """
        if not domain:
            return None

        # Normalize domain
        domain = domain.lower().strip()
        if domain.startswith('www.'):
            domain = domain[4:]

        # PRIORITY 1: Use Company Pipeline if available
        if self._company_pipeline:
            try:
                company = self._company_pipeline.find_company_by_domain(domain)
                if company:
                    logger.debug(f"Domain {domain} matched via Company Pipeline")
                    return company.company_unique_id
            except Exception as e:
                logger.error(f"Company Pipeline domain lookup failed: {e}")

        # PRIORITY 2: Direct Company Hub lookup
        try:
            from hub.company import CompanyHub
            company_hub = CompanyHub()
            company = company_hub.find_company_by_domain(domain)
            if company:
                logger.debug(f"Domain {domain} matched via Company Hub")
                return company.company_unique_id
        except Exception as e:
            logger.error(f"Company Hub domain lookup failed: {e}")

        # PRIORITY 3: Legacy hub.db lookup (fallback)
        try:
            if hasattr(self.hub, 'db') and self.hub.db:
                result = self.hub.db.execute(
                    """
                    SELECT company_unique_id
                    FROM company.company_master
                    WHERE domain = %s
                    LIMIT 1
                    """,
                    (domain,)
                )
                row = result.fetchone() if result else None
                if row:
                    return row[0] if isinstance(row, (list, tuple)) else row.get('company_unique_id')
        except Exception as e:
            logger.error(f"Legacy domain lookup failed for {domain}: {e}")

        return None

    def _lookup_by_name(self, company_name: str) -> Optional[str]:
        """
        Look up company by name (with fuzzy matching).

        Priority:
        1. Company Pipeline with fuzzy matching
        2. Company Hub direct lookup
        3. Legacy hub.db lookup (exact match fallback)

        Uses fuzzy matching threshold of 0.90 for high confidence.
        """
        if not company_name:
            return None

        # Normalize name
        normalized = company_name.strip()

        # PRIORITY 1: Use Company Pipeline if available (with fuzzy matching)
        if self._company_pipeline:
            try:
                # Try via hub's fuzzy matching
                if hasattr(self._company_pipeline, 'hub'):
                    company = self._company_pipeline.hub.find_company_by_name(
                        normalized,
                        fuzzy_threshold=0.90  # High threshold for news matching
                    )
                    if company:
                        logger.debug(f"Company name {normalized} matched via Pipeline fuzzy")
                        return company.company_unique_id
            except Exception as e:
                logger.error(f"Company Pipeline name lookup failed: {e}")

        # PRIORITY 2: Direct Company Hub lookup with fuzzy matching
        try:
            from hub.company import CompanyHub
            company_hub = CompanyHub()
            company = company_hub.find_company_by_name(
                normalized,
                fuzzy_threshold=0.90
            )
            if company:
                logger.debug(f"Company name {normalized} matched via Company Hub fuzzy")
                return company.company_unique_id
        except Exception as e:
            logger.error(f"Company Hub name lookup failed: {e}")

        # PRIORITY 3: Legacy hub.db lookup (exact match fallback)
        try:
            if hasattr(self.hub, 'db') and self.hub.db:
                result = self.hub.db.execute(
                    """
                    SELECT company_unique_id
                    FROM company.company_master
                    WHERE LOWER(company_name) = %s
                    LIMIT 1
                    """,
                    (normalized.lower(),)
                )
                row = result.fetchone() if result else None
                if row:
                    return row[0] if isinstance(row, (list, tuple)) else row.get('company_unique_id')
        except Exception as e:
            logger.error(f"Legacy name lookup failed for {company_name}: {e}")

        return None

    def _queue_for_identity(self, article: NewsArticle, correlation_id: str):
        """Queue unmatched article for Company Hub identity resolution."""
        logger.info(
            f"Queuing article for identity resolution",
            extra={
                'correlation_id': correlation_id,
                'article_id': article.article_id,
                'company_mentions': article.company_mentions[:3],
                'domain_mentions': article.domain_mentions[:3],
            }
        )
        # In production, this would write to a queue table
        # blog_unmatched or similar

    def _emit_signal(
        self,
        correlation_id: str,
        company_id: str,
        article: NewsArticle,
        event: DetectedEvent
    ) -> bool:
        """
        Emit signal to BIT Engine with deduplication.

        Per PRD v2.1:
        - Dedup key: (company_id, signal_type, article_id)
        - Window: 30 days

        Returns True if signal was emitted, False if deduped/skipped.
        """
        if not self.bit_engine:
            return False

        # Check confidence threshold
        min_confidence = self._get_min_confidence()
        if event.confidence < min_confidence:
            self.stats['signals_below_threshold'] += 1
            logger.debug(
                f"Signal below threshold: {event.event_type.value} "
                f"(confidence: {event.confidence:.2f} < {min_confidence:.2f})"
            )
            return False

        # Check deduplication
        signal_type_str = event.event_type.value
        if self.signal_cache.exists(company_id, signal_type_str, article.article_id):
            self.stats['signals_deduped'] += 1
            logger.debug(
                f"Signal deduped: {signal_type_str} for company {company_id}",
                extra={'correlation_id': correlation_id}
            )
            return False

        # Map event type to SignalType
        signal_type = EVENT_TO_SIGNAL.get(event.event_type)
        if not signal_type:
            # Event type not mapped to BIT Engine signal
            logger.debug(f"Event type {event.event_type.value} not mapped to SignalType")
            return False

        # Emit to BIT Engine (with Neon persistence)
        try:
            self.bit_engine.create_signal(
                signal_type=signal_type,
                company_id=company_id,
                source_spoke=self.name,
                impact=event.impact,
                metadata={
                    'article_id': article.article_id,
                    'confidence': event.confidence,
                    'keywords_matched': event.keywords_matched[:5],
                    'source_url': article.url,
                    'detected_at': datetime.utcnow().isoformat(),
                },
                correlation_id=correlation_id  # For Neon persistence
            )

            # Record for deduplication
            self.signal_cache.record(
                company_id=company_id,
                signal_type=signal_type_str,
                article_id=article.article_id,
                correlation_id=correlation_id,
                confidence=event.confidence
            )

            self.stats['signals_emitted'] += 1
            logger.info(
                f"Signal emitted: {signal_type.value} for company {company_id} "
                f"(impact: {event.impact:+.1f}, confidence: {event.confidence:.2f})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to emit signal: {e}")
            self.stats['errors'] += 1
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get spoke statistics."""
        return {
            **self.stats,
            'event_detector_stats': self.event_detector.get_stats(),
            'rss_ingestor_stats': self.rss_ingestor.get_stats(),
            'config': {
                'enabled': self.config.enabled,
                'burn_in_mode': self.config.burn_in_mode,
                'min_confidence': self._get_min_confidence(),
                'dedup_window_days': self.config.dedup_window_days,
            }
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "BlogNodeSpoke",
    "BlogSpokeConfig",
    "load_blog_config",
    "SignalCache",
]
