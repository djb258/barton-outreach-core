"""
Blog Sub-Hub — Input Layer
═══════════════════════════════════════════════════════════════════════════

Ingestion and normalization of raw article content.

Modules:
    - ingest_article: Article ingestion and validation
"""

from .ingest_article import (
    ingest_article,
    ArticlePayload,
    ArticleSource,
    IngestionResult,
    normalize_newsapi_article,
    normalize_rss_entry,
    normalize_sec_8k,
)

__all__ = [
    'ingest_article',
    'ArticlePayload',
    'ArticleSource',
    'IngestionResult',
    'normalize_newsapi_article',
    'normalize_rss_entry',
    'normalize_sec_8k',
]
