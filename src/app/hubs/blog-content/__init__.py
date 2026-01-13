"""
Blog Sub-Hub — News & Content Signal Pipeline
═══════════════════════════════════════════════════════════════════════════

Doctrine: /hubs/blog-content/PRD.md
Version: 1.0.0

This sub-hub processes external news content and converts it into structured
BIT (Buyer Intent Tool) signals for downstream consumption.

ROLE:
    - Read-only signal emitter
    - CANNOT create companies
    - CANNOT trigger enrichment
    - CANNOT mutate Company Lifecycle

PIPELINE:
    Ingest → Parse → Extract → Classify → Match → Validate → Emit

TERMINAL STATES:
    - EMITTED: Signal sent to BIT Engine
    - QUEUED: Article queued for identity resolution
    - DROPPED: Failed validation or processing

USAGE:
    from hubs.blog_content import run
    
    result = await run({
        'title': 'Acme Corp Raises $50M Series B',
        'content': '...',
        'source': 'newsapi',
        'source_url': 'https://...',
        'published_at': '2024-01-15T10:30:00Z'
    })
    
    print(result.terminal_state)  # EMITTED / QUEUED / DROPPED
"""

from .blog_node_spoke import run, get_spoke, BlogNodeSpoke, PipelineResult

__all__ = [
    'run',
    'get_spoke',
    'BlogNodeSpoke',
    'PipelineResult',
]

__version__ = '1.0.0'
