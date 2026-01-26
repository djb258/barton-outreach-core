"""
Blog Sub-Hub — Middle Layer
═══════════════════════════════════════════════════════════════════════════

Core processing pipeline stages.

Modules:
    - parse_content: Content cleaning and normalization
    - extract_entities: NER and entity extraction
    - classify_event: Event classification (deterministic + LLM)
    - match_company: Company matching (FAIL CLOSED)
    - validate_signal: Signal validation gate
"""

from .parse_content import parse_content, ParsedContent, ParseResult
from .extract_entities import extract_entities, ExtractedEntities, ExtractionResult
from .classify_event import classify_event, ClassifiedEvent, ClassificationResult, EventType
from .match_company import match_company, MatchedEvent, MatchResult
from .validate_signal import validate_signal, ValidatedSignal, ValidationResult
from .hub_status import (
    BlogHubStatusResult,
    compute_blog_hub_status,
    backfill_blog_hub_status,
    generate_blog_signal_hash,
    FRESHNESS_DAYS as BLOG_FRESHNESS_DAYS,
    MIN_SIGNALS,
)

__all__ = [
    # Parse
    'parse_content',
    'ParsedContent',
    'ParseResult',
    # Extract
    'extract_entities',
    'ExtractedEntities',
    'ExtractionResult',
    # Classify
    'classify_event',
    'ClassifiedEvent',
    'ClassificationResult',
    'EventType',
    # Match
    'match_company',
    'MatchedEvent',
    'MatchResult',
    # Validate
    'validate_signal',
    'ValidatedSignal',
    'ValidationResult',
    # Hub status computation
    'BlogHubStatusResult',
    'compute_blog_hub_status',
    'backfill_blog_hub_status',
    'generate_blog_signal_hash',
    'BLOG_FRESHNESS_DAYS',
    'MIN_SIGNALS',
]
