"""
Blog Sub-Hub — IMO (Input-Middle-Output) Pipeline
═══════════════════════════════════════════════════════════════════════════

Complete signal pipeline for processing news articles and emitting BIT signals.

Pipeline Order:
    1. Input (ingest_article)
    2. Middle:
        a. parse_content
        b. extract_entities
        c. classify_event
        d. match_company
        e. validate_signal
    3. Output (emit_bit_signal)

Usage:
    from hubs.blog_content.imo.input import ingest_article
    from hubs.blog_content.imo.middle import parse_content, extract_entities, ...
    from hubs.blog_content.imo.output import emit_bit_signal

Or use the orchestrator:
    from hubs.blog_content.blog_node_spoke import run
"""

from . import input
from . import middle
from . import output

__all__ = ['input', 'middle', 'output']
