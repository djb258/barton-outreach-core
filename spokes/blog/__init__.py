"""
Blog Node - Spoke #3
====================
News and blog monitoring for company intelligence.

Signals to BIT Engine:
    - FUNDING_EVENT: +15 per funding announcement
    - ACQUISITION: +12 per M&A event
    - LEADERSHIP_CHANGE: +8 per executive change
    - EXPANSION: +7 per expansion announcement
    - PRODUCT_LAUNCH: +5 per product announcement
    - PARTNERSHIP: +5 per partnership announcement
    - LAYOFF: -3 per layoff announcement
    - NEGATIVE_NEWS: -5 per negative news event

Tools:
    - Tool 19: RSS Ingestor (rss_ingestor.py)

Barton ID Range: 04.04.02.04.4XXXX.###
"""

from .blog_spoke import (
    BlogNodeSpoke,
    BlogSpokeConfig,
    load_blog_config,
    SignalCache,
)

from .models import (
    # Enums
    EventType,
    ArticleSource,
    ConfidenceLevel,
    # Constants
    EVENT_IMPACTS,
    # Data classes
    NewsArticle,
    FundingDetails,
    AcquisitionDetails,
    LeadershipChangeDetails,
    LayoffDetails,
    ExpansionDetails,
    DetectedEvent,
    ArticleProcessingResult,
    # RSS models
    RSSFeed,
    RSSEntry,
)

from .event_detector import (
    EventDetector,
    # Keyword lists
    FUNDING_KEYWORDS,
    MA_KEYWORDS,
    LEADERSHIP_KEYWORDS,
    LAYOFF_KEYWORDS,
    EXPANSION_KEYWORDS,
    PRODUCT_LAUNCH_KEYWORDS,
    PARTNERSHIP_KEYWORDS,
    NEGATIVE_NEWS_KEYWORDS,
)

from .rss_ingestor import (
    RSSIngestor,
    RSSIngestorConfig,
    load_rss_config,
    FeedDiscovery,
    create_ingestor,
    ingest_company_blog,
)


__all__ = [
    # Main spoke
    "BlogNodeSpoke",
    "BlogSpokeConfig",
    "load_blog_config",
    "SignalCache",
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
    "RSSFeed",
    "RSSEntry",
    # Event detection
    "EventDetector",
    "FUNDING_KEYWORDS",
    "MA_KEYWORDS",
    "LEADERSHIP_KEYWORDS",
    "LAYOFF_KEYWORDS",
    "EXPANSION_KEYWORDS",
    "PRODUCT_LAUNCH_KEYWORDS",
    "PARTNERSHIP_KEYWORDS",
    "NEGATIVE_NEWS_KEYWORDS",
    # RSS ingestion (Tool 19)
    "RSSIngestor",
    "RSSIngestorConfig",
    "load_rss_config",
    "FeedDiscovery",
    "create_ingestor",
    "ingest_company_blog",
]
