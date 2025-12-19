"""
RSS Ingestor - Tool 19
======================
Ingests RSS feeds from company blogs and news sources.

Part of the Blog Sub-Hub (Spoke #3).
Tool Tier: Tier 0 (Free)

Sources:
- Company blogs (primary)
- PR Newswire RSS feeds
- Industry news feeds
"""

import os
import uuid
import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .models import (
    NewsArticle,
    ArticleSource,
    RSSFeed,
    RSSEntry,
)


logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class RSSIngestorConfig:
    """Configuration for RSS ingestor."""
    max_entries_per_feed: int = 50
    max_age_days: int = 30
    timeout_seconds: int = 30
    cache_ttl_hours: int = 1
    user_agent: str = "BartonOutreach/1.0 (RSS Ingestor)"
    enabled: bool = True


def load_rss_config() -> RSSIngestorConfig:
    """Load RSS configuration from environment."""
    return RSSIngestorConfig(
        max_entries_per_feed=int(os.getenv("RSS_MAX_ENTRIES", "50")),
        max_age_days=int(os.getenv("RSS_MAX_AGE_DAYS", "30")),
        timeout_seconds=int(os.getenv("RSS_TIMEOUT", "30")),
        cache_ttl_hours=int(os.getenv("RSS_CACHE_TTL_HOURS", "1")),
        enabled=os.getenv("RSS_ENABLED", "true").lower() == "true"
    )


# =============================================================================
# RSS INGESTOR (TOOL 19)
# =============================================================================

class RSSIngestor:
    """
    Tool 19: RSS Feed Ingestor

    Ingests and parses RSS feeds from company blogs and news sources.
    Converts entries to NewsArticle format for processing.

    Per PRD v2.1:
    - Company blogs: Daily polling
    - PR Newswire: Real-time (via RSS)
    - Industry news: Hourly polling
    """

    def __init__(self, config: RSSIngestorConfig = None):
        """
        Initialize RSS ingestor.

        Args:
            config: RSS ingestor configuration
        """
        self.config = config or load_rss_config()
        self._feedparser = None  # Lazy load
        self._article_cache: Dict[str, datetime] = {}  # Deduplication cache
        self._stats = {
            'feeds_processed': 0,
            'entries_found': 0,
            'entries_new': 0,
            'entries_cached': 0,
            'entries_too_old': 0,
            'errors': 0,
        }

    def _get_feedparser(self):
        """Lazy load feedparser."""
        if self._feedparser is None:
            try:
                import feedparser
                self._feedparser = feedparser
                logger.info("feedparser loaded successfully")
            except ImportError:
                logger.error("feedparser not installed: pip install feedparser")
                self._feedparser = False
        return self._feedparser if self._feedparser else None

    def ingest_feed(
        self,
        feed: RSSFeed,
        correlation_id_prefix: str = None
    ) -> List[NewsArticle]:
        """
        Ingest a single RSS feed.

        Args:
            feed: RSSFeed to process
            correlation_id_prefix: Optional prefix for correlation IDs

        Returns:
            List of NewsArticle objects (new entries only)
        """
        if not self.config.enabled:
            logger.info("RSS ingestor disabled")
            return []

        feedparser = self._get_feedparser()
        if not feedparser:
            logger.error("feedparser not available")
            self._stats['errors'] += 1
            return []

        articles = []
        self._stats['feeds_processed'] += 1

        try:
            # Parse feed
            logger.info(f"Parsing RSS feed: {feed.feed_url}")
            parsed = feedparser.parse(
                feed.feed_url,
                agent=self.config.user_agent
            )

            if parsed.bozo and parsed.bozo_exception:
                logger.warning(
                    f"Feed parse warning for {feed.feed_url}: {parsed.bozo_exception}"
                )

            entries = parsed.entries[:self.config.max_entries_per_feed]
            self._stats['entries_found'] += len(entries)

            for entry in entries:
                rss_entry = self._parse_entry(entry, feed.feed_id)
                if not rss_entry:
                    continue

                # Check if already processed (deduplication)
                if self._is_cached(rss_entry.entry_id):
                    self._stats['entries_cached'] += 1
                    continue

                # Check age
                if rss_entry.published:
                    age = datetime.utcnow() - rss_entry.published
                    if age.days > self.config.max_age_days:
                        self._stats['entries_too_old'] += 1
                        continue

                # Generate correlation ID
                correlation_id = self._generate_correlation_id(
                    rss_entry.entry_id,
                    correlation_id_prefix
                )

                # Convert to NewsArticle
                source = self._map_feed_type_to_source(feed.feed_type)
                article = rss_entry.to_news_article(correlation_id, source)

                # Add company context if known
                if feed.company_id:
                    article.raw_metadata['known_company_id'] = feed.company_id
                if feed.company_domain:
                    article.domain_mentions.append(feed.company_domain)

                articles.append(article)
                self._cache_entry(rss_entry.entry_id)
                self._stats['entries_new'] += 1

            # Update feed state
            feed.last_polled_at = datetime.utcnow()
            if entries:
                feed.last_entry_id = entries[0].get('id', entries[0].get('link'))

        except Exception as e:
            logger.error(f"Error ingesting feed {feed.feed_url}: {e}")
            self._stats['errors'] += 1

        logger.info(f"Ingested {len(articles)} new articles from {feed.feed_url}")
        return articles

    def ingest_feeds(
        self,
        feeds: List[RSSFeed],
        correlation_id_prefix: str = None
    ) -> List[NewsArticle]:
        """
        Ingest multiple RSS feeds.

        Args:
            feeds: List of RSSFeed objects
            correlation_id_prefix: Optional prefix for correlation IDs

        Returns:
            Combined list of NewsArticle objects
        """
        all_articles = []
        for feed in feeds:
            if not feed.enabled:
                continue

            # Check polling frequency
            if feed.last_polled_at:
                since_last = datetime.utcnow() - feed.last_polled_at
                if since_last.total_seconds() < (feed.poll_frequency_hours * 3600):
                    logger.debug(f"Skipping feed {feed.feed_url} (not due for poll)")
                    continue

            articles = self.ingest_feed(feed, correlation_id_prefix)
            all_articles.extend(articles)

        return all_articles

    def _parse_entry(self, entry: Dict[str, Any], feed_id: str) -> Optional[RSSEntry]:
        """Parse a feedparser entry into RSSEntry."""
        try:
            entry_id = entry.get('id') or entry.get('link') or entry.get('title', '')
            if not entry_id:
                return None

            # Generate stable entry ID
            entry_id = self._generate_entry_id(entry_id, feed_id)

            # Parse published date
            published = None
            if 'published_parsed' in entry and entry.published_parsed:
                try:
                    from time import mktime
                    published = datetime.fromtimestamp(mktime(entry.published_parsed))
                except Exception:
                    pass

            # Get content
            content = ""
            if 'content' in entry and entry.content:
                content = entry.content[0].get('value', '')
            elif 'summary' in entry:
                content = entry.summary

            # Clean HTML from content
            content = self._strip_html(content)

            return RSSEntry(
                entry_id=entry_id,
                feed_id=feed_id,
                title=entry.get('title', 'Untitled'),
                link=entry.get('link', ''),
                published=published,
                summary=self._strip_html(entry.get('summary', '')),
                content=content,
                author=entry.get('author'),
                tags=[tag.get('term', '') for tag in entry.get('tags', [])]
            )

        except Exception as e:
            logger.warning(f"Failed to parse entry: {e}")
            return None

    def _generate_entry_id(self, original_id: str, feed_id: str) -> str:
        """Generate stable entry ID from original."""
        combined = f"{feed_id}:{original_id}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _generate_correlation_id(
        self,
        entry_id: str,
        prefix: str = None
    ) -> str:
        """Generate correlation ID for article."""
        # Use entry_id as seed for reproducible correlation ID
        # This ensures reprocessing uses same correlation_id (idempotency)
        seed = f"rss:{entry_id}"
        hash_bytes = hashlib.sha256(seed.encode()).digest()

        # Format as UUID v4
        uuid_obj = uuid.UUID(bytes=hash_bytes[:16], version=4)

        if prefix:
            return f"{prefix}-{str(uuid_obj)}"
        return str(uuid_obj)

    def _map_feed_type_to_source(self, feed_type: str) -> ArticleSource:
        """Map feed type to ArticleSource enum."""
        mapping = {
            'company_blog': ArticleSource.COMPANY_BLOG,
            'pr_newswire': ArticleSource.PR_NEWSWIRE,
            'globenewswire': ArticleSource.GLOBENEWSWIRE,
            'news': ArticleSource.RSS_FEED,
        }
        return mapping.get(feed_type, ArticleSource.RSS_FEED)

    def _strip_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ""
        try:
            import re
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        except Exception:
            return text

    def _is_cached(self, entry_id: str) -> bool:
        """Check if entry is in deduplication cache."""
        if entry_id in self._article_cache:
            cached_at = self._article_cache[entry_id]
            cache_age = datetime.utcnow() - cached_at
            if cache_age.total_seconds() < (self.config.cache_ttl_hours * 3600):
                return True
        return False

    def _cache_entry(self, entry_id: str):
        """Add entry to deduplication cache."""
        self._article_cache[entry_id] = datetime.utcnow()

        # Clean old entries (simple TTL cleanup)
        cutoff = datetime.utcnow() - timedelta(hours=self.config.cache_ttl_hours * 2)
        self._article_cache = {
            k: v for k, v in self._article_cache.items()
            if v > cutoff
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get ingestor statistics."""
        return {
            **self._stats,
            'cache_size': len(self._article_cache),
            'enabled': self.config.enabled,
        }


# =============================================================================
# FEED DISCOVERY
# =============================================================================

class FeedDiscovery:
    """
    Discovers RSS feeds from company websites.

    Used to automatically find blog/news feeds for companies.
    """

    # Common RSS feed paths
    COMMON_PATHS = [
        '/feed',
        '/feed/',
        '/rss',
        '/rss/',
        '/blog/feed',
        '/blog/rss',
        '/news/feed',
        '/news/rss',
        '/feed.xml',
        '/rss.xml',
        '/atom.xml',
        '/index.xml',
        '/blog/feed.xml',
        '/blog/atom.xml',
    ]

    def __init__(self):
        self._requests = None

    def _get_requests(self):
        """Lazy load requests."""
        if self._requests is None:
            try:
                import requests
                self._requests = requests
            except ImportError:
                logger.error("requests not installed")
                self._requests = False
        return self._requests if self._requests else None

    def discover_feeds(self, domain: str) -> List[str]:
        """
        Discover RSS feeds for a domain.

        Args:
            domain: Company domain (e.g., 'acme.com')

        Returns:
            List of discovered feed URLs
        """
        requests = self._get_requests()
        if not requests:
            return []

        discovered = []
        base_url = f"https://{domain}"

        for path in self.COMMON_PATHS:
            url = f"{base_url}{path}"
            try:
                response = requests.head(
                    url,
                    timeout=5,
                    allow_redirects=True,
                    headers={'User-Agent': 'BartonOutreach/1.0'}
                )
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if any(ct in content_type for ct in ['xml', 'rss', 'atom']):
                        discovered.append(url)
                        logger.info(f"Discovered feed: {url}")
            except Exception:
                continue

        return discovered

    def create_feed_for_company(
        self,
        company_id: str,
        domain: str,
        feed_url: str = None
    ) -> Optional[RSSFeed]:
        """
        Create RSSFeed for a company.

        Args:
            company_id: Company unique ID
            domain: Company domain
            feed_url: Optional specific feed URL

        Returns:
            RSSFeed object or None if no feed found
        """
        if feed_url:
            urls = [feed_url]
        else:
            urls = self.discover_feeds(domain)

        if not urls:
            return None

        feed_id = hashlib.sha256(f"{company_id}:{urls[0]}".encode()).hexdigest()[:12]

        return RSSFeed(
            feed_id=feed_id,
            feed_url=urls[0],
            company_id=company_id,
            company_domain=domain,
            feed_type='company_blog',
            poll_frequency_hours=24
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_ingestor(config: Dict[str, Any] = None) -> RSSIngestor:
    """Create RSS ingestor with optional config overrides."""
    base_config = load_rss_config()
    if config:
        for key, value in config.items():
            if hasattr(base_config, key):
                setattr(base_config, key, value)
    return RSSIngestor(config=base_config)


def ingest_company_blog(
    company_id: str,
    domain: str,
    feed_url: str = None
) -> List[NewsArticle]:
    """
    Convenience function to ingest a company's blog RSS feed.

    Args:
        company_id: Company unique ID
        domain: Company domain
        feed_url: Optional specific feed URL

    Returns:
        List of NewsArticle objects
    """
    discovery = FeedDiscovery()
    feed = discovery.create_feed_for_company(company_id, domain, feed_url)

    if not feed:
        logger.warning(f"No RSS feed found for {domain}")
        return []

    ingestor = create_ingestor()
    return ingestor.ingest_feed(feed, correlation_id_prefix=company_id[:8])


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Config
    "RSSIngestorConfig",
    "load_rss_config",
    # Main classes
    "RSSIngestor",
    "FeedDiscovery",
    # Convenience
    "create_ingestor",
    "ingest_company_blog",
]
